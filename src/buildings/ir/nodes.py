"""The IR node vocabulary.

Geometry convention: **metres, origin at pavement level at the left edge of
the parcel, +x right, +y up.** Every node with extent carries `x`, `y`, `w`,
`h` in `props` — there is no separate geometry field, because `props` is
already the sparse, sink-for-everything-else bag and a second parallel
geometry field would just invite the two to disagree.

`trace` is non-empty on every node, enforced in `Node.__post_init__` (I4): a
node with no trace is a bug, not a valid IR node, and construction raises
rather than letting one slip through to be discovered later by a test walking
the tree.

`children` and `props` are defensively frozen in `__post_init__` (a tuple and
a `trace.FrozenMapping` respectively) even though the dataclass itself is
frozen — `frozen=True` only stops *reassignment* of a field, not mutation of
a mutable object a field happens to point at. Without this, a caller handing
in a list or a plain dict could still mutate a node after construction,
silently violating I1 for whichever earlier phase built it.

`FrozenMapping` (rather than `MappingProxyType`, used previously) is what
makes `Node` genuinely hashable (A1.5): `MappingProxyType` itself has no
`__hash__`, so a `props` field of that type made `hash(Node(...))` raise —
surprising for a frozen dataclass, which is normally hashable — even though
putting nodes in a set is a reasonable thing for later code (block, trace
layers) to want to do.

Each concrete subclass fixes its own `kind` string in `__post_init__`,
overriding whatever was passed at construction. This exists so the string tag
is a property of the *class* the way an enum variant is, not something a
caller can typo or forget to set to the wrong sibling's value, while still
keeping subclasses free of any field the base `Node` doesn't already declare
(CONTRACTS.md gives every concrete kind the same field set).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from buildings.trace import FrozenMapping, TraceEntry


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    trace: tuple[TraceEntry, ...]  # NON-EMPTY (I4)
    children: tuple[Node, ...] = ()
    props: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace", tuple(self.trace))
        if not self.trace:
            raise ValueError(
                f"Node {self.id!r} (kind={self.kind!r}) has an empty trace — "
                "every emitted element must record the rule that produced it (I4)"
            )
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "props", FrozenMapping(self.props))


def _fixed_kind(name: str):
    """Build the `__post_init__` override a concrete subclass uses to pin
    its `kind` string, regardless of what was passed at construction."""

    def __post_init__(self: Node) -> None:  # noqa: N807 - dataclass hook name
        Node.__post_init__(self)
        object.__setattr__(self, "kind", name)

    return __post_init__


@dataclass(frozen=True)
class BuildingNode(Node):
    __post_init__ = _fixed_kind("building")


@dataclass(frozen=True)
class StoreyNode(Node):
    __post_init__ = _fixed_kind("storey")


@dataclass(frozen=True)
class BayNode(Node):
    __post_init__ = _fixed_kind("bay")


@dataclass(frozen=True)
class OpeningNode(Node):
    __post_init__ = _fixed_kind("opening")


@dataclass(frozen=True)
class SurroundNode(Node):
    __post_init__ = _fixed_kind("surround")


@dataclass(frozen=True)
class BalconyNode(Node):
    __post_init__ = _fixed_kind("balcony")


@dataclass(frozen=True)
class CorniceNode(Node):
    __post_init__ = _fixed_kind("cornice")


@dataclass(frozen=True)
class StringCourseNode(Node):
    __post_init__ = _fixed_kind("string_course")


@dataclass(frozen=True)
class SocleNode(Node):
    __post_init__ = _fixed_kind("socle")


@dataclass(frozen=True)
class ShopfrontNode(Node):
    __post_init__ = _fixed_kind("shopfront")


@dataclass(frozen=True)
class RoofNode(Node):
    __post_init__ = _fixed_kind("roof")


@dataclass(frozen=True)
class DormerNode(Node):
    __post_init__ = _fixed_kind("dormer")


@dataclass(frozen=True)
class BrisisWindowNode(Node):
    """A window in the PLANE of the brisis, not a dormer standing out of it.

    A19.2. Where a comble holds more than one garret storey, the lowest one's
    openings are windows in the roof's own face — sill, surround and
    garde-corps flush with the slope — because a brisis steep enough to carry
    two storeys is a wall that happens to be roof, and both deep-comble plates
    in the corpus build and face it as one. Only the register under the eaves
    is ever a lucarne.

    A separate kind rather than a ``dormer`` with a flag, because it is a
    different object: it has no cheeks, no roof of its own, and nothing to cast
    a shadow onto the slope.
    """

    __post_init__ = _fixed_kind("brisis_window")


@dataclass(frozen=True)
class SilhouetteNode(Node):
    __post_init__ = _fixed_kind("silhouette")


@dataclass(frozen=True)
class IronworkNode(Node):
    __post_init__ = _fixed_kind("ironwork")


@dataclass(frozen=True)
class KeystoneNode(Node):
    __post_init__ = _fixed_kind("keystone")


@dataclass(frozen=True)
class SpecialNode(Node):
    __post_init__ = _fixed_kind("special")


@dataclass(frozen=True)
class ColumnNode(Node):
    """An engaged column or pilaster on a pier: the cast-iron front's order."""

    __post_init__ = _fixed_kind("column")


CONCRETE_NODE_KINDS: tuple[type[Node], ...] = (
    BuildingNode,
    StoreyNode,
    BayNode,
    OpeningNode,
    SurroundNode,
    BalconyNode,
    CorniceNode,
    StringCourseNode,
    SocleNode,
    ShopfrontNode,
    RoofNode,
    DormerNode,
    BrisisWindowNode,
    SilhouetteNode,
    IronworkNode,
    KeystoneNode,
    SpecialNode,
    ColumnNode,
)
