"""Lisbon Pombaline buildings, Soviet panel blocks and English Tudor houses."""

from __future__ import annotations

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.paris.generate import walk
from buildings.typologies.pombaline.grammar import PombalineSite, derive_pombaline, generate_pombaline
from buildings.typologies.soviet_panel.grammar import PanelSite, derive_soviet_panel, generate_soviet_panel, series_for
from buildings.typologies.tudor.grammar import TudorSite, derive_tudor, generate_tudor

CASES = [
    ("pombaline_nobre", generate_pombaline, derive_pombaline, PombalineSite(13.0, 1765, K.GRAND, "nobre", 0), {"Cornice"}),
    ("pombaline_secondary_tiled", generate_pombaline, derive_pombaline, PombalineSite(8.0, 1860, K.ORDINARY, "secondary", 4), {"Cornice"}),
    ("pombaline_alley", generate_pombaline, derive_pombaline, PombalineSite(6.0, 1800, K.MODEST, "alley", 3), {"Cornice"}),
    ("pombaline_raised", generate_pombaline, derive_pombaline, PombalineSite(11.5, 1885, K.COMFORTABLE, "nobre", 5), {"Cornice"}),
    ("panel_k7", generate_soviet_panel, derive_soviet_panel, PanelSite(2, 1960, K.MODEST, 0), {"Cornice"}),
    ("panel_1_464", generate_soviet_panel, derive_soviet_panel, PanelSite(3, 1966, K.ORDINARY, 1), {"Cornice"}),
    ("panel_p44", generate_soviet_panel, derive_soviet_panel, PanelSite(2, 1985, K.COMFORTABLE, 4), {"Cornice"}),
    ("tudor_cottage", generate_tudor, derive_tudor, TudorSite("cottage", 1540, K.MODEST, 0), {"Chimney"}),
    ("tudor_town", generate_tudor, derive_tudor, TudorSite("town", 1560, K.ORDINARY, 1), {"Chimney"}),
    ("tudor_double_gable", generate_tudor, derive_tudor, TudorSite("town", 1590, K.COMFORTABLE, 2, width=10.0), {"Chimney"}),
    ("tudor_manor", generate_tudor, derive_tudor, TudorSite("manor", 1570, K.GRAND, 3), {"Chimney"}),
    ("tudor_revival", generate_tudor, derive_tudor, TudorSite("town", 1895, K.COMFORTABLE, 5), {"Chimney"}),
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


# --- Pombaline -----------------------------------------------------------------


def _upper_windows(site):
    lot, _ = derive_pombaline(site)
    return [s for s in lot.walk() if s.label == "Light" and s.attr("role") != "ground"]


def test_the_regulation_gives_every_window_one_width_and_the_street_its_floors():
    for site in (PombalineSite(13.0, 1765, K.GRAND, "nobre", 0), PombalineSite(6.0, 1800, K.MODEST, "alley", 3)):
        widths = {round(s.scope.w, 6) for s in _upper_windows(site)}
        assert widths == {1.1}

    def floors(street):
        b, _ = generate_pombaline(PombalineSite(10.0, 1780, K.ORDINARY, street, 0))
        return len([n for n in b.children if n.kind == "storey"])

    assert floors("nobre") == floors("secondary") == 4 > floors("alley") == 3

    def balconies(street):
        b, _ = generate_pombaline(PombalineSite(10.0, 1780, K.ORDINARY, street, 0))
        return [n for n in walk(b) if n.kind == "balcony"]

    assert balconies("nobre") and not balconies("alley")


def test_later_owners_tile_and_raise_the_front():
    def finishes(site):
        b, _ = generate_pombaline(site)
        return [n.props["wall_material"] for n in b.children if n.kind == "storey"]

    early = finishes(PombalineSite(11.5, 1780, K.COMFORTABLE, "nobre", 5))
    late = finishes(PombalineSite(11.5, 1885, K.COMFORTABLE, "nobre", 5))
    assert "azulejo" not in early and "azulejo" in late
    assert len(late) == len(early) + 1


# --- Soviet panel --------------------------------------------------------------


def test_the_date_picks_the_series_and_the_series_its_height():
    assert [series_for(y) for y in (1960, 1966, 1975, 1985)] == ["K-7", "1-464", "II-49", "P-44"]
    lot5, _ = derive_soviet_panel(PanelSite(2, 1966, K.ORDINARY))
    lot17, _ = derive_soviet_panel(PanelSite(2, 1985, K.GRAND))
    assert lot5.attrs["floors_n"] == 5 and lot17.attrs["floors_n"] == 17
    rooms = lambda lot: [s for s in lot.walk() if s.label == "Storey" and s.attr("role") == "machine_room"]  # noqa: E731
    assert not rooms(lot5) and len(rooms(lot17)) == 2


def test_a_panel_per_bay_per_floor_and_the_stair_half_a_floor_off():
    site = PanelSite(2, 1966, K.ORDINARY, 1)
    lot, _ = derive_soviet_panel(site)
    stacks = [s for s in lot.walk() if s.label == "Stack"]
    floor_h = lot.attrs["spec"]["floor_h"]
    rooms = [st for st in stacks if st.attrs["bay_kind"] != "stair"]
    stairs = [st for st in stacks if st.attrs["bay_kind"] == "stair"]
    assert len(stairs) == site.sections
    # Every room stack is its storeys' panels, one a floor, all alike.
    for st in rooms:
        assert len(st.children) == 5 and {round(p.scope.h, 6) for p in st.children} == {floor_h}
    # The stair's panel joints fall half a floor between the rooms'.
    room_joints = {round(p.scope.y, 6) for p in rooms[0].children}
    for st in stairs:
        for p in st.children[1:]:
            assert round(p.scope.y, 6) not in room_joints
            assert any(abs(p.scope.y - j - floor_h / 2.0) < 1e-6 for j in room_joints)
    # One room window, one size.
    widths = {round(s.scope.w, 6) for s in lot.walk() if s.label == "LightBay" and s.attr("bay_kind") == "room"}
    assert len(widths) == 1


# --- Tudor ---------------------------------------------------------------------


def test_the_town_house_is_jettied_leaded_and_no_stud_crosses_a_light():
    lot, _ = derive_tudor(TudorSite("town", 1560, K.ORDINARY, 1))
    storeys = [f.children[0] for f in lot.children[0].children]
    widths = [s.scope.w for s in storeys]
    assert widths == sorted(widths) and widths[0] < widths[-1]
    for cell in (c for s in storeys for c in s.children if c.label == "Cell" and len(c.children) > 1 and c.children[1].label == "LightBay"):
        light = cell.children[1].scope
        for stud in (p for p in cell.children if p.label == "Post" and p.scope.h > 0.5):
            assert stud.scope.x + stud.scope.w <= light.x + 1e-6 or stud.scope.x >= light.x + light.w - 1e-6
    b, _ = generate_tudor(TudorSite("town", 1560, K.ORDINARY, 1))
    windows = [n for n in walk(b) if n.kind == "opening" and n.props["opening_type"] == "window"]
    leads = {n.id.rsplit("/leading/", 1)[0] for n in walk(b) if n.kind == "gable" and n.props["form"] == "came"}
    assert windows and len(leads) == len(windows)


def test_gables_and_roofs_follow_the_kind_the_width_and_the_money():
    def gables(site):
        b, _ = generate_tudor(site)
        return [n for n in b.children if n.kind == "gable" and n.props["form"] == "front_gable"]

    assert len(gables(TudorSite("town", 1560, K.ORDINARY))) == 1
    assert len(gables(TudorSite("town", 1590, K.ORDINARY, width=10.0))) == 2
    assert len(gables(TudorSite("manor", 1570, K.GRAND))) == 3
    assert len(gables(TudorSite("manor", 1570, K.ORDINARY))) == 1

    def roof(site):
        b, _ = generate_tudor(site)
        return next(n for n in b.children if n.kind == "roof").props["material"]

    assert roof(TudorSite("cottage", 1540, K.MODEST)) == "thatch"
    assert roof(TudorSite("cottage", 1890, K.MODEST)) == "slate"
