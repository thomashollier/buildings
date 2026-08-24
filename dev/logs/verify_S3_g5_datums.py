"""G3.5 — datums are received, not resampled (I2)."""
import sys, types
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure
import buildings.typologies.paris.reglement as R

def D(sw,ch):
    return types.SimpleNamespace(street_width=sw, cornice_height=ch,
                                 string_course_levels=(4.0,8.0), balcony_levels=(12.0,))

ok=True
cases=[(1870,8.0,18.37),(1870,30.0,12.05),(1800,12.0,16.66),(1895,22.0,19.13),(1905,9.0,13.3333333)]
for year,sw_site,ch in cases:
    site=SiteContext(street_width=sw_site,parcel_width=12.0,parcel_depth=16.0,year=year,
                     klass=BuildingClass.ORDINARY,ground=GroundProgramme.SHOP)
    for dsw in [sw_site, sw_site+7.0]:
        g=solve_structure(site, D(dsw, ch))
        got=float(g.cornice_height)
        recomputed=R.get_reglement(R.era_for_year(year)).facade_height_limit(sw_site)
        exact = (got==ch)
        env_ok = (g.envelope.facade_height==ch)
        print(f"year={year} site.sw={sw_site} datum.sw={dsw} datum.ch={ch}: "
              f"grid.cornice={got!r} exact={exact} envelope.facade_height={g.envelope.facade_height!r} "
              f"env_matches={env_ok}  (recomputed-from-site would be {recomputed})")
        if not exact or not env_ok: ok=False

# datum must also drive envelope geometry from datum street width, not site's
site=SiteContext(street_width=8.0,parcel_width=12.0,parcel_depth=16.0,year=1895,
                 klass=BuildingClass.ORDINARY,ground=GroundProgramme.SHOP)
a=solve_structure(site, D(30.0, 20.0))
b=solve_structure(site, D(8.0, 20.0))
print("\nenvelope depends on datum street_width, not site's:", a.envelope != b.envelope,
      "| ridge a", round(a.envelope.ridge_height,3), "ridge b", round(b.envelope.ridge_height,3))

# no datums -> recomputed
g=solve_structure(site)
print("no datums: cornice", float(g.cornice_height), "== facade_height_limit(8.0) ",
      float(g.cornice_height)==R.get_reglement(R.era_for_year(1895)).facade_height_limit(8.0))
print("citation with datums:", solve_structure(site, D(30.0,20.0)).cornice_height.why)
print("RESULT:", "PASS" if ok else "FAIL")
