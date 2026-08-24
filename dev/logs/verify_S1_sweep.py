"""Independent verification sweep for S1 (fitting solver). Written by the verifier.

Nothing here is imported from the implementer's tests.
"""
from __future__ import annotations

import math
import sys
from collections import Counter

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")

from buildings.solver.fitting import (  # noqa: E402
    FitInfeasible,
    Rung,
    SlotKind,
    SlotSpec,
    solve,
)

WIDTHS = [round(4.0 + 0.05 * i, 10) for i in range(int((40.0 - 4.0) / 0.05) + 1)]
print(f"sweep widths: {len(WIDTHS)} from {WIDTHS[0]} to {WIDTHS[-1]}")

END = SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.55, 1.10, elasticity=3.0)
BAY = SlotSpec("bay", SlotKind.REPEATING, 2.60, 3.00, 3.60, elasticity=1.0)
SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.60, 1.20, 1.90, elasticity=0.5)
DOOR = SlotSpec("porte-cochere", SlotKind.FIXED, 2.60, 2.60, 2.60, rigid=True)

# a second, tighter vocabulary
END2 = SlotSpec("end2", SlotKind.FLEXIBLE, 0.20, 0.40, 0.70, elasticity=3.0)
BAY2 = SlotSpec("bay2", SlotKind.REPEATING, 2.20, 2.40, 2.75)
SPECIAL2 = SlotSpec("sp2", SlotKind.FLEXIBLE, 0.50, 0.90, 1.40)

RESULTS: dict[str, tuple[bool, str]] = {}


def bounds_of(name, end, bay, special, fixed):
    m = {end.name: end, bay.name: bay}
    if special is not None:
        m[special.name] = special
    for _, s in fixed:
        m[s.name] = s
    return m


def check_result(budget, res, specmap):
    """Return list of violation strings."""
    v = []
    total = math.fsum(s.width for s in res.slots)
    if abs(total - budget) > 1e-9:
        v.append(f"sum {total!r} != budget {budget!r} (err {total-budget:.3e})")
    if not (res.residual < 1e-9):
        v.append(f"residual {res.residual:.3e} >= 1e-9")
    for s in res.slots:
        spec = specmap.get(s.name)
        if spec is None:
            v.append(f"unknown slot name {s.name!r}")
            continue
        if s.width < spec.minimum - 1e-12 or s.width > spec.maximum + 1e-12:
            v.append(
                f"slot {s.name!r} width {s.width!r} outside "
                f"[{spec.minimum}, {spec.maximum}]"
            )
    # contiguity
    cur = 0.0
    for s in res.slots:
        if abs(s.start - cur) > 1e-9:
            v.append(f"slot {s.name!r} start {s.start} != cursor {cur}")
        cur += s.width
    return v


# ---------------------------------------------------------------- CHECK 1 + 2
def check_1_and_2():
    cases = [
        ("A: end/bay/special", dict(end=END, bay=BAY, special=SPECIAL, fixed=())),
        ("B: no special", dict(end=END, bay=BAY, special=None, fixed=())),
        ("C: rigid carriage door", dict(end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),))),
        ("D: tight vocab + special", dict(end=END2, bay=BAY2, special=SPECIAL2, fixed=())),
        ("E: central_feature+special", dict(end=END, bay=BAY, special=SPECIAL, fixed=(), central_feature=True)),
        ("F: central_feature+door", dict(end=END, bay=BAY, special=SPECIAL, fixed=((2, DOOR),), central_feature=True)),
    ]
    all_ok = True
    lines = []
    for label, kw in cases:
        fixed = kw.get("fixed", ())
        specmap = bounds_of(label, kw["end"], kw["bay"], kw.get("special"), fixed)
        n_raise = 0
        raised_widths = []
        viol = 0
        viol_examples = []
        door_drift = []
        for w in WIDTHS:
            try:
                res = solve(w, **kw)
            except FitInfeasible as e:
                n_raise += 1
                if len(raised_widths) < 200:
                    raised_widths.append(w)
                continue
            except Exception as e:  # noqa
                n_raise += 1
                raised_widths.append((w, "NON-FitInfeasible: %r" % e))
                continue
            vs = check_result(w, res, specmap)
            if vs:
                viol += 1
                if len(viol_examples) < 5:
                    viol_examples.append((w, vs))
            # rigid door exactness, strict ==
            for s in res.slots:
                if s.name == DOOR.name and s.width != DOOR.preferred:
                    door_drift.append((w, s.width))
        ok = (n_raise == 0 and viol == 0 and not door_drift)
        all_ok = all_ok and ok
        lines.append(
            f"  {label}: infeasible={n_raise}, bound/sum violations={viol}, "
            f"rigid drift={len(door_drift)}"
        )
        if raised_widths:
            lines.append(f"     infeasible widths (first 30): {raised_widths[:30]}")
            if len(raised_widths) > 30:
                lines.append(f"     ... total {n_raise}")
        for w, vs in viol_examples:
            lines.append(f"     width {w}: {vs}")
        if door_drift:
            lines.append(f"     rigid drift examples: {door_drift[:5]}")
    print("\n=== CHECK 1+2: exact fill / bounds / rigid exactness ===")
    print("\n".join(lines))
    return all_ok, "\n".join(lines)


# ------------------------------------------------------------------- CHECK 3
def check_3_monotonic():
    """Within a fixed bay count, rung must not decrease as slack grows."""
    print("\n=== CHECK 3: ladder monotonicity in slack (per bay count) ===")
    out = []
    all_ok = True
    for label, kw in [
        ("A: with special", dict(end=END, bay=BAY, special=SPECIAL)),
        ("B: no special", dict(end=END, bay=BAY, special=None)),
        ("D: tight vocab", dict(end=END2, bay=BAY2, special=SPECIAL2)),
    ]:
        end = kw["end"]; bay = kw["bay"]
        # bucket by (n_bays used in result)
        buckets: dict[int, list[tuple[float, float, int, float]]] = {}
        for w in WIDTHS:
            try:
                res = solve(w, **kw)
            except FitInfeasible:
                continue
            n = sum(1 for s in res.slots if s.kind is SlotKind.REPEATING)
            slack = w - 2 * end.preferred - n * bay.preferred
            buckets.setdefault(n, []).append((slack, w, res.rung.value, res.rung))
        bad = []
        bad_neg = []
        for n, rows in sorted(buckets.items()):
            rows.sort()
            for (s0, w0, r0, R0), (s1, w1, r1, R1) in zip(rows, rows[1:]):
                if r1 < r0:
                    entry = (n, w0, R0.name, s0, w1, R1.name, s1)
                    if s0 < -1e-9:
                        bad_neg.append(entry)
                    else:
                        bad.append(entry)
        ok = not bad
        all_ok = all_ok and ok
        out.append(f"  {label}: bay-counts seen={sorted(buckets)}; "
                   f"non-monotonic pairs (slack>=0)={len(bad)}; "
                   f"non-monotonic pairs involving negative slack={len(bad_neg)}")
        for e in bad[:6]:
            out.append(f"     n={e[0]}: width {e[1]} slack {e[3]:+.4f} rung {e[2]}"
                       f"  ->  width {e[4]} slack {e[6]:+.4f} rung {e[5]}  (WENT BACKWARDS)")
        for e in bad_neg[:4]:
            out.append(f"     [neg-slack region] n={e[0]}: width {e[1]} slack {e[3]:+.4f} rung {e[2]}"
                       f"  ->  width {e[4]} slack {e[6]:+.4f} rung {e[5]}")
    print("\n".join(out))
    return all_ok, "\n".join(out)


# ------------------------------------------------------------------- CHECK 4
def check_4_parity():
    print("\n=== CHECK 4: parity with central_feature=True ===")
    out = []
    all_ok = True
    for label, kw in [
        ("E: cf + special", dict(end=END, bay=BAY, special=SPECIAL, central_feature=True)),
        ("F: cf + door", dict(end=END, bay=BAY, special=SPECIAL, fixed=((2, DOOR),), central_feature=True)),
        ("G: cf tight vocab", dict(end=END2, bay=BAY2, special=SPECIAL2, central_feature=True)),
    ]:
        seq = []
        for w in WIDTHS:
            try:
                res = solve(w, **kw)
            except FitInfeasible:
                seq.append((w, None))
                continue
            n = sum(1 for s in res.slots if s.kind is SlotKind.REPEATING)
            seq.append((w, n, res.rung))
        jumps = []
        prev = None
        for item in seq:
            if len(item) == 2:
                prev = None
                continue
            w, n, rung = item
            if prev is not None and abs(n - prev) not in (0, 2):
                jumps.append((w, prev, n, rung.name))
            prev = n
        parities = Counter(n for item in seq if len(item) == 3 for n in [item[1]])
        odd = sum(v for k, v in parities.items() if k % 2)
        even = sum(v for k, v in parities.items() if k % 2 == 0)
        ok = not jumps
        all_ok = all_ok and ok
        out.append(f"  {label}: bay-count changes of 1 across sweep = {len(jumps)}; "
                   f"counts seen={sorted(parities)}; odd-count widths={odd}, even-count widths={even}")
        for j in jumps[:8]:
            out.append(f"     width {j[0]}: bay count {j[1]} -> {j[2]} (change of {j[2]-j[1]}), rung {j[3]}")
        if len(jumps) > 8:
            out.append(f"     ... {len(jumps)} total single-step changes")
    print("\n".join(out))
    return all_ok, "\n".join(out)


# --------------------------------------------------------- CHECK 4b (contract)
def check_4b_addmodule_step():
    """CONTRACTS.md wording: on ADD_MODULE the count steps by 2, never 1.

    Probe directly: compare the bay count the solver would naturally take (n0)
    with the count it actually emits when the rung is ADD_MODULE.
    """
    print("\n=== CHECK 4b: ADD_MODULE step size only (contract wording) ===")
    out = []
    ok = True
    end, bay = END, BAY
    for label, cf in [("central_feature=True", True), ("central_feature=False", False)]:
        bad = []
        seen = Counter()
        for w in WIDTHS:
            try:
                res = solve(w, end=end, bay=bay, special=SPECIAL, central_feature=cf)
            except FitInfeasible:
                continue
            if res.rung is not Rung.ADD_MODULE:
                continue
            n = sum(1 for s in res.slots if s.kind is SlotKind.REPEATING)
            n0 = min(max(int(math.floor((w - 2 * end.preferred) / bay.preferred + 1e-9)), 1), 24)
            seen[n - n0] += 1
            if cf and (n - n0) % 2 != 0:
                bad.append((w, n0, n))
        out.append(f"  {label}: ADD_MODULE hits={sum(seen.values())}, step sizes={dict(seen)}")
        for b in bad[:5]:
            out.append(f"     width {b[0]}: n0={b[1]} -> n={b[2]} (odd step)")
        if cf and bad:
            ok = False
    print("\n".join(out))
    return ok, "\n".join(out)


# ------------------------------------------------------------------- CHECK 5
def check_5_centreline():
    print("\n=== CHECK 5: centreline property (interior span == n * bay_width) ===")
    out = []
    all_ok = True
    for label, kw in [
        ("A", dict(end=END, bay=BAY, special=SPECIAL)),
        ("C rigid door", dict(end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),))),
        ("E cf", dict(end=END, bay=BAY, special=SPECIAL, central_feature=True)),
    ]:
        bad = []
        bad_equal = []
        checked = 0
        for w in WIDTHS:
            try:
                res = solve(w, **kw)
            except FitInfeasible:
                continue
            checked += 1
            slots = res.slots
            bays = [s for s in slots if s.kind is SlotKind.REPEATING]
            if not bays:
                continue
            widths = {s.width for s in bays}
            if len(widths) != 1:
                bad_equal.append((w, sorted(widths)))
            bw = bays[0].width
            n = len(bays)
            if abs(math.fsum(s.width for s in bays) - n * bw) > 1e-9:
                bad.append((w, math.fsum(s.width for s in bays), n * bw))
            # interior span = everything between the two end slots
            first, last = slots[0], slots[-1]
            interior = last.start - (first.start + first.width)
            others = math.fsum(
                s.width for s in slots[1:-1] if s.kind is not SlotKind.REPEATING
            )
            if abs(interior - (n * bw + others)) > 1e-9:
                bad.append((w, "interior", interior, n * bw + others))
        ok = not bad and not bad_equal
        all_ok = all_ok and ok
        out.append(f"  {label}: widths checked={checked}; "
                   f"unequal-bay widths={len(bad_equal)}; span mismatches={len(bad)}")
        for b in (bad_equal[:3] + bad[:3]):
            out.append(f"     {b}")
    # explicit sub-case: ends pinned at minimum
    endmin = SlotSpec("endmin", SlotKind.FLEXIBLE, 0.55, 0.55, 0.55)
    hits = 0
    bad = []
    for w in WIDTHS:
        try:
            res = solve(w, end=endmin, bay=BAY, special=SPECIAL)
        except FitInfeasible:
            continue
        hits += 1
        bays = [s for s in res.slots if s.kind is SlotKind.REPEATING]
        if not bays:
            continue
        n = len(bays); bw = bays[0].width
        first, last = res.slots[0], res.slots[-1]
        if abs(first.width - 0.55) > 1e-12 or abs(last.width - 0.55) > 1e-12:
            bad.append((w, "end not at minimum", first.width, last.width))
        interior = last.start - (first.start + first.width)
        others = math.fsum(s.width for s in res.slots[1:-1] if s.kind is not SlotKind.REPEATING)
        if abs(interior - (n * bw + others)) > 1e-9:
            bad.append((w, interior, n * bw + others))
    out.append(f"  ends held at minimum (min==pref==max=0.55): widths solved={hits}, mismatches={len(bad)}")
    for b in bad[:5]:
        out.append(f"     {b}")
    all_ok = all_ok and not bad
    print("\n".join(out))
    return all_ok, "\n".join(out)


# ------------------------------------------------------------------- CHECK 6
def check_6_determinism():
    print("\n=== CHECK 6: determinism (100 identical solves) ===")
    out = []
    ok = True
    for w in (7.35, 12.0, 18.65, 23.10, 31.45, 39.95):
        base = None
        for i in range(100):
            r = solve(w, end=END, bay=BAY, special=SPECIAL, fixed=((1, DOOR),), central_feature=False)
            key = (tuple((s.name, s.kind, s.start, s.width, s.is_special) for s in r.slots),
                   r.rung, r.account, r.residual)
            if base is None:
                base = key
            elif key != base:
                ok = False
                out.append(f"  width {w}: run {i} differs from run 0")
                break
    out.append(f"  100 repeats x 6 widths: identical = {ok}")
    print("\n".join(out))
    return ok, "\n".join(out)


if __name__ == "__main__":
    r1 = check_1_and_2()
    r3 = check_3_monotonic()
    r4 = check_4_parity()
    r4b = check_4b_addmodule_step()
    r5 = check_5_centreline()
    r6 = check_6_determinism()
    print("\n=== SUMMARY ===")
    for name, (ok, _) in [
        ("1+2 fill/bounds/rigid", r1), ("3 monotonic", r3), ("4 parity(sweep)", r4),
        ("4b ADD_MODULE step", r4b), ("5 centreline", r5), ("6 determinism", r6),
    ]:
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
