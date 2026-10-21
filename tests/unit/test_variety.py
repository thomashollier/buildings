"""Stochastic alternatives: ``draw``/``between``/``chance`` in expressions and
``pick`` in rules, and the variety they give a style on one fixed site."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from buildings.ir.serial import to_json
from buildings.site import BuildingClass
from buildings.typologies.common.rulefile import RuleFileError, load_style
from buildings.typologies.paris.generate import walk
from buildings.typologies.victorian.grammar import VictorianSite, derive_victorian, generate_victorian


def _coarse(building) -> str:
    """A signature of what a viewer would see as a different design: every
    number rounded to 0.25 m, so sub-step jitter does not count as variety."""

    def snap(v):
        if isinstance(v, float):
            return round(v * 4) / 4
        if isinstance(v, dict):
            return {k: snap(x) for k, x in v.items() if k != "trace"}
        if isinstance(v, list):
            return [snap(x) for x in v]
        return v

    data = snap(json.loads(to_json(building)))
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize("year", [1875, 1885, 1892])
def test_a_hundred_seeds_give_a_hundred_victorians_on_one_lot(year):
    designs = {_coarse(generate_victorian(VictorianSite(year, BuildingClass.ORDINARY, s))[0]) for s in range(100)}
    assert len(designs) >= 80, len(designs)


def test_every_floor_matches_itself():
    for seed in range(30):
        lot, _ = derive_victorian(VictorianSite(1875, BuildingClass.ORDINARY, seed))
        for storey in (s for s in lot.walk() if s.label == "Storey"):
            cells = [c for c in storey.walk() if c.label == "Cell" and c.attrs.get("opening_type") == "window"]
            assert len({c.attrs["head"] for c in cells}) <= 1, storey.id
            assert len({c.attrs["surround_kind"] for c in cells}) <= 1, storey.id


def test_a_round_head_is_never_over_one_wide_front_sash():
    for seed in range(60):
        lot, _ = derive_victorian(VictorianSite(1875, BuildingClass.ORDINARY, seed))
        for c in lot.walk():
            if c.label == "Cell" and c.attrs.get("head") == "round" and not c.attrs.get("lights"):
                assert c.attrs["light_width"] <= 1.3, c.id


def test_draws_are_reproducible():
    site = VictorianSite(1885, BuildingClass.COMFORTABLE, 17)
    assert to_json(generate_victorian(site)[0]) == to_json(generate_victorian(site)[0])


def _style(tmp_path: Path, body: str):
    path = tmp_path / "toy.toml"
    path.write_text(
        '[style]\nname = "toy"\nsite = ["seed"]\naxiom = { w = "10", h = "6" }\n\n'
        "[params]\nheads = { segmental = 3, round = 1 }\n\n" + body
    )
    return load_style(path)


_TOY = """
[[production]]
id = "toy.lot"
label = "Lot"
do = [ { split = "y", parts = [ { repeat = "[3.0, 3.0]", label = "Storey", size = "item", name = "s{i}" } ] } ]

[[production]]
id = "toy.storey"
label = "Storey"
do = [ { split = "x", parts = [ { repeat = "range(4)", label = "Cell", size = "2.5", name = "c{i}" } ] } ]
"""


class _Site:
    def __init__(self, seed):
        self.seed = seed


def test_pick_draws_once_per_named_shape(tmp_path):
    style = _style(
        tmp_path,
        _TOY + '\n[[rule]]\nid = "toy.head"\nlabel = "Cell"\npick = { per = "Storey", head = { segmental = 3, round = 1, flat = 2 } }\n',
    )
    floors_differ = False
    for seed in range(40):
        lot, _ = style.derive(_Site(seed))
        per_floor = [{c.attrs["head"] for c in s.children} for s in lot.children]
        assert all(len(h) == 1 for h in per_floor)
        floors_differ |= per_floor[0] != per_floor[1]
    assert floors_differ


def test_a_new_draw_does_not_reshuffle_an_old_one(tmp_path):
    base = _TOY + '\n[[rule]]\nid = "toy.head"\nlabel = "Cell"\nset = { head = "= draw(\'head\', heads, per=\'Storey\')" }\n'
    more = base.replace(
        "set = { head", "set = { colour = \"= draw('colour', ['red', 'blue'])\", head"
    )
    a, b = _style(tmp_path, base), _style(tmp_path / ".." / tmp_path.name, more)
    for seed in range(20):
        ha = [c.attrs["head"] for c in a.derive(_Site(seed))[0].walk() if c.label == "Cell"]
        hb = [c.attrs["head"] for c in b.derive(_Site(seed))[0].walk() if c.label == "Cell"]
        assert ha == hb


def test_pick_options_need_weights(tmp_path):
    with pytest.raises(RuleFileError):
        _style(tmp_path, _TOY + '\n[[rule]]\nid = "toy.bad"\nlabel = "Cell"\npick = { head = "round" }\n')
