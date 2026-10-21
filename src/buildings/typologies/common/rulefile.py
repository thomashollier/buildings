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

import dataclasses
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
from buildings.cga import lsystem as _ls
from buildings.ir.nodes import BuildingNode
from buildings.rng import DecisionStream
from buildings.solver.fitting import PlacedSlot, SlotKind, SlotSpec
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common import kit

__all__ = ["Refused", "RuleFileError", "Style", "load_style", "register_writer", "register_production"]


class RuleFileError(ValueError):
    """A rule file is malformed: an unknown verb, a missing field, a bad name."""


class Refused(ValueError):
    """A rule file declined a situation it does not model (``refuse``)."""


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


def _anchor(shape: Shape, per: str | None) -> Shape:
    """The shape a draw belongs to: the shape itself, the whole lot, or the
    nearest shape (itself or an ancestor) with the label ``per``."""
    if per is None:
        return shape
    node = shape
    if per == "Lot":
        while node.parent is not None:
            node = node.parent
        return node
    while node is not None and node.label != per:
        node = node.parent
    if node is None:
        raise ExprError(f"draw(..., per={per!r}): {shape.id} ({shape.label}) has no {per} above it")
    return node


def _drawer(shape: Shape, rng: DecisionStream | None):
    """Stochastic choices, each from its own stream addressed by the shape it
    belongs to and a key, so adding a draw anywhere never reshuffles another,
    and two floors (or two houses) choose independently."""

    def stream(key: str, per: str | None):
        if rng is None:
            raise ExprError(f"draw({key!r}): random draws are not available here (a production guard or a site attribute)")
        return rng.at(f"draw/{_anchor(shape, per).id}/{key}")

    def draw(key: str, options, weights=None, per: str | None = None):
        if isinstance(options, Mapping):
            options, weights = list(options.keys()), list(options.values())
        options = list(options)
        if not options:
            raise ExprError(f"draw({key!r}): no options")
        r = stream(key, per)
        if weights is None:
            return r.choice(options)
        weights = [float(w) for w in weights]
        if len(weights) != len(options) or sum(weights) <= 0:
            raise ExprError(f"draw({key!r}): weights must match the options and not all be zero")
        return r.choices(options, weights=weights, k=1)[0]

    def between(key: str, lo: float, hi: float, per: str | None = None) -> float:
        return stream(key, per).uniform(float(lo), float(hi))

    def chance(key: str, p: float, per: str | None = None) -> bool:
        return stream(key, per).random() < float(p)

    return {"draw": draw, "between": between, "chance": chance}


def _functions(shape: Shape, rng: DecisionStream | None = None) -> dict[str, Callable[..., Any]]:
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
        "sqrt": math.sqrt,
        "log2": math.log2,
        "ceil": math.ceil,
        "floor": math.floor,
        "is_bay": lambda: kit.is_bay(shape),
        "is_first_bay": lambda: bool(bays()) and shape is bays()[0],
        "is_last_bay": lambda: bool(bays()) and shape is bays()[-1],
        "is_middle_bay": lambda: bool(bays()) and shape is bays()[len(bays()) // 2],
        "has": lambda name: shape.attr(name, _MISSING) is not _MISSING,
        # Where the shape stands in the tree.
        "in_parent": lambda label: shape.parent is not None and shape.parent.label == label,
        "index_of": lambda label: shape.ancestor(label).index,
        "is_last": lambda label: _is_last(shape if shape.label == label else shape.ancestor(label)),
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
        # Where each part of a run starts, added part by part from ``start``.
        "starts": _starts,
        # The frame lines of a fitted run -- every joint between two bays, and
        # with ``ends`` the middle of each end pier -- as the {x, w} of a pier
        # ``width`` wide centred on each (an end pier's no wider than itself).
        "frame_lines": _frame_lines,
        # A value stepped down by ``step`` until the next step would reach
        # ``floor``: the widths a setback law leaves, tier by tier.
        "stepping": _stepping,
        "size_of": lambda part: part.size,
        # A column on every joint of a run and on the middle of its two end
        # parts, ``width`` wide (the end ones no wider than the first part).
        "column_lines": _column_lines,
        # The {x, w} of every window bay of a run, from ``start``.
        "bay_spans": _bay_spans,
        # The scope of this shape's first child with a label, once split.
        "child": lambda label: next(c.scope for c in shape.children if c.label == label),
        "every_other": lambda items: list(items)[::2],
        # The axes (centres) of the window bays of the shape with this id,
        # wherever it is in the tree.
        "bay_axes": lambda shape_id: _bay_axes(shape, shape_id),
        # Timber-frame posts across a run: at ``spacing`` from its start, none
        # across ``light`` (a scope, or None), one either side of it, and one
        # closing the run where ``last``; clamped inside the run.
        "frame_posts": _frame_posts,
        # Stochastic alternatives: draw(key, options[, weights][, per]),
        # between(key, lo, hi[, per]), chance(key, p[, per]). ``per`` names the
        # shape the choice belongs to ("Storey", "Lot", ...; default the shape
        # itself), so every window of a floor can share one draw.
        **_drawer(shape, rng),
    }


def _joints(parts, start: float) -> list[float]:
    out, x = [], start
    for p in list(parts)[:-1]:
        x += p.size
        out.append(x)
    return out


def _is_last(shape: Shape) -> bool:
    same = [s for s in shape.siblings if s.label == shape.label]
    return shape.index == len(same) - 1


def _starts(sizes, start: float) -> list[float]:
    out, x = [], start
    for size in sizes:
        out.append(x)
        x += size
    out.append(x)
    return out


def _frame_lines(parts, start: float, width: float, ends: bool = True) -> list[dict]:
    parts = list(parts)
    edges, x = [], start
    for p in parts:
        edges.append((x, x + p.size, p.attrs["slot"].name))
        x += p.size
    joints = [e[1] for e, f in zip(edges, edges[1:]) if e[2] == "bay" and f[2] == "bay"]
    if not ends:
        return [{"x": cx - width / 2.0, "w": width} for cx in joints]
    lines = [(edges[0][0] + edges[0][1]) / 2.0, *joints, (edges[-1][0] + edges[-1][1]) / 2.0]
    out = []
    for i, cx in enumerate(lines):
        w = min(width, parts[0].size) if i in (0, len(lines) - 1) else width
        out.append({"x": cx - w / 2.0, "w": w})
    return out


def _column_lines(parts, start: float, width: float) -> list[dict]:
    parts = list(parts)
    xs, x = [], start
    for p in parts:
        xs.append(x)
        x += p.size
    first_w = parts[0].size
    lines = [xs[0] + first_w / 2.0, *xs[1:], xs[-1] + parts[-1].size / 2.0]
    out = []
    for i, cx in enumerate(lines):
        w = min(width, first_w if i in (0, len(lines) - 1) else width)
        out.append({"x": cx - w / 2.0, "w": w})
    return out


def _bay_axes(shape: Shape, shape_id: str) -> list[float]:
    root = shape
    while root.parent is not None:
        root = root.parent
    target = next(s for s in root.walk() if s.id == shape_id)
    return [c.scope.x + c.scope.w / 2.0 for c in target.children if kit.is_bay(c)]


def _frame_posts(x0: float, w: float, spacing: float, post: float, light, last: bool) -> list[float]:
    xs, x = [], x0
    while x < x0 + w - post * 0.5:
        if light is None or not (light.x - post < x < light.x + light.w):
            xs.append(x)
        x += spacing
    if light is not None:
        xs += [light.x - post, light.x + light.w]
    if last:
        xs.append(x0 + w - post)
    return [min(max(px, x0), x0 + w - post) for px in sorted(set(round(v, 6) for v in xs))]


def _bay_spans(parts, start: float) -> list[dict]:
    out, x = [], start
    for p in parts:
        if p.attrs.get("slot") is not None and p.attrs["slot"].name == "bay":
            out.append({"x": x, "w": p.size})
        x += p.size
    return out


def _stepping(start: float, step: float, floor: float) -> list[float]:
    out, v = [], start
    while True:
        v -= step
        if v <= floor:
            return out
        out.append(v)


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

    def __init__(
        self,
        shape: Shape,
        params: Mapping[str, Any],
        local: Mapping[str, Any] | None = None,
        rng: DecisionStream | None = None,
    ) -> None:
        self.shape = shape
        self.params = params
        self.local: dict[str, Any] = dict(local or {})
        self.rng = rng
        self.functions = _functions(shape, rng)

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
        return _Env(self.shape, self.params, {**self.local, **local}, self.rng)


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

    def __init__(self, spec: Mapping[str, Any], where: str, systems: Mapping[str, Any] | None = None) -> None:
        verbs = [v for v in ("set", "let", "fit", "split", "insert", "each", "call", "refuse", "grow") if v in spec]
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
            self.end = _expr(spec["end"], f"{where}.end")
            self.bay = _expr(spec["bay"], f"{where}.bay")
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
            self.body = [_Op(o, f"{where}.do[{i}]", systems) for i, o in enumerate(spec["do"])]
        elif v == "refuse":
            self.message = spec["refuse"]
        elif v == "grow":
            self._grow(spec, where, systems or {})
        elif v == "call":
            if spec["call"] not in PRODUCTIONS:
                raise RuleFileError(f"{where}: no production named {spec['call']!r}")
            self.fn = PRODUCTIONS[spec["call"]]

    def _grow(self, spec: Mapping[str, Any], where: str, systems: Mapping[str, Any]) -> None:
        extra = set(spec) - {"grow", "generations", "params", "seed", "as", "name", "axiom", "when"}
        if extra:
            raise RuleFileError(f"{where}: unknown key(s) {sorted(extra)} in a grow")
        if spec["grow"] not in systems:
            raise RuleFileError(f"{where}: no [[lsystem]] with id {spec['grow']!r}")
        system = systems[spec["grow"]]
        if "axiom" in spec:
            system = dataclasses.replace(system, axiom=_ls.parse_modules(spec["axiom"], f"{where}.axiom", _expr))
        self.system = system
        self.generations = _expr(spec.get("generations", 0), f"{where}.generations")
        self.grow_params = [(k, _expr(e, f"{where}.params.{k}")) for k, e in (spec.get("params") or {}).items()]
        self.stream = _expr(spec["seed"], f"{where}.seed") if "seed" in spec else None
        self.prefix = spec.get("name", "g")
        self.store = spec.get("as")

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
            end, bay = _run(env, self.end), _run(env, self.bay)
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
        elif v == "grow":
            # Parameters are evaluated in order, each seeing the ones before.
            values: dict[str, Any] = {}
            for k, compiled in self.grow_params:
                values[k] = _run(env.child(**values), compiled)
            inner = env.child(**values)
            growth = _ls.grow(
                d,
                shape,
                self.system,
                generations=int(_run(inner, self.generations)),
                params=values,
                lookup=env.lookup,
                functions=env.functions,
                stream=None if self.stream is None else str(_run(inner, self.stream)),
                name=self.prefix,
            )
            if self.store is not None:
                shape.attrs[self.store] = {
                    "lsystem": self.system.id,
                    "generations": growth.generations,
                    "modules": len(growth.string),
                    "marks": growth.marks,
                    "choices": tuple(growth.choices),
                }
        elif v == "call":
            self.fn(shape, d)
        elif v == "refuse":
            raise Refused(self.message)
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


def _production(
    spec: Mapping[str, Any], params: Mapping[str, Any], where: str, systems: Mapping[str, Any] | None = None
) -> Production:
    ops = [_Op(o, f"{where}.do[{i}]", systems) for i, o in enumerate(spec.get("do", ()))]
    lets = [(k, _expr(e, f"{where}.let.{k}")) for k, e in spec.get("let", {}).items()]

    def body(shape: Shape, d: Derivation) -> None:
        env = _lets(_Env(shape, params, rng=d.rng), lets)
        for op in ops:
            env = op.run(shape, d, env)

    doc = spec.get("doc")
    if doc is None and len(ops) == 1 and ops[0].verb == "call":
        doc = ops[0].fn.__doc__
    body.__doc__ = doc
    guard_expr = _expr(spec["when"], f"{where}.when") if "when" in spec else None
    guard = (lambda s: True) if guard_expr is None else (lambda s: bool(_Env(s, params).eval(guard_expr)))
    return Production(spec["id"], spec["label"], body, guard=guard, priority=spec.get("priority", 0))


def _picks(spec: Mapping[str, Any] | None, where: str):
    """``pick = { per = "Storey", head = { segmental = 3, round = 1 } }``: each
    attribute drawn from weighted options (weights may be expressions), once
    per ``per`` shape."""
    if spec is None:
        return None
    spec = dict(spec)
    per = spec.pop("per", None)
    table: dict[str, tuple[list[Any], list[Any]]] = {}
    for name, options in spec.items():
        if not isinstance(options, Mapping) or not options:
            raise RuleFileError(f"{where}.{name}: options are a table of option = weight")
        table[name] = (list(options.keys()), [_expr(w, f"{where}.{name}.{o}") for o, w in options.items()])
    return per, table


def _rule(spec: Mapping[str, Any], params: Mapping[str, Any], where: str):
    when = _expr(spec["when"], f"{where}.when") if "when" in spec else None
    lets = [(k, _expr(e, f"{where}.let.{k}")) for k, e in spec.get("let", {}).items()]
    values = _map(spec.get("set"), f"{where}.set")
    picks = _picks(spec.get("pick"), f"{where}.pick")
    if not values and not picks:
        raise RuleFileError(f"{where}: a rule needs 'set' or 'pick'")
    rule_id, specificity = spec["id"], spec.get("specificity", 0)

    def rule(shape: Shape, rng: DecisionStream) -> Attrs | None:
        env = _Env(shape, params, rng=rng)
        if when is not None and not env.eval(when):
            return None
        env = _lets(env, lets)
        out = _eval_map(env, values)
        if picks is not None:
            per, table = picks
            draw = env.functions["draw"]
            for name, (options, weights) in table.items():
                ws = [_run(env, w) for w in weights]
                out[name] = draw(f"{rule_id}/{name}", options, ws, per)
        return Attrs(out, rule=rule_id, specificity=specificity)

    rule.__name__ = rule_id.rsplit(".", 1)[-1]
    rule.__doc__ = spec.get("doc")
    return rule


# ===========================================================================
# L-systems grown inside a shape
# ===========================================================================

_RULE_KEYS = {"id", "pred", "left", "right", "when", "to", "weight", "doc"}
_DRAW_VERBS = ("split", "repeat", "inset", "place", "line", "over", "arch", "round", "ring", "outline", "pierce", "polygon")
_DRAW_KEYS = {"split", "repeat", "inset", "place", "line", "weights", "n", "at", "width", "straight", "slant",
              "attrs", "when", "each"}
#: The keys each of the shaped verbs takes besides its own, ``when`` and
#: ``each``; the first set is required.
_SHAPED = {
    "over": ({"span", "rise"}, {"pitch", "count", "start", "spring", "band", "finial"}),
    "arch": ({"rise"}, set()),
    "round": ({"at"}, {"fit"}),
    "ring": ({"radius", "size"}, {"start"}),
    "outline": (set(), {"attrs"}),
    "pierce": (set(), {"at"}),
    "polygon": ({"points"}, {"attrs"}),
}


def _lsystem(spec: Mapping[str, Any], where: str) -> _ls.LSystem:
    """A ``[[lsystem]]`` table: an axiom, rewriting rules and how each symbol
    is drawn in its cell. See ``dev/RULES.md``, "Growing ornament"."""
    try:
        rules = []
        for i, r in enumerate(spec.get("rules", ())):
            rw = f"{where}: rule {r.get('id', i)}"
            extra = set(r) - _RULE_KEYS
            if extra:
                raise RuleFileError(f"{rw}: unknown key(s) {sorted(extra)}")
            symbol, formals = _ls.parse_pattern(r["pred"], rw)
            left = _ls.parse_pattern(r["left"], rw) if "left" in r else None
            right = _ls.parse_pattern(r["right"], rw) if "right" in r else None
            names = [*formals, *(left[1] if left else ()), *(right[1] if right else ())]
            if len(set(names)) != len(names):
                raise RuleFileError(f"{rw}: a formal parameter is named twice across the rule's context")
            rules.append(
                _ls.LRule(
                    id=r.get("id", f"{spec['id']}.{symbol}.{i}"),
                    symbol=symbol,
                    formals=formals,
                    successor=_ls.parse_modules(r["to"], f"{rw}.to", _expr),
                    when=_expr(r["when"], f"{rw}.when") if "when" in r else None,
                    weight=_expr(r["weight"], f"{rw}.weight") if "weight" in r else None,
                    left=left,
                    right=right,
                )
            )
        interpret: dict[str, _ls.Interpretation] = {}
        for i, entry in enumerate(spec.get("interpret", ())):
            iw = f"{where}: interpret {entry.get('module', i)}"
            symbol, formals = _ls.parse_pattern(entry["module"], iw)
            if symbol in interpret:
                raise RuleFileError(f"{iw}: {symbol!r} is interpreted twice")
            steps = entry.get("do")
            if steps is None:
                steps = [{k: v for k, v in entry.items() if k != "module"}]
            elif set(entry) - {"module", "do"}:
                raise RuleFileError(f"{iw}: an entry with 'do' has no other keys")
            interpret[symbol] = _ls.Interpretation(
                symbol, formals, tuple(_draw(s, f"{iw}.do[{k}]") for k, s in enumerate(steps))
            )
        extra = set(spec) - _KEYS["lsystem"]
        if extra:
            raise RuleFileError(f"{where}: unknown key(s) {sorted(extra)}")
        return _ls.LSystem(
            id=spec["id"],
            axiom=_ls.parse_modules(spec["axiom"], f"{where}.axiom", _expr),
            rules=tuple(rules),
            interpret=interpret,
            ignore=frozenset(spec.get("ignore", ())),
            doc=spec.get("doc", ""),
        )
    except _ls.GrowError as exc:
        raise RuleFileError(str(exc)) from exc
    except KeyError as exc:
        raise RuleFileError(f"{where}: missing {exc.args[0]!r}") from exc


def _draw(spec: Mapping[str, Any], where: str) -> _ls.Draw:
    verbs = [v for v in _DRAW_VERBS if v in spec]
    if len(verbs) != 1:
        raise RuleFileError(f"{where}: a drawing step has exactly one verb of {list(_DRAW_VERBS)}, got {verbs or list(spec)}")
    verb = verbs[0]
    when = _expr(spec["when"], f"{where}.when") if "when" in spec else None
    each = _expr(spec["each"], f"{where}.each") if "each" in spec else None
    attrs = _map(spec.get("attrs"), where)
    if verb in _SHAPED:
        return _shaped(verb, spec, where, when, each, attrs)
    extra = set(spec) - _DRAW_KEYS
    if extra:
        raise RuleFileError(f"{where}: unknown key(s) {sorted(extra)}")
    if verb in ("split", "repeat"):
        if spec[verb] not in _AXES:
            raise RuleFileError(f"{where}: {verb} along 'x' or 'y', not {spec[verb]!r}")
        if ("n" in spec) == ("weights" in spec):
            raise RuleFileError(f"{where}: a {verb} takes 'n' or 'weights'")
        key = "n" if "n" in spec else "weights"
        return _ls.Draw(verb, _AXES[spec[verb]], {key: _expr(spec[key], f"{where}.{key}")}, when=when, each=each)
    if verb == "inset":
        return _ls.Draw(verb, fields={"inset": _expr(spec["inset"], f"{where}.inset")}, when=when, each=each)
    if verb == "place":
        if len(spec.get("at", ())) != 4:
            raise RuleFileError(f"{where}: 'at' is [x, y, w, h] in the cell")
        at = [_expr(a, f"{where}.at") for a in spec["at"]]
        return _ls.Draw(verb, fields={"at": at}, label=spec["place"], attrs=attrs, when=when, each=each)
    if len(spec["line"]) != 4 or "width" not in spec:
        raise RuleFileError(f"{where}: a line is [x0, y0, x1, y1] in the cell, with a 'width'")
    return _ls.Draw(
        verb,
        fields={"line": [_expr(a, f"{where}.line") for a in spec["line"]], "width": _expr(spec["width"], f"{where}.width")},
        label=spec.get("straight", "Bar"),
        slant=spec.get("slant", "Slant"),
        attrs=attrs,
        when=when,
        each=each,
    )


def _shaped(verb: str, spec: Mapping[str, Any], where: str, when, each, attrs) -> _ls.Draw:
    """The verbs that shape a cell (``over``, ``arch``, ``round``, ``ring``)
    or draw an outline (``outline``, ``polygon``) and cut it (``pierce``)."""
    required, optional = _SHAPED[verb]
    extra = set(spec) - required - optional - {verb, "when", "each"}
    if extra:
        raise RuleFileError(f"{where}: unknown key(s) {sorted(extra)} in {verb!r}")
    missing = required - set(spec)
    if missing:
        raise RuleFileError(f"{where}: {verb!r} needs {sorted(missing)}")
    if verb in ("outline", "polygon"):
        fields = {} if verb == "outline" else {"points": _expr(spec["points"], f"{where}.points")}
        return _ls.Draw(verb, fields=fields, label=spec[verb], attrs=attrs, when=when, each=each)
    fields: dict[str, Any] = {verb: _expr(spec[verb], f"{where}.{verb}")}
    for key in (required | optional) - {"attrs"}:
        if key not in spec:
            continue
        if key == "at":
            if len(spec["at"]) != 2:
                raise RuleFileError(f"{where}: 'at' is [x, y] in the cell")
            fields["at"] = [_expr(a, f"{where}.at") for a in spec["at"]]
        else:
            fields[key] = _expr(spec[key], f"{where}.{key}")
    return _ls.Draw(verb, fields=fields, when=when, each=each)


def write_stone(shape: Shape, below, d) -> list:
    """A grown outline (``outline``, ``polygon``) drawn as stone standing in
    front of the wall: its points are the outline, its piercings cut out."""
    from buildings.ir.nodes import GableNode

    return [
        GableNode(
            id=shape.id,
            kind="gable",
            trace=tuple(shape.trace),
            props={**kit.xywh(shape.scope), "form": "stoop", "points": tuple(shape.attrs["points"]),
                   "hoist_beam": None, "wall_material": "stone"},
        )
    ]


WRITERS["grow.stone"] = write_stone


def write_slant(shape: Shape, below, d) -> list:
    """A grown diagonal: a bar across its own rectangle, rising or falling."""
    from buildings.ir.nodes import BraceNode

    return [
        BraceNode(
            id=shape.id,
            kind="brace",
            trace=tuple(shape.trace),
            props={**kit.xywh(shape.scope), "direction": shape.attrs["direction"]},
        )
    ]


WRITERS["grow.slant"] = write_slant


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


_KEYS = {
    "production": {"id", "label", "when", "priority", "doc", "let", "do"},
    "lsystem": {"id", "doc", "axiom", "ignore", "rules", "interpret"},
    "rule": {"id", "label", "layer", "when", "let", "set", "pick", "specificity", "doc"},
    "layer": {"name", "order"},
}
_TOP = {"style", "params", "lot_props", "emit", "production", "rule", "layer", "lsystem"}


def _check(data: Mapping[str, Any], path: Path) -> None:
    """Refuse what the loader would otherwise silently ignore: an unknown
    section or key, and an attribute that a parameter of the same name would
    hide (names resolve to a parameter before an attribute, so such an
    attribute could be written and never read)."""
    unknown = set(data) - _TOP
    if unknown:
        raise RuleFileError(f"{path.name}: unknown section(s) {sorted(unknown)}")
    for section, allowed in _KEYS.items():
        for i, entry in enumerate(data.get(section, ())):
            extra = set(entry) - allowed
            if extra:
                raise RuleFileError(f"{path.name}: {section} {entry.get('id', entry.get('name', i))}: unknown key(s) {sorted(extra)}")
    params = set(data.get("params") or {})
    written: set[str] = set()

    def ops(items):
        for op in items:
            written.update((op.get("set") or {}).keys())
            written.update((op.get("attrs") or {}).keys())
            for part in op.get("parts", ()):
                written.update((part.get("attrs") or {}).keys())
            if "as" in op:
                written.add(op["as"])
            ops(op.get("do", ()))

    for prod in data.get("production", ()):
        ops(prod.get("do", ()))
    for rule in data.get("rule", ()):
        written.update((rule.get("set") or {}).keys())
        written.update(k for k in (rule.get("pick") or {}) if k != "per")
    shadowed = sorted(written & params)
    if shadowed:
        raise RuleFileError(
            f"{path.name}: attribute(s) {shadowed} share a name with a parameter; a name "
            "resolves to the parameter first, so the attribute would never be read -- rename one"
        )


def load_style(path: str | Path) -> Style:
    path = Path(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    _check(data, path)
    meta = data.get("style") or {}
    name = meta.get("name") or path.stem
    params = dict(data.get("params") or {})
    systems: dict[str, _ls.LSystem] = {}
    for i, spec in enumerate(data.get("lsystem", ())):
        system = _lsystem(spec, f"{path.name}: lsystem {spec.get('id', i)}")
        if system.id in systems:
            raise RuleFileError(f"{path.name}: two [[lsystem]] tables with id {system.id!r}")
        systems[system.id] = system
    productions = tuple(
        _production(p, params, f"{path.name}: production {p.get('id', i)}", systems)
        for i, p in enumerate(data.get("production", ()))
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
