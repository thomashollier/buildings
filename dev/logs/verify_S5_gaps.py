"""Where in the working range 1820-1902 does available() break down?"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from buildings.site import BuildingClass  # noqa: E402
from buildings.typologies.paris import chronology as ch  # noqa: E402
from buildings.rng import DecisionStream  # noqa: E402

empty = []
allzero = []
for feat in ch.FEATURES:
    for klass in BuildingClass:
        for year in range(1820, 1903):
            got = ch.available(feat, year, klass)
            if not got:
                empty.append((feat, klass.value, year))
            elif all(w == 0.0 for _, w in got):
                allzero.append((feat, klass.value, year, [v.name for v, _ in got]))

print(f"EMPTY available() in 1820-1902: {len(empty)}")
byk = {}
for f, k, y in empty:
    byk.setdefault((f, k), []).append(y)
for k, ys in sorted(byk.items()):
    print(f"   {k}: years {ys[0]}-{ys[-1]} ({len(ys)})")

print(f"\nALL-ZERO-WEIGHT available() in 1820-1902: {len(allzero)}")
for c in allzero:
    print("   ", c)
if allzero:
    f, k, y, _ = allzero[0]
    got = ch.available(f, y, BuildingClass(k))
    try:
        DecisionStream(seed=7).choice("p", [v for v, _ in got], [w for _, w in got])
        print("    choice() did not raise")
    except Exception as e:
        print(f"    DecisionStream.choice -> {type(e).__name__}: {e}")

print("\nZero-weight members returned inside 1820-1902 (docstring says 'always > 0'):")
cnt = 0
ex = []
for feat in ch.FEATURES:
    for klass in BuildingClass:
        for year in range(1820, 1903):
            for v, w in ch.available(feat, year, klass):
                if w == 0.0:
                    cnt += 1
                    if len(ex) < 8:
                        ex.append((feat, klass.value, year, v.name))
print(f"   count={cnt}; examples={ex}")
