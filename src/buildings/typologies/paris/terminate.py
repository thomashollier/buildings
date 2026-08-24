"""Phase 5 — termination (S7). The comble, and the silhouette that proves it legal.

Nothing in this file chooses a roof shape. The comble is the **residue** of the
gabarit: the legal solid computed in S3 (``Grid.envelope``) already says how far
back from the facade plane the roof must be at every height above the eaves, and
all this phase does is trace that boundary and hang things off it. Change the
decree and the roof changes shape without a line of this module moving —

- pre-1884, the comble is inscribed below a **45° diagonal** springing from the
  eaves (*égout du toit*), so the profile comes back as two points and a
  straight face;
- 1884+ (Alphand) the diagonal is replaced by an **arc of a circle whose radius
  depends on street width**, near-vertical where it leaves the eaves, which is
  precisely what lets a further storey be built set back from the facade — the
  profile comes back sampled and curved;
- 1902+ (Bonnier) that arc runs for an eighth of a turn and is then continued by
  a **45° oblique**, so the profile has a visible break in it and the ridge can
  go very high on a deep parcel.

Those three sentences are in ``reglement.py`` as ``GabaritEnvelope.setback_at``.
This module calls it. There is no ``if year > 1884`` here, and no second copy of
the geometry.

### Where the comble springs from, and where it stops (A3.1)

Two different questions, and running them off one number was the defect.

The comble **springs** from the built eaves — ``Grid.built_height``, the sum of
the storeys — not from the legal cornice ceiling. The decree draws the comble
from the *égout du toit*: a 45° diagonal springing from it before 1884,
Alphand's arc after. So a building that stopped its stone short carries the
whole roof *shape* down with it, which is what keeps a pre-1884 comble a single
straight plane in the section instead of a vertical stub with a plane on top of
it. Anchoring the shape at the legal ceiling instead would put a slab of
full-depth phantom mass above the stone of every building that spent less than
its allowance.

The comble **stops** at the top of the gabarit, ``env.total_height``, and that
line does not come down with the eaves. ``env.ridge_height`` is a height above
the legal cornice — ``compute_envelope`` derives it there — so reading it as a
height above a lower eaves line re-anchors a cornice-referenced number at the
wrong datum and deducts the facade's unspent ambition a second time, from the
roof. In the harness case that silently destroyed 1.23 m of legal height: the
building was forbidden its own allowance because it had declined to spend it on
stone. A comble may not exceed the gabarit; it is under no obligation to be as
short as the building under it is modest.

The lawful way to give that height back is the one the règlement provides:
trace the **same curve** from the **same springing** to a **taller top**. The
comble still leaves the eaves as a 45° plane (or Alphand's arc); it simply runs
higher up that plane, and pays the règlement's price for doing so, which is
inset — every extra metre of height is an extra metre back from the facade, so
it is the *parcel* that decides how much of the headroom is affordable. That is
what ``slope_profile(top=...)`` exists for, and this file passes ``top`` for
exactly this reason. Re-anchoring the springing at the cornice would have been
free, and it would have been illegal: that was A2.4, now retracted.

``structure.Grid.comble_height`` is the one place those two facts are put
together — the curve sprung from the eaves, carried to the top of the solid,
capped by the parcel where the two opposing slopes meet — and both this phase
and the garret storey in phase 1 read it rather than each doing the arithmetic.
The single conversion between the cornice datum and the eaves datum lives there
too, named and asserted, as ``_above_the_cornice_to_above_the_eaves``: nothing
computed above the cornice reaches the eaves any other way (A3.1 §3).

The containment query follows the springing. ``Silhouette.within`` is legality:
the eaves may not exceed ``env.facade_height``, no point may pass
``env.total_height``, and every comble point is set back by at least
``setback_at(h)`` for *h* above the **built eaves**. That is the question the
decree asks, and it is what this phase's own tripwire asserts on its output.
``Silhouette.within_the_gabarit_from_the_cornice`` measures the same setbacks
from the cornice line; it is strictly weaker, it is not legality, and it is
kept only to report how far the two lines have drifted apart. Anything that
passes it alone is a comble standing where the diagonal from the real eaves
forbids — which is what A2.4 briefly made ``within`` accept.

### Where the comble folds (A12.1)

The height of the comble is settled above and is not in question: it is the
decree's own allowance sprung from these eaves, and against César Daly's
sixteen measured buildings the canonical case comes out at 3.20 m to their
median 3.19 m. What was wrong was the *fold*.

``structure._comble_section`` decides the fold as a fact about the ROOMS: the
brisis rises in whole *chambres de bonne*, so it lands on the last storey line
the allowance will stand, and the terrasson climbs whatever is left from there
at its own pitch. On the canonical section that is a fold at 90.6 % of the
comble, a 0.30 m terrasson, and 3.69 m of flat zinc behind it — which is not a
*comble brisé*, it is a slab with a nick near the top, and at facade scale that
is what it reads as.

The section is over-determined once the terrasson's pitch is fixed, so the same
three numbers can be read the other way round: the terrasson **arrives at the
ridge in the middle of the plot**, and the brisis folds wherever that line
crosses the gabarit. Both readings give the same ridge at the same height. This
phase takes the second — ``_fold_the_terrasson_reaches_the_ridge_from`` — which
puts the canonical fold at 1.904 m, 59.5 % of the comble, against the ≈⅔ Daly's
own section of 125 Champs-Élysées shows. The fold slides *down the envelope*,
so every vertex of the brisis is still a point ``setback_at`` returned and the
containment sweep is unmoved.

Two things stop it: a plot deep enough that a terrasson sprung from the eaves
themselves would top out before mid-depth (that plot has earned its flat
terrasse and keeps it), and the lucarne — the brisis is the garret's outside
wall and the window fills it, so the fold does not go below the height a
window needs. Neither is a period test; both are geometry, and 1884 and 1902
combles pass through the same function.

### What the silhouette is, and in which plane

``Silhouette.points`` is the **section** through the building on a plane
perpendicular to the street: ``(inset from the facade plane, height above the
pavement)``, both in metres, inset positive going back into the parcel. It runs
from the pavement at the facade plane, up the face to the eaves, then out along
the comble to the ridge (and across the flat zinc *terrasse* on top, where the
programme's ridge falls short of the height the parcel's depth would allow).

This is the plane the gabarit is *written* in — ``setback_at``,
``max_height_for_setback`` and ``slope_profile`` all speak ``(inset, height)`` —
so ``within`` is a literal containment test rather than an analogy, and it is
the only view in which the era's geometry is visible at all: a mid-block comble
runs straight from party wall to party wall, so in *front* elevation the 45°
diagonal, the 1884 arc and the 1902 oblique are the same rectangle. G7 asks for
the arc to be "visible in the IR"; the section is where it is visible.

The renderer therefore receives the profile as data and still decides nothing:
whether to mirror it (a corner building's comble is hipped and shows the profile
at its returns) or to extrude it flat between party walls is decided *here*,
from the site, and handed over as the ``ends`` prop with a trace entry on it.

### Sampling the envelope, not re-deriving it

``slope_profile`` rounds its output to 4 decimal places, which is fine for
drawing and not fine for a containment assertion at ``tol=1e-6``: a 5e-5 rounding
of an inset *downward* puts a point microscopically outside the very curve it
was sampled from. So the profile is used for the sample *heights* it chooses —
which is where the knowledge lives, since it is the envelope that knows to put a
vertex on the 1902 break — and every inset is then re-evaluated exactly through
``setback_at``. That is still reading the geometry off ``GabaritEnvelope``; it
is not a second implementation of it.

``slope_profile`` also samples uniformly *in height*, which is the wrong
parameter near the apex of a circular arc: there the curve is nearly
horizontal, so one step in height is a long step in inset and the chord
between two samples cuts 0.15 m inside the arc on a wide boulevard, and 0.37 m
for a comble built all the way to the apex of its arc. That error is safe — a
chord lies inside a convex envelope, so containment never
notices — but a visibly clipped ridge is not the shape the decree describes,
and the whole claim of this stage is that the shape is the decree's. So each
segment is subdivided until it tracks the curve to 2 cm, asking the envelope
for the midpoint along whichever axis the segment spans more (``setback_at``
climbing, ``max_height_for_setback`` running back). Every vertex, original or
inserted, is still a point the envelope returned; straight segments — the 45°
diagonal, the 1902 oblique — deviate by nothing and are never subdivided.

### The two depth limits are one invariant, and it is now asserted (A2.6)

``compute_envelope`` cuts the ridge off where the parcel's two opposing slopes
meet — it takes ``parcel_depth`` and depth-limits ``ridge_height`` from it.
``_comble_profile`` separately takes ``half_depth`` and uses it to decide
whether a flat zinc *terrasse* closes the top. Nothing truncated a comble whose
ridge inset ran past the middle of the parcel, and nothing had to, *as long as*
both numbers came from the same ``site.parcel_depth``. That is two modules
relying on the same unstated invariant, which is the shape of the previous
attempt's street-width disaster — two buildings on one block disagreeing about
how wide their street was, silently. The block stage (S9) is where an envelope
starts arriving from ``BlockDatums`` rather than from this site, so this is the
last moment the assumption is free.

``_comble_profile`` therefore states it: the parcel it is being cut to must be
the parcel its envelope was computed from, and the ridge may not rise above the
height that envelope reaches once half that depth of inset is available. Both
raise. Neither is reachable through ``terminate`` today; that is the point of
asserting them rather than trusting them.

### Dating: geometry is not on this axis at all

``chronology`` catalogues four ``roof`` variants, but they are not four
alternatives, and — this is the correction in A2.5 — none of them is a comble
*shape*.

Comble geometry is **legality**: a 45° plane before 1884, an arc of a circle
after it, Bonnier's eighth-circle-and-oblique after 1902. It arrives on the
decree date, it is not subject to class lag, and it is owned entirely by
``reglement.GabaritEnvelope.roof_envelope``. Nothing in this module chooses it.

What the catalogue dates is **fashion**: three entries are a *dormer-and-
ornament repertoire* (small plain dormers, pedimented dormers, varied dormers
with iron cresting) and one — ``zinc_roofing`` — is a *covering material*, and
its own source says so. Sampling all four from one weighted draw would make a
zinc roof and a pedimented dormer mutually exclusive, which is nonsense; so the
catalogue is partitioned, once, explicitly, and ``_check_roof_axes_are_covered``
fails at import if a future variant lands in neither half.

The axis used to be called ``ROOF_SHAPE_VARIANTS`` and its members used to be
named after comble geometries, and the two chronologies promptly contradicted
each other: at 1885 for a comfortable building the envelope is ``circular_arc``
while the lagged fashion draw returns the variant then called
``diagonal_45_pedimented_dormers``. The *building* was right — an arc comble
carrying old-fashioned pedimented lucarnes is exactly the straggler BRIEF.md
says is the common case — but the name said otherwise and nothing checked.
Two guards now hold the split open, sharing one vocabulary derived from
``RoofEnvelope`` itself so it cannot drift from the decree:

- ``_check_no_geometry_on_the_fashion_axis`` refuses **at import** any
  repertoire entry (or dormer form) whose name uses comble-geometry
  vocabulary. The fashion axis may not spell a decree.
- ``_geometry_claimed_by`` is applied again to the variant actually drawn, and
  a claim that contradicts ``env.roof_envelope`` raises. That is the assertion
  A2.5 asks for literally; the import guard is what makes it unreachable, which
  is the desired state and not an excuse for omitting it.

Both draws are weighted by ``chronology.prevalence`` at ``(year, class)``. There
is no period test anywhere in this file — ``dev/harness/check_no_period_branching.py``
is the automated form of that claim.

### Dormers light the attic, and take its grid (A2.1)

Where the comble is deep enough, ``structure.py`` puts a habitable storey inside
it and ``roles.py`` labels it ``ATTIC`` — the *chambres de bonne*. The lucarnes
are that storey's windows, so their count and placement are read off it rather
than decided here: the attic fills the one shared bay grid like every other
storey, so this module takes the grid from ``roled`` and hangs one dormer on
each of its bays. Where there is no attic storey the comble is a garret rather
than a floor, and the same grid still governs — but the trace says which of the
two it is emitting, because "a window for the servant who sleeps here" and "a
light into a roof void" are not the same element.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from buildings.ir.nodes import (
    DormerNode,
    BrisisWindowNode,
    IronworkNode,
    Node,
    RoofNode,
    SilhouetteNode,
    SpecialNode,
)
from buildings.quantity import Abs, Prop, Quantity, scale_for_class
from buildings.rng import DecisionStream
from buildings.site import SiteContext
from buildings.solver.fitting import PlacedSlot
from buildings.trace import TraceEntry
from buildings.typologies.paris import catalogue, chronology
from buildings.typologies.paris.reglement import GabaritEnvelope, RoofEnvelope
from buildings.typologies.paris.roles import Role, RoledGrid
from buildings.typologies.paris.structure import BRISIS_RISE, Grid

__all__ = [
    "Silhouette",
    "terminate",
    "DORMER_ORNAMENT_VARIANTS",
    "ROOF_MATERIAL_VARIANTS",
    # A10.4: the hip arris derivation is exported so `block._chamfer_roof` can
    # derive it again for the chamfer's own (narrower) width instead of
    # copying the value this phase computed for the parent building's — the
    # same "one function, every caller" discipline A9.3 put in place here.
    "derive_hip_arris",
]


#: Float tolerance for the postconditions this module asserts on its own
#: output. Millimetres matter in a legal envelope; this is float noise only.
_EPS = 1e-9

#: How many halvings the fold is found by (A12.1). The terrasson's line and
#: the envelope are both continuous and the bracket starts at the whole
#: comble, so sixty of them put the answer inside float noise of the crossing
#: for any comble a parcel in Paris can carry — the fold has to land on the
#: same line the polyline's vertex does, and it is the vertex.
_FOLD_BISECTIONS = 60

#: How finely the curved envelopes are sampled into the silhouette polyline.
#: The straight 45° envelope ignores this and returns two points, because
#: ``slope_profile`` knows a straight segment needs no sampling.
_PROFILE_SAMPLES = 24

#: How far the emitted polyline is allowed to fall short of the curve it
#: traces, in metres. ``slope_profile`` samples uniformly *in height*, which is
#: the wrong parameter near the apex of a circular arc: there the curve is
#: nearly horizontal, so a step in height is a long step in inset and the chord
#: between two consecutive samples cuts 0.15 m inside the arc on a boulevard
#: (0.37 m for a comble built to the apex of its arc). That error is safe — a chord lies inside a convex envelope,
#: so the roof is merely smaller than the law allowed — but it is a visibly
#: clipped ridge in anything that draws the polyline, and it is not the shape
#: the decree describes. So each segment is subdivided until it tracks the
#: curve to this tolerance. 2 cm is the width of a slate's lap: below that the
#: polyline is finer than the roof it describes.
_PROFILE_TOLERANCE = 0.02

#: Cap on subdivisions per original segment, so a pathological envelope costs
#: bounded work rather than hanging. Reached only if the tolerance cannot be
#: met; the profile is then as good as this budget allows and still legal.
_PROFILE_MAX_SPLITS = 6

#: How far the two parcel-depth statements (A2.6) may differ before this
#: module treats it as a disagreement rather than as arithmetic.
#:
#: One millimetre, and that figure is not a taste: ``compute_envelope`` rounds
#: ``ridge_height`` to three decimal places, so a ridge that is *exactly*
#: depth-limited can read as up to 0.0005 m above the height the parcel
#: allows. Everything this guard is for — an envelope carrying a different
#: parcel than the site, a hand-built envelope whose comble runs past the
#: middle of the plot — is a disagreement of decimetres or metres, so a
#: millimetre band is wide enough to swallow the rounding and nothing else.
#:
#: The ridge check below is deliberately posed in the HEIGHT domain, where
#: that rounding stays a millimetre. Posed in the inset domain it would not:
#: near the flat apex of a wide-street arc, ``d(inset)/d(height)`` is in the
#: hundreds, and the same half-millimetre reads as two or three centimetres of
#: inset. That is the envelope's own rounding wearing a bigger number, not a
#: roof over the neighbour's garden.
_MAX_DEPTH_MISMATCH = 1e-3


# ---------------------------------------------------------------------------
# Body-derived and compositional quantities (I3)
# ---------------------------------------------------------------------------


#: ABSOLUTE. The shortest lucarne face worth cutting a hole in a roof for: a
#: garret window a person can see out of standing, and reach to open.
_DORMER_FACE_MINIMUM = Abs(
    1.30,
    "INFERRED — a garret window a person can see out of standing, and reach to open",
)

#: ABSOLUTE. The masonry (or zinc-clad framing) over a lucarne's light, before
#: its own little roof starts: the head, and the plate carrying the joue.
_DORMER_HEAD = Abs(0.25, "INFERRED — the head over a lucarne's light and the plate above it")


def _dormer_face_height(brisis: float, skirt: float) -> Quantity:
    """Height of a lucarne's own vertical face, on a brisis this tall.

    **A8.3.** This used to be a flat 1.30 m regardless of the roof. Measured
    against the combles the system actually built, that put the dormers in the
    lowest fifth of the slope with bare zinc filling the whole plane above
    them — the opposite of a Paris roofscape, where the lucarnes are the
    dominant thing on the comble and a bare brisis is what you see on a
    warehouse.

    A real lucarne occupies the whole **brisis** of the storey it lights. That
    is not a proportion anybody chose: the brisis is the outside wall of the
    *chambre de bonne*, the lucarne is that room's window, and a window fills
    the wall it is in between the skirt the plumber needs below it and the
    head carrying the joues above it. So the face is one ``BRISIS_RISE`` band
    less those two, and it is ABSOLUTE for the same reason it always was — a
    servant's window is sized by the servant, and none of the three numbers it
    is made of scales with the building's ambition.

    One band, not the whole brisis, because a post-1884 gabarit can stand two
    or three bands of rooms behind one slope and each of them has its own row
    of lucarnes. This phase draws the lowest row (one per bay); the rows above
    it are not yet modelled, and a face stretched over all of them would be a
    single four-metre window into three different rooms.

    On a comble too shallow to give even ``_DORMER_FACE_MINIMUM`` this returns
    that minimum, and the caller's own "will it fit" test then refuses the
    lucarne rather than drawing a slot too short to see out of.
    """
    band = min(brisis, float(BRISIS_RISE))
    on_the_brisis = band - skirt - float(_DORMER_HEAD)
    if on_the_brisis <= float(_DORMER_FACE_MINIMUM):
        return _DORMER_FACE_MINIMUM
    return Abs(
        on_the_brisis,
        f"the lucarne fills the brisis of the storey it lights: a {band:.2f} m band of "
        f"steep slope, less the {skirt:.2f} m zinc skirt below it and the "
        f"{float(_DORMER_HEAD):.2f} m head above it — a garret room's window is as tall "
        f"as the garret's own wall",
    )


def _dormer_skirt() -> Quantity:
    """The zinc apron between the eaves and the foot of the dormer.

    ABSOLUTE: the gutter and the first course of zinc have to pass in front of
    the dormer's cheeks, and that width is set by the plumber's work, not by
    ambition.
    """
    return Abs(0.35, "INFERRED — gutter and the first course of zinc, passing below the lucarne")


def _shortest_brisis_that_carries_a_lucarne(skirt: float) -> float:
    """The shortest brisis with a garret window still in it, in metres.

    Not a fourth quantity: it is the three the lucarne is already made of,
    added up — the plumber's skirt below it, the shortest face worth cutting a
    hole in a roof for, and the head above it. A brisis shorter than this is a
    slope with a room behind it and no window in it, which is the bare-zinc
    defect A8.3 named, so it is the line the fold does not go below however
    much the terrasson above would like it to (A12.1).
    """
    return skirt + float(_DORMER_FACE_MINIMUM) + float(_DORMER_HEAD)


def _shortest_brisis_that_carries_its_lucarnes(skirt: float, garret_wall: float) -> float:
    """The same line, for a brisis standing more than one storey of rooms.

    **A15.1.** A12.1's third stopping rule — *the fold does not slide below
    the lucarne the brisis carries* — was written when a 45° comble stood
    exactly one band of garret and could only ever have one row of windows in
    it. A comble standing two bands has two rows, the upper row stands on the
    upper band, and a fold that slides past it takes that row off the roof
    just as surely as a fold under ``_DORMER_FACE_MINIMUM`` takes off the
    lower one. Measured, that is what happened: on a 22 m plot the fold went
    to 4.78 m through a 5.80 m brisis and the second row of lucarnes vanished
    from a two-storey garret.

    So the line is the whole rooms below the top one, plus the shortest band
    that still carries a window. On the one-band comble this is exactly
    ``_shortest_brisis_that_carries_a_lucarne`` and nothing moves.
    """
    band = float(BRISIS_RISE)
    rows = max(1, int(garret_wall / band + _EPS)) if band > 0.0 else 1
    return (rows - 1) * band + _shortest_brisis_that_carries_a_lucarne(skirt)


def _fold_the_terrasson_reaches_the_ridge_from(
    env: GabaritEnvelope,
    half_depth: float,
    ridge: float,
    brisis: float,
    ridge_inset: float,
) -> tuple[float, float]:
    """Where this section actually folds, as ``(fold, the fold's own reach)``.

    **A12.1.** ``structure._comble_section`` answers a question about the
    *rooms*: the brisis rises in whole *chambres de bonne*, so the fold lands
    on the last storey line the decree's allowance will stand, and whatever
    the terrasson has left to climb from there it climbs at its own pitch —
    topping out early, and leaving the rest of the plot a flat zinc deck. On
    the canonical Second Empire case that is a fold at 90.6 % of a 3.20 m
    comble, a 0.30 m terrasson, and 3.69 m of flat: a slab with a nick near
    the top, and not a *comble brisé* at all.

    The section is over-determined once the terrasson's pitch is fixed, and
    that is the way out. The same three numbers can be read as: a terrasson of
    that pitch **arriving at the ridge in the middle of the plot**, and a
    brisis that folds wherever that line meets the gabarit. Both readings put
    the same ridge at the same height — the comble height is the decree's and
    Daly's, and nothing here moves it — and they differ only in where the fold
    sits. Only one of them is a roof anybody built.

    So the terrasson is taken as given (its pitch is read off the two ends
    ``structure`` gave it, never restated here) and run back from
    ``(half_depth, ridge)`` until it meets the envelope. That intersection is
    the fold, and the brisis below it is still the gabarit traced by
    ``setback_at`` — the fold moves down the same curve, it does not leave it.

    Three things stop the fold short of that crossing, and each is a real case
    rather than a fallback. The first two hand back exactly the fold and the
    reach ``structure`` stated:

    * **the terrasson already reaches the middle of the plot** — a shallow
      parcel, where the two opposing slopes meet and there is no flat deck to
      remove;
    * **the line meets the envelope at or below the eaves** — a parcel deep
      enough that a terrasson sprung from the eaves themselves tops out before
      mid-depth. That is the plot that *earns* a flat terrasse, and it gets to
      keep one;
    * **the crossing is below the lucarne the brisis carries.** The brisis is
      the garret's outside wall and the lucarne fills it
      (``_dormer_face_height``); a fold under
      ``_shortest_brisis_that_carries_a_lucarne`` would buy a legible break by
      putting the windows out of the roof. So the fold stops on that line
      instead — lower than the garret's wall, higher than the crossing — and
      its terrasson tops out where it tops out, leaving a flat terrasse on the
      only plots deep enough to want one.

    The second returned number is where the fold's own terrasson gets to:
    ``half_depth`` where it ran the whole way, and short of it where the
    lucarne stopped the fold. It is returned with the fold rather than
    recomputed by the caller so the two cannot disagree.
    """
    if ridge <= _EPS or half_depth <= _EPS:
        return (brisis, ridge_inset)
    fold_inset = env.setback_at(brisis)
    rise = ridge - brisis
    run = ridge_inset - fold_inset
    if rise <= _EPS or run <= _EPS:
        return (brisis, ridge_inset)  # no terrasson: nothing to run to the ridge
    if ridge_inset >= half_depth - 1e-6:
        return (brisis, ridge_inset)  # it already gets there
    # The terrasson's pitch, read off its own two ends rather than restated
    # here: a second copy of the constant in ``structure`` is how a roof and
    # the section that draws it come to disagree by a degree.
    slope = rise / run

    def forward_of_the_envelope(h: float) -> float:
        """How far in front of the gabarit the terrasson line runs at height
        ``h`` — negative below the fold, where the line is still outside the
        legal solid, and positive above it."""
        return (half_depth - (ridge - h) / slope) - env.setback_at(h)

    if forward_of_the_envelope(0.0) >= 0.0:
        return (brisis, ridge_inset)  # the line meets the envelope below the eaves
    if forward_of_the_envelope(brisis) <= 0.0:  # pragma: no cover - defensive
        return (brisis, ridge_inset)
    lo, hi = 0.0, brisis
    for _ in range(_FOLD_BISECTIONS):
        mid = 0.5 * (lo + hi)
        if forward_of_the_envelope(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    fold = 0.5 * (lo + hi)
    lowest = _shortest_brisis_that_carries_its_lucarnes(float(_dormer_skirt()), brisis)
    if fold < lowest:
        fold = lowest
        if fold >= brisis:
            return (brisis, ridge_inset)
        # The terrasson leaves that fold at the same pitch and tops out where
        # it tops out; the rest of the plot is the flat terrasse this plot is
        # deep enough to have earned.
        reach = env.setback_at(fold) + (ridge - fold) / slope
        return (fold, min(max(reach, env.setback_at(fold)), half_depth))
    return (min(fold, brisis), half_depth)


def _souche_visible_height() -> Quantity:
    """How much of a souche's masonry stands clear of the roof surface it
    emerges through.

    ABSOLUTE, and this is the quantity A7.3 holds constant — not the stack's
    absolute head height. A souche is built up in brick from the roof outward
    just far enough to flash cleanly and keep its flue out of the eddy the
    roof itself throws (a fact about air and about courses of brick, not
    about the building's ambition), and that showing is roughly 0.5-1.5 m
    whatever the roof is doing beneath it. The predecessor of this quantity,
    `_flue_ridge_clearance`, instead fixed the stack's absolute HEAD height at
    the ridge plus a margin and let the base fall away toward a hipped
    return — which is exactly backwards: on a real building the stack is a
    constant few courses of brick above whatever roof surface it is standing
    on, and it is the head that follows the roof down, not the base that
    follows the head up. Held the old way, a souche at the fully-fallen-away
    end of a hipped return kept the SAME head as one on the ridge and grew
    into a smokestack standing clear of the roof entirely.
    """
    return Abs(
        0.80,
        "INFERRED — a souche shows roughly 0.5-1.5 m of brick above the tiles it emerges through",
    )


def _cresting_height(klass) -> Quantity:
    """Height of the iron cresting along the ridge. PROPORTIONAL: pure
    display, and display is what scales with ambition."""
    return scale_for_class(Prop(0.35, "iron cresting on the ridge — display, ambition-driven"), klass)


def _souche_width(klass) -> Quantity:
    """Width of one chimney stack. PROPORTIONAL: a grander building has more
    rooms per stack, so more flues gathered into one souche."""
    return scale_for_class(
        Prop(0.70, "a souche gathering the flues of one vertical stack of rooms"), klass
    )


# ---------------------------------------------------------------------------
# The two FASHION axes of the `roof` feature family
#
# Neither of them is comble geometry. Geometry is the decree's, it arrives on
# the decree date, and it is read off `env.roof_envelope` — see A2.5 in the
# module docstring for the contradiction that made this worth spelling out.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DormerRepertoire:
    """What a named dormer-and-ornament repertoire consists of.

    ``chronology`` owns *when* a variant was in use; this owns *what it is*.
    Keeping the two apart is what stops "iron cresting" from being spelled as
    a date, which is the conflation the brief names.

    What it deliberately does NOT own is the shape of the comble underneath.
    A repertoire is a set of lucarne forms and a yes/no on cresting: things a
    builder chose, that ramp, that lag down the class ladder, and that a
    modest building keeps for twenty years after the boulevards drop them.
    The plane or curve those lucarnes stand on is not on this axis at all.
    """

    dormer_forms: tuple[str, ...]
    cresting: bool
    source: str


#: The three variants of the ``roof`` family that describe the DORMER-AND-
#: ORNAMENT repertoire. Sampled against each other. (Formerly, and wrongly,
#: ``ROOF_SHAPE_VARIANTS`` — see A2.5: they never described a shape, and
#: naming them as though they did put the fashion axis in a position to
#: contradict the decree.)
DORMER_ORNAMENT_VARIANTS: Mapping[str, _DormerRepertoire] = {
    "small_plain_dormers": _DormerRepertoire(
        dormer_forms=("flat_lucarne",),
        cresting=False,
        source="BRIEF.md roof: 'plain slate slope with small dormers'",
    ),
    "pedimented_dormers": _DormerRepertoire(
        dormer_forms=("pedimented",),
        cresting=False,
        source="BRIEF.md roof: '45° comble with pedimented dormers (canonical 1853–84)'",
    ),
    "varied_dormers_iron_cresting": _DormerRepertoire(
        # "varied dormer shapes" read literally: more than one form is offered,
        # and each dormer draws its own. The earlier repertoires offer one
        # form, so their draw is a formality that always returns the same
        # answer — which is the point: variety is a property of the variant,
        # not of a branch somewhere that knows the year.
        dormer_forms=("pedimented", "round_arched", "segmental", "oeil_de_boeuf"),
        cresting=True,
        source=(
            "BRIEF.md roof: 'curved arc comble, taller and more elaborate, with "
            "varied dormer shapes and iron cresting (1884+)'"
        ),
    ),
}

#: Variants of the same family that describe the covering MATERIAL. A third
#: independent axis — drawn separately, and able to co-occur with any
#: repertoire and any envelope, exactly as the catalogue entry's own source
#: says.
ROOF_MATERIAL_VARIANTS: frozenset[str] = frozenset({"zinc_roofing"})

#: What a roof is covered with when the material of the moment did not win.
_DEFAULT_ROOF_MATERIAL = "slate"


#: The comble-geometry vocabulary, derived from ``RoofEnvelope`` itself rather
#: than typed out here, so that a decree added to ``reglement.py`` widens this
#: guard on its own. Maps a word to the envelope(s) that word could be naming;
#: ``arc`` is deliberately ambiguous between the 1884 circle and Bonnier's
#: eighth of one, because a name containing it is already on the wrong axis
#: whichever it meant.
_GEOMETRY_WORDS: Mapping[str, frozenset[RoofEnvelope]] = MappingProxyType(
    {
        word: frozenset(
            e for e in RoofEnvelope if word in str(e.value).lower().split("_")
        )
        for e0 in RoofEnvelope
        for word in str(e0.value).lower().split("_")
    }
)


def _geometry_claimed_by(name: str) -> frozenset[RoofEnvelope]:
    """The comble geometry a fashion-variant name claims, if any.

    Empty means the name is honest about being fashion. A non-empty result is
    the set of envelopes the name could be naming — narrowed by intersection
    where the words agree (``circular`` ∧ ``arc`` is the 1884 circle) and
    widened back to their union where they do not, since a name asserting two
    contradictory geometries is certainly asserting geometry.
    """
    matched = [
        _GEOMETRY_WORDS[word]
        for word in str(name).lower().replace("-", "_").split("_")
        if word in _GEOMETRY_WORDS
    ]
    if not matched:
        return frozenset()
    narrowed = frozenset.intersection(*matched)
    return narrowed or frozenset().union(*matched)


def _check_roof_axes_are_covered() -> None:
    """Fail loudly at import if the catalogue grows a roof variant this module
    does not know which axis to put it on.

    Without this, a new variant would silently vanish from the repertoire draw
    (if it were a repertoire) or silently become one (if it were a material),
    and the only symptom would be a roof that looks subtly wrong in a contact
    sheet six stages later.
    """
    catalogued = {v.name for v in chronology.variants_for("roof")}
    known = set(DORMER_ORNAMENT_VARIANTS) | set(ROOF_MATERIAL_VARIANTS)
    missing = sorted(catalogued - known)
    stale = sorted(known - catalogued)
    if missing or stale:
        raise RuntimeError(
            "terminate.py and chronology's roof catalogue disagree — "
            f"unclassified variant(s): {missing}; classified but not catalogued: {stale}. "
            "Every roof variant must be declared a DORMER-AND-ORNAMENT repertoire "
            "(DORMER_ORNAMENT_VARIANTS) or a MATERIAL (ROOF_MATERIAL_VARIANTS); the "
            "two are different axes and must not be sampled against each other."
        )


def _check_no_geometry_on_the_fashion_axis() -> None:
    """Fail loudly at import if a fashion variant names a comble geometry.

    This is A2.5 made mechanical. Comble geometry is a step function on a
    decree date and belongs to ``reglement``; the repertoire below is a ramped,
    class-lagged fashion. A variant called ``diagonal_45_pedimented_dormers``
    puts one inside the other, and then a 1885 comfortable building — legally
    obliged to use the arc, and by class lag still fitting pedimented lucarnes
    — carries a variant whose *name* denies the law it is obeying.

    The building was never wrong; only the name was. So the name is what is
    forbidden. Dormer forms are checked as well as variant names, because a
    form is a name a node carries downstream just the same.
    """
    offenders: list[str] = []
    for name, repertoire in DORMER_ORNAMENT_VARIANTS.items():
        for candidate in (name, *repertoire.dormer_forms):
            claimed = _geometry_claimed_by(candidate)
            if claimed:
                offenders.append(
                    f"{candidate!r} names {sorted(e.value for e in claimed)}"
                )
    for name in ROOF_MATERIAL_VARIANTS:
        if _geometry_claimed_by(name):
            offenders.append(f"{name!r} (material axis) names a comble geometry")
    if offenders:
        raise RuntimeError(
            "the roof FASHION axis names a comble GEOMETRY: "
            + "; ".join(sorted(offenders))
            + ". Comble geometry is legality — a 45° plane, an arc, or Bonnier's "
            "eighth-circle-and-oblique, fixed by decree on the decree date and not "
            "subject to class lag — and reglement.GabaritEnvelope.roof_envelope owns "
            "it. This axis dates dormer form, cresting and ornament only. Rename the "
            "variant after what a builder actually chose."
        )


_check_roof_axes_are_covered()
_check_no_geometry_on_the_fashion_axis()


# ---------------------------------------------------------------------------
# Silhouette
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Silhouette:
    """The street-facing section through the building, as a polyline.

    ``points`` are ``(inset_from_facade_plane, height_above_pavement)`` in
    metres, bottom to top: the pavement, the facade plane, the eaves, then the
    comble out to the ridge. Inset is positive going back into the parcel, so
    a negative inset is something hanging over the street.

    Containment hangs off it, and ``within`` is the legal question (A3.1): *is
    this comble inscribed below the envelope springing from this building's own
    eaves* — the égout du toit, which is where the règlement springs it. That
    is the only test a caller asking "is this building legal?" wants.

    ``within_the_gabarit_from_the_cornice`` is kept beside it as a strictly
    weaker query — the same setbacks measured from the legal cornice line. It
    is not legality and must not be used as it; A2.4 briefly made it so, which
    accepted combles the diagonal from the real eaves forbids. It is retained
    only for reporting the gap between the two lines, and ``within`` implies it
    and never the reverse.
    """

    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "points", tuple((float(a), float(b)) for a, b in self.points)
        )
        if len(self.points) < 2:
            raise ValueError(
                "a silhouette needs at least the pavement and the eaves; "
                f"got {len(self.points)} point(s)"
            )

    # -- readers ------------------------------------------------------------

    @property
    def eaves_height(self) -> float:
        """Where the facade stops and the comble begins.

        Derived from the polyline itself rather than stored beside it: the
        eaves are the highest point still on the facade plane. Storing it
        twice would let the two disagree, and then ``within`` would be
        checking the comble against the wrong origin without saying so.
        """
        on_plane = [y for inset, y in self.points if abs(inset) <= 1e-6]
        return max(on_plane) if on_plane else 0.0

    @property
    def ridge_height(self) -> float:
        """Total height of the silhouette above the pavement."""
        return max(y for _, y in self.points)

    def _margins(self, env: GabaritEnvelope, anchor: float) -> list[float]:
        """Every margin between this silhouette and the envelope, in metres,
        with the *setback* clause measured from ``anchor``.

        The one place the containment arithmetic lives, so the legal test and
        its weaker cousin cannot drift apart while claiming to be the same
        geometry read from two datums. See ``within`` for what ``anchor`` is
        and why there are two of them.

        **Only the setback clause takes the anchor.** The ceiling does not:
        the top of the solid is ``env.total_height``, a height above the
        pavement, and it is the same number whatever datum the slopes are
        measured from. ``env.ridge_height`` is a height above the LEGAL
        cornice, so subtracting an eaves-relative height from it — which this
        method used to do — re-anchored a cornice number at a lower line and
        deducted the facade's unspent ambition from the roof a second time.
        What makes the legal query the legal one is where the *slopes* spring
        from, not a shorter ceiling; the two facts are kept apart here rather
        than tangled into one subtraction (A3.1 §3).
        """
        margins = [env.facade_height - self.eaves_height]
        for inset, y in self.points:
            margins.append(env.total_height - y)
            h = y - anchor
            if h <= 0.0:
                margins.append(inset)
                continue
            margins.append(inset - env.setback_at(h))
        return margins

    def _contained(self, env: GabaritEnvelope, anchor: float, tol: float) -> bool:
        pts = self.points
        for (_, y0), (_, y1) in zip(pts, pts[1:]):
            if y1 < y0 - tol:
                return False
        return min(self._margins(env, anchor)) >= -tol

    def within(self, env: GabaritEnvelope, tol: float = 1e-6) -> bool:
        """Is every point of this silhouette inside the legal solid?

        Three separate things have to hold, and each of them is a different
        clause of the regulation rather than three spellings of one:

        1. **Nothing overhangs the street.** Every inset is >= 0. (Projections
           over the public way were forbidden from the edicts of 1607 and 1667
           until 1882, and even then only to 0.40 m; a silhouette is the
           building's mass, not its balconies, so it never overhangs.)
        2. **The facade does not exceed the height its street earns.** The
           eaves sit at or below ``env.facade_height``.
        3. **The comble is inscribed in the envelope springing from this
           building's own eaves.** No point rises above ``env.total_height``,
           and at every height *h* above the **eaves** the point is set back by
           at least ``env.setback_at(h)`` — the 45° diagonal, the 1884 arc or
           the 1902 arc-and-oblique, depending on nothing this method knows.

        The polyline must also be monotonically non-decreasing in height, or
        "the eaves" is not a well-defined point on it and clause 2 has no
        subject.

        **Clause 3 is anchored at the built eaves** — the *égout du toit* —
        and that is the legal question, not a stricter one (A3.1). The
        règlement springs the comble from the eaves: "combles must be
        inscribed below a 45° diagonal springing from the eaves (égout du
        toit)". A building that stopped its stone short therefore carries the
        whole roof shape down with it; it does not bank the difference and
        start its roof higher up. A2.4 briefly anchored this clause at the
        legal cornice, which made it **too permissive** — it accepted combles
        the diagonal from the real eaves forbids — and that amendment is
        retracted.

        What the eaves anchoring does NOT do is lower the ceiling to match.
        The top of the solid is ``env.total_height``, a height above the
        pavement that does not come down with the eaves. So a comble sprung
        from eaves below the cornice may run *further above those eaves* than
        ``env.ridge_height`` stands above the cornice — it traces the same
        curve to a taller top, paying for it in inset, which is what
        ``slope_profile(top=...)`` and ``Grid.comble_height`` do. The headroom
        comes back through the height of the curve, never by moving where it
        springs from.

        ``within_the_gabarit_from_the_cornice`` measures the same setbacks
        from the legal cornice. It is strictly weaker and it is **not**
        legality; it exists to report the gap between the two lines.
        """
        return self._contained(env, self.eaves_height, tol)

    def within_the_gabarit_from_the_cornice(
        self, env: GabaritEnvelope, tol: float = 1e-6
    ) -> bool:
        """The weaker cousin of ``within``: the *slopes* measured from the
        legal cornice line rather than from the eaves the comble springs from.

        This is **not** the legality test — ``within`` is (A3.1). It is kept
        because the distance between the two lines is a fact worth reporting:
        a building whose stone reached its ceiling has the eaves and the
        cornice in the same place and the two queries coincide, and how far
        apart they have drifted is exactly the facade ambition left unspent.

        Because the eaves sit at or below the cornice and ``setback_at`` is
        non-decreasing, every setback ``within`` demands is at least the one
        this asks for: passing ``within`` implies passing this, never the
        reverse. Anything that passes only this one is a comble standing in
        space the 45° diagonal from its own eaves forbids.
        """
        return self._contained(env, env.facade_height, tol)

    def clearance(self, env: GabaritEnvelope) -> float:
        """The tightest margin between this silhouette and the legal solid, in
        metres — negative if it breaks out. Useful in a report and in a test
        failure message, where "False" on its own tells you nothing.

        Anchored where ``within`` is anchored, at the built eaves, so that
        ``clearance(env) >= 0`` and ``within(env)`` answer the same question.
        """
        return min(self._margins(env, self.eaves_height))

    def clearance_from_the_cornice(self, env: GabaritEnvelope) -> float:
        """The margin ``within_the_gabarit_from_the_cornice`` measures, in
        metres.

        Same relationship: this is never smaller than ``clearance``, and the
        difference between the two is the facade headroom this building left
        unspent. It is a reporting number, not a legality one.
        """
        return min(self._margins(env, env.facade_height))


# ---------------------------------------------------------------------------
# The comble profile
# ---------------------------------------------------------------------------


def _refine(
    env: GabaritEnvelope,
    lo: tuple[float, float],
    hi: tuple[float, float],
    out: list[tuple[float, float]],
    depth: int,
) -> None:
    """Append ``hi``, subdividing first if the chord ``lo``→``hi`` does not
    follow the envelope to ``_PROFILE_TOLERANCE``.

    The midpoint is asked of the envelope along whichever axis the segment
    spans more: ``setback_at`` where the segment climbs, ``max_height_for_setback``
    where it runs back. Both are the same curve read from opposite sides, and
    using the wider axis is what keeps the near-horizontal apex of a circular
    arc from needing hundreds of samples in height to resolve. A straight
    segment — the 45° diagonal, the 1902 oblique — deviates by nothing and is
    never subdivided, so those profiles come out with exactly the vertices the
    decree has and no more.
    """
    (i0, h0), (i1, h1) = lo, hi
    if depth < _PROFILE_MAX_SPLITS:
        d_i, d_h = i1 - i0, h1 - h0
        chord_i = (i0 + i1) / 2.0
        chord_h = (h0 + h1) / 2.0
        # The gap is measured on BOTH axes, because either one of them alone
        # understates it where the curve runs nearly parallel to it: at the
        # apex of an arc a 1 cm vertical gap is a 20 cm horizontal one.
        gap = max(
            chord_i - env.setback_at(chord_h),
            env.max_height_for_setback(chord_i) - chord_h,
        )
        if d_h >= d_i:
            hm = (h0 + h1) / 2.0
            mid = (env.setback_at(hm), hm)
        else:
            im = (i0 + i1) / 2.0
            mid = (im, env.max_height_for_setback(im))
        if gap > _PROFILE_TOLERANCE:
            # Only if the midpoint genuinely lies between the ends: a clamped
            # envelope (inset past the apex of an arc) returns the same point
            # twice, and recursing on that would not terminate.
            if i0 + _EPS < mid[0] < i1 - _EPS or h0 + _EPS < mid[1] < h1 - _EPS:
                _refine(env, lo, mid, out, depth + 1)
                _refine(env, mid, hi, out, depth + 1)
                return
    out.append(hi)


def _check_the_parcel_is_one_parcel(
    env: GabaritEnvelope, half_depth: float, ridge: float | None = None
) -> None:
    """A2.6 — the two depth limits are one invariant. Say so, loudly.

    A comble is bounded twice over by the same parcel, from two different
    modules. ``reglement.compute_envelope`` takes ``parcel_depth`` and cuts
    ``ridge_height`` off at the height where the two opposing slopes would
    meet. ``_comble_profile`` separately takes ``half_depth`` and uses it to
    close the top with a flat zinc *terrasse* when the ridge falls short of the
    middle. Neither truncates anything on the other's behalf, and neither
    needed to — *provided* both numbers came from one ``site.parcel_depth``.

    That proviso was never written down, and an unwritten invariant shared
    between two modules is the exact shape of the failure this project exists
    to avoid: the previous attempt let two buildings on one block hold
    different opinions about how wide their street was, and nothing said a
    word. S9 is where an envelope starts arriving from ``BlockDatums`` instead
    of from this site, so this is where the same class of bug would land — and
    its symptom would be a roof silently running past the middle of the parcel,
    into the courtyard or over the neighbour, with a perfectly clean silhouette
    and a perfectly clean trace.

    Two things are therefore checked, and they catch different failures:

    1. the parcel this comble is being cut to IS the parcel its envelope was
       computed from — the ``BlockDatums`` disagreement, caught at the datum;
    2. neither the envelope's own ridge nor the comble this building actually
       carries rises above the height the envelope reaches once half that
       depth of inset is available — the geometric invariant, which catches an
       envelope that agrees about the parcel but was never depth-limited by it
       (built by hand, or by a future code path that forgets to), and equally
       a *built* comble carried past the middle of the plot on the strength of
       facade headroom the parcel has no room for.
    """
    ridge = env.ridge_height if ridge is None else float(ridge)
    if abs(2.0 * half_depth - env.parcel_depth) > _MAX_DEPTH_MISMATCH:
        raise ValueError(
            "the parcel this comble is being cut to and the parcel its gabarit was "
            f"computed from are not the same parcel: the comble is being closed at "
            f"{half_depth:.4f} m from the facade (a {2.0 * half_depth:.4f} m parcel) "
            f"while the envelope was derived for a {env.parcel_depth:.4f} m one. "
            "compute_envelope depth-limits the ridge from its own parcel_depth and "
            "this phase closes the terrasse from the site's; the two must be one "
            "number or the roof runs past the middle of the plot with nothing "
            "objecting. If this envelope came from a block datum, the block and the "
            "site disagree — resolve it there, one way, before it reaches here."
        )
    reachable = env.max_height_for_setback(half_depth)
    # Two heights, two anchors, and they are checked SEPARATELY rather than
    # through a `max()` of the pair (A3.1 §3). Both are heights above a
    # springing, but not above the same one: `env.ridge_height` is above the
    # legal cornice — the springing `compute_envelope` assumed, since it
    # reckons for a facade built to its ceiling — while `ridge` is above the
    # eaves this building actually has. The parcel limit is springing-relative
    # too, so each comparison is sound on its own; taking the larger of the
    # two first would have silently reported one anchor's number under the
    # other's name in the failure message, which is the confusion this
    # amendment exists to stop.
    for height, datum in ((env.ridge_height, "legal cornice"), (ridge, "built eaves")):
        if height <= reachable + _MAX_DEPTH_MISMATCH:
            continue
        raise ValueError(
            f"this comble's ridge stands {height:.4f} m above the {datum} it is "
            f"reckoned from, but on a {2.0 * half_depth:.4f} m parcel the "
            f"{env.roof_envelope.value} envelope has only reached {reachable:.4f} m by "
            f"the time it is halfway back (inset {half_depth:.4f} m) — the two opposing "
            "slopes have already met and this roof continues past them. "
            "compute_envelope depth-limits the ridge for exactly this reason; an "
            "envelope that arrives here without having been depth-limited must be "
            "rejected rather than drawn."
        )


def _comble_profile(
    env: GabaritEnvelope,
    half_depth: float,
    ridge: float | None = None,
    brisis: float | None = None,
    ridge_inset: float | None = None,
) -> tuple[tuple[float, float], ...]:
    """The comble boundary as ``(inset, height above the eaves)``, exactly.

    **A8.3.** This traces the comble that was BUILT, not the envelope it was
    built inside. Those are not the same shape and saying they were is what
    gave the whole Second Empire a roof with no mansard break in it. A 45°
    diagonal is a legal maximum: the line a builder may not cross. The
    building inside it is a *comble brisé* — a steep **brisis** and a shallow
    **terrasson** — and that break is the single most recognisable thing about
    a Paris roof.

    Two arguments, one for each plane, and both come from
    ``structure._comble_section`` so that the roof this phase cuts, the garret
    S3 put inside it and the storey stack all read one answer:

    * ``brisis`` — where the steep lower slope folds. The brisis follows the
      gabarit exactly, because a builder takes every centimetre of floor the
      law allows him: it is ``slope_profile`` traced to the fold, so every
      vertex on it is still a point ``setback_at`` returned, at a height above
      the *eaves*.
    * ``ridge`` and ``ridge_inset`` — the top, and how far back it stands.
      From the fold the terrasson leaves the envelope and runs STRAIGHT back
      to ``ridge_inset``. It is inside the gabarit by construction: it starts
      on the envelope and climbs more shallowly than the envelope does, and
      every envelope in ``reglement`` is concave, so a chord under it stays
      under it. ``terminate`` asserts that anyway. Where ``ridge_inset`` falls
      short of ``half_depth`` — the terrasson reached the top of what the
      decree allows before it reached the middle of the plot — a flat zinc
      *terrasse* closes the rest. **A12.1**: that is now the deep-parcel case
      and not the ordinary one. ``terminate`` asks
      ``_fold_the_terrasson_reaches_the_ridge_from`` for the fold, which slides
      it down the same gabarit until the terrasson runs the whole way, so on an
      ordinary parcel the two opposing slopes meet and there is no deck.

    Both default to ``env.ridge_height`` — the envelope traced to its own top
    with no break at all, which is what a caller probing the envelope *as an
    envelope* means, and the only case where the legal maximum and a roof
    section are the same polyline.

    They are heights above the eaves, never above the LEGAL cornice; applying
    a cornice-relative number here is the anchor mix A3.1 §3 forbids, and the
    one conversion lives in
    ``structure._above_the_cornice_to_above_the_eaves``.


    Segments that cut across the curve rather than following it are then
    subdivided (see ``_refine``), which changes nothing about *which* curve is
    being traced — every vertex, original or inserted, is still a point the
    envelope returned.

    ``half_depth`` and ``env`` each carry a statement about the parcel, and
    until A2.6 nothing checked that they were the same statement — see the
    module docstring. They are checked here, where the two meet, and a
    disagreement raises rather than producing a roof over the middle of
    someone else's plot.
    """
    ridge = env.ridge_height if ridge is None else float(ridge)
    brisis = ridge if brisis is None else min(float(brisis), ridge)
    top_inset = half_depth if ridge_inset is None else float(ridge_inset)
    top_inset = min(max(top_inset, 0.0), half_depth)
    _check_the_parcel_is_one_parcel(env, half_depth, ridge)

    if ridge <= _EPS:
        return ((0.0, 0.0),)

    # ---- the brisis: the gabarit itself, traced to the fold ---------------
    heights: list[float] = []
    for _, h in env.slope_profile(_PROFILE_SAMPLES, top=brisis):
        h = min(max(h, 0.0), brisis)
        if not heights or h > heights[-1] + _EPS:
            heights.append(h)
    if not heights or heights[0] > _EPS:
        heights.insert(0, 0.0)
    if heights[-1] < brisis - _EPS:
        heights.append(brisis)
    heights[-1] = brisis

    pts: list[tuple[float, float]] = [(0.0, 0.0)]
    for h0, h1 in zip(heights, heights[1:]):
        _refine(env, (env.setback_at(h0), h0), (env.setback_at(h1), h1), pts, 0)

    # ---- the terrasson, then whatever flat deck is left ------------------
    #
    # Two appends and neither is a decision: the first runs from the fold to
    # the ridge at ``ridge_inset``, the second closes the rest of the plot
    # flat. Where the terrasson reached the middle of the plot the two
    # collapse into one, and where the comble had no height to break in
    # (``ridge == brisis``) the first is already horizontal and IS the flat
    # deck. One shape, read off the three numbers ``structure`` stated, with
    # nothing here deciding which of the cases it turned out to be.
    fold_inset = pts[-1][0]
    if top_inset > fold_inset + 1e-6:
        pts.append((top_inset, ridge))
    if half_depth > pts[-1][0] + 1e-6:
        pts.append((half_depth, ridge))
    return tuple(pts)


def _mansard_angles_of(
    profile: Sequence[tuple[float, float]], brisis: float, ridge: float
) -> tuple[float, float, float]:
    """The built comble described as a broken mansard:
    ``(lower_angle_deg, upper_angle_deg, break_pct)``.

    **A8.3.** This used to be ``env.mansard_angles(ridge)`` — the *envelope*
    asked to describe itself. For a pre-1884 building that answer is
    ``45° / 45° / 100 %``, which is a truthful description of a legal maximum
    and a false description of every Second Empire roof ever built: the
    renderer read it, correctly concluded there was no break, and drew a plain
    slope on the whole Haussmann era. The envelope's own method is still right
    for what it is for — describing an envelope — and is still where a caller
    who wants the *legal* two-segment reading goes. What the IR must state is
    what this phase BUILT, so it is measured off the polyline this phase just
    built, and the polyline is the only source.

    The angles are chord angles, taken from the springing to the fold and from
    the fold to the ridge, so a curved brisis is reported by the single slope a
    reader (and a renderer) would call it — which is what a two-segment
    description is for. ``break_pct`` is the fold as a fraction of the built
    height, which is exactly the number the renderer multiplies by.

    A comble with no terrasson reports its break at 100 % and its two angles
    equal, which is the renderer's own test for "there is nothing to fold".
    """
    if ridge <= _EPS or not profile:
        return (45.0, 45.0, 1.0)
    fold_inset = 0.0
    for inset, h in profile:
        if h <= brisis + _EPS:
            fold_inset = max(fold_inset, inset)
    lower = math.degrees(math.atan2(brisis, max(fold_inset, 1e-6)))
    # The terrasson's OWN far end, which is the first point at the ridge — not
    # the last point of the polyline, which may be the far side of a flat
    # terrasse and would report a terrasson shallower than the one built.
    top_inset = next(
        (inset for inset, h in profile if h >= ridge - _EPS), profile[-1][0]
    )
    d_h = ridge - brisis
    d_i = max(top_inset - fold_inset, 1e-6)
    upper = math.degrees(math.atan2(d_h, d_i))
    if d_h <= _EPS:
        # No terrasson: the two planes are one plane, and saying so in the
        # renderer's own vocabulary (equal angles, break at 100 %) is how this
        # phase states "do not draw a fold here".
        return (round(min(lower, 89.0), 2), round(min(lower, 89.0), 2), 1.0)
    # The two angles are rounded because they are a DESCRIPTION — nobody
    # measures a roof to a hundredth of a degree — but ``break_pct`` is not:
    # the renderer multiplies it by the ridge height to find the fold, and it
    # has to land on the same line the ``profile`` vertex does. Rounded to
    # three places it missed by up to a centimetre on a tall comble, which is
    # a break line drawn beside the break rather than on it.
    return (round(min(lower, 89.0), 2), round(upper, 2), brisis / ridge)


def _bay_slots(roled: RoledGrid) -> list[tuple[int, PlacedSlot]]:
    """The horizontal slots a lucarne may stand over — **asked of ``roled``,
    not re-derived here (A9.1).**

    This used to be the predicate itself: repeating bays plus the entrance's
    slot, spelled out in this module. It is the same question ``RoledGrid``
    answers as ``lit_bays`` — which axes on this frontage carry a window
    above the pavement — and two modules holding the same predicate is the
    divergence I1 exists to remove, exactly as A9.3 finds for the hip run.
    So the predicate lives with the grid it is about, and this reads it.

    Its reasoning, kept where it is used: the end piers and any narrow
    special are not bays and get no lucarne (a dormer over a 1.35 m blind
    panel would be a window into the party wall), while the entrance column
    does get one — a porte cochère is a ground-floor fact, and four storeys
    up the same column is carrying ordinary windows like every other.

    **A10.3 — the residual fall in the lucarne count, and why nothing here
    is what causes it.** A10.3 measured the count falling as class rises on 9
    of 21 combinations (12 m: 4/4/3/3, 18 m: 6/6/5/5, 20 m: 7/7/6/6). Those
    are the AXIS counts of the same frontages, digit for digit, because this
    function is the whole of how the roofscape is counted: one lucarne per
    axis per band of brisis, and no rhythm of its own to drift with anything.
    The frontages fall because the two richer classes have a carriage arch
    taking 1.05 m more frontage than a pedestrian door — A10.2 prices it —
    and the comble has no opinion about that whatever; it counts the axes it
    is standing on.

    So there is nothing to fix in the comble, and fixing it here would be the
    damage: decoupling the lucarne count from the bay grid to make a bad
    comparison come out flat would put the roof windows out of line with the
    windows below them, which is the one thing a Paris frontage never does.
    What is contractual, and what the tests now assert in the exact form
    rather than as "must not fall", is that the count is a function of the
    comble's own frontage and geometry with class nowhere in it: two
    buildings of any two classes on one parcel with one door get the same
    roofscape, not "give or take one".
    """
    return list(roled.lit_bays)


def _attic_storey(roled: RoledGrid):
    """The habitable storey inside the comble, if the comble is deep enough
    for one — the *chambres de bonne*. ``None`` where it is not.

    Read off ``roles.assign_roles``' answer rather than recomputed: whether a
    slot lies inside the roof envelope is a question about the cornice line
    and the storey stack, both of which belong to the earlier phases, and this
    module asking it again would be a second opinion able to disagree with the
    first (I1). The lucarnes below are that storey's windows when it exists,
    so the trace can say whose room it is lighting.
    """
    attic = [st for st in roled.storeys if st.role is Role.ATTIC]
    return attic[0] if attic else None


# ---------------------------------------------------------------------------
# Where the roof surface actually is, along the frontage (A7.3, A9.3)
#
# Mid-block the front slope is one flat band the whole frontage wide, so the
# ridge line IS the roof surface at every x. A hipped corner comble is not
# flat along the frontage: it returns at both ends, and the surface falls
# away from the ridge toward each return exactly the way a real arêtier
# (hip rafter) does. Where a souche emerges is a STRUCTURAL fact about that
# surface, not a rendering approximation — so it is computed here, from the
# same profile this phase already built, and carried on the stack's own IR
# props. The renderer draws the base it is given and does not recompute it.
#
# **A9.3.** ``derive_hip_arris`` (named ``_hip_arris`` until A10.4 gave it a
# second legitimate caller — see below) is now the ONLY place this geometry is
# derived. Before this fix ``elements._hip_arris`` (the renderer) and this
# module's own ``_hip_arris_end`` computed it independently — A8 had already
# fixed the renderer's copy to key the pitch to the section's own TRUE reach
# (where the profile first climbs to full height) rather than ``profile[-1]``,
# which can run on flat for however much of the parcel's depth a terrasse or a
# curve's own flattening leaves spare, but this module's copy was never given
# the same fix. The two disagreed by up to 1.559 m — the mirror image of the
# bug A7.3 exists to eliminate, and the fourth time this project has hit "two
# modules hold independent opinions about the same structural fact" (A4.1,
# A6.8, A7.3). Structurally, not just numerically, this time: the result is
# carried on the roof node's own ``hip_arris`` prop, the renderer reads it
# rather than recomputing it from the profile, and there is now exactly one
# function that knows how a hip arris is derived.
#
# **A10.4.** A fifth instance of the same defect class, this time in
# ``block._chamfer_roof``: the pan coupé copies the parent building's roof
# props wholesale and overrides only ``w`` (frontage) and ``seam_count`` for
# the chamfer's own narrower width — leaving the copied ``hip_arris`` stating
# a run derived from the WIDE parent facade on a roof node now half as wide,
# which draws two hip lines that cross past the narrow face's own mid-span
# (a bowtie). Fixed the way A9.3 fixed the mirror bug: this function, unchanged,
# is the one and only place a hip arris is derived, so it is exported (no
# leading underscore) and ``block.py`` calls it again for the chamfer's own
# width instead of trusting a copied value computed for a different one.
# ---------------------------------------------------------------------------


def derive_hip_arris(
    facade_w: float,
    profile: Sequence[tuple[float, float]],
    break_h: float | None = None,
) -> tuple[tuple[float, float], ...]:
    """The hip's own arris, one side, as ``((0, 0), (run, height))`` — how far
    in from the end of the frontage and how high over the eaves the front
    slope proper begins. Empty if there is no return to trace (no frontage,
    or a comble with no rise at all) — the caller's cue that the surface is
    the ridge everywhere. Mirrored at the right-hand end, and never computed
    there separately: a run past mid-span folds back onto this same half by
    distance from the *nearest* end.

    STRAIGHT SEGMENTS, one per plane of the roof (A4.5, as A19.1 corrects it).

    A real arêtier is a straight timber, so this is never the curved
    depth-section reused edge-on — that is what bulged into an onion dome on a
    narrow chamfer. But a mansard is not one plane, and it therefore is not one
    timber: a steep brisis and a shallow terrasson meet at a fold, and the hip
    breaks there like everything else on the roof does.

    A4.5 originally read "straight" as "a single straight line at the section's
    AVERAGE pitch". That average is what a two-plane roof is precisely not. On
    a tall comble it puts the hip far too shallow near the eaves, which drags
    the fold inward until it disappears: on the post-1884 corner preset the
    brisis break was drawn across 1.00 m of a 15 m frontage where the geometry
    puts it across 9.68 m, and the roof read as a plain cone rather than a
    steep skirt under a small pyramidal cap.

    So the arris is a polyline whose every SEGMENT is straight, with a knot at
    the fold. The onion dome cannot come back, because no segment ever follows
    the curve: on a post-1884 arc the lower segment is the arc's CHORD, which
    lies inside the section by construction.

    ``break_h`` is the fold's height over the eaves, and it comes from the
    roof's own ``break_pct`` — the A6.10 rule, that where a plane changes is a
    stated fact and not something to be guessed from a polyline vertex, since
    "a curve refined for tolerance can carry an extra vertex nowhere near the
    actual break". Omitted, this degrades to the single-plane line, which is
    the right answer for a roof that genuinely has one plane.

    Both knots are taken to the section's TRUE reach — the point the profile
    FIRST climbs to full height, not ``profile[-1]`` (A8.2/A9.3), which can run
    on flat for however much of the parcel's depth a terrasse or a curve's own
    flattening approach to the ridge leaves spare, and has nothing to do with
    the frontage.
    """
    half = facade_w / 2.0
    if half <= _EPS or len(profile) < 2:
        return ()
    full_run, full_h = profile[-1]
    if full_run <= _EPS or full_h <= _EPS:
        return ()

    # The section's TRUE reach: the first point the profile climbs to full
    # height, rather than wherever the polyline happens to end. Where there
    # is no flat run-out this is `full_run` itself and nothing below changes.
    rise_run = full_run
    prev_x, prev_h = profile[0]
    for x, h in profile[1:]:
        if h >= full_h - _EPS:
            span = h - prev_h
            t = (full_h - prev_h) / span if span > 1e-12 else 0.0
            rise_run = prev_x + t * (x - prev_x)
            break
        prev_x, prev_h = x, h

    # The knots: the eaves, the fold if there is one inside the true reach,
    # and the point the section is fully risen.
    knots: list[tuple[float, float]] = [(0.0, 0.0)]
    if break_h is not None and _EPS < float(break_h) < full_h - _EPS:
        fold_run = _profile_run_at_height(profile, float(break_h))
        if _EPS < fold_run < rise_run - _EPS:
            knots.append((fold_run, float(break_h)))
    knots.append((rise_run, full_h))

    # Two returns have to fit side by side in the frontage there is. Where the
    # section outruns it the arris stops at mid-frontage, on whichever plane it
    # had got to — a pavilion peak (A9.3), not a spike and not a clamp.
    if half >= rise_run:
        return tuple(knots)
    kept: list[tuple[float, float]] = []
    prev_x, prev_h = knots[0]
    for x, h in knots:
        if x >= half:
            span = x - prev_x
            t = (half - prev_x) / span if span > 1e-12 else 0.0
            kept.append((half, prev_h + t * (h - prev_h)))
            break
        kept.append((x, h))
        prev_x, prev_h = x, h
    return tuple(kept)


def _profile_run_at_height(
    profile: Sequence[tuple[float, float]], height: float
) -> float:
    """How far into the section the profile stands at ``height`` over the
    eaves — linear between the sampled points, and the LAST such run where a
    profile touches that height more than once (a flat terrasse at exactly the
    fold's height would otherwise report its own near edge)."""
    run = 0.0
    prev_x, prev_h = profile[0]
    for x, h in profile[1:]:
        if (prev_h - height) * (h - height) <= 0.0 and abs(h - prev_h) > 1e-12:
            run = prev_x + (height - prev_h) / (h - prev_h) * (x - prev_x)
        prev_x, prev_h = x, h
    return run


def _arris_height_at(
    arris: Sequence[tuple[float, float]], run: float
) -> float | None:
    """How high the hip arris stands over the eaves at ``run`` metres in from
    the end of the frontage — ``None`` past the arris's own last point, which
    means the front slope has already reached the ridge and stays there (the
    flat ridge run between the two hip heads), the caller's cue to answer
    ``ridge_h`` instead.

    Pure interpolation over an arris already computed by ``derive_hip_arris``; this
    does not derive the arris itself, so a caller holding one it read off the
    IR (rather than one it just computed) gets the identical answer.
    """
    if not arris or run < 0.0 or run > arris[-1][0]:
        return None
    prev_x, prev_h = arris[0]
    for ax, ah in arris[1:]:
        if run <= ax:
            span = ax - prev_x
            t = (run - prev_x) / span if span > 1e-12 else 1.0
            return prev_h + t * (ah - prev_h)
        prev_x, prev_h = ax, ah
    return arris[-1][1]


def _roof_surface_height_at(
    x: float,
    facade_w: float,
    ridge_h: float,
    ends: str,
    profile: Sequence[tuple[float, float]],
    break_h: float | None = None,
) -> float:
    """How high the roof surface stands over the eaves at ``x`` metres along
    the frontage — the ridge everywhere mid-block, falling away toward a
    hipped return's own arris near the ends (A7.3), including at the exact
    mid-span of a corner parcel too narrow for the hip to ever reach the
    ridge (A9.3: a pavilion peak, not the full ridge height — the previous
    form of this function answered ``ridge_h`` there too, which is the same
    two-independent-opinions defect one function width narrower).

    This is where a souche standing at ``x`` actually emerges. Stating it
    here, once, structurally, is what stops the base of a hip-end stack and
    the roof mass it is meant to stand on from being two independent
    opinions that only happened to agree by construction — which is what the
    renderer computing this same figure for itself, from the same inputs,
    amounted to.
    """
    if ends != "hipped" or facade_w <= _EPS:
        return ridge_h
    arris = derive_hip_arris(facade_w, profile, break_h)
    if not arris:
        return ridge_h
    x0 = max(x, 0.0)
    run = min(x0, facade_w - x0)
    height = _arris_height_at(arris, run)
    return ridge_h if height is None else height


# ---------------------------------------------------------------------------
# terminate
# ---------------------------------------------------------------------------


def terminate(
    grid: Grid,
    roled: RoledGrid,
    site: SiteContext,
    rng: DecisionStream,
) -> tuple[SilhouetteNode, tuple[Node, ...]]:
    """Put the comble on the building and emit it, with its silhouette, as IR.

    Reads the frozen output of the earlier phases and never reaches back into
    them (I1): ``grid`` for the envelope and the built height, ``roled`` for
    the storey stack the comble sits on, ``site`` for date, class and parcel.

    Returns ``(silhouette, others)`` where ``others`` is the comble itself and
    everything standing on it — dormers, cresting, chimney stacks — each a node
    carrying the rules that produced it (I4).
    """
    env = grid.envelope
    eaves = grid.built_height
    facade_w = math.fsum(b.width for b in grid.bays)
    half_depth = max(0.0, site.parcel_depth / 2.0)
    # How tall the comble stands over the eaves it springs from — asked of the
    # grid, which is where the arithmetic and the single cornice-to-eaves
    # conversion live, so the roof this phase cuts and the garret storey phase
    # 1 put inside it cannot disagree by a centimetre. It is NOT
    # `env.ridge_height`: that is a height above the legal cornice, and reading
    # it here as a height above a lower eaves line is what used to throw away
    # the facade's unspent allowance. It is the top of the SAME curve, sprung
    # from these eaves and carried higher (A3.1).
    ridge_h = grid.comble_height
    # The rooms behind the brisis (A8.3): whole *chambres de bonne*, decided
    # once in ``structure._comble_section`` — the same call that sized the
    # garret — and read here rather than re-derived, so the roof and the room
    # inside it cannot disagree about how many storeys of wall there are.
    garret_wall = min(grid.brisis_height, ridge_h)
    # Where the section this phase CUTS folds (A12.1). At or below the wall
    # above — the fold slides down the same gabarit until the terrasson
    # arriving at the ridge in the middle of the plot meets it, because a
    # terrasson that tops out early and leaves 3.69 m of flat zinc behind it
    # is a slab with a nick in it rather than a comble brisé. The ridge does
    # not move: the comble height is the decree's, and Daly's.
    brisis_h, terrasson_reach = _fold_the_terrasson_reaches_the_ridge_from(
        env, half_depth, ridge_h, garret_wall, grid.ridge_setback
    )
    headroom = grid.unused_facade_headroom
    ridge_y = eaves + ridge_h

    # ---- 1. The silhouette: the facade plane, then the envelope ----------
    profile = _comble_profile(env, half_depth, ridge_h, brisis_h, terrasson_reach)
    points: list[tuple[float, float]] = [(0.0, 0.0), (0.0, eaves)]
    for inset, h in profile:
        if h <= _EPS and inset <= _EPS:
            continue  # the eaves point again
        points.append((inset, eaves + h))

    silhouette = Silhouette(tuple(points))

    # A tripwire, not a test: if the phase whose one job is to inscribe the
    # comble in the envelope emits something outside it, that is a bug here
    # and it should stop here, not be discovered by a renderer three stages
    # downstream drawing a roof through the sky.
    #
    # `within` is the right and only test to assert here (A3.1): it is
    # anchored at the built eaves, which is both where this phase springs its
    # comble from and where the règlement springs it. There is no weaker test
    # to fall back on — a comble that needed the cornice anchoring to pass is
    # one the 45° diagonal from its own eaves forbids, and it must stop here.
    if not silhouette.within(env):  # pragma: no cover - tripwire
        raise RuntimeError(
            "the comble this phase built is not inscribed, below the envelope springing "
            "from the eaves it springs from, in the gabarit it was built from (worst "
            f"clearance {silhouette.clearance(env):+.6f} m; measured from the legal "
            f"cornice — which is not the test — it would be "
            f"{silhouette.clearance_from_the_cornice(env):+.6f} m); eaves "
            f"{eaves:.3f} m, ridge {ridge_h:.3f} m above them, envelope "
            f"{env.roof_envelope.value} r={env.arc_radius:.3f} m"
        )

    # The renderer must not have to decide how the comble closes at the ends,
    # so it is decided here, from the site, and handed over as data.
    ends = "hipped" if site.corner else "party_wall"

    # A8.3: measured off the section this phase just built, NOT asked of the
    # envelope. `env.mansard_angles(ridge_h)` describes the legal maximum, and
    # for every pre-1884 building that description is 45°/45°/100% — no break —
    # which the renderer faithfully drew.
    lower_angle, upper_angle, break_pct = _mansard_angles_of(profile, brisis_h, ridge_h)
    # A19.1: the fold's height over the eaves, resolved ONCE here from the
    # stated break, and handed to everything that needs to know where the roof
    # changes plane — the hip arris, the surface a souche stands on, and the
    # test that a lucarne is not standing where the surface has fallen below
    # its own head. Stated rather than re-derived per caller, which is the
    # defect A9.3 removed from this same geometry one level up.
    fold_h = (
        ridge_h * float(break_pct)
        if abs(float(lower_angle) - float(upper_angle)) > 1.0 and float(break_pct) < 0.995
        else None
    )
    # How far back the ridge stands — the terrasson's own far end, decided
    # with the fold it leaves (A12.1) so the two cannot disagree. NOT
    # ``profile[-1]``: the polyline runs on past it wherever a flat terrasse
    # closes the plot, which is now only where the plot is deep enough to have
    # earned one.
    ridge_inset = terrasson_reach
    brisis_inset = env.setback_at(brisis_h)

    silhouette_trace = (
        TraceEntry(
            rule="paris.terminate.silhouette.traced_from_the_gabarit",
            phase="termination",
            detail=(
                f"section through the building on a plane perpendicular to the street: "
                f"pavement to eaves at {eaves:.3f} m up the facade plane, then the brisis "
                f"ON the {env.roof_envelope.value} envelope to the fold {brisis_h:.3f} m "
                f"above the eaves, then the terrasson to a ridge {ridge_h:.3f} m above "
                f"them and {ridge_inset:.3f} m back from the facade — {len(points)} "
                f"point(s). The brisis is not chosen: it is the boundary of the legal "
                f"solid, sampled, because a builder takes every centimetre of garret "
                f"floor the law allows. What stands above it IS chosen — it is a roof, "
                f"not an envelope (A8.3) — and it is inscribed inside the same boundary."
            ),
            inputs={
                "eaves_height": round(eaves, 6),
                "brisis_height_above_eaves": round(brisis_h, 6),
                "ridge_height_above_eaves": round(ridge_h, 6),
                "envelope": env.roof_envelope.value,
                "arc_radius": round(env.arc_radius, 6),
                "legal_facade_height": env.facade_height,
                "legal_ridge_height": env.legal_ridge_height,
                "clearance_to_envelope": round(silhouette.clearance(env), 6),
                "clearance_from_the_cornice": round(
                    silhouette.clearance_from_the_cornice(env), 6
                ),
            },
        ),
        TraceEntry(
            rule="paris.terminate.silhouette.the_fold_is_where_the_terrasson_reaches_the_ridge",
            phase="termination",
            detail=(
                f"the fold is at {brisis_h:.3f} m over the eaves, "
                f"{brisis_h / ridge_h if ridge_h > _EPS else 1.0:.1%} of the comble, and "
                f"{brisis_inset:.3f} m back from the facade — where the terrasson, "
                f"arriving at the ridge {ridge_inset:.3f} m back, meets the "
                f"{env.roof_envelope.value} envelope on its way down (A12.1). It is NOT "
                f"the {garret_wall:.3f} m the garret's own wall stands: that number is a "
                f"count of whole chambres de bonne and it puts the fold within "
                f"{ridge_h - garret_wall:.3f} m of the ridge, leaving a hairline "
                f"terrasson and a flat deck across the rest of the plot — a slab with a "
                f"nick near the top rather than a comble brisé. The section is "
                f"over-determined once the terrasson's pitch is fixed, so the SAME three "
                f"numbers are read as a terrasson running the whole way to the ridge and "
                f"a fold wherever that line crosses the gabarit. The ridge did not move "
                f"({ridge_h:.3f} m, the decree's and the measured plates'); only the fold "
                f"did, and it slid down the envelope, so it is still a point "
                f"setback_at returned."
            ),
            inputs={
                "fold_above_eaves": round(brisis_h, 6),
                "fold_inset": round(brisis_inset, 6),
                "garret_wall_above_eaves": round(garret_wall, 6),
                "ridge_above_eaves": round(ridge_h, 6),
                "ridge_inset": round(ridge_inset, 6),
                "half_depth": round(half_depth, 6),
                "flat_terrasse_depth": round(max(0.0, half_depth - ridge_inset), 6),
                "shortest_brisis_that_carries_a_lucarne": round(
                    _shortest_brisis_that_carries_a_lucarne(float(_dormer_skirt())), 6
                ),
            },
        ),
        TraceEntry(
            rule="paris.terminate.silhouette.springs_from_the_built_eaves",
            phase="termination",
            detail=(
                f"the comble springs from the eaves the building actually has "
                f"({eaves:.3f} m, the sum of its storeys), not from the legal cornice "
                f"ceiling ({env.facade_height:.2f} m) — the diagonal springs from the "
                f"égout du toit, so a building that stopped short of its ceiling carries "
                f"the whole roof SHAPE down with it. Its CEILING does not come down with "
                f"it: {headroom:.3f} m of cornice height went unbuilt, and that is legal "
                f"space the building declined to occupy rather than space it forfeited, "
                f"so the SAME curve is traced to a taller top and the comble MAY stand "
                f"{grid.comble_ceiling:.3f} m over these eaves — "
                f"{grid.comble_ceiling - env.ridge_height:.3f} m more than the "
                f"{env.ridge_height:.3f} m the ridge stands over the cornice — on a "
                f"parcel with {half_depth:.3f} m to give. The springing did not move; "
                f"only the top did (A3.1). It does NOT stand there: a ceiling is not a "
                f"height, and building to it made the roof grow by exactly what the "
                f"stone gave up, so every immeuble in Paris came out at its legal total "
                f"(A8.5). What was built is {ridge_h:.3f} m — the garret storeys behind "
                f"the brisis and the terrasson closing over them — set back "
                f"{ridge_inset:.3f} m, leaving {grid.comble_ceiling - ridge_h:.3f} m of "
                f"legal volume nobody had a use for. This silhouette is inscribed below "
                f"the envelope sprung from "
                f"its own eaves (worst margin {silhouette.clearance(env):+.3f} m); "
                f"measured from the legal cornice — the weaker line, which is not the "
                f"test — it would be "
                f"{silhouette.clearance_from_the_cornice(env):+.3f} m. A margin of "
                f"exactly zero is the facade standing on the street line, which is where "
                f"a Paris facade stands."
            ),
            inputs={
                "built_height": round(eaves, 6),
                "legal_cornice_ceiling": float(grid.cornice_height),
                "cornice_citation": grid.cornice_height.why,
                "unused_facade_headroom": round(headroom, 6),
                "comble_height_over_the_eaves": round(ridge_h, 6),
                "ridge_height_above_the_cornice": round(env.ridge_height, 6),
                "legal_total_height": round(env.total_height, 6),
            },
        ),
        TraceEntry(
            rule="paris.terminate.silhouette.ends",
            phase="termination",
            detail=(
                f"ends {ends!r}: a corner building's comble is hipped and shows this "
                f"profile at its returns; a mid-block one runs straight between party "
                f"walls. Decided here so the renderer decides nothing."
            ),
            inputs={"corner": site.corner},
        ),
    )

    silhouette_node = SilhouetteNode(
        id="b/silhouette",
        kind="silhouette",
        trace=silhouette_trace,
        props={
            # Extent, in this node's own plane: depth back from the facade
            # plane and height above the pavement. The plane is named in
            # `axes` rather than assumed, because it is NOT the facade frame
            # the storey and bay nodes live in.
            "x": 0.0,
            "y": 0.0,
            "w": max(inset for inset, _ in points),
            "h": silhouette.ridge_height,
            "plane": "section_perpendicular_to_street",
            "axes": ("inset_from_facade_plane_m", "height_above_pavement_m"),
            "points": silhouette.points,
            "eaves_height": eaves,
            "ridge_height": silhouette.ridge_height,
            "facade_width": facade_w,
            "ends": ends,
            "envelope": env.roof_envelope.value,
        },
    )

    others: list[Node] = []

    # ---- 2. The comble: geometry from the decree, dress from the date ------
    #
    # The geometry is already decided and this phase had no say in it — it is
    # `env.roof_envelope`, a step on 1884 and 1902, no class lag. What is drawn
    # below is the dormer-and-ornament repertoire and the covering material,
    # both of them fashion: ramped, class-lagged, retained late by modest
    # builders. The two axes must not be able to contradict each other, which
    # is what `_geometry_claimed_by` is checking (A2.5).
    repertoire_options = [
        (v, w)
        for v, w in chronology.available("roof", site.year, site.klass)
        if v.name in DORMER_ORNAMENT_VARIANTS
    ]
    material_options = [
        (v, w)
        for v, w in chronology.available("roof", site.year, site.klass)
        if v.name in ROOF_MATERIAL_VARIANTS
    ]

    if repertoire_options:
        dormer_variant = rng.choice(
            "roof/dormers/variant",
            [v.name for v, _ in repertoire_options],
            [w for _, w in repertoire_options],
        )
        repertoire_detail = (
            "dormer-and-ornament repertoire drawn from the variants genuinely in use "
            f"at {site.year} for a {site.klass.value} building: "
            + ", ".join(f"{v.name} {w:.0%}" for v, w in repertoire_options)
            + f". The comble under them is a {env.roof_envelope.value} because the "
            "decree says so, which is a different kind of fact and is not on this axis"
        )
    else:
        # No opinion rather than a default: a date the catalogue cannot dress.
        dormer_variant = None
        repertoire_detail = (
            f"the roof catalogue offers no dormer repertoire in use at {site.year} for "
            f"a {site.klass.value} building — the comble is emitted bare rather than "
            "given a variant its date cannot support"
        )

    # A2.5, literally: whatever fashion returned, it may not contradict the
    # decree. Unreachable while `_check_no_geometry_on_the_fashion_axis` holds
    # at import — a name with no geometry in it cannot claim the wrong one —
    # and that is the arrangement being asserted, not a reason to assume it.
    claimed = _geometry_claimed_by(dormer_variant) if dormer_variant else frozenset()
    if claimed and env.roof_envelope not in claimed:  # pragma: no cover - tripwire
        raise RuntimeError(
            f"the dormer repertoire drawn for {site.year} / {site.klass.value} is named "
            f"{dormer_variant!r}, which claims a {sorted(e.value for e in claimed)} "
            f"comble, but the decree in force gives this building a "
            f"{env.roof_envelope.value} one. Comble geometry is legality and arrives on "
            "the decree date; a repertoire is fashion and lags by class, so the two "
            "genuinely can be out of step — an arc comble carrying old-fashioned "
            "lucarnes is the common case, not an error. What is an error is a fashion "
            "variant asserting a geometry at all."
        )

    repertoire = DORMER_ORNAMENT_VARIANTS.get(dormer_variant) if dormer_variant else None

    zinc_weight = material_options[0][1] if material_options else 0.0
    material = rng.choice(
        "roof/material",
        [material_options[0][0].name if material_options else _DEFAULT_ROOF_MATERIAL,
         _DEFAULT_ROOF_MATERIAL],
        [zinc_weight, 1.0 - zinc_weight],
    )

    # The observation-date channel, wired even though nothing yet feeds it:
    # `SiteContext` carries only the construction year, so the comble is dated
    # to the building. When a block or a corpus later supplies an observation
    # year, `raised_comble` is where the Rue de Rivoli case (cornice held, roof
    # heightened afterwards) enters, and every draw above already reads a year
    # rather than a period.
    roof_date = chronology.raised_comble(site.year, site.year)

    roof_trace = (
        TraceEntry(
            rule="paris.terminate.comble.inscribed_in_the_gabarit",
            phase="termination",
            detail=(
                f"comble inscribed in the {env.roof_envelope.value} envelope: "
                f"{ridge_h:.3f} m tall over eaves at {eaves:.3f} m — the top of the legal "
                f"solid ({env.total_height:.3f} m) reckoned from those eaves, capped by the "
                f"parcel where its two slopes meet — ridge set back "
                f"{ridge_inset:.3f} m, approximated as a broken mansard of "
                f"{lower_angle:.1f}° / {upper_angle:.1f}° breaking at {break_pct:.0%} of "
                f"its height. Nobody chose the angle — it is the boundary of the legal "
                f"solid for a {env.street_width:.2f} m street."
            ),
            inputs={
                "envelope": env.roof_envelope.value,
                "arc_radius": round(env.arc_radius, 6),
                "ridge_height": round(ridge_h, 6),
                "ridge_height_above_the_cornice": round(env.ridge_height, 6),
                "unused_facade_headroom": round(headroom, 6),
                "legal_ridge_height": env.legal_ridge_height,
                "parcel_depth": site.parcel_depth,
            },
        ),
        TraceEntry(
            rule="paris.terminate.roof.dormer_repertoire_of_its_date",
            phase="termination",
            detail=repertoire_detail,
            inputs={
                "year": site.year,
                "klass": site.klass.value,
                "chosen": dormer_variant,
                "source": repertoire.source if repertoire else "",
                "envelope_from_the_decree": env.roof_envelope.value,
            },
        ),
        TraceEntry(
            rule="paris.terminate.roof.geometry_is_not_on_the_fashion_axis",
            phase="termination",
            detail=(
                f"the comble is a {env.roof_envelope.value} because the decree in force "
                f"says so, and for no other reason: geometry is a step on the decree "
                f"date and carries no class lag, while {dormer_variant!r} is fashion and "
                f"does. The two are free to be out of step — a lagged builder fitting "
                f"pedimented lucarnes to an arc comble is the straggler the brief calls "
                f"the common case — and neither may be inferred from the other, so no "
                f"variant on the fashion axis is allowed to name a comble geometry."
            ),
            inputs={
                "envelope": env.roof_envelope.value,
                "geometry_claimed_by_the_variant": sorted(e.value for e in claimed),
            },
        ),
        TraceEntry(
            rule="paris.terminate.roof.material_of_its_date",
            phase="termination",
            detail=(
                f"covering {material!r}: zinc stood at {zinc_weight:.0%} prevalence at "
                f"{site.year} for a {site.klass.value} building, and the material axis is "
                "drawn separately from the dormer axis because a zinc roof and a "
                "pedimented dormer are not alternatives"
            ),
            inputs={"zinc_prevalence": round(zinc_weight, 4), "year": site.year},
        ),
    )

    # A9.3: the hip's own arris, computed once, here, from the profile this
    # phase already built — the same structural fact `_roof_surface_height_at`
    # uses below to place every souche, now also carried on the roof node's
    # own props so the renderer draws exactly this shape instead of deriving
    # its own from the profile a second time. Empty mid-block: there is no
    # return to trace and the front slope is the ridge everywhere.
    hip_arris = derive_hip_arris(facade_w, profile, fold_h) if ends == "hipped" else ()

    roof_node = RoofNode(
        id="b/roof",
        kind="roof",
        trace=roof_trace,
        props={
            "x": 0.0,
            "y": eaves,
            "w": facade_w,
            "h": ridge_h,
            "eaves_height": eaves,
            "ridge_height": ridge_y,
            "ridge_setback": ridge_inset,
            "envelope": env.roof_envelope.value,
            "arc_radius": env.arc_radius,
            "lower_angle_deg": lower_angle,
            "upper_angle_deg": upper_angle,
            "break_pct": break_pct,
            "profile": profile,
            # A9.3: the ONE derivation of the hip arris — see the module-level
            # comment above `derive_hip_arris`. The renderer reads this rather than
            # recomputing it from `profile`, which is what let it and this
            # phase disagree by up to 1.559 m.
            "hip_arris": hip_arris,
            # A flat zinc deck between the two opposing slopes, closing the
            # plot beyond where the terrasson topped out. Unchanged in meaning
            # since A8.3 and still read off the ridge's own setback — but that
            # setback is now the terrasson's far end rather than the whole
            # comble's, so this answers a question about the deck instead of
            # one about the gabarit.
            "has_terrasse": bool(half_depth > ridge_inset + 1e-6),
            "dormer_variant": dormer_variant,
            "material": material,
            # A7.2: how many seams run down this slope. The interval is the
            # covering's own — a zinc table is as wide as the works rolled it
            # and no owner's ambition made the sheet wider, so
            # ``catalogue.roof_seam_module`` states it as ABSOLUTE — and the
            # count is that interval taken across THIS roof's width. The
            # renderer used to hold both numbers itself and divide the facade
            # by whichever the material picked.
            "seam_count": catalogue.repeats_across(
                facade_w, float(catalogue.roof_seam_module(material)), minimum=4
            ),
            "ends": ends,
            "built_year": roof_date.building_year,
            "observed_year": roof_date.observed,
            "altered": roof_date.altered,
        },
    )
    others.append(roof_node)

    # ---- 3. Dormers, one per bay of the storey they light, one row per band -
    #
    # A lucarne is a window, and a window belongs to a room. Where the comble
    # is deep enough to hold one, `structure.py` puts a habitable storey inside
    # it and `roles.py` calls it the ATTIC — the chambres de bonne — and these
    # are its windows. So the grid is taken from `roled`, whose attic storey
    # fills the one shared bay solve like every other storey, rather than
    # decided here from `grid.bays` as though the roofscape had a rhythm of its
    # own (A2.1). Where there is no attic storey the comble is a garret and the
    # lucarnes light a roof void instead; same grid, different room, and the
    # trace says which.
    #
    # **A8.3.** How many ROWS is not a decision either: the brisis rises in
    # whole ``BRISIS_RISE`` bands, one per storey of rooms behind it
    # (``structure._comble_section``), and each band is one room's outside wall
    # with one row of windows in it. Measured against the combles this system
    # builds, a single row put the lucarnes in the lowest fifth of the slope
    # with bare zinc filling the whole plane above them — a warehouse roof.
    # Under a 45° gabarit the brisis is one band and this reduces to exactly
    # the row it always emitted; under an 1884 or 1902 arc it is two or three,
    # which is what those decrees were for and what their roofs look like.
    #
    # **A12.1.** The count is taken from ``garret_wall`` — the rooms — and not
    # from the fold this phase cut, because the rooms did not move when the
    # fold slid down the gabarit. Whether each of those rows actually fits
    # *under* the fold is a separate question and the loop below asks it, one
    # row at a time, against ``brisis_h``: a row with no brisis left to stand
    # in is not drawn, which is the same test that has always stopped a row
    # from overhanging the terrasson.
    skirt_q = _dormer_skirt()
    skirt = float(skirt_q)
    # A8.3: the lucarne fills the band of brisis it stands in, so its face is a
    # question about THIS roof's section rather than a constant — and A12.1:
    # the section's own fold, so a shorter brisis carries a shorter lucarne
    # instead of the same one overhanging the fold.
    # A15.1: asked of the band this row stands in rather than of the whole
    # brisis, because a comble standing two bands has a full band under its
    # upper row and whatever the fold left above it — and a face measured off
    # the whole brisis is the same window drawn twice at two heights. On a
    # one-band comble, and on every row with a whole band above its foot, this
    # is exactly the number the single call used to give.
    face_q = _dormer_face_height(brisis_h, skirt)
    face = float(face_q)
    dormer_top = skirt + face
    band = float(BRISIS_RISE)
    rows = max(1, int(garret_wall / band + _EPS)) if band > 0.0 else 1

    attic = _attic_storey(roled)
    attics = roled.attic_storeys

    def _lights(row: int) -> str:
        """Whose room the lucarnes in this row are the windows of.

        **A15.1.** S3 now divides the comble into one storey per band of
        brisis, so a second row of lucarnes names the second room instead of
        saying that the room behind it is not modelled. Where a band has no
        storey — a roof standing more bands than the plot holds rooms in — the
        honest answer is still the band, and it is not the same answer as
        "there is no habitable storey at all".
        """
        if row < len(attics):
            st = attics[row]
            return (
                f"the attic storey at index {st.index_from_bottom} "
                f"({st.slot.width:.2f} m clear, its floor at {st.slot.start:.2f} m)"
            )
        if not attics:
            return "the garret — this comble holds no habitable storey"
        return "a band of the comble the plot has no room's depth of floor behind"

    bays = _bay_slots(roled)
    if repertoire is not None and bays and dormer_top <= ridge_h + _EPS:
        dormer_w = min(
            float(scale_for_class(Prop(1.05, "a lucarne reads narrower than the bay below it"), site.klass)),
            max(b.width * 0.6 for _, b in bays),
        )
        n = -1
        for row in range(rows):
            foot = row * band
            face_q = _dormer_face_height(brisis_h - foot, skirt)
            face = float(face_q)
            dormer_top = skirt + face
            if foot + dormer_top > brisis_h + _EPS:
                break  # the band above this one is not a whole room
            # As far forward as the law lets it stand at its own highest point.
            # Not a style decision: a lucarne set back further wastes the
            # comble's only usable floor area, and one set forward of this
            # breaks the plane the decree draws. Each row asks it at its OWN
            # head, so the rows step back up the slope the way the slope does.
            dormer_inset = env.setback_at(foot + dormer_top)
            for slot_index, slot in bays:
                n += 1
                centre = slot.start + slot.width / 2.0
                # A9.3: on a hipped corner the roof surface falls away toward
                # the returns — the same structural fact that places every
                # souche (`_roof_surface_height_at`) says whether the tiles
                # under THIS bay still stand as tall as the dormer's own head
                # needs. Skipping it here is what stops an end lucarne from
                # overhanging the hip into the sky (measured: a 2.65 m head
                # over eaves standing over a return whose surface has already
                # fallen to 1.12-2.45 m) — mid-block, or anywhere still
                # inside a hipped return's own flat ridge run, this is
                # `ridge_h` and the check never fires.
                local_surface = _roof_surface_height_at(
                    centre, facade_w, ridge_h, ends, profile, fold_h
                )
                if foot + dormer_top > local_surface + _EPS:
                    others.append(
                        SpecialNode(
                            id=f"b/roof/no_dormer{n}",
                            kind="special",
                            trace=(
                                TraceEntry(
                                    rule="paris.terminate.dormer.clipped_by_the_hip",
                                    phase="termination",
                                    detail=(
                                        f"no lucarne over bay {slot_index} in row "
                                        f"{row + 1} of {rows}: it needs a head of "
                                        f"{foot + dormer_top:.3f} m over the eaves, but "
                                        f"the roof surface at this bay's own centre "
                                        f"({centre:.3f} m along the frontage) has "
                                        f"already fallen to {local_surface:.3f} m on the "
                                        "hip return. A dormer built to the mid-block "
                                        "height here would stand clear of the tiles "
                                        "that are actually there, over the sky beyond "
                                        "the hip's own arris."
                                    ),
                                    inputs={
                                        "bay_index": slot_index,
                                        "row": row,
                                        "head_above_eaves": round(foot + dormer_top, 6),
                                        "local_surface": round(local_surface, 6),
                                    },
                                ),
                            ),
                            props={
                                # A10.5: the marker's extent is the domain the
                                # absence is a fact about — this bay — the
                                # same convention `b/roof/no_dormers` already
                                # uses for the whole facade below (`w`:
                                # `facade_w`, not some hypothetical dormer's
                                # width). "No dormer over 0 m of frontage" is
                                # not a fact; "no dormer over this bay" is,
                                # and the bay has a width.
                                "x": slot.start,
                                "y": eaves + local_surface,
                                "w": slot.width,
                                "h": 0.0,
                                "absence": "dormer",
                            },
                        )
                    )
                    continue
                width = min(dormer_w, slot.width * 0.75)

                # A19.2 — the lowest garret's openings are in the WALL.
                #
                # A brisis steep enough to carry two storeys is a wall that
                # happens to be roof, and both deep-comble plates in the corpus
                # build and face it as one: at 2 et 4 bd de Sébastopol the
                # brisis is brick, carrying a full storey of moulded surrounds
                # with individual balconettes and, above them, a row of small
                # plain lights under the eaves — no dormer projects anywhere on
                # that plate. At 1 bd de Sébastopol the brisis is faced in
                # vertical-seamed metal and only the UPPER row is a true
                # lucarne; the lower row is again windows set in the face.
                #
                # So the register under the eaves is the lucarne, and every row
                # below it is a window in the slope. On a one-band comble —
                # which is the majority — `rows` is 1, this row IS the register
                # under the eaves, and nothing here changes.
                if row < rows - 1:
                    others.append(
                        BrisisWindowNode(
                            id=f"b/roof/brisis_window{n}",
                            kind="brisis_window",
                            trace=(
                                TraceEntry(
                                    rule="paris.terminate.brisis.window_in_the_face",
                                    phase="termination",
                                    detail=(
                                        f"window {n} in the brisis face lights "
                                        f"{_lights(row)}, over bay {slot_index} "
                                        f"({slot.width:.3f} m wide, centred at "
                                        f"{slot.start + slot.width / 2:.3f} m), in row "
                                        f"{row + 1} of {rows}. Not a lucarne: this comble "
                                        f"stands {rows} bands of brisis, so the row under "
                                        "the eaves is the lucarne and every row below it "
                                        "is a window in the slope's own face (A19.2). A "
                                        "brisis carrying two storeys is a wall that "
                                        "happens to be roof, and Daly's two deep combles "
                                        "both build it as one — brick at 2 et 4 bd de "
                                        "Sébastopol, seamed metal at 1 bd."
                                    ),
                                    inputs={
                                        "bay_index": slot_index,
                                        "row": row,
                                        "rows": rows,
                                        "lights_storey_index": (
                                            attics[row].index_from_bottom
                                            if row < len(attics)
                                            else None
                                        ),
                                    },
                                ),
                            ),
                            props={
                                "x": slot.start + (slot.width - width) / 2.0,
                                "y": eaves + foot + skirt,
                                "w": width,
                                "h": face,
                                # Flush with the slope: how far the roof plane
                                # itself has set back at this window's own head,
                                # so a consumer places it ON the brisis rather
                                # than guessing an offset. The SAME
                                # `env.setback_at` a lucarne's inset reads.
                                "setback": dormer_inset,
                                "garde_corps": True,
                                # How many bars the railing across this light
                                # is made of. Decided HERE, from the same
                                # ABSOLUTE a balustrade's gap has always been
                                # measured against — a child's head — because
                                # a count derived in the renderer from a
                                # spacing chosen in the renderer is the
                                # renderer deciding, which the guard forbids
                                # and which would put a second opinion about
                                # this railing next to the first.
                                "bar_count": catalogue.repeats_across(
                                    width, float(catalogue.balustrade_child_gap_max())
                                ),
                            },
                        )
                    )
                    continue

                form = rng.choice(
                    f"roof/dormer/{n}/form",
                    list(repertoire.dormer_forms),
                )
                others.append(
                    DormerNode(
                        id=f"b/roof/dormer{n}",
                        kind="dormer",
                        trace=(
                            TraceEntry(
                                rule="paris.terminate.dormer.one_per_bay_of_the_storey_it_lights",
                                phase="termination",
                                detail=(
                                    f"lucarne {n} lights "
                                    f"{_lights(row)}, and stands "
                                    f"over that storey's "
                                    f"horizontal slot {slot_index} (a bay, {slot.width:.3f} m "
                                    f"wide, centred at {slot.start + slot.width / 2:.3f} m), "
                                    f"in row {row + 1} of {rows} — one row for each "
                                    f"{band:.2f} m band of brisis, because each band is one "
                                    f"room's outside wall. The count and the spacing are the "
                                    "storey's, not the roofscape's: a storey never lays out, "
                                    "it fills the one shared bay grid, so the windows in the "
                                    "roof line up with the windows below them by "
                                    "construction. End piers and inserted specials carry none."
                                ),
                                inputs={
                                    "bay_index": slot_index,
                                    "bay_start": round(slot.start, 6),
                                    "bay_width": round(slot.width, 6),
                                    "row": row,
                                    "rows": rows,
                                    "lights_storey_index": (
                                        attics[row].index_from_bottom
                                        if row < len(attics)
                                        else None
                                    ),
                                },
                            ),
                            TraceEntry(
                                rule="paris.terminate.dormer.tangent_to_the_envelope",
                                phase="termination",
                                detail=(
                                    f"face set back {dormer_inset:.3f} m — exactly "
                                    f"setback_at({foot + dormer_top:.3f} m) for the "
                                    f"{env.roof_envelope.value} envelope, i.e. as far forward as "
                                    f"the gabarit permits at the dormer's own head. Face "
                                    f"{face:.2f} m ({face_q.why}) over a {skirt:.2f} m skirt "
                                    f"({skirt_q.why}), standing on the band whose foot is "
                                    f"{foot:.2f} m over the eaves."
                                ),
                                inputs={
                                    "head_above_eaves": round(foot + dormer_top, 6),
                                    "setback": round(dormer_inset, 6),
                                    "face_height": face_q,
                                    "skirt": skirt_q,
                                },
                            ),
                            TraceEntry(
                                rule="paris.terminate.dormer.form_from_the_fashion_repertoire",
                                phase="termination",
                                detail=(
                                    f"form {form!r}, drawn from the {dormer_variant!r} "
                                    f"repertoire's own forms {repertoire.dormer_forms} — "
                                    f"{repertoire.source}. Form is fashion; the "
                                    f"{env.roof_envelope.value} comble it stands on is not."
                                ),
                                inputs={
                                    "repertoire": dormer_variant,
                                    "forms_offered": repertoire.dormer_forms,
                                },
                            ),
                        ),
                        props={
                            "x": slot.start + slot.width / 2.0 - width / 2.0,
                            "y": eaves + foot + skirt,
                            "w": width,
                            "h": face,
                            "form": form,
                            "setback": dormer_inset,
                            "bay_index": slot_index,
                            "lights_storey_index": (
                                attics[row].index_from_bottom
                                if row < len(attics)
                                else None
                            ),
                        },
                    )
                )
    else:
        # Why there are none is as much a result as where they are.
        reason = (
            "no dormer repertoire for this date, so no lucarne forms to draw from"
            if repertoire is None
            else (
                f"the comble is {ridge_h:.3f} m tall and a lucarne needs {dormer_top:.3f} m "
                f"(a {skirt:.2f} m skirt under a {face:.2f} m face) — it will not fit"
                if bays
                else "the facade has no repeating bay for a lucarne to stand over"
            )
        )
        others.append(
            SpecialNode(
                id="b/roof/no_dormers",
                kind="special",
                trace=(
                    TraceEntry(
                        rule="paris.terminate.dormer.none",
                        phase="termination",
                        detail=reason,
                        inputs={
                            "ridge_height": round(ridge_h, 6),
                            "dormer_head_required": round(dormer_top, 6),
                            "bay_count": len(bays),
                            "lights_storey_index": (
                                attic.index_from_bottom if attic is not None else None
                            ),
                        },
                    ),
                ),
                props={
                    "x": 0.0,
                    "y": eaves,
                    "w": facade_w,
                    "h": 0.0,
                    "absence": "dormer",
                },
            )
        )

    # ---- 4. Cresting — a property of the repertoire, never of a period -----
    if repertoire is not None and repertoire.cresting:
        crest_q = _cresting_height(site.klass)
        iron_options = chronology.available("ironwork", site.year, site.klass)
        crest_variant = (
            rng.choice(
                "roof/cresting/variant",
                [v.name for v, _ in iron_options],
                [w for _, w in iron_options],
            )
            if iron_options
            else None
        )
        others.append(
            IronworkNode(
                id="b/roof/cresting",
                kind="ironwork",
                trace=(
                    TraceEntry(
                        rule="paris.terminate.cresting.belongs_to_the_repertoire",
                        phase="termination",
                        detail=(
                            f"iron cresting along the ridge: the {dormer_variant!r} "
                            f"repertoire carries it — {repertoire.source}. Presence is a "
                            "fact about the variant, not about the year; the year only "
                            "decided which variant."
                        ),
                        inputs={"repertoire": dormer_variant},
                    ),
                    TraceEntry(
                        rule="paris.terminate.cresting.ironwork_of_its_date",
                        phase="termination",
                        detail=(
                            f"pattern {crest_variant!r}, drawn from the ironwork in use at "
                            f"{site.year} for a {site.klass.value} building — the roof's "
                            "smith is the facade's smith"
                        ),
                        inputs={
                            "year": site.year,
                            "offered": tuple(v.name for v, _ in iron_options),
                        },
                    ),
                ),
                props={
                    "x": 0.0,
                    "y": ridge_y,
                    "w": facade_w,
                    "h": float(crest_q),
                    # A4.3: named for what it is (the renderer's guard forbids
                    # branching on a raw "variant" key — see compose.py's
                    # ironwork/shopfront props for the same rename).
                    "ironwork_pattern": crest_variant,
                    "position": "ridge",
                    "height_why": crest_q.why,
                    # A7.2: how many uprights stand along this ridge. Cresting
                    # guards nobody, so it has no ABSOLUTE gap to honour the
                    # way a garde-corps does — its rhythm is ornament and
                    # nothing else, and the renderer used to divide the ridge
                    # by a spacing of its own to get it. The module is the
                    # catalogue's; the count is that module taken across THIS
                    # ridge. Cresting is only ever present at all on the rich
                    # repertoire, so its presence already carries the ambition
                    # its spacing would otherwise have to.
                    "ornament_count": catalogue.repeats_across(
                        facade_w, float(catalogue.cresting_module()), minimum=4
                    ),
                },
            )
        )

    # ---- 5. Chimney stacks, gathered at the piers -------------------------
    souche_w = float(_souche_width(site.klass))
    visible_q = _souche_visible_height()
    visible_h = float(visible_q)
    # A4.4. Where the stack EMERGES, which is not where it starts.
    #
    # A souche is masonry from the cellar up; the part of it there is anything
    # to draw is the part standing clear of the roof. Emitting `y = eaves` and
    # `h = ridge - eaves` gave the stack's full section extent, so every
    # consumer faithfully drew a full-height bar down the face of the comble.
    # That is not a rendering bug: the IR was stating a section as if it were
    # an elevation.
    #
    # A7.3: where it emerges is the roof SURFACE at this stack's own x, which
    # is the ridge everywhere mid-block (there is nowhere for it to fall away
    # to — the front slope is one flat band the whole frontage wide) but
    # falls toward the eaves near a hipped return's own ends. That surface is
    # a structural fact about the comble this phase already built, computed
    # once here (`_roof_surface_height_at`) rather than left for the renderer
    # to recompute from the same inputs and risk a second opinion. What is
    # visible above it is `_souche_visible_height`: roughly constant brick
    # showing above the tiles, not an absolute head height held at the ridge
    # regardless of how far below it the base has fallen — which is what
    # turned a hip-end souche into a 12 m smokestack the first time this was
    # fixed only at the renderer.
    #
    # A flue serves one fireplace per storey in one vertical stack of rooms,
    # and the flues of a stack of rooms rise together inside the masonry that
    # is already there: the party walls at the two ends, and the piers between
    # bays. So the souches stand on the joints of the bay grid, not on a
    # spacing invented for the roofscape.
    # The joints are the piers between REPEATING bays. The entrance's slot is
    # in ``bays`` because the comble over it carries a lucarne like any other
    # column (A8.3), but a carriage arch is a hole in the masonry rather than a
    # pier with flues in it, so the chimney grid is unchanged by that.
    piers = [(i, b) for i, b in bays if b.name == "bay"]
    joints: list[tuple[float, str]] = [(0.0, "party wall"), (facade_w, "party wall")]
    for (_, left), (_, right) in zip(piers, piers[1:]):
        joints.append(((left.start + left.width + right.start) / 2.0, "pier between bays"))
    joints.sort()

    flues_each = max(1, len(roled.storeys) - 1)
    for n, (x, where) in enumerate(joints):
        # A souche on a party wall straddles the boundary: half of its mass is
        # the neighbour's, built against ours. Until the block phase can pair
        # the two halves, this building emits only its own — so a party-wall
        # souche is half-width and flush inside the parcel, and nothing here
        # draws geometry on land it does not own.
        shared = where == "party wall"
        width = souche_w / 2.0 if shared else souche_w
        left = min(max(x - width / 2.0, 0.0), max(facade_w - width, 0.0))
        centre = left + width / 2.0
        # A7.3: the surface THIS stack actually stands on, not the ridge held
        # regardless of where along the frontage the stack sits. Mid-block —
        # or anywhere on a hipped frontage still inside the flat ridge run —
        # this is the ridge exactly as A4.4 had it; only near a hipped
        # return's own ends does it fall.
        surface_h = _roof_surface_height_at(
            centre, facade_w, ridge_h, ends, profile, fold_h
        )
        souche_base = eaves + surface_h
        souche_top = souche_base + visible_h
        souche_hidden = max(0.0, souche_base - eaves)
        emerges_from = "ridge" if surface_h >= ridge_h - 1e-6 else "hip return"
        others.append(
            SpecialNode(
                id=f"b/roof/souche{n}",
                kind="special",
                trace=(
                    TraceEntry(
                        rule="paris.terminate.chimney.flues_gather_in_the_masonry",
                        phase="termination",
                        detail=(
                            f"souche {n} on the {where} at x={x:.3f} m, gathering roughly "
                            f"{flues_each} flue(s) — one fireplace per storey above the "
                            f"ground floor in the room-stack below it. The flues rise "
                            f"inside masonry the building already has, so the souches "
                            f"stand on the joints of the same bay grid as everything else."
                            + (
                                " Half-width and flush inside the parcel: the other half "
                                "of a party-wall souche is the neighbour's, and pairing "
                                "the two is the block's job, not this building's."
                                if shared
                                else ""
                            )
                        ),
                        inputs={
                            "x": round(x, 6),
                            "position": where,
                            "shared_with_neighbour": shared,
                            "storeys": len(roled.storeys),
                        },
                    ),
                    TraceEntry(
                        rule="paris.terminate.chimney.emerges_from_the_roof_surface_beneath_it",
                        phase="termination",
                        detail=(
                            f"emerges from the {emerges_from} at {souche_base:.3f} m — "
                            f"{surface_h:.3f} m over the eaves at {centre:.3f} m along the "
                            f"frontage. A7.3: this is the roof SURFACE at this stack's own x, "
                            "a structural fact about the comble this phase already built "
                            "(`_roof_surface_height_at`), not the ridge held regardless of "
                            "where the stack stands — mid-block, or anywhere still inside a "
                            "hipped return's own flat ridge run, that surface IS the ridge "
                            f"({ridge_y:.3f} m); only near the hip's own ends does it fall "
                            "away toward the eaves, and a souche standing there now emerges "
                            "from the surface actually beneath it rather than floating over "
                            "tiles the return never draws that high."
                        ),
                        inputs={
                            "base_height": round(souche_base, 6),
                            "eaves_height": round(eaves, 6),
                            "ridge_height": round(ridge_y, 6),
                            "hidden_in_the_comble": round(souche_hidden, 6),
                            "emerges_from": emerges_from,
                            "ends": ends,
                        },
                    ),
                    TraceEntry(
                        rule="paris.terminate.chimney.shows_a_constant_height_above_its_surface",
                        phase="termination",
                        detail=(
                            f"head at {souche_top:.3f} m — {visible_h:.2f} m of brick standing "
                            f"clear above the surface it emerges from ({visible_q.why}). "
                            "ABSOLUTE, and held constant ABOVE THE SURFACE rather than as an "
                            "absolute head height measured from the ridge: a souche near a "
                            "hipped return's fully-fallen-away end shows the SAME masonry as "
                            "one standing on the ridge, not a taller stack reaching back up to "
                            "the ridge's own height (A7.3) — the fix that turned a hip-end "
                            "souche into a 12 m smokestack the first time this was corrected "
                            "only at the renderer."
                        ),
                        inputs={"visible_height": visible_q, "base_height": round(souche_base, 6)},
                    ),
                ),
                props={
                    "x": left,
                    "y": souche_base,
                    "w": width,
                    "h": souche_top - souche_base,
                    "element": "chimney_stack",
                    "flues": flues_each,
                    "position": where,
                    "shared_with_neighbour": shared,
                    # The visible base, named, so a consumer never has to
                    # infer it from the roof node — and the part that is not
                    # visible, named too, so nobody reads `h` as the stack's
                    # whole height and adds the difference back.
                    "base_height": souche_base,
                    "head_height": souche_top,
                    "emerges_from": emerges_from,
                    "hidden_in_the_comble": souche_hidden,
                },
            )
        )

    return silhouette_node, tuple(others)
