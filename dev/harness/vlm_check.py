"""S11 — the VLM reference check.

Takes the operator's ground-truth selection (``dev/reference/selection.json``,
falling back to every ``quality == "good"`` record in ``dev/reference/meta/*.json``
when no selection has been made), turns each reference photograph's recorded
situation into a ``SiteContext``, generates and renders the closest matching
building, and writes the pair side by side into a comparison sheet for a human
or a VLM to look at.

Two limits are structural here, not advisory, and the sheet states both:

* **A photograph supports qualitative comparison and no measurement at all.**
  Every image in the corpus was taken from an unknown position with an unknown
  lens; the facade is foreshortened, the roof is seen from below, verticals
  converge. Nothing in this harness reports a metre or a ratio read off a
  photograph, and nothing should. Where a number appears next to a generated
  render it comes from the IR, never from the JPEG.
* **A visual check is a tripwire, not a passing grade.** "That looks wrong" is
  strong evidence; "that looks right" is weak. A systematic small error — every
  window three percent too tall — is invisible here by construction, and
  belongs to the dimensional assertions in ``tests/`` instead.

The situation table
-------------------
The corpus records ``year``, ``klass``, ``street`` (a postal address) and
sometimes ``corner``. It does **not** record street width, parcel width or
ground programme, and the generator needs all three. ``SITUATIONS`` below
supplies them per street, and every entry carries its own provenance flag:

``measured``  — width taken from a published carriageway/alignment figure.
``estimated`` — width inferred from the street's class and date of cutting.
``unknown``   — nothing better than the family default was available.

An estimated street width is an input to the comparison, not an output of it:
if a pair disagrees only about height, the first question is whether this table
is wrong, and the sheet prints the flag next to every render so that question
is always askable.

Usage
-----
    python3 dev/harness/vlm_check.py [--out DIR]

Writes ``dev/logs/vlm/`` : one ``pair_NN_*.png`` per comparable reference,
``sheet.html`` (all pairs, with metadata and the limits stated), and
``situations.json`` (what was fed to ``generate()`` for each, so a disputed
pair can be re-run by hand).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import zlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.render.svg import render  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402

REFERENCE = ROOT / "dev" / "reference"
DEFAULT_OUT = ROOT / "dev" / "logs" / "vlm"


# --------------------------------------------------------------------------
# 1. The situation table
# --------------------------------------------------------------------------
# Keyed by a lowercase substring of the record's ``street`` field. First match
# wins, so put the specific before the general. ``w`` is the full street width
# in metres (facade to facade — what the gabarit reads), ``src`` its provenance,
# ``parcel`` a typical parcel frontage for that street's parcellaire.

SITUATIONS: tuple[tuple[str, dict], ...] = (
    # --- grand percements: the wide cut streets -----------------------------
    ("place saint-michel", dict(w=30.0, parcel=17.0, src="estimated", ground="shop")),
    ("avenue de l'op", dict(w=30.0, parcel=18.0, src="measured", ground="shop")),
    ("avenue opera", dict(w=30.0, parcel=18.0, src="measured", ground="shop")),
    ("magenta", dict(w=30.0, parcel=16.0, src="estimated", ground="shop")),
    ("sébastopol", dict(w=30.0, parcel=15.0, src="measured", ground="shop")),
    ("sebastopol", dict(w=30.0, parcel=15.0, src="measured", ground="shop")),
    ("boulevard voltaire", dict(w=35.0, parcel=14.0, src="measured", ground="shop")),
    ("port-royal", dict(w=35.0, parcel=15.0, src="measured", ground="shop")),
    ("boulevard saint-michel", dict(w=30.0, parcel=15.0, src="measured", ground="shop")),
    ("blvd saint-michel", dict(w=30.0, parcel=15.0, src="measured", ground="shop")),
    ("rue de rennes", dict(w=22.0, parcel=15.0, src="measured", ground="shop")),
    ("rue réaumur", dict(w=20.0, parcel=16.0, src="measured", ground="shop")),
    ("reaumur", dict(w=20.0, parcel=16.0, src="measured", ground="shop")),
    ("rue royale", dict(w=25.0, parcel=14.0, src="measured", ground="shop")),
    ("avenue henri martin", dict(w=40.0, parcel=18.0, src="measured", ground="residential")),
    ("place de l'alma", dict(w=30.0, parcel=15.0, src="estimated", ground="residential")),
    ("place alma", dict(w=30.0, parcel=15.0, src="estimated", ground="residential")),
    ("avenue rapp", dict(w=35.0, parcel=13.0, src="measured", ground="residential")),
    ("rue étienne marcel", dict(w=20.0, parcel=13.0, src="measured", ground="shop")),
    ("rue etienne marcel", dict(w=20.0, parcel=13.0, src="measured", ground="shop")),
    ("rue ordener", dict(w=20.0, parcel=12.0, src="estimated", ground="shop")),
    ("jules sandeau", dict(w=20.0, parcel=14.0, src="estimated", ground="residential")),
    ("spontini", dict(w=20.0, parcel=14.0, src="estimated", ground="residential")),
    ("longchamp", dict(w=20.0, parcel=14.0, src="estimated", ground="residential")),
    ("tocqueville", dict(w=15.0, parcel=12.0, src="estimated", ground="shop")),
    ("rue legendre", dict(w=12.0, parcel=11.0, src="estimated", ground="shop")),
    ("rue de charenton", dict(w=15.0, parcel=10.0, src="estimated", ground="shop")),
    ("faubourg saint-antoine", dict(w=15.0, parcel=9.0, src="estimated", ground="shop")),
    ("faubourg montmartre", dict(w=12.0, parcel=10.0, src="estimated", ground="shop")),
    ("tombe-issoire", dict(w=12.0, parcel=11.0, src="estimated", ground="carriage")),
    # --- ordinary and old streets -----------------------------------------
    ("rue le peletier", dict(w=12.0, parcel=15.0, src="estimated", ground="shop")),
    ("rue la fontaine", dict(w=12.0, parcel=16.0, src="estimated", ground="residential")),
    ("rue de fleurus", dict(w=12.0, parcel=13.0, src="estimated", ground="residential")),
    ("rue blanche", dict(w=12.0, parcel=12.0, src="estimated", ground="shop")),
    ("rue de la victoire", dict(w=12.0, parcel=12.0, src="estimated", ground="residential")),
    ("tour-des-dames", dict(w=10.0, parcel=12.0, src="estimated", ground="residential")),
    ("tour des dames", dict(w=10.0, parcel=12.0, src="estimated", ground="residential")),
    ("cité malesherbes", dict(w=10.0, parcel=11.0, src="estimated", ground="residential")),
    ("square d'orl", dict(w=15.0, parcel=14.0, src="estimated", ground="residential")),
    ("rue du sommerard", dict(w=10.0, parcel=9.0, src="estimated", ground="shop")),
    ("saint-merri", dict(w=8.0, parcel=8.0, src="estimated", ground="shop")),
    ("monsieur-le-prince", dict(w=10.0, parcel=10.0, src="estimated", ground="shop")),
    ("monsieur le prince", dict(w=10.0, parcel=10.0, src="estimated", ground="shop")),
    ("francs-bourgeois", dict(w=10.0, parcel=8.0, src="estimated", ground="shop")),
    ("francs bourgeois", dict(w=10.0, parcel=8.0, src="estimated", ground="shop")),
    ("vaucouleurs", dict(w=10.0, parcel=8.0, src="estimated", ground="shop")),
    ("rue vavin", dict(w=12.0, parcel=11.0, src="measured", ground="shop")),
    ("rue boulard", dict(w=12.0, parcel=11.0, src="estimated", ground="shop")),
    ("rue halévy", dict(w=18.0, parcel=15.0, src="estimated", ground="shop")),
    ("rue halevy", dict(w=18.0, parcel=15.0, src="estimated", ground="shop")),
    ("rue agar", dict(w=10.0, parcel=12.0, src="estimated", ground="shop")),
    ("rue gros", dict(w=10.0, parcel=12.0, src="estimated", ground="shop")),
    ("rue broca", dict(w=12.0, parcel=12.0, src="estimated", ground="shop")),
    ("labiche", dict(w=15.0, parcel=13.0, src="estimated", ground="residential")),
)

# Family default when the street is unknown or absent.
FAMILY_DEFAULT = {
    "restauration": dict(w=10.0, parcel=11.0, year=1835, src="unknown", ground="residential"),
    "second-empire": dict(w=22.0, parcel=15.0, year=1865, src="unknown", ground="shop"),
    "third-republic": dict(w=20.0, parcel=14.0, year=1878, src="unknown", ground="shop"),
    "belle-epoque": dict(w=15.0, parcel=14.0, year=1893, src="unknown", ground="residential"),
    "post-1902": dict(w=15.0, parcel=13.0, year=1902, src="unknown", ground="shop"),
    "corner": dict(w=18.0, parcel=14.0, year=1880, src="unknown", ground="shop"),
    "class-range": dict(w=15.0, parcel=12.0, year=1875, src="unknown", ground="shop"),
    "ground-floor": dict(w=12.0, parcel=11.0, year=1875, src="unknown", ground="shop"),
}

KLASS = {
    "modest": BuildingClass.MODEST,
    "ordinary": BuildingClass.ORDINARY,
    "comfortable": BuildingClass.COMFORTABLE,
    "grand": BuildingClass.GRAND,
}

GROUND = {
    "residential": GroundProgramme.RESIDENTIAL,
    "shop": GroundProgramme.SHOP,
    "cafe": GroundProgramme.CAFE,
    "carriage": GroundProgramme.CARRIAGE,
    "office": GroundProgramme.OFFICE,
}

# Reference photographs that are close-up DETAILS (a mascaron, a stretch of
# railing, one shopfront, a dormer) rather than a whole elevation. A detail
# cannot be compared against a whole-facade render on the axes this check
# cares about — storey count, proportion, roofline — so they are rendered in
# the sheet under their own heading, compared only on the one feature they
# show, and never counted as a facade pair.
DETAIL_MARKERS = (
    "mascaron",
    "caryatid",
    "caryatide",
    "atlas",
    "ironwork",
    "portail",
    "detail",
    "devanture",
    "comptoir",
    "entree",
    "entrée",
    "lettering",
    "dormers",
    "metro",
    "passage",
    "cour",
    "bakery",
    "old-bakery",
    "porte-cochere",
    "pediment",
)


@dataclass(frozen=True)
class Pair:
    index: int
    family: str
    ref_file: str
    title: str
    shows: str
    street: str
    ref_year: str
    klass: str
    is_detail: bool
    # what we fed the generator
    street_width: float
    street_width_source: str
    parcel_width: float
    year: int
    corner: bool
    ground: str
    seed: int
    # what came back (from the IR, never from the photograph)
    storeys: int
    bay_count: int
    bay_widths: tuple
    eaves_height: float
    total_height: float
    legal_ceiling: float
    envelope: str
    gen_png: str
    pair_png: str


# --------------------------------------------------------------------------
# 2. Loading the ground-truth set
# --------------------------------------------------------------------------


def _good_from_meta(families: set[str] | None = None) -> list[dict]:
    """Every ``quality == "good"`` record, optionally restricted to families."""
    out: list[dict] = []
    for meta in sorted((REFERENCE / "meta").glob("*.json")):
        blob = json.loads(meta.read_text())
        family = blob.get("family", meta.stem)
        if families is not None and family not in families:
            continue
        for img in blob.get("images", []):
            if img.get("quality") == "good":
                out.append({**img, "family": family})
    return out


def load_selection(augment: bool = False) -> tuple[list[dict], str]:
    """The operator's selection, or the documented fallback.

    Returns ``(records, provenance)``. ``provenance`` is printed at the top of
    the sheet and of the report: a fallback run is a materially weaker check —
    it uses the scraper's own ``quality`` field, which grades how good the
    PHOTOGRAPH is, not whether the operator judged the BUILDING to be ground
    truth — and that difference has to be visible in the output.

    ``augment`` covers the third case, which is the one this corpus is
    actually in: a selection exists, but the scraper has since added whole
    FAMILIES the selection could not have contained because they did not exist
    when it was made. Silently checking only the selection would then leave the
    newest — and most targeted — reference material unlooked-at, while
    silently folding it in would misreport unreviewed images as ground truth.
    So it is opt-in, and every record it adds is tagged ``unselected`` and
    reported separately.
    """
    sel = REFERENCE / "selection.json"
    if sel.exists():
        data = json.loads(sel.read_text())
        records = list(data.get("selected", []))
        note = (
            f"operator selection ({sel.relative_to(ROOT)}, "
            f"{len(records)} images, generated_by={data.get('generated_by', '?')!r})"
        )
        chosen = {r.get("family") for r in records}
        extra_families = {
            r["family"] for r in _good_from_meta() if r["family"] not in chosen
        }
        if extra_families:
            note += (
                f" — NOTE: {len(extra_families)} scraped families postdate this selection "
                f"and are not in it: {', '.join(sorted(extra_families))}"
            )
            if augment:
                added = _good_from_meta(extra_families)
                for r in added:
                    r["unselected"] = True
                records += added
                note += f"; --augment folded in their {len(added)} quality=='good' records, tagged UNSELECTED"
        return records, note
    records = []
    for meta in sorted((REFERENCE / "meta").glob("*.json")):
        blob = json.loads(meta.read_text())
        family = blob.get("family", meta.stem)
        for img in blob.get("images", []):
            if img.get("quality") == "good":
                records.append({**img, "family": family})
    return records, (
        f"FALLBACK — no selection.json on disk; used every quality=='good' record "
        f"in dev/reference/meta/*.json ({len(records)} images)"
    )


def parse_year(raw: str, default: int) -> int:
    """First four-digit year in the record, else the family default.

    A record like ``"1895-1898"`` or ``"between 1895 and 1899"`` gives the
    first year; ``"circa 1900-1902"`` likewise. The corpus's own dating
    discipline means most records are empty, and an empty record must fall
    through to the family default rather than be invented here.
    """
    digits = ""
    for ch in str(raw):
        if ch.isdigit():
            digits += ch
            if len(digits) == 4:
                return int(digits)
        else:
            digits = ""
    return default


def situation_for(rec: dict) -> dict:
    family = rec.get("family", "")
    default = FAMILY_DEFAULT.get(family, FAMILY_DEFAULT["class-range"])
    street = (rec.get("street") or "").lower()
    # EARLIEST match in the string wins, not first-in-table. Several records
    # append provenance prose to the address ("31, rue de Fleurus ... filed
    # within a Commons album titled 'Immeuble avenue Henri Martin'"), and a
    # table-order match picked the album's street over the building's — a
    # 12 m street generated as a 40 m avenue. The address is at the front of
    # the field by the corpus's own convention, so position is the tie-break.
    hit = None
    best = len(street) + 1
    for key, cfg in SITUATIONS:
        at = street.find(key)
        if at != -1 and at < best:
            best, hit = at, cfg
    cfg = dict(default)
    if hit:
        cfg.update(hit)
    year = parse_year(rec.get("year", ""), default["year"])
    # The generator's typology is Paris 1820-1902. A record outside that is
    # clamped and SAID SO rather than silently extrapolated.
    clamped = min(max(year, 1820), 1902)
    cfg["year"] = clamped
    cfg["year_clamped"] = clamped != year
    cfg["year_raw"] = year
    return cfg


def is_detail(rec: dict) -> bool:
    name = os.path.basename(rec.get("file", "")).lower()
    title = (rec.get("title") or "").lower()
    return any(m in name or m in title for m in DETAIL_MARKERS)


def corner_of(rec: dict) -> bool:
    if rec.get("corner") is True:
        return True
    if rec.get("family") == "corner":
        return True
    blob = f"{rec.get('title', '')} {rec.get('shows', '')}".lower()
    return "corner" in blob or "angle" in blob


# --------------------------------------------------------------------------
# 3. Rendering the pairs
# --------------------------------------------------------------------------


def rasterise(svg_path: Path, png_path: Path, width_px: int) -> bool:
    try:
        subprocess.run(
            ["rsvg-convert", "-w", str(width_px), str(svg_path), "-o", str(png_path)],
            check=True,
            capture_output=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def stitch(ref: Path, gen: Path, out: Path, height_px: int = 900) -> bool:
    """Reference left, generated right, on one canvas at a shared HEIGHT.

    Shared height, never shared width: the two are put beside each other so a
    reader can compare storey COUNT and RHYTHM, which survive the scaling. It
    is emphatically not a shared scale — the photograph has no scale.
    No burnt-in caption, and that is deliberate rather than lazy: ``montage
    -label`` needs a usable Freetype font, this machine's ImageMagick has
    none, and montage then WRITES THE FILE AND STILL EXITS 1 — so a
    ``check=True`` wrapper reports failure for a sheet that is sitting on
    disk and perfectly readable. Captioning is the sheet's job (``sheet.html``
    carries the full metadata beside each pair); the pair PNG carries only the
    two pictures, and success is judged by whether the output actually
    appeared, not by an exit code that lies.
    """
    try:
        subprocess.run(
            [
                "magick",
                str(ref), "-resize", f"x{height_px}",
                str(gen), "-resize", f"x{height_px}",
                "-background", "#111111", "-gravity", "south", "+append",
                "-bordercolor", "#111111", "-border", "10",
                str(out),
            ],
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return out.exists() and out.stat().st_size > 0


def build(out_dir: Path, augment: bool = False) -> tuple[list[Pair], str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "svg").mkdir(exist_ok=True)
    records, provenance = load_selection(augment)
    pairs: list[Pair] = []

    for i, rec in enumerate(records):
        cfg = situation_for(rec)
        klass = KLASS.get(rec.get("klass", ""), BuildingClass.COMFORTABLE)
        ground = GROUND[cfg["ground"]]
        detail = is_detail(rec)
        site = SiteContext(
            street_width=cfg["w"],
            parcel_width=cfg["parcel"],
            parcel_depth=18.0,
            year=cfg["year"],
            klass=klass,
            ground=ground,
            corner=corner_of(rec),
            # Seed derived from the reference's own filename so a pair is
            # reproducible and stable across runs, and so two references do
            # not silently get the same building. ``crc32`` and not ``hash``:
            # Python salts string hashing per process, so ``hash`` would give
            # a different building every run and make "this pair looks wrong"
            # unciteable an hour later.
            seed=zlib.crc32(os.path.basename(rec["file"]).encode()) % 9973,
        )
        node, _log = generate(site)
        svg = render(node, width_px=900)
        stem = f"pair_{i:02d}_{Path(rec['file']).stem}"
        svg_path = out_dir / "svg" / f"{stem}.svg"
        svg_path.write_text(svg)
        gen_png = out_dir / f"{stem}_gen.png"
        rasterise(svg_path, gen_png, 900)
        ref_abs = REFERENCE / rec["file"]
        pair_png = out_dir / f"{stem}.png"
        ok = ref_abs.exists() and stitch(ref_abs, gen_png, pair_png)

        bays = []
        for st in node.children:
            if st.kind == "storey":
                bays = [round(float(b.props.get("w", 0.0)), 2) for b in st.children if b.kind == "bay"]
                break
        storeys = sum(1 for c in node.children if c.kind == "storey")

        pairs.append(
            Pair(
                index=i,
                family=rec.get("family", ""),
                ref_file=rec["file"],
                title=rec.get("title", ""),
                shows=rec.get("shows", ""),
                street=rec.get("street", ""),
                ref_year=str(rec.get("year", "")),
                klass=rec.get("klass", ""),
                is_detail=detail,
                street_width=site.street_width,
                street_width_source=cfg["src"] + (" (year clamped to typology range)" if cfg["year_clamped"] else ""),
                parcel_width=site.parcel_width,
                year=site.year,
                corner=site.corner,
                ground=site.ground.value,
                seed=site.seed,
                storeys=storeys,
                bay_count=len(bays),
                bay_widths=tuple(bays),
                eaves_height=round(float(node.props.get("eaves_height", 0.0)), 2),
                total_height=round(float(node.props.get("h", 0.0)), 2),
                legal_ceiling=round(float(node.props.get("legal_cornice_ceiling", 0.0)), 2),
                envelope=str(node.props.get("envelope", "")),
                gen_png=gen_png.name,
                pair_png=pair_png.name if ok else "",
            )
        )
    return pairs, provenance


# --------------------------------------------------------------------------
# 4. The sheet
# --------------------------------------------------------------------------

LIMITS = """
<h2>Two limits this sheet does not get to ignore</h2>
<ol>
<li><b>A photograph supports qualitative comparison and no measurement at all.</b>
Unknown camera position, unknown lens, converging verticals, a roof seen from
below. Every number printed beside a render below came out of the IR. No number
anywhere on this page was read off a photograph, and none should be.</li>
<li><b>A visual check is a tripwire, not a passing grade.</b> "That looks wrong"
is strong evidence something is broken. "That looks right" is weak evidence of
nothing much. Systematic small error is invisible here by construction and
belongs to the dimensional assertions.</li>
</ol>
<p>The photographs' situations are also partly <i>estimated</i> — the corpus
records an address, not a street width. Each pair prints the provenance of the
width it was generated from. A height disagreement on an <code>estimated</code>
row is a question about this harness's table before it is a question about the
generator.</p>
"""


def write_sheet(pairs: Iterable[Pair], provenance: str, out_dir: Path) -> None:
    rows = []
    for p in pairs:
        ref_rel = os.path.relpath(REFERENCE / p.ref_file, out_dir)
        badge = "DETAIL — one feature only" if p.is_detail else "FACADE"
        rows.append(f"""
<section class="{'detail' if p.is_detail else 'facade'}">
  <h3>{p.index:02d} · {p.title} <span class="badge">{badge}</span></h3>
  <p class="meta">{p.family} · {p.street or '(street unrecorded)'} ·
     recorded year {p.ref_year or '(none)'} · class {p.klass}</p>
  <p class="shows">{p.shows}</p>
  <div class="pair">
    <figure><img src="{ref_rel}"><figcaption>reference photograph</figcaption></figure>
    <figure><img src="{p.gen_png}"><figcaption>generated</figcaption></figure>
  </div>
  <table>
   <tr><td>street width</td><td>{p.street_width:.1f} m <i>({p.street_width_source})</i></td>
       <td>parcel</td><td>{p.parcel_width:.1f} m</td>
       <td>year</td><td>{p.year}</td>
       <td>corner</td><td>{p.corner}</td>
       <td>ground</td><td>{p.ground}</td></tr>
   <tr><td>storeys</td><td>{p.storeys}</td>
       <td>bays</td><td>{p.bay_count} @ {p.bay_widths}</td>
       <td>eaves</td><td>{p.eaves_height} m</td>
       <td>legal ceiling</td><td>{p.legal_ceiling} m</td>
       <td>envelope</td><td>{p.envelope}</td></tr>
  </table>
</section>""")

    html = f"""<!doctype html><meta charset="utf-8"><title>VLM reference check</title>
<style>
 body {{ font: 14px/1.5 -apple-system, sans-serif; margin: 2rem; background:#151515; color:#ddd; }}
 h1,h2,h3 {{ font-weight: 600; }}
 section {{ border-top: 1px solid #333; padding: 1.2rem 0; }}
 section.detail {{ opacity: .85; }}
 .badge {{ font-size: 11px; background:#333; padding:2px 8px; border-radius:9px; }}
 .meta {{ color:#8a8a8a; }}
 .shows {{ color:#b9b9b9; max-width: 70ch; }}
 .pair {{ display:flex; gap:1rem; align-items:flex-start; }}
 .pair img {{ max-height: 620px; max-width: 46vw; background:#222; }}
 figcaption {{ color:#777; font-size:12px; }}
 table {{ font-size:12px; color:#999; border-collapse: collapse; margin-top:.6rem; }}
 td {{ padding: 2px 10px 2px 0; }}
</style>
<h1>VLM reference check</h1>
<p><b>Ground-truth set:</b> {provenance}</p>
{LIMITS}
{''.join(rows)}
"""
    (out_dir / "sheet.html").write_text(html)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument(
        "--augment",
        action="store_true",
        help="also check quality=='good' images from families that postdate selection.json, tagged UNSELECTED",
    )
    args = ap.parse_args()
    out_dir = Path(args.out)
    pairs, provenance = build(out_dir, args.augment)
    write_sheet(pairs, provenance, out_dir)
    (out_dir / "situations.json").write_text(
        json.dumps({"provenance": provenance, "pairs": [asdict(p) for p in pairs]}, indent=1)
    )
    n_facade = sum(1 for p in pairs if not p.is_detail)
    print(f"{provenance}")
    print(f"{len(pairs)} pairs written to {out_dir} ({n_facade} facade, {len(pairs) - n_facade} detail)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
