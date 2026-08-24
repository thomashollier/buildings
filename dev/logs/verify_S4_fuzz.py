"""Fuzz S4 invariants + check whether the M4 survivor is an equivalent mutant."""
from __future__ import annotations
import random, sys
from pathlib import Path

sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")
from buildings.quantity import Reg
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris.reglement import Era, GabaritEnvelope, RoofEnvelope
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris.structure import Grid
import buildings.typologies.paris.roles as rmod

src = Path(rmod.__file__).read_text()
m4 = src.replace("if i != base_idx and i != mezzanine_idx and not attic_flags[i]",
                 "if i != base_idx and not attic_flags[i]", 1)
assert m4 != src
ns = {}
exec(compile(m4, "m4.py", "exec"), ns)
assign_m4 = ns["assign_roles"]

def mk(hs, cornice):
    env = GabaritEnvelope(era=Era.SECOND_EMPIRE, street_width=18.0, facade_height=cornice,
                          roof_envelope=RoofEnvelope.DIAGONAL_45, arc_radius=0.0,
                          ridge_height=6.0, parcel_depth=15.0)
    slots, c = [], 0.0
    for h in hs:
        slots.append(PlacedSlot("storey", SlotKind.REPEATING, c, h)); c += h
    return Grid(tuple(slots), (), Reg(cornice, "fx"), env, ())

rng = random.Random(12345)
bad = []
m4_diff = 0
mezz_seen = attic_seen = 0
N = 200000
for t in range(N):
    n = rng.randint(1, 12)
    hs = [round(rng.uniform(1.5, 6.0), 2) for _ in range(n)]
    total = sum(hs)
    cornice = round(rng.uniform(0.0, total * 1.2), 2)
    g = mk(hs, cornice)
    rg = assign_roles(g)
    roles = [r.role for r in rg.storeys]

    if roles.count(Role.BASE) != 1:
        bad.append(("BASE count", hs, cornice, [r.value for r in roles])); continue
    if roles.count(Role.MEZZANINE) > 1:
        bad.append(("MEZZ count", hs, cornice, [r.value for r in roles])); continue
    if roles.count(Role.PRINCIPAL) > 1:
        bad.append(("PRINC count", hs, cornice, [r.value for r in roles])); continue
    if roles[0] is not Role.BASE:
        bad.append(("base not bottom", hs, cornice, [r.value for r in roles])); continue
    if Role.MEZZANINE in roles:
        mezz_seen += 1
        if roles.index(Role.MEZZANINE) != 1:
            bad.append(("mezz not idx1", hs, cornice, [r.value for r in roles])); continue
    if Role.ATTIC in roles:
        attic_seen += 1
    # principal must genuinely be the tallest of the eligible pool, lowest on tie
    if Role.PRINCIPAL in roles:
        p = roles.index(Role.PRINCIPAL)
        elig = [i for i in range(n) if roles[i] in (Role.PRINCIPAL, Role.UPPER)]
        mx = max(hs[i] for i in elig)
        if abs(hs[p] - mx) > 1e-9:
            bad.append(("not tallest", hs, cornice, [r.value for r in roles])); continue
        lowest = min(i for i in elig if abs(hs[i] - mx) <= 1e-9)
        if p != lowest:
            bad.append(("tie not lowest", hs, cornice, [r.value for r in roles])); continue
        if any(r.rank_from_principal != r.index_from_bottom - p for r in rg.storeys):
            bad.append(("rank", hs, cornice, None)); continue
    for i, r in enumerate(rg.storeys):
        if r.index_from_bottom != i or r.index_from_top != n - 1 - i:
            bad.append(("index", hs, cornice, None)); break
    # attic <=> slot.start >= cornice (except base)
    for i, r in enumerate(rg.storeys):
        expect_attic = i != 0 and r.slot.start >= cornice - 1e-6
        if expect_attic and r.role is not Role.ATTIC:
            bad.append(("attic pred", hs, cornice, [x.role.value for x in rg.storeys])); break
        if r.role is Role.ATTIC and not expect_attic:
            bad.append(("attic pred2", hs, cornice, [x.role.value for x in rg.storeys])); break
    if [r.role.value for r in assign_m4(g).storeys] != [r.value for r in roles]:
        m4_diff += 1
        if m4_diff <= 3:
            print("M4 DIFFERS:", hs, cornice, [r.value for r in roles],
                  [r.role.value for r in assign_m4(g).storeys])

print(f"fuzz cases: {N}")
print(f"invariant violations: {len(bad)}")
for b in bad[:10]:
    print("  ", b)
print(f"cases producing a MEZZANINE: {mezz_seen}")
print(f"cases producing an ATTIC:    {attic_seen}")
print(f"cases where the M4 mutant (no mezzanine exclusion) differs: {m4_diff}"
      f"  -> {'EQUIVALENT MUTANT' if m4_diff == 0 else 'REAL untested behaviour'}")

# determinism
g = mk([4.0, 2.0, 3.4, 3.2, 3.0], 20.0)
a, b = assign_roles(g), assign_roles(g)
print("determinism (same grid twice, equal):", a == b)
