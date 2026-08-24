"""G3.3 — one bay solve per building."""
import sys, ast, itertools, pickle
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure
import buildings.solver.fitting as fitting

src="/Users/thomas/Documents/claude/buildings/src/buildings/typologies/paris/structure.py"
tree=ast.parse(open(src).read())
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and
       ((isinstance(n.func,ast.Name) and n.func.id=="solve") or
        (isinstance(n.func,ast.Attribute) and n.func.attr=="solve"))]
print("static solve() call sites in structure.py:", [c.lineno for c in calls])

# dynamic: count actual solve() invocations per solve_structure call
orig=fitting.solve
log=[]
def spy(budget,**kw):
    log.append((budget, kw["bay"].name, kw["end"].name))
    return orig(budget,**kw)
import buildings.typologies.paris.structure as S
S.solve=spy

worst=0
for y in [1800,1870,1885,1905]:
  for k in BuildingClass:
    for g in GroundProgramme:
      for pw in [8.0,10.5,13.7,22.3]:
        log.clear()
        grid=S.solve_structure(SiteContext(street_width=18.0,parcel_width=pw,parcel_depth=16.0,year=y,klass=k,ground=g))
        horiz=[l for l in log if abs(l[0]-pw)<1e-9]
        worst=max(worst,len(log))
        assert len(log)==2, (y,k,g,pw,log)
        assert len(horiz)==1, (y,k,g,pw,log)
        # bays is ONE shared tuple; storeys carry no per-storey bay grid
        assert not any(hasattr(s,"bays") for s in grid.storeys)
        b1=pickle.dumps(grid.bays)
        for _ in grid.storeys:
            assert pickle.dumps(grid.bays)==b1
print("dynamic: exactly 2 solve() calls per building (1 vertical + 1 horizontal); max seen", worst)
print("Grid.bays is a single shared tuple; PlacedSlot fields:", [f for f in __import__('dataclasses').fields(fitting.PlacedSlot)])
print("RESULT: PASS")
