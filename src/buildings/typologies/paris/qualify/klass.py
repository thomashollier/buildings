"""The class layer — the same frontage, with money in it.

Class is not a period, and this layer is allowed to branch on it: the
prohibition in the brief is specifically against a rule reading
``period == SECOND_EMPIRE``, because a period enum cannot represent the
straggler. ``BuildingClass`` has no such problem — a modest building is modest
in every year, and the *lag* down the class ladder is already modelled where it
belongs, in ``chronology``'s ``class_lag``.

What this layer is for is the brief's absolute/proportional split, stated as
composition rather than as arithmetic scattered through the rules:

> "A building reads as large or small *because* its absolute elements stay put
> while its proportional ones grow. The grand building on the boulevard is
> legible as grand precisely because its doorway is only a little bigger than
> the modest one's while its windows are much bigger."

So every number this layer moves goes through ``scale_for_class`` — the one
place proportional scaling is allowed to happen — and every number it leaves
alone is left alone on purpose. The carriage door does not appear in this file.
Neither does the sill height, nor the balustrade gap. They are ABSOLUTE, and
``scale_for_class`` would refuse them anyway.

**A9.4 moved the balcony out of this file's argument, and it is worth saying
why the old argument was wrong.** This module used to hold up the balcony as
its sharpest case: the depth an owner wanted was PROPORTIONAL, the 0.80 m cap
REGULATORY, and a grand building's want exceeded the cap and was clipped —
"which is exactly why grand haussmannian balconies all project the same
80 cm". Daly prints the number twice, on two buildings in the same class, and
it is 0.600 and 0.590 m. Nothing in the corpus is clipped by the 1823 cap
because nothing in the corpus comes near it. The depth is a body's, like the
door's, and the two kinds of number never met at all: an INFERRED class factor
had been pushing an absolute into a statute and the collision was being read
as a finding. See ``_BALCONY_PROJECTION``.

The window is the case that survives, and it is a better one because a period
source separates its two halves for us: the same aperture has an ABSOLUTE
width (1.04-1.30 m across all sixteen of Daly's buildings, non-monotonic by
class) and a PROPORTIONAL height (2.92 / 2.24 / 2.09 m at the noble floor,
monotonic). That split lives in ``catalogue.opening_window`` and
``catalogue.opening_height_at_the_nobile``; this layer only asks for it.
"""

from __future__ import annotations

from buildings.quantity import Abs, Prop, scale_for_class
from buildings.rng import DecisionStream
from buildings.site import BuildingClass
from buildings.typologies.paris.roles import Role
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.reglement_adapter import balcony_rule, era_for_year
from buildings.typologies.paris.qualify.base import (
    SPEC_ROLE,
    SPEC_SLOT,
    SPEC_SLOT_AND_ROLE,
    SPEC_UNIVERSAL,
    aspect_for_rank,
    base_entablature_depth,
    carries_an_ordinary_window,
    opening_type_for,
    ornament_for_rank,
    ornament_modules_at,
    sill_height_for,
)
from buildings.typologies.paris.qualify.context import Properties, QualContext, Rule

__all__ = ["CLASS_RULES"]

_EPS = 1e-9

# ---------------------------------------------------------------------------
# INFERRED. As everywhere else in this project, only the ordering is
# contractual — a grander building carries more ornament and a deeper balcony
# than a meaner one — and the tests assert the ordering, not these figures.
# ---------------------------------------------------------------------------

#: How far a balcony stands out from the wall face. **ABSOLUTE and SOURCED
#: (A9.4)**, where it used to be PROPORTIONAL and INFERRED.
#:
#: Daly prints this figure twice, on two different buildings in the same
#: class: **0.600 m** at 88 rue de Rivoli and **0.590 m** at 120 boulevard de
#: Sébastopol — two printed callouts, 2 % apart. Two independent printed
#: values landing on one number is the signature of an absolute, and the
#: reason is the same as the door's and the garde-corps': what sets a
#: balcony's depth is the body standing on it. Half a metre is somewhere to
#: put your feet; a metre would be a room, and a Paris balcon filant is not a
#: room.
#:
#: It was ``Prop(0.60)``, so a MODEST balcony projected 0.51 m and a GRAND one
#: asked for 0.81 m and was clipped to the ordonnance's 0.80 m. The clipping
#: hid the error: the grand building looked as though the *law* had decided
#: its balcony when in fact an INFERRED class factor had pushed it there.
_BALCONY_PROJECTION = Abs(
    0.60,
    f"SOURCED — {catalogue.DALY_1864}, printed '0.600' at 88 rue de Rivoli and "
    f"printed '0.590' at 120 boulevard de Sébastopol ({catalogue.PRINTED}, two "
    "buildings). A balcony is as deep as the body standing on it, so it does "
    "not scale with the building",
)

#: How rich a surround the owner could afford, as the richest named form each
#: class reaches on its best floor. Read down from this by ornament density.
_AFFORDABLE_SURROUND: dict[BuildingClass, tuple[str, ...]] = {
    # meanest form first, richest last
    BuildingClass.MODEST: ("none", "bare_band"),
    BuildingClass.ORDINARY: ("none", "bare_band", "moulded_architrave"),
    BuildingClass.COMFORTABLE: ("bare_band", "moulded_architrave", "pedimented"),
    BuildingClass.GRAND: ("bare_band", "moulded_architrave", "pedimented"),
}


#: The top of the ambition scale, read out of ``scale_for_class`` itself
#: rather than restated: whatever factors that function uses, the grandest
#: class defines full ornament and every other class reads as a fraction of
#: it. Computed once, so a change to the factors moves the whole ladder
#: together and cannot be applied twice.
_AMBITION_CEILING = float(
    scale_for_class(Prop(1.0, "ornament density, ambition-driven"), BuildingClass.GRAND)
)


def ornament_density_scales_with_money(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The same rank decay, with ambition in it.

    Restates the base layer's relation rather than patching its output —
    rules never read each other, only the context (I1). Later layer wins, so
    this is the value that survives.

    Normalised against the grandest class instead of clamped at 1.0. Clamping
    was the first thing tried and it was wrong in a way worth recording: a
    comfortable building's rank 0, rank 1 and rank 2 storeys all multiplied
    past 1.0 and came back identical, which flattened the very decay the rule
    exists to express. A dial that saturates silently is a dial that stops
    reading — the same failure as scaling everything together.

    A7.2: the six repeat intervals come out of the same dial, in the same
    rule, for the same reason the base layer emits them together — the count
    of modillions under a cornice, of refends across a socle, of scrolls along
    a garde-corps is "the scale and density of ornament", which the brief
    lists among the PROPORTIONAL quantities. Money moving the wall's size
    while leaving its rhythm alone is the "same facade at two sizes" failure;
    money moving both is what makes a grand frontage read as finely worked
    rather than merely large.
    """
    wanted = scale_for_class(
        Prop(ornament_for_rank(ctx.rank_from_principal), "ornament density, ambition-driven"),
        ctx.klass,
    )
    density = float(wanted) / _AMBITION_CEILING
    return Properties(
        {"ornament_density": density, **ornament_modules_at(density)},
        rule="paris.qualify.klass.ornament.scales_with_money",
        specificity=SPEC_UNIVERSAL,
    )


def balcony_depth_is_absolute_under_the_ordonnance(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The depth is ABSOLUTE (0.60 m, printed twice); the cap is REGULATORY.

    **A9.4 turned this rule inside out and it is the more honest for it.**
    It used to read "wanted depth is PROPORTIONAL; the 0.80 m cap is
    REGULATORY", and pointed at the grand building being clipped as proof
    that carrying the kinds around was worth it. Daly's two printed callouts
    — 0.600 m and 0.590 m, on two buildings — say the depth never wanted to
    be proportional at all. It is a body's, exactly like the door beneath it,
    and the ``min`` below is now *never* the binding constraint on anything
    Daly drew.

    The ``min`` stays, and stays meaningful, because the two numbers are
    still two kinds and an earlier or stricter ordonnance is still entitled
    to bind: what changed is that the model no longer manufactures a
    collision in order to have one to point at. ``scale_for_class`` is still
    called, and is a documented no-op on an ``Abs`` — which is the mechanism
    demonstrating itself rather than being asserted.

    Applicability: a floor the ordonnance permits a balcony on. ``SPEC_ROLE``.
    """
    ordonnance = balcony_rule(
        [ctx.level_above_pavement], era_for_year(ctx.year), second_line=False
    )
    if ctx.level_above_pavement < float(ordonnance.min_height) - _EPS:
        return None
    wanted = scale_for_class(_BALCONY_PROJECTION, ctx.klass)  # ABSOLUTE: a no-op
    cap = ordonnance.max_projection  # Reg — never scaled, by construction
    return Properties(
        {"balcony_projection": min(float(wanted), float(cap))},
        rule="paris.qualify.klass.balcony.absolute_depth_under_the_ordonnance",
        specificity=SPEC_ROLE,
    )


def surround_is_what_the_owner_could_afford(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """Pick the richest surround this class reaches, read down by rank.

    One expression, two axes: the class sets the ceiling, the rank from the
    principal floor decides how far below that ceiling this storey sits. No
    per-floor row, and no per-class copy of the floor list.

    Applicability: a bay, **above the base block**. ``SPEC_SLOT``.

    The base exclusion is A6.7's. This ladder is a ladder of stone frames
    around windows in a wall, and the ground floor of a Paris immeuble is not
    that: it is a devanture or a plain-faced socle, with its own vocabulary,
    which the base layer reads out of the catalogue. Left unexcluded, the top
    of this ladder put a bare pediment in the enseigne band over every shop
    window on the block — a later layer overruling a rule that was right,
    with money, about something money does not decide.

    **A13.1** widens the exclusion from the base storey to the base BLOCK, for
    exactly the reason A6.7 gave: the entresol belongs to the base, its arch
    is cut in the base's own coursing, and the top of this ladder was putting
    a pediment over it — a stone frame from the residential vocabulary
    standing on a storey that has none.
    """
    if ctx.stands_in_the_base_block or not carries_an_ordinary_window(ctx, rng):
        return None
    ladder = _AFFORDABLE_SURROUND[ctx.klass]
    richness = ornament_for_rank(ctx.rank_from_principal)
    # richness in [0, 1] indexes the ladder from meanest to richest
    step = min(len(ladder) - 1, int(richness * len(ladder)))
    return Properties(
        {"surround_kind": ladder[step], "surround_richness": richness},
        rule="paris.qualify.klass.surround.what_the_owner_could_afford",
        specificity=SPEC_SLOT,
    )


def modest_frontages_carve_only_the_noble_floor(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A modest building pays for sculpture once, over the good windows.

    Applicability: a modest frontage, on a bay that is not the noble floor.
    ``SPEC_SLOT_AND_ROLE``, above the base layer's presence rule and above
    this layer's other rules, none of which touch ``keystone_present``.
    """
    if ctx.klass is not BuildingClass.MODEST:
        return None
    if ctx.rank_from_principal == 0 or not carries_an_ordinary_window(ctx, rng):
        return None
    return Properties(
        {"keystone_present": False},
        rule="paris.qualify.klass.keystone.modest_carves_only_the_noble_floor",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def cornice_weight_scales_with_ambition(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """"The projection of a cornice relative to the height it crowns" is the
    brief's own example of a proportional quantity. So it scales, here, once.

    Applicability: the topmost habitable storey. ``SPEC_ROLE``.
    """
    if not ctx.is_topmost_habitable:
        return None
    wanted = scale_for_class(
        Prop(0.28 * ctx.slot_h, "cornice projection relative to the storey it crowns"),
        ctx.klass,
    )
    return Properties(
        {
            "cornice_projection": float(wanted),
            "cornice_richness": float(
                scale_for_class(
                    Prop(ornament_for_rank(ctx.rank_from_principal), "cornice richness"),
                    ctx.klass,
                )
            )
            / _AMBITION_CEILING,
        },
        rule="paris.qualify.klass.cornice.weight_scales_with_ambition",
        specificity=SPEC_ROLE,
    )


# ===========================================================================
# How big the opening is — the contrast the eye reads as scale
# ===========================================================================
#
# An opening is NOT a bay. The bay is the slot phase 1 solved; the opening is
# the hole cut in the wall that fills it, and between the two there is a pier
# either side, a spandrel below the sill and a course of masonry over the
# lintel. Emitting the bay's own rectangle as the opening's — which is what
# this file used to leave the renderer to do — turns a stone facade into a
# curtain wall, and no amount of ornament on top of it repairs that.
#
# It lives in the CLASS layer because size is where the brief's split becomes
# visible:
#
#   "The grand building on the boulevard is legible as grand precisely
#    because its doorway is only a little bigger than the modest one's while
#    its windows are much bigger."
#
# So the window is here, going through `scale_for_class` like everything else
# in this file, and the porte cochère is NOT here at all — it is in the base
# layer, sized by a carriage, and the class layer has no opinion about it.
# The contrast between those two facts is the mechanism. The absolute numbers
# that bound the opening vertically (the sill a body leans on, the lintel a
# floor bears on) are in `catalogue` and reach the geometry unscaled.


def _geometry_props(geom, asked_sill: float) -> dict[str, object]:
    """The three numbers a geometry rule always states, and the fourth it
    states only when it had to.

    The sill is a body fact and belongs to the base layer, which says *why* it
    is where it is — a lean, a step, a threshold walked over. This layer
    restating the same number would put its own summary ("...its size is
    ambition") against a property ambition had nothing to do with, and the
    trace would read as though money had chosen the sill. So it is emitted
    here only in the one case where the class layer genuinely moved it: a
    storey too short to hold the sill, the shortest useful light and a lintel
    at once, where ``catalogue`` drops the sill rather than emit an opening of
    no height.
    """
    props: dict[str, object] = {
        "opening_width": geom.width,
        "opening_height": geom.height,
        "opening_offset_x": geom.offset_x,
    }
    if abs(geom.sill - asked_sill) > 1e-9:
        props["opening_sill_height"] = geom.sill
    return props


def window_size_is_what_the_bay_and_the_owner_allow(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A window is a tall rectangle cut in a wall, and its size is ambition.

    Width is ``opening_window``'s band resolved for this class and fitted
    into the slot with ``pier_filler``'s own minimum left standing either
    side — the pier is the catalogue's masonry module, never a margin
    invented to make the drawing look right. Height is that width times the
    proportion the noble floor wants, cut down by whatever the storey has
    left over the ABSOLUTE sill and lintel, which is why the openings shorten
    as they go up without any rule counting floors.

    Applicability: every slot the base layer puts an ordinary window in — an
    ordinary bay, or the strip over the carriage arch. ``SPEC_SLOT``; the
    shopfront rule below is narrower and the entrance is not a window.
    """
    if opening_type_for(ctx, rng) != "window":
        return None
    sill = float(sill_height_for(ctx))
    geom = catalogue.window_in_slot(
        ctx.slot_w,
        ctx.slot_h,
        ctx.klass,
        wanted_aspect=aspect_for_rank(ctx.rank_from_principal),
        sill=sill,
    )
    return Properties(
        _geometry_props(geom, sill),
        rule="paris.qualify.klass.opening.window_size_is_ambition_within_the_bay",
        specificity=SPEC_SLOT,
    )


def shopfront_opening_is_as_wide_as_the_structure_allows(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """A devanture buys all the glass the masonry will give it.

    Not the window rule with different numbers: the trumeau between two shops
    is ``pier_filler``'s *minimum*, not its preferred width, and the vertical
    bounds are a step up from the pavement and the board carrying the shop's
    name — three ABSOLUTE facts, none of them a proportion. So a grand
    building's shopfront is bigger than a modest one's only by as much as its
    bay and its ground storey are, which is far less than the difference
    between their upper windows.

    **A17.2.** A13.2 had this rule spanning two storeys, splitting the
    devanture's two ABSOLUTE bands between them so that neither landed at the
    storey line. There is no such framework: the shopfront stands in the
    rez-de-chaussée and closes at the entablature over it, so it is one
    register with a soubassement at the pavement and an enseigne board under
    its own cornice.

    Applicability: any storey the devanture faces on a frontage that sells
    something — which ``opening_type_for`` already answers, because it is the
    same shared expression that decided the opening is a shop bay at all.
    ``SPEC_SLOT_AND_ROLE``, above the window rule it shares its keys with.
    """
    if opening_type_for(ctx, rng) != "shop_bay":
        return None
    geom = catalogue.shopfront_in_slot(
        ctx.slot_w,
        ctx.slot_h,
        ctx.klass,
    )
    asked = float(catalogue.shop_threshold_height())
    return Properties(
        _geometry_props(geom, asked),
        rule="paris.qualify.klass.opening.shopfront_is_as_wide_as_the_structure_allows",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def entresol_arcade_is_sized_by_the_storey_it_lights(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """An arcaded entresol light fills the storey it lights, not a window's
    share of it.

    Same mechanism as the ordinary window — ``catalogue.window_in_slot``, the
    ABSOLUTE width band fitted into the slot with the catalogue's own pier
    either side — asked over a *much* lower breast wall
    (``catalogue.entresol_allege_height``, a third of the height a body leans
    on). That one substitution is A13's complaint answered arithmetically: in
    a 2.66 m entresol the lean-on sill leaves 1.46 m of light and the low
    allège leaves better than 1.75 m, and because A8.4's aspect band then buys
    width with the height it has, the opening comes out both taller and wider.
    A shrunken upper-floor window becomes an entresol arch.

    The sill is restated here, unusually for this layer, because it is not the
    base layer's number being echoed: ``window_in_slot`` may drop a sill it
    cannot fit, and ``_geometry_props`` states the sill only when it moved.

    Applicability: exactly the cells ``base.entresol_is_arcaded_in_the_base_s_
    own_stone`` puts an arch in — read off ``opening_type_for``, the shared
    expression, so the two can never disagree about which slots those are.
    ``SPEC_SLOT_AND_ROLE``, above
    ``window_size_is_what_the_bay_and_the_owner_allow``, which would otherwise
    size this light off ``sill_height_for``'s lean-on sill.
    """
    if ctx.role is not Role.MEZZANINE or not ctx.has_an_entresol:
        return None
    if ctx.slot_name != "bay" and ctx.slot_name not in catalogue.ENTRANCE_SLOT_NAMES:
        return None
    if opening_type_for(ctx, rng) != "window":
        return None
    sill = float(catalogue.entresol_allege_height())
    # The head stops under the band that crowns the base. An arcade whose
    # arches run up behind their own entablature is an arch drawn through its
    # own cornice, so what must stand over this light IS that entablature —
    # ``base_entablature_depth``, the same expression the string course reads,
    # which is how the two lines meet.
    #
    # What is subtracted here is only the EXCESS, because ``window_in_slot``
    # reserves its own share over every opening and this must total the
    # entablature rather than stack on top of it. **A23 widened that share**
    # from the bare lintel bearing to the bearing plus the facade's floor band,
    # so the excess is measured against both — otherwise the entresol pays for
    # a floor band it already has, and its light loses 0.30 m, which is the
    # shrunken-window defect A13 exists to have fixed.
    over_the_head = max(
        0.0,
        base_entablature_depth(ctx)
        - float(catalogue.lintel_bearing_depth())
        - float(catalogue.floor_band_depth()),
    )
    geom = catalogue.window_in_slot(
        ctx.slot_w,
        max(0.0, ctx.slot_h - over_the_head),
        ctx.klass,
        wanted_aspect=aspect_for_rank(ctx.rank_from_principal),
        sill=sill,
    )
    return Properties(
        _geometry_props(geom, sill),
        rule="paris.qualify.klass.opening.entresol_arcade_is_sized_by_the_storey_it_lights",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def a_narrow_special_is_sized_off_its_own_module(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The odd slot gets its own module's dimensions, not a squeezed window's.

    A blind panel — and, since A6.2, a narrow window — takes the window
    geometry of the storey it stands in, so it lines up with the openings
    either side of it and reads as a panel, or a light, in the same wall. An
    oeil-de-boeuf takes ``narrow_special_oeil_de_boeuf``'s own width and is
    hung off the line of its neighbours' heads: a round window has no sill, so
    aligning its bottom with theirs would be aligning the wrong edge.

    Applicability: an inserted or edge special. ``SPEC_SLOT``; disjoint from
    the two rules above, which test the slot's name.
    """
    if not ctx.is_special:
        return None
    kind = opening_type_for(ctx, rng)
    sill = float(sill_height_for(ctx))
    neighbour = catalogue.window_in_slot(
        ctx.slot_w,
        ctx.slot_h,
        ctx.klass,
        wanted_aspect=aspect_for_rank(ctx.rank_from_principal),
        sill=sill,
    )
    if kind == "oeil_de_boeuf":
        geom = catalogue.roundel_in_slot(
            ctx.slot_w,
            ctx.klass,
            head_above_floor=neighbour.sill + neighbour.height,
        )
        # A roundel is hung off its neighbours' heads and has no sill of its
        # own, so this layer really does own its vertical position — there is
        # no base-layer body fact for it to defer to.
        asked = geom.sill
        props = _geometry_props(geom, asked)
        props["opening_sill_height"] = geom.sill
        return Properties(
            props,
            rule="paris.qualify.klass.opening.a_narrow_special_is_sized_off_its_own_module",
            specificity=SPEC_SLOT,
        )
    geom = neighbour
    return Properties(
        _geometry_props(geom, sill),
        rule="paris.qualify.klass.opening.a_narrow_special_is_sized_off_its_own_module",
        specificity=SPEC_SLOT,
    )


CLASS_RULES: tuple[Rule, ...] = (
    window_size_is_what_the_bay_and_the_owner_allow,
    shopfront_opening_is_as_wide_as_the_structure_allows,
    entresol_arcade_is_sized_by_the_storey_it_lights,
    a_narrow_special_is_sized_off_its_own_module,
    ornament_density_scales_with_money,
    balcony_depth_is_absolute_under_the_ordonnance,
    surround_is_what_the_owner_could_afford,
    modest_frontages_carve_only_the_noble_floor,
    cornice_weight_scales_with_ambition,
)
