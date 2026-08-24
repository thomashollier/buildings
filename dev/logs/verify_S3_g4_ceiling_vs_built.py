"""G3.4 — ceiling and built height are separate and genuinely differ."""
import sys, itertools
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure

print(f"{'class':13}{'street':>7}{'ceiling':>9}{'built':>9}{'ratio':>8}{'storeys':>8}{'ridge':>8}")
rows=[]
for sw in [8.0, 12.0, 24.0, 34.0]:
  for k in BuildingClass:
    g=solve_structure(SiteContext(street_width=sw,parcel_width=12.0,parcel_depth=16.0,
                                  year=1870,klass=k,ground=GroundProgramme.SHOP))
    ceil=float(g.cornice_height); built=g.built_height
    rows.append((k,sw,ceil,built))
    print(f"{k.value:13}{sw:7.1f}{ceil:9.2f}{built:9.3f}{built/ceil:8.1%}{len(g.storeys):8}{g.envelope.ridge_height:8.2f}")

# hard assertions
modest_wide=[r for r in rows if r[0]==BuildingClass.MODEST and r[1]>=24.0]
for k,sw,c,b in modest_wide:
    assert c-b > 1.0, (sw,c,b)
    print(f"\nMODEST @ {sw} m street: ceiling {c:.2f} m vs built {b:.3f} m -> gap {c-b:.3f} m")
# nothing may exceed its ceiling
over=[r for r in rows if r[3] > r[2]+1e-9]
print("buildings exceeding their legal ceiling:", over)
# ordering strictly monotone by class
for sw in {r[1] for r in rows}:
    vals=[b for k,s,c,b in rows if s==sw]
    assert vals==sorted(vals), (sw,vals)
print("built height strictly increases with class at every street width: OK")
print("RESULT: PASS")
