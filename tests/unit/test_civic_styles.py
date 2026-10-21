"""Second Empire, Beaux-Arts, Spanish Colonial Revival and the brownstone."""

from __future__ import annotations

import math

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.beaux_arts.grammar import BeauxArtsSite, derive_beaux_arts, generate_beaux_arts, manner
from buildings.typologies.brownstone.grammar import BrownstoneSite, brownstone_dress, derive_brownstone, generate_brownstone
from buildings.typologies.paris.generate import walk
from buildings.typologies.second_empire.grammar import SecondEmpireSite, derive_second_empire, generate_second_empire
from buildings.typologies.spanish_colonial.grammar import SpanishSite, derive_spanish_colonial, generate_spanish_colonial

SE = ("Cornice", "Chimney")
BA = ("Cornice",)
SC = ()
BR = ("Cornice", "Hood", "Sill")

CASES = [
    ("second_empire_centre", generate_second_empire, derive_second_empire, SecondEmpireSite(30.0, 1872, K.MODEST, seed=1), SE),
    ("second_empire_ends", generate_second_empire, derive_second_empire, SecondEmpireSite(28.0, 1869, K.COMFORTABLE, seed=2), SE),
    ("second_empire_five", generate_second_empire, derive_second_empire, SecondEmpireSite(60.0, 1884, K.GRAND, seed=5), SE),
    ("beaux_arts_palazzo", generate_beaux_arts, derive_beaux_arts, BeauxArtsSite(26.0, 1890, K.COMFORTABLE, seed=2), BA),
    ("beaux_arts_giant", generate_beaux_arts, derive_beaux_arts, BeauxArtsSite(40.0, 1902, K.GRAND, seed=3), BA),
    ("beaux_arts_giant_small", generate_beaux_arts, derive_beaux_arts, BeauxArtsSite(24.0, 1899, K.COMFORTABLE, seed=0), BA),
    ("spanish_small", generate_spanish_colonial, derive_spanish_colonial, SpanishSite(12.0, 1918, K.MODEST, seed=0), SC),
    ("spanish_tower", generate_spanish_colonial, derive_spanish_colonial, SpanishSite(22.0, 1926, K.COMFORTABLE, seed=2), SC),
    ("spanish_tower_wing", generate_spanish_colonial, derive_spanish_colonial, SpanishSite(38.0, 1932, K.GRAND, seed=4), SC),
    ("brownstone_italianate", generate_brownstone, derive_brownstone, BrownstoneSite(1860, K.ORDINARY, 0), BR),
    ("brownstone_neo_grec_bay", generate_brownstone, derive_brownstone, BrownstoneSite(1880, K.ORDINARY, 3, 6.7), BR),
    ("brownstone_romanesque", generate_brownstone, derive_brownstone, BrownstoneSite(1890, K.GRAND, 5, 7.6), BR),
]


@pytest.mark.parametrize("name,generate,derive,site,overhangs", CASES, ids=[c[0] for c in CASES])
def test_each_derives_traces_renders_and_repeats(name, generate, derive, site, overhangs):
    building, _ = generate(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in overhangs:
            assert shape.parent.scope.contains(shape.scope), shape


# --- Second Empire: pavilions rise above the ranges ---------------------------


def _roof_height_at(points, x):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1 and x1 > x0:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError(x)


def test_second_empire_pavilion_roofs_rise_above_the_ranges_and_carry_paired_columns():
    site = SecondEmpireSite(60.0, 1884, K.GRAND, seed=5)
    lot, _ = derive_second_empire(site)
    kinds, sizes = lot.attrs["kinds"], lot.attrs["sizes"]
    assert kinds == ["end", "range", "centre", "range", "end"]
    building, _ = generate_second_empire(site)
    roof = next(n for n in walk(building) if n.kind == "gable" and n.props["form"] == "pavilion")
    starts = [sum(sizes[:i]) for i in range(len(sizes))]
    tops = [_roof_height_at(roof.props["points"], s + w / 2.0) for s, w in zip(starts, sizes)]
    for i, k in enumerate(kinds):
        if k == "range":
            assert tops[i] + 2.0 < tops[i - 1] and tops[i] + 2.0 < tops[i + 1]
    # A rich building's pavilions pair their columns: two on every pier line.
    principal = next(s for s in lot.walk() if s.label == "Storey" and s.attr("floor") == "principal" and s.attr("kind") == "end")
    columns = [c for c in principal.children if c.label == "Column"]
    firsts = [c for c in columns if c.id.endswith("a")]
    seconds = [c for c in columns if c.id.endswith("b")]
    assert firsts and len(seconds) == len(firsts)
    for a, b in zip(firsts, seconds):
        assert 0.0 < b.scope.x - (a.scope.x + a.scope.w) < 0.5


# --- Beaux-Arts: a giant order spans storeys; a palazzo goes storey by storey -


def test_beaux_arts_giant_order_spans_several_storeys_and_a_palazzo_has_none():
    giant = BeauxArtsSite(40.0, 1902, K.GRAND, seed=3)
    palazzo = BeauxArtsSite(26.0, 1890, K.COMFORTABLE, seed=2)
    assert manner(giant) == "giant" and manner(palazzo) == "palazzo"

    lot, _ = derive_beaux_arts(giant)
    storeys = [s for s in lot.walk() if s.label == "Storey" and s.attr("kind") == "colonnade"]
    giant_storeys = [s for s in storeys if s.attr("floor") == "giant"]
    columns = [c for c in lot.walk() if c.label == "Column" and c.attr("order") == "corinthian"]
    assert columns and all(c.scope.h >= 2 * giant_storeys[0].scope.h for c in columns)
    # The attic stands over the main entablature, at the top.
    assert storeys[-1].attr("floor") == "attic" and storeys[-2].attr("floor") == "frieze"
    # A grand front is crowned by a sculpture group over its centre.
    b, _ = generate_beaux_arts(giant)
    group = next(n for n in walk(b) if n.id.endswith("sculpture"))
    assert abs(group.props["x"] + group.props["w"] / 2.0 - giant.width / 2.0) < 1e-6

    lot, _ = derive_beaux_arts(palazzo)
    tallest = max(s.scope.h for s in lot.walk() if s.label == "Storey")
    assert all(c.scope.h <= tallest for c in lot.walk() if c.label == "Column")


# --- Spanish Colonial: a tower clear of a low tile roof, grilles below ------


def test_spanish_tower_rises_clear_of_a_low_tile_roof_and_ground_windows_are_grilled():
    site = SpanishSite(38.0, 1932, K.GRAND, seed=4)
    lot, _ = derive_spanish_colonial(site)
    assert lot.attrs["kinds"] == ["tower", "main", "wing"]
    roofs = {s.parent.attr("kind"): s for s in lot.walk() if s.label == "TileRoof"}
    main = roofs["main"].scope
    tower_storeys = [s for s in lot.walk() if s.label == "Storey" and s.attr("kind") == "tower"]
    assert tower_storeys[-1].attr("floor") == "belfry"
    assert tower_storeys[-1].scope.y >= main.y + main.h  # the belfry stands clear of the main roof
    # A tile roof's pitch is low: its rise is half the block's depth at 22 degrees.
    assert math.isclose(main.h, min(main.w, 12.0) / 2.0 * math.tan(math.radians(22.0)))
    b, _ = generate_spanish_colonial(site)
    grilles = [n for n in walk(b) if n.kind == "ironwork" and n.props.get("guards") == "window_grille"]
    assert grilles
    ground_top = next(s for s in lot.walk() if s.label == "Storey" and s.attr("floor") == "ground").scope.h
    assert all(g.props["y"] + g.props["h"] <= ground_top for g in grilles)
    # And a small one is a single block with no tower.
    small, _ = derive_spanish_colonial(SpanishSite(12.0, 1918, K.MODEST))
    assert small.attrs["kinds"] == ["main"]


# --- Brownstone: the stoop climbs the basement to the parlour door ----------


def test_brownstone_dress_by_date_and_the_stoop_climbs_to_the_parlour_door():
    from collections import Counter

    def dress(year):
        return Counter(derive_brownstone(BrownstoneSite(year, K.ORDINARY, seed))[0].attrs["kind"] for seed in range(30)).most_common(1)[0][0]

    assert [dress(y) for y in (1860, 1878, 1892)] == ["italianate", "neo_grec", "romanesque"]
    assert brownstone_dress(1860) == "italianate"
    for site in (BrownstoneSite(1860, K.ORDINARY, 0), BrownstoneSite(1888, K.ORDINARY, 1)):
        b, _ = generate_brownstone(site)
        stoop = next(n for n in walk(b) if n.kind == "gable" and n.id.endswith("/stoop"))
        door = next(n for n in walk(b) if n.kind == "opening" and n.props["opening_type"] == "pedestrian_entrance")
        assert math.isclose(stoop.props["y"] + stoop.props["h"], door.props["y"])
        assert stoop.props["x"] <= door.props["x"] + door.props["w"] / 2.0 <= stoop.props["x"] + stoop.props["w"]

    def hoods(year, seed):
        lot, _ = derive_brownstone(BrownstoneSite(year, K.ORDINARY, seed))
        b, _ = generate_brownstone(BrownstoneSite(year, K.ORDINARY, seed))
        return lot.attrs["kind"], {n.kind for n in walk(b) if n.id.endswith("/hood")}

    for seed in range(12):
        for year in (1860, 1878, 1892):
            kind, found = hoods(year, seed)
            expect = {"italianate": [{"cornice"}, {"string_course"}], "neo_grec": [{"string_course"}], "romanesque": [set()]}[kind]
            assert found in expect, (year, seed, kind, found)
