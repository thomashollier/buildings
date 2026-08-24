"""Independent S5 gate verification. Throwaway."""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.site import BuildingClass  # noqa: E402
from buildings.typologies.paris import chronology as ch  # noqa: E402
from buildings.typologies.paris import catalogue as cat  # noqa: E402
from buildings.quantity import scale_for_class, Kind  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, evidence: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {evidence}")
    if not ok:
        FAILS.append(f"{name}: {evidence}")


print("=" * 72)
print("G5.2  CLASS LAG IS REAL — year 1885")
print("=" * 72)
diffs = 0
for feat in ch.FEATURES:
    g = ch.available(feat, 1885, BuildingClass.GRAND)
    m = ch.available(feat, 1885, BuildingClass.MODEST)
    gn = [(v.name, round(w, 4)) for v, w in g]
    mn = [(v.name, round(w, 4)) for v, w in m]
    print(f"  {feat:10s} GRAND  -> {gn}")
    print(f"  {feat:10s} MODEST -> {mn}")
    if gn != mn:
        diffs += 1
    print()
check("1885 GRAND vs MODEST differ for every feature family", diffs == len(ch.FEATURES),
      f"{diffs}/{len(ch.FEATURES)} families differ")

# set-level difference (not just weights) somewhere
setdiff = [f for f in ch.FEATURES
           if {v.name for v, _ in ch.available(f, 1885, BuildingClass.GRAND)}
           != {v.name for v, _ in ch.available(f, 1885, BuildingClass.MODEST)}]
check("at least one family differs in variant SET (not just weights) at 1885",
      bool(setdiff), f"families with set difference: {setdiff}")

print("=" * 72)
print("G5.3a FASHION IS CONTINUOUS + ACTUALLY RISES AND FALLS")
print("=" * 72)
EPS = 0.12  # a 1-year step on the shortest ramp in the table
worst = (0.0, None)
for feat in ch.FEATURES:
    for v in ch.variants_for(feat):
        for klass in BuildingClass:
            prev = None
            vals = []
            for y in range(1820, 1911):
                p = ch.prevalence(v, y, klass)
                vals.append(p)
                if not (0.0 <= p <= 1.0):
                    FAILS.append(f"prevalence out of [0,1]: {v.name} {klass} {y} = {p}")
                if prev is not None:
                    d = abs(p - prev)
                    if d > worst[0]:
                        worst = (d, (v.name, klass.value, y, prev, p))
                prev = p
            # rise and fall
            mx = max(vals)
            first_max = vals.index(mx)
            rises = any(vals[i + 1] > vals[i] for i in range(len(vals) - 1))
            falls = any(vals[i + 1] < vals[i] for i in range(len(vals) - 1))
            if mx <= 0.0:
                FAILS.append(f"variant never nonzero in 1820-1910: {v.name}/{klass.value}")
            elif not (rises and falls):
                print(f"  NOTE {v.name}/{klass.value}: rises={rises} falls={falls} "
                      f"max={mx:.3f} first={vals[0]:.3f} last={vals[-1]:.3f}")
print(f"  largest 1-year jump anywhere: {worst[0]:.4f} at {worst[1]}")
check("no 1-year prevalence jump exceeds eps", worst[0] <= EPS, f"max jump {worst[0]:.4f} (eps={EPS})")

# finer sampling for true continuity (float years)
worst_f = (0.0, None)
for feat in ch.FEATURES:
    for v in ch.variants_for(feat):
        e, pf, pt, la = v.window_for(BuildingClass.ORDINARY)
        prev = None
        y = e - 3
        while y <= la + 3:
            p = ch.prevalence(v, y, BuildingClass.ORDINARY)
            if prev is not None and abs(p - prev) > worst_f[0]:
                worst_f = (abs(p - prev), (v.name, round(y, 2), prev, p))
            prev = p
            y += 0.01
check("no 0.01-yr prevalence jump > 0.02 (true continuity)", worst_f[0] <= 0.02,
      f"max jump {worst_f[0]:.5f} at {worst_f[1]}")

# spot-print a curve
v = [x for x in ch.variants_for("keystone") if x.name == "mascaron"][0]
curve = [(y, round(ch.prevalence(v, y, BuildingClass.ORDINARY), 3))
         for y in range(1855, 1930, 5)]
print(f"  mascaron/ORDINARY curve: {curve}")
rises = any(curve[i + 1][1] > curve[i][1] for i in range(len(curve) - 1))
falls = any(curve[i + 1][1] < curve[i][1] for i in range(len(curve) - 1))
check("mascaron curve rises AND falls", rises and falls, f"rises={rises} falls={falls}")

print("=" * 72)
print("G5.3b LEGALITY IS A STEP — oriels false 1881, true 1882")
print("=" * 72)
row = [(y, ch.legal("oriel", y)) for y in range(1878, 1890)]
print(f"  legal('oriel', y): {row}")
check("oriel illegal in 1881", ch.legal("oriel", 1881) is False, f"got {ch.legal('oriel', 1881)}")
check("oriel LEGAL in 1882 (brief: 'illegal in 1881 and legal in 1882')",
      ch.legal("oriel", 1882) is True, f"got {ch.legal('oriel', 1882)}")
# is it a step at all?
transitions = [y for y in range(1800, 1920) if ch.legal("oriel", y) != ch.legal("oriel", y - 1)]
check("oriel legality has exactly one transition (a step)", len(transitions) == 1,
      f"transitions at {transitions}")

print("=" * 72)
print("G5.4  WINDOWS CONTAIN THE YEAR — 500 random (feature, year, class)")
print("=" * 72)
rng = random.Random(20260820)
bad = []
n = 0
for _ in range(500):
    feat = rng.choice(ch.FEATURES)
    year = rng.randint(1800, 1930)
    klass = rng.choice(list(BuildingClass))
    for v, w in ch.available(feat, year, klass):
        n += 1
        e, pf, pt, la = v.window_for(klass)
        if not (e <= year <= la):
            bad.append(("window", v.name, year, klass.value, (e, la)))
        if not (0.0 <= w <= 1.0):
            bad.append(("weight", v.name, year, klass.value, w))
        if w <= 0.0:
            bad.append(("zero-weight-returned", v.name, year, klass.value, w))
        if abs(w - ch.prevalence(v, year, klass)) > 1e-12:
            bad.append(("weight!=prevalence", v.name, year, klass.value, w))
print(f"  checked {n} returned variants across 500 draws; violations: {len(bad)}")
if bad:
    for b in bad[:10]:
        print("   ", b)
check("all returned variants satisfy earliest<=year<=latest and weight in [0,1]", not bad,
      f"{len(bad)} violations of {n} returned variants")

print("=" * 72)
print("G5.5  SOURCES POPULATED / INFERRED MARKED")
print("=" * 72)
bare = []
noinf = []
total_v = 0
for feat in ch.FEATURES:
    for v in ch.variants_for(feat):
        total_v += 1
        s = v.source.strip()
        if not s or len(s) < 15:
            bare.append((v.feature, v.name, repr(v.source)))
        if "INFERRED" not in v.source:
            noinf.append((v.feature, v.name))
print(f"  {total_v} variants; bare/short sources: {bare}")
print(f"  variants with NO 'INFERRED' marker: {noinf}")
check("every source non-empty and substantive", not bare, f"{len(bare)} bare")
# every variant here has at least one inferred boundary per implementer claim
check("every variant marks INFERRED somewhere (all have guessed boundaries)", not noinf,
      f"{len(noinf)} without marker: {noinf}")
try:
    ch.Variant(feature="x", name="y", earliest=1, peak_from=1, peak_to=1, latest=1, source="  ")
    check("blank source rejected", False, "no ValueError raised")
except ValueError as e:
    check("blank source rejected", True, f"ValueError: {e}")

print("=" * 72)
print("G5.6  OBSERVATION DATE != CONSTRUCTION DATE")
print("=" * 72)
bones = ch.ElementDate(building_year=1860, observed=1860, reason="original fabric")
roof = ch.raised_comble(1860, 1885)
shop = ch.ElementDate(building_year=1860, observed=1898, reason="shopfront replaced")
print(f"  bones altered={bones.altered} observed={bones.observed}")
print(f"  roof  altered={roof.altered} observed={roof.observed} reason={roof.reason[:60]}...")
print(f"  shop  altered={shop.altered} observed={shop.observed}")
kl = BuildingClass.ORDINARY
roof_by_building = [(v.name, round(w, 3)) for v, w in ch.available("roof", bones.observed, kl)]
roof_by_element = [(v.name, round(w, 3)) for v, w in ch.available("roof", roof.observed, kl)]
shop_by_building = [(v.name, round(w, 3)) for v, w in ch.available("shopfront", bones.observed, kl)]
shop_by_element = [(v.name, round(w, 3)) for v, w in ch.available("shopfront", shop.observed, kl)]
print(f"  roof @1860 -> {roof_by_building}")
print(f"  roof @1885 -> {roof_by_element}")
print(f"  shop @1860 -> {shop_by_building}")
print(f"  shop @1898 -> {shop_by_element}")
check("element date changes the available roof set vs building year",
      roof_by_building != roof_by_element, "sets differ")
check("element date changes the available shopfront set vs building year",
      shop_by_building != shop_by_element, "sets differ")
check("ElementDate.altered flags the difference",
      (not bones.altered) and roof.altered and shop.altered,
      f"{bones.altered}/{roof.altered}/{shop.altered}")

print("=" * 72)
print("G5.7  ABSOLUTE vs PROPORTIONAL IN THE CATALOGUE")
print("=" * 72)
car = cat.door_carriage_entrance()
bay = cat.standard_bay()
print(f"  carriage kinds: {car.minimum.kind}/{car.preferred.kind}/{car.maximum.kind}")
print(f"  bay kinds:      {bay.minimum.kind}/{bay.preferred.kind}/{bay.maximum.kind}")
check("carriage entrance bounds are ABSOLUTE",
      all(q.kind is Kind.ABSOLUTE for q in (car.minimum, car.preferred, car.maximum)),
      str([q.kind.value for q in (car.minimum, car.preferred, car.maximum)]))
car_w = {}
bay_w = {}
for k in BuildingClass:
    cs = car.to_slot_spec(k)
    bs = bay.to_slot_spec(k)
    car_w[k.value] = (cs.minimum, cs.preferred, cs.maximum, cs.rigid, cs.kind.value)
    bay_w[k.value] = (bs.minimum, bs.preferred, bs.maximum, bs.rigid, bs.kind.value)
    print(f"  {k.value:12s} carriage={cs.minimum}/{cs.preferred}/{cs.maximum} rigid={cs.rigid} kind={cs.kind.value}")
    print(f"  {k.value:12s} bay     ={bs.minimum:.4f}/{bs.preferred:.4f}/{bs.maximum:.4f} rigid={bs.rigid} kind={bs.kind.value}")
check("carriage width identical across all four classes",
      len({v[:3] for v in car_w.values()}) == 1, str(car_w))
check("carriage slot is FIXED and rigid", all(v[3] and v[4] == "fixed" for v in car_w.values()), str(car_w))
check("bay width DIFFERS across all four classes",
      len({round(v[1], 6) for v in bay_w.values()}) == 4, str({k: v[1] for k, v in bay_w.items()}))
check("bay preferred is monotonic MODEST<ORDINARY<COMFORTABLE<GRAND",
      bay_w["modest"][1] < bay_w["ordinary"][1] < bay_w["comfortable"][1] < bay_w["grand"][1],
      str({k: v[1] for k, v in bay_w.items()}))
# scale_for_class direct
sc = scale_for_class(car.preferred, BuildingClass.GRAND)
check("scale_for_class is a no-op on the carriage Quantity", float(sc) == float(car.preferred),
      f"{float(car.preferred)} -> {float(sc)}")
sb = scale_for_class(bay.preferred, BuildingClass.GRAND)
check("scale_for_class does move bay Quantity", float(sb) != float(bay.preferred),
      f"{float(bay.preferred)} -> {float(sb)}")

print("=" * 72)
print(f"SUMMARY: {len(FAILS)} failure(s)")
for f in FAILS:
    print("  FAIL:", f)
sys.exit(1 if FAILS else 0)
