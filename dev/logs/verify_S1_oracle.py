"""Third verifier pass.

(a) A brute-force feasibility oracle: for the solver's own model (2 equal ends,
    n equal bays, k in {0,1,2} equal specials, fixed slots at preferred) the set
    of reachable budgets for a given n is exactly the interval
        [2*e_min + n*b_min + k*s_min, 2*e_max + n*b_max + k*s_max] + reserved.
    If solve() raises FitInfeasible while that interval contains the budget for
    some admissible n, the solver refused a width it could have made.
(b) gate item 2 re-run with min_bays=0 so the rigid door is exercised over the
    whole 4.0-40.0 range.
"""
from __future__ import annotations

import math
import sys

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")

from buildings.solver.fitting import FitInfeasible, SlotKind, SlotSpec, solve  # noqa: E402

WIDTHS = [round(4.0 + 0.05 * i, 10) for i in range(721)]

END = SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.55, 1.10, elasticity=3.0)
BAY = SlotSpec("bay", SlotKind.REPEATING, 2.60, 3.00, 3.60)
SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.60, 1.20, 1.90, elasticity=0.5)
DOOR = SlotSpec("porte-cochere", SlotKind.FIXED, 2.60, 2.60, 2.60, rigid=True)
E5 = SlotSpec("e5", SlotKind.FLEXIBLE, 0.40, 0.50, 0.60)
B5 = SlotSpec("b5", SlotKind.REPEATING, 2.60, 3.00, 3.10)
S5 = SlotSpec("s5", SlotKind.FLEXIBLE, 0.60, 0.80, 1.00)


def oracle_feasible(budget, end, bay, special, fixed=(), min_bays=1, max_bays=24,
                    central=False):
    reserved = math.fsum(s.preferred for _, s in fixed)
    ks = (0, 1, 2) if special is not None else (0,)
    hits = []
    for n in range(min_bays, max_bays + 1):
        for k in ks:
            lo = 2 * end.minimum + n * bay.minimum + reserved + (k * special.minimum if k else 0)
            hi = 2 * end.maximum + n * bay.maximum + reserved + (k * special.maximum if k else 0)
            if lo - 1e-12 <= budget <= hi + 1e-12:
                hits.append((n, k))
    return hits


print("=== 10: brute-force feasibility oracle vs solve() ===")
CASES = [
    ("END/BAY/SPECIAL", dict(end=END, bay=BAY, special=SPECIAL)),
    ("END/BAY no special", dict(end=END, bay=BAY, special=None)),
    ("rung-5 vocab", dict(end=E5, bay=B5, special=S5)),
    ("rung-5 vocab cf", dict(end=E5, bay=B5, special=S5, central_feature=True)),
    ("door, min_bays=1", dict(end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),))),
    ("door, min_bays=0", dict(end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),), min_bays=0)),
]
for label, kw in CASES:
    refused_but_possible = []
    raised = 0
    for w in WIDTHS:
        try:
            solve(w, **kw)
        except FitInfeasible:
            raised += 1
            hits = oracle_feasible(
                w, kw["end"], kw["bay"], kw.get("special"), kw.get("fixed", ()),
                kw.get("min_bays", 1), kw.get("max_bays", 24),
            )
            if hits:
                refused_but_possible.append((w, hits[:3]))
    print(f"  {label}: raised={raised}, of which an in-bounds arrangement DID exist = "
          f"{len(refused_but_possible)}")
    for r in refused_but_possible[:10]:
        print(f"     width {r[0]}: oracle says feasible with (n_bays,k_specials) in {r[1]}")
    if len(refused_but_possible) > 10:
        print(f"     ... {len(refused_but_possible)} total")

print("\n=== 2b: gate item 2 with min_bays=0 so the door covers the whole range ===")
for label, kw in [
    ("door alone", dict(end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),), min_bays=0)),
    ("door + cf", dict(end=END, bay=BAY, special=SPECIAL, fixed=((2, DOOR),), min_bays=0,
                       central_feature=True)),
]:
    drift = 0
    n = 0
    inf = 0
    sumerr = 0
    oob = 0
    for w in WIDTHS:
        try:
            res = solve(w, **kw)
        except FitInfeasible:
            inf += 1
            continue
        n += 1
        if abs(math.fsum(s.width for s in res.slots) - w) > 1e-9:
            sumerr += 1
        for s in res.slots:
            if s.name == DOOR.name:
                if s.width != DOOR.preferred:
                    drift += 1
            spec = {"end": END, "bay": BAY, "special": SPECIAL}.get(s.name)
            if spec and (s.width < spec.minimum - 1e-12 or s.width > spec.maximum + 1e-12):
                oob += 1
    print(f"  {label}: solved={n}, infeasible={inf}, door drift (strict ==)={drift}, "
          f"sum errors={sumerr}, out-of-bounds slots={oob}")

print("\n=== 11: max residual observed over every successful solve in every case ===")
worst = 0.0
worst_at = None
count = 0
for label, kw in CASES:
    for w in WIDTHS:
        try:
            res = solve(w, **kw)
        except FitInfeasible:
            continue
        count += 1
        err = abs(math.fsum(s.width for s in res.slots) - w)
        if err > worst:
            worst, worst_at = err, (label, w)
print(f"  {count} successful solves; worst |sum-budget| = {worst:.3e} at {worst_at}")

print("\n=== 12: bounds check uses EPS=1e-9 slack - is any slot outside by >0? ===")
over = []
for label, kw in CASES:
    for w in WIDTHS:
        try:
            res = solve(w, **kw)
        except FitInfeasible:
            continue
        for s in res.slots:
            spec = {"end": END, "bay": BAY, "special": SPECIAL, "e5": E5, "b5": B5,
                    "s5": S5, DOOR.name: DOOR}.get(s.name)
            if spec is None:
                continue
            d = max(spec.minimum - s.width, s.width - spec.maximum)
            if d > 0:
                over.append((label, w, s.name, d))
print(f"  slots outside declared bounds by any positive amount: {len(over)}")
for o in over[:6]:
    print("   ", o)
