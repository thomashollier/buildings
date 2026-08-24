"""The block's invariants: one street, one wall.

    "In the previous attempt every building sampled its own street width
    independently — so buildings that were, by construction, on the same street
    disagreed about how wide it was, and their cornice lines did not line up.
    **Nothing errored.** The street simply looked subtly wrong, and the cause
    was a block-level fact being resolved per building."

This file is the answer to that paragraph. ``test_the_named_failure_errors_now``
is the single most important test in the stage, and it is written in two halves
on purpose:

* the first half proves the failure is **invisible** — two buildings told
  different street widths can come out geometrically identical, line for line,
  so no amount of looking at the output finds it;
* the second half proves it is now **loud** — ``check_alignment`` reads what
  each building believed out of its own trace and raises.

A test that only did the second half would not show why the first attempt got
away with it for so long.

The rest of the file is the G9 gate: buildings on one block share exactly one
street-width value; cornice lines across a block are equal to within 1e-9; and
the shared horizontals run across the party wall rather than stopping at it
(circulaire du 21 septembre 1855).
"""

from __future__ import annotations

import itertools
import math

import pytest

from buildings.block.block import (
    _lines_of,
    _street_widths_of,
    BlockDatums,
    BlockDatumViolation,
    GroundRegime,
    check_alignment,
    plan_block,
    resolve_datums,
    solve_block,
)
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.reglement_adapter import era_for_year, get_reglement

YEARS = (1830, 1865, 1888, 1910)
WIDTHS = (8.0, 12.0, 20.0, 26.0)
CLASSES = tuple(BuildingClass)
REGIMES = tuple(GroundRegime)


_CORPUS: list = []


def _blocks():
    """A small, deliberately mixed corpus of solved blocks.

    Built once and reused: every test below asks a different question of the
    same corpus, and generating a few hundred buildings per question would buy
    nothing but a slow suite.
    """
    if _CORPUS:
        return _CORPUS
    for i, (year, width, klass, regime) in enumerate(
        itertools.product(YEARS, WIDTHS, CLASSES, REGIMES)
    ):
        if i % 3:  # keep the sweep honest but affordable
            continue
        seed = 3 + i
        block = plan_block(
            72.0,
            width,
            year,
            klass=klass,
            regime=regime,
            seed=seed,
            corner_left=(i % 2 == 0),
            corner_right=(i % 5 == 0),
        )
        nodes = solve_block(block, year, klass=klass, regime=regime, seed=seed)
        _CORPUS.append((block, nodes))
    return _CORPUS


def _buildings(nodes):
    return [n.children[0] for n in nodes if n.kind == "parcel"]


# ===========================================================================
# The named failure
# ===========================================================================


def test_the_named_failure_errors_now():
    """Two buildings on one street, disagreeing about how wide it is.

    The pair is chosen so that the disagreement leaves **no geometric trace**:
    in 1865 a 12 m street and a 20 m street earn the same legal cornice
    ceiling, so two buildings of the same class told those two widths come out
    identical line for line. That is precisely the previous attempt's
    condition — nothing errors, nothing looks broken in isolation, and the run
    is out of register for a reason no one can see.

    Half one: the failure is invisible.
    Half two: it is not silent any more.
    """
    year = 1865
    reg = get_reglement(era_for_year(year))
    narrow, wide = 12.0, 20.0
    ceiling = reg.facade_height_limit(wide)
    assert reg.facade_height_limit(narrow) == pytest.approx(ceiling, abs=1e-12), (
        "this test needs two street widths that earn the same cornice ceiling, so "
        "that the disagreement is geometrically invisible; the height table changed"
    )

    honest = resolve_datums(wide, year, BuildingClass.COMFORTABLE)
    rogue = BlockDatums(
        street_width=narrow,  # the building rolled its own; the block said 20 m
        cornice_height=honest.cornice_height,
        string_course_levels=honest.string_course_levels,
        balcony_levels=honest.balcony_levels,
    )

    def build(datums, seed):
        site = SiteContext(
            street_width=datums.street_width,
            parcel_width=12.0,
            parcel_depth=18.0,
            year=year,
            klass=BuildingClass.COMFORTABLE,
            ground=GroundProgramme.SHOP,
            seed=seed,
        )
        node, _ = generate(site, datums)
        return node

    good = build(honest, 0)
    bad = build(rogue, 0)

    # -- half one: nothing to see -----------------------------------------
    assert _lines_of(good) == _lines_of(bad)
    assert good.props["eaves_height"] == pytest.approx(
        float(bad.props["eaves_height"]), abs=1e-12
    )
    assert good.props["legal_cornice_ceiling"] == pytest.approx(
        float(bad.props["legal_cornice_ceiling"]), abs=1e-12
    )

    # -- half two: it stops the build now ---------------------------------
    check_alignment([good], honest)  # the honest building alone is fine
    with pytest.raises(BlockDatumViolation, match="how wide the street is"):
        check_alignment([good, bad], honest)


def test_the_audit_catches_a_disagreement_of_any_size():
    """Not a threshold test — a *shared fact* test. Half a millimetre of
    disagreement about the street width is the same defect as four metres of
    it, because in both cases a block-level fact was resolved twice."""
    year = 1865
    honest = resolve_datums(20.0, year, BuildingClass.ORDINARY)
    for drift in (0.0005, 0.05, 4.0):
        rogue = BlockDatums(
            street_width=20.0 + drift,
            cornice_height=honest.cornice_height,
            string_course_levels=honest.string_course_levels,
            balcony_levels=honest.balcony_levels,
        )
        site = SiteContext(20.0 + drift, 12.0, 18.0, year, BuildingClass.ORDINARY,
                           GroundProgramme.SHOP)
        node, _ = generate(site, rogue)
        with pytest.raises(BlockDatumViolation, match="how wide the street is"):
            check_alignment([node], honest)


def test_the_audit_catches_a_cornice_that_does_not_continue():
    """The second half of the named failure: cornice lines that do not line up.

    Two buildings of different classes on one datum bundle stop their stone
    faces at different heights, because ``structure`` scales facade ambition by
    class. On one block that is a broken cornice line, and it is refused.
    """
    year = 1865
    datums = resolve_datums(20.0, year, BuildingClass.ORDINARY)
    nodes = []
    for klass in (BuildingClass.ORDINARY, BuildingClass.GRAND):
        site = SiteContext(20.0, 12.0, 18.0, year, klass, GroundProgramme.SHOP)
        node, _ = generate(site, datums)
        nodes.append(node)
    assert nodes[0].props["eaves_height"] != nodes[1].props["eaves_height"]
    with pytest.raises(BlockDatumViolation, match="does not continue across the party wall"):
        check_alignment(nodes, datums)


def test_the_audit_catches_a_line_that_stops_at_the_party_wall():
    """A mixed ground regime moves the bandeau and the balcon filant by the
    better part of a metre. It is caught at the seam, by name."""
    year = 1865
    datums = resolve_datums(20.0, year, BuildingClass.ORDINARY, GroundRegime.COMMERCIAL)
    nodes = []
    for ground in (GroundProgramme.SHOP, GroundProgramme.RESIDENTIAL):
        site = SiteContext(20.0, 12.0, 18.0, year, BuildingClass.ORDINARY, ground)
        node, _ = generate(site, datums)
        nodes.append(node)
    with pytest.raises(BlockDatumViolation, match="string course|balcon filant"):
        check_alignment(nodes, datums)


def test_a_mixed_regime_is_refused_before_anything_is_built():
    """``solve_block`` will not even start a run whose ground regimes would put
    it out of register — the failure is named in the message, with the remedy."""
    block = plan_block(60.0, 20.0, 1865, regime=GroundRegime.COMMERCIAL, seed=2)
    grounds = [GroundProgramme.SHOP] * len(block.parcels)
    grounds[1] = GroundProgramme.CARRIAGE
    with pytest.raises(BlockDatumViolation, match="belong to another regime"):
        solve_block(block, 1865, regime=GroundRegime.COMMERCIAL, seed=2, grounds=grounds)


# ===========================================================================
# G9 — the gate
# ===========================================================================


def test_one_street_width_for_the_whole_block():
    """G9, first clause, asserted directly against every trace on the run.

    Read from the IR rather than from the ``SiteContext`` handed in: the
    question is not what the block meant to say but what each building
    actually used.
    """
    for block, nodes in _blocks():
        widths = set()
        for building in _buildings(nodes):
            widths.update(_street_widths_of(building))
        assert widths, "no building recorded the street width it used"
        assert len(widths) == 1, f"the run disagrees about its street: {sorted(widths)}"
        assert widths.pop() == pytest.approx(block.street_width, abs=1e-9)


def test_cornice_lines_across_a_block_are_equal_to_1e_9():
    """G9, second clause. The cornice continues its neighbour's cornice."""
    for _block, nodes in _blocks():
        buildings = _buildings(nodes)
        eaves = [float(b.props["eaves_height"]) for b in buildings]
        assert max(eaves) - min(eaves) < 1e-9
        cornices = [
            tuple(sorted(float(n.props["y"]) for n in walk(b) if n.kind == "cornice"))
            for b in buildings
        ]
        for other in cornices[1:]:
            assert other == pytest.approx(cornices[0], abs=1e-9)


def test_the_shared_horizontals_run_across_the_party_wall():
    """G9, restated for the lines the 1855 circulaire actually names: balcony,
    cornice and entablature. Every building's own lines coincide with the
    block's datum, so the run reads as one wall rather than as eight."""
    for block, nodes in _blocks():
        for building in _buildings(nodes):
            string_courses, balconies = _lines_of(building)
            assert string_courses == pytest.approx(
                block.datums.string_course_levels, abs=1e-9
            )
            assert balconies == pytest.approx(block.datums.balcony_levels, abs=1e-9)


def test_the_blocks_datum_nodes_agree_with_the_buildings_under_them():
    """The datum node is not a decoration drawn near the buildings' lines; it
    is the line they are shares of."""
    for _block, nodes in _blocks():
        datum_levels = {
            n.kind: sorted(
                float(m.props["y"])
                for m in nodes
                if m.props.get("datum") and m.kind == n.kind
            )
            for n in nodes
            if n.props.get("datum")
        }
        for building in _buildings(nodes):
            string_courses, balconies = _lines_of(building)
            if "string_course" in datum_levels:
                assert sorted(string_courses) == pytest.approx(
                    datum_levels["string_course"], abs=1e-9
                )
            if "balcony" in datum_levels:
                assert sorted(balconies) == pytest.approx(
                    datum_levels["balcony"], abs=1e-9
                )
            assert datum_levels["cornice"][0] == pytest.approx(
                float(building.props["eaves_height"]), abs=1e-9
            )


def test_a_solved_block_tiles_its_frontage():
    """Adjacency and subdivision are the block's under every relation, so they
    are checked on every block in the corpus and not only in the unit file."""
    for block, nodes in _blocks():
        parcels = [n for n in nodes if n.kind == "parcel"]
        assert len(parcels) == len(block.parcels)
        x = float(parcels[0].props["x"])
        for node in parcels:
            assert float(node.props["x"]) == pytest.approx(x, abs=1e-9)
            x += float(node.props["w"])
        chamfer_width = math.fsum(c.width for c in block.chamfers)
        assert x + chamfer_width - float(parcels[0].props["x"]) == pytest.approx(
            block.frontage, abs=1e-9
        )
        walls = [n for n in nodes if n.kind == "party_wall"]
        assert len(walls) == len(block.parcels) - 1


# ===========================================================================
# I2 — the channel is one-way
# ===========================================================================


def test_a_building_has_no_way_to_sample_a_block_fact():
    """I2, restated at the level that hands the facts down.

    ``SiteContext`` is the whole of what a building is told, and it carries no
    RNG and no method that samples. The previous attempt's bug is not merely
    absent here; it is unwritable.
    """
    site = SiteContext(20.0, 12.0, 18.0, 1865, BuildingClass.ORDINARY, GroundProgramme.SHOP)
    for name in dir(site):
        if name.startswith("_"):
            continue
        assert not callable(getattr(site, name)), f"SiteContext.{name} is callable"
    for forbidden in ("rng", "random", "stream", "sample", "choose", "draw"):
        assert not hasattr(site, forbidden)


def test_the_datums_do_not_move_when_the_buildings_do():
    """The block resolves its registration from block facts alone, so a
    different seed on the run changes the buildings and moves no line."""
    year, width = 1865, 20.0
    reference = resolve_datums(width, year, BuildingClass.COMFORTABLE)
    seen = set()
    for seed in (0, 1, 2, 7, 19):
        block = plan_block(72.0, width, year, klass=BuildingClass.COMFORTABLE, seed=seed)
        nodes = solve_block(block, year, klass=BuildingClass.COMFORTABLE, seed=seed)
        assert block.datums == reference
        seen.add(tuple(round(p.width, 6) for p in block.parcels))
        for building in _buildings(nodes):
            assert _lines_of(building) == (
                reference.string_course_levels,
                reference.balcony_levels,
            )
    assert len(seen) > 1, "the seeds should actually have produced different runs"


def test_registration_depends_only_on_block_facts():
    """The measured fact the reference elevation rests on.

    ``resolve_datums`` draws one reference elevation for the run and registers
    every building to it. That is only legitimate if the reference lot is not a
    hidden parameter — so: hold ``(street_width, year, klass, regime)`` and
    vary parcel width, parcel depth, corner and seed, and nothing moves.

    If this test ever fails, the failing input is a block fact wearing a
    parcel's clothes and it must move into ``BlockDatums``, not be averaged
    away.
    """
    for year, width, klass, regime in itertools.product(
        (1865, 1890), (12.0, 20.0), (BuildingClass.MODEST, BuildingClass.GRAND), REGIMES
    ):
        datums = resolve_datums(width, year, klass, regime)
        expected = (datums.string_course_levels, datums.balcony_levels)
        reference_eaves = float(
            generate(
                SiteContext(width, 12.0, 18.0, year, klass, regime.programmes[0]), datums
            )[0].props["eaves_height"]
        )
        for parcel_w, parcel_d, corner, seed in itertools.product(
            (7.0, 12.0, 19.5), (9.0, 18.0, 30.0), (False, True), (0, 5)
        ):
            for ground in regime.programmes:
                site = SiteContext(
                    street_width=width,
                    parcel_width=parcel_w,
                    parcel_depth=parcel_d,
                    year=year,
                    klass=klass,
                    ground=ground,
                    corner=corner,
                    seed=seed,
                )
                building, _ = generate(site, datums)
                assert _lines_of(building) == expected, (
                    f"registration moved for parcel_width={parcel_w}, depth={parcel_d}, "
                    f"corner={corner}, seed={seed}, ground={ground.value}"
                )
                assert float(building.props["eaves_height"]) == pytest.approx(
                    reference_eaves, abs=1e-9
                )
