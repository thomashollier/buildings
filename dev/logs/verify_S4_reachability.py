"""Do MEZZANINE and ATTIC ever occur on grids solve_structure actually produces?"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris.structure import solve_structure

counts = Counter()
n_grids = 0
attic_examples = []
mezz_examples = []
worst_headroom = None
for year in (1830, 1850, 1865, 1880, 1890, 1905, 1920):
    for klass in BuildingClass:
        for ground in GroundProgramme:
            for sw in [6.0, 7.5, 9.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 26.0, 30.0]:
                for pw in (7.0, 10.0, 14.0, 20.0):
                    site = SiteContext(street_width=sw, parcel_width=pw, parcel_depth=15.0,
                                       year=year, klass=klass, ground=ground)
                    try:
                        g = solve_structure(site)
                    except Exception as e:
                        counts["SOLVE_FAIL"] += 1
                        continue
                    n_grids += 1
                    rg = assign_roles(g)
                    for rs in rg.storeys:
                        counts[rs.role.value] += 1
                    if any(rs.role is Role.ATTIC for rs in rg.storeys):
                        attic_examples.append((year, klass.value, ground.value, sw, pw))
                    if any(rs.role is Role.MEZZANINE for rs in rg.storeys):
                        mezz_examples.append((year, klass.value, ground.value, sw, pw))
                    top = g.storeys[-1]
                    head = float(g.cornice_height) - top.start
                    if worst_headroom is None or head < worst_headroom[0]:
                        worst_headroom = (head, year, klass.value, ground.value, sw, pw,
                                          float(g.cornice_height), g.built_height)

print(f"grids solved: {n_grids}")
print("role counts across every real grid:", dict(counts))
print("grids containing an ATTIC:", len(attic_examples))
print("grids containing a MEZZANINE:", len(mezz_examples))
print("closest any top slot's START gets to the cornice line:")
print("  headroom m =", worst_headroom)

# What would it take? Show the gap for the tallest-ambition case.
site = SiteContext(street_width=30.0, parcel_width=14.0, parcel_depth=15.0,
                   year=1875, klass=BuildingClass.GRAND, ground=GroundProgramme.SHOP)
g = solve_structure(site)
print()
print("GRAND/shop/30m:  cornice(legal) =", round(float(g.cornice_height), 3),
      " built =", round(g.built_height, 3),
      " top slot start =", round(g.storeys[-1].start, 3),
      " -> start >= cornice?", g.storeys[-1].start >= float(g.cornice_height))

# Edge cases on the predicate itself
from buildings.quantity import Reg
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris.reglement import Era, GabaritEnvelope, RoofEnvelope
from buildings.typologies.paris.structure import Grid

def mk(hs, cornice):
    env = GabaritEnvelope(era=Era.SECOND_EMPIRE, street_width=18.0, facade_height=cornice,
                          roof_envelope=RoofEnvelope.DIAGONAL_45, arc_radius=0.0,
                          ridge_height=6.0, parcel_depth=15.0)
    slots, c = [], 0.0
    for h in hs:
        slots.append(PlacedSlot("storey", SlotKind.REPEATING, c, h)); c += h
    return Grid(tuple(slots), (), Reg(cornice, "fx"), env, ())

print()
print("--- edge cases ---")
print("empty grid:", assign_roles(mk([], 10.0)).storeys)
print("single storey, cornice 0:", [r.role.value for r in assign_roles(mk([3.0], 0.0)).storeys])
print("attic reachable synthetically [4,3.4,3.2,2.2] cornice=10.6:",
      [r.role.value for r in assign_roles(mk([4.0, 3.4, 3.2, 2.2], 10.6)).storeys])
print("all above cornice [4,3.4,3.2] cornice=0:",
      [r.role.value for r in assign_roles(mk([4.0, 3.4, 3.2], 0.0)).storeys])
r = assign_roles(mk([4.0, 3.4, 3.2], 0.0))
print("   ranks:", [x.rank_from_principal for x in r.storeys])
print("mezz + attic-only-above [4,2.0,3.0] cornice=6.0:",
      [x.role.value for x in assign_roles(mk([4.0, 2.0, 3.0], 6.0)).storeys],
      "ranks", [x.rank_from_principal for x in assign_roles(mk([4.0, 2.0, 3.0], 6.0)).storeys])
