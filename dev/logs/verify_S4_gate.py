"""Independent S4 gate verification. Written by the verifier, not the implementer."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("/Users/thomas/Documents/claude/buildings/src")))

from buildings.quantity import Reg
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris.reglement import Era, GabaritEnvelope, RoofEnvelope
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris.structure import Grid, solve_structure

RESULTS = []


def check(name, ok, evidence):
    RESULTS.append((name, ok, evidence))
    print(("PASS " if ok else "FAIL ") + name)
    print("      " + str(evidence))


def stack(heights, names=None):
    names = names or ["storey"] * len(heights)
    out = []
    c = 0.0
    for n, h in zip(names, heights):
        out.append(PlacedSlot(name=n, kind=SlotKind.REPEATING, start=c, width=h))
        c += h
    return tuple(out)


def grid(storeys, cornice):
    env = GabaritEnvelope(
        era=Era.SECOND_EMPIRE, street_width=18.0, facade_height=cornice,
        roof_envelope=RoofEnvelope.DIAGONAL_45, arc_radius=0.0,
        ridge_height=6.0, parcel_depth=15.0,
    )
    return Grid(storeys=storeys, bays=(), cornice_height=Reg(cornice, "verifier fixture"),
                envelope=env, account=())


def roles_of(g):
    return [rs.role.value for rs in assign_roles(g).storeys]


print("=" * 70)
print("G4.1  Same rules, different heights: 5-storey and 9-storey")
print("=" * 70)

# 5-storey: tall ground (4.2), mezzanine (2.0), then 3.4, 3.1, 2.9. cornice above all.
h5 = [4.2, 2.0, 3.4, 3.1, 2.9]
g5 = grid(stack(h5), cornice=100.0)
r5 = roles_of(g5)
print("heights", h5, "->", r5)

h9 = [4.2, 2.0, 3.4, 3.3, 3.2, 3.1, 3.0, 2.9, 2.8]
g9 = grid(stack(h9), cornice=100.0)
r9 = roles_of(g9)
print("heights", h9, "->", r9)

exp5 = ["base", "mezzanine", "principal", "upper", "upper"]
exp9 = ["base", "mezzanine", "principal", "upper", "upper", "upper", "upper", "upper", "upper"]
check("G4.1 five-storey roles", r5 == exp5, f"{h5} -> {r5} (expected {exp5})")
check("G4.1 nine-storey roles", r9 == exp9, f"{h9} -> {r9} (expected {exp9})")

# ranks
ranks9 = [rs.rank_from_principal for rs in assign_roles(g9).storeys]
print("ranks9:", ranks9)
check("G4.1 ranks increase upward from principal (0 at principal)",
      ranks9 == [-2, -1, 0, 1, 2, 3, 4, 5, 6], f"ranks={ranks9}")

# Sweep: many stack lengths, roles must be derived not enumerated
sweep_ok = True
sweep_detail = []
for n in range(2, 15):
    hs = [4.5] + [3.5 - 0.05 * i for i in range(n - 1)]
    r = roles_of(grid(stack(hs), cornice=1000.0))
    exp = ["base", "principal"] + ["upper"] * (n - 2)
    if r != exp:
        sweep_ok = False
        sweep_detail.append((n, r, exp))
sweep_detail = sweep_detail or [("n=2..14 all correct")]
check("G4.1 sweep n=2..14 base+principal+uppers", sweep_ok, str(sweep_detail))

print()
print("=" * 70)
print("G4.2  Base exclusion: tallest slot overall IS the ground floor")
print("=" * 70)
hb = [5.5, 3.4, 3.2, 3.0]  # ground is strictly the tallest
gb = grid(stack(hb), cornice=100.0)
rb = assign_roles(gb)
rb_roles = [rs.role.value for rs in rb.storeys]
tallest_idx = max(range(len(hb)), key=lambda i: hb[i])
principal_idx = [i for i, rs in enumerate(rb.storeys) if rs.role is Role.PRINCIPAL]
print("heights", hb, "->", rb_roles)
print("tallest index:", tallest_idx, " principal index:", principal_idx)
ok = (rb.storeys[0].role is Role.BASE and principal_idx == [1] and tallest_idx == 0)
check("G4.2 tall ground floor does NOT get PRINCIPAL", ok,
      f"heights={hb}; tallest slot index={tallest_idx} (h={hb[0]}); "
      f"role[0]={rb_roles[0]}; PRINCIPAL at index {principal_idx[0] if principal_idx else None} "
      f"(h={hb[principal_idx[0]] if principal_idx else None})")

# Non-trivial: verify the exclusion actually bites by removing it (mutation)
import buildings.typologies.paris.roles as rmod
src = Path(rmod.__file__).read_text()
mutated = src.replace("if i != base_idx and i != mezzanine_idx and not attic_flags[i]",
                      "if i != mezzanine_idx and not attic_flags[i]")
mut_applied = mutated != src
ns = {}
exec(compile(mutated, "roles_mut.py", "exec"), ns)
mut_roles = [rs.role.value for rs in ns["assign_roles"](gb).storeys]
print("mutated (base exclusion removed) ->", mut_roles)
check("G4.2 mutation test: removing base exclusion changes the answer",
      mut_applied and mut_roles != rb_roles,
      f"original={rb_roles}  mutated={mut_roles}  (mutation applied={mut_applied})")

print()
print("=" * 70)
print("G4.3  Tallest, not first-tall; ties -> lowest")
print("=" * 70)
# first tall storey (3.4 at idx1) is NOT the tallest (3.9 at idx3)
ht = [4.0, 3.4, 3.2, 3.9, 3.0]
gt = grid(stack(ht), cornice=100.0)
rt = assign_roles(gt)
pi = [i for i, rs in enumerate(rt.storeys) if rs.role is Role.PRINCIPAL]
print("heights", ht, "->", [rs.role.value for rs in rt.storeys])
check("G4.3 principal lands on the tallest (idx3, 3.9), not the first tall (idx1, 3.4)",
      pi == [3], f"heights={ht}; PRINCIPAL index={pi}; h at principal={ht[pi[0]] if pi else None}")

# ties -> lowest
hti = [4.0, 3.5, 3.2, 3.5, 3.0]
gti = grid(stack(hti), cornice=100.0)
rti = assign_roles(gti)
pit = [i for i, rs in enumerate(rti.storeys) if rs.role is Role.PRINCIPAL]
print("heights", hti, "->", [rs.role.value for rs in rti.storeys])
check("G4.3 tie between idx1 and idx3 (both 3.5) breaks to the LOWEST (idx1)",
      pit == [1], f"heights={hti}; PRINCIPAL index={pit}")

# tie including a float-noise variant
htf = [4.0, 3.5, 3.2, 3.5 + 1e-12, 3.0]
pitf = [i for i, rs in enumerate(assign_roles(grid(stack(htf), 100.0)).storeys)
        if rs.role is Role.PRINCIPAL]
check("G4.3 near-tie within eps also breaks to the lowest",
      pitf == [1], f"heights={htf}; PRINCIPAL index={pitf}")

# exactly one principal always
multi = [i for i, rs in enumerate(rti.storeys) if rs.role is Role.PRINCIPAL]
check("G4.3 exactly one PRINCIPAL", len(multi) == 1, f"count={len(multi)}")

print()
print("=" * 70)
print("G4.4  Mezzanine removal moves the principal BY ITSELF")
print("=" * 70)
with_mezz = [4.0, 2.0, 3.4, 3.2, 3.0]
without = [4.0, 3.4, 3.2, 3.0]
gm = grid(stack(with_mezz), cornice=100.0)
gn = grid(stack(without), cornice=100.0)
rm = assign_roles(gm)
rn = assign_roles(gn)
pm = next(rs for rs in rm.storeys if rs.role is Role.PRINCIPAL)
pn = next(rs for rs in rn.storeys if rs.role is Role.PRINCIPAL)
print("with mezzanine   :", [rs.role.value for rs in rm.storeys],
      "principal idx", pm.index_from_bottom, "level above pavement", pm.slot.start)
print("without mezzanine:", [rs.role.value for rs in rn.storeys],
      "principal idx", pn.index_from_bottom, "level above pavement", pn.slot.start)
check("G4.4 principal index shifts down by exactly 1 when the mezzanine is removed",
      pm.index_from_bottom - pn.index_from_bottom == 1,
      f"with={pm.index_from_bottom} without={pn.index_from_bottom}")
check("G4.4 principal LEVEL ABOVE PAVEMENT drops by the mezzanine height (2.0 m)",
      abs((pm.slot.start - pn.slot.start) - 2.0) < 1e-9,
      f"with={pm.slot.start:.3f} m, without={pn.slot.start:.3f} m, delta={pm.slot.start - pn.slot.start:.3f} m "
      f"(mezzanine height 2.0 m)")

print()
print("=" * 70)
print("G4.5  Phase isolation (I1)")
print("=" * 70)
import ast
tree = ast.parse(src)
imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports += [a.name for a in node.names]
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module or "")
print("imports:", imports)
banned = [m for m in imports if any(b in (m or "") for b in
          ("site", "rng", "reglement", "chronology", "compose", "qualify", "terminate"))]
check("G4.5 no import of site/rng/reglement/chronology", not banned,
      f"module imports = {imports}; banned hits = {banned}")

# identifier-level scan of code (excluding docstrings/comments)
code_names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Name):
        code_names.add(node.id)
    if isinstance(node, ast.Attribute):
        code_names.add(node.attr)
bad_ids = sorted(n for n in code_names if n.lower() in
                 {"sitecontext", "year", "klass", "buildingclass", "reglement", "era",
                  "chronology", "decisionstream", "seed", "street_width"})
check("G4.5 no SiteContext/year/klass/era identifiers used in code", not bad_ids,
      f"suspicious identifiers in AST = {bad_ids or 'none'}")

print()
print("=" * 70)
print("G4.1b  Hardcoded position enumeration scan")
print("=" * 70)
import re
lines = src.splitlines()
hits = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith("#"):
        continue
    for pat in (r"==\s*[2-9]\b", r"storeys\[\s*[2-9]\s*\]", r"floor_\d", r"\[\s*[2-9]\s*\]"):
        if re.search(pat, line):
            hits.append((i, stripped))
print("index-literal hits (excluding 0/1):", hits)
check("G4.1b no enumeration of positions >= 2", not hits, f"hits={hits or 'none'}")

# report all integer literals used as indices
idx_lits = []
for node in ast.walk(tree):
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        idx_lits.append(node.slice.value)
print("literal subscript constants used anywhere:", sorted(set(idx_lits)))

print()
print("=" * 70)
print("EXTRA  Real solve_structure grids")
print("=" * 70)
for klass in BuildingClass:
    for ground in (GroundProgramme.RESIDENTIAL, GroundProgramme.SHOP, GroundProgramme.CARRIAGE):
        for sw in (8.0, 12.0, 18.0, 26.0):
            site = SiteContext(street_width=sw, parcel_width=14.0, parcel_depth=15.0,
                               year=1875, klass=klass, ground=ground)
            g = solve_structure(site)
            rg = assign_roles(g)
            rs = [x.role.value for x in rg.storeys]
            hs = [round(x.slot.width, 2) for x in rg.storeys]
            print(f"{klass.value:12s} {ground.value:12s} sw={sw:5.1f} n={len(rs)} "
                  f"cornice={float(g.cornice_height):5.2f} built={g.built_height:5.2f} {hs} -> {rs}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
for n, ok, ev in RESULTS:
    print(("PASS" if ok else "FAIL"), n)
print("ALL PASSED" if all(r[1] for r in RESULTS) else "SOME FAILED")
