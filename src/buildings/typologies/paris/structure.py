"""Phase 1 — the structure phase (S3).

Three things happen here and nothing else:

1. **Envelope from regulation.** The cornice height ceiling and the roof
   envelope (45 deg plane pre-1884, arc post-1884) come straight from
   ``reglement`` — nothing here re-derives regulatory arithmetic. Street width
   in, a legal solid out.

2. **Ceiling vs built, kept separate.** The previous attempt's named failure:
   "The law says how tall you may build. Economics and programme say how
   tall you did. Conflating them makes every building a maximal building."
   ``Grid.cornice_height`` is the LEGAL ceiling. ``Grid.eaves_height`` is
   where the stone face actually stops, deliberately below the ceiling for
   anything short of a grand building on a wide street, and
   ``Grid.built_height`` asks the storeys the same question rather than
   storing a second copy of the answer.

   The stone and the roof answer to different things and neither is a
   fraction of the other. ``_FACADE_AMBITION`` decides how much of the legal
   cornice the stone face buys; the comble's height is a *programme* — the
   *chambres de bonne* behind its brisis and the terrasson closing over them
   (``_comble_section``) — capped by, and normally well under, what the
   gabarit would allow. A8.5 is why: with the roof taking a fixed 0.99 of
   whatever the facade left, every metre of cornice height a modest builder
   declined came back as zinc, ``eaves + comble`` landed exactly on the legal
   total in all four classes, and the poorer the building the bigger its hat.

3. **Budgets filled by the S1 solver.** Storeys fill the built-height budget;
   bays fill the parcel width. The bay grid is solved exactly ONCE per
   building — every storey later decorates the same ``Grid.bays`` tuple, so
   openings cannot drift out of vertical alignment because there is only one
   grid to read from.

   The bay *pitch* is structural and only weakly class-dependent
   (``_bay_pitch_band``). Class scaling used to be applied to it, which meant
   a grand building got FEWER windows on the same frontage than a modest one
   (A8.6). Money buys the opening inside the bay, the storey height and the
   ornament; it never thins the rhythm.

4. **The stack is not only the facade.** A Paris comble is not empty roof:
   the *chambres de bonne* are in it. Where the roof has the clear height
   and the floor depth for a room, one more storey slot is emitted standing
   on the eaves, and ``Grid.stands_in_the_roof`` is the geometric question
   that separates it from the storeys behind the stone. Where the roof has
   not — a shallow parcel, a low legal comble — nothing is emitted.

   How much roof there is over that storey is ``Grid.comble_height``. The
   comble springs from the *built eaves* — the égout du toit, which is where
   the decree springs it (A3.1) — and it is carried up the same curve to the
   top of the legal solid, which does not come down with the eaves. Reading
   ``envelope.ridge_height`` — a height above the LEGAL cornice — directly as
   a height above the eaves would charge the roof a second time for the
   cornice height the facade declined to build: in the canonical case, 1.23 m
   of legal height, deleted from the garret it would otherwise have gone
   into. The two anchors differ by exactly that headroom, and the one place
   the conversion between them happens is
   ``_above_the_cornice_to_above_the_eaves``.

5. **Every building has an entrance, and it is placed by rule.** A6.1: the
   door used to be reachable only through ``GroundProgramme.CARRIAGE``, so
   every shop, café, office and residential frontage in the city came out of
   this phase with no way into it. It is unconditional now. *Which* door —
   porte cochère or porte piétonne — is ``catalogue.entrance_for``, read off
   the class and the street width; how much frontage it takes is ABSOLUTE and
   the catalogue's; and *where* it stands is ``_entrance_index_hint``: the
   middle of the interior run, or half a bay left of the axis where the run
   has no middle, in which case the fitting solver answers the offset by
   putting the narrow special on the other side. The decision is taken before
   either budget is filled, because it constrains both — a fixed slot in the
   bay run and a floor under the ground storey's height.

6. **The entresol is programme, not remainder.** Whether a low storey sits
   over the ground floor is decided from the ground-floor use and the class
   *before* the height budget is filled, and handed to the solver as a fixed
   element of the vertical run. Nothing about how the budget divides can
   conjure one up: the vertical solve is offered no ``special`` at all, and
   the facade target — an INFERRED fraction — is rounded to a height whole
   storeys can actually fill rather than closed with an invented half-storey.

One thing this phase does *after* the solver has answered, and the rule it
obeys: the storey taper may not loosen anything the solver was told. It is
fitted inside the very ``[minimum, maximum]`` band declared to it, so the
solver's "no slot outside its bounds" guarantee survives to ``Grid.storeys``
— which is what downstream phases actually read — and a REGULATORY storey
minimum can never be bent by an INFERRED taper constant.

The output is an unnamed grid: no roles, no floor names, no meaning. A slot's
identity (base, mezzanine, principal, ...) is derived in S4 by walking this
grid — it is never decided here. If a word from ``roles.Role`` shows up in
this file outside a comment, that is this module doing S4's job.

Fully deterministic: nothing here samples anything. ``solve_structure`` takes
no RNG, by contract — every quantity is a pure function of ``site`` (and,
when supplied, of the block's handed-down ``datums``), which is what makes
I5 (seed + situation -> identical output) trivial for this phase.

Geometry note: heights are measured bottom-up from pavement level (metres),
matching the IR's origin convention (``ir.nodes``); the bay axis is measured
left to right from the parcel's left edge, centreline to centreline, per the
fitting solver's own convention.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import Mapping

from buildings.quantity import Abs, Prop, Quantity, Reg, scale_for_class
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import FitInfeasible, PlacedSlot, SlotKind, SlotSpec, solve
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.reglement import (
    GabaritEnvelope,
    Reglement,
    compute_envelope,
    era_for_year,
    get_reglement,
)

__all__ = ["BRISIS_RISE", "Grid", "solve_structure"]

# ---------------------------------------------------------------------------
# BlockDatums (buildings.block) — not yet built at the time this stage runs.
# ---------------------------------------------------------------------------
#
# CONTRACTS.md types ``datums`` as ``buildings.block.BlockDatums | None``.
# `` from __future__ import annotations`` makes every annotation in this file
# a string that is never evaluated at runtime (PEP 563), so the signature
# below is legal Python today even though ``buildings.block.BlockDatums``
# does not exist yet — S9 introduces the real dataclass later, on schedule.
# At runtime ``datums`` is accessed by simple attribute (``.street_width``,
# ``.cornice_height``), so any object shaped like the frozen contract's
# ``BlockDatums`` — including the real one, once S9 lands — satisfies this
# function without this module importing it. For static type-checkers only:
#
#   from typing import TYPE_CHECKING
#   if TYPE_CHECKING:
#       from buildings.block import BlockDatums

#: Tolerance on "the site and the block agree about the street" (A4.8).
#: Deliberately the same figure as ``block.DATUM_TOLERANCE``, restated rather
#: than imported for the reason above — importing ``buildings.block`` here
#: would make the dependency run backwards, block -> building being the only
#: direction allowed (I2). Both are exact-equality-with-float-slack, not a
#: fudge factor: the two numbers are copies of one value, so anything beyond
#: float noise between them is a disagreement, not a rounding.
_DATUM_TOLERANCE: float = 1e-9


# ---------------------------------------------------------------------------
# Inferred constants — placeholders, not findings (same status as A1.3's
# _CLASS_SCALE in quantity.py). Only the monotonic ordering is contractual;
# the numbers themselves are provisional pending real design input.
# ---------------------------------------------------------------------------

#: INFERRED. How much of the legal cornice ceiling a class of building
#: actually builds to. Grand buildings on wide streets build near the limit;
#: modest ones do not — the brief's own example, made numeric. Neither the
#: brief nor any source gives figures for this; only the monotonic increase
#: toward 1.0 is contractual here.
#:
#: This used to be handed to ``compute_envelope`` as ``roof_fill`` as well, so
#: one number decided both how tall the stone face is and how full the comble
#: is. Those are different decisions taken by different people for different
#: reasons — the first is what the owner spends on show, the second is what
#: the roof is *for* — and tying them made a modest building's garret shallow
#: precisely where the garrets were most crowded. The comble now has its own
#: constant, immediately below.
#:
#: **A9.4 — the shape of this ladder is now sourced, though the figures are
#: not.** Daly's cornice heights above the pavement are 19.11 / 18.90 /
#: 15.79 m down the class ladder. The step between the two TOP classes is
#: 0.21 m — nothing, well inside the corpus's own 0.2-0.4 m error on a storey
#: height — while the step down to the bottom class is 3.1 m and is real. Six
#: of the sixteen buildings sit between 19.0 and 20.0 m: they are not a class
#: ladder at that end, they are a queue against the 1859 decree's 20 m facade
#: maximum for a wide street. **The regulation is visible in the data**, and
#: that is the most direct evidence this project has that the regulatory
#: quantity is doing real work.
#:
#: So the top of the ladder is flattened to reproduce it. COMFORTABLE and
#: GRAND both build within a metre of the ceiling and both land in Daly's own
#: 19.0-20.0 m band on a street the decree gives 20 m to; ORDINARY and MODEST
#: keep the fall. The ordering is still strictly increasing — that remains
#: the only contractual thing here — and the figures remain INFERRED: what
#: Daly supports is the *flatness at the top and the drop at the bottom*, not
#: four fractions.
_FACADE_AMBITION: Mapping[BuildingClass, float] = {
    BuildingClass.MODEST: 0.74,
    BuildingClass.ORDINARY: 0.85,
    BuildingClass.COMFORTABLE: 0.96,
    BuildingClass.GRAND: 0.99,
}

# ---------------------------------------------------------------------------
# The comble as a SECTION, not as a fraction (A8.3 / A8.5)
# ---------------------------------------------------------------------------
#
# This is where ``_COMBLE_FILL = 0.99`` used to be: a class-invariant fraction
# of the permitted curve, handed to ``compute_envelope`` as ``roof_fill``. Two
# independent harnesses convicted it. The validation sweep found the comble's
# share of the building running *inversely* to class — 37 % of a modest
# building and 16 % of a grand one, with ``total_height == legal_total_height``
# in all four classes — and the oracle, built for something else entirely,
# found 22 of its 29 proportion outliers were ``total_height_m``, every one of
# them new > old, in every class.
#
# The mechanism was this. ``_FACADE_AMBITION`` stops the stone face short of
# its ceiling; ``Grid.comble_height`` then carries the same curve from those
# lower eaves up to the top of the legal solid (A3.1, and that part is right —
# the legal solid does not come down with the eaves). With the roof taking
# *nearly all* of whatever that leaves, every metre of cornice height a modest
# builder declined to spend came back as ROOF. The building was maximal after
# all; only the line between stone and zinc had moved. That is precisely the
# conflation the brief names: "The law says how tall you may build. Economics
# and programme say how tall you did. Conflating them makes every building a
# maximal building, which is wrong and looks it."
#
# A fraction was the wrong shape of answer. A comble is not a percentage of a
# legal solid, it is a SECTION with two planes and a reason for each:
#
#   * the **brisis**, the steep lower slope, is the outside wall of the
#     *chambres de bonne*. Its rise is the room behind it — ABSOLUTE, a body
#     and a joist, the same in a modest immeuble and a grand one, because a
#     servant's room is a servant's room. This is the part of the old
#     constant's reasoning that was right ("a comble is not show, it is
#     floor") and it survives here with teeth: the roof is sized by the floor
#     it holds, not by the fraction of the gabarit left over it.
#   * the **terrasson**, the shallow upper slope, closes over that room and
#     runs back to the middle of the plot. Its pitch is what zinc needs to
#     drain, not what anybody wanted.
#
# The fold between them is one or more whole *chambres de bonne* up from the
# eaves, and the terrasson is then simply the chord that closes the section
# from there to the middle of the plot. Its pitch is a CONSEQUENCE and not a
# constant, which is what makes it always shallower than the brisis: the
# brisis hugs the envelope, every envelope in ``reglement`` is concave, and a
# chord leaving a concave curve leaves it more shallowly than the curve
# climbs. Nobody had to choose a number for it.
#
# And **the comble's height is the decree's own comble allowance, laid on the
# eaves this building actually has**. That single sentence is the A8.5 fix.
# ``_comble_ceiling_over_the_eaves`` still carries the A3.1 recovery — the
# legal solid does not come down with the eaves, and that remains true — but a
# CEILING is not a height. Building to it meant the roof grew by exactly what
# the facade gave up, so the two moved in lockstep and the sum never changed:
# hence ``total_height == legal_total_height`` in all four classes. Now the
# comble is a function of the street, the era and the plot and of nothing
# else — the same roof on a modest immeuble and a grand one, which is what "a
# comble is floor, not show" actually implies — and the class shows up in the
# TOTAL, through the stone underneath it, which is where the brief puts it.

#: ABSOLUTE. What stands behind the brisis: one *chambre de bonne*. A room a
#: person lives in and the floor carrying it — ``_PLAIN_STOREY_HEIGHT``, the
#: same body-and-joist figure the storeys below use — plus the plate below.
#: Never scaled: a garret room is not bought with ambition.
_BRISIS_PLATE = Abs(
    0.30, "the wall plate the terrasson's rafters land on, over the garret's ceiling"
)

#: INFERRED. The terrasson's pitch, in degrees from horizontal. A terrasson is
#: a zinc deck over the garret's ceiling: it has to shed water and it has to be
#: invisible from the street, and those two facts bracket it tightly. Only that
#: it is much shallower than the brisis — which is what makes the roof read as
#: a mansard rather than as a gable — is contractual.
#:
#: This is what stops the roof from being the gabarit. Left uncapped, an 1902
#: comble ran the whole 11 m the decree permits and came out as nine metres of
#: bare zinc over one row of lucarnes: legal, and nothing anybody built. The
#: builder stops where the rooms stop and closes over them.
_TERRASSON_PITCH_DEG = 12.0

#: INFERRED. Each typical storey is this fraction of the one below it —
#: "shorter than the one below" as a relation applied uniformly, not a
#: stored table of per-floor heights.
#:
#: The figure is not free-floating: a canonical Paris section diminishes
#: from the étage noble to the storey under the cornice by roughly a fifth
#: over three intervals (≈3.6 m -> ≈2.9 m), and ``(2.9 / 3.6) ** (1 / 3)``
#: is 0.930. That is the rate here. The previous 0.965 was chosen for
#: mildness rather than fidelity and produced a ramp — 4.08 / 4.00 / 3.86 —
#: where the real section steps down markedly. Only the direction (< 1.0)
#: is contractual; the value is a reading of the canonical section, which
#: is a better class of guess than an invented one but still a guess.
_TAPER_RATE = 0.93

#: 1859 règlement, art. on storey height (``Reglement.min_floor_height``) is
#: 0.0 for the Royal era, meaning the texts impose no hygiene minimum before
#: 1859 — not that a storey may be zero metres tall. This is the physical
#: floor under that: a room a person can stand up in.
_HUMAN_MIN_STOREY_HEIGHT = Abs(2.20, "a person must be able to stand upright inside a room")

#: ABSOLUTE. The height a storey has before any ambition is spent on it: a
#: room a person lives in, plus the floor structure carrying the room above.
#: A body and a joist, not a taste — so it never scales (A1.1 enforces that
#: for the ``Quantity`` itself).
#:
#: This is the datum the brief's classification actually asks for. Under
#: "Proportional" it lists *"storey height above its legal minimum"* — the
#: MARGIN, not the storey. The first implementation scaled the whole storey
#: height by the class factor, which multiplied this rigid core along with
#: the ambition and put four 4 m storeys where a Paris immeuble carries five.
#: Splitting the two is the fix: ambition buys the margin, never the body.
#:
#: That it lands a hair over the 1859 hygiene minimum of 2.60 m is the
#: expected relation rather than a coincidence — the statute codified the
#: meanest storey already being built. The minimum is still enforced
#: separately, as a REGULATORY bound, so the two never merge.
_PLAIN_STOREY_HEIGHT = Abs(
    2.60, "a room a person lives in, plus the floor structure carrying the one above"
)

#: ABSOLUTE and **SOURCED (A9.4)**. A rez-de-chaussée in trade: the shop, its
#: counter, the joists over it and the height a devanture needs to be worth
#: putting glass in. Daly, 16 buildings across all three classes: median
#: 3.95 m, range 3.42-4.85 m, class medians 4.20 / 3.95 / 3.81 m — a 9 % fall
#: end to end with ranges that overlap almost entirely. Class-independent, and
#: therefore ``Abs``: this is the second-most stable absolute in the corpus,
#: behind the carriage door.
#:
#: The one extreme (4.85 m at 88 rue de Rivoli) is a deliberate tall-boutique
#: type rather than measurement error, and it is what the upper end of the
#: range is; the model states the median and lets the entrance's own ABSOLUTE
#: height raise it where a door needs more, which is the only way this number
#: ever moves.
_TRADE_GROUND_HEIGHT = Abs(
    3.95,
    "SOURCED — Daly 1864 (Sér. 1 Vol. 1 t. 2), rez-de-chaussée floor-to-floor over "
    "16 buildings: median 3.95 m, range 3.42-4.85 m, class medians 4.20 / 3.95 / "
    "3.81 m. The ladder falls 9 % across the whole social range while the ranges "
    "overlap almost completely, so the commercial ground storey is ABSOLUTE and "
    "class-independent (scale-bar measured, ±10 %, with the 125 Champs-Élysées "
    "printed ladder anchoring the Première end)",
)

#: ABSOLUTE, INFERRED. What a residential ground floor — a hall, a stair, a
#: concierge's loge — has above a plain storey. Deliberately NOT sourced:
#: Daly's plates are commercial frontages and contain no observation of this
#: at all. What A9.4 carries over from them is the KIND and not the value:
#: since the measured ground storey does not move with class, neither does
#: this one, so the margin is ``Abs`` rather than ``Prop`` and the ground
#: floor of a modest house and a grand one are the same height.
_RESIDENTIAL_GROUND_MARGIN = Abs(
    0.90,
    "INFERRED — a residential ground floor has a hall and a stair above a plain "
    "storey; no Daly plate measures one, so the figure is the generator's. It is "
    "ABSOLUTE because the rez-de-chaussée Daly DOES measure is class-independent "
    "(SOURCED), and a hall is no more bought with ambition than a shop is",
)

#: ABSOLUTE. How far the brisis rises above the eaves: one plain storey — the
#: *chambre de bonne* standing behind it — and the plate the terrasson lands
#: on. Composed of the two facts that produce it rather than restated as a
#: figure of its own, so the garret behind the brisis and the storeys below it
#: are the same body-and-joist number and cannot drift apart.
#:
#: One of the two things that decide how tall a comble is, and it is ABSOLUTE.
#: A grand building does not buy a taller garret; it buys a taller *étage*,
#: and its comble ends up SHORTER because its stone face already used the
#: legal solid up. The other thing is HOW MANY of these bands the roof stands,
#: which is the subject of the section immediately below (A15.1).
BRISIS_RISE = _PLAIN_STOREY_HEIGHT + _BRISIS_PLATE

# ---------------------------------------------------------------------------
# How many storeys of chambres de bonne the roof holds (A15.1 / A15.2)
# ---------------------------------------------------------------------------
#
# **A15.1.** A8.3/A8.5 got the SHAPE of the answer right — the comble is a
# section sized by the rooms behind it, not a fraction of the gabarit — and
# then left the number of rooms to fall out of the decree's own allowance:
# ``bands = int(allowance / BRISIS_RISE)``. Under the post-1884 arcs that
# allowance stands two and three storeys of garret and the comble moves with
# the plot, which is right and is why those decrees were passed. Under the 45°
# diagonal the allowance is ``Reglement.max_roof_height``, which is 3.20 m and
# is documented in ``reglement.py`` as "calibrated so a Second Empire roof
# holds exactly the one storey of chambres de bonne it was built for". One
# storey, always; hence one band, always; hence — measured over 180 sites —
# **a comble of 3.20 m for every street, parcel, class and programme in the
# whole of the 45° era**, with the parcel depth unable to bind because 3.20 m
# of 45° roof needs only 6.40 m of plot.
#
# Daly's nine measured 1864 commercial buildings run 2.69 / 2.77 / 2.85 /
# 3.18 / 3.34 / 3.45 / 4.72 / 6.80 / 7.00 m — one era, a 2.6× range, and the
# measurement pass says why in as many words: *"the corpus mixes plain
# mansards with combles containing two full storeys"*. The quantity is
# bimodal, and a bimodal quantity is a variable with two modes, not an
# invariant (**A15.2**, correcting A9.1's over-reading: what Daly supports is
# that comble share is not a function of CLASS, which is a different claim
# and still holds).
#
# So the storey count becomes a decision, and the section follows it. Three
# things about how that decision is taken here:
#
# 1. **It is not keyed to class**, and cannot be: nothing in this module's
#    comble arithmetic reads ``BuildingClass``, and A9.1's retraction — that
#    comble share is not a class function — is the one solid piece of evidence
#    in the area. The drivers are the PROGRAMME and the PARCEL.
# 2. **The second storey is bought, not granted.** The legal solid does not
#    move: ``envelope.total_height`` is what the decree allows over the
#    pavement, and a roof that stands two storeys of garret under it has to
#    take the height from the stone below. So an extra band of garret costs
#    the facade exactly one band of cornice height (see ``solve_structure``),
#    the building keeps its silhouette inside the same gabarit, and the
#    accommodation has simply moved from stone into zinc. Daly's three
#    tall-comble buildings are exactly this trade made visible: 1 and 2-4
#    boulevard de Sébastopol carry 6.80 m and 7.00 m of comble over cornices
#    at 17.55 m and 17.52 m, where their five short-comble neighbours on the
#    same boulevard carry 2.7-3.3 m over cornices at 19.5-20.0 m. Same total,
#    fewer étages, more roof.
# 3. **What is paid for has to be received (A16.1), and that is a PARCEL
#    question.** The circulaire du 21 septembre 1855 runs the cornice across
#    the party wall and ``block.check_alignment`` enforces it: every eaves
#    line on a run must be identical to 1e-9. A15 read that as forbidding this
#    decision to look at the plot at all — the street, the date, the class and
#    the ground REGIME are shared down a run, and the parcel depth is not —
#    and left the depth to bind afterwards, in the SECTION.
#
#    It bound there, and nothing carried its answer back. The facade spent a
#    band of cornice height on a 10 m lot and ``_comble_section`` then refused
#    to build the band, so a shop under a 20.00 m ceiling came out at 15.99 m
#    holding exactly the one storey of garret a residential building gets for
#    nothing: **the sixth time in this project that two functions have held
#    independent opinions about one fact** (A4.1, A6.8, A7.3, A9.3, A10.4).
#
#    So the buyer asks the holder first, through the single function
#    ``_extra_garret_storeys_the_parcel_holds``, which is also the one
#    ``_comble_section`` clamps against. The trade is therefore a lot-level
#    decision and the trade-off is stated rather than hidden: a commercial run
#    on a street wide enough to offer the trade whose lots straddle the depth
#    that holds a second band — about 12.20 m at 1865, against a typical Paris
#    lot of 18 m — would step its cornice at a party wall, and
#    ``block.check_alignment`` refuses that loudly. A height spent and never
#    received was the same fault with nobody to notice it.
# 4. **The rate is INFERRED and is not calibrated.** Daly shows 3 of 9, but
#    comble share is marked INSUFFICIENT in the measurements and n=9 carries a
#    known publication bias. What is contractual is only that BOTH MODES
#    OCCUR and that a two-storey garret carries two rows of lucarnes; the
#    frequency is a consequence of the two predicates below and nobody should
#    read a percentage out of it.

# ---------------------------------------------------------------------------
# The bay pitch — structure, not ambition (A8.6)
# ---------------------------------------------------------------------------
#
# The bay band used to be ``_scaled_bounds(2.70, 3.00, 3.30)``, i.e. wholly
# PROPORTIONAL, so the class factor multiplied the *rhythm*: on one 16 m
# frontage a modest building got a 2.55 m pitch and a grand one 4.05 m, which
# is eight bays against six. Money bought a building FEWER windows.
#
# Paris runs the other way. What a bay may measure is set by what a stone
# lintel and its piers will span and by the joist run behind it — a fact about
# masonry, the same for a rentier's immeuble and a banker's — so it is
# ABSOLUTE, and the rhythm of a Paris street is astonishingly uniform because
# of it. What money buys is the OPENING inside the bay (wider and much
# taller), the storey height, and the ornament. Never a thinner wall of
# windows: a grand facade with the rhythm of a warehouse is exactly the "too
# blank for its pretension" the validation saw.
#
# So the two bounds are ABSOLUTE and the preferred pitch carries a weak class
# trend inside them. Weak is the contract: the whole span from MODEST to GRAND
# moves the pitch by ``_BAY_PITCH_CLASS_SPREAD`` of the structural band, and
# because the result is composed as ABSOLUTE nothing downstream can scale it
# a second time.

#: ABSOLUTE. The narrowest bay: a window a person gets light and air through,
#: with a pier either side that still reads as carrying something.
#:
#: **A10.1 — what this floor is a floor UNDER, said explicitly.** It bounds the
#: ``REPEATING`` bay and nothing else: the module the rhythm of the frontage is
#: made of, the one the solver lays down over and over. It is *not* a floor
#: under every slot standing in the run, and two of them are deliberately
#: below it:
#:
#: * the **narrow special** (1.10-1.80 m), which is defined by being narrower
#:   than a bay — "a strip of wall with one light in it", the absorber that
#:   closes a rhythm the parcel will not divide evenly. Its whole maximum is
#:   0.90 m under this figure, on purpose.
#: * the **entrance slot** — 2.35 m for a *porte piétonne*, 0.35 m under this
#:   figure. That number is not free to move: 1.75 m of it is Daly's SOURCED
#:   median of eight measured doors, and the two 0.30 m jambs are already
#:   thicker per metre of span than the 0.40 m jamb carrying a carriage arch.
#:   Reaching 2.70 m would need 0.475 m jambs on a pedestrian door — a bigger
#:   pier under a smaller load, which is a lie about masonry told to satisfy
#:   an arithmetic the door was never inside.
#:
#: And it should not be inside it. This bound is about a *rhythm*: what the
#: repeating module may narrow to before the wall stops reading as piers
#: carrying lintels. A door is a one-off standing in that rhythm, and what
#: constrains a one-off is what the column has to do — carry a light at every
#: storey above the pavement — not what the repeat has to look like. A 2.35 m
#: column takes its neighbours' window with 0.60 m of pier either side and is
#: perfectly good masonry; a facade built of 2.35 m bays is not the same claim
#: at all.
#:
#: So the floor is enforced on what it is about. ``solve_structure`` asserts
#: it over the ``bay`` slots the solver returns — the postcondition matching
#: the ``_BAY_PITCH_MAX`` tripwire on the entrance, so that the band is now
#: guarded on both sides, each over its own domain — and the entrance carries
#: its own two-sided guard there against the bounds that are genuinely its.
#:
#: **A25 — EVIDENCE AGAINST THIS FIGURE, recorded but NOT yet acted on.** The
#: 2026-08 measuring pass read 16 elevations off the plates against their own
#: scale bars. Six of the fifteen usable frontages come in under this floor:
#:
#:     2.11  rue du Conservatoire, 9      (GOOD)
#:     2.28  125 Champs-Elysees           (MEDIUM)
#:     2.41  1 bd de Sebastopol           (HIGH — operator read 2.40 independently)
#:     2.48  77 bd de Sebastopol          (HIGH)
#:     2.51  rue de Longchamps            (MEDIUM)
#:     2.52  11 bd de Sebastopol          (MEDIUM)
#:
#: The paragraph above argues that "a facade built of 2.35 m bays is not the
#: same claim" as a single narrow column. On the evidence it is the same claim,
#: and Paris built it repeatedly — 1 bd de Sebastopol carries seven axes at
#: 2.41 m across a 16.84 m frontage. The lowest reading, 2.11 m, also lands
#: within 0.02 m of the 2.09 m corpus minimum quoted at
#: ``_BAY_PITCH_PREFERRED``, from a wholly separate measurement.
#:
#: **A26 — MOVED, and by decision rather than by measurement.** The paragraph
#: above ended "the value is left at 2.70 deliberately … moving it is a
#: decision about what this generator claims". That decision has now been
#: taken: the operator set the band directly at **2.00 / 2.60 / 3.20 m**. The
#: figure is therefore **OPERATOR-SET**, not SOURCED and not derived from the
#: evidence listed above — though it moves in the direction that evidence
#: pointed, and 2.00 sits just under the 2.11 m lowest reading in the corpus
#: rather than a metre away from it. The old 2.70 was never a measurement
#: either; what changes is only which person's judgement it records.
_BAY_PITCH_MIN = Abs(
    2.00,
    "OPERATOR-SET — the narrowest REPEATING bay this generator will build. Not a "
    "corpus figure: the 2026-08 pass read six of fifteen frontages under the old "
    "2.70 floor, lowest 2.11 m, so the corpus is consistent with a floor here but "
    "did not choose it",
)

#: ABSOLUTE. The widest bay: what a stone lintel spans over an opening, and
#: what the floor joists behind it run, before the wall wants a column.
#:
#: **A25 — the ceiling is crossed too, once.** 119 avenue des Champs-Elysees
#: measures **3.71 m** (HIGH confidence: 14.86 m frontage, 4 axes, clean glass
#: detection), which is 0.31 m ABOVE this bound. Avenue de l'Imperatrice sits
#: just under at 3.37 m. So the band stated here is crossed at both ends by
#: the corpus it claims to describe.
#:
#: One plate is not grounds to move an ABSOLUTE bound, and this one carries a
#: caveat: 119 Champs-Elysees is the plate whose facade width was disputed —
#: the operator read 12.4 m, two independent measurements give 14.86/14.93 m,
#: and the 3.71 m pitch follows from the larger width. That dispute is now
#: resolved in favour of the larger figure (see
#: ``dev/reference/operator_axis_counts.json``), which means the exceedance is
#: real rather than an artefact of the disputed number. Recorded here so the
#: next person does not rediscover it as a surprise.
#:
#: **A26 — MOVED to 3.20 m, OPERATOR-SET.** Set directly by the operator along
#: with the other two figures of the band. It moves *away* from the corpus at
#: this end rather than toward it — 119 Champs-Elysees at 3.71 m and avenue de
#: l'Imperatrice at 3.37 m are now both outside — so the ceiling is a statement
#: about what this generator builds and not a description of the sixteen
#: plates. Recorded plainly rather than dressed as a reading.
#:
#: **It is also 0.20 m under the porte cochere's own 3.40 m slot**, which the
#: A9.2 tripwire in ``solve_structure`` forbids outright. See the note at
#: ``_CARRIAGE_SLOT_OVER_BAY_MAX`` below.
_BAY_PITCH_MAX = Abs(
    3.20,
    "OPERATOR-SET — the widest REPEATING bay this generator will build. Not a "
    "corpus figure: two of the fifteen measured frontages run wider (3.37 and "
    "3.71 m)",
)

#: The pitch a facade takes when nothing forces it off, stated explicitly
#: rather than derived as the midpoint of the two bounds above.
#:
#: **INFERRED, and deliberately still INFERRED (A9.4).** Daly's sixteen
#: buildings give a corpus median of 2.80 m over a 2.09-3.49 m range, and the
#: measurement pass marks that corpus-wide figure usable while marking bay
#: pitch INSUFFICIENT *as a function of class*. This module states 2.80 m and
#: cites Daly as **corroboration, not as a source**: A9.4 names eleven
#: quantities that may be promoted to SOURCED and this is not one of them, so
#: it keeps its marker. A number that agrees with a period source is not the
#: same thing as a number taken from one, and the difference is exactly what
#: the INFERRED marker exists to record.
#:
#: The midpoint (3.05 m) was doing quiet damage while it was implicit. The
#: natural bay count is a FLOOR of a division by this figure, so a preferred
#: pitch a quarter of a metre too wide loses a whole bay on frontages around
#: 16 m and hands the leftover to a narrow special: a grand frontage came out
#: as three 3.40 m bays and a 1.35 m panel where four 2.85 m bays — well
#: inside the same ABSOLUTE band — were available and are what Paris built.
#:
#: **A25 — re-measured, and it holds.** The corroboration above came from one
#: automated pass whose axis counts were never re-verified. A second pass,
#: independent of it, measured 16 elevations directly off the plates —
#: calibrated on each sheet's own printed scale bar, with every window/pier
#: detection checked against the drawing by eye. Over the 15 usable single
#: frontages the median pitch is **2.80 m**, the same figure to two decimals,
#: on a range of 2.11-3.71 m. Two measuring passes that share no method and no
#: intermediate numbers landing on the same median is about as much support as
#: an INFERRED quantity can get without becoming SOURCED — and it stays
#: INFERRED, because A9.4 still does not list it among the promotable
#: quantities. See ``dev/reference/daly_elevation_scan_2026-08-24.json``.
#:
#: What the same pass says about the two bounds either side of this one is
#: less comfortable, and is recorded at ``_BAY_PITCH_MIN``/``_BAY_PITCH_MAX``.
#: **A26 — MOVED to 2.60 m, and its marker changes with it.** Everything above
#: is the record of a number that agreed with two independent corpus medians of
#: 2.80 m. It no longer equals them: the operator set 2.60 m directly. So the
#: quantity is **OPERATOR-SET** rather than INFERRED-and-corroborated, and the
#: Daly medians are kept as context — they are what the figure used to rest on
#: and they are 0.20 m away from it — rather than as its justification.
_BAY_PITCH_PREFERRED = Abs(
    2.60,
    "OPERATOR-SET — the pitch a facade falls to when nothing forces it off. It is "
    "NOT the corpus median: Daly 1864 gives 2.80 m over 16 buildings (2.09-3.49 m), "
    "and an independent 2026-08 pass over the plates gives 2.80 m over 15 frontages "
    "(2.11-3.71 m). Both medians sit 0.20 m above this figure and are kept here as "
    "context, not as its source",
)

#: **A26 — the third of the operator's figures, and the SOFT one.** How much of
#: a bay the opening in it should be. OPERATOR-SET at 0.45, and explicitly
#: *soft*: it has no minimum and no maximum, it may not make any frontage
#: infeasible, and it may not override the bay band above.
#:
#: It has to be soft, because **the three figures cannot all hold at once**.
#: The operator's ideal window is 1.30 m and the ideal bay 2.60 m, and
#: ``1.30 / 2.60 = 0.500``, not 0.45. Reaching 0.45 with a 1.30 m window needs
#: a **2.889 m** bay — inside the [2.00, 3.20] band, but 0.29 m above the bay
#: the same instruction calls ideal. Two of the three can hold and the third
#: cannot, and the operator settled which one gives way: this one. So at rest
#: a facade shows a ratio of **0.500** and not 0.45.
#:
#: What the figure therefore does is exactly one thing: it is handed to the
#: solver as the bay's ``affinity`` — a lean, not a target — where it breaks
#: ties between bay counts that are otherwise equally far from the preferred
#: widths. It never widens a bay on its own account, because doing that would
#: be preferring 0.45 over the 2.60 that outranks it.
_WINDOW_BAY_RATIO = Abs(
    0.45,
    "OPERATOR-SET and SOFT — the share of a bay its opening wants to be. It cannot "
    "hold together with the other two ideals (a 1.30 m window in a 2.60 m bay is "
    "0.500, and 0.45 would need a 2.889 m bay), and it is the one of the three that "
    "gives way: it only breaks ties between bay counts",
)

#: **D6, closed (A9.2).** The porte cochère's slot is the one fixed element
#: standing in the bay run, and it is carried the full height of the facade —
#: so if it is wider than a bay may be, a grand frontage pays for its
#: entrance in windows. It was: an INFERRED 3.00 m clear opening plus two
#: 0.40 m jambs is 3.80 m, 0.40 m ABOVE the maximum stated two constants up,
#: and the measured cost was a grand building getting 4 openings on a 16 m
#: frontage where a modest one got 5.
#:
#: Daly's printed 2.600 m closes it arithmetically: 2.60 + 0.40 + 0.40 =
#: 3.40 m, which is ``_BAY_PITCH_MAX`` exactly. The column over a carriage
#: arch is therefore an ordinary bay — the widest one the masonry allows, as
#: it should be, but inside the band and not outside it — and above the
#: ground storey qualification already puts an ordinary window in it. The
#: relation is asserted in ``solve_structure`` rather than left to arithmetic
#: two modules apart, because it is exactly the kind of agreement that
#: silently stops holding.
#:
#: **A10.2 — the residual, and why it is not a defect.** After A9.2 a grand
#: frontage still came out with one axis fewer than a modest one on 12, 18
#: and 20 m parcels. The cause is the whole of it: the two richer classes
#: have a *porte cochère* and the two poorer ones a *porte piétonne*, and an
#: arch takes 3.40 m of frontage against a door's 2.35 m. That 1.05 m is a
#: third of a bay, so on some parcels it really is an axis — and it should
#: be. A carriage entrance is a hole a vehicle drives through and a passage
#: and a cour behind it; the building spent frontage on it, deliberately, and
#: a generator that hid the cost would be describing a facade nobody built.
#:
#: The class signal in a Paris entrance is **entitlement, not scaling** —
#: Daly: a carriage entrance in 4 of 4 Première, 3 of 10 Deuxième, 0 of 2
#: Troisième, while the doors themselves differ by 0.4 % between the classes
#: that have them — so "the grand building has fewer windows" is really "the
#: building with the arch has fewer windows", and the classes differ because
#: entitlement to an arch is what a class IS here.
#:
#: What changed at A10.2 is therefore the measurement and not the model.
#: Comparing a carriage frontage with a pedestrian one and calling the
#: difference a class effect is comparing two different buildings; compared
#: like with like the contract is exact rather than an inequality — the axis
#: count is a function of the frontage and the door, with class nowhere in
#: it. ``tests/unit/test_structure.py`` asserts that exact form, and prices
#: the door's own cost beside it — one axis, never two, because the 1.05 m
#: between the two doors is less than ``_BAY_PITCH_MIN``.
#:
#: How much of the structural band the whole class range moves the preferred
#: pitch across. **Zero (A9.1/A9.4): the bay pitch is now class-independent,
#: and Daly is why.**
#:
#: A8.6 cut the class dependence from the whole band down to a third of it,
#: deliberately leaving a weak increasing trend and calling the weakness the
#: contract. Daly's sixteen buildings say there is no trend at all to be weak
#: about: the class medians are **2.81 / 2.85 / 2.54 m** — Deuxième stands
#: ABOVE Première, so the ladder is non-monotonic — and the within-class
#: spread is 1.5× in both top classes, larger than any difference between
#: them. Première alone runs 2.32 to 3.49 m: "Première Classe" does not name
#: one bay rhythm. The measurement pass marks bay pitch INSUFFICIENT as a
#: class discriminator, and the amendment's reading of that is direct —
#: making it class-independent was correct.
#:
#: The residual third was not free. A window column is a bay, a lucarne
#: stands over a bay, and ``_natural_count`` floors a division: on a 12 m
#: frontage on a 10 m street, where no class has a carriage entrance and the
#: pitch trend was the ONLY difference between them, a modest building got
#: four window columns and every richer class got three. Money bought a
#: blanker wall, which is D6 in miniature and survived D6's fix.
#:
#: The mechanism above is kept rather than deleted, and this is the one
#: number that would restore the trend — because "no class ladder in the bay
#: pitch" is a finding about a corpus of sixteen buildings from one year, and
#: a later source may say otherwise. What is contractual now is that the two
#: bounds are ABSOLUTE and that the preferred pitch between them is the same
#: for every class.
_BAY_PITCH_CLASS_SPREAD = 0.0

#: Where each class sits in that spread, 0 at the modest end and 1 at the
#: grand. A grander building does take a slightly wider bay — the opening
#: inside it is wider — but slightly is the point.
_BAY_PITCH_CLASS_POSITION: Mapping[BuildingClass, float] = {
    BuildingClass.MODEST: 0.0,
    BuildingClass.ORDINARY: 1.0 / 3.0,
    BuildingClass.COMFORTABLE: 2.0 / 3.0,
    BuildingClass.GRAND: 1.0,
}

#: PROPORTIONAL. What a class of building buys ABOVE a plain storey — the
#: brief's "storey height above its legal minimum", as a (preferred, most)
#: pair. INFERRED in magnitude; only the fact that it is the margin and not
#: the storey that scales is contractual.
_STOREY_MARGIN_PREFERRED = Prop(0.55, "storey height bought above a plain one, ambition-driven")
_STOREY_MARGIN_MOST = Prop(0.95, "the most storey height ambition ever buys above a plain one")

# ---------------------------------------------------------------------------
# The entresol — a programme decision, taken before the budget is filled
# ---------------------------------------------------------------------------
#
# This used to be the solver's ``special``: a short slot offered as a way of
# closing a height budget that whole storeys could not close, and therefore
# present exactly where the class factor happened to leave an awkward
# remainder. Measured over 600 situations that gave 42 % / 64 % / 57 % / 43 %
# by class — not monotonic, and for a reason that has nothing to do with what
# an entresol is. On a boulevard an entresol over a shop is MORE common the
# richer the building, not less.
#
# So it is decided here, from the programme, before anything is filled, and
# the solver is then told to accommodate it as a fixed element of the run.
# Nothing about the height budget can conjure one up or take one away.

#: Which ground-floor uses want a low storey over them. Trade wants one — the
#: stock, the counting-house, the café's gallery, all lit by the top of the
#: shop's own glazing. A residential ground floor has a hall and a stair and
#: no use for a half-storey over it, and a carriage entrance is a hole in the
#: building that something must span.
_ENTRESOL_PROGRAMMES: frozenset[GroundProgramme] = frozenset(
    {GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE}
)

#: **The presence of the compressed level is SOURCED (A9.4); this table is
#: how it is produced, and its figures are INFERRED.**
#:
#: Daly's structural finding is not about how tall an entresol is, it is that
#: there IS one: **14 of the 16 buildings with measured storeys carry a
#: compressed level between the commercial ground storey and the noble
#: floor** — 4 of 4 Première, 10 of 10 Deuxième, 0 of 2 Troisième. What
#: differs is only how the level is dressed. Deuxième calls it an entresol
#: (9 of 10, 2.40-3.12 m); Première calls the same band a low *1er étage*
#: (4 of 4, 3.20-3.60 m) and gives it a full storey's dignity. The two
#: independent readings of one plate (26 rue Bergère) disagreed about which
#: word applied to the same physical band, which is the corpus telling us
#: that the LABEL is an interpretation and the BAND is the measurement.
#:
#: So this table produces the band and ``roles.py`` names it. The contractual
#: content is the ordering — the bar falls as the class rises, which is what
#: makes the compressed level commoner the richer the building, and Daly's
#: 4/4 against 0/2 at the two ends of the ladder is the evidence for it.
#:
#: INFERRED. How many ordinary letting storeys the facade must still carry
#: over the entresol before an owner of this class will give up the height
#: for it. An entresol is bought with height that would otherwise have been
#: an étage; a modest owner cannot spare that unless the building is tall
#: enough not to notice, while a grand one takes it as soon as the section
#: allows. Only the *decreasing* order is contractual — it is what makes the
#: entresol commoner the richer the building, which is the fact this table
#: exists to state.
#:
#: Note what these particular figures currently imply: a MODEST facade never
#: clears its own bar anywhere in Paris, because four letting storeys over a
#: shop and an entresol is more section than 0.74 of any legal ceiling in the
#: tables buys. That is a statement of this table, not a property of the
#: system — the role it produces is reachable for every other class, and one
#: number here changes it — but it is a statement, and a reader who thinks a
#: modest shop should sometimes carry an entresol should change the 4 rather
#: than conclude the mechanism is broken.
_ENTRESOL_STOREYS_REQUIRED: Mapping[BuildingClass, int] = {
    BuildingClass.MODEST: 4,
    BuildingClass.ORDINARY: 3,
    BuildingClass.COMFORTABLE: 2,
    BuildingClass.GRAND: 1,
}

#: **SOURCED (A9.4).** How tall an entresol is as a fraction of the ground
#: storey it stands on. Daly, nine Deuxième Classe buildings: median 0.775,
#: range 0.585-0.871. This is the one number here Daly's sample is strong
#: enough to give as a value rather than as an ordering, and it is a ratio
#: rather than a height because that is the shape the evidence has — the nine
#: heights are 2.40-3.12 m and the nine ground storeys under them are
#: 3.42-4.85 m, and the ratio is tighter than either.
#:
#: Note what it is NOT: a class quantity. No Première and no Troisième
#: building in the corpus has an entresol at all, so there is no ladder to
#: calibrate and the class signal lives entirely in the PRESENCE of the
#: storey — which is where ``_ENTRESOL_STOREYS_REQUIRED`` puts it.
_ENTRESOL_OVER_GROUND = 0.775

#: **INFERRED.** How much taller the floor a compressed storey serves is than
#: the compressed storey itself.
#:
#: Daly reads 1.25 in Première and 1.30 in Deuxième, and 1.275 sits between
#: them — but this constant may NOT be called sourced, for three reasons, and
#: the demotion is deliberate rather than pedantic:
#:   * the nobile ÷ compressed ratio is not among the eleven quantities
#:     `daly_measurements.json` marks SOURCED;
#:   * its Première half is computed from Première storey heights, which the
#:     same file marks WEAK by name ("all Premiere storey-height values");
#:   * it is a *derived ratio*, and DALY_MEASUREMENTS.md warns that derived
#:     ratios carry worse error than either measurement they come from.
#: Two WEAK values divided by one another do not make a sourced one. The value
#: is retained because it is a reasonable guess; the claim is not.
#:
#: This is the relation that makes "squeezed" mean something. Height alone
#: cannot: Daly's nine entresols are 2.40-3.12 m in buildings whose topmost
#: étages run down to 2.32 m, so a squeezed storey is routinely *taller* than
#: some of the storeys above it and is never the shortest thing in the
#: building. What it is always shorter than is the floor it exists to serve.
_COMPRESSED_UNDER_THE_FLOOR_IT_SERVES = 1.275

# ---------------------------------------------------------------------------
# The comble — habitable when it is deep enough to hold a room
# ---------------------------------------------------------------------------
#
# A Paris comble is not empty roof. The *chambres de bonne* are in it, lit by
# the lucarnes the termination phase puts on the slope. So where the roof has
# the clear height and the floor depth for a room, this phase emits a storey
# slot standing inside it; where it does not, it emits nothing and the roof is
# just a roof. Which of the two happened is a question about the envelope, and
# ``Grid.stands_in_the_roof`` is where it is asked.

#: ABSOLUTE. A garret room is small — famously so — but it is a room, and a
#: room needs a bed's length of floor with the ceiling clear above it. This is
#: measured across the parcel, between the two opposing slopes, which is what
#: makes a shallow parcel unable to hold a comble storey at all.
_COMBLE_ROOM_DEPTH = Abs(2.00, "a garret room needs a bed's length of floor under full height")

#: Float tolerance for the postconditions this module asserts on its own
#: output. Millimetres matter here — a storey 4 mm under a legal minimum is
#: still a storey under a legal minimum — so this is float noise only, an
#: order of magnitude tighter than anything anyone measures a building with.
_TOL = 1e-9

#: Tolerance for the one comparison that decides whether a slot is standing
#: on the roof or behind the wall. Looser than ``_TOL`` because a storey's
#: ``start`` is a running sum over the whole stack, and a micron either way
#: must not flip a storey between the facade and the comble.
_ROOF_EPS = 1e-6


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Grid:
    """Phase 1 output. Purely quantitative. NO roles, NO names, NO meaning.

    ``storeys`` is bottom-up; ``bays`` is left-right, solved once for the
    whole building.

    Three heights, and keeping them apart is most of the point of this phase:

    * ``cornice_height`` — the LEGAL ceiling on the stone face (a
      ``Quantity``, carrying its regulatory citation). What the decree
      permits.
    * ``eaves_height`` — where the stone face actually stops. What was built.
      Below the ceiling for anything short of a grand building on a wide
      street; the gap between the two is ambition the owner declined to
      spend, and it is not a defect.
    * ``built_height`` — the same number as ``eaves_height``, asked of the
      storeys instead of stored: the slots standing below the roof, summed.
      Deliberately a reader rather than a field, because it is not a separate
      fact.

    Storeys standing *above* ``eaves_height`` are inside the comble. They are
    ordinary slots on this grid — no flag, no name — and whether a given one
    stands in the roof is answered geometrically by ``stands_in_the_roof``.
    """

    storeys: tuple[PlacedSlot, ...]  # vertical, bottom-up
    bays: tuple[PlacedSlot, ...]  # horizontal, left-right — ONE solve per building
    cornice_height: Quantity
    eaves_height: float
    envelope: GabaritEnvelope
    account: tuple[str, ...]
    #: **A15.1.** Bands of garret this roof stands OVER the number the decree's
    #: own comble allowance stands — 0 or 1, decided from the programme and the
    #: parcel by ``_a_second_storey_of_chambres_de_bonne`` and paid for out of
    #: the cornice height. Stored rather than re-derived because the facade was
    #: already built shorter for it: a second opinion here would be a roof and
    #: a stone face that disagree about what the owner bought.
    extra_garret_storeys: int = 0

    def stands_in_the_roof(self, index: int) -> bool:
        """True when storey ``index`` stands above the top of the stone face.

        A geometric question, not a role: the stone stops at ``eaves_height``
        and anything whose floor is at or above that line is standing inside
        the comble rather than behind the facade. The LEGAL cornice is a
        ceiling on the stone, not the level at which the roof begins — a
        building that declined to spend its last metre of ambition still has
        its roof start where its own wall stopped, and asking the question
        against ``cornice_height`` is exactly why no storey was ever found
        inside a comble.

        Index 0 is never in the roof. The bottom slot is the building
        standing on the pavement whatever the arithmetic says, and a
        degenerate grid whose eaves line sits at or below zero must not turn
        its own footing into a garret. Stated once, here, so that every
        caller downstream reads the same answer.
        """
        if index <= 0:
            return False
        slot = self.storeys[index]
        return slot.start >= self.eaves_height - _ROOF_EPS

    @property
    def built_height(self) -> float:
        """The height of the stone face actually constructed — the storeys
        standing below the roof, summed. Not the legal ceiling, and not the
        full silhouette: the comble stands on top of this.

        A convenience reader over ``storeys``; not a fact this class stores
        independently of them (``solve_structure`` asserts it agrees with
        ``eaves_height`` before returning)."""
        return math.fsum(
            s.width for i, s in enumerate(self.storeys) if not self.stands_in_the_roof(i)
        )

    @property
    def comble_storeys(self) -> tuple[PlacedSlot, ...]:
        """The storey slots standing inside the comble, bottom-up. Empty when
        the roof was too shallow to hold a room."""
        return tuple(s for i, s in enumerate(self.storeys) if self.stands_in_the_roof(i))

    @property
    def comble_height(self) -> float:
        """How tall the comble stands over the eaves it springs from.

        The one place this is answered, because two phases need it and a
        second opinion is how a roof and the storey inside it come to
        disagree: S3 asks it to size the *chambres de bonne*, S7 asks it to
        cut the profile.

        It is NOT ``envelope.ridge_height``. That number is a height above the
        LEGAL cornice, and reading it as a height above the built eaves —
        which is what this phase and the termination phase both used to do —
        silently deducted every centimetre of unspent facade ambition from the
        roof. A building that stopped its stone short did not thereby forfeit
        the legal solid above it: the top of that solid is
        ``envelope.total_height``, wherever the eaves happen to be.

        Nor is the fix to spring the comble from the cornice — that was the
        retracted A2.4, and it would let a roof stand in space the 45°
        diagonal from its own eaves forbids. The springing is the eaves, and
        the recovery comes from tracing *that* curve to a taller top (A3.1).

        Nor is it ``comble_ceiling``. **A8.5**: it used to be, and that made
        every building maximal — the cornice height a modest builder declined
        to spend came straight back as roof, so ``eaves + comble`` landed on
        the legal total in every class and the poorer the building the bigger
        its hat. What is built is a *section* with rooms behind it
        (``_comble_section``); the ceiling is only the line it may not cross.
        """
        return _comble_section(
            self.envelope,
            self.eaves_height,
            self.envelope.parcel_depth,
            self.extra_garret_storeys,
        )[1]

    @property
    def brisis_height(self) -> float:
        """Where the comble's steep lower slope folds into its shallow one,
        measured over the eaves — the *brisis*/*terrasson* break.

        The fold is a fact about the building, not about the drawing: it is
        the ceiling of the *chambres de bonne* and the line a lucarne's face
        rises to. S7 states it in the IR and the renderer draws it; nobody
        downstream recomputes it. Equal to ``comble_height`` where the comble
        was too low to break at all, which is how a caller asks "is there a
        terrasson here?" without a second rule.
        """
        return _comble_section(
            self.envelope,
            self.eaves_height,
            self.envelope.parcel_depth,
            self.extra_garret_storeys,
        )[0]

    @property
    def ridge_setback(self) -> float:
        """How far back from the facade plane the ridge stands, in metres.

        Where the terrasson reaches the top of what the decree allows before
        it reaches the middle of the plot — the ordinary pre-1884 case — this
        is short of ``parcel_depth / 2`` and the rest of the section is a flat
        zinc *terrasse* between the two opposing slopes. Where it does not, the
        two slopes meet and this IS half the plot."""
        return _comble_section(
            self.envelope,
            self.eaves_height,
            self.envelope.parcel_depth,
            self.extra_garret_storeys,
        )[2]

    @property
    def comble_ceiling(self) -> float:
        """The tallest comble these eaves could legally carry on this plot —
        the top of the legal solid expressed over the eaves (A3.1), capped
        where the two opposing slopes meet.

        Two limits, and the smaller wins:

        * **the top of the legal solid**, expressed over the eaves through
          ``_above_the_cornice_to_above_the_eaves`` — the only conversion
          between the two anchors;
        * **the parcel**, since the comble springs from the eaves and the two
          opposing slopes meet at ``max_height_for_setback(parcel_depth / 2)``
          above them however much legal height is left over. This is the limit
          that makes the headroom only *partly* recoverable: a taller top on
          the same curve costs inset, and a shallow plot runs out of it first.

        A ceiling, and read as one: ``comble_height`` is what was built under
        it. The gap between the two is the same kind of fact as the gap
        between ``cornice_height`` and ``eaves_height`` — allowance left
        unspent, which the roof used to swallow.
        """
        return _comble_ceiling_over_the_eaves(
            self.envelope, self.eaves_height, self.envelope.parcel_depth
        )

    @property
    def unused_facade_headroom(self) -> float:
        """Legal cornice height the stone face declined to use, in metres.

        Not a defect and not waste: it is ambition unspent, and it is the
        distance between the two anchors — the offset
        ``_above_the_cornice_to_above_the_eaves`` applies, and the reason a
        comble sprung from these eaves may run further above *them* than the
        ridge stands above the cornice (A3.1)."""
        return max(0.0, self.envelope.facade_height - self.eaves_height)


# ---------------------------------------------------------------------------
# Quantities — everything a rule needs to justify a number, before it
# becomes a bare float for the (domain-blind) SlotSpec.
# ---------------------------------------------------------------------------


def _scaled_value(unscaled: float, why: str, klass: BuildingClass) -> float:
    """A PROPORTIONAL reference value, scaled for ambition, as a bare float."""
    return float(scale_for_class(Prop(unscaled, why), klass))


def _scaled_bounds(
    lo_ref: float, pref_ref: float, hi_ref: float, why: str, klass: BuildingClass
) -> tuple[float, float, float]:
    """Scale a (min, preferred, max) triple by the same class factor, which
    preserves ``min <= preferred <= max`` because scaling is monotonic and
    identical across the three.

    Nothing in this module calls it any more, and that is worth recording
    rather than deleting: every horizontal band it used to resolve — the bay
    pitch (A8.6) and the edge pier (A9.1) — turned out to be masonry rather
    than money, and is now ABSOLUTE. It survives as the composed form of the
    operation for whatever proportional band comes next, and as the marker
    that its two former callers moved deliberately.
    """
    return (
        _scaled_value(lo_ref, why, klass),
        _scaled_value(pref_ref, why, klass),
        _scaled_value(hi_ref, why, klass),
    )


def _bay_pitch_band(klass: BuildingClass) -> tuple[float, float, float]:
    """The ``[minimum, preferred, maximum]`` the bay grid is solved against.

    A8.6. The two bounds are the masonry's and are handed back unchanged for
    every class. **A9.1/A9.4: so is the preferred pitch** — the class spread
    is now zero, because Daly's sixteen buildings show the class ladder in
    this quantity does not exist (non-monotonic, and with within-class spread
    larger than any difference between classes). The result is composed as
    ABSOLUTE and never passes through ``scale_for_class``, so a caller may
    assert directly that the bay grid of a modest frontage and a grand one on
    the same parcel have the same number of bays in them — not "give or take
    one", exactly the same, unless the two buildings have different doors.

    The spread mechanism is kept and centred on ``_BAY_PITCH_PREFERRED``
    rather than on the midpoint of the bounds, so that restoring a trend is
    one constant and so that the resting pitch is a number somebody chose
    rather than an accident of where two unrelated bounds happen to sit.
    """
    lo, hi = float(_BAY_PITCH_MIN), float(_BAY_PITCH_MAX)
    span = hi - lo
    moved = span * _BAY_PITCH_CLASS_SPREAD
    lowest = float(_BAY_PITCH_PREFERRED) - moved / 2.0
    preferred = lowest + moved * _BAY_PITCH_CLASS_POSITION[klass]
    return (lo, min(max(preferred, lo), hi), hi)


def _storey_minimum_quantity(reg: Reglement) -> Quantity:
    """The regulatory floor under a typical storey — or, before 1859 when
    the texts impose none, the physical floor a person needs."""
    if reg.min_floor_height > 0.0:
        return Reg(reg.min_floor_height, reg.decree)
    return _HUMAN_MIN_STOREY_HEIGHT


def _ground_height_quantity(
    ground: GroundProgramme, klass: BuildingClass, entrance: catalogue.Entrance
) -> Quantity:
    """How tall the ground-floor slot must be, by programme AND by its door.

    A carriage entrance is a body that must pass, so it is ABSOLUTE and
    never scales with ambition.

    Since A6.1 every building has an entrance, so every ground storey has a
    door standing in it and every ground storey has a floor under its height
    that the programme cannot argue with: ``entrance.storey_height``, the
    clear height that door needs plus the lintel spanning it. A shop's ground
    floor is normally taller than that anyway — but a *modest* shop on a
    narrow street is not always, and before this the porte piétonne was
    silently the one element the storey was too short to hold. The programme's
    own want and the door's ABSOLUTE need are two claims on one number, so
    they are resolved here, in the open, by taking whichever is greater.

    **A9.4 — the rez-de-chaussée does not scale with class, and this is one
    of the eleven quantities Daly's sample is strong enough to say so about.**
    Sixteen buildings, 3.42-4.85 m, median 3.95 m; the class medians are
    4.20 / 3.95 / 3.81 m, a fall of 9 % across the entire social ladder,
    against ranges that overlap almost completely — the Deuxième range alone
    (3.42-4.85 m) contains every value in every other class. The measurement
    pass calls it "the single most stable absolute in the corpus after the
    door" and recommends it as SOURCED *as class-independent*, which is a
    claim about the KIND of number and not only about its size.

    So the trade ground floor is now one ABSOLUTE figure for every class. It
    was ``_PLAIN_STOREY_HEIGHT`` plus a PROPORTIONAL margin, which ran
    3.75 m (MODEST) to 4.42 m (GRAND) — a ladder in a quantity the source
    says has none, and one whose grand end stood above every building Daly
    drew but one.

    The residential ground floor keeps its own, lower figure and it stays
    INFERRED: Daly's corpus is a corpus of commercial ground floors on
    Haussmann corridors and says nothing whatever about a hall and a stair.
    What carries across is not the number but the finding about its kind —
    a ground storey is a room and a vehicle and a shopfront, none of which
    got bigger when the owner got richer — so this one no longer scales
    either, and says so rather than borrowing a citation it has not got.
    """
    if ground is GroundProgramme.CARRIAGE:
        # The reason is a body and a load passing through, so the wording
        # stays on the body. The number is not restated here: it is the sum
        # of the two ABSOLUTE facts that produce it — the clear height a
        # laden carriage needs and the lintel that spans over it — held in
        # the catalogue, which is also where the opening itself is cut. This
        # module used to carry its own 3.30 m for this, 0.40 m short of the
        # two figures it claimed to be about, and the porte cochère came out
        # capped at 3.00 m clear: an ABSOLUTE that must pass, overruled by a
        # second opinion about the same fact.
        return catalogue.carriage_storey_height()
    if ground in (GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE):
        wanted = _TRADE_GROUND_HEIGHT
    else:
        wanted = _PLAIN_STOREY_HEIGHT + _RESIDENTIAL_GROUND_MARGIN
    needed = entrance.storey_height
    if float(needed) > float(wanted) + _TOL:
        return Abs(
            float(needed),
            f"{needed.why} — the {entrance.kind} standing in this storey needs more "
            f"height than the {ground.value} ground floor would otherwise have bought "
            f"({float(wanted):.2f} m), and the door is ABSOLUTE",
        )
    return wanted


def _typical_storey_band(reg: Reglement, klass: BuildingClass) -> tuple[Quantity, Quantity, Quantity]:
    """The ``[minimum, preferred, most]`` band for a typical habitable storey.

    Three quantities of three different kinds, and the kinds are the whole
    point:

    - the **minimum** is REGULATORY (or, before 1859, the ABSOLUTE human
      floor) — a number in a text, which ambition may not move;
    - **preferred** and **most** are a plain storey (ABSOLUTE) plus a
      PROPORTIONAL margin that ambition buys.

    Scaling the margin rather than the whole height is what keeps the band
    architectural. Under the earlier form the band was
    ``scale_for_class(Prop(3.10 .. 3.55))``, so COMFORTABLE preferred 4.08 m
    and GRAND 4.79 m and the class factor was silently paying for the joists
    as well as the ceiling rose. Both bounds are returned as quantities so
    the caller can narrate *why* each edge of the band is where it is.

    Named and returned rather than inlined at the call site so a test can
    assert against the band this module actually declares instead of
    re-deriving it from the same literals.
    """
    minimum = _storey_minimum_quantity(reg)
    preferred = _PLAIN_STOREY_HEIGHT + scale_for_class(_STOREY_MARGIN_PREFERRED, klass)
    most = _PLAIN_STOREY_HEIGHT + scale_for_class(_STOREY_MARGIN_MOST, klass)
    # A band must be ordered even where a future règlement's minimum rises
    # above what ambition would have chosen: the law wins and the band
    # collapses upward onto it, never the other way round.
    if float(preferred) < float(minimum):
        preferred = minimum
    if float(most) < float(preferred):
        most = preferred
    return minimum, preferred, most


def _entrance_slot_width_quantity(entrance: catalogue.Entrance) -> Quantity:
    """The frontage this building's entrance takes up — ABSOLUTE, never scales.

    A slot in this phase is a piece of WALL, not an opening: the 3.45 m bay
    beside this one carries a 1.32 m window between two real piers. So either
    entrance's slot is the clear width that has to pass through it PLUS the
    jamb its head lands on either side, and both figures are the catalogue's,
    stated once.

    This was ``_carriage_slot_width_quantity``, with its own ``Abs(3.00)`` —
    the clear width, with no jambs — which made this the one slot on the
    frontage that was an opening rather than a piece of wall and left the
    porte cochère as the one opening with no masonry beside it (A4.1's "a real
    pier either side"). Since A6.1 there are two doors rather than one, so
    the arithmetic is the catalogue's for both and this only reads it.
    """
    return entrance.slot_width


def _entrance_index_hint(n_bays: int) -> tuple[int, str]:
    """Where the entrance stands in the interior run, and why (A6.1).

    **The rule is positional and it is stated, not left to chance.** The
    entrance takes the MIDDLE of the run. ``index_hint`` is the number of bays
    standing to its left, so ``n_bays // 2`` puts the same number of bays each
    side of it whenever ``n_bays`` is even, and the door is on the axis.

    Where ``n_bays`` is odd there is no middle to take: any index leaves one
    more bay on one side than the other. The entrance then takes the stated
    offset of **half a bay left of the axis** — the same ``n_bays // 2``, one
    bay short on the left — and the composition *answers* it, because the
    fitting solver's ``_special_side`` reads exactly this index hint and puts
    the narrow special on the opposite (right-hand) side of the run. So the
    two halves of the brief's requirement are one arithmetic fact rather than
    two rules that could disagree:

    > "when it sits off-centre the composition should answer it — putting the
    >  narrow special on the opposite side, for instance."

    Returns the hint and the sentence the account narrates it with.
    """
    hint = n_bays // 2
    if n_bays % 2 == 0:
        return hint, (
            f"entrance placed ON the axis: {hint} bay(s) either side of it in a run of "
            f"{n_bays} — a positional rule, not a remainder"
        )
    return hint, (
        f"entrance placed half a bay LEFT of the axis: {hint} bay(s) to its left and "
        f"{n_bays - hint} to its right, because a run of {n_bays} has no middle "
        "element to take. The composition answers the offset — a lone narrow special "
        "goes to the right-hand end, which is the side the door is not on"
    )


def _entresol_height(ground_height: float) -> Quantity:
    """How tall the low storey over a shop is, when the programme wants one.

    **A9.4 — a RATIO to the storey below it, and SOURCED.** Daly measures
    nine Deuxième Classe entresols: median **2.98 m**, range 2.40-3.12 m, and
    an entresol/ground ratio whose median is **0.775** (range 0.585-0.871,
    n = 9). The ratio is the sourced quantity, not the height: an entresol is
    the top of the shop's own volume, cut off at the level the shopfront's
    top lights reach, so it is a fraction of the storey under it rather
    than a number of its own. Stating it that way means the entresol follows
    the ground floor wherever the ground floor goes — a tall boutique gets a
    tall entresol — with no second opinion to keep in step.

    **It is ABSOLUTE, not proportional**, and the distinction is worth being
    exact about: the ratio multiplies an ABSOLUTE ground storey, so by the
    rigidity rule the product is ABSOLUTE too, and the entresol does not move
    with the class any more than the shop below it does. Daly agrees — this
    is a Deuxième-only quantity precisely *because* the presence of an
    entresol is the class marker, never its height.

    This replaces a flat ``Abs(2.20)`` held deliberately clear of the
    habitable-storey minimum, on the reasoning that the exemption letting an
    entresol exist is an exemption *from* that minimum. **Daly refutes that
    reasoning outright**: his nine entresols run 2.40 to 3.12 m and the
    median, 2.98 m, is well ABOVE the 1859 decree's 2.60 m — six of the nine
    clear it. A Paris entresol is not a slot squeezed under a legal floor; it
    is the head of a commercial volume, and it is short only relative to
    the étages, which is exactly what a ratio says and what a ceiling clamped
    to the statute could not.
    """
    return Abs(
        ground_height * _ENTRESOL_OVER_GROUND,
        f"SOURCED — Daly 1864 (Sér. 1 Vol. 1 t. 2): nine Deuxième Classe entresols, "
        f"entresol/ground ratio median {_ENTRESOL_OVER_GROUND:.3f} (range 0.585-0.871), "
        f"heights 2.40-3.12 m about a median of 2.98 m (scale-bar measured, ±10 %). "
        f"Applied to this building's {ground_height:.2f} m ground storey. ABSOLUTE, "
        "because an ABSOLUTE ground storey times a ratio is ABSOLUTE: the entresol "
        "is the top of the shop's own volume and does not move with ambition — its "
        "PRESENCE is the class marker, not its height"
    )


def _wants_an_entresol(
    ground: GroundProgramme,
    klass: BuildingClass,
    *,
    budget: float,
    ground_height: float,
    entresol_height: float,
    storey_preferred: float,
) -> tuple[bool, str]:
    """Whether the programme asks for a low storey over the ground floor.

    Two questions, both answered before a single metre of the height budget
    has been filled, so that nothing about how the budget happens to divide
    can produce or suppress one:

    1. **Does the use want it?** Trade does; a hall and a stair do not.
    2. **Will this owner pay for it?** The height comes out of the letting
       floors, so the building has to be tall enough to still carry
       ``_ENTRESOL_STOREYS_REQUIRED[klass]`` of them above it — a bar that
       falls as the class rises, which is what makes the entresol commoner
       the richer the building.

    Returns the decision and the sentence that justifies it, so the account
    can narrate a refusal as readily as an acceptance.
    """
    if ground not in _ENTRESOL_PROGRAMMES:
        return False, (
            f"ground floor ({ground.value}) is not a trade that wants a low storey over "
            "it — no entresol, whatever the height budget leaves over"
        )
    required = _ENTRESOL_STOREYS_REQUIRED[klass]
    needed = ground_height + entresol_height + required * storey_preferred
    if budget + _TOL < needed:
        return False, (
            f"ground floor ({ground.value}) wants an entresol, but class {klass.value} "
            f"only gives up the height where {required} letting storey(s) still stand "
            f"over it: that needs {needed:.2f} m and the facade budget is {budget:.2f} m"
        )
    return True, (
        f"ground floor ({ground.value}) wants an entresol and class {klass.value} will "
        f"pay for it: {required} letting storey(s) still stand over it inside a "
        f"{budget:.2f} m facade budget (needs {needed:.2f} m). Decided from programme, "
        "before the budget is filled — never from what the budget left over"
    )


#: How far the built eaves may sit *above* the legal cornice before
#: ``_above_the_cornice_to_above_the_eaves`` refuses to convert. Zero, up to
#: float noise: a facade that overran its ceiling is an S1 failure, and
#: converting a height across an inverted pair of anchors would hide it.
_ANCHOR_TOL = 1e-6


def _above_the_cornice_to_above_the_eaves(
    height_above_the_cornice: float, envelope: GabaritEnvelope, eaves: float
) -> float:
    """Convert a CORNICE-relative height into an EAVES-relative one.

    The one boundary between the two datums this module speaks, and the only
    place a number may cross it (A3.1 §3). The gabarit is *written* from the
    legal cornice — ``envelope.ridge_height`` and ``legal_ridge_height`` are
    both heights above ``envelope.facade_height`` — while the comble is
    *built* from the égout du toit, the eaves the building actually has. The
    two lines differ by the cornice height the facade declined to spend, and
    applying a number from one at the other without adding that difference is
    the arithmetic that produced both the original defect and the retracted
    A2.4 "fix" for it. Naming the conversion is what stops it recurring
    silently: an unconverted mix now has to be written as an addition someone
    can see.

    The assertion is not decoration. The eaves may sit below the legal cornice
    (the ordinary case, and the whole subject of A3.1) or exactly on it, never
    above it — ``solve_structure`` fills a budget capped at the cornice. Eaves
    above the cornice would make the offset negative and this function would
    quietly *shorten* the very heights it exists to raise.
    """
    drop = float(envelope.facade_height) - float(eaves)
    assert drop >= -_ANCHOR_TOL, (
        f"eaves at {float(eaves):.4f} m stand above the {envelope.facade_height:.4f} m "
        "legal cornice, so there is no conversion from cornice-relative to "
        "eaves-relative heights to make: the facade has already broken the gabarit "
        "and no arithmetic here can put it back inside."
    )
    return float(height_above_the_cornice) + max(0.0, drop)


def _comble_ceiling_over_the_eaves(
    envelope: GabaritEnvelope, eaves: float, parcel_depth: float
) -> float:
    """How tall the comble **may** stand over the eaves it springs from.

    The CEILING on the comble, not the comble. What was actually built is
    ``_comble_section`` below, which stops where the rooms stop; this is the
    line it may not cross. The two were one number until A8.5, which is
    exactly how every building came out maximal.

    The comble **springs from the eaves** — the égout du toit, which is what
    the decree says and what the retracted A2.4 got wrong. So the curve in the
    section is the decree's curve laid on *this building's* eaves line: a 45°
    plane before 1884, Alphand's arc after, starting where the stone stops.
    Nothing here re-anchors that springing, and a building that stopped its
    stone short does not get to start its roof higher up.

    What *is* recoverable is the top. The curve is bounded by two facts that
    have nothing to do with where it springs from, and the smaller wins:

    * **the top of the legal solid.** ``envelope.total_height`` is a height
      above the pavement and does not come down with the eaves, so a facade
      that stopped short still has all of it overhead. Expressed over the
      eaves it is ``ridge_height`` converted through
      ``_above_the_cornice_to_above_the_eaves`` — the same curve carried to a
      *taller top*, which is exactly what ``slope_profile(top=...)`` is for;
    * **the parcel.** The two opposing slopes spring from the same eaves and
      meet at ``max_height_for_setback(parcel_depth / 2)`` above them. This is
      why the headroom is only *partly* recoverable: running the same curve
      higher costs inset, and a shallow plot runs out of inset first. No
      amount of unspent facade allowance pushes a ridge past the middle of the
      plot.

    So the recovered height is bought at the price the règlement charges for
    it — depth — rather than granted by moving the datum. In the canonical
    20 m / 1865 / comfortable case the eaves stop 1.23 m below the cornice and
    the comble runs 4.40 m above them instead of 3.17 m, standing 4.40 m back
    from the facade instead of 3.17 m, on a plot with 7.00 m to give.
    """
    if parcel_depth <= 0.0:
        return 0.0
    top_of_the_legal_solid = _above_the_cornice_to_above_the_eaves(
        envelope.ridge_height, envelope, eaves
    )
    where_the_slopes_meet = envelope.max_height_for_setback(parcel_depth / 2.0)
    return max(0.0, min(top_of_the_legal_solid, where_the_slopes_meet))


def _the_decrees_own_comble_allowance(
    envelope: GabaritEnvelope, parcel_depth: float
) -> float:
    """How tall a comble the decree itself stands, in metres.

    Two facts, and the smaller wins: the comble allowance the decree writes
    over the cornice (``envelope.ridge_height``), and the height at which the
    parcel's two opposing slopes meet. Both are written from the DECREE and
    the PLOT and neither mentions this building, which is what makes it safe
    to read at cornice level — before the eaves exist — as well as after.

    Not a ceiling on the comble (that is ``_comble_ceiling_over_the_eaves``,
    which is anchored at the eaves and recovers the facade's unspent height)
    and not the comble (that is ``_comble_section``). It is the allowance, and
    the only thing that reads it is the arithmetic below that counts how many
    *chambres de bonne* it stands.
    """
    if parcel_depth <= 0.0:
        return 0.0
    return max(
        0.0,
        min(
            float(envelope.ridge_height),
            envelope.max_height_for_setback(parcel_depth / 2.0),
        ),
    )


def _garret_storeys_the_decrees_allowance_stands(envelope: GabaritEnvelope) -> int:
    """How many whole *chambres de bonne* the decree's comble allowance stands
    over the LEGAL cornice, before any plot is brought into it.

    The same count as ``_garret_storeys_the_decree_stands`` with the parcel
    taken out of it, and it is a separate function because it answers a
    different question for a different consumer. This one decides how much
    CORNICE HEIGHT a run gives up, and the cornice runs across the party wall
    (A15.1 §3): every fact it reads has to be one the whole block shares, and
    the parcel depth is not — it varies lot to lot. The other one decides how
    many bands THIS building's section stands, which is a parcel question and
    reads the parcel.

    One under a 45° diagonal, whatever the street; two or three under an 1884
    or 1902 arc, which is what those decrees were for and why no building of
    those eras has any cornice height to trade.
    """
    band = float(BRISIS_RISE)
    ridge = max(0.0, float(envelope.ridge_height))
    if ridge <= 0.0 or band <= 0.0:
        return 0
    return max(1, int(ridge / band + _TOL))


def _garret_storeys_the_decree_stands(
    envelope: GabaritEnvelope, parcel_depth: float
) -> int:
    """How many whole *chambres de bonne* the decree's own allowance stands.

    The A8.3 count, unchanged and now named: the brisis rises in whole rooms,
    never a fraction of one, so this is the allowance divided by
    ``BRISIS_RISE`` and rounded down — one under a 45° diagonal, two or three
    under an 1884 or 1902 arc, which is what those decrees were for.

    A comble with an allowance at all stands at least one room, even where the
    allowance is short of a whole band: the section is then cut off by the
    allowance rather than by the room, which is the shallow-roof case and is
    how it has always behaved.
    """
    allowance = _the_decrees_own_comble_allowance(envelope, parcel_depth)
    if allowance <= 0.0:
        return 0
    band = float(BRISIS_RISE)
    return max(1, int(allowance / band + _TOL)) if band > 0.0 else 1


def _the_shortest_room_a_garret_may_hold(envelope: GabaritEnvelope) -> float:
    """The clear height under which a band of brisis holds no room at all.

    The REGULATORY floor the facade's own storeys are held to — the 1859 and
    1902 hygiene provisions — because a *chambre de bonne* is a room somebody
    lives in and the decree does not stop at the eaves; or, where the era
    imposes none, the physical floor, a room a person can stand up in. Read
    off the envelope's own era rather than passed in, so no caller can ask
    this question about a different decree from the one it is standing under.

    Stated once, here, because it is asked in two places that must not
    disagree: ``_garret_storeys_the_parcel_holds`` counting the bands a plot
    would carry, and ``_comble_storey_heights`` emitting the rooms behind the
    bands it built. While the count used the human floor and the emitter used
    the decree's, a plot between the two — 12.20 to 13.00 m of depth at 1865 —
    was counted as holding a second room and then emitted only one, so a
    brisis could stand two bands in front of one room. That is the A8.3
    defect, and after A16.1 it was also a band paid for and never received.
    """
    return max(
        float(_HUMAN_MIN_STOREY_HEIGHT),
        float(_storey_minimum_quantity(get_reglement(envelope.era))),
    )


def _garret_storeys_the_parcel_holds(
    envelope: GabaritEnvelope, parcel_depth: float
) -> int:
    """How many whole bands of brisis have a habitable room behind them, on
    this plot, ignoring what the decree allows above the cornice.

    The question the parcel answers, asked band by band with exactly the three
    limits ``_comble_storey_heights`` applies to the rooms it emits — the band
    itself, the depth the two opposing slopes leave at that height, and a
    typical storey — so a band counted here is a band that will hold a room
    when it is built, and the two cannot disagree.

    This is the constraint A15.1 calls for by name: *on a shallow parcel the
    45° diagonals meet before the second storey fits, and it must not be
    built*. It is derived rather than declared — at 1865 it works out at about
    12.2 m of plot for a second storey, because a room's floor 2.90 m up on a
    45° section is already 5.80 m narrower than the parcel — and nothing here
    is a tolerance or a guard.
    """
    if parcel_depth <= 0.0:
        return 0
    band = float(BRISIS_RISE)
    if band <= 0.0:  # pragma: no cover - defensive
        return 0
    habitable = _the_shortest_room_a_garret_may_hold(envelope)
    held = 0
    while held < _MOST_GARRET_STOREYS:
        clear = _clear_height_of_a_garret_band(envelope, parcel_depth, held, band)
        if clear < habitable - _ROOF_EPS:
            break
        held += 1
    return held


def _extra_garret_storeys_the_parcel_holds(
    envelope: GabaritEnvelope, parcel_depth: float
) -> int:
    """How many bands of garret this plot holds OVER the ones the decree's own
    allowance already stands on it — i.e. how many a facade could buy here and
    actually RECEIVE.

    **A16.1, and the reason this exists is that it is the ONLY answer to that
    question.** It used to be asked twice and answered independently: the
    buyer (``_a_second_storey_of_chambres_de_bonne``) decided to spend a band
    of cornice height reading the street, the programme and the ceiling, and
    the holder (``_comble_section``) then refused to build the band on a
    shallow plot. Nothing tied them together, so on a 10 or 12 m parcel a shop
    gave up 4 m of facade and received exactly the one garret storey a
    residential building gets for nothing.

    Both now call this, so the height that is spent and the band that is built
    are the same number by construction rather than by agreement.
    """
    return max(
        0,
        _garret_storeys_the_parcel_holds(envelope, parcel_depth)
        - _garret_storeys_the_decree_stands(envelope, parcel_depth),
    )


def _facade_given_up_for_a_bought_garret(bands: int) -> float:
    """The cornice height the stone face gives up to buy ``bands`` extra
    storeys of *chambres de bonne*: **one band of garret each, and nothing
    else**.

    **A16.2.** A band of garret is one storey of rooms, so it costs one storey
    of facade — and the storey it costs is the storey it IS. The figure is
    ``BRISIS_RISE``, which is itself composed of the room and the plate the
    terrasson lands on (``_PLAIN_STOREY_HEIGHT + _BRISIS_PLATE``) rather than
    restated as a number, so the height the stone gives up and the height the
    zinc receives are one quantity and cannot drift apart. Read the same way
    ``_stone_under_a_bought_garret`` is: composed of what it is made of.

    What this is NOT is a fifth of the ceiling. Before A16.2 the observed drop
    on a 20.00 m ceiling was 4.01 m — a whole étage and half of another —
    because a band of price was compounded by a facade budget divided against
    an entresol the section then held down and never gave back (see
    ``_entresol_the_section_will_stand``). Daly's two two-storey garrets sit
    at cornices of 17.52 and 17.55 m under the same 20 m decree: about one
    storey of stone given up, which is what this is.

    The RATE at which the trade is taken remains INFERRED (A15.2) — Daly's
    3-of-9 is drawn from a quantity his own measurement pass marks
    INSUFFICIENT — and the two cornices above are a CHECK on the price, not
    its source.
    """
    return max(0, int(bands)) * float(BRISIS_RISE)


def _stone_under_a_bought_garret() -> float:
    """The stone that has to stand under a bought garret before the trade is
    worth making: the trade floor, the entresol over it, and THREE letting
    storeys.

    The servants in the roof are the servants of the households below, so a
    facade with no households left after the trade has nobody to house — and a
    building giving up a fifth of a narrow street's 11.70 m cornice to gain
    servants' rooms has traded the wrong way round. Composed of the quantities
    it is made of rather than restated as a figure, for the same reason
    ``BRISIS_RISE`` is.

    It works out at 14.81 m, so on the 1859 tables only the 20 m step clears
    it — a street over 20 m, which is where Daly's two two-storey garrets are
    (1 and 2-4 boulevard de Sébastopol, a 30 m percée). That is a CHECK on the
    bar and deliberately not its source: the rate is INFERRED (A15.2), n = 2
    cannot support one, and only the ordering is contractual.
    """
    return (
        float(_TRADE_GROUND_HEIGHT)
        + _ENTRESOL_OVER_GROUND * float(_TRADE_GROUND_HEIGHT)
        + 3.0 * float(_PLAIN_STOREY_HEIGHT)
    )


def _a_second_storey_of_chambres_de_bonne(
    envelope: GabaritEnvelope,
    ground: GroundProgramme,
    facade_ceiling: float,
    parcel_depth: float,
) -> tuple[int, str]:
    """Whether this building buys a second storey of garret out of its
    cornice height — ``(extra bands, the sentence that justifies it)``.

    **A15.1, as A16.1 corrects it.** The decision, and the whole of it. Four
    questions, none of which is the class, and the first ``no`` answers it:

    1. **Does the gabarit already stand more than one storey of rooms?** Where
       the decree's own allowance stands two or three — the 1884 and 1902
       arcs — the garret is there for nothing and no stone is given up for
       it. It is the roof whose allowance stands exactly ONE room that has a
       trade to make, which is the 45° diagonal and is precisely where the
       comble was found to be a constant.
    2. **Would this plot hold the band if it were bought?**
       ``_extra_garret_storeys_the_parcel_holds``, asked here rather than left
       to contradict this decision three phases later — see **A16.1** below.
    3. **Does the programme want it?** ``_ENTRESOL_PROGRAMMES``, and the same
       set for the same reason: trade takes levels of the stone face that
       would have been let, and the dwellings come back under the roof. It is
       also exactly ``block.GroundRegime.COMMERCIAL``, which is what makes it
       safe to read here — see §3 of the note this module's A15 section opens
       with.
    4. **Is there a facade left to buy it with?** The band comes out of the
       cornice at the price ``_facade_given_up_for_a_bought_garret`` charges,
       and ``_stone_under_a_bought_garret`` has to stand under it afterwards.

    **A16.1 — why the parcel is now one of the questions.** A15 kept it out
    on the grounds that the cornice runs across the party wall (circulaire du
    21 septembre 1855) while parcel depths do not, and left the depth to bind
    later, in the SECTION. The section duly refused the band on a shallow lot
    — and nothing carried that refusal back here, so the height went on being
    spent. Measured: a 10 m or 12 m lot with a shop under a 20.00 m ceiling
    gave up a band of cornice and came out at 15.99 m with exactly ONE storey
    of garret, which is the storey a residential building gets for nothing.

    A band paid for and never received is not a smaller fault than a cornice
    that steps at a party wall; it is the same fault with nobody to notice it.
    So the buyer asks the holder before it pays, through the one function that
    answers the question — the same one ``_comble_section`` clamps against —
    and the two can no longer hold independent opinions about one fact. What
    it costs is that the trade is a lot decision: a commercial run wide enough
    to offer the trade whose lots straddle the depth that holds a second band
    (about 12.20 m at 1865, against a typical Paris lot of 18 m) would break
    its cornice line, and ``block.check_alignment`` says so out loud rather
    than letting it pass.

    The RATE this produces is **INFERRED** and must not be calibrated
    (A15.2): Daly's 3-of-9 is drawn from a sample marked INSUFFICIENT for
    exactly this quantity, with a known publication bias. What may be
    asserted is that both modes occur and that the second one carries a
    second row of lucarnes.
    """
    stands = _garret_storeys_the_decrees_allowance_stands(envelope)
    if stands != 1:
        return 0, (
            f"the decree's own comble allowance ({envelope.ridge_height:.2f} m over the "
            f"cornice) already stands {stands} storey(s) of chambres de bonne, so there "
            "is no cornice height to trade for garret: the gabarit is already carrying "
            "the rooms"
        )
    holds = _extra_garret_storeys_the_parcel_holds(envelope, parcel_depth)
    if holds < 1:
        return 0, (
            f"a {parcel_depth:.2f} m parcel holds no band of brisis above the "
            f"{_garret_storeys_the_decree_stands(envelope, parcel_depth)} the decree's "
            "own allowance already stands on it — the two 45° slopes meet before a "
            "second room has its floor — so there is nothing here to buy and the "
            "cornice keeps its height (A16.1: what is paid for has to be received)"
        )
    if ground not in _ENTRESOL_PROGRAMMES:
        return 0, (
            f"ground floor ({ground.value}) is not a trade taking letting floors out of "
            "the stone face, so there are no displaced households to house in the roof "
            "— one storey of chambres de bonne, the storey the decree's own allowance "
            "stands"
        )
    stone = _stone_under_a_bought_garret()
    price = _facade_given_up_for_a_bought_garret(1)
    if facade_ceiling - price + _TOL < stone:
        return 0, (
            f"a second storey of chambres de bonne costs {price:.2f} m of "
            f"the {facade_ceiling:.2f} m legal cornice, which would leave "
            f"{facade_ceiling - price:.2f} m of stone under it — less than "
            f"the {stone:.2f} m a trade floor, its entresol and three letting storeys "
            "need. The servants in the roof are the servants of the households below, "
            "and there would not be enough of them"
        )
    return 1, (
        f"ground floor ({ground.value}) takes letting floors out of the stone face and a "
        f"{facade_ceiling:.2f} m legal cornice still stands {stone:.2f} m of trade floor, "
        f"entresol and letting storeys after the trade, so the roof carries TWO storeys "
        f"of chambres de bonne and buys the second out of the cornice: "
        f"{price:.2f} m off the ceiling — one band of garret and nothing else "
        f"({BRISIS_RISE.why}) — and the legal solid overhead does "
        "not move. INFERRED (A15.2) — Daly's plates show both modes and cannot support a "
        "rate, so this is a mechanism and not a frequency. The band is bought only "
        f"because this {parcel_depth:.2f} m parcel holds {holds} band(s) over the "
        "decree's own, which is what makes the height spent a height received (A16.1)"
    )


#: The most bands of garret this module will look for on any plot. Not a rule
#: about roofs — the 1902 gabarit stands four on a deep parcel and gets them —
#: only a terminator on the loop that counts them, an order of magnitude above
#: anything the tables allow.
_MOST_GARRET_STOREYS = 12


def _clear_height_of_a_garret_band(
    envelope: GabaritEnvelope,
    parcel_depth: float,
    band_index: int,
    band: float,
    brisis: float | None = None,
) -> float:
    """The clear height of the room behind band ``band_index`` of a brisis.

    Three limits and the smallest wins, and they are the three
    ``_comble_storey_height`` has always applied — stated once here so that
    the count of bands the plot holds and the heights of the rooms actually
    emitted are the same arithmetic:

    * **the band.** Its foot is ``band_index * band`` over the eaves and its
      ceiling is the fold above it, less the plate the rafters land on. Where
      *brisis* is given the topmost band is cut off by it, which is what
      happens when the gabarit or the plot stops the section mid-room.
    * **the depth the two opposing slopes leave.** A room needs
      ``_COMBLE_ROOM_DEPTH`` of floor under full height, so the room's ceiling
      may stand no higher than ``max_height_for_setback((depth - room) / 2)``
      — the same curve read the other way — and this band's share of that is
      measured from its own floor.
    A typical storey does not appear among the limits and does not need to:
    a band is one *chambre de bonne* and its plate, so the room inside it is
    ``_PLAIN_STOREY_HEIGHT`` at most, which is under the shortest typical
    storey any class ever builds. ``_comble_storey_heights`` applies the
    typical-storey cap anyway, where it is harmless; it must not be applied
    HERE, because the count of bands the plot holds decides how much cornice
    height the facade gives up, and nothing about that decision may read the
    class (A15.2).
    """
    foot = band_index * band
    top = foot + band if brisis is None else min(foot + band, brisis)
    under_the_fold = top - float(_BRISIS_PLATE) - foot
    if under_the_fold <= 0.0 or parcel_depth <= 0.0:
        return 0.0
    half_free = (parcel_depth - float(_COMBLE_ROOM_DEPTH)) / 2.0
    if half_free <= 0.0:
        return 0.0
    under_the_slopes = envelope.max_height_for_setback(half_free) - foot
    return min(under_the_fold, under_the_slopes)


def _comble_section(
    envelope: GabaritEnvelope,
    eaves: float,
    parcel_depth: float,
    extra_garret_storeys: int = 0,
) -> tuple[float, float, float]:
    """The comble the builder actually cut, as
    ``(brisis, ridge, ridge_inset)`` — two heights above the eaves it springs
    from, and how far back from the facade the ridge stands.

    A *comble brisé* is two planes, and this returns the fold between them and
    the top. It is the one place either number is decided, because S3 sizes
    the garret against the first and S7 cuts the profile against both, and a
    second opinion is how a roof and the room inside it come to disagree.

    **The ridge** is where the terrasson gets to. Everything that decides it —
    the decree's own comble allowance, the plot's depth, the number of garret
    storeys that allowance will stand — is a function of the street, the era
    and the parcel, and of NOTHING about the owner. Two immeubles side by
    side, one modest and one grand, carry the same comble at different
    heights; the money is in the stone below it, not in the zinc.

    **A8.5** is that this used to read ``_comble_ceiling_over_the_eaves``
    instead. The ceiling is a real and correct number (A3.1: the top of the
    legal solid does not descend with the eaves) but it is a CEILING, and
    building to it made the roof grow by exactly what the facade gave up. The
    two moved in lockstep, the sum never moved at all, and every building in
    the city came out at ``legal_total_height`` — the brief's named failure,
    "conflating them makes every building a maximal building", arrived by a
    different road. The ceiling is still enforced, one line below, as what it
    is: a limit that mostly does not bind.

    **The brisis** rises in whole *chambres de bonne*: as many ``BRISIS_RISE``
    bands as the decree's own comble allowance will stand, and never a
    fraction of one. That is how the 1884 and 1902 gabarits show what they
    were FOR — the arc lets the slope stand nearly plumb, so the same decree
    that raised the roof put a second and a third storey of rooms behind it,
    and the fold climbs to meet them. Its foot is on the envelope, so the
    inset at the fold is ``setback_at(brisis)`` and never a number chosen
    here, and ``terminate`` puts one row of lucarnes on each band (A8.3): the
    brisis is the garret's outside WALL, and a wall with rooms behind it and
    no windows in it is the bare-zinc defect wearing different arithmetic.

    The count is taken from the *allowance* and not from
    ``_comble_ceiling_over_the_eaves``, which is the difference between a
    number about the decree and a number about this owner's budget. Quantised
    against the ceiling, a modest building's unspent stone could buy it a
    whole extra band of garret and the class totals stopped being ordered.

    **The terrasson** closes over the top band at ``_TERRASSON_PITCH_DEG``. It
    runs back either to the middle of the plot, where the two opposing slopes
    meet, or to the top of what the decree allows — whichever it reaches
    first. Where the decree stops it short the last of the section is a flat
    zinc *terrasse* between the two slopes, which is the ordinary pre-1884
    case and the reason ``ridge_inset`` is a third answer rather than "half
    the parcel": on a 16 m plot an 1865 terrasson tops out about 4.3 m back
    and the remaining 3.7 m is deck.

    It never leaves the gabarit. It starts ON the envelope and both its ends
    are under it (the ridge is capped by the allowance and by the plot), and
    every envelope in ``reglement`` is concave — a 45° plane, a quarter arc,
    an eighth arc easing into a 45° oblique — so the chord between two points
    under a concave curve stays under it. ``terminate`` asserts containment
    anyway; this is a reason, not a substitute for the check.

    A comble with no height to break in returns the same number twice, which
    is how a caller asks "is there a fold here?" without a second rule.

    **A15.1 — ``extra_garret_storeys``.** How many bands of garret the roof
    stands OVER the number the decree's own allowance stands, decided once by
    ``_a_second_storey_of_chambres_de_bonne`` and passed in rather than
    re-derived, because ``solve_structure`` has already taken the same number
    out of the facade's cornice height and the two may not disagree. Zero —
    the default, and every era whose gabarit already stands the rooms — leaves
    this function's arithmetic exactly as A8.5 left it. One raises the
    allowance by one whole *chambre de bonne*, which is what the facade paid
    for, and by nothing else: the roof grows by the rooms and not by the
    headroom, so A8.5's "the ceiling is not a target" survives intact. The
    ceiling is still enforced above both.
    """
    if parcel_depth <= 0.0:
        return (0.0, 0.0, 0.0)
    half_depth = parcel_depth / 2.0
    ceiling = _comble_ceiling_over_the_eaves(envelope, eaves, parcel_depth)
    band = float(BRISIS_RISE)
    decree = _the_decrees_own_comble_allowance(envelope, parcel_depth)
    stands = _garret_storeys_the_decree_stands(envelope, parcel_depth)
    # **A15.1, and this is the plot's own answer about its own section.** A
    # band of brisis is only built where the plot puts a room behind it, and
    # where it does not the roof is the one the decree's own allowance stands
    # — never a tall bare brisis with nothing behind it, which is the A8.3
    # defect wearing a second storey.
    #
    # **A16.1**: this and the purchase now ask ONE function, so the clamp can
    # no longer contradict what the cornice paid for — a band bought is a band
    # this plot was already known to hold. It stays because ``extra`` is an
    # argument: a caller that passes a number of its own must still not be
    # able to build rooms the plot has no floor for.
    extra = max(0, min(int(extra_garret_storeys),
                       _extra_garret_storeys_the_parcel_holds(envelope, parcel_depth)))
    allowance = min(decree + extra * band, ceiling)
    if allowance <= 0.0:
        return (0.0, 0.0, 0.0)

    bands = stands + extra
    brisis = min(bands * band, allowance)

    fold_inset = envelope.setback_at(brisis)
    run = max(0.0, half_depth - fold_inset)
    slope = math.tan(math.radians(_TERRASSON_PITCH_DEG))
    ridge = min(brisis + run * slope, allowance)
    rise = max(0.0, ridge - brisis)
    reach = fold_inset + (rise / slope if slope > 0.0 else run)
    return (brisis, max(brisis, ridge), min(max(reach, fold_inset), half_depth))


def _comble_storey_heights(
    envelope: GabaritEnvelope,
    eaves: float,
    parcel_depth: float,
    storey_maximum: float,
    extra_garret_storeys: int,
) -> tuple[float, ...]:
    """The clear height of every storey standing inside the comble, bottom-up,
    and empty where the roof cannot hold one.

    One entry per band of brisis the section stands, each measured by
    ``_clear_height_of_a_garret_band`` — the band itself less the plate, the
    depth the two opposing slopes leave at that band's own floor, and a
    typical storey; smallest wins. The rooms and the roof are therefore the
    same arithmetic: the brisis this reads is ``_comble_section``'s, so a
    gabarit or a plot that cut the section short cuts the top room with it,
    which is the right direction.

    **A15.1.** This used to be ``_comble_storey_height``, singular, and could
    only ever answer for the lowest band — which was harmless while the 45°
    era's allowance stood exactly one band and no other era's rooms were
    modelled at all, and is the reason a two-storey garret had nowhere to put
    its second storey. Bands above the first stop where the same three limits
    stop them, so a roof standing two bands on a plot that only carries a room
    in the lower one emits one storey and a taller roof over it.

    A band whose clear height is under what a room may legally be ends the
    stack: there is no habitable room above an uninhabitable one, and the roof
    over it is simply roof. That floor is
    ``_the_shortest_room_a_garret_may_hold``, read off the era rather than
    passed in — the same one the count of bands the plot holds is asked with,
    so a band counted as held is a band that gets a room (A16.1).
    """
    if parcel_depth <= 0.0:
        return ()
    brisis, _ridge, _inset = _comble_section(
        envelope, eaves, parcel_depth, extra_garret_storeys
    )
    band = float(BRISIS_RISE)
    if brisis <= 0.0 or band <= 0.0:
        return ()
    habitable = _the_shortest_room_a_garret_may_hold(envelope)
    heights: list[float] = []
    for index in range(_MOST_GARRET_STOREYS):
        if index * band >= brisis - _TOL:
            break
        clear = min(
            _clear_height_of_a_garret_band(
                envelope, parcel_depth, index, band, brisis=brisis
            ),
            storey_maximum,
        )
        if clear < habitable - _ROOF_EPS:
            break
        heights.append(clear)
    return tuple(heights)


def _budget_candidates(
    target: float,
    ceiling: float,
    reserved: float,
    storey_minimum: float,
    storey_maximum: float,
    max_storeys: int,
) -> list[float]:
    """Heights a whole-storey stack can actually fill, nearest the target first.

    The ambition fraction is INFERRED and a section is built of whole
    storeys, so the target is exactly that — a target — and not a figure the
    stack must hit to the millimetre. The old code hit it to the millimetre
    by inventing a short slot to swallow whatever was left over, which is how
    a squeezed half-storey ended up standing for an entresol. Round the
    target instead: with ``n`` typical storeys over the reserved slots the
    facade can be anywhere in ``[reserved + n * minimum, reserved + n *
    maximum]``, so the nearest reachable height is the target clamped into
    whichever of those windows lies closest.

    The LEGAL ceiling caps the list from above — rounding up is an owner
    building a little more than intended, which is ordinary; rounding up past
    the decree is not. Ties go to the taller stack: given two equally close
    answers a builder takes the extra floor.
    """
    seen: dict[int, tuple[float, float, int]] = {}
    for n in range(1, max_storeys + 1):
        low = reserved + n * storey_minimum
        high = reserved + n * storey_maximum
        candidate = min(max(target, low), high)
        if candidate <= 0.0 or candidate > ceiling + _TOL:
            continue
        seen[n] = (abs(target - candidate), candidate, n)
    ordered = sorted(seen.values(), key=lambda t: (t[0], -t[2]))
    return [candidate for _distance, candidate, _n in ordered]


# ---------------------------------------------------------------------------
# Taper — "shorter than the one below" as a relation, not a stored table.
# ---------------------------------------------------------------------------


def _taper_heights(
    n: int,
    total: float,
    minimum: float,
    rate: float = _TAPER_RATE,
    *,
    maximum: float = math.inf,
) -> list[float]:
    """``n`` heights summing exactly to ``total``, every one of them inside
    ``[minimum, maximum]``, each no taller than the one before it (index 0
    is the bottom of the run).

    The bounds are the point, not a courtesy. ``minimum`` is the law — a
    REGULATORY storey height that no INFERRED taper constant may bend — and
    ``maximum`` is the same band this module already declared to the fitting
    solver, so the solver's "no slot outside [minimum, maximum]" guarantee
    survives all the way to what the caller actually reads. A taper that
    quietly steps outside either bound is not a taper, it is a rule being
    overruled by a decoration.

    The shape is a geometric relation (``rate`` per storey going up), not a
    table of per-floor values, and it is fitted to the budget by scaling the
    whole geometric series against the bounds rather than by patching
    individual entries afterwards:

        h_i(lam) = clamp(lam * rate**i, minimum, maximum)

    ``sum(h_i(lam))`` is continuous and non-decreasing in ``lam``, running
    from ``n * minimum`` to ``n * maximum``, so exactly one ``lam`` makes it
    equal ``total`` and a bisection finds it. Because ``rate <= 1`` and
    ``clamp`` is monotone, the result is non-increasing by construction —
    "shorter than the one below" is a property of the formula, not something
    restored by a final sort. Clamping is inside the fitted quantity, so
    nothing is ever redistributed back across a bound.

    A ``total`` outside ``[n * minimum, n * maximum]`` has no answer at all
    and raises: it means the caller declared a band it then failed to fill
    within, which is a bug where it happened rather than a silhouette that
    is 4 mm illegal three phases later. The one thing tolerated there is
    float noise — the solver honours its own bounds to within ``EPS`` per
    slot, so a total may arrive a few nanometres outside the band it was
    built from. That much is absorbed at the band edge: where the two
    cannot both hold, the bound wins and the sum gives up a nanometre,
    never the other way round.
    """
    if n <= 0:
        return []
    if not (0.0 < rate <= 1.0):
        raise ValueError(f"taper rate must be in (0, 1], got {rate}")
    if minimum > maximum:
        raise ValueError(f"taper band is empty: minimum {minimum} > maximum {maximum}")

    noise = _TOL * n  # the solver's per-slot EPS, accumulated over the run
    if n * minimum > total + noise:
        raise ValueError(
            f"cannot fit {n} storeys of at least {minimum:.3f} m each into "
            f"a budget of {total:.3f} m"
        )
    if n * maximum < total - noise:
        raise ValueError(
            f"cannot fit {n} storeys of at most {maximum:.3f} m each into "
            f"a budget of {total:.3f} m"
        )
    total = min(max(total, n * minimum), n * maximum)

    def clamp(x: float) -> float:
        return minimum if x < minimum else (maximum if x > maximum else x)

    if n == 1:
        heights = [total]
    else:
        # lam_lo drives every entry onto the floor (sum n*minimum <= total);
        # lam_hi drives every entry onto the ceiling (sum n*maximum >= total).
        # The bracket is therefore valid before the first bisection step.
        lam_lo = minimum
        tail = rate ** (n - 1)
        lam_hi = max(total, minimum, (maximum / tail) if math.isfinite(maximum) else total)
        for _ in range(100):  # far past float resolution on any real bracket
            lam = 0.5 * (lam_lo + lam_hi)
            if math.fsum(clamp(lam * rate**i) for i in range(n)) < total:
                lam_lo = lam
            else:
                lam_hi = lam
        heights = [clamp(0.5 * (lam_lo + lam_hi) * rate**i) for i in range(n)]

    # Bisection converges to float noise, not to zero. The last few 1e-13 m
    # go onto an entry that has room for them *and* stays in order: upward
    # onto the bottom (already the tallest), downward off the top (already
    # the shortest).
    residual = total - math.fsum(heights)
    if residual > 0.0:
        for i in range(n):
            room = maximum - heights[i]
            if i > 0:
                room = min(room, heights[i - 1] - heights[i])
            take = min(residual, max(room, 0.0))
            heights[i] += take
            residual -= take
            if residual <= 0.0:
                break
    elif residual < 0.0:
        for i in range(n - 1, -1, -1):
            room = heights[i] - minimum
            if i < n - 1:
                room = min(room, heights[i] - heights[i + 1])
            give = min(-residual, max(room, 0.0))
            heights[i] -= give
            residual += give
            if residual >= 0.0:
                break

    # The postconditions this function exists to guarantee, checked on the
    # value actually returned rather than trusted from the arithmetic above —
    # the same discipline the fitting solver applies to its own assembly.
    if abs(math.fsum(heights) - total) > _TOL:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"taper of {n} over {total:.6f} m summed to {math.fsum(heights):.6f} m"
        )
    for i, h in enumerate(heights):  # pragma: no cover - tripwire
        if h < minimum - _TOL or h > maximum + _TOL:
            raise RuntimeError(
                f"taper entry {i} at {h:.6f} m left the band "
                f"[{minimum:.6f}, {maximum:.6f}]"
            )
        if i and h > heights[i - 1] + _TOL:
            raise RuntimeError(
                f"taper entry {i} at {h:.6f} m is taller than the one below it "
                f"({heights[i - 1]:.6f} m)"
            )
    return heights


#: How many passes the entresol/letting-storey settlement below is allowed
#: before it is called divergent. It is a contraction with a ratio around
#: 0.22 — a metre of error is a millimetre after four passes — so this is a
#: terminator on a loop and not a tuning knob.
_ENTRESOL_PASSES = 32

#: The settlement is on a height, so it settles to a height's precision. Well
#: under ``_TOL``, deliberately: what leaves this function has to satisfy the
#: relation to ``_TOL``, so the search has to be finer than the promise.
_ENTRESOL_SETTLE_TOL = 1e-12


def _the_entresol_and_the_storeys_it_serves(
    entresol: float,
    typical_total: float,
    count: int,
    storey_minimum: float,
    storey_maximum: float,
) -> tuple[float, float]:
    """Divide what the fill put over the ground floor between the entresol and
    the letting storeys — ``(entresol, typical total)``, summing to exactly
    what came in.

    Two facts have to hold at once and neither may be applied after the other
    has finished:

    * the entresol is Daly's fraction of the ground storey it caps
      (``_entresol_height``), and never more;
    * it is shorter than the floor it SERVES, by Daly's measured ratio
      (``_COMPRESSED_UNDER_THE_FLOOR_IT_SERVES``) — which is the relation that
      makes "squeezed" mean anything, since Daly's entresols are routinely
      taller than the topmost étages above them (A9.4).

    The second reads the letting storeys, and the letting storeys are whatever
    is left after the first — so the two are one equation, not two rules in
    sequence. It is solved here, by iteration: the taper is monotone in its
    total and the ratio is a division, so the map is a contraction and the
    settlement is unique.

    **A16.2 — and this is why it is a settlement rather than a correction.**
    A9.4 applied the ratio to the finished stack and threw the difference
    away: *"the height given back is not respent; the facade is that much
    shorter"*. On the canonical commercial section that cost 0.41 m of a
    facade that had already been granted it — a height reserved for a storey
    nobody built, which is the same fault as a garret band paid for and never
    received (A16.1), and 0.41 m of the 4.01 m A16.2 measures. The facade now
    fills the budget it was given: the storeys the entresol was squeezed FOR
    stand the height it gave up, which is what "low relative to the floor it
    serves" describes in the first place.

    A9.4's case is untouched and still behaves as A9.4 requires. Where the
    section genuinely cannot afford the storey — an 1783 shopfront under an
    11.70 m ceiling — the letting storeys are already against their own
    bounds, there is nowhere for the height to go, and the facade is simply
    shorter. That is the floor ``lowest`` states below.
    """
    pot = entresol + typical_total
    if count <= 0 or entresol <= 0.0:
        return entresol, typical_total
    # What the letting storeys can take at all: their own band, the same
    # maximum the solver and the taper are held to. Where they are already
    # against it the height the entresol gives up has nowhere to go, and
    # A9.4's answer stands unchanged — the facade is simply that much shorter.
    cap = count * storey_maximum
    settled = entresol
    previous = entresol
    for _pass in range(_ENTRESOL_PASSES):
        heights = _taper_heights(
            count,
            min(pot - settled, cap),
            storey_minimum,
            _TAPER_RATE,
            maximum=storey_maximum,
        )
        served = max(heights) / _COMPRESSED_UNDER_THE_FLOOR_IT_SERVES
        held = min(entresol, served)
        previous, settled = settled, held
        if abs(settled - previous) <= _ENTRESOL_SETTLE_TOL:
            break
    # The iteration alternates about its fixed point, so the lower of the last
    # two is the one that satisfies the relation rather than merely approaching
    # it. They differ by less than a picometre; this is about which side.
    settled = min(settled, previous)
    return settled, min(pot - settled, cap)


# ---------------------------------------------------------------------------
# solve_structure
# ---------------------------------------------------------------------------


def solve_structure(site: SiteContext, datums: BlockDatums | None = None) -> Grid:
    """Build the unnamed grid: envelope, ceiling vs built, storeys and bays.

    If ``datums`` is given, ``street_width`` and ``cornice_height`` are the
    block's handed-down facts (I2) — received, not recomputed. Everything
    else here is a pure function of ``site``; there is no RNG anywhere in
    this phase.
    """
    era = era_for_year(site.year)
    reg = get_reglement(era)
    account: list[str] = [f"era {era.value} ({reg.decree})"]

    # ---- 1. Envelope from regulation -------------------------------------
    if datums is not None:
        # A4.8. `site.street_width` and `datums.street_width` are the same
        # fact stored twice, and until this check existed the preference for
        # the datum was silent: hand in a site that disagreed with its block
        # and the building was built to the block's street and traced to the
        # site's, with nothing anywhere saying so. That is a second source of
        # truth, which is the class of bug this project exists to remove.
        #
        # They may not legitimately differ. A street has one width; the block
        # resolves it and hands it down (I2), and `SiteContext` carries it
        # only so a building generated without a block has somewhere to read
        # it from. `block._hand_down` already builds every `SiteContext` from
        # `block.datums.street_width`, so an honest caller cannot trip this —
        # which is exactly why it is worth asserting rather than tolerating.
        if abs(site.street_width - float(datums.street_width)) > _DATUM_TOLERANCE:
            raise ValueError(
                "site.street_width and datums.street_width are the same fact "
                f"stored twice and they disagree: {site.street_width!r} vs "
                f"{float(datums.street_width)!r}. One street, one width — the "
                "block resolves it and the building receives it (I2), so a "
                "SiteContext handed alongside datums must already carry the "
                "value the block resolved."
            )
        street_width = float(datums.street_width)
        ceiling_value = float(datums.cornice_height)
        ceiling_citation = f"{reg.decree} — received from block datum, not recomputed (I2)"
        account.append(
            f"datums received from block: street_width {street_width:.2f} m, "
            f"cornice_height {ceiling_value:.2f} m"
        )
    else:
        street_width = site.street_width
        ceiling_value = reg.facade_height_limit(street_width)
        ceiling_citation = reg.decree

    account.append(
        f"street width {street_width:.2f} m -> legal cornice ceiling "
        f"{ceiling_value:.2f} m ({ceiling_citation})"
    )

    # A8.5. ``roof_fill`` is 1.0 — the ONE meaning of ``GabaritEnvelope`` is
    # the legal solid, and a builder's fraction has no business inside it. How
    # much of that solid this building's roof occupies is decided further down,
    # by ``_comble_section``, out of the rooms the comble is for; the envelope
    # states only what the decree permits. While a fraction lived here,
    # ``envelope.ridge_height`` was neither the law nor the building and
    # ``legal_total_height`` on the IR was 1 % short of the legal total.
    envelope = compute_envelope(
        street_width, era, site.parcel_depth, roof_fill=1.0, max_ridge=None
    )
    if datums is not None and abs(envelope.facade_height - ceiling_value) > 1e-9:
        # The datum is the fact of record; the recomputed roof geometry
        # around it must agree with it exactly, not merely approximately.
        envelope = dataclasses.replace(envelope, facade_height=ceiling_value)
    account.append(
        f"roof envelope {envelope.roof_envelope.value}: ridge {envelope.ridge_height:.2f} m "
        f"above the cornice (legal max {envelope.legal_ridge_height:.2f} m)"
    )

    # ---- 1b. How many storeys of chambres de bonne the roof holds (A15.1) -
    #
    # Taken here, from the envelope, the parcel and the ground programme,
    # before a metre of either budget is filled — for the same reason the
    # entresol is (nothing about how a budget happens to divide may conjure a
    # storey up or take one away), and with the same shape of answer: a
    # decision plus the sentence that justifies it.
    #
    # It is taken BEFORE the facade ambition because it changes what the
    # ambition is a fraction OF. A band of garret above the number the decree's
    # own allowance stands is bought out of the cornice: the legal solid does
    # not move, so the stone gives up exactly the height the zinc takes and the
    # building keeps the same gabarit with its accommodation redistributed.
    # That is the trade Daly's tall-comble buildings show — 6.80 m and 7.00 m
    # of comble over cornices at 17.55 m, against 2.7-3.3 m over cornices at
    # 19.5-20.0 m on the same boulevard.
    extra_garret_storeys, garret_why = _a_second_storey_of_chambres_de_bonne(
        envelope, site.ground, ceiling_value, site.parcel_depth
    )
    account.append(f"garret storeys: {garret_why}")
    facade_ceiling = max(
        0.0, ceiling_value - _facade_given_up_for_a_bought_garret(extra_garret_storeys)
    )

    fraction = _FACADE_AMBITION[site.klass]
    target_value = facade_ceiling * fraction
    account.append(
        f"class {site.klass.value}: facade ambition {fraction:.2f} (INFERRED, only the "
        f"ordering is contractual) -> facade target {target_value:.2f} m "
        f"({target_value / facade_ceiling:.0%} of the "
        f"{facade_ceiling:.2f} m the stone face may fill)"
    )

    cornice_height = Reg(ceiling_value, ceiling_citation)

    # ---- 2a. The entrance: one per building, decided before anything fills-
    #
    # A6.1. Every Paris immeuble has an entrance, so this is unconditional —
    # it used to be reachable only through ``GroundProgramme.CARRIAGE``, which
    # left every shop and residential frontage in the city sealed. Which of
    # the two doors it is comes from ``catalogue.entrance_for``, out of the
    # class and the street width, never from a literal in this file.
    #
    # Decided HERE, before either budget is filled, for the same reason the
    # entresol is: the entrance constrains both axes at once — a floor under
    # the ground storey's height and a fixed slot in the bay run — and a
    # decision taken after a budget has been divided is a decision the
    # remainder took.
    entrance = catalogue.entrance_for(site.klass, street_width, site.ground)
    account.append(f"entrance: {entrance.why}")

    # ---- 3a. Storeys into the height budget ------------------------------
    ground_q = _ground_height_quantity(site.ground, site.klass, entrance)
    ground_value = float(ground_q)
    ground_spec = SlotSpec(
        "ground", SlotKind.FIXED, ground_value, ground_value, ground_value, rigid=ground_q.rigid
    )
    account.append(
        f"ground floor ({site.ground.value}): {ground_value:.2f} m ({ground_q.why})"
    )

    storey_min_q, storey_pref_q, storey_max_q = _typical_storey_band(reg, site.klass)
    storey_min = float(storey_min_q)
    storey_pref = float(storey_pref_q)
    storey_max = float(storey_max_q)
    storey_spec = SlotSpec("storey", SlotKind.REPEATING, storey_min, storey_pref, storey_max)
    account.append(f"storey minimum {storey_min:.2f} m ({storey_min_q.why})")
    account.append(
        f"typical storey band [{storey_min:.2f}, {storey_pref:.2f}, {storey_max:.2f}] m: a plain "
        f"storey of {float(_PLAIN_STOREY_HEIGHT):.2f} m ({_PLAIN_STOREY_HEIGHT.why}) plus the "
        f"margin ambition buys above it — class {site.klass.value} scales the MARGIN only, never "
        "the plain storey inside it"
    )

    # ---- 2. The entresol: a programme decision, taken before the fill -----
    #
    # Decided here, from the ground-floor use and the class, with the height
    # budget known but untouched. When it is wanted it goes to the solver as
    # a FIXED element of the vertical run — reserved before a single storey
    # is placed, so the solver has to accommodate it rather than discover it.
    #
    # Its position needs no separate rule. An entresol is BY DEFINITION the
    # storey immediately over the ground floor — that is what the word means,
    # and it is why its height is stated as a fraction of the storey below it
    # (A9.4) — and a fixed slot sharing the ground floor's index hint is
    # placed exactly there, so the justification and the geometry are the same
    # fact instead of two facts that have to be reconciled afterwards.
    entresol_q = _entresol_height(ground_value)
    entresol_value = float(entresol_q)
    wants_entresol, entresol_why = _wants_an_entresol(
        site.ground,
        site.klass,
        budget=target_value,
        ground_height=ground_value,
        entresol_height=entresol_value,
        storey_preferred=storey_pref,
    )
    account.append(f"entresol: {entresol_why}")

    fixed_storeys: list[tuple[int, SlotSpec]] = [(0, ground_spec)]
    if wants_entresol:
        fixed_storeys.append(
            (
                0,
                SlotSpec(
                    "entresol",
                    SlotKind.FIXED,
                    entresol_value,
                    entresol_value,
                    entresol_value,
                    rigid=entresol_q.rigid,
                ),
            )
        )
        account.append(
            f"entresol height {entresol_value:.2f} m ({entresol_q.why}) — reserved as a "
            "fixed element of the vertical run, immediately over the ground floor"
        )

    # A zero-width placeholder: the shared solver always brackets its run
    # with two "end" slots, and the vertical axis has no equivalent to the
    # horizontal pier at the edge of a facade. Rigid, so it never absorbs
    # slack, and filtered back out below so it never reaches the Grid.
    _edge = SlotSpec("_edge", SlotKind.FIXED, 0.0, 0.0, 0.0, rigid=True)

    # No ``special`` is offered on this axis, deliberately. A narrow special
    # is the solver's way of closing a budget whole modules cannot close, and
    # vertically the only thing it can be is a squeezed half-storey standing
    # over the ground floor — i.e. an entresol produced by arithmetic rather
    # than by programme, appearing wherever the class factor happened to
    # leave an awkward remainder. The remainder is answered where it belongs
    # instead: the facade target is INFERRED and a section is built of whole
    # storeys, so the target is rounded to the nearest height a whole-storey
    # stack can fill (see ``_budget_candidates``), and nothing is invented to
    # swallow the difference.
    reserved = math.fsum(spec.preferred for _, spec in fixed_storeys)
    max_storeys = 12
    candidates = _budget_candidates(
        target_value, facade_ceiling, reserved, storey_min, storey_max, max_storeys
    )
    if not candidates and extra_garret_storeys > 0:
        # The trade is refused by the section rather than by the predicate: a
        # facade that cannot stand a single whole storey over its fixed slots
        # once the garret has been paid for does not buy the garret. Nothing
        # is degraded quietly — the account says so, and the roof is then the
        # one the decree's own allowance stands.
        account.append(
            f"garret storeys: the {facade_ceiling:.2f} m left after buying a second "
            f"storey of chambres de bonne cannot stand {reserved:.2f} m of fixed "
            f"slot(s) and a whole storey over them, so the trade is off and the roof "
            f"is the {envelope.ridge_height:.2f} m the decree's own allowance stands"
        )
        extra_garret_storeys = 0
        facade_ceiling = ceiling_value
        target_value = facade_ceiling * fraction
        candidates = _budget_candidates(
            target_value, facade_ceiling, reserved, storey_min, storey_max, max_storeys
        )
    storey_result = None
    last_error: FitInfeasible | None = None
    for candidate in candidates:
        try:
            storey_result = solve(
                candidate,
                end=_edge,
                bay=storey_spec,
                special=None,
                fixed=tuple(fixed_storeys),
                central_feature=False,
                min_bays=1,
                max_bays=max_storeys,
            )
        except FitInfeasible as exc:  # try the next reachable height
            last_error = exc
            continue
        built_value = candidate
        break
    if storey_result is None:
        # Every reachable height was refused, so the situation genuinely has
        # no section — say so, rather than degrading quietly.
        if last_error is not None:
            raise last_error
        raise FitInfeasible(
            f"a {ceiling_value:.2f} m legal ceiling leaves no room for "
            f"{reserved:.2f} m of fixed slot(s) and a single storey of at least "
            f"{storey_min:.2f} m over them"
        )
    account.append(
        f"facade target {target_value:.2f} m rounded to {built_value:.2f} m — the height a "
        f"whole-storey stack can actually fill over {reserved:.2f} m of fixed slot(s), "
        f"capped by the {ceiling_value:.2f} m legal ceiling. The fraction is a target, "
        "not a quota, and a section is built of whole storeys"
    )
    account.extend(f"[vertical] {line}" for line in storey_result.account)

    raw_storeys = [s for s in storey_result.slots if s.name != "_edge"]
    typical = [s for s in raw_storeys if s.name == storey_spec.name]

    # The taper reshapes only the uniform typical-storey band, inside the
    # very band this module declared to the solver — so the solver's
    # "no slot outside [minimum, maximum]" guarantee still holds of what the
    # caller reads, and the REGULATORY minimum narrated two lines above
    # cannot be bent by an INFERRED constant. The fixed slots — the ground
    # floor, and the entresol where the programme asked for one — are already
    # their own size and are not tapered a second time.
    total_typical = math.fsum(s.width for s in typical)

    # A squeezed storey is squeezed RELATIVE TO SOMETHING, and A9.4 is where
    # that stopped being implicit. Its height is Daly's measured fraction of
    # the ground storey it stands on (``_entresol_height``), which is right
    # for a section with room in it — and wrong for one without. A 1783 shop
    # front under an 11.70 m facade ceiling gets the same 3.95 m rez-de-
    # chaussée and the same 0.775 of it, and the letting storeys left over it
    # come out at 2.37 m: the squeezed storey ends up the TALLEST floor in
    # the building, which is not a low storey over a shop, it is a piano
    # nobile with a shop under it.
    #
    # The ratio Daly measured for it — the noble floor is 1.25× this storey in
    # Première Classe and 1.30× in Deuxième — is therefore enforced against
    # the letting storeys and not against a table. But the letting storeys are
    # what is left after the entresol, so the two are one equation and are
    # settled as one (**A16.2**): the height the entresol gives up goes to the
    # storeys it was squeezed FOR, and the facade fills the budget it was
    # granted instead of coming out 0.41 m short of it with nobody the taller.
    # Nothing about the DECISION moves — whether the building has an entresol
    # at all was settled from the programme before a metre was filled.
    entresol_placed = math.fsum(s.width for s in raw_storeys if s.name == "entresol")
    entresol_built, total_typical = _the_entresol_and_the_storeys_it_serves(
        entresol_placed, total_typical, len(typical), storey_min, storey_max
    )
    tapered = _taper_heights(
        len(typical), total_typical, storey_min, _TAPER_RATE, maximum=storey_max
    )
    account.append(
        f"taper: {len(typical)} typical storey(s) at rate {_TAPER_RATE} (INFERRED), "
        f"held inside [{storey_min:.2f}, {storey_max:.2f}] m -> "
        f"{[round(h, 3) for h in tapered]} m, bottom to top"
    )
    if entresol_placed - entresol_built > _TOL:
        account.append(
            f"squeezed storey held down to {entresol_built:.2f} m: Daly's fraction of "
            f"the {ground_value:.2f} m ground storey is {entresol_placed:.2f} m, which "
            f"is not short of the {max(tapered):.2f} m letting storeys this section "
            f"stands over it — a low storey over a shop is low relative to the "
            f"floor it serves, and Daly measures that floor at "
            f"{_COMPRESSED_UNDER_THE_FLOOR_IT_SERVES:.3f}× it (1.25 in Première "
            f"Classe, 1.30 in Deuxième). The {entresol_placed - entresol_built:.2f} m "
            "it gives up stands in the letting storeys over it, which is the floor the "
            "relation is about (A16.2): the facade was granted this budget and fills "
            "it, and the only height a facade loses is height nobody could use"
        )

    tapered_iter = iter(tapered)
    resolved: list[tuple[PlacedSlot, float]] = []
    for slot in raw_storeys:
        if slot.name == storey_spec.name:
            width = next(tapered_iter)
        elif slot.name == "entresol":
            width = entresol_built
        else:
            width = slot.width
        resolved.append((slot, width))

    final_slots: list[PlacedSlot] = []
    cursor = 0.0
    for slot, width in resolved:
        final_slots.append(
            PlacedSlot(
                name=slot.name, kind=slot.kind, start=cursor, width=width, is_special=slot.is_special
            )
        )
        cursor += width

    # ---- 3a-bis. The storeys standing inside the comble ------------------
    #
    # The stone face stops here, and the roof begins. A Paris comble is not
    # empty volume: the *chambres de bonne* are in it, and the lucarnes the
    # termination phase puts on the slope are their windows. So for every band
    # of brisis with the clear height and the floor depth for a room, the
    # stack gets one more slot — an ordinary slot, unnamed and unflagged like
    # every other, distinguished only by standing above ``eaves_height``.
    # Where the roof has not, nothing is emitted and the comble is just a
    # comble.
    #
    # **A15.1**: one slot per BAND, where this used to emit at most one slot
    # however many bands of rooms the brisis stood. The lucarnes have always
    # been drawn one row per band (A8.3) — so a two-band comble had two rows
    # of windows and one room behind them, and the second row's trace had to
    # say in as many words that it lit "a band of the comble S3 has not yet
    # divided into a storey of its own". It does now.
    #
    # They are deliberately outside the facade budget and outside the taper:
    # their height is not bought with ambition, it is whatever the envelope
    # and the parcel left over the eaves.
    eaves_height = cursor
    headroom = max(0.0, envelope.facade_height - eaves_height)
    comble_ceiling = _comble_ceiling_over_the_eaves(
        envelope, eaves_height, site.parcel_depth
    )
    brisis_over_eaves, comble_over_eaves, _ridge_inset = _comble_section(
        envelope, eaves_height, site.parcel_depth, extra_garret_storeys
    )
    account.append(
        f"comble CEILING {comble_ceiling:.2f} m over the {eaves_height:.2f} m eaves it "
        f"springs from — the égout du toit, where the decree springs it, not the legal "
        f"cornice: the gabarit's top is {envelope.total_height:.2f} m above the "
        f"pavement ({envelope.facade_height:.2f} m legal cornice + {envelope.ridge_height:.2f} m "
        f"comble), and the {headroom:.2f} m of cornice height this facade declined to build "
        f"is legal height the roof still has over it — not height the roof forfeited with "
        f"it. The same curve is simply traced to a taller top, which costs "
        f"{envelope.setback_at(comble_ceiling):.2f} m of inset against the "
        f"{envelope.setback_at(envelope.ridge_height):.2f} m a comble sprung from the "
        f"cornice would need, and the parcel is what says whether that is affordable"
    )
    bought = (
        f" plus the {extra_garret_storeys} band(s) of chambres de bonne this building "
        f"bought out of its cornice (A15.1)"
        if extra_garret_storeys
        else ""
    )
    account.append(
        f"comble BUILT {comble_over_eaves:.2f} m — sized by the garret storeys it holds, "
        f"inside the decree's own {envelope.ridge_height:.2f} m allowance sprung from these "
        f"eaves{bought}, and not up to the "
        f"{comble_ceiling:.2f} m ceiling over them. A8.5: building "
        f"to the ceiling made the roof grow by exactly what the facade declined, so the sum "
        f"never moved and every building in the city reached its legal total. Nothing here "
        f"reads the class — a comble is floor, not show — so the "
        f"{comble_ceiling - comble_over_eaves:.2f} m left under the ceiling is legal volume "
        f"nobody had a use for"
    )
    account.append(
        f"the plot: a {site.parcel_depth:.2f} m parcel stands "
        f"{_garret_storeys_the_parcel_holds(envelope, site.parcel_depth)} whole band(s) "
        f"of brisis with a room behind them — a room needs "
        f"{float(_COMBLE_ROOM_DEPTH):.2f} m of floor between the two opposing slopes "
        f"under {float(_HUMAN_MIN_STOREY_HEIGHT):.2f} m of standing height, and on a "
        f"shallow plot the slopes meet before the next band has it. This is what the "
        f"cornice may not read (A15.1): the cornice runs across the party wall and "
        f"parcel depths do not, so the plot limits what gets BUILT and never what was "
        f"given up for it"
    )
    account.append(
        f"comble section: a brisis of {brisis_over_eaves:.2f} m — "
        f"{brisis_over_eaves / float(BRISIS_RISE):.0f} × {float(BRISIS_RISE):.2f} m "
        f"({BRISIS_RISE.why}) — standing on the gabarit, then a terrasson at "
        f"{_TERRASSON_PITCH_DEG:.0f}° closing the remaining "
        f"{comble_over_eaves - brisis_over_eaves:.2f} m over the "
        f"{max(0.0, site.parcel_depth / 2.0 - envelope.setback_at(brisis_over_eaves)):.2f} m "
        f"back to the middle of the plot. The fold is what makes it a comble BRISÉ (A8.3)"
    )
    comble_clears = _comble_storey_heights(
        envelope,
        eaves_height,
        site.parcel_depth,
        storey_max,
        extra_garret_storeys,
    )
    if comble_clears:
        band_foot = eaves_height
        for band_index, comble_clear in enumerate(comble_clears):
            final_slots.append(
                PlacedSlot(
                    name="comble",
                    kind=SlotKind.FLEXIBLE,
                    start=band_foot,
                    width=comble_clear,
                    is_special=False,
                )
            )
            account.append(
                f"comble holds a storey ({band_index + 1} of {len(comble_clears)}): "
                f"{comble_clear:.2f} m clear, its floor at {band_foot:.2f} m, behind "
                f"band {band_index + 1} of a {brisis_over_eaves:.2f} m brisis, inside a "
                f"{comble_over_eaves:.2f} m roof, with "
                f"{site.parcel_depth - 2.0 * envelope.setback_at((band_index + 1) * float(BRISIS_RISE) - float(_BRISIS_PLATE)):.2f} m "
                f"of floor between the slopes at its ceiling (a room needs "
                f"{float(_COMBLE_ROOM_DEPTH):.2f} m — {_COMBLE_ROOM_DEPTH.why})"
            )
            band_foot += comble_clear
    else:
        account.append(
            f"comble holds no storey: a {comble_over_eaves:.2f} m roof over a "
            f"{site.parcel_depth:.2f} m parcel leaves nowhere with the "
            f"{max(float(_HUMAN_MIN_STOREY_HEIGHT), storey_min):.2f} m of clear height a "
            f"room may legally have ({_HUMAN_MIN_STOREY_HEIGHT.why}, and the era's own "
            f"hygiene minimum where it is higher) over "
            f"{float(_COMBLE_ROOM_DEPTH):.2f} m of floor"
        )
    storeys = tuple(final_slots)

    # ---- 3b. Bays into the parcel width — solved ONCE per building -------
    #
    # **A9.1: the edge pier is ABSOLUTE, for exactly the reason A8.6 gave for
    # the bay pitch.** It was ``_scaled_bounds(0.20, 0.35, 0.75)``, wholly
    # PROPORTIONAL, so a grand facade started from a 0.47 m edge pier and a
    # modest one from 0.30 m. What that bought was not a grander margin — the
    # ends are the most elastic module here and get resized by the solver
    # anyway — it was a whole window: the natural bay count is a FLOOR of
    # ``(frontage - 2 * end.preferred) / bay.preferred``, so 0.35 m of extra
    # edge pier, spread over two ends, could take an entire axis off the
    # frontage. Measured over 36 situations it did exactly that on a 20 m
    # parcel on a narrow street, where no class has a carriage entrance and
    # the edge pier was the only thing separating them: 7 axes for a modest
    # building and 6 for a grand one, which is D6 wearing a different hat.
    #
    # What stands at the edge of a facade is the pier carrying the corner of
    # the building and abutting the party wall — masonry, and the same
    # masonry whoever paid for it. What ambition buys there is the ornament
    # ON it, which is `qualify`'s business and is PROPORTIONAL there. So the
    # three bounds are ABSOLUTE and identical for every class, and the values
    # are unchanged from what ORDINARY used to resolve to.
    end_lo = float(Abs(0.20, "the narrowest edge pier that still reads as carrying the corner"))
    end_pref = float(
        Abs(0.35, "INFERRED — the edge pier a Paris frontage rests at when nothing forces it off")
    )
    end_hi = float(Abs(0.75, "as wide as an edge pier may get before it reads as its own bay"))
    end_spec = SlotSpec("pier_end", SlotKind.FLEXIBLE, end_lo, end_pref, end_hi, elasticity=2.0)

    bay_lo, bay_pref, bay_hi = _bay_pitch_band(site.klass)

    # **A26 — the SOFT window/bay ratio, and the only way it is allowed to
    # act.** ``_WINDOW_BAY_RATIO`` says an opening wants to be 0.45 of the bay
    # carrying it. The opening's own width is ABSOLUTE and comes from the
    # catalogue, so the ratio is a statement about the BAY: the bay that would
    # satisfy it is ``window / ratio``. That figure is handed to the solver as
    # the bay's ``affinity`` — a lean the solver consults only to separate two
    # bay counts that sit equally far from the preferred pitch, never a bound
    # and never a reason to refuse a frontage.
    #
    # It is emphatically not the preferred pitch, and the two disagree on
    # purpose: at the operator's own figures the lean asks for 2.889 m and the
    # preferred pitch is 2.60 m. The preferred pitch wins every time the two
    # are in contention, which is what "soft" means here (see
    # ``_WINDOW_BAY_RATIO`` for why all three figures cannot hold at once).
    _window_pref = float(catalogue.opening_window().preferred)
    _ratio = float(_WINDOW_BAY_RATIO)
    bay_affinity = _window_pref / _ratio if _ratio > _TOL else None
    bay_spec = SlotSpec(
        "bay", SlotKind.REPEATING, bay_lo, bay_pref, bay_hi, affinity=bay_affinity
    )
    account.append(
        f"bay pitch {bay_pref:.2f} m, held in [{bay_lo:.2f}, {bay_hi:.2f}] m, leaning "
        f"toward {bay_affinity:.2f} m where nothing else decides — the width at which "
        f"a {_window_pref:.2f} m opening is {_ratio:.2f} of its bay ("
        f"{_WINDOW_BAY_RATIO.why}). At the preferred pitch the ratio lands at "
        f"{_window_pref / bay_pref:.3f}, and the pitch outranks the ratio — "
        f"{_BAY_PITCH_MIN.why} / {_BAY_PITCH_MAX.why}. The rhythm is what the masonry "
        f"spans, so it is very nearly the same on every frontage in Paris; a "
        f"{site.klass.value} builder moves it by "
        f"{abs(bay_pref - (float(_BAY_PITCH_MIN) + float(_BAY_PITCH_MAX)) / 2.0):.2f} m "
        f"and buys the rest of what the money shows in the OPENING inside the bay, in "
        f"storey height and in ornament (A8.6)"
    )

    # ABSOLUTE, for the same reason the bay pitch is (A8.6) and discovered by
    # the same change. A narrow special is a strip of wall with one light in
    # it: how narrow it may be is ``minimum_light_width`` and two piers, how
    # wide it may be is "still narrower than a bay", and neither of those is
    # something an owner buys. While it scaled with the class, a MODEST
    # facade's only absorber shrank by 15 % against a bay minimum that no
    # longer shrank with it, and the two bands stopped overlapping: a 6.50 m
    # frontage with a porte cochère on it had a leftover too wide for two thin
    # piers and this special, and too narrow for a whole bay. The solver could
    # only answer that honestly by refusing a facade Paris is full of.
    #
    # The maximum is what closes that hole, and it is chosen to close it with
    # room to spare rather than to fit: the reachable widths must be
    # CONTINUOUS from a bare pair of piers upward, or some frontage somewhere
    # has no facade. It is deliberately not closed by making the END piers
    # more elastic instead — measured, that let a 7.62 m corner parcel absorb
    # its whole remainder into two one-metre piers and drop its last bay,
    # which is a blanker wall than the problem.
    special_lo = float(
        Abs(1.10, "the narrowest strip that carries a light and a pier either side")
    )
    special_pref = float(Abs(1.35, "INFERRED — a comfortable half-bay of wall"))
    special_hi = float(
        Abs(1.80, "as wide as a leftover may be before it should have been a bay")
    )
    special_spec = SlotSpec("special", SlotKind.FLEXIBLE, special_lo, special_pref, special_hi)

    # ---- 3c. The entrance — one per building, always, placed by rule ------
    #
    # A6.1: the worst defect this system ever had was that a whole block of
    # ten immeubles offered 108 windows, 27 shopfronts and no way into any of
    # them. The entrance used to be conditional on ``GroundProgramme.CARRIAGE``
    # — the one programme that names a door — so every shop, café, office and
    # residential frontage in Paris came out sealed.
    #
    # It is unconditional now. Which of the two doors it is comes from
    # ``catalogue.entrance_for`` (class and street width, with the programme
    # able to name it outright), never from a literal here; how much frontage
    # it takes is ABSOLUTE and comes from the catalogue too; and WHERE it
    # stands is ``_entrance_index_hint``'s positional rule. ``entrance``
    # itself was resolved in 2a, before either budget was filled.
    entrance_q = _entrance_slot_width_quantity(entrance)
    entrance_w = float(entrance_q)

    # **A27 — an entrance is an opening in an ordinary bay, like a window is.**
    #
    # ``entrance_w`` is the clear width the body or the vehicle needs plus the
    # jamb its head lands on either side. That is a *structural minimum* — the
    # narrowest this slot may be — and it used to be handed to the solver as
    # the slot's width, full stop: FIXED, rigid, exactly ``entrance_w`` and not
    # a millimetre more. Which made the entrance the one rigid element in an
    # elastic run, and produced the thing backwards: on a 14.40 m frontage the
    # bays came out at 2.638 m and the door slot at 2.350 m, so the masonry
    # between the door and its neighbour was 0.969 m against 1.338 m between
    # two windows. The wall carrying the biggest hole in the facade, at the
    # storey where the whole building's load arrives, was the THINNEST wall on
    # the frontage. Nobody chose that; it is what a rigid slot sitting in an
    # elastic run does.
    #
    # So the entrance is offered to the solver as a member of the repeating
    # pool: a bay like any other, standing at a named place, carrying a wider
    # opening. It takes the frontage's own pitch, and the masonry beside it
    # then differs from the masonry between two windows by exactly what the two
    # OPENINGS differ by — which is a real difference and the right one, since
    # a 1.75 m hole in a 2.60 m bay does leave less wall than a 1.30 m one.
    #
    # ``entrance_w`` keeps its whole meaning as the slot's ``minimum``. Where
    # the frontage's pitch is under it — a carriage arch is 3.04 m and the
    # pitch is 2.60 m, so this is the porte cochère's ordinary case — the
    # solver refuses, and the fallback below gives the entrance a module of its
    # own at exactly the width it always had. **The exception is conditioned on
    # WIDTH, not on being a door**, which is what the D6 guard's own words ask
    # for: "a fixed slot WIDER than a bay is carried up every storey and costs
    # the building a window on every floor". A door narrower than a bay has no
    # such problem and should not pay that price.
    #
    # The maximum is the bay's own: above the pavement this column is an
    # ordinary window column, so whatever ceiling the rhythm has is its ceiling
    # too. ``max()`` guards both bounds against a band that does not bracket
    # the door, which the two tripwires below refuse outright anyway.
    entrance_in_rhythm = SlotSpec(
        entrance.kind,
        SlotKind.REPEATING,
        entrance_w,
        max(bay_pref, entrance_w),
        max(bay_hi, entrance_w),
    )
    entrance_own_bay = SlotSpec(
        entrance.kind, SlotKind.FIXED, entrance_w, entrance_w, entrance_w, rigid=True
    )

    # **D6, asserted (A9.2).** The entrance slot stands in the bay run for the
    # full height of the facade, so a slot wider than a bay may be is a bay the
    # building does not get — paid for by the classes that have a carriage
    # entrance, which is to say by the grand ones. It was 3.80 m against a
    # 3.40 m maximum and cost exactly that: 4 openings on a 16 m frontage where
    # a modest building got 5.
    #
    # A27 sharpened what this guard is *for* without weakening it. It is the
    # ceiling on the FALLBACK — on the entrance that takes a module of its own
    # because the rhythm will not hold it — and that is precisely the case D6
    # was always about, since an entrance inside the rhythm is by construction
    # no wider than a bay and can cost nothing. So this now bounds exactly the
    # arrangement it describes, and the arithmetic it checks is unchanged.
    #
    # The relation this asserts is that the widest entrance this typology can
    # place still fits inside the band the masonry states, so the column over
    # the door is an ordinary bay at every storey above the pavement rather
    # than a permanent scar the width of a carriage. It is a postcondition of
    # two modules agreeing, which is why it is checked instead of trusted:
    # ``catalogue`` owns the door and its jambs, ``structure`` owns the band,
    # and neither can see the other's arithmetic.
    if entrance_w > float(_BAY_PITCH_MAX) + _TOL:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"the {entrance.kind} takes {entrance_w:.3f} m of frontage, wider than the "
            f"{float(_BAY_PITCH_MAX):.3f} m this module states a bay may be "
            f"({_BAY_PITCH_MAX.why}). A fixed slot wider than a bay is carried up every "
            "storey and costs the building a window on every floor — the D6 defect. "
            "Narrow the door or the jambs in `catalogue`, or widen the band here; do "
            "not let the two disagree"
        )

    # **A10.1 — and the other side of the entrance, against the bound that is
    # actually its own.** The check above had no partner below it, so a stated
    # ABSOLUTE band was enforced on one side and silently crossed on the other:
    # the porte piétonne's 2.35 m slot sits 0.35 m under ``_BAY_PITCH_MIN``.
    #
    # The resolution is not to widen the door. It is that ``_BAY_PITCH_MIN``
    # is a floor under the REPEATING bay — under a *rhythm* — and the entrance
    # is a one-off standing in that rhythm rather than a member of it. The
    # constant now says so, and the floor is enforced over the bays themselves
    # after the solve.
    #
    # What genuinely bounds the entrance below is what its COLUMN has to do.
    # The slot is carried the full height of the facade, and above the
    # pavement it is an ordinary window column like any other — so the
    # narrowest it may be is the narrowest strip this module already states
    # will carry a light with a pier either side. That is ``special_lo``,
    # stated once just above and read from here rather than restated as a
    # twelfth number that could drift from it. Under that width the entrance
    # column goes blank on every storey and the frontage carries a
    # full-height blind stripe through its middle — the sideways twin of the
    # defect the maximum above exists to catch.
    if entrance_w < special_lo - _TOL:
        raise RuntimeError(
            f"the {entrance.kind} takes only {entrance_w:.3f} m of frontage, narrower "
            f"than the {special_lo:.3f} m this module states is the narrowest strip "
            "that carries a light and a pier either side. The entrance slot is carried "
            "the full height of the facade and above the pavement it is an ordinary "
            "window column, so a slot under this width is a blind stripe running the "
            "whole facade. Widen the door or the jambs in `catalogue`. Note this is "
            f"NOT {float(_BAY_PITCH_MIN):.2f} m: that floor is under the REPEATING bay, "
            "and an entrance is a one-off standing in the rhythm rather than a member "
            "of it (A10.1)"
        )

    # The entrance is ABSOLUTE: it cannot be narrowed to fit the parcel, so a
    # parcel narrower than the entrance plus its two thinnest piers has no
    # facade at all. Said here, in the vocabulary of the thing that is
    # impossible, rather than as a solver refusal listing bounds.
    narrowest = entrance_w + 2.0 * end_lo
    if site.parcel_width < narrowest - _TOL:
        raise FitInfeasible(
            f"a parcel {site.parcel_width:.2f} m wide cannot carry a "
            f"{entrance_w:.2f} m {entrance.kind} ({entrance_q.why}): every building "
            f"has an entrance, the entrance is absolute, and the two piers beside it "
            f"are already at their minimum {end_lo:.2f} m, so the frontage needs at "
            f"least {narrowest:.2f} m"
        )

    # How few *bays* this facade may consist of. Zero: a rigid fixed element
    # IS an element of the run, and on a narrow parcel the entrance plus its
    # two piers is very nearly the whole frontage — demanding a full bay
    # beside it as well is demanding a facade the parcel cannot hold, and the
    # solver can only answer that honestly by refusing. Paris is full of 6-7 m
    # parcels whose ground floor is the porte cochère and nothing else.
    min_bays = 0

    # The index hint is the number of bays standing left of the entrance, so
    # it depends on how many bays the solver ends up placing — which depends
    # on the width the entrance reserved, not on where it went. So: solve,
    # read the bay count back, and re-solve with the hint that count implies.
    # It converges on the second pass by construction (moving a fixed slot
    # within a run changes no width), and the loop is bounded and
    # deterministic. The alternative — the estimate this used to carry, with
    # "approximate centring" written in the account — is precisely the "left
    # to chance" A6.1 refuses.
    avail = max(site.parcel_width - 2.0 * end_pref - entrance_w, 0.0)
    n_bays_guess = max(1, round(avail / bay_pref)) if bay_pref > 0.0 else 1
    bay_result = None
    placement_why = ""
    entrance_in_the_rhythm = True
    for _ in range(4):
        hint, placement_why = _entrance_index_hint(n_bays_guess)
        # In rhythm first, and a module of its own only where that is refused.
        # The order is the rule: an entrance is an opening in an ordinary bay
        # UNLESS it is too wide to fit one. Both calls are the same solve with
        # the same hint and the same bands — only the entrance's declared kind
        # differs — so the frontage that ends up in the second branch is
        # exactly the frontage whose pitch cannot hold the door, and it solves
        # there precisely as it always did.
        for spec, in_rhythm in ((entrance_in_rhythm, True), (entrance_own_bay, False)):
            try:
                bay_result = solve(
                    site.parcel_width,
                    end=end_spec,
                    bay=bay_spec,
                    special=special_spec,
                    fixed=((hint, spec),),
                    central_feature=False,
                    min_bays=min_bays,
                    max_bays=40,
                )
            except FitInfeasible:
                if in_rhythm:
                    continue  # the pitch cannot hold the door: give it its own bay
                raise
            entrance_in_the_rhythm = in_rhythm
            break
        assert bay_result is not None
        n_bays_solved = sum(1 for s in bay_result.slots if s.name == "bay")
        if n_bays_solved == n_bays_guess:
            break
        n_bays_guess = n_bays_solved
    assert bay_result is not None  # the loop body runs at least once
    account.append(
        f"{entrance.kind}: {entrance_w:.2f} m of frontage — the clear opening plus the "
        f"jamb its head lands on either side ({entrance_q.why}). {placement_why}"
    )
    # A27, in the account because it is the one thing about this frontage a
    # reader will want explained: whether the door is in step with the windows
    # or standing in a bay of its own, and which of the two it is is a fact
    # about the door's width against this frontage's pitch, nothing else.
    _door_slot = next(s for s in bay_result.slots if s.name in catalogue.ENTRANCE_SLOT_NAMES)
    if entrance_in_the_rhythm:
        account.append(
            f"the entrance stands IN the rhythm: its slot came out at "
            f"{_door_slot.width:.3f} m, the frontage's own pitch, because "
            f"{entrance_w:.2f} m — the opening plus a jamb either side — fits inside "
            "it. An entrance is an opening in an ordinary bay exactly as a window is, "
            "and the masonry beside it is then thinner than the masonry between two "
            "windows by exactly half what the two openings differ by, which is the "
            "only difference there should be (A27)"
        )
    else:
        account.append(
            f"the entrance takes a bay of its OWN, {_door_slot.width:.3f} m wide against "
            f"the rhythm around it: {entrance_w:.2f} m of opening and jambs will not go "
            "inside this frontage's pitch. This is the exception, and it is conditioned "
            "on width rather than on the slot being a door — a slot wider than a bay is "
            "carried up every storey and costs the building a window on every floor, "
            "which a narrower one does not (A27, D6)"
        )
    # **A10.2, in the account rather than only in a comment.** The one thing on
    # this frontage that costs the building axes is the door it has, and a
    # trade that real is worth saying out loud in the artefact that records
    # the decisions. Stated as the difference between the two doors, so a
    # reader can see the cost without knowing either number, and stated as
    # entitlement rather than ambition, which is what the corpus says it is.
    _other = (
        catalogue.ENTRANCE_PEDESTRIAN
        if entrance.kind == catalogue.ENTRANCE_CARRIAGE
        else catalogue.ENTRANCE_CARRIAGE
    )
    _delta = entrance_w - float(catalogue.entrance_slot_width(_other))
    account.append(
        f"which is {abs(_delta):.2f} m {'more' if _delta > 0 else 'less'} frontage than "
        f"a {_other} would have taken — on a narrow parcel a difference that size is a "
        f"whole window axis, carried up every storey. Which door a frontage has is "
        f"entitlement and not ambition, so this is the one thing on the facade that "
        f"buys windows or spends them (A10.2)"
    )
    account.extend(f"[horizontal] {line}" for line in bay_result.account)
    bays = bay_result.slots

    # **A10.1 — the bay-pitch floor, enforced over what it is a floor under.**
    # ``_BAY_PITCH_MAX`` had a tripwire and ``_BAY_PITCH_MIN`` had none, which
    # left a stated ABSOLUTE band guarded on one side only. This is the other
    # side, and it is deliberately asserted over the ``bay`` slots rather than
    # over every slot in the run: the band is a statement about the REPEATING
    # module, and the two things below it — the narrow special and the
    # entrance — are not that module and carry their own bounds (the special
    # by its own spec, the entrance by the two checks in 3c).
    #
    # It is a postcondition, not a hope: the solver is handed the band as
    # ``bay_spec`` and returns bays inside it, so this can only fire if the
    # fitting phase ever starts resizing a repeating slot past the bounds it
    # was given — which is exactly the divergence worth catching here, one
    # phase from where it happened, instead of in a silhouette three phases
    # downstream.
    for slot in bays:
        if slot.name != "bay":
            continue
        if slot.width < float(_BAY_PITCH_MIN) - _TOL:
            raise RuntimeError(
                f"a repeating bay came back {slot.width:.3f} m wide, under the "
                f"{float(_BAY_PITCH_MIN):.3f} m this module states a bay may be "
                f"({_BAY_PITCH_MIN.why}). The rhythm of the frontage is what this "
                "bound is about; below it the piers stop reading as carrying the "
                "lintels between them"
            )
        if slot.width > float(_BAY_PITCH_MAX) + _TOL:  # pragma: no cover - tripwire
            raise RuntimeError(
                f"a repeating bay came back {slot.width:.3f} m wide, over the "
                f"{float(_BAY_PITCH_MAX):.3f} m this module states a bay may be "
                f"({_BAY_PITCH_MAX.why})"
            )

    # A6.1, asserted rather than believed: exactly one entrance, always. This
    # is a postcondition of the phase, not a hope about the solver, and the
    # cheapest place to catch a fixed slot that got dropped or duplicated.
    doors = [i for i, s in enumerate(bays) if s.name in catalogue.ENTRANCE_SLOT_NAMES]
    if len(doors) != 1:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"a building has exactly one entrance; this grid has {len(doors)}: "
            f"{[bays[i].name for i in doors]}"
        )
    # And it is where the rule put it. ``_entrance_index_hint`` promises the
    # middle of the interior run, or one place left of it on an odd run; the
    # narrow specials the solver may have added sit outside that count, so the
    # door is allowed to be one further off centre for each of them.
    interior = [i for i, s in enumerate(bays) if s.name != "pier_end"]
    if interior:
        n_special = sum(1 for s in bays if s.is_special)
        place = interior.index(doors[0])
        off_axis = abs(2 * place - (len(interior) - 1))
        if off_axis > 1 + n_special:  # pragma: no cover - tripwire
            raise RuntimeError(
                f"the entrance landed {off_axis / 2.0:.1f} element(s) off the axis of a "
                f"run of {len(interior)} with {n_special} narrow special(s); the "
                "positional rule allows the middle, or half a place left of it"
            )

    grid = Grid(
        storeys=storeys,
        bays=bays,
        cornice_height=cornice_height,
        eaves_height=eaves_height,
        envelope=envelope,
        account=tuple(account),
        extra_garret_storeys=extra_garret_storeys,
    )

    # ``built_height`` asks the storeys the question ``eaves_height`` stores
    # the answer to. They are one fact, so they are checked against each
    # other here rather than merely asserted to agree in a docstring: if a
    # future change ever puts a slot on the wrong side of the eaves line,
    # this is where it fails, not three phases downstream in a silhouette.
    if abs(grid.built_height - eaves_height) > _ROOF_EPS:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"the storeys below the eaves sum to {grid.built_height:.6f} m but the "
            f"eaves line is at {eaves_height:.6f} m"
        )
    if grid.built_height > ceiling_value + _ROOF_EPS:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"built facade {grid.built_height:.6f} m exceeds the legal ceiling "
            f"{ceiling_value:.6f} m ({ceiling_citation})"
        )
    return grid
