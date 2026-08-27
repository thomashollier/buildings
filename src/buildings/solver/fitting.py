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
increment would preserve whatever parity the natural count happened to fall
on, which is the axis landing on a pier half the time.

**The natural count is the closest one, not the largest one that fits.**
``_natural_count`` picks the bay count whose resulting widths land nearest
their preferred values, adding a bay and going narrower where that is nearer
than using one fewer and going wider, and it takes a count only if every slot
the count implies stays inside its own declared bounds. The ladder then starts
from a real answer rather than from the answer-from-below a ``floor()`` gives,
whose leftover has to be hidden somewhere.

**The leftover is architecturally meaningful.** Past the elastic range the
answer is not to pad but to insert a narrow special — a half-bay, a blind
panel, a small round window. Five good bays plus one narrow odd one reads far
better than six squeezed bays, so INSERT_SPECIAL sits *below* ADD_MODULE on the
ladder and is tried first.

**Every dimension is the caller's.** There is no width, no ratio and no class
table in this module, and no branch anywhere on what kind of building it is: a
caller that wants grand frontages to carry wider bays passes a wider ``bay``
band when the frontage is grand. The same goes for the ends, the entrance and
the specials. ``special`` accepts a *sequence* of specs for that reason — the
leftover takes the first one it fits, so the order is the caller's preference
order and "a half-bay, or failing that an oeil-de-boeuf" is something the
caller can simply say.

Deterministic by construction: there is no RNG in this module at all, and the
seam is deliberately drawn so that it never needs one. Where the choice of
absorber should vary between buildings — biased by class, or by how strained
the composition is — the *caller* makes that choice with its own seeded RNG and
hands the result in as an ordered list of specials and a set of bands. What
arrives here is a decision already taken, never a decision to be taken. Two
things exist to make that loop workable:

* ``FitResult.strain`` says how hard the answer had to be pushed, **per kind of
  slot** — 0 where it came out at its preferred width, 1 where it is sitting on
  a bound. Per slot rather than one number because the ends are the first thing
  spent and a single figure would read 1.0 almost everywhere; a caller watching
  for the *bay* drifting to the extremes of its band asks
  ``result.strain_of("bay")`` and re-solves with something else on offer.
* ``SlotSpec.affinity`` lets a caller name a *second*, softer ideal for a slot —
  the width some ratio would rather it had — which is consulted only to
  separate arrangements the real rule leaves tied.

**A positioned slot may be a member of the repeating pool.** ``fixed`` names
*where* a slot stands; it does not, on its own, say the slot stands outside the
rhythm. Which of those two it is, is the slot's own ``kind``:

* ``SlotKind.FIXED`` — the slot is reserved off the budget at ``preferred``
  before anything is divided, and never absorbs. This is for a positioned
  element genuinely too big for the rhythm to hold, whose width the run must
  work around.
* ``SlotKind.REPEATING`` — the slot **is** one of the modules. It occupies one
  place in the run at its index hint, it counts toward the module count, and it
  comes out at the same width every other module does. Its own
  ``[minimum, maximum]`` still bind, so a rhythm too narrow to hold it is
  refused rather than quietly delivered, and the caller is free to answer that
  refusal by re-solving with the slot declared FIXED instead — which is exactly
  "this one module has to grow".

That distinction is the whole of it, and note what it is *not*: it is not a
statement about what the slot is for. A positioned slot narrow enough to live
inside the rhythm should be in the rhythm, and only a slot the rhythm cannot
hold earns a module of its own. Nothing here knows or cares which is which; the
caller declares a kind and the arithmetic follows from it.

There is no iteration involved and none is needed. A pooled slot is a module,
so ``N`` modules beside two ends fill the budget by the same division they
always did — the circularity a caller might expect, where the module width
depends on the pooled slot's width and the pooled slot's width depends on the
module width, does not arise because the two are the same number.

One absorber the brief anticipates is still **not** supported and would need a
real change rather than a parameter: bays that vary symmetrically across the
run — narrower in the middle, wider at the ends, or the inverse. It would
attach at ``_absorb``, which is the one place that decides where slack goes.

Two interpretations this file had to make, because the frozen contract exposes
no separate "filler" slot and no placement rule for fixed slots:

* WIDEN_FILLER is bay growth attributable to the pier alone — the first
  ``FILLER_SHARE`` of the bay's declared headroom. Past that the opening has to
  stretch too, which is WIDEN_BAY. The caller declares the latitude by choosing
  ``bay.maximum``; this module only decides how much of that latitude the pier
  can plausibly account for on its own.
* ``fixed`` slots are *inserted into* the run rather than substituted for a bay:
  ``index_hint`` is the number of **ordinary bays** standing to the left of the
  positioned slot. A porte cochere therefore sits between two half-piers exactly
  as a bay does, and the centreline arithmetic of the remaining run is
  untouched.
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
_FIXED = "fixed"  # positioned, reserved off the budget, outside the rhythm
_POOLED = "pooled"  # positioned, but a member of the rhythm: takes the bay width
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
    #: A member of the rhythm. As the ``bay`` argument it is the module whose
    #: count may change; as a ``fixed`` entry it is a module that has been given
    #: a *place* in the run, and it comes out at the module width like any
    #: other. Same meaning in both positions — "this is one of the repeats" —
    #: which is why one kind serves both.
    REPEATING = "repeating"
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
    #: A second width this slot *leans* toward. Not a bound, not a target the
    #: solver will pay anything to reach, and never a reason to refuse a
    #: budget: it separates arrangements that the real rule — distance from
    #: ``preferred`` — leaves tied, and does nothing whatever otherwise. A
    #: caller with two incompatible ideals for the same slot declares the one
    #: it insists on as ``preferred`` and the one it would merely like as
    #: ``affinity``, and gets exactly that ordering. ``None`` means no lean.
    affinity: float | None = None

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
        # A lean toward a width that is not a width is a caller bug of the same
        # species. It is deliberately NOT required to lie inside the bounds:
        # leaning toward something the slot cannot quite reach is a coherent
        # thing to say, and means "get as close to it as the bounds allow".
        if self.affinity is not None and not math.isfinite(self.affinity):
            raise ValueError(f"slot {self.name!r}: non-finite affinity {self.affinity}")

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
    #: How hard the answer had to be pushed, **per kind of slot**, worst first:
    #: ``(name, fraction)`` pairs where the fraction is how much of that slot's
    #: own declared latitude the answer consumed, up to 1 sitting exactly on a
    #: bound. Pinned slots never appear — they did not move and were never
    #: going to — and neither do slots that came out at their preferred width,
    #: so an empty tuple means nothing had to move at all.
    #:
    #: Reported per slot rather than as one number because the one number is
    #: nearly always about the ends. They are the most elastic thing in the
    #: composition and therefore the first to be spent, so a single worst-slot
    #: figure reads 1.0 on most frontages and discriminates nothing. What a
    #: caller actually wants to know is whether *the bay* is drifting toward
    #: the extremes of its band, which is this, keyed by name.
    #:
    #: **It exists to be read and acted on.** A rhythm that comes back at 0.95
    #: is one the vocabulary only just reached, and the answer to that is a
    #: *different vocabulary* — wider ends, another kind of special, an
    #: entrance allowed to take some of the slack — not a different solver. The
    #: caller re-solves with what it decides to offer, and because it decides,
    #: it is also where any randomness lives: this module has no RNG and must
    #: not acquire one.
    strain: tuple[tuple[str, float], ...] = ()

    def strain_of(self, name: str) -> float:
        """How strained the slot called ``name`` came out, 0.0 if it never moved."""
        for slot_name, fraction in self.strain:
            if slot_name == name:
                return fraction
        return 0.0

    @property
    def worst_strain(self) -> float:
        """The most strained slot's fraction, or 0.0 if nothing had to move."""
        return self.strain[0][1] if self.strain else 0.0


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


def _is_pooled(spec: SlotSpec) -> bool:
    """True when a positioned slot is a member of the rhythm rather than beside it.

    Stated once, as a function, because four places need the same answer and a
    solver where the count chooser and the assembler disagreed about whether an
    element is a module would be very hard to read backwards from.
    """
    return spec.kind is SlotKind.REPEATING


def _order_run(
    n_modules: int, bay: SlotSpec, fixed: Sequence[tuple[int, SlotSpec]]
) -> list[tuple[str, SlotSpec]]:
    """The interior run: modules with the positioned slots interleaved.

    ``n_modules`` counts every element that comes out at the module width,
    which includes any positioned slot declared REPEATING — those occupy one of
    the modules rather than standing beside them, so the ordinary bays this
    lays down are ``n_modules`` less the number of pooled slots.

    ``index_hint`` is read as the number of **ordinary bays** standing to the
    left of the positioned slot, so hint 0 puts it first and a hint at or past
    the bay count puts it last. Counting only ordinary bays keeps the hint
    meaning one thing whichever kind the caller declared, so a caller may
    re-solve with the other kind and the same hint and get the same placement.
    """
    n_bays = n_modules - sum(1 for _h, s in fixed if _is_pooled(s))
    keyed: list[tuple[int, int, str, SlotSpec]] = [
        (i, 1, _BAY, bay) for i in range(max(n_bays, 0))
    ]
    for hint, spec in fixed:
        role = _POOLED if _is_pooled(spec) else _FIXED
        keyed.append((min(max(int(hint), 0), max(n_bays, 0)), 0, role, spec))
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
) -> tuple[tuple[PlacedSlot, ...], float, tuple[tuple[str, float], ...]]:
    """Turn chosen widths into placed slots, then close the float gap exactly.

    Width is assigned by **role**, and the roles are the whole of the geometry:
    the two ends take ``end_w``, every module takes ``bay_w`` — including a
    positioned slot the caller declared REPEATING, which is what makes it a
    member of the rhythm rather than an interruption in it — a special takes
    ``special_w``, and a reserved positioned slot takes the ``preferred`` it
    reserved.

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
        elif role in (_BAY, _POOLED):
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
    for slot, (role, spec) in zip(slots, specs):
        if spec.pinned and abs(slot.width - spec.preferred) > EPS:
            raise FitInfeasible(
                f"rigid slot {spec.name!r} would emerge at {slot.width}, "
                f"not {spec.preferred}"
            )
        if slot.width < spec.minimum - EPS or slot.width > spec.maximum + EPS:
            # A pooled slot out of its own band is the one case here that has a
            # named remedy rather than being a dead end: the rhythm this run
            # settled on is not one this module can be a member of, so it has
            # to stop being a member and take a module of its own. That is a
            # decision about the composition, so it is the caller's to take —
            # by re-solving with the slot declared FIXED — and saying so is the
            # difference between a refusal and a refusal one can act on.
            remedy = (
                (
                    f"; {spec.name!r} is positioned IN the repeating pool, and this "
                    f"rhythm is one it cannot be a member of. Re-solve with it "
                    "declared SlotKind.FIXED to give it a module of its own"
                )
                if role == _POOLED
                else ""
            )
            raise FitInfeasible(
                f"slot {spec.name!r} at {slot.width} outside "
                f"[{spec.minimum}, {spec.maximum}]{remedy}"
            )

    residual = abs(budget - math.fsum(s.width for s in slots))
    return tuple(slots), residual, _strain(slots, [spec for _role, spec in specs])


def _strain(
    slots: Sequence[PlacedSlot], specs: Sequence[SlotSpec]
) -> tuple[tuple[str, float], ...]:
    """Per slot name, the fraction of its own latitude this answer consumed.

    Measured against each slot's *own* headroom in the direction it actually
    moved, so it says "this element is near its limit" rather than "this
    element moved a lot" — a bay with 0.60 m of room to grow and a pier with
    0.05 m are not comparable in metres and are exactly comparable here.

    A pinned slot has no latitude and contributes nothing: it did not move,
    and it was never going to. A slot whose band is a single point likewise —
    dividing by a zero range would report infinite strain for an element that
    is simply fixed.

    Keyed by name and not by position, because two slots with the same name are
    the same *kind* of element and a caller asking "how hard is the bay being
    pushed" wants one answer, not one per bay. Where they disagree — they
    should not, the ladder moves a tier together — the worst is reported.
    Sorted worst first, and ties broken by name so the order is total.
    """
    worst: dict[str, float] = {}
    for slot, spec in zip(slots, specs):
        if spec.pinned:
            continue
        delta = slot.width - spec.preferred
        room = (spec.maximum - spec.preferred) if delta > 0.0 else (
            spec.preferred - spec.minimum
        )
        if room <= EPS:
            continue
        fraction = min(abs(delta) / room, 1.0)
        worst[spec.name] = max(worst.get(spec.name, 0.0), fraction)
    return tuple(
        sorted(
            ((name, f) for name, f in worst.items() if f > EPS),
            key=lambda kv: (-kv[1], kv[0]),
        )
    )


# --------------------------------------------------------------------------
# the ladder
# --------------------------------------------------------------------------


def _slack(avail: float, n_bays: int, end: SlotSpec, bay: SlotSpec) -> float:
    """What two preferred ends and ``n_bays`` preferred bays leave over.

    One statement of it, because three places need the number and a facade
    where the count chooser and the ladder disagreed about how much was left
    over would be very hard to read backwards from.
    """
    return avail - 2.0 * end.preferred - n_bays * bay.preferred


def _plain(
    avail: float, n_bays: int, end: SlotSpec, bay: SlotSpec
) -> tuple[_Absorbed, float] | None:
    """Rungs 0-3: two ends plus ``n_bays`` bays, elastic tiers only."""
    slack = _slack(avail, n_bays, end, bay)
    got = _absorb(slack, n_bays, end, bay)
    return None if got is None else (got, slack)


def _counts_by_closeness(
    avail: float, end: SlotSpec, bay: SlotSpec, min_bays: int, max_bays: int
):
    """``min_bays..max_bays``, nearest-filling first.

    Yields every allowed count exactly once, in non-decreasing order of
    ``abs(_slack(...))`` — i.e. starting from the count whose preferred bays
    and preferred ends come nearest to filling the budget on their own, and
    walking outward from it. Two pointers rather than a sort: the sequence is
    V-shaped about the real-valued ideal, so the next-closest count is always
    one of the two frontiers.

    Ordering the search this way is what lets the caller stop at the first
    count the bounds allow instead of scoring the whole range: everything after
    it is strictly further from preferred.
    """
    down = int(math.floor((avail - 2.0 * end.preferred) / bay.preferred + 0.5))
    down = min(max(down, min_bays), max_bays)
    up = down + 1
    while down >= min_bays or up <= max_bays:
        if down < min_bays:
            take_down = False
        elif up > max_bays:
            take_down = True
        else:
            take_down = abs(_slack(avail, down, end, bay)) <= abs(
                _slack(avail, up, end, bay)
            )
        if take_down:
            yield down
            down -= 1
        else:
            yield up
            up += 1


def _departure(n_bays: int, end: SlotSpec, bay: SlotSpec, got: _Absorbed) -> float:
    """How far, in metres, an arrangement lands from its preferred widths.

    Summed over every slot the arrangement actually contains — two ends and
    ``n_bays`` bays — rather than averaged or taken per slot, because the
    question being asked is about the whole geometry and not about its worst
    element. Distance is measured in metres and not as a fraction of each
    slot's declared latitude: a bay 0.43 m off its preferred width is 0.43 m
    off it whether the caller left the bay generous headroom or none, and it
    is the width a bricklayer sets out, not the headroom, that a facade shows.

    Two consequences worth knowing, because they are what make this cheap and
    what make it safe to scan the whole declared range:

    * For any arrangement that fills the budget exactly this sum is precisely
      ``abs(slack)`` — the deviations all share the sign of the slack and they
      have to add up to it. So ranking by departure is ranking by how nearly
      ``n`` preferred bays and two preferred ends fill the budget on their own.
    * It is therefore V-shaped in ``n``, with its floor at the real-valued
      ideal. Counts far from that ideal cannot win, whatever else is true of
      them.
    """
    return 2.0 * abs(got.end_w - end.preferred) + n_bays * abs(got.bay_w - bay.preferred)


def _affinity_miss(end: SlotSpec, bay: SlotSpec, got: _Absorbed) -> float:
    """How far the arrangement sits from any width the caller declared a lean to.

    Per slot rather than summed over the run, unlike ``_departure``. A lean is
    a statement about a *proportion* — the caller's example is the ratio of an
    opening to the bay carrying it — and a proportion is no more wrong for
    being repeated eleven times than for being repeated three. Summing would
    make the miss grow with the bay count and quietly turn a preference about
    shape into a preference for fewer bays.

    Slots that declared no ``affinity`` contribute nothing, so a vocabulary
    that declares none scores zero everywhere and this never decides anything.
    """
    miss = 0.0
    if end.affinity is not None:
        miss += abs(got.end_w - end.affinity)
    if bay.affinity is not None:
        miss += abs(got.bay_w - bay.affinity)
    return miss


def _natural_count(
    avail: float, end: SlotSpec, bay: SlotSpec, *, min_bays: int = 1, max_bays: int = 24
) -> int:
    """The bay count the ladder starts from: the one that lands closest.

    This used to be a bare ``floor()`` — as many whole preferred bays as stand
    beside two preferred ends — which always rounds *down* and leaves the whole
    remainder for the ladder to hide. On a frontage a hair short of the next
    whole bay that is the wrong answer twice over: the ends saturate at their
    maximum and every bay inflates to near its own, when one more bay would
    have sat a few centimetres inside the preferred width. Flooring does not
    choose the closest arrangement, it chooses the closest arrangement *from
    below*, and nothing in the brief ever asked for the second thing.

    So: try every count the caller allows, and take the one whose resulting
    slots land closest to their preferred widths — narrower with one more bay
    or wider with one fewer, whichever is nearer. A count is **eligible** only
    if the arrangement it implies is one the declared bounds actually permit,
    which is exactly the question ``_absorb`` already answers: it returns
    ``None`` when the slack will not go into the elastic tiers without pushing
    some slot outside its own ``[minimum, maximum]``. Rigid slots are excluded
    from those tiers there, so an eligible count never buys its closeness out
    of an ABSOLUTE quantity.

    Ties — possible only where the budget falls exactly between two counts —
    are settled in three steps, each of which is a real preference rather than
    a coin-flip, because this module is deterministic by construction and an
    arbitrary choice here would move a whole window axis:

    1. any ``affinity`` the caller declared, which is where a *soft* second
       ideal gets its say and the only place it gets one;
    2. then the arrangement that disturbed the *more* elastic tier — ends
       before filler before bay, the ladder's own ordering;
    3. then the smaller count.

    **When nothing is eligible, the old floor is returned unchanged**, and that
    is not a fallback bolted on for safety — it is what keeps the rest of the
    ladder meaning what it meant. Rungs 4 and 5 exist for widths that no plain
    arrangement reaches, and ``_with_special`` can only answer a *surplus*, so
    they need a count with slack in hand. Since a count is eligible exactly
    when its plain arrangement fits, "nothing is eligible" is precisely the
    case where rungs 0-3 were going to fail anyway; handing back the floor
    leaves those widths — the ones the narrow special exists to close — solved
    exactly as before.

    The search walks *outward* from the nearest-filling count rather than
    testing only the two counts either side of it, so where the bounds forbid
    the nearest one — a bay minimum that will not let the run go that narrow,
    say — it finds the nearest count that is allowed instead of stepping down
    one and giving up. And because ``_counts_by_closeness`` yields in
    non-decreasing distance and departure *is* that distance, the first
    eligible count it reaches is already the answer: everything after it is
    strictly further from preferred. So this normally costs one or two probes,
    and only walks the whole range in the case where nothing at all fits.
    """
    if bay.preferred <= EPS:
        # A degenerate spec: bays of no width, so the count says nothing about
        # the geometry and every candidate has the same departure. Answer as
        # this function always has.
        return min(max(max_bays, min_bays), max_bays)

    best_n: int | None = None
    best_departure = 0.0
    best_key: tuple[float, int] = (0.0, 0)
    for n in _counts_by_closeness(avail, end, bay, min_bays, max_bays):
        slack = _slack(avail, n, end, bay)
        if best_n is not None and abs(slack) > best_departure + EPS:
            break  # ordered by closeness: nothing further out can beat it
        got = _absorb(slack, n, end, bay)
        if got is None:
            continue  # not eligible: some slot would leave its own bounds
        departure = _departure(n, end, bay, got)
        key = (_affinity_miss(end, bay, got), got.tier)
        if best_n is None or key < best_key:
            best_n, best_departure, best_key = n, departure, key
    if best_n is not None:
        return best_n

    raw = int(math.floor((avail - 2.0 * end.preferred) / bay.preferred + EPS))
    return min(max(raw, min_bays), max_bays)


def _count_with_run_parity(
    natural: int, n_fixed: int, min_bays: int, max_bays: int, *, odd_run: bool
) -> int | None:
    """The count nearest ``natural`` whose interior run has the wanted parity.

    Parity is a property of *this* number, not of the ADD_MODULE increment:
    constrain the increment alone and the count still walks 1, 2, 3, 4 as the
    budget grows, putting the axis on a pier half the time.

    The adjustment goes *down* first, and deliberately still does now that
    ``natural`` is the closest count rather than the largest that fits. Going
    down adds a whole bay's worth of slack, so the parity-corrected count keeps
    surplus in hand — and surplus is the only thing rung 4 can answer, since a
    narrow special is inserted into a leftover and cannot be inserted into a
    shortfall. Correcting parity *upward* would hand the special path a
    negative slack and take rung 4 off the ladder for every central
    composition, which is a worse trade than the extra distance from preferred
    that going down costs. Which is also the brief's claim made literal: a
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
    #: Which of the caller's specials this attempt took, if any. Carried on the
    #: attempt rather than looked up again later, so that the spec the widths
    #: were computed against is the spec that gets placed.
    special_spec: SlotSpec | None = None


def _with_special(
    avail: float,
    n_bays: int,
    end: SlotSpec,
    bay: SlotSpec,
    special: SlotSpec,
    count: int,
) -> tuple[_Absorbed, float, float] | None:
    """Rung 4: give the surplus to ``count`` narrow specials, absorb the rest."""
    slack = _slack(avail, n_bays, end, bay)
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
    special: SlotSpec | Sequence[SlotSpec] | None = None,
    fixed: Sequence[tuple[int, SlotSpec]] = (),  # (index_hint, spec) e.g. carriage door
    central_feature: bool = False,  # parity: ADD_MODULE steps by 2
    min_bays: int = 1,
    max_bays: int = 24,
) -> FitResult:
    """Fill ``budget`` exactly with ends, bays, any fixed slots, and maybe a special.

    Climbs the absorption ladder only as far as it must, and returns an account
    of what it did, so that someone can later ask the solver why a facade came
    out the way it did and get an answer.

    **Everything this function decides, it decides from what it was handed.**
    There is no table of widths in this module and no branch on what kind of
    building it is: a caller that wants grand frontages to carry wider bays
    passes a wider ``bay`` band for grand frontages, and one that wants a
    narrower rhythm passes a narrower one. The same is true of the ends, of
    the entrance, and of the specials. That is not a convenience, it is the
    reason one solver can serve both axes.

    ``special`` accepts **several specs**, and the order is the caller's
    preference order. A leftover the vocabulary has to answer is offered each
    in turn and takes the first that fits — so "a half-bay, or failing that an
    oeil-de-boeuf" is written by passing the two in that order, and a caller
    that wants the choice to vary with the building shuffles the sequence
    before it calls. **That is where any randomness belongs**: this module is
    deterministic by construction, so a biased choice among specials is made by
    the caller with the caller's own seeded RNG and arrives here as an ordered
    list, which is a decision already taken rather than one to be taken.

    ``fixed`` places a slot at an index; the slot's own ``kind`` says whether it
    stands **in** the rhythm or beside it. A ``SlotKind.REPEATING`` entry is one
    of the modules — it reserves nothing, it counts toward the module count, and
    it comes out at the module width, so a run of them is one pitch throughout.
    A ``SlotKind.FIXED`` entry is reserved off the budget at ``preferred`` and
    the rhythm divides what is left. The first is the right declaration for a
    positioned element the rhythm can hold; the second for one it cannot.

    A pooled slot's own ``[minimum, maximum]`` still bind. Where the rhythm this
    budget settles on falls outside them, the solve is **refused** rather than
    delivered out of band, and the answer to that refusal is a *composition*
    decision the caller owns: re-solve with the slot declared FIXED and it gets
    a module of its own, wider than the rest. That is deliberately not decided
    here. Whether an element too big for the rhythm should break the rhythm or
    the rhythm should open up for it is a question about the thing being built,
    and this module does not know what is being built.

    ``min_bays`` and ``max_bays`` bound the **ordinary** bays — the anonymous
    repeats — so they mean the same thing whichever kind a positioned slot is
    declared, and a caller may re-solve with the other kind without rewriting
    them. ``min_bays=0`` therefore admits a run consisting of nothing but the
    positioned slots.

    Read ``FitResult.strain`` to find out whether the answer was comfortable.
    A caller that gets back a strained composition and wants to try a different
    absorber — wider ends, another special, an entrance permitted to take some
    of the slack — changes what it offers and calls again.
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
    for _hint, spec in fixed:
        if _is_pooled(spec) and spec.rigid:
            # Contradictory: pooling a slot is exactly saying its width is the
            # rhythm's to set, and ``rigid`` is exactly saying nothing may set
            # it. Caught here rather than allowed to surface as a bounds
            # failure in ``_assemble`` on some frontage far from the call.
            raise ValueError(
                f"positioned slot {spec.name!r} is REPEATING and rigid=True: a member "
                "of the repeating pool takes the module width, which a rigid slot by "
                "definition never does. Declare it SlotKind.FIXED to keep it rigid, or "
                "drop rigid to let it join the rhythm"
            )
    specials: tuple[SlotSpec, ...] = (
        () if special is None
        else (special,) if isinstance(special, SlotSpec)
        else tuple(special)
    )

    # Positioned slots split two ways, and the split is the slot's own `kind`.
    # A pooled one IS a module: it reserves nothing, it counts toward the module
    # count, and it comes out at the module width. A reserved one stands beside
    # the rhythm and is taken off the budget before anything is divided.
    n_pooled = sum(1 for _h, s in fixed if _is_pooled(s))
    n_reserved = len(fixed) - n_pooled
    reserved = math.fsum(spec.preferred for _, spec in fixed if not _is_pooled(spec))
    avail = budget - reserved

    # Counts inside this function are **module** counts — every element that
    # comes out at the bay width, pooled positioned slots included — because
    # that is the number the arithmetic is about. The caller's `min_bays` and
    # `max_bays` bound the ORDINARY bays, so the two differ by exactly the
    # number of pooled slots and are converted once, here.
    lo_modules = min_bays + n_pooled
    hi_modules = max_bays + n_pooled

    account: list[str] = [f"budget {budget:.4f} m"]
    if n_reserved:
        account.append(
            f"{n_reserved} fixed slot(s) reserve {reserved:.4f} m at exactly their "
            "preferred width — absolute, so they never absorb"
        )
    if n_pooled:
        account.append(
            f"{n_pooled} positioned slot(s) stand IN the repeating pool: each takes one "
            "of the modules and comes out at the module width, so the rhythm runs "
            "through them rather than around them"
        )

    # The natural count: the count whose bays and ends land closest to their
    # preferred widths, out of those the declared bounds allow. Slack is
    # therefore in [-bay.preferred / 2, +bay.preferred / 2] whenever any count
    # is allowed at all — the ladder runs downward as readily as upward, which
    # is why `_absorb` was written to take a signed delta. Where no count is
    # allowed the old floor comes back instead, slack is non-negative again,
    # and rungs 4 and 5 get the surplus they need to work with.
    natural = _natural_count(avail, end, bay, min_bays=lo_modules, max_bays=hi_modules)
    if central_feature:
        # Two admissible families, because two arrangements put an element on the
        # axis: an odd run (its middle element is the centre) and an even run
        # carrying a lone central special (the special is the centre). Only the
        # RESERVED positioned slots are extra elements of the run — a pooled one
        # is already inside the module count, so counting it again here would
        # get the run's parity wrong by one per pooled slot.
        n0 = _count_with_run_parity(
            natural, n_reserved, lo_modules, hi_modules, odd_run=True
        )
        n_axis = _count_with_run_parity(
            natural, n_reserved, lo_modules, hi_modules, odd_run=False
        )
    else:
        n0, n_axis = natural, None

    # One of the two families always contains `natural` itself, so there is
    # always a base count to report even when the other family is empty.
    base = natural if n0 is None or n_axis is None else n0
    account.append(
        f"{base} module(s) at preferred {bay.preferred:.4f} m, centreline to centreline "
        f"= {base * bay.preferred:.4f} m"
        + (f" ({n_pooled} of them a positioned slot in the pool)" if n_pooled else "")
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
    #
    # The specials are tried in the order the caller listed them, and the first
    # that fits is taken. The order is therefore a design statement — "a
    # half-bay, or failing that an oeil-de-boeuf" — and a caller that wants the
    # choice to vary between buildings arrives here with the list already
    # shuffled, because the shuffling is a decision and decisions are not made
    # in this module.
    if attempt is None and specials:
        for n, count in _rung4_arrangements(central_feature, n0, n_axis):
            for spec in specials:
                got_s = _with_special(avail, n, end, bay, spec, count)
                if got_s is None:
                    continue
                got, each, slack = got_s
                side = (
                    "centre" if central_feature else _special_side(fixed, n - n_pooled)
                )
                if count >= 2:
                    placed = (
                        f"inserted {count} narrow specials {spec.name!r} at "
                        f"{each:.4f} m each, flanking the run"
                    )
                elif side == "centre":
                    placed = (
                        f"inserted narrow special {spec.name!r} at {each:.4f} m on the "
                        f"centreline, between {n + len(fixed)} element(s) — the special "
                        "itself is the centre"
                    )
                else:
                    placed = (
                        f"inserted narrow special {spec.name!r} at {each:.4f} m ({side})"
                    )
                notes: tuple[str, ...] = (
                    f"slack {slack:+.4f} m exceeds the elastic range",
                )
                if len(specials) > 1:
                    notes += (
                        f"took {spec.name!r}, the first of {len(specials)} special(s) "
                        "the caller offered that this leftover fits",
                    )
                if n != base:
                    notes += (
                        f"took {n} bay(s) rather than {base}, so the special lands on "
                        "the centreline",
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
                    spec,
                )
                break
            if attempt is not None:
                break

    # Rung 5. Parity-aware: a composition with a central feature steps by two, so
    # it takes twice the slack to reach.
    if attempt is None and n0 is not None:
        for n in range(n0 + step, hi_modules + 1, step):
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
            if specials:
                # The step of two preserves the run's parity, so the odd family
                # stays odd and takes its specials as a flanking pair.
                for count in (2,) if central_feature else (1,):
                    for spec in specials:
                        got_s = _with_special(avail, n, end, bay, spec, count)
                        if got_s is None:
                            continue
                        got, each, slack = got_s
                        side = (
                            "centre"
                            if central_feature
                            else _special_side(fixed, n - n_pooled)
                        )
                        attempt = _Attempt(
                            Rung.ADD_MODULE,
                            n,
                            got.end_w,
                            got.bay_w,
                            each,
                            count,
                            side,
                            (
                                added,
                                f"and {count} narrow special(s) {spec.name!r} at "
                                f"{each:.4f} m each",
                            )
                            + got.notes,
                            spec,
                        )
                        break
                    if attempt is not None:
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
        if not specials:
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
    if attempt.special_count and attempt.special_spec is not None:
        run = _place_specials(
            run, attempt.special_spec, attempt.special_count, attempt.special_side
        )

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

    slots, residual, strain = _assemble(
        budget, end, attempt.end_w, attempt.bay_w, run, attempt.special_w
    )

    account.extend(attempt.notes)
    account.append(
        "rung {}; residual {:.3e} m; strain {} (share of each slot's own latitude "
        "spent: 0 = at its preferred width, 1 = on its bound)".format(
            attempt.rung.name,
            residual,
            ", ".join(f"{name} {value:.2f}" for name, value in strain) or "none",
        )
    )
    return FitResult(
        slots=slots,
        rung=attempt.rung,
        account=tuple(account),
        residual=residual,
        strain=strain,
    )
