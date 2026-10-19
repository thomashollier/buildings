"""Renaissance palazzi, Gothic cathedral fronts, Romanesque and Baroque church
fronts, and the classical temple front with its Greek Revival use."""

from __future__ import annotations

import math

import pytest

from buildings.ir.serial import to_json
from buildings.render.svg.render import render
from buildings.site import BuildingClass as K
from buildings.typologies.baroque.grammar import BaroqueSite, derive_baroque, generate_baroque
from buildings.typologies.classical.grammar import ClassicalSite, derive_classical, generate_classical, portico_of
from buildings.typologies.gothic_cathedral.grammar import CathedralSite, derive_gothic_cathedral, generate_gothic_cathedral
from buildings.typologies.paris.generate import walk
from buildings.typologies.renaissance.grammar import RenaissanceSite, derive_renaissance, generate_renaissance, palazzo_type
from buildings.typologies.romanesque.grammar import RomanesqueSite, derive_romanesque, front_type, generate_romanesque

R, G, Ro, B, C = (
    (generate_renaissance, derive_renaissance),
    (generate_gothic_cathedral, derive_gothic_cathedral),
    (generate_romanesque, derive_romanesque),
    (generate_baroque, derive_baroque),
    (generate_classical, derive_classical),
)

CASES = [
    ("rucellai", *R, RenaissanceSite(24.0, 1446, K.ORDINARY, seed=0)),
    ("medici", *R, RenaissanceSite(32.0, 1445, K.GRAND, seed=1)),
    ("strozzi", *R, RenaissanceSite(30.0, 1489, K.GRAND, seed=3)),
    ("farnese", *R, RenaissanceSite(44.0, 1540, K.GRAND, seed=5)),
    ("notre_dame", *G, CathedralSite(41.0, 1163, K.GRAND, seed=0)),
    ("amiens", *G, CathedralSite(46.0, 1220, K.GRAND, seed=0)),
    ("one_spire", *G, CathedralSite(40.0, 1277, K.COMFORTABLE, seed=2)),
    ("pisan", *Ro, RomanesqueSite(35.0, 1118, K.GRAND, seed=0)),
    ("pisan_parish", *Ro, RomanesqueSite(14.0, 1160, K.ORDINARY, seed=4)),
    ("battlements", *Ro, RomanesqueSite(30.0, 1110, K.COMFORTABLE, seed=1)),
    ("helm", *Ro, RomanesqueSite(28.0, 1130, K.GRAND, seed=3)),
    ("gesu", *B, BaroqueSite(35.0, 1575, K.GRAND, seed=0)),
    ("susanna", *B, BaroqueSite(22.0, 1603, K.COMFORTABLE, seed=0)),
    ("agnese", *B, BaroqueSite(40.0, 1655, K.GRAND, seed=0)),
    ("parthenon", *C, ClassicalSite(31.0, -447, K.GRAND, seed=0)),
    ("ionic", *C, ClassicalSite(8.0, -420, K.MODEST, seed=2)),
    ("maison_carree", *C, ClassicalSite(15.0, -16, K.COMFORTABLE, seed=4)),
    ("custom_house", *C, ClassicalSite(17.0, 1836, K.MODEST, seed=0)),
    ("portico_on_block", *C, ClassicalSite(40.0, 1852, K.COMFORTABLE, seed=5)),
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
        if shape.parent is not None and shape.label not in ("Cornice",):
            assert shape.parent.scope.contains(shape.scope), shape


# --- signatures ----------------------------------------------------------------


def test_the_family_dresses_the_palazzo_and_medici_rustication_smooths_as_it_climbs():
    assert [palazzo_type(RenaissanceSite(24.0, 1450, K.ORDINARY, seed=s)) for s in (0, 1, 3)] == ["rucellai", "medici", "strozzi"]
    assert palazzo_type(RenaissanceSite(24.0, 1520, K.ORDINARY, seed=1)) == "farnese"

    def treatments(seed):
        b, _ = generate_renaissance(RenaissanceSite(32.0, 1445, K.GRAND, seed=seed))
        storeys = [n for n in b.children if n.kind == "storey"]
        return [next((c.props["treatment"] for c in s.children if c.kind == "socle"), None) for s in storeys]

    assert treatments(1) == ["raised_bossage", "flat_incised_refends", None]
    assert treatments(3) == ["raised_bossage", "raised_bossage", "flat_incised_refends"]
    # Rucellai: one order of pilasters a floor, Tuscan, Ionic (drawn doric), Corinthian.
    b, _ = generate_renaissance(RenaissanceSite(24.0, 1446, K.ORDINARY, seed=0))
    orders = [{c.props["order"] for c in s.children if c.kind == "column" and c.id.split("/")[-1].startswith("pilaster")}
              for s in b.children if s.kind == "storey"]
    assert orders == [{"pilaster"}, {"doric"}, {"corinthian"}]


def test_a_florentine_piano_nobile_opens_in_bifore_under_one_arch():
    lot, _ = derive_renaissance(RenaissanceSite(32.0, 1445, K.GRAND, seed=1))
    nobile = next(s for s in lot.walk() if s.label == "Storey" and s.attrs["floor"] == "nobile")
    for bay in (c for c in nobile.children if c.label == "Cell" and c.attrs["slot"].name == "bay"):
        lights = [s for s in bay.walk() if s.label == "Light"]
        arch = next(s for s in bay.walk() if s.label == "Archivolt")
        assert len(lights) == 2
        assert all(l.attr("head") == "round" for l in lights)
        assert arch.scope.x <= lights[0].scope.x and arch.scope.x + arch.scope.w >= lights[1].scope.x + lights[1].scope.w - 1e-9


def test_the_cathedral_has_three_portals_the_central_widest_and_a_rose_over_it():
    lot, _ = derive_gothic_cathedral(CathedralSite(41.0, 1163, K.GRAND, seed=0))
    portals = [s for s in lot.walk() if s.label == "Portal"]
    assert len(portals) == 3
    centre = next(p for p in portals if p.attrs["central"])
    assert all(centre.scope.w > p.scope.w for p in portals if p is not centre)
    rose = next(s for s in lot.walk() if s.label == "Cell" and s.attr("opening_type") == "oeil_de_boeuf")
    cx = lambda s: s.scope.x + s.scope.w / 2.0
    assert abs(cx(rose) - cx(centre)) < 1e-6 and rose.scope.y > centre.scope.y + centre.scope.h
    # A later, richer front has deeper portals.
    early = centre.attrs["rings"]
    late = next(p for p in derive_gothic_cathedral(CathedralSite(41.0, 1230, K.GRAND, seed=0))[0].walk() if p.label == "Portal" and p.attrs["central"])
    assert late.attrs["rings"] > early and late.attrs["gablet"]


def test_romanesque_pisan_galleries_stack_and_the_fortress_front_has_towers():
    assert front_type(RomanesqueSite(35.0, 1118, K.GRAND, seed=0)) == "pisan"
    assert front_type(RomanesqueSite(35.0, 1118, K.GRAND, seed=1)) == "fortress"
    lot, _ = derive_romanesque(RomanesqueSite(35.0, 1118, K.GRAND, seed=0))
    galleries = sorted((s for s in lot.walk() if s.label == "Gallery"), key=lambda s: s.scope.y)
    assert len(galleries) == 4
    assert all(a.scope.y + a.scope.h == pytest.approx(b.scope.y) for a, b in zip(galleries, galleries[1:]))
    assert galleries[0].scope.w > galleries[1].scope.w  # the aisles slope in beside the nave
    lot, _ = derive_romanesque(RomanesqueSite(30.0, 1110, K.COMFORTABLE, seed=1))
    stages = [s for s in lot.walk() if s.label == "Storey" and s.attrs.get("register") == "stage"]
    lights = [max(1, len([l for l in s.walk() if l.label == "Light"])) for s in stages if s.parent.id.endswith("tower_l")]
    assert lights == sorted(lights) and lights[-1] == 3


def test_the_baroque_upper_order_is_narrower_and_its_planes_step_forward():
    lot, _ = derive_baroque(BaroqueSite(22.0, 1603, K.COMFORTABLE, seed=0))
    lower, upper = (o for o in lot.walk() if o.label == "Order")
    width = lambda o: sum(p.scope.w for p in o.children if p.label == "Storey")
    assert width(upper) < width(lower) * 0.75
    depths = [p.attrs["depth"] for p in lower.children if p.label == "Storey"]
    assert depths == [0, 1, 2, 3, 2, 1, 0]
    assert [v.attrs["side"] for v in lot.walk() if v.label == "Volute"] == ["left", "right"]
    gesu, _ = derive_baroque(BaroqueSite(22.0, 1575, K.COMFORTABLE, seed=0))
    assert max(p.attrs["depth"] for p in gesu.walk() if p.label == "Storey") == 1
    agnese, _ = derive_baroque(BaroqueSite(40.0, 1655, K.GRAND, seed=0))
    labels = {s.label for s in agnese.walk()}
    assert {"Tower", "Dome"} <= labels and "Volute" not in labels


def test_the_order_sets_every_proportion_of_the_portico():
    for seed, order, ratio in ((0, "doric", 5.5), (2, "ionic", 9.0), (4, "corinthian", 10.0)):
        site = ClassicalSite(20.0, 100, K.COMFORTABLE, seed=seed)
        p = portico_of(site)
        assert p["order"] == order and p["columns"] == 6
        lot, _ = derive_classical(site)
        cols = sorted((s for s in lot.walk() if s.label == "Column"), key=lambda s: s.scope.x)
        d = p["module"]
        assert all(c.scope.w == pytest.approx(d) and c.scope.h == pytest.approx(ratio * d) for c in cols)
        ent = next(s for s in lot.walk() if s.label == "Storey" and s.attrs.get("role") == "entablature")
        assert ent.scope.h == pytest.approx(cols[0].scope.h * (0.32 if order == "doric" else 0.25))
        ped = next(s for s in lot.walk() if s.label == "Pediment")
        slope = math.degrees(math.atan(ped.scope.h / (ped.scope.w / 2.0)))
        assert 12.0 <= slope <= 15.0
    assert portico_of(ClassicalSite(31.0, -447, K.GRAND))["columns"] == 8
    assert portico_of(ClassicalSite(8.0, -420, K.MODEST, seed=2))["columns"] == 4
    assert portico_of(ClassicalSite(40.0, 1852, K.COMFORTABLE, seed=5))["use"] == "revival"
