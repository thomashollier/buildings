"""The Paris immeuble written as a rule file, like the other styles."""

from __future__ import annotations

import itertools

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.generate import walk
from buildings.typologies.paris.reglement import era_for_year, get_reglement
from buildings.typologies.paris.rules import derive_haussmann, generate_haussmann

SITES = [
    SiteContext(sw, pw, 14.0, year, klass, ground, seed=i)
    for i, (sw, pw, year, klass, ground) in enumerate(
        itertools.product(
            (8.0, 12.0, 20.0, 30.0),
            (9.0, 14.0, 22.0),
            (1840, 1865, 1890),
            (BuildingClass.MODEST, BuildingClass.GRAND),
            (GroundProgramme.SHOP, GroundProgramme.RESIDENTIAL),
        )
    )
]


@pytest.mark.parametrize("site", SITES[::7], ids=lambda s: f"{s.street_width:g}m-{s.parcel_width:g}m-{s.year}-{s.klass.value}-{s.ground.value}")
def test_it_derives_traces_renders_and_repeats(site):
    building, _ = generate_haussmann(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate_haussmann(site)[0]) == to_json(building)
    assert "<svg" in render(building)


@pytest.mark.parametrize("site", SITES)
def test_the_stone_stays_under_the_legal_cornice(site):
    building, _ = generate_haussmann(site)
    legal = get_reglement(era_for_year(site.year)).facade_height_limit(site.street_width)
    assert building.props["eaves_height"] <= legal + 1e-9


def test_one_entrance_and_the_noble_floor_is_tallest_above_the_base():
    lot, _ = derive_haussmann(SiteContext(20.0, 14.0, 14.0, 1865, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=8))
    storeys = lot.children[0].children
    principal = next(s for s in storeys if s.attrs["role"] == "principal")
    assert all(principal.scope.h >= s.scope.h for s in storeys if s.attrs["role"] == "upper")
    building, _ = generate_haussmann(SiteContext(20.0, 14.0, 14.0, 1865, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=8))
    assert sum(1 for n in walk(building) if n.props.get("opening_type") == "pedestrian_entrance") == 1
