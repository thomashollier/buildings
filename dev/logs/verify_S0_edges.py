"""Verifier probes for edge cases the reported tests may not cover."""
from __future__ import annotations

import json

from buildings.quantity import Abs, Prop, Reg, Kind
from buildings.trace import TraceEntry, TraceLog
from buildings.ir.nodes import Node, SilhouetteNode, OpeningNode
from buildings.ir.serial import to_json, from_json

NOTES = []


def probe(name, fn):
    try:
        res = fn()
        print(f"[ok  ] {name}: {res}")
    except Exception as e:
        print(f"[RAISE] {name}: {type(e).__name__}: {e}")
        NOTES.append((name, f"{type(e).__name__}: {e}"))


te = TraceEntry(rule="r", phase="structure", detail="d")

print("=== immutability defences ===")
probe("mutate props via handed-in dict", lambda: (
    lambda d, n: (d.update({"hacked": True}), dict(n.props))[1]
)({"x": 1.0}, Node(id="n", kind="k", trace=(te,), props={"x": 1.0})))
d = {"x": 1.0}
n = Node(id="n", kind="k", trace=(te,), props=d)
d["hacked"] = True
print(f"       after mutating the caller's dict, node.props = {dict(n.props)}")
probe("assign into node.props", lambda: n.props.__setitem__("z", 1))
probe("mutate children list handed in", lambda: type(Node(id="a", kind="k", trace=(te,), children=[]).children).__name__)
ti = {"a": 1}
e2 = TraceEntry(rule="r", phase="p", detail="d", inputs=ti)
ti["b"] = 2
print(f"       after mutating caller's inputs dict, entry.inputs = {dict(e2.inputs)}")

print()
print("=== hashability of IR types ===")
probe("hash(TraceEntry)", lambda: hash(te))
probe("hash(Node)", lambda: hash(Node(id="n", kind="k", trace=(te,))))

print()
print("=== TraceLog ===")
log = TraceLog()
log.record("n1", te)
log.record("n1", TraceEntry(rule="r2", phase="roles", detail="d2"))
log.record("n2", te)
got = log.explain("n1")
got.append("POLLUTION")
print(f"       explain('n1') len after caller appended junk: {len(log.explain('n1'))} (want 2)")
print(f"       all_ids: {log.all_ids()}")
print(f"       explain(unknown): {log.explain('nope')!r}")
ids = log.all_ids(); ids.append("junk")
print(f"       all_ids after caller appended junk: {log.all_ids()}")

print()
print("=== serial: non-JSON payloads ===")
probe("to_json with a Quantity in props",
      lambda: to_json(Node(id="q", kind="k", trace=(te,), props={"h": Abs(2.1, "door")}))[:80])
probe("to_json with a Quantity in trace inputs",
      lambda: to_json(Node(id="q", kind="k", trace=(TraceEntry(rule="r", phase="p", detail="d",
                                                              inputs={"limit": Reg(6.0, "law")}),)))[:80])
sil = SilhouetteNode(id="sil", kind="silhouette", trace=(te,),
                     props={"points": ((0.0, 0.0), (1.0, 5.0), (2.0, 0.0))})
rt = from_json(to_json(sil))
print(f"[{'ok  ' if rt == sil else 'LOSSY'}] silhouette polyline (tuple of tuples in props) round-trip: "
      f"eq={rt == sil}; back as {type(rt.props['points']).__name__} = {rt.props['points']}")
probe("to_json with an int key in props", lambda: json.loads(to_json(
    Node(id="q", kind="k", trace=(te,), props={1: "x"})))["props"])
probe("from_json with unknown __type__",
      lambda: from_json(json.dumps({"__type__": "BogusNode", "id": "x", "kind": "k",
                                    "trace": [{"rule": "r", "phase": "p", "detail": "d", "inputs": {}}],
                                    "children": [], "props": {}})))
probe("from_json rejects empty trace payload",
      lambda: from_json(json.dumps({"__type__": "Node", "id": "x", "kind": "k",
                                    "trace": [], "children": [], "props": {}})))

print()
print("=== quantity: scaling escape hatches ===")
print(f"       Abs(2.1) * 1.35            -> {Abs(2.1,'door') * 1.35}")
print(f"       Abs(2.1) / 2.0             -> {Abs(2.1,'door') / 2.0}")
print(f"       Reg(6.0) * 1.35            -> {Reg(6.0,'law') * 1.35}")
probe("Quantity + float (bare number)", lambda: Abs(2.1, "d") + 1.0)
probe("float + Quantity", lambda: 1.0 + Abs(2.1, "d"))
probe("Quantity / Quantity(0)", lambda: Abs(2.1, "d") / Prop(0.0, "z"))
probe("Reg(v, None)", lambda: Reg(6.0, None))
probe("Reg(v, '   ') whitespace-only source", lambda: Reg(6.0, "   ").why)
