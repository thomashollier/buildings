"""Rules: what a production is, and how attribute rules are layered.

Two kinds of rule act on a shape, and a split grammar needs both.

* A **production** expands a shape -- splits it into children, inserts a shape
  beside them, or declines to and leaves it a terminal. At most one fires per
  shape: a facade is split into storeys one way, not two. Among the productions
  whose label and guard match, the highest priority wins, and **two at the
  same priority is a conflict and raises**, for the same reason the attribute
  layers do: picking silently is how a rule system becomes undebuggable.

* An **attribute rule** gives a shape properties without changing its
  geometry. Every applicable one speaks; the opinions are layered (later layer
  wins, then higher specificity, and a tie raises) and the losers are kept so
  the trace can say who nearly won. This is the machinery Paris had in
  ``compose.py``; it moved here unchanged because nothing in it was Paris.

A rule's output is duck-typed: anything with ``values`` (a mapping),
``rule`` (a dotted id, I4) and ``specificity``. Paris returns its own
``Properties``, which also checks keys against its vocabulary; a grammar with
no vocabulary to police returns ``Attrs``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from buildings.rng import DecisionStream
from buildings.trace import RuleId

if TYPE_CHECKING:
    from buildings.cga.derive import Derivation
    from buildings.cga.shape import Shape

__all__ = [
    "Attrs",
    "AttributeRule",
    "AttributeStage",
    "Candidate",
    "Layer",
    "Production",
    "ProductionConflict",
    "RuleConflict",
    "layer_candidates",
    "pick_winners",
    "resolve_layers",
    "ScopedLayer",
    "everywhere",
    "under",
]

#: ``(context, rng) -> result | None``. ``None`` is "no opinion".
AttributeRule = Callable[[Any, DecisionStream], Any]


@dataclass(frozen=True)
class Attrs:
    """A rule's opinion, for grammars with no property vocabulary to check."""

    values: Mapping[str, Any]
    rule: RuleId
    specificity: int = 0


@dataclass(frozen=True)
class Layer:
    """One rule set, and where it sits in the stack.

    A user override is a ``Layer`` like any other, with the highest ``order``.
    There is deliberately no second mechanism for overriding: a parallel
    "force this value" channel would sit outside the trace and outside the
    conflict check, which is exactly where unexplainable output comes from.
    """

    name: str
    order: int
    rules: tuple[AttributeRule, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Layer.name must be non-empty — it appears in every conflict message")
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True)
class Candidate:
    """One rule's opinion about one property — winners and losers alike.

    Losers are kept. "Which rule *nearly* set this, and why did it lose?" is
    the second question anybody debugging a rule set asks, and answering it
    from a discarded value is impossible.
    """

    key: str
    value: object
    rule: RuleId
    layer: str
    order: int
    specificity: int
    func: object = None  # the rule callable, for its docstring

    @property
    def summary(self) -> str:
        """The rule's own account of itself — its docstring's opening
        paragraph, unwrapped. The first *line* is not enough: a rule whose
        summary wraps would be quoted mid-sentence in every trace it appears
        in, which is precisely the sort of small illegibility that makes
        people stop reading the trace."""
        doc = getattr(self.func, "__doc__", None)
        if not doc:
            return ""
        lines: list[str] = []
        for raw in doc.strip().splitlines():
            line = raw.strip()
            if not line:
                break
            lines.append(line)
        return " ".join(lines)


class RuleConflict(Exception):
    """Two rules at the same order and specificity claimed one property.

    Never resolved by picking; always raised. The message names the property,
    every tied rule, and its layer, because that is the whole content of the
    fix: one of them must be made more specific, or they must be merged.
    """



def layer_candidates(
    ctx: Any,
    layers: Sequence[Layer],
    rng: DecisionStream,
    *,
    result_type: type | None = None,
) -> list[Candidate]:
    """Every opinion every rule in every layer has about ``ctx``, in layer order.

    Every rule sees the same frozen ``ctx``; none sees another's output, which
    is what makes the result independent of the order rules are listed in.
    """
    candidates: list[Candidate] = []
    for layer in sorted(layers, key=lambda ly: ly.order):
        for rule in layer.rules:
            props = rule(ctx, rng)
            if props is None:
                continue
            if result_type is not None and not isinstance(props, result_type):
                raise TypeError(
                    f"rule {getattr(rule, '__name__', rule)!r} in layer "
                    f"{layer.name!r} returned {type(props).__name__}; a rule "
                    f"returns {result_type.__name__} or None (no opinion)"
                )
            for key, value in props.values.items():
                candidates.append(
                    Candidate(
                        key=key,
                        value=value,
                        rule=props.rule,
                        layer=layer.name,
                        order=layer.order,
                        specificity=props.specificity,
                        func=rule,
                    )
                )
    return candidates


def pick_winners(candidates: Sequence[Candidate]) -> dict[str, Candidate]:
    """Later layer wins; within a layer, higher specificity wins; a tie raises."""
    winners: dict[str, Candidate] = {}
    for key in sorted({c.key for c in candidates}):
        for_key = [c for c in candidates if c.key == key]
        top = max((c.order, c.specificity) for c in for_key)
        tied = [c for c in for_key if (c.order, c.specificity) == top]
        if len(tied) > 1:
            detail = "\n".join(
                f"    {c.rule}  (layer {c.layer!r}, order {c.order}, "
                f"specificity {c.specificity})  ->  {c.value!r}"
                for c in tied
            )
            raise RuleConflict(
                f"property {key!r} was claimed by {len(tied)} rules at the same "
                f"order ({top[0]}) and the same specificity ({top[1]}):\n{detail}\n"
                "  Nothing here is arbitrary enough to break the tie, and picking "
                "one silently would make this facade look nondeterministic. Either "
                "raise the specificity of the rule that is genuinely narrower, or "
                "merge the two into one rule with one id."
            )
        winners[key] = tied[0]
    return winners


@dataclass(frozen=True)
class Resolved:
    """The generic resolver's result: values, winners and every candidate."""

    values: Mapping[str, Any]
    winners: Mapping[str, Candidate]
    candidates: tuple[Candidate, ...]


def resolve_layers(ctx: Any, layers: Sequence[Layer], rng: DecisionStream) -> Resolved:
    candidates = layer_candidates(ctx, layers, rng)
    winners = pick_winners(candidates)
    return Resolved(
        values={k: c.value for k, c in winners.items()},
        winners=winners,
        candidates=tuple(candidates),
    )


@dataclass(frozen=True)
class AttributeStage:
    """The attribute layers that run on every shape of one label.

    ``context`` turns the shape into whatever the rules read -- the shape
    itself by default, or a typology's own frozen context object. ``resolver``
    layers the opinions; its result must carry ``values``, which are merged
    into the shape's attributes, and is kept whole on ``shape.resolution``.

    A stage runs when its shape is created, and **all the siblings of one split
    are attributed before any of them is expanded** -- so a rule may read its
    siblings' attributes as well as their geometry, which is how a storey
    learns it is the tallest above the base without anyone numbering floors.
    """

    label: str
    layers: tuple[Layer, ...]
    context: Callable[["Shape"], Any] | None = None
    resolver: Callable[[Any, Sequence[Layer], DecisionStream], Any] = resolve_layers


@dataclass(frozen=True)
class Production:
    """``label [: guard] --> body``, with a priority and a traceable id.

    ``body(shape, derivation)`` expands the shape through the derivation's
    operations (``split``, ``insert``, ``fit``); a body that adds no children
    leaves the shape a terminal, which is how a rule says "nothing more here".
    """

    rule: RuleId
    label: str
    body: Callable[["Shape", "Derivation"], None]
    guard: Callable[["Shape"], bool] = field(default=lambda shape: True)
    priority: int = 0

    @property
    def summary(self) -> str:
        doc = getattr(self.body, "__doc__", None) or ""
        lines: list[str] = []
        for raw in doc.strip().splitlines():
            if not raw.strip():
                break
            lines.append(raw.strip())
        return " ".join(lines)


class ProductionConflict(Exception):
    """Two productions at the same priority both matched one shape."""


def everywhere(shape: "Shape") -> bool:
    return True


def under(*shape_ids: str) -> Callable[["Shape"], bool]:
    """A selector for the named shapes and everything derived inside them."""

    def select(shape: "Shape") -> bool:
        node: Shape | None = shape
        while node is not None:
            if node.id in shape_ids:
                return True
            node = node.parent
        return False

    return select


@dataclass(frozen=True)
class ScopedLayer:
    """An attribute layer that joins one label's stage only where ``where``
    holds -- the noble floor, one axis, one building of a block.

    It is resolved with the stage's own layers, by the same rules: its order
    decides whether it outranks them, ties raise, and the losers it beat stay
    in the trace. So a local override is not a second mechanism beside the
    layers; it is a layer with an address. Outside its address it does not
    run at all, which is what keeps it from reaching anything else.
    """

    label: str
    layer: Layer
    where: Callable[["Shape"], bool] = everywhere
