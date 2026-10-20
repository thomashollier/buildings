"""The Amsterdam canal house against the independent fidelity review
(dev/fidelity/amsterdam/grading.md): one test per recommendation."""

from __future__ import annotations

from collections import Counter

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.amsterdam.grammar import CanalSite, derive_amsterdam, gable_form, generate_amsterdam
from buildings.typologies.paris.generate import walk

SEEDS = range(60)


def _nodes(site, kind):
    building, _ = generate_amsterdam(site)
    return [n for n in walk(building) if n.kind == kind]


def _storeys(building):
    return [n for n in building.children if n.kind == "storey"]


def _openings(storey, kind=None):
    return [o for o in walk(storey) if o.kind == "opening" and (kind is None or o.props["opening_type"] == kind)]


def _xs(node):
    return [p[0] for p in node.props["points"]]


def _ys(node):
    return [p[1] for p in node.props["points"]]


@pytest.mark.parametrize("site", [
    CanalSite(6.6, 1620, K.COMFORTABLE), CanalSite(7.0, 1650, K.ORDINARY, 1), CanalSite(5.8, 1740, K.ORDINARY, 4),
    CanalSite(11.0, 1760, K.GRAND, 3), CanalSite(7.0, 1800, K.ORDINARY), CanalSite(9.5, 1700, K.ORDINARY, 5),
])
def test_every_house_derives_renders_repeats_and_stays_inside(site):
    building, _ = generate_amsterdam(site)
    assert len({n.id for n in walk(building)}) == sum(1 for _ in walk(building))
    assert to_json(generate_amsterdam(site)[0]) == to_json(building)
    assert "<svg" in render(building)
    lot, _ = derive_amsterdam(site)
    for shape in lot.walk():
        if shape.parent is not None and shape.label != "Cornice":
            assert shape.parent.scope.contains(shape.scope), shape


# --- 1. The stoop -----------------------------------------------------------

@pytest.mark.parametrize("seed", [0, 1])
def test_the_stoop_is_a_landing_before_the_door_and_a_side_flight_down_to_the_street(seed):
    site = CanalSite(6.6, 1750, K.ORDINARY, seed)
    building, _ = generate_amsterdam(site)
    lot, _ = derive_amsterdam(site)
    basement = lot.attrs["souterrain"]
    door = _openings(_storeys(building)[1], "pedestrian_entrance")[0].props
    parts = {n.id.rsplit("/", 1)[-1]: n for n in walk(building) if n.id.startswith("b/stoop/")}
    landing = parts["landing"]
    # The landing is at the bel-etage floor, in front of the door, wider than it by 0.3 m.
    assert max(_ys(landing)) == pytest.approx(basement)
    assert min(_xs(landing)) <= door["x"] - 0.15 + 1e-9 or min(_xs(landing)) <= 0.0 + 1e-9
    assert max(_xs(landing)) - min(_xs(landing)) >= door["w"] + 0.3
    assert min(_xs(landing)) <= door["x"] and max(_xs(landing)) >= door["x"] + door["w"]
    # One flight, beside the landing and not under the door, of 7-9 treads of about 0.19 m.
    flight = parts["flight0"]
    treads = [n for k, n in parts.items() if k.startswith("flight0_rail")]
    assert 7 <= len(treads) <= 9
    rises = sorted({round(n.props["y"], 4) for n in treads}, reverse=True)
    assert all(0.15 <= a - b <= 0.22 for a, b in zip(rises, rises[1:]))
    assert max(_ys(flight)) < basement
    door_span = (door["x"], door["x"] + door["w"])
    assert max(_xs(flight)) <= door_span[0] + 1e-9 or min(_xs(flight)) >= door_span[1] - 1e-9
    # Every tread descends away from the landing.
    ordered = sorted(treads, key=lambda n: abs(n.props["x"] - door["x"]))
    assert [n.props["y"] for n in ordered] == sorted((n.props["y"] for n in ordered), reverse=True)
    # An iron railing along both.
    assert parts["landing_rail"].kind == "ironwork" and parts["landing_rail"].props["h"] >= 0.85


def test_the_souterrain_door_is_under_the_landing_and_the_other_bays_keep_their_windows():
    building, _ = generate_amsterdam(CanalSite(6.6, 1750, K.ORDINARY, 0))
    souterrain, bel = _storeys(building)[:2]
    (sdoor,) = _openings(souterrain, "pedestrian_entrance")
    (door,) = _openings(bel, "pedestrian_entrance")
    assert abs((sdoor.props["x"] + sdoor.props["w"] / 2) - (door.props["x"] + door.props["w"] / 2)) < 0.01
    assert len(_openings(souterrain, "window")) >= 1


def test_a_door_in_the_middle_of_five_bays_has_a_double_stoop():
    building, _ = generate_amsterdam(CanalSite(11.0, 1760, K.GRAND, 3))
    bel = _storeys(building)[1]
    bays = [n for n in walk(bel) if n.kind == "bay" and n.props["slot_name"] == "bay"]
    assert len(bays) == 5
    (door,) = _openings(bel, "pedestrian_entrance")
    assert abs(door.props["x"] + door.props["w"] / 2 - 5.5) < 0.05
    assert {n.id for n in walk(building)} >= {"b/stoop/flight0", "b/stoop/flight1"}


# --- 2. Gable form by seeded, overlapping odds -----------------------------

def test_the_forms_overlap_in_time_and_the_seed_draws_from_them():
    def forms(year):
        return Counter(gable_form(year, seed) for seed in SEEDS)

    assert set(forms(1620)) == {"step"}
    assert {"step", "neck", "raised_neck"} <= set(forms(1650))  # Herengracht 168 (1638) is a neck
    assert {"neck", "bell", "straight"} <= set(forms(1690))  # Van Loon (1672) is a lijst
    late = forms(1770)
    assert late.most_common(1)[0][0] == "bell" and late["neck"] > 0
    assert forms(1810).most_common(1)[0][0] == "straight"


def test_a_wide_or_grand_front_takes_a_cornice_from_1660():
    assert all(gable_form(1700, s, width=11.0) == "straight" for s in SEEDS)
    assert all(gable_form(1680, s, klass=K.GRAND) == "straight" for s in SEEDS)
    assert gable_form(1630, 0, klass=K.GRAND) == "step"


# --- 3. The bell, 11. the hatch and the beam ------------------------------

@pytest.mark.parametrize("site", [CanalSite(5.8, 1740, K.ORDINARY, 4), CanalSite(6.6, 1770, K.ORDINARY, 0), CanalSite(8.0, 1770, K.COMFORTABLE, 0)])
def test_the_bell_holds_one_opening_on_the_axis_under_its_beam_and_closes_to_a_narrow_cap(site):
    building, _ = generate_amsterdam(site)
    assert building.props.get("w") == site.width
    (gable,) = [n for n in walk(building) if n.id == "b/gable"]
    assert gable.props["form"] == "bell"
    (attic,) = [n for n in _storeys(building) if n.props["role"] == "gable"]
    (hatch,) = _openings(attic)
    cx = site.width / 2
    assert hatch.props["opening_type"] == "pedestrian_entrance"
    assert abs(hatch.props["x"] + hatch.props["w"] / 2 - cx) < 1e-6
    bx, by = gable.props["hoist_beam"]
    assert abs(bx - cx) < 1e-6 and by >= hatch.props["y"] + hatch.props["h"]
    # Crown: the top 0.6 m of the outline is no wider than 0.3 of the frontage.
    top = max(_ys(gable))
    crown = [x for x, y in gable.props["points"] if y >= top - 0.6]
    assert max(crown) - min(crown) <= 0.3 * site.width
    # The outline encloses the attic storey: at its top it is wider than the storey.
    st_top = attic.props["y"] + attic.props["h"]
    near = [x for x, y in gable.props["points"] if abs(y - st_top) < 0.25 and x < cx]
    assert near and min(cx - x for x in near) > attic.props["w"] / 2
    # A stone band edges it.
    assert {"b/gable/band_l", "b/gable/band_r"} <= {n.id for n in walk(building)}


# --- 4. Neck: one tier; raised neck: two ------------------------------------

def test_the_neck_is_one_storey_and_the_raised_neck_has_a_shoulder():
    lot, _ = derive_amsterdam(CanalSite(7.2, 1690, K.COMFORTABLE, 1))
    gable = next(s for s in lot.children if s.label == "Gable")
    assert lot.attrs["form"] == "neck"
    tiers = [t for t in gable.children if t.label == "GableTier"]
    assert len(tiers) == 1 and tiers[0].children[0].scope.w == pytest.approx(0.40 * 7.2)
    assert 3.2 <= gable.scope.h <= 4.0  # about 0.5 of the frontage
    lot, _ = derive_amsterdam(CanalSite(7.0, 1650, K.ORDINARY, 1))
    assert lot.attrs["form"] == "raised_neck"
    gable = next(s for s in lot.children if s.label == "Gable")
    widths = [t.children[0].scope.w for t in gable.children if t.label == "GableTier"]
    assert len(widths) == 2 and widths[0] > widths[1]


# --- 5. Step gable: lower, fewer and larger steps; fewer storeys early ------

def test_the_step_gable_climbs_in_four_or_five_steps_a_side_over_two_storeys():
    building, _ = generate_amsterdam(CanalSite(6.6, 1620, K.COMFORTABLE))
    (gable,) = [n for n in walk(building) if n.id == "b/gable"]
    pts = gable.props["points"]
    cx = 3.3
    left = [p for p in pts if p[0] < cx - 1e-6]
    risers = sum(1 for a, b in zip(left, left[1:]) if abs(a[0] - b[0]) < 1e-9 and b[1] > a[1] + 1e-9)
    assert 4 <= risers <= 6
    assert gable.props["h"] <= 5.6
    caps = [n for n in walk(building) if n.id.startswith("b/gable/cap")]
    assert len(caps) >= 8 and all(n.props["wall_material"] != gable.props["wall_material"] for n in caps)
    lot, _ = derive_amsterdam(CanalSite(6.6, 1620, K.COMFORTABLE))
    assert len(lot.attrs["storey_heights"]) == 4  # souterrain, bel-etage, two uppers
    assert lot.attrs["souterrain"] == pytest.approx(1.0)


# --- 6. Stone trim ----------------------------------------------------------

def test_claw_pieces_pediment_and_plinth_are_stone():
    building, _ = generate_amsterdam(CanalSite(7.2, 1690, K.COMFORTABLE, 1))
    ids = {n.id: n for n in walk(building)}
    wall = ids["b/gable"].props["wall_material"]
    for part in ("claw0", "claw0_r", "pediment"):
        assert ids[f"b/gable/{part}"].props["wall_material"] not in (wall, "brick", "brick_dark", "basalt")
    souterrain = _storeys(building)[0]
    assert souterrain.props["wall_material"] != _storeys(building)[1].props["wall_material"]


# --- 7. Bel-etage and window taper -----------------------------------------

def test_the_bel_etage_is_tall_and_the_windows_shrink_going_up():
    building, _ = generate_amsterdam(CanalSite(6.6, 1750, K.ORDINARY, 0))
    storeys = _storeys(building)
    assert storeys[1].props["h"] >= 1.25 * storeys[2].props["h"]
    ratios = []
    for st in storeys[1:]:
        if st.props["role"] == "gable":
            continue
        w = _openings(st, "window")[0].props
        ratios.append(w["h"] / w["w"])
    assert ratios == sorted(ratios, reverse=True)
    assert 2.2 <= ratios[0] <= 3.0 and 1.45 <= ratios[-1] <= 1.8
    # The door and its fanlight reach the bel-etage window heads.
    (door,) = _openings(storeys[1], "pedestrian_entrance")
    win = _openings(storeys[1], "window")[0]
    assert door.props["y"] + door.props["h"] == pytest.approx(win.props["y"] + win.props["h"])


# --- 8. The cornice house's top ---------------------------------------------

@pytest.mark.parametrize("site,top", [(CanalSite(7.0, 1800, K.ORDINARY, 0), "dormer"), (CanalSite(11.0, 1760, K.GRAND, 3), "crest")])
def test_a_cornice_house_has_a_dormer_or_crest_with_a_beam_and_a_cornice_inside_the_party_walls(site, top):
    lot, _ = derive_amsterdam(site)
    gable = next(s for s in lot.children if s.label == "Gable")
    assert gable.attrs["top"] == top
    building, _ = generate_amsterdam(site)
    ids = {n.id: n for n in walk(building)}
    bx, _ = ids["b/gable"].props["hoist_beam"]
    assert abs(bx - site.width / 2) < 1e-6
    (cornice,) = [n for n in walk(building) if n.kind == "cornice"]
    assert cornice.props["cornice_ornament"] == "bracketed" and cornice.props["projection"] >= 0.8
    lip = min(cornice.props["projection"] * 0.35, 0.35)  # the drawn lip, see elements.draw_cornice
    assert cornice.props["x"] - lip >= -1e-6 and cornice.props["x"] + cornice.props["w"] + lip <= site.width + 1e-6


# --- 9. Door side; 12-13. dress and colour by date and builder --------------

def test_the_door_side_follows_the_builder():
    sides = set()
    for seed in range(4):
        building, _ = generate_amsterdam(CanalSite(6.6, 1720, K.ORDINARY, seed))
        (door,) = _openings(_storeys(building)[1], "pedestrian_entrance")
        sides.add(door.props["x"] < 3.3)
    assert sides == {True, False}


def test_early_fronts_are_red_and_banded_later_ones_dark_or_tarred():
    early, _ = generate_amsterdam(CanalSite(6.6, 1620, K.COMFORTABLE))
    assert _storeys(early)[1].props["wall_material"] == "brick"
    assert any(n.kind == "string_course" for n in walk(early))
    assert any(n.kind == "keystone" for n in walk(early))
    walls = Counter(derive_amsterdam(CanalSite(6.6, 1720, K.ORDINARY, s))[0].attrs["wall"] for s in SEEDS)
    assert walls.most_common(1)[0][0] == "brick_dark" and walls["basalt"] > 0
    late, _ = generate_amsterdam(CanalSite(6.6, 1720, K.ORDINARY, 0))
    assert not any(n.kind == "keystone" for n in walk(late))


def test_window_share_grows_with_the_date():
    shares = [derive_amsterdam(CanalSite(6.6, y, K.ORDINARY))[0].attrs["glass"] for y in (1620, 1700, 1780)]
    assert shares == sorted(shares) and shares[0] < shares[-1]


# --- Round 2 -------------------------------------------------------------------

def test_upper_windows_are_never_square_and_no_storey_drops_under_2_6_m():
    """Window h:w about 2.5 / 1.9 / 1.7 / 1.5 going up; no habitable storey of
    the front under 2.6 m."""
    for width in (4.5, 6.6, 8.0, 11.0):
        for year in (1620, 1690, 1760, 1810):
            for klass in K:
                for seed in range(0, 40, 7):
                    building, _ = generate_amsterdam(CanalSite(width, year, klass, seed))
                    front = [st for st in _storeys(building)[1:] if st.props["role"] != "gable"]
                    for i, st in enumerate(front):
                        assert st.props["h"] >= 2.6
                        for win in _openings(st, "window"):
                            assert win.props["h"] / win.props["w"] >= (2.2 if i == 0 else 1.45)


def test_the_stoop_never_runs_across_a_souterrain_window():
    for width in (4.5, 5.0, 6.6, 8.0, 11.0):
        for year in (1620, 1700, 1780):
            for klass in K:
                for seed in range(12):
                    building, _ = generate_amsterdam(CanalSite(width, year, klass, seed))
                    souterrain = _storeys(building)[0]
                    flights = [n for n in walk(building) if n.id.startswith("b/stoop/flight") and n.kind == "gable"]
                    assert flights
                    for win in _openings(souterrain, "window"):
                        for f in flights:
                            xs = [x for x, _ in f.props["points"]]
                            assert max(xs) <= win.props["x"] + 1e-6 or min(xs) >= win.props["x"] + win.props["w"] - 1e-6
