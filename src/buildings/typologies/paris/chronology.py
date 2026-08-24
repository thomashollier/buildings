"""Date windows on feature variants -- not periods on buildings.

A vocabulary is not static across a century. Ironwork, sculpture, socle
treatment and shopfronts all turn over, at different rates, and a building is
datable precisely *because* they do. The obvious way to represent that --
sorting features into named periods -- is the wrong one, for two reasons the
brief is explicit about:

1. **Two chronologies that do not align.** Regulation changes on decree dates
   (1859, 1882, 1884, 1902); style changes on political and cultural ones
   (roughly 1848, 1853, 1870). One period enum cannot carry both without
   being wrong for one of them.
2. **The straggler is the common case, not the exception.** A period enum
   cannot represent the building that kept its outdated ironwork for twenty
   years after the fashion moved on -- and that is *most* buildings.

So the date is attached to the **variant**, never to the building: each
variant carries ``earliest`` / ``peak_from`` / ``peak_to`` / ``latest``, and a
building of year *Y* sees the variants whose windows contain *Y*, weighted by
prevalence at *Y*. Period names (Restauration, Second Empire, Belle Époque...)
survive only as comments and ``source`` prose -- never as something this
module's code branches on. That discipline is checked mechanically:
``dev/harness/check_no_period_branching.py`` greps the whole tree (except
``reglement.py``, where the regulation genuinely *is* a period enum) for
``era ==`` / ``period ==`` style comparisons and fails the build if it finds
one.

Two mechanisms live here, and they are never conflated:

- ``legal()`` -- a STEP function. Binary, and dated to the **decree** that
  made the switch, not to a regulatory era: oriels are illegal in 1881 and
  legal in 1882, by the décret du 22 juillet 1882. See ``_LEGAL_SWITCHES``
  for why the decree date, not ``reglement.era_for_year``, is the datum --
  it is point 1 above, in miniature.
- ``prevalence()`` -- a DISTRIBUTION. A continuous ramp up to a plateau and
  back down, in ``[0, 1]``. Mascarons do not appear on a date; they grow
  common through the 1870s and elaborate through the 1890s -- that sentence
  *is* the ramp.

Conflating the two gives streets where every facade of a given year is
suddenly identical, which is exactly the toy-building failure mode the brief
warns about. ``MIN_RAMP_YEARS`` is what keeps the second from decaying into
the first: a variant whose rise or fall is shorter than that is rejected at
construction, because a "fashion" that goes from unseen to universal inside a
few years is a step function wearing a ramp's clothes. The floor also bounds
what a caller sees when it samples at whole years: the largest possible
one-year change in ``prevalence`` is exactly ``1 / MIN_RAMP_YEARS``.

Availability is a function of ``(feature, year, class)``, not ``(feature,
year)``: adoption lags down the class ladder, by ten to twenty years per the
brief, and -- the detail most systems miss -- lower classes *retain*
superseded forms long after they have gone from the boulevards. This module
models both with the same mechanism: a class's whole window (start *and* end)
is shifted later by its lag. A grand building adopts on schedule and drops
the variant on schedule; a modest building adopts late *and* keeps it late,
which is the retention the brief asks for, not a second free parameter.

Shifting both ends has one consequence that has to be paid for rather than
ignored: at the *front* of the catalogue a lagged class would fall off the
edge entirely, and a modest building of 1825 would have no ironwork at all
rather than old-fashioned ironwork. So the earliest variant of every family
is an **open-front anchor**: its ``earliest`` runs back to 1770, well before
this project's working range, standing in for whatever vocabulary preceded
the one the brief dates. Its ``peak_from`` still carries the brief's own
stated decade -- the open front is a modelling convention about coverage, not
a historical claim that palmette railings were common in 1770.

Finally, construction date is not observation date: ``ElementDate`` lets an
individual element (a roof, a shopfront) carry a date that differs from the
building's own, so a facade seen in 1900 can genuinely have 1860 bones, an
1885 roof and an 1898 shopfront.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Mapping

from buildings.site import BuildingClass

from . import reglement

__all__ = [
    "Variant",
    "ElementDate",
    "LegalSwitch",
    "MIN_RAMP_YEARS",
    "OPEN_FRONT_YEAR",
    "prevalence",
    "available",
    "legal",
    "raised_comble",
    "FEATURES",
    "variants_for",
]


# ---------------------------------------------------------------------------
# Shape invariants for a fashion curve
# ---------------------------------------------------------------------------

#: Shortest rise (``earliest`` -> ``peak_from``) or fall (``peak_to`` ->
#: ``latest``) a variant may declare, in years.
#:
#: This is a *shape* invariant, not a date: it exists to stop the fashion
#: mechanism collapsing into the legality mechanism. A variant that went from
#: nothing to universal in two years would produce, at the whole-year
#: granularity every caller actually samples at, a 0.5 jump between adjacent
#: years -- a step function, which is what ``legal()`` is for and what
#: ``prevalence()`` must never be.
#:
#: Twelve years is INFERRED, and is chosen to match the resolution of the
#: source: BRIEF.md states every one of these windows at decade granularity
#: ("1820s-40s", "common from the 1870s"), so no boundary here is known to
#: better than roughly a decade anyway, and pretending to a two-year
#: transition would be false precision. The bound it buys is exact and
#: testable: ``max |prevalence(v, y+1) - prevalence(v, y)| == 1 / 12``.
MIN_RAMP_YEARS: int = 12

#: ``earliest`` for the open-front anchor variant of each family -- see the
#: module docstring. INFERRED: it is not a date the source gives, it is a
#: coverage convention, chosen far enough back that no class's adoption lag
#: can push the front of the catalogue past the start of the working range.
OPEN_FRONT_YEAR: int = 1770


# ---------------------------------------------------------------------------
# Adoption-lag schedules
# ---------------------------------------------------------------------------
#
# INFERRED (BRIEF.md gives only the qualitative bracket "ten to twenty years",
# not per-feature numbers): three reusable lag schedules, keyed by
# BuildingClass and expressed as years BEHIND GRAND (which is 0 by
# definition -- the boulevard sets the pace, everything else follows it).
#
# Every MODEST figure below sits inside the brief's stated ten-to-twenty-year
# bracket. That is a deliberate constraint on this table: an earlier draft
# used a 60-year modest lag for "elite" features so that Art Nouveau ironwork
# would never reach a modest street, which reads the brief's "if ever" as a
# licence to invent a number four times larger than the only figure the
# source actually gives. It is not. "If ever" is a statement about the
# *working range*, and it comes out of the arithmetic on its own: a fashion
# that starts in 1893 and lags twenty years to modest streets simply has not
# arrived by 1910, without anyone having to reach for a bigger lag.
#
# _ADOPTION_LAG is the default, used by the ordinary run of variants below.
# _ELITE_LAG is for features the brief explicitly restricts to grand
# buildings (figurative sculpture, avant-garde ironwork): the same bracket,
# taken at its top end rather than its middle.
# _FAST_LAG is for shopfronts, which the brief singles out as turning over
# "fastest": commerce chases fashion faster than masonry does, so the lag
# schedule is compressed rather than stretched.

_ADOPTION_LAG: Mapping[BuildingClass, int] = MappingProxyType(
    {
        BuildingClass.GRAND: 0,
        BuildingClass.COMFORTABLE: 6,
        BuildingClass.ORDINARY: 12,
        BuildingClass.MODEST: 18,
    }
)

_ELITE_LAG: Mapping[BuildingClass, int] = MappingProxyType(
    {
        BuildingClass.GRAND: 0,
        BuildingClass.COMFORTABLE: 7,
        BuildingClass.ORDINARY: 13,
        BuildingClass.MODEST: 20,
    }
)

_FAST_LAG: Mapping[BuildingClass, int] = MappingProxyType(
    {
        BuildingClass.GRAND: 0,
        BuildingClass.COMFORTABLE: 2,
        BuildingClass.ORDINARY: 4,
        BuildingClass.MODEST: 7,
    }
)


# ---------------------------------------------------------------------------
# Variant
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Variant:
    """One dated form a feature can take.

    ``earliest``/``latest`` bound the window a building of that exact year
    might plausibly show the variant at all (weight 0 *at* and outside those
    bounds); ``peak_from``/``peak_to`` bound the plateau where it is at its
    most common/elaborate (weight 1 inside it). All four are GRAND-class
    years; ``class_lag`` shifts the whole window later, per class, for both
    ends at once -- see the module docstring for why one shift models both
    lag and retention.

    Both ramps must be at least ``MIN_RAMP_YEARS`` long; see that constant
    for why a shorter one is rejected rather than merely discouraged.

    ``source`` must always be populated (empty is a bug, not "no comment"):
    a citation to BRIEF.md's own prose where the window is stated at
    decade granularity, with the word ``INFERRED`` wherever a boundary was
    picked rather than given, per the brief's own instruction to "mark
    clearly the ones you inferred because the source was silent."
    """

    feature: str  # "ironwork" | "socle" | "keystone" | "roof" | "shopfront"
    name: str
    earliest: int
    peak_from: int
    peak_to: int
    latest: int
    class_lag: Mapping[BuildingClass, int] = field(
        default_factory=lambda: MappingProxyType({})
    )
    source: str = ""

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError(f"variant {self.name!r}: source must be non-blank")
        if not (self.earliest <= self.peak_from <= self.peak_to <= self.latest):
            raise ValueError(
                f"variant {self.name!r}: need earliest <= peak_from <= peak_to "
                f"<= latest, got {self.earliest}/{self.peak_from}/"
                f"{self.peak_to}/{self.latest}"
            )
        rise = self.peak_from - self.earliest
        fall = self.latest - self.peak_to
        if rise < MIN_RAMP_YEARS or fall < MIN_RAMP_YEARS:
            raise ValueError(
                f"variant {self.name!r}: fashion ramps must be at least "
                f"{MIN_RAMP_YEARS} years (got rise={rise}, fall={fall}). A "
                f"shorter ramp is a step function in disguise -- if this "
                f"really is a legal or regulatory switch, it belongs in "
                f"legal()/reglement.py, not in a prevalence curve."
            )
        object.__setattr__(self, "class_lag", MappingProxyType(dict(self.class_lag)))

    def window_for(self, klass: BuildingClass) -> tuple[int, int, int, int]:
        """This variant's window, shifted for ``klass``'s adoption lag."""
        lag = self.class_lag.get(klass, 0)
        return (
            self.earliest + lag,
            self.peak_from + lag,
            self.peak_to + lag,
            self.latest + lag,
        )


def prevalence(v: Variant, year: int, klass: BuildingClass) -> float:
    """Fashion: a continuous ramp/peak/decline in ``[0, 1]``. NOT a step.

    Zero at and before ``earliest``, and at and after ``latest`` (both
    shifted by the class's adoption lag); ramps linearly from 0 at
    ``earliest`` to 1 at ``peak_from``; holds at 1 across the plateau; ramps
    back down to 0 by ``latest``. Continuous at every seam by construction --
    there is no year where the value jumps, and because both ramps are at
    least ``MIN_RAMP_YEARS`` long, a caller stepping a whole year at a time
    never sees a change larger than ``1 / MIN_RAMP_YEARS``.
    """
    earliest, peak_from, peak_to, latest = v.window_for(klass)
    if year <= earliest or year >= latest:
        return 0.0
    if peak_from <= year <= peak_to:
        return 1.0
    if year < peak_from:
        return (year - earliest) / (peak_from - earliest)
    return 1.0 - (year - peak_to) / (latest - peak_to)


def available(
    feature: str, year: int, klass: BuildingClass
) -> list[tuple[Variant, float]]:
    """Variants genuinely in use in ``year`` for ``klass``, with weights.

    Weight is ``prevalence(variant, year, klass)``, and membership is
    ``weight > 0`` -- not the closed window ``earliest <= year <= latest``,
    which admits the two endpoint years where the ramp is exactly 0. The
    distinction is not pedantic: a zero-weight member is a variant nobody
    built that year, and ``DecisionStream.choice`` raises ``ValueError`` on a
    weight vector that sums to zero, so a list of them is a crash rather than
    a shrug. Everything returned here has a strictly positive weight, which
    means this list can be handed straight to ``DecisionStream.choice`` as
    ``(options, weights)``.

    Sorted most-prevalent first; ties keep catalogue order, so the result is
    deterministic for a given ``(feature, year, klass)``.
    """
    out: list[tuple[Variant, float]] = []
    for v in variants_for(feature):
        weight = prevalence(v, year, klass)
        if weight > 0.0:
            out.append((v, weight))
    out.sort(key=lambda pair: -pair[1])
    return out


# ---------------------------------------------------------------------------
# Legality -- a step on the decree date, cross-checked against reglement.py
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LegalSwitch:
    """One binary, sourced, dated change in what the law permits.

    ``year`` is the year the decree took effect -- the *step*. ``flag`` is
    the corresponding field on ``reglement.Reglement``, kept here so the two
    representations can be checked against each other at import (see
    ``_check_switches_against_reglement``) instead of drifting apart.
    """

    feature: str
    year: int
    decree: str
    flag: Callable[[reglement.Reglement], bool]
    source: str


# Why these carry their own year instead of asking ``reglement.era_for_year``:
#
# ``reglement.Era`` is a four-way split of the *envelope* regulations, on the
# hinges 1859 / 1884 / 1902. Oriel legality is not one of those hinges. It
# changed on the décret du 22 juillet 1882, two years before the Alphand
# height-table decree that starts ``Era.ALPHAND`` -- and ``reglement.py``'s
# own docstring and its ``oriels_allowed=True`` comment both say 1882, while
# its era table cannot express it. Delegating the *year* to ``era_for_year``
# therefore returned 1884 for a date the brief states outright ("Oriels are
# illegal in 1881 and legal in 1882") and the regulatory source agrees on.
#
# That is exactly the failure this module exists to prevent, one level up:
# two chronologies that do not align, forced through a single period enum,
# and wrong for one of them. The fix is the same fix -- put the date on the
# thing it belongs to. ``reglement`` keeps owning the *rule* (what an oriel
# may project, where it may start, what it may be made of); this table owns
# the *date the switch happened*, which the era split cannot represent.
_LEGAL_SWITCHES: Mapping[str, LegalSwitch] = MappingProxyType(
    {
        "oriel": LegalSwitch(
            feature="oriel",
            year=1882,
            decree="Décret du 22 juillet 1882",
            flag=lambda reg: reg.oriels_allowed,
            source=(
                "BRIEF.md: 'Legality is a step function. Oriels are illegal "
                "in 1881 and legal in 1882.' Same date in reglement.py's "
                "source list ('Décret du 22 juillet 1882 -- oriels (bow "
                "windows) permitted') and in its ALPHAND entry's own comment "
                "('1882, metal or wood'). NOT INFERRED: an exact, cited "
                "decree date. It is deliberately NOT taken from "
                "reglement.era_for_year, whose four-way envelope split "
                "cannot start before 1884."
            ),
        ),
        "balcony_individual": LegalSwitch(
            feature="balcony_individual",
            year=1884,
            decree="Décret du 23 juillet 1884 (Alphand)",
            flag=lambda reg: reg.individual_balconies,
            source=(
                "reglement.Reglement.individual_balconies, first set true by "
                "the Alphand règlement. Here the decree date and the era "
                "boundary genuinely coincide, so this entry agrees with "
                "reglement.era_for_year exactly -- which is what makes the "
                "oriel entry's two-year disagreement a real finding about "
                "the era split rather than a quirk of this table."
            ),
        ),
    }
)


def _era_spans() -> list[tuple[int, int, reglement.Era]]:
    """``(first_year, last_year, era)`` for each regulatory era.

    Derived by scanning ``reglement.era_for_year`` over a range that brackets
    every hinge, rather than reading ``reglement``'s private start table.
    Note there is no comparison against an era value anywhere here -- the era
    is used as a dictionary key, never as a branch condition.
    """
    seen: dict[reglement.Era, list[int]] = {}
    for y in range(1700, 1951):
        seen.setdefault(reglement.era_for_year(y), []).append(y)
    return [(min(ys), max(ys), e) for e, ys in seen.items()]


def _check_switches_against_reglement() -> None:
    """Import-time guard: the decree dates must agree with ``reglement``.

    For every era whose whole span lies before a switch's year, the
    corresponding ``Reglement`` flag must be false; for every era beginning
    at or after it, true. The single era that *straddles* the decree date is
    the one the era split cannot represent, and is the only one exempt --
    that exemption is the two-year oriel gap, made explicit and bounded
    instead of silently swallowed. If ``reglement.py`` ever changes, this
    raises at import rather than letting the two drift.
    """
    for switch in _LEGAL_SWITCHES.values():
        for first, last, era in _era_spans():
            flag = switch.flag(reglement.get_reglement(era))
            if last < switch.year:
                expected = False
            elif first >= switch.year:
                expected = True
            else:
                continue  # straddles the decree: the era split cannot say
            if flag is not expected:
                raise RuntimeError(
                    f"chronology/{switch.feature}: {switch.decree} says "
                    f"{expected} for {first}-{last}, but reglement says "
                    f"{flag}. One of the two is out of date."
                )


_check_switches_against_reglement()


def legal(feature: str, year: int) -> bool:
    """Legality: a STEP function, sourced. Distinct mechanism from prevalence.

    Binary and instantaneous: false right up to the decree year, true from
    it on, with nothing in between and no ramp -- the opposite of
    ``prevalence``. ``legal("oriel", 1881) is False`` and
    ``legal("oriel", 1882) is True``, on the décret du 22 juillet 1882.

    A ``feature`` with no known legal restriction -- which is every one of
    the five fashion families this module dates -- is legal at every year:
    the regulations are silent on ironwork, socle treatment, keystone
    sculpture, roof shape and shopfronts, so nothing here blocks them; only
    *fashion* (``prevalence``) governs whether they appear.

    See ``_LEGAL_SWITCHES`` for why the date lives here rather than being
    read off ``reglement.era_for_year``, and
    ``_check_switches_against_reglement`` for the guard that keeps the two
    from disagreeing anywhere the era split is capable of having an opinion.
    """
    switch = _LEGAL_SWITCHES.get(feature)
    if switch is None:
        return True
    return year >= switch.year


# ---------------------------------------------------------------------------
# Construction date vs. observation date
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ElementDate:
    """An element's own date, alongside -- not instead of -- the building's.

    "Construction date is not observation date" (BRIEF.md): a facade seen in
    1900 may have 1860 bones, an 1885 roof and an 1898 shopfront, because
    shopfronts turn over every generation or two, ironwork gets added, and
    combles were demonstrably raised after 1884 while the cornice line held.

    Any node that can plausibly be altered independently of the building it
    sits on carries one of these rather than the building's bare ``year``,
    and every ``available()``/``prevalence()`` call for that element is made
    with ``observed``, not ``building_year``.
    """

    building_year: int  # when the building itself went up
    observed: int  # when THIS element was actually built or replaced
    reason: str = ""  # why they differ, if known

    @property
    def altered(self) -> bool:
        """True when this element postdates the building itself."""
        return self.observed != self.building_year


def raised_comble(building_year: int, roof_observed_year: int) -> ElementDate:
    """The Rue de Rivoli case: the cornice line held while a later owner
    raised the comble above it. ``roof_observed_year`` is normally
    ``>= building_year``; a roof observed no later than the building itself
    is recorded plainly, with no "raised" reason attached.
    """
    reason = ""
    if roof_observed_year > building_year:
        reason = (
            "comble raised after the building went up -- the cornice line "
            "held while the roof above it was heightened later, per BRIEF.md "
            "('combles were demonstrably raised after 1884... visible along "
            "the Rue de Rivoli')"
        )
    return ElementDate(
        building_year=building_year, observed=roof_observed_year, reason=reason
    )


# ---------------------------------------------------------------------------
# The catalogue itself -- five feature families, real BRIEF.md dates
# ---------------------------------------------------------------------------
#
# BRIEF.md states these windows at decade granularity ("1820s-40s" and the
# like); the peak window is taken directly from the stated decades wherever
# given, and every earliest/latest boundary that had to be picked rather
# than read off the text is marked INFERRED in that variant's `source`, per
# the brief's own instruction. Where the brief names an exact year (the
# 1882 oriel décret via `legal()`, the 1884 Alphand comble, Castel Béranger
# 1895-98, the métro entrances of 1900), that exact year anchors the window
# instead of a decade guess.
#
# Two shape rules apply throughout and explain most of the padding:
#   * no rise or fall shorter than MIN_RAMP_YEARS (see that constant);
#   * the first variant of each family opens at OPEN_FRONT_YEAR, so that a
#     lagged class never falls off the front of the catalogue and ends up
#     with no variant at all.

IRONWORK: tuple[Variant, ...] = (
    Variant(
        feature="ironwork",
        name="lozenge_palmette",
        earliest=OPEN_FRONT_YEAR,
        peak_from=1822,
        peak_to=1842,
        latest=1858,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md ironwork: 'Thin repeating lozenges and palmettes "
            "(1820s-40s)'. peak_from/peak_to taken from the stated decades; "
            "latest INFERRED padding. earliest is the OPEN_FRONT_YEAR "
            "convention, INFERRED and not a claim about 1770: this is the "
            "family's front anchor, and without an open front a MODEST "
            "building of 1825 -- which at an 18-year lag is showing c.1807 "
            "ironwork -- would have no ironwork variant available at all."
        ),
    ),
    Variant(
        feature="ironwork",
        name="haussmannian_scrollwork",
        earliest=1842,
        peak_from=1855,
        peak_to=1880,
        latest=1896,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md ironwork: 'dense symmetrical cast scrollwork, the "
            "standard haussmannian railing (1850s-80s)'. peak_from/peak_to "
            "from the stated decades; earliest/latest INFERRED padding, "
            "sized to the MIN_RAMP_YEARS floor."
        ),
    ),
    Variant(
        feature="ironwork",
        name="renaissance_revival",
        earliest=1870,
        peak_from=1883,
        peak_to=1896,
        latest=1910,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md ironwork: 'looser Renaissance-revival variants "
            "(1880s-90s)'. peak_from/peak_to from the stated decades; "
            "earliest/latest INFERRED padding, sized to the MIN_RAMP_YEARS "
            "floor."
        ),
    ),
    Variant(
        feature="ironwork",
        name="whiplash_art_nouveau",
        earliest=1893,
        peak_from=1905,
        peak_to=1911,
        latest=1925,
        class_lag=_ELITE_LAG,
        source=(
            "BRIEF.md ironwork: 'asymmetric organic whiplash (from c. 1895; "
            "Guimard's Castel Beranger 1895-98, the metro entrances 1900)'. "
            "The two dated buildings anchor the ramp rather than the "
            "plateau: at earliest=1893 the weight is 0 and by Castel "
            "Beranger's 1895 it is still only ~0.17, which is what 'from "
            "c. 1895' should mean for a form that was avant-garde when it "
            "appeared; the metro entrances of 1900 sit at ~0.58, on the way "
            "up. peak_from/peak_to/latest INFERRED. class_lag uses the "
            "ELITE schedule -- avant-garde and concentrated on grand, "
            "architect-driven commissions, per the source's own examples. "
            "NOTE the consequence, which is arithmetic and not a fudge: "
            "1893 + a 20-year modest lag is 1913, so whiplash ironwork does "
            "not reach modest streets inside this project's working range. "
            "That IS the brief's 'ten to twenty years later, if ever'; it "
            "does not need, and no longer uses, an invented 60-year lag. "
            "COMFORTABLE (from 1900) and ORDINARY (from 1906) do reach it "
            "in range, so this is a statement about the bottom of the "
            "ladder only -- and even there the brief's other mechanism "
            "still gets you there, since 'ironwork gets added': a modest "
            "1870 building with an ElementDate observed in 1915 draws from "
            "the 1915 catalogue, whiplash included."
        ),
    ),
)

SOCLE: tuple[Variant, ...] = (
    Variant(
        feature="socle",
        name="flat_incised_refends",
        earliest=OPEN_FRONT_YEAR,
        peak_from=1822,
        peak_to=1852,
        latest=1868,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md socle: 'flat incised refends (1820s-50s)'. "
            "peak_from/peak_to from the stated decades; latest INFERRED "
            "padding. earliest is the OPEN_FRONT_YEAR convention (INFERRED, "
            "a coverage rule not a date) -- this is the family's front "
            "anchor."
        ),
    ),
    Variant(
        feature="socle",
        name="raised_bossage",
        earliest=1842,
        peak_from=1855,
        peak_to=1875,
        latest=1890,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md socle: 'raised bossage, heavy and regular "
            "(1850s-70s)'. peak_from/peak_to from the stated decades; "
            "earliest/latest INFERRED padding, sized to MIN_RAMP_YEARS."
        ),
    ),
    Variant(
        feature="socle",
        name="picturesque_rustication",
        earliest=1872,
        peak_from=1885,
        peak_to=1898,
        latest=1912,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md socle: 'exaggerated picturesque rustication, "
            "vermiculated and rock-faced (1880s-90s)'. peak_from/peak_to "
            "from the stated decades; earliest/latest INFERRED padding, "
            "sized to MIN_RAMP_YEARS."
        ),
    ),
)

KEYSTONE: tuple[Variant, ...] = (
    Variant(
        feature="keystone",
        name="plain",
        earliest=OPEN_FRONT_YEAR,
        peak_from=1818,
        peak_to=1848,
        latest=1868,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md keystone: 'plain (Restauration)'. Restauration runs "
            "roughly 1815-1830 in the usual periodisation; window widened "
            "to the mid-century since plain keystones persist below the "
            "elaboration this catalogue tracks. peak_from/peak_to/latest "
            "INFERRED -- the source names only the period, not years. "
            "earliest is the OPEN_FRONT_YEAR convention: the family's front "
            "anchor."
        ),
    ),
    Variant(
        feature="keystone",
        name="console_volute",
        earliest=1840,
        peak_from=1855,
        peak_to=1878,
        latest=1892,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md keystone: 'simple console or volute (Second Empire)'. "
            "Second Empire is 1852-1870; window widened either side for "
            "adoption lag and retention. All boundary years INFERRED -- "
            "the source names only the period."
        ),
    ),
    Variant(
        feature="keystone",
        name="mascaron",
        earliest=1858,
        peak_from=1888,
        peak_to=1902,
        latest=1918,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md keystone: 'mascaron appearing sparingly, common from "
            "the 1870s, elaborate and near-universal by the 1890s'. This "
            "sentence IS the ramp -- one variant, not three: sparse "
            "appearance is the early ramp (~0.2 through the 1860s), 'common "
            "from the 1870s' is the approach to the plateau (~0.4-0.7), and "
            "'near-universal by the 1890s' is the plateau itself. "
            "earliest/peak_from/peak_to/latest all INFERRED to reproduce "
            "that shape, since the source gives no exact years."
        ),
    ),
    Variant(
        feature="keystone",
        name="figurative_caryatid_atlante",
        earliest=1858,
        peak_from=1888,
        peak_to=1902,
        latest=1918,
        class_lag=_ELITE_LAG,
        source=(
            "BRIEF.md keystone: 'Figurative work, caryatids and atlantes "
            "follow the same curve on grand buildings.' Same window as "
            "mascaron per the source's own words ('the same curve'); "
            "class_lag uses the ELITE schedule because the source "
            "explicitly restricts this to grand buildings -- the schedule "
            "itself is INFERRED, the restriction is not. At a 20-year "
            "modest lag the window is 1878-1938, so figurative keystones do "
            "reach modest streets late in the working range, which is the "
            "brief's 'ten to twenty years later' read literally."
        ),
    ),
)

# The `roof` family dates the DORMER-AND-ORNAMENT repertoire and the covering
# material. It does NOT date the comble's geometry, and -- per Amendment A2.5
# -- none of these names may say otherwise.
#
# Comble geometry is a step function owned entirely by reglement.py: a 45
# degree plane before 1884, an arc of a circle after it, Bonnier's eighth of a
# circle continued by an oblique after 1902. That is legality, it applies on
# the decree date, and it is emphatically NOT subject to the class lag this
# module models. Dormer form, cresting and ornament are fashion: they ramp,
# they lag down the class ladder, and a modest builder keeps pedimented
# lucarnes for twenty years after the boulevards stopped fitting them.
#
# The earlier names for these three variants (`diagonal_45_pedimented_dormers`,
# `circular_arc_varied_dormers`) spelled a comble geometry into a fashion
# variant, and the two then contradicted each other in the obvious place: at
# 1885/comfortable the law says `circular_arc` while the lagged fashion draw
# returns the variant called `diagonal_45_...`. Nothing was wrong except the
# name -- the building really did have an arc comble with pedimented dormers,
# which is exactly the straggler the brief asks for -- but a name that can
# contradict the decree will eventually be read as though it did not.
# terminate.py now refuses at import any `roof` variant whose name uses the
# comble-geometry vocabulary of `reglement.RoofEnvelope`.
ROOF: tuple[Variant, ...] = (
    Variant(
        feature="roof",
        name="small_plain_dormers",
        earliest=OPEN_FRONT_YEAR,
        peak_from=1818,
        peak_to=1848,
        latest=1866,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md roof: 'plain slate slope with small dormers' -- the "
            "pre-canonical roof, dated by elimination against the "
            "documented 1853 start of the next variant. Only the dormers "
            "are dated here: the 'slate slope' half of that phrase is "
            "covering (the material axis) and comble geometry (reglement.py), "
            "neither of which is a fashion. peak_from/peak_to/latest "
            "INFERRED; earliest is the OPEN_FRONT_YEAR convention, the "
            "family's front anchor."
        ),
    ),
    Variant(
        feature="roof",
        name="pedimented_dormers",
        earliest=1847,
        peak_from=1859,
        peak_to=1884,
        latest=1898,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md roof: '45 degree comble with pedimented dormers "
            "(canonical 1853-84)'. The 45-degree comble in that phrase is "
            "the Reglement du 27 juillet 1859's envelope and belongs to "
            "reglement.py; what is dated here is the pedimented LUCARNE. "
            "The window is unchanged by that split, because BRIEF.md dates "
            "the dormer itself -- 'canonical 1853-84' -- and both ends are "
            "read off that sentence rather than off a decree: peak_from is "
            "the 1859 Reglement, which is when the canonical dormer arrived "
            "with the canonical roof it stood on, and peak_to is the brief's "
            "own 1884. earliest/latest INFERRED -- the 14-year tail is "
            "retention, not regulation: the 1884 decree governs what "
            "geometry a comble may have, not what a lucarne may look like, "
            "and pedimented dormers went on being fitted, to ARC combles, by "
            "conservative builders long after it. That combination is not a "
            "contradiction and terminate.py no longer reads it as one."
        ),
    ),
    Variant(
        feature="roof",
        name="varied_dormers_iron_cresting",
        earliest=1882,
        peak_from=1894,
        peak_to=1906,
        latest=1920,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md roof: 'curved arc comble, taller and more elaborate, "
            "with varied dormer shapes and iron cresting (1884+)'. Note "
            "carefully what is and is not dated here. The ENVELOPE switch "
            "-- 45-degree diagonal to circular arc, on the Decret du 23 "
            "juillet 1884 (Alphand) -- is a step, and reglement.py already "
            "owns it; this variant is the DECORATIVE repertoire that grows "
            "on that envelope (varied dormer shapes, iron cresting), which "
            "is a fashion and ramps. Pinning peak_from to 1884 would have "
            "made this curve a two-year cliff, i.e. a copy of the "
            "regulatory step under a different name -- the exact conflation "
            "BRIEF.md warns against. earliest padded 2yr ahead of the "
            "decree for buildings begun just before it; "
            "peak_from/peak_to/latest INFERRED."
        ),
    ),
    Variant(
        feature="roof",
        name="zinc_roofing",
        earliest=1840,
        peak_from=1858,
        peak_to=1900,
        latest=1914,
        class_lag=_ADOPTION_LAG,
        source=(
            "BRIEF.md roof: 'Zinc becomes the dominant Parisian roofing "
            "material mid-century.' A MATERIAL axis, independent both of the "
            "DORMER-AND-ORNAMENT repertoire above (it can co-occur with any "
            "of the three) and of the comble geometry the decree fixes. All "
            "years INFERRED around 'mid-century'."
        ),
    ),
)

SHOPFRONT: tuple[Variant, ...] = (
    Variant(
        feature="shopfront",
        name="timber_small_panes",
        earliest=OPEN_FRONT_YEAR,
        peak_from=1818,
        peak_to=1848,
        latest=1862,
        class_lag=_FAST_LAG,
        source=(
            "BRIEF.md shopfront: 'timber with small panes, pilasters and a "
            "painted fascia (1820s-50s)'. peak_from/peak_to from the "
            "stated decades; latest INFERRED padding; earliest is the "
            "OPEN_FRONT_YEAR front-anchor convention. class_lag uses the "
            "FAST schedule -- 'shopfronts turn over fastest' per BRIEF.md."
        ),
    ),
    Variant(
        feature="shopfront",
        name="cast_iron_larger_panes",
        earliest=1840,
        peak_from=1855,
        peak_to=1872,
        latest=1886,
        class_lag=_FAST_LAG,
        source=(
            "BRIEF.md shopfront: 'cast-iron framing with larger panes "
            "(1850s+)'. peak_from from the stated decade; "
            "earliest/peak_to/latest INFERRED. FAST class_lag, as above."
        ),
    ),
    Variant(
        feature="shopfront",
        name="plate_glass",
        earliest=1860,
        peak_from=1875,
        peak_to=1890,
        latest=1904,
        class_lag=_FAST_LAG,
        source=(
            "BRIEF.md shopfront: 'plate glass (1870s+)'. peak_from from the "
            "stated decade; earliest/peak_to/latest INFERRED. FAST "
            "class_lag, as above."
        ),
    ),
    Variant(
        feature="shopfront",
        name="devanture_elaborate",
        earliest=1880,
        peak_from=1893,
        peak_to=1906,
        latest=1920,
        class_lag=_FAST_LAG,
        source=(
            "BRIEF.md shopfront: 'elaborate carved devantures, mosaic "
            "stall risers, gilded lettering on glass (1890s+)'. "
            "peak_from from the stated decade; earliest/peak_to/latest "
            "INFERRED as the project horizon. FAST class_lag, as above."
        ),
    ),
)


FEATURES: tuple[str, ...] = ("ironwork", "socle", "keystone", "roof", "shopfront")

_CATALOGUE: Mapping[str, tuple[Variant, ...]] = MappingProxyType(
    {
        "ironwork": IRONWORK,
        "socle": SOCLE,
        "keystone": KEYSTONE,
        "roof": ROOF,
        "shopfront": SHOPFRONT,
    }
)


def variants_for(feature: str) -> tuple[Variant, ...]:
    """All catalogued variants of ``feature``, regardless of date or class."""
    return _CATALOGUE.get(feature, ())
