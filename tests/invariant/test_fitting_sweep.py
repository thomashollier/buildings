"""Gate G1 — the exhaustive fitting sweep.

Widths 4.00 m to 40.00 m at 0.05 m steps, across nine declared vocabularies.
The contract's requirements are asserted at every single point, not sampled:
exact fill, bounds, rigid slots pinned to preferred, centreline arithmetic,
parity, and a rung that is monotonic in slack.

There is no seed axis here because there is nothing to seed: the solver contains
no RNG at all, which is a stronger statement than reproducibility across eight
of them. The axis that would have been seeds is instead nine *vocabularies* —
the thing that actually varies the solver's behaviour — spanning both axes of
the building, rigid slots, parity, and deliberately impoverished ranges.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterator

import pytest

from buildings.solver.fitting import (
    EPS,
    FitInfeasible,
    FitResult,
    Rung,
    SlotKind,
    SlotSpec,
    solve,
)

LO, HI, STEP = 4.00, 40.00, 0.05
TOL = 1e-9

PORTE = SlotSpec("porte_cochere", SlotKind.FIXED, 2.60, 2.60, 2.60, rigid=True)
GROUND = SlotSpec("ground_floor", SlotKind.FIXED, 4.20, 4.20, 4.20, rigid=True)


def _budgets() -> Iterator[float]:
    n = int(round((HI - LO) / STEP)) + 1
    for i in range(n):
        yield LO + i * STEP


@dataclass(frozen=True)
class Vocabulary:
    """One declared set of elements, plus the width from which it can fill.

    ``covers_from`` is not a solver tolerance — it is an honest property of the
    vocabulary. A set of elements with almost no elasticity and no usable
    special genuinely cannot make certain narrow widths, and the solver's only
    truthful answer there is to refuse. Vocabularies that claim to cover the
    whole sweep declare ``covers_from = LO`` and any refusal fails the gate.

    It is not taken on trust either: ``test_every_refusal_is_genuinely_infeasible``
    brute-forces every arrangement the solver is permitted to build at each
    refused width, so a number raised here to quieten a failure would be caught
    by that test instead.
    """

    name: str
    kwargs: dict[str, Any]
    covers_from: float = LO
    parity: bool = False

    def specs(self) -> dict[str, SlotSpec]:
        out = {self.kwargs["end"].name: self.kwargs["end"], self.kwargs["bay"].name: self.kwargs["bay"]}
        special = self.kwargs.get("special")
        if special is not None:
            out[special.name] = special
        for _hint, spec in self.kwargs.get("fixed", ()):
            out[spec.name] = spec
        return out


def _ordinary() -> dict[str, Any]:
    return dict(
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.20, 0.40, 0.75, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, 2.70, 3.00, 3.30),
        special=SlotSpec("special", SlotKind.FLEXIBLE, 1.10, 1.35, 1.60),
        min_bays=0,
    )


def _tight() -> dict[str, Any]:
    # Almost no room to widen, plenty to squeeze: this is the vocabulary that
    # drives the solver onto ADD_MODULE and keeps it there.
    return dict(
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.30, 0.40, 0.45),
        bay=SlotSpec("bay", SlotKind.REPEATING, 2.00, 3.00, 3.05),
        special=SlotSpec("special", SlotKind.FLEXIBLE, 0.20, 0.30, 0.35),
        min_bays=0,
    )


VOCABULARIES: tuple[Vocabulary, ...] = (
    Vocabulary("ordinary", _ordinary()),
    Vocabulary(
        "grand",
        dict(
            end=SlotSpec("end", SlotKind.FLEXIBLE, 0.35, 0.70, 1.30, elasticity=2.0),
            bay=SlotSpec("bay", SlotKind.REPEATING, 3.30, 3.80, 4.30),
            special=SlotSpec("special", SlotKind.FLEXIBLE, 1.30, 1.70, 2.10),
            min_bays=0,
        ),
    ),
    Vocabulary(
        "modest",
        dict(
            end=SlotSpec("end", SlotKind.FLEXIBLE, 0.12, 0.25, 0.50, elasticity=2.0),
            bay=SlotSpec("bay", SlotKind.REPEATING, 2.10, 2.40, 2.70),
            special=SlotSpec("special", SlotKind.FLEXIBLE, 0.85, 1.05, 1.35),
            min_bays=0,
        ),
    ),
    Vocabulary("with_porte", dict(**_ordinary(), fixed=[(1, PORTE)])),
    # A central feature restricts the *arrangements* available to those that put
    # an element on the axis: an odd run between the ends, or an even run with a
    # lone narrow special at its middle. Both are offered (A1.6), so the only
    # widths left unreachable are the ones no centred arrangement covers at all —
    # here the gap between one bay alone (up to 4.80 m) and one bay flanked by
    # two specials (from 5.30 m). The honest answer in that gap is to refuse.
    Vocabulary("central", dict(**_ordinary(), central_feature=True), covers_from=5.30, parity=True),
    Vocabulary(
        "central_with_porte",
        dict(**_ordinary(), central_feature=True, fixed=[(2, PORTE)]),
        covers_from=5.20,
        parity=True,
    ),
    Vocabulary("tight", _tight(), covers_from=4.60),
    Vocabulary(
        "tight_central",
        dict(**_tight(), central_feature=True),
        covers_from=6.60,
        parity=True,
    ),
    Vocabulary(
        "storeys",
        dict(
            end=SlotSpec("parapet", SlotKind.FLEXIBLE, 0.30, 0.60, 1.20, elasticity=2.0),
            bay=SlotSpec("storey", SlotKind.REPEATING, 2.60, 3.05, 3.60),
            special=SlotSpec("mezzanine", SlotKind.FLEXIBLE, 1.90, 2.20, 2.55),
            fixed=[(0, GROUND)],
            min_bays=0,
        ),
        covers_from=6.70,
    ),
)

IDS = [v.name for v in VOCABULARIES]


def _reserved(v: Vocabulary) -> float:
    return math.fsum(spec.preferred for _h, spec in v.kwargs.get("fixed", ()))


def _plain_count(budget: float, v: Vocabulary) -> int:
    """The count the *plain* rungs start from: whole preferred bays beside two ends.

    Restated here rather than imported, so the gate checks an independent
    statement of the rule and not the implementation's own arithmetic.

    Under ``central_feature`` the plain rungs need an odd run between the ends —
    with no special in the composition there is nothing else to put on the axis —
    so the count is the largest one of that parity that still fits at preferred
    widths. That is a property of the composition, not of the ADD_MODULE step,
    which is why it is computed here and not by adjusting the increment.

    It is emphatically *not* the only admissible count. An even run carrying a
    lone central special is centred too (A1.6), and nothing below reads this
    function as if it were: it is used only where the odd-run family is the
    subject, i.e. to measure the ADD_MODULE increment.
    """
    end = v.kwargs["end"]
    bay = v.kwargs["bay"]
    lo = v.kwargs.get("min_bays", 1)
    hi = v.kwargs.get("max_bays", 24)
    n_fixed = len(v.kwargs.get("fixed", ()))
    raw = int(math.floor((budget - _reserved(v) - 2 * end.preferred) / bay.preferred + EPS))
    n = min(max(raw, lo), hi)
    if v.kwargs.get("central_feature") and (n + n_fixed) % 2 == 0:
        n = n - 1 if n - 1 >= lo else n + 1
    return n


def _slack_at(budget: float, v: Vocabulary, n_bays: int) -> float:
    """Metres ``n_bays`` preferred bays beside two preferred ends leave over."""
    end = v.kwargs["end"]
    bay = v.kwargs["bay"]
    return budget - _reserved(v) - 2 * end.preferred - n_bays * bay.preferred


def _bay_count(result: FitResult, v: Vocabulary) -> int:
    return len([s for s in result.slots if s.name == v.kwargs["bay"].name])


def _run(result: FitResult) -> list[Any]:
    """The interior run: everything between the two ends."""
    return list(result.slots[1:-1])


def _check(result: FitResult, budget: float, v: Vocabulary) -> None:
    specs = v.specs()
    bay_name = v.kwargs["bay"].name
    end_name = v.kwargs["end"].name

    # exact fill
    assert abs(math.fsum(s.width for s in result.slots) - budget) < TOL
    assert result.residual < TOL

    # contiguous, starting at the left edge of the parcel
    assert abs(result.slots[0].start) < TOL
    for a, b in zip(result.slots, result.slots[1:]):
        assert abs(a.start + a.width - b.start) < TOL

    for slot in result.slots:
        spec = specs[slot.name]
        # no slot outside [minimum, maximum]
        assert spec.minimum - TOL <= slot.width <= spec.maximum + TOL, slot
        # rigid slots always emerge at exactly preferred
        if spec.pinned:
            assert slot.width == spec.preferred, slot

    # exactly two ends, and only the two ends are special-cased
    ends = [s for s in result.slots if s.name == end_name]
    assert len(ends) == 2
    assert result.slots[0] is ends[0] and result.slots[-1] is ends[1]

    # centreline units: N bays is exactly N x width
    row = [s for s in result.slots if s.name == bay_name]
    if row:
        w = row[0].width
        assert max(s.width for s in row) - min(s.width for s in row) < TOL
        assert abs(math.fsum(s.width for s in row) - len(row) * w) < TOL
    assert v.kwargs.get("min_bays", 1) <= len(row) <= v.kwargs.get("max_bays", 24)

    # a central feature means an element ON the axis, not a flag that changed
    # nothing. An odd interior run is what puts one there — either one of the
    # run's own elements, or a lone narrow special inserted at its middle, which
    # is then the middle element itself. Where the vocabulary is symmetric the
    # axis is checked geometrically as well.
    if v.kwargs.get("central_feature"):
        interior = result.slots[1:-1]
        assert len(interior) % 2 == 1, [s.name for s in result.slots]
        specials = [s for s in interior if s.is_special]
        # A lone special is admissible only as the centre; a pair only as flanks.
        if len(specials) == 1:
            assert interior[len(interior) // 2] is specials[0], [
                s.name for s in result.slots
            ]
        elif specials:
            assert len(specials) == 2, [s.name for s in result.slots]
            assert interior[0] is specials[0] and interior[-1] is specials[1]
        if not v.kwargs.get("fixed"):
            ws = [s.width for s in result.slots]
            assert all(abs(a - b) < TOL for a, b in zip(ws, reversed(ws))), ws
            middle = interior[len(interior) // 2]
            axis = budget / 2.0
            assert middle.start + TOL < axis < middle.start + middle.width - TOL

    # an account, always
    assert isinstance(result.rung, Rung)
    assert result.account and all(isinstance(a, str) and a for a in result.account)
    assert result.rung.name in result.account[-1]


@pytest.mark.parametrize("v", VOCABULARIES, ids=IDS)
def test_sweep_meets_every_hard_requirement(v: Vocabulary) -> None:
    solved = 0
    for budget in _budgets():
        try:
            result = solve(budget, **v.kwargs)
        except FitInfeasible:
            # Only ever below the vocabulary's declared coverage, and only ever
            # as a loud refusal — never as a wrong answer.
            assert budget < v.covers_from, f"{v.name} refused {budget:.2f} m"
            continue
        _check(result, budget, v)
        solved += 1
    assert solved > 600, f"{v.name} only solved {solved} widths"


@pytest.mark.parametrize("v", VOCABULARIES, ids=IDS)
def test_rung_is_monotonic_in_slack(v: Vocabulary) -> None:
    """Hold the module count fixed and the ladder is only ever climbed, never skipped down.

    The ladder's claim is about one composition: *given* this many bays, the more
    the budget differs from what they want, the further up the ladder the answer
    has to come from. So the group is the emitted bay count and the slack is
    measured against that count — the arrangement's own slack, not some other
    arrangement's.

    Grouping instead by a *natural* count computed from the budget silently
    assumes there is only one admissible arrangement per width, which is exactly
    the assumption A1.6 removed: a central composition may answer with an odd run
    of `n` bays or with an even run of `n + 1` carrying a central special, and
    those are two ladders, not one.

    Monotonic in the *magnitude* of the slack, not in the budget: a budget below
    the arrangement has negative slack and runs the same ladder downward, so the
    two directions are separate sequences that each climb from EXACT.
    """
    groups: dict[tuple[int, int], list[tuple[float, Rung, float]]] = {}
    for budget in _budgets():
        try:
            result = solve(budget, **v.kwargs)
        except FitInfeasible:
            continue
        n = _bay_count(result, v)
        slack = _slack_at(budget, v, n)
        groups.setdefault((n, 0 if slack >= 0 else 1), []).append(
            (abs(slack), result.rung, budget)
        )

    checked = 0
    for key, seq in groups.items():
        seq.sort()
        rungs = [r.value for _s, r, _b in seq]
        assert rungs == sorted(rungs), f"{v.name}, group {key}: {seq}"
        checked += 1
    assert checked > 5


@pytest.mark.parametrize("v", VOCABULARIES, ids=IDS)
def test_the_whole_ladder_stays_available(v: Vocabulary) -> None:
    """Every vocabulary reaches the elastic rungs; none is stuck on one answer."""
    seen: set[Rung] = set()
    for budget in _budgets():
        try:
            seen.add(solve(budget, **v.kwargs).rung)
        except FitInfeasible:
            continue
    assert {Rung.EXACT, Rung.WIDEN_ENDS, Rung.WIDEN_FILLER, Rung.WIDEN_BAY} <= seen
    assert seen & {Rung.INSERT_SPECIAL, Rung.ADD_MODULE}


def test_absolute_slots_never_change_width_across_the_whole_sweep() -> None:
    """A carriage entrance must admit a carriage at 4 m of frontage and at 40."""
    seen: set[float] = set()
    for v in VOCABULARIES:
        fixed = v.kwargs.get("fixed", ())
        if not fixed:
            continue
        for budget in _budgets():
            try:
                result = solve(budget, **v.kwargs)
            except FitInfeasible:
                continue
            for slot in result.slots:
                spec = v.specs()[slot.name]
                if spec.pinned:
                    assert slot.width == spec.preferred
                    seen.add(slot.width)
    assert seen == {PORTE.preferred, GROUND.preferred}


@pytest.mark.parametrize("v", [v for v in VOCABULARIES if v.parity], ids=lambda v: v.name)
def test_parity_steps_the_composition_by_two_never_one(v: Vocabulary) -> None:
    """Both halves of the rule: the ADD_MODULE increment *and* the sweep.

    The increment alone is not the property. A solver can step ADD_MODULE by two
    and still walk the composition 1, 2, 3, 4 elements as the budget grows,
    because the count it starts from was chosen by a bare floor(), which puts the
    axis on a joint half the time. The composition as a function of the budget is
    therefore checked directly, and every ADD_MODULE firing is checked as well —
    `fired > 0`, so a vocabulary that never reaches the top rung cannot pass this
    test by asserting nothing.

    The thing that steps by two is the **interior run**, not the bay count. That
    is what parity is about: the run is what carries the centreline, and holding
    it odd is the whole content of the flag. Since A1.6 the bay count is no
    longer a faithful proxy for it — an even bay count with a central special is
    a legal centred composition — so asserting on the bay count would be
    asserting the old over-strong policy back into place. What the bay count is
    still held to is the one thing the contract says about it: on ADD_MODULE it
    changes by two, never one.
    """
    shape: list[tuple[float, int, int]] = []  # budget, run length, bay count
    fired = 0
    for budget in _budgets():
        try:
            result = solve(budget, **v.kwargs)
        except FitInfeasible:
            continue
        n = _bay_count(result, v)
        shape.append((budget, len(_run(result)), n))
        if result.rung is not Rung.ADD_MODULE:
            continue
        delta = n - _plain_count(budget, v)
        assert delta > 0 and delta % 2 == 0, f"{v.name} at {budget:.2f}: stepped by {delta}"
        fired += 1

    for (b0, r0, n0), (b1, r1, n1) in zip(shape, shape[1:]):
        assert r1 >= r0, f"{v.name}: run {r0} -> {r1} from {b0:.2f} to {b1:.2f} m"
        assert (r1 - r0) % 2 == 0, (
            f"{v.name}: interior run stepped by {r1 - r0} between {b0:.2f} and {b1:.2f} m"
        )
        # The bay count may fall by one *only* by handing that bay's place on the
        # run to the central special — the run is unchanged and a special has
        # appeared. Anything else would be the composition shrinking as the
        # frontage grows, which is a bug and not a swap.
        if n1 < n0:
            assert (n0 - n1, r1) == (1, r0), (
                f"{v.name}: {n0} -> {n1} bays between {b0:.2f} and {b1:.2f} m"
            )
    assert fired > 0, f"{v.name} never reached ADD_MODULE; the assertion above is vacuous"


@pytest.mark.parametrize("v", VOCABULARIES, ids=IDS)
def test_every_refusal_is_genuinely_infeasible(v: Vocabulary) -> None:
    """A refusal must be poverty of vocabulary, never a solver that gave up.

    For each width the solver refuses, every arrangement it is permitted to
    build is enumerated and shown to be unable to reach the budget inside the
    declared bounds. Each arrangement is a contiguous interval — all the bays
    take one width, both ends another, the specials a third — so the whole
    reachable set of a (bay count, special count) pair is [sum of minima, sum of
    maxima], and the test is exact rather than sampled.

    The enumeration must not restate the implementation's *policy*, only the
    contract's requirements — otherwise it cannot see a solver that narrowed
    itself. In particular it does **not** enumerate bay counts by parity. The
    requirement `central_feature` states is that something stands on the
    centreline, and an interior run of odd length is what does that, however the
    run is made up: `n` bays and a flanking pair, or `n` bays and one special at
    the middle. Filtering on `(n + n_fixed)` instead — the shape the old
    implementation happened to produce — is what let the narrowing A1.6 repairs
    hide here, because the test and the solver were skipping the same
    arrangements.

    Two of the solver's declared *design decisions* are honoured, because they
    are choices about what a good composition is rather than limits on what it
    can reach:

    * a narrow special answers surplus and never a shortfall — it is what the
      leftover becomes, not a filler the bays are squeezed to pay for;
    * a flanking pair is the symmetric answer a central composition wants, and
      is not offered to a composition that has no axis to be symmetric about.

    Both are load-bearing: drop either and this test starts flagging widths, so
    each is a real constraint on the answer rather than a hole in the check.
    """
    end = v.kwargs["end"]
    bay = v.kwargs["bay"]
    special = v.kwargs.get("special")
    central = bool(v.kwargs.get("central_feature"))
    n_fixed = len(v.kwargs.get("fixed", ()))
    reserved = _reserved(v)
    lo_bays = v.kwargs.get("min_bays", 1)
    hi_bays = v.kwargs.get("max_bays", 24)

    counts = (0,) if special is None else (0, 1, 2) if central else (0, 1)
    refused = 0
    for budget in _budgets():
        try:
            solve(budget, **v.kwargs)
            continue
        except FitInfeasible:
            refused += 1
        for n in range(lo_bays, hi_bays + 1):
            surplus = _slack_at(budget, v, n)
            for count in counts:
                if central and (n + n_fixed + count) % 2 == 0:
                    continue  # an even run leaves the centreline on a joint
                if count and surplus <= EPS:
                    continue  # a special answers surplus, never a shortfall
                # A pinned end cannot move, so its interval is a point.
                lo_end = end.preferred if end.pinned else end.minimum
                hi_end = end.preferred if end.pinned else end.maximum
                low = reserved + 2 * lo_end + n * bay.minimum
                high = reserved + 2 * hi_end + n * bay.maximum
                if count and special is not None:
                    low += count * special.minimum
                    high += count * special.maximum
                assert not (low - TOL <= budget <= high + TOL), (
                    f"{v.name} refused {budget:.2f} m, but {n} bay(s) and {count} "
                    f"special(s) reach [{low:.2f}, {high:.2f}]"
                )
    assert refused == 0 or v.covers_from > LO


def test_without_parity_the_module_count_can_step_by_one() -> None:
    """The control for the parity test: the step of 2 is a decision, not an artefact."""
    plain = Vocabulary("tight", _tight())
    stepped_by_one = 0
    for budget in _budgets():
        try:
            result = solve(budget, **plain.kwargs)
        except FitInfeasible:
            continue
        if result.rung is not Rung.ADD_MODULE:
            continue
        n = len([s for s in result.slots if s.name == "bay"])
        if n - _plain_count(budget, plain) == 1:
            stepped_by_one += 1
    assert stepped_by_one > 0


#: Above this width both vocabularies below are in steady state. The first
#: interval of each sequence is clipped by the bottom of the sweep — the widest
#: composition a 4 m budget admits is not the one the rhythm would have chosen —
#: so the counting below starts here rather than at LO.
STEADY_FROM = 10.0


def _run_changes(kwargs: dict[str, Any]) -> list[tuple[float, int, int]]:
    """(budget, before, after) at every width where the interior run grows or shrinks.

    The run, not the bay count: the run is what carries the centreline, so it is
    the quantity parity constrains. A central composition can trade one of its
    bays for the central special without the run changing at all, and that is a
    change of material, not a change of rhythm.
    """
    out: list[tuple[float, int, int]] = []
    previous: int | None = None
    for budget in _budgets():
        try:
            result = solve(budget, **kwargs)
        except FitInfeasible:
            continue
        n = len(_run(result))
        if previous is not None and n != previous and budget >= STEADY_FROM:
            out.append((budget, previous, n))
        previous = n
    return out


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


@pytest.mark.parametrize("base", [_ordinary, _tight], ids=["ordinary", "tight"])
def test_parity_makes_a_module_cost_twice_the_slack(base: Any) -> None:
    """The brief's claim measured as a price, which is what it is.

    Not "the central composition never reaches ADD_MODULE sooner at the same
    budget" — that is false and ought to be: parity closes half the compositions,
    so the rungs below the top do more of the work and the top one is reached
    from further back. The claim is that a module *costs twice as much*: the
    plain composition gains an element every bay-width of frontage, the central
    one every two, and it gains them two at a time.

    Measured on the interior run rather than the bay count, because since A1.6
    the two are no longer the same thing — a central composition may swap one of
    its bays for the central special without changing the rhythm at all.
    """
    plain = _run_changes(base())
    central = _run_changes(dict(**base(), central_feature=True))

    assert all(after - before == 1 for _b, before, after in plain)
    assert all(after - before == 2 for _b, before, after in central)
    assert 2 * len(central) == len(plain), (len(plain), len(central))

    plain_gaps = [b - a for (a, *_), (b, *_) in zip(plain, plain[1:])]
    central_gaps = [b - a for (a, *_), (b, *_) in zip(central, central[1:])]
    assert _median(central_gaps) >= 2 * _median(plain_gaps) - STEP


# ------------------------------------------------- A1.6: the centreline, not parity


def test_an_even_bay_count_with_a_central_special_is_a_legal_answer() -> None:
    """A1.6, from the verifier's own counter-example.

    8.05 m is a real Paris frontage and this vocabulary makes it exactly, once,
    and symmetrically. The arrangement is not a compromise the solver settles
    for: every slot is at or inside its bounds, the two bays are at their
    preferred width, and the special sits on the axis with the same composition
    either side of it. Refusing it was the solver imposing a rule of its own —
    "the bay count must be odd" — that no one asked for.
    """
    r = solve(8.05, **dict(**_ordinary(), central_feature=True))
    assert [round(s.width, 4) for s in r.slots] == [0.40, 3.00, 1.25, 3.00, 0.40]
    assert [s.is_special for s in r.slots] == [False, False, True, False, False]
    assert r.rung is Rung.INSERT_SPECIAL
    assert abs(math.fsum(s.width for s in r.slots) - 8.05) < TOL

    middle = r.slots[2]
    assert middle.start < 8.05 / 2 < middle.start + middle.width


@pytest.mark.parametrize("v", [v for v in VOCABULARIES if v.parity], ids=lambda v: v.name)
def test_the_centred_special_is_used_and_is_genuinely_central(v: Vocabulary) -> None:
    """The arrangement A1.6 restores must actually appear, and be centred when it does.

    ``_check`` asserts the invariant at every width; this asserts the invariant
    is not vacuous — that the even-run-with-a-central-special arrangement is
    reached often enough to be worth having, and that where it is reached the
    bays really do divide equally either side of the special.
    """
    used = 0
    for budget in _budgets():
        try:
            result = solve(budget, **v.kwargs)
        except FitInfeasible:
            continue
        run = _run(result)
        specials = [s for s in run if s.is_special]
        if len(specials) != 1:
            continue
        used += 1
        at = run.index(specials[0])
        assert at == len(run) // 2, [s.name for s in result.slots]
        assert at == len(run) - 1 - at  # the same number of elements either side
        assert _bay_count(result, v) % 2 == 0 or v.kwargs.get("fixed")
    assert used > 20, f"{v.name} never used the centred special: {used}"


def test_the_parity_fix_does_not_reintroduce_an_off_centre_special() -> None:
    """The narrowing A1.6 removes must not be replaced by a lopsided answer.

    This is the vocabulary the verifier used to show the misplacement: three bays
    and one special can make 10.90 m, but only as `bay special bay bay` or a
    mirror of it, with the special one place off the middle. That is worse than a
    refusal, because it looks like an answer. The solver must either find a
    genuinely centred arrangement or refuse.
    """
    kwargs = dict(
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.45, 0.50, 0.60),
        bay=SlotSpec("bay", SlotKind.REPEATING, 2.95, 3.00, 3.10),
        special=SlotSpec("special", SlotKind.FLEXIBLE, 0.90, 1.00, 1.20),
        min_bays=0,
    )
    for i in range(80, 721):
        budget = i * STEP
        try:
            result = solve(budget, central_feature=True, **kwargs)
        except FitInfeasible:
            continue
        run = _run(result)
        assert len(run) % 2 == 1, (budget, [s.name for s in result.slots])
        middle = run[len(run) // 2]
        assert middle.start + TOL < budget / 2.0 < middle.start + middle.width - TOL, (
            budget,
            [s.name for s in result.slots],
        )


# ------------------------------------------------- A1.8: `rigid` is not `FIXED`

#: A quoin: a FLEXIBLE slot with a genuinely wide declared range that is
#: nonetheless an ABSOLUTE quantity and must never move. The width of the range
#: is the whole point — a rigid slot whose bounds already pin it to `preferred`
#: proves nothing, because `SlotKind.FIXED` would produce the same answer.
RIGID_QUOIN = SlotSpec("quoin", SlotKind.FLEXIBLE, 0.30, 0.50, 1.20, rigid=True)
SUPPLE_QUOIN = SlotSpec("quoin", SlotKind.FLEXIBLE, 0.30, 0.50, 1.20)
_QUOIN_BAY = SlotSpec("bay", SlotKind.REPEATING, 2.40, 3.00, 3.60)
_QUOIN_SPECIAL = SlotSpec("special", SlotKind.FLEXIBLE, 0.80, 1.20, 1.80)


def _quoin_sweep(end: SlotSpec) -> list[tuple[float, float]]:
    """(budget, end width) at every width this vocabulary can make."""
    out: list[tuple[float, float]] = []
    for budget in _budgets():
        try:
            result = solve(
                budget, end=end, bay=_QUOIN_BAY, special=_QUOIN_SPECIAL, min_bays=0
            )
        except FitInfeasible:
            continue
        # The float residual lands on the last elastic slot, so the two ends
        # agree to within it rather than bit for bit.
        assert abs(result.slots[0].width - result.slots[-1].width) < TOL
        out.append((budget, result.slots[0].width))
    return out


def test_a_rigid_slot_never_drifts_even_when_its_range_is_wide() -> None:
    """A1.8: `rigid` is a fact about the quantity, not a synonym for `SlotKind.FIXED`.

    A quoin is dimensioned by the stone, not by the composition, so it carries an
    ABSOLUTE quantity — but it is still a FLEXIBLE slot, and its declared range
    is 0.30 to 1.20 m, nine tenths of a metre of latitude the solver could take
    if it were reading the kind instead of the flag. Across the whole sweep it
    takes none of it.

    Deriving `pinned` from `SlotKind.FIXED` alone passes every test that only
    ever declares rigid slots whose bounds already pin them; this one it fails at
    the first width with any slack, which is the point.
    """
    seen = {width for _b, width in _quoin_sweep(RIGID_QUOIN)}
    assert seen == {RIGID_QUOIN.preferred}
    assert len(_quoin_sweep(RIGID_QUOIN)) > 600


def test_the_rigid_flag_is_what_pins_it_and_nothing_else() -> None:
    """The control: the same slot without the flag drifts across most of its range.

    Without this, the test above could be passing because the sweep never
    produces slack for the ends to absorb — a green light meaning nothing. The
    identical spec with `rigid=False` moves over more than half a metre, so the
    latitude is real and the flag is what refuses it.
    """
    assert RIGID_QUOIN.pinned and not SUPPLE_QUOIN.pinned
    supple = {round(width, 6) for _b, width in _quoin_sweep(SUPPLE_QUOIN)}
    assert len(supple) > 20, supple
    assert max(supple) - min(supple) > 0.5, (min(supple), max(supple))
    assert max(supple) <= SUPPLE_QUOIN.maximum + TOL
    assert min(supple) >= SUPPLE_QUOIN.minimum - TOL


def test_a_rigid_end_still_fills_the_budget_exactly() -> None:
    """Pinning must not be bought by letting the arithmetic go slightly wrong.

    The residual has to land somewhere, and the one place it may never land is a
    pinned slot — so this checks the exactness requirement holds at the same
    widths where the pinning does.
    """
    for budget, width in _quoin_sweep(RIGID_QUOIN):
        assert width == RIGID_QUOIN.preferred
        result = solve(
            budget, end=RIGID_QUOIN, bay=_QUOIN_BAY, special=_QUOIN_SPECIAL, min_bays=0
        )
        assert abs(math.fsum(s.width for s in result.slots) - budget) < TOL
        assert result.residual < TOL


def test_the_sweep_is_deterministic() -> None:
    """I5: same input, same output, always. The solver draws no random numbers."""
    for v in VOCABULARIES:
        for budget in _budgets():
            if int(round(budget / STEP)) % 17:
                continue
            try:
                first = solve(budget, **v.kwargs)
            except FitInfeasible:
                with pytest.raises(FitInfeasible):
                    solve(budget, **v.kwargs)
                continue
            assert solve(budget, **v.kwargs) == first
