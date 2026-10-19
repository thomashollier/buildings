"""Sana'a tower houses, Cairo house fronts, Straits shophouses and pagodas."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.cairo.grammar import CairoSite, derive_cairo, generate_cairo
from buildings.typologies.pagoda.grammar import PagodaSite, derive_pagoda, generate_pagoda
from buildings.typologies.paris.generate import walk
from buildings.typologies.sanaa.grammar import SanaaSite, derive_sanaa, generate_sanaa
from buildings.typologies.shophouse.grammar import ShophouseSite, derive_shophouse, generate_shophouse, shophouse_kind

CASES = [
    ("sanaa_modest", generate_sanaa, derive_sanaa, SanaaSite(7.0, 1850, K.MODEST, seed=0)),
    ("sanaa_setback", generate_sanaa, derive_sanaa, SanaaSite(9.0, 1900, K.COMFORTABLE, seed=3)),
    ("sanaa_shibam", generate_sanaa, derive_sanaa, SanaaSite(8.5, 1880, K.ORDINARY, seed=4)),
    ("cairo_modest", generate_cairo, derive_cairo, CairoSite(8.0, 1650, K.MODEST, seed=0)),
    ("cairo_rashid", generate_cairo, derive_cairo, CairoSite(13.0, 1780, K.COMFORTABLE, seed=5)),
    ("cairo_grand", generate_cairo, derive_cairo, CairoSite(18.0, 1648, K.GRAND, seed=4)),
    ("shophouse_early", generate_shophouse, derive_shophouse, ShophouseSite(4.6, 1845, K.MODEST, seed=0)),
    ("shophouse_late_straits", generate_shophouse, derive_shophouse, ShophouseSite(5.8, 1920, K.GRAND, seed=3)),
    ("shophouse_deco_row", generate_shophouse, derive_shophouse, ShophouseSite(4.8, 1938, K.COMFORTABLE, seed=4, units=3)),
    ("pagoda_japanese", generate_pagoda, derive_pagoda, PagodaSite(6.4, 700, K.ORDINARY, seed=1)),
    ("pagoda_mokoshi", generate_pagoda, derive_pagoda, PagodaSite(8.6, 826, K.GRAND, seed=3)),
    ("pagoda_chinese", generate_pagoda, derive_pagoda, PagodaSite(12.0, 707, K.GRAND, seed=5)),
]


@pytest.mark.parametrize("name,generate,derive,site", CASES, ids=[c[0] for c in CASES])
def test_each_derives_traces_renders_and_repeats(name, generate, derive, site):
    building, _ = generate(site)
    nodes = list(walk(building))
    assert all(n.trace for n in nodes)
    assert len({n.id for n in nodes}) == len(nodes)
    assert to_json(generate(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, derivation = derive(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label not in derivation.grammar.overhangs:
            assert shape.parent.scope.contains(shape.scope), shape


def _shapes(lot, label):
    return [s for s in lot.walk() if s.label == label]


def test_every_sanaa_window_carries_its_qamariya_and_the_stone_floors_none():
    lot, _ = derive_sanaa(SanaaSite(10.0, 1870, K.GRAND, seed=1))
    for cell in (c for c in _shapes(lot, "Cell") if c.attr("opening_type") == "window"):
        fans = [s for s in cell.walk() if s.label == "Qamariya"]
        lights = [s for s in cell.walk() if s.label == "Light"]
        if cell.attr("floor") in ("brick", "mafraj"):
            assert fans and all(f.scope.y >= max(l.scope.y + l.scope.h for l in lights) for f in fans)
        else:
            assert not fans
    floors = [s.attr("floor") for s in _shapes(lot, "Storey")]
    assert floors[:2] == ["ground", "store"] and floors[-1] == "mafraj"
    # Shibam: no friezes and no fanlights.
    shibam, _ = derive_sanaa(SanaaSite(8.5, 1880, K.ORDINARY, seed=4))
    assert not _shapes(shibam, "Qamariya") and "frieze" not in [s.attr("floor") for s in _shapes(shibam, "Storey")]


def test_money_builds_the_sanaa_tower_higher():
    def storeys(klass):
        lot, _ = derive_sanaa(SanaaSite(8.0, 1880, klass, seed=0))
        return sum(1 for s in _shapes(lot, "Storey") if s.attr("floor") != "frieze")

    counts = [storeys(k) for k in (K.MODEST, K.ORDINARY, K.COMFORTABLE, K.GRAND)]
    assert counts == sorted(counts) and 5 <= counts[0] and counts[-1] <= 8


def test_the_cairo_ground_floor_is_blind_but_for_its_portal_and_oriels_stand_on_corbels():
    lot, _ = derive_cairo(CairoSite(14.0, 1650, K.COMFORTABLE, seed=0))
    ground = next(s for s in _shapes(lot, "Storey") if s.attr("floor") == "ground")
    openings = [c for c in ground.children if c.label == "Cell" and c.attr("opening_type") != "none"]
    doors = [c for c in openings if c.attr("opening_type") == "pedestrian_entrance"]
    assert len(doors) == 1 and any(s.label == "Hood" for s in doors[0].walk())
    assert all(c.attr("sill") >= 3.0 for c in openings if c not in doors)
    oriels = _shapes(lot, "Oriel")
    assert oriels
    for oriel in oriels:
        corbel, box = oriel.children
        assert corbel.label == "Corbel" and box.label == "Box" and corbel.scope.y < box.scope.y
        # The wall behind an oriel is the oriel's: no window cut there.
        storey = oriel.parent
        behind = [c for c in storey.children if c.label == "Cell" and c.scope.x <= oriel.scope.x and oriel.scope.x + oriel.scope.w <= c.scope.x + c.scope.w]
        assert behind and behind[0].attr("opening_type") == "none"


def test_the_date_picks_the_shophouse_and_the_shop_stands_back_in_the_five_foot_way():
    years = (1845, 1875, 1900, 1920, 1938, 1955)
    assert [shophouse_kind(y) for y in years] == ["early", "southern_chinese", "early_straits", "late_straits", "art_deco", "early_modern"]
    b, _ = generate_shophouse(ShophouseSite(5.0, 1920, K.ORDINARY, units=2))
    recesses = [n for n in walk(b) if n.kind == "storey" and n.props["role"] == "recess"]
    piers = [n for n in walk(b) if n.kind == "storey" and n.props["role"] == "pier"]
    assert len(recesses) == 2 and len(piers) == 4
    assert all(r.props["wall_material"] == "shadow" for r in recesses)
    assert all(p.props["wall_material"] != "shadow" for p in piers)

    def upper_windows(year):
        lot, _ = derive_shophouse(ShophouseSite(5.8, year, K.ORDINARY))
        upper = next(s for s in _shapes(lot, "Storey") if s.attr("floor") == "upper")
        return sum(1 for c in upper.children if c.label == "Cell" and c.attr("opening_type") == "window")

    assert [upper_windows(y) for y in (1845, 1875, 1920)] == [1, 2, 3]


def test_pagoda_tiers_narrow_upwards_and_japanese_eaves_reach_further():
    for site in (PagodaSite(6.4, 700, K.ORDINARY, seed=1), PagodaSite(12.0, 707, K.GRAND, seed=5)):
        lot, _ = derive_pagoda(site)
        tiers = _shapes(lot, "Tier")
        assert len(tiers) % 2 == 1 and len(tiers) == lot.attrs["tiers"]
        widths = [t.scope.w for t in tiers]
        assert widths == sorted(widths, reverse=True) and len(set(widths)) == len(widths)
        floors = [t.scope.y for t in tiers]
        assert floors == sorted(floors)
    jp, _ = derive_pagoda(PagodaSite(6.4, 700, K.ORDINARY, seed=1))
    cn, _ = derive_pagoda(PagodaSite(6.4, 700, K.ORDINARY, seed=2))
    assert jp.attrs["tradition"] == "japanese" and cn.attrs["tradition"] == "chinese"
    first_eave = _shapes(jp, "Eave")[0]
    assert first_eave.scope.w > 1.7 * _shapes(jp, "Tier")[0].scope.w
    assert len(_shapes(cn, "Tier")) > len(_shapes(jp, "Tier"))
    assert next(iter(_shapes(jp, "Finial"))).attr("finial_form") == "sorin"
