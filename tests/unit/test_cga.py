"""The split-grammar engine, on a grammar that knows nothing about Paris."""

from __future__ import annotations

import pytest

from buildings.cga import (
    Attrs,
    AttributeStage,
    Grammar,
    Layer,
    LockedAttributes,
    OutsideParent,
    Part,
    Production,
    ProductionConflict,
    RuleConflict,
    Scope,
    Shape,
    SplitMismatch,
    X,
    Y,
    derive,
    interpret,
    under,
)
from buildings.ir.nodes import Node
from buildings.rng import DecisionStream
from buildings.solver.fitting import SlotKind, SlotSpec
from buildings.trace import TraceEntry


def _node(shape: Shape, kind: str = "bay") -> Node:
    s = shape.scope
    return Node(
        id=shape.id,
        kind=kind,
        trace=(TraceEntry(rule="test", phase="test", detail=shape.label),),
        props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, **{k: v for k, v in shape.attrs.items() if isinstance(v, (int, float, str))}},
    )


def _floors(box: Shape, d) -> None:
    """A box is three floors."""
    d.split(box, Y, [Part("Floor", 3.0, f"f{i}") for i in range(3)])


def _bays(floor: Shape, d) -> None:
    """A floor is a run of bays the fitting solver sizes."""
    parts, _ = d.fit(
        floor.scope.w,
        "Bay",
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.2, 0.4, 0.8, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, 2.0, 2.5, 3.0),
    )
    d.split(floor, X, parts)


def _tallest(floor: Shape, rng) -> Attrs:
    """A floor knows whether it is the top one by looking at its siblings."""
    return Attrs({"top": floor.index == len(floor.siblings) - 1}, rule="test.top")


def _grammar(**kw) -> Grammar:
    return Grammar(
        name="box",
        productions=(
            Production("box.floors", "Box", _floors),
            Production("box.bays", "Floor", _bays),
        ),
        stages=(AttributeStage("Floor", (Layer("base", 0, (_tallest,)),)),),
        interpreters={"Bay": lambda s, below, d: [_node(s)]},
        **kw,
    )


def _box(w: float = 10.0) -> Shape:
    return Shape("Box", Scope(0.0, 0.0, w, 9.0), "box")


def test_split_partitions_and_the_solver_sizes_a_repeat():
    box, d = derive(_grammar(), _box(), DecisionStream(1))
    floors = box.children
    assert [f.scope.y for f in floors] == [0.0, 3.0, 6.0]
    for f in floors:
        assert sum(b.scope.w for b in f.children) == pytest.approx(10.0)
        assert all(f.scope.contains(b.scope) for b in f.children)
    assert [f.attrs["top"] for f in floors] == [False, False, True]
    nodes = interpret(box, d)
    assert len(nodes) == 3 * len(floors[0].children)


def test_every_shape_says_which_rule_made_it():
    box, d = derive(_grammar(), _box(), DecisionStream(1))
    for shape in box.walk():
        assert shape.trace, shape
    assert box.children[0].trace[0].rule == "box.floors"
    assert box.rule == "box.floors"


def test_a_split_that_does_not_add_up_raises():
    g = _grammar().with_production(
        Production("box.floors", "Box", lambda b, d: d.split(b, Y, [Part("Floor", 3.0, "f0")]))
    )
    with pytest.raises(SplitMismatch):
        derive(g, _box(), DecisionStream(1))


def test_two_productions_at_one_priority_raise():
    g = _grammar().with_production(Production("box.other", "Box", _floors))
    with pytest.raises(ProductionConflict):
        derive(g, _box(), DecisionStream(1))


def test_a_rule_cannot_write_another_shape():
    def meddle(floor: Shape, d) -> None:
        floor.parent.attrs["touched"] = True

    g = _grammar().with_production(Production("box.bays", "Floor", meddle))
    with pytest.raises(LockedAttributes):
        derive(g, _box(), DecisionStream(1))


def test_a_child_outside_its_parent_raises_unless_declared():
    def overhang(floor: Shape, d) -> None:
        s = floor.scope
        d.insert(floor, "Cornice", Scope(s.x - 0.3, s.y + s.h, s.w + 0.6, 0.4), "cornice")

    g = _grammar().with_production(Production("box.bays", "Floor", overhang))
    with pytest.raises(OutsideParent):
        derive(g, _box(), DecisionStream(1))
    import dataclasses

    derive(dataclasses.replace(g, overhangs=frozenset({"Cornice"})), _box(), DecisionStream(1))


def test_an_addressed_override_runs_only_where_addressed():
    def mark(floor, rng):
        return Attrs({"marked": True}, rule="test.mark")

    g = _grammar().with_override("Floor", Layer("local", 10, (mark,)), where=under("box/f1"))
    box, _ = derive(g, _box(), DecisionStream(1))
    assert [f.attrs.get("marked", False) for f in box.children] == [False, True, False]


def test_an_override_outranks_by_order_and_ties_raise():
    def not_top(floor, rng):
        return Attrs({"top": False}, rule="test.not_top")

    box, _ = derive(
        _grammar().with_override("Floor", Layer("later", 10, (not_top,))), _box(), DecisionStream(1)
    )
    assert not any(f.attrs["top"] for f in box.children)
    with pytest.raises(RuleConflict):
        derive(
            _grammar().with_override("Floor", Layer("same", 0, (not_top,))),
            _box(),
            DecisionStream(1),
        )


def test_a_scoped_interpreter_leaves_everything_else_alone():
    plain_box, plain = derive(_grammar(), _box(), DecisionStream(1))
    before = interpret(plain_box, plain)

    g = _grammar().with_interpreter(
        "Bay", lambda s, below, d: [_node(s, kind="special")], where=under("box/f2")
    )
    box, d = derive(g, _box(), DecisionStream(1))
    after = interpret(box, d)
    changed = [b.id for a, b in zip(before, after) if a != b]
    assert changed and all(i.startswith("box/f2/") for i in changed)
