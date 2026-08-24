"""Unit tests for the block level.

Split of responsibility with ``tests/invariant/test_block_datums.py``: this
file tests the *pieces* — that frontage subdivision fills the run exactly and
records who abuts whom, that a chamfer is a facade of its own, that a ``Block``
refuses to hold two versions of one fact. The invariant file tests the thing
the level exists for: that a run of buildings shares its datums, and that a run
which does not fails loudly.
"""

from __future__ import annotations

import math
import statistics

import pytest

from buildings.block.block import (
    _CHAMFER_BAY,
    _MAX_PARCEL_WIDTH,
    _MIN_PARCEL_WIDTH,
    Block,
    BlockDatums,
    BlockDatumViolation,
    Chamfer,
    GroundRegime,
    Parcel,
    block_nodes,
    chamfer_for,
    plan_block,
    resolve_datums,
    solve_block,
    subdivide,
)
from buildings.ir.serial import to_json
from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme
from buildings.solver.fitting import SlotKind
from buildings.typologies.paris.reglement_adapter import (
    balcony_rule,
    era_for_year,
    get_reglement,
)

FRONTAGES = (18.0, 34.5, 52.0, 71.3, 96.0, 140.0)
SEEDS = (0, 1, 2, 3, 5, 8, 13)


# ===========================================================================
# subdivide — frontage and adjacency, the block's under every relation
# ===========================================================================


@pytest.mark.parametrize("frontage", FRONTAGES)
@pytest.mark.parametrize("seed", SEEDS)
def test_subdivide_fills_the_frontage_exactly(frontage, seed):
    """No gaps and no overlap: the lots tile the run.

    A block with a 30 cm gap in it is not a block, and 30 cm is exactly the
    size of error that renders as "something is slightly off" rather than as a
    crash.
    """
    parcels = subdivide(frontage, DecisionStream(seed))
    assert math.fsum(p.width for p in parcels) == pytest.approx(frontage, abs=1e-9)


@pytest.mark.parametrize("frontage", FRONTAGES)
@pytest.mark.parametrize("seed", SEEDS)
def test_subdivide_keeps_every_lot_in_the_band(frontage, seed):
    parcels = subdivide(frontage, DecisionStream(seed))
    for p in parcels:
        assert _MIN_PARCEL_WIDTH - 1e-9 <= p.width <= _MAX_PARCEL_WIDTH + 1e-9
        assert p.depth > 0.0


def test_subdivide_records_who_abuts_whom():
    parcels = subdivide(96.0, DecisionStream(4))
    assert len(parcels) > 3
    assert parcels[0].left_neighbour is None
    assert parcels[-1].right_neighbour is None
    for i, p in enumerate(parcels):
        assert p.left_neighbour == (i - 1 if i else None)
        assert p.right_neighbour == (i + 1 if i + 1 < len(parcels) else None)


def test_a_single_lot_run_abuts_nothing():
    parcels = subdivide(9.0, DecisionStream(1))
    assert len(parcels) == 1
    assert parcels[0].detached


def test_subdivide_is_deterministic():
    a = subdivide(88.0, DecisionStream(11))
    b = subdivide(88.0, DecisionStream(11))
    assert a == b


def test_subdivide_varies_along_the_run():
    """Parcels were not uniform. A run of identical lots is the failure mode
    this draw exists to avoid — it reads as a shelf of models even when every
    building on it is right."""
    parcels = subdivide(140.0, DecisionStream(3))
    widths = [p.width for p in parcels]
    assert len(set(round(w, 6) for w in widths)) > 1
    # Enough spread to be visible, not so much that the band is meaningless.
    assert statistics.pstdev(widths) > 0.25


def test_adding_a_draw_does_not_perturb_the_widths():
    """I5 at block scale: parcel depth is drawn on its own path, so changing
    it cannot move a single lot line."""
    a = subdivide(96.0, DecisionStream(6), depth_variation=0.0)
    b = subdivide(96.0, DecisionStream(6), depth_variation=0.30)
    assert [p.width for p in a] == [p.width for p in b]
    assert [p.depth for p in a] != [p.depth for p in b]


def test_pinning_one_parcel_path_leaves_its_neighbours_alone():
    """The addressable-stream guarantee, stated where the block relies on it:
    two runs that share a seed share every draw they share a path for."""
    a = subdivide(96.0, DecisionStream(2), path="rue-de-rivoli")
    b = subdivide(96.0, DecisionStream(2), path="rue-de-rivoli")
    assert a == b
    c = subdivide(96.0, DecisionStream(2), path="rue-saint-antoine")
    assert [p.width for p in a] != [p.width for p in c]


def test_corner_lots_are_wider():
    """The corner building is the one with something to show on two streets."""
    corner_widths, interior_widths = [], []
    for seed in range(24):
        parcels = subdivide(96.0, DecisionStream(seed), corner_left=True, corner_right=True)
        corner_widths += [parcels[0].width, parcels[-1].width]
        interior_widths += [p.width for p in parcels[1:-1]]
    assert statistics.mean(corner_widths) > statistics.mean(interior_widths)


def test_subdivide_refuses_a_frontage_that_is_not_one():
    with pytest.raises(ValueError):
        subdivide(0.0, DecisionStream(0))
    with pytest.raises(ValueError):
        subdivide(-12.0, DecisionStream(0))


# ===========================================================================
# The chamfer — a third short facade, not a module of the row
# ===========================================================================


def test_chamfer_has_a_rhythm_of_its_own():
    """The pan coupé is solved against its own band, and every bay it produces
    is narrower than the narrowest bay ``structure`` will put on a facade
    (2.70 m before class scaling). That is what "its own rhythm" means
    numerically: the two grammars do not overlap."""
    for seed in range(16):
        c = chamfer_for(0, "left", DecisionStream(seed))
        bays = [s for s in c.bays if s.kind is SlotKind.REPEATING]
        assert 1 <= len(bays) <= 2
        for slot in bays:
            assert _CHAMFER_BAY[0] - 1e-9 <= slot.width <= _CHAMFER_BAY[2] + 1e-9
            assert slot.width < 2.70
        assert math.fsum(s.width for s in c.bays) == pytest.approx(c.width, abs=1e-9)


def test_chamfer_says_why_it_is_the_width_it_is():
    c = chamfer_for(0, "right", DecisionStream(1))
    joined = " ".join(c.account)
    assert "pan coupé" in joined
    assert "INFERRED" in joined
    assert "own rhythm" in joined


def test_chamfer_is_cut_out_of_the_corner_lot_not_added_to_the_run():
    """A chamfer consumes real frontage. The corner building gives up part of
    its face on this street to gain a face on the other one."""
    plain = plan_block(96.0, 20.0, 1865, seed=9)
    cut = plan_block(96.0, 20.0, 1865, seed=9, corner_left=True, corner_right=True)
    assert plain.frontage == pytest.approx(96.0, abs=1e-9)
    assert cut.frontage == pytest.approx(96.0, abs=1e-9)
    assert cut.chamfers
    assert math.fsum(p.width for p in cut.parcels) < math.fsum(p.width for p in plain.parcels)


def test_a_chamfer_may_only_cut_a_corner_lot():
    datums = resolve_datums(20.0, 1865, BuildingClass.ORDINARY)
    parcels = (Parcel(12.0, 18.0, False, None, 1), Parcel(12.0, 18.0, False, 0, None))
    chamfer = chamfer_for(0, "left", DecisionStream(0))
    with pytest.raises(ValueError, match="not marked as a corner"):
        Block(20.0, parcels, datums, (chamfer,))


def test_a_run_has_at_most_one_chamfer_at_each_end():
    datums = resolve_datums(20.0, 1865, BuildingClass.ORDINARY)
    parcels = (Parcel(12.0, 18.0, True, None, 1), Parcel(12.0, 18.0, True, 0, None))
    left = chamfer_for(0, "left", DecisionStream(0))
    other = Chamfer(1, "left", 3.5, left.bays)
    with pytest.raises(ValueError, match="at most one chamfer"):
        Block(20.0, parcels, datums, (left, other))


# ===========================================================================
# Block — one fact, stored once, or asserted where it is stored twice
# ===========================================================================


def test_block_refuses_two_street_widths():
    """``Block`` carries the street width and so do its datums. CONTRACTS.md
    puts it in both places, so the two are checked against each other rather
    than trusted — the A2.6 discipline of stating an invariant where two things
    meet."""
    datums = resolve_datums(20.0, 1865, BuildingClass.ORDINARY)
    parcels = subdivide(40.0, DecisionStream(0))
    with pytest.raises(BlockDatumViolation, match="One street, one width"):
        Block(18.0, parcels, datums)


def test_block_refuses_adjacency_that_contradicts_the_run():
    datums = resolve_datums(20.0, 1865, BuildingClass.ORDINARY)
    parcels = (Parcel(12.0, 18.0, False, None, 1), Parcel(12.0, 18.0, False, 0, 7))
    with pytest.raises(ValueError, match="Adjacency is the block"):
        Block(20.0, parcels, datums)


def test_block_needs_at_least_one_parcel():
    datums = resolve_datums(20.0, 1865, BuildingClass.ORDINARY)
    with pytest.raises(ValueError):
        Block(20.0, (), datums)


def test_origins_tile_the_frontage():
    block = plan_block(96.0, 20.0, 1865, seed=5, corner_left=True)
    origins = block.origins
    left = block.chamfer_at("left")
    assert origins[0] == pytest.approx(left.width, abs=1e-12)
    for i in range(len(block.parcels) - 1):
        assert origins[i + 1] == pytest.approx(
            origins[i] + block.parcels[i].width, abs=1e-12
        )
    end = origins[-1] + block.parcels[-1].width
    assert end == pytest.approx(block.frontage, abs=1e-9)


def test_a_party_wall_is_named_once_per_junction():
    block = plan_block(96.0, 20.0, 1865, seed=5)
    junctions = block.junctions()
    assert len(junctions) == len(block.parcels) - 1
    for left, right, x in junctions:
        assert right == left + 1
        assert 0.0 < x < block.frontage


# ===========================================================================
# BlockDatums — what goes down the channel
# ===========================================================================


def test_datums_take_the_cornice_ceiling_from_the_reglement():
    for year in (1830, 1865, 1890, 1910):
        for width in (8.0, 12.0, 20.0, 30.0):
            datums = resolve_datums(width, year, BuildingClass.ORDINARY)
            expected = get_reglement(era_for_year(year)).facade_height_limit(width)
            assert datums.cornice_height == pytest.approx(expected, abs=1e-12)


def test_balcony_datums_obey_the_1823_ordinance():
    """A datum may not be less legal than the buildings hung on it. The 6 m
    threshold is read from ``reglement``, not written down here."""
    for year in (1830, 1865, 1890, 1910):
        threshold = float(balcony_rule([0.0], era_for_year(year)).min_height)
        for klass in BuildingClass:
            for regime in GroundRegime:
                datums = resolve_datums(20.0, year, klass, regime)
                for level in datums.balcony_levels:
                    assert level >= threshold - 1e-9


def test_datums_are_ordered_bottom_up():
    with pytest.raises(ValueError, match="strictly increasing"):
        BlockDatums(20.0, 17.55, (6.0, 4.0), ())
    with pytest.raises(ValueError, match="strictly increasing"):
        BlockDatums(20.0, 17.55, (), (9.0, 9.0))


def test_datums_reject_a_street_with_no_width():
    with pytest.raises(ValueError):
        BlockDatums(0.0, 17.55, (), ())


def test_levels_gathers_every_shared_line():
    datums = resolve_datums(20.0, 1865, BuildingClass.COMFORTABLE)
    levels = datums.levels
    assert list(levels) == sorted(levels)
    for line in (*datums.string_course_levels, *datums.balcony_levels):
        assert line in levels
    assert datums.cornice_height in levels


def test_a_commercial_run_carries_the_entresol_line():
    """Two bandeaux over a shop — the plat-bande closing the entresol and the
    bandeau under the noble floor — and one on a residential run, which has no
    entresol to close. The datum bundle is a consequence of the regime, which
    is why the regime is a block fact."""
    commercial = resolve_datums(20.0, 1865, BuildingClass.GRAND, GroundRegime.COMMERCIAL)
    residential = resolve_datums(20.0, 1865, BuildingClass.GRAND, GroundRegime.RESIDENTIAL)
    assert len(commercial.string_course_levels) == 2
    assert len(residential.string_course_levels) == 1


# ===========================================================================
# solve_block — assembly
# ===========================================================================


def test_solve_block_emits_the_blocks_own_objects():
    block = plan_block(96.0, 20.0, 1865, seed=7, corner_left=True, corner_right=True)
    nodes = solve_block(block, 1865, seed=7)
    kinds = [n.kind for n in nodes]
    assert kinds.count("parcel") == len(block.parcels)
    assert kinds.count("party_wall") == len(block.parcels) - 1
    assert kinds.count("chamfer") == 2
    datum_lines = [n for n in nodes if n.props.get("datum")]
    assert len(datum_lines) == (
        len(block.datums.string_course_levels) + len(block.datums.balcony_levels) + 1
    )


def test_every_node_on_the_block_is_addressable():
    """Ids are how an element is pointed at. Eight buildings all called ``b``
    would make the block un-addressable, so the block namespaces them."""
    block = plan_block(96.0, 20.0, 1865, seed=7, corner_left=True)
    nodes = solve_block(block, 1865, seed=7)
    ids = [n.id for n in block_nodes(nodes)]
    assert len(ids) == len(set(ids))


def test_a_building_stays_in_its_own_parcel_coordinates():
    """The IR convention is "origin at the left edge of the parcel". The offset
    along the frontage lives on the parcel node, so there is exactly one place
    a building's position on the street is decided."""
    block = plan_block(96.0, 20.0, 1865, seed=7)
    nodes = solve_block(block, 1865, seed=7)
    parcels = [n for n in nodes if n.kind == "parcel"]
    for node, origin in zip(parcels, block.origins):
        assert node.props["x"] == pytest.approx(origin, abs=1e-12)
        building = node.children[0]
        assert building.kind == "building"
        assert float(building.props.get("x", 0.0)) == pytest.approx(0.0, abs=1e-12)


def test_the_datum_lines_span_the_whole_frontage():
    block = plan_block(96.0, 20.0, 1865, seed=7)
    nodes = solve_block(block, 1865, seed=7)
    for node in nodes:
        if node.props.get("datum"):
            assert node.props["x"] == pytest.approx(0.0, abs=1e-12)
            assert node.props["w"] == pytest.approx(block.frontage, abs=1e-9)


def test_the_chamfer_carries_the_datums_around_the_corner():
    """What makes a pan coupé part of the block rather than a gap between two
    blocks is that the lines run across it at the heights they run at on both
    neighbours."""
    block = plan_block(96.0, 20.0, 1865, seed=7, corner_left=True)
    nodes = solve_block(block, 1865, seed=7)
    chamfer = next(n for n in nodes if n.kind == "chamfer")
    carried = sorted(
        float(c.props["y"]) for c in chamfer.children if c.props.get("datum")
    )
    on_the_run = sorted(float(n.props["y"]) for n in nodes if n.props.get("datum"))
    assert carried == pytest.approx(on_the_run, abs=1e-12)
    # The chamfer's bays now live under its storeys, the way a facade's do
    # (A4.5): a pan coupé used to be a flat row of bays from pavement to
    # eaves with nothing in them, which is why every one of them rendered as
    # a blank unpierced wall. Reached through `block_nodes` rather than
    # `.children` for that reason, not to weaken the assertion — the check
    # below is strictly more than the old one, because it also demands that
    # the bays be pierced.
    bays = [n for n in block_nodes((chamfer,)) if n.kind == "bay"]
    assert bays
    assert any(c.kind == "opening" for bay in bays for c in bay.children), (
        "a pan coupé with no opening anywhere on it is a blank wall"
    )


def test_one_fact_one_name_every_bay_on_the_block_says_slot_name():
    """A4.7. Chamfer bays used to carry ``props['slot']`` while every building
    bay carried ``props['slot_name']``, so a consumer keying on ``slot_name``
    read ``None`` on a pan coupé — silently, because a missing key and "no
    opinion" are the same thing to ``props.get``. The renderer's pier test
    (``render.py``: ``slot_name in _PIER_KINDS``) is exactly such a consumer.
    """
    block = plan_block(96.0, 20.0, 1865, seed=7, corner_left=True, corner_right=True)
    nodes = solve_block(block, 1865, seed=7)
    bays = [n for n in block_nodes(nodes) if n.kind == "bay"]
    assert bays
    chamfer_bays = [n for n in bays if "/chamfer/" in n.id]
    assert chamfer_bays, "this fixture is supposed to have two pan coupés"
    for bay in bays:
        assert "slot" not in bay.props, f"{bay.id} still carries the old name"
        assert isinstance(bay.props.get("slot_name"), str), (
            f"{bay.id} has no slot_name"
        )


def test_solve_block_is_deterministic():
    a = solve_block(plan_block(70.0, 20.0, 1865, seed=4), 1865, seed=4)
    b = solve_block(plan_block(70.0, 20.0, 1865, seed=4), 1865, seed=4)
    assert [to_json(n) for n in a] == [to_json(n) for n in b]


def test_every_block_node_carries_a_trace():
    block = plan_block(70.0, 20.0, 1865, seed=4, corner_right=True)
    for node in block_nodes(solve_block(block, 1865, seed=4)):
        assert node.trace  # I4 — enforced at construction, restated here


def test_the_blocks_own_nodes_cite_the_circulaire():
    block = plan_block(70.0, 20.0, 1865, seed=4)
    nodes = solve_block(block, 1865, seed=4)
    for node in nodes:
        if node.props.get("datum"):
            detail = " ".join(e.detail for e in node.trace)
            assert "1855" in detail


def test_solve_block_refuses_datums_from_another_situation():
    """A handed-down bundle that no longer matches its situation is a block
    fact resolved twice."""
    block = plan_block(70.0, 20.0, 1865, klass=BuildingClass.ORDINARY, seed=4)
    with pytest.raises(BlockDatumViolation, match="not resolved for the situation"):
        solve_block(block, 1865, klass=BuildingClass.GRAND, seed=4)
    with pytest.raises(BlockDatumViolation, match="not resolved for the situation"):
        solve_block(block, 1890, klass=BuildingClass.ORDINARY, seed=4)


def test_solve_block_checks_the_programme_count():
    block = plan_block(70.0, 20.0, 1865, seed=4)
    with pytest.raises(ValueError, match="ground programmes"):
        solve_block(block, 1865, seed=4, grounds=(GroundProgramme.SHOP,))


def test_regime_membership_is_total():
    for programme in GroundProgramme:
        assert programme in GroundRegime.of(programme).programmes


# ---------------------------------------------------------------------------
# A4.5 — "a corner is a third short facade with its own rhythm"
#
# Only the rhythm was ever built. `_chamfer_node` gave each chamfer bay
# x/y/w/slot_name and no children at all, so every pan coupé in every block
# was a blank unpierced wall between two pierced ones — and nothing errored,
# because a bay with no opening is a perfectly legal pier.
# ---------------------------------------------------------------------------


def _chamfers(nodes):
    return [n for n in nodes if n.kind == "chamfer"]


def test_a_pan_coupe_carries_the_storeys_of_the_building_it_cuts():
    """Its floors are that building's floors — a cut face is a face of one
    building, not a third building wedged into the angle."""
    block = plan_block(96.0, 20.0, 1868, seed=3, corner_left=True, corner_right=True)
    nodes = solve_block(block, 1868, seed=3)
    parcels = [n for n in nodes if n.kind == "parcel"]

    for chamfer in _chamfers(nodes):
        parcel = parcels[int(chamfer.props["parcel"])]
        building = next(c for c in parcel.children if c.kind == "building")
        facade = [
            (round(float(s.props["y"]), 9), round(float(s.props["h"]), 9))
            for s in building.children
            if s.kind == "storey" and s.props.get("on_the_stone_facade") is not False
        ]
        cut = [
            (round(float(s.props["y"]), 9), round(float(s.props["h"]), 9))
            for s in chamfer.children
            if s.kind == "storey"
        ]
        assert cut, f"{chamfer.id} has no storeys"
        assert cut == [lvl for lvl in facade if lvl in cut]
        assert len(cut) >= len(facade) - 1, (
            f"{chamfer.id} carries {len(cut)} of the facade's {len(facade)} storeys"
        )


def test_a_pan_coupe_has_its_own_rhythm_and_its_neighbours_openings():
    """Both halves of the sentence, asserted separately.

    The bays are the chamfer's own — narrower than the facade's, from
    ``_CHAMFER_BAY`` — and what stands in them is the corner building's own
    opening: same type, same head, same sill, re-centred, and narrowed only
    where the narrower slot cannot carry it with a real pier either side.
    """
    block = plan_block(96.0, 20.0, 1868, seed=3, corner_left=True, corner_right=True)
    nodes = solve_block(block, 1868, seed=3)
    parcels = [n for n in nodes if n.kind == "parcel"]

    for chamfer in _chamfers(nodes):
        parcel = parcels[int(chamfer.props["parcel"])]
        building = next(c for c in parcel.children if c.kind == "building")
        facade_bays = [
            float(b.props["w"])
            for s in building.children
            if s.kind == "storey"
            for b in s.children
            if b.kind == "bay" and b.props.get("slot_name") == "bay"
        ]
        cut_bays = [
            float(b.props["w"])
            for s in chamfer.children
            if s.kind == "storey"
            for b in s.children
            if b.kind == "bay" and b.props.get("slot_name") == "bay"
        ]
        assert cut_bays and facade_bays
        assert max(cut_bays) < min(facade_bays), (
            "the pan coupé is using the facade's bay band, not its own"
        )

        openings = [n for n in block_nodes((chamfer,)) if n.kind == "opening"]
        assert openings, f"{chamfer.id} is a blank wall"
        by_storey = {}
        for s in chamfer.children:
            if s.kind != "storey":
                continue
            for b in s.children:
                for c in b.children:
                    if c.kind == "opening":
                        by_storey.setdefault(round(float(s.props["y"]), 6), []).append(c)

        for s in building.children:
            if s.kind != "storey":
                continue
            key = round(float(s.props["y"]), 6)
            if key not in by_storey:
                continue
            model = next(
                (
                    c
                    for b in s.children
                    if b.kind == "bay" and b.props.get("slot_name") == "bay"
                    for c in b.children
                    if c.kind == "opening"
                ),
                None,
            )
            assert model is not None
            for cut in by_storey[key]:
                assert cut.props["opening_type"] == model.props["opening_type"]
                assert cut.props["head"] == model.props["head"]
                assert float(cut.props["y"]) == pytest.approx(float(model.props["y"]))
                assert float(cut.props["h"]) == pytest.approx(float(model.props["h"]))
                assert float(cut.props["w"]) <= float(model.props["w"]) + 1e-9
                # A real pier either side of it, in a slot narrower than the
                # facade's — which is the whole difficulty of a corner.
                assert float(cut.props["pier_width"]) > 0.0
                assert float(cut.props["x"]) > float(cut.props["slot_x"]) + 1e-9


def test_no_pan_coupe_anywhere_in_the_sweep_is_a_blank_wall():
    """The defect was visible on every block the contact sheets rendered, so
    it is checked over a sweep rather than on one fixture."""
    blank = []
    for i in range(12):
        year = 1820 + i * 7
        street_width = 9.0 + i * 1.3
        klass = list(BuildingClass)[i % 4]
        regime = list(GroundRegime)[i % 3]
        block = plan_block(
            70.0 + i * 5,
            street_width,
            year,
            klass=klass,
            regime=regime,
            seed=i,
            corner_left=True,
            corner_right=True,
        )
        nodes = solve_block(block, year, klass=klass, regime=regime, seed=i)
        for chamfer in _chamfers(nodes):
            if not [n for n in block_nodes((chamfer,)) if n.kind == "opening"]:
                blank.append((year, street_width, klass.value, regime.value))
    assert not blank, f"blank pan coupés: {blank}"


# ---------------------------------------------------------------------------
# A6.3 — the pan coupé has no roof
#
# Both chamfer nodes carried storeys, string courses, balconies and a cornice,
# and no roof child — bare sky above the one place a Paris roof is most
# visible. A pan coupé's comble is the corner building's own comble, read at
# the chamfer's own (narrower) width, not a second roof invented for a third
# facade.
# ---------------------------------------------------------------------------


def test_a_pan_coupe_carries_a_roof():
    block = plan_block(96.0, 20.0, 1888, seed=5, corner_left=True, corner_right=True)
    nodes = solve_block(block, 1888, seed=5)
    parcels = [n for n in nodes if n.kind == "parcel"]

    for chamfer in _chamfers(nodes):
        roofs = [c for c in chamfer.children if c.kind == "roof"]
        silhouettes = [c for c in chamfer.children if c.kind == "silhouette"]
        assert roofs, f"{chamfer.id} has no roof — bare sky above the cut face"
        assert silhouettes, f"{chamfer.id} has no silhouette to draw that roof from"
        roof, silhouette = roofs[0], silhouettes[0]

        # Not a second roof invented for a third facade: the SAME envelope,
        # eaves, ridge, material and dormer choice as the corner building's
        # own comble — only the width along the frontage is the chamfer's.
        parcel = parcels[int(chamfer.props["parcel"])]
        building = next(c for c in parcel.children if c.kind == "building")
        building_roof = next(c for c in building.children if c.kind == "roof")
        assert float(roof.props["h"]) == pytest.approx(float(building_roof.props["h"]))
        assert float(roof.props["eaves_height"]) == pytest.approx(
            float(building_roof.props["eaves_height"])
        )
        assert roof.props["material"] == building_roof.props["material"]
        assert roof.props["envelope"] == building_roof.props["envelope"]
        assert float(roof.props["w"]) == pytest.approx(float(chamfer.props["w"]))

        # A pan coupé is a return on both of its sides, never a run
        # continuing into a party wall.
        assert roof.props["ends"] == "hipped"
        assert silhouette.props["ends"] == "hipped"


def test_a_pan_coupes_roof_stands_above_its_own_eaves():
    """The chamfer node's own ``h`` is its stone face — the eaves, same
    convention as a building's ``eaves_height`` versus its ``h`` — so a
    consumer sizing a canvas from the chamfer alone must add its roof's own
    height in, the same way it already does for a building's total height."""
    block = plan_block(70.0, 20.0, 1888, seed=6, corner_left=True, corner_right=False)
    nodes = solve_block(block, 1888, seed=6)
    chamfer = next(n for n in nodes if n.kind == "chamfer")
    roof = next(c for c in chamfer.children if c.kind == "roof")
    eaves_only = float(chamfer.props["h"])
    with_roof = eaves_only + float(roof.props["h"])
    assert with_roof > eaves_only + 1e-6
