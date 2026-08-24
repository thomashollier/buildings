"""Follow-ups: isolate what actually failed and how bad it is."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.site import BuildingClass  # noqa: E402
from buildings.typologies.paris import chronology as ch  # noqa: E402
from buildings.rng import DecisionStream  # noqa: E402

print("=== A. gate-4 LITERAL conditions only (window + weight in [0,1]) ===")
import random
rng = random.Random(20260820)
win_bad = w_bad = n = 0
for _ in range(500):
    feat = rng.choice(ch.FEATURES)
    year = rng.randint(1800, 1930)
    klass = rng.choice(list(BuildingClass))
    for v, w in ch.available(feat, year, klass):
        n += 1
        e, _, _, la = v.window_for(klass)
        if not (e <= year <= la):
            win_bad += 1
        if not (0.0 <= w <= 1.0):
            w_bad += 1
print(f"  {n} returned; window violations={win_bad}; weight-range violations={w_bad}")

print("\n=== B. exhaustive: does available() ever return an all-zero weight list? ===")
allzero = []
zero_members = 0
total_members = 0
for feat in ch.FEATURES:
    for klass in BuildingClass:
        for year in range(1700, 2050):
            got = ch.available(feat, year, klass)
            if not got:
                continue
            total_members += len(got)
            zero_members += sum(1 for _, w in got if w == 0.0)
            if all(w == 0.0 for _, w in got):
                allzero.append((feat, klass.value, year, [v.name for v, _ in got]))
print(f"  zero-weight members returned: {zero_members}/{total_members}")
print(f"  cases where EVERY returned weight is 0.0: {len(allzero)}")
for c in allzero[:12]:
    print("   ", c)
if allzero:
    feat, kv, yr, _ = allzero[0]
    kl = BuildingClass(kv)
    got = ch.available(feat, yr, kl)
    ds = DecisionStream(seed=1)
    try:
        pick = ds.choice("t", [v for v, _ in got], [w for _, w in got])
        print(f"    DecisionStream.choice on that case -> {pick.name} (no raise)")
    except Exception as exc:
        print(f"    DecisionStream.choice on that case RAISES: {type(exc).__name__}: {exc}")

print("\n=== C. 1-year prevalence jumps > 0.12, ranked ===")
jumps = []
for feat in ch.FEATURES:
    for v in ch.variants_for(feat):
        for klass in BuildingClass:
            prev = None
            for y in range(1750, 2000):
                p = ch.prevalence(v, y, klass)
                if prev is not None and abs(p - prev) > 0.12:
                    jumps.append((round(abs(p - prev), 4), v.name, klass.value, y, prev, p))
                prev = p
jumps.sort(reverse=True)
for j in jumps[:15]:
    print("   ", j)
print(f"  total 1-yr jumps > 0.12: {len(jumps)}")
print(f"  variants involved: {sorted({j[1] for j in jumps})}")

print("\n=== D. coverage: is any feature EMPTY for some (year, class) in 1820-1910? ===")
gaps = []
for feat in ch.FEATURES:
    for klass in BuildingClass:
        for year in range(1820, 1911):
            got = ch.available(feat, year, klass)
            if not got or all(w == 0.0 for _, w in got):
                gaps.append((feat, klass.value, year))
byfk = {}
for feat, kv, yr in gaps:
    byfk.setdefault((feat, kv), []).append(yr)
for k, yrs in sorted(byfk.items()):
    print(f"   {k}: {len(yrs)} years, e.g. {yrs[:6]}{'...' if len(yrs) > 6 else ''}")
print(f"  total (feature,class,year) gaps in 1820-1910: {len(gaps)}")

print("\n=== E. art nouveau / figurative reachability by class (window after lag) ===")
for name in ("whiplash_art_nouveau", "figurative_caryatid_atlante"):
    v = next(x for f in ch.FEATURES for x in ch.variants_for(f) if x.name == name)
    for klass in BuildingClass:
        print(f"   {name:32s} {klass.value:12s} window={v.window_for(klass)}")

print("\n=== F. legal() for the other declared feature ===")
row = [(y, ch.legal("balcony_individual", y)) for y in (1858, 1859, 1883, 1884, 1901, 1902)]
print("   balcony_individual:", row)
print("   unknown feature 'ironwork':", ch.legal("ironwork", 1850))
