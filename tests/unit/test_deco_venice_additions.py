"""The Art Deco family (its programmes, the Miami Beach hotel, the movie
palace, the tower's new crowns) and the Veneto-Byzantine palazzo."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.deco.grammar import PROGRAMMES, DecoSite, TowerSite, derive_deco, generate_deco
from buildings.typologies.miami_deco.grammar import MiamiSite, derive_miami_deco, generate_miami_deco
from buildings.typologies.movie_palace.grammar import PalaceSite, derive_movie_palace, generate_movie_palace
from buildings.typologies.paris.generate import walk
from buildings.typologies.venice.grammar import PalazzoSite, derive_venice, generate_venice

CASES = [
    ("miami", generate_miami_deco, derive_miami_deco, MiamiSite(15.0, 1932, K.ORDINARY, seed=0), ()),
    ("miami-streamline-corner", generate_miami_deco, derive_miami_deco, MiamiSite(30.0, 1941, K.GRAND, seed=5, corner=True), ()),
    ("miami-modest", generate_miami_deco, derive_miami_deco, MiamiSite(16.0, 1936, K.MODEST, seed=1), ()),
    ("palace-narrow", generate_movie_palace, derive_movie_palace, PalaceSite(13.0, 1929, K.MODEST, seed=0), ()),
    ("palace-twin-signs", generate_movie_palace, derive_movie_palace, PalaceSite(40.0, 1931, K.GRAND, seed=3), ()),
    ("palace-corner-sign", generate_movie_palace, derive_movie_palace, PalaceSite(26.0, 1936, K.ORDINARY, seed=7), ()),
    ("tower-chrysler", generate_deco, derive_deco, TowerSite(36.0, 18.0, 1929, K.GRAND, seed=3), ()),
    ("tower-mast", generate_deco, derive_deco, TowerSite(42.0, 24.0, 1930, K.GRAND, seed=4), ()),
    ("tower-clock", generate_deco, derive_deco, TowerSite(50.0, 30.0, 1931, K.GRAND, seed=5), ()),
    ("tower-clock-granite", generate_deco, derive_deco, TowerSite(50.0, 30.0, 1931, K.GRAND, seed=11), ()),
    ("venice-byzantine", generate_venice, derive_venice, PalazzoSite(30.0, 1225, K.GRAND), ("Cornice",)),
    ("venice-byzantine-small", generate_venice, derive_venice, PalazzoSite(12.0, 1200, K.ORDINARY), ("Cornice",)),
] + [
    (f"deco-{p}-{year}", generate_deco, derive_deco, DecoSite(p, w, year, k, seed=s), ())
    for p in PROGRAMMES[1:]
    for (w, year, k, s) in ((18.0, 1929, K.ORDINARY, 0), (46.0, 1938, K.GRAND, 3))
]


@pytest.mark.parametrize("name,generate,derive,site,overhangs", CASES, ids=[c[0] for c in CASES])
def test_each_style_derives_traces_renders_and_repeats(name, generate, derive, site, overhangs):
    building, _ = generate(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes), "ids are unique"
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in overhangs:
            assert shape.parent.scope.contains(shape.scope), shape


# --- Art Deco: the family -------------------------------------------------------


def test_the_programme_picks_the_composition():
    parts = {
        p: [b.attrs["part"] for b in derive_deco(DecoSite(p, 46.0, 1931, K.GRAND))[0].children if b.label == "Block"]
        for p in PROGRAMMES[1:]
    }
    assert parts["civic"] == ["wing", "centre", "wing"]
    assert parts["institutional"] == ["pavilion", "wing", "entrance", "wing", "pavilion"]
    assert parts["religious"] == ["wing", "tower", "wing"]
    assert parts["commercial"] in (["store", "tower", "store"], ["tower", "store"])
    assert parts["office"] == ["wing", "office", "wing"]
    assert parts["works"] == ["hall", "centre", "hall"]
    lot, _ = derive_deco(TowerSite(36.0, 18.0, 1929, K.GRAND))
    assert [t.label for t in lot.children].count("Tier") >= 3  # the skyscraper keeps its zoning grammar


def test_a_civic_front_is_three_divisions_of_3_to_7_storeys_the_centre_higher():
    for k, storeys in ((K.MODEST, 3), (K.ORDINARY, 4), (K.COMFORTABLE, 5), (K.GRAND, 7)):
        lot, _ = derive_deco(DecoSite("civic", 34.0, 1937, k))
        wing, centre, _ = (b for b in lot.children if b.label == "Block")
        floors = [f for f in centre.children if f.label == "Floor" and f.attrs["role"] != "parapet"]
        assert len(floors) == storeys

        def top(block):
            return max(f.scope.y + f.scope.h for f in block.walk() if f.label == "Floor")

        assert top(centre) > top(wing)
        bays = sum(1 for b in lot.children if b.label == "Block" for c in b.children[1].children if c.label == "Cell" and c.attrs["slot"].name == "bay")
        assert 9 <= bays <= 15


def test_zigzag_then_streamline_by_date():
    zig, _ = generate_deco(DecoSite("institutional", 32.0, 1929, K.ORDINARY))
    stream, _ = generate_deco(DecoSite("institutional", 32.0, 1938, K.ORDINARY))
    stripes = lambda b: [n for n in walk(b) if n.kind == "storey" and n.props["role"] == "panel"]  # noqa: E731
    assert not stripes(zig) and stripes(stream)


# --- Art Deco: the tower's new crowns and skin ----------------------------------------


def test_new_crowns_are_appended_and_every_one_is_reachable():
    crown = lambda s: derive_deco(TowerSite(36.0, 18.0, 1929, K.GRAND, seed=s))[0].attrs["crown"]  # noqa: E731
    assert [crown(s) for s in range(6)] == ["spire", "ziggurat", "lantern", "chrysler", "mast", "clock"]
    assert [crown(s) for s in (6, 7, 8)] == ["spire", "ziggurat", "lantern"]  # old seeds keep their crowns
    skins = {derive_deco(TowerSite(50.0, 30.0, 1931, K.GRAND, seed=s))[0].attrs["skin"] for s in (5, 11)}
    assert skins == {"terracotta", "shadow"}  # Eastern Columbia and Carbide & Carbon


def test_the_chrysler_crown_has_triangular_windows_and_the_clock_tower_a_face():
    building, _ = generate_deco(TowerSite(36.0, 18.0, 1929, K.GRAND, seed=3))
    windows = [n for n in walk(building) if n.kind == "gable" and "/window" in n.id]
    assert len(windows) >= 20 and all(len(n.props["points"]) == 3 for n in windows)
    building, _ = generate_deco(TowerSite(50.0, 30.0, 1931, K.GRAND, seed=5))
    assert any(n.kind == "dormer" and n.props["form"] == "oeil_de_boeuf" for n in building.children)
    spandrels = [n for n in walk(building) if n.kind == "column" and n.props["order"] == "timber"]
    assert spandrels  # dark spandrel plates between the continuous piers


# --- Miami Beach --------------------------------------------------------------------


def test_miami_every_window_has_its_eyebrow_and_the_centre_rises_in_a_fin():
    site = MiamiSite(22.0, 1939, K.GRAND, seed=4)
    building, _ = generate_miami_deco(site)
    for storey in (n for n in building.children if n.kind == "storey" and n.props["role"] in ("upper", "ground")):
        windows = {n.id.split("/")[-3] for n in walk(storey) if n.kind == "opening" and n.props["opening_type"] == "window"}
        eyebrows = [n for n in storey.children if n.kind == "string_course" and "eyebrow" in n.id]
        assert len(eyebrows) >= len(windows) - 1  # the porthole bay has none
    lot, _ = derive_miami_deco(site)
    fin = next(s for s in lot.walk() if s.label == "Crest")
    assert fin.attr("crest") == "fin" and fin.parent.attrs["part"] == "centre"
    assert sum(1 for n in building.children if n.kind == "dormer") == 3  # a porthole on each room floor
    corner, _ = derive_miami_deco(MiamiSite(20.0, 1937, K.ORDINARY, corner=True))
    assert [b.attrs["part"] for b in corner.children][-1] == "corner"
    assert any(s.label == "Crest" and s.attr("crest") == "rounded" for s in corner.walk())


# --- Movie palace ---------------------------------------------------------------------


def test_the_palace_has_a_marquee_over_its_doors_and_a_blade_taller_than_its_front():
    for seed, blades in ((0, 1), (3, 2), (7, 1)):
        building, _ = generate_movie_palace(PalaceSite(30.0, 1931, K.COMFORTABLE, seed=seed))
        panels = {n.id.rsplit("/", 1)[-1]: n for n in building.children if n.kind == "storey" and n.props["role"] == "panel"}
        marquee = panels["marquee"]
        doors = [n for n in walk(building) if n.props.get("opening_type") == "pedestrian_entrance"]
        assert len(doors) >= 3 and all(d.props["y"] + d.props["h"] <= marquee.props["y"] + 1e-6 for d in doors)
        signs = [n for k, n in panels.items() if k.startswith("blade") and "letter" not in k]
        facade_top = max(n.props["y"] + n.props["h"] for n in building.children if n.kind == "storey" and n.props["role"] != "panel")
        assert len(signs) == blades and all(s.props["y"] + s.props["h"] > facade_top for s in signs)


# --- Venice ---------------------------------------------------------------------------


def test_before_1300_the_palazzo_is_veneto_byzantine():
    lot, _ = derive_venice(PalazzoSite(30.0, 1225, K.GRAND))
    assert [s.label for s in lot.children] == ["Torresella", "Body", "Torresella"]
    building, _ = generate_venice(PalazzoSite(30.0, 1225, K.GRAND))
    by_role = {n.props["role"]: n for n in building.children if n.kind == "storey"}
    arches = {r: sum(1 for o in walk(by_role[r]) if o.kind == "opening") for r in ("portico", "loggia")}
    assert arches["loggia"] >= 2 * arches["portico"] - 1 and arches["portico"] >= 3
    assert all(o.props["head"] == "round" for r in ("portico", "loggia") for o in walk(by_role[r]) if o.kind == "opening")
    body_top = by_role["loggia"].props["y"] + by_role["loggia"].props["h"]
    assert by_role["tower_top"].props["y"] >= body_top - 1e-6  # the towers rise above the cornice
    assert any(n.kind == "gable" and "merlons" in n.id for n in building.children)  # the Fondaco's crenellation
    # The Gothic type is untouched from 1300 on.
    gothic, _ = derive_venice(PalazzoSite(19.0, 1430, K.GRAND))
    assert gothic.children[0].label == "Facade"
