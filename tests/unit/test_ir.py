from __future__ import annotations

import random

import pytest

from buildings.quantity import Kind, Quantity, Reg
from buildings.ir.nodes import (
    CONCRETE_NODE_KINDS,
    BalconyNode,
    BayNode,
    BuildingNode,
    CorniceNode,
    DormerNode,
    IronworkNode,
    KeystoneNode,
    Node,
    OpeningNode,
    RoofNode,
    ShopfrontNode,
    SilhouetteNode,
    SocleNode,
    SpecialNode,
    StoreyNode,
    StringCourseNode,
    SurroundNode,
)
from buildings.ir.serial import from_json, to_json
from buildings.trace import TraceEntry


def _entry(rule: str = "paris.structure.storey.solve") -> TraceEntry:
    return TraceEntry(rule=rule, phase="structure", detail="filled the height budget", inputs={"budget": 30.0})


def test_node_requires_non_empty_trace() -> None:
    with pytest.raises(ValueError):
        Node(id="n0", kind="building", trace=())


def test_base_node_kind_is_whatever_was_passed() -> None:
    n = Node(id="n0", kind="anything", trace=(_entry(),))
    assert n.kind == "anything"


@pytest.mark.parametrize("cls", CONCRETE_NODE_KINDS)
def test_concrete_node_pins_its_own_kind(cls: type[Node]) -> None:
    # pass an intentionally wrong kind string; construction must correct it
    n = cls(id="x", kind="WRONG", trace=(_entry(),))
    assert n.kind != "WRONG"
    assert n.kind != ""


def test_expected_kind_strings() -> None:
    expected = {
        BuildingNode: "building",
        StoreyNode: "storey",
        BayNode: "bay",
        OpeningNode: "opening",
        SurroundNode: "surround",
        BalconyNode: "balcony",
        CorniceNode: "cornice",
        StringCourseNode: "string_course",
        SocleNode: "socle",
        ShopfrontNode: "shopfront",
        RoofNode: "roof",
        DormerNode: "dormer",
        SilhouetteNode: "silhouette",
        IronworkNode: "ironwork",
        KeystoneNode: "keystone",
        SpecialNode: "special",
    }
    for cls, kind in expected.items():
        n = cls(id="x", kind="", trace=(_entry(),))
        assert n.kind == kind


def test_node_children_and_props_are_immutable_containers() -> None:
    n = Node(id="n0", kind="building", trace=(_entry(),), children=[], props={"x": 1.0})
    assert isinstance(n.children, tuple)
    with pytest.raises(TypeError):
        n.props["x"] = 2.0  # type: ignore[index]


def test_node_is_frozen() -> None:
    n = Node(id="n0", kind="building", trace=(_entry(),))
    with pytest.raises(Exception):
        n.id = "other"  # type: ignore[misc]


def test_extent_props_convention() -> None:
    n = StoreyNode(
        id="storey/2",
        kind="storey",
        trace=(_entry(),),
        props={"x": 0.0, "y": 6.4, "w": 18.0, "h": 3.1},
    )
    assert n.props["x"] == 0.0
    assert n.props["y"] == 6.4
    assert n.props["w"] == 18.0
    assert n.props["h"] == 3.1


def _sample_tree() -> BuildingNode:
    opening = OpeningNode(
        id="bay/0/opening",
        kind="opening",
        trace=(_entry("paris.qualify.opening.window"),),
        props={"x": 0.5, "y": 0.0, "w": 1.2, "h": 2.4},
    )
    surround = SurroundNode(
        id="bay/0/opening/surround",
        kind="surround",
        trace=(_entry("paris.qualify.surround.plain"),),
        props={"x": 0.4, "y": 0.0, "w": 1.4, "h": 2.6},
    )
    balcony = BalconyNode(
        id="storey/2/balcony",
        kind="balcony",
        trace=(_entry("paris.qualify.balcony.ordonnance_1823"),),
        props={"x": 0.0, "y": 6.4, "w": 18.0, "h": 0.1, "projection": 0.8},
    )
    bay = BayNode(
        id="bay/0",
        kind="bay",
        trace=(_entry("paris.structure.bay.solve"),),
        children=(opening, surround),
        props={"x": 0.0, "y": 0.0, "w": 3.2, "h": 3.1},
    )
    storey = StoreyNode(
        id="storey/2",
        kind="storey",
        trace=(_entry("paris.roles.principal.tallest"),),
        children=(bay, balcony),
        props={"x": 0.0, "y": 6.4, "w": 18.0, "h": 3.1},
    )
    cornice = CorniceNode(
        id="cornice",
        kind="cornice",
        trace=(_entry("paris.reglement.cornice_height"),),
        props={"x": 0.0, "y": 20.0, "w": 18.0, "h": 0.6},
    )
    silhouette = SilhouetteNode(
        id="silhouette",
        kind="silhouette",
        trace=(_entry("paris.terminate.silhouette"),),
        props={"points": [[0.0, 20.0], [18.0, 20.0], [9.0, 28.5]]},
    )
    return BuildingNode(
        id="building",
        kind="building",
        trace=(_entry("paris.structure.envelope"),),
        children=(storey, cornice, silhouette),
        props={"x": 0.0, "y": 0.0, "w": 18.0, "h": 28.5},
    )


def test_roundtrip_full_tree() -> None:
    tree = _sample_tree()
    restored = from_json(to_json(tree))
    assert restored == tree
    assert type(restored) is BuildingNode
    assert type(restored.children[0]) is StoreyNode
    assert type(restored.children[0].children[0]) is BayNode
    assert type(restored.children[0].children[0].children[0]) is OpeningNode


@pytest.mark.parametrize("cls", CONCRETE_NODE_KINDS)
def test_roundtrip_every_concrete_node_kind(cls: type[Node]) -> None:
    n = cls(
        id=f"{cls.__name__}/0",
        kind="ignored",
        trace=(_entry(f"paris.test.{cls.__name__.lower()}"),),
        props={"x": 1.0, "y": 2.0, "w": 3.0, "h": 4.0, "note": "sample", "flag": True, "count": 3},
    )
    restored = from_json(to_json(n))
    assert restored == n
    assert type(restored) is cls
    assert restored.trace == n.trace


def test_roundtrip_preserves_trace_contents() -> None:
    entry = TraceEntry(
        rule="paris.qualify.balcony.ordonnance_1823",
        phase="qualification",
        detail="floor >= 6m above pavement",
        inputs={"level_above_pavement": 6.4, "threshold": 6.0},
    )
    n = BalconyNode(id="b", kind="balcony", trace=(entry,))
    restored = from_json(to_json(n))
    assert restored.trace[0].rule == entry.rule
    assert restored.trace[0].phase == entry.phase
    assert restored.trace[0].detail == entry.detail
    assert dict(restored.trace[0].inputs) == dict(entry.inputs)


def test_roundtrip_unknown_type_raises() -> None:
    import json

    payload = json.loads(to_json(BuildingNode(id="b", kind="building", trace=(_entry(),))))
    payload["__type__"] = "NotARealNodeType"
    with pytest.raises(ValueError):
        from_json(json.dumps(payload))


def test_to_json_is_deterministic() -> None:
    tree = _sample_tree()
    assert to_json(tree) == to_json(tree)


# --- A1.4: sequences must round-trip losslessly ----------------------------


def test_roundtrip_tuple_props_survive_as_tuples() -> None:
    # This is exactly S7's payload: a polyline of (x, y) pairs.
    n = SilhouetteNode(
        id="silhouette",
        kind="silhouette",
        trace=(_entry("paris.terminate.silhouette"),),
        props={"points": ((0.0, 0.0), (1.0, 5.0))},
    )
    restored = from_json(to_json(n))
    assert restored == n
    assert restored.props["points"] == ((0.0, 0.0), (1.0, 5.0))
    assert isinstance(restored.props["points"], tuple)
    assert isinstance(restored.props["points"][0], tuple)


def test_roundtrip_nested_tuple_and_dict_props() -> None:
    n = SpecialNode(
        id="special",
        kind="special",
        trace=(_entry("paris.test.special"),),
        props={
            "outline": (
                (0.0, 0.0),
                (1.0, 1.0),
                ((2.0, 2.0), (3.0, 3.0)),  # tuple of tuples nested inside a tuple
            ),
            "meta": {"tags": ("a", "b"), "count": 2},
        },
    )
    restored = from_json(to_json(n))
    assert restored == n
    assert restored.props["outline"][2] == ((2.0, 2.0), (3.0, 3.0))
    assert isinstance(restored.props["meta"]["tags"], tuple)


# --- A1.4: Quantity must round-trip losslessly with kind + citation intact -


def test_roundtrip_quantity_in_props_does_not_raise() -> None:
    n = BalconyNode(
        id="storey/2/balcony",
        kind="balcony",
        trace=(_entry("paris.qualify.balcony.ordonnance_1823"),),
        props={"min_height": Reg(6.0, "ordonnance de 1823")},
    )
    restored = from_json(to_json(n))  # must not raise TypeError
    assert restored == n
    q = restored.props["min_height"]
    assert isinstance(q, Quantity)
    assert q.kind is Kind.REGULATORY
    assert q.value == pytest.approx(6.0)
    assert q.why == "ordonnance de 1823"


def test_roundtrip_quantity_in_trace_inputs_does_not_raise() -> None:
    entry = TraceEntry(
        rule="paris.qualify.balcony.ordonnance_1823",
        phase="qualification",
        detail="floor >= 6m above pavement",
        inputs={"limit": Reg(6.0, "ordonnance de 1823")},
    )
    n = BalconyNode(id="b", kind="balcony", trace=(entry,))
    restored = from_json(to_json(n))  # must not raise TypeError
    limit = restored.trace[0].inputs["limit"]
    assert isinstance(limit, Quantity)
    assert limit.kind is Kind.REGULATORY
    assert limit.value == pytest.approx(6.0)
    assert limit.why == "ordonnance de 1823"


def test_roundtrip_nested_quantity_inside_a_dict_prop() -> None:
    n = BalconyNode(
        id="b",
        kind="balcony",
        trace=(_entry(),),
        props={"limits": {"height": Reg(6.0, "1823 ordonnance"), "projection": Reg(0.8, "1823 ordonnance")}},
    )
    restored = from_json(to_json(n))
    assert restored == n
    assert restored.props["limits"]["height"].kind is Kind.REGULATORY
    assert restored.props["limits"]["projection"].value == pytest.approx(0.8)


def _random_json_safe_value(rng: random.Random, depth: int = 0):
    """Build a nested structure of the shapes the IR actually carries:
    floats, strings, bools, None, Quantity, and nested lists/tuples/dicts of
    the same -- used to fuzz the round-trip property."""
    if depth >= 3:
        choices = ["leaf"]
    else:
        choices = ["leaf", "list", "dict"]
    shape = rng.choice(choices)
    if shape == "list":
        return tuple(_random_json_safe_value(rng, depth + 1) for _ in range(rng.randint(0, 3)))
    if shape == "dict":
        return {
            f"k{i}": _random_json_safe_value(rng, depth + 1)
            for i in range(rng.randint(0, 3))
        }
    leaf_kind = rng.choice(["float", "str", "bool", "none", "quantity"])
    if leaf_kind == "float":
        return rng.uniform(-100.0, 100.0)
    if leaf_kind == "str":
        return rng.choice(["a", "bay", "1823 ordonnance", ""])
    if leaf_kind == "bool":
        return rng.choice([True, False])
    if leaf_kind == "none":
        return None
    return Quantity(rng.uniform(0.0, 30.0), rng.choice(list(Kind)), "fuzz")


@pytest.mark.parametrize("seed", range(20))
def test_roundtrip_property_over_nested_structures(seed: int) -> None:
    rng = random.Random(seed)
    props = {f"p{i}": _random_json_safe_value(rng, 1) for i in range(4)}
    n = SpecialNode(id="s", kind="special", trace=(_entry(),), props=props)
    restored = from_json(to_json(n))
    assert restored == n


# --- A1.5: hashability -------------------------------------------------


def test_node_is_hashable() -> None:
    n = _sample_tree()
    assert isinstance(hash(n), int)


def test_trace_entry_is_hashable() -> None:
    e = TraceEntry(rule="r", phase="structure", detail="d", inputs={"x": 1.0})
    assert isinstance(hash(e), int)


def test_node_with_quantity_in_props_is_hashable() -> None:
    n = BalconyNode(
        id="b", kind="balcony", trace=(_entry(),), props={"min_height": Reg(6.0, "1823 ordonnance")}
    )
    assert isinstance(hash(n), int)


def test_nodes_usable_in_a_set() -> None:
    a = _sample_tree()
    b = _sample_tree()  # structurally identical, separately constructed
    c = BuildingNode(id="other", kind="building", trace=(_entry(),))
    s = {a, b, c}
    assert len(s) == 2  # a and b are equal (and equally hashed); c is distinct
    assert a in s and c in s


def test_props_mapping_still_rejects_item_assignment() -> None:
    n = Node(id="n0", kind="building", trace=(_entry(),), props={"x": 1.0})
    with pytest.raises(TypeError):
        n.props["x"] = 2.0  # type: ignore[index]
