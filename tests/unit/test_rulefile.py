"""The declarative rule format: its expression language, its errors, and a
style written from scratch with no Python at all."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from buildings.cga import Layer, LockedAttributes
from buildings.cga.expr import Expr, ExprError
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.common.rulefile import RuleFileError, load_style
from buildings.typologies.paris.generate import walk


def _eval(src, names=None, functions=None):
    names = names or {}
    return Expr(src)(names.__getitem__, functions or {})


def test_expressions_compute_and_test():
    assert _eval("min(a * 2, b) + 1", {"a": 1.5, "b": 2.0}, {"min": min}) == 3.0
    assert _eval("'x' if n == 0 else 'y'", {"n": 0}) == "x"
    assert _eval("item.h", {"item": {"h": 3.5}}) == 3.5
    assert _eval("(1.0,) * 3") == (1.0, 1.0, 1.0)
    assert _eval("f'{w:.1f} m'", {"w": 7.62}) == "7.6 m"


@pytest.mark.parametrize(
    "src",
    ["__import__('os')", "(lambda: 1)()", "[x for x in y]", "a.__class__", "open('f')", "a.b.c"],
)
def test_expressions_cannot_reach_out(src):
    with pytest.raises(ExprError):
        Expr(src)({"a": object(), "y": [1], "x": 1}.__getitem__, {})


BOX = """
[style]
name = "box"
site = ["width", "year", "klass", "seed"]
axiom = { w = "width", h = 30 }
overhangs = ["Cornice"]
describe = { rule = "box.house", detail = "f'a box, {width:.1f} m'" }

[params]
floors = [3.0, 2.8, 2.8]
bay = [1.8, 2.4, 3.0]
end = [0.4, 0.6, 1.0]

[[production]]
id = "box.lot"
label = "Lot"
do = [ { insert = "Facade", at = ["0.0", "0.0", "w", "fsum(floors)"], name = "facade" } ]

[[production]]
id = "box.facade"
label = "Facade"
do = [
  { fit = "x", end = "end", bay = "bay", as = "rhythm" },
  { split = "y", id_base = "parent", parts = [ { repeat = "floors", label = "Storey", size = "item", name = "s{i}" } ] },
]

[[production]]
id = "box.storey"
label = "Storey"
do = [
  { split = "x", by = "rhythm", label = "Cell" },
  { insert = "Cornice", at = ["x", "y + h", "w", "0.4"], name = "cornice", attrs = { cornice_ornament = "modillioned" }, when = "index == count - 1" },
]

[[production]]
id = "box.cell"
label = "Cell"
when = "opening_type != 'none'"
do = [ { call = "kit.split_cell_around_its_light" } ]

[[production]]
id = "box.light_bay"
label = "LightBay"
do = [ { call = "kit.split_light_bay" } ]

[[production]]
id = "box.light"
label = "Light"
do = [ { call = "kit.dress_the_light" } ]

[[rule]]
id = "box.roles"
label = "Storey"
layer = "roles"
set = { role = "= 'base' if index == 0 else 'upper'", wall_material = "brick" }

[[rule]]
id = "box.wall"
label = "Cell"
when = "not is_bay()"
set = { opening_type = "none" }

[[rule]]
id = "box.window"
label = "Cell"
when = "is_bay()"
set = { opening_type = "window", head = "flat", light_width = "= w * 0.5", sill = 0.9, light_height = "= h - 1.5", surround_kind = "moulded_architrave", keystone_present = false }

[[rule]]
id = "box.door"
label = "Cell"
when = "is_bay() and role == 'base' and is_middle_bay()"
specificity = 10
set = { opening_type = "pedestrian_entrance", light_width = 1.1, sill = 0.0, light_height = 2.4 }
"""


@dataclass(frozen=True)
class Site:
    width: float
    year: int = 1900
    klass: BuildingClass = BuildingClass.ORDINARY
    seed: int = 0


def _style(tmp_path: Path, text: str = BOX):
    path = tmp_path / "box.toml"
    path.write_text(text)
    return load_style(path)


def test_a_style_written_only_as_rules_builds_and_draws(tmp_path):
    style = _style(tmp_path)
    building, _ = style.generate(Site(9.0))
    nodes = list(walk(building))
    assert sum(1 for n in nodes if n.kind == "storey") == 3
    doors = [n for n in nodes if n.props.get("opening_type") == "pedestrian_entrance"]
    assert len(doors) == 1
    assert any(e.rule == "box.door" for e in doors[0].trace)
    assert "<svg" in render(building)


def test_a_rule_file_style_takes_scoped_overrides_like_any_other(tmp_path):
    from buildings.cga import Attrs

    def round_heads(shape, rng):
        return Attrs({"head": "round"}, rule="override.round")

    style = _style(tmp_path)
    building, _ = style.generate(
        Site(9.0), refine=lambda g: g.with_override("Cell", Layer("o", 40, (round_heads,)), where=lambda s: s.attr("role") == "upper")
    )
    heads = {(n.id.split("/")[1], n.props["head"]) for n in walk(building) if n.kind == "opening" and n.props["opening_type"] == "window"}
    assert ("s0", "flat") in heads and ("s1", "round") in heads


def test_the_engine_still_enforces_locality_on_rule_files(tmp_path):
    bad = BOX.replace(
        'do = [ { call = "kit.dress_the_light" } ]',
        'do = [ { call = "kit.dress_the_light" } ]\n\n[[production]]\nid = "box.meddle"\nlabel = "Breast"\ndo = [ { set = { opening_type = "none" } } ]',
    )
    # Writing the shape in hand is allowed; the engine refuses writes to any
    # other shape, so a rule file cannot reach sideways either.
    style = _style(tmp_path, bad)
    style.generate(Site(9.0))
    lot, _ = style.derive(Site(9.0))
    cell = next(s for s in lot.walk() if s.label == "Cell" and s.children)
    with pytest.raises(LockedAttributes):
        cell.attrs["opening_type"] = "none"


@pytest.mark.parametrize(
    "broken,message",
    [
        ('do = [ { call = "kit.dress_the_light" } ]', 'do = [ { call = "kit.no_such_thing" } ]'),
        ('{ split = "x", by = "rhythm", label = "Cell" }', '{ split = "x", insert = "Cell", by = "rhythm" }'),
        ('when = "is_bay()"', 'when = "is_bay() and __import__(\'os\')"'),
    ],
)
def test_a_malformed_rule_file_is_refused_when_loaded(tmp_path, broken, message):
    with pytest.raises((RuleFileError, ExprError)):
        _style(tmp_path, BOX.replace(broken, message, 1))
