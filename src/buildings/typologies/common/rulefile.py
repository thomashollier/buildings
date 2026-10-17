"""Styles as rule files: a TOML file in, a ``Grammar`` out.

A rule file says, in data, what a style module used to say in Python: the
named numbers it is built from, how each shape is split (``[[production]]``)
and what each shape is given (``[[rule]]``). The engine is unchanged; this
module only turns the file into the same ``Production`` and ``Attrs``-
returning rules a hand-written module would have built.

The format, briefly (``dev/RULES.md`` has the whole of it):

```toml
[style]
name = "georgian"
describe = { rule = "georgian.terrace_house", phase = "structure", detail = "f'... {year}'" }
axiom = { w = "width", h = 40 }
site = ["width", "year", "klass", "seed"]
overhangs = ["Cornice"]

[params]
window_w = 1.05
bay = [1.9, 2.2, 2.7]

[[production]]
id = "georgian.storey"
label = "Storey"
when = "role != 'parapet'"            # optional guard
do = [ { split = "x", by = "rhythm" },
       { insert = "Cornice", at = ["x", "y + h", "w", "0.4"], name = "cornice",
         attrs = { cornice_ornament = "modillioned" }, when = "floor == 'third'" } ]

[[rule]]
id = "georgian.base.the_window_of_its_floor"
label = "Cell"
layer = "base"
when = "is_bay() and floor != 'parapet'"
let = { height = "min(window_w * ratio, h - 0.3)" }
set = { opening_type = "window", light_height = "= height" }
```

Two kinds of string, and the difference is deliberate. A geometry or a
condition (``at``, ``size``, ``when``, ``let``) is always an expression. A
value in ``set`` or ``attrs`` is a literal unless it starts with ``=`` -- so
``opening_type = "window"`` reads as what it is, and ``light_height =
"= height"`` is visibly computed.

What a file cannot express it names: the shared window anatomy
(``call = "kit.split_cell_around_its_light"``) and a style's special drawings
(``[emit] Pavilion = "modernist.pavilion"``), registered in Python by name.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from buildings.cga import (
    Attrs,
    AttributeStage,
    Derivation,
    Grammar,
    Layer,
    Part,
    Production,
    Scope,
    Shape,
    X,
    Y,
    derive,
    interpret,
)
from buildings.cga.expr import Expr, ExprError
from buildings.ir.nodes import BuildingNode
from buildings.rng import DecisionStream
from buildings.solver.fitting import PlacedSlot, SlotKind, SlotSpec
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common import kit

__all__ = ["RuleFileError", "Style", "load_style", "register_writer", "register_production"]


class RuleFileError(ValueError):
    """A rule file is malformed: an unknown verb, a missing field, a bad name."""


#: Python productions a rule file may ``call`` by name.
PRODUCTIONS: dict[str, Callable[[Shape, Derivation], None]] = {
    "kit.split_cell_around_its_light": kit.split_cell_around_its_light,
    "kit.split_light_bay": kit.split_light_bay,
    "kit.split_light_bay_into_lights": kit.split_light_bay_into_lights,
    "kit.dress_the_light": kit.dress_the_light,
}

#: IR writers a rule file may name in ``[emit]``.
WRITERS: dict[str, Callable] = {f"kit.{label.lower()}": fn for label, fn in kit.INTERPRETERS.items()}


def register_production(name: str, fn: Callable[[Shape, Derivation], None]) -> None:
    PRODUCTIONS[name] = fn


def register_writer(name: str, fn: Callable) -> None:
    WRITERS[name] = fn


_MISSING = object()
_AXES = {"x": X, "y": Y}


# ===========================================================================
# Evaluation context
# ===========================================================================


def _same_label(shape: Shape) -> list[Shape]:
    return [s for s in shape.siblings if s.label == shape.label]


def _functions(shape: Shape) -> dict[str, Callable[..., Any]]:
    def bays() -> list[Shape]:
        return [c for c in shape.siblings if kit.is_bay(c)]

    return {
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "len": len,
        "sum": sum,
        "fsum": math.fsum,
        "float": float,
        "int": int,
        "range": lambda *a: list(range(*a)),
        "column": lambda rows, key: [r[key] for r in rows],
        "sin": math.sin,
        "cos": math.cos,
        "pi": lambda: math.pi,
        "is_bay": lambda: kit.is_bay(shape),
        "is_first_bay": lambda: bool(bays()) and shape is bays()[0],
        "is_last_bay": lambda: bool(bays()) and shape is bays()[-1],
        "is_middle_bay": lambda: bool(bays()) and shape is bays()[len(bays()) // 2],
        "has": lambda name: shape.attr(name, _MISSING) is not _MISSING,
        # Where the shape stands in the tree.
        "in_parent": lambda label: shape.parent is not None and shape.parent.label == label,
        "index_of": lambda label: shape.ancestor(label).index,
        # Running positions along a fitted run: the joints between its parts,
        # starting from ``start`` and added part by part.
        "joints": _joints,
        # A step table read the way a regulation is: the first row whose
        # limit the value does not exceed gives the answer.
        "step": lambda table, value: next(v for limit, v in table if value <= limit),
        # A run that shrinks by a ratio: storeys tapering up a facade.
        "geometric": lambda first, ratio, n: [first * ratio**k for k in range(int(n))],
        # The middle of every window bay of a fitted run, from ``start``.
        "bay_centres": _bay_centres,
    }


def _joints(parts, start: float) -> list[float]:
    out, x = [], start
    for p in list(parts)[:-1]:
        x += p.size
        out.append(x)
    return out


def _bay_centres(parts, start: float) -> list[float]:
    out, x = [], start
    for p in parts:
        if p.attrs.get("slot") is not None and p.attrs["slot"].name == "bay":
            out.append(x + p.size / 2.0)
        x += p.size
    return out


class _Env:
    """Name resolution for one shape: locals, the shape's own geometry and
    place, the file's parameters, then the shape's attributes up the tree."""

    def __init__(self, shape: Shape, params: Mapping[str, Any], local: Mapping[str, Any] | None = None) -> None:
        self.shape = shape
        self.params = params
        self.local: dict[str, Any] = dict(local or {})
        self.functions = _functions(shape)

    def lookup(self, name: str) -> Any:
        if name in self.local:
            return self.local[name]
        s = self.shape
        special = {
            "x": lambda: s.scope.x,
            "y": lambda: s.scope.y,
            "w": lambda: s.scope.w,
            "h": lambda: s.scope.h,
            "index": lambda: s.index,
            "nth": lambda: _same_label(s).index(s),
            "count": lambda: len(_same_label(s)),
            "label": lambda: s.label,
            "parent": lambda: s.parent.scope if s.parent is not None else s.scope,
        }
        if name in special:
            return special[name]()
        if name in self.params:
            return self.params[name]
        value = s.attr(name, _MISSING)
        if value is _MISSING:
            raise ExprError(f"{name!r} is not a local, a parameter, or an attribute of {s.id} ({s.label})")
        return value

    def eval(self, expr: Expr) -> Any:
        return expr(self.lookup, self.functions)

    def child(self, **local: Any) -> _Env:
        return _Env(self.shape, self.params, {**self.local, **local})


#: The functions an expression may call; checked when the file is loaded.
FUNCTION_NAMES = frozenset(_functions(Shape("Lot", Scope(0.0, 0.0, 0.0, 0.0), "probe")))


def _expr(value: Any, where: str) -> Expr | Any:
    """A geometry field: a string is an expression, anything else a literal."""
    if isinstance(value, str):
        try:
            compiled = Expr(value)
        except ExprError as exc:
            raise RuleFileError(f"{where}: {exc}") from exc
        unknown = compiled.calls - FUNCTION_NAMES
        if unknown:
            raise RuleFileError(f"{where}: unknown function(s) {sorted(unknown)} in {value!r}")
        return compiled
    return value


def _value(value: Any, where: str) -> Expr | Any:
    """A ``set`` / ``attrs`` value: an expression only when it starts with '='."""
    if isinstance(value, str) and value.startswith("="):
        return _expr(value[1:], where)
    return value


def _run(env: _Env, compiled: Any) -> Any:
    return env.eval(compiled) if isinstance(compiled, Expr) else compiled


def _map(spec: Mapping[str, Any] | None, where: str) -> dict[str, Any]:
    return {k: _value(v, f"{where}.{k}") for k, v in (spec or {}).items()}


def _eval_map(env: _Env, compiled: Mapping[str, Any]) -> dict[str, Any]:
    return {k: _run(env, v) for k, v in compiled.items()}


def _lets(env: _Env, lets: Sequence[tuple[str, Any]]) -> _Env:
    for name, compiled in lets:
        env = env.child(**{name: _run(env, compiled)})
    return env


# ===========================================================================
# Operations
# ===========================================================================


def _slot_for(name: str, start: float, size: float) -> PlacedSlot:
    return PlacedSlot(name, SlotKind.REPEATING if name == "bay" else SlotKind.FLEXIBLE, start, size)


class _Op:
    """One verb of a production body, compiled."""

    def __init__(self, spec: Mapping[str, Any], where: str) -> None:
        verbs = [v for v in ("set", "let", "fit", "split", "insert", "each", "call") if v in spec]
        if len(verbs) != 1:
            raise RuleFileError(f"{where}: an operation has exactly one verb, got {verbs or list(spec)}")
        self.verb = verbs[0]
        self.where = where
        self.when = _expr(spec["when"], f"{where}.when") if "when" in spec else None
        v = self.verb
        if v == "set":
            self.values = _map(spec["set"], where)
        elif v == "let":
            self.lets = [(k, _expr(e, f"{where}.let.{k}")) for k, e in spec["let"].items()]
        elif v == "fit":
            self.axis = _AXES[spec["fit"]]
            self.budget = _expr(spec.get("budget", "w" if spec["fit"] == "x" else "h"), where)
            self.end, self.bay = spec["end"], spec["bay"]
            self.label = spec.get("label", "Cell")
            self.store = spec["as"]
            self.min_bays = spec.get("min_bays", 1)
            self.max_bays = spec.get("max_bays", 24)
        elif v == "split":
            self.axis = _AXES[spec["split"]]
            self.id_base = spec.get("id_base")
            self.by = spec.get("by")
            self.label = spec.get("label")
            self.name = spec.get("name", "x{i}")
            self.parts = [self._part(p, f"{where}.parts[{i}]") for i, p in enumerate(spec.get("parts", ()))]
            if self.by is None and not self.parts:
                raise RuleFileError(f"{where}: a split needs 'parts' or 'by'")
        elif v == "insert":
            self.label = spec["insert"]
            at = spec["at"]
            if len(at) != 4:
                raise RuleFileError(f"{where}: 'at' is [x, y, w, h]")
            self.at = [_expr(a, f"{where}.at") for a in at]
            self.name = spec["name"]
            self.attrs = _map(spec.get("attrs"), where)
        elif v == "each":
            self.items = _expr(spec["each"], where)
            self.body = [_Op(o, f"{where}.do[{i}]") for i, o in enumerate(spec["do"])]
        elif v == "call":
            if spec["call"] not in PRODUCTIONS:
                raise RuleFileError(f"{where}: no production named {spec['call']!r}")
            self.fn = PRODUCTIONS[spec["call"]]

    def _part(self, p: Mapping[str, Any], where: str) -> dict[str, Any]:
        out = {
            "label": p.get("label", self.label),
            "size": _expr(p["size"], f"{where}.size"),
            "name": p.get("name", self.name),
            "attrs": _map(p.get("attrs"), where),
            "slot": p.get("slot"),
        }
        if "repeat" in p:
            out["repeat"] = _expr(p["repeat"], f"{where}.repeat")
        return out

    def run(self, shape: Shape, d: Derivation, env: _Env) -> _Env:
        if self.when is not None and not env.eval(self.when):
            return env
        v = self.verb
        if v == "set":
            for k, val in _eval_map(env, self.values).items():
                shape.attrs[k] = val
        elif v == "let":
            env = _lets(env, self.lets)
        elif v == "fit":
            end, bay = env.lookup(self.end), env.lookup(self.bay)
            parts, _ = d.fit(
                _run(env, self.budget),
                self.label,
                end=SlotSpec("end", SlotKind.FLEXIBLE, *end, elasticity=2.0),
                bay=SlotSpec("bay", SlotKind.REPEATING, *bay),
                min_bays=self.min_bays,
                max_bays=self.max_bays,
            )
            shape.attrs[self.store] = parts
        elif v == "split":
            d.split(shape, self.axis, self._parts(shape, env), id_base=self._id_base(shape))
        elif v == "insert":
            x, y, w, h = (float(_run(env, a)) for a in self.at)
            d.insert(shape, self.label, Scope(x, y, w, h), self.name.format(**env.local), _eval_map(env, self.attrs))
        elif v == "each":
            for i, item in enumerate(_run(env, self.items)):
                inner = env.child(item=item, i=i)
                for op in self.body:
                    inner = op.run(shape, d, inner)
        elif v == "call":
            self.fn(shape, d)
        return env

    def _id_base(self, shape: Shape) -> str | None:
        if self.id_base == "parent":
            return shape.parent.id
        return self.id_base

    def _parts(self, shape: Shape, env: _Env) -> list[Part]:
        if self.by is not None:
            fitted = env.lookup(self.by)
            label = self.label
            return [
                Part(label or p.label, p.size, self.name.format(i=i, n=i), p.attrs)
                for i, p in enumerate(fitted)
            ]
        out: list[Part] = []
        cursor = shape.scope.start(self.axis)
        for spec in self.parts:
            items = list(_run(env, spec["repeat"])) if "repeat" in spec else [None]
            for i, item in enumerate(items):
                e = env.child(item=item, i=i) if item is not None else env
                size = float(_run(e, spec["size"]))
                attrs = _eval_map(e, spec["attrs"])
                if spec["slot"] is not None:
                    attrs["slot"] = _slot_for(spec["slot"], cursor, size)
                out.append(Part(spec["label"], size, spec["name"].format(i=i, n=len(out)), attrs))
                cursor += size
        return out


# ===========================================================================
# The style
# ===========================================================================


def _production(spec: Mapping[str, Any], params: Mapping[str, Any], where: str) -> Production:
    ops = [_Op(o, f"{where}.do[{i}]") for i, o in enumerate(spec.get("do", ()))]
    lets = [(k, _expr(e, f"{where}.let.{k}")) for k, e in spec.get("let", {}).items()]

    def body(shape: Shape, d: Derivation) -> None:
        env = _lets(_Env(shape, params), lets)
        for op in ops:
            env = op.run(shape, d, env)

    doc = spec.get("doc")
    if doc is None and len(ops) == 1 and ops[0].verb == "call":
        doc = ops[0].fn.__doc__
    body.__doc__ = doc
    guard_expr = _expr(spec["when"], f"{where}.when") if "when" in spec else None
    guard = (lambda s: True) if guard_expr is None else (lambda s: bool(_Env(s, params).eval(guard_expr)))
    return Production(spec["id"], spec["label"], body, guard=guard, priority=spec.get("priority", 0))


def _rule(spec: Mapping[str, Any], params: Mapping[str, Any], where: str):
    when = _expr(spec["when"], f"{where}.when") if "when" in spec else None
    lets = [(k, _expr(e, f"{where}.let.{k}")) for k, e in spec.get("let", {}).items()]
    values = _map(spec["set"], f"{where}.set")
    rule_id, specificity = spec["id"], spec.get("specificity", 0)

    def rule(shape: Shape, rng: DecisionStream) -> Attrs | None:
        env = _Env(shape, params)
        if when is not None and not env.eval(when):
            return None
        env = _lets(env, lets)
        return Attrs(_eval_map(env, values), rule=rule_id, specificity=specificity)

    rule.__name__ = rule_id.rsplit(".", 1)[-1]
    rule.__doc__ = spec.get("doc")
    return rule


@dataclass
class Style:
    """A style loaded from its rule file."""

    name: str
    path: Path
    params: dict[str, Any]
    productions: tuple[Production, ...]
    stages: tuple[AttributeStage, ...]
    writers: dict[str, Callable]
    overhangs: frozenset[str]
    axiom_spec: dict[str, Any]
    site_fields: tuple[str, ...]
    describe: dict[str, Any]
    lot_props: dict[str, Any] = field(default_factory=dict)

    def grammar(self) -> Grammar:
        return Grammar(
            name=self.name,
            productions=self.productions,
            stages=self.stages,
            interpreters={**self.writers, "Lot": kit.write_lot(self._describe, self._lot_props)},
            overhangs=self.overhangs,
        )

    def _site_attrs(self, site: Any) -> dict[str, Any]:
        out: dict[str, Any] = {"site": site}
        for f in self.site_fields:
            value = getattr(site, f)
            out[f] = getattr(value, "value", value)
        return out

    def _describe(self, lot: Shape) -> TraceEntry:
        env = _Env(lot, self.params)
        return TraceEntry(rule=self.describe["rule"], phase=self.describe.get("phase", "structure"), detail=_run(env, self.describe["detail"]))

    def _lot_props(self, lot: Shape) -> dict[str, Any]:
        return _eval_map(_Env(lot, self.params), self.lot_props)

    def axiom(self, site: Any) -> Shape:
        attrs = self._site_attrs(site)
        probe = Shape("Lot", Scope(0.0, 0.0, 0.0, 0.0), "b", attrs=attrs)
        env = _Env(probe, self.params)
        w = float(_run(env, self.axiom_spec["w"]))
        h = float(_run(env, self.axiom_spec["h"]))
        return Shape("Lot", Scope(0.0, 0.0, w, h), "b", attrs=attrs)

    def derive(self, site: Any, *, refine: Callable[[Grammar], Grammar] | None = None):
        grammar = self.grammar() if refine is None else refine(self.grammar())
        return derive(grammar, self.axiom(site), DecisionStream(getattr(site, "seed", 0)))

    def generate(self, site: Any, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
        lot, derivation = self.derive(site, refine=refine)
        (root,) = interpret(lot, derivation)
        return root, kit.log_of(root)


def load_style(path: str | Path) -> Style:
    path = Path(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    meta = data.get("style") or {}
    name = meta.get("name") or path.stem
    params = dict(data.get("params") or {})
    productions = tuple(
        _production(p, params, f"{path.name}: production {p.get('id', i)}") for i, p in enumerate(data.get("production", ()))
    )
    layers_spec = {l["name"]: l.get("order", 0) for l in data.get("layer", ())}
    by_label: dict[str, dict[str, list]] = {}
    for i, r in enumerate(data.get("rule", ())):
        layer = r.get("layer", "base")
        if layer not in layers_spec:
            layers_spec[layer] = 0
        by_label.setdefault(r["label"], {}).setdefault(layer, []).append(_rule(r, params, f"{path.name}: rule {r.get('id', i)}"))
    stages = tuple(
        AttributeStage(label, tuple(Layer(lname, layers_spec[lname], tuple(rules)) for lname, rules in layers.items()))
        for label, layers in by_label.items()
    )
    writers = dict(kit.INTERPRETERS)
    for label, writer in (data.get("emit") or {}).items():
        if writer not in WRITERS:
            raise RuleFileError(f"{path.name}: no writer named {writer!r} for {label}")
        writers[label] = WRITERS[writer]
    describe = dict(meta.get("describe") or {"rule": f"{name}.style", "detail": name})
    describe["detail"] = _expr(describe["detail"], f"{path.name}: style.describe.detail")
    axiom = {k: _expr(v, f"{path.name}: style.axiom.{k}") for k, v in (meta.get("axiom") or {"w": "width", "h": 40}).items()}
    return Style(
        name=name,
        path=path,
        params=params,
        productions=productions,
        stages=stages,
        writers=writers,
        overhangs=frozenset(meta.get("overhangs", ())),
        axiom_spec=axiom,
        site_fields=tuple(meta.get("site", ())),
        describe=describe,
        lot_props=_map(data.get("lot_props"), f"{path.name}: lot_props"),
    )
