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
    #
    # The margin above 1.45 is thin now and that is not an accident. The count
    # chooser takes the *closest* count, so the slack it hands the ladder never
    # exceeds half a bay — 1.50 m here — and the window in which the bay itself
    # must stretch is whatever lies between the filler band and that half. Ask
    # for more and the answer is a sixth bay, correctly.
    budget = BASE + 5 * BAY.preferred + 1.48
    r = solve(budget, end=END, bay=BAY, special=SPECIAL)
    assert r.rung is Rung.WIDEN_BAY
    assert len(bays(r)) == 5
    assert abs(r.slots[0].width - END.maximum) < EPS
    assert abs(bays(r)[0].width - (3.0 + (1.48 - 0.70) / 5)) < EPS


def test_insert_special_fires_before_add_module() -> None:
    """A leftover no whole number of bays reaches is answered with a special.

    The budget had to move. It used to be five preferred bays plus 2.40 m,
    chosen because flooring produced a 2.40 m leftover the elastic range could
    not swallow. Nothing produces a leftover that size any more: the count
    chooser takes the closest count, so it would simply have built six bays,
    which is what the old ladder had to climb two rungs to discover.

    What still reaches this rung is a width no whole number of bays gets near
    at all — here 8.11 m, where two bays leave 1.31 m over and three bays are
    1.69 m short, and the vocabulary's elastic bands reach neither. That is the
    leftover the brief calls architecturally meaningful, and it is now the only
    kind there is.
    """
    r = solve(8.11, end=END, bay=BAY, special=SPECIAL, min_bays=0)
    assert r.rung is Rung.INSERT_SPECIAL
    assert len(bays(r)) == 2
    specials = [s for s in r.slots if s.is_special]
    assert len(specials) == 1
    assert SPECIAL.minimum - EPS <= specials[0].width <= SPECIAL.maximum + EPS


def test_a_closest_count_leaves_add_module_nothing_to_repair() -> None:
    """Rung 5 is now unreachable without parity, and that is a proof, not a gap.

    ADD_MODULE is the repair for a count chosen from below: floor the division,
    discover the leftover will not fit, add a module. Once the count chooser
    looks upward on its own account the repair is subsumed — if one more bay
    were the better answer it is already the count that was chosen.

    Stated as an argument, since it is one: ADD_MODULE is only reached after
    the plain rungs failed at the natural count, and the natural count falls
    back to the floor *only* when no count at all is permitted by the bounds.
    So when rung 5 runs, ``_plain`` cannot succeed at any count, including
    every count rung 5 would step to. Measured below over the whole sweep to
    make sure the argument matches the code.

    Parity is the exception and has its own test: it moves the count off the
    closest one deliberately, which is exactly when adding modules can help.
    """
    seen = set()
    for i in range(20, 4000):
        budget = i / 100.0
        for kwargs in (
            dict(end=END, bay=BAY, special=SPECIAL),
            dict(end=END, bay=BAY),  # no special offered
        ):
            try:
                seen.add(solve(budget, min_bays=0, **kwargs).rung)
            except FitInfeasible:
                continue
    assert Rung.ADD_MODULE not in seen
    assert {Rung.EXACT, Rung.WIDEN_ENDS, Rung.WIDEN_FILLER, Rung.WIDEN_BAY} <= seen


def test_add_module_still_fires_where_parity_forbids_the_closest_count() -> None:
    """The other half of the argument above: rung 5 is subsumed, not deleted.

    A central composition may not take the closest count when that count gives
    the run the wrong parity, so it steps down to one that leaves surplus in
    hand — and where the vocabulary is too stiff to absorb that surplus, adding
    modules two at a time is still the honest answer and still the last one
    tried.
    """
    r = solve(6.60, end=TIGHT_END, bay=TIGHT_BAY, central_feature=True, min_bays=0)
    assert r.rung is Rung.ADD_MODULE
    n = len([s for s in r.slots if s.name == TIGHT_BAY.name])
    assert n == 3
    assert n - _natural_count(6.60, TIGHT_END, TIGHT_BAY, central=True) == 2
    assert len(interior(r)) % 2 == 1  # still centred


def test_ladder_is_climbed_in_order_as_slack_grows() -> None:
    """For a fixed natural bay count the rung must be monotonic in slack.

    The sweep stops at half a bay rather than a whole one, because that is now
    where the natural count changes: past the half the closest count is the
    next one up and the slack starts again from the other side. Running on
    would not show a ladder being climbed out of order, it would show two
    ladders spliced together.

    INSERT_SPECIAL has left this set for the same reason it left the test
    above: at five bays the elastic range reaches 2.20 m and the slack can no
    longer exceed 1.50 m, so there is nothing here for a special to answer.
    """
    seen: list[Rung] = []
    slack = 0.0
    while slack < BAY.preferred / 2.0 - 1e-6:
        r = solve(BASE + 5 * BAY.preferred + slack, end=END, bay=BAY, special=SPECIAL)
        assert len(bays(r)) == 5, slack
        seen.append(r.rung)
        slack += 0.02
    assert seen[0] is Rung.EXACT
    assert [s.value for s in seen] == sorted(s.value for s in seen)
    assert set(seen) == {
        Rung.EXACT,
        Rung.WIDEN_ENDS,
        Rung.WIDEN_FILLER,
        Rung.WIDEN_BAY,
    }


def test_the_ladder_is_climbed_in_order_downward_too() -> None:
    """The same ordering going the other way, which is now a reachable regime.

    A closest count may sit *above* the budget as readily as below it, so the
    ladder runs downward for half of every bay-width of frontage. The rung
    ordering is a fact about which elements exist to be adjusted, not about
    which direction they are adjusted in, so it must hold identically here.
    """
    seen: list[Rung] = []
    slack = 0.0
    while slack < BAY.preferred / 2.0 - 1e-6:
        r = solve(BASE + 5 * BAY.preferred - slack, end=END, bay=BAY, special=SPECIAL)
        assert len(bays(r)) == 5, slack
        seen.append(r.rung)
        slack += 0.02
    assert seen[0] is Rung.EXACT
    assert [s.value for s in seen] == sorted(s.value for s in seen)
    assert {Rung.WIDEN_ENDS, Rung.WIDEN_FILLER} <= set(seen)


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

    **Restated for the closest-count rule, and deliberately restated rather
    than imported**, so these tests check an independent statement of the rule
    and not the implementation's own arithmetic. It used to be a bare
    ``floor()``: as many whole preferred bays as stand beside two preferred
    ends. It is now the count whose resulting widths land *nearest* their
    preferred values — which, because those deviations have to add up to the
    slack, is the count leaving the least slack in absolute value — restricted
    to counts the declared bounds actually permit. Where the bounds permit
    none, the solver falls back to the old floor and so does this.
    """
    run = budget - 2 * end.preferred

    def permitted(n: int) -> bool:
        """Can two ends and ``n`` bays swallow this slack without leaving their
        own bounds? Stated as capacity, which is the fact, rather than by
        calling the solver's own absorber."""
        slack = run - n * bay.preferred
        if slack >= 0.0:
            room = 2 * (end.maximum - end.preferred) + n * (bay.maximum - bay.preferred)
        else:
            room = 2 * (end.preferred - end.minimum) + n * (bay.preferred - bay.minimum)
        return abs(slack) <= room + EPS

    allowed = [n for n in range(0, 80) if permitted(n)]
    if allowed:
        n = min(allowed, key=lambda k: (abs(run - k * bay.preferred), k))
    else:
        n = int(math.floor(run / bay.preferred + EPS))
    if central and n % 2 == 0:
        n -= 1  # the adjustment goes down first, so surplus stays in hand
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
    """Same budget, same vocabulary: the plain composition needs no module and
    the central one needs two.

    The budget moved for the reason given at
    ``test_a_closest_count_leaves_add_module_nothing_to_repair``. It used to be
    a width at which *both* compositions had to add modules, one stepping by
    one and the other by two, and the pair of them made the contrast. No plain
    composition adds a module any more — the count chooser has already looked
    upward — so the contrast is now sharper rather than weaker: the plain
    answer rests where it is, and the central one, forbidden the count that
    would have rested, steps past it two at a time.
    """
    budget = 6.60

    plain = solve(budget, end=TIGHT_END, bay=TIGHT_BAY, min_bays=0)
    central = solve(
        budget, end=TIGHT_END, bay=TIGHT_BAY, central_feature=True, min_bays=0
    )
    assert plain.rung is not Rung.ADD_MODULE
    assert central.rung is Rung.ADD_MODULE

    n_plain = len([s for s in plain.slots if s.name == TIGHT_BAY.name])
    n_central = len([s for s in central.slots if s.name == TIGHT_BAY.name])
    assert n_plain - _natural_count(budget, TIGHT_END, TIGHT_BAY) == 0
    assert n_central - _natural_count(budget, TIGHT_END, TIGHT_BAY, central=True) == 2
    assert len(interior(central)) % 2 == 1  # and it is still centred


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
    # Both arrangements must actually occur, or every assertion in the loop is
    # vacuous. The lone-special band has narrowed sharply — 9 budgets out of
    # 614 where it used to be about 200 — and that is the closest-count rule
    # showing through rather than a regression: a lone central special exists
    # to make an even run centred, and an even run is now reached only where
    # the odd family beside it cannot absorb the width at all. The flanking
    # pair, which the odd family takes, correspondingly does more of the work.
    # The per-budget assertions above are the substance and they still run on
    # every one of the 614 widths; these two numbers only keep them honest.
    assert lone >= 5, lone
    assert paired > 100, paired


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
    # The budget moved down to a width the whole bays genuinely cannot reach —
    # two bays leave 1.31 m over and three are short by more than the bands
    # allow — because that is now the only way rung 4 is entered at all. The
    # rule under test, which side the special takes, is untouched by that.
    budget = BASE + 2 * BAY.preferred + PORTE.preferred + 1.31
    left = solve(budget, end=END, bay=BAY, special=SPECIAL, fixed=[(0, PORTE)], min_bays=0)
    right = solve(budget, end=END, bay=BAY, special=SPECIAL, fixed=[(9, PORTE)], min_bays=0)
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
    # 8.11 m for the reason `test_insert_special_fires_before_add_module`
    # gives: it is a width no whole number of bays reaches, which is what the
    # narrow special is for and now the only thing that summons it.
    budget = 8.11
    r = solve(budget, end=END, bay=BAY, special=SPECIAL, min_bays=0)
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


# ------------------------------------------- the solver is parameter-driven
#
# The operator will constrain these numbers from outside — arbitrarily, and by
# building type, so that a grand frontage carries wider bays than a modest one.
# Nothing in the solver may resist that. These three tests are the guarantee
# that it does not: the same call, different specs, different composition, and
# no branch anywhere in the module on what kind of building it is.


def test_a_wider_bay_band_gives_a_wider_rhythm_on_the_same_frontage() -> None:
    """The whole of "grand buildings have wider bays", as far as this module is
    concerned: the caller passes a different band and gets a different rhythm.

    Asserted as a relation rather than as two numbers, because the numbers are
    the caller's to choose and will change; what may not change is that
    choosing them has the effect it obviously ought to.
    """
    modest = SlotSpec("bay", SlotKind.REPEATING, 2.00, 2.40, 2.80)
    grand = SlotSpec("bay", SlotKind.REPEATING, 3.00, 3.60, 4.20)
    frontage = 24.0

    a = solve(frontage, end=END, bay=modest, special=SPECIAL, min_bays=0)
    b = solve(frontage, end=END, bay=grand, special=SPECIAL, min_bays=0)

    n_a = len([s for s in a.slots if s.name == "bay"])
    n_b = len([s for s in b.slots if s.name == "bay"])
    assert n_a > n_b, (n_a, n_b)
    assert [s.width for s in a.slots if s.name == "bay"][0] < (
        [s.width for s in b.slots if s.name == "bay"][0]
    )
    # And both filled the same budget exactly, which is the hard requirement
    # the freedom must not cost.
    for r in (a, b):
        assert abs(total(r) - frontage) < EPS
        assert r.residual < EPS


def test_the_module_names_no_widths_of_its_own() -> None:
    """Every number the solver acts on came in through its arguments.

    A literal width compiled into this module is a building type it cannot be
    told about. The two constants it does own are a float tolerance and a share
    of declared headroom, neither of which is a dimension.
    """
    import buildings.solver.fitting as module

    numeric = {
        name: value
        for name, value in vars(module).items()
        if isinstance(value, float) and not name.startswith("__")
    }
    assert set(numeric) == {"EPS", "FILLER_SHARE"}, numeric


def test_the_caller_chooses_among_several_specials_in_its_own_order() -> None:
    """Support for "a half-bay, or an oeil-de-boeuf, or a blind panel".

    The solver takes the first special the leftover fits, in the order given,
    so the order is the caller's design statement. A caller that wants the
    choice biased by building type shuffles the list before calling — which is
    also how randomness stays out of a module that must be deterministic.
    """
    half_bay = SlotSpec("half_bay", SlotKind.FLEXIBLE, 1.25, 1.35, 1.60)
    oeil = SlotSpec("oeil_de_boeuf", SlotKind.FLEXIBLE, 0.90, 1.10, 1.31)
    budget = 8.11  # a width no whole number of bays reaches

    # The 1.31 m leftover is inside both bands, so nothing about the geometry
    # decides between them and the caller's ordering is the only thing that
    # does. That is the case worth pinning: where both fit, the list is a
    # preference and is obeyed as one.
    first = solve(budget, end=END, bay=BAY, special=[oeil, half_bay], min_bays=0)
    second = solve(budget, end=END, bay=BAY, special=[half_bay, oeil], min_bays=0)
    assert [s.name for s in first.slots if s.is_special] == ["oeil_de_boeuf"]
    assert [s.name for s in second.slots if s.is_special] == ["half_bay"]

    # A single spec still works, unchanged, and means the same as a list of one.
    lone = solve(budget, end=END, bay=BAY, special=oeil, min_bays=0)
    assert [s.width for s in lone.slots] == [s.width for s in first.slots]


def test_a_special_the_leftover_cannot_take_is_passed_over_for_one_it_can() -> None:
    """The list is a set of options, not a set of attempts that may fail.

    A caller offering three specials expects the leftover answered by whichever
    of them fits, not a refusal because the first one did not.
    """
    too_wide = SlotSpec("porch", SlotKind.FLEXIBLE, 2.60, 2.65, 2.69)
    usable = SlotSpec("oeil_de_boeuf", SlotKind.FLEXIBLE, 0.90, 1.10, 1.40)
    r = solve(8.11, end=END, bay=BAY, special=[too_wide, usable], min_bays=0)
    assert r.rung is Rung.INSERT_SPECIAL
    assert [s.name for s in r.slots if s.is_special] == ["oeil_de_boeuf"]


# ------------------------------------------------------------------- strain


def test_strain_is_zero_at_preferred_and_one_on_a_bound() -> None:
    """The signal a caller reads to decide it wants a different vocabulary.

    Not an error and not a bound: a report. It says how much of each slot's own
    declared latitude the answer had to spend, so a caller can notice that a
    composition only just reached its width and offer something else — wider
    ends, another special — before drawing it.
    """
    exact = solve(BASE + 5 * BAY.preferred, end=END, bay=BAY, special=SPECIAL)
    assert exact.rung is Rung.EXACT
    assert exact.strain == ()
    assert exact.worst_strain == pytest.approx(0.0)
    assert exact.strain_of("bay") == pytest.approx(0.0)

    # Ends at their maximum: 0.70 m of slack is exactly their whole headroom,
    # and the bay has not been touched at all.
    at_the_bound = solve(BASE + 5 * BAY.preferred + 0.70, end=END, bay=BAY, special=SPECIAL)
    assert at_the_bound.slots[0].width == pytest.approx(END.maximum)
    assert at_the_bound.strain_of("end") == pytest.approx(1.0)
    assert at_the_bound.strain_of("bay") == pytest.approx(0.0)

    # Monotonic in how hard the answer was pushed, within one count, per slot.
    for name in ("end", "bay"):
        strains = [
            solve(
                BASE + 5 * BAY.preferred + k * 0.05, end=END, bay=BAY, special=SPECIAL
            ).strain_of(name)
            for k in range(0, 14)
        ]
        assert strains == sorted(strains), (name, strains)


def test_strain_separates_the_ends_from_the_rhythm() -> None:
    """Why it is keyed by name and not reduced to one number.

    The ends are the most elastic thing in the composition, so the ladder
    spends them first and they sit on a bound over most of the range. A single
    worst-slot figure would therefore read 1.0 almost everywhere and tell a
    caller nothing. Keyed by name, the bay's own strain is visible underneath
    it — which is the thing an operator watching for a rhythm drifting to the
    extremes of its band actually wants.
    """
    ends_maxed = bay_still_easy = 0
    for i in range(200, 3600):
        r = solve(i / 100.0, end=END, bay=BAY, special=SPECIAL, min_bays=0)
        if r.strain_of("end") >= 1.0 - EPS:
            ends_maxed += 1
            if r.strain_of("bay") < 0.5:
                bay_still_easy += 1
    assert ends_maxed > 500, ends_maxed
    assert bay_still_easy > 100, (ends_maxed, bay_still_easy)


def test_strain_never_counts_a_slot_that_could_not_move() -> None:
    """A rigid slot is at its preferred width by construction, so it is not
    evidence about how hard anything was pushed. Counting it would report a
    comfortable facade as comfortable *because* of the one element that was
    never in question."""
    r = solve(24.0, end=END, bay=BAY, special=SPECIAL, fixed=[(2, PORTE)])
    porte = [s for s in r.slots if s.name == PORTE.name][0]
    assert porte.width == PORTE.preferred
    assert PORTE.name not in dict(r.strain)
    assert all(0.0 <= fraction <= 1.0 for _name, fraction in r.strain)
    # Worst first, so a caller can read the top of the list and stop.
    assert [f for _n, f in r.strain] == sorted((f for _n, f in r.strain), reverse=True)


def test_strain_is_reported_in_the_account_too() -> None:
    r = solve(BASE + 5 * BAY.preferred + 0.70, end=END, bay=BAY, special=SPECIAL)
    assert any("strain" in line for line in r.account)


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
