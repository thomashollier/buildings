"""Second verifier pass: monotonicity bucketed by natural count, ADD_MODULE
parity under a vocabulary that actually forces rung 5, mirror symmetry of a
central_feature composition, and the infeasible band with a rigid door.
"""
from __future__ import annotations

import math
import sys
from collections import Counter

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")

from buildings.solver.fitting import (  # noqa: E402
    FitInfeasible, Rung, SlotKind, SlotSpec, solve,
)

WIDTHS = [round(4.0 + 0.05 * i, 10) for i in range(721)]

END = SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.55, 1.10, elasticity=3.0)
BAY = SlotSpec("bay", SlotKind.REPEATING, 2.60, 3.00, 3.60)
SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.60, 1.20, 1.90, elasticity=0.5)
DOOR = SlotSpec("porte-cochere", SlotKind.FIXED, 2.60, 2.60, 2.60, rigid=True)

# vocabulary tuned so rung 5 is actually reachable
E5 = SlotSpec("e5", SlotKind.FLEXIBLE, 0.40, 0.50, 0.60)
B5 = SlotSpec("b5", SlotKind.REPEATING, 2.60, 3.00, 3.10)
S5 = SlotSpec("s5", SlotKind.FLEXIBLE, 0.60, 0.80, 1.00)


def natural_n(budget, end, bay, fixed=(), min_bays=1, max_bays=24):
    avail = budget - math.fsum(s.preferred for _, s in fixed)
    raw = int(math.floor((avail - 2 * end.preferred) / bay.preferred + 1e-9))
    return min(max(raw, min_bays), max_bays)


print("=== 3b: monotonicity bucketed by NATURAL bay count n0, slack >= 0 ===")
for label, kw in [
    ("with special", dict(end=END, bay=BAY, special=SPECIAL)),
    ("no special", dict(end=END, bay=BAY, special=None)),
    ("rung-5 vocab", dict(end=E5, bay=B5, special=S5)),
    ("rung-5 vocab, cf", dict(end=E5, bay=B5, special=S5, central_feature=True)),
]:
    end, bay = kw["end"], kw["bay"]
    buckets: dict[int, list] = {}
    for w in WIDTHS:
        try:
            res = solve(w, **kw)
        except FitInfeasible:
            continue
        n0 = natural_n(w, end, bay)
        slack = w - 2 * end.preferred - n0 * bay.preferred
        buckets.setdefault(n0, []).append((slack, w, res.rung))
    bad, badneg = [], []
    for n0, rows in sorted(buckets.items()):
        rows.sort()
        for (s0, w0, r0), (s1, w1, r1) in zip(rows, rows[1:]):
            if r1.value < r0.value:
                (badneg if s0 < -1e-9 else bad).append((n0, w0, r0.name, s0, w1, r1.name, s1))
    print(f"  {label}: n0 buckets={sorted(buckets)}, backward steps at slack>=0: {len(bad)}, "
          f"backward steps in negative-slack region: {len(badneg)}")
    for e in bad[:8]:
        print(f"     n0={e[0]} width {e[1]} slack {e[3]:+.4f} {e[2]} -> width {e[4]} "
              f"slack {e[6]:+.4f} {e[5]}")
    for e in badneg[:3]:
        print(f"     [neg] n0={e[0]} width {e[1]} slack {e[3]:+.4f} {e[2]} -> width {e[4]} "
              f"slack {e[6]:+.4f} {e[5]}")

print("\n=== 4c: does rung 5 ever fire, and by what step? ===")
for label, cf in [("cf=False", False), ("cf=True", True)]:
    steps = Counter()
    rungs = Counter()
    infeas = 0
    odd_steps = []
    for w in WIDTHS:
        try:
            res = solve(w, end=E5, bay=B5, special=S5, central_feature=cf)
        except FitInfeasible:
            infeas += 1
            continue
        rungs[res.rung.name] += 1
        if res.rung is Rung.ADD_MODULE:
            n = sum(1 for s in res.slots if s.kind is SlotKind.REPEATING)
            n0 = natural_n(w, E5, B5)
            steps[n - n0] += 1
            if cf and (n - n0) % 2:
                odd_steps.append((w, n0, n))
    print(f"  {label}: infeasible={infeas}, rungs={dict(rungs)}, ADD_MODULE steps={dict(steps)}")
    if odd_steps:
        print(f"     ODD ADD_MODULE steps under central_feature: {odd_steps[:10]}")

print("\n=== 4d: is a central_feature composition mirror-symmetric? ===")
for label, kw in [
    ("cf + special (END/BAY)", dict(end=END, bay=BAY, special=SPECIAL, central_feature=True)),
    ("cf + special (rung-5 vocab)", dict(end=E5, bay=B5, special=S5, central_feature=True)),
]:
    asym = []
    n_ok = 0
    for w in WIDTHS:
        try:
            res = solve(w, **kw)
        except FitInfeasible:
            continue
        ws = [s.width for s in res.slots]
        names = [s.name for s in res.slots]
        if not (all(abs(a - b) < 1e-9 for a, b in zip(ws, reversed(ws)))
                and names == names[::-1]):
            asym.append((w, names, [round(x, 3) for x in ws]))
        else:
            n_ok += 1
    print(f"  {label}: symmetric={n_ok}, ASYMMETRIC={len(asym)}")
    for a in asym[:4]:
        print(f"     width {a[0]}: {a[1]}")
        print(f"                 {a[2]}")

print("\n=== 4e: does central_feature ever produce a centre BAY (odd count, no special)? ===")
c = Counter()
for w in WIDTHS:
    try:
        res = solve(w, end=END, bay=BAY, special=SPECIAL, central_feature=True)
    except FitInfeasible:
        continue
    n = sum(1 for s in res.slots if s.kind is SlotKind.REPEATING)
    has_sp = any(s.is_special for s in res.slots)
    c[(n % 2, has_sp)] += 1
print("  (bay_count_parity, has_special) -> widths:", dict(c))

print("\n=== 1b: rigid-door infeasible band, and does min_bays=0 rescue it? ===")
for mb in (1, 0):
    bad = []
    for w in WIDTHS:
        try:
            solve(w, end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),), min_bays=mb)
        except FitInfeasible:
            bad.append(w)
    print(f"  min_bays={mb}: infeasible count={len(bad)}"
          + (f", range {bad[0]}..{bad[-1]}" if bad else ""))

print("\n=== 1c: minimum feasible width arithmetic for the door case ===")
print(f"  2*end.min + bay.min + door = {2*END.minimum + BAY.minimum + DOOR.preferred:.2f} m")
print(f"  2*end.min + door           = {2*END.minimum + DOOR.preferred:.2f} m")

print("\n=== 1d: FitInfeasible band for vocabularies with NO special (impl's claim) ===")
bad = []
for w in WIDTHS:
    try:
        solve(w, end=END, bay=BAY, special=None)
    except FitInfeasible:
        bad.append(w)
print(f"  end/bay no special: infeasible={len(bad)} {bad[:20]}")

print("\n=== 7: rigid slot exactness under adversarial float budgets ===")
import random
rnd = random.Random(12345)
drift = 0
tested = 0
for _ in range(5000):
    w = rnd.uniform(6.0, 40.0)
    try:
        res = solve(w, end=END, bay=BAY, special=SPECIAL, fixed=((rnd.randint(0, 6), DOOR),))
    except FitInfeasible:
        continue
    tested += 1
    for s in res.slots:
        if s.name == DOOR.name and s.width != DOOR.preferred:
            drift += 1
            if drift < 4:
                print(f"     DRIFT width={w!r} door={s.width!r}")
    total = math.fsum(s.width for s in res.slots)
    if abs(total - w) > 1e-9:
        print(f"     SUM ERROR width={w!r} err={total-w:.3e}")
print(f"  {tested} random budgets: rigid drift occurrences={drift}")

print("\n=== 8: two fixed slots + special, bounds and sum ===")
D2 = SlotSpec("shop-door", SlotKind.FIXED, 1.4, 1.4, 1.4, rigid=True)
bad = 0
inf = 0
for w in WIDTHS:
    try:
        res = solve(w, end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR), (4, D2)))
    except FitInfeasible:
        inf += 1
        continue
    if abs(math.fsum(s.width for s in res.slots) - w) > 1e-9:
        bad += 1
    for s in res.slots:
        if s.name in (DOOR.name, D2.name) and s.width != {DOOR.name: 2.6, D2.name: 1.4}[s.name]:
            bad += 1
print(f"  two fixed slots: infeasible={inf}, violations={bad}")

print("\n=== 9: elasticity ordering actually honoured (ends before bays) ===")
res = solve(12.0, end=END, bay=BAY, special=SPECIAL)
print("  12.0 m:", [(s.name, round(s.width, 4)) for s in res.slots], res.rung.name)
for a in res.account:
    print("    ", a)
