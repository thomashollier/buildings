"""SoHo: a second typology written as data on the same split-grammar engine."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.paris.generate import walk
from buildings.typologies.soho.grammar import derive_soho, generate_soho
from buildings.typologies.soho.recipes import Programme, SohoSite, recipe_for

FEDERAL = SohoSite(1, 1825, Programme.DWELLING, BuildingClass.ORDINARY)
IRON = SohoSite(1, 1858, Programme.LOFT, BuildingClass.COMFORTABLE)
IRON_WIDE = SohoSite(3, 1872, Programme.LOFT, BuildingClass.GRAND)
BRICK = SohoSite(1, 1886, Programme.LOFT, BuildingClass.ORDINARY)
ALL = [FEDERAL, IRON, IRON_WIDE, BRICK]


def test_date_and_programme_choose_the_type():
    assert [recipe_for(s).name for s in ALL] == [
        "federal_rowhouse",
        "cast_iron_loft",
        "cast_iron_loft",
        "brick_store_and_loft",
    ]
    with pytest.raises(ValueError):
        recipe_for(SohoSite(1, 1830, Programme.LOFT, BuildingClass.ORDINARY))


@pytest.mark.parametrize("site", ALL, ids=lambda s: recipe_for(s).name + f"-{s.lots}")
def test_every_type_derives_traces_and_renders(site):
    building, _ = generate_soho(site)
    for node in walk(building):
        assert node.trace, node.id
    assert to_json(generate_soho(site)[0]) == to_json(building)
    assert "<svg" in render(building)


def _glass_share(site: SohoSite) -> float:
    building, _ = generate_soho(site)
    upper = [n for n in building.children if n.kind == "storey" and n.props["role"] != "base"]
    wall = sum(s.props["w"] * s.props["h"] for s in upper)
    glass = sum(
        o.props["w"] * o.props["h"]
        for s in upper
        for o in walk(s)
        if o.kind == "opening"
    )
    return glass / wall


def test_an_iron_front_carries_far_more_glass_than_a_brick_one():
    iron, brick, federal = _glass_share(IRON), _glass_share(BRICK), _glass_share(FEDERAL)
    assert iron > 1.5 * brick and brick > federal, (iron, brick, federal)


def test_the_entrance_is_one_door_and_on_its_side():
    for site, side in ((FEDERAL, "left"), (BRICK, "right")):
        building, _ = generate_soho(site)
        doors = [n for n in walk(building) if n.props.get("opening_type") == "pedestrian_entrance"]
        assert len(doors) == 1
        x = doors[0].props["x"] / building.props["w"]
        assert (x < 0.5) == (side == "left")


def test_iron_heads_follow_the_date():
    def heads(year):
        building, _ = generate_soho(SohoSite(1, year, Programme.LOFT, BuildingClass.COMFORTABLE))
        return {n.props["head"] for n in walk(building) if n.props.get("opening_type") == "window"}

    assert heads(1858) == {"round"}
    assert heads(1866) == {"segmental"}
    assert heads(1876) == {"flat"}


def test_every_part_stands_inside_the_part_it_refines():
    for site in ALL:
        lot, _ = derive_soho(site)
        for shape in lot.walk():
            if shape.parent is not None and shape.label not in ("Cornice", "Chimney"):
                assert shape.parent.scope.contains(shape.scope), shape
