"""The base vocabulary layer — what a Paris frontage is, before date or money.

Every rule here has the same shape: ``(QualContext, DecisionStream) ->
Properties | None``. ``None`` means *no opinion*, and so does every key a rule
declines to set; that sparseness is not laziness, it is the mechanism by which
a later layer can have an opinion about one property without having to restate
the other twenty.

Two disciplines run through the whole file.

**Applicability is explicit.** No rule tests a floor number. Where a real
Parisian rule is a height above the pavement, it is written as a height above
the pavement — ``balcony_ordonnance_1823`` reads its 6 m threshold and its
0.80 m cap out of ``reglement.balcony_rule`` and compares against
``ctx.level_above_pavement``. Nothing about it knows what a "second floor" is,
which is why deleting the mezzanine from the stack moves the balcony up a
storey with no rule change at all.

**Treatment diminishes with rank from the principal floor.** That single
relation replaces the per-floor ornament table. ``rank_from_principal`` is 0 on
the étage noble and counts outward, so one formula covers a five-storey and a
nine-storey building alike.

### Specificity

Within a layer, higher specificity wins; **equal order and equal specificity is
a conflict and raises**. So the scale below is not decoration — two rules in
this layer that can fire on the same cell must either set disjoint keys or sit
at different rungs. Each rule's docstring says which.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from buildings.quantity import Abs, Quantity
from buildings.rng import DecisionStream
from buildings.typologies.paris import catalogue, chronology
from buildings.typologies.paris.reglement_adapter import balcony_rule, era_for_year
from buildings.typologies.paris.roles import Role
from buildings.typologies.paris.qualify.context import Properties, QualContext, Rule
from buildings.site import GroundProgramme

__all__ = [
    "BASE_RULES",
    "SPEC_UNIVERSAL",
    "SPEC_SLOT",
    "SPEC_ROLE",
    "SPEC_SLOT_AND_ROLE",
    "SPEC_EXACT",
    "ornament_for_rank",
    "ornament_modules_at",
    "aspect_for_rank",
    "filant_runs_here",
    "sill_height_for",
    "opening_type_for",
    "base_entablature_depth",
    "entresol_head_form",
    "devanture_faces",
    "carries_an_ordinary_window",
    "crowned_by_a_carved_stone",
    "entrance_arch_form_for",
    "two_storey_arch_at",
]

# --- the specificity scale -------------------------------------------------
#: Fires on every cell of the grid.
SPEC_UNIVERSAL = 0
#: Narrowed by what the horizontal slot is.
SPEC_SLOT = 10
#: Narrowed by the floor — its role, or its height above the pavement.
SPEC_ROLE = 20
#: Narrowed by both.
SPEC_SLOT_AND_ROLE = 30
#: Narrowed by both plus one further fact (the entrance, the corner, the axis).
SPEC_EXACT = 40

# ---------------------------------------------------------------------------
# INFERRED constants. Same status as structure.py's _TAPER_RATE and roles.py's
# _MEZZANINE_RATIO: placeholders with the right *shape*, standing in for a
# figure nobody has measured. Only the direction is contractual — treatment
# falls off as you move away from the principal floor — and the tests assert
# the direction, never these numbers.
# ---------------------------------------------------------------------------

#: Ornament lost per storey of distance from the principal floor.
_RANK_DECAY = 0.12
#: Floor under the decay: even the meanest storey is not blank masonry.
_RANK_FLOOR = 0.15

#: Cornice projection as a fraction of the storey it crowns. PROPORTIONAL by
#: nature (the brief lists "the projection of a cornice relative to the height
#: it crowns" as the type case), so the class layer is free to move it.
_CORNICE_FRACTION = 0.28

#: String-course band depth as a fraction of the storey it runs under. Same
#: species as the cornice fraction, and proportional for the same reason.
#:
#: It is the DEPTH OF THE BAND, in metres, and ``compose`` puts it straight
#: into the node's ``h``. Until A13 the renderer drew ``2 x`` this number, so
#: the IR stated one band and the drawing showed another — the same species of
#: defect as A4.1's opening rectangle. The renderer draws the stated band now
#: and the figure below absorbed the factor, so nothing on any existing
#: frontage moved by a millimetre.
_STRING_COURSE_FRACTION = 0.12

#: Depth of the band that crowns the commercial base, as a fraction of THE
#: BASE IT CROWNS (A13.1) — not of the storey above it, which is a floor the
#: entablature has nothing to do with. Same species as ``_CORNICE_FRACTION``,
#: which is a fraction of the storey the cornice crowns, and proportional for
#: the same reason: a two-storey commercial base carries a heavier crowning
#: band than a one-storey one, exactly as a taller wall carries a heavier
#: cornice.
#:
#: INFERRED, like every other figure in this block. What is contractual is
#: the ORDERING — the course that crowns the base is the emphatic one, deeper
#: than the line inside the base and than the plain bandeau under a noble
#: floor — and that is what the tests assert, never the number.
_BASE_COURSE_FRACTION = 0.09

_EPS = 1e-9


def ornament_for_rank(rank_from_principal: int) -> float:
    """Treatment as a function of distance from the principal floor.

    The one relation that replaces a per-floor ornament table. Symmetric:
    the socle two ranks below the noble floor and the attic two ranks above
    it are both quieter than the noble floor, for the same reason — they are
    not the floor the building is showing off with.
    """
    return max(_RANK_FLOOR, 1.0 - _RANK_DECAY * abs(rank_from_principal))


#: How far the ornament dial is allowed to stretch a repeat interval. At full
#: density a rhythm runs at the module ``catalogue`` states; at no density at
#: all it runs this much coarser, which is the same ornament thinned out
#: rather than a different ornament. INFERRED, like every other figure in this
#: block; what is contractual is that the interval widens as the density falls
#: — a modest attic carries fewer modillions per metre than a grand entresol,
#: and that is what makes the two facades read as differently ambitious rather
#: than as the same facade at two sizes (A7.2).
_COARSEST_MODULE = 1.9


def ornament_modules_at(density: float) -> dict[str, object]:
    """Every ornament repeat interval, at one storey's ornament density.

    The counting rhythm of a facade is not a fact about how wide the facade
    is: it is "the scale and density of ornament", which BRIEF.md lists among
    the PROPORTIONAL quantities that move with ambition and budget. So it is
    resolved here, from the same dial that already decides how rich the
    surrounds are, and the count it produces travels in the IR.

    Until A7.2 these intervals were literals inside the renderer — ``spacing =
    0.5``, ``w / 0.35``, ``course_h = 0.22`` — and a modest attic cornice and
    a grand entresol's carried exactly the same brackets per metre. What money
    moved was the size of the wall behind them and nothing on it, which is
    precisely the "same facade at two sizes" failure the brief warns about.

    One expression covers all six because they are one decision: how finely
    this storey is worked. ``catalogue`` owns each module at FULL ornament —
    the interval a grand building's principal floor gets — and everything
    quieter reads out from it, coarsening as the density falls. Emitted
    together so that a facade cannot end up with fine dentils over coarse
    refends, which is what a per-ornament dial would eventually produce.
    """
    stretch = 1.0 + (_COARSEST_MODULE - 1.0) * (1.0 - max(0.0, min(1.0, density)))
    return {
        "ornament_modillion_module": float(catalogue.modillion_module()) * stretch,
        "ornament_dentil_module": float(catalogue.dentil_module()) * stretch,
        "ornament_course_width": float(catalogue.rustication_course_width()) * stretch,
        "ornament_course_height": float(catalogue.rustication_course_height()) * stretch,
        "ornament_bracket_module": float(catalogue.balcony_bracket_module()) * stretch,
        "ornament_ironwork_module": float(catalogue.ironwork_ornament_module()) * stretch,
    }


#: How much of its 1:2 proportion an opening loses per storey ABOVE the
#: principal floor. INFERRED; only the direction is contractual, and the
#: floor is ``catalogue.opening_aspect_band``'s own lower bound rather than a
#: second number stated here.
_ASPECT_DECAY_PER_RANK = 0.10


def aspect_for_rank(rank_from_principal: int) -> float:
    """How tall an opening wants to be for its width, by distance from the
    noble floor.

    The noble floor gets the top of ``catalogue.opening_aspect_band`` and
    every storey above it gets a little less, down to the bottom of the band
    — which is what "the openings shorten upward" means when it is said as a
    relation instead of as a table of floors. Asymmetric on purpose, unlike
    ``ornament_for_rank``: ornament falls off in both directions from the
    floor the building shows off, but a window does not get taller as you go
    *down* towards the shopfront. Storeys below the principal are their own
    programme (a devanture, an entresol, a carriage arch) and are sized by
    the rules that name them, so ``rank < 0`` is held at the noble floor's
    want and then cut down by the storey it actually has.
    """
    low, high = catalogue.opening_aspect_band()
    return max(low, high - _ASPECT_DECAY_PER_RANK * max(0, rank_from_principal))


def base_entablature_depth(ctx: QualContext) -> float:
    """Depth of the band that crowns the commercial base, in metres (A13.1).

    Stated once, here, because two rules in two layers need it and a rule may
    never read another rule's output (I1): the string course *is* this band,
    and the arcaded entresol's arch has to stop under it — an arch whose head
    runs behind the entablature over it is an arch drawn through its own
    cornice. Both read it off ``base_block_top``, which every cell of the
    frontage carries, so the storey below the line and the storey above it
    cannot disagree about where the band starts.
    """
    return _BASE_COURSE_FRACTION * ctx.base_block_top


def filant_runs_here(ctx: QualContext) -> bool:
    """Does a continuous balcony run along this storey?

    The condition, not the consequence — stated once, here, because three
    rules need it and a rule may never read another rule's output (I1). It
    is the 1823 ordonnance's height gate applied to the two lines a Paris
    frontage runs a balcon filant along: the floor the building shows off,
    and the top of the wall.
    """
    if not (ctx.rank_from_principal == 0 or ctx.is_topmost_habitable):
        return False
    ordonnance = balcony_rule(
        [ctx.level_above_pavement], era_for_year(ctx.year), second_line=False
    )
    return ctx.level_above_pavement >= float(ordonnance.min_height) - _EPS


def sill_height_for(ctx: QualContext) -> Quantity:
    """Where the underside of an ordinary opening sits above this storey's
    floor.

    Normally ``catalogue.sill_lean_height`` — ABSOLUTE, the height a body can
    lean on — and it is the same number on the first floor and the fifth,
    which is exactly why the top storey's windows come out squarer than the
    noble floor's without anybody writing that down.

    The one exception is not a taste and not a discount: where the noble
    floor's own *balcon filant* runs, the opening onto it is a porte-fenêtre
    and a person walks through it. There is no sill to lean on because there
    is no sill. Still ABSOLUTE — what changed is the body's relation to the
    opening, not the building's budget — and still nothing a class may argue
    with. It applies at the noble floor only: the second filant, along the
    top of the wall, guards a window rather than carrying a room out onto a
    terrace (INFERRED).
    """
    if ctx.rank_from_principal == 0 and filant_runs_here(ctx):
        return Abs(
            0.0,
            "a porte-fenêtre onto the balcon filant is stepped through, not leaned on",
        )
    return catalogue.sill_lean_height()


def _special_feature(ctx: QualContext, rng: DecisionStream) -> str:
    """Which narrow feature a special slot carries, on THIS storey.

    One addressable draw, in one place, so the rule that names it and the
    rule that sizes it cannot disagree — the stream is keyed on
    ``(seed, path)`` and re-asking it is free and identical.

    **A6.2.** This used to offer ``blind_panel`` and nothing else on every
    storey but the topmost, so a parcel that carried a narrow special carried
    a column of blind panels from the pavement to the cornice and read as a
    walled-up building. The narrow special exists so that the leftover the
    rhythm could not absorb is architecturally *meaningful*, and a stack of
    one element repeated five times is the opposite of that.

    So the vocabulary is offered by storey, and it is the storey's own facts
    that decide which:

    * **The ground storey** takes a blind panel and only that. The strip
      beside a devanture is where the shopfront's structure lands and where
      the stair or the passage runs behind; it is the one level where the
      leftover really is solid wall. (Under A6.1 it is no longer a candidate
      for the entrance either — the entrance is its own FIXED slot, placed by
      a positional rule, not a use found for whatever the rhythm left over.)
    * **The topmost habitable storey** takes an *œil-de-bœuf* or a narrow
      light, and never a blind panel. A roundel is a top-of-the-wall form —
      it belongs exactly where the wall is running out — and a blank panel on
      the most-seen line of the facade is the defect this rule exists to
      remove, not a form to put back at the top of it.
    * **Everything between** takes a narrow light or a blind panel — a real
      window in a real strip of wall, which is what most such leftovers are
      on a real Paris frontage.

    A draw rather than a table because both members of each pair are honest
    answers and the path is per-storey, so the column varies down the facade
    instead of repeating. And it cannot *fail* to vary, which a coin alone
    could: the ground storey's answer is always ``blind_panel`` and the top of
    the wall's is never ``blind_panel``, so any column two storeys tall or
    more carries at least two different things by construction rather than
    by luck.

    **A7.5.** "At least two different things" turned out to be a weak claim.
    Nearly a third of special columns still read as a near-full stack of one
    element — worst case ``blind_panel`` four storeys running under a single
    oeil-de-boeuf, which is the walled-up frontage A6.2 set out to remove,
    wearing a hat. The letter held and the spirit did not, because each storey
    was tossing its own coin and four heads in a row is ordinary luck.

    So the column is read as a column. ``_special_column`` below replays every
    storey's draw from the pavement upward and caps how many identical
    answers may stand on top of one another; this function is the answer for
    one storey of that column. The draws themselves are untouched — the same
    ``(seed, path)`` keys, in the same order — and what the cap changes is the
    one storey that would have continued a run, which takes the other member
    of its own pair. A narrow special is a leftover the rhythm could not
    absorb, and the whole reason it is worth composing at all is that a person
    looking up it sees the building doing something different at each floor.
    """
    return _special_column(ctx, rng)[ctx.index_from_bottom]


#: How many storeys of the same narrow-special fill may stand on top of one
#: another before the column has stopped varying (A7.5). Two: a pair reads as
#: a deliberate stack of two, three reads as a wall. INFERRED; what is
#: contractual is that the cap exists and is small.
_MAX_IDENTICAL_SPECIAL_RUN = 2


def _special_options(index_from_bottom: int, topmost_habitable: int) -> list[str]:
    """The vocabulary a narrow special is offered on one storey.

    Split out of ``_special_feature`` so the column can be replayed from the
    bottom without a ``QualContext`` per storey. It asks the same two
    questions that function's prose asks — is this the ground storey, is this
    the top of the wall — of the storey INDEX, because a column is a column
    and the answer for the storey three floors down is not available as a
    context here. The two agree by construction: ``roles.assign_roles`` makes
    the bottom slot ``Role.BASE`` unconditionally, and
    ``QualContext.is_topmost_habitable`` is exactly
    ``index_from_top == storeys_within_comble``, which is this index.
    """
    if index_from_bottom == 0:
        return ["blind_panel"]
    if index_from_bottom == topmost_habitable:
        return ["oeil_de_boeuf", "narrow_window"]
    return ["narrow_window", "blind_panel"]


def _special_column(ctx: QualContext, rng: DecisionStream) -> list[str]:
    """Every narrow-special fill from the pavement up to ``ctx``'s storey.

    Pure and cheap to re-ask: each storey's draw is keyed on
    ``(seed, path)``, so replaying the column costs nothing and returns the
    same answer every time — which is what lets ``_special_feature`` remain a
    function of one cell while the cap it applies is a fact about the whole
    column.

    The cap is applied bottom-up because that is the direction the constraint
    actually runs: the ground storey's fill is forced (it is solid wall behind
    a devanture), so a run always starts from a decision nobody made, and the
    storey that has to give way is the one above it rather than the one below.
    Where a storey is offered a single answer — the ground — the cap has
    nothing to swap to and leaves it alone; that can only ever happen on the
    first storey of the column, where there is no run yet to break.
    """
    topmost_habitable = ctx.storey_count - 1 - ctx.storeys_within_comble
    column: list[str] = []
    for i in range(ctx.index_from_bottom + 1):
        options = _special_options(i, topmost_habitable)
        pick = rng.choice(
            f"facade/storey/{i}/special/{ctx.bay_index_from_left}", options
        )
        run = column[-_MAX_IDENTICAL_SPECIAL_RUN:]
        if len(run) == _MAX_IDENTICAL_SPECIAL_RUN and all(v == pick for v in run):
            pick = next((o for o in options if o != pick), pick)
        column.append(pick)
    return column


def opening_type_for(ctx: QualContext, rng: DecisionStream) -> str:
    """What occupies this slot, as one expression.

    The five rules below each state one case of this and are the authority;
    this restates the whole of it so that a rule which needs to *size* the
    opening can know which one it is sizing without reading another rule's
    output. Duplication of this kind is normally how a rule set rots, so it
    is not left as a comment claiming the two agree: ``test_qualify`` walks
    every slot-name × role × programme combination and asserts that this
    function and the layered resolution return the same string.
    """
    if ctx.is_special:
        return _special_feature(ctx, rng)
    if ctx.slot_name == "pier_end":
        return "none"
    if ctx.slot_name in catalogue.ENTRANCE_SLOT_NAMES:
        if ctx.role is Role.BASE:
            return catalogue.ENTRANCE_OPENING_TYPES[ctx.slot_name]
        # A14.1: where the entrance rises through the entresol as one round
        # arch, the entresol's opening in THIS bay is inside the arch — a
        # balconette with its ironwork under the head — and not a separate
        # window standing beside it. Stated here, in the shared expression,
        # so that the two class-layer rules which size windows
        # (``window_size_is_what_the_bay_and_the_owner_allow`` and
        # ``entresol_arcade_is_sized_by_the_storey_it_lights``) decline on
        # this cell by the test they already make, rather than by learning a
        # new one.
        if two_storey_arch_at(ctx, rng) is not None:
            return catalogue.ENTRANCE_ARCH_HEAD_OPENING
        return "window"
    if ctx.slot_name == "bay":
        # The devanture faces the rez-de-chaussée and stops there (A17.2),
        # so a bay it stands in front of is glass and every bay above it is a
        # window in a wall.
        if devanture_faces(ctx, rng):
            return "shop_bay"
        return "window"
    return "none"


#: What the ground floor is *for*, as the face it presents to the street.
#: Lifted out of ``ground_programme_treatment`` so that every rule needing the
#: frontage's face reads one table rather than restating the mapping — two
#: copies of it would eventually disagree.
_GROUND_PROGRAMME_FACE: Mapping[GroundProgramme, str] = MappingProxyType(
    {
        GroundProgramme.SHOP: "devanture",
        GroundProgramme.CAFE: "devanture",
        GroundProgramme.OFFICE: "glazed_counting_house",
        GroundProgramme.CARRIAGE: "porte_cochere_and_masonry",
        GroundProgramme.RESIDENTIAL: "plain_masonry",
    }
)

#: Ground programmes whose frontage is glazed joinery rather than masonry,
#: which is what puts a devanture on the rez-de-chaussée at all.
_GLAZED_GROUND = (GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE)


def entresol_head_form(ctx: QualContext, rng: DecisionStream) -> str:
    """Square-headed or *arc surbaissé* — the one thing that genuinely varies
    between Daly's two entresols.

    * **77 bd de Sébastopol** — square-headed lights over the shopfront band.
    * **120 bd de Sébastopol** — segmental arches turned in the base's own
      coursing.

    Same year, same class, same architect, same 4.00 + 3.10 base. So this is
    not a date fact and not a money fact: it is variation *within* a class and
    a period, which is what ``DecisionStream`` is for. Evenly weighted because
    the evidence is one plate each, and the rate is INFERRED — n = 2 cannot
    support one. The path is per FRONTAGE, because a building has one entresol
    and one mason.
    """
    return rng.choice("facade/entresol/head", ["flat", "segmental"])


def devanture_faces(ctx: QualContext, rng: DecisionStream) -> bool:
    """Does the shopfront's own framework stand in front of THIS storey?

    The rez-de-chaussée of a glazed frontage, and nothing above it. Reads no
    horizontal fact, so every cell of a row agrees about it — which is what
    lets the storey-scope rules (the garde-corps, the string course) read it
    too.

    **A17.2.** This used to answer yes on the entresol as well, where the
    devanture was said to have absorbed it. Both plates show otherwise: at 77
    and at 120 bd de Sébastopol the shopfront closes at a full-width
    entablature and the entresol above it is a separate register in the
    stone. The framework never spanned both.
    """
    if ctx.ground not in _GLAZED_GROUND:
        return False
    return ctx.role is Role.BASE


# ---------------------------------------------------------------------------
# A14 — the entrance that rises through the entresol
# ---------------------------------------------------------------------------


def _base_block_registers(ctx: QualContext) -> tuple[float, float] | None:
    """``(rez-de-chaussée height, entresol height)``, in metres, read from
    whichever of the two rows is asking. ``None`` where there is no entresol.

    The same asymmetry ``storeys_in_the_base_block`` exists to remove, in the
    one place it is unavoidable: the base row knows its own height and the
    block's top, the entresol row knows its own height and its floor level,
    and each can name the other's from those. They agree by construction,
    because ``base_block_top`` is the sum of exactly these two.
    """
    if not ctx.has_an_entresol or not ctx.stands_in_the_base_block:
        return None
    if ctx.role is Role.BASE:
        return ctx.slot_h, ctx.base_block_top - ctx.level_above_pavement - ctx.slot_h
    return ctx.level_above_pavement, ctx.slot_h


def entrance_arch_form_for(ctx: QualContext, rng: DecisionStream) -> str | None:
    """Which of the two heights this frontage's entrance takes (A14.2):
    ``"two_storey"`` — one round-headed arch spanning the base and the
    entresol — or ``"one_storey"``. ``None`` where the base block could not
    carry the tall form at all, so there was no choice to make.

    **Why this is a draw and not a table**, in exactly the shape A13.2's is.
    Daly's four are:

    * Avenue de l'Impératrice — porte cochère, Première Classe, 1864
    * 39 rue Neuve des Mathurins — porte cochère, Deuxième Classe, 1864
    * 2 et 4 bd de Sébastopol — porte piétonne, Deuxième Classe, 1864
    * 87 bd de Sébastopol — porte piétonne, Première Classe, 1864

    Same year for all four, so it is not a date fact. Two Première and two
    Deuxième, so it is not a class fact. It is variation *within* a class and
    a period, which is what ``DecisionStream`` is for.

    **The entrance kind does move the rate, and A17.1 got this wrong twice.**
    "Two carriage and two pedestrian" was the reason this used to give for
    calling it kind-blind, and it counts numerators only: the corpus holds 7
    carriage entrances and 10 pedestrian ones, so the same four are 2 of 7
    against 2 of 10. A17.1 then over-corrected and made the tall form
    compulsory on every porte cochère, which 26 rue Bergère refutes on a
    measured plate. The lean is real, the absolute is not, so the kind picks
    a rate (``catalogue.two_storey_arch_rate``) and both outcomes stay
    reachable on both kinds. Both rates are INFERRED and neither is a
    calibration; only the ordering is contractual.

    The path is per FRONTAGE (``facade/entrance/arch_form``), the same shape
    as A17.2's ``facade/entresol/head``, because a building has one
    entrance and one mason, and because a path that does not move when a
    storey is added is a path a test can pin. Stated as a choice between two
    NAMED forms rather than as a flag some buildings have set: three quarters
    of Daly's entrances are one-storey, and that is the other outcome of the
    decision, not the absence of one.

    **Offered only where the base block could build one.** Two conditions,
    both structural rather than tasteful:

    1. There is an entresol for it to rise through (A14.1). The test is
       ``has_an_entresol`` — the structural fact that there is a second
       register in the base block — and not anything about how that register
       is drawn. (This condition used to justify itself by the Impératrice,
       where the entresol was said to be *absorbed* into the base; A17.2
       retracted that form, and the Impératrice carries no measured entresol
       at all. The condition stands on its own without the example.)
    2. The entresol is deep enough to turn the round head in — a semicircle
       on an ABSOLUTE span, under the band that crowns the base. Asked
       *before* the draw, so a frontage that could never build one does not
       spend a coin on it and quietly move the reported rate.
    """
    if ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES:
        return None
    registers = _base_block_registers(ctx)
    if registers is None:
        return None
    base_h, entresol_h = registers
    if not catalogue.two_storey_entrance_arch_fits(
        ctx.slot_name,
        ctx.slot_w,
        base_h,
        entresol_h,
        crown_below=_crown_below(ctx),
    ):
        return None
    # A17.1, as corrected. One draw for both kinds of entrance, at a rate the
    # entrance kind sets — not a branch that hands the carriage arch out
    # unconditionally.
    #
    # A17.1 first read the asymmetry as an absolute: only one opening on a
    # Paris frontage crosses the entresol FLOOR, and it is the carriage
    # entrance, because a carriage has to pass under that floor to reach the
    # cour. The clearance argument is sound and it is still the wrong shape of
    # rule — it says why a carriage door MAY span the floor, not why every one
    # must. Daly refutes the absolute directly: 26 rue Bergère carries a porte
    # cochère of 3.474 m under an entresol of 3.09 m, stopping at the
    # rez-de-chaussée like any shop door.
    #
    # So the lean lives in the rate (``catalogue.two_storey_arch_rate``) and
    # both outcomes stay reachable on both kinds. One path, not two: a
    # building has one entrance and one mason, and a frontage that changes its
    # entrance kind should move along the same decision rather than start a
    # fresh one — which also keeps the path pinnable, as A14.2 requires.
    rate = catalogue.two_storey_arch_rate(ctx.slot_name)
    return rng.choice(
        "facade/entrance/arch_form",
        [catalogue.ENTRANCE_ARCH_TWO_STOREY, catalogue.ENTRANCE_ARCH_ONE_STOREY],
        [rate, 1.0 - rate],
    )


def _crown_below(ctx: QualContext) -> float:
    """How much of the entresol the band crowning the base takes off the top.

    The SAME expression ``qualify.klass.entresol_arcade_is_sized_by_the_
    storey_it_lights`` fits the flanking entresol arches under: the crowning
    entablature where that is deeper than the floor structure, and the floor
    structure otherwise. A14 says the arch "springs from the same coursing as
    the flanking arches"; an arch coursed with its neighbours ends on their
    line as well as starting on it, and sharing the expression is what makes
    that true rather than approximately true.
    """
    return max(base_entablature_depth(ctx), float(catalogue.lintel_bearing_depth()))


def two_storey_arch_at(
    ctx: QualContext, rng: DecisionStream
) -> catalogue.TwoStoreyEntranceArch | None:
    """The two-storey arch standing in this cell, or ``None``.

    One shared expression for a geometry five rules in three layers need
    (I1): the lower register's leaves, the upper register's head, the
    ironwork inside it, the agrafe at the crown, and the two class-layer
    window rules that have to decline. Every one of them gets the identical
    object, so no two can disagree about where the springing is.

    Returns ``None`` on every cell that is not one of the arch's own two —
    including the entrance slot's ordinary upper storeys, which carry the
    same plain windows they always did.
    """
    registers = _base_block_registers(ctx)
    if registers is None:
        return None
    if entrance_arch_form_for(ctx, rng) != catalogue.ENTRANCE_ARCH_TWO_STOREY:
        return None
    base_h, entresol_h = registers
    return catalogue.two_storey_entrance_arch(
        ctx.slot_name,
        ctx.slot_w,
        base_h,
        entresol_h,
        crown_below=_crown_below(ctx),
    )


def carries_an_ordinary_window(ctx: QualContext, rng: DecisionStream) -> bool:
    """Does this cell hold a plain window in a wall?

    The predicate the window's *attendant* elements are keyed to — surround,
    keystone, garde-corps — instead of the slot's name.

    Keying them to ``slot_name == "bay"`` was a positional test wearing an
    architectural coat, and A6.1 exposed what it cost: with an entrance slot
    on every frontage, the whole column of wall standing over the door came
    out bare — no architrave, no keystone, no railing — because the slot is
    named for the door underneath it rather than for the four ordinary
    windows above it. On a real immeuble that column is indistinguishable
    from its neighbours above the ground storey, which is exactly what
    ``opening_type_for`` already says: it returns ``"window"`` there.

    Not a rule reading another rule's output (I1): ``opening_type_for`` is the
    single shared expression of what occupies a slot, computed from the
    context alone, and ``test_qualify`` holds it to agreeing with the layered
    resolution over every slot × role × programme combination.
    """
    return opening_type_for(ctx, rng) == "window"


def crowned_by_a_carved_stone(ctx: QualContext, rng: DecisionStream) -> bool:
    """Does a carved stone close this opening at its crown?

    Every cell ``carries_an_ordinary_window`` names, plus one more: the head
    register of a two-storey entrance arch, whose crown carries an **agrafe**
    — the sculpted keystone the Impératrice plate puts a mascaron in. It is
    the same sculptor's programme and the same structural fact (a keystone is
    what closes an opening), so it is one predicate and not two, and the
    period layer names the agrafe from the same dated draw as every other
    keystone on the building.
    """
    return (
        carries_an_ordinary_window(ctx, rng)
        or opening_type_for(ctx, rng) == catalogue.ENTRANCE_ARCH_HEAD_OPENING
    )


# ===========================================================================
# What occupies the slot
# ===========================================================================


def bay_is_a_window(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """An ordinary bay carries an ordinary window.

    Applicability: the slot is a bay. Sets ``opening_type``/``opening_head``
    and the sill at ``SPEC_SLOT``; ``ground_floor_of_a_shop`` and
    ``noble_floor_steps_out_onto_its_balcon_filant`` override from
    ``SPEC_SLOT_AND_ROLE``, and the pier/special/entrance rules below never
    co-apply because a slot has exactly one name. How *big* the window is
    belongs to the class layer, which is where the money is; how high off the
    floor it starts is a body, and stays here.
    """
    if ctx.slot_name != "bay":
        return None
    sill = catalogue.sill_lean_height()  # ABSOLUTE: never scales with class
    return Properties(
        {
            "opening_type": "window",
            "opening_head": "flat",
            "opening_sill_height": float(sill),
        },
        rule="paris.qualify.base.opening.bay_is_a_window",
        specificity=SPEC_SLOT,
    )


def pier_is_blank_wall(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """The end piers are wall, not opening.

    Applicability: the slot is an end pier. Disjoint from every other
    ``opening_type`` rule at this rung.
    """
    if ctx.slot_name != "pier_end":
        return None
    return Properties(
        {"opening_type": "none", "surround_kind": "none", "surround_richness": 0.0},
        rule="paris.qualify.base.opening.pier_is_blank_wall",
        specificity=SPEC_SLOT,
    )


def entrance_fills_the_door_slot(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The entrance, and it is ABSOLUTE — the ruler the facade is read against.

    A6.1: every building has exactly one entrance, and phase 1 places a FIXED
    slot for it on every frontage by a positional rule (the middle of the run,
    or one place left of it with the composition answering on the other side).
    This rule fills that slot. *Which* door it is was decided in the
    catalogue, from the class and the street width, and it arrives here as the
    slot's own name — this rule reads it and never re-decides it.

    Whichever it is, its width and its height are a body and a vehicle and
    never scale: the porte cochère is a carriage, the porte piétonne is two
    people and a trunk under an imposte. So the dimensions are stated HERE,
    in the base layer, where no class rule may touch them —
    ``catalogue.entrance_in_slot`` refuses a class argument, so there is
    nowhere for ambition to enter even by accident — and the catalogue raises
    rather than shrinking when the slot or the storey cannot hold them
    (A5.5).

    Applicability: an entrance slot, on the base storey, where the arch does
    NOT rise through the entresol. ``SPEC_SLOT_AND_ROLE``; the two-storey form
    below is narrower still and states the same keys.
    """
    if ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES or ctx.role is not Role.BASE:
        return None
    if two_storey_arch_at(ctx, rng) is not None:
        return None
    geom = catalogue.entrance_in_slot(ctx.slot_name, ctx.slot_w, ctx.slot_h)
    return Properties(
        {
            "opening_type": catalogue.ENTRANCE_OPENING_TYPES[ctx.slot_name],
            # A carriage arch is turned; a pedestrian door has a flat head
            # with the imposte under it. The head follows from what the
            # opening is, which is why it is stated with it.
            "opening_head": (
                "segmental" if ctx.slot_name == catalogue.ENTRANCE_CARRIAGE else "flat"
            ),
            "surround_kind": "moulded_architrave",
            "surround_richness": 1.0,
            "opening_width": geom.width,
            "opening_height": geom.height,
            "opening_offset_x": geom.offset_x,
            "opening_sill_height": geom.sill,
        },
        rule="paris.qualify.base.opening.entrance_fills_the_door_slot",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def over_the_entrance(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Above the door the entrance strip is ordinary wall with an ordinary
    window in it. Applicability: an entrance slot, on any floor but the base
    — disjoint from ``entrance_fills_the_door_slot`` by that test alone.

    A14.1 carves out one cell of that strip: where the arch rises through the
    entresol, the entresol is not "above the door" at all, it is *inside the
    arch*, and the two rules below own it. Everything higher up the column is
    untouched — a two-storey arch does not change what the third floor is."""
    if ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES or ctx.role is Role.BASE:
        return None
    if two_storey_arch_at(ctx, rng) is not None:
        return None
    return Properties(
        {
            "opening_type": "window",
            "opening_head": "flat",
            # An ordinary window, so an ordinary sill. Without this the strip
            # over the door was the one column of the facade whose windows
            # sat on the floor, because the sill rule tests for a slot named
            # "bay" and this slot is named for the door underneath it.
            "opening_sill_height": float(catalogue.sill_lean_height()),
        },
        rule="paris.qualify.base.opening.over_the_entrance",
        specificity=SPEC_SLOT,
    )


def the_entrance_arch_rises_through_the_entresol(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The lower register of a two-storey entrance arch (A14.1).

    The leaves, and the carved tympanum panel standing on them — which is
    what the Impératrice plate draws: two panelled leaves to about nine
    tenths of the rez-de-chaussée, then a carved band of rosettes, and the
    arch carrying on up past both into the entresol.

    Two things are stated here that a one-storey door does not have:

    * ``opening_height`` is the WHOLE storey. There is no lintel band under
      the ceiling in this one bay, because the arch does not stop at the
      ceiling — it carries the floor structure up into the entresol, which is
      precisely what the two-storey form buys and why a mason built one.
    * ``opening_head`` is ``"none"``. The head is real and it is round, but it
      is one storey up: the jambs run straight out of the top of this
      register into the next. A head drawn here as well would be an arch
      turned twice.

    ``opening_width`` is ``entrance_in_slot``'s, to the centimetre, and
    ``entrance_leaf_height`` is its clear height, unchanged. **A tall arch is
    not a wide one** (A14.1) — the arch is 2.60 m across whether it rises 3.70
    m or 6.01, exactly as Daly's 2.57 and 2.62 sit inside his one-storey band
    of 2.41–2.67.

    Applicability: the base storey of an entrance slot whose arch rises
    through the entresol. ``SPEC_EXACT`` — the slot, the role, and the arch
    decision — above ``entrance_fills_the_door_slot``, which also declines.
    """
    if ctx.role is not Role.BASE:
        return None
    arch = two_storey_arch_at(ctx, rng)
    if arch is None:
        return None
    return Properties(
        {
            "opening_type": catalogue.ENTRANCE_OPENING_TYPES[ctx.slot_name],
            "opening_head": "none",
            "entrance_arch_register": catalogue.ENTRANCE_ARCH_LEAVES,
            "entrance_leaf_height": arch.leaves_height,
            "surround_kind": "moulded_architrave",
            "surround_richness": 1.0,
            "opening_width": arch.clear_width,
            "opening_height": arch.leaves_register_height,
            "opening_offset_x": arch.offset_x,
            "opening_sill_height": 0.0,
        },
        rule="paris.qualify.base.opening.the_entrance_arch_rises_through_the_entresol",
        specificity=SPEC_EXACT,
    )


def the_entresol_register_of_a_tall_arch_is_its_head(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The upper register of the same arch: its round head, and nothing else.

    Renamed by **A20.1**, which removed the balconette this used to put here.

    A14.1's own words: "the entresol's opening in that bay is **inside the
    arch** — a balconette with ironwork — not a separate window beside it."
    So this cell carries no window. It carries the arch's upper light, with

    * a **round** head, and its rise stated
      (``catalogue.round_arch_rise`` — half the span, because that is what
      round means) rather than left to whatever depth the drawing picks;
    * an **agrafe** at the crown (``keystone_present``; the period layer
      names it, from the same dated draw as every other keystone on the
      building — at the Impératrice it is a mascaron);
    * a **garde-corps** across the light. Not a projecting balconette: it
      stands in the reveal, inside the arch, which is exactly why the form
      is lawful this low down — the 1823 ordonnance governs what may project
      over the street, and this projects nothing. So ``ironwork_present``
      without ``balcony_present``, and ``compose`` hangs it in the light's
      own width. **A15.3**: and its HEIGHT is the straight portion of that
      light, ``catalogue.garde_corps_in_an_arched_light``. A rail standing in
      the reveal is in the same plane as the archivolt; carried to the
      flat-headed ``sill_lean_height`` it crossed the springing on 90 of 210
      tall arches and cut through the moulding. What projects nothing may not
      pass through anything either.

    No ``surround_kind`` here, deliberately. The moulded architrave belongs
    to the register below, whose top edge is the imposte the arch springs
    from; the moulding that follows the curve is the archivolt, and it is
    part of the head rather than a frame around a rectangle. A second
    rectangular architrave drawn around a semicircle would be a stone frame
    boxing in the one element the whole form exists to show.

    Applicability: the entresol of an entrance slot whose arch rises through
    it. ``SPEC_EXACT``, above three rules that would otherwise put an ordinary
    opening here: ``over_the_entrance`` (which declines outright), the
    ``SPEC_SLOT_AND_ROLE`` arcade rule
    ``entresol_is_arcaded_in_the_base_s_own_stone`` — which is right about
    every OTHER slot on this storey and would give this one a segmental light
    on an allège — and the two class-layer rules that size windows, which
    decline because ``opening_type_for`` no longer calls this cell a window.
    """
    if ctx.role is not Role.MEZZANINE:
        return None
    arch = two_storey_arch_at(ctx, rng)
    if arch is None:
        return None
    return Properties(
        {
            "opening_type": catalogue.ENTRANCE_ARCH_HEAD_OPENING,
            "opening_head": "round",
            "opening_head_rise": arch.head_rise,
            "entrance_arch_register": catalogue.ENTRANCE_ARCH_HEAD,
            "opening_width": arch.clear_width,
            "opening_height": arch.head_register_height,
            "opening_offset_x": arch.offset_x,
            # The light runs down to the imposte band in the register below,
            # so there is no allège under it and no sill: this is one arch
            # cut through two storeys, not two openings stacked.
            "opening_sill_height": 0.0,
            "surround_kind": "none",
            "surround_richness": 0.0,
            "keystone_present": True,
            # A20.1: what fills the head, which the two plates disagree about
            # and so is stated rather than assumed. At 39 rue Neuve des
            # Mathurins the CARRIAGE arch is filled by a carved tympanum in
            # the same timber as the leaves — the whole opening reads as one
            # solid door from the threshold to the crown. At 2 et 4 bd de
            # Sébastopol the PEDESTRIAN one carries a glazed overlight over
            # its carved overpanel, which is how a stairhall gets its light.
            # Keyed to the entrance kind because that is what differs between
            # the two plates; both are read, neither is inferred.
            "arch_head_infill": (
                "tympanum"
                if ctx.slot_name == catalogue.ENTRANCE_CARRIAGE
                else "glazed"
            ),
            # **A20.1: and NOTHING else.** Stated as a refusal rather than
            # left to `compose` to decline, because the storey-scope
            # `garde_corps` rule says every light above the base carries one
            # and this cell is not a light. A cell where qualification says
            # "railing" and composition quietly draws none is the two-opinions
            # defect this codebase keeps finding; SPEC_EXACT outranks
            # SPEC_ROLE, so the answer is settled here, once, in the IR.
            "ironwork_present": False,
            # No garde-corps, no balconette, no rail of any kind. A14.1 put one here in its own words — "the
            # entresol's opening in that bay is inside the arch — a balconette
            # with ironwork" — and no plate shows it. `daly_detail_56` draws
            # this object at full scale (2 et 4 bd de Sébastopol, the 5.01 m
            # entrance) as one joinery assembly in one frame with an unbroken
            # architrave up both sides; `daly_elevation_52` draws the carriage
            # form at 39 rue Neuve des Mathurins as leaves running into a
            # carved tympanum inside a single archivolt. Nothing crosses
            # either. A rail across a porte cochère would also be a rail
            # across the way in, which is the one thing the opening is for.
        },
        rule=(
            "paris.qualify.base.opening."
            "the_entresol_register_of_a_tall_arch_is_its_head"
        ),
        specificity=SPEC_EXACT,
    )


def special_slot_takes_a_narrow_feature(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A narrow special is not a squeezed window.

    Phase 1 inserts a special when the rhythm cannot absorb the remainder;
    what goes in it is a blind panel, a narrow light or an oeil-de-boeuf —
    real vocabulary, sampled through an addressable path so the choice is
    stable and can be pinned, and offered per storey so the column varies
    from pavement to cornice instead of repeating one element five times
    (A6.2). ``_special_feature`` holds which vocabulary each storey gets and
    why.

    Applicability: the slot is a special. Disjoint from the bay and pier
    rules at ``SPEC_SLOT``.
    """
    if not ctx.is_special:
        return None
    kind = _special_feature(ctx, rng)
    return Properties(
        {
            "opening_type": kind,
            "opening_head": "round" if kind == "oeil_de_boeuf" else "flat",
            # A blind panel stands in the same wall as the windows either side
            # of it, so it starts where they start. (A roundel does not — it
            # has no sill and hangs off its neighbours' heads, which the class
            # layer resolves from above.)
            "opening_sill_height": float(sill_height_for(ctx)),
            "surround_kind": "bare_band",
            "surround_richness": 0.4 * ornament_for_rank(ctx.rank_from_principal),
        },
        rule="paris.qualify.base.opening.special_slot_takes_a_narrow_feature",
        specificity=SPEC_SLOT,
    )


#: Head form a devanture takes, by the era of the SAME "shopfront" chronology
#: ``period.shopfront_of_its_date`` reads for its pane span — a devanture is
#: exactly as dated as the sheet of glass it is glazed with, so the head
#: standing over that sheet is dated by the same distribution rather than by
#: a second, disconnected axis. INFERRED, same status as ``_RANK_DECAY``:
#: nobody has measured the crossover, only the direction is contractual — a
#: shopfront simple enough to be timber and small panes is simple enough to
#: be flat-headed, and the carved, gilded devanture of the 1890s takes the
#: arch its money and its cast iron or worked stone can afford.
_SHOP_HEAD_BY_ERA: Mapping[str, str] = MappingProxyType(
    {
        "timber_small_panes": "flat",  # BRIEF.md: plain carpentry and a painted fascia
        "cast_iron_larger_panes": "segmental",  # cast iron spans a shallow arch a timber lintel could not
        "plate_glass": "segmental",
        "devanture_elaborate": "round",  # the carved, gilded devanture of the 1890s+
    }
)


def _shop_opening_head(ctx: QualContext, rng: DecisionStream) -> str:
    """Which head form a devanture takes — drawn from chronology, not a
    constant (A7.4).

    ``ground_floor_of_a_shop`` used to state ``opening_head='flat'``
    unconditionally, so ``draw_opening``'s segmental-head branch (A6.8) was
    dead code no site could ever reach: the premise the contract asked for —
    shops carry ``segmental`` — was made false rather than satisfied. This
    reads the same "shopfront" catalogue ``shopfront_of_its_date`` already
    reads for the pane span, weighted by prevalence at this building's own
    ``(year, klass)`` exactly the way every other fashion axis is decided,
    and maps the era it draws to the head form that era built. A date the
    catalogue cannot dress gets ``'flat'`` — no opinion, not a crash and not a
    lie about which era supplied it.
    """
    options = chronology.available("shopfront", ctx.year, ctx.klass)
    if not options:
        return "flat"
    era = rng.choice(
        "facade/shop_bay/head_form",
        [v.name for v, _ in options],
        [w for _, w in options],
    )
    return _SHOP_HEAD_BY_ERA.get(era, "flat")


def ground_floor_of_a_shop(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Where the ground floor is trade, the bays open to the street.

    Applicability: the base storey, a bay slot, and a ground programme that
    sells something. Sits above ``bay_is_a_window`` at ``SPEC_SLOT_AND_ROLE``
    so it wins the ``opening_type`` it shares with it.
    """
    if ctx.role is not Role.BASE or ctx.slot_name != "bay":
        return None
    if ctx.ground not in (GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE):
        return None
    return Properties(
        {
            "opening_type": "shop_bay",
            # Segmental and round-headed devantures are common in Paris; the
            # head form is dated the same way every other fashion axis is
            # dated, not hard-coded (A7.4) — see ``_shop_opening_head``.
            #
            # A13.2 used to flatten this head where the devanture was said to
            # carry on above the storey, on the reasoning that an arch halfway
            # up a framework springs off nothing. A17.2 retracted the form: a
            # devanture stops at the entablature over the shop, so this head
            # is always the one the date supplies.
            "opening_head": _shop_opening_head(ctx, rng),
            # A devanture has no sill: you walk into a shop over a step, and
            # ``shop_threshold_height`` is that step. ABSOLUTE, like the lean
            # height it replaces, and for the same kind of reason — a leg
            # rather than a torso. Without it the ground floor of every
            # commercial building carried its glass 0.90 m up the wall.
            "opening_sill_height": float(catalogue.shop_threshold_height()),
            # How big a sheet of glass this light can be made of. Stated in
            # the BASE layer as the ordinary sheet of the century, because a
            # counting-house window is glazed by the same glassworks as a
            # devanture even though it is not a devanture and gets no
            # ``shopfront_variant``. Where the date DOES name a devanture
            # form, the period layer states that form's own sheet and wins,
            # because a later layer always does — which is the mechanism
            # doing exactly what it exists for, rather than this rule trying
            # to guess what the date would have said.
            "shopfront_pane_max_span": float(catalogue.shopfront_pane_max_span(None)),
        },
        rule="paris.qualify.base.opening.ground_floor_of_a_shop",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def entresol_is_arcaded_in_the_base_s_own_stone(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The arcaded entresol: arched openings in the coursing of the base.

    **A17.2 — and since A17.2 this is what every entresol does.** The
    entresol is its own band and it belongs to the base: *arcs surbaissés* cut in the same ashlar the
    ground floor is faced in (which is what ``socle_carries_the_wall`` running
    through this storey puts there), standing on the shopfront's entablature,
    with a small individual railing across each light. Together the two levels
    read as one two-storey commercial base.

    Two facts distinguish it from the upper-floor window it used to be drawn
    as, and both are about the body rather than the budget: the head is
    *segmental*, because it is an arch turned in coursed stone rather than a
    lintel laid across a reveal; and it stands on
    ``catalogue.entresol_allege_height``'s low breast wall rather than on a
    sill somebody leans out over the street from.

    **The strip over the entrance takes this form too.** At 77 bd de
    Sébastopol the column carrying the porte piétonne is masonry from the
    pavement to the cornice, and the entresol light above the door sits in it
    exactly as its neighbours sit in theirs. So this is simply what the
    entresol does, across the whole storey — which since A17.2 is the only
    thing it does, the *absorbed* alternative having been retracted.

    Applicability: a bay or the strip over the entrance, on an entresol.
    ``SPEC_SLOT_AND_ROLE``, above ``bay_is_a_window``'s flat head and lean-on
    sill and above ``over_the_entrance``'s ordinary window.
    """
    if ctx.role is not Role.MEZZANINE:
        return None
    if ctx.slot_name != "bay" and ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES:
        return None
    if not ctx.has_an_entresol:
        return None
    return Properties(
        {
            "opening_type": "window",
            "opening_head": entresol_head_form(ctx, rng),
            "opening_sill_height": float(catalogue.entresol_allege_height()),
        },
        rule="paris.qualify.base.opening.entresol_is_arcaded_in_the_base_s_own_stone",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def the_base_block_states_its_entresol_s_form(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """Say, once, which head Daly's two entresols turn their lights with.

    The property nothing downstream *has* to read and every trace does: it is
    what makes "why are these lights arched?" answerable from the serialised
    IR alone. Stated on BOTH storeys of the block, because A13.1's socle runs
    through the entresol and the two registers are one base.

    Applicability: the base block of a frontage that has an entresol.
    ``SPEC_ROLE``; the only rule that touches ``entresol_head_form``.
    """
    if not ctx.stands_in_the_base_block:
        return None
    if not ctx.has_an_entresol:
        return None
    return Properties(
        {"entresol_head_form": entresol_head_form(ctx, rng)},
        rule="paris.qualify.base.entresol.belongs_to_the_base",
        specificity=SPEC_ROLE,
    )


def noble_floor_steps_out_onto_its_balcon_filant(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """Where the noble floor's balcon filant runs, the window is walked through.

    A porte-fenêtre has no sill, and that is not a discount or a taste: it is
    the same ABSOLUTE reasoning as the sill it replaces, applied to a
    different relation between the body and the opening. Somebody leans on a
    sill; somebody steps over a threshold onto a balcony. The condition is the
    1823 ordonnance's own — ``filant_runs_here`` asks ``reglement`` — so
    raising the balcony threshold, or taking the mezzanine out and dropping
    the noble floor below 6 m, moves this by itself.

    The noble floor only. The second filant along the top of the wall guards a
    window rather than carrying a room out onto a terrace, which is INFERRED
    and is the one part of this a person could argue with.

    Applicability: a bay or the strip over the entrance, on rank 0, on a
    frontage the ordonnance lets a balcony onto. ``SPEC_SLOT_AND_ROLE``, above
    ``bay_is_a_window``'s plain sill and disjoint from the shopfront (which is
    never rank 0).
    """
    if ctx.slot_name != "bay" and ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES:
        return None
    if ctx.rank_from_principal != 0 or not filant_runs_here(ctx):
        return None
    return Properties(
        {"opening_sill_height": float(sill_height_for(ctx))},
        rule="paris.qualify.base.opening.noble_floor_steps_out_onto_its_balcon_filant",
        specificity=SPEC_SLOT_AND_ROLE,
    )


# ===========================================================================
# The surround
# ===========================================================================


def surround_diminishes_with_rank(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The frame around a window is richest on the floor the building shows off.

    One relation, no table: richness is ``ornament_for_rank``, and the named
    form is a threshold on it. A nine-storey building needs no extra rows.

    Applicability: the cell carries an ordinary window — a bay, or the wall
    over the entrance, which above the ground storey is the same window in the
    same wall. Sets ``surround_kind`` and ``surround_richness`` at
    ``SPEC_SLOT``; the pier, special and entrance rules set the same keys but
    can never co-apply, because none of those cells carries an ordinary
    window.
    """
    if not carries_an_ordinary_window(ctx, rng):
        return None
    richness = ornament_for_rank(ctx.rank_from_principal)
    if richness >= 0.95:
        kind = "moulded_architrave"
    elif richness >= 0.6:
        kind = "bare_band"
    else:
        kind = "none"
    return Properties(
        {"surround_kind": kind, "surround_richness": richness},
        rule="paris.qualify.base.surround.diminishes_with_rank",
        specificity=SPEC_SLOT,
    )


def ground_floor_surround_is_the_ground_floor_s_own(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A shop light is framed by the devanture, not by a stone pediment.

    **A6.7.** Every ground-floor bay used to resolve ``surround_kind =
    'pedimented'``, which put a bare triangle floating in the *enseigne* band
    over every shop window on the block. A pediment is an entablature carried
    on consoles over an opening in a wall; a devanture has neither wall nor
    entablature at that point, and no Paris shopfront has ever had one.

    The ground floor has its own vocabulary and this rule reads it from the
    catalogue: a shop light gets the devanture's frame, an ordinary
    ground-floor window (a hall, a stair, a counting house) gets a plain band
    of dressed stone. Richness is held at the ground storey's own rank decay
    rather than raised — the base is the socle of the composition and the
    money goes upstairs.

    **A13.1.** The ground floor's vocabulary is the base BLOCK's: an entresol
    that belongs to the base is framed the way the base is framed, not by the
    ladder of stone architraves the residential storeys climb. So an arcaded
    entresol's arch takes the same plain band of dressed stone an ordinary
    ground-floor window takes — which is what 120 bd de Sébastopol draws, and
    what 77 draws too under a square head.

    Applicability: a bay in the base block. ``SPEC_SLOT_AND_ROLE``, above
    ``surround_diminishes_with_rank`` in this layer; the class layer's
    affordability ladder declines to fire on the base block for the same
    reason, so nothing later overrules this. The entrance is not a "bay" and
    keeps the architrave ``entrance_fills_the_door_slot`` gives it.
    """
    if not ctx.stands_in_the_base_block or ctx.slot_name != "bay":
        return None
    if ctx.role is Role.MEZZANINE and devanture_faces(ctx, rng):
        kind = "none"
    else:
        kind = catalogue.ground_floor_surround(opening_type_for(ctx, rng))
    return Properties(
        {
            "surround_kind": kind,
            "surround_richness": ornament_for_rank(ctx.rank_from_principal),
        },
        rule="paris.qualify.base.surround.ground_floor_is_the_ground_floor_s_own",
        specificity=SPEC_SLOT_AND_ROLE,
    )


# ===========================================================================
# The 1823 ordonnance
# ===========================================================================


def balcony_ordonnance_1823(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """A balcony where the floor is at least 6 m above the pavement.

    This is the rule the whole design is arguing for, so it is worth being
    precise about what it does *not* do. It does not consult a list of floors.
    It does not know what a second floor is. It asks
    ``reglement.balcony_rule`` — the ported regulatory core — for the
    threshold and the projection cap in force in ``ctx.year``, and compares
    the threshold against this storey's own height above the pavement.

    Both numbers are REGULATORY: they carry a citation and they change on a
    date, not with money or taste. Neither is written down here.

    The consequence is the brief's own test: take the mezzanine out of the
    stack and every floor above it drops by the mezzanine's height, the noble
    floor falls below 6 m, and the balcony moves up a storey — with nothing
    edited, because the rule was never about which floor it was.

    Applicability: every cell (it is a fact about the storey, and reads no
    horizontal fact — which is what keeps the storey-scope invariant true).
    ``SPEC_UNIVERSAL``; the filant rule below refines ``balcony_continuous``
    from ``SPEC_ROLE``.
    """
    ordonnance = balcony_rule(
        [ctx.level_above_pavement], era_for_year(ctx.year), second_line=False
    )
    threshold = ordonnance.min_height  # Reg: 6.00 m, ordonnance de 1823
    cap = ordonnance.max_projection  # Reg: 0.80 m, ordonnance de 1823
    permitted = ctx.level_above_pavement >= float(threshold) - _EPS
    if not permitted:
        return Properties(
            {
                "balcony_present": False,
                "balcony_min_height": float(threshold),
            },
            rule="paris.qualify.base.balcony.ordonnance_1823",
            specificity=SPEC_UNIVERSAL,
        )
    return Properties(
        {
            "balcony_present": True,
            "balcony_continuous": False,
            "balcony_projection": float(cap),
            "balcony_min_height": float(threshold),
            # ABSOLUTE: the rail is as high as a body leaning on it, and
            # stays there whatever the building's ambition.
            "balcony_rail_height": float(catalogue.sill_lean_height()),
        },
        rule="paris.qualify.base.balcony.ordonnance_1823",
        specificity=SPEC_UNIVERSAL,
    )


def balcon_filant_on_the_shown_floors(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The two continuous lines: the noble floor and the top of the wall.

    ``reglement.balcony_rule`` expresses this as *first eligible index* and
    *last eligible index*. Those are indices, and indices are what this design
    is removing, so it is restated with the derived identities they stand for:
    the floor the building shows off (rank 0) and the topmost habitable floor,
    the line that lets the tenants above the noble floor share the view.
    Either way the 6 m gate is the ordonnance's, not this rule's.

    One rule, not two, deliberately: on a short building the noble floor *is*
    the topmost habitable floor, and two rules at ``SPEC_ROLE`` both claiming
    ``balcony_continuous`` on that cell would be a genuine conflict — the
    resolver would raise, correctly, and the fix would be to merge them. So
    they are merged.
    """
    if not filant_runs_here(ctx):
        return None
    return Properties(
        {"balcony_continuous": True},
        rule="paris.qualify.base.balcony.filant_on_the_shown_floors",
        specificity=SPEC_ROLE,
    )


# ===========================================================================
# Ironwork
# ===========================================================================


def garde_corps_where_a_body_could_fall(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """Ironwork wherever a window opens above a drop.

    Whether a railing is present is a question about a body and a drop, not
    about the date — the gap between its balusters is ABSOLUTE, set by the
    width of a child's head (``catalogue.balustrade_child_gap_max``), and the
    sill it guards is the height someone can lean on
    (``catalogue.sill_lean_height``). *Which* railing it is, by contrast, is
    a dated question, so this rule sets the presence and the dimensions and
    stops; the period layer names the variant.

    **A6.6.** The railing's height is stated here, as this rule's own
    ABSOLUTE fact. It used to be read off ``balcony_rail_height``, which only
    exists on the floors the 1823 ordonnance permits a balcony on — so every
    garde-corps below 6 m, the mezzanine's included, arrived in the IR with
    ``h = 0.000`` and drew nothing at all. A rule emitting an element that
    cannot be seen is a rule putting a lie in the IR. A railing guarding a
    window is as high as a body leaning on it whether or not the law lets a
    balcony project in front of it, so it is the same ``sill_lean_height``
    the sill above it is, and it is never zero.

    Applicability: any storey above the base — the presence of a railing is a
    fact about the storey's height off the ground and nothing horizontal, so
    this reads no horizontal fact and every cell of the row agrees about it.
    That is what lets the *balcon filant* carry one continuous railing along
    its whole length instead of a row of disconnected panels with the gaps
    between them opening onto an 8 m drop; ``compose`` reads
    ``balcony_continuous`` to decide which of the two shapes to hang it in,
    and hangs the per-opening kind only where there is an opening to guard.
    ``SPEC_ROLE``.
    """
    # The rez-de-chaussée has no drop to guard, and neither has the comble's
    # inside. Everything between does — including the entresol, whose short
    # lights carry an individual garde-corps on both plates. (A13.2 excepted
    # an entresol the devanture had absorbed; A17.2 retracted that form, and
    # with it the exception.)
    if ctx.role is Role.BASE or ctx.within_comble:
        return None
    gap = catalogue.balustrade_child_gap_max()  # ABSOLUTE: never scales
    rail = catalogue.sill_lean_height()  # ABSOLUTE: a body leaning on it

    # **A21.** Two railings, one rule, told apart by the opening's own sill.
    #
    # Where the light comes down to the floor it is a porte-fenêtre and the
    # railing is a guard: it stands at the floor, full ``sill_lean_height``,
    # because a body could otherwise walk straight through. That is the noble
    # floor, and it is what makes its railing line up with the floor line.
    #
    # Where the light stands on an appui, the appui IS the guard — it is the
    # same 0.90 m, which is not a coincidence but the same fact about a body —
    # and the iron across it is a *barre d'appui*, guarding the openable lower
    # sash. It stands INSIDE the opening, on the appui, crossing the glass.
    # It does NOT stand on the wall underneath, where there is nothing to fall
    # through: every railing on plate 77 crosses its light, and none stands on
    # masonry below one.
    #
    # ``compose`` hangs it at the light's own foot either way, so this states
    # only how tall it is; on a porte-fenêtre the two answers coincide, which
    # is the point of them being one expression.
    # This rule reads no horizontal fact — that is what lets the filant run
    # continuous — so it cannot know how TALL a given light is. It states which
    # of the two railings this storey carries, and ``compose`` measures it
    # against the light it is hanging it in.
    # Both facts are stated, and ``compose`` uses whichever fits the shape it
    # is hanging. A *balcon filant* is a barrier standing at the balcony's own
    # floor and takes the ABSOLUTE either way — what is behind it does not
    # change how high a body leans. Only a bar crossing a LIGHT is a share of
    # that light, and only a light standing on an appui gets one.
    props: dict[str, object] = {
        "ironwork_present": True,
        "ironwork_gap_max": float(gap),
        "ironwork_height": float(rail),
    }
    if float(sill_height_for(ctx)) > _EPS:
        props["ironwork_share_of_light"] = catalogue.BARRE_D_APPUI_SHARE_OF_LIGHT
    return Properties(
        props,
        rule="paris.qualify.base.ironwork.garde_corps",
        specificity=SPEC_ROLE,
    )


# ===========================================================================
# Sculpture over the opening
# ===========================================================================


def keystone_over_an_opening(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Every arched or framed opening has something at its crown.

    Presence is structural — a keystone is what closes an opening — so it is
    stated here; *what* the keystone is (plain, console, mascaron, caryatid)
    is a dated question and belongs to the period layer.

    Applicability: a cell whose opening is closed by a carved stone, above the
    base — the strip over the entrance included, since above the ground storey
    it is the same window in the same wall, and (A14.1) the head register of a
    two-storey entrance arch, whose crown carries an agrafe. ``SPEC_SLOT``;
    the arch's own rule states the same value at ``SPEC_EXACT``, so the two
    agree rather than race.
    """
    if ctx.role is Role.BASE or not crowned_by_a_carved_stone(ctx, rng):
        return None
    return Properties(
        {"keystone_present": True},
        rule="paris.qualify.base.keystone.closes_the_opening",
        specificity=SPEC_SLOT,
    )


# ===========================================================================
# The ground floor
# ===========================================================================


def socle_carries_the_wall(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """The base is read as the thing holding the rest up — and the base is
    the rez-de-chaussée AND the entresol over it (A13.1).

    The socle used to stop at the ceiling of the ground storey, which left the
    entresol standing on plain wall above it: a short storey with a shrunken
    window in it, reading as the meanest *residential* floor of the building
    rather than as the top of its commercial base. Daly draws it the other
    way round on both of the plates that have a measured entresol — at 120 bd
    de Sébastopol the entresol's arches are cut in the same coursing as the
    ground floor, and at 77 the same two levels are one devanture. Either way
    the block is two storeys tall and the first "proper" floor is the one
    above it.

    So the applicability is the base BLOCK and not the base STOREY, and it is
    asked of the roles phase 2 derived rather than of an index: take the
    entresol out of the stack and the socle stops at the ground floor by
    itself.

    Sets ``socle_present`` only — ``ground_programme_treatment`` owns
    ``ground_treatment`` and the period layer owns ``socle_treatment``, so
    nothing at ``SPEC_ROLE`` collides.
    """
    if not ctx.stands_in_the_base_block:
        return None
    return Properties(
        {"socle_present": True},
        rule="paris.qualify.base.socle.carries_the_wall",
        specificity=SPEC_ROLE,
    )


def ground_programme_treatment(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """What the ground floor is *for* decides how it is faced.

    Applicability: the base storey. Sets ``ground_treatment`` and
    ``shopfront_present``; the period layer names the shopfront's form.
    """
    if ctx.role is not Role.BASE:
        return None
    trade = ctx.ground in (GroundProgramme.SHOP, GroundProgramme.CAFE)
    return Properties(
        {
            "ground_treatment": _GROUND_PROGRAMME_FACE[ctx.ground],
            "shopfront_present": trade,
        },
        rule="paris.qualify.base.ground.programme_decides_the_face",
        specificity=SPEC_ROLE,
    )


# ===========================================================================
# The horizontal lines
# ===========================================================================


def cornice_crowns_the_wall(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """The cornice sits where the wall stops, not on a numbered floor.

    "Where the wall stops" is ``is_topmost_habitable`` — derived from the
    envelope, so a building that fills its gabarit and one that stops short of
    it both get their cornice in the right place with the same rule.

    Applicability: the topmost habitable storey. ``SPEC_ROLE``.
    """
    if not ctx.is_topmost_habitable:
        return None
    return Properties(
        {
            "cornice_present": True,
            "cornice_projection": _CORNICE_FRACTION * ctx.slot_h,
            "cornice_richness": ornament_for_rank(ctx.rank_from_principal),
        },
        rule="paris.qualify.base.cornice.crowns_the_wall",
        specificity=SPEC_ROLE,
    )


def string_course_crowns_the_base_block(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The strongest horizontal on the lower facade: the line where commerce
    stops and residence begins (A13.1).

    A Paris frontage's lower half has two possible horizontals — the top of
    the rez-de-chaussée and the top of the entresol — and only one of them is
    a division of *use*. On both of Daly's plates with a measured entresol the
    emphatic band is the upper one, over the entresol. What runs under it,
    inside the block — the cornice closing the devanture at the top of the
    rez-de-chaussée — is the lesser of the two, and it divides a shop from
    the storeroom over it rather than commerce from residence.

    So the weight goes here, and it goes here by *level*: the applicability is
    "this storey's floor is the ceiling of the base block", a height above the
    pavement compared against a height above the pavement, exactly like the
    1823 ordonnance. Take the entresol out of the stack and this drops to the
    top of the ground floor by itself; it never asks which floor number it is
    standing on, and it does not care whether the storey it runs under happens
    to be the étage noble.

    Applicability: the first storey standing on a base block of TWO storeys —
    a commercial base with an entresol in it. A one-storey base is crowned by
    the ordinary bandeau below, which is what a residential frontage has
    always had and what Daly draws on the plates without an entresol; the
    entablature is what a base earns by being two storeys of one use.
    ``SPEC_ROLE``, and disjoint from ``string_course_under_the_noble_floor`` —
    which stands down wherever this fires, because two rules claiming the same
    key at the same rung of the same layer is a conflict and would raise,
    correctly.
    """
    if not (ctx.crowns_the_base_block and ctx.has_an_entresol):
        return None
    return Properties(
        {
            "string_course_present": True,
            # Not a bandeau. A bandeau is a sill band for the storey above it
            # and its mass sits above the line; an entablature is the CROWN of
            # the block below and its mass hangs under the line, which is
            # where the eye reads it and where both Daly plates draw it. One
            # word, and the renderer draws the moulding that word names.
            "string_course_kind": "entablature",
            "string_course_projection": base_entablature_depth(ctx),
        },
        rule="paris.qualify.base.string_course.crowns_the_base_block",
        specificity=SPEC_ROLE,
    )


def string_course_under_the_noble_floor(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A bandeau at the floor line of the étage noble.

    Applicability: rank 0, where the noble floor does not already stand on a
    two-storey commercial base — there the same line is the base's own
    entablature (``string_course_crowns_the_base_block``), said more
    emphatically and for a better reason, and this rule stands down so the two
    never collide at ``SPEC_ROLE``.
    """
    if ctx.rank_from_principal != 0 or (
        ctx.crowns_the_base_block and ctx.has_an_entresol
    ):
        return None
    return Properties(
        {
            "string_course_present": True,
            "string_course_kind": "bandeau",
            "string_course_projection": _STRING_COURSE_FRACTION * ctx.slot_h,
        },
        rule="paris.qualify.base.string_course.under_the_noble_floor",
        specificity=SPEC_ROLE,
    )


def string_course_at_the_head_of_the_ground_floor(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The thin line INSIDE the base block: the head of the rez-de-chaussée,
    which an entresol stands on.

    Thin, and much thinner than the entablature crowning the block above it,
    because it divides one use from itself — the shop and the mezzanine that
    belongs to it — where the line above divides commerce from residence. That
    ordering is A13.1's requirement and it is the only thing about these two
    numbers that is contractual.

    **Renamed, and the rename is the point.** This rule used to be called
    ``string_course_over_the_entresol`` and it fires on the mezzanine, whose
    string-course node is emitted at the mezzanine's FLOOR — so the rule named
    for the line above the entresol has always drawn the line below it. That
    name is what reads as an inverted hierarchy; the geometry never was one,
    and now the two agree.

    **Why its presence may not follow the entresol's form.** A string course is
    a BLOCK DATUM — the Circulaire du 21 septembre 1855, enforced by
    ``block.check_alignment`` — so every frontage on the block runs it at the
    same level. What the entresol's lights vary in is their HEAD, building to
    building; that is A17.2's point, two plates on the same boulevard, square
    at 77 and segmental at 120. A course whose presence followed that draw
    would be a datum line that stops at the party wall, which is the failure
    the block level exists to prevent. So the line is where the entresol is,
    under whichever head its lights are turned with.

    Applicability: the mezzanine. Disjoint from both rules above — the
    mezzanine is never rank 0, and it never stands on top of the block it is
    part of.
    """
    if ctx.role is not Role.MEZZANINE:
        return None
    return Properties(
        {
            "string_course_present": True,
            "string_course_kind": "plat_bande",
            "string_course_projection": 0.6 * _STRING_COURSE_FRACTION * ctx.slot_h,
        },
        rule="paris.qualify.base.string_course.at_the_head_of_the_ground_floor",
        specificity=SPEC_ROLE,
    )


# ===========================================================================
# The overall dial
# ===========================================================================


def ornament_diminishes_with_rank(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """Density falls off from the principal floor. Fires everywhere.

    ``SPEC_UNIVERSAL``: the class layer restates it with money in it, and the
    site layer can push it up on a corner, both from above.

    The dial and the six repeat intervals it sets come out together (A7.2).
    They are one decision — how finely this storey is worked — and splitting
    them across two rules would let a later layer move the density without
    moving the rhythm it is the density *of*, which is exactly the drift that
    left the renderer inventing spacings of its own.
    """
    density = ornament_for_rank(ctx.rank_from_principal)
    return Properties(
        {"ornament_density": density, **ornament_modules_at(density)},
        rule="paris.qualify.base.ornament.diminishes_with_rank",
        specificity=SPEC_UNIVERSAL,
    )


BASE_RULES: tuple[Rule, ...] = (
    bay_is_a_window,
    pier_is_blank_wall,
    entrance_fills_the_door_slot,
    over_the_entrance,
    the_entrance_arch_rises_through_the_entresol,
    the_entresol_register_of_a_tall_arch_is_its_head,
    special_slot_takes_a_narrow_feature,
    ground_floor_of_a_shop,
    entresol_is_arcaded_in_the_base_s_own_stone,
    the_base_block_states_its_entresol_s_form,
    noble_floor_steps_out_onto_its_balcon_filant,
    surround_diminishes_with_rank,
    ground_floor_surround_is_the_ground_floor_s_own,
    balcony_ordonnance_1823,
    balcon_filant_on_the_shown_floors,
    garde_corps_where_a_body_could_fall,
    keystone_over_an_opening,
    socle_carries_the_wall,
    ground_programme_treatment,
    cornice_crowns_the_wall,
    string_course_crowns_the_base_block,
    string_course_under_the_noble_floor,
    string_course_at_the_head_of_the_ground_floor,
    ornament_diminishes_with_rank,
)
