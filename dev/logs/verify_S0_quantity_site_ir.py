"""Independent verification of gate G0 checks 1, 2, 4, 5. Written by the verifier."""
from __future__ import annotations

import json
import subprocess
import sys
import traceback

from buildings.quantity import Abs, Kind, Prop, Quantity, Reg, scale_for_class
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.ir.nodes import CONCRETE_NODE_KINDS, Node
from buildings.ir.serial import from_json, to_json
from buildings.trace import TraceEntry, TraceLog

FAILS: list[str] = []


def check(name: str, cond: bool, evidence: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} :: {evidence}")
    if not cond:
        FAILS.append(f"{name} :: {evidence}")


print("=== CHECK 1: Quantity arithmetic / kind mixing ===")
a = Abs(2.10, "door height, human body")
p = Prop(1.00, "lintel allowance")
r = Reg(6.00, "ordonnance 1823 art.4")

# most rigid wins: ABSOLUTE > REGULATORY > PROPORTIONAL
cases = [
    ("abs+prop", a + p, Kind.ABSOLUTE),
    ("prop+abs", p + a, Kind.ABSOLUTE),
    ("reg+prop", r + p, Kind.REGULATORY),
    ("prop+reg", p + r, Kind.REGULATORY),
    ("abs+reg", a + r, Kind.ABSOLUTE),
    ("reg+abs", r + a, Kind.ABSOLUTE),
    ("prop+prop", p + p, Kind.PROPORTIONAL),
    ("abs-prop", a - p, Kind.ABSOLUTE),
    ("prop-reg", p - r, Kind.REGULATORY),
    ("abs*prop", a * p, Kind.ABSOLUTE),
    ("prop*reg", p * r, Kind.REGULATORY),
    ("abs/prop", a / p, Kind.ABSOLUTE),
    ("prop/reg", p / r, Kind.REGULATORY),
]
for label, got, want in cases:
    check(f"kind mixing {label}", got.kind is want, f"got {got.kind.value}, want {want.value}, value={got.value}")

check("neg preserves kind", (-a).kind is Kind.ABSOLUTE and (-a).value == -2.10, f"{(-a)!r}")
check("float() works", float(a) == 2.10, f"float(a)={float(a)}")
check("rigid property", a.rigid and r.rigid and not p.rigid,
      f"abs.rigid={a.rigid} reg.rigid={r.rigid} prop.rigid={p.rigid}")

# scaled(): ABS/REG ignore, PROP scales
check("Abs.scaled is no-op", a.scaled(2.0) is a or (a.scaled(2.0).value == 2.10),
      f"a.scaled(2.0)={a.scaled(2.0)!r}")
check("Reg.scaled is no-op", r.scaled(2.0).value == 6.00, f"r.scaled(2.0)={r.scaled(2.0)!r}")
check("Prop.scaled scales", p.scaled(2.0).value == 2.00, f"p.scaled(2.0)={p.scaled(2.0)!r}")

# scale_for_class
for klass in BuildingClass:
    sa = scale_for_class(a, klass)
    sr = scale_for_class(r, klass)
    sp = scale_for_class(p, klass)
    check(f"scale_for_class {klass.value}: ABS unchanged", sa.value == 2.10, f"{sa.value}")
    check(f"scale_for_class {klass.value}: REG unchanged", sr.value == 6.00, f"{sr.value}")
    print(f"      PROP {klass.value} -> {sp.value}")
ramp = [scale_for_class(p, k).value for k in
        (BuildingClass.MODEST, BuildingClass.ORDINARY, BuildingClass.COMFORTABLE, BuildingClass.GRAND)]
check("scale_for_class PROP monotonic", ramp == sorted(ramp) and len(set(ramp)) == 4, f"ramp={ramp}")

# Reg("") raises
try:
    Reg(6.0, "")
    check("Reg with empty source raises ValueError", False, "no exception raised")
except ValueError as e:
    check("Reg with empty source raises ValueError", True, f"ValueError: {e}")
except Exception as e:  # wrong exception type
    check("Reg with empty source raises ValueError", False, f"raised {type(e).__name__}: {e}")

# frozen-ness of Quantity
try:
    object.__getattribute__(a, "value")
    a.value = 9.0  # type: ignore[misc]
    check("Quantity is frozen", False, "assignment succeeded")
except Exception as e:
    check("Quantity is frozen", type(e).__name__ == "FrozenInstanceError", f"{type(e).__name__}: {e}")

# probe: does arithmetic with a bare number bypass rigidity?
scaled_abs_via_mul = a * 1.35
print(f"      NOTE probe: Abs * 1.35 -> value={scaled_abs_via_mul.value} kind={scaled_abs_via_mul.kind.value}")

print()
print("=== CHECK 2: IR JSON round-trip, every concrete node type ===")
te1 = TraceEntry(rule="paris.qualify.balcony.ordonnance_1823", phase="qualification",
                 detail="balcony allowed at 6m", inputs={"level": 6.0, "klass": "grand", "n": 3, "flag": True,
                                                         "nested": {"a": [1, 2, 3]}, "none": None})
te2 = TraceEntry(rule="paris.structure.bays", phase="structure", detail="7 bays")

check("node count matches contract (16)", len(CONCRETE_NODE_KINDS) == 16,
      f"{len(CONCRETE_NODE_KINDS)}: {[c.__name__ for c in CONCRETE_NODE_KINDS]}")

expected_names = {"BuildingNode", "StoreyNode", "BayNode", "OpeningNode", "SurroundNode", "BalconyNode",
                  "CorniceNode", "StringCourseNode", "SocleNode", "ShopfrontNode", "RoofNode",
                  "DormerNode", "SilhouetteNode", "IronworkNode", "KeystoneNode", "SpecialNode"}
got_names = {c.__name__ for c in CONCRETE_NODE_KINDS}
check("all 16 contract kinds present", got_names == expected_names,
      f"missing={expected_names - got_names} extra={got_names - expected_names}")

for cls in CONCRETE_NODE_KINDS:
    n = cls(id=f"{cls.__name__}#1", kind="IGNORED", trace=(te1, te2),
            props={"x": 0.0, "y": 3.25, "w": 1.4, "h": 2.6, "s": "text", "b": False, "i": 7})
    s = to_json(n)
    back = from_json(s)
    ok = back == n and type(back) is cls
    check(f"round-trip {cls.__name__}", ok,
          f"type={type(back).__name__} eq={back == n} kind={back.kind!r} "
          f"trace_eq={back.trace == n.trace} props_eq={dict(back.props) == dict(n.props)} "
          f"inputs_eq={dict(back.trace[0].inputs) == dict(n.trace[0].inputs)}")

# nested tree round-trip
from buildings.ir.nodes import BuildingNode, StoreyNode, BayNode, OpeningNode
tree = BuildingNode(id="b", kind="building", trace=(te2,), children=(
    StoreyNode(id="s0", kind="storey", trace=(te2,), children=(
        BayNode(id="b0", kind="bay", trace=(te2,), children=(
            OpeningNode(id="o0", kind="opening", trace=(te1,), props={"x": 1.0, "y": 2.0, "w": 1.0, "h": 2.2}),
        )),
    )),
))
rt = from_json(to_json(tree))
check("round-trip nested 4-deep tree", rt == tree,
      f"eq={rt == tree}; leaf inputs preserved="
      f"{dict(rt.children[0].children[0].children[0].trace[0].inputs) == dict(te1.inputs)}")

# base Node round-trip
bn = Node(id="raw", kind="anything", trace=(te2,))
check("round-trip base Node", from_json(to_json(bn)) == bn and type(from_json(to_json(bn))) is Node,
      f"type={type(from_json(to_json(bn))).__name__}")

# I4: empty trace rejected
try:
    Node(id="x", kind="k", trace=())
    check("empty trace rejected (I4)", False, "construction succeeded")
except ValueError as e:
    check("empty trace rejected (I4)", True, f"ValueError: {e}")

print()
print("=== CHECK 4: SiteContext frozen + hashable ===")
sc = SiteContext(street_width=12.0, parcel_width=8.0, parcel_depth=18.0, year=1867,
                 klass=BuildingClass.ORDINARY, ground=GroundProgramme.SHOP)
try:
    sc.street_width = 20.0  # type: ignore[misc]
    check("SiteContext frozen", False, "assignment succeeded")
except Exception as e:
    check("SiteContext frozen", type(e).__name__ == "FrozenInstanceError", f"{type(e).__name__}: {e}")

try:
    d = {sc: "ok"}
    sc2 = SiteContext(street_width=12.0, parcel_width=8.0, parcel_depth=18.0, year=1867,
                      klass=BuildingClass.ORDINARY, ground=GroundProgramme.SHOP)
    check("SiteContext hashable + value-equal key", d[sc2] == "ok",
          f"hash={hash(sc)} lookup by equal instance -> {d[sc2]!r}")
except Exception as e:
    check("SiteContext hashable", False, f"{type(e).__name__}: {e}")

check("SiteContext defaults corner/seed", sc.corner is False and sc.seed == 0,
      f"corner={sc.corner} seed={sc.seed}")
check("SiteContext field names match contract",
      [f for f in sc.__dataclass_fields__] == ["street_width", "parcel_width", "parcel_depth", "year",
                                               "klass", "ground", "corner", "seed"],
      f"{list(sc.__dataclass_fields__)}")

print()
print("=== CHECK 5: site.py imports no random / rng (I2) ===")
import ast, inspect
import buildings.site as site_mod
src_path = inspect.getsourcefile(site_mod)
tree_ast = ast.parse(open(src_path).read())
imported = []
for node in ast.walk(tree_ast):
    if isinstance(node, ast.Import):
        imported += [al.name for al in node.names]
    elif isinstance(node, ast.ImportFrom):
        imported.append(node.module or "")
bad = [m for m in imported if m.split(".")[0] in {"random", "rng"} or m.endswith(".rng") or "rng" in m.split(".")]
check("site.py has no random/rng import", not bad, f"imports={imported}; offending={bad}")
check("SiteContext has no sampling methods",
      not [m for m in dir(SiteContext) if not m.startswith("__") and callable(getattr(SiteContext, m, None))],
      f"public callables={[m for m in dir(SiteContext) if not m.startswith('__')]}")

print()
print("FAILURES:", len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
