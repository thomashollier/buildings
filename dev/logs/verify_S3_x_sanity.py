"""Extra adversarial checks the gate does not name but S3 must satisfy."""
import sys, itertools, math, collections
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure
from buildings.quantity import Kind, Prop, scale_for_class
from buildings.solver.fitting import FitInfeasible
import buildings.typologies.paris.reglement as R

bad=collections.Counter(); examples={}
def flag(tag, ctx):
    bad[tag]+=1; examples.setdefault(tag, ctx)

n=0
for y in [1790,1800,1858,1860,1870,1883,1885,1900,1910,1930]:
 for k in BuildingClass:
  for g in GroundProgramme:
   for sw in [6.0,7.8,7.9,9.7,9.8,12.0,20.0,20.1,26.0,40.0]:
    for pw in [8.0,9.3,10.0,12.4,15.0,18.7,26.0]:
     site=SiteContext(street_width=sw,parcel_width=pw,parcel_depth=15.0,year=y,klass=k,ground=g)
     try: grid=solve_structure(site)
     except FitInfeasible: flag("FitInfeasible",(y,k.value,g.value,sw,pw)); continue
     n+=1
     st=grid.storeys; by=grid.bays
     # contiguity + origin
     if abs(st[0].start)>1e-12: flag("storeys don't start at 0",(y,k.value,g.value,sw,pw,st[0].start))
     for a,b in zip(st,st[1:]):
        if abs(a.start+a.width-b.start)>1e-9: flag("storey gap/overlap",(y,k.value,g.value,sw,pw))
     for a,b in zip(by,by[1:]):
        if abs(a.start+a.width-b.start)>1e-9: flag("bay gap/overlap",(y,k.value,g.value,sw,pw))
     if abs(math.fsum(s.width for s in by)-pw)>1e-9: flag("bays != parcel_width",(y,k.value,g.value,sw,pw))
     # built height vs ceiling
     ceil=float(grid.cornice_height)
     if grid.built_height > ceil+1e-9: flag("built exceeds legal ceiling",(y,k.value,g.value,sw,pw,grid.built_height,ceil))
     # built height must equal ceiling*fraction after taper (sum preserved)
     if abs(grid.built_height - ceil*{"modest":.74,"ordinary":.85,"comfortable":.93,"grand":.99}[k.value])>1e-6:
        flag("taper changed the total",(y,k.value,g.value,sw,pw,grid.built_height))
     # monotone taper over the typical band
     typ=[s for s in st if s.name=="storey"]
     for a,b in zip(typ,typ[1:]):
        if b.width > a.width+1e-9: flag("typical storey taller than one below",(y,k.value,g.value,sw,pw,[round(t.width,3) for t in typ]))
     # regulatory storey minimum honoured by EVERY storey
     reg=R.get_reglement(R.era_for_year(y))
     mn = reg.min_floor_height
     for s in st:
        if mn>0 and s.width < mn-1e-9 and not s.is_special and s.name=="storey":
            flag("typical storey below reg minimum",(y,k.value,g.value,sw,pw,s.width,mn))
        if s.width < 1.79: flag("storey under 1.79 m",(y,k.value,g.value,sw,pw,s.name,s.width))
     # taper must not push a storey above the declared max
     smax=max(float(scale_for_class(Prop(3.55,"x"),k)), float(scale_for_class(Prop(3.10,"x"),k)))
     for s in typ:
        if s.width > smax+1e-9: flag("tapered storey ABOVE declared max",(y,k.value,g.value,sw,pw,round(s.width,3),round(smax,3)))
     # envelope facade height agrees with cornice
     if abs(grid.envelope.facade_height-ceil)>1e-9: flag("envelope.facade_height != cornice",(y,k.value,g.value,sw,pw))
     # cornice quantity is REGULATORY with a citation
     if grid.cornice_height.kind is not Kind.REGULATORY or not grid.cornice_height.why.strip():
        flag("cornice not a cited Reg",(y,k.value,g.value,sw,pw))
     if not grid.account: flag("empty account",(y,k.value,g.value,sw,pw))
     # interstitial count
     ints=[s for s in st if s.name=="interstitial"]
     if len(ints)>1: flag("more than one interstitial",(y,k.value,g.value,sw,pw,len(ints)))

print("grids built:", n)
print("\n== findings ==")
if not bad: print("  none")
for t,c in bad.most_common():
    print(f"  {t}: {c}   e.g. {examples[t]}")
