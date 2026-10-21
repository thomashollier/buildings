"""San Francisco Victorians and Normandy half-timbered houses."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass
from buildings.typologies.normandy.grammar import NormandySite, derive_normandy, generate_normandy
from buildings.typologies.paris.generate import walk
from buildings.typologies.victorian.grammar import VictorianSite, derive_victorian, generate_victorian, victorian_type

CASES = [
    ("italianate", generate_victorian, derive_victorian, VictorianSite(1875, BuildingClass.ORDINARY, 0)),
    ("stick", generate_victorian, derive_victorian, VictorianSite(1885, BuildingClass.ORDINARY, 1)),
    ("queen_anne", generate_victorian, derive_victorian, VictorianSite(1892, BuildingClass.ORDINARY, 2)),
    ("queen_anne_turret", generate_victorian, derive_victorian, VictorianSite(1895, BuildingClass.GRAND, 3)),
    ("normandy_town", generate_normandy, derive_normandy, NormandySite("town", 1620, BuildingClass.COMFORTABLE)),
    ("normandy_country", generate_normandy, derive_normandy, NormandySite("country", 1700, BuildingClass.ORDINARY)),
]


@pytest.mark.parametrize("name,generate,derive,site", CASES, ids=[c[0] for c in CASES])
def test_each_derives_traces_renders_and_repeats(name, generate, derive, site):
    building, _ = generate(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in ("Cornice", "Chimney"):
            assert shape.parent.scope.contains(shape.scope), shape


def test_the_date_weights_the_victorian_type_and_a_square_bay_shows_less_side():
    def kinds(year):
        return [victorian_type(year, seed) for seed in range(60)]

    assert set(kinds(1875)) == {"italianate"}
    assert kinds(1886).count("stick") > 25 and "italianate" in kinds(1886)
    assert kinds(1895).count("queen_anne") > 45

    def side_share(seed):
        lot, _ = derive_victorian(VictorianSite(1886, BuildingClass.ORDINARY, seed))
        zone = next(s for s in lot.walk() if s.label == "BayZone" and s.attr("role") == "parlour")
        cells = [c for c in zone.children if c.label == "Cell"]
        return lot.attrs["bay_form"], cells[0].scope.w / zone.scope.w

    shares = dict(side_share(seed) for seed in range(40))
    assert shares["slanted"] > 2 * shares["square"]


def test_turrets_are_rarer_on_an_ordinary_queen_anne_than_a_grand_one():
    def turrets(klass):
        n = 0
        for seed in range(80):
            b, _ = generate_victorian(VictorianSite(1897, klass, seed))
            n += any(x.kind == "storey" and x.props["role"] == "turret" for x in walk(b))
        return n

    ordinary, grand = turrets(BuildingClass.ORDINARY), turrets(BuildingClass.GRAND)
    assert 0 < ordinary < grand


def test_the_town_house_is_jettied_and_no_post_crosses_a_window():
    lot, _ = derive_normandy(NormandySite("town", 1620, BuildingClass.COMFORTABLE))
    storeys = [f.children[0] for f in lot.children[0].children]
    widths = [s.scope.w for s in storeys]
    assert widths == sorted(widths) and widths[0] < widths[-1]
    for cell in (c for s in storeys for c in s.children if c.label == "Cell" and c.children and c.children[1].label == "LightBay"):
        light = cell.children[1].scope
        for post in (p for p in cell.children if p.label == "Post"):
            assert post.scope.x + post.scope.w <= light.x + 1e-6 or post.scope.x >= light.x + light.w - 1e-6


def test_the_country_house_is_close_set_under_thatch():
    b, _ = generate_normandy(NormandySite("country", 1700, BuildingClass.ORDINARY))
    roof = next(n for n in walk(b) if n.kind == "roof")
    assert roof.props["material"] == "thatch"
    town, _ = generate_normandy(NormandySite("town", 1620, BuildingClass.ORDINARY))

    def posts_per_metre(building):
        """Posts across the ground storey, per metre of it."""
        ground = next(n for n in building.children if n.kind == "storey")
        posts = [n for n in ground.children if n.kind == "column" and n.props.get("order") == "timber"]
        return len(posts) / ground.props["w"]

    assert posts_per_metre(b) > posts_per_metre(town)


def test_most_doors_are_set_back_in_a_recessed_porch():
    from buildings.site import BuildingClass
    from buildings.typologies.victorian.grammar import VictorianSite, derive_victorian

    porches = 0
    for seed in range(30):
        lot, _ = derive_victorian(VictorianSite(1880 + seed % 15, BuildingClass.ORDINARY, seed))
        shade = [s for s in lot.walk() if s.label == "PorchShade"]
        porches += bool(shade)
        if shade:
            door = next(c for c in lot.walk() if c.label == "Cell" and c.attrs.get("opening_type") == "pedestrian_entrance")
            assert door.attrs["surround_kind"] == "none"
            assert shade[0].scope.contains(door.children[0].scope) or shade[0].scope.w >= door.attrs["light_width"]
    assert 12 <= porches <= 28
