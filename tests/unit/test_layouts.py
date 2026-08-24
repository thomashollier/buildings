"""The named layouts render, and the ones that claim a form actually show it.

``dev/harness/layouts.py`` is where a situation gets a name, a reason and —
where one exists — the Daly plate it answers to. It is a harness rather than
library code, but a preset that no longer produces the building its ``expect``
line describes is worse than no preset: it is a caption on the wrong picture.
A14.3 adds two whose whole purpose is one form, so the claim is checked.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _layouts_module():
    spec = importlib.util.spec_from_file_location(
        "dev_harness_layouts", ROOT / "dev" / "harness" / "layouts.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("dev_harness_layouts", module)
    spec.loader.exec_module(module)
    return module


LAYOUTS = _layouts_module()


def _openings(building):
    for storey in building.children:
        if storey.kind != "storey":
            continue
        for bay in storey.children:
            if bay.kind != "bay":
                continue
            for child in bay.children:
                if child.kind == "opening":
                    yield child


def _arch_registers(building) -> dict[str, object]:
    return {
        o.props["arch_register"]: o
        for o in _openings(building)
        if o.props.get("arch_register")
    }


@pytest.mark.parametrize("key", sorted(LAYOUTS.LAYOUTS))
def test_every_layout_generates_and_renders(key: str) -> None:
    """``python3 dev/harness/layouts.py --svg`` must not be the only place
    anybody finds out a preset stopped working."""
    from buildings.render.svg import render
    from buildings.typologies.paris.generate import generate

    layout = LAYOUTS.LAYOUTS[key]
    building, _log = generate(layout.site)
    svg = render(building, width_px=620)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert layout.why.strip(), f"{key} states no reason for being shaped as it is"


@pytest.mark.parametrize("key", sorted(LAYOUTS.LAYOUTS))
def test_every_layout_is_named_and_keyed_consistently(key: str) -> None:
    layout = LAYOUTS.LAYOUTS[key]
    assert layout.key == key
    assert layout.title.strip()
    assert layout.expect.strip()


def test_the_two_storey_arch_layouts_actually_carry_a_two_storey_arch() -> None:
    """A14.3. ``AC`` and ``AP`` exist to show the form; a seed that stopped
    drawing it would leave two presets captioned for a building they no longer
    produce."""
    from buildings.typologies.paris import catalogue
    from buildings.typologies.paris.generate import generate

    expected = {
        "AC": "carriage_entrance",
        "AP": "pedestrian_entrance",
    }
    for key, door in expected.items():
        building, _log = generate(LAYOUTS.LAYOUTS[key].site)
        registers = _arch_registers(building)
        assert set(registers) == {
            catalogue.ENTRANCE_ARCH_LEAVES,
            catalogue.ENTRANCE_ARCH_HEAD,
        }, f"{key} does not draw a two-storey arch"
        lower = registers[catalogue.ENTRANCE_ARCH_LEAVES]
        upper = registers[catalogue.ENTRANCE_ARCH_HEAD]
        assert lower.props["opening_type"] == door, key
        assert upper.props["head"] == "round", key
        # A14.1's assertion, at the one place a reader will actually look.
        wanted = (
            2.60 if door == "carriage_entrance" else 1.75
        )
        assert float(lower.props["w"]) == pytest.approx(wanted, abs=1e-6), (
            f"{key}: the tall arch is not the sourced width"
        )
        assert float(upper.props["w"]) == pytest.approx(wanted, abs=1e-6), key


def test_layout_A_still_shows_the_one_storey_door_the_variants_are_a_variant_of() -> None:
    """A14.3 says to keep ``A`` as it is. It is the reference the pair reads
    against: same street, same parcel, same date, same class, same programme,
    and only the entrance's height differs — so if ``A`` ever drew the tall
    arch too, ``AC`` would stop being a variant of anything."""
    from buildings.typologies.paris.generate import generate

    a = LAYOUTS.LAYOUTS["A"]
    ac = LAYOUTS.LAYOUTS["AC"]
    for field in ("street_width", "parcel_width", "parcel_depth", "year", "klass", "ground"):
        assert getattr(a.site, field) == getattr(ac.site, field), field
    assert a.site.seed != ac.site.seed, (
        "the pair differs only in the seed, and therefore only in the draw"
    )
    building, _log = generate(a.site)
    assert not _arch_registers(building), "layout A now draws a two-storey arch"
    doors = [
        o for o in _openings(building)
        if o.props["opening_type"] in ("carriage_entrance", "pedestrian_entrance")
    ]
    assert len(doors) == 1
    assert float(doors[0].props["w"]) == pytest.approx(2.60, abs=1e-6)


def test_the_pedestrian_arch_layout_is_on_a_narrower_parcel() -> None:
    """A14.3 asks for the pedestrian variant on a narrower parcel, and the
    narrowness is not decoration: an 11 m street is under the 12 m a carriage
    needs to draw out of the traffic, which is *why* this frontage takes a
    porte piétonne at all."""
    ac = LAYOUTS.LAYOUTS["AC"].site
    ap = LAYOUTS.LAYOUTS["AP"].site
    assert ap.parcel_width < ac.parcel_width
    assert ap.street_width < 12.0 <= ac.street_width


def test_every_layout_that_claims_a_daly_plate_names_a_file_that_exists() -> None:
    """A citation pointing at nothing is worse than no citation."""
    for key, layout in LAYOUTS.LAYOUTS.items():
        for token in layout.daly.replace("\n", " ").split():
            token = token.strip(".,;()")
            if token.endswith(".jpg"):
                assert (ROOT / token).exists(), f"{key} cites a missing plate: {token}"


# ---------------------------------------------------------------------------
# The 1884 hinge — H83 / H87
# ---------------------------------------------------------------------------
#
# The brief's own discontinuity test: "move the date past the 1884 decree and
# the roofline changes shape." A preset pair is a picture of that; what follows
# is the claim, so that a regression reads as a failure rather than as a
# slightly different picture nobody looked at.


def _roof(building):
    for node in building.children:
        if node.kind == "roof":
            return node
    raise AssertionError("this building has no roof node")


def _storeys(building):
    return [n for n in building.children if n.kind == "storey"]


def test_the_1884_pair_differs_in_the_year_and_in_nothing_else() -> None:
    """The control half of the experiment. If the two situations differed in
    any other input — a metre of street, a seed, a class — then whatever moves
    between them could be that instead of the decree, and the pair would prove
    nothing."""
    a = LAYOUTS.LAYOUTS["H83"].site
    b = LAYOUTS.LAYOUTS["H87"].site
    for field in (
        "street_width", "parcel_width", "parcel_depth",
        "klass", "ground", "corner", "seed",
    ):
        assert getattr(a, field) == getattr(b, field), field
    assert a.year < 1884 < b.year, "the pair must straddle the decree"


def test_past_the_1884_decree_the_comble_stops_being_a_plane() -> None:
    """A8/A15: before the décret du 23 juillet 1884 the comble is inscribed in
    a 45° PLANE; after it, in a circular ARC. The section is the place that
    shows it — a plane needs a handful of points and an arc needs many — so
    this asserts the shape of the profile, not a height that could move for
    any number of unrelated reasons."""
    from buildings.typologies.paris.generate import generate

    before, _ = generate(LAYOUTS.LAYOUTS["H83"].site)
    after, _ = generate(LAYOUTS.LAYOUTS["H87"].site)

    plane = _roof(before).props["profile"]
    arc = _roof(after).props["profile"]
    assert len(plane) <= 6, f"a 45° plane should not need {len(plane)} points"
    assert len(arc) > 12, f"an arc sampled at {len(arc)} points is not a curve"

    # And the arc genuinely bows INSIDE the chord it would be if it were a
    # plane: sampled at mid-height, the curve stands further back from the
    # eaves than a straight line between its own ends would.
    run_end, rise_end = arc[-2]
    mid = rise_end / 2.0
    on_curve = next(x for x, h in arc if h >= mid)
    on_chord = run_end * (mid / rise_end)
    assert on_curve < on_chord - 0.05, (
        f"at half height the profile is at {on_curve:.3f} m against a chord's "
        f"{on_chord:.3f} m — that is a straight line, not an arc"
    )


def test_the_decree_raises_the_stone_a_little_and_the_roof_a_lot() -> None:
    """Both halves of what 1884 changed, and their ORDERING, which is the part
    that is contractual. The cornice a 20 m street earns moves 17.55 -> 18.00 m,
    a courtesy; the comble allowance moves 3.20 -> 7.65 m, which is what buys
    the extra garret storey. Asserting the ordering rather than the figures
    keeps this honest if either table is later recalibrated."""
    from buildings.typologies.paris.generate import generate
    from buildings.typologies.paris.structure import solve_structure

    before = solve_structure(LAYOUTS.LAYOUTS["H83"].site)
    after = solve_structure(LAYOUTS.LAYOUTS["H87"].site)

    stone_gain = float(after.cornice_height) - float(before.cornice_height)
    roof_gain = after.envelope.ridge_height - before.envelope.ridge_height
    assert stone_gain > 0.0, "the 1884 cornice table did not rise"
    assert roof_gain > stone_gain, (
        f"the roof gained {roof_gain:.2f} m against the stone's {stone_gain:.2f} m — "
        "1884 is a ROOF decree, and if the stone ever outruns it this pair is "
        "demonstrating something else"
    )

    # ...and the storey the roof bought is a garret, not a letting floor.
    old, _ = generate(LAYOUTS.LAYOUTS["H83"].site)
    new, _ = generate(LAYOUTS.LAYOUTS["H87"].site)
    attics_before = [s for s in _storeys(old) if s.props.get("role") == "attic"]
    attics_after = [s for s in _storeys(new) if s.props.get("role") == "attic"]
    assert len(attics_after) == len(attics_before) + 1, (
        f"{len(attics_before)} -> {len(attics_after)} garret storeys"
    )
    habitable_before = [s for s in _storeys(old) if s.props.get("role") != "attic"]
    habitable_after = [s for s in _storeys(new) if s.props.get("role") != "attic"]
    assert len(habitable_after) == len(habitable_before), (
        "the decree moved the roof, so it must not have added a letting storey"
    )
