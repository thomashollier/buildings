"""Shapes and scopes: the nodes a split grammar rewrites.

A **shape** is a labelled region of space -- its **scope** -- plus the
attributes rules have given it. Where an L-system rewrites a string of
size-less symbols and draws them afterwards, a split grammar rewrites shapes
that already know where they are and how big they are, so a rule can read its
own extent ("this facade is 14 m wide") and its neighbours' ("the storey under
me is taller than I am") before it decides anything.

Scopes are in the facade plane for now -- metres, origin at pavement level at
the left edge of the parcel, +x right, +y up, the same convention as the IR.
That is the one level the Paris typology needs; a massing stage would add the
third axis here, not somewhere else.

Shapes are built by ``derive`` and nowhere else. Each is written only by the
rules that fire on it, and only while it is being derived; after that the
derivation never touches it again, which is I1 restated for a tree: a rule may
read any shape that already exists, and may write only the one in hand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

from buildings.trace import TraceEntry

__all__ = ["X", "Y", "Attributes", "LockedAttributes", "Scope", "Part", "Shape"]

#: The two split axes of the facade plane.
X = "x"
Y = "y"

_MISSING = object()


@dataclass(frozen=True)
class Scope:
    """An axis-aligned rectangle in the facade plane."""

    x: float
    y: float
    w: float
    h: float

    def extent(self, axis: str) -> float:
        return self.w if axis == X else self.h

    def start(self, axis: str) -> float:
        return self.x if axis == X else self.y

    def contains(self, other: Scope, tol: float = 1e-6) -> bool:
        return (
            other.x >= self.x - tol
            and other.y >= self.y - tol
            and other.x + other.w <= self.x + self.w + tol
            and other.y + other.h <= self.y + self.h + tol
        )

    def slice(self, axis: str, start: float, size: float) -> Scope:
        """The sub-scope running ``size`` along ``axis`` from ``start``, and the
        whole of this scope across it."""
        if axis == X:
            return Scope(start, self.y, size, self.h)
        return Scope(self.x, start, self.w, size)


@dataclass(frozen=True)
class Part:
    """One piece of a split: what it will be called and how much it takes.

    ``size`` is resolved before the split -- by a fixed number, a solver, or a
    Paris size function -- because a split partitions, and a partition whose
    pieces are still negotiating is not one. ``name`` is the child's id
    segment; ``attrs`` are handed to the child as its starting attributes.
    """

    label: str
    size: float
    name: str
    attrs: Mapping[str, Any] = field(default_factory=dict)


class LockedAttributes(Exception):
    """A rule wrote an attribute of a shape that is not the one in hand."""


class Attributes(dict):
    """A shape's attributes: readable by anyone, writable only while unlocked.

    The derivation unlocks a shape for exactly two things -- its own attribute
    stage, and the body of the production expanding it -- and locks it again
    straight after. So a rule refining a keystone cannot reach sideways and
    change the window it sits on: the write raises, naming both shapes.
    """

    __slots__ = ("owner", "locked")

    def __init__(self, owner: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.locked = False

    def _guard(self) -> None:
        if self.locked:
            raise LockedAttributes(
                f"attributes of {self.owner} are locked: a rule may write only the "
                "shape it is deriving, and only while it is deriving it"
            )

    def __setitem__(self, key, value) -> None:
        self._guard()
        super().__setitem__(key, value)

    def __delitem__(self, key) -> None:
        self._guard()
        super().__delitem__(key)

    def update(self, *args, **kwargs) -> None:
        self._guard()
        super().update(*args, **kwargs)

    def setdefault(self, key, default=None):
        self._guard()
        return super().setdefault(key, default)

    def pop(self, *args):
        self._guard()
        return super().pop(*args)

    def clear(self) -> None:
        self._guard()
        super().clear()


class Shape:
    """A node of the derivation tree."""

    __slots__ = (
        "label",
        "scope",
        "id",
        "parent",
        "index",
        "attrs",
        "resolution",
        "children",
        "trace",
        "rule",
    )

    def __init__(
        self,
        label: str,
        scope: Scope,
        id: str,
        *,
        parent: Shape | None = None,
        index: int = 0,
        attrs: Mapping[str, Any] | None = None,
    ) -> None:
        self.label = label
        self.scope = scope
        self.id = id
        self.parent = parent
        self.index = index
        self.attrs = Attributes(id, attrs or {})
        #: The attribute stage's full result (winners and losers), when one ran.
        self.resolution: object = None
        self.children: list[Shape] = []
        self.trace: list[TraceEntry] = []
        #: The production that expanded this shape, or ``None`` for a terminal.
        self.rule: str | None = None

    # --- context queries ---------------------------------------------------

    @property
    def siblings(self) -> list[Shape]:
        """Every shape the parent's split produced, this one included, in order."""
        return self.parent.children if self.parent is not None else [self]

    def ancestor(self, label: str) -> Shape:
        node = self.parent
        while node is not None:
            if node.label == label:
                return node
            node = node.parent
        raise LookupError(f"{self.id} ({self.label}) has no {label!r} above it")

    def attr(self, key: str, default: Any = _MISSING) -> Any:
        """This shape's attribute, or the nearest ancestor's (CGA's attribute
        inheritance): a fact stated on the facade is visible to every cell."""
        node: Shape | None = self
        while node is not None:
            if key in node.attrs:
                return node.attrs[key]
            node = node.parent
        if default is _MISSING:
            raise KeyError(f"{key!r} is set on neither {self.id} nor any shape above it")
        return default

    def walk(self) -> Iterator[Shape]:
        yield self
        for child in self.children:
            yield from child.walk()

    @property
    def is_terminal(self) -> bool:
        return self.rule is None

    def __repr__(self) -> str:
        s = self.scope
        return (
            f"Shape({self.label} {self.id!r} @ x={s.x:.3f} y={s.y:.3f} "
            f"w={s.w:.3f} h={s.h:.3f}, {len(self.children)} children)"
        )


def total(parts: list[Part]) -> float:
    return math.fsum(p.size for p in parts)
