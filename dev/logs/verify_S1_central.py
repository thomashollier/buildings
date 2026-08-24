"""What does central_feature=True actually change, and does the result ever
contain an identifiable central element?"""
from __future__ import annotations

import math
import sys
from collections import Counter

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")

from buildings.solver.fitting import FitInfeasible, SlotKind, SlotSpec, solve  # noqa: E402

WIDTHS = [round(4.0 + 0.05 * i, 10) for i in range(721)]
END = SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.55, 1.10, elasticity=3.0)
BAY = SlotSpec("bay", SlotKind.REPEATING, 2.60, 3.00, 3.60)
SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.60, 1.20, 1.90, elasticity=0.5)


def key(res):
    return tuple((s.name, round(s.width, 12), s.is_special) for s in res.slots)


same = 0
diff = 0
only_cf_fails = 0
no_central_element = []
has_central = 0
parity = Counter()
for w in WIDTHS:
    try:
        a = solve(w, end=END, bay=BAY, special=SPECIAL, central_feature=False)
    except FitInfeasible:
        a = None
    try:
        b = solve(w, end=END, bay=BAY, special=SPECIAL, central_feature=True)
    except FitInfeasible:
        b = None
        only_cf_fails += 1
        continue
    if a is not None:
        if key(a) == key(b):
            same += 1
        else:
            diff += 1
    interior = b.slots[1:-1]            # everything between the two ends
    n = len(interior)
    parity[n % 2] += 1
    # a "central feature" means an element sits on the centreline: the interior
    # run has odd length, so one element is the middle one.
    if n % 2 == 1:
        has_central += 1
    else:
        no_central_element.append(w)

print(f"widths: {len(WIDTHS)}")
print(f"central_feature=True produces a layout IDENTICAL to central_feature=False "
      f"on {same} widths; different on {diff}")
print(f"central_feature=True infeasible where False succeeds: {only_cf_fails}")
print(f"interior run has an element on the centreline (odd length): {has_central} widths")
print(f"interior run has NO element on the centreline (even length): "
      f"{len(no_central_element)} widths "
      f"({100*len(no_central_element)/max(1,has_central+len(no_central_element)):.1f}%)")
print(f"  e.g. {no_central_element[:12]}")

print()
for w in (10.10, 13.10, 16.10, 20.00, 25.10):
    try:
        r = solve(w, end=END, bay=BAY, special=SPECIAL, central_feature=True)
    except FitInfeasible as e:
        print(f"  {w}: INFEASIBLE {e}")
        continue
    print(f"  {w}: {[ (s.name[:4], round(s.width,3)) for s in r.slots ]} rung={r.rung.name}")
