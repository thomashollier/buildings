"""Old Havana: colonial, neoclassical and eclectic fronts, grown ornament, variety."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.havana.grammar import HavanaSite, derive_havana, generate_havana, havana_manner
from buildings.typologies.paris.generate import walk



def _coarse(building) -> str:
    """What a viewer would see as a different design: numbers to 0.25 m."""
    import hashlib
    import json

    def snap(v):
        if isinstance(v, float):
            return round(v * 4) / 4
        if isinstance(v, dict):
            return {k: snap(x) for k, x in v.items() if k != "trace"}
        if isinstance(v, list):
            return [snap(x) for x in v]
        return v

    return hashlib.md5(json.dumps(snap(json.loads(to_json(building))), sort_keys=True).encode()).hexdigest()

SITES = [
    HavanaSite(11.0, 1720, BuildingClass.COMFORTABLE, 0),
    HavanaSite(16.0, 1820, BuildingClass.COMFORTABLE, 2, True),
    HavanaSite(12.0, 1850, BuildingClass.ORDINARY, 3),
    HavanaSite(18.0, 1920, BuildingClass.GRAND, 5),
]


@pytest.mark.parametrize("site", SITES, ids=lambda s: f"{s.year}-{s.width}")
def test_it_derives_traces_renders_and_repeats(site):
    building, _ = generate_havana(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate_havana(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive_havana(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in ("Cornice", "Balcon"):
            assert shape.parent.scope.contains(shape.scope), shape


def test_the_date_weights_the_manner():
    assert {havana_manner(1720, s) for s in range(30)} == {"colonial"}
    assert [havana_manner(1850, s) for s in range(40)].count("neoclassical") > 25
    assert [havana_manner(1915, s) for s in range(40)].count("eclectic") > 25


def test_ornament_is_grown():
    labels = set()
    for seed in range(12):
        lot, _ = derive_havana(HavanaSite(12.0, 1740, BuildingClass.COMFORTABLE, seed, seed % 2 == 0))
        labels |= {s.label for s in lot.walk()}
        grown = [s for s in lot.walk() if s.label in ("Mediopunto", "Transom", "Reja", "Balcon", "Persiana")]
        assert all(s.children for s in grown)
    assert {"Transom", "Reja", "Persiana", "Balcon"} <= labels
    later = {s.label for seed in range(12) for s in derive_havana(HavanaSite(12.0, 1850, BuildingClass.COMFORTABLE, seed))[0].walk()}
    assert "Mediopunto" in later


def test_every_opening_is_leaves_not_glass():
    """Each window and upper opening is filled by its grown leaves, under the head."""
    for seed in range(20):
        lot, _ = derive_havana(HavanaSite(14.0, 1850, BuildingClass.COMFORTABLE, seed))
        for storey in (s for s in lot.walk() if s.label == "Storey" and s.attrs.get("role") == "upper"):
            windows = [c for c in storey.children if c.label == "Cell" and c.attrs.get("opening_type") == "window"]
            leaves = [c for c in storey.children if c.label == "Persiana"]
            assert len(leaves) == len(windows)


def test_openings_nearly_fill_the_storey_under_a_band_of_wall():
    for seed in range(30):
        lot, _ = derive_havana(HavanaSite(12.0, 1760 + seed * 5, BuildingClass.ORDINARY, seed))
        for c in lot.walk():
            if c.label == "Cell" and c.attrs.get("opening_type") == "window" and c.parent.attrs.get("role") == "upper":
                assert 0.6 <= c.attrs["light_height"] / c.scope.h <= 0.8
                assert c.scope.h - c.attrs["sill"] - c.attrs["light_height"] >= 1.0


def test_a_plaza_front_opens_in_a_portal():
    portals = 0
    for seed in range(20):
        lot, _ = derive_havana(HavanaSite(16.0, 1820, BuildingClass.COMFORTABLE, seed, True))
        portals += any(s.label == "Arch" for s in lot.walk())
        if lot.attrs["portal"]:
            ground = next(s for s in lot.walk() if s.label == "Storey")
            assert ground.attrs["wall_material"].endswith("_deep")
    assert portals >= 10


@pytest.mark.parametrize("year", [1740, 1850, 1910])
def test_a_hundred_seeds_give_a_hundred_fronts(year):
    designs = {_coarse(generate_havana(HavanaSite(12.0, year, BuildingClass.COMFORTABLE, s))[0]) for s in range(100)}
    assert len(designs) >= 80, len(designs)


def test_the_builders_choices_vary_across_seeds():
    """Louvred leaves, pilasters, bodegas and the three mediopunto patterns
    each turn up on some fronts and not on others."""
    from buildings.typologies.havana.grammar import derive_havana

    seen = {"Persiana": set(), "Column": set(), "shop": set(), "pattern": set(), "paint": set()}
    for s in range(60):
        lot, _ = derive_havana(HavanaSite(12.0, 1800 + s, BuildingClass.COMFORTABLE, s))
        labels = {x.label for x in lot.walk()}
        seen["Persiana"].add(lot.attrs["louvred"])
        seen["Column"].add("Column" in labels)
        seen["shop"].add(lot.attrs["shop"])
        seen["pattern"].add(lot.attrs["fan_pattern"])
        seen["paint"].add(lot.attrs["louvre_paint"])
    assert seen["Persiana"] == seen["Column"] == seen["shop"] == {True, False}
    assert seen["pattern"] == {"fan", "ring"}
    assert len(seen["paint"]) >= 3
