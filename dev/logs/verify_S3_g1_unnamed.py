"""G3.1 — the grid is unnamed."""
import dataclasses, re, sys, itertools
sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext, BuildingClass, GroundProgramme
from buildings.typologies.paris.structure import Grid, solve_structure

ROLE_WORDS = ["base","mezzanine","principal","noble","upper","attic","entresol","piano"]

print("== Grid fields ==")
for f in dataclasses.fields(Grid):
    print("  ", f.name, ":", f.type)
print("Grid properties:", [n for n,v in vars(Grid).items() if isinstance(v, property)])

bad = []
for f in dataclasses.fields(Grid):
    for w in ROLE_WORDS:
        if w in f.name.lower():
            bad.append(("field", f.name, w))

# runtime: every string value anywhere in a produced Grid
years = [1800, 1860, 1870, 1885, 1895, 1905]
strs_seen = set()
n = 0
for y, k, g, sw, pw in itertools.product(
        years, list(BuildingClass), list(GroundProgramme), [8.0, 12.0, 18.0, 26.0], [8.0, 9.0, 13.0, 22.0]):
    site = SiteContext(street_width=sw, parcel_width=pw, parcel_depth=16.0, year=y, klass=k, ground=g)
    grid = solve_structure(site)
    n += 1
    for s in grid.storeys + grid.bays:
        strs_seen.add(("slotname", s.name))
    for a in grid.account:
        strs_seen.add(("account", a))
    strs_seen.add(("citation", grid.cornice_height.why))

print(f"\ngrids built: {n}")
print("distinct slot names:", sorted({v for t,v in strs_seen if t=='slotname'}))
for t, v in sorted(strs_seen):
    low = v.lower()
    for w in ROLE_WORDS:
        if re.search(r"\b"+w, low):
            bad.append((t, v, w))

print("\n== runtime role-word hits ==")
for b in bad: print("  HIT", b)
if not bad: print("  none")

# source grep outside comments/docstrings
import io, tokenize
src = "/Users/thomas/Documents/claude/buildings/src/buildings/typologies/paris/structure.py"
code_hits = []
with open(src) as fh:
    toks = list(tokenize.generate_tokens(fh.readline))
for tok in toks:
    if tok.type in (tokenize.COMMENT,):
        continue
    if tok.type == tokenize.STRING and tok.start[0] < 45:  # module docstring region
        continue
    low = tok.string.lower()
    for w in ROLE_WORDS:
        if re.search(r"\b"+w, low):
            code_hits.append((tok.start[0], tokenize.tok_name[tok.type], tok.string[:90], w))
print("\n== source hits (non-comment, non-module-docstring tokens) ==")
for h in code_hits: print("  ", h)
if not code_hits: print("   none")
print("\nRESULT:", "PASS" if not bad and not code_hits else "FAIL")
