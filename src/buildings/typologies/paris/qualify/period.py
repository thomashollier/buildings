"""The period layer — the same frontage, dated.

Nothing in this file names a period. There is no ``Era``, no
``SECOND_EMPIRE``, no ``if year > 1884``. Every rule here asks
``chronology.available(feature, year, klass)`` for the variants genuinely in
use for that building's date *and class* — adoption lags down the class ladder,
so a grand and a modest frontage of 1885 are not stylistic contemporaries — and
samples from them weighted by prevalence. That is the brief's requirement
stated as code: fashion is a distribution, and the building that kept its
outdated ironwork for twenty years is representable because the tail of the
distribution is still there in 1885.

The layer is thin on purpose. It sets *which* variant, never *whether* the
element exists — presence is a question about bodies, drops and openings and
belongs to the base layer. Splitting it that way is what lets the period layer
be swapped wholesale without the facade losing its railings.

### Paths

Every draw goes through ``DecisionStream.at`` on a **stable** path. The
ironwork, socle, keystone and shopfront families are drawn once per facade
(``"facade/ironwork/variant"``) rather than once per element, because a
building has one blacksmith and one sculptor, not one per window — and because
a path that is stable under adding storeys is a path you can pin in a test and
argue with later.
"""

from __future__ import annotations

from buildings.rng import DecisionStream
from buildings.site import GroundProgramme
from buildings.typologies.paris import catalogue, chronology
from buildings.typologies.paris.roles import Role
from buildings.typologies.paris.qualify.base import (
    SPEC_ROLE,
    SPEC_SLOT,
    SPEC_SLOT_AND_ROLE,
    carries_an_ordinary_window,
    crowned_by_a_carved_stone,
    devanture_faces,
)
from buildings.typologies.paris.qualify.context import Properties, QualContext, Rule

__all__ = ["PERIOD_RULES", "variant_name"]


def variant_name(feature: str, ctx: QualContext, rng: DecisionStream, path: str) -> str | None:
    """Sample one variant of ``feature`` for this building's date and class.

    Returns ``None`` — no opinion, not a crash and not a default — when the
    catalogue offers nothing for that ``(feature, year, klass)``. A silent
    fallback would be worse than silence: it would put a variant on a facade
    whose date cannot support it, and no trace would say so.
    """
    options = chronology.available(feature, ctx.year, ctx.klass)
    if not options:
        return None
    variants = [v for v, _ in options]
    weights = [w for _, w in options]
    return rng.choice(path, variants, weights).name


def ironwork_of_its_date(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Which railing. Thin lozenges, haussmannian scrollwork, Renaissance
    revival or Guimard's whiplash — decided by the date's distribution, not by
    a period test.

    Applicability: any storey above the base, matching the base layer's
    ``garde_corps`` exactly so a variant is never named for an element that is
    not there, and reading no horizontal fact for the same reason it does —
    the continuous railing along a balcon filant is a storey-scope element.
    ``SPEC_ROLE``.
    """
    if ctx.role is Role.BASE or ctx.within_comble:
        return None
    name = variant_name("ironwork", ctx, rng, "facade/ironwork/variant")
    if name is None:
        return None
    return Properties(
        {"ironwork_variant": name},
        rule="paris.qualify.period.ironwork.of_its_date",
        specificity=SPEC_ROLE,
    )


def socle_of_its_date(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Flat incised refends, raised bossage, or picturesque rustication.

    Applicability: the base BLOCK — the rez-de-chaussée and the entresol over
    it (A13.1), matching ``base.socle_carries_the_wall`` exactly so a
    treatment is never named for a storey that has no socle and never
    withheld from one that does. One draw, one path, so the two levels are
    coursed in the same stone: at 120 bd de Sébastopol the entresol's arches
    are cut in the ground floor's own ashlar, and a second draw here would be
    a second mason. ``SPEC_ROLE``.
    """
    if not ctx.stands_in_the_base_block:
        return None
    name = variant_name("socle", ctx, rng, "facade/socle/variant")
    if name is None:
        return None
    return Properties(
        {"socle_treatment": name},
        rule="paris.qualify.period.socle.of_its_date",
        specificity=SPEC_ROLE,
    )


def keystone_of_its_date(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Plain, console, mascaron or figurative — one sculptural programme for
    the whole facade, drawn from the date's distribution.

    Applicability: a cell whose opening is closed by a carved stone, above the
    base — the strip over the entrance included, which is where ``slot_name ==
    "bay"`` used to leave a bare column of un-keystoned windows, and (A14.1)
    the agrafe at the crown of a two-storey entrance arch. One building, one
    sculptor: the agrafe comes off the same ``facade/keystone/variant`` draw
    as every other carved stone on the frontage, which is why this widens
    rather than growing a second rule with a second path. ``SPEC_SLOT``.
    """
    if ctx.role is Role.BASE or not crowned_by_a_carved_stone(ctx, rng):
        return None
    name = variant_name("keystone", ctx, rng, "facade/keystone/variant")
    if name is None:
        return None
    return Properties(
        {"keystone_kind": name},
        rule="paris.qualify.period.keystone.of_its_date",
        specificity=SPEC_SLOT,
    )


def keystone_richer_on_the_noble_floor(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """The noble floor takes the most elaborate keystone the date allows.

    Not a different mechanism — the same ``available()`` list, read for its
    most prevalent *non-plain* member instead of sampled. Sits at
    ``SPEC_SLOT_AND_ROLE``, above ``keystone_of_its_date``, which is the
    specificity mechanism doing exactly what it is for: a narrower rule beats
    a broader one inside one layer, with no ordering games between layers.
    """
    if ctx.rank_from_principal != 0 or not carries_an_ordinary_window(ctx, rng):
        return None
    options = chronology.available("keystone", ctx.year, ctx.klass)
    elaborate = [(v, w) for v, w in options if v.name != "plain"]
    if not elaborate:
        return None
    best = max(elaborate, key=lambda pair: pair[1])[0]
    return Properties(
        {"keystone_kind": best.name},
        rule="paris.qualify.period.keystone.richer_on_the_noble_floor",
        specificity=SPEC_SLOT_AND_ROLE,
    )


def shopfront_of_its_date(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """Timber and small panes, cast iron, plate glass, or a carved devanture.

    Shopfronts turn over fastest of the five families, which is why the brief
    calls them the best carrier of the observation-date idea. That idea is
    *available* here — ``chronology.ElementDate`` exists and
    ``chronology.raised_comble`` uses it — but no observation year reaches
    this phase: ``SiteContext`` carries only the construction year. So this
    rule dates the shopfront to the building, and the report says so.

    Applicability: every storey the devanture's framework stands in front of,
    on a frontage that sells something — the rez-de-chaussée, and the entresol
    too where the devanture absorbed it (A13.2). One draw on one path, because
    a building has one shopfitter and the upper register of a framework is not
    glazed by a different decade from its lower one. ``SPEC_ROLE``.
    """
    if not devanture_faces(ctx, rng):
        return None
    if ctx.ground not in (GroundProgramme.SHOP, GroundProgramme.CAFE):
        return None
    name = variant_name("shopfront", ctx, rng, "facade/shopfront/variant")
    if name is None:
        return None
    return Properties(
        {
            "shopfront_variant": name,
            # The devanture's form and the size of sheet it was glazed with
            # are one fact, resolved together: "timber with small panes" and
            # "plate glass" name the same shop window under two different
            # manufacturing limits. Stated here so nobody downstream has to
            # choose how many glazing bars cross a shop window — which is
            # what the renderer was doing, at 1.5 m centres across the whole
            # frontage, in contradiction of the structural bays.
            "shopfront_pane_max_span": float(catalogue.shopfront_pane_max_span(name)),
        },
        rule="paris.qualify.period.shopfront.of_its_date",
        specificity=SPEC_ROLE,
    )


PERIOD_RULES: tuple[Rule, ...] = (
    ironwork_of_its_date,
    socle_of_its_date,
    keystone_of_its_date,
    keystone_richer_on_the_noble_floor,
    shopfront_of_its_date,
)
