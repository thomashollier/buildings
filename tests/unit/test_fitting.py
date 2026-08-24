"""Unit tests for the fitting solver.

Each rung of the absorption ladder gets a test that fires it and a test that
proves the rungs below it were tried first. The ladder ordering is the solver,
so an off-by-one rung is a design failure, not a cosmetic one.
"""

from __future__ import annotations

import math

import pytest

from buildings.solver.fitting import (
    EPS,
    FitInfeasible,
    PlacedSlot,
    Rung,
    SlotKind,
    SlotSpec,
    solve,
)

# A plausible Parisian vocabulary. The ranges are the design statement: they say
# how far each element may be pushed before the next rung is the honest answer.
END = SlotSpec("end", SlotKind.FLEXIBLE, 0.20, 0.40, 0.75, elasticity=2.0)
BAY = SlotSpec("bay", SlotKind.REPEATING, 2.70, 3.00, 3.30)
SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 1.10, 1.35, 1.60)
PORTE = SlotSpec("porte_cochere", SlotKind.FIXED, 2.60, 2.60, 2.60, rigid=True)

# Elastic capacity at N bays, for reading the tests below:
#   ends   0.70 m  (2 x 0.35)
#   filler 0.15 N  (half the bay's 0.30 headroom)
#   bay    0.15 N
BASE = 2 * END.preferred  # both ends at preferred


def widths(result) -> list[float]:
    return [s.width for s in result.slots]


def bays(result) -> list[PlacedSlot]:
    return [s for s in result.slots if s.name == BAY.name]


def total(result) -> float:
    return math.fsum(s.width for s in result.slots)


# ---------------------------------------------------------------- the ladder


def test_exact_fill_climbs_no_rung() -> None:
    budget = BASE + 5 * BAY.preferred
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.EXACT
    assert widths(r) == [0.40, 3.0, 3.0, 3.0, 3.0, 3.0, 0.40]


def test_widen_ends_leaves_the_interior_rhythm_perfect() -> None:
    budget = BASE + 5 * BAY.preferred + 0.30
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.WIDEN_ENDS
    assert all(abs(b.width - BAY.preferred) < EPS for b in bays(r))
    assert abs(r.slots[0].width - (0.40 + 0.15)) < EPS
    assert abs(r.slots[0].width - r.slots[-1].width) < EPS  # ends stay equal


def test_widen_filler_only_after_the_ends_are_at_maximum() -> None:
    # 0.70 m fills the ends; the next 0.30 m goes into the filler of 5 bays.
    budget = BASE + 5 * BAY.preferred + 0.70 + 0.30
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.WIDEN_FILLER
    assert abs(r.slots[0].width - END.maximum) < EPS
    assert abs(bays(r)[0].width - (3.0 + 0.06)) < EPS


def test_widen_bay_only_after_the_filler_band_is_spent() -> None:
    # ends 0.70 + filler 5x0.15 = 1.45 exhausted, so the opening must stretch.
    budget = BASE + 5 * BAY.preferred + 1.45 + 0.20
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.WIDEN_BAY
    assert abs(r.slots[0].width - END.maximum) < EPS
    assert abs(bays(r)[0].width - (3.0 + (1.45 + 0.20 - 0.70) / 5)) < EPS


def test_insert_special_fires_before_add_module() -> None:
    # Slack 2.40 m: past the full elastic range (0.70 + 5x0.30 = 2.20) but not
    # worth squeezing a sixth bay in. Five good bays plus one narrow odd one.
    budget = BASE + 5 * BAY.preferred + 2.40
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.INSERT_SPECIAL
    assert len(bays(r)) == 5
    specials = [s for s in r.slots if s.is_special]
    assert len(specials) == 1
    assert SPECIAL.minimum - EPS <= specials[0].width <= SPECIAL.maximum + EPS


def test_add_module_fires_when_no_special_is_in_the_vocabulary() -> None:
    budget = BASE + 5 * BAY.preferred + 2.40
    r = solve(budget, end=END, bay=BAY)  # no special offered
    assert r.rung is Rung.ADD_MODULE
    assert len(bays(r)) == 6


def test_ladder_is_climbed_in_order_as_slack_grows() -> None:
    """For a fixed natural bay count the rung must be monotonic in slack."""
    seen: list[Rung] = []
    slack = 0.0
    while slack < BAY.preferred - 1e-6:
        r = solve(BASE + 5 * BAY.preferred + slack, end=END, bay=BAY, special=SPECIAL)
        seen.append(r.rung)
        slack += 0.02
    assert seen[0] is Rung.EXACT
    assert [s.value for s in seen] == sorted(s.value for s in seen)
    assert set(seen) == {
        Rung.EXACT,
        Rung.WIDEN_ENDS,
        Rung.WIDEN_FILLER,
        Rung.WIDEN_BAY,
        Rung.INSERT_SPECIAL,
    }


# ------------------------------------------------------------ centreline unit


def test_n_bays_is_exactly_n_times_the_bay_width() -> None:
    """Centreline to centreline: the only special case is the two ends."""
    for budget in (12.0, 17.35, 23.8, 31.05):
        r = solve(budget, end=END, bay=BAY, special=SPECIAL)
        b = bays(r)
        assert b, budget
        assert abs(math.fsum(s.width for s in b) - len(b) * b[0].width) < EPS
        assert max(s.width for s in b) - min(s.width for s in b) < EPS


def test_only_the_two_ends_are_special_cased() -> None:
    r = solve(20.0, end=END, bay=BAY, special=SPECIAL)
    assert r.slots[0].name == END.name
    assert r.slots[-1].name == END.name
    assert abs(r.slots[0].width - r.slots[-1].width) < EPS
    assert r.slots[0].start == 0.0


# -------------------------------------------------------------------- rigidity


def test_rigid_slot_never_absorbs_slack() -> None:
    """A carriage entrance must admit a carriage, at every budget."""
    for i in range(0, 400):
        budget = 8.0 + i * 0.05
        r = solve(budget, end=END, bay=BAY, special=SPECIAL, fixed=[(1, PORTE)])
        porte = [s for s in r.slots if s.name == PORTE.name]
        assert len(porte) == 1
        assert porte[0].width == PORTE.preferred


def test_fixed_kind_is_rigid_even_without_the_rigid_flag() -> None:
    shop = SlotSpec("shopfront", SlotKind.FIXED, 3.0, 3.4, 4.0)
    r = solve(19.13, end=END, bay=BAY, special=SPECIAL, fixed=[(0, shop)])
    got = [s for s in r.slots if s.name == "shopfront"][0]
    assert got.width == shop.preferred


def test_elasticity_declares_the_absorption_order() -> None:
    """`elasticity` is not decoration: raise the bay above the end and the bay goes first."""
    stiff_end = SlotSpec("end", SlotKind.FLEXIBLE, 0.20, 0.40, 0.75, elasticity=0.5)
    eager_bay = SlotSpec("bay", SlotKind.REPEATING, 2.70, 3.00, 3.30, elasticity=3.0)
    budget = BASE + 5 * BAY.preferred + 0.30
    r = solve(budget, end=stiff_end, bay=eager_bay, special=SPECIAL)
    assert r.rung is Rung.WIDEN_FILLER
    assert r.slots[0].width == stiff_end.preferred  # the ends never moved
    assert abs(bays(r)[0].width - (3.0 + 0.06)) < EPS


def test_a_rigid_end_forces_the_ladder_to_start_at_the_filler() -> None:
    rigid_end = SlotSpec("quoin", SlotKind.FLEXIBLE, 0.40, 0.40, 0.40, rigid=True)
    r = solve(0.80 + 5 * 3.0 + 0.20, end=rigid_end, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.WIDEN_FILLER
    assert r.slots[0].width == 0.40


# --------------------------------------------------------------------- parity


def _natural_count(
    budget: float, end: SlotSpec, bay: SlotSpec, *, central: bool = False
) -> int:
    """The count the ladder starts from, parity included.

    Parity is a property of *this* number. Constraining only the ADD_MODULE
    increment leaves the count free to walk 1, 2, 3, 4 as the budget grows,
    which puts the axis on a pier half the time — so the tests below measure the
    step against a count that already knows the rule.
    """
    n = int(math.floor((budget - 2 * end.preferred) / bay.preferred + EPS))
    if central and n % 2 == 0:
        n -= 1  # the largest odd count that still fits at preferred widths
    return n


def interior(result) -> list[PlacedSlot]:
    return list(result.slots[1:-1])


# A vocabulary with almost no stretch upward but plenty of squeeze downward, so
# that ADD_MODULE is reachable and the parity rule is observable.
TIGHT_END = SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.40, 0.45)
TIGHT_BAY = SlotSpec("bay", SlotKind.REPEATING, 2.00, 3.00, 3.05)
TINY_SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.20, 0.30, 0.35)

# Below this width the ordinary vocabulary has no centred arrangement at all:
# one bay alone reaches 4.80 m and one bay flanked by two specials starts at
# 5.30 m, and nothing spans the gap. The sweeps below therefore start above it;
# that the refusals underneath are genuine and not a solver giving up early is
# the invariant suite's business.
#
# It used to sit at 8.50 m, because the solver refused everything up to there:
# it held the bay count odd rather than holding an element on the axis, which
# made "two bays with a special between them" — a composition it can build,
# exactly and symmetrically — unreachable (A1.6).
CENTRED_FROM = 106  # 5.30 m, in units of the 0.05 m sweep step


def test_central_feature_steps_the_bay_count_by_two() -> None:
    budget = 0.80 + 8 * 3.00 + 2.50

    plain = solve(budget, end=TIGHT_END, bay=TIGHT_BAY, special=TINY_SPECIAL)
    central = solve(
        budget,
        end=TIGHT_END,
        bay=TIGHT_BAY,
        special=TINY_SPECIAL,
        central_feature=True,
    )
    assert plain.rung is Rung.ADD_MODULE
    assert central.rung is Rung.ADD_MODULE

    n_plain = len([s for s in plain.slots if s.name == TIGHT_BAY.name])
    n_central = len([s for s in central.slots if s.name == TIGHT_BAY.name])
    assert n_plain - _natural_count(budget, TIGHT_END, TIGHT_BAY) == 1
    assert n_central - _natural_count(budget, TIGHT_END, TIGHT_BAY, central=True) == 2


def test_central_feature_puts_an_element_on_the_axis_at_every_width() -> None:
    """The flag's whole content. A pier on the centreline is the failure it names.

    Checked against the ordinary vocabulary across a wide sweep rather than at a
    chosen budget, because the defect this guards against is not that the
    centring is wrong somewhere — it is that the centring drifts in and out as
    the budget grows, which no single width can show.
    """
    checked = 0
    for i in range(CENTRED_FROM, 720):
        budget = i * 0.05
        r = solve(
            budget, end=END, bay=BAY, special=SPECIAL, central_feature=True, min_bays=0
        )
        run = interior(r)
        assert len(run) % 2 == 1, (budget, [s.name for s in r.slots])
        middle = run[len(run) // 2]
        assert middle.start < budget / 2 < middle.start + middle.width, budget
        ws = widths(r)
        assert all(abs(a - b) < EPS for a, b in zip(ws, reversed(ws))), budget
        checked += 1
    assert checked > 500


def test_without_the_flag_the_axis_lands_on_a_pier_about_half_the_time() -> None:
    """The control: centring is a decision the flag makes, not a coincidence."""
    on_a_joint = 0
    for i in range(CENTRED_FROM, 720):
        budget = i * 0.05
        r = solve(budget, end=END, bay=BAY, special=SPECIAL, min_bays=0)
        if len(interior(r)) % 2 == 0:
            on_a_joint += 1
    assert on_a_joint > 200


def test_central_feature_places_its_specials_symmetrically() -> None:
    """A special in a central composition is either the axis or symmetric about it.

    Two arrangements, and no third. A **pair** flanks the run, leaving the run's
    own middle element on the centreline. A **lone** special is the middle
    element — which requires the run it joins to have even length, so that the
    same number of elements stands on either side of it. What is forbidden is a
    lone special anywhere else: on an odd run it would sit one place off the
    middle, which is the exact opposite of what the flag asked for.

    This test used to assert that a lone special never appeared at all. That was
    the over-correction A1.6 names: it is true that a lone special may not join
    an *odd* run, and false that the solver may therefore refuse every even one.
    """
    budget = BASE + 5 * BAY.preferred + 2.60
    r = solve(budget, end=END, bay=BAY, special=SPECIAL, central_feature=True)
    assert r.rung is Rung.INSERT_SPECIAL
    assert len([s for s in r.slots if s.is_special]) == 2
    ws = widths(r)
    assert all(abs(a - b) < EPS for a, b in zip(ws, reversed(ws)))

    lone = paired = 0
    for i in range(CENTRED_FROM, 720):
        budget = i * 0.05
        got = solve(
            budget, end=END, bay=BAY, special=SPECIAL, central_feature=True, min_bays=0
        )
        run = interior(got)
        specials = [s for s in run if s.is_special]
        if len(specials) == 1:
            lone += 1
            assert run[len(run) // 2] is specials[0], budget
            assert specials[0].start < budget / 2 < specials[0].start + specials[0].width
        elif specials:
            paired += 1
            assert len(specials) == 2, budget
            assert run[0] is specials[0] and run[-1] is specials[1], budget
        ws = widths(got)
        assert all(abs(a - b) < EPS for a, b in zip(ws, reversed(ws))), budget
    assert lone > 20 and paired > 20, (lone, paired)


def test_a_central_composition_refuses_rather_than_apologising() -> None:
    """Where no centred arrangement exists the answer is a refusal, not a lopsided one.

    This vocabulary can make 10.90 m only as four bays or as three bays with one
    special beside them — both of which put the joint between two elements on
    the axis. Returning one of them anyway is the failure mode this replaces.
    """
    stiff_end = SlotSpec("end", SlotKind.FLEXIBLE, 0.45, 0.50, 0.60)
    stiff_bay = SlotSpec("bay", SlotKind.REPEATING, 2.95, 3.00, 3.10)
    stiff_special = SlotSpec("special", SlotKind.FLEXIBLE, 0.90, 1.00, 1.20)
    kwargs = dict(end=stiff_end, bay=stiff_bay, special=stiff_special, min_bays=0)

    loose = solve(10.90, **kwargs)
    assert len(interior(loose)) % 2 == 0  # four bays: the axis is on a pier
    with pytest.raises(FitInfeasible):
        solve(10.90, central_feature=True, **kwargs)


def test_parity_that_no_bay_count_can_satisfy_is_refused_not_ignored() -> None:
    budget = BASE + 4 * BAY.preferred
    assert solve(budget, end=END, bay=BAY, min_bays=4, max_bays=4).rung is Rung.EXACT
    with pytest.raises(FitInfeasible):
        solve(budget, end=END, bay=BAY, min_bays=4, max_bays=4, central_feature=True)


def test_a_fixed_slot_counts_toward_the_centring() -> None:
    """The centreline is a fact about the run, not about the bays alone.

    With the porte cochere in the run, it is the porte that makes the count odd:
    everything else in the run — the bays and whatever specials the composition
    took — has to come to an even number for the whole to be odd. Asserting on
    the bays alone would be assuming the specials always arrive in pairs, which
    since A1.6 they do not.
    """
    for i in range(104, 700):  # 5.20 m; the porte reserves 2.60 m of the width
        r = solve(
            i * 0.05,
            end=END,
            bay=BAY,
            special=SPECIAL,
            fixed=[(2, PORTE)],
            central_feature=True,
            min_bays=0,
        )
        run = interior(r)
        assert len(run) % 2 == 1
        assert len([s for s in run if s.name != PORTE.name]) % 2 == 0
        assert len([s for s in run if s.name == PORTE.name]) == 1


# ------------------------------------------------------- special has a position


def test_a_lone_special_answers_the_entrance_from_the_opposite_side() -> None:
    budget = BASE + 5 * BAY.preferred + 2.60 + PORTE.preferred
    left = solve(budget, end=END, bay=BAY, special=SPECIAL, fixed=[(0, PORTE)])
    right = solve(budget, end=END, bay=BAY, special=SPECIAL, fixed=[(5, PORTE)])
    assert left.rung is right.rung is Rung.INSERT_SPECIAL

    def special_index(r) -> int:
        return [i for i, s in enumerate(r.slots) if s.is_special][0]

    def porte_index(r) -> int:
        return [i for i, s in enumerate(r.slots) if s.name == PORTE.name][0]

    assert special_index(left) > porte_index(left)
    assert special_index(right) < porte_index(right)


def test_fixed_index_hint_counts_the_bays_to_its_left() -> None:
    r = solve(24.0, end=END, bay=BAY, special=SPECIAL, fixed=[(2, PORTE)])
    names = [s.name for s in r.slots]
    assert names.index(PORTE.name) == 3  # end, bay, bay, porte, ...


def test_fixed_hint_is_clamped_rather_than_dropped() -> None:
    r = solve(24.0, end=END, bay=BAY, special=SPECIAL, fixed=[(99, PORTE)])
    assert any(s.name == PORTE.name for s in r.slots)
    r2 = solve(24.0, end=END, bay=BAY, special=SPECIAL, fixed=[(-4, PORTE)])
    assert [s.name for s in r2.slots].index(PORTE.name) == 1


# ------------------------------------------------------- the hard requirements


def test_exact_fill_and_bounds_hold_for_arbitrary_budgets() -> None:
    for i in range(0, 500):
        budget = 6.0 + i * 0.0673
        r = solve(budget, end=END, bay=BAY, special=SPECIAL)
        assert abs(total(r) - budget) < 1e-9
        assert r.residual < 1e-9
        assert abs(r.slots[0].start) < EPS
        for a, b in zip(r.slots, r.slots[1:]):
            assert abs(a.start + a.width - b.start) < 1e-9


def test_determinism() -> None:
    a = solve(21.37, end=END, bay=BAY, special=SPECIAL, fixed=[(2, PORTE)])
    b = solve(21.37, end=END, bay=BAY, special=SPECIAL, fixed=[(2, PORTE)])
    assert a == b


# ------------------------------------------------------------------- the account


def test_the_account_explains_the_result() -> None:
    budget = BASE + 5 * BAY.preferred + 2.40
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.account
    assert all(isinstance(line, str) and line for line in r.account)
    joined = "\n".join(r.account)
    assert "budget" in joined
    assert "centreline" in joined
    assert Rung.INSERT_SPECIAL.name in joined


def test_the_account_says_where_the_centreline_went() -> None:
    """Someone must be able to ask why the composition is the shape it is."""
    r = solve(BASE + 5 * BAY.preferred, end=END, bay=BAY, central_feature=True)
    assert any("centreline" in line for line in r.account)


def test_the_account_names_the_reserved_absolute_width() -> None:
    r = solve(24.0, end=END, bay=BAY, special=SPECIAL, fixed=[(2, PORTE)])
    assert any("2.6000" in line for line in r.account)


# --------------------------------------------------------------- both axes


def test_the_same_solver_fits_storeys_into_a_height_budget() -> None:
    """One solver serves both axes; nothing in it is horizontal."""
    parapet = SlotSpec("parapet", SlotKind.FLEXIBLE, 0.30, 0.60, 1.20, elasticity=2.0)
    storey = SlotSpec("storey", SlotKind.REPEATING, 2.60, 3.05, 3.60)
    ground = SlotSpec("ground_floor", SlotKind.FIXED, 4.20, 4.20, 4.20, rigid=True)
    r = solve(18.0, end=parapet, bay=storey, fixed=[(0, ground)], min_bays=1, max_bays=9)
    assert abs(total(r) - 18.0) < 1e-9
    assert [s for s in r.slots if s.name == "ground_floor"][0].width == 4.20
    assert all(s.width >= 2.60 - EPS for s in r.slots if s.name == "storey")


# ------------------------------------------------------------------ failures


def test_a_vocabulary_that_cannot_make_the_width_says_so() -> None:
    with pytest.raises(FitInfeasible):
        # One bay is too narrow, two are too wide, and nothing may stretch.
        solve(5.35, end=END, bay=BAY, min_bays=1, max_bays=24)


def test_the_narrow_special_is_what_closes_those_gaps() -> None:
    """The brief's claim, made testable: rung 4 is not decoration."""
    gaps = []
    for i in range(0, 60):
        budget = 4.0 + i * 0.05
        try:
            solve(budget, end=END, bay=BAY)
        except FitInfeasible:
            gaps.append(budget)
    assert gaps, "expected a vocabulary without a special to have unreachable widths"
    for budget in gaps:
        solve(budget, end=END, bay=BAY, special=SPECIAL)  # must not raise


def test_bad_specs_are_rejected_at_construction() -> None:
    with pytest.raises(ValueError):
        SlotSpec("bad", SlotKind.FLEXIBLE, 1.0, 0.5, 2.0)
    with pytest.raises(ValueError):
        SlotSpec("bad", SlotKind.FLEXIBLE, -1.0, 0.5, 2.0)


def test_bad_arguments_are_rejected() -> None:
    with pytest.raises(ValueError):
        solve(0.0, end=END, bay=BAY)
    with pytest.raises(ValueError):
        solve(20.0, end=END, bay=BAY, min_bays=5, max_bays=2)
    with pytest.raises(ValueError):
        solve(20.0, end=END, bay=END)  # bay must be REPEATING
