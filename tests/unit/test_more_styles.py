"""Georgian, Kyoto, Art Deco and Corbusian grammars, each with its signature."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.deco.grammar import TowerSite, derive_deco, generate_deco, tiers_for
from buildings.typologies.georgian.grammar import TerraceSite, derive_georgian, generate_georgian
from buildings.typologies.kyoto.grammar import MachiyaSite, derive_kyoto, generate_kyoto
from buildings.typologies.modernist.grammar import VillaSite, derive_modernist, generate_modernist
from buildings.typologies.paris.generate import walk

CASES = [
    ("georgian", generate_georgian, derive_georgian, TerraceSite(7.6, 1790, BuildingClass.COMFORTABLE)),
    ("georgian-wide", generate_georgian, derive_georgian, TerraceSite(11.5, 1775, BuildingClass.GRAND)),
    ("kyoto", generate_kyoto, derive_kyoto, MachiyaSite(6.4, 1890, BuildingClass.ORDINARY)),
    ("kyoto-wide", generate_kyoto, derive_kyoto, MachiyaSite(9.0, 1870, BuildingClass.COMFORTABLE)),
    ("deco", generate_deco, derive_deco, TowerSite(36.0, 18.0, 1929, BuildingClass.GRAND)),
    ("deco-narrow-street", generate_deco, derive_deco, TowerSite(30.0, 12.0, 1927, BuildingClass.ORDINARY)),
    ("modernist", generate_modernist, derive_modernist, VillaSite(19.0, 1929, BuildingClass.COMFORTABLE)),
    ("modernist-small", generate_modernist, derive_modernist, VillaSite(12.0, 1927, BuildingClass.MODEST)),
]


@pytest.mark.parametrize("name,generate,derive,site", CASES, ids=[c[0] for c in CASES])
def test_each_style_derives_traces_renders_and_repeats(name, generate, derive, site):
    building, _ = generate(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label != "Cornice":
            assert shape.parent.scope.contains(shape.scope), shape


def test_georgian_windows_are_one_width_and_their_floor_sets_the_height():
    building, _ = generate_georgian(TerraceSite(7.6, 1790, BuildingClass.COMFORTABLE))
    by_floor = {}
    for st in (n for n in building.children if n.kind == "storey"):
        ws = [o for o in walk(st) if o.kind == "opening" and o.props["opening_type"] == "window"]
        if ws:
            by_floor[st.props["role"]] = ws[0]
    assert len({round(o.props["w"], 6) for o in by_floor.values()}) == 1
    ratio = {f: o.props["h"] / o.props["w"] for f, o in by_floor.items()}
    assert ratio["first"] > ratio["ground"] > ratio["second"] > ratio["third"] == pytest.approx(1.0)


def test_the_machiya_loft_is_low_and_its_lights_are_screened():
    building, _ = generate_kyoto(MachiyaSite(6.4, 1890, BuildingClass.ORDINARY))
    ground, loft = [n for n in building.children if n.kind == "storey"]
    assert loft.props["h"] < 0.7 * ground.props["h"]
    lattices = [n for n in walk(building) if n.props.get("ironwork_pattern") == "timber_lattice"]
    windows = [n for n in walk(building) if n.kind == "opening" and n.props["opening_type"] == "window"]
    assert lattices and len(lattices) == len(windows)


def test_the_setback_tower_follows_the_street():
    narrow = tiers_for(TowerSite(36.0, 12.0, 1929, BuildingClass.GRAND))
    wide = tiers_for(TowerSite(36.0, 24.0, 1929, BuildingClass.GRAND))
    assert wide[0][1] > narrow[0][1]  # a wider street lets the street wall rise further
    widths = [w for _role, _n, w in wide]
    assert widths == sorted(widths, reverse=True)
    tower = next(t for t in wide if t[0] == "tower")
    assert tower[2] <= 0.5 * 36.0 + 1e-9


def test_the_ribbon_ignores_the_grid_and_the_ground_stands_on_posts():
    lot, _ = derive_modernist(VillaSite(19.0, 1929, BuildingClass.COMFORTABLE))
    pilotis, *floors = lot.children[0].children
    grid_cells = [c for c in pilotis.children if c.label == "Cell"]
    posts = [c for c in pilotis.children if c.label == "Column"]
    assert len(posts) == len(grid_cells) - 1
    for floor in floors:
        cells = [c for c in floor.children if c.label == "Cell"]
        assert len(cells) == 3 and cells[1].scope.w > 0.8 * floor.scope.w
