"""The generic 1-D budget solver: fill an exact budget with typed slots.

One solver serves both axes — storeys into a height budget, bays into a width.
Nothing in here knows which axis it is on, and nothing in here knows about
Paris.

Three decisions in this file are architectural rather than incidental, and are
the reason this is not a generic layout engine with a cosmetic gutter:

**The repeating unit is the bay, measured centreline-to-centreline of the
filler** — half-pier, opening, half-pier. `N` bays is therefore *exactly*
``N * bay_width`` and the only special case is the two ends, which is where you
wanted it. If the opening were the module and the pier the gap between modules,
every run would carry a permanent decision about whether it starts on a half
pier or a whole one, and the ends would infect the interior.

**Elasticity is per type, and that ordering IS the solver.** Slack is absorbed
into the most elastic thing available: ends first (they exist to be adjusted),
then the filler inside each bay (the pier thickens, the opening does not move),
then the bay as a whole (the opening itself stretches — visible past a few
percent). ``rigid=True`` slots carry ABSOLUTE quantities — a carriage entrance
must admit a carriage — and never absorb anything. Stretching a doorway to make
the arithmetic work is the move that destroys scale.

**Parity belongs to the composition, not to one rung.** ``central_feature``
says an element sits on the axis, and *that* — not any statement about bay
counts — is the whole invariant. Two arrangements satisfy it, and both are
chosen where the arrangement is chosen, before the ladder is climbed:

* an **odd interior run**, whose middle element stands on the centreline. This
  is the preferred answer because it needs no special at all, and it is the one
  the natural bay count is nudged towards.
* an **even interior run with one narrow special inserted at its middle** — the
  special *is* the centre. This is what makes narrow frontages reachable, where
  the odd count below is already too wide and the odd count above still too
  narrow; ``end | bay | special | bay | end`` is a perfectly ordinary Parisian
  composition and refusing it would be a solver giving up, not a vocabulary
  running out.

Every rung then preserves the run's parity: a flanking pair of specials adds
two, and ADD_MODULE steps by two. Enforcing parity only on the ADD_MODULE
increment would preserve whatever parity the bare ``floor()`` happened to
produce, which is the axis landing on a pier half the time.

**The leftover is architecturally meaningful.** Past the elastic range the
answer is not to pad but to insert a narrow special — a half-bay, a blind
panel, a small round window. Five good bays plus one narrow odd one reads far
better than six squeezed bays, so INSERT_SPECIAL sits *below* ADD_MODULE on the
ladder and is tried first.

Deterministic by construction: there is no RNG in this module at all.

Two interpretations this file had to make, because the frozen contract exposes
no separate "filler" slot and no placement rule for fixed slots:

* WIDEN_FILLER is bay growth attributable to the pier alone — the first
  ``FILLER_SHARE`` of the bay's declared headroom. Past that the opening has to
  stretch too, which is WIDEN_BAY. The caller declares the latitude by choosing
  ``bay.maximum``; this module only decides how much of that latitude the pier
  can plausibly account for on its own.
* ``fixed`` slots are *inserted into* the run rather than substituted for a bay:
  ``index_hint`` is the number of bays standing to the left of the fixed slot.
  A porte cochere therefore sits between two half-piers exactly as a bay does,
  and the centreline arithmetic of the remaining run is untouched.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

__all__ = [
    "EPS",
    "FILLER_SHARE",
    "FitInfeasible",
    "FitResult",
    "PlacedSlot",
    "Rung",
    "SlotKind",
    "SlotSpec",
    "solve",
]

#: Exactness tolerance. The contract requires exact fill to within 1e-9.
EPS = 1e-9

#: How much of a bay's headroom the *filler* can account for on its own. Below
#: this the pier thickens and the opening never moves (rung 2); above it the
#: opening has to stretch as well (rung 3). Expressed as a share of the caller's
#: declared headroom rather than an absolute figure, so a caller who declares
#: ``maximum == preferred`` correctly gets no filler rung at all.
FILLER_SHARE = 0.5

# Internal role tags. Identity of the SlotSpec object is not usable here — a
# caller may legitimately reuse one spec in two positions.
_END = "end"
_BAY = "bay"
_FIXED = "fixed"
_SPECIAL = "special"


class FitInfeasible(ValueError):
    """No arrangement inside the declared bounds sums to the budget.

    A subclass of ``ValueError`` so callers that only know the frozen contract
    still catch it. Raising is the only honest answer available: exact fill and
    bound-respect are both hard requirements, so a budget that cannot satisfy
    both has no valid result to return.
    """


class SlotKind(Enum):
    FIXED = "fixed"  # exactly `preferred`; never absorbs (use for ABSOLUTE)
    REPEATING = "repeating"  # the bay; count may change
    FLEXIBLE = "flexible"  # filler and ends; absorbs first


@dataclass(frozen=True)
class SlotSpec:
    name: str
    kind: SlotKind
    minimum: float
    preferred: float
    maximum: float
    elasticity: float = 1.0  # higher absorbs sooner. ends > filler > opening > door
    rigid: bool = False  # True for ABSOLUTE-kind: NEVER absorbs slack

    def __post_init__(self) -> None:
        # A spec whose bounds do not bracket its preferred width is a caller bug
        # that would otherwise surface as an unexplained infeasibility far away
        # from the line that caused it.
        if not all(
            math.isfinite(v) for v in (self.minimum, self.preferred, self.maximum)
        ):
            raise ValueError(f"slot {self.name!r}: non-finite bound")
        if not (self.minimum <= self.preferred <= self.maximum):
            raise ValueError(
                f"slot {self.name!r}: need minimum <= preferred <= maximum, got "
                f"{self.minimum} / {self.preferred} / {self.maximum}"
            )
        if self.minimum < 0.0:
            raise ValueError(f"slot {self.name!r}: negative minimum {self.minimum}")

    @property
    def pinned(self) -> bool:
        """Cannot absorb: an ABSOLUTE quantity, or a slot declared FIXED."""
        return self.rigid or self.kind is SlotKind.FIXED


class Rung(Enum):
    """The absorption ladder, in order. Recorded for the trace."""

    EXACT = 0  # no slack
    WIDEN_ENDS = 1
    WIDEN_FILLER = 2
    WIDEN_BAY = 3
    INSERT_SPECIAL = 4  # narrow special: half-bay, blind panel, oeil-de-boeuf
    ADD_MODULE = 5


@dataclass(frozen=True)
class PlacedSlot:
    name: str
    kind: SlotKind
    start: float
    width: float
    is_special: bool = False


@dataclass(frozen=True)
class FitResult:
    slots: tuple[PlacedSlot, ...]
    rung: Rung  # the highest rung the solver had to climb
    account: tuple[str, ...]  # what it did, step by step, for the trace
    residual: float  # must be < 1e-9


# --------------------------------------------------------------------------
# absorption — the ladder's lower rungs
# --------------------------------------------------------------------------

# Which rung an elastic tier corresponds to. Tier 0 is the pair of ends, tier 1
# the filler inside every bay, tier 2 the bay as a whole.
_TIER_RUNG = {0: Rung.WIDEN_ENDS, 1: Rung.WIDEN_FILLER, 2: Rung.WIDEN_BAY}


@dataclass(frozen=True)
class _Absorbed:
    end_w: float
    bay_w: float
    tier: int  # -1 == nothing had to move
    notes: tuple[str, ...] = field(default_factory=tuple)


def _absorb(delta: float, n_bays: int, end: SlotSpec, bay: SlotSpec) -> _Absorbed | None:
    """Push ``delta`` metres into the elastic tiers, most elastic first.

    ``delta`` may be negative: the same type ordering governs taking width back
    out, because the fact it encodes — which elements exist to be adjusted — is
    not a fact about direction. The rung reported is the *highest* tier that had
    to move, which is what makes the ladder monotonic in slack.
    """
    end_w = end.preferred
    bay_w = bay.preferred
    if abs(delta) <= EPS:
        return _Absorbed(end_w, bay_w, -1)

    sign = 1.0 if delta > 0.0 else -1.0
    remaining = abs(delta)
    verb = "widened" if sign > 0 else "narrowed"

    # (tier, elasticity, capacity, count). Sorted so the most elastic pool goes
    # first; with the contract's default elasticity of 1.0 everywhere that is
    # exactly ends -> filler -> bay, the ladder the brief specifies. `elasticity`
    # only bites when a caller deliberately reorders it.
    pools: list[tuple[int, float, float, int]] = []
    if not end.pinned:
        head = (end.maximum - end.preferred) if sign > 0 else (end.preferred - end.minimum)
        pools.append((0, end.elasticity, 2.0 * head, 2))
    if n_bays > 0 and not bay.pinned:
        head = (bay.maximum - bay.preferred) if sign > 0 else (bay.preferred - bay.minimum)
        pools.append((1, bay.elasticity, n_bays * head * FILLER_SHARE, n_bays))
        pools.append((2, bay.elasticity, n_bays * head * (1.0 - FILLER_SHARE), n_bays))
    pools.sort(key=lambda p: (-p[1], p[0]))

    tier = -1
    notes: list[str] = []
    for tier_id, _elasticity, capacity, count in pools:
        if remaining <= EPS:
            break
        take = min(remaining, max(capacity, 0.0))
        if take <= EPS:
            continue
        per = sign * take / count
        if tier_id == 0:
            end_w += per
            notes.append(f"{verb} both ends by {abs(per):.4f} m ({take:.4f} m absorbed)")
        else:
            bay_w += per
            what = "the filler in each bay" if tier_id == 1 else "each bay"
            notes.append(f"{verb} {what} by {abs(per):.4f} m ({take:.4f} m absorbed)")
        remaining -= take
        tier = max(tier, tier_id)

    if remaining > EPS:
        return None
    return _Absorbed(end_w, bay_w, tier, tuple(notes))


# --------------------------------------------------------------------------
# arrangement
# --------------------------------------------------------------------------


def _special_side(fixed: Sequence[tuple[int, SlotSpec]], n_bays: int) -> str:
    """Which end of the run a lone special answers.

    From the brief: when the entrance sits off-centre the composition should
    answer it, putting the narrow special on the opposite side. With no fixed
    slot to answer, the choice is arbitrary and is therefore pinned, so that the
    solver stays deterministic.
    """
    if not fixed:
        return "right"
    mean = sum(min(max(int(h), 0), n_bays) for h, _ in fixed) / len(fixed)
    return "right" if mean < n_bays / 2.0 else "left"


def _order_run(
    n_bays: int, bay: SlotSpec, fixed: Sequence[tuple[int, SlotSpec]]
) -> list[tuple[str, SlotSpec]]:
    """The interior run: bays with the fixed slots interleaved.

    ``index_hint`` is read as the number of bays standing to the left of the
    fixed slot, so hint 0 puts it first and hint ``n_bays`` puts it last.
    """
    keyed: list[tuple[int, int, str, SlotSpec]] = [
        (i, 1, _BAY, bay) for i in range(n_bays)
    ]
    for hint, spec in fixed:
        keyed.append((min(max(int(hint), 0), n_bays), 0, _FIXED, spec))
    keyed.sort(key=lambda t: (t[0], t[1]))  # stable: equal hints keep input order
    return [(role, spec) for _, _, role, spec in keyed]


def _centred(run_length: int) -> bool:
    """True when a run of this many interior elements has one on the axis.

    The whole content of ``central_feature``: an odd interior run has a middle
    element and an even one has a joint there. Stated once, so that the count
    chooser, the special chooser and the final self-check cannot drift apart.
    """
    return run_length % 2 == 1


def _centre_index(run_length: int) -> int:
    """Where a lone special goes to *become* the centre of an even run.

    Inserting at ``run_length // 2`` leaves exactly ``run_length // 2`` elements
    on each side, so the special is the middle element of the odd run that
    results. Stated as its own function because "the middle" is the only thing
    ``central_feature`` promises, and the caller and the self-check must agree on
    what it means down to the index.
    """
    return run_length // 2


def _place_specials(
    run: list[tuple[str, SlotSpec]], special: SlotSpec, count: int, side: str
) -> list[tuple[str, SlotSpec]]:
    """A pair flanks the run symmetrically; a lone special takes one side.

    With a central feature there are two symmetric answers. A flanking pair
    leaves the run's own middle element on the axis and adds two, so it never
    disturbs parity. A lone special *is* the middle: it may take the centre only
    of an **even** run, where inserting it at ``_centre_index`` puts the same
    number of elements on either side. Asking for a centred lone special on an
    odd run is incoherent — there is no index that divides the run evenly — and
    is refused here rather than silently placed off-centre.
    """
    out = list(run)
    if count >= 2:
        return [(_SPECIAL, special)] + out + [(_SPECIAL, special)]
    if side == "centre":
        if _centred(len(out)):
            raise RuntimeError(
                f"a lone centred special cannot be centred on a run of {len(out)}: "
                "no index divides an odd run evenly"
            )
        at = _centre_index(len(out))
        out.insert(at, (_SPECIAL, special))
        if at != len(out) - 1 - at:  # elements to its left, elements to its right
            raise RuntimeError(  # pragma: no cover - arithmetic tripwire
                f"the centred special landed at {at} of a run of {len(out)}, with "
                f"{at} element(s) left of it and {len(out) - 1 - at} right"
            )
        return out
    if side == "left":
        return [(_SPECIAL, special)] + out
    return out + [(_SPECIAL, special)]


def _assemble(
    budget: float,
    end: SlotSpec,
    end_w: float,
    bay_w: float,
    run: list[tuple[str, SlotSpec]],
    special_w: float,
) -> tuple[tuple[PlacedSlot, ...], float]:
    """Turn chosen widths into placed slots, then close the float gap exactly.

    The residual gap is float noise (order 1e-16), not a design decision, so it
    lands on an elastic slot and never on a pinned one — a pinned slot emerging
    at anything other than ``preferred`` is precisely the failure this solver
    exists to prevent.
    """
    specs: list[tuple[str, SlotSpec]] = [(_END, end)] + run + [(_END, end)]
    widths: list[float] = []
    for role, spec in specs:
        if role == _END:
            widths.append(end_w)
        elif role == _BAY:
            widths.append(bay_w)
        elif role == _SPECIAL:
            widths.append(special_w)
        else:
            widths.append(spec.preferred)

    err = budget - math.fsum(widths)
    if err != 0.0:
        for i in range(len(specs) - 1, -1, -1):
            if specs[i][1].pinned:
                continue
            widths[i] += err
            break

    slots: list[PlacedSlot] = []
    cursor = 0.0
    for (role, spec), w in zip(specs, widths):
        slots.append(
            PlacedSlot(
                name=spec.name,
                kind=spec.kind,
                start=cursor,
                width=w,
                is_special=(role == _SPECIAL),
            )
        )
        cursor += w

    # Bounds are re-checked on the assembled result rather than trusted from the
    # arithmetic that produced it, so no future change to the ladder can quietly
    # emit an out-of-range slot.
    for slot, (_role, spec) in zip(slots, specs):
        if spec.pinned and abs(slot.width - spec.preferred) > EPS:
            raise FitInfeasible(
                f"rigid slot {spec.name!r} would emerge at {slot.width}, "
                f"not {spec.preferred}"
            )
        if slot.width < spec.minimum - EPS or slot.width > spec.maximum + EPS:
            raise FitInfeasible(
                f"slot {spec.name!r} at {slot.width} outside "
                f"[{spec.minimum}, {spec.maximum}]"
            )

    residual = abs(budget - math.fsum(s.width for s in slots))
    return tuple(slots), residual


# --------------------------------------------------------------------------
# the ladder
# --------------------------------------------------------------------------


def _natural_count(
    avail: float, end: SlotSpec, bay: SlotSpec, *, min_bays: int = 1, max_bays: int = 24
) -> int:
    """The bay count the ladder starts from: whole preferred bays beside two ends."""
    if bay.preferred > EPS:
        raw = int(math.floor((avail - 2.0 * end.preferred) / bay.preferred + EPS))
    else:
        raw = max_bays
    return min(max(raw, min_bays), max_bays)


def _count_with_run_parity(
    natural: int, n_fixed: int, min_bays: int, max_bays: int, *, odd_run: bool
) -> int | None:
    """The count nearest ``natural`` whose interior run has the wanted parity.

    Parity is a property of *this* number, not of the ADD_MODULE increment:
    constrain the increment alone and the count still walks 1, 2, 3, 4 as the
    budget grows, putting the axis on a pier half the time.

    The adjustment goes *down* first. The preferred arrangement then still fits
    inside the budget, so slack stays non-negative and the ladder keeps its
    single meaning — absorb surplus, and add modules only when the surplus
    outgrows the vocabulary. Which is also the brief's claim made literal: a
    central composition rests with up to two bays of slack in hand, so step 5
    costs twice as much to reach.

    ``None`` means the wanted parity is unreachable inside ``min_bays..max_bays``
    — a fact about the caller's declared range, so it is returned rather than
    raised; the other parity may still have an answer.
    """
    if _centred(natural + n_fixed) == odd_run:
        return natural
    if natural - 1 >= min_bays:
        return natural - 1
    if natural + 1 <= max_bays:
        return natural + 1
    return None


def _rung4_arrangements(
    central: bool, n_odd: int | None, n_even: int | None
) -> tuple[tuple[int, int], ...]:
    """``(bay count, special count)`` pairs rung 4 may try, most preferred first.

    Without a central feature there is one arrangement: a lone special answering
    the entrance from the far side.

    With one there are two, and the order between them is a design decision. The
    flanking **pair** on an odd run comes first: it leaves the run's own middle
    element — a bay, or the entrance — on the axis, and it is the arrangement a
    wide facade wants. The lone **centred** special on an even run comes second,
    because it is the answer to a width the first cannot make: it puts the
    special itself on the centreline, which is how a narrow parcel gets a
    symmetric composition at all.
    """
    if not central:
        return () if n_odd is None else ((n_odd, 1),)
    out: list[tuple[int, int]] = []
    if n_odd is not None:
        out.append((n_odd, 2))
    if n_even is not None:
        out.append((n_even, 1))
    return tuple(out)


@dataclass(frozen=True)
class _Attempt:
    rung: Rung
    n_bays: int
    end_w: float
    bay_w: float
    special_w: float
    special_count: int
    special_side: str
    notes: tuple[str, ...]


def _plain(
    avail: float, n_bays: int, end: SlotSpec, bay: SlotSpec
) -> tuple[_Absorbed, float] | None:
    """Rungs 0-3: two ends plus ``n_bays`` bays, elastic tiers only."""
    slack = avail - 2.0 * end.preferred - n_bays * bay.preferred
    got = _absorb(slack, n_bays, end, bay)
    return None if got is None else (got, slack)


def _with_special(
    avail: float,
    n_bays: int,
    end: SlotSpec,
    bay: SlotSpec,
    special: SlotSpec,
    count: int,
) -> tuple[_Absorbed, float, float] | None:
    """Rung 4: give the surplus to ``count`` narrow specials, absorb the rest."""
    slack = avail - 2.0 * end.preferred - n_bays * bay.preferred
    if slack <= EPS:
        return None  # a special answers surplus; it can never answer a shortfall
    each = min(max(slack / count, special.minimum), special.maximum)
    got = _absorb(slack - count * each, n_bays, end, bay)
    return None if got is None else (got, each, slack)


def solve(
    budget: float,
    *,
    end: SlotSpec,
    bay: SlotSpec,
    special: SlotSpec | None = None,
    fixed: Sequence[tuple[int, SlotSpec]] = (),  # (index_hint, spec) e.g. carriage door
    central_feature: bool = False,  # parity: ADD_MODULE steps by 2
    min_bays: int = 1,
    max_bays: int = 24,
) -> FitResult:
    """Fill ``budget`` exactly with ends, bays, any fixed slots, and maybe a special.

    Climbs the absorption ladder only as far as it must, and returns an account
    of what it did, so that someone can later ask the solver why a facade came
    out the way it did and get an answer.
    """
    if not math.isfinite(budget) or budget <= 0.0:
        raise ValueError(f"budget must be finite and positive, got {budget}")
    if min_bays < 0:
        raise ValueError(f"min_bays must be >= 0, got {min_bays}")
    if max_bays < min_bays:
        raise ValueError(f"max_bays {max_bays} < min_bays {min_bays}")
    if bay.kind is not SlotKind.REPEATING:
        raise ValueError(f"bay slot {bay.name!r} must be SlotKind.REPEATING")
    fixed = tuple(fixed)

    reserved = math.fsum(spec.preferred for _, spec in fixed)
    avail = budget - reserved

    account: list[str] = [f"budget {budget:.4f} m"]
    if fixed:
        account.append(
            f"{len(fixed)} fixed slot(s) reserve {reserved:.4f} m at exactly their "
            "preferred width — absolute, so they never absorb"
        )

    # The natural count: as many whole bays at their preferred width as stand
    # beside two preferred ends. Slack is therefore in [0, bay.preferred) — or in
    # [0, 2 * bay.preferred) under parity — except where the budget is too small
    # even for `min_bays`, in which case the very same ladder runs downward.
    natural = _natural_count(avail, end, bay, min_bays=min_bays, max_bays=max_bays)
    if central_feature:
        # Two admissible families, because two arrangements put an element on the
        # axis: an odd run (its middle element is the centre) and an even run
        # carrying a lone central special (the special is the centre).
        n0 = _count_with_run_parity(
            natural, len(fixed), min_bays, max_bays, odd_run=True
        )
        n_axis = _count_with_run_parity(
            natural, len(fixed), min_bays, max_bays, odd_run=False
        )
    else:
        n0, n_axis = natural, None

    # One of the two families always contains `natural` itself, so there is
    # always a base count to report even when the other family is empty.
    base = natural if n0 is None or n_axis is None else n0
    account.append(
        f"{base} bay(s) at preferred {bay.preferred:.4f} m, centreline to centreline "
        f"= {base * bay.preferred:.4f} m"
    )
    if central_feature:
        account.append(
            "central feature: something must stand on the centreline — either the "
            "middle element of an odd run between the ends, or a lone narrow "
            "special inserted at the middle of an even one (a flanking pair of "
            "specials or a step of two modules keeps an odd run odd)"
        )

    step = 2 if central_feature else 1
    attempt: _Attempt | None = None

    # Rungs 0-3. Only an odd run can carry them: with no special in the
    # composition there is nothing to put on the axis but an element of the run
    # itself.
    got_plain = None if n0 is None else _plain(avail, n0, end, bay)
    if got_plain is not None and n0 is not None:
        got, slack = got_plain
        if got.tier < 0:
            attempt = _Attempt(
                Rung.EXACT, n0, got.end_w, got.bay_w, 0.0, 0, "", ("exact fill: no slack",)
            )
        else:
            attempt = _Attempt(
                _TIER_RUNG[got.tier],
                n0,
                got.end_w,
                got.bay_w,
                0.0,
                0,
                "",
                (f"slack {slack:+.4f} m",) + got.notes,
            )

    # Rung 4. Deliberately tried before adding a module: five good bays plus one
    # narrow odd one reads far better than six squeezed bays.
    if attempt is None and special is not None:
        for n, count in _rung4_arrangements(central_feature, n0, n_axis):
            got_s = _with_special(avail, n, end, bay, special, count)
            if got_s is None:
                continue
            got, each, slack = got_s
            side = "centre" if central_feature else _special_side(fixed, n)
            if count >= 2:
                placed = (
                    f"inserted {count} narrow specials {special.name!r} at "
                    f"{each:.4f} m each, flanking the run"
                )
            elif side == "centre":
                placed = (
                    f"inserted narrow special {special.name!r} at {each:.4f} m on the "
                    f"centreline, between {n + len(fixed)} element(s) — the special "
                    "itself is the centre"
                )
            else:
                placed = (
                    f"inserted narrow special {special.name!r} at {each:.4f} m ({side})"
                )
            notes: tuple[str, ...] = (f"slack {slack:+.4f} m exceeds the elastic range",)
            if n != base:
                notes += (
                    f"took {n} bay(s) rather than {base}, so the special lands on the "
                    "centreline",
                )
            attempt = _Attempt(
                Rung.INSERT_SPECIAL,
                n,
                got.end_w,
                got.bay_w,
                each,
                count,
                side,
                notes + (placed,) + got.notes,
            )
            break

    # Rung 5. Parity-aware: a composition with a central feature steps by two, so
    # it takes twice the slack to reach.
    if attempt is None and n0 is not None:
        for n in range(n0 + step, max_bays + 1, step):
            added = (
                f"added {n - n0} module(s), stepping by {step}"
                + (" to hold the central feature's parity" if central_feature else "")
                + f": {n0} -> {n} bays"
            )
            got_plain = _plain(avail, n, end, bay)
            if got_plain is not None:
                got, slack = got_plain
                attempt = _Attempt(
                    Rung.ADD_MODULE,
                    n,
                    got.end_w,
                    got.bay_w,
                    0.0,
                    0,
                    "",
                    (added, f"slack {slack:+.4f} m") + got.notes,
                )
                break
            if special is not None:
                # The step of two preserves the run's parity, so the odd family
                # stays odd and takes its specials as a flanking pair.
                for count in (2,) if central_feature else (1,):
                    got_s = _with_special(avail, n, end, bay, special, count)
                    if got_s is None:
                        continue
                    got, each, slack = got_s
                    side = "centre" if central_feature else _special_side(fixed, n)
                    attempt = _Attempt(
                        Rung.ADD_MODULE,
                        n,
                        got.end_w,
                        got.bay_w,
                        each,
                        count,
                        side,
                        (added, f"and {count} narrow special(s) at {each:.4f} m each")
                        + got.notes,
                    )
                    break
                if attempt is not None:
                    break

    if attempt is None:
        # Not a solver failure but a poverty of vocabulary: no arrangement the
        # caller declared can make this width. The narrow special is the element
        # that normally closes these gaps, and a central feature halves the bay
        # counts on offer, so say which of the two it was rather than leaving the
        # caller guessing.
        hint = ""
        if special is None:
            hint = "; no `special` was offered, and a narrow special is what closes gaps like this"
        elif central_feature:
            hint = (
                "; `central_feature` admits only arrangements that put an element on the "
                "centreline — an odd run between the ends, taking any specials as a "
                "symmetric pair, or an even run with one special at its middle — and "
                "neither reaches this width"
            )
        raise FitInfeasible(
            f"no arrangement of {min_bays}..{max_bays} bays fills {budget:.4f} m "
            f"within the declared bounds (ends {end.minimum}..{end.maximum}, "
            f"bays {bay.minimum}..{bay.maximum}, {reserved:.4f} m reserved){hint}"
        )

    run = _order_run(attempt.n_bays, bay, fixed)
    if attempt.special_count and special is not None:
        run = _place_specials(run, special, attempt.special_count, attempt.special_side)

    # Centring is re-checked on the assembled run for the same reason the bounds
    # are: it is the flag's entire content, and nothing downstream would notice
    # its absence. Unreachable — the arrangement was chosen for it, not hoped for.
    if central_feature:
        if not _centred(len(run)):
            raise RuntimeError(
                f"central_feature produced an interior run of {len(run)} elements, "
                "which leaves the centreline on a joint"
            )
        if attempt.special_count == 1 and run[_centre_index(len(run))][0] is not _SPECIAL:
            raise RuntimeError(
                "central_feature took a lone special, which must therefore be the "
                f"middle of the run, but the middle is {run[_centre_index(len(run))][0]!r}"
            )

    slots, residual = _assemble(
        budget, end, attempt.end_w, attempt.bay_w, run, attempt.special_w
    )

    account.extend(attempt.notes)
    account.append(f"rung {attempt.rung.name}; residual {residual:.3e} m")
    return FitResult(slots=slots, rung=attempt.rung, account=tuple(account), residual=residual)
