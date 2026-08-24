import sys
sys.path.insert(0, "/Users/thomas/Documents/claude/buildings/src")
from buildings.typologies.paris import reglement_adapter as A
from buildings.quantity import Kind

print("--- every Reg-returning accessor, all 4 eras ---")
bad = []
for era in A.Era:
    env = A.compute_envelope(30.0, era, parcel_depth=40.0)
    for name, q in [("total_height", env.total_height),
                    ("setback_at(2)", env.setback_at(2.0)),
                    ("max_height_for_setback(1)", env.max_height_for_setback(1.0))]:
        ok = q.kind == Kind.REGULATORY and q.why.strip() and "unknown" not in q.why.lower()
        if not ok: bad.append((era.name, name, q.why))
        print(f"{era.name:14s} {name:26s} value={float(q):8.3f}  why={q.why!r}")
    br = A.balcony_rule([0.0, 7.0, 10.0], era)
    for name, q in [("balcony.max_projection", br.max_projection), ("balcony.min_height", br.min_height)]:
        print(f"{era.name:14s} {name:26s} value={float(q):8.3f}  why={q.why!r}")
        if not q.why.strip() or "unknown" in q.why.lower(): bad.append((era.name, name, q.why))
    orl = A.oriel_rule([0.0,4.0,7.0,10.0,13.0], ["rdc","1","2","3","4"], 20.0, era)
    q = orl.max_projection
    print(f"{era.name:14s} {'oriel.max_projection':26s} value={float(q):8.3f}  why={q.why!r}")
    if not q.why.strip() or "unknown" in q.why.lower(): bad.append((era.name, "oriel", q.why))

print("\nPLACEHOLDER/EMPTY CITATIONS:", bad)

print("\n--- string-era path: does 'Unknown era' become reachable? ---")
env = A.compute_envelope(30.0, "alphand", parcel_depth=40.0)
print("era type:", type(env.era), "value:", env.era, "citation:", env.total_height.why)

print("\n--- reachability of the 'Unknown era' fallback ---")
print("Era members:", [e.name for e in A.Era])
print("citation_map covers all:", set(A.Era) == {A.Era.ROYAL, A.Era.SECOND_EMPIRE, A.Era.ALPHAND, A.Era.BONNIER})

print("\n--- adapter public-surface check vs CONTRACTS.md ---")
required = ["Era","RoofEnvelope","Reglement","GabaritEnvelope","BalconyRule","OrielRule",
            "era_for_year","get_reglement","compute_envelope","balcony_rule","oriel_rule"]
for r in required:
    print(f"  {r:20s} {'OK' if hasattr(A,r) else 'MISSING'}")
env = A.compute_envelope(30.0, A.Era.ALPHAND, parcel_depth=40.0)
for m in ["total_height","setback_at","max_height_for_setback","slope_profile","mansard_angles"]:
    print(f"  GabaritEnvelope.{m:24s} {'OK' if hasattr(env,m) else 'MISSING'}")
print("  slope_profile ->", env.slope_profile(4))
print("  mansard_angles ->", env.mansard_angles())
reg = A.get_reglement(A.Era.ALPHAND)
print("  Reglement.facade_height_limit(30) ->", reg.facade_height_limit(30.0), type(reg.facade_height_limit(30.0)).__name__)
print("  Reglement.arc_radius(30) ->", reg.arc_radius(30.0), type(reg.arc_radius(30.0)).__name__)
