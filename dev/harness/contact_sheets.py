#!/usr/bin/env python3
"""Contact sheets (S10/S11): many generated situations, one grid, one glance.

    "Render generated output alongside them routinely, not once at the end.
    Contact sheets -- twenty seeds in one grid -- are the cheapest way to
    catch the single broken outlier among many."   -- BRIEF.md

This is a VALIDATION harness, not a feature of the generator: it calls
``generate()``, ``plan_block``/``solve_block`` and ``render`` exactly as any
caller would, and draws no building geometry of its own -- every facade on
every sheet below is drawn by the same ``draw_building`` the renderer itself
uses (imported, not reimplemented), so a sheet can never show something the
real renderer would not.

Five sheets, each a specific, falsifiable claim about the system:

  1. seed        -- one situation, 20 seeds.        Claim: no seed breaks it.
  2. width        -- one seed, streets 8->38 m.      Claim: height steps, not ramps.
  3. date         -- one seed/site, 1830->1905.      Claim: two chronologies
                                                       (legality steps at 1884;
                                                       fashion drifts).
  4. class        -- modest->grand, fixed year/width. Claim: the door is
                                                       ABSOLUTE (barely moves)
                                                       while everything else
                                                       is PROPORTIONAL (grows).
  5. block        -- one run of 8-12 parcels.        Claim: it reads as ONE
                                                       WALL, not a shelf of
                                                       separately-finished
                                                       models.

Per the brief, a broken cell must not take the whole sheet down with it: if
``generate()`` (or the block pipeline) raises for one situation, that cell
becomes a visible red error tile carrying the exception, and every other cell
on the sheet still renders. A missing cell is exactly the outlier this harness
exists to catch, so the harness never lets one turn into a silent gap or an
aborted run.

Run:

    python3 dev/harness/contact_sheets.py                  # all five sheets + index
    python3 dev/harness/contact_sheets.py --sheet width     # just one
    python3 dev/harness/contact_sheets.py --list

Output goes to ``dev/logs/sheets/*.svg`` plus ``dev/logs/sheets/index.html``.

Exit 0 = every sheet is well-formed XML (a per-cell failure still counts as a
successful sheet -- it is drawn, on purpose, as a red tile). Exit 1 = a sheet
itself failed to become well-formed SVG, which is a bug in this harness.
"""
from __future__ import annotations

import argparse
import math
import sys
import textwrap
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.block.block import plan_block, solve_block  # noqa: E402
from buildings.ir.nodes import Node  # noqa: E402
from buildings.render.svg import render_block  # noqa: E402
from buildings.render.svg.canvas import Canvas  # noqa: E402
from buildings.render.svg.colors import COLORS  # noqa: E402
from buildings.render.svg.render import building_extent_m, draw_building  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402

SHEETS_DIR = ROOT / "dev" / "logs" / "sheets"

_C = COLORS

# ---------------------------------------------------------------------------
# Layout constants for the custom grid renderer (mirrors
# ``render.svg.contact_sheet`` but with a caption *this harness* controls --
# the situation, not just the building's own width/height -- and a visible
# error tile in place of a cell whose generation raised.)
# ---------------------------------------------------------------------------
_MARGIN_M = 1.2
_GROUND_BAND_M = 0.5
_CELL_GAP_M = 0.5
_CAPTION_LINE_M = 0.40
_MAX_CAPTION_LINES = 3
_ERROR_W_M = 7.0
_ERROR_H_M = 10.0


# ---------------------------------------------------------------------------
# A cell: one situation, resolved (or not) to a building.
# ---------------------------------------------------------------------------


@dataclass
class Cell:
    caption: tuple[str, ...]
    node: Node | None = None
    error: str | None = None


def _find(node: Node, kind: str) -> Node | None:
    if node.kind == kind:
        return node
    for child in node.children:
        found = _find(child, kind)
        if found is not None:
            return found
    return None


def _find_entrance(building: Node) -> Node | None:
    for kind in ("carriage_entrance", "pedestrian_entrance"):
        n = _find_by_opening_type(building, kind)
        if n is not None:
            return n
    return None


def _find_by_opening_type(node: Node, opening_type: str) -> Node | None:
    if node.props.get("opening_type") == opening_type:
        return node
    for child in node.children:
        found = _find_by_opening_type(child, opening_type)
        if found is not None:
            return found
    return None


def _situation(caption_lines: Sequence[str], site: SiteContext, *, extra: Callable[[Node], list[str]] | None = None) -> Cell:
    """Build one ``Cell`` from a situation, never letting a bad situation take
    the sheet down: an exception becomes the cell's ``error`` instead of
    propagating."""
    try:
        building, _log = generate(site)
    except Exception as exc:  # noqa: BLE001 - a broken cell, not a broken sheet
        detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        return Cell(tuple(caption_lines), None, detail)
    lines = list(caption_lines)
    if extra is not None:
        try:
            lines.extend(extra(building))
        except Exception as exc:  # noqa: BLE001 - a caption bug is not a render bug
            lines.append(f"(caption error: {exc})")
    return Cell(tuple(lines), building, None)


# ---------------------------------------------------------------------------
# The custom grid renderer
# ---------------------------------------------------------------------------


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _px_rect(canvas: Canvas, x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_w: float = 0.4) -> None:
    s = stroke or "none"
    canvas.elements.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}" stroke="{s}" stroke-width="{stroke_w}"/>'
    )


def _px_line(canvas: Canvas, x1: float, y1: float, x2: float, y2: float, stroke: str, stroke_w: float = 1.0) -> None:
    canvas.elements.append(
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{stroke_w}"/>'
    )


def _px_text(canvas: Canvas, x: float, y: float, label: str, size: float = 9.5, fill: str = "#4A4038", weight: str = "normal") -> None:
    canvas.elements.append(
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="Helvetica Neue, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="middle">{_esc(label)}</text>'
    )


def render_situations(cells: Sequence[Cell], *, cols: int | None = None, width_px: int = 2200) -> str:
    """Lay ``cells`` into one grid SVG, each drawn at the SAME scale, standing
    on the SAME ground line, in a cell of the SAME size -- so a broken outlier
    reads as a shape that does not match its neighbours, and a failed cell
    reads as an unmissable red tile rather than a gap.

    Every building is drawn by ``draw_building`` -- the function ``render()``
    itself calls -- so this is never a second way of drawing a building, only
    a shared grid and the per-cell caption/error chrome around it.
    """
    n = len(cells)
    if n == 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"/>'

    good = [c for c in cells if c.node is not None]
    extents = [building_extent_m(c.node) for c in good]  # type: ignore[arg-type]
    max_w = max((w for w, _ in extents), default=_ERROR_W_M)
    max_h = max((h for _, h in extents), default=_ERROR_H_M)
    # An error tile reserves at least its own footprint so it reads as a real
    # cell, not a sliver -- but never shrinks the good cells around it either.
    max_w = max(max_w, _ERROR_W_M if any(c.error for c in cells) else 0.0)
    max_h = max(max_h, _ERROR_H_M if any(c.error for c in cells) else 0.0)

    caption_band_m = _CAPTION_LINE_M * _MAX_CAPTION_LINES + 0.18

    cols = cols or max(1, round(math.sqrt(n)))
    rows = math.ceil(n / cols)

    cell_w_m = max_w + 2 * _MARGIN_M
    cell_h_m = max_h + _MARGIN_M + _GROUND_BAND_M + caption_band_m

    sheet_w_m = cols * cell_w_m + (cols + 1) * _CELL_GAP_M
    sheet_h_m = rows * cell_h_m + (rows + 1) * _CELL_GAP_M
    scale = max(1.0, width_px / sheet_w_m)

    sheet_w_px = sheet_w_m * scale
    sheet_h_px = sheet_h_m * scale
    canvas = Canvas(scale=scale)

    _px_rect(canvas, 0, 0, sheet_w_px, sheet_h_px, "#F2EFE8")

    caption_h_px = caption_band_m * scale
    ground_h_px = _GROUND_BAND_M * scale

    for index, cell in enumerate(cells):
        row, col = divmod(index, cols)
        cell_x0_m = _CELL_GAP_M + col * (cell_w_m + _CELL_GAP_M)
        cell_y0_m = _CELL_GAP_M + row * (cell_h_m + _CELL_GAP_M)
        cell_x0_px, cell_y0_px = cell_x0_m * scale, cell_y0_m * scale
        cell_w_px, cell_h_px = cell_w_m * scale, cell_h_m * scale

        border = "#B23B2E" if cell.error else "#B8AE9A"
        sky = "#FBE0DC" if cell.error else _C["sky"]
        _px_rect(canvas, cell_x0_px, cell_y0_px, cell_w_px, cell_h_px, "#FFFFFF", border, 1.1 if cell.error else 0.6)
        _px_rect(canvas, cell_x0_px, cell_y0_px + caption_h_px, cell_w_px, cell_h_px - caption_h_px - ground_h_px, sky)
        _px_rect(canvas, cell_x0_px, cell_y0_px + cell_h_px - ground_h_px, cell_w_px, ground_h_px, _C["ground"])

        for li, line in enumerate(cell.caption[:_MAX_CAPTION_LINES]):
            _px_text(
                canvas,
                cell_x0_px + cell_w_px / 2.0,
                cell_y0_px + (li + 0.9) * (caption_h_px / _MAX_CAPTION_LINES),
                line,
                size=9.3 if li == 0 else 8.2,
                fill="#2E2A24" if li == 0 else "#5A5248",
                weight="bold" if li == 0 else "normal",
            )

        pavement_y_m = cell_y0_m + cell_h_m - _GROUND_BAND_M
        canvas.x_origin = (cell_x0_m + _MARGIN_M) * scale
        canvas.y_origin = pavement_y_m * scale

        if cell.error is not None:
            _draw_error_tile(canvas, max_w, max_h, cell.error)
        else:
            draw_building(canvas, cell.node, False)  # type: ignore[arg-type]

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w_px:.2f}" '
        f'height="{sheet_h_px:.2f}" viewBox="0 0 {sheet_w_px:.2f} {sheet_h_px:.2f}">\n'
        f'<style>text {{ font-family: "Helvetica Neue", Arial, sans-serif; }}</style>\n'
    )
    svg += "\n".join(canvas.elements)
    svg += "\n</svg>"
    return svg


def _draw_error_tile(canvas: Canvas, w_m: float, h_m: float, message: str) -> None:
    """A visible, unmissable failure -- per the brief, a missing cell IS the
    outlier this harness exists to catch, so a raised exception must never
    silently drop a cell or abort the whole sheet."""
    canvas.rect(0.0, 0.0, w_m, h_m, "#FBE0DC", stroke="#B23B2E", stroke_w=0.10)
    canvas.line(0.0, 0.0, w_m, h_m, "#B23B2E", 0.10)
    canvas.line(0.0, h_m, w_m, 0.0, "#B23B2E", 0.10)
    canvas.text(w_m / 2.0, h_m * 0.62, "RENDER FAILED", size=15, fill="#8A2418")
    wrapped = textwrap.wrap(message.replace("\n", " "), width=30)[:8]
    for i, line in enumerate(wrapped):
        canvas.text(w_m / 2.0, h_m * 0.62 - 0.62 * (i + 1), line, size=9, fill="#8A2418")


def _write_svg(svg: str, path: Path) -> str | None:
    """Validate well-formedness and write. Returns an error string, or None."""
    try:
        ET.fromstring(svg)
    except ET.ParseError as exc:
        return f"not well-formed XML: {exc}"
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# Chronology captions -- read straight off the IR the running text names:
# ironwork pattern, socle treatment, keystone kind, roof envelope. Nothing
# here decides anything; it only prints what qualification already resolved.
# ---------------------------------------------------------------------------


def _chronology_caption(building: Node) -> list[str]:
    socle = _find(building, "socle")
    iron = _find(building, "ironwork")
    keystone = _find(building, "keystone")
    roof = _find(building, "roof")
    socle_v = socle.props.get("treatment") if socle is not None else "-"
    iron_v = iron.props.get("ironwork_pattern") if iron is not None else "-"
    key_v = keystone.props.get("keystone_kind") if keystone is not None else "-"
    roof_v = roof.props.get("envelope") if roof is not None else "-"
    return [
        f"roof: {roof_v}",
        f"socle:{socle_v}  iron:{iron_v}  ks:{key_v}",
    ]


def _door_caption(building: Node) -> list[str]:
    ent = _find_entrance(building)
    if ent is None:
        return ["no entrance found!"]
    kind = "carriage" if ent.props.get("opening_type") == "carriage_entrance" else "pedestrian"
    return [f"door {_num(ent,'w'):.2f}x{_num(ent,'h'):.2f}m ({kind})"]


def _num(n: Node, key: str) -> float:
    v = n.props.get(key)
    return float(v) if v is not None else 0.0


def _dims_caption(building: Node) -> list[str]:
    return [f"{_num(building,'w'):.2f} x {_num(building,'h'):.2f} m"]


# ---------------------------------------------------------------------------
# The canonical situation every sweep below holds fixed except the one axis
# it is testing: a mid-block immeuble on an 18 m street, comfortable, shop
# below -- wide enough to earn a carriage entrance, narrow enough to be an
# ordinary Paris lot rather than a boulevard showpiece.
# ---------------------------------------------------------------------------
BASE = dict(
    street_width=18.0,
    parcel_width=13.0,
    parcel_depth=18.0,
    year=1870,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
    corner=False,
    seed=42,
)


def _site(**kw) -> SiteContext:
    fields = dict(BASE)
    fields.update(kw)
    return SiteContext(**fields)


# ---------------------------------------------------------------------------
# 1. Seed sweep
# ---------------------------------------------------------------------------

SEED_SWEEP_YEAR = 1875
N_SEEDS = 20


# ---------------------------------------------------------------------------
# 2. Street-width sweep -- the règlement's own breakpoints (7.80 m, 9.75 m,
# 20.00 m), each straddled closely enough that the jump is unmistakable, plus
# the requested 8->38 m span. Held at one fixed post-1884 year so the only
# thing moving is street width, not the regulatory era too.
# ---------------------------------------------------------------------------

WIDTH_SWEEP_YEAR = 1890
STREET_WIDTHS = (8.0, 9.0, 9.75, 9.8, 10.0, 12.0, 14.0, 16.0, 18.0, 19.75, 20.0, 20.25, 22.0, 26.0, 30.0, 34.0, 38.0)


# ---------------------------------------------------------------------------
# 3. Date sweep -- one seed, one site, 1830->1905 at 5-year steps. The
# roofline must visibly change shape at 1884/85 (the Alphand decree switches
# the envelope from a 45 degree diagonal to a circular arc); ironwork, socle
# and keystone turn over gradually, which is the whole point of attaching
# dates to variants rather than to buildings.
# ---------------------------------------------------------------------------

YEARS = tuple(range(1830, 1906, 5))


# ---------------------------------------------------------------------------
# 4. Class sweep -- modest -> grand, fixed year and width. The claim: the
# entrance is ABSOLUTE (identical within its kind across every class that uses
# it) while bays, windows and cornice are PROPORTIONAL and visibly grow. Two
# rows, two different years, so the lagging-fashion case (comfortable/grand
# reach a variant before modest/ordinary do) reads as the difference between
# the rows as well.
# ---------------------------------------------------------------------------

CLASS_SWEEP_YEARS = (1870, 1895)
CLASS_SWEEP_WIDTH = 18.0


# ---------------------------------------------------------------------------
# 5. A block -- 8-12 buildings in a run, including one chamfered corner, all
# solved and rendered through the SAME block pipeline and the SAME
# ``render_block`` a real caller would use. Unlike the four sweeps above this
# is not a grid of independent situations, so it is not built from ``Cell``;
# a failure here still cannot be allowed to raise past this function, so the
# whole pipeline is wrapped and a full-width error tile substitutes for the
# block if it breaks.
# ---------------------------------------------------------------------------

BLOCK_FRONTAGE = 110.0
BLOCK_STREET_WIDTH = 18.0
BLOCK_YEAR = 1870
BLOCK_KLASS = BuildingClass.ORDINARY
BLOCK_SEED = 5


def build_block_sheet() -> tuple[str, str]:
    """Returns ``(svg, situation_caption)``."""
    caption = (
        f"{BLOCK_FRONTAGE:g} m frontage, {BLOCK_STREET_WIDTH:g} m street, {BLOCK_YEAR}, "
        f"{BLOCK_KLASS.value}, seed {BLOCK_SEED}, one chamfered corner"
    )
    try:
        block = plan_block(
            BLOCK_FRONTAGE,
            BLOCK_STREET_WIDTH,
            BLOCK_YEAR,
            klass=BLOCK_KLASS,
            seed=BLOCK_SEED,
            corner_left=True,
        )
        n_parcels = len(block.parcels)
        nodes = solve_block(block, BLOCK_YEAR, klass=BLOCK_KLASS, seed=BLOCK_SEED)
        svg = render_block(list(nodes), width_px=2600)
        caption += f" -- {n_parcels} parcels"
    except Exception as exc:  # noqa: BLE001 - a broken block is still a drawable tile
        detail = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        canvas = Canvas(scale=1.0)
        w_px, h_px = 1400, 700
        canvas.elements.append(f'<rect x="0" y="0" width="{w_px}" height="{h_px}" fill="#FBE0DC" stroke="#B23B2E" stroke-width="3"/>')
        canvas.elements.append(f'<text x="{w_px/2}" y="{h_px/2 - 10}" font-size="22" fill="#8A2418" text-anchor="middle">BLOCK RENDER FAILED</text>')
        for i, line in enumerate(textwrap.wrap(detail.replace("\n", " "), width=90)[:10]):
            canvas.elements.append(f'<text x="{w_px/2}" y="{h_px/2 + 20 + 18*i}" font-size="13" fill="#8A2418" text-anchor="middle">{_esc(line)}</text>')
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px}" height="{h_px}" viewBox="0 0 {w_px} {h_px}">\n'
            + "\n".join(canvas.elements)
            + "\n</svg>"
        )
    return svg, caption


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

_SHEET_META: dict[str, dict[str, str]] = {
    "seed": dict(
        title="1. Seed sweep",
        filename="seed_sweep.svg",
        situation=f"street {BASE['street_width']:g} m, parcel {BASE['parcel_width']:g}x{BASE['parcel_depth']:g} m, "
        f"{SEED_SWEEP_YEAR}, {BASE['klass'].value}, {BASE['ground'].value} -- seeds 0..{N_SEEDS - 1}",
        looking_for=(
            "Every building should read as an ordinary variation on the same theme: same street, "
            "same envelope, same class. Look for the ONE building that stands out -- a facade with "
            "no bays, a storey stack a module too tall, a roofline that broke its envelope, ironwork "
            "or a socle wildly out of family with its neighbours. That single outlier is exactly what "
            "this sheet exists to catch; nothing here should surprise you twice."
        ),
    ),
    "width": dict(
        title="2. Street-width sweep",
        filename="street_width_sweep.svg",
        situation=f"seed {BASE['seed']}, {WIDTH_SWEEP_YEAR}, {BASE['klass'].value}, {BASE['ground'].value} -- "
        f"street width {STREET_WIDTHS[0]:g}→{STREET_WIDTHS[-1]:g} m",
        looking_for=(
            "The height must move in STEPS, not a ramp: several widths in a row give the SAME height, "
            "then it jumps. The règlement's own breakpoints (7.80 m, 9.75 m, 20.00 m) are straddled "
            "closely on this sheet -- 9.75 vs 9.80, 20.00 vs 20.25 -- so the jump should land exactly "
            "between one pair of adjacent cells and nowhere else. A height that creeps up gradually "
            "instead of jumping is the regulatory table being fitted rather than looked up."
        ),
    ),
    "date": dict(
        title="3. Date sweep",
        filename="date_sweep.svg",
        situation=f"seed {BASE['seed']}, street {BASE['street_width']:g} m, parcel {BASE['parcel_width']:g}x{BASE['parcel_depth']:g} m, "
        f"{BASE['klass'].value}, {BASE['ground'].value} -- {YEARS[0]}→{YEARS[-1]} at 5-year steps",
        looking_for=(
            "This is the visual proof of the two-chronologies design. The ROOFLINE must visibly change "
            "SHAPE right at 1884/85 -- a 45° diagonal comble before, a circular-arc comble after -- "
            "because that is a decree, a step function. Everything else (the socle's rustication, the "
            "ironwork pattern, the keystone) should turn over GRADUALLY across the sheet, often at a "
            "different pace and on different years than the roof and than each other, because those are "
            "fashion, not law. If the roof drifts instead of jumping, or the ironwork jumps in lockstep "
            "with the roof, the two chronologies have collapsed into one."
        ),
    ),
    "class": dict(
        title="4. Class sweep",
        filename="class_sweep.svg",
        situation=f"street {CLASS_SWEEP_WIDTH:g} m, seed {BASE['seed']}, {BASE['ground'].value} -- modest→grand at "
        f"{CLASS_SWEEP_YEARS[0]} and again at {CLASS_SWEEP_YEARS[1]}",
        looking_for=(
            "This is the sheet most worth studying closely: the absolute/proportional split made "
            "visible. Read the printed door dimensions left to right along each row -- they should "
            "barely move (identical within an entrance kind: modest/ordinary share one pedestrian-door "
            "size, comfortable/grand share one carriage-arch size), because a door is sized to a body "
            "and a carriage, not to ambition. Meanwhile the bays, window sizes and cornice should grow "
            "visibly richer toward 'grand'. A door that grows with the building has silently become "
            "PROPORTIONAL, which is the exact failure Amendment 1 named."
        ),
    ),
}


def build_index_html(results: dict[str, dict]) -> str:
    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="en"><head><meta charset="utf-8">')
    parts.append("<title>Contact sheets</title>")
    parts.append(
        "<style>"
        "body{font-family:'Helvetica Neue',Arial,sans-serif;max-width:1500px;margin:0 auto;"
        "padding:2rem;background:#faf8f4;color:#2e2a24;}"
        "h1{font-size:1.8rem;margin-bottom:0.2rem;}"
        "h2{margin-top:3rem;border-top:2px solid #b8ae9a;padding-top:1.2rem;}"
        ".situation{font-family:ui-monospace,Menlo,monospace;font-size:0.85rem;color:#5a5248;"
        "background:#f2efe8;padding:0.4rem 0.7rem;border-radius:4px;display:inline-block;margin:0.3rem 0;}"
        ".looking-for{background:#fff;border-left:4px solid #6b8f5a;padding:0.8rem 1.2rem;margin:0.8rem 0;"
        "border-radius:0 4px 4px 0;}"
        ".status{font-weight:bold;}"
        ".status.ok{color:#3a6b3a;}"
        ".status.fail{color:#b23b2e;}"
        "img{max-width:100%;border:1px solid #b8ae9a;border-radius:4px;background:#fff;}"
        ".meta{color:#8a8378;font-size:0.85rem;}"
        "</style>"
    )
    parts.append("</head><body>")
    parts.append("<h1>Contact sheets</h1>")
    parts.append(
        "<p>Twenty seeds in one grid is the cheapest way to catch the single broken outlier among "
        "many (BRIEF.md). Every building on every sheet below is generated by the real "
        "<code>generate()</code> pipeline and drawn by the real renderer's own "
        "<code>draw_building</code> -- nothing here is a mock. A cell shown in red is a situation "
        "whose generation raised an exception; the exception text is printed in the tile itself "
        "rather than the cell silently vanishing.</p>"
    )
    parts.append(
        "<div class='looking-for' style='border-left-color:#b23b2e;'>"
        "<strong>Caught while building this harness -- the porte piétonne renders as a plain "
        "window.</strong> <code>elements.draw_opening</code> special-cases "
        "<code>opening_type == \"carriage_entrance\"</code> (a solid brown double door) but has no "
        "branch for <code>\"pedestrian_entrance\"</code>, so it falls through to the generic window "
        "path -- same blue glass fill, same cross-mullion, same frame. The IR is not at fault: "
        "<code>catalogue.entrance_for</code> correctly places exactly one <code>porte_piétonne</code> "
        "slot on every building that does not earn a carriage arch (any class on a street under 12 m, "
        "and modest/ordinary on any street), and the node carries "
        "<code>opening_type='pedestrian_entrance'</code> with its own ABSOLUTE 1.40&times;2.90 m "
        "rectangle -- the renderer simply discards that fact, the same offence A4.1/A6.8/A7.3 already "
        "named twice. Since the porte piétonne is, per the catalogue's own docstring, "
        "“the commoner Paris entrance” (most of the city's immeubles have one, not a carriage "
        "arch), this silently reproduces Amendment 6.1 (“There is no door. Anywhere.”) for every "
        "modest and ordinary building, and for any class on a narrow street. "
        "See the <strong>street-width sweep</strong> (w=8&ndash;10 m: three shop-like glass openings, "
        "no door), the <strong>class sweep</strong> (modest/ordinary columns: the labelled "
        "1.40&times;2.90 m door is indistinguishable from the window beside it) and the "
        "<strong>block</strong> below (9 ordinary parcels, one continuous run of glass at ground level "
        "-- not one visible door along the whole wall). Fix belongs in "
        "<code>render/svg/elements.py::draw_opening</code>, not in this harness or in qualification.</div>"
    )

    for key in ("seed", "width", "date", "class"):
        meta = _SHEET_META[key]
        res = results[key]
        parts.append(f"<h2>{meta['title']}</h2>")
        parts.append(f"<div class='situation'>{meta['situation']}</div>")
        parts.append(f"<div class='looking-for'><strong>What to look for:</strong> {meta['looking_for']}</div>")
        if res["ok"]:
            parts.append(f"<p class='meta'>{res['n_error']} of {res['n_cells']} cells failed to generate.</p>")
            parts.append(f"<img src='{meta['filename']}' alt='{meta['title']}'>")
        else:
            parts.append(f"<p class='status fail'>SHEET FAILED TO RENDER: {res['error']}</p>")

    parts.append("<h2>5. A block</h2>")
    block_res = results["block"]
    parts.append(f"<div class='situation'>{block_res['situation']}</div>")
    parts.append(
        "<div class='looking-for'><strong>What to look for:</strong> This must read as ONE WALL -- "
        "a continuous cornice line, continuous string courses and balcony lines running across every "
        "party wall without a seam, and the chamfered corner at the left end sitting in as a third "
        "short facade with its own roof and rhythm, not a gap or a blank stub. If you can pick out "
        "where one building ends and the next begins by anything other than the party-wall hairline, "
        "the block has failed at the one thing it exists for.</div>"
    )
    if block_res["ok"]:
        parts.append(f"<img src='{block_res['filename']}' alt='Block'>")
    else:
        parts.append(f"<p class='status fail'>BLOCK FAILED TO RENDER: {block_res['error']}</p>")

    parts.append(
        "<p class='meta' style='margin-top:3rem;'>Generated by "
        "<code>dev/harness/contact_sheets.py</code>. Two limits apply to all five sheets, per PLAN.md "
        "S11: this is a qualitative tripwire, not a passing grade -- “looks wrong” is strong "
        "evidence, “looks right” is weak, and a systematic few-percent error belongs to the "
        "assertion suite, not to this page.</p>"
    )
    parts.append("</body></html>")
    return "\n".join(parts)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", default="all", choices=sorted(list(_CELL_BUILDERS) + ["block", "all"]))
    ap.add_argument("--list", action="store_true", help="list the sheets and exit")
    args = ap.parse_args(argv)

    if args.list:
        for name in list(_CELL_BUILDERS) + ["block"]:
            print(name)
        return 0

    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    to_build = list(_CELL_BUILDERS) if args.sheet in ("all",) else ([args.sheet] if args.sheet != "block" else [])
    build_block = args.sheet in ("all", "block")

    results: dict[str, dict] = {}
    overall_ok = True

    for name in to_build:
        print(f"building sheet: {name}")
        # Re-derive the cell count/error count by rebuilding through the same
        # public entry points main() exposes, so what is reported matches
        # exactly what got drawn.
        cells = _CELL_BUILDERS[name]()
        svg = render_situations(cells, cols=_SHEET_COLS[name])
        meta = _SHEET_META[name]
        out_path = SHEETS_DIR / meta["filename"]
        err = _write_svg(svg, out_path)
        n_error = sum(1 for c in cells if c.error)
        if err:
            overall_ok = False
            results[name] = dict(ok=False, error=err)
            print(f"  FAIL: {err}")
        else:
            results[name] = dict(ok=True, n_error=n_error, n_cells=len(cells), filename=meta["filename"])
            print(f"  {out_path}  ({len(svg):,} bytes, {n_error}/{len(cells)} cells failed)")

    if build_block:
        print("building sheet: block")
        svg, caption = build_block_sheet()
        out_path = SHEETS_DIR / "block_wall.svg"
        err = _write_svg(svg, out_path)
        if err:
            overall_ok = False
            results["block"] = dict(ok=False, error=err, situation=caption)
            print(f"  FAIL: {err}")
        else:
            results["block"] = dict(ok=True, filename="block_wall.svg", situation=caption)
            print(f"  {out_path}  ({len(svg):,} bytes)")

    if args.sheet == "all":
        index_html = build_index_html(results)
        index_path = SHEETS_DIR / "index.html"
        index_path.write_text(index_html, encoding="utf-8")
        print(f"\nindex -> {index_path}")

    return 0 if overall_ok else 1


# Each sweep as a list of ``Cell`` -- one function per sheet, so ``main`` can
# report exactly how many situations failed to generate without re-deriving
# anything the sweep already decided.
def _seed_cells() -> list[Cell]:
    return [
        _situation([f"seed {seed}"], _site(year=SEED_SWEEP_YEAR, seed=seed), extra=_dims_caption)
        for seed in range(N_SEEDS)
    ]


def _width_cells() -> list[Cell]:
    return [
        _situation([f"w = {w:g} m"], _site(street_width=w, year=WIDTH_SWEEP_YEAR), extra=_dims_caption)
        for w in STREET_WIDTHS
    ]


def _date_cells() -> list[Cell]:
    return [_situation([str(y)], _site(year=y), extra=_chronology_caption) for y in YEARS]


def _class_cells() -> list[Cell]:
    out = []
    for year in CLASS_SWEEP_YEARS:
        for klass in BuildingClass:
            site = _site(year=year, street_width=CLASS_SWEEP_WIDTH, klass=klass)
            out.append(
                _situation(
                    [f"{klass.value} / {year}"],
                    site,
                    extra=lambda b: _door_caption(b) + _dims_caption(b),
                )
            )
    return out


_CELL_BUILDERS: dict[str, Callable[[], list[Cell]]] = {
    "seed": _seed_cells,
    "width": _width_cells,
    "date": _date_cells,
    "class": _class_cells,
}

_SHEET_COLS: dict[str, int] = {"seed": 5, "width": 6, "date": 8, "class": 4}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
