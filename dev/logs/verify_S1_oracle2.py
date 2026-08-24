"""Refined oracle: only arrangements the solver itself is allowed to build.

non-central: k specials in {0,1}, any n in [min_bays, max_bays]
central:     k in {0,2} (a pair) or {0,1} centred, n restricted by parity to
             n0, n0+2, n0+4 ... (the contract's ADD_MODULE-steps-by-2 rule)
"""
from __future__ import annotations

import math
import sys

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")

from buildings.solver.fitting import FitInfeasible, SlotKind, SlotSpec, solve  # noqa: E402

WIDTHS = [round(4.0 + 0.05 * i, 10) for i in range(721)]
E5 = SlotSpec("e5", SlotKind.FLEXIBLE, 0.40, 0.50, 0.60)
B5 = SlotSpec("b5", SlotKind.REPEATING, 2.60, 3.00, 3.10)
S5 = SlotSpec("s5", SlotKind.FLEXIBLE, 0.60, 0.80, 1.00)


def n0_of(budget, end, bay, min_bays=1, max_bays=24):
    raw = int(math.floor((budget - 2 * end.preferred) / bay.preferred + 1e-9))
    return min(max(raw, min_bays), max_bays)


def reachable(budget, end, bay, special, central, min_bays=1, max_bays=24):
    n0 = n0_of(budget, end, bay, min_bays, max_bays)
    ns = ([n0] + list(range(n0 + 2, max_bays + 1, 2))) if central else list(
        range(min_bays, max_bays + 1))
    ks = (0, 1, 2) if (special is not None and central) else ((0, 1) if special else (0,))
    hits = []
    for n in ns:
        for k in ks:
            lo = 2 * end.minimum + n * bay.minimum + (k * special.minimum if k else 0)
            hi = 2 * end.maximum + n * bay.maximum + (k * special.maximum if k else 0)
            if lo - 1e-12 <= budget <= hi + 1e-12:
                hits.append((n, k))
    return n0, hits


for label, central in [("rung-5 vocab, cf=False", False), ("rung-5 vocab, cf=True", True)]:
    raised = 0
    missed = []
    for w in WIDTHS:
        try:
            solve(w, end=E5, bay=B5, special=S5, central_feature=central)
        except FitInfeasible:
            raised += 1
            n0, hits = reachable(w, E5, B5, S5, central)
            if hits:
                missed.append((w, n0, hits[:3]))
    print(f"{label}: raised={raised}; refused-though-reachable={len(missed)}")
    for m in missed[:12]:
        print(f"   width {m[0]}: n0={m[1]} reachable with (n,k)={m[2]}")
    if len(missed) > 12:
        print(f"   ... {len(missed)} total")
