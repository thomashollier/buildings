"""Three more styles on the split-grammar engine, each with its signature."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.amsterdam.grammar import CanalSite, derive_amsterdam, gable_form, generate_amsterdam
from buildings.typologies.chicago.grammar import OfficeSite, derive_chicago, generate_chicago
from buildings.typologies.paris.generate import walk
from buildings.typologies.venice.grammar import PalazzoSite, derive_venice, generate_venice

CASES = [
    ("amsterdam-step", generate_amsterdam, derive_amsterdam, CanalSite(6.6, 1625, BuildingClass.COMFORTABLE)),
    ("amsterdam-neck", generate_amsterdam, derive_amsterdam, CanalSite(7.2, 1670, BuildingClass.COMFORTABLE)),
    ("amsterdam-bell", generate_amsterdam, derive_amsterdam, CanalSite(5.8, 1750, BuildingClass.ORDINARY)),
    ("amsterdam-straight", generate_amsterdam, derive_amsterdam, CanalSite(7.0, 1800, BuildingClass.ORDINARY)),
    ("venice", generate_venice, derive_venice, PalazzoSite(19.0, 1430, BuildingClass.GRAND)),
    ("venice-modest", generate_venice, derive_venice, PalazzoSite(14.0, 1400, BuildingClass.ORDINARY)),
    ("chicago", generate_chicago, derive_chicago, OfficeSite(20.5, 1895, BuildingClass.COMFORTABLE)),
    ("chicago-wide", generate_chicago, derive_chicago, OfficeSite(33.0, 1905, BuildingClass.GRAND)),
]


@pytest.mark.parametrize("name,generate,derive,site", CASES, ids=[c[0] for c in CASES])
def test_each_style_derives_traces_renders_and_repeats(name, generate, derive, site):
    building, _ = generate(site)
    for node in walk(building):
        assert node.trace, node.id
    assert len({n.id for n in walk(building)}) == sum(1 for _ in walk(building)), "ids are unique"
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in ("Cornice",):
            assert shape.parent.scope.contains(shape.scope), shape


def test_the_gable_follows_the_date_and_narrows_as_it_climbs():
    assert [gable_form(y) for y in (1620, 1680, 1750, 1800)] == ["step", "neck", "bell", "straight"]
    lot, _ = derive_amsterdam(CanalSite(6.6, 1625, BuildingClass.COMFORTABLE))
    gable = next(s for s in lot.children if s.label == "Gable")
    widths = [t.children[0].scope.w for t in gable.children if t.label == "GableTier"]
    assert len(widths) == 3 and widths == sorted(widths, reverse=True)
    building, _ = generate_amsterdam(CanalSite(6.6, 1800, BuildingClass.ORDINARY))
    assert not any(n.kind == "gable" for n in walk(building))


def test_every_venetian_storey_is_wing_centre_wing_and_the_nobile_opens_in_a_polifora():
    lot, _ = derive_venice(PalazzoSite(19.0, 1430, BuildingClass.GRAND))
    storeys = lot.children[0].children
    for st in storeys:
        assert [c.label for c in st.children if c.label in ("Wing", "Centre")] == ["Wing", "Centre", "Wing"]
    building, _ = generate_venice(PalazzoSite(19.0, 1430, BuildingClass.GRAND))
    centre_lights = [
        sum(1 for n in walk(s) if n.kind == "opening" and "/centre/" in n.id)
        for s in building.children
        if s.kind == "storey"
    ]
    assert centre_lights[1] == 5 and centre_lights[2] == 4  # first nobile richer than the second
    assert any(n.props.get("head") == "ogee" for n in walk(building))


def test_the_chicago_shaft_is_uniform_its_piers_run_through_and_its_windows_are_1_2_1():
    building, _ = generate_chicago(OfficeSite(20.5, 1895, BuildingClass.COMFORTABLE))
    storeys = [n for n in building.children if n.kind == "storey"]
    shaft = [s for s in storeys if s.props["role"] == "shaft"]
    assert len({round(s.props["h"], 6) for s in shaft}) == 1
    piers = [n for n in building.children if n.kind == "column"]
    assert piers and all(abs(p.props["h"] - sum(s.props["h"] for s in shaft)) < 1e-6 for p in piers)
    bay = next(n for n in walk(shaft[0]) if n.kind == "bay" and n.props["slot_name"] == "bay")
    lights = sorted((o for o in bay.children if o.kind == "opening"), key=lambda o: o.props["x"])
    w = [o.props["w"] for o in lights]
    assert len(w) == 3 and w[1] == pytest.approx(2 * w[0]) and w[0] == pytest.approx(w[2])
