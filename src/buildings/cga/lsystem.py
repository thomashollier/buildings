"""Growing ornament inside one shape: a parametric L-system as a split-grammar
operation.

A split grammar is good at layout -- a facade cut into storeys, a storey
into bays -- and poor at self-similar ornament, which it can only place, not
grow. An L-system is the reverse. ``grow`` is where the two meet: a
production hands **one shape's scope** to an L-system, the L-system rewrites
a string of parametric modules for a number of generations, and the result
is interpreted as **cells** inside that scope, every mark becoming a child
shape of the grown one. So the ornament is derived, not drawn, and it is
still a split grammar's child: it is inserted by the engine (``insert``), so
it cannot leave its parent (``OutsideParent``), each mark is traced to the
L-system, the rule and the generation that made it, and the label it is
given is written by whatever interpreter the grammar names for it.

The parts, in order:

**Modules.** ``Grid(a / 2, b) [ Bead ] Rx(2)`` -- a symbol, optionally with
arguments, and ``[`` ``]`` for a branch. Arguments are expressions in the
rule language (``cga/expr.py``): whitelisted, checked when parsed.

**Rewriting.** Every generation rewrites every module in parallel. A rule is
``pred : when -> successor`` with optional ``left < pred > right`` context
and an optional ``weight``. Of the rules whose predecessor, context and
guard match, context-sensitive ones beat context-free ones; if several are
left they must all carry a weight, and one is drawn by weight from the
derivation's ``DecisionStream`` at a path naming the L-system, the stream
key, the generation, the symbol and its occurrence -- never from a shared
sequence, so adding a rule elsewhere moves nothing (I5). Several matches
without weights raise ``GrowConflict``, as two productions at one priority
do.

**Interpretation.** Not a turtle but a *cell*: the state is the rectangle the
module draws in, starting as the grown shape's scope. A module's
interpretation may

* ``split`` the cell along x or y by weights -- each following ``[ ... ]``
  takes the next part;
* ``repeat`` the cell along x or y into ``n`` equal parts -- the following
  ``[ ... ]`` is drawn once in each (CGA's ``{ ~1 : X }*``; the string stays
  short while the drawing multiplies);
* ``inset`` the cell;
* ``place`` a rectangle, or draw a ``line`` of a given width, in cell-local
  metres (``cw`` and ``ch`` are the cell's size).

A ``[`` with no pending part draws in a copy of the current cell, and every
change made inside a branch is forgotten at its ``]``. A mark must lie inside
its cell (``OutsideParent`` again), so a module can draw only where its own
cell is.

Nothing here knows about any style; ``typologies/common/rulefile.py`` reads
``[[lsystem]]`` tables and the ``grow`` operation into these objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from buildings.cga.derive import Derivation, OutsideParent
from buildings.cga.expr import Expr, ExprError
from buildings.cga.shape import Scope, Shape
from buildings.trace import TraceEntry

__all__ = [
    "Draw",
    "GrowConflict",
    "GrowError",
    "Interpretation",
    "LRule",
    "LSystem",
    "Mark",
    "Module",
    "Template",
    "derive_string",
    "grow",
    "interpret_string",
    "parse_modules",
    "parse_pattern",
    "render_string",
]

#: A cell or mark may overrun its container by this much, in metres.
_TOL = 1e-6
#: Hard limits, so a runaway rule fails loudly instead of eating the machine.
MAX_GENERATIONS = 16
MAX_MODULES = 50_000
MAX_MARKS = 20_000


class GrowError(ValueError):
    """An L-system is malformed, or grew past its limits."""


class GrowConflict(GrowError):
    """Several rules matched one module and not all of them carry a weight."""


Compile = Callable[[str, str], Expr]


def _compile(src: str, where: str) -> Expr:
    try:
        return Expr(src)
    except ExprError as exc:
        raise GrowError(f"{where}: {exc}") from exc


# ===========================================================================
# Modules and their syntax
# ===========================================================================


@dataclass(frozen=True)
class Template:
    """A module as written in an axiom or a successor: arguments still
    expressions. ``symbol`` is ``"["`` or ``"]"`` for a branch."""

    symbol: str
    args: tuple[Expr, ...] = ()


@dataclass(frozen=True)
class Module:
    """A module of a grown string: arguments evaluated, and a record of the
    generation that wrote it (0 for the axiom) and the rule that did."""

    symbol: str
    args: tuple[Any, ...] = ()
    born: int = 0
    by: str = ""

    def __str__(self) -> str:
        if self.symbol in "[]" or not self.args:
            return self.symbol
        return f"{self.symbol}({', '.join(_fmt(a) for a in self.args)})"


def _fmt(v: Any) -> str:
    return f"{v:.4g}" if isinstance(v, float) else repr(v) if isinstance(v, str) else str(v)


def _tokens(src: str, where: str) -> list[tuple[str, list[str]]]:
    """``"A(x, f(y)) [ B ] +"`` -> ``[("A", ["x", "f(y)"]), ("[", []), ...]``."""
    out: list[tuple[str, list[str]]] = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c in "[]":
            out.append((c, []))
            i += 1
            continue
        if c in "(),":
            raise GrowError(f"{where}: unexpected {c!r} at {i} in {src!r}")
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            symbol = src[i:j]
        else:
            # A one-character symbol: + - & ^ / | ! and the like.
            j = i + 1
            symbol = c
        args: list[str] = []
        if j < n and src[j] == "(":
            depth, k, start = 0, j, j + 1
            while k < n:
                ch = src[k]
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth -= 1
                    if depth == 0:
                        break
                elif ch == "," and depth == 1:
                    args.append(src[start:k])
                    start = k + 1
                k += 1
            if k >= n:
                raise GrowError(f"{where}: unclosed '(' after {symbol!r} in {src!r}")
            last = src[start:k]
            if last.strip() or args:
                args.append(last)
            if any(not a.strip() for a in args):
                raise GrowError(f"{where}: an empty argument to {symbol!r} in {src!r}")
            j = k + 1
        out.append((symbol, [a.strip() for a in args]))
        i = j
    depth = 0
    for symbol, _ in out:
        depth += {"[": 1, "]": -1}.get(symbol, 0)
        if depth < 0:
            raise GrowError(f"{where}: ']' without '[' in {src!r}")
    if depth:
        raise GrowError(f"{where}: unbalanced brackets in {src!r}")
    return out


def parse_modules(src: str, where: str = "modules", compile: Compile = _compile) -> tuple[Template, ...]:
    """An axiom or a successor: modules whose arguments are expressions."""
    return tuple(
        Template(s, tuple(compile(a, f"{where}: {s}") for a in args)) for s, args in _tokens(src, where)
    )


def parse_pattern(src: str, where: str = "pattern") -> tuple[str, tuple[str, ...]]:
    """A predecessor or a context: one symbol and its formal parameter names."""
    toks = _tokens(src, where)
    if len(toks) != 1 or toks[0][0] in "[]":
        raise GrowError(f"{where}: a predecessor is one module, got {src!r}")
    symbol, formals = toks[0]
    for f in formals:
        if not f.isidentifier():
            raise GrowError(f"{where}: formal parameter {f!r} of {symbol!r} is not a name")
    if len(set(formals)) != len(formals):
        raise GrowError(f"{where}: repeated formal parameter in {src!r}")
    return symbol, tuple(formals)


# ===========================================================================
# Rules and interpretation, as data
# ===========================================================================


@dataclass(frozen=True)
class LRule:
    id: str
    symbol: str
    formals: tuple[str, ...]
    successor: tuple[Template, ...]
    when: Expr | None = None
    weight: Expr | float | None = None
    left: tuple[str, tuple[str, ...]] | None = None
    right: tuple[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class Draw:
    """One step of a module's interpretation. ``verb`` is one of ``split``,
    ``repeat``, ``inset``, ``place``, ``line``; ``fields`` holds its compiled
    expressions; ``each`` repeats it with ``item`` and ``i`` bound."""

    verb: str
    axis: str | None = None
    fields: Mapping[str, Any] = field(default_factory=dict)
    label: str | None = None
    slant: str | None = None
    attrs: Mapping[str, Any] = field(default_factory=dict)
    when: Expr | None = None
    each: Expr | None = None


@dataclass(frozen=True)
class Interpretation:
    symbol: str
    formals: tuple[str, ...]
    steps: tuple[Draw, ...]


@dataclass(frozen=True)
class LSystem:
    id: str
    axiom: tuple[Template, ...]
    rules: tuple[LRule, ...]
    interpret: Mapping[str, Interpretation]
    #: Symbols context matching looks past (bookkeeping such as an inset).
    ignore: frozenset[str] = frozenset()
    doc: str = ""

    def rules_for(self, symbol: str, arity: int) -> list[LRule]:
        return [r for r in self.rules if r.symbol == symbol and len(r.formals) == arity]


# ===========================================================================
# Rewriting
# ===========================================================================


class _Scope:
    """Name resolution inside an L-system: bound names first (formals, cell
    size, loop variables), then the grow's parameters, then the caller's."""

    def __init__(self, bound: Mapping[str, Any], params: Mapping[str, Any], outer: Callable[[str], Any]) -> None:
        self.bound, self.params, self.outer = bound, params, outer

    def __call__(self, name: str) -> Any:
        if name in self.bound:
            return self.bound[name]
        if name in self.params:
            return self.params[name]
        return self.outer(name)


def _bind(formals: Sequence[str], module: Module) -> dict[str, Any]:
    return dict(zip(formals, module.args))


def _left(string: Sequence[Module], i: int, ignore: frozenset[str]) -> Module | None:
    """The module before ``i`` in the ABOP sense: past complete branches,
    out of the branch ``i`` is in, past ignored symbols."""
    j = i - 1
    while j >= 0:
        s = string[j].symbol
        if s == "]":
            depth = 1
            j -= 1
            while j >= 0 and depth:
                depth += {"]": 1, "[": -1}.get(string[j].symbol, 0)
                j -= 1
            continue
        if s == "[" or s in ignore:
            j -= 1
            continue
        return string[j]
    return None


def _right(string: Sequence[Module], i: int, ignore: frozenset[str]) -> Module | None:
    """The module after ``i`` at its own level: past complete branches and
    ignored symbols, never out of the branch ``i`` is in."""
    j = i + 1
    while j < len(string):
        s = string[j].symbol
        if s == "[":
            depth = 1
            j += 1
            while j < len(string) and depth:
                depth += {"[": 1, "]": -1}.get(string[j].symbol, 0)
                j += 1
            continue
        if s == "]":
            return None
        if s in ignore:
            j += 1
            continue
        return string[j]
    return None


def _context_ok(pattern, module: Module | None, bound: dict[str, Any]) -> bool:
    if pattern is None:
        return True
    symbol, formals = pattern
    if module is None or module.symbol != symbol or len(module.args) != len(formals):
        return False
    bound.update(_bind(formals, module))
    return True


def _instantiate(templates: Sequence[Template], ev: Callable[[Expr], Any], born: int, by: str) -> list[Module]:
    return [Module(t.symbol, tuple(ev(a) for a in t.args), born, by) for t in templates]


@dataclass
class Growth:
    """What a grow did: the final string, how many generations ran, and every
    stochastic choice (which rule a draw picked over which)."""

    system: str
    generations: int
    string: list[Module]
    choices: list[str] = field(default_factory=list)
    marks: int = 0


def derive_string(
    system: LSystem,
    generations: int,
    *,
    params: Mapping[str, Any],
    lookup: Callable[[str], Any],
    functions: Mapping[str, Callable[..., Any]],
    rng=None,
    stream: str = "",
) -> Growth:
    """Rewrite the axiom ``generations`` times."""
    n = int(generations)
    if not 0 <= n <= MAX_GENERATIONS:
        raise GrowError(f"{system.id}: {generations} generations is outside 0..{MAX_GENERATIONS}")

    def ev_in(bound):
        scope = _Scope(bound, params, lookup)
        return lambda e: e(scope, functions) if isinstance(e, Expr) else e

    string = _instantiate(system.axiom, ev_in({}), 0, f"{system.id}.axiom")
    growth = Growth(system.id, n, string)
    for gen in range(1, n + 1):
        out: list[Module] = []
        seen: dict[str, int] = {}
        for i, module in enumerate(string):
            if module.symbol in "[]":
                out.append(module)
                continue
            occurrence = seen.get(module.symbol, 0)
            seen[module.symbol] = occurrence + 1
            matched: list[tuple[LRule, dict[str, Any]]] = []
            for rule in system.rules_for(module.symbol, len(module.args)):
                bound = _bind(rule.formals, module)
                if not _context_ok(rule.left, _left(string, i, system.ignore) if rule.left else None, bound):
                    continue
                if not _context_ok(rule.right, _right(string, i, system.ignore) if rule.right else None, bound):
                    continue
                if rule.when is not None and not ev_in(bound)(rule.when):
                    continue
                matched.append((rule, bound))
            if any(r.left or r.right for r, _ in matched):
                matched = [(r, b) for r, b in matched if r.left or r.right]
            if not matched:
                out.append(module)
                continue
            if len(matched) == 1:
                rule, bound = matched[0]
            else:
                if any(r.weight is None for r, _ in matched):
                    raise GrowConflict(
                        f"{system.id}: {module} in generation {gen} matched {[r.id for r, _ in matched]}; "
                        "rules that compete for one module must all carry a weight, or one must be guarded"
                    )
                weights = [float(ev_in(b)(r.weight)) for r, b in matched]
                if rng is None:
                    raise GrowError(f"{system.id}: a stochastic rule needs a decision stream")
                path = f"lsystem/{system.id}/{stream}/g{gen}/{module.symbol}/{occurrence}"
                k = rng.at(path).choices(range(len(matched)), weights=weights, k=1)[0]
                rule, bound = matched[k]
                growth.choices.append(
                    f"generation {gen}: {module} -> {rule.id} (weight {weights[k]:g} of {sum(weights):g}; "
                    f"over {[r.id for j, (r, _) in enumerate(matched) if j != k]})"
                )
            out.extend(_instantiate(rule.successor, ev_in(bound), gen, rule.id))
            if len(out) > MAX_MODULES:
                raise GrowError(f"{system.id}: the string passed {MAX_MODULES} modules in generation {gen}")
        string = out
    growth.string = string
    return growth


# ===========================================================================
# Interpretation: modules as marks in nested cells
# ===========================================================================


@dataclass(frozen=True)
class Mark:
    """One thing a grown string draws: a label, where (absolute metres), the
    attributes it is given, and the module that drew it."""

    label: str
    scope: Scope
    attrs: Mapping[str, Any]
    module: Module


def _tree(string: Sequence[Module]) -> list:
    """The flat string as nested lists: a branch is a list."""
    root: list = []
    stack = [root]
    for m in string:
        if m.symbol == "[":
            branch: list = []
            stack[-1].append(branch)
            stack.append(branch)
        elif m.symbol == "]":
            stack.pop()
        else:
            stack[-1].append(m)
    return root


def _parts(cell: Scope, axis: str, weights: Sequence[float], where: str) -> list[Scope]:
    weights = [float(v) for v in weights]
    if not weights or any(v < 0 for v in weights) or sum(weights) <= 0:
        raise GrowError(f"{where}: split weights {weights} must be non-negative and not all zero")
    total, extent = math.fsum(weights), cell.extent(axis)
    out, cursor = [], cell.start(axis)
    for v in weights:
        size = extent * v / total
        out.append(cell.slice(axis, cursor, size))
        cursor += size
    return out


def _inside(outer: Scope, inner: Scope) -> bool:
    return outer.contains(inner, _TOL)


def interpret_string(
    system: LSystem,
    string: Sequence[Module],
    scope: Scope,
    *,
    params: Mapping[str, Any],
    lookup: Callable[[str], Any],
    functions: Mapping[str, Callable[..., Any]],
) -> list[Mark]:
    """Draw a grown string into ``scope``, in order."""
    marks: list[Mark] = []

    def run(items: list, cell: Scope) -> None:
        pending: list[Scope] = []
        replicate: list[Scope] | None = None
        for item in items:
            if isinstance(item, list):
                if replicate is not None:
                    for part in replicate:
                        run(item, part)
                    replicate = None
                elif pending:
                    run(item, pending.pop(0))
                else:
                    run(item, cell)
                continue
            how = system.interpret.get(item.symbol)
            if how is None:
                continue
            if len(how.formals) != len(item.args):
                raise GrowError(f"{system.id}: {item} is interpreted as {item.symbol}{how.formals}")
            for step in how.steps:
                cell, made = _draw(system, step, item, how, cell, params, lookup, functions, marks)
                if made is not None:
                    kind, parts = made
                    if kind == "split":
                        pending, replicate = parts, None
                    else:
                        pending, replicate = [], parts

    run(_tree(string), scope)
    if len(marks) > MAX_MARKS:
        raise GrowError(f"{system.id}: drew {len(marks)} marks, more than {MAX_MARKS}")
    return marks


def _draw(system, step: Draw, module: Module, how: Interpretation, cell: Scope, params, lookup, functions, marks):
    where = f"{system.id}: {module}"
    base = {**_bind(how.formals, module), "cw": cell.w, "ch": cell.h}
    scope = _Scope(base, params, lookup)
    if step.when is not None and not step.when(scope, functions):
        return cell, None
    items = [(None, None)]
    if step.each is not None:
        items = list(enumerate(step.each(scope, functions)))
    made = None
    for i, item in items:
        bound = base if step.each is None else {**base, "item": item, "i": i}
        sc = _Scope(bound, params, lookup)
        ev = lambda e: e(sc, functions) if isinstance(e, Expr) else e  # noqa: E731
        v = step.verb
        if v in ("split", "repeat"):
            if "n" in step.fields:
                weights = [1.0] * int(ev(step.fields["n"]))
            else:
                weights = ev(step.fields["weights"])
            made = (v, _parts(cell, step.axis, weights, where))
        elif v == "inset":
            d = ev(step.fields["inset"])
            l, b, r, t = (d, d, d, d) if not isinstance(d, (list, tuple)) else d
            if l + r > cell.w + _TOL or b + t > cell.h + _TOL:
                raise GrowError(f"{where}: inset {d} is larger than its cell {cell}")
            cell = Scope(cell.x + l, cell.y + b, max(0.0, cell.w - l - r), max(0.0, cell.h - b - t))
        elif v == "place":
            x, y, w, h = (float(ev(a)) for a in step.fields["at"])
            _mark(marks, step.label, Scope(cell.x + x, cell.y + y, w, h), cell, ev, step, module, where, {})
        elif v == "line":
            x0, y0, x1, y1 = (float(ev(a)) for a in step.fields["line"])
            width = float(ev(step.fields["width"]))
            dx, dy = x1 - x0, y1 - y0
            if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                continue
            if abs(dx) < 1e-9:
                at = Scope(cell.x + x0 - width / 2.0, cell.y + min(y0, y1), width, abs(dy))
                _mark(marks, step.label, at, cell, ev, step, module, where, {})
            elif abs(dy) < 1e-9:
                at = Scope(cell.x + min(x0, x1), cell.y + y0 - width / 2.0, abs(dx), width)
                _mark(marks, step.label, at, cell, ev, step, module, where, {})
            else:
                at = Scope(cell.x + min(x0, x1), cell.y + min(y0, y1), abs(dx), abs(dy))
                extra = {"direction": "rising" if dx * dy > 0 else "falling"}
                _mark(marks, step.slant, at, cell, ev, step, module, where, extra)
    return cell, made


def _mark(marks, label, at: Scope, cell: Scope, ev, step: Draw, module: Module, where: str, extra) -> None:
    if at.w < -_TOL or at.h < -_TOL:
        raise GrowError(f"{where}: a {label} of negative size {at}")
    if not _inside(cell, at):
        raise OutsideParent(
            f"{where} drew {label} at {at} outside its cell {cell}. A grown mark stays inside the "
            "cell its module draws in"
        )
    attrs = {k: ev(v) for k, v in step.attrs.items()}
    marks.append(Mark(label, at, {**extra, **attrs}, module))


# ===========================================================================
# The operation
# ===========================================================================


def render_string(string: Sequence[Module], limit: int = 400) -> str:
    text = " ".join(str(m) for m in string)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def grow(
    d: Derivation,
    shape: Shape,
    system: LSystem,
    *,
    generations: int,
    params: Mapping[str, Any],
    lookup: Callable[[str], Any],
    functions: Mapping[str, Callable[..., Any]],
    stream: str | None = None,
    name: str = "g",
) -> Growth:
    """Grow ``system`` inside ``shape``: rewrite, interpret into its scope, and
    insert every mark as a child shape through the derivation, so the engine's
    containment check and trace apply to each.

    Each child carries, after the engine's own ``insert`` entry, one entry
    naming the L-system, the rule that wrote its module and the generation
    it was written in; the grown shape carries one entry for the growth as a
    whole (generations, final string, every stochastic choice).
    """
    key = shape.id if stream is None else str(stream)
    growth = derive_string(
        system, generations, params=params, lookup=lookup, functions=functions, rng=d.rng, stream=key
    )
    marks = interpret_string(system, growth.string, shape.scope, params=params, lookup=lookup, functions=functions)
    growth.marks = len(marks)
    summary = TraceEntry(
        rule=system.id,
        phase="grammar",
        detail=(
            f"grew {system.id} for {growth.generations} generation(s): {len(growth.string)} modules, "
            f"{len(marks)} marks; {render_string(growth.string, 200)}"
            + (f"; {'; '.join(growth.choices)}" if growth.choices else "")
        ),
        inputs={"lsystem": system.id, "generations": growth.generations, "stream": key},
    )
    shape.trace.append(summary)
    d.log.append(summary)
    for k, mark in enumerate(marks):
        child = d.insert(shape, mark.label, mark.scope, f"{name}{k}", mark.attrs)
        m = mark.module
        child.trace.append(
            TraceEntry(
                rule=m.by,
                phase="grammar",
                detail=(
                    f"grown by {system.id}: {m.symbol}{'(...)' if m.args else ''} written in generation "
                    f"{m.born} of {growth.generations} by {m.by}, drawn as {mark.label}"
                ),
                inputs={"lsystem": system.id, "generation": m.born, "generations": growth.generations},
            )
        )
    return growth
