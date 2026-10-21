"""The Venetian palazzo against the fidelity review (dev/fidelity/venice/grading.md):
one test per recommendation it implements, in its ranked order."""

from __future__ import annotations

from collections import Counter

import pytest

from buildings.site import BuildingClass as K
from buildings.typologies.paris.generate import walk
from buildings.typologies.venice.grammar import PalazzoSite, derive_venice, generate_venice

SEEDS = range(100)


def _storeys(building):
    return [n for n in building.children if n.kind == "storey"]


def _lot_attrs(site):
    lot, _ = derive_venice(site)
    return lot.attrs


# 1. The ogee and the springing ------------------------------------------------------


def test_arches_spring_from_their_capitals_and_an_ogee_has_a_point_and_a_finial():
    for site in (PalazzoSite(19.0, 1430, K.GRAND), PalazzoSite(16.0, 1250, K.COMFORTABLE, seed=1)):
        building, _ = generate_venice(site)
        for storey in _storeys(building):
            cols = [n for n in storey.children if n.kind == "column" and n.props.get("order") in ("colonnette", "byzantine")]
            lights = [n for n in walk(storey) if n.kind == "opening" and n.props.get("head_rise")]
            for col in cols:
                top = col.props["y"] + col.props["h"]
                springings = [
                    o.props["y"] + o.props["h"] - o.props["head_rise"]
                    for o in lights
                    if abs(o.props["x"] - (col.props["x"] + col.props["w"])) < 0.3 or abs(o.props["x"] + o.props["w"] - col.props["x"]) < 0.3
                ]
                assert springings and top <= min(springings) + 1e-6  # the capital is at (or under a stilt below) the springing
                assert top >= min(springings) - 0.4
    building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND))
    ogees = [n for n in walk(building) if n.kind == "opening" and n.props.get("head") == "ogee"]
    assert ogees and all(0.6 <= o.props["head_rise"] / o.props["w"] <= 0.8 for o in ogees if o.props["opening_type"] == "window")
    assert all(o.props.get("head_finial") == "fleuron" for o in ogees)


# 2-3. The Byzantine front: centre and wings, its tectonics ----------------------------


@pytest.mark.parametrize("width,klass", [(12.0, K.ORDINARY), (16.0, K.COMFORTABLE), (22.0, K.COMFORTABLE)])
def test_a_byzantine_front_is_an_odd_graded_centre_between_two_wings(width, klass):
    lot, _ = derive_venice(PalazzoSite(width, 1230, klass))
    assert [s.label for s in lot.children] == ["Body"]  # no torreselle but on the fondaco
    portico, loggia = (s for s in lot.children[0].children if s.label == "Storey")
    bays = [c for c in portico.children if c.label == "Cell" and c.attrs["slot"].name == "bay"]
    assert [b.attrs["part"] for b in bays] == ["wing", "centre", "wing"]
    piers = [c for c in portico.children if c.label == "Cell" and c.attrs["slot"].name == "end"]
    assert piers[1].scope.w > piers[0].scope.w  # a wider pier sets the wings off
    centre = bays[1].attrs
    n = len(centre["lights"])
    assert n % 2 == 1 and 3 <= n <= 7
    fr = centre["lights"]
    assert fr[n // 2] == max(fr) and fr[0] == fr[-1] == min(fr)  # graded: widest in the middle
    assert 1 <= len(bays[0].attrs["lights"]) <= 2
    up = [c for c in loggia.children if c.label == "Cell" and c.attrs["slot"].name == "bay"]
    assert len(up[1].attrs["lights"]) == 2 * n - 1
    assert len(up[0].attrs["lights"]) == len(bays[0].attrs["lights"]) + 1


def test_byzantine_supports_are_smooth_columns_the_portico_open_with_paterae():
    building, _ = generate_venice(PalazzoSite(30.0, 1225, K.GRAND))
    nodes = list(walk(building))
    orders = {n.props.get("order") for n in nodes if n.kind == "column"}
    assert "corinthian" not in orders and "pilaster" not in orders
    assert {"byzantine", "arris"} <= orders
    portico = next(s for s in _storeys(building) if s.props["role"] == "portico")
    assert {o.props["opening_type"] for o in walk(portico) if o.kind == "opening"} == {"open_arch"}
    assert any(n.kind == "keystone" and n.props["keystone_kind"] == "patera" for n in nodes)
    assert any(n.kind == "string_course" and n.props["course_kind"] == "paterae" for n in nodes)


# 4. Polifora light counts ---------------------------------------------------------------


def test_both_nobile_polifore_have_the_same_lights_and_the_class_caps_them():
    caps = {K.MODEST: 4, K.ORDINARY: 5, K.COMFORTABLE: 6, K.GRAND: 6}
    for width in (11.0, 14.0, 16.0, 19.0, 22.0, 25.0, 30.0):
        for klass in K:
            for seed in range(6):
                lot, _ = derive_venice(PalazzoSite(width, 1450, klass, seed=seed))
                cells = {
                    st.attrs["floor"]: next(c for c in st.walk() if c.label == "Cell" and c.attrs.get("divider") == "Colonnette")
                    for st in lot.children[0].children
                    if st.label == "Storey" and st.attrs["floor"] in ("nobile1", "nobile2", "third")
                }
                n1, n2 = len(cells["nobile1"].attrs["lights"]), len(cells["nobile2"].attrs["lights"])
                assert n1 == n2
                assert 3 <= n1 <= caps[klass] + (2 if klass == K.GRAND else 0)
                if "third" in cells:
                    assert len(cells["third"].attrs["lights"]) <= max(3, n1 - 2)


def test_polifora_lights_are_slender_everywhere_never_broad_and_squat():
    """Round 2: no three broad lights (about 1:1.2) on a third floor or a
    modest front; a light at most 1.1 m wide and at least 2.5 times as tall."""
    for width in (9.0, 11.0, 14.0, 17.0, 20.0, 26.0, 30.0):
        for klass in K:
            for seed in range(0, 100, 9):
                building, _ = generate_venice(PalazzoSite(width, 1440, klass, seed=seed))
                for storey in _storeys(building):
                    if storey.props["role"] not in ("nobile", "third"):
                        continue
                    for o in walk(storey):
                        if o.kind == "opening" and o.props["opening_type"] == "window":
                            assert o.props["w"] <= 1.1 + 1e-9, o.id
                            assert o.props["h"] >= 2.5 * o.props["w"] - 1e-9, o.id


# 5. Stone balustrades -----------------------------------------------------------------------


def test_balconies_are_stone_balustrades_on_corbels_iron_only_as_a_later_variant():
    rails = Counter()
    for seed in range(20):
        building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=seed))
        for n in building.children:
            if n.kind == "ironwork":
                rails[n.props.get("ironwork_pattern")] += 1
                if "/centre/" in n.id:
                    assert n.props["ironwork_pattern"] == "stone_balustrade"
    assert rails["stone_balustrade"] > 3 * rails[None]
    # A Veneto-Byzantine loggia has no balusters: solid marble plutei, or nothing.
    building, _ = generate_venice(PalazzoSite(30.0, 1225, K.GRAND))
    patterns = {n.props.get("ironwork_pattern") for n in building.children if n.kind == "ironwork"}
    assert patterns == {"pluteus"}
    pluteus = next(n for n in building.children if n.kind == "ironwork")
    assert len(pluteus.props["panel_edges"]) == pluteus.props["panel_count"] + 1
    open_loggias = sum(
        not any(n.kind == "ironwork" for n in generate_venice(PalazzoSite(16.0, 1250, K.ORDINARY, seed=s))[0].children)
        for s in range(20)
    )
    assert 0 < open_loggias < 20


# 6. The storey stack ----------------------------------------------------------------------


def test_the_water_storey_is_as_tall_as_a_nobile_floor_and_its_mezzanine_is_in_the_wings():
    for klass in K:
        lot, _ = derive_venice(PalazzoSite(16.0, 1420, klass, seed=0))
        heights = {s.attrs["floor"]: s.scope.h for s in lot.children[0].children if s.label == "Storey"}
        assert heights["water"] == pytest.approx(heights["nobile1"], abs=0.25)
        assert abs(heights["nobile2"] - heights["nobile1"]) <= 0.2 + 1e-9
    lot, _ = derive_venice(PalazzoSite(16.0, 1420, K.COMFORTABLE, seed=0))
    assert lot.attrs["mezz"]
    water = next(s for s in lot.children[0].children if s.label == "Storey" and s.attrs["floor"] == "water")
    tiers = [t for t in water.walk() if t.label == "WingTier"]
    assert tiers and all(t.parent.label == "Wing" for t in tiers)
    assert not any(c.attrs.get("tier") == "mezz" for c in water.walk() if c.label == "Cell" and c.parent.label == "Centre")
    assert sum(_lot_attrs(PalazzoSite(16.0, 1420, K.ORDINARY, seed=s))["mezz"] for s in SEEDS) == 50


def test_over_the_second_nobile_floor_nothing_an_attic_or_a_third_floor():
    tops = Counter(_lot_attrs(PalazzoSite(22.0, 1440, K.GRAND, seed=s))["top"] for s in SEEDS)
    assert tops == {"none": 40, "attic": 35, "third": 25}
    poorer = Counter(_lot_attrs(PalazzoSite(22.0, 1440, K.ORDINARY, seed=s))["top"] for s in SEEDS)
    assert poorer["third"] == 0


# 7. Two gates ---------------------------------------------------------------------------------


def test_one_wide_front_in_four_has_two_gates_side_by_side_under_the_polifora():
    attrs = [_lot_attrs(PalazzoSite(22.0, 1440, K.GRAND, seed=s)) for s in SEEDS]
    assert sum(a["gate_pair"] for a in attrs) == 25
    # Round 2: never out in the wings, whatever the family.
    for seed in SEEDS:
        building, _ = generate_venice(PalazzoSite(20.0, 1376, K.COMFORTABLE, seed=seed))
        gates = [n for n in walk(building) if n.kind == "opening" and n.props["opening_type"] == "water_gate"]
        assert gates and all("/centre/" in g.id for g in gates)
    assert not any(_lot_attrs(PalazzoSite(18.0, 1440, K.GRAND, seed=s))["gate_pair"] for s in SEEDS)
    building, _ = generate_venice(PalazzoSite(22.0, 1440, K.GRAND, seed=0))
    gates = [n for n in walk(building) if n.kind == "opening" and n.props["opening_type"] == "water_gate"]
    assert len(gates) == 2 and all("/centre/" in g.id for g in gates)
    polifora = [n for n in walk(building) if n.kind == "surround" and n.props["surround_kind"] == "dentil_panel" and n.id.endswith("/frame")]
    left, right = polifora[0].props["x"], polifora[0].props["x"] + polifora[0].props["w"]
    assert all(left <= g.props["x"] and g.props["x"] + g.props["w"] <= right for g in gates)


# 8. Stone frames and the quatrefoil band --------------------------------------------------


def test_the_polifora_and_wing_windows_stand_in_dentilled_stone_frames():
    building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=4))
    kinds = Counter(n.props["surround_kind"] for n in walk(building) if n.kind == "surround")
    assert set(kinds) == {"dentil_panel"} and kinds["dentil_panel"] > 10


def test_a_quatrefoil_over_every_colonnette_on_the_traceried_floor_from_1420():
    building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=4))  # tracery on the first nobile floor
    for storey in _storeys(building):
        q = sum(1 for n in walk(storey) if n.kind == "opening" and n.props["opening_type"] == "quatrefoil")
        cols = sum(1 for n in storey.children if n.kind == "column" and n.props.get("order") == "colonnette")
        traced = storey.id.endswith("s1")
        assert q == (cols if traced else 0), storey.id
    # Round 2: the tracery is one web with the arcade. Each quatrefoil stands
    # between the two arch tips beside it, its centre about level with them,
    # and the stone web begins at the arches' springing, inside the frame.
    storey = next(s for s in _storeys(building) if s.id.endswith("s1"))
    lights = [n for n in walk(storey) if n.kind == "opening" and n.props["opening_type"] == "window" and "/centre/" in n.id]
    tips = max(o.props["y"] + o.props["h"] for o in lights)
    spring = min(o.props["y"] + o.props["h"] - o.props["head_rise"] for o in lights)
    (band,) = [n for n in walk(storey) if n.kind == "opening" and n.props["opening_type"] == "tracery_band"]
    assert band.props["y"] == pytest.approx(spring)
    frame = next(n for n in walk(storey) if n.kind == "surround" and n.id.endswith("/frame"))
    assert band.props["y"] + band.props["h"] == pytest.approx(frame.props["y"] + frame.props["h"])
    for q in (n for n in walk(storey) if n.kind == "opening" and n.props["opening_type"] == "quatrefoil"):
        cy = q.props["y"] + q.props["h"] / 2.0
        assert abs(cy - tips) < 0.35
    bay = next(n for n in walk(storey) if n.kind == "bay" and any(c.props.get("opening_type") == "tracery_band" for c in n.children))
    assert bay.children[0].props["opening_type"] == "tracery_band"  # drawn behind the arches
    early, _ = generate_venice(PalazzoSite(19.0, 1400, K.GRAND, seed=4))
    assert not any(n.props.get("opening_type") == "quatrefoil" for n in walk(early))
    plain, _ = generate_venice(PalazzoSite(19.0, 1450, K.ORDINARY, seed=4))
    assert not any(n.props.get("opening_type") == "quatrefoil" for n in walk(plain))


# 9-14 -------------------------------------------------------------------------------------------


def test_the_water_gate_is_an_open_arch_whose_head_is_the_familys():
    heads = Counter(_lot_attrs(PalazzoSite(16.0, 1440, K.ORDINARY, seed=s))["gate_head"] for s in SEEDS)
    assert heads == {"pointed": 45, "ogee": 55}  # no round-headed gate on a Gothic front
    early = Counter(_lot_attrs(PalazzoSite(16.0, 1320, K.ORDINARY, seed=s))["gate_head"] for s in SEEDS)
    assert early == {"pointed": 75, "round": 25}
    middle = Counter(_lot_attrs(PalazzoSite(16.0, 1360, K.ORDINARY, seed=s))["gate_head"] for s in SEEDS)
    assert middle == {"pointed": 100}
    building, _ = generate_venice(PalazzoSite(16.0, 1440, K.ORDINARY, seed=1))
    water = next(s for s in _storeys(building) if s.props["role"] == "water")
    (gate,) = [n for n in walk(water) if n.kind == "opening" and n.props["opening_type"] == "water_gate"]
    assert gate.props["grille_bars"] >= 3
    frame = next(n for n in walk(water) if n.kind == "surround" and n.id.startswith(gate.id.rsplit("/", 1)[0]))
    assert frame.props["y"] + frame.props["h"] < water.props["y"] + water.props["h"] - 0.2  # inside the water storey


def test_istrian_corners_a_base_course_and_the_wall_by_family():
    building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND))
    assert sum(1 for n in building.children if n.kind == "column" and n.props["order"] in ("dentil_strip", "quoins")) == 2
    corners = Counter(
        next(n.props["order"] for n in generate_venice(PalazzoSite(16.0, 1440, K.ORDINARY, seed=s))[0].children if n.kind == "column")
        for s in range(20)
    )
    assert corners["quoins"] > 0 and corners["dentil_strip"] > 0
    assert any(n.kind == "socle" and n.props["treatment"] == "istrian_course" for n in walk(building))
    walls = Counter(_lot_attrs(PalazzoSite(16.0, 1440, K.ORDINARY, seed=s))["palazzo_wall"] for s in SEEDS)
    assert walls == {"brick": 40, "stucco_rose": 30, "stucco": 20, "plaster_ochre": 10}


def test_the_family_reaches_the_byzantine_front():
    """Round 2: two modest fronts of different families were byte-identical."""
    from buildings.render.svg.render import render

    for width, klass in ((28.0, K.MODEST), (16.0, K.ORDINARY), (22.0, K.COMFORTABLE)):
        drawings = {render(generate_venice(PalazzoSite(width, 1250, klass, seed=s))[0]) for s in range(20)}
        assert len(drawings) >= 10
    a = render(generate_venice(PalazzoSite(28.0, 1291, K.MODEST, seed=54))[0])
    b = render(generate_venice(PalazzoSite(28.0, 1245, K.MODEST, seed=73))[0])
    assert a != b


def test_only_the_grand_fondaco_has_towers_and_merlons_and_they_are_large():
    for width, klass in ((22.0, K.COMFORTABLE), (18.0, K.GRAND), (16.0, K.ORDINARY)):
        lot, _ = derive_venice(PalazzoSite(width, 1230, klass))
        assert [s.label for s in lot.children] == ["Body"]
        assert not lot.attrs["crenellated"]
    building, _ = generate_venice(PalazzoSite(30.0, 1225, K.GRAND))
    merlons = [n for n in building.children if n.kind == "gable" and "merlons" in n.id]
    assert merlons and all(m.props["h"] >= 2.0 for m in merlons)
    tower = next(s for s in _storeys(building) if s.props["role"] == "tower_loggia")
    assert sum(1 for n in walk(tower) if n.kind == "opening") == 4


@pytest.mark.parametrize("width", [14.0, 16.0, 19.0, 22.0])
def test_two_windows_a_wing_on_a_middling_front(width):
    lot, _ = derive_venice(PalazzoSite(width, 1430, K.COMFORTABLE))
    nobile = next(s for s in lot.children[0].children if s.label == "Storey" and s.attrs["floor"] == "nobile1")
    for wing in (c for c in nobile.children if c.label == "Wing"):
        assert sum(1 for c in wing.children if c.label == "Cell" and c.attrs["slot"].name == "bay") == 2
        for cell in wing.children:
            if cell.attrs["slot"].name == "bay":
                assert cell.attrs["light_height"] <= 3.2 * cell.attrs["light_width"] + 1e-9


def test_a_narrow_palazzetto_has_one_wing():
    lot, _ = derive_venice(PalazzoSite(8.0, 1420, K.ORDINARY))
    st = next(s for s in lot.children[0].children if s.label == "Storey")
    assert [c.label for c in st.children if c.label in ("Wing", "Centre")] in (["Centre", "Wing"], ["Wing", "Centre"])


def test_a_low_roof_behind_the_cornice_and_funnel_chimneys_by_family():
    building, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND))
    assert sum(1 for n in building.children if n.kind == "special" and n.props["element"] == "fumaiolo") == 2
    cornice = next(n for n in walk(building) if n.kind == "cornice")
    assert cornice.props["cornice_ornament"] == "corbelled_eave" and cornice.props["projection"] >= 0.6
    roofs, counts, plinths = 0, set(), set()
    for s in range(20):
        b, _ = generate_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=s))
        top = next(n for n in walk(b) if n.kind == "cornice")
        for roof in (n for n in b.children if n.kind == "gable" and n.props["wall_material"] == "tile_red"):
            roofs += 1
            # a sliver at most, standing back from the front, behind the cornice
            assert roof.props["h"] <= 1.2 and roof.props["x"] >= 1.0
            assert roof.props["y"] >= top.props["y"] + 0.3
        counts.add(sum(1 for n in b.children if n.kind == "special"))
        plinths.add(next(n for n in walk(b) if n.kind == "socle").props["h"])
    assert 0 < roofs < 20 and len(counts) >= 2 and len(plinths) >= 3


# Round 3 of the blind test ---------------------------------------------------------


def test_the_palazzo_stands_in_the_canal_with_steps_at_the_gate():
    from buildings.render.svg.colors import COLORS
    from buildings.render.svg.render import render

    for site in (PalazzoSite(16.0, 1410, K.COMFORTABLE), PalazzoSite(16.0, 1250, K.COMFORTABLE, seed=1)):
        building, _ = generate_venice(site)
        assert building.props["ground"] == "canal"
        svg = render(building)
        assert COLORS["water"] in svg and COLORS["ground"] not in svg
    building, _ = generate_venice(PalazzoSite(16.0, 1410, K.COMFORTABLE))
    steps = [n for n in walk(building) if n.kind == "socle" and n.props["treatment"] == "water_steps"]
    assert steps and all(s.props["y"] < 0 for s in steps)


def test_some_lights_are_rondel_glazed_or_shuttered():
    glazings = Counter()
    for s in range(20):
        building, _ = generate_venice(PalazzoSite(16.0, 1430, K.ORDINARY, seed=s))
        for o in walk(building):
            if o.kind == "opening" and o.props.get("glazing"):
                glazings[o.props["glazing"]] += 1
                if o.props["glazing"] == "rondel":
                    assert o.props["rondel_cols"] >= 2 and o.props["rondel_rows"] >= 2
    assert glazings["rondel"] > 0 and glazings["scuri"] > 0


def test_byzantine_stilted_arches_have_an_extradosed_archivolt_down_the_stilt():
    building, _ = generate_venice(PalazzoSite(16.0, 1250, K.COMFORTABLE, seed=1))
    arches = [o for o in walk(building) if o.kind == "opening" and o.props.get("head") == "round"]
    assert arches and all(o.props["archivolt"] == "extradosed" and o.props["archivolt_stilt"] > 0 for o in arches)
