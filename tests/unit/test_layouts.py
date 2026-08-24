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
