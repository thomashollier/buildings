#!/usr/bin/env python3
"""A15.1 verification: the comble across the 45 degree era, and the envelope.

Two measurements, and the amendment asks for both.

1. **The distribution.** Sweep 1865 across street width, parcel width, parcel
   depth, class and ground programme and report every comble height the
   generator produces. Before A15.1 this was one value -- 3.20 m on all 180
   sites of the amendment's own sweep -- against Daly's nine 1864 commercial
   buildings at 2.69 / 2.77 / 2.85 / 3.18 / 3.34 / 3.45 / 4.72 / 6.80 / 7.00 m.

2. **The envelope still holds.** Every silhouette point, over the same sweep,
   measured against ``max_height_for_setback`` -- the inverse of the curve --
   anchored at the eaves the comble springs from, which is how legality is
   asked (A3.1). The A14 gate reported 0 violations and a worst overshoot of
   0.000000 m and A15 requires that to survive.

    python3 dev/logs/verify_A15_comble_sweep.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402
from buildings.typologies.paris.structure import solve_structure  # noqa: E402

STREETS = (6.0, 7.8, 9.75, 12.0, 15.0, 18.0, 20.0, 24.0, 30.0, 40.0)
DEPTHS = (8.0, 11.0, 14.0, 18.0, 22.0, 30.0)
PARCELS = (8.0, 12.0, 18.0)

DALY_1864_COMMERCIAL = (2.69, 2.77, 2.85, 3.18, 3.34, 3.45, 4.72, 6.80, 7.00)


def main() -> int:
    combles: Counter[float] = Counter()
    rooms: Counter[int] = Counter()
    bought = 0
    sites = 0
    worst_overshoot = 0.0
    violations = 0

    for street in STREETS:
        for depth in DEPTHS:
            for parcel in PARCELS:
                for klass in BuildingClass:
                    for ground in GroundProgramme:
                        s = SiteContext(
                            street_width=street,
                            parcel_width=parcel,
                            parcel_depth=depth,
                            year=1865,
                            klass=klass,
                            ground=ground,
                        )
                        grid = solve_structure(s)
                        sites += 1
                        combles[round(grid.comble_height, 3)] += 1
                        rooms[len(grid.comble_storeys)] += 1
                        bought += grid.extra_garret_storeys

                        root, _log = generate(s)
                        sil = next(
                            n for n in root.children if n.kind == "silhouette"
                        )
                        env = grid.envelope
                        eaves = grid.built_height
                        for inset, y in sil.props["points"]:
                            h = y - eaves
                            if h <= 1e-9:
                                continue
                            allowed = env.max_height_for_setback(inset)
                            over = h - allowed
                            if over > 1e-6:
                                violations += 1
                            worst_overshoot = max(worst_overshoot, over)

    values = sorted(combles)
    print(f"sites swept                : {sites}")
    print(f"distinct comble heights    : {len(values)}")
    print(f"range                      : {values[0]:.2f} - {values[-1]:.2f} m "
          f"(x{values[-1] / values[0]:.2f})")
    print(f"Daly 1864 commercial (n=9) : "
          f"{DALY_1864_COMMERCIAL[0]:.2f} - {DALY_1864_COMMERCIAL[-1]:.2f} m "
          f"(x{DALY_1864_COMMERCIAL[-1] / DALY_1864_COMMERCIAL[0]:.2f})")
    print()
    for v in values:
        n = combles[v]
        print(f"  {v:6.3f} m  {n:5d}  {n / sites:6.1%}  {'#' * max(1, n * 40 // sites)}")
    print()
    print("storeys of chambres de bonne in the comble:")
    for k in sorted(rooms):
        print(f"  {k}  {rooms[k]:5d}  {rooms[k] / sites:6.1%}")
    print(f"runs that bought a second storey out of the cornice: "
          f"{bought} ({bought / sites:.1%}) -- INFERRED rate (A15.2), not calibrated")
    print()
    print(f"envelope violations        : {violations}")
    print(f"worst overshoot            : {worst_overshoot:.6f} m")
    return 0 if violations == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
