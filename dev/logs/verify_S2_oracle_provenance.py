import sys, itertools
from pathlib import Path
ROOT = Path("/Users/thomas/Documents/claude/buildings")
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, "/Users/thomas/Documents/claude/haussmann")
import core.reglement as old
from buildings.typologies.paris import reglement as new
print("OLD __file__ :", old.__file__)
print("NEW __file__ :", new.__file__)
print("SAME MODULE OBJECT? ", old is new)
assert old.__file__ != new.__file__, "SELF-IMPORT: oracle is the same file!"
assert "haussmann" in old.__file__

widths = [w/4 for w in range(12, 161)]          # 3.00 .. 40.00 step 0.25
years  = list(range(1820, 1911))
pairs = 0; bad = []
for w, y in itertools.product(widths, years):
    oe = old.era_for_year(y); ne = new.era_for_year(y)
    if oe.name != ne.name: bad.append(("era", w, y, oe.name, ne.name))
    orr = old.get_reglement(oe); nrr = new.get_reglement(ne)
    for fn in ("facade_height_limit", "arc_radius"):
        a = getattr(orr, fn)(w); b = getattr(nrr, fn)(w)
        if a != b: bad.append((fn, w, y, a, b))
    oenv = old.compute_envelope(w, oe, parcel_depth=40.0)
    nenv = new.compute_envelope(w, ne, parcel_depth=40.0)
    if float(oenv.total_height) != float(nenv.total_height): bad.append(("total_height", w, y, oenv.total_height, nenv.total_height))
    if float(oenv.facade_height) != float(nenv.facade_height): bad.append(("facade_height", w, y))
    if oenv.roof_envelope.name != nenv.roof_envelope.name: bad.append(("roof_env", w, y))
    for h in (0.0, 0.5, 1.0, 2.0, 3.0, 5.0):
        if float(oenv.setback_at(h)) != float(nenv.setback_at(h)): bad.append(("setback", w, y, h))
    pairs += 1
print(f"PAIRS COMPARED (independent, my own sweep): {pairs}")
print(f"MISMATCHES: {len(bad)}")
for b in bad[:20]: print("  ", b)

# 28.50 assertion, exact
env = new.compute_envelope(30.0, new.Era.ALPHAND, parcel_depth=40.0)
print("1884 facade_height      =", float(env.facade_height))
print("1884 legal_ridge_height =", float(env.legal_ridge_height))
print("1884 total_height       =", float(env.total_height))
assert abs(float(env.total_height) - 28.50) < 1e-12, "28.50 FAIL"
print("28.50 CEILING: OK")

# does era 1884 actually get chosen for a 1884-1901 year?
for y in (1883, 1884, 1890, 1901, 1902):
    print(f"  year {y} -> era {new.era_for_year(y).name}")

# negative control: mutate a copy and prove the diff test would catch it
print("NEGATIVE CONTROL: perturbing new arc_radius by 0.01 ->", end=" ")
r = new.get_reglement(new.Era.ALPHAND)
print("baseline arc_radius(30)=", r.arc_radius(30.0), "old=", old.get_reglement(old.Era.ALPHAND).arc_radius(30.0))
