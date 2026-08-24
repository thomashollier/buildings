"""Lossless JSON round-trip for the IR, from day one.

`to_json` / `from_json` preserve node subclass identity (a `StoreyNode`
serialises and deserialises back to a `StoreyNode`, not a bare `Node`) via an
explicit `"__type__"` tag resolved against a small registry — Python's
`json` module has no notion of a dataclass hierarchy on its own, so the tag
is the only thing standing between "lossless" and "lossy."

Two further gaps (A1.4), both hit by real payloads later stages write:

- **Nested sequences.** JSON has no tuple type, so a tuple placed in
  `Node.props` (e.g. `SilhouetteNode`'s `"points"` polyline — exactly S7's
  payload) would come back as a list, and `from_json(to_json(n)) == n` would
  be `False`. `_decode_value` restores tuples for every JSON array it finds,
  recursively, so the round trip is genuinely lossless for the sequence
  shapes the IR actually carries.
- **`Quantity` values.** A qualification rule recording
  `inputs={"limit": Reg(6.0, "ordonnance de 1823")}` is an obvious and
  intended use of the trace facility. `_encode_value`/`_decode_value` give
  `Quantity` a tagged encoding (kind + value + why) so it survives
  `props`/`inputs` intact instead of raising `TypeError` on `json.dumps`.

Everything else placed in `Node.props` or `TraceEntry.inputs` must still be
JSON-representable (numbers, strings, booleans, `None`, and nested
lists/dicts/tuples of the same, plus `Quantity`); geometry values (`x`, `y`,
`w`, `h`) are plain floats and are unaffected by any of this.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from buildings.ir.nodes import CONCRETE_NODE_KINDS, Node
from buildings.quantity import Kind, Quantity
from buildings.trace import TraceEntry

_REGISTRY: dict[str, type[Node]] = {"Node": Node}
_REGISTRY.update({cls.__name__: cls for cls in CONCRETE_NODE_KINDS})

# Sentinel key marking a tagged `Quantity` encoding. Collides only with a
# prop/input literally named "__quantity__", the same trade-off `__type__`
# already makes for node identity.
_QUANTITY_TAG = "__quantity__"


def _encode_value(value: Any) -> Any:
    """Recursively encode one `props`/`inputs` value to plain JSON-able data.

    `Quantity` -> a tagged dict carrying kind/value/why. Any other `Mapping`
    -> a plain dict of recursively-encoded values. `list`/`tuple` -> a JSON
    array of recursively-encoded elements (tuple-ness itself isn't
    representable in JSON; `_decode_value` restores it on the way back).
    Everything else (numbers, strings, booleans, `None`) passes through.
    """
    if isinstance(value, Quantity):
        return {
            _QUANTITY_TAG: True,
            "value": value.value,
            "kind": value.kind.value,
            "why": value.why,
        }
    if isinstance(value, Mapping):
        return {k: _encode_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode_value(v) for v in value]
    return value


def _decode_value(value: Any) -> Any:
    """Inverse of `_encode_value`.

    A tagged dict decodes back to a `Quantity`. Any other JSON object
    decodes to a plain `dict` (dicts are already lossless across JSON).
    A JSON array decodes to a `tuple` — restoring the tuple-ness JSON itself
    cannot carry — with every element recursively decoded first.
    """
    if isinstance(value, dict):
        if value.get(_QUANTITY_TAG) is True:
            return Quantity(value["value"], Kind(value["kind"]), value["why"])
        return {k: _decode_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return tuple(_decode_value(v) for v in value)
    return value


def _entry_to_obj(entry: TraceEntry) -> dict[str, Any]:
    return {
        "rule": entry.rule,
        "phase": entry.phase,
        "detail": entry.detail,
        "inputs": _encode_value(entry.inputs),
    }


def _entry_from_obj(obj: Mapping[str, Any]) -> TraceEntry:
    return TraceEntry(
        rule=obj["rule"],
        phase=obj["phase"],
        detail=obj["detail"],
        inputs=_decode_value(obj.get("inputs", {})),
    )


def _node_to_obj(node: Node) -> dict[str, Any]:
    return {
        "__type__": type(node).__name__,
        "id": node.id,
        "kind": node.kind,
        "trace": [_entry_to_obj(e) for e in node.trace],
        "children": [_node_to_obj(c) for c in node.children],
        "props": _encode_value(node.props),
    }


def _node_from_obj(obj: Mapping[str, Any]) -> Node:
    type_name = obj["__type__"]
    try:
        cls = _REGISTRY[type_name]
    except KeyError as exc:
        raise ValueError(f"unknown IR node type {type_name!r}") from exc
    trace = tuple(_entry_from_obj(e) for e in obj["trace"])
    children = tuple(_node_from_obj(c) for c in obj["children"])
    return cls(
        id=obj["id"],
        kind=obj["kind"],
        trace=trace,
        children=children,
        props=_decode_value(obj.get("props", {})),
    )


def to_json(node: Node) -> str:
    return json.dumps(_node_to_obj(node))


def from_json(s: str) -> Node:
    return _node_from_obj(json.loads(s))
