"""The derivation: an axiom shape in, a tree of shapes out, then IR.

A grammar is three tables keyed by shape label:

* **productions** -- how a shape of that label is expanded;
* **attribute stages** -- the layered rules that give it properties;
* **interpreters** -- how a finished shape becomes IR nodes, bottom-up, once
  every shape below it has been interpreted. This is the split grammar's
  equivalent of an L-system's turtle: the derivation decides everything, and
  interpretation only writes it down.

The order of work is fixed and stated once:

1. The axiom is attributed.
2. Shapes are expanded depth-first, children in order. Expanding a shape runs
   exactly one production (or none, and it is a terminal).
3. When a production creates children, **all** of them are attributed before
   any is expanded, so a rule can read its siblings.

Nothing else about order is promised, and no rule may depend on it: randomness
comes from ``DecisionStream`` paths, not from a shared sequence, so a rule
added anywhere cannot shift a decision anywhere else (I5).

Every shape records the production that made it and the one that expanded it
(I4); ``derivation.log`` is the whole derivation in order, for a reader who
wants to replay it.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from buildings.cga.rules import AttributeStage, Layer, Production, ProductionConflict, ScopedLayer, everywhere
from buildings.cga.shape import Part, Scope, Shape
from buildings.ir.nodes import Node
from buildings.rng import DecisionStream
from buildings.solver.fitting import FitResult, SlotSpec, solve
from buildings.trace import TraceEntry

__all__ = ["Grammar", "Derivation", "derive", "interpret", "SplitMismatch", "OutsideParent"]

#: A split must partition its scope to within this, in metres.
_SPLIT_TOLERANCE = 1e-6

Interpreter = Callable[[Shape, Sequence[Node], "Derivation"], Sequence[Node]]


class SplitMismatch(ValueError):
    """A split's parts do not add up to the extent they claim to partition."""


class OutsideParent(ValueError):
    """A child shape reaches outside its parent's scope without declaring it."""


@dataclass(frozen=True)
class Grammar:
    name: str
    productions: tuple[Production, ...]
    stages: tuple[AttributeStage, ...] = ()
    interpreters: Mapping[str, Interpreter] = field(default_factory=dict)
    #: Labels allowed to stand outside their parent's scope -- a cornice that
    #: projects, a roof that oversails. Every other child must lie inside its
    #: parent, which is what keeps a sub-part's effects inside the part.
    overhangs: frozenset[str] = frozenset()
    #: Attribute layers with an address: each joins its label's stage only on
    #: the shapes its selector picks. See ``ScopedLayer``.
    overrides: tuple[ScopedLayer, ...] = ()

    # --- editing a grammar ---------------------------------------------------
    # A refinement replaces one entry and leaves the rest untouched, so what
    # changed is exactly what was named.

    def with_production(self, production: Production) -> Grammar:
        """This grammar with ``production`` replacing the one of the same rule
        id, or added if there is none."""
        kept = tuple(p for p in self.productions if p.rule != production.rule)
        return dataclasses.replace(self, productions=(*kept, production))

    def with_interpreter(
        self, label: str, fn: Interpreter, where: Callable[[Shape], bool] | None = None
    ) -> Grammar:
        """This grammar with ``fn`` writing ``label`` -- everywhere, or only on
        the shapes ``where`` picks, the rest keeping the interpreter they had."""
        if where is not None:
            previous = self.interpreters.get(label)

            def scoped(shape: Shape, below: Sequence[Node], d: Derivation) -> Sequence[Node]:
                if where(shape):
                    return fn(shape, below, d)
                return previous(shape, below, d) if previous is not None else below

            return dataclasses.replace(self, interpreters={**self.interpreters, label: scoped})
        return dataclasses.replace(self, interpreters={**self.interpreters, label: fn})

    def with_override(
        self, label: str, layer: Layer, where: Callable[[Shape], bool] = everywhere
    ) -> Grammar:
        """This grammar with ``layer`` joining ``label``'s attribute stage on
        the shapes ``where`` picks, and nowhere else."""
        return dataclasses.replace(
            self, overrides=(*self.overrides, ScopedLayer(label, layer, where))
        )

    def with_stage(self, stage: AttributeStage) -> Grammar:
        """This grammar with ``stage`` replacing the stage for its label."""
        kept = tuple(s for s in self.stages if s.label != stage.label)
        return dataclasses.replace(self, stages=(*kept, stage))

    def productions_for(self, shape: Shape) -> list[Production]:
        return [p for p in self.productions if p.label == shape.label and p.guard(shape)]

    def stages_for(self, label: str) -> list[AttributeStage]:
        return [s for s in self.stages if s.label == label]


class Derivation:
    """The operations a production body may call, and the record of what they did."""

    def __init__(self, grammar: Grammar, rng: DecisionStream) -> None:
        self.grammar = grammar
        self.rng = rng
        self.log: list[TraceEntry] = []
        self._current: Production | None = None

    # --- operations ----------------------------------------------------------

    def split(
        self, shape: Shape, axis: str, parts: Sequence[Part], *, id_base: str | None = None
    ) -> list[Shape]:
        """Cut ``shape`` along ``axis`` into consecutive children, one per part.

        The parts must add up to the shape's extent on that axis: a split
        partitions, and a remainder nobody owns is a defect, not a margin.
        """
        extent = shape.scope.extent(axis)
        size = math.fsum(p.size for p in parts)
        if abs(size - extent) > _SPLIT_TOLERANCE:
            raise SplitMismatch(
                f"{self._rule_id()} split {shape.id} ({shape.label}) along {axis} into "
                f"{len(parts)} part(s) totalling {size:.6f} m, but the shape is "
                f"{extent:.6f} m on that axis"
            )
        cursor = shape.scope.start(axis)
        children: list[Shape] = []
        base = shape.id if id_base is None else id_base
        for part in parts:
            if part.size < -_SPLIT_TOLERANCE:
                raise SplitMismatch(f"part {part.name!r} of {shape.id} has negative size")
            children.append(
                self._child(
                    shape,
                    part.label,
                    shape.scope.slice(axis, cursor, part.size),
                    f"{base}/{part.name}" if part.name else base,
                    part.attrs,
                    detail=f"split {axis} -> {part.label} {part.name!r} {part.size:.3f} m",
                )
            )
            cursor += part.size
        return children

    def insert(
        self,
        shape: Shape,
        label: str,
        scope: Scope,
        name: str,
        attrs: Mapping[str, Any] | None = None,
    ) -> Shape:
        """Add a child that does not partition its parent -- a roof standing on a
        wall, an element applied to a face. CGA's ``i()``, for shapes that are
        derived further rather than inserted as finished geometry."""
        return self._child(
            shape,
            label,
            scope,
            f"{shape.id}/{name}",
            attrs or {},
            detail=f"insert {label} {name!r}",
        )

    def fit(
        self,
        budget: float,
        label: str,
        *,
        end: SlotSpec,
        bay: SlotSpec,
        special: SlotSpec | Sequence[SlotSpec] | None = None,
        fixed: Sequence[tuple[int, SlotSpec]] = (),
        central_feature: bool = False,
        min_bays: int = 1,
        max_bays: int = 24,
    ) -> tuple[list[Part], FitResult]:
        """Size a run of parts with the fitting solver: CGA's repeat split
        (``{ ~w : Bay }*``) done properly. The count is chosen by closeness to
        the preferred module and the slack is absorbed by the solver's ladder,
        not spread evenly. Returns the parts, ready for ``split``, and the
        solver's own account for the trace."""
        result = solve(
            budget,
            end=end,
            bay=bay,
            special=special,
            fixed=fixed,
            central_feature=central_feature,
            min_bays=min_bays,
            max_bays=max_bays,
        )
        parts = [
            Part(label, s.width, f"{s.name}{i}", {"slot": s}) for i, s in enumerate(result.slots)
        ]
        return parts, result

    # --- bookkeeping ---------------------------------------------------------

    def _rule_id(self) -> str:
        return self._current.rule if self._current is not None else "(axiom)"

    def _child(
        self,
        parent: Shape,
        label: str,
        scope: Scope,
        id: str,
        attrs: Mapping[str, Any],
        *,
        detail: str,
    ) -> Shape:
        if label not in self.grammar.overhangs and not parent.scope.contains(scope):
            raise OutsideParent(
                f"{self._rule_id()} put {label} {id!r} at {scope} outside its parent "
                f"{parent.id} ({parent.label}) at {parent.scope}. A part stays inside "
                "the part it refines; declare the label in Grammar.overhangs if it "
                "genuinely projects"
            )
        child = Shape(label, scope, id, parent=parent, index=len(parent.children), attrs=attrs)
        entry = TraceEntry(
            rule=self._rule_id(),
            phase="grammar",
            detail=detail,
            inputs={"parent": parent.id, "label": label},
        )
        child.trace.append(entry)
        self.log.append(entry)
        parent.children.append(child)
        return child

    def attribute(self, shape: Shape) -> None:
        for stage in self.grammar.stages_for(shape.label):
            ctx = stage.context(shape) if stage.context is not None else shape
            local = tuple(
                o.layer
                for o in self.grammar.overrides
                if o.label == shape.label and o.where(shape)
            )
            result = stage.resolver(ctx, (*stage.layers, *local), self.rng)
            shape.attrs.update(result.values)
            shape.resolution = result
        shape.attrs.locked = True

    def expand(self, shape: Shape) -> None:
        matching = self.grammar.productions_for(shape)
        if not matching:
            return
        top = max(p.priority for p in matching)
        winners = [p for p in matching if p.priority == top]
        if len(winners) > 1:
            raise ProductionConflict(
                f"{shape.id} ({shape.label}) matched {len(winners)} productions at "
                f"priority {top}: {[p.rule for p in winners]}. One must be made more "
                "specific (a guard) or given a different priority."
            )
        production = winners[0]
        self._current = production
        shape.attrs.locked = False
        try:
            before = len(shape.children)
            production.body(shape, self)
        finally:
            self._current = None
            shape.attrs.locked = True
        shape.rule = production.rule
        entry = TraceEntry(
            rule=production.rule,
            phase="grammar",
            detail=f"{shape.label} expanded by {production.rule}"
            + (f" -- {production.summary}" if production.summary else ""),
            inputs={"shape": shape.id, "children": len(shape.children) - before},
        )
        shape.trace.append(entry)
        self.log.append(entry)
        # Every sibling of this split is attributed before any is expanded.
        for child in shape.children[before:]:
            self.attribute(child)


def derive(grammar: Grammar, axiom: Shape, rng: DecisionStream) -> tuple[Shape, Derivation]:
    """Expand ``axiom`` until only terminals are left."""
    d = Derivation(grammar, rng)
    d.attribute(axiom)
    stack = [axiom]
    while stack:
        shape = stack.pop()
        d.expand(shape)
        stack.extend(reversed(shape.children))
    return axiom, d


def interpret(shape: Shape, derivation: Derivation) -> list[Node]:
    """The derived tree as IR, bottom-up. A label with no interpreter passes
    its children's nodes through unchanged."""
    below: list[Node] = []
    for child in shape.children:
        below.extend(interpret(child, derivation))
    fn = derivation.grammar.interpreters.get(shape.label)
    if fn is None:
        return below
    return list(fn(shape, below, derivation))
