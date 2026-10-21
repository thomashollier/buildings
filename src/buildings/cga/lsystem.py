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

A cell need not be a rectangle. It may stand ``over`` a row of arches (its
floor their extrados), be an ``arch`` (its ceiling the head), or be
``round`` (a disc, fitted if asked between its floor and ceiling), and a
``ring`` sets round cells about a centre (the following ``[ ... ]`` drawn in
each, ``angle`` bound). What it draws may be an ``outline`` -- the cell's
own shape as a polygon -- which later modules ``pierce``: piercings that
overlap open as one, so four foils round a heart cut a quatrefoil, and the
outline is emitted as one simple polygon with its openings cut out (by a
slit from its top, or as a bite out of the edge an opening is centred on).
So tracery is grown as stone, and its openings are what the stone leaves.

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
    "Cell",
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
    "head_outline",
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
    ``repeat``, ``inset``, ``place``, ``line`` (rectangles), ``over``,
    ``arch``, ``round``, ``ring`` (shaped cells), ``outline``, ``pierce``,
    ``polygon`` (outlines); ``fields`` holds its compiled expressions;
    ``each`` repeats it with ``item`` and ``i`` bound."""

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
    attributes it is given, and the module that drew it. An outline's
    attributes carry its ``points``."""

    label: str
    scope: Scope
    attrs: Mapping[str, Any]
    module: Module


Point = tuple[float, float]


@dataclass(frozen=True)
class Cell(Scope):
    """The region a module draws in: a rectangle (the ``Scope`` it is), which
    may have a *profile* -- a ``floor`` or a ``ceil`` (polylines, left to
    right, in absolute metres) that is not straight: the extrados of the
    arches the cell stands over (``over``), or the head of the arch the cell
    is (``arch``) -- or be *round*: a disc of ``radius`` about ``centre``
    (``round``, ``ring``), its rectangle only the disc's box, and ``clip`` the
    rectangle it was made in. ``names`` are bound for whatever draws in it (a
    ring part's ``angle``)."""

    floor: tuple[Point, ...] = ()
    ceil: tuple[Point, ...] = ()
    centre: Point | None = None
    radius: float = 0.0
    clip: Scope | None = None
    names: tuple[tuple[str, Any], ...] = ()


def _cell(s: Scope, like: Cell | None = None, axis: str | None = None) -> Cell:
    """A rectangle as a cell. A part cut from a profiled cell keeps the
    profile over its own width (cut across x) or the edge it shares (cut
    across y); every part keeps the names bound in its parent."""
    if like is None:
        return Cell(s.x, s.y, s.w, s.h)
    floor = ceil = ()
    if axis == "x" or axis is None:
        floor, ceil = _clip_profile(like.floor, s.x, s.x + s.w), _clip_profile(like.ceil, s.x, s.x + s.w)
    else:
        if abs(s.y - like.y) < _TOL and like.floor:
            floor = tuple((x, min(y, s.y + s.h)) for x, y in like.floor)
        if abs(s.y + s.h - like.y - like.h) < _TOL and like.ceil:
            ceil = tuple((x, max(y, s.y)) for x, y in like.ceil)
    return Cell(s.x, s.y, s.w, s.h, floor=floor, ceil=ceil, names=like.names)


def _rect(cell: Scope) -> Scope:
    return Scope(cell.x, cell.y, cell.w, cell.h)


# --- profiles: arches, as the renderer turns them ---------------------------------


def head_outline(x: float, spring: float, w: float, rise: float, form: str) -> list[Point]:
    """An arch's head over the span ``x .. x + w`` springing at ``spring``,
    from one springing over the top to the other, exactly as the renderer
    turns it: ``round`` (a semicircle scaled to its rise), ``pointed`` (two
    arcs struck from the opposite springings, scaled to the rise) or ``ogee``
    (a cubic that leaves the springing upright, turns about two thirds of the
    way up and runs concave into the point)."""
    if form == "round":
        return [(x + w / 2.0 - w / 2.0 * math.cos(math.pi * i / 16), spring + rise * math.sin(math.pi * i / 16)) for i in range(17)]
    if form == "ogee":
        left = []
        for i in range(15):
            t = i / 14
            across = 3 * t * t - 2 * t**3
            up = 3 * t * (1 - t) ** 2 * 0.50 + 3 * t * t * (1 - t) * 0.12 + t**3
            left.append((x + w / 2.0 * across, spring + rise * up))
    elif form == "pointed":
        k = rise / (w * math.sin(math.pi / 3.0))
        left = [(x + w - w * math.cos(a), spring + k * w * math.sin(a)) for a in (math.pi / 3.0 * i / 10 for i in range(11))]
    else:
        raise GrowError(f"an arch is round, pointed or ogee, not {form!r}")
    right = [(x + w - (px - x), py) for px, py in reversed(left[:-1])]
    return [(x, spring), *left, *right, (x + w, spring)]


def _height(poly: Sequence[Point], x: float, pick=max) -> float | None:
    """Where a polyline stands at ``x`` (``pick`` of several where it doubles
    back); None off its ends."""
    best = None
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if min(x0, x1) - 1e-9 <= x <= max(x0, x1) + 1e-9:
            y = pick(y0, y1) if abs(x1 - x0) < 1e-12 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            best = y if best is None else pick(best, y)
    return best


def _clip_profile(poly: Sequence[Point], x0: float, x1: float) -> tuple[Point, ...]:
    if not poly:
        return ()
    inside = [(x, y) for x, y in poly if x0 + 1e-9 < x < x1 - 1e-9]
    ends = []
    for x in (x0, x1):
        y = _height(poly, x)
        ends.append((x, poly[0][1] if y is None and x <= poly[0][0] else (poly[-1][1] if y is None else y)))
    return (ends[0], *inside, ends[1])


def _floor(cell: Cell) -> tuple[Point, ...]:
    return cell.floor or ((cell.x, cell.y), (cell.x + cell.w, cell.y))


def _ceil(cell: Cell) -> tuple[Point, ...]:
    return cell.ceil or ((cell.x, cell.y + cell.h), (cell.x + cell.w, cell.y + cell.h))


def _arcade(form, x0, span, pitch, count, spring, rise, band, finial) -> list[list[Point]]:
    """The extrados of a row of ``count`` arches ``span`` wide at ``pitch``,
    their stone band ``band`` wide included, and the fleuron (``finial``
    high) on each tip: what stands over them has to clear."""
    curves: list[list[Point]] = []
    for k in range(count):
        x = x0 + k * pitch
        curves.append(head_outline(x - band, spring, span + 2.0 * band, rise + band, form))
        if finial > 0.0:
            cx, tip = x + span / 2.0, spring + rise
            curves.append([(cx - 0.32 * finial, tip + 0.45 * finial), (cx, tip + finial), (cx + 0.32 * finial, tip + 0.45 * finial)])
    return curves


def _envelope(curves, base: Sequence[Point], x0: float, x1: float) -> tuple[Point, ...]:
    xs = sorted({x0, x1, *(px for c in [base, *curves] for px, _ in c if x0 < px < x1)})
    out = []
    for x in xs:
        y = _height(base, x)
        for c in curves:
            h = _height(c, x)
            if h is not None:
                y = h if y is None else max(y, h)
        out.append((x, y))
    return tuple(out)


def _distance(px: float, py: float, poly: Sequence[Point]) -> float:
    best = math.inf
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0.0 if L < 1e-18 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L))
        best = min(best, math.hypot(px - x0 - t * dx, py - y0 - t * dy))
    return best


# --- outlines and piercings -------------------------------------------------------

#: Samples round a full turn of a piercing or a disc.
_ARC = 96


@dataclass
class _Solid:
    """An outline waiting for its piercings: drawn when the string is."""

    label: str
    cell: Cell
    attrs: dict
    module: Module
    where: str
    discs: list = field(default_factory=list)


@dataclass
class _Rose:
    """Piercings that overlap, as one opening: star-shaped about the middle
    of their centres (``reach`` is how far it opens along a ray), with the
    angles where two of its circles meet (its cusps)."""

    cx: float
    cy: float
    discs: list
    cusps: list

    def reach(self, theta: float) -> float:
        ux, uy = math.cos(theta), math.sin(theta)
        best = 0.0
        for x, y, r in self.discs:
            dx, dy = x - self.cx, y - self.cy
            b = ux * dx + uy * dy
            disc = b * b - (dx * dx + dy * dy) + r * r
            if disc >= 0.0:
                best = max(best, b + math.sqrt(disc))
        return best

    def at(self, theta: float) -> Point:
        r = self.reach(theta)
        return (self.cx + r * math.cos(theta), self.cy + r * math.sin(theta))

    def arc(self, a0: float, a1: float) -> list[Point]:
        """The opening's edge from angle ``a0`` round to ``a1`` (radians,
        anticlockwise when ``a1 > a0``), its cusps kept sharp."""
        n = max(1, math.ceil(abs(a1 - a0) / (2 * math.pi) * _ARC))
        angles = {a0 + (a1 - a0) * i / n for i in range(n + 1)}
        lo, hi = min(a0, a1), max(a0, a1)
        for c in self.cusps:
            for turn in (-2, -1, 0, 1, 2):
                a = c + turn * 2 * math.pi
                if lo + 1e-9 < a < hi - 1e-9:
                    angles.add(a)
        return [self.at(a) for a in sorted(angles, reverse=a1 < a0)]


def _roses(discs: Sequence[tuple[float, float, float]], where: str) -> list[_Rose]:
    groups: list[list] = []
    for d in discs:
        touching = [g for g in groups if any(math.hypot(d[0] - e[0], d[1] - e[1]) < d[2] + e[2] - 1e-9 for e in g)]
        groups = [g for g in groups if all(g is not t for t in touching)] + [[*(e for t in touching for e in t), d]]
    out = []
    for g in groups:
        cx = math.fsum(d[0] for d in g) / len(g)
        cy = math.fsum(d[1] for d in g) / len(g)
        if not any(math.hypot(d[0] - cx, d[1] - cy) <= d[2] + 1e-9 for d in g):
            raise GrowError(
                f"{where}: piercings that overlap open as one, about the middle of their centres, so one of them "
                "must cover that middle (a heart, or foils that reach it)"
            )
        rose = _Rose(cx, cy, g, [])
        for i, (x1, y1, r1) in enumerate(g):
            for x2, y2, r2 in g[i + 1:]:
                dd = math.hypot(x2 - x1, y2 - y1)
                if dd < 1e-12 or dd >= r1 + r2 or dd <= abs(r1 - r2):
                    continue
                a = (r1 * r1 - r2 * r2 + dd * dd) / (2 * dd)
                hgt = math.sqrt(max(0.0, r1 * r1 - a * a))
                mx, my = x1 + a * (x2 - x1) / dd, y1 + a * (y2 - y1) / dd
                for sgn in (1, -1):
                    px, py = mx + sgn * hgt * (y2 - y1) / dd, my - sgn * hgt * (x2 - x1) / dd
                    theta = math.atan2(py - cy, px - cx)
                    if abs(rose.reach(theta) - math.hypot(px - cx, py - cy)) < 1e-7:
                        rose.cusps.append(theta)
        out.append(rose)
    return sorted(out, key=lambda r: (r.cx, r.cy))


def _close(pts: list[Point]) -> tuple[Point, ...]:
    out: list[Point] = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) > 1e-9:
        out.append(out[0])
    return tuple((round(x, 6), round(y, 6)) for x, y in out)


_UP, _DOWN = math.pi / 2.0, -math.pi / 2.0


def _profile_pieces(solid: _Solid, roses: list[_Rose]) -> list[tuple[Point, ...]]:
    """A profiled cell's outline, each opening in it cut out. An opening
    inside is reached by a slit from the ceiling straight down to its top (a
    joint, drawn); one centred on the cell's left or right edge is a bite out
    of that edge -- the half the edge leaves. So every outline is one simple
    polygon, and what the openings show is whatever is behind."""
    cell = solid.cell
    x0, x1 = cell.x, cell.x + cell.w
    floor, ceil = _floor(cell), _ceil(cell)
    inner, left, right = [], None, None
    for rose in roses:
        if abs(rose.cx - x0) < _TOL:
            left = rose
        elif abs(rose.cx - x1) < _TOL:
            right = rose
        elif x0 < rose.cx < x1:
            inner.append(rose)
        else:
            raise OutsideParent(f"{solid.where}: a piercing at x = {rose.cx:.3f} is outside the {solid.label} it cuts")
        for a in (2 * math.pi * i / _ARC for i in range(_ARC)):
            px, py = rose.at(a)
            if px < x0 - _TOL or px > x1 + _TOL:
                if rose is left and px < x0 + _TOL or rose is right and px > x1 - _TOL:
                    continue
                raise OutsideParent(f"{solid.where}: a piercing breaks out of the side of the {solid.label} it cuts")
            lo, hi = _height(floor, px), _height(ceil, px, min)
            if lo is not None and py < lo - _TOL or hi is not None and py > hi + _TOL:
                raise OutsideParent(f"{solid.where}: a piercing breaks through the {solid.label} it cuts, at ({px:.3f}, {py:.3f})")
    pts: list[Point] = []
    # Along the ceiling, left to right, down every slit and round every opening.
    stops = sorted(inner, key=lambda r: r.cx)
    for (ax, ay), (bx, by) in zip(ceil, ceil[1:]):
        pts.append((ax, ay))
        for rose in stops:
            if ax <= rose.cx < bx:
                top = _height(ceil, rose.cx, min)
                pts += [(rose.cx, top), *rose.arc(_UP, _UP + 2 * math.pi), (rose.cx, top)]
    pts.append(ceil[-1])
    # Down the right edge, bitten by an opening centred on it.
    if right is not None:
        pts += right.arc(_UP, _UP + math.pi)
    # Back along the floor, right to left.
    pts += list(reversed(floor))
    # Up the left edge.
    if left is not None:
        pts += left.arc(_DOWN, _UP)
    return [_close(pts)]


def _round_pieces(solid: _Solid, roses: list[_Rose]) -> list[tuple[Point, ...]]:
    """A disc's outline, its opening (about its own centre) cut out by a slit
    from the top; or, where its centre stands on an edge of the rectangle it
    was made in, the half that edge leaves (a half-oculus against a jamb)."""
    cell = solid.cell
    (ox, oy), R = cell.centre, cell.radius
    if len(roses) > 1 or roses and math.hypot(roses[0].cx - ox, roses[0].cy - oy) > 1e-6:
        raise GrowError(f"{solid.where}: a round {solid.label} is pierced only about its own centre")
    rose = roses[0] if roses else None
    if rose is not None and any(rose.reach(2 * math.pi * i / _ARC) > R - _TOL for i in range(_ARC)):
        raise OutsideParent(f"{solid.where}: a piercing breaks through the rim of the round {solid.label}")
    clip = cell.clip or _rect(cell)

    def rim(a0, a1):
        n = max(1, math.ceil(abs(a1 - a0) / (2 * math.pi) * _ARC))
        return [(ox + R * math.cos(a0 + (a1 - a0) * i / n), oy + R * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

    if abs(ox - clip.x) < _TOL:
        pts = rim(_UP, _DOWN) + (rose.arc(_DOWN, _UP) if rose else [])
    elif abs(ox - clip.x - clip.w) < _TOL:
        pts = rim(3 * _UP, _UP) + (rose.arc(_UP, 3 * _UP) if rose else [])
    elif rose is None and abs(oy - clip.y) < _TOL:
        # Centred on the floor: the half standing on it (a sunburst).
        pts = rim(0.0, math.pi)
    elif rose is None and abs(oy - clip.y - clip.h) < _TOL:
        # Centred on the ceiling: the half hanging from it (a shingle's butt).
        pts = rim(math.pi, 2 * math.pi)
    else:
        pts = rim(_UP, _UP - 2 * math.pi)
        if rose is not None:
            pts += rose.arc(_UP, _UP + 2 * math.pi) + [(ox, oy + R)]
    return [_close(pts)]


def _pieces(solid: _Solid) -> list[Mark]:
    roses = _roses(solid.discs, solid.where)
    cell = solid.cell
    polys = _round_pieces(solid, roses) if cell.centre is not None else _profile_pieces(solid, roses)
    room = cell.clip if cell.centre is not None and cell.clip is not None else _rect(cell)
    out = []
    for pts in polys:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        at = Scope(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        if not _inside(room, at):
            raise OutsideParent(
                f"{solid.where} drew {solid.label} at {at} outside its cell {room}. A grown mark stays inside the "
                "cell its module draws in"
            )
        out.append(Mark(solid.label, at, {**solid.attrs, "points": pts}, solid.module))
    return out


# --- the interpreter --------------------------------------------------------------


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
    """Draw a grown string into ``scope``, in order. An outline is drawn
    where it was made in that order, once every piercing of it is known."""
    drawn: list = []

    def run(items: list, cell: Cell, solids: list) -> None:
        pending: list[Cell] = []
        replicate: list[Cell] | None = None
        for item in items:
            if isinstance(item, list):
                if replicate is not None:
                    for part in replicate:
                        run(item, part, list(solids))
                    replicate = None
                elif pending:
                    run(item, pending.pop(0), list(solids))
                else:
                    run(item, cell, list(solids))
                continue
            how = system.interpret.get(item.symbol)
            if how is None:
                continue
            if len(how.formals) != len(item.args):
                raise GrowError(f"{system.id}: {item} is interpreted as {item.symbol}{how.formals}")
            for step in how.steps:
                cell, made = _draw(system, step, item, how, cell, params, lookup, functions, drawn, solids)
                if made is not None:
                    kind, parts = made
                    if kind == "split":
                        pending, replicate = parts, None
                    else:
                        pending, replicate = [], parts

    run(_tree(string), _cell(scope), [])
    marks: list[Mark] = []
    for entry in drawn:
        marks.extend(_pieces(entry) if isinstance(entry, _Solid) else [entry])
    if len(marks) > MAX_MARKS:
        raise GrowError(f"{system.id}: drew {len(marks)} marks, more than {MAX_MARKS}")
    return marks


def _draw(system, step: Draw, module: Module, how: Interpretation, cell: Cell, params, lookup, functions, marks, solids):
    where = f"{system.id}: {module}"
    base = {**dict(cell.names), **_bind(how.formals, module), "cw": cell.w, "ch": cell.h}
    if cell.centre is not None:
        base["cr"] = cell.radius
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
        f = step.fields
        v = step.verb
        if v in ("split", "repeat"):
            if "n" in f:
                weights = [1.0] * int(ev(f["n"]))
            else:
                weights = ev(f["weights"])
            made = (v, [_cell(p, cell, step.axis) for p in _parts(cell, step.axis, weights, where)])
        elif v == "inset":
            d = ev(f["inset"])
            l, b, r, t = (d, d, d, d) if not isinstance(d, (list, tuple)) else d
            if l + r > cell.w + _TOL or b + t > cell.h + _TOL:
                raise GrowError(f"{where}: inset {d} is larger than its cell {cell}")
            inner = Scope(cell.x + l, cell.y + b, max(0.0, cell.w - l - r), max(0.0, cell.h - b - t))
            cell = Cell(inner.x, inner.y, inner.w, inner.h,
                        floor=_clip_profile(tuple((x, y + b) for x, y in cell.floor), inner.x, inner.x + inner.w),
                        ceil=_clip_profile(tuple((x, y - t) for x, y in cell.ceil), inner.x, inner.x + inner.w),
                        names=cell.names)
        elif v == "place":
            x, y, w, h = (float(ev(a)) for a in f["at"])
            _mark(marks, step.label, Scope(cell.x + x, cell.y + y, w, h), cell, ev, step, module, where, {})
        elif v == "line":
            x0, y0, x1, y1 = (float(ev(a)) for a in f["line"])
            width = float(ev(f["width"]))
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
        elif v == "over":
            span = float(ev(f["span"]))
            curves = _arcade(
                str(ev(f["over"])), cell.x + float(ev(f.get("start", 0.0))), span, float(ev(f.get("pitch", span))),
                int(ev(f.get("count", 1))), cell.y + float(ev(f.get("spring", 0.0))), float(ev(f["rise"])),
                float(ev(f.get("band", 0.0))), float(ev(f.get("finial", 0.0))),
            )
            floor = _envelope(curves, _floor(cell), cell.x, cell.x + cell.w)
            ceil = _ceil(cell)
            if any(y > _height(ceil, x, min) + _TOL for x, y in floor):
                raise GrowError(f"{where}: the arches it stands over rise out of its cell {_rect(cell)}")
            cell = Cell(cell.x, cell.y, cell.w, cell.h, floor=floor, ceil=cell.ceil, names=cell.names)
        elif v == "arch":
            rise = float(ev(f["rise"]))
            if not 0.0 < rise <= cell.h + _TOL:
                raise GrowError(f"{where}: an arch rising {rise} does not fit its cell {_rect(cell)}")
            head = head_outline(cell.x, cell.y + cell.h - rise, cell.w, rise, str(ev(f["arch"])))
            cell = Cell(cell.x, cell.y, cell.w, cell.h, floor=cell.floor, ceil=tuple(head), names=cell.names)
        elif v == "round":
            r0 = r = float(ev(f["round"]))
            clear = None if "fit" not in f else float(ev(f["fit"]))
            while True:
                fit_scope = _Scope({**bound, "r": r}, params, lookup)
                cx, cy = (float(e(fit_scope, functions)) for e in f["at"])
                cx, cy = cell.x + cx, cell.y + cy
                if clear is None or (
                    _distance(cx, cy, _floor(cell)) >= r + clear and _distance(cx, cy, _ceil(cell)) >= r + clear
                ):
                    break
                r -= 0.01
                if r < 0.25 * r0:
                    raise GrowError(f"{where}: no round cell from {r0} down to a quarter of it fits its cell {_rect(cell)}")
            cell = Cell(cx - r, cy - r, 2 * r, 2 * r, centre=(cx, cy), radius=r,
                        clip=cell.clip if cell.centre is not None else _rect(cell), names=cell.names)
        elif v == "ring":
            n, d, size = int(ev(f["ring"])), float(ev(f["radius"])), float(ev(f["size"]))
            start = float(ev(f.get("start", 90.0)))
            ox, oy = cell.centre if cell.centre is not None else (cell.x + cell.w / 2.0, cell.y + cell.h / 2.0)
            clip = cell.clip if cell.centre is not None else _rect(cell)
            parts = []
            for k in range(n):
                angle = start + 360.0 * k / n
                px, py = ox + d * math.cos(math.radians(angle)), oy + d * math.sin(math.radians(angle))
                parts.append(Cell(px - size / 2.0, py - size / 2.0, size, size, centre=(px, py), radius=size / 2.0,
                                  clip=clip, names=(*cell.names, ("angle", angle))))
            made = ("ring", parts)
        elif v == "outline":
            solid = _Solid(step.label, cell, {k: ev(e) for k, e in step.attrs.items()}, module, where)
            marks.append(solid)
            solids.append(solid)
        elif v == "pierce":
            if not solids:
                raise GrowError(f"{where}: a pierce with no outline round it to cut")
            r = float(ev(f["pierce"]))
            if "at" in f:
                cx, cy = (cell.x + float(ev(a)) for a in f["at"])
            else:
                cx, cy = cell.centre if cell.centre is not None else (cell.x + cell.w / 2.0, cell.y + cell.h / 2.0)
            if r > 0.0:
                solids[-1].discs.append((cx, cy, r))
        elif v == "polygon":
            pts = tuple((round(cell.x + float(px), 6), round(cell.y + float(py), 6)) for px, py in ev(f["points"]))
            if len(pts) < 3:
                raise GrowError(f"{where}: a polygon has at least three points")
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            at = Scope(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            _mark(marks, step.label, at, cell.clip if cell.centre is not None and cell.clip is not None else cell,
                  ev, step, module, where, {"points": pts + ((pts[0],) if pts[0] != pts[-1] else ())})
    return cell, made


def _mark(marks, label, at: Scope, cell: Scope, ev, step: Draw, module: Module, where: str, extra) -> None:
    if at.w < -_TOL or at.h < -_TOL:
        raise GrowError(f"{where}: a {label} of negative size {at}")
    if not _inside(cell, at):
        raise OutsideParent(
            f"{where} drew {label} at {at} outside its cell {_rect(cell)}. A grown mark stays inside the "
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
