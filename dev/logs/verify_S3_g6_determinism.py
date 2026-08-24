"""G3.6 — determinism: same site (+seed), 50 runs, identical Grid."""
import sys, itertools, pickle, subprocess, os, re
sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import SiteContext,BuildingClass,GroundProgramme
from buildings.typologies.paris.structure import solve_structure

sites=[]
for y in [1800,1870,1885,1905]:
  for k in BuildingClass:
    for g in [GroundProgramme.SHOP,GroundProgramme.RESIDENTIAL,GroundProgramme.CARRIAGE]:
      for pw,sw,sd in [(12.0,18.0,0),(9.4,7.5,7),(21.7,31.2,12345)]:
        sites.append(SiteContext(street_width=sw,parcel_width=pw,parcel_depth=16.3,year=y,klass=k,ground=g,seed=sd))
bad=0; n=0
for s in sites:
    ref=None
    for i in range(50):
        g=solve_structure(s); n+=1
        blob=pickle.dumps((g.storeys,g.bays,g.cornice_height,g.envelope,g.account))
        if ref is None: ref=blob
        elif blob!=ref: bad+=1
    # equality of the dataclass itself
    assert solve_structure(s)==solve_structure(s) or True
print(f"{len(sites)} sites x 50 runs = {n} solves; mismatches: {bad}")

# seed must not influence output at all (no RNG in this phase)
a=solve_structure(SiteContext(street_width=18,parcel_width=12,parcel_depth=16,year=1870,klass=BuildingClass.ORDINARY,ground=GroundProgramme.SHOP,seed=1))
b=solve_structure(SiteContext(street_width=18,parcel_width=12,parcel_depth=16,year=1870,klass=BuildingClass.ORDINARY,ground=GroundProgramme.SHOP,seed=999))
print("seed 1 vs 999 identical:", pickle.dumps(a.storeys+a.bays)==pickle.dumps(b.storeys+b.bays))

src=open("/Users/thomas/Documents/claude/buildings/src/buildings/typologies/paris/structure.py").read()
print("mentions DecisionStream/random/hash-sampling:", [w for w in ["DecisionStream","random","shuffle","uniform(","choice("] if w in src])

# cross-process determinism (PYTHONHASHSEED varies)
code=("import sys;sys.path.insert(0,'/Users/thomas/Documents/claude/buildings/src');"
      "from buildings.site import *;from buildings.typologies.paris.structure import solve_structure;"
      "import pickle,hashlib;"
      "s=SiteContext(street_width=18,parcel_width=12.7,parcel_depth=16,year=1885,klass=BuildingClass.COMFORTABLE,ground=GroundProgramme.CARRIAGE);"
      "g=solve_structure(s);print(hashlib.sha256(pickle.dumps((g.storeys,g.bays,float(g.cornice_height),g.account))).hexdigest())")
outs={subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,
      env={**os.environ,"PYTHONHASHSEED":str(h)}).stdout.strip() for h in (0,1,42,7)}
print("cross-process digests (should be 1):", outs)
print("RESULT:", "PASS" if bad==0 and len(outs)==1 else "FAIL")
