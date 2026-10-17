#!/usr/bin/env python3
"""Named canonical Second Empire situations — the layouts, in one place.

A *layout* here is not a building. It is a **situation**: the handful of facts
the generator needs, from which the building follows. Nothing in this file
chooses a storey count, a roof angle or an ornament level; those are consequences.

Each preset records why it is shaped as it is, and — where one exists — the real
building from César Daly's 1864 plates that it answers to. See
`dev/reference/SOURCES.md`.

    python3 dev/harness/layouts.py            # list them, with the stack each gives
    python3 dev/harness/layouts.py A --svg    # render one
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(ROOT / "src"))

from buildings.site import SiteContext, BuildingClass, GroundProgramme  # noqa: E402


@dataclass(frozen=True)
class Layout:
    key: str
    title: str
    site: SiteContext
    expect: str
    why: str
    daly: str = ""


LAYOUTS: dict[str, Layout] = {
    "A": Layout(
        key="A",
        title="Commercial boulevard — the maximal stack",
        site=SiteContext(
            street_width=22.0, parcel_width=14.0, parcel_depth=11.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=8,
        ),
        expect="RdC + entresol + 4 étages + comble",
        why=(
            "A street over 20 m lets the 1859 règlement grant the full 20 m of "
            "facade, and a shop ground floor buys an entresol. Four étages is "
            "then what fits underneath the ceiling — not a choice. This is the "
            "densest lawful Second Empire stack, and the commonest on the percées."
            "\n\nThe 11 m parcel is part of the situation and not a detail "
            "(A16.1). On a wide commercial street the one thing that can take "
            "height out of this stack is the garret trade — a second storey of "
            "chambres de bonne bought out of the cornice — and it is only on "
            "offer where the plot would actually hold the band, which at 1865 "
            "takes about 12.20 m of depth before the two 45 degree slopes meet. "
            "A shallower lot is never offered it, so the height stays in the "
            "stone and the facade fills its ceiling. C1 is the same street with "
            "a deep lot, and it is a visibly different building."
        ),
        daly=(
            "63 / 77 / 120 bd de Sébastopol, 39 rue Neuve des Mathurins, "
            "6 bd Saint-Germain — all five carry exactly this stack, with "
            "cornices between 19.05 and 19.98 m against the 20 m limit."
        ),
    ),
    "AC": Layout(
        key="AC",
        title="Commercial boulevard — two-storey carriage arch",
        site=SiteContext(
            street_width=22.0, parcel_width=14.0, parcel_depth=11.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=5,
        ),
        expect=(
            "A's stack exactly, with the porte cochère rising through the "
            "entresol as one round arch"
        ),
        why=(
            "The same situation as A in every fact the generator reads — same "
            "street, same parcel, same date, same class, same ground programme, "
            "so the same stack to the millimetre. The only difference is the "
            "seed, and therefore the draw on "
            "'facade/entrance/arch_form' (A14.2). That is the "
            "whole claim: the two-storey arch is not a consequence of the date, "
            "the class or the street — all four of Daly's are 1864, two are "
            "Première and two Deuxième — it is "
            "variation within a class and a period, and the pair A / AC is what "
            "makes that visible. The arch is 2.60 m wide in both, unchanged; "
            "only its height moves."
        ),
        daly=(
            "39 rue Neuve des Mathurins — porte cochère 2.57 x 5.00 m over a "
            "4.10 m rez-de-chaussée and a 2.40 m entresol, and one of the five "
            "canonical-stack buildings (cornice 19.82 m). So the tall arch does "
            "not replace the entresol stack, it rises through it. See also "
            "Avenue de l'Impératrice (Raban), 2.62 x 7.30 m, the tallest arch "
            "in the corpus — dev/reference/images/daly-1864/"
            "daly_elevation_25_avenue-imperatrice.jpg. That plate carries no "
            "measured entresol; the reading that it had one 'absorbed' into "
            "the base was retracted by A17.2."
        ),
    ),
    "AP": Layout(
        key="AP",
        title="Narrow parcel — two-storey pedestrian arch",
        site=SiteContext(
            street_width=11.0, parcel_width=9.0, parcel_depth=15.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=5,
        ),
        expect="RdC + entresol + 3 étages + comble, porte piétonne rising through the entresol",
        why=(
            "An 11 m street is under the 12 m a carriage needs to draw out of "
            "the traffic and turn in, so this frontage takes a porte piétonne "
            "however comfortable the household is (catalogue.entrance_for). A "
            "shop below still buys the entresol, so there is a base block for "
            "the arch to rise through — and Daly shows the tall arch on "
            "pedestrian doors too, though less often than on carriage ones: 2 "
            "of 10 against 2 of 7, and 1 of 7 against 1 of 2 among the "
            "frontages that have an entresol for it to rise through at all "
            "(A18). Rarer is not absent, which is why this preset exists. The parcel is "
            "9 m against A's 14, which is the point: the arch is 1.75 m wide "
            "here and 2.60 m at AC, and neither figure moved a centimetre when "
            "the arch grew to two storeys."
        ),
        daly=(
            "2 et 4 bd de Sébastopol (Davioud) — porte piétonne 1.74 x 5.01 m "
            "over a 3.42 m rez-de-chaussée and a 2.65 m entresol; and 87 bd de "
            "Sébastopol, 1.76 x 5.07 m. Against a one-storey pedestrian median "
            "of 3.03 m. See dev/reference/images/daly-1864/"
            "daly_elevation_02_blvd-sebastopol-2-4.jpg."
        ),
    ),
    "P": Layout(
        key="P",
        title="Post-1884 commercial corner — the dated anchor",
        site=SiteContext(
            street_width=20.0, parcel_width=15.0, parcel_depth=17.0, year=1887,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
            corner=True, seed=1887,
        ),
        expect="R+5 over commerce, corner with a pan coupé, ARC comble",
        why=(
            "1887 is three years after the Alphand decree of 23 July 1884, so the "
            "comble is inscribed in a circular arc rather than the 45 degree plane "
            "that governs every Daly plate. The building still obeys everything the "
            "1859 reglement asked; only the roof rule changed. It reads as a classic "
            "haussmannien corner to almost any eye, which is exactly why the "
            "chronology is modelled as date windows rather than a period enum: an "
            "enum would file this under Third Republic and lose that."
        ),
        daly=(
            "OUTSIDE the Daly corpus, deliberately. Anchored instead to "
            "31 rue de la Chaussee d'Antin / 71 rue de Provence, architect Alfred "
            "Leroux: permit 13 Feb 1886 (Bulletin municipal officiel), completion "
            "estimated c.1888, and 1887 carved on the escutcheon. R+5, ~20 m, "
            "421 m2, commerce below and housing above. See dev/reference/SOURCES.md "
            "section 6. The carved date is the operator's reading from the street; "
            "the only located photograph is a 340px thumbnail, too small to confirm "
            "the roofline."
        ),
    ),
    # ---- the 1884 hinge: one situation, two sides of a decree -----------
    # A matched PAIR, and the only thing that differs between them is the
    # year. Same street, same parcel, same class, same programme, same seed —
    # so every draw on `DecisionStream` lands the same way and anything that
    # moves, moved because the law moved. Mid-block on purpose: a corner adds
    # a pan coupe and a hipped roof, and the point here is the roof RULE, not
    # the roof's plan.
    "H83": Layout(
        key="H83",
        title="Before the 1884 decree — the 45 degree comble",
        site=SiteContext(
            street_width=20.0, parcel_width=15.0, parcel_depth=17.0, year=1883,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
            corner=False, seed=1884,
        ),
        expect="6 storeys, cornice 16.85 m, a 3.20 m comble inscribed in the 45 degree plane",
        why=(
            "The 1859 reglement still governs: a 20 m street earns a 17.55 m "
            "cornice, and over it the comble is inscribed in a plane at 45 "
            "degrees, which on this frontage is 3.20 m of ridge and room for "
            "ONE garret storey. Nothing about this building is chosen — it is "
            "what the two rules leave once a shop has bought its entresol."
        ),
        daly=(
            "Inside the Daly window in rule though not in date: this is the "
            "same envelope every 1864 plate obeys, which is why the pair works "
            "as a control. Compare H87, the same situation three years later."
        ),
    ),
    "H87": Layout(
        key="H87",
        title="After the 1884 decree — Alphand's circular arc",
        site=SiteContext(
            street_width=20.0, parcel_width=15.0, parcel_depth=17.0, year=1887,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
            corner=False, seed=1884,
        ),
        expect="7 storeys, cornice 17.28 m, a 7.04 m comble inscribed in a circular arc",
        why=(
            "H83's situation, moved past the Decret du 23 juillet 1884. Two "
            "things change and both are the decree's: the cornice a 20 m "
            "street earns goes from 17.55 to 18.00 m, and the comble is "
            "inscribed in a CIRCULAR ARC instead of a 45 degree plane, which "
            "on this frontage allows 7.65 m of roof where the plane allowed "
            "3.20. The building takes 7.04 of it and puts a SECOND garret "
            "storey up there.\n\n"
            "So the stone rises 0.43 m and the roof rises 3.84 m, and the "
            "whole building goes from 20.05 to 24.32 m — on the same street, "
            "the same parcel, the same purse and the same seed. This is the "
            "brief's own test: move the date past a decree and the roofline "
            "changes shape."
        ),
        daly=(
            "OUTSIDE the Daly corpus by construction — the corpus is 1864 and "
            "this is the point of it being outside. P is the other post-1884 "
            "preset, on a corner and anchored to a real address; this one is "
            "deliberately anchored to nothing but H83."
        ),
    ),

    # ---- the commercial varieties (dev/LAYOUTS_COMMERCIAL.md) ----------
    # Defined as SITUATIONS, not as fits to a target. The facade/roof split
    # that separates them is a consequence of street width and parcel depth,
    # which is the point.
    "C1": Layout(
        key="C1",
        title="Commercial — comble-heavy, height in the roof",
        site=SiteContext(
            street_width=22.0, parcel_width=11.0, parcel_depth=16.0, year=1865,
            klass=BuildingClass.GRAND, ground=GroundProgramme.SHOP, seed=3,
        ),
        expect="3 etages under a deep TWO-storey garret, two rows of openings in it",
        why=(
            "Two conditions have to hold together and both are structural. The "
            "street must clear the 14.81 m of stone a bought garret has to stand "
            "on, which on the 1859 tables only the 20 m step does; and the parcel "
            "must be deep enough to hold two garret bands before the 45 degree "
            "slopes meet, which is 12.20 m. Given both, a shop ground floor takes "
            "letting storeys out of the stone face and the dwellings come back "
            "under the roof. The facade stops short of its ceiling and the height "
            "goes into the comble."
        ),
        daly=(
            "2 et 4 bd de Sebastopol (Davioud): cornice 17.52, comble 7.00, "
            "total 24.52 — the tallest building in the corpus, reached by building "
            "the facade LOWER. Also 1 bd de Sebastopol (17.55 / 6.80). "
            "Ours reaches comble 6.10 against 7.00: a residual of -0.90 m, the "
            "cap being decree ridge 3.20 + one brisis rise 2.90.\n\n"
            "A19: both plates carry TWO rows of openings in the comble, which is "
            "what this preset is for and is corpus-attested. Neither, however, "
            "shows what we draw. At 2 et 4 the brisis is a BRICK WALL: a full "
            "storey of moulded window surrounds with individual balconettes, and "
            "above it a row of small plain lights under the eaves — no dormer "
            "projects anywhere on that plate. At 1 bd the brisis is faced in "
            "vertical-seamed metal, and only the UPPER row is a true lucarne "
            "(round-arched, scrolled consoles); the lower row is again windows "
            "set in the brisis face, each with its own balconette. We draw both "
            "rows as pedimented dormers, so the lower row is wrong on both "
            "anchors. See dev/reference/images/daly-1864/"
            "daly_elevation_02_blvd-sebastopol-2-4.jpg and "
            "dev/reference/images/daly-1864/"
            "daly_elevation_73_sebastopol-1-deuxieme-classe.jpg."
        ),
    ),
    "C2": Layout(
        key="C2",
        title="Commercial — the middle strategy (NOT REACHABLE)",
        site=SiteContext(
            street_width=20.0, parcel_width=13.0, parcel_depth=13.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=7,
        ),
        expect="UNREACHABLE — a comble around 4.7 m falls in the gap",
        why=(
            "Kept deliberately as a FAILING case rather than deleted. The comble "
            "is either one garret band or two, so the reachable set is roughly "
            "[2.0, 3.2] and [5.9, 6.1] with nothing between. A 4.72 m comble sits "
            "in that gap. Whether the gap is wrong is genuinely open: Daly's two "
            "independent readings of this building disagree (4.32 vs 5.12), so the "
            "target is inside the corpus's own error bar. Left here so the gap "
            "stays visible instead of being quietly rounded to a neighbour."
        ),
        daly="26 rue Bergere: cornice 18.74, comble 4.72, total 23.46, one-storey porte cochere.",
    ),
    "C3": Layout(
        key="C3",
        title="Commercial — the small end",
        site=SiteContext(
            street_width=14.0, parcel_width=11.0, parcel_depth=10.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=5,
        ),
        expect="3 etages, low cornice, shallow comble, the shortest commercial",
        why=(
            "A 14 m street never reaches the 20 m step, so the ceiling binds low "
            "and the 14.81 m stone bar is never cleared — no bought garret is "
            "possible here whatever the programme wants. The shallow parcel would "
            "refuse it anyway. This is the case where the envelope, not ambition, "
            "decides how big the building is."
        ),
        daly="9 rue du Conservatoire: cornice 18.15, comble 2.85, total 21.00 — the shortest commercial building in the corpus.",
    ),
    "C4": Layout(
        key="C4",
        title="Commercial — facade to the ceiling",
        site=SiteContext(
            street_width=22.0, parcel_width=15.0, parcel_depth=11.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=3,
        ),
        expect="4 etages pressed to the cornice limit, ONE-storey garret",
        why=(
            "The mirror of C1 and the commonest case, 4 of the 9 commercial "
            "buildings. Same 22 m street, so the same 20 m ceiling and the same "
            "stone bar cleared — but the parcel is too shallow at 11 m to hold a "
            "second garret band, so the trade is not on offer and the height stays "
            "in the facade. Depth, not money, is what separates this from C1."
        ),
        daly="39 rue Neuve des Mathurins: cornice 19.82, comble 3.18, 4 etages, two-storey porte cochere 2.57 x 5.00. Also 120 / 63 / 77 bd de Sebastopol and 6 bd Saint-Germain.",
    ),
    "O": Layout(
        key="O",
        title="Ordinary — Daly's Troisieme Classe, no shop and no entresol",
        site=SiteContext(
            street_width=14.0, parcel_width=12.0, parcel_depth=13.0, year=1865,
            klass=BuildingClass.ORDINARY, ground=GroundProgramme.RESIDENTIAL, seed=6,
        ),
        expect="RdC + 5 levels, NO entresol, porte pietonne in the rhythm, 6 axes",
        why=(
            "The first preset that is not a commercial building, and it is here "
            "because the other ten were all COMFORTABLE or GRAND — the two "
            "poorest classes had no canonical case at all, which is how the "
            "squat-window problem stayed off the contact sheet for so long.\n\n"
            "Two things make it Troisieme rather than a cheap Deuxieme. There is "
            "no shop, so no entresol is bought and the base is one storey; and "
            "the door is a porte pietonne, which since A27 takes an ordinary "
            "2.625 m slot in the rhythm instead of displacing it. Both are what "
            "the corpus shows at this class.\n\n"
            "Note the street stops mattering here. Above about 10 m the cornice "
            "plateaus at 14.92 m because the STOREY STACK binds before the 1859 "
            "step table does — an ordinary building does not have the storey "
            "heights to reach its own legal ceiling. That is the opposite of C3, "
            "where the envelope decides, and it is worth having one preset of "
            "each."
        ),
        daly=(
            "Troisieme Classe, both of it: 36/38/40 bd Beaumarchais (Rolland) — "
            "8.57 m per house, pitch 2.69, cornice 15.93, porte pietonne 1.36, "
            "aspect_principal 1.96 — and rue de Longchamps (Bourlier) — 12.27 m, "
            "pitch 2.39, cornice 15.64, aspect 1.93. NEITHER has an entresol and "
            "both have a porte pietonne. The model reaches 14.92 m of cornice "
            "against their 15.6-15.9, so it is about 0.8 m short at this class."
        ),
    ),
    "M": Layout(
        key="M",
        title="Modest — the street binds, and the corpus runs out",
        site=SiteContext(
            street_width=8.0, parcel_width=9.0, parcel_depth=13.0, year=1865,
            klass=BuildingClass.MODEST, ground=GroundProgramme.RESIDENTIAL, seed=6,
        ),
        expect="RdC + 4 levels on an 8 m street, 5 axes, cornice 11.30",
        why=(
            "The bottom of the ladder, and the one preset where the STREET binds "
            "rather than the stack: at 8 m the 1859 step table caps the cornice "
            "at 11.30 m and the building loses a storey against the same parcel "
            "on a 10 m street. Every other preset is on a street wide enough that "
            "something else decides first.\n\n"
            "**Read this one against O.** Same programme, same seed, one class "
            "and six metres of street apart, and the difference is the whole "
            "argument of the model: nobody chose to make this building shorter."
        ),
        daly=(
            "NOT IN THE CORPUS, and this is the honest caveat. Daly has three "
            "classes and Troisieme is the bottom of them, so MODEST is an "
            "extrapolation below everything measured — the generic ranges "
            "extended downward, not a building anybody drew. Treat its numbers "
            "as the model's opinion rather than as evidence, and do not "
            "calibrate on it."
        ),
    ),
}


def stack_of(site: SiteContext) -> list[tuple[str, float, float]]:
    from buildings.typologies.paris.structure import solve_structure
    from buildings.typologies.paris.roles import assign_roles
    rg = assign_roles(solve_structure(site))
    return [(s.role.value, s.slot.start, s.slot.width) for s in rg.storeys]


def describe(lay: Layout) -> None:
    from buildings.typologies.paris.structure import solve_structure
    grid = solve_structure(lay.site)
    print(f"\n[{lay.key}] {lay.title}")
    print(f"    street {lay.site.street_width:.0f} m · parcel {lay.site.parcel_width:.0f} m "
          f"· {lay.site.year} · {lay.site.klass.value} · {lay.site.ground.value}")
    print(f"    expect: {lay.expect}")
    for role, y, h in stack_of(lay.site):
        print(f"      {role:10} y={y:6.2f}  h={h:4.2f}")
    print(f"    legal cornice {float(grid.cornice_height):.2f} m · "
          f"built {grid.built_height:.2f} m "
          f"({100 * grid.built_height / float(grid.cornice_height):.0f}% of it)")
    if lay.daly:
        print(f"    Daly: {lay.daly}")


def render_one(lay: Layout, out: Path) -> Path:
    from buildings.typologies.paris.generate import generate
    from buildings.render.svg import render
    node, _ = generate(lay.site)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(node, width_px=620), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    keys = [a for a in argv if a in LAYOUTS]
    want_svg = "--svg" in argv
    for lay in (LAYOUTS[k] for k in (keys or LAYOUTS)):
        describe(lay)
        if want_svg:
            p = render_one(lay, ROOT / "dev" / "logs" / "layouts" / f"{lay.key}.svg")
            print(f"    -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
