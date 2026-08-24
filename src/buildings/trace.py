"""The "why is this here?" facility.

Built before the second rule exists, per the brief: a rule system is strictly
harder to debug than a table until any element can be asked which rule
produced it. Defer this and the failure mode is concrete — weeks spent
bisecting rule sets by hand.

Every emitted IR node carries its own `trace: tuple[TraceEntry, ...]`
directly (I4), non-empty by construction (see `ir.nodes.Node.__post_init__`).
`TraceLog` is the separate bookkeeping structure a phase can use *while*
building a tree — accumulating entries keyed by node id as it goes — so that
`explain(node_id)` can answer the question for a human without them having to
walk the IR tree themselves.
"""

from __future__ import annotations

from collections.abc import Mapping as ABCMapping
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

RuleId = str  # stable dotted id, e.g. "paris.qualify.balcony.ordonnance_1823"


def _freeze_value(value: object) -> object:
    """Recursively turn a value into something both immutable and hashable.

    Mappings become `FrozenMapping`; lists/tuples become tuples of
    recursively-frozen elements; everything else (str, int, float, bool,
    None, enums, and already-hashable frozen dataclasses such as
    `quantity.Quantity`) is assumed hashable and passed through unchanged.
    """
    if isinstance(value, ABCMapping):
        return FrozenMapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    return value


class FrozenMapping(ABCMapping):
    """An immutable, genuinely hashable stand-in for `dict`/`MappingProxyType`.

    A1.5: frozen dataclasses are normally hashable, but `MappingProxyType`
    itself is not, so a `props`/`inputs` field of that type silently makes
    `hash(Node(...))` and `hash(TraceEntry(...))` raise — a surprise for any
    later code (block, trace layers) that wants to put nodes in a set.

    Construction deep-freezes: nested dicts/lists become `FrozenMapping`s and
    tuples respectively, so hashing is well-defined all the way down. Two
    `FrozenMapping`s compare and hash equal iff their contents are equal,
    independent of insertion order (matching ordinary dict `==` semantics).
    """

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, object] = ()) -> None:
        items = data.items() if isinstance(data, ABCMapping) else data
        object.__setattr__(self, "_data", {k: _freeze_value(v) for k, v in items})

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"FrozenMapping({self._data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrozenMapping):
            return self._data == other._data
        if isinstance(other, ABCMapping):
            return self._data == dict(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(frozenset(self._data.items()))


@dataclass(frozen=True)
class TraceEntry:
    """One rule's contribution to one node.

    `inputs` is defensively copied into a read-only, hashable `FrozenMapping`
    in `__post_init__` so a frozen dataclass can't be quietly mutated through
    a mutable field — the same discipline `ir.nodes.Node` applies to `props`
    — and so `hash(TraceEntry(...))` works (A1.5).
    """

    rule: RuleId
    phase: str  # "structure" | "roles" | "qualification" | "termination"
    detail: str  # human-readable: what it decided and why
    inputs: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", FrozenMapping(self.inputs))


class TraceLog:
    """Accumulates `TraceEntry` records keyed by node id during a phase.

    Not frozen — this is a working scratchpad a phase writes to while it
    builds a tree, not part of the frozen IR itself. Once a node is
    constructed its own `trace` tuple is the durable, immutable record; this
    log exists to let a phase collect entries incrementally and to let a
    human ask "why does node X look like this?" across the whole run.
    """

    def __init__(self) -> None:
        self._entries: dict[str, list[TraceEntry]] = {}

    def record(self, node_id: str, entry: TraceEntry) -> None:
        self._entries.setdefault(node_id, []).append(entry)

    def explain(self, node_id: str) -> list[TraceEntry]:
        """A real answer to "why is this here?" — every rule that touched
        this node, in the order they fired. Empty list, not an error, if
        the id was never recorded: absence of an opinion is itself
        information."""
        return list(self._entries.get(node_id, ()))

    def all_ids(self) -> list[str]:
        return list(self._entries.keys())
