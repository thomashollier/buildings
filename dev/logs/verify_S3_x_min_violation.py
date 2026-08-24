"""Confirmed defect: post-1859 storeys can land BELOW the règlement's 2.60 m
hygiene minimum, because _taper_heights' redistribution pass has no re-clamp."""
import sys, math, collections
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure, _taper_heights
import buildings.typologies.paris.reglement as R
from buildings.solver.fitting import FitInfeasible

site=SiteContext(street_width=9.8,parcel_width=12.0,parcel_depth=15.0,year=1860,
                 klass=BuildingClass.MODEST,ground=GroundProgramme.CARRIAGE)
g=solve_structure(site)
reg=R.get_reglement(R.era_for_year(1860))
print("site:",site)
print("reg.min_floor_height =",reg.min_floor_height,"(",reg.decree,")")
print("storeys:",[(s.name,round(s.width,6)) for s in g.storeys])
print("violating storeys:",[(s.name,s.width) for s in g.storeys if s.name=='storey' and s.width<reg.min_floor_height-1e-9])
print("account line for taper:", [a for a in g.account if a.startswith("taper")])

# scale of the problem across a realistic sweep
viol=[]; tot=0
years=[1860,1865,1870,1875,1880,1885,1890,1900,1910]
for y in years:
 for k in BuildingClass:
  for gp in GroundProgramme:
   for sw in [round(6+0.2*i,2) for i in range(0,171)]:
     try: gr=solve_structure(SiteContext(street_width=sw,parcel_width=12.0,parcel_depth=15.0,year=y,klass=k,ground=gp))
     except FitInfeasible: continue
     tot+=1
     mn=R.get_reglement(R.era_for_year(y)).min_floor_height
     w=[s.width for s in gr.storeys if s.name=='storey']
     if w and min(w)<mn-1e-9: viol.append((y,k.value,gp.value,sw,round(min(w),6),mn))
print(f"\npost-1859 grids checked: {tot}; storeys under the legal minimum: {len(viol)}")
print("worst deficit:", max((v[5]-v[4],v) for v in viol) if viol else None)
print("classes affected:", collections.Counter(v[1] for v in viol))
print("first 5:", viol[:5])

print("\n-- direct probe of the helper's own documented postcondition --")
for n,total,mn in [(6,6*2.61,2.60),(8,8*2.62,2.60),(5,5*2.25,2.20),(10,10*2.63,2.60)]:
    h=_taper_heights(n,total,mn,0.965)
    print(f"  _taper_heights(n={n}, total={total:.2f}, minimum={mn}) -> min {min(h):.4f}  "
          f"{'VIOLATES >=minimum' if min(h)<mn-1e-9 else 'ok'}   sum ok={abs(math.fsum(h)-total)<1e-9}")
