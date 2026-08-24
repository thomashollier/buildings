"""G3.2 — height moves in STEPS, not continuously."""
import sys, itertools
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure

def sweep(year, klass, quant):
    xs=[6.0+0.1*i for i in range(int((40-6)/0.1)+1)]
    out=[]
    for sw in xs:
        g=solve_structure(SiteContext(street_width=round(sw,4),parcel_width=12.0,parcel_depth=16.0,
                                      year=year,klass=klass,ground=GroundProgramme.SHOP))
        out.append((round(sw,4), quant(g)))
    return out

def plateaus(series, tol=1e-9):
    ps=[]
    for x,v in series:
        if not ps or abs(ps[-1][2]-v)>tol: ps.append([x,x,v])
        else: ps[-1][1]=x
    return ps

for year,klass in [(1870,BuildingClass.ORDINARY),(1870,BuildingClass.MODEST),
                   (1800,BuildingClass.ORDINARY),(1895,BuildingClass.GRAND)]:
    for label,q in [("cornice_height(legal)", lambda g: float(g.cornice_height)),
                    ("built_height",          lambda g: round(g.built_height,9)),
                    ("n_storeys",             lambda g: len(g.storeys))]:
        s=sweep(year,klass,q)
        ps=plateaus(s)
        vals=sorted({p[2] for p in ps})
        print(f"\n=== year={year} class={klass.value} {label}: {len(ps)} runs, {len(vals)} distinct values ===")
        for a,b,v in ps: print(f"   {a:5.1f}–{b:5.1f} m  ->  {v}")
