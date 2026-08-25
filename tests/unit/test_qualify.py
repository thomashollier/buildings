"""S6 phase 3 — the qualification context and the rule layers.

The centrepiece is ``test_removing_the_mezzanine_moves_the_balcony_up_a_floor``:
the brief names it as the test of the whole rule model, and it passes here with
no rule edited, because the balcony rule is about a height above the pavement
and never about which floor it is.
"""

from __future__ import annotations

import dataclasses

import pytest

from buildings.quantity import Reg
from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris import catalogue, chronology, reglement
from buildings.typologies.paris.reglement_adapter import compute_envelope, era_for_year
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris.structure import Grid, solve_structure
from buildings.typologies.paris import compose as compose_module
from buildings.typologies.paris.qualify import base as base_layer
from buildings.typologies.paris.qualify import klass as klass_layer
from buildings.typologies.paris.qualify import period as period_layer
from buildings.typologies.paris.qualify.context import (
    PROPERTY_KEYS,
    Properties,
    QualContext,
    contexts_for,
    storey_contexts_for,
)


# ---------------------------------------------------------------------------
# Helpers: hand-built grids, so an experiment can change exactly one thing
# ---------------------------------------------------------------------------


def _grid(
    storey_heights: list[float],
    bay_widths: list[float],
    cornice: float = 30.0,
    entrance: str | None = catalogue.ENTRANCE_PEDESTRIAN,
) -> Grid:
    """A Grid assembled by hand.

    Going through ``solve_structure`` would mean asking the solver for two
    stacks that differ *only* in the mezzanine, which it has no way to
    guarantee. The roles are still derived by the real ``assign_roles``, so
    the predicate under test is not stubbed — only the arithmetic upstream of
    it is pinned.
    """
    storeys = []
    y = 0.0
    for i, h in enumerate(storey_heights):
        storeys.append(
            PlacedSlot(name="storey" if i else "ground", kind=SlotKind.REPEATING, start=y, width=h)
        )
        y += h
    bays = []
    x = 0.0
    names = ["pier_end"] + ["bay"] * (len(bay_widths) - 2) + ["pier_end"]
    # A6.1: every building has exactly one entrance, and a fixture without one
    # is not a building anybody could get into — ``compose`` refuses it. The
    # real phase 1 puts the door in the middle of the interior run, so the
    # fixture does the same rather than inventing a second placement rule.
    if entrance is not None and len(bay_widths) > 2:
        names[1 + (len(bay_widths) - 2) // 2] = entrance
    for name, w in zip(names, bay_widths):
        bays.append(
            PlacedSlot(
                name=name,
                kind=SlotKind.FIXED
                if name in catalogue.ENTRANCE_SLOT_NAMES
                else (SlotKind.FLEXIBLE if name == "pier_end" else SlotKind.REPEATING),
                start=x,
                width=w,
            )
        )
        x += w
    return Grid(
        storeys=tuple(storeys),
        bays=tuple(bays),
        cornice_height=Reg(cornice, "test fixture"),
        # The fixture builds a facade and no comble, so the eaves line is the
        # top of the stack: no slot stands inside the roof.
        eaves_height=y,
        envelope=compute_envelope(15.0, era_for_year(1870), 14.0)._core,
        account=("hand-built test fixture",),
    )


def _site(**over) -> SiteContext:
    fields = dict(
        street_width=15.0,
        parcel_width=13.0,
        parcel_depth=14.0,
        year=1870,
        klass=BuildingClass.ORDINARY,
        ground=GroundProgramme.RESIDENTIAL,
        corner=False,
        seed=11,
    )
    fields.update(over)
    return SiteContext(**fields)


def _ctx(**over) -> QualContext:
    fields = dict(
        slot_h=3.2,
        slot_w=3.0,
        level_above_pavement=6.5,
        index_from_bottom=2,
        index_from_top=2,
        storey_count=5,
        role=Role.PRINCIPAL,
        rank_from_principal=0,
        bay_index_from_left=2,
        bay_index_from_centre=0,
        is_centre_bay=True,
        distance_from_entrance=0,
        is_edge_special=False,
        is_inserted_special=False,
        slot_kind=SlotKind.REPEATING,
        year=1870,
        klass=BuildingClass.ORDINARY,
        street_width=15.0,
        corner=False,
        cornice_height=18.0,
        within_comble=False,
        ground=GroundProgramme.RESIDENTIAL,
        slot_name="bay",
        storeys_within_comble=0,
    )
    fields.update(over)
    # A13's two envelope facts about the commercial base (context EXTENSIONs 4
    # and 5). Derived here rather than defaulted, so that a fixture asking for
    # ``role=Role.MEZZANINE`` gets a context that is INTERNALLY CONSISTENT: the
    # entresol exists exactly when the stack says it does, and the top of the
    # base is where the storeys put it. A caller that means to test the
    # inconsistent case passes them explicitly.
    # A21.4 (context EXTENSION 6): the noble floor's own level, derived the
    # same way and for the same reason — a fixture must be internally
    # consistent about whether THIS building steps out onto balconies. On a
    # rank-0 fixture that is this storey's own level; otherwise assume the
    # noble floor sits where a Paris one does, clear of the 1823 threshold,
    # which is what every fixture here was implicitly relying on before the
    # field existed. A caller testing the low-noble-floor case passes it.
    if "principal_level" not in over:
        fields["principal_level"] = (
            fields["level_above_pavement"]
            if fields["rank_from_principal"] == 0
            else 6.5
        )
    if "storeys_in_the_base_block" not in over:
        fields["storeys_in_the_base_block"] = (
            2 if fields["role"] is Role.MEZZANINE else 1
        )
    if "base_block_top" not in over:
        if fields["role"] is Role.BASE:
            top = fields["level_above_pavement"] + fields["slot_h"]
        elif fields["role"] is Role.MEZZANINE:
            top = fields["level_above_pavement"] + fields["slot_h"]
        else:
            # A stack whose base block ends well below this cell: enough that
            # ``crowns_the_base_block`` is False, which is what every fixture
            # above the base wants unless it says otherwise.
            top = 0.5
        fields["base_block_top"] = top
    # A slot named `porte_cochere` that is 3.00 x 3.20 m is a grid phase 1
    # never produces: it places that slot at `carriage_slot_width` in a storey
    # of `carriage_storey_height`, because a carriage has to fit. Since A5.5
    # the catalogue refuses such a slot loudly rather than handing back a
    # shortened door, so a fixture that wants a carriage entrance has to give
    # it the frontage and the headroom one takes — and a caller that means to
    # test the refusal passes the short dimensions explicitly.
    if fields["slot_name"] == "porte_cochere":
        if "slot_w" not in over:
            fields["slot_w"] = float(catalogue.carriage_slot_width())
        if "slot_h" not in over:
            fields["slot_h"] = float(catalogue.carriage_storey_height())
    return QualContext(**fields)


RNG = DecisionStream(42)


# ===========================================================================
# The context is read-only and complete
# ===========================================================================


def test_context_is_frozen_and_mutation_raises():
    ctx = _ctx()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.year = 1890  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.level_above_pavement = 0.0  # type: ignore[misc]


def test_context_refuses_new_attributes_too():
    """Not just the declared fields — a rule cannot stash state on the context
    either, which is what "never mutated by qualification" has to mean."""
    ctx = _ctx()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.scratch = "whatever"  # type: ignore[attr-defined]


def test_a_rule_that_tries_to_mutate_the_context_raises_rather_than_drifting():
    def naughty(ctx, rng):
        ctx.rank_from_principal = 0  # type: ignore[misc]
        return None

    with pytest.raises(dataclasses.FrozenInstanceError):
        naughty(_ctx(), RNG)


def test_context_grid_covers_every_cell_exactly_once():
    site = _site()
    roled = assign_roles(solve_structure(site))
    cells = contexts_for(roled, site)
    assert len(cells) == len(roled.storeys)
    assert all(len(row) == len(roled.bays) for row in cells)
    for row_i, row in enumerate(cells):
        for col_i, ctx in enumerate(row):
            assert ctx.index_from_bottom == row_i
            assert ctx.bay_index_from_left == col_i
            assert ctx.slot_w == pytest.approx(roled.bays[col_i].width)
            assert ctx.slot_h == pytest.approx(roled.storeys[row_i].slot.width)
            assert ctx.level_above_pavement == pytest.approx(
                roled.storeys[row_i].slot.start
            )


def test_context_carries_the_block_fact_it_was_handed_and_never_a_sampled_one():
    """I2: the building receives ``street_width``; it never chooses it."""
    site = _site(street_width=22.0)
    roled = assign_roles(solve_structure(site))
    for row in contexts_for(roled, site):
        for ctx in row:
            assert ctx.street_width == 22.0


def test_entrance_and_centre_are_facts_not_decisions():
    site = _site(ground=GroundProgramme.CARRIAGE, parcel_width=14.0)
    roled = assign_roles(solve_structure(site))
    cells = contexts_for(roled, site)
    entrance_col = [
        i for i, b in enumerate(roled.bays) if b.name == "porte_cochere"
    ]
    assert entrance_col, "this fixture is supposed to have a carriage entrance"
    for row in cells:
        zero = [c.bay_index_from_left for c in row if c.distance_from_entrance == 0]
        assert zero == entrance_col
    # exactly one slot can be the centre, and never more
    for row in cells:
        assert sum(1 for c in row if c.is_centre_bay) <= 1


def test_context_is_deterministic_for_a_situation():
    site = _site()
    a = contexts_for(assign_roles(solve_structure(site)), site)
    b = contexts_for(assign_roles(solve_structure(site)), site)
    assert a == b


# ===========================================================================
# Properties are sparse, closed and attributed
# ===========================================================================


def test_properties_reject_an_unknown_key():
    with pytest.raises(ValueError, match="unknown property key"):
        Properties({"balcony_projeciton": 0.8}, rule="test.typo")


def test_properties_reject_an_anonymous_rule():
    with pytest.raises(ValueError, match="non-empty RuleId"):
        Properties({"opening_type": "window"}, rule="  ")


def test_properties_are_sparse_by_design():
    p = Properties({"opening_type": "window"}, rule="test.sparse")
    assert set(p.values) == {"opening_type"}
    assert "balcony_present" not in p.values  # no opinion, not False


def test_every_key_a_shipped_rule_sets_is_in_the_vocabulary():
    seen: set[str] = set()
    for rules in (base_layer.BASE_RULES, period_layer.PERIOD_RULES, klass_layer.CLASS_RULES):
        for rule in rules:
            for ctx in _every_kind_of_cell():
                props = rule(ctx, RNG)
                if props is not None:
                    seen |= set(props.values)
    assert seen <= PROPERTY_KEYS
    assert seen, "the sweep did not exercise any rule — the fixture is wrong"


def _every_kind_of_cell():
    for site in (
        _site(),
        _site(ground=GroundProgramme.SHOP, klass=BuildingClass.GRAND, year=1895),
        _site(ground=GroundProgramme.CARRIAGE, klass=BuildingClass.MODEST, year=1830),
        _site(corner=True, klass=BuildingClass.COMFORTABLE, year=1860, street_width=25.0),
    ):
        roled = assign_roles(solve_structure(site))
        for row in contexts_for(roled, site):
            yield from row


# ===========================================================================
# THE test: the balcony is a height above the pavement, not a floor number
# ===========================================================================


def _balconied_ranks(storey_heights: list[float], site: SiteContext) -> list[int]:
    """Which ranks-from-principal carry a balcony, by the base rule alone."""
    grid = _grid(storey_heights, [0.5, 3.0, 3.0, 3.0, 3.0, 0.5])
    roled = assign_roles(grid)
    out = []
    for ctx in storey_contexts_for(roled, site):
        props = base_layer.balcony_ordonnance_1823(ctx, RNG)
        assert props is not None, "the ordonnance always has an opinion"
        if props.values.get("balcony_present"):
            out.append(ctx.rank_from_principal)
    return out


WITH_MEZZANINE = [4.2, 2.1, 3.6, 3.4, 3.2]
WITHOUT_MEZZANINE = [4.2, 3.6, 3.4, 3.2]


def test_the_fixture_really_does_differ_only_by_the_mezzanine():
    """Guard on the experiment itself: the roles phase must agree that one
    stack has a mezzanine and the other does not, or the test below is
    measuring something else."""
    with_m = assign_roles(_grid(WITH_MEZZANINE, [0.5, 3.0, 3.0, 3.0, 3.0, 0.5]))
    without_m = assign_roles(_grid(WITHOUT_MEZZANINE, [0.5, 3.0, 3.0, 3.0, 3.0, 0.5]))
    assert [s.role for s in with_m.storeys].count(Role.MEZZANINE) == 1
    assert [s.role for s in without_m.storeys].count(Role.MEZZANINE) == 0
    # ...and the storeys above the entresol are otherwise the same heights
    assert WITH_MEZZANINE[2:] == WITHOUT_MEZZANINE[1:]


def test_removing_the_mezzanine_moves_the_balcony_up_a_floor():
    """The brief's own test of the rule model, run literally.

    "Take away the mezzanine and the balcony should jump up a floor by itself
    — because the balcony rule is about height above the pavement, not about
    which floor it is."

    Nothing is edited between the two halves of this test. The 2.1 m entresol
    lifts the noble floor to 6.3 m, which the 1823 ordonnance permits; without
    it the noble floor sits at 4.2 m, which it does not, and the lowest
    balcony lands one rank higher.
    """
    site = _site()
    with_mezzanine = _balconied_ranks(WITH_MEZZANINE, site)
    without_mezzanine = _balconied_ranks(WITHOUT_MEZZANINE, site)

    assert min(with_mezzanine) == 0, "the entresol lifts the noble floor over 6 m"
    assert min(without_mezzanine) == 1, "without it, the noble floor is under 6 m"
    assert min(without_mezzanine) == min(with_mezzanine) + 1


def test_the_threshold_is_the_ordonnance_and_not_a_number_in_the_rule():
    """G6: asserted against ``reglement.balcony_rule``, not against 6.0."""
    site = _site()
    grid = _grid(WITH_MEZZANINE, [0.5, 3.0, 3.0, 3.0, 3.0, 0.5])
    roled = assign_roles(grid)
    levels = [s.slot.start for s in roled.storeys]
    oracle = reglement.balcony_rule(levels, era_for_year(site.year))

    eligible_by_oracle = {
        i for i, y in enumerate(levels) if y >= oracle.min_height - 1e-9
    }
    eligible_by_rule = set()
    for ctx in storey_contexts_for(roled, site):
        props = base_layer.balcony_ordonnance_1823(ctx, RNG)
        assert props.values["balcony_min_height"] == pytest.approx(oracle.min_height)
        if props.values.get("balcony_present"):
            eligible_by_rule.add(ctx.index_from_bottom)

    assert eligible_by_rule == eligible_by_oracle


def test_the_projection_cap_is_the_ordonnance_too():
    site = _site()
    ctx = _ctx(level_above_pavement=9.0)
    oracle = reglement.balcony_rule([9.0], era_for_year(site.year))
    props = base_layer.balcony_ordonnance_1823(ctx, RNG)
    assert props.values["balcony_projection"] == pytest.approx(oracle.max_projection)


def test_the_balcony_projects_the_same_distance_however_grand_the_building():
    """**A9.4, and it reverses the test it replaces.**

    This used to be ``test_a_grand_owner_asks_for_more_than_the_law_allows_
    and_gets_the_law``: a strict MODEST < ORDINARY < COMFORTABLE ladder in the
    wanted depth, with GRAND asserted to land exactly on the 1823 ordonnance's
    0.80 m cap. Daly prints the figure on two different buildings in the same
    class — **0.600 m at 88 rue de Rivoli and 0.590 m at 120 boulevard de
    Sébastopol**, two printed callouts 2 % apart — and nothing in the corpus
    is anywhere near 0.80 m. A balcony is as deep as the body standing on it.

    So the assertion is now the harder one: four classes, one depth. The cap
    is still asked and still bounds it, because the two numbers are still two
    kinds and an ordonnance is still entitled to bind — what has stopped is
    the model manufacturing a collision in order to have one to point at.
    """
    cap = reglement.balcony_rule([9.0], era_for_year(1870)).max_projection
    depths = {}
    for k in BuildingClass:
        props = klass_layer.balcony_depth_is_absolute_under_the_ordonnance(
            _ctx(level_above_pavement=9.0, klass=k), RNG
        )
        depths[k] = props.values["balcony_projection"]
    assert len(set(round(d, 9) for d in depths.values())) == 1, (
        f"the balcony projection scaled with class: {depths}"
    )
    assert all(d <= cap + 1e-12 for d in depths.values())
    # Daly's two printed callouts, as the band the model has to sit in.
    assert all(0.59 - 1e-9 <= d <= 0.60 + 1e-9 for d in depths.values()), depths


def test_no_balcony_below_the_threshold_however_grand_the_building():
    for k in BuildingClass:
        ctx = _ctx(level_above_pavement=4.0, klass=k)
        assert base_layer.balcony_ordonnance_1823(ctx, RNG).values["balcony_present"] is False
        assert (
            klass_layer.balcony_depth_is_absolute_under_the_ordonnance(ctx, RNG)
            is None
        )


# ===========================================================================
# Treatment diminishes with rank — one relation instead of a per-floor table
# ===========================================================================


def test_ornament_falls_off_from_the_principal_floor_in_both_directions():
    peak = base_layer.ornament_for_rank(0)
    for r in range(1, 6):
        assert base_layer.ornament_for_rank(r) <= base_layer.ornament_for_rank(r - 1)
        assert base_layer.ornament_for_rank(-r) <= base_layer.ornament_for_rank(-(r - 1))
    assert peak == max(base_layer.ornament_for_rank(r) for r in range(-6, 7))


def test_ornament_needs_no_extra_rows_for_a_taller_building():
    """A five-storey and a nine-storey stack are qualified by the same rules;
    the extra storeys are not special cases anywhere."""
    site = _site()
    short = assign_roles(_grid([4.2, 2.1, 3.6, 3.4, 3.2], [0.5, 3.0, 3.0, 0.5]))
    tall = assign_roles(
        _grid([4.2, 2.1, 3.6, 3.4, 3.2, 3.1, 3.0, 2.9, 2.8], [0.5, 3.0, 3.0, 0.5], cornice=40.0)
    )
    for roled in (short, tall):
        densities = [
            base_layer.ornament_diminishes_with_rank(c, RNG).values["ornament_density"]
            for c in storey_contexts_for(roled, site)
        ]
        assert len(densities) == len(roled.storeys)
    ranks = [s.rank_from_principal for s in tall.storeys]
    assert ranks == sorted(ranks), "rank must increase monotonically up the stack"


def test_richer_class_carries_more_ornament_at_every_rank():
    for rank in (-1, 0, 1, 2, 3):
        got = [
            klass_layer.ornament_density_scales_with_money(
                _ctx(rank_from_principal=rank, klass=k), RNG
            ).values["ornament_density"]
            for k in (
                BuildingClass.MODEST,
                BuildingClass.ORDINARY,
                BuildingClass.COMFORTABLE,
                BuildingClass.GRAND,
            )
        ]
        assert got == sorted(got)
        assert all(0.0 <= g <= 1.0 for g in got)


def test_class_scaling_does_not_saturate_and_flatten_the_decay():
    """The bug this test exists for: clamping at 1.0 made a comfortable
    building's top three storeys identical."""
    for k in BuildingClass:
        got = [
            klass_layer.ornament_density_scales_with_money(
                _ctx(rank_from_principal=r, klass=k), RNG
            ).values["ornament_density"]
            for r in range(0, 5)
        ]
        assert len(set(got)) == len(got), f"{k} saturated: {got}"


# ===========================================================================
# What occupies the slot
# ===========================================================================


def test_a_slot_gets_the_opening_its_kind_implies_not_its_index():
    assert (
        base_layer.bay_is_a_window(_ctx(slot_name="bay"), RNG).values["opening_type"]
        == "window"
    )
    assert (
        base_layer.pier_is_blank_wall(_ctx(slot_name="pier_end"), RNG).values["opening_type"]
        == "none"
    )
    assert base_layer.bay_is_a_window(_ctx(slot_name="pier_end"), RNG) is None
    assert base_layer.pier_is_blank_wall(_ctx(slot_name="bay"), RNG) is None


def test_the_carriage_entrance_is_absolute_and_the_rules_do_not_resize_it():
    """The door is the ruler the eye measures the facade against.

    Since A4.1 the entrance rule states the opening's geometry — it has to,
    or the renderer glazes the whole slot — so the claim can no longer be
    "it sets no dimensions". It is now the stronger and more interesting one:
    the dimensions it sets are the SAME for all four classes, and the class
    layer never gets a word in. ``catalogue.carriage_entrance_in_slot`` takes
    no class argument, so there is nowhere for ambition to enter.
    """
    sizes = set()
    for klass in BuildingClass:
        ctx = _ctx(
            slot_name="porte_cochere", role=Role.BASE, rank_from_principal=-1, klass=klass
        )
        props = base_layer.entrance_fills_the_door_slot(ctx, RNG)
        assert props.values["opening_type"] == "carriage_entrance"
        sizes.add(
            (
                props.values["opening_width"],
                props.values["opening_height"],
                props.values["opening_sill_height"],
            )
        )
    assert len(sizes) == 1, f"the carriage entrance changed size with the class: {sizes}"
    # ...and no rule in the class layer touches it either.
    ctx = _ctx(slot_name="porte_cochere", role=Role.BASE, rank_from_principal=-1)
    for rule in klass_layer.CLASS_RULES:
        out = rule(ctx, RNG)
        keys = set(out.values) if out is not None else set()
        assert not (keys & {"opening_width", "opening_height", "opening_offset_x"}), (
            f"{rule.__name__} resized the carriage entrance"
        )


# ===========================================================================
# A4.1 — an opening is not a bay
# ===========================================================================


def _window_geometry(**over):
    """One cell's resolved opening geometry, through the whole Paris stack.

    Deliberately the resolution rather than one rule's output: the size comes
    from the class layer and the sill from the base layer, and which layer
    owns which is part of what these tests are checking.
    """
    ctx = _ctx(**over)
    res = compose_module.resolve(ctx, compose_module.paris_layers(), RNG)
    assert res.get("opening_width") is not None, f"no window geometry for {over}"
    return ctx, res.values


def test_the_class_layer_states_the_openings_own_rectangle_not_the_bays():
    """The defect A4.1 names, asserted at the rule that fixes it.

    Before this, ``opening_*`` carried no dimensions at all and the only
    rectangle in the IR was the bay's, so a consumer had nothing to draw but
    a glazed slot.
    """
    ctx = _ctx()
    stated = klass_layer.window_size_is_what_the_bay_and_the_owner_allow(ctx, RNG)
    assert stated is not None
    assert set(stated.values) >= {"opening_width", "opening_height", "opening_offset_x"}
    # The sill is a body fact and stays in the base layer, which says why it
    # is where it is; the class layer states size and nothing else.
    assert "opening_sill_height" not in stated.values

    _, vals = _window_geometry()
    assert set(vals) >= {
        "opening_width",
        "opening_height",
        "opening_offset_x",
        "opening_sill_height",
    }
    assert vals["opening_width"] < ctx.slot_w
    assert vals["opening_height"] < ctx.slot_h
    assert vals["opening_offset_x"] > 0.0


def test_the_pier_beside_a_window_is_the_catalogues_pier_not_an_invented_margin():
    """A4.1: "take the pier from the bay's own filler width".

    The masonry either side of a window is ``pier_filler`` — a module with a
    stated minimum and a reason — resolved for this class. A renderer that
    invents 0.10 m instead produces a facade with hairline joints between
    panes of glass; a rule that invents any other number has smuggled a
    dimension in without a source.
    """
    for klass in BuildingClass:
        ctx, vals = _window_geometry(klass=klass)
        pier_min = catalogue.pier_filler().to_slot_spec(klass).minimum
        assert vals["opening_offset_x"] >= pier_min - 1e-9, (
            f"{klass.value}: pier {vals['opening_offset_x']:.3f} m is thinner than "
            f"pier_filler's own minimum {pier_min:.3f} m"
        )
        # ...and it is symmetric, so the window is centred in its slot.
        right = ctx.slot_w - vals["opening_offset_x"] - vals["opening_width"]
        assert right == pytest.approx(vals["opening_offset_x"], abs=1e-9)


def test_a_grand_buildings_windows_are_much_bigger_while_its_door_barely_changes():
    """The brief's own sentence, as an assertion — and since A9.4, Daly's.

    "The grand building on the boulevard is legible as grand precisely because
    its doorway is only a little bigger than the modest one's while its
    windows are much bigger." That contrast is the absolute/proportional split
    doing its work, and it is the thing the eye reads as scale — so if it ever
    stops being true, no amount of correct ornament will save the facade.

    **The window is now split in two, and the split is measured.** Across
    Daly's sixteen buildings the opening WIDTH runs 1.04-1.30 m and is
    *non-monotonic* by class (medians 1.139 / 1.235 / 1.070), while the
    opening HEIGHT at the noble floor runs 2.923 / 2.236 / 2.085 m — a 1.40×
    spread, monotonic, and the clearest statement of the absolute/proportional
    distinction in the whole corpus. So this test asserts three things where
    it used to assert one:

    * the width does not move with class **at all** (new, and the sourced half);
    * the height moves with class, strictly, and by at least 1.25× end to end
      (Daly measures 1.40× over his three classes; this typology's four
      classes are bracketed by it, and the top of the ladder is additionally
      capped by the storey it has to fit inside);
    * the door does not move at all.

    The old form asserted only ``area > 1.5×``, which conflated the two halves
    into one number and would have been satisfied by a facade that scaled its
    windows in both directions — exactly the "photographs of one building at
    two distances" failure the brief names.
    """
    widths = {}
    heights = {}
    doors = {}
    for klass in BuildingClass:
        _, vals = _window_geometry(klass=klass)
        widths[klass] = vals["opening_width"]
        heights[klass] = vals["opening_height"]
        door = base_layer.entrance_fills_the_door_slot(
            _ctx(slot_name="porte_cochere", role=Role.BASE, klass=klass), RNG
        ).values
        doors[klass] = door["opening_width"] * door["opening_height"]

    ladder = [
        BuildingClass.MODEST,
        BuildingClass.ORDINARY,
        BuildingClass.COMFORTABLE,
        BuildingClass.GRAND,
    ]
    assert len(set(round(w, 9) for w in widths.values())) == 1, (
        f"the window WIDTH moved with class, and Daly says it does not: {widths}"
    )
    tall = [heights[k] for k in ladder]
    assert tall == sorted(tall) and tall[0] < tall[-1], (
        f"window height is not monotone in class: {heights}"
    )
    assert heights[BuildingClass.GRAND] > 1.25 * heights[BuildingClass.MODEST], (
        f"a grand window is barely taller than a modest one: {heights}"
    )
    assert len(set(doors.values())) == 1, f"the carriage entrance scaled: {doors}"


def test_an_opening_is_a_tall_rectangle_and_the_noble_floor_gets_the_tallest():
    """Shape, and how it falls off — the two claims A4.1 makes about height.

    The band comes from ``catalogue.opening_aspect_band`` rather than from a
    number written here, and only its top is a hard ceiling: an opening may
    never be taller for its width than a Paris opening gets. The floor of the
    band is what an opening *wants*, and a storey too short to give it wins —
    which is why the assertion below is on the ordering, not on the value.
    """
    low, high = catalogue.opening_aspect_band()
    heights = []
    for rank in range(0, 5):
        _, vals = _window_geometry(rank_from_principal=rank, slot_h=6.0)
        aspect = vals["opening_height"] / vals["opening_width"]
        assert aspect <= high + 1e-9, f"rank {rank}: {aspect:.2f} is taller than 1:{high}"
        assert aspect >= low - 1e-9, f"rank {rank}: {aspect:.2f} is squatter than 1:{low}"
        heights.append(vals["opening_height"])
    assert heights[0] == max(heights), "the noble floor's opening is not the tallest"
    assert heights == sorted(heights, reverse=True), (
        f"openings do not shorten as they move up from the noble floor: {heights}"
    )


def test_the_sill_stays_where_a_body_puts_it_however_short_the_storey():
    """``sill_height`` is ABSOLUTE, so a shorter storey shortens the WINDOW,
    never the sill. Getting this backwards — deriving the sill as a fraction
    of the storey — is what makes a facade read as curtain wall going up."""
    sills = set()
    heights = []
    for slot_h in (4.2, 3.4, 3.0, 2.7):
        # An upper floor, so the opening is a window with a sill rather than
        # the noble floor's porte-fenêtre onto the balcon filant.
        _, vals = _window_geometry(slot_h=slot_h, rank_from_principal=1, role=Role.UPPER)
        sills.add(round(vals["opening_sill_height"], 9))
        heights.append(vals["opening_height"])
    # A22: the sill is the ALLÈGE, the breast a light stands on — not
    # ``sill_lean_height``, which is the height a body leans on and therefore
    # the top of the GUARD. Still ABSOLUTE, still identical on every storey,
    # which is all this test was ever about.
    assert sills == {round(float(catalogue.window_allege_height()), 9)}
    assert heights == sorted(heights, reverse=True)


def test_a_porte_fenetre_onto_the_balcon_filant_has_no_sill_to_lean_on():
    """The one opening with no sill, and it is still not a class decision.

    Where the noble floor's own balcon filant runs, the window is walked
    through. The condition is the 1823 ordonnance's, read from
    ``reglement``, so raising the balcony threshold moves this by itself.
    """
    on_the_filant = _ctx(rank_from_principal=0, level_above_pavement=7.0)
    below_it = _ctx(rank_from_principal=0, level_above_pavement=4.0)
    assert base_layer.filant_runs_here(on_the_filant)
    assert not base_layer.filant_runs_here(below_it)
    assert float(base_layer.sill_height_for(on_the_filant)) == 0.0
    assert float(base_layer.sill_height_for(below_it)) == float(
        catalogue.window_allege_height()
    )
    # ...and it is the same for every class: a grand owner does not buy the
    # absence of a sill.
    for klass in BuildingClass:
        _, vals = _window_geometry(
            klass=klass, rank_from_principal=0, level_above_pavement=7.0
        )
        assert vals["opening_sill_height"] == 0.0


def test_the_openings_of_one_facade_stay_centred_and_never_widen_going_up():
    """A storey never lays out — it fills the one shared grid — so the axes of
    a facade are fixed and its openings hang on them.

    **A8.4** changed what may vary along those axes. The widths used to be
    identical from the first floor to the cornice, with only the heights
    changing, and the cost of that was 94 % of upper openings below
    ``catalogue.opening_aspect_band``'s stated floor — a wall of squares. The
    proportion is what carries the reading, so where a storey is too short to
    give it the WIDTH comes in.

    What must still hold, and is what "the jambs line up" was really about:

    * every opening is centred on its bay, so the vertical axis of the facade
      is the same line on every storey;
    * the widths are *monotonic* going up — an opening never grows over the
      one below it — so the jambs step inward toward the cornice rather than
      wandering;
    * and every one of them is inside the band.
    """
    low, high = catalogue.opening_aspect_band()
    seen = []
    for r, h in ((0, 3.6), (1, 3.3), (2, 3.0), (3, 2.8)):
        ctx, vals = _window_geometry(rank_from_principal=r, slot_h=h)
        w = vals["opening_width"]
        ht = vals["opening_height"]
        seen.append(w)
        assert vals["opening_offset_x"] == pytest.approx((ctx.slot_w - w) / 2.0, abs=1e-9)
        assert low - 1e-6 <= ht / w <= high + 1e-6, (r, w, ht, ht / w)
    assert seen == sorted(seen, reverse=True), (
        f"a window widened over the one below it: {seen}"
    )


def test_the_shared_opening_type_derivation_agrees_with_the_layered_rules():
    """``base.opening_type_for`` restates what the five opening rules decide
    between them, because a rule that must *size* an opening may not read
    another rule's output (I1). Duplication of that kind is how a rule set
    rots, so the agreement is asserted over the whole combination space
    rather than claimed in a comment.

    Swept over two seeds since A14: the entrance slot's entresol cell is now
    one of two things depending on a draw (a window beside the door, or the
    upper light of the arch that rose through it), and a single seed would
    have exercised whichever of the two it happened to land on and called the
    other one covered.
    """
    layers = compose_module.paris_layers()
    seen: set[str] = set()
    for seed in (77, 5):
        for slot_name in ("bay", "pier_end", "porte_cochere", "special"):
            for role in Role:
                for ground in GroundProgramme:
                    for topmost in (False, True):
                        special = slot_name == "special"
                        extra = {}
                        if role is Role.MEZZANINE:
                            # A15.4. The fixture's default puts the entresol
                            # floor 6.50 m up, which makes the base register of
                            # a two-storey arch 6.50 m tall — taller than any
                            # rez-de-chaussée Daly measures (3.42-4.85 m) — and
                            # an arch carried through it would stand more than
                            # three times its own span. The catalogue now
                            # refuses that rather than drawing it, so the cell
                            # is given a real ground storey to sit over.
                            extra["level_above_pavement"] = 3.95
                        ctx = _ctx(
                            slot_name=slot_name,
                            role=role,
                            ground=ground,
                            is_edge_special=special,
                            index_from_top=0 if topmost else 2,
                            storeys_within_comble=0,
                            rank_from_principal=0 if role is Role.PRINCIPAL else 1,
                            **extra,
                        )
                        rng = DecisionStream(seed)
                        resolved = compose_module.resolve(ctx, layers, rng).get("opening_type")
                        expected = base_layer.opening_type_for(ctx, rng)
                        seen.add(expected)
                        if resolved is None:
                            assert expected == "none", (
                                f"{slot_name}/{role.value}/{ground.value}: the layers had no "
                                f"opinion but the shared derivation said {expected!r}"
                            )
                            continue
                        assert resolved == expected, (
                            f"seed {seed} {slot_name}/{role.value}/{ground.value}: layers say "
                            f"{resolved!r}, shared derivation says {expected!r}"
                        )
    assert catalogue.ENTRANCE_ARCH_HEAD_OPENING in seen, (
        "the sweep never reached a two-storey entrance arch, so the agreement was "
        "never asserted for the one opening type A14 added"
    )


def test_a_special_is_not_a_squeezed_window():
    """A narrow special carries one of the narrow forms, never a full bay's.

    The allowed set is the whole narrow-special vocabulary, not two thirds of
    it: A6.2 added ``narrow_window`` to the storeys between the pavement and
    the top of the wall, and A7.5 made *which* of the pair appears a fact
    about the column rather than one storey's coin, so either member can now
    turn up on this fixture. What the slot may never carry is the full-bay
    opening it is too narrow for, and that is asserted against the whole list
    of them rather than against ``"window"`` alone.
    """
    ctx = _ctx(slot_name="special", is_edge_special=True)
    props = base_layer.special_slot_takes_a_narrow_feature(ctx, RNG)
    assert props.values["opening_type"] in (
        "blind_panel",
        "oeil_de_boeuf",
        "narrow_window",
    )
    assert props.values["opening_type"] not in (
        "window",
        "shop_bay",
        *catalogue.ENTRANCE_OPENING_TYPES.values(),
    )


def test_absolute_quantities_reach_the_facade_unscaled():
    """The sill and the balustrade gap are set by a body. A grand building
    does not get a taller sill, and that is what makes it read as grand."""
    sills = {
        k: base_layer.bay_is_a_window(_ctx(klass=k), RNG).values["opening_sill_height"]
        for k in BuildingClass
    }
    assert len(set(sills.values())) == 1
    gaps = {
        k: base_layer.garde_corps_where_a_body_could_fall(
            _ctx(klass=k, role=Role.UPPER, rank_from_principal=1), RNG
        ).values["ironwork_gap_max"]
        for k in BuildingClass
    }
    assert len(set(gaps.values())) == 1


# ===========================================================================
# The period layer: date windows, never a period enum
# ===========================================================================


def test_the_variant_chosen_is_one_the_date_actually_offers():
    for year in (1830, 1855, 1875, 1890, 1899):
        ctx = _ctx(year=year, role=Role.UPPER, rank_from_principal=1)
        props = period_layer.ironwork_of_its_date(ctx, RNG)
        offered = {v.name for v, _ in chronology.available("ironwork", year, ctx.klass)}
        assert props.values["ironwork_variant"] in offered


def test_class_lag_makes_two_frontages_of_one_year_stylistic_non_contemporaries():
    """Availability is a function of (feature, year, class). Somewhere in the
    century the grand and the modest frontage must differ, or the lag is
    decorative."""
    differed = False
    for year in range(1830, 1900):
        grand = {
            v.name for v, _ in chronology.available("ironwork", year, BuildingClass.GRAND)
        }
        modest = {
            v.name for v, _ in chronology.available("ironwork", year, BuildingClass.MODEST)
        }
        if grand != modest:
            differed = True
            break
    assert differed


def test_the_period_layer_names_variants_only_where_the_element_exists():
    """A named ironwork variant on a floor with no railing would be a
    property nothing reads and nobody could explain."""
    base_ctx = _ctx(role=Role.BASE, rank_from_principal=-2, slot_name="bay")
    assert base_layer.garde_corps_where_a_body_could_fall(base_ctx, RNG) is None
    assert period_layer.ironwork_of_its_date(base_ctx, RNG) is None


def test_a_variant_draw_is_stable_under_the_seed_and_addressable_by_path():
    ctx = _ctx(role=Role.UPPER, rank_from_principal=1)
    a = period_layer.ironwork_of_its_date(ctx, DecisionStream(5)).values
    b = period_layer.ironwork_of_its_date(ctx, DecisionStream(5)).values
    assert a == b
    # ...and it does not depend on which storey asked, because a facade has
    # one blacksmith
    higher = _ctx(role=Role.UPPER, rank_from_principal=3, index_from_bottom=4)
    c = period_layer.ironwork_of_its_date(higher, DecisionStream(5)).values
    assert a == c


def test_adding_a_new_decision_path_does_not_perturb_an_existing_one():
    """I5's real requirement. If this fails, pinning one choice silently
    rerolls every other choice in the building."""
    rng = DecisionStream(9)
    ctx = _ctx(role=Role.UPPER, rank_from_principal=1)
    before = period_layer.ironwork_of_its_date(ctx, rng).values["ironwork_variant"]
    rng.at("some/brand/new/path/nobody/used/before").random()
    rng.choice("another/new/path", ["a", "b", "c"])
    after = period_layer.ironwork_of_its_date(ctx, rng).values["ironwork_variant"]
    assert before == after


def test_no_rule_reads_a_period_enum():
    """The mechanical guard lives in dev/harness; this is the same claim
    asserted where the rules are, so a rewrite of the rule files trips it."""
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "src" / "buildings" / "typologies" / "paris"
    for path in [root / "compose.py", *sorted((root / "qualify").glob("*.py"))]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                text = ast.unparse(node)
                assert "era" not in text.lower() and "period" not in text.lower(), (
                    f"{path.name}: {text}"
                )


def test_the_shopfront_only_appears_where_something_is_sold():
    for ground in GroundProgramme:
        ctx = _ctx(role=Role.BASE, rank_from_principal=-1, ground=ground)
        props = base_layer.ground_programme_treatment(ctx, RNG)
        sells = ground in (GroundProgramme.SHOP, GroundProgramme.CAFE)
        assert props.values["shopfront_present"] is sells
        assert (period_layer.shopfront_of_its_date(ctx, RNG) is not None) is sells


# ===========================================================================
# A2.1 — ``within_comble`` is an envelope fact, and it is now reachable
# ===========================================================================
#
# The brief lists "whether the slot lies within the comble" under *Envelope*,
# not under *Role*: the slot lies in the comble, and THEREFORE the role is
# attic. The context used to read the field off ``Role.ATTIC``, which inverted
# that — and since no storey ever stood inside a roof, the field was False on
# every cell of every building ever generated and every rule reading it was
# unexercised.


def _real_contexts(**over):
    from buildings.typologies.paris.qualify.context import storey_contexts_for
    from buildings.typologies.paris.structure import solve_structure

    site = _site(**over)
    grid = solve_structure(site)
    roled = assign_roles(grid)
    return grid, roled, storey_contexts_for(roled, site)


def test_within_comble_is_true_for_the_storey_standing_in_the_roof():
    grid, roled, ctxs = _real_contexts(street_width=20.0, parcel_depth=15.0)
    assert grid.comble_storeys, "this situation was chosen for having one"
    assert [c.within_comble for c in ctxs] == [False] * (len(ctxs) - 1) + [True]
    assert all(c.storeys_within_comble == 1 for c in ctxs)


def test_within_comble_is_the_geometry_and_agrees_with_the_role_everywhere():
    """Derived from ``Grid.stands_in_the_roof`` rather than from the role, so
    the direction of derivation matches the brief — and the two must still
    agree on every storey of every building, since they call one predicate."""
    for street in (8.0, 14.0, 22.0, 30.0):
        for depth in (5.0, 8.0, 14.0, 20.0):
            for klass in BuildingClass:
                grid, roled, ctxs = _real_contexts(
                    street_width=street, parcel_depth=depth, klass=klass
                )
                for st, ctx in zip(roled.storeys, ctxs):
                    assert ctx.within_comble is (st.role is Role.ATTIC), (
                        street, depth, klass, st.index_from_bottom, st.role,
                    )
                assert ctx.storeys_within_comble == sum(
                    1 for c in ctxs if c.within_comble
                )


def test_a_shallow_comble_leaves_within_comble_false_on_every_cell():
    grid, _roled, ctxs = _real_contexts(street_width=12.0, parcel_depth=5.0)
    assert grid.comble_storeys == ()
    assert not any(c.within_comble for c in ctxs)
    assert all(c.storeys_within_comble == 0 for c in ctxs)


def test_the_cornice_now_crowns_the_wall_and_not_the_garret():
    """``is_topmost_habitable`` was ``index_from_top == 0`` in practice,
    because ``storeys_within_comble`` was always 0. With a storey in the roof
    it means what it says: the last floor behind the stone, the one the
    cornice sits on."""
    grid, roled, ctxs = _real_contexts(street_width=20.0, parcel_depth=15.0)
    flagged = [c.index_from_bottom for c in ctxs if c.is_topmost_habitable]
    assert len(flagged) == 1
    top = flagged[0]
    assert top == len(ctxs) - 2  # the storey below the comble, not the comble
    assert not ctxs[top].within_comble
    assert ctxs[top + 1].within_comble


def test_the_cornice_still_crowns_the_top_slot_where_there_is_no_comble_storey():
    grid, _roled, ctxs = _real_contexts(street_width=12.0, parcel_depth=5.0)
    assert grid.comble_storeys == ()
    flagged = [c.index_from_bottom for c in ctxs if c.is_topmost_habitable]
    assert flagged == [len(ctxs) - 1]


# ===========================================================================
# A4.1 — the porte cochère is an opening in a wall, like every other opening
#
# It used to be the exception: `carriage_entrance_in_slot` returned the slot
# itself, edge to edge, so 44/44 sampled doors had `offset_x == 0.0` and a
# width exactly equal to their slot — an arch standing on nothing. And the
# storey over it was `Abs(3.30)`, stated in `structure` and nowhere near the
# sum of the two catalogue facts it claimed to be about (3.40 clear + 0.30 of
# lintel), so the clear height an ABSOLUTE said a carriage needs was quietly
# capped 0.40 m below it and the door came out square.
# ===========================================================================


def test_the_carriage_entrance_stands_on_a_real_jamb():
    slot_w = float(catalogue.carriage_slot_width())
    slot_h = float(catalogue.carriage_storey_height())
    geom = catalogue.carriage_entrance_in_slot(slot_w, slot_h)

    clear = float(catalogue.door_carriage_entrance().preferred)
    jamb = float(catalogue.carriage_jamb_width())
    assert geom.width == pytest.approx(clear), "the clear opening is no longer a carriage wide"
    assert geom.offset_x == pytest.approx(jamb), "no jamb on the left"
    assert slot_w - (geom.offset_x + geom.width) == pytest.approx(jamb), "no jamb on the right"
    assert geom.offset_x > 0.0


def test_the_storey_over_a_carriage_entrance_is_tall_enough_for_the_carriage():
    """The one ABSOLUTE on this facade that a body has to physically clear.

    Asserted end to end — through phase 1's storey stack and the base layer's
    entrance rule — because the defect was that the two disagreed, not that
    either was wrong on its own.
    """
    clear = float(catalogue.carriage_clear_height())
    heights = set()
    for klass in BuildingClass:
        for street_width in (10.0, 14.0, 20.0, 25.0):
            for year in (1830, 1865, 1900):
                grid = solve_structure(
                    _site(
                        klass=klass,
                        street_width=street_width,
                        year=year,
                        parcel_width=12.0,
                        ground=GroundProgramme.CARRIAGE,
                    )
                )
                ground = grid.storeys[0]
                assert ground.width >= clear + float(catalogue.lintel_bearing_depth()) - 1e-9, (
                    f"a {ground.width:.2f} m ground storey cannot hold a {clear:.2f} m "
                    "carriage entrance and the lintel over it"
                )
                door = [s for s in grid.bays if s.name == "porte_cochere"][0]
                geom = catalogue.carriage_entrance_in_slot(door.width, ground.width)
                heights.add(round(geom.height, 9))
    assert heights == {round(clear, 9)}, (
        f"the carriage entrance was capped below its own clear height: {heights}"
    )


def test_the_carriage_entrance_is_a_tall_arch_and_not_a_square_hole():
    """3.00 x 3.00 is a garage door. The opening has to be taller than it is
    wide, and it has to stay that shape across every class, because neither of
    the two numbers making it may scale."""
    slot_w = float(catalogue.carriage_slot_width())
    slot_h = float(catalogue.carriage_storey_height())
    geom = catalogue.carriage_entrance_in_slot(slot_w, slot_h)
    assert geom.aspect > 1.05, f"aspect {geom.aspect:.2f}: that is a square"
    assert geom.height == pytest.approx(float(catalogue.carriage_clear_height()))


# ===========================================================================
# A5.5 — the clear height is ABSOLUTE, so a storey that cannot give it refuses
#
# The height used to be `min(clear_height, slot_h - lintel)`. That `min` reads
# as prudence and is in fact the inversion of the project's central rule: an
# ABSOLUTE — a body that must physically pass — silently overruled by a
# PROPORTIONAL one, the storey height ambition and the règlement negotiated.
# The observable was 44/44 sampled doors at 3.00 x 3.00 m, 0.40 m short of the
# clear height the catalogue itself declares, with nothing raised anywhere.
# A door a carriage cannot pass is not a smaller door; it is not a door.
# ===========================================================================


def test_a_storey_too_short_for_a_carriage_refuses_instead_of_shortening_the_door():
    clear = float(catalogue.carriage_clear_height())
    lintel = float(catalogue.lintel_bearing_depth())
    slot_w = float(catalogue.carriage_slot_width())

    with pytest.raises(catalogue.CarriageCannotPass) as caught:
        catalogue.carriage_entrance_in_slot(slot_w, clear + lintel - 0.01)
    message = str(caught.value)
    # The refusal has to be usable: it names the height that was offered, the
    # height that is needed, and where to fix it — which is upstream.
    assert f"{clear:.2f}" in message and f"{clear + lintel:.2f}" in message
    assert "Raise the storey" in message


def test_the_storey_that_phase_1_builds_for_a_carriage_is_exactly_enough():
    """The boundary from the other side, so the two numbers cannot drift apart.

    ``carriage_storey_height`` is the smallest storey the catalogue accepts,
    to the last bit: one centimetre less refuses, and the value itself does
    not. If a later edit lowers the storey or raises the clear height without
    touching the other, this fails rather than the drawing quietly going wrong.
    """
    slot_w = float(catalogue.carriage_slot_width())
    storey = float(catalogue.carriage_storey_height())

    geom = catalogue.carriage_entrance_in_slot(slot_w, storey)
    assert geom.height == pytest.approx(float(catalogue.carriage_clear_height()))
    with pytest.raises(catalogue.CarriageCannotPass):
        catalogue.carriage_entrance_in_slot(slot_w, storey - 0.01)


def test_a_taller_storey_does_not_make_the_carriage_entrance_taller():
    """The refusal is not the whole claim. The height is the clear height
    flat — it neither shrinks with a short storey (it refuses) nor grows with
    a generous one, because the carriage did not get bigger either."""
    slot_w = float(catalogue.carriage_slot_width())
    clear = float(catalogue.carriage_clear_height())
    heights = {
        round(catalogue.carriage_entrance_in_slot(slot_w, slot_h).height, 9)
        for slot_h in (3.70, 4.00, 4.50, 5.20, 6.00)
    }
    assert heights == {round(clear, 9)}, f"the door followed the storey: {heights}"


def test_a_slot_too_narrow_for_a_carriage_refuses_too():
    """Horizontally the jamb gives way first — that is the stated position —
    but only down to the clear width. Below the narrowest opening a carriage
    can pass, the slot is refused for the same reason the short storey is."""
    narrowest = float(catalogue.door_carriage_entrance().minimum)
    clear = float(catalogue.door_carriage_entrance().preferred)
    storey = float(catalogue.carriage_storey_height())

    # A pinched slot: the jambs go, the opening stays passable, no refusal.
    pinched = catalogue.carriage_entrance_in_slot(clear + 0.40, storey)
    assert pinched.width == pytest.approx(clear)
    assert pinched.offset_x == pytest.approx(0.20)

    with pytest.raises(catalogue.CarriageCannotPass):
        catalogue.carriage_entrance_in_slot(narrowest - 0.01, storey)


def test_no_generated_carriage_entrance_is_ever_refused():
    """The refusal must be unreachable from a real site, or it is not a
    tripwire but a bug: phase 1 sizes both the slot and the storey from the
    same two catalogue facts. Swept over the situations, end to end."""
    for klass in BuildingClass:
        for parcel_width in (7.0, 9.0, 12.0, 18.0):
            for street_width in (8.0, 14.0, 20.0, 30.0):
                for year in (1830, 1865, 1900):
                    grid = solve_structure(
                        _site(
                            klass=klass,
                            street_width=street_width,
                            year=year,
                            parcel_width=parcel_width,
                            ground=GroundProgramme.CARRIAGE,
                        )
                    )
                    door = [s for s in grid.bays if s.name == "porte_cochere"][0]
                    # Raises on failure; that IS the assertion.
                    catalogue.carriage_entrance_in_slot(door.width, grid.storeys[0].width)


# ===========================================================================
# A6.1 — the two doors, at rule level
# ===========================================================================


def test_the_entrance_rule_fills_whichever_door_slot_phase_1_placed():
    """One rule, two doors. *Which* door was decided in the catalogue from the
    class and the street width; this rule reads the slot's name and never
    re-decides it, which is why there is no second place for the two answers
    to disagree."""
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        ctx = _ctx(
            slot_name=kind,
            role=Role.BASE,
            rank_from_principal=-1,
            slot_w=float(catalogue.entrance_slot_width(kind)),
            slot_h=float(catalogue.entrance_storey_height(kind)),
        )
        props = base_layer.entrance_fills_the_door_slot(ctx, RNG).values
        assert props["opening_type"] == catalogue.ENTRANCE_OPENING_TYPES[kind]
        assert props["opening_sill_height"] == pytest.approx(0.0)
        geom = catalogue.entrance_in_slot(kind, ctx.slot_w, ctx.slot_h)
        assert props["opening_width"] == pytest.approx(geom.width)
        assert props["opening_height"] == pytest.approx(geom.height)
        # ...and the shared expression of "what occupies this slot" agrees.
        assert base_layer.opening_type_for(ctx, RNG) == props["opening_type"]


def test_the_pedestrian_entrance_is_absolute_and_no_class_rule_resizes_it():
    """The twin of the carriage entrance's test. ``entrance_in_slot`` takes no
    class argument, so there is nowhere for ambition to enter even by
    accident."""
    kind = catalogue.ENTRANCE_PEDESTRIAN
    sizes = set()
    for klass in BuildingClass:
        ctx = _ctx(
            slot_name=kind,
            role=Role.BASE,
            rank_from_principal=-1,
            klass=klass,
            slot_w=float(catalogue.entrance_slot_width(kind)),
            slot_h=float(catalogue.entrance_storey_height(kind)),
        )
        vals = base_layer.entrance_fills_the_door_slot(ctx, RNG).values
        sizes.add((round(vals["opening_width"], 9), round(vals["opening_height"], 9)))
        # No class rule has an opinion about the door's size.
        for rule in klass_layer.CLASS_RULES:
            got = rule(ctx, RNG)
            if got is None:
                continue
            assert not ({"opening_width", "opening_height"} & set(got.values)), rule
    assert len(sizes) == 1, sizes


def test_a_short_storey_refuses_the_pedestrian_entrance_rather_than_shrinking_it():
    """A5.5's rule applied to the other door: a shrunken entrance stops being
    the ruler the facade is measured against, so the catalogue raises and the
    fix is upstream."""
    with pytest.raises(catalogue.EntranceCannotFit, match="clear height"):
        catalogue.pedestrian_entrance_in_slot(
            float(catalogue.pedestrian_slot_width()), 2.0
        )
    with pytest.raises(catalogue.EntranceCannotFit, match="two people"):
        catalogue.pedestrian_entrance_in_slot(1.0, 4.0)
    assert issubclass(catalogue.CarriageCannotPass, catalogue.EntranceCannotFit)


def test_the_wall_over_the_entrance_is_an_ordinary_window_wall():
    """Above the ground storey the entrance strip is the same window in the
    same wall as its neighbours, and the elements that attend a window are
    keyed to that fact rather than to the slot's name — which is what left the
    whole column over every door bare of architrave, keystone and railing."""
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        ctx = _ctx(slot_name=kind, role=Role.PRINCIPAL, rank_from_principal=0)
        assert base_layer.opening_type_for(ctx, RNG) == "window"
        assert base_layer.carries_an_ordinary_window(ctx, RNG)
        assert base_layer.surround_diminishes_with_rank(ctx, RNG) is not None
        assert base_layer.keystone_over_an_opening(ctx, RNG) is not None
        assert base_layer.garde_corps_where_a_body_could_fall(ctx, RNG) is not None


# ===========================================================================
# A6.6 / A6.7 at rule level
# ===========================================================================


def test_the_garde_corps_states_its_own_height_and_it_is_never_zero():
    """A6.6. The railing's height used to be borrowed from
    ``balcony_rail_height``, which exists only where the 1823 ordonnance
    permits a balcony — so every railing below 6 m drew nothing."""
    for level in (3.0, 4.2, 6.5, 12.0):
        ctx = _ctx(level_above_pavement=level, role=Role.MEZZANINE, rank_from_principal=-1)
        props = base_layer.garde_corps_where_a_body_could_fall(ctx, RNG)
        assert props is not None, level
        assert props.values["ironwork_height"] == pytest.approx(
            float(catalogue.sill_lean_height())
        )
        assert props.values["ironwork_height"] > 0.0
    assert "ironwork_height" in PROPERTY_KEYS


def test_the_ground_floors_surround_comes_from_the_ground_floor_not_the_ladder():
    """A6.7. A shop light is framed by the devanture; an ordinary
    ground-floor window by a plain band of stone. Neither takes a pediment,
    and the class layer's affordability ladder — which is what put one there —
    declines to bid on the base storey at all."""
    shop = _ctx(role=Role.BASE, rank_from_principal=-2, ground=GroundProgramme.SHOP)
    hall = _ctx(role=Role.BASE, rank_from_principal=-2, ground=GroundProgramme.RESIDENTIAL)
    assert base_layer.opening_type_for(shop, RNG) == "shop_bay"
    got = base_layer.ground_floor_surround_is_the_ground_floor_s_own(shop, RNG).values
    assert got["surround_kind"] == catalogue.ground_floor_surround("shop_bay")
    assert got["surround_kind"] != "pedimented"
    got = base_layer.ground_floor_surround_is_the_ground_floor_s_own(hall, RNG).values
    assert got["surround_kind"] == catalogue.ground_floor_surround("window")
    assert got["surround_kind"] != "pedimented"
    for klass in BuildingClass:
        for ctx in (shop, hall):
            assert (
                klass_layer.surround_is_what_the_owner_could_afford(
                    dataclasses.replace(ctx, klass=klass), RNG
                )
                is None
            ), "the affordability ladder must not reach the ground storey"


# ===========================================================================
# A7.4 — the devanture's head is dated, not hard-coded
# ===========================================================================


def test_a_shop_bay_can_carry_a_segmental_or_round_head():
    """A6.8 drew a shop bay's ``head`` prop correctly, but
    ``ground_floor_of_a_shop`` hard-coded ``opening_head='flat'`` and nothing
    could ever produce anything else — so the branch A6.8 wired up was dead
    code, unreachable by any site. Sweeping years, classes and seeds must
    reach every head form the vocabulary and the shopfront chronology
    together allow, or the contract's premise is still false."""
    seen: set[str] = set()
    for year in (1800, 1830, 1850, 1860, 1870, 1880, 1885, 1895, 1905, 1915):
        for klass in BuildingClass:
            for seed in range(6):
                ctx = _ctx(
                    role=Role.BASE,
                    ground=GroundProgramme.SHOP,
                    year=year,
                    klass=klass,
                )
                got = base_layer.ground_floor_of_a_shop(ctx, DecisionStream(seed))
                assert got is not None
                seen.add(got.values["opening_head"])
    assert seen == {"flat", "segmental", "round"}, (
        f"only reached {sorted(seen)} — the shop head branch must be reachable, "
        "not just re-hard-coded to a different constant"
    )


def test_a_shop_bay_s_head_form_is_valid_vocabulary():
    """Whatever era supplies it, the value is one ``draw_opening`` (and the
    ``opening_head`` vocabulary in ``qualify.context``) actually knows."""
    for year in (1780, 1800, 1850, 1885, 1910, 1920):
        ctx = _ctx(role=Role.BASE, ground=GroundProgramme.SHOP, year=year)
        got = base_layer.ground_floor_of_a_shop(ctx, RNG)
        assert got.values["opening_head"] in ("flat", "segmental", "round", "irregular")


def test_a_shop_bay_falls_back_to_flat_before_any_devanture_chronology():
    """A date before the shopfront catalogue's own ``OPEN_FRONT_YEAR`` has no
    era to read — no opinion, not a crash, and not a lie about which era
    supplied the value."""
    assert not chronology.available("shopfront", 1700, BuildingClass.ORDINARY)
    ctx = _ctx(role=Role.BASE, ground=GroundProgramme.SHOP, year=1700)
    got = base_layer.ground_floor_of_a_shop(ctx, RNG)
    assert got.values["opening_head"] == "flat"


def test_the_shop_head_is_dated_the_same_way_every_other_fashion_axis_is():
    """Not a period test in disguise: the function reads
    ``chronology.available``, exactly like ``period.shopfront_of_its_date``
    reads it for the pane span, rather than branching on a year it has
    inlined."""
    import inspect

    src = inspect.getsource(base_layer._shop_opening_head)
    assert "chronology.available" in src
    assert "if ctx.year" not in src and "ctx.year >" not in src and "ctx.year <" not in src


# ===========================================================================
# A7.2 — the density of ornament is a proportional quantity, so it moves
# ===========================================================================


_ORNAMENT_MODULE_KEYS = (
    "ornament_modillion_module",
    "ornament_dentil_module",
    "ornament_course_width",
    "ornament_course_height",
    "ornament_bracket_module",
    "ornament_ironwork_module",
)


def test_every_ornament_module_is_stated_by_both_layers_that_own_the_dial():
    """The base layer sets the ornament density and the class layer restates
    it with money in it. Whichever wins, a consumer must find the rhythm as
    well as the dial — a density with no module is a number nothing can be
    counted from, and that gap is exactly where the renderer used to put its
    own spacing."""
    ctx = _ctx()
    for rule in (
        base_layer.ornament_diminishes_with_rank,
        klass_layer.ornament_density_scales_with_money,
    ):
        got = rule(ctx, RNG).values
        assert "ornament_density" in got
        for key in _ORNAMENT_MODULE_KEYS:
            assert key in got, f"{rule.__name__} states no {key}"
            assert float(got[key]) > 0.0


def test_a_richer_building_is_worked_more_finely_not_just_bigger():
    """The brief's own list puts "the scale and density of ornament" among
    the PROPORTIONAL quantities. So the repeat interval of every rhythm on
    the frontage must shorten as ambition rises — a grand cornice carries
    more modillions per metre than a modest one, and not merely longer ones.

    Ordering only; the figures themselves are INFERRED.
    """
    ladder = [BuildingClass.MODEST, BuildingClass.ORDINARY,
              BuildingClass.COMFORTABLE, BuildingClass.GRAND]
    modules = [
        klass_layer.ornament_density_scales_with_money(_ctx(klass=k), RNG).values
        for k in ladder
    ]
    for key in _ORNAMENT_MODULE_KEYS:
        series = [float(m[key]) for m in modules]
        assert series == sorted(series, reverse=True), f"{key} does not tighten: {series}"
        assert series[0] > series[-1] * 1.15, (
            f"{key} barely moves between a modest and a grand frontage: {series}"
        )


def test_ornament_thins_out_away_from_the_principal_floor_too():
    """The same dial, on the other axis. Rank is what makes an attic quieter
    than the étage noble of the same building, and a rhythm that ignored it
    would put the noble floor's coursing on the storey nobody looks at."""
    modules = [
        klass_layer.ornament_density_scales_with_money(
            _ctx(rank_from_principal=rank), RNG
        ).values
        for rank in (0, 1, 2, 3)
    ]
    for key in _ORNAMENT_MODULE_KEYS:
        series = [float(m[key]) for m in modules]
        assert series == sorted(series), f"{key} does not coarsen with rank: {series}"


def test_the_baluster_gap_is_not_one_of_the_things_money_moves():
    """The instructive pair, asserted rather than asserted-in-a-comment. The
    ornament hung on a railing is PROPORTIONAL and moves; the gap between its
    bars is ABSOLUTE — a child's head — and does not. A single "railing
    density" would have quietly merged the two."""
    ornament = {
        k: float(
            klass_layer.ornament_density_scales_with_money(_ctx(klass=k), RNG)
            .values["ornament_ironwork_module"]
        )
        for k in BuildingClass
    }
    gaps = {
        k: base_layer.garde_corps_where_a_body_could_fall(
            _ctx(klass=k, role=Role.UPPER, rank_from_principal=1), RNG
        ).values["ironwork_gap_max"]
        for k in BuildingClass
    }
    assert len(set(ornament.values())) == len(BuildingClass)
    assert len(set(gaps.values())) == 1


def test_a_module_and_a_length_become_a_count_in_exactly_one_place():
    """``catalogue.repeats_across`` is the whole of the arithmetic A7.2 moved
    upstream, so it is worth pinning: more length is more repeats, a finer
    module is more repeats, and a module of nothing degrades to the stated
    minimum instead of dividing by zero."""
    assert catalogue.repeats_across(10.0, 0.5) == 20
    assert catalogue.repeats_across(20.0, 0.5) > catalogue.repeats_across(10.0, 0.5)
    assert catalogue.repeats_across(10.0, 0.25) > catalogue.repeats_across(10.0, 0.5)
    assert catalogue.repeats_across(10.0, 0.0, minimum=3) == 3
    assert catalogue.repeats_across(0.0, 0.5, minimum=2) == 2


def test_the_roof_seam_is_the_covering_s_own_fact_and_never_scales():
    """A zinc table is as wide as the works rolled it. That is ABSOLUTE, and
    it is why the seam module is the one member of this family that is not on
    the ornament dial at all."""
    from buildings.quantity import Kind

    zinc = catalogue.roof_seam_module("zinc_roofing")
    slate = catalogue.roof_seam_module("slate")
    assert zinc.kind is Kind.ABSOLUTE and slate.kind is Kind.ABSOLUTE
    assert float(zinc) < float(slate), "zinc's standing seams are the denser rhythm"
    assert catalogue.roof_seam_module(None) == slate


# ===========================================================================
# A7.5 — a special bay varies up the facade
# ===========================================================================


def _special_column_for(storey_count: int, seed: int, bay: int) -> list[str]:
    rng = DecisionStream(seed)
    ctx = _ctx(
        slot_name="special",
        is_edge_special=True,
        storey_count=storey_count,
        index_from_bottom=storey_count - 1,
        index_from_top=0,
        storeys_within_comble=0,
        bay_index_from_left=bay,
    )
    return base_layer._special_column(ctx, rng)


def test_a_special_column_never_repeats_itself_more_than_twice():
    """A7.5. A6.2's letter held — never *all* storeys — and its spirit did
    not: nearly a third of special columns still read as a near-full stack of
    one element, worst case four blind panels running under a single
    oeil-de-boeuf. Two of anything is a pair; three is a wall."""
    worst = 0
    for storey_count in range(2, 9):
        for seed in range(60):
            for bay in range(3):
                column = _special_column_for(storey_count, seed, bay)
                run = best = 1
                for a, b in zip(column, column[1:]):
                    run = run + 1 if a == b else 1
                    best = max(best, run)
                assert best <= 2, f"{storey_count} storeys, seed {seed}: {column}"
                worst = max(worst, best)
    assert worst == 2, "the cap is never actually reached — the sweep proves nothing"


def test_capping_the_run_does_not_take_the_ground_storey_s_answer_away():
    """The strip beside a devanture is solid wall, and that is a fact about
    what is behind it rather than a coin the cap may flip. It is also the one
    storey offered a single answer, so the cap has to leave it alone instead
    of failing to find an alternative."""
    for storey_count in range(2, 7):
        for seed in range(40):
            assert _special_column_for(storey_count, seed, 0)[0] == "blind_panel"


def test_the_top_of_the_wall_is_never_blank_however_the_run_was_capped():
    """A6.2's own claim, re-asserted under A7.5's rewrite: the cap chooses
    from the storey's OWN vocabulary, so it can never introduce a form that
    storey does not offer."""
    for storey_count in range(2, 9):
        for seed in range(60):
            top = _special_column_for(storey_count, seed, 1)[-1]
            assert top in ("oeil_de_boeuf", "narrow_window")


def test_the_column_is_the_same_column_however_often_it_is_asked():
    """``_special_feature`` is called by every rule that needs to know what a
    slot carries, and each call now replays the whole column. That is only
    safe because the draws are keyed on ``(seed, path)`` and re-asking is
    free and identical."""
    first = _special_column_for(6, 11, 2)
    for _ in range(4):
        assert _special_column_for(6, 11, 2) == first


# ===========================================================================
# A13 — the entresol belongs to the base, not to the upper facade
# ===========================================================================
#
# Two Deuxième Classe plates of 1864, both by Paul Mesnard, both with a
# measured 4.00 + 3.10 base:
#
#   77 bd de Sébastopol   the devanture spans both levels as one framework and
#                         there is no entresol band on the facade at all
#   120 bd de Sébastopol  the entresol is its own band and belongs to the base:
#                         arched openings in the ground floor's own coursing,
#                         on the shopfront's entablature, with small railings
#
# Same year, same class, same architect, same stack — so what follows asserts
# that BOTH are reachable and that neither is keyed to a date or a class.


_A13_SITE = dict(
    street_width=22.0,
    parcel_width=14.0,
    parcel_depth=18.0,
    year=1865,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
)


def _a13_rows(seed: int):
    """The qualified grid of a commercial boulevard frontage with an entresol,
    as ``(contexts, resolutions)`` per storey."""
    site = _site(seed=seed, **_A13_SITE)
    roled = assign_roles(solve_structure(site))
    assert any(s.role is Role.MEZZANINE for s in roled.storeys), (
        "this situation was chosen because a shop ground floor buys an entresol"
    )
    layers = compose_module.paris_layers()
    rows = []
    for row in contexts_for(roled, site):
        rng = DecisionStream(site.seed)
        rows.append((row, [compose_module.resolve(ctx, layers, rng) for ctx in row]))
    return rows


def _a13_storey(rows, role: Role):
    for row, res in rows:
        if row[0].role is role:
            return row, res
    raise AssertionError(f"no {role} storey in the fixture")


def _a13_head_forms(seeds=range(24)) -> dict[str, int]:
    counted: dict[str, int] = {}
    for seed in seeds:
        rows = _a13_rows(seed)
        row, res = _a13_storey(rows, Role.MEZZANINE)
        form = res[0].get("entresol_head_form")
        counted[form] = counted.get(form, 0) + 1
    return counted


# --- A13.1: the commercial base is RdC + entresol ---------------------------


def test_the_socle_runs_through_the_entresol():
    """A13.1. The socle used to stop at the ceiling of the rez-de-chaussée,
    which left the entresol standing on plain wall with a shrunken window in
    it — a short *residential* storey. It is the top of the commercial base,
    and on both Daly plates it is faced in the base's own stone."""
    for seed in range(6):
        rows = _a13_rows(seed)
        _base_row, base_res = _a13_storey(rows, Role.BASE)
        _mezz_row, mezz_res = _a13_storey(rows, Role.MEZZANINE)
        assert base_res[0].get("socle_present") is True
        assert mezz_res[0].get("socle_present") is True, (
            f"seed {seed}: the entresol has no socle — the base stops short of it"
        )
        # ...and it is the SAME stone, not a second mason's.
        assert mezz_res[0].get("socle_treatment") == base_res[0].get("socle_treatment")


def test_the_base_block_is_the_rez_de_chaussee_and_the_entresol_over_it():
    """The context fact the rules read, asserted against the roled stack it is
    derived from rather than against a floor number."""
    site = _site(seed=3, **_A13_SITE)
    roled = assign_roles(solve_structure(site))
    block = [s for s in roled.storeys if s.role in (Role.BASE, Role.MEZZANINE)]
    top = max(s.slot.start + s.slot.width for s in block)
    for row in contexts_for(roled, site):
        ctx = row[0]
        assert ctx.storeys_in_the_base_block == len(block) == 2
        assert ctx.has_an_entresol
        assert ctx.base_block_top == pytest.approx(top)
        assert ctx.stands_in_the_base_block == (
            ctx.role in (Role.BASE, Role.MEZZANINE)
        )


def test_the_course_that_crowns_the_base_is_the_emphatic_one():
    """A13.1's stated inversion, fixed and asserted as an ORDERING — never as
    a number. The line that divides commerce from residence is the strongest
    horizontal on the lower facade; the line inside the base, between a shop
    and its own mezzanine, is the thin one."""
    rows = _a13_rows(3)
    _mezz_row, mezz_res = _a13_storey(rows, Role.MEZZANINE)
    crowning = [
        res[0]
        for row, res in rows
        if row[0].crowns_the_base_block and res[0].get("string_course_present")
    ]
    assert len(crowning) == 1, "exactly one line crowns the commercial base"
    inside = float(mezz_res[0].get("string_course_projection"))
    crown = float(crowning[0].get("string_course_projection"))
    assert crown > inside, (
        f"the base's crowning course ({crown:.3f} m) is not deeper than the "
        f"line inside the base ({inside:.3f} m)"
    )
    assert crowning[0].get("string_course_kind") == "entablature"


def test_the_crowning_course_is_a_level_and_follows_the_entresol_out_of_the_stack():
    """The same discipline as ``balcony_ordonnance_1823``: the rule reads a
    height above the pavement, so deleting the entresol drops the line to the
    top of the ground floor with no rule edited. ``_grid`` supplies the two
    stacks; the roles, the contexts and the rules are all the real ones."""
    site = _site(ground=GroundProgramme.SHOP)
    bays = [0.5, 3.0, 3.0, 3.0, 3.0, 0.5]
    seen = {}
    for name, heights in (("with", WITH_MEZZANINE), ("without", WITHOUT_MEZZANINE)):
        roled = assign_roles(_grid(heights, bays))
        levels = [
            ctx.base_block_top
            for ctx in storey_contexts_for(roled, site)
            if ctx.crowns_the_base_block
        ]
        assert len(levels) == 1, f"{name}: {levels}"
        seen[name] = levels[0]
    assert seen["with"] == pytest.approx(WITH_MEZZANINE[0] + WITH_MEZZANINE[1])
    assert seen["without"] == pytest.approx(WITHOUT_MEZZANINE[0])
    assert seen["without"] < seen["with"]


# --- A13.2: the entresol gets its own opening treatment --------------------


def test_both_of_dalys_entresol_head_forms_are_reachable():
    """A17.2. What actually varies between the two plates is the head the
    entresol's lights are turned with — square at 77 bd de Sébastopol,
    *arc surbaissé* at 120. Neither is the norm and the other an exception;
    both are Deuxième Classe of 1864 on the same boulevard."""
    counted = _a13_head_forms()
    assert set(counted) == {"flat", "segmental"}, counted
    assert min(counted.values()) >= 4, f"one form is barely reachable: {counted}"


def test_the_entresol_form_is_not_keyed_to_the_date_or_the_class():
    """The property this whole mechanism exists for: one year, one class, one
    street — and the frontages still differ, because the choice runs through
    ``DecisionStream`` and not through a period or a price."""
    counted = _a13_head_forms()
    assert len(counted) == 2, (
        "every frontage of 1865, comfortable class, on a 22 m boulevard came "
        f"out the same way: {counted}"
    )


def test_the_entresol_form_is_addressable_on_a_stable_path():
    """It has to be pinnable, or it cannot be argued with later. The path is
    per FRONTAGE — a building has one entresol and one mason — so it is
    stable under adding storeys and bays."""
    ctx = _ctx(role=Role.MEZZANINE, slot_name="bay", ground=GroundProgramme.SHOP)
    for seed in range(30):
        rng = DecisionStream(seed)
        drawn = rng.choice("facade/entresol/head", ["flat", "segmental"])
        assert base_layer.entresol_head_form(ctx, rng) == drawn
    # ...and re-asking is free and identical, because the stream is keyed on
    # (seed, path) and nothing here consumes a cursor.
    rng = DecisionStream(5)
    first = base_layer.entresol_head_form(ctx, rng)
    assert all(base_layer.entresol_head_form(ctx, rng) == first for _ in range(4))


def test_the_devanture_stops_at_the_rez_de_chaussee():
    """A17.2, as the thing it forbids. A13 had the shopfront framework span
    the rez-de-chaussée and the entresol as one object, sourced to plate 77.
    The plate does not show that: the devanture closes at a full-width
    entablature and the entresol above it is a separate register in the
    stone. So no storey above the base is ever faced by the framework, on any
    seed and any glazed programme."""
    for ground in (GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE):
        for seed in range(8):
            rng = DecisionStream(seed)
            base = _ctx(role=Role.BASE, slot_name="bay", ground=ground)
            mezz = _ctx(role=Role.MEZZANINE, slot_name="bay", ground=ground)
            assert base_layer.devanture_faces(base, rng)
            assert not base_layer.devanture_faces(mezz, rng), (
                f"{ground.value}/{seed}: the devanture reached the entresol"
            )


def test_an_entresol_never_carries_a_shrunken_upper_floor_window():
    """A13.2's complaint, as the thing it forbids. Whichever form the frontage
    takes, the entresol's opening is not an ordinary window sitting on the
    lean-on sill of the storeys above it."""
    lean = float(catalogue.sill_lean_height())
    for seed in range(12):
        rows = _a13_rows(seed)
        row, res = _a13_storey(rows, Role.MEZZANINE)
        lit = [
            (ctx, r)
            for ctx, r in zip(row, res)
            if r.get("opening_type") in ("window", "shop_bay")
        ]
        assert lit, f"seed {seed}: the entresol has no openings at all"
        for ctx, r in lit:
            assert float(r.get("opening_sill_height")) != pytest.approx(lean), (
                f"seed {seed}, slot {ctx.slot_name!r}: the entresol light stands "
                "on the same sill as an upper-floor window"
            )


def test_the_entresol_over_a_shop_is_its_own_register_of_windows():
    """A17.2, and the guard against A13's error coming back. Both plates show
    the same arrangement: over the devanture's entablature the entresol is a
    separate register in the base's stone, with its own short lights standing
    on a low *allège* — not glass in the shopfront's framework.

    Stated over every seed rather than one, because the reading A13 invented
    was reachable half the time."""
    lean = float(catalogue.sill_lean_height())
    allege = float(catalogue.entresol_allege_height())
    for seed in range(12):
        rows = _a13_rows(seed)
        _base_row, base_res = _a13_storey(rows, Role.BASE)
        _mezz_row, mezz_res = _a13_storey(rows, Role.MEZZANINE)
        shops = [i for i, r in enumerate(base_res) if r.get("opening_type") == "shop_bay"]
        assert shops, f"seed {seed}: the fixture's ground floor sells nothing"
        for i in shops:
            # A window in stone, not the upper half of a devanture.
            assert mezz_res[i].get("opening_type") == "window", (
                f"seed {seed} slot {i}: the devanture absorbed the entresol again"
            )
            assert not mezz_res[i].get("shopfront_present")
            # Standing on the low allège — which is A13.2's real complaint,
            # and the half of it that survives: not the lean-on sill of the
            # storeys above, and not the zero sill of a shopfront either.
            sill = float(mezz_res[i].get("opening_sill_height"))
            assert sill == pytest.approx(allege), f"seed {seed} slot {i}: sill {sill}"
            assert sill < lean
            # ...and the RdC keeps its own soubassement, one storey down.
            assert float(base_res[i].get("opening_sill_height")) == pytest.approx(
                float(catalogue.shop_threshold_height())
            )


def test_the_arcaded_entresol_is_an_arch_in_the_bases_own_stone():
    """120 bd de Sébastopol. Its own band, and it belongs to the base: an
    *arc surbaissé* in the ground floor's coursing, on a low allège, with a
    small individual railing across the light."""
    seed = next(s for s in range(24) if _a13_head_forms([s]).get("segmental"))
    rows = _a13_rows(seed)
    row, res = _a13_storey(rows, Role.MEZZANINE)
    lit = [(ctx, r) for ctx, r in zip(row, res) if r.get("opening_type") == "window"]
    assert lit, "the arcaded entresol has no lights"
    for ctx, r in lit:
        assert r.get("opening_head") == "segmental", ctx.slot_name
        assert float(r.get("opening_sill_height")) == pytest.approx(
            float(catalogue.entresol_allege_height())
        )
        assert r.get("ironwork_present") is True
        # In the base's own stone, and framed by the base's own vocabulary —
        # never by the ladder of stone architraves the residential storeys
        # climb (A6.7's reasoning, widened to the block by A13.1).
        assert r.get("socle_present") is True
        assert r.get("surround_kind") != "pedimented"


def test_the_arcade_stops_under_the_band_that_crowns_the_base():
    """An arch whose head runs up behind its own entablature is an arch drawn
    through its own cornice. Both rules read ``base_entablature_depth``, so
    the two lines meet instead of crossing.

    Swept over seeds rather than pinned to one, because since A17.2 the
    entresol always has its own lights and both head forms have to clear the
    band — the segmental one by its rise, the square one by its lintel."""
    for seed in range(12):
        rows = _a13_rows(seed)
        row, res = _a13_storey(rows, Role.MEZZANINE)
        for ctx, r in zip(row, res):
            if r.get("opening_type") != "window":
                continue
            head = (
                ctx.level_above_pavement
                + float(r.get("opening_sill_height"))
                + float(r.get("opening_height"))
            )
            crown = ctx.base_block_top - base_layer.base_entablature_depth(ctx)
            assert head <= crown + 1e-9, (
                f"seed {seed}: the arch head reaches {head:.3f} m; the "
                f"entablature starts at {crown:.3f} m"
            )


# ===========================================================================
# A14 — the two-storey arched entrance
# ===========================================================================
#
# Four of Daly's sixteen buildings put the entrance under one round-headed
# arch spanning the rez-de-chaussée and the entresol:
#
#   Avenue de l'Impératrice (Raban)    porte cochère    2.62 x 7.30   RdC 4.30
#   39 rue Neuve des Mathurins         porte cochère    2.57 x 5.00   RdC 4.10
#   2 et 4 bd de Sébastopol (Davioud)  porte piétonne   1.74 x 5.01   RdC 3.42
#   87 bd de Sébastopol                porte piétonne   1.76 x 5.07
#
# against one-storey medians of 3.49 m (cochère) and 3.03 m (piétonne). All
# four are 1864; two are Première and two Deuxième; two are carriage and two
# pedestrian. So what follows asserts that the form is reachable for BOTH
# entrance kinds, that it is a draw rather than a table, and — the load-bearing
# one — that the WIDTH did not move.


#: The same commercial boulevard situation A13 uses, because A14 has to
#: compose with A13 and the cheapest way to prove that is to test it on the
#: same frontage. A narrower parcel on a narrower street takes the pedestrian
#: door instead: 11 m is under the 12 m a carriage needs to turn in off the
#: roadway, so ``entrance_for`` gives a porte piétonne however comfortable the
#: household, while a shop below still buys the entresol the arch rises
#: through.
_A14_PEDESTRIAN_SITE = dict(
    street_width=11.0,
    parcel_width=9.0,
    parcel_depth=15.0,
    year=1865,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
)


def _a14_rows(seed: int, site_over=None):
    site = _site(seed=seed, **(site_over if site_over is not None else _A13_SITE))
    roled = assign_roles(solve_structure(site))
    assert any(s.role is Role.MEZZANINE for s in roled.storeys)
    layers = compose_module.paris_layers()
    rows = []
    for row in contexts_for(roled, site):
        rng = DecisionStream(site.seed)
        rows.append((row, [compose_module.resolve(ctx, layers, rng) for ctx in row]))
    return rows


def _a14_entrance_cell(rows, role: Role):
    """The (ctx, resolution) of the entrance slot on the storey of ``role``."""
    row, res = _a13_storey(rows, role)
    for ctx, r in zip(row, res):
        if ctx.slot_name in catalogue.ENTRANCE_SLOT_NAMES:
            return ctx, r
    raise AssertionError("this frontage has no entrance slot")


def _a14_forms(seeds=range(24), site_over=None) -> dict[object, int]:
    counted: dict[object, int] = {}
    for seed in seeds:
        _ctx_, res = _a14_entrance_cell(_a14_rows(seed, site_over), Role.BASE)
        form = res.get("entrance_arch_register")
        counted[form] = counted.get(form, 0) + 1
    return counted


def _a14_two_storey_seed(site_over=None) -> int:
    for seed in range(64):
        _ctx_, res = _a14_entrance_cell(_a14_rows(seed, site_over), Role.BASE)
        if res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_LEAVES:
            return seed
    raise AssertionError("no seed in 64 produced a two-storey arch")


def _a14_one_storey_seed(site_over=None) -> int:
    for seed in range(64):
        _ctx_, res = _a14_entrance_cell(_a14_rows(seed, site_over), Role.BASE)
        if res.get("entrance_arch_register") is None:
            return seed
    raise AssertionError("no seed in 64 produced a one-storey entrance")


# --- A14.1: the width does not move ----------------------------------------


def test_a_tall_arch_is_not_a_wide_one():
    """**The single assertion A14.1 asks for by name.**

    Daly's tall carriage arches are 2.57 and 2.62 m; his one-storey ones are
    2.41-2.67. His tall pedestrian doors are 1.74 and 1.76; the one-storey
    ones 1.36-1.91. The tall form sits squarely inside the ordinary width band
    in both kinds, so the two-storey arch is a compositional decision about
    HEIGHT taken against an ABSOLUTE width — and getting this wrong would undo
    A9.2, which is the best-evidenced result in the project.

    Checked against the one-storey geometry directly, for every class, so that
    no accident of a particular frontage can hide a divergence.
    """
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        slot_w = float(catalogue.entrance_slot_width(kind))
        base_h = float(catalogue.entrance_storey_height(kind))
        one_storey = catalogue.entrance_in_slot(kind, slot_w, base_h)
        for entresol_h in (2.40, 2.66, 2.90, 3.10):
            arch = catalogue.two_storey_entrance_arch(
                kind, slot_w, base_h, entresol_h, crown_below=0.30
            )
            assert arch.clear_width == one_storey.width, (
                f"{kind}: the two-storey arch is {arch.clear_width:.4f} m wide and "
                f"the one-storey door {one_storey.width:.4f} m — a tall arch is "
                "not a wide one (A14.1)"
            )
            assert arch.offset_x == one_storey.offset_x, (
                f"{kind}: the arch moved off its jambs"
            )
            assert arch.leaves_height == one_storey.height, (
                f"{kind}: the leaves grew with the arch; what passes through the "
                "gate did not change"
            )


def test_the_arch_is_taller_than_the_door_it_replaces_and_by_daly_s_margin():
    """The height DOES move, and by roughly the factor Daly measured: a
    two-storey arch is most of twice a one-storey door.

    Asserted as a band rather than a value. Daly's four clear heights over
    their widths are 2.79, 1.95, 2.88 and 2.88; the generator's storeys are
    not Daly's storeys, so what is contractual is that the tall form lands
    inside the observed aspect band and well clear of the one-storey door.
    """
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        slot_w = float(catalogue.entrance_slot_width(kind))
        base_h = float(catalogue.entrance_storey_height(kind))
        one_storey = catalogue.entrance_in_slot(kind, slot_w, base_h)
        arch = catalogue.two_storey_entrance_arch(
            kind, slot_w, base_h, 2.66, crown_below=0.60
        )
        assert arch.clear_height > one_storey.height * 1.4
        assert 1.9 <= arch.clear_height / arch.clear_width <= 3.7, (
            f"{kind}: aspect {arch.clear_height / arch.clear_width:.2f} is outside "
            "the band Daly's four tall arches span"
        )


def test_the_head_is_round_and_its_rise_is_half_the_span():
    """A14.1: "the head is round; that is what makes the form". A semicircle
    turned on a span rises half of it — not a number anybody may argue with,
    which is why it is stated rather than left to the drawing."""
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        slot_w = float(catalogue.entrance_slot_width(kind))
        arch = catalogue.two_storey_entrance_arch(
            kind, slot_w, float(catalogue.entrance_storey_height(kind)),
            2.90, crown_below=0.30,
        )
        assert arch.head_rise == pytest.approx(arch.clear_width / 2.0)
        assert arch.springing_above_pavement == pytest.approx(
            arch.clear_height - arch.clear_width / 2.0
        )


def test_an_entresol_too_short_to_turn_the_head_in_refuses_rather_than_flattening():
    """A5.5, applied to the head. The width is ABSOLUTE, so the rise of a
    round head is ABSOLUTE too: an entresol that cannot contain the semicircle
    cannot have the arch flattened to fit, because a flattened arch is a
    different form. The honest answer is the one-storey door."""
    kind = catalogue.ENTRANCE_CARRIAGE
    slot_w = float(catalogue.entrance_slot_width(kind))
    base_h = float(catalogue.carriage_storey_height())
    rise = float(catalogue.door_carriage_entrance().preferred) / 2.0
    with pytest.raises(catalogue.EntranceCannotFit):
        catalogue.two_storey_entrance_arch(
            kind, slot_w, base_h, rise * 0.5, crown_below=0.30
        )
    assert not catalogue.two_storey_entrance_arch_fits(
        kind, slot_w, base_h, rise * 0.5, crown_below=0.30
    )
    assert catalogue.two_storey_entrance_arch_fits(
        kind, slot_w, base_h, rise + 0.31, crown_below=0.30
    )


def test_the_two_storey_arch_takes_no_class_argument_anywhere():
    """The same absence ``entrance_in_slot`` has, and for the same reason:
    this is the opening money may not touch. A14 adds a height decision to it
    and must not smuggle a class in with it."""
    import inspect

    for fn in (
        catalogue.two_storey_entrance_arch,
        catalogue.two_storey_entrance_arch_fits,
        catalogue.round_arch_rise,
    ):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"klass", "class_", "building_class"}, fn.__name__


# --- A14.2: how it is chosen -----------------------------------------------


def test_both_heights_are_reachable_and_neither_is_the_only_one():
    """A14.2. It is a draw, so the corpus of seeds must show both outcomes —
    a form nothing can reach is a form the generator does not have, and a form
    everything reaches is not a decision."""
    counted = _a14_forms()
    assert counted.get(catalogue.ENTRANCE_ARCH_LEAVES, 0) > 0, (
        "no seed produced a two-storey arch"
    )
    assert counted.get(None, 0) > 0, "every seed produced a two-storey arch"


def test_the_tall_arch_is_the_minority_form():
    """The rate is **INFERRED** — Daly's 4 of 16 with a known publication bias,
    n = 16 — so this asserts the ORDERING and not the number: the two-storey
    arch is the rarer of the two. Pinning 0.25 here would dress an observation
    as a calibration."""
    counted = _a14_forms(seeds=range(48))
    tall = counted.get(catalogue.ENTRANCE_ARCH_LEAVES, 0)
    plain = counted.get(None, 0)
    assert 0 < tall < plain, f"{tall} tall against {plain} one-storey"


def test_the_choice_is_not_keyed_to_date_or_class_or_entrance_kind():
    """All four of Daly's are 1864; two are Première and two Deuxième; two are
    carriage and two pedestrian. So the same seed must give the same answer
    across dates and classes — the decision is variation *within* a class and
    a period, which is what ``DecisionStream`` is for."""
    seed = _a14_two_storey_seed()
    for year in (1855, 1865, 1875):
        for klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
            over = dict(_A13_SITE, year=year, klass=klass)
            _c, res = _a14_entrance_cell(_a14_rows(seed, over), Role.BASE)
            assert res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_LEAVES, (
                f"the tall arch vanished at {year} / {klass.value}"
            )
    # ...and it is reachable on the pedestrian door too, which is the half of
    # the evidence a carriage-only implementation would have thrown away.
    _c, res = _a14_entrance_cell(
        _a14_rows(_a14_two_storey_seed(_A14_PEDESTRIAN_SITE), _A14_PEDESTRIAN_SITE),
        Role.BASE,
    )
    assert res.get("opening_type") == "pedestrian_entrance"
    assert res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_LEAVES


def test_the_decision_path_is_stable_under_adding_storeys():
    """A path per FRONTAGE, like A13.2's. Change the parcel depth — which
    moves the comble and nothing about the entrance — and the answer must not
    move, or the decision cannot be pinned in a test or argued with later."""
    seed = _a14_two_storey_seed()
    for depth in (16.0, 18.0, 22.0):
        over = dict(_A13_SITE, parcel_depth=depth)
        _c, res = _a14_entrance_cell(_a14_rows(seed, over), Role.BASE)
        assert res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_LEAVES


def test_a_frontage_with_no_entresol_is_never_offered_the_form():
    """A14.1: the arch spans the base and the entresol. Where the base block
    is the rez-de-chaussée alone there is nothing for it to rise through, and
    a coin is not spent on a question the frontage cannot answer."""
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        ctx = _ctx(
            slot_name=kind,
            role=Role.BASE,
            rank_from_principal=-1,
            slot_w=float(catalogue.entrance_slot_width(kind)),
            slot_h=float(catalogue.entrance_storey_height(kind)),
        )
        assert ctx.has_an_entresol is False
        assert base_layer.entrance_arch_form_for(ctx, RNG) is None
        assert base_layer.two_storey_arch_at(ctx, RNG) is None
        # ...and the ordinary one-storey rule still fills the slot.
        assert base_layer.entrance_fills_the_door_slot(ctx, RNG) is not None


# --- A14.1/A14.2: what the two registers say --------------------------------


def test_the_entresol_of_a_tall_arch_is_inside_the_arch_and_not_beside_it():
    """A14.1's own words, less the half A20.1 retracted. The entresol cell of
    that bay carries the arch's own head — not a separate window standing next
    to the door — and carries NOTHING across it."""
    for over in (_A13_SITE, _A14_PEDESTRIAN_SITE):
        rows = _a14_rows(_a14_two_storey_seed(over), over)
        ctx, res = _a14_entrance_cell(rows, Role.MEZZANINE)
        assert res.get("opening_type") == catalogue.ENTRANCE_ARCH_HEAD_OPENING
        assert res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_HEAD
        assert res.get("opening_head") == "round"
        # A20.1: no railing and no balcony. A14.1 asked for "a balconette with
        # ironwork" here; no plate of this object has one, and a rail across a
        # porte cochère is a rail across the way in.
        assert res.get("ironwork_present") is False
        assert not res.get("balcony_present")
        # A20.1: and what fills the head is stated, because the two plates
        # differ — carved timber on the carriage form, glazed on the pedestrian.
        assert res.get("arch_head_infill") in ("tympanum", "glazed")
        # It sits on the imposte band in the register below, so no allège.
        assert float(res.get("opening_sill_height")) == pytest.approx(0.0)
        assert res.get("keystone_present") is True, "no agrafe at the crown"
        assert res.get("keystone_kind"), "the agrafe was never named by the period layer"


def test_the_lower_register_leaves_room_over_the_leaves_for_the_tympanum():
    """The Impératrice plate: two panelled leaves to about nine tenths of the
    rez-de-chaussée, then a carved band, then the arch carrying on up. The
    leaves keep their own ABSOLUTE clear height and the rest of the register
    is the tympanum — the opening rectangle is the HOLE, and the leaves are
    the door inside it."""
    for over in (_A13_SITE, _A14_PEDESTRIAN_SITE):
        rows = _a14_rows(_a14_two_storey_seed(over), over)
        ctx, res = _a14_entrance_cell(rows, Role.BASE)
        kind = ctx.slot_name
        one_storey = catalogue.entrance_in_slot(kind, ctx.slot_w, ctx.slot_h)
        assert res.get("entrance_leaf_height") == pytest.approx(one_storey.height)
        assert float(res.get("opening_height")) == pytest.approx(ctx.slot_h)
        assert float(res.get("opening_height")) > float(res.get("entrance_leaf_height"))
        # No head in this register: it is one storey up, and an arch turned
        # twice is not an arch.
        assert res.get("opening_head") == "none"
        assert float(res.get("opening_width")) == pytest.approx(one_storey.width)


def test_the_arch_crown_is_its_own_rise_and_nothing_else():
    """**A20.2.** The head of a two-storey entrance is a HEAD, not a light with
    a head on it.

    This used to assert that the crown landed on the line the flanking entresol
    openings' heads do — A14.1's "springs from the same coursing as the flanking
    arches", read as ending on their line too. The corpus says otherwise: three
    of Daly's four tall entrances measure 5.00, 5.01 and 5.07 m, crowning 38-60 %
    of the way up their entresol, where that rule put ours at 78 %.

    So the head register IS the rise, and the curve turns straight off the
    leaves with no straight register between them. The old bounds still hold —
    an arch may not be drawn through its own crowning band, nor past
    ``TALL_ARCH_MOST_SLENDER`` spans — they are simply no longer what decides
    it."""
    for over in (_A13_SITE, _A14_PEDESTRIAN_SITE):
        rows = _a14_rows(_a14_two_storey_seed(over), over)
        ctx, res = _a14_entrance_cell(rows, Role.MEZZANINE)
        height = float(res.get("opening_height"))
        rise = float(res.get("opening_head_rise"))
        assert height == pytest.approx(rise, abs=1e-9), (
            f"{ctx.slot_name}: a {height:.3f} m head register on a {rise:.3f} m "
            "rise — that is a straight light under the curve, and no plate has one"
        )
        crown = ctx.level_above_pavement + float(res.get("opening_sill_height")) + height
        band = ctx.base_block_top - base_layer.base_entablature_depth(ctx)
        assert crown <= band + 1e-9, (
            f"the arch crown reaches {crown:.3f} m; the band that crowns the base "
            f"starts at {band:.3f} m — an arch drawn through its own cornice"
        )
        # ...and it stops well short of the entresol's own ceiling, which is
        # what A17.1 wrongly had it reach.
        assert crown < ctx.base_block_top - 1e-9

def test_both_entresol_head_forms_carry_the_tall_arch():
    """A14.2 asked that the tall arch not be keyed to the entresol's form.
    A13 stated that form as *absorbed* against *arcaded*; A17.2 retracted the
    absorbed one, so what is left to be independent of is the head the
    entresol's own lights are turned with — square at 77, segmental at 120.
    The arch rises through the entresol either way, because what it needs is
    a storey to rise through and not a fashion in the lights beside it."""
    seen: dict[str, int] = {}
    for seed in range(64):
        rows = _a14_rows(seed)
        _c, base_res = _a14_entrance_cell(rows, Role.BASE)
        if base_res.get("entrance_arch_register") != catalogue.ENTRANCE_ARCH_LEAVES:
            continue
        _m, mez_res = _a14_entrance_cell(rows, Role.MEZZANINE)
        head = mez_res.get("entresol_head_form")
        seen[head] = seen.get(head, 0) + 1
        # Whichever it is, the arch is there and it is the same arch.
        assert mez_res.get("opening_type") == catalogue.ENTRANCE_ARCH_HEAD_OPENING
    assert set(seen) == {"flat", "segmental"}, (
        f"the tall arch reached only {sorted(seen)} — A14.2 needs both"
    )


def test_the_column_above_the_arch_is_still_ordinary_wall_with_windows_in_it():
    """A two-storey arch changes the base block and nothing else. The strip
    over the entrance carries the same plain windows it always did, or A6.1's
    fix would have been undone one storey higher up."""
    rows = _a14_rows(_a14_two_storey_seed())
    for row, res in rows:
        if row[0].role in (Role.BASE, Role.MEZZANINE) or row[0].within_comble:
            continue
        ctx, r = next(
            (c, x) for c, x in zip(row, res)
            if c.slot_name in catalogue.ENTRANCE_SLOT_NAMES
        )
        assert r.get("opening_type") == "window", ctx.index_from_bottom
        assert r.get("entrance_arch_register") is None


# ===========================================================================
# A15.3 / A15.4 — the balconette inside the arch, and how tall the arch goes
# ===========================================================================


def test_an_arch_head_carries_no_railing_at_all():
    """**A20.1**, which is strictly stronger than the A15.3 bound it replaces.

    A15.3 measured the old defect precisely — on 90 of 210 tall arches a 0.90 m
    flat-headed rail stood taller than the straight part of the light and cut
    through the archivolt — and fixed it by shortening the rail to that straight
    part. A20.2 then removed the straight part entirely, and A20.1 removed the
    rail: no plate of this object has one.

    So the assertion is no longer "the rail fits under the springing". It is
    that there is no rail. A bound that can only be satisfied by a zero-height
    element is a bound on an element that should not be emitted (A6.6)."""
    seen = 0
    for over in (_A13_SITE, _A14_PEDESTRIAN_SITE):
        rows = _a14_rows(_a14_two_storey_seed(over), over)
        ctx, res = _a14_entrance_cell(rows, Role.MEZZANINE)
        assert res.get("entrance_arch_register") == catalogue.ENTRANCE_ARCH_HEAD
        assert not res.get("ironwork_present"), (
            f"{ctx.slot_name}: the arch head still states a railing"
        )
        seen += 1
    assert seen == 2

def test_the_tall_pedestrian_arch_is_shorter_than_the_tall_carriage_arch():
    """**A15.4, asserted as an ORDERING.**

    Measured against Daly: ours ran 6.11-6.35 m for a tall *porte piétonne*
    against his two examples at 5.01 m (2 et 4 bd de Sébastopol, Davioud) and
    5.07 m (87 bd de Sébastopol) — 1.05-1.35 m too tall, an aspect of 3.49:1
    against 2.88:1 — while the tall carriage arch at 6.01-6.24 m sat happily
    inside his 5.00-7.30 m band. Both were being carried to the same crown
    line, and a narrower opening carried to a wider one's crown is not a
    taller arch, it is a thinner one.

    n = 2 is thin, so what is asserted is the ordering and not the value:
    pedestrian shorter than carriage, both clearly taller than the one-storey
    door they replace, and neither past the slenderness the catalogue states.
    The proportion itself is INFERRED (``TALL_ARCH_MOST_SLENDER``) and must
    not be calibrated.

    **The widths are untouched**, which A14 proved byte-identical across the
    two forms under a paired test and which A9.2 is the best-evidenced result
    in the project. It is re-asserted here because a height rule that reached
    for the width would undo it.
    """
    base_h = 3.95  # a Daly rez-de-chaussée in trade
    entresol_h = 3.06
    arches = {}
    for kind in sorted(catalogue.ENTRANCE_SLOT_NAMES):
        slot_w = float(catalogue.entrance_slot_width(kind))
        one_storey = catalogue.entrance_in_slot(kind, slot_w, base_h)
        arch = catalogue.two_storey_entrance_arch(
            kind, slot_w, base_h, entresol_h, crown_below=0.5775
        )
        arches[kind] = arch
        assert arch.clear_width == pytest.approx(one_storey.width), (
            f"{kind}: A15.4 moved a width (A14 / A9.2)"
        )
        assert arch.clear_height > one_storey.height + 1.0, (
            f"{kind}: the two-storey arch is not clearly taller than the one-storey "
            "door it replaces"
        )
        assert arch.clear_height / arch.clear_width <= (
            catalogue.TALL_ARCH_MOST_SLENDER + 1e-9
        )
    pedestrian = arches[catalogue.ENTRANCE_PEDESTRIAN]
    carriage = arches[catalogue.ENTRANCE_CARRIAGE]
    assert pedestrian.clear_height < carriage.clear_height, (
        f"the porte piétonne reaches {pedestrian.clear_height:.3f} m and the porte "
        f"cochère {carriage.clear_height:.3f} m — the narrow arch is still being "
        "carried to the wide one's crown (A15.4)"
    )
    # The carriage arch is the one A15.4 says is already right, and it stays
    # inside the band Daly's own two tall carriage arches make (5.00-7.30 m).
    assert 5.00 <= carriage.clear_height <= 7.30, carriage.clear_height
