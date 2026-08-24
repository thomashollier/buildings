"""Phase 2 — the roles phase (S4).

Identity is DERIVED, never declared. Phase 1 (``structure.solve_structure``)
hands us a ``Grid``: a stack of storey slots with no idea which one is the
ground floor, which is the noble floor, which is the attic. Nothing in this
module says "storey 2 is the principal floor" — it says what makes a slot
*principal* (the uniquely tallest habitable slot above the base and the
compressed level) and lets the label fall out of walking the stack. That is what removes
the fixed floor enumeration the brief names as the failure mode: a five-storey
and a nine-storey building get correct roles from the *same* predicates, with
no special case for the extra storeys, because nothing here enumerates
positions.

Five predicates, exactly as CONTRACTS.md and the brief state them:

- **Base** — the bottom slot. Unconditional.
- **Mezzanine** — the *compressed level*: the slot directly above the base
  that is shorter than the tallest habitable storey over it. Present only if
  the stack produced one. See the note below on why the yardstick is the
  tallest storey above rather than every storey above.
- **Principal** — the **uniquely** tallest habitable slot above the base and
  the compressed level. NOT "the first tall one": tallest is what the étage
  noble actually is. **The base exclusion is load-bearing**: a Paris ground
  floor is routinely taller than the noble floor above it, so "tallest slot"
  without qualification picks the wrong one. And where the tallest height is
  *shared*, there is no principal at all — a building whose étages are the
  same height has no floor it shows off, which is a real kind of building and
  not a degenerate case (see below).
- **Upper** — every slot between principal and attic, ranked upward.
- **Attic** — the slot inside the roof envelope: the one standing above the
  top of the stone face, where the *chambres de bonne* are. The predicate is
  ``Grid.stands_in_the_roof``, asked of the grid's own eaves line rather than
  of its LEGAL cornice — the decree caps the facade, it does not say where
  the roof starts, and a building that declined to spend its last metre of
  ambition still roofs over its own wall. Asking against the legal ceiling is
  why this role was unreachable for four stages: no storey ever started that
  high, so ``ATTIC`` was a label the system could not produce.

``assign_roles`` reads ``Grid`` alone (I1) — no ``SiteContext``, no year, no
class. Everything it needs (storey heights, positions, the cornice line) is
already on the grid it is handed; anything else would mean S3 failed to
produce a fact this phase needs, not that this phase should reach around it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris.catalogue import ENTRANCE_SLOT_NAMES as _ENTRANCE_SLOT_NAMES
from buildings.typologies.paris.structure import Grid

__all__ = ["Role", "RoledStorey", "RoledGrid", "assign_roles"]

# ---------------------------------------------------------------------------
# "Markedly below", without a magic number
# ---------------------------------------------------------------------------
#
# This predicate used to read "below 0.75 x the median habitable storey" —
# an INFERRED cutoff with no source behind it. The S7 acceptance run found
# its blind spot the moment S3's storey heights were corrected: a COMFORTABLE
# building on a 20 m boulevard came out
#
#     4.15 (base) | 2.47 | 3.47 | 3.23 | 3.00
#
# and the 2.47 m slot — an entresol by any reading, a full 0.53 m shorter
# than the shortest habitable storey over it — was labelled UPPER, because
# 2.47 is 0.76 of the 3.23 m median and the cutoff was 0.75. Moving the
# constant to 0.80 or 0.85 would have bought the next stack, not the rule.
#
# The constant-free reading is stronger and needs no tuning: a mezzanine is
# the slot directly above the base *and shorter than the tallest habitable
# storey over it*. It says what "markedly" means without inventing a number
# to mean it, and it cannot produce a phantom: a genuine storey at index 1
# sits at the bottom of a taper that only ever descends, so it is itself the
# tallest of the habitable run and can never be shorter than it.
#
# **A9.4 — the yardstick was wrong, and Daly says so.** It used to read
# "shorter than EVERY habitable storey in the building", and that is a
# stricter test than the thing being tested for. Daly measures nine Deuxième
# Classe entresols at 2.40-3.12 m in buildings whose topmost étages run down
# to 2.32 m: the compressed level is emphatically *not* the shortest storey
# in the building, it is shorter than the floor it serves. Under the old
# reading a correctly-built entresol standing under a 3.52 m noble floor was
# labelled UPPER because a garret-adjacent storey five floors up happened to
# be shorter than it — which is the mezzanine role quietly disappearing on
# exactly the buildings Daly says always have one.
#
# What the corpus supports is the *relation*, not a threshold: the ratio of
# noble floor to compressed level is 1.25 in Première and 1.30 in Deuxième.
# So the comparison is against the tallest storey above, and it stays
# constant-free.
#
# A tie is deliberately not a mezzanine. A slot exactly as tall as the
# tallest storey above it is a habitable storey, whatever the solver called
# it on the way in.
#
# ---------------------------------------------------------------------------
# "Has a principal floor" is itself class-dependent (A9.4)
# ---------------------------------------------------------------------------
#
# Daly's sixteen buildings carry a compressed level between the ground storey
# and the noble floor in fourteen of them — 4 of 4 Première, 10 of 10
# Deuxième, and **0 of 2 Troisième**. The two Troisième buildings have no
# compressed level and no piano nobile either: their étages are equal within
# 0.07 m (3.00 / 3.07 / 3.00 / 2.84 and 3.00 / 3.00 / 2.93 / 3.11). There is
# no floor those buildings show off, because they were not built to show a
# floor off.
#
# The predicates express that without a special case, and the mechanism is
# one word: the principal is the **uniquely** tallest habitable slot. Where
# the tallest height is shared, ``_find_principal`` returns ``None`` and the
# building simply has no PRINCIPAL — every habitable storey above the base is
# an UPPER, and rank is measured from the lowest of them instead, so a
# building with no shown floor still has ornament falling off upward and
# nothing downstream has to test for a missing role.
#
# Nothing here reads the class, and that is the point: what makes the
# difference class-dependent is the SECTION the structure phase builds, not a
# branch in this file. See the note in the report accompanying A9.4 for the
# one thing this does not yet reach — the structure phase applies a single
# uniform taper rate to every class, so an exactly-flat étage run is not
# currently produced, and the tie branch is reachable only through the storey
# minimum clamping two slots to the same height. Making it reachable means
# giving the taper a class ordering, and Daly marks the taper WEAK (Première
# n=3, Troisième n=1), so that is an ordering to assert, never a value to
# calibrate.

#: Float tolerance for comparing storey heights (tie-breaking, cornice-line
#: membership). Generous enough to absorb solver-scale rounding, tight
#: enough never to blur two genuinely different storey heights.
_EPS = 1e-6


class Role(Enum):
    BASE = "base"
    MEZZANINE = "mezzanine"
    PRINCIPAL = "principal"
    UPPER = "upper"
    ATTIC = "attic"


@dataclass(frozen=True)
class RoledStorey:
    slot: PlacedSlot
    role: Role
    rank_from_principal: int  # 0 for principal, +1 upward (negative below it)
    index_from_bottom: int
    index_from_top: int


@dataclass(frozen=True)
class RoledGrid:
    storeys: tuple[RoledStorey, ...]
    bays: tuple[PlacedSlot, ...]
    grid: Grid

    @property
    def attic(self) -> RoledStorey | None:
        """The storey standing inside the comble, or ``None`` where the roof
        was too shallow to hold one.

        Exposed because the termination phase needs it and should not have to
        re-derive it: the lucarnes on the slope are this storey's windows, so
        their sill level, and whether there is anything to light at all, are
        facts about this slot. Where a comble somehow held more than one
        storey this returns the lowest; ``attic_storeys`` has them all.
        """
        return next((st for st in self.storeys if st.role is Role.ATTIC), None)

    @property
    def attic_storeys(self) -> tuple[RoledStorey, ...]:
        """Every storey standing inside the comble, bottom-up."""
        return tuple(st for st in self.storeys if st.role is Role.ATTIC)

    @property
    def lit_bays(self) -> tuple[tuple[int, PlacedSlot], ...]:
        """Every slot on the frontage that carries a window above the
        pavement, with its index — the axes a lucarne may stand over.

        **A9.1 puts this here, once.** How many lucarnes a comble carries is
        the same question as how many window axes the frontage has, because a
        lucarne stands over an axis; and that question is answered by the one
        bay grid phase 1 solved, not by a rhythm the roofscape made up. Two
        modules were answering it independently, which is the class of
        divergence I1 exists to remove.

        The **entrance column is included, and that is the substance**, not a
        detail. A porte cochère is a ground-floor fact: it is a hole a vehicle
        drives through. Four storeys up, the same column carries an ordinary
        window on every floor — ``qualify.base.over_the_entrance`` puts one
        there — and the comble, higher still, has no reason whatever to know
        where the carriages go in. Leaving it out put a hole in the middle of
        every roof in Paris; the VLM check saw it as "two dormers, shoved to
        the extreme ends of a roof they do not fill".

        End piers are wall and any narrow special inserted to close the
        rhythm is a panel, not a room, so neither is here.

        This is what makes the lucarne count class-independent, which is what
        A9.1 asks for and what "a comble is floor rather than show" means: the
        bay pitch is ABSOLUTE, the edge pier is ABSOLUTE, so two buildings of
        different classes on one frontage get the same axes and the same
        roofscape. The one thing that still moves the count is which DOOR the
        frontage has — a carriage arch takes 3.40 m of frontage where a
        pedestrian door takes 2.35 m, and on a narrow parcel that difference
        really is an axis. That is a vehicle, not an ambition.
        """
        return tuple(
            (i, b)
            for i, b in enumerate(self.bays)
            if b.kind is SlotKind.REPEATING or b.name in _ENTRANCE_SLOT_NAMES
        )

    @property
    def attic_bays(self) -> tuple[PlacedSlot, ...]:
        """The horizontal slots the attic storey fills as rooms.

        ``lit_bays`` without the indices, and empty when the comble holds no
        storey: there is nothing to light.
        """
        if self.attic is None:
            return ()
        return tuple(b for _i, b in self.lit_bays)


def _is_within_roof_envelope(grid: Grid, index: int) -> bool:
    """A slot lies inside the roof envelope if it stands above the top of the
    stone face — which is what ``Grid.stands_in_the_roof`` answers.

    The question is geometric, so it is asked once, where the geometry lives,
    and every phase that needs it reads the same answer. Phase 2's job is not
    to own the arithmetic; it is to turn the answer into a role.
    """
    return grid.stands_in_the_roof(index)


def _find_mezzanine(storeys: tuple[PlacedSlot, ...], attic_flags: list[bool]) -> int | None:
    """Index of the compressed level, or ``None`` if the stack has none.

    Only the slot directly above the base (index 1) is ever eligible — a
    mezzanine is defined by position as well as height, and "the storey over
    the shop" is what the word means. It qualifies if it is shorter than the
    **tallest** habitable slot above it: the floor it is compressed relative
    to is the one the building shows off, not the meanest garret under the
    cornice. See the note at the top of this module for Daly's nine measured
    entresols and why the previous "shorter than every habitable storey"
    reading loses them.
    """
    n = len(storeys)
    if n < 2 or attic_flags[1]:
        return None

    pool = [
        storeys[i].width
        for i in range(1, n)
        if i != 1 and not attic_flags[i]
    ]
    if not pool:
        return None

    tallest_above = max(pool)
    if tallest_above <= 0.0:
        return None

    return 1 if storeys[1].width < tallest_above - _EPS else None


def _find_principal(
    storeys: tuple[PlacedSlot, ...],
    base_idx: int,
    mezzanine_idx: int | None,
    attic_flags: list[bool],
) -> int | None:
    """Index of the **uniquely** tallest habitable slot above base and
    mezzanine, or ``None`` where the tallest height is shared.

    The base exclusion is what makes the "tallest" reading correct — without
    it a tall ground floor would win every time. The uniqueness is what makes
    "has a piano nobile" a fact about the section rather than an assumption:
    a building whose étages are all the same height has no floor it shows
    off, and Daly's two Troisième Classe buildings are exactly that (étages
    equal within 0.07 m, and no compressed level under them either). It used
    to break ties to the lowest, which manufactured a noble floor for a
    building that had not built one.
    """
    candidates = [
        i
        for i in range(len(storeys))
        if i != base_idx and i != mezzanine_idx and not attic_flags[i]
    ]
    if not candidates:
        return None

    tallest = max(storeys[i].width for i in candidates)
    at_the_top = [i for i in candidates if abs(storeys[i].width - tallest) <= _EPS]
    if len(at_the_top) != 1:
        return None
    return at_the_top[0]


def _rank_anchor(
    storeys: tuple[PlacedSlot, ...],
    base_idx: int | None,
    mezzanine_idx: int | None,
    attic_flags: list[bool],
) -> int | None:
    """Which storey rank 0 is measured from where there is no principal.

    The lowest habitable slot above the base and the compressed level — the
    *premier étage*. A building with no distinguished noble floor still has
    ornament that thins as it climbs and openings that shorten as they climb;
    what it has lost is the peak, not the gradient. Anchoring on the first
    letting floor keeps every rank-driven relation downstream working on a
    Troisième-shaped section with no rule anywhere testing for a missing
    role.
    """
    candidates = [
        i
        for i in range(len(storeys))
        if i != base_idx and i != mezzanine_idx and not attic_flags[i]
    ]
    return candidates[0] if candidates else None


def assign_roles(grid: Grid) -> RoledGrid:
    """Walk ``grid.storeys`` bottom-up and derive a role for each slot.

    Reads ``grid`` and nothing else (I1): no ``SiteContext``, no year, no
    class — every predicate below is a pure function of storey positions and
    heights already present on the ``Grid``.
    """
    storeys = grid.storeys
    n = len(storeys)

    # The base is the bottom slot, unconditionally — even in the degenerate
    # case of a single-storey grid whose eaves line sits at (or below)
    # pavement level. That guard lives inside ``stands_in_the_roof`` so that
    # this phase and the qualification context cannot disagree about which
    # storeys are in the comble.
    attic_flags = [_is_within_roof_envelope(grid, i) for i in range(n)]

    base_idx = 0 if n > 0 else None
    mezzanine_idx = _find_mezzanine(storeys, attic_flags) if n > 0 else None
    principal_idx = (
        _find_principal(storeys, base_idx, mezzanine_idx, attic_flags) if n > 0 else None
    )

    roles: list[Role] = [Role.UPPER] * n
    for i in range(n):
        if attic_flags[i]:
            roles[i] = Role.ATTIC
    if base_idx is not None:
        roles[base_idx] = Role.BASE
    if mezzanine_idx is not None:
        roles[mezzanine_idx] = Role.MEZZANINE
    if principal_idx is not None:
        roles[principal_idx] = Role.PRINCIPAL

    # Rank is measured from the floor the building shows off. Where it shows
    # none — the Troisième Classe section, whose étages are all one height —
    # it is measured from the first letting floor instead, so that every
    # rank-driven relation downstream (ornament, opening aspect, surround)
    # keeps working without a single test for a missing role.
    anchor = principal_idx
    if anchor is None:
        anchor = _rank_anchor(storeys, base_idx, mezzanine_idx, attic_flags)

    roled: list[RoledStorey] = []
    for i, slot in enumerate(storeys):
        rank = i - anchor if anchor is not None else 0
        roled.append(
            RoledStorey(
                slot=slot,
                role=roles[i],
                rank_from_principal=rank,
                index_from_bottom=i,
                index_from_top=n - 1 - i,
            )
        )

    return RoledGrid(storeys=tuple(roled), bays=grid.bays, grid=grid)
