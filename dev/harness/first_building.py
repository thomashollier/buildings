#!/usr/bin/env python3
"""The brief's first-week acceptance, run as a script.

    "Reproduce one real building's elevation end to end through all four
    phases, with a trace explaining every element, before generalising
    anything. If the phase model is wrong, this surfaces it in days rather
    than after rules have been built on top of it."   — BRIEF.md / PLAN.md §4

The building is the canonical case and nothing more exotic: a mid-block
immeuble on a 20 m boulevard, c. 1865, comfortable but not grand, with a shop
on the ground floor. Every number below is derived — the only things chosen
are the five facts in ``SITE``, which are the situation, not the design.

Run:  python3 dev/harness/first_building.py [--json]

Exit 0 = the building generated, every element carries a trace, and the
silhouette is inside the gabarit. Exit 1 = one of those is false.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.ir.serial import to_json  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import generate, walk  # noqa: E402
from buildings.typologies.paris.reglement import era_for_year, get_reglement  # noqa: E402
from buildings.typologies.paris.roles import assign_roles  # noqa: E402
from buildings.typologies.paris.structure import solve_structure  # noqa: E402
from buildings.typologies.paris.terminate import Silhouette  # noqa: E402


SITE = SiteContext(
    street_width=20.0,  # a percée: the 1859 règlement's own top step
    parcel_width=12.0,  # an ordinary haussmannian lot
    parcel_depth=14.0,
    year=1865,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
    corner=False,
    seed=1865,
)

RULE = "═" * 78
THIN = "─" * 78


def head(text: str) -> None:
    print()
    print(RULE)
    print(text)
    print(RULE)


def main(argv: list[str]) -> int:
    building, log = generate(SITE)

    if "--json" in argv:
        print(to_json(building))
        return 0

    era = era_for_year(SITE.year)
    reg = get_reglement(era)
    grid = solve_structure(SITE)
    roled = assign_roles(grid)

    # ---------------------------------------------------------------- situation
    head("THE SITUATION  — the only things chosen")
    print(f"  street width    {SITE.street_width:>6.2f} m   (handed down by the block; never rolled here — I2)")
    print(f"  parcel          {SITE.parcel_width:>6.2f} m wide × {SITE.parcel_depth:.2f} m deep")
    print(f"  year            {SITE.year:>6d}")
    print(f"  class           {SITE.klass.value}")
    print(f"  ground floor    {SITE.ground.value}")
    print(f"  corner          {SITE.corner}")
    print(f"  seed            {SITE.seed}")
    print()
    print(f"  regulation in force: {reg.label} — {reg.decree}")
    print(f"  roof envelope:       {reg.roof_envelope.value}")

    # ---------------------------------------------------------------- envelope
    head("PHASE 1 · STRUCTURE  — the envelope, then the budgets")
    ceiling = float(grid.cornice_height)
    built = grid.built_height
    env = grid.envelope
    print(f"  legal cornice ceiling   {ceiling:>6.2f} m   ({grid.cornice_height.why})")
    print(f"  built to                {built:>6.2f} m   ({built / ceiling:.0%} of it — the law says how")
    print(f"                                       tall you MAY build; programme says how tall you DID)")
    print(f"  legal comble above it   {env.legal_ridge_height:>6.2f} m")
    print(f"  comble built            {env.ridge_height:>6.2f} m")
    print(f"  legal total             {env.total_height:>6.2f} m   vs built {built + env.ridge_height:.2f} m")

    # ---------------------------------------------------------------- stack
    head("PHASE 2 · ROLES  — identity derived from the stack, never declared")
    print(f"  {'#':>2}  {'role':<11} {'level':>8} {'height':>8} {'rank':>5}  why")
    print(f"  {THIN}")
    median = sorted(s.slot.width for s in roled.storeys)[len(roled.storeys) // 2]
    for s in reversed(roled.storeys):
        why = {
            "base": "bottom slot — unconditional",
            "mezzanine": "directly above the base and markedly shorter",
            "principal": "TALLEST habitable slot above base and mezzanine",
            "upper": "between the principal floor and the attic",
            "attic": "inside the roof envelope",
        }[s.role.value]
        print(
            f"  {s.index_from_bottom:>2}  {s.role.value:<11} "
            f"{s.slot.start:>7.2f}m {s.slot.width:>7.2f}m {s.rank_from_principal:>+5d}  {why}"
        )
    print(f"  {THIN}")
    print(f"  median storey height {median:.2f} m; the ground floor is {roled.storeys[0].slot.width:.2f} m —")
    print("  taller than the noble floor, which is exactly why the base exclusion is load-bearing.")

    # ---------------------------------------------------------------- bays
    head("PHASE 1 · STRUCTURE  — the bay grid, solved ONCE for the whole building")
    for i, b in enumerate(grid.bays):
        mark = "  ← inserted special" if b.is_special else ""
        print(f"  slot {i}  {b.name:<12} start {b.start:>6.2f} m  width {b.width:>5.2f} m{mark}")
    print(f"  every storey decorates this one grid, so no opening can drift out of alignment.")

    # ---------------------------------------------------------------- comble
    head("PHASE 5 · TERMINATION  — the comble is the residue of the rule")
    roof = next(n for n in walk(building) if n.kind == "roof")
    sil_node = next(n for n in walk(building) if n.kind == "silhouette")
    sil = Silhouette(sil_node.props["points"])
    print(f"  envelope             {roof.props['envelope']}  (radius {roof.props['arc_radius']:.2f} m)")
    print(f"  eaves                {roof.props['eaves_height']:>6.2f} m")
    print(f"  ridge                {roof.props['ridge_height']:>6.2f} m, set back {roof.props['ridge_setback']:.2f} m")
    print(f"  as a broken mansard  {roof.props['lower_angle_deg']:.1f}° / {roof.props['upper_angle_deg']:.1f}°"
          f" breaking at {roof.props['break_pct']:.0%}")
    print(f"  dormer repertoire    {roof.props['dormer_variant']}")
    print(f"  comble envelope      {roof.props['envelope']} (from the decree, not the fashion)")
    print(f"  covering             {roof.props['material']}")
    print()
    print("  silhouette (section perpendicular to the street: inset from the facade plane, height):")
    for inset, y in sil.points:
        print(f"      {inset:>7.3f} m in,  {y:>7.3f} m up")
    print()
    print(f"  inside the gabarit: {sil.within(env)}   (tightest clearance {sil.clearance(env):+.3f} m)")

    # ---------------------------------------------------------------- elements
    head("THE ELEMENTS  — every node, and the rule that produced it")
    counts: dict[str, int] = {}
    for node in walk(building):
        counts[node.kind] = counts.get(node.kind, 0) + 1
    print("  " + ", ".join(f"{k}×{v}" for k, v in sorted(counts.items())))
    print(f"  {len(list(walk(building)))} nodes, {len(log.all_ids())} of them recorded in the trace log")

    head("THE FULL TRACE  — for every element, the rule and the reason")
    for node in walk(building):
        extent = ""
        if "w" in node.props and "h" in node.props:
            extent = (
                f"  [x {float(node.props['x']):.2f} y {float(node.props['y']):.2f} "
                f"w {float(node.props['w']):.2f} h {float(node.props['h']):.2f}]"
            )
        print()
        print(f"{node.id}  ({node.kind}){extent}")
        interesting = {
            k: v
            for k, v in sorted(node.props.items())
            if k not in ("x", "y", "w", "h", "points", "profile") and v is not None
        }
        if interesting:
            print("    props: " + ", ".join(f"{k}={v!r}" for k, v in interesting.items()))
        for entry in node.trace:
            for i, line in enumerate(entry.detail.splitlines() or [""]):
                if i == 0:
                    print(f"    ├─ [{entry.phase}] {entry.rule}")
                    print(f"    │    {line}")
                else:
                    print(f"    │    {line}")
            if entry.inputs:
                print(
                    "    │    given: "
                    + ", ".join(f"{k}={v!r}" for k, v in sorted(entry.inputs.items()))
                )

    # ---------------------------------------------------------------- gates
    head("ACCEPTANCE")
    nodes = list(walk(building))
    untraced = [n.id for n in nodes if not n.trace]
    ok_trace = not untraced
    ok_env = sil.within(env)
    again, _ = generate(SITE)
    ok_det = to_json(again) == to_json(building)

    print(f"  every element records its rule (I4)        {'PASS' if ok_trace else 'FAIL ' + str(untraced)}")
    print(f"  silhouette inscribed in the gabarit (G7)   {'PASS' if ok_env else 'FAIL'}")
    print(f"  seed + situation ⇒ identical output (I5)   {'PASS' if ok_det else 'FAIL'}")
    print()
    return 0 if (ok_trace and ok_env and ok_det) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
