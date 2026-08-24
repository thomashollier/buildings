"""The module catalogue: named building blocks and their dimensional limits.

Per the brief's "module model": a facade is a row of modules of a few kinds
-- openings, filler (piers), ends, doors -- each with a *range* of
acceptable widths, fed to the generic solver in ``solver.fitting``. This
module is the vocabulary those ranges come from, and every one of them is
built with ``buildings.quantity`` so the kind travels with the number:

- **Doors are ABSOLUTE.** "A carriage entrance must admit a carriage; it
  does not scale with the building." Both the pedestrian entrance and the
  carriage entrance (porte cochère) are set by what has to pass through
  them, not by how grand the building is -- so they are ``Abs`` and pinned
  in the solver (``SlotKind.FIXED``, ``rigid=True``), and ``to_slot_spec``
  proves it: ``scale_for_class`` is a documented no-op on them. **A14 adds
  the sharpest case of this**: an entrance may rise two storeys as one round
  arch, and its width is still the same number to the centimetre -- Daly's
  tall arches measure 2.57-2.62 m against one-storey arches of 2.41-2.67 m.
  Height is composition; width is a carriage. ``two_storey_entrance_arch``
  takes its width by calling the one-storey ``entrance_in_slot``, so the two
  cannot diverge even by accident.
- **Openings, filler and ends are PROPORTIONAL.** Bay width, the pier/opening
  ratio and how much the ends can stretch are compositional -- "ambition and
  budget show up" there, per the brief -- so they carry ``Prop`` and DO move
  under ``scale_for_class``, together, as the one coherent shift the brief
  asks for.
- **The 2.60 m storey minimum is REGULATORY**, and it already lives in
  ``reglement.py`` (``Reglement.min_floor_height``, from the 1859 hygiene
  provisions). ``storey_minimum_height`` here is a thin, sourced wrapper --
  not a second copy of the number -- so there is exactly one place that
  figure can drift out of date.

Each ``ModuleSpec`` below states ONE canonical width per bound, at the same
implicit reference point ``scale_for_class`` treats as its 1.0x factor
(``BuildingClass.ORDINARY``). Class-specific widths are never hand-authored
here; they come out of calling ``to_slot_spec(klass)``, which is the only
place in this module ``scale_for_class`` is called -- matching
``quantity.py``'s own rule that it is called nowhere else.

Numeric values without a specific citation are the generator's own working
figures for a plausible haussmannian bay grid (comparable in scale to the
historically-tuned proportions in the prior implementation's
``core/profile.py``), marked INFERRED rather than presented as sourced fact.

**A9.4 — what is SOURCED here, and on what.** Four of this module's numbers
are no longer INFERRED: the carriage door's clear width, the pedestrian
door's, the ordinary window's opening width, and the floor structure over an
opening. All four come from the measurement pass over César Daly's 1864
plates (``dev/reference/daly_measurements.json``), and each citation names
the plate and says whether the figure was **printed on the plate** or **read
off its scale bar** — the latter carrying the corpus's own ±10 % error bar,
established by measuring one building (26 rue Bergère) twice independently
and by one scale-bar reading of 2.99 m sitting against a printed 2.600 m on
the same door. Where a printed callout exists it is the one used.

Everything Daly's sample could not carry — the comble's share of the
building, the cornice band's depth, the aspect of an upper-storey opening,
the entresol's opening shape, bay pitch as a function of class — is
deliberately still INFERRED. A thin number promoted to SOURCED would be
worse than no number at all, because the marker is what tells a later stage
which figures are still open.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from buildings.quantity import Abs, Prop, Quantity, Reg, scale_for_class
from buildings.site import BuildingClass, GroundProgramme
from buildings.solver.fitting import SlotKind, SlotSpec

from . import reglement

#: The source every SOURCED figure in this module is read from, written once
#: so that seventeen citations cannot drift into seventeen spellings of one
#: book. Callers append the plate and the *kind* of reading — the two things
#: that decide how much the number is worth.
DALY_1864 = (
    "Daly 1864 (César Daly, L'Architecture privée au XIXme siècle sous "
    "Napoléon III, Sér. 1 Vol. 1 t. 2)"
)

#: What a scale-bar reading is worth in this corpus, in the corpus's own
#: words. Appended to every measured (as opposed to printed) figure, because
#: a number whose error bar is not travelling with it will eventually be
#: treated as exact by somebody who did not read this file.
SCALE_BAR = "scale-bar measured, ±10 %"
PRINTED = "printed dimension on the plate"

#: Float slack for comparing a dimension against a dimension. Small enough
#: that no real slot passes a check it should fail, large enough that a sum
#: of catalogue quantities compared against itself does not fail one on the
#: last bit (``3.40 + 0.30`` is ``3.6999999999999997``).
_EPS = 1e-9


class EntranceCannotFit(ValueError):
    """An entrance was asked for where its ABSOLUTE dimensions do not fit.

    The base of ``CarriageCannotPass`` and the exception a *porte piétonne*
    raises for the same reason. Every immeuble has exactly one entrance
    (A6.1), and an entrance is ABSOLUTE in width and height — it is the ruler
    the eye measures the facade against. So when the slot or the storey
    cannot give it its clear dimensions the honest answer is that the
    combination is wrong, not that the door got smaller: a shrunken entrance
    would silently destroy the one fixed reference the whole composition is
    read against.
    """


class CarriageCannotPass(EntranceCannotFit):
    """A porte cochère was asked for where a carriage physically could not go.

    Raised, never absorbed. The brief's rule is that a carriage entrance is
    ABSOLUTE — "it does not scale with the building" — and the only honest
    reading of that is that when the frontage or the storey cannot give the
    opening its clear dimensions, the *combination* is wrong, not the
    dimensions. Returning a smaller door instead would be the catalogue
    quietly deciding a carriage had got smaller.

    It names a phase-1 problem: the situation asked for a programme the
    structure it was given cannot carry. The cure is to raise the ground
    storey (``carriage_storey_height``) or widen the slot
    (``carriage_slot_width``), both of which phase 1 already does for every
    site it generates — so in practice this fires only on a hand-built grid.
    """


__all__ = [
    "EntranceCannotFit",
    "CarriageCannotPass",
    "ModuleSpec",
    "facade_end",
    "pier_filler",
    "opening_window",
    "opening_height_at_the_nobile",
    "standard_bay",
    "door_pedestrian",
    "door_carriage_entrance",
    "narrow_special_half_bay",
    "narrow_special_blind_panel",
    "narrow_special_oeil_de_boeuf",
    "storey_minimum_height",
    "sill_lean_height",
    "balustrade_child_gap_max",
    "lintel_bearing_depth",
    "minimum_light_height",
    "minimum_light_width",
    "shop_threshold_height",
    "shopfront_fascia_depth",
    "entresol_allege_height",
    "carriage_clear_height",
    "carriage_jamb_width",
    "carriage_slot_width",
    "carriage_storey_height",
    "pedestrian_jamb_width",
    "pedestrian_clear_height",
    "pedestrian_slot_width",
    "pedestrian_storey_height",
    "ENTRANCE_CARRIAGE",
    "ENTRANCE_PEDESTRIAN",
    "ENTRANCE_SLOT_NAMES",
    "ENTRANCE_OPENING_TYPES",
    "Entrance",
    "entrance_for",
    "entrance_slot_width",
    "entrance_storey_height",
    "entrance_in_slot",
    "ENTRANCE_ARCH_ONE_STOREY",
    "ENTRANCE_ARCH_TWO_STOREY",
    "ENTRANCE_ARCH_LEAVES",
    "ENTRANCE_ARCH_HEAD",
    "ENTRANCE_ARCH_HEAD_OPENING",
    "TWO_STOREY_ARCH_RATE",
    "TWO_STOREY_ARCH_RATE_CARRIAGE",
    "two_storey_arch_rate",
    "round_arch_rise",
    "TwoStoreyEntranceArch",
    "two_storey_entrance_arch",
    "two_storey_entrance_arch_fits",
    "pedestrian_entrance_in_slot",
    "shopfront_pane_max_span",
    "ground_floor_surround",
    "opening_aspect_band",
    "OpeningGeometry",
    "window_in_slot",
    "shopfront_in_slot",
    "carriage_entrance_in_slot",
    "roundel_in_slot",
]


@dataclass(frozen=True)
class ModuleSpec:
    """A named module's width bounds, each carrying its own ``Quantity``.

    ``minimum``/``preferred``/``maximum`` are ordinarily all the same
    ``Kind`` (a door's three bounds are all ``Abs`` together; a bay's are
    all ``Prop`` together), but nothing here *requires* that -- ``to_slot_spec``
    scales whichever bounds are ``PROPORTIONAL`` and leaves ``ABSOLUTE``/
    ``REGULATORY`` bounds untouched no matter which bound they land on, so a
    mismatched module degrades safely rather than silently.
    """

    name: str
    slot_kind: SlotKind
    minimum: Quantity
    preferred: Quantity
    maximum: Quantity
    elasticity: float = 1.0

    def to_slot_spec(self, klass: BuildingClass) -> SlotSpec:
        """Resolve this module for ``klass`` into a solver ``SlotSpec``.

        The only place ``scale_for_class`` is called in this module. A
        rigid (``ABSOLUTE``/``REGULATORY``) module's bounds come back
        bit-for-bit unchanged for every class -- ``scale_for_class`` is a
        documented no-op on them -- which is what lets a caller assert "the
        carriage entrance does not change under ``scale_for_class``" and
        "bay width does" directly against this method's output.
        """
        lo = scale_for_class(self.minimum, klass)
        pref = scale_for_class(self.preferred, klass)
        hi = scale_for_class(self.maximum, klass)
        return SlotSpec(
            name=self.name,
            kind=self.slot_kind,
            minimum=float(lo),
            preferred=float(pref),
            maximum=float(hi),
            elasticity=self.elasticity,
            rigid=pref.rigid,
        )


# ---------------------------------------------------------------------------
# Ends -- the most elastic module, absorbs slack first
# ---------------------------------------------------------------------------


def facade_end() -> ModuleSpec:
    """The margin at either edge of the facade.

    PROPORTIONAL: how generous a facade's margins are is a compositional
    choice, not a body-derived one. "Ends are the most elastic, with a hard
    minimum" (BRIEF.md) -- given the highest elasticity of any module here,
    so the solver's absorption ladder reaches for it before anything else.
    INFERRED figures: a plausible edge-pier range for a haussmannian bay
    grid, not a cited measurement.
    """
    return ModuleSpec(
        name="facade_end",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Prop(0.35, "INFERRED — a masonry margin narrow enough to still read as a pier"),
        preferred=Prop(0.55, "INFERRED — typical edge-pier width on a haussmannian bay grid"),
        maximum=Prop(1.20, "INFERRED — as elastic as an end may get before it reads as its own bay"),
        elasticity=3.0,
    )


# ---------------------------------------------------------------------------
# Filler / piers
# ---------------------------------------------------------------------------


def pier_filler() -> ModuleSpec:
    """The masonry pier between two openings within a bay.

    PROPORTIONAL: "Filler is elastic; it exists to be adjusted" (BRIEF.md)
    -- second in the elasticity ordering, behind the ends and ahead of the
    opening. Descriptive here (the solver's own ``bay`` slot absorbs filler
    growth internally via its own headroom); useful to qualification rules
    that want to know the pier's own width, independent of the bay it sits
    in.
    """
    return ModuleSpec(
        name="pier_filler",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Prop(0.35, "INFERRED — narrowest pier that still reads as load-bearing masonry"),
        preferred=Prop(0.50, "INFERRED — typical interior pier width, ordinary class"),
        maximum=Prop(0.90, "INFERRED — pier growth before the opening itself must also stretch"),
        elasticity=2.0,
    )


# ---------------------------------------------------------------------------
# Openings
# ---------------------------------------------------------------------------


def opening_window() -> ModuleSpec:
    """A standard window opening — **the width half of it, and ABSOLUTE**.

    **This function is where the project's central distinction stops being a
    claim and becomes a measurement (A9.4).** One aperture, two kinds of
    number, and Daly's sixteen buildings separate them cleanly:

    ==========================  =========  =========  =========  ======
    quantity                    Première   Deuxième   Troisième  spread
    ==========================  =========  =========  =========  ======
    opening WIDTH (median)      1.139 m    1.235 m    1.070 m    ×1.25
    opening HEIGHT at nobile    2.923 m    2.236 m    2.085 m    ×1.40
    ==========================  =========  =========  =========  ======

    The width is not merely flatter — it is **non-monotonic**: the Deuxième
    median stands above the Première one, so there is no ladder in it at all,
    only a band 1.04-1.30 m wide that every building in the corpus sits
    inside. A window is a thing a person opens, leans out of and closes the
    shutters of, and it stayed the size a person is. The height at the noble
    floor, over the same three classes, moves by 40 % and moves *in order*:
    that is where the money went.

    So the width is ``Abs`` and never passes through ``scale_for_class``,
    while the height is ``opening_height_at_the_nobile`` immediately below
    and is ``Prop``. ``window_in_slot`` composes the two. It used to be
    ``Prop(0.90 / 1.15 / 1.55)`` — a single proportional band doing both
    jobs — which put a 1.55 m opening on a grand frontage (wider than any of
    the sixteen) and a 0.98 m one on a modest frontage (narrower than any of
    the sixteen), and made the height a mere consequence of the width rather
    than the place the class actually shows.

    Still ``FLEXIBLE`` in the solver, and still the least elastic of the
    three composable tiers: the band has real width, and an opening may move
    inside it. What it may not do is move *with the class*.
    """
    return ModuleSpec(
        name="opening_window",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Abs(
            1.04,
            f"SOURCED — {DALY_1864}, narrowest typical croisée in the corpus "
            f"(rue de Longchamps, Troisième Classe; {SCALE_BAR})",
        ),
        preferred=Abs(
            1.20,
            f"SOURCED — {DALY_1864}, 16 buildings across all three classes, "
            f"1.04-1.30 m, medians 1.139 / 1.235 / 1.070 by class — non-monotonic, "
            f"so ABSOLUTE. The printed croisée callout '1.300' at 2-4 boulevard de "
            f"Sébastopol and the window chain at 9 rue du Conservatoire "
            f"('2.100/1.800/0.800/0.300') anchor the band ({PRINTED})",
        ),
        maximum=Abs(
            1.30,
            f"SOURCED — {DALY_1864}, widest typical croisée in the corpus, printed "
            f"'1.300' at 2-4 boulevard de Sébastopol ({PRINTED})",
        ),
        elasticity=1.0,
    )


def opening_height_at_the_nobile() -> Quantity:
    """How tall the noble floor's window is — **the PROPORTIONAL half**.

    The twin of ``opening_window``'s ABSOLUTE width, and the reason that
    function's docstring is worth reading first: same aperture, opposite
    kind. Daly's noble-floor opening heights run **2.92 / 2.24 / 2.09 m**
    down the class ladder — monotonic, and a 1.40× spread on a quantity
    whose width moves 1.25× and moves the wrong way. All of the class signal
    in a Paris window is in its height.

    **The ORDERING is SOURCED; the value is INFERRED**, and the distinction
    matters. Daly's Première median rests effectively on one printed plate
    (the other three buildings have source-flagged uncertain floor lines),
    and the Troisième figure is two buildings; the measurement pass therefore
    marks this quantity "SOURCED for the ordering, WEAK for the Première and
    Troisième values". So what this module states is a reference height for
    the class ``scale_for_class`` treats as 1.0×, chosen so the four classes
    land across Daly's measured 2.09-2.92 m span, and what a test may assert
    is that the four heights are strictly increasing — never that any one of
    them is right to the centimetre.

    Storeys above the noble floor read down from this by rank, in
    ``window_in_slot``, through the aspect band — which is how the openings
    shorten upward without any rule counting floors.
    """
    return Prop(
        2.40,
        f"the noble floor's window height, INFERRED in magnitude; the ORDERING is "
        f"SOURCED — {DALY_1864} measures 2.923 / 2.236 / 2.085 m at the piano "
        f"nobile down the Première / Deuxième / Troisième ladder ({SCALE_BAR}, and "
        "WEAK at both ends of the ladder), against an opening width that is "
        "non-monotonic across the same sixteen buildings",
    )


def standard_bay() -> ModuleSpec:
    """The repeating unit itself: half-pier, opening, half-pier, centreline
    to centreline -- fed straight to ``solver.fitting.solve`` as ``bay``.

    PROPORTIONAL, and REPEATING per the fitting contract. Bounds are chosen
    so ``minimum``/``maximum`` bracket the combined stretch of
    ``opening_window`` and ``pier_filler`` above them, without double-scaling
    (the composed bay is its own single ``Prop`` figure, not the arithmetic
    sum of two already-``Prop`` quantities re-scaled again).
    """
    return ModuleSpec(
        name="standard_bay",
        slot_kind=SlotKind.REPEATING,
        minimum=Prop(1.95, "INFERRED — opening + two half-piers at their combined minimum"),
        preferred=Prop(2.30, "INFERRED — typical haussmannian bay width, ordinary class"),
        maximum=Prop(2.65, "INFERRED — opening + two half-piers before the rhythm reads as stretched"),
        elasticity=1.0,
    )


# ---------------------------------------------------------------------------
# Doors -- ABSOLUTE, never scale
# ---------------------------------------------------------------------------


def door_pedestrian() -> ModuleSpec:
    """The main residential entrance -- a double-leaf porte d'entrée.

    ABSOLUTE: "a door is as tall as a person plus clearance" (BRIEF.md) --
    set by the human body passing through it, not by the building's
    ambition. ``FIXED`` and pinned: it never absorbs slack, and
    ``scale_for_class`` is a no-op on every bound.

    **SOURCED (A9.4).** Daly measures eight *portes piétonnes* in Deuxième
    Classe: 1.609 / 1.630 / 1.705 / 1.740 / 1.760 / 1.776 / 1.810 / 1.910 m,
    median 1.75 m, two of them printed on the plate. The band below is that
    sample's own floor, median and ceiling. It was 1.20 / 1.40 / 1.60 —
    every bound under the measured median, which made the commoner Paris
    entrance a third narrower than the one Daly drew.

    Daly's two *Troisième* pedestrian doors are 1.36 m, narrower than any
    Deuxième door, and that figure is deliberately **not** used: n = 2 makes
    it WEAK, and using it as this band's floor would put a class ladder in a
    quantity the corpus says is absolute within its door type.
    """
    return ModuleSpec(
        name="door_pedestrian",
        slot_kind=SlotKind.FIXED,
        minimum=Abs(
            1.61,
            f"SOURCED — {DALY_1864}, narrowest of eight portes piétonnes "
            f"(No 77 boulevard de Sébastopol, Paul Mesnard, plate "
            f"daly_elevation_03; {SCALE_BAR}). Two people and a trunk pass "
            "through it",
        ),
        preferred=Abs(
            1.75,
            f"SOURCED — {DALY_1864}, median of eight portes piétonnes measured in "
            f"Deuxième Classe (1.61-1.91 m); the printed callouts '1.760' at 87 "
            f"boulevard de Sébastopol and '1.630' at 9 rue du Conservatoire bracket "
            f"it ({PRINTED})",
        ),
        maximum=Abs(
            1.91,
            f"SOURCED — {DALY_1864}, widest of eight portes piétonnes "
            f"(1 boulevard de Sébastopol; {SCALE_BAR}). Wider than this and Daly's "
            "own plates call it a carriage entrance",
        ),
    )


def door_carriage_entrance() -> ModuleSpec:
    """The porte cochère: an ABSOLUTE quantity by PLAN.md's own instruction.

    "A carriage entrance must admit a carriage; it does not scale with the
    building" (BRIEF.md). Fixed and pinned in the solver regardless of
    class -- a grand and a modest carriage entrance are the same width,
    because the carriage did not get smaller.

    **SOURCED (A9.2/A9.4), and the corpus proves the rule rather than merely
    illustrating it.** Daly measures seven carriage doors across the two top
    classes:

    ===============  ===  ==========  ==================================
    class            n    median      values
    ===============  ===  ==========  ==================================
    Première Classe  4    2.567 m     2.410, 2.534, **2.600 printed**, 2.619
    Deuxième Classe  3    2.575 m     2.570, 2.575, 2.672
    ===============  ===  ==========  ==================================

    The two medians agree to **0.4 %**. That is the finding: a carriage door
    does not scale with money because a carriage does not, and here is a
    period source saying so across the whole social range that had carriages
    at all. What *does* move with class is **entitlement** — whether the
    building gets one — and that is decided in ``entrance_for``, not here.

    The preferred width was ``Abs(3.00, "INFERRED")``, 15 % over every door
    Daly drew, and it cost more than accuracy. The slot it produced
    (3.00 + two 0.40 m jambs = 3.80 m) stood **above** the 3.40 m maximum
    ``structure`` states for a bay, and was carried up every storey, so a
    grand frontage lost a whole bay to it — 4 openings against a modest
    building's 5 on the same 16 m of street (the D6 residual). At 2.60 m
    clear the slot is 3.40 m and sits exactly at the top of the structural
    bay band, so the column over the arch is an ordinary bay like any other.
    """
    return ModuleSpec(
        name="door_carriage_entrance",
        slot_kind=SlotKind.FIXED,
        minimum=Abs(
            2.41,
            f"SOURCED — {DALY_1864}, narrowest of seven carriage doors "
            f"(3 rue de la Paix, plate daly_elevation_50; {SCALE_BAR}). Narrower "
            "than this and no carriage in the corpus would pass",
        ),
        preferred=Abs(
            2.60,
            f"SOURCED — the clear width of a porte cochère. {DALY_1864}, plan callout "
            f"'2.600' at 119 avenue des "
            f"Champs-Élysées, plates daly_elevation_49 / daly_detail_05 ({PRINTED}). "
            "The same door read off the elevation's scale bar gives 2.99 m, a 15 % "
            "error caught only because the printed value existed to check it "
            "against — which is why a printed dimension is preferred wherever one "
            "exists. Première median 2.567 m (n=4), Deuxième 2.575 m (n=3): the two "
            "classes agree to 0.4 %, so this is ABSOLUTE across the whole ladder",
        ),
        maximum=Abs(
            2.70,
            f"SOURCED — {DALY_1864}, widest of seven carriage doors is 2.672 m "
            f"(26 rue Bergère, plate daly_elevation_34; {SCALE_BAR}); rounded up to "
            "the nearest centimetre band. Wider than this is two openings, and no "
            "plate in the corpus has one",
        ),
    )


# ---------------------------------------------------------------------------
# Narrow specials -- rung 4 of the absorption ladder
# ---------------------------------------------------------------------------


def narrow_special_half_bay() -> ModuleSpec:
    """A half-width bay, inserted when slack exceeds the elastic range.

    PROPORTIONAL: still a compositional element, sized off ``standard_bay``,
    not off the body. "Five good bays plus one narrow odd one reads far
    better than six squeezed bays" (BRIEF.md) -- this is that odd one.
    """
    return ModuleSpec(
        name="narrow_special_half_bay",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Prop(0.90, "INFERRED — half of standard_bay's minimum, roughly"),
        preferred=Prop(1.35, "INFERRED — half of standard_bay's preferred width"),
        maximum=Prop(1.65, "INFERRED — half of standard_bay's maximum, roughly"),
        elasticity=1.5,
    )


def narrow_special_blind_panel() -> ModuleSpec:
    """A blank masonry panel filling a narrow gap -- no opening at all."""
    return ModuleSpec(
        name="narrow_special_blind_panel",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Prop(0.45, "INFERRED — narrowest panel that reads as deliberate, not an error"),
        preferred=Prop(0.70, "INFERRED — typical blind-panel width"),
        maximum=Prop(0.95, "INFERRED — widest before it should have been an opening instead"),
        elasticity=1.5,
    )


def narrow_special_oeil_de_boeuf() -> ModuleSpec:
    """A small round or oval window (oeil-de-boeuf), used as a narrow special."""
    return ModuleSpec(
        name="narrow_special_oeil_de_boeuf",
        slot_kind=SlotKind.FLEXIBLE,
        minimum=Prop(0.60, "INFERRED — smallest oeil-de-boeuf that still reads as glazed"),
        preferred=Prop(0.90, "INFERRED — typical oeil-de-boeuf width"),
        maximum=Prop(1.10, "INFERRED — widest before it should have been a round-headed window"),
        elasticity=1.5,
    )


# ---------------------------------------------------------------------------
# Regulatory limits -- delegated to reglement.py, never duplicated
# ---------------------------------------------------------------------------


def storey_minimum_height(year: int) -> Quantity:
    """The minimum habitable storey height in force in ``year``.

    REGULATORY: 2.60 m from the Règlement du 27 juillet 1859's hygiene
    provisions (0.0, i.e. unset, before it). Delegates to ``reglement`` --
    which already owns and sources this number -- rather than holding a
    second copy that could drift.
    """
    reg = reglement.get_reglement(reglement.era_for_year(year))
    return Reg(reg.min_floor_height, f"{reg.decree} — minimum habitable storey height")


# ---------------------------------------------------------------------------
# A few more ABSOLUTE, body-derived limits, for a rounder catalogue
# ---------------------------------------------------------------------------


def sill_lean_height() -> Quantity:
    """Height of a window sill someone can lean on without stooping.

    ABSOLUTE: set by the human body, not by the building's ambition.
    """
    return Abs(0.90, "INFERRED — a sill height an adult can lean on without bending")


def balustrade_child_gap_max() -> Quantity:
    """Maximum gap in a balcony balustrade -- narrow enough a child's head
    cannot pass through it.

    ABSOLUTE: set by the human (specifically child's) body, per BRIEF.md's
    own list of absolute quantities ("balustrade gaps narrow enough for a
    child's head").
    """
    return Abs(0.11, "INFERRED — a gap a child's head cannot pass through; not a cited French ordinance")


def lintel_bearing_depth() -> Quantity:
    """Masonry between the head of an opening and the floor above it.

    ABSOLUTE: it is the lintel stone spanning the opening plus the ends of
    the joists bearing on the wall over it. What sets it is how far stone
    spans and how deep a floor has to be to carry a room -- not how much the
    owner had to spend. A grand building's windows are much taller than a
    modest one's; the course of wall over their heads is very nearly the
    same, which is one of the two reasons a facade reads as scaled at all
    (the other is the sill below).

    **SOURCED (A9.4).** Daly prints this one twice, on two different
    buildings, and both times it is 0.30 m: the repeated "30" on the storey
    ladder of the 125 avenue des Champs-Élysées section (Première Classe),
    and the "0.300" that closes the window chain "2.100 / 1.800 / 0.800 /
    0.300" at 9 rue du Conservatoire (Deuxième Classe). Two classes, two
    printed callouts, the same number — which is exactly the signature of an
    ABSOLUTE, and the value was already right.
    """
    return Abs(
        0.30,
        f"SOURCED — {DALY_1864}, floor structure over an opening: printed '30' "
        f"repeated on the 125 avenue des Champs-Élysées storey ladder (plate "
        f"daly_coupe_76) and printed '0.300' in the window chain at 9 rue du "
        f"Conservatoire ({PRINTED}, two buildings in two classes). The lintel "
        "stone plus the joist ends bearing on the wall above it",
    )


def minimum_light_height() -> Quantity:
    """The shortest opening that still lights a room a person stands in.

    ABSOLUTE. Exists so a very short slot (an entresol, a squeezed top
    storey) degrades by dropping its sill rather than by emitting an opening
    of zero or negative height.
    """
    return Abs(0.60, "INFERRED — the shortest opening that still lights a room a person stands in")


def minimum_light_width() -> Quantity:
    """The narrowest opening that still reads as a window rather than a slit.

    ABSOLUTE, and the sideways twin of ``minimum_light_height``. It exists so
    a slot too narrow to carry a proper light — a short chamfer bay, a
    squeezed special — degrades by going blank rather than by emitting a
    loophole, which is what an arrow slit in a nineteenth-century Paris
    frontage would look like.
    """
    return Abs(0.55, "INFERRED — narrower than this is a loophole, not a window")


def shop_threshold_height() -> Quantity:
    """The *soubassement*: the boarded or stone plinth a devanture stands on.

    ABSOLUTE: it is a step, and a step is a leg. A devanture has no sill to
    lean on -- you walk through it -- so ``sill_lean_height`` is the wrong
    number for a shop bay and this is the right one. A real soubassement runs
    0.3-0.6 m -- a plinth to protect the joinery and take the knocks of the
    street, not one step's worth of rise -- and 0.15 m of it read as glass
    meeting the pavement with nothing between them (A6.9).
    """
    return Abs(0.40, "INFERRED — a boarded soubassement, 0.3-0.6 m being the documented range")


def shopfront_fascia_depth() -> Quantity:
    """The board over a devanture that carries the shop's name.

    ABSOLUTE: it is sized by the lettering a person reads from across the
    street, and it stays that size whatever the building above it cost.
    """
    return Abs(0.45, "INFERRED — the enseigne board over a devanture, sized by legible lettering")


def carriage_clear_height() -> Quantity:
    """Clear height of a porte cochère.

    ABSOLUTE, and the vertical twin of ``door_carriage_entrance``'s width:
    "a carriage entrance must admit a carriage; it does not scale with the
    building" (BRIEF.md). A laden carriage with its driver up is the ruler,
    and the driver did not get taller when the owner got richer.
    """
    return Abs(3.40, "INFERRED — a laden carriage with its driver up must pass beneath")


def carriage_jamb_width() -> Quantity:
    """The masonry either side of a porte cochère's arch.

    ABSOLUTE, and it is the reason ``carriage_slot_width`` exists. What
    carries an arch three metres across is a pier, not a margin, and its
    thickness is set by the thrust of that arch and the wall standing on it —
    neither of which knows what the owner paid. So it does not scale, and it
    is deliberately NOT ``pier_filler``'s minimum: that one is PROPORTIONAL
    and would put a wider jamb on a grand carriage entrance than a modest
    one, which is the doll's-house effect this door exists to refuse.
    """
    return Abs(
        0.40,
        "INFERRED — the jamb carrying the arch over a carriage opening; the arch's "
        "thrust does not scale with ambition, so neither does the pier under it",
    )


def carriage_slot_width() -> Quantity:
    """The piece of FACADE a porte cochère occupies: the clear opening plus a
    jamb either side.

    Every other slot in this catalogue is a piece of *wall* with its opening
    cut inside it — a 3.45 m bay carries a 1.32 m window between two real
    piers. The carriage entrance used to be the one exception: phase 1 placed
    a slot exactly one carriage wide and the opening filled it edge to edge,
    so the one element on the frontage that is genuinely a hole in the wall
    was also the only one with no masonry holding its head up. The clear
    width is unchanged and still ABSOLUTE — a carriage still has to pass —
    and what has changed is that the *slot* now includes the stone the arch
    lands on, which is what makes it a slot like every other.
    """
    return door_carriage_entrance().preferred + carriage_jamb_width() + carriage_jamb_width()


def carriage_storey_height() -> Quantity:
    """How tall the storey holding a porte cochère has to be.

    ABSOLUTE throughout: the clear height a laden carriage needs, plus the
    lintel and joist ends that have to span over it. Both figures are stated
    once, above, and added here rather than restated as a third number —
    ``structure`` used to carry its own 3.30 m for this, which was 0.40 m
    less than the two quantities it was supposed to be the sum of, so the
    porte cochère came out capped at 3.00 m clear: an ABSOLUTE that must pass
    being quietly overruled by a storey height that claimed to be about it.
    """
    return carriage_clear_height() + lintel_bearing_depth()


# ---------------------------------------------------------------------------
# The porte piétonne -- the other entrance, and ABSOLUTE for the same reason
# ---------------------------------------------------------------------------
#
# Every Paris immeuble has an entrance (A6.1). On the grander streets it is a
# porte cochère; on the modest ones it is a *porte piétonne* -- a double-leaf
# door under an imposte, wide enough for two people and a trunk and no wider.
# It is ABSOLUTE in exactly the way the carriage entrance is: what sets it is
# the body that passes through it, so it does not scale with ambition, and
# ``entrance_in_slot`` refuses rather than shrinks it (A5.5's rule, applied to
# the other door).


def pedestrian_jamb_width() -> Quantity:
    """The masonry either side of a porte piétonne's head.

    ABSOLUTE, and the same species of fact as ``carriage_jamb_width``: what
    carries the head over an opening is a pier, and its thickness comes from
    the load over it rather than from what the owner paid. Narrower than the
    carriage jamb because the span it carries is less than half as wide --
    which is the honest reason, not a taste.
    """
    return Abs(
        0.30,
        "INFERRED — the jamb carrying the head over a pedestrian entrance; a "
        "shorter span than a carriage arch, so a thinner pier, and neither "
        "figure knows what the building cost",
    )


def pedestrian_clear_height() -> Quantity:
    """Clear height of a porte piétonne, door leaf plus imposte.

    ABSOLUTE throughout, and stated as the two body facts it is the sum of
    rather than as one round number: a person passes under the door head, and
    the fanlight over it is what lights the hall behind. Neither grows with
    the building's ambition, which is why the entrance of a grand immeuble is
    only a little taller than a modest one's while its windows are half again
    as tall -- the contrast the whole absolute/proportional split exists to
    produce.
    """
    return Abs(
        2.10, "INFERRED — a person passes under the head of a door with room over their hat"
    ) + Abs(
        0.80,
        "INFERRED — the imposte over an entrance door, which is what lights the hall behind it",
    )


def pedestrian_slot_width() -> Quantity:
    """The piece of FACADE a porte piétonne occupies: the clear opening plus a
    jamb either side.

    The twin of ``carriage_slot_width``, and a slot for the same reason: a
    slot in phase 1 is a piece of wall with its opening cut inside it, never
    an opening flush with its own joints.
    """
    return door_pedestrian().preferred + pedestrian_jamb_width() + pedestrian_jamb_width()


def pedestrian_storey_height() -> Quantity:
    """How tall the storey holding a porte piétonne has to be.

    Clear height plus the lintel and joist ends spanning over it, exactly as
    ``carriage_storey_height`` is built -- one addition of two ABSOLUTE facts
    stated once each, so no third number can drift away from their sum.
    """
    return pedestrian_clear_height() + lintel_bearing_depth()


# ---------------------------------------------------------------------------
# Which entrance -- a decision, taken here, from class and street
# ---------------------------------------------------------------------------

#: The two entrance forms this typology knows, named once. These strings are
#: both the phase-1 SLOT name and (with the ``opening_type`` map below) what
#: qualification puts in it, so there is one spelling of each, not two.
ENTRANCE_CARRIAGE = "porte_cochere"
ENTRANCE_PEDESTRIAN = "porte_pietonne"

#: Slot names that ARE the entrance. ``context.QualContext`` and
#: ``compose.qualify_from_grid`` both ask this rather than testing a literal,
#: so adding a third entrance form is one entry here.
ENTRANCE_SLOT_NAMES: frozenset[str] = frozenset({ENTRANCE_CARRIAGE, ENTRANCE_PEDESTRIAN})

#: The ``opening_type`` each entrance slot carries on the ground storey. The
#: census that asserts "exactly one entrance per building" counts these.
ENTRANCE_OPENING_TYPES: Mapping[str, str] = {
    ENTRANCE_CARRIAGE: "carriage_entrance",
    ENTRANCE_PEDESTRIAN: "pedestrian_entrance",
}

#: ABSOLUTE. The narrowest street a carriage entrance is worth building on.
#: A porte cochère is not a wide door: it is the mouth of a passage a horse
#: and carriage drive through, off the roadway, and turn in the cour behind.
#: Below this the vehicle cannot leave the traffic to enter, so the gateway
#: leads to a yard nobody could reach -- which is why the modest streets of
#: Paris have pedestrian doors and the percées have carriage arches. The
#: number is INFERRED; the relation (a wider street earns the carriage) is
#: what is contractual.
_CARRIAGE_STREET_MINIMUM = Abs(
    12.0,
    "INFERRED — a carriage must draw out of the traffic and turn in off the "
    "roadway to use a porte cochère; on a narrower street the gateway leads "
    "to a cour nothing could reach",
)

#: Which classes keep a carriage at all. A porte cochère costs a frontage bay,
#: a passage through the ground floor and a cour behind it, and it is only
#: bought by a household that has something to drive into it.
#:
#: **This membership, not the door's width, is where class lives (A9.2).**
#: Daly's seven carriage doors are the same size in both classes that have
#: them — 2.567 m against 2.575 m, a 0.4 % difference — but the *count* is a
#: clean ladder:
#:
#:     Première Classe   4 of 4 buildings have a carriage entrance
#:     Deuxième Classe   3 of 10
#:     Troisième Classe  0 of 2
#:
#: So the class signal in a Paris entrance is ENTITLEMENT and not scaling,
#: and it is stated here as a set rather than there as a multiplier. This
#: typology's four classes straddle Daly's three: the top class always has
#: one (Première, 4/4), the bottom class never does (Troisième, 0/2), and the
#: two middle classes split — which is the closest a deterministic membership
#: can come to Daly's 3-in-10 for the middle of the ladder. Which three of
#: the ten Deuxième buildings got one is not predicted by anything in the
#: corpus (they are on streets of every width and facades of every size, and
#: n = 3), so nothing here pretends to model it.
#:
#: Ordering only is contractual: that entitlement never falls as class rises,
#: and that the bottom of the ladder has none. The exact members are the
#: reading of Daly's proportions onto four classes, not a measurement.
_CARRIAGE_CLASSES: frozenset[BuildingClass] = frozenset(
    {BuildingClass.COMFORTABLE, BuildingClass.GRAND}
)


@dataclass(frozen=True)
class Entrance:
    """Which entrance this building has, how much frontage it takes, and why.

    ``kind`` is also the phase-1 slot name, so nothing downstream has to map
    one onto the other. ``why`` is the sentence that goes into the account and
    the trace: the choice between a carriage arch and a pedestrian door is a
    real decision about the building, and a decision with no stated reason is
    the table this project exists to remove.
    """

    kind: str
    slot_width: Quantity
    storey_height: Quantity
    why: str

    @property
    def opening_type(self) -> str:
        """What qualification puts in this slot on the ground storey."""
        return ENTRANCE_OPENING_TYPES[self.kind]


def entrance_for(
    klass: BuildingClass, street_width: float, ground: GroundProgramme | None = None
) -> Entrance:
    """Carriage arch or pedestrian door: decided from the street and the class.

    Three conditions, in the order a builder would have weighed them:

    1. **The programme may name it.** ``GroundProgramme.CARRIAGE`` *is* the
       statement that this building's ground floor is a carriage entrance, so
       it settles the question by itself.
    2. **The street must admit a carriage** -- ``_CARRIAGE_STREET_MINIMUM``,
       an ABSOLUTE about a vehicle leaving the roadway, not a taste.
    3. **The household must keep one** -- ``_CARRIAGE_CLASSES``.

    Anything else gets the porte piétonne, which is not a lesser fallback but
    the commoner Paris entrance: most of the city's immeubles have one.

    Deliberately not a literal in a rule. This is a fact about the vocabulary
    a date and a purse could reach, which is what this module is for, and
    keeping it here means the ``qualify`` rules read a decision rather than
    re-deriving it three times over with three chances to disagree.
    """
    if ground is GroundProgramme.CARRIAGE:
        return Entrance(
            ENTRANCE_CARRIAGE,
            carriage_slot_width(),
            carriage_storey_height(),
            "the ground floor's programme IS the carriage entrance, so the door is "
            "a porte cochère whatever the street and the purse say",
        )
    wide_enough = street_width >= float(_CARRIAGE_STREET_MINIMUM) - _EPS
    keeps_one = klass in _CARRIAGE_CLASSES
    if wide_enough and keeps_one:
        return Entrance(
            ENTRANCE_CARRIAGE,
            carriage_slot_width(),
            carriage_storey_height(),
            f"a {street_width:.2f} m street admits a carriage "
            f"({_CARRIAGE_STREET_MINIMUM.why}) and a {klass.value} household keeps "
            f"one, so the entrance is a porte cochère "
            f"({float(carriage_slot_width()):.2f} m of frontage, ABSOLUTE)",
        )
    if not wide_enough:
        because = (
            f"a {street_width:.2f} m street is under the "
            f"{float(_CARRIAGE_STREET_MINIMUM):.2f} m a carriage needs to draw out of "
            f"the traffic and turn in ({_CARRIAGE_STREET_MINIMUM.why})"
        )
    else:
        because = (
            f"a {klass.value} household does not keep a carriage, and a porte cochère "
            "costs a frontage bay, a passage and a cour behind it"
        )
    return Entrance(
        ENTRANCE_PEDESTRIAN,
        pedestrian_slot_width(),
        pedestrian_storey_height(),
        f"the entrance is a porte piétonne ({float(pedestrian_slot_width()):.2f} m of "
        f"frontage, ABSOLUTE): {because}",
    )


def entrance_slot_width(kind: str) -> Quantity:
    """The frontage either entrance takes. ABSOLUTE; never scales."""
    if kind == ENTRANCE_CARRIAGE:
        return carriage_slot_width()
    if kind == ENTRANCE_PEDESTRIAN:
        return pedestrian_slot_width()
    raise KeyError(f"no entrance named {kind!r}; known: {sorted(ENTRANCE_SLOT_NAMES)}")


def entrance_storey_height(kind: str) -> Quantity:
    """The ground storey either entrance needs. ABSOLUTE; never scales."""
    if kind == ENTRANCE_CARRIAGE:
        return carriage_storey_height()
    if kind == ENTRANCE_PEDESTRIAN:
        return pedestrian_storey_height()
    raise KeyError(f"no entrance named {kind!r}; known: {sorted(ENTRANCE_SLOT_NAMES)}")


#: The largest span of glass the trade could deliver, by the devanture form
#: the date resolved to. ABSOLUTE in every entry: what limits a sheet of
#: glass is how big a sheet the glassworks could cast, blow or roll and get
#: across Paris intact, and no owner's ambition made the sheet bigger.
#: This is the fact that gives a shopfront its glazing bars — small panes in
#: 1830 and one pane in 1885 is the same shop window under two different
#: manufacturing limits, which is exactly why the brief calls shopfronts the
#: fastest-turning element on the facade.
_SHOPFRONT_PANE_MAX_SPAN: Mapping[str, Quantity] = {
    "timber_small_panes": Abs(
        0.45, "INFERRED — a crown- or cylinder-glass pane in a timber sash, c. 1820-50"
    ),
    "cast_iron_larger_panes": Abs(
        1.10, "INFERRED — the larger sheet cast-iron framing was developed to carry, 1850s+"
    ),
    "plate_glass": Abs(
        2.60, "INFERRED — polished plate: a shop window in a single sheet, 1870s+"
    ),
    "devanture_elaborate": Abs(
        1.80, "INFERRED — plate glass again, subdivided by the carved joinery around it"
    ),
}

#: Fallback for a frontage whose devanture form the date did not resolve —
#: the ordinary sheet of the period this typology covers.
_SHOPFRONT_PANE_DEFAULT = Abs(
    1.10, "INFERRED — an ordinary nineteenth-century shop-window sheet"
)


def shopfront_pane_max_span(style: str | None) -> Quantity:
    """The widest single sheet of glass a devanture of this form could use.

    A dimensional limit keyed by a form the *date* already resolved (S5's
    ``shopfront`` variants), which is why it lives here and not in the
    renderer: how many glazing bars cross a shop window is a fact about what
    a glassworks could make in that decade, and a renderer dividing the light
    by a number of its own choosing is deciding something a person could
    argue about.
    """
    return _SHOPFRONT_PANE_MAX_SPAN.get(style or "", _SHOPFRONT_PANE_DEFAULT)


def opening_aspect_band() -> tuple[float, float]:
    """How tall a Paris opening is relative to its own width: 1:1.7 to 1:2.

    A dimensional limit on the *shape* of an opening, not on its size, so it
    is a bare ratio rather than a ``Quantity``: it survives ``scale_for_class``
    untouched by construction, because scaling a rectangle does not change
    its proportion. That is the whole point -- the grand building's window is
    much bigger than the modest one's and exactly as tall for its width.

    **A8.4.** This is a bound, not a wish, and ``window_in_slot`` now asserts
    it. It used to be a wish, and the wall paid: 94 % of upper-storey openings
    fell below 1.70 and the worst of them was 1.00 — a square hole. It was
    *worse for the grander classes*, because a grand building buys a wider
    window and then has the same absolute sill and lintel eating the same
    absolute amount of a storey that is not proportionally taller. A facade
    full of squares reads as a wall with holes in it, not as a wall with
    windows in it, which is the single loudest thing wrong with the drawings.

    Where a storey is too short to give the band at the width the bay would
    like, the opening gets **narrower, not squatter**. Width is proportional
    and elastic — the pier beside it simply widens — while the aspect is what
    carries the reading, and there is no such thing as an elastic proportion.
    Upper floors still read differently from the noble floor: their openings
    are shorter and narrower and sit at ``1.70`` rather than ``2.00``, which
    is a change of size and of proportion within the band, not a collapse
    out of it.
    """
    return (1.70, 2.00)


@dataclass(frozen=True)
class OpeningGeometry:
    """One opening's own rectangle, stated *within the slot that carries it*.

    ``offset_x`` is measured from the slot's left edge and ``sill`` from the
    storey's floor, so the numbers are readable without knowing where on the
    frontage the slot landed -- and a consumer that does know adds the slot's
    origin and gets the facade coordinates. There is no second, absolute copy
    of either number in here: one fact, one name.
    """

    width: float
    height: float
    offset_x: float  # slot's left edge -> opening's left edge. This IS the pier.
    sill: float  # storey's floor -> underside of the opening

    @property
    def aspect(self) -> float:
        """Height over width. 1.7--2.0 is the Paris band; see ``opening_aspect_band``."""
        return self.height / self.width if self.width > 0.0 else 0.0


def _fit_width(slot_w: float, wanted: float, floor_w: float, pier_min: float) -> float:
    """Widest opening ``slot_w`` can carry, given a real pier either side.

    The pier is not a margin invented to look right -- it is
    ``pier_filler``'s own minimum, the narrowest masonry that still reads as
    load-bearing, scaled for the class by the caller. Where the slot cannot
    give the wanted width and that minimum too, the opening gives way, never
    the pier: a window pinched to nothing beside a fat pier is a bad facade,
    but a window running out to the joint is not a facade at all.
    """
    room = slot_w - 2.0 * pier_min
    if room <= 0.0:
        # Degenerate slot (narrower than two minimum piers). Keep the opening
        # strictly inside it rather than emitting geometry that overhangs.
        return max(0.0, slot_w * 0.5)
    width = min(wanted, room)
    if width < floor_w:
        width = min(floor_w, room)
    return max(0.0, width)


def _fit_height(slot_h: float, sill: float, wanted: float) -> tuple[float, float]:
    """Opening height and the sill it actually sat on, inside one storey.

    Three ABSOLUTE numbers bound this and none of them scales: the sill below
    (``sill_lean_height``), the lintel and joists above
    (``lintel_bearing_depth``), and the shortest useful light
    (``minimum_light_height``). The proportional want is capped by what is
    left. Where even that is not enough the SILL drops -- it is the only one
    of the three the building may argue with, because a lower sill is still a
    sill, whereas a floor without a lintel over its window is a floor that
    falls down.
    """
    head_room = max(0.0, slot_h - float(lintel_bearing_depth()))
    min_light = float(minimum_light_height())
    sill_eff = min(sill, max(0.0, head_room - min_light))
    height = max(0.0, min(wanted, head_room - sill_eff))
    return height, sill_eff


def window_in_slot(
    slot_w: float, slot_h: float, klass: BuildingClass, *, wanted_aspect: float, sill: float
) -> OpeningGeometry:
    """An ordinary window, cut in the wall of one slot on one storey.

    **The two halves of the aperture are two kinds of number (A9.4).** Width
    comes from ``opening_window``, which is ABSOLUTE and identical for every
    class; height comes from ``opening_height_at_the_nobile``, which is
    PROPORTIONAL and is the only thing here ``scale_for_class`` touches. Daly
    is the reason and both functions carry the figures: across sixteen
    buildings the width band is 1.04-1.30 m and *non-monotonic* by class,
    while the noble floor's height runs 2.92 / 2.24 / 2.09 m in order. So a
    grand window in this catalogue is not a modest one enlarged — it is the
    same width and half again as tall, which is precisely what makes a Paris
    street legible as a social ladder rather than as a set of scale models.

    ``wanted_aspect`` is still the caller's, and still comes from the storey's
    rank rather than from its class: it is now read as *where in the aspect
    band this storey sits*, and it reduces the class's noble height in the
    same proportion. Rank shortens the opening, class lengthens it, and the
    two axes never touch each other's quantity.

    Four facts decide it, in this order, and the order is the substance:

    1. **What a body needs.** ``opening_window``'s ABSOLUTE band, fitted
       into the slot with ``pier_filler``'s minimum left standing either
       side. No class anywhere.
    2. **What the class bought.** The noble-floor height, scaled once through
       ``scale_for_class``, read down for this storey's rank.
    3. **What the storey can give.** ``_fit_height``: the slot less the
       ABSOLUTE lintel above and the ABSOLUTE sill below, the sill dropping
       first where even that is not enough.
    4. **The proportion, which does not give way.** If the height in (3) will
       not carry the width in (1) at ``opening_aspect_band``'s lower bound,
       the WIDTH comes in until it does.

    (4) is A8.4 and it stands unchanged. It used to stop at (3): height was
    ``width * wanted_aspect`` capped by the storey, so a storey that could not
    afford the height simply got a squarer window, and the measured result was
    94 % of upper openings under the band with a minimum of 1.00. The band is
    the catalogue's own stated contract about what a Paris opening looks like;
    a facade may run out of height, but it may not thereby stop being a Paris
    facade.

    What gives way instead is the width, and it can still afford to even now
    that it is ABSOLUTE: the ``Abs`` band has real width (1.04-1.30 m, which
    is the sixteen-building spread Daly measured), the pier beside it is
    elastic and absorbs the difference, and the opening stays centred on its
    bay so the vertical axes of the facade are untouched -- the jambs step in
    slightly toward the top instead of running dead straight, which is what a
    real Paris frontage does under its cornice. Moving *inside* a fixed band
    is not the same thing as scaling with the class, and the difference is
    visible in the output: every class's windows are drawn from one band.

    Both mechanisms are still visible: on a tall storey (1)-(3) all fit and
    the window is the class's full height at the corpus width; on a short one
    it is a narrower rectangle at the band's lower bound. What can no longer
    come out of here is a square.

    Where even ``minimum_light_width`` cannot be made to satisfy the band, the
    slot has no window in it at all -- two ABSOLUTE facts have collided and
    the honest answer is a blind panel, not a loophole. That is returned as a
    zero-width opening, and it does not happen on any storey a person lives
    in: at the shortest, an opening ``minimum_light_height`` tall carries the
    band at 0.35 m, well under the 0.55 m floor.
    """
    low, high = opening_aspect_band()
    # ABSOLUTE: ``to_slot_spec`` calls ``scale_for_class``, which is a
    # documented no-op on every bound of this module now that the width is
    # ``Abs``. It is still called, rather than skipped, so that the one
    # sanctioned scaling site stays the one sanctioned scaling site — and so
    # that a reader can see the no-op happening instead of inferring it.
    win = opening_window().to_slot_spec(klass)
    pier_min = pier_filler().to_slot_spec(klass).minimum
    width = _fit_width(slot_w, win.preferred, win.minimum, pier_min)
    # PROPORTIONAL, and the only place in this function class enters at all.
    # ``wanted_aspect`` is the storey's rank expressed as a position in the
    # aspect band; dividing by the band's top turns it into "what fraction of
    # the noble floor's height this storey asks for", which is 1.0 at rank 0
    # and falls upward. The class's noble height then multiplies it.
    nobile = float(scale_for_class(opening_height_at_the_nobile(), klass))
    wanted_h = nobile * (wanted_aspect / high) if high > _EPS else nobile
    height, sill_eff = _fit_height(slot_h, sill, wanted_h)

    if height > _EPS and height < width * low - _EPS:
        # The storey could not carry the class's width at the band. Narrow,
        # never squat: the widest width this height keeps in proportion.
        width = height / low
        floor_w = float(minimum_light_width())
        if width < floor_w - _EPS:
            # Even the narrowest light is squat here, so the SILL gives — the
            # one of the three ABSOLUTE bounds a building may argue with, for
            # the reason `_fit_height` already gives — and it gives exactly as
            # far as the band needs and no further. Not to keep the window
            # WIDE: a sill that dropped for width would put a fifth-floor
            # opening at ankle height, and the height a body can lean on is
            # ABSOLUTE precisely so that cannot happen. Only to keep it a
            # window at all.
            head_room = max(0.0, slot_h - float(lintel_bearing_depth()))
            height = min(head_room, floor_w * low)
            width = height / low
            sill_eff = max(0.0, head_room - height)
        if width < floor_w - _EPS:
            width = height = 0.0

    geom = OpeningGeometry(
        width=width, height=height, offset_x=(slot_w - width) / 2.0, sill=sill_eff
    )
    # The stated band, asserted rather than hoped for (A8.4). An opening with
    # no height is a blind panel and has no proportion to be wrong about.
    assert geom.height <= _EPS or low - 1e-6 <= geom.aspect, (
        f"a {geom.width:.4f} x {geom.height:.4f} m opening has aspect "
        f"{geom.aspect:.3f}, under the {low:.2f} this catalogue states as the Paris "
        f"band (slot {slot_w:.3f} x {slot_h:.3f} m, sill {sill:.3f} m, class "
        f"{klass.value})"
    )
    return geom


def shopfront_in_slot(
    slot_w: float,
    slot_h: float,
    klass: BuildingClass,
    *,
    soubassement: bool = True,
    enseigne: bool = True,
) -> OpeningGeometry:
    """A devanture: the ground floor opened up to the street.

    The masonry either side is the *trumeau* -- ``pier_filler``'s minimum,
    not its preferred width, because a shop buys as much glass as the
    structure will let it. Vertically it runs from one step above the
    pavement to the underside of the enseigne board. Both of those are
    ABSOLUTE, so a grand building's shopfront is taller and wider than a
    modest one's only by as much as its bay and its ground storey are --
    which is the honest amount.

    **A13.2 -- the two registers.** A devanture that has absorbed an entresol
    is one framework standing across two storeys of the stack, and the two
    ABSOLUTE bands that close it belong to the framework, not to each storey
    of it: there is one soubassement, at the pavement, and one enseigne
    board, under the course that crowns the base. So each register says which
    of the two it carries. A devanture that faces a single storey carries
    both, which is the default and is bit-for-bit what this function returned
    before. What is deliberately NOT here is a band between the registers:
    the transom that divides a shop window from the entresol light above it
    is joinery, drawn inside the glass, and inventing a second soubassement
    or a second fascia at the storey line would cut the one framework in two
    -- which is exactly the reading A13 exists to remove.
    """
    pier_min = pier_filler().to_slot_spec(klass).minimum
    width = max(0.0, slot_w - 2.0 * pier_min) if slot_w > 2.0 * pier_min else slot_w * 0.5
    sill = float(shop_threshold_height()) if soubassement else 0.0
    fascia = float(shopfront_fascia_depth()) if enseigne else 0.0
    height = max(0.0, slot_h - sill - fascia)
    if height <= 0.0:
        sill, height = 0.0, max(0.0, slot_h * 0.5)
    return OpeningGeometry(
        width=width, height=height, offset_x=(slot_w - width) / 2.0, sill=sill
    )


def entresol_allege_height() -> Quantity:
    """The *allege* under an arcaded entresol opening -- the low breast wall
    the small garde-corps stands on.

    ABSOLUTE, and deliberately much lower than ``sill_lean_height``: an
    entresol light is not a window somebody leans out of over the street, it
    is the upper half of a shop's own volume, carried down nearly to the
    floor so the mezzanine behind it gets the light a low storey needs. At
    120 bd de Sebastopol the arch springs from just above the shopfront's
    entablature and the railing crosses the glass rather than standing on a
    sill under it.

    Reading ``sill_lean_height`` here is what produced A13's complaint: a
    0.90 m sill in a 2.66 m storey leaves 1.46 m between the lintel and the
    breast, which draws as a shrunken version of an upper-floor window --
    a short residential storey, which is the one thing an entresol is not.
    """
    return Abs(
        0.30,
        "INFERRED -- a low allege carrying a small garde-corps across an "
        "entresol light, not a sill a body leans on",
    )


def garde_corps_in_an_arched_light(straight_portion: float) -> Quantity:
    """How tall the garde-corps across an arched light stands (A15.3).

    ABSOLUTE, and derived rather than defaulted. A railing in a flat-headed
    window has the whole light to stand in and stops at ``sill_lean_height``,
    the height a body leans against. A railing inside an ARCH does not: above
    the springing the light is bounded by the curve, and the archivolt — the
    moulding that follows it — is stone in the same plane as the railing's own
    stiles. So the rail has the STRAIGHT portion of the light and nothing
    more.

    Measured before this existed: on 90 of 210 tall arches the flat-headed
    0.90 m rail stood taller than the straight light beneath the springing
    (0.7615 m on layout AC), and its top rail and outer stiles crossed the
    springing and cut through the moulding, worst overflow 0.138 m. That is
    not a railing behind an arch, it is a railing drawn through one.

    A short straight light therefore gives a low rail, which is what the form
    is — a garde-corps across the foot of a fanlight, not a balustrade — and
    where the arch springs from the imposte itself there is no straight light
    and no rail, which the caller reads as ``0.0``.

    Where the straight light is generous the rail still stops at
    ``sill_lean_height``: what a body leans against is a fact about the body,
    and an arch with three metres of straight light under its springing does
    not get a three-metre railing. So this is the flat-headed rule with one
    more bound on it, and never a taller answer than the one it replaces.
    """
    return Abs(
        max(0.0, min(straight_portion, float(sill_lean_height()))),
        "ABSOLUTE -- the straight portion of the light below the springing, "
        "capped by the height a body leans against, because a garde-corps "
        "standing inside an arch may not cross the archivolt that follows the "
        "curve (A15.3)",
    )


def carriage_entrance_in_slot(slot_w: float, slot_h: float) -> OpeningGeometry:
    """The porte cochère. ABSOLUTE in both directions; no class anywhere.

    The clear opening is ``door_carriage_entrance``'s own width — a carriage
    has to pass — and the slot phase 1 placed for it is that width plus a
    ``carriage_jamb_width`` either side (``carriage_slot_width``), so what is
    left inside the slot after the two jambs IS the door. It used to be the
    slot itself, edge to edge: the only opening on the frontage with no
    masonry either side of it, and an arch standing on nothing. Where a slot
    arrives narrower than its own jambs allow (a hand-built grid, a degenerate
    frontage) the JAMB gives way before the clear width does, because a
    carriage that cannot get through the gate is not a gate.

    Its height is ``carriage_clear_height``, flat: not the storey's height
    minus a lintel, and never a ``min`` of the two. The storey standing over a
    porte cochère is ``carriage_storey_height`` — that same clear height plus
    the lintel bearing on it — so a storey that cannot hold the pair is a
    storey too short for the programme it carries, and this raises rather than
    quietly handing back a shorter door (A5.5).

    That is the whole of the absolute/proportional rule in one function. A
    clear height that yields to whatever height happens to be available is not
    ABSOLUTE, it is a preference; and the failure mode it produced was not a
    slightly wrong drawing but a carriage entrance a carriage could not pass,
    which is the same defect as a door with no handle on either side. When
    ``CarriageCannotPass`` is raised the fix is upstream, in phase 1: give the
    ground storey ``carriage_storey_height``, or do not put a carriage
    entrance on this frontage.

    ``klass`` is absent from the signature on purpose. It is the one opening
    in the catalogue that takes no class argument, and that absence is the
    contrast the whole absolute/proportional split exists to produce: between
    a modest frontage and a grand one the windows change by half again, and
    this changes by nothing at all.
    """
    spec = door_carriage_entrance()
    clear = float(spec.preferred)
    narrowest = float(spec.minimum)
    jamb = float(carriage_jamb_width())
    clear_h = float(carriage_clear_height())
    lintel = float(lintel_bearing_depth())

    if slot_h < clear_h + lintel - _EPS:
        raise CarriageCannotPass(
            f"a {slot_h:.2f} m ground storey cannot carry a porte cochère: a carriage "
            f"needs {clear_h:.2f} m of clear height ({carriage_clear_height().why}) and "
            f"the lintel over it bears {lintel:.2f} m more, so the storey must be at "
            f"least {clear_h + lintel:.2f} m ({carriage_storey_height().why}). Raise the "
            f"storey or drop the carriage entrance; do not shorten the door."
        )

    width = min(clear, slot_w) if slot_w < clear + 2.0 * jamb else clear
    if width < narrowest - _EPS:
        raise CarriageCannotPass(
            f"a {slot_w:.2f} m slot cannot carry a porte cochère: it leaves {width:.2f} m "
            f"clear and a carriage needs at least {narrowest:.2f} m ({spec.minimum.why}). "
            f"The frontage a carriage entrance takes is {float(carriage_slot_width()):.2f} m "
            f"({carriage_slot_width().why})."
        )

    return OpeningGeometry(
        width=width, height=clear_h, offset_x=(slot_w - width) / 2.0, sill=0.0
    )


def pedestrian_entrance_in_slot(slot_w: float, slot_h: float) -> OpeningGeometry:
    """The porte piétonne. ABSOLUTE in both directions; no class anywhere.

    Written as the twin of ``carriage_entrance_in_slot`` and refusing on the
    same terms (A5.5): the clear width is ``door_pedestrian``'s own, the clear
    height is ``pedestrian_clear_height``, and where the slot or the storey
    cannot give them the JAMB yields first and then the function raises. It
    never hands back a shorter or narrower door, because an entrance that
    quietly shrinks stops being the ruler the eye measures the facade against
    -- which is the whole reason A6.1 asks for it to be ABSOLUTE.

    ``klass`` is absent from the signature for the same reason it is absent
    from the carriage entrance's: this is the opening money may not touch.
    """
    spec = door_pedestrian()
    clear = float(spec.preferred)
    narrowest = float(spec.minimum)
    jamb = float(pedestrian_jamb_width())
    clear_h = float(pedestrian_clear_height())
    lintel = float(lintel_bearing_depth())

    if slot_h < clear_h + lintel - _EPS:
        raise EntranceCannotFit(
            f"a {slot_h:.2f} m ground storey cannot carry a porte piétonne: the door "
            f"and the imposte over it need {clear_h:.2f} m of clear height "
            f"({pedestrian_clear_height().why}) and the lintel bears {lintel:.2f} m "
            f"more, so the storey must be at least {clear_h + lintel:.2f} m "
            f"({pedestrian_storey_height().why}). Raise the storey; do not shorten "
            "the door."
        )

    width = min(clear, slot_w) if slot_w < clear + 2.0 * jamb else clear
    if width < narrowest - _EPS:
        raise EntranceCannotFit(
            f"a {slot_w:.2f} m slot cannot carry a porte piétonne: it leaves "
            f"{width:.2f} m clear and two people and a trunk need at least "
            f"{narrowest:.2f} m ({spec.minimum.why}). The frontage a pedestrian "
            f"entrance takes is {float(pedestrian_slot_width()):.2f} m "
            f"({pedestrian_slot_width().why})."
        )

    return OpeningGeometry(
        width=width, height=clear_h, offset_x=(slot_w - width) / 2.0, sill=0.0
    )


def entrance_in_slot(kind: str, slot_w: float, slot_h: float) -> OpeningGeometry:
    """Either entrance, cut in the slot phase 1 placed for it.

    One door per building and one function that cuts it, so a rule that needs
    the entrance's rectangle asks for "the entrance" rather than branching on
    which of the two it is -- the branch lives here, once, beside the two
    geometries it chooses between.
    """
    if kind == ENTRANCE_CARRIAGE:
        return carriage_entrance_in_slot(slot_w, slot_h)
    if kind == ENTRANCE_PEDESTRIAN:
        return pedestrian_entrance_in_slot(slot_w, slot_h)
    raise KeyError(f"no entrance named {kind!r}; known: {sorted(ENTRANCE_SLOT_NAMES)}")


# ---------------------------------------------------------------------------
# A14 -- the entrance that rises through the entresol as one round arch
# ---------------------------------------------------------------------------
#
# Daly draws it on four of his sixteen buildings, in both entrance kinds:
#
#     Avenue de l'Imperatrice (Raban)   porte cochere   2.62 x 7.30   RdC 4.30
#     39 rue Neuve des Mathurins        porte cochere   2.57 x 5.00   RdC 4.10
#     2 et 4 bd de Sebastopol (Davioud) porte pietonne  1.74 x 5.01   RdC 3.42
#     87 bd de Sebastopol               porte pietonne  1.76 x 5.07
#
# against one-storey medians of 3.49 m (cochere) and 3.03 m (pietonne).
#
# **The width does not move, and that is the whole point.** Daly's two tall
# carriage arches are 2.57 and 2.62 m; his seven one-storey ones are
# 2.41-2.67. His two tall pedestrian doors are 1.74 and 1.76; the one-storey
# ones are 1.36-1.91. The tall arch is squarely inside the ordinary width band
# in both kinds -- so a two-storey arch is a *compositional* decision about
# height taken against an *absolute* width, and nothing below may touch the
# width. ``two_storey_entrance_arch`` gets its clear width by calling
# ``entrance_in_slot``, the same function the one-storey door calls, precisely
# so that there is no second place a width could be written down and drift.


#: The two forms an entrance takes in height. Named, and stated as a pair,
#: because A14.2 is a choice between two real architectural forms in exactly
#: the way A13.2's ``"absorbed"``/``"arcaded"`` is -- not a flag that some
#: buildings have set. Three quarters of Daly's entrances are one-storey and
#: that is not the absence of a decision, it is the other outcome of it.
ENTRANCE_ARCH_ONE_STOREY = "one_storey"
ENTRANCE_ARCH_TWO_STOREY = "two_storey"

#: The rez-de-chaussee register of a two-storey arch: the leaves, and the
#: carved tympanum panel standing on them. Named, not spelled out at each use,
#: because the string is both a qualification decision and a renderer branch.
ENTRANCE_ARCH_LEAVES = "leaves"

#: The entresol register of the same arch: the balconette with its ironwork,
#: the light behind it, and the round head with its agrafe at the crown.
ENTRANCE_ARCH_HEAD = "arch_head"

#: What occupies the entresol cell of an entrance slot whose arch rises
#: through it. NOT one of ``ENTRANCE_OPENING_TYPES`` on purpose: a building
#: has exactly one entrance (A6.1) and ``compose._assert_one_entrance``
#: counts those, so the upper register of the one arch must not read as a
#: second door. It is the arch's own upper light, and it is named for that.
ENTRANCE_ARCH_HEAD_OPENING = "entrance_arch_head"

#: How often a *porte pietonne* takes the two-storey arch, where the base
#: block can carry one.
#:
#: **INFERRED, and deliberately not calibrated.** Daly shows 4 of 16, which
#: is where 0.25 comes from, but n = 16 with a known publication bias is an
#: *observation*, not a rate: it is not keyed to date (all four are 1864) and
#: not to class (two Premiere, two Deuxieme). What is contractual is that
#: both forms occur and that the tall one is the minority; the figure itself
#: is one number a later measurement pass should expect to move.
#:
#: **A17.1, corrected.** This constant used to say the choice was not keyed
#: to entrance kind either, "two of each". That counted numerators and left
#: the denominators out. Set against how many entrances of each kind the
#: corpus holds, the two are not alike:
#:
#: * *porte cochere* -- 2 of 7 take the tall form (Imperatrice 7.30 m,
#:   39 rue Neuve des Mathurins 5.00 m)
#: * *porte pietonne* -- 2 of 10 (2 et 4 bd de Sebastopol 5.01 m,
#:   87 bd de Sebastopol 5.07 m)
#:
#: A17.1 then over-corrected the other way and made the tall arch compulsory
#: on every carriage entrance. That is refuted inside our own corpus by
#: **26 rue Bergere**: an entresol of 3.09 m under a porte cochere measuring
#: 3.474 m, a carriage entrance that plainly stops at the rez-de-chaussee.
#: So it is a draw for both kinds, drawn at different rates.
TWO_STOREY_ARCH_RATE = 0.25

#: The same decision for a *porte cochere*, which leans to the tall form.
#:
#: **INFERRED, and calibrated by nothing.** There is a real reason to expect
#: the lean -- a carriage has to pass under the entresol floor to reach the
#: cour, which is a clearance fact about a vehicle rather than a fashion --
#: and there is no sound way to get a number out of it. The corpus offers two
#: denominators and neither is the right one:
#:
#: * **0.286**, 2 of all 7 carriage entrances, which counts four entresol-less
#:   grand addresses where the choice did not exist to be made
#: * **0.50**, 1 of the 2 carriage entrances standing on a frontage that has
#:   an entresol at all (26 rue Bergere plain, 39 rue Neuve des Mathurins
#:   tall), which is n = 2
#:
#: 0.40 sits between them because the honest reading is between them. Only
#: the ORDERING is contractual, and it is a two-sided ordering: the carriage
#: arch is likelier than the pedestrian one AND still the minority of carriage
#: entrances. Nothing may assert the value.
TWO_STOREY_ARCH_RATE_CARRIAGE = 0.40


def two_storey_arch_rate(kind: str) -> float:
    """The rate at which an entrance of ``kind`` draws the two-storey arch.

    One expression rather than a conditional at the call site, for the reason
    ``entrance_for`` is in this module at all: a rate is a fact about the
    vocabulary, and a rule should read the decision rather than re-derive it.
    """
    if kind == ENTRANCE_CARRIAGE:
        return TWO_STOREY_ARCH_RATE_CARRIAGE
    if kind == ENTRANCE_PEDESTRIAN:
        return TWO_STOREY_ARCH_RATE
    raise KeyError(f"no entrance named {kind!r}; known: {sorted(ENTRANCE_SLOT_NAMES)}")


#: INFERRED, and **not calibrated** (A15.4). How many times its own span a
#: round-headed opening may be carried before it stops reading as an arch and
#: starts reading as a slot with a curved top. It is a proportion of the
#: opening, not a height: a *porte piétonne* is narrower than a *porte
#: cochère*, so carrying both to the same crown line — which is what the
#: entresol's own ceiling does, since the two-storey arch used to be sized by
#: the storey it rises through and by nothing else — makes the narrow one
#: lanky. Measured, ours came out at 3.49-3.57 spans against Daly's 2.88.
#:
#: Daly's two tall pedestrian doors are 5.01 m on 1.740 m (2.879) and 5.07 m
#: on 1.760 m (2.881), which is a check on the figure and deliberately not its
#: source: n = 2, from a corpus with a known publication bias, and A15.4 is
#: explicit that only the ORDERING is contractual — the pedestrian arch is
#: shorter than the carriage arch, and both are clearly taller than their
#: one-storey forms. Nothing may assert the value.
#:
#: It binds on the narrow form only. On the 2.60 m carriage span it allows
#: 7.54 m, which is above anything the entresol's own ceiling ever offers, so
#: the carriage arch is left exactly where A14 put it — 6.01-6.24 m, inside
#: Daly's own 5.00-7.30 m band — and this quantity never touches it. That is
#: the shape of the finding: one form overshot, not both.
TALL_ARCH_MOST_SLENDER = 2.90


def round_arch_rise(clear_width: float) -> float:
    """How far a ROUND head rises over its springing: half the span.

    Not a taste and not a proportion anybody may argue with -- it is what the
    word "round" means. A14.1 asks for a round head specifically ("the head is
    round; that is what makes the form"), and a semicircle turned on a
    ``clear_width`` span rises ``clear_width / 2``. It is stated here, once, so
    that the height the arch needs in the entresol and the height the renderer
    draws the curve at come from the same expression and cannot disagree --
    the renderer used to pick every head's depth itself, out of
    ``min(0.5, max(0.15, w * 0.30))``, which on a 2.60 m arch is a 0.50 m
    segment: a flattened bow drawn where a semicircle was stated.
    """
    return max(0.0, clear_width) / 2.0


@dataclass(frozen=True)
class TwoStoreyEntranceArch:
    """One entrance arch spanning the rez-de-chaussee and the entresol.

    Stated as its two REGISTERS rather than as one rectangle, because that is
    how the facade is built and how it has to be drawn: the base storey's wall
    is one course of masonry and the entresol's is the one above it, and an
    opening rectangle handed across that joint would be drawn over by the wall
    of the storey it trespasses into. It is the same shape A13 already gave
    the absorbed devanture -- one architectural object, two registers of one
    grid, unified by a fact both of them state -- and it means every existing
    invariant about an opening fitting the storey that carries it survives
    untouched.

    ``clear_width`` is the ONE dimension shared by both registers and by the
    one-storey door: it comes from ``entrance_in_slot`` and is ABSOLUTE.
    """

    kind: str
    clear_width: float
    offset_x: float
    #: Rez-de-chaussee register: the whole storey. The leaves stand in the
    #: bottom of it and the carved tympanum fills what is left, because an
    #: arch that carries the floor structure up into the entresol leaves no
    #: lintel band under the ceiling for this one bay -- which is exactly
    #: what the two-storey form buys.
    leaves_register_height: float
    #: The leaves themselves: the SAME clear height the one-storey door has,
    #: because what passes through the gate did not change.
    leaves_height: float
    #: Entresol register: the balconette, the light behind it and the head.
    head_register_height: float
    #: The semicircle at the top of that register.
    head_rise: float

    @property
    def tympanum_depth(self) -> float:
        """The carved panel over the leaves, inside the lower register."""
        return max(0.0, self.leaves_register_height - self.leaves_height)

    @property
    def clear_height(self) -> float:
        """Pavement to crown, in metres -- the figure Daly's table reports."""
        return self.leaves_register_height + self.head_register_height

    @property
    def springing_above_pavement(self) -> float:
        """Where the curve starts. Read by nothing that draws; it is the
        number a reader checks a plate against."""
        return self.clear_height - self.head_rise


def two_storey_entrance_arch(
    kind: str,
    slot_w: float,
    base_storey_h: float,
    entresol_h: float,
    *,
    crown_below: float,
) -> TwoStoreyEntranceArch:
    """The two-storey arch, or a refusal (A14.1).

    ``crown_below`` is how much of the entresol the band crowning the base
    block takes off the top -- the caller passes ``max(entablature depth,
    lintel bearing)``, the same expression the *flanking* entresol arcade is
    fitted under (``qualify.klass.entresol_arcade_is_sized_by_the_storey_it_
    lights``). That is not a coincidence and not a tidy default: A14 says the
    arch "springs from the same coursing as the flanking arches", and an arch
    coursed with its neighbours ends where they end as well as starting where
    they start. Passing the same expression is what puts the crown of this
    arch and the heads of the entresol openings either side of it on one line.

    Refuses rather than shrinking, on A5.5's terms and for A5.5's reason: the
    width is ABSOLUTE, so the round head's rise is ABSOLUTE too, and an
    entresol too short to turn the semicircle in cannot have the arch flattened
    to fit. The caller's answer is the one-storey door, which is not a lesser
    form -- it is what three quarters of Daly's buildings have.
    """
    if kind not in ENTRANCE_SLOT_NAMES:
        raise KeyError(f"no entrance named {kind!r}; known: {sorted(ENTRANCE_SLOT_NAMES)}")

    # The width comes from the ONE-storey geometry, unchanged, and so does the
    # leaves' clear height. A14.1: "a tall arch is not a wide one."
    leaves = entrance_in_slot(kind, slot_w, base_storey_h)
    rise = round_arch_rise(leaves.width)
    head_register = entresol_h - crown_below

    # A15.4. The crown is the smaller of two facts, and until now it was only
    # the first: where the coursing of the base block puts it, and how far
    # this arch's own span lets it be carried. A14 gave both forms the same
    # crown line because both rise through the same entresol, and a narrower
    # arch carried to a wider one's crown is not a taller arch, it is a
    # thinner one. So the head register gives way — the leaves and the round
    # head over them are what the form IS, and the straight light between them
    # is the only part with any give in it.
    slenderest = TALL_ARCH_MOST_SLENDER * leaves.width - base_storey_h
    head_register = min(head_register, max(0.0, slenderest))

    if head_register < rise + _EPS:
        raise EntranceCannotFit(
            f"a {entresol_h:.2f} m entresol cannot carry the head of a two-storey "
            f"{kind}: under the {crown_below:.2f} m band that crowns the base block, "
            f"and under the {TALL_ARCH_MOST_SLENDER:.2f} spans of its own "
            f"{leaves.width:.2f} m width this form may be carried to (A15.4), it "
            f"leaves {max(0.0, head_register):.2f} m, and a ROUND head on that span "
            f"rises {rise:.2f} m. Widening the arch to lower its head is not "
            "available -- the width is what a carriage or a body needs (A9.2) -- so "
            "this frontage takes the one-storey door."
        )

    return TwoStoreyEntranceArch(
        kind=kind,
        clear_width=leaves.width,
        offset_x=leaves.offset_x,
        leaves_register_height=base_storey_h,
        leaves_height=leaves.height,
        head_register_height=head_register,
        head_rise=rise,
    )


def two_storey_entrance_arch_fits(
    kind: str,
    slot_w: float,
    base_storey_h: float,
    entresol_h: float,
    *,
    crown_below: float,
) -> bool:
    """Can this base block carry the two-storey arch at all?

    Asked BEFORE the draw that chooses the form, so that a frontage which
    could never build one does not consume a decision on it -- a coin whose
    outcome is then overruled by geometry is a coin that has moved the
    reported rate without moving any building.
    """
    try:
        two_storey_entrance_arch(
            kind, slot_w, base_storey_h, entresol_h, crown_below=crown_below
        )
    except EntranceCannotFit:
        return False
    return True


# ---------------------------------------------------------------------------
# The ground floor's own surround vocabulary (A6.7)
# ---------------------------------------------------------------------------

#: The frame around a devanture's light. A shop window is framed by the
#: devanture's own joinery -- pilasters carrying the enseigne board over the
#: glass -- and NOT by the stone architrave-and-pediment vocabulary of the
#: floors above. A pediment is an entablature on consoles over a window in a
#: wall; a shopfront has neither wall nor entablature at that point, which is
#: why a triangle over a shop light reads as a mistake to anybody who has seen
#: a Paris street (A6.7).
_DEVANTURE_FRAME = "devanture_frame"

#: The frame around an ordinary ground-floor window where the ground floor is
#: not trade -- a hall, a stair, a counting house behind plain masonry. A flat
#: band of dressed stone, the plainest named surround there is: the ground
#: storey is the socle of the composition and the money goes upstairs.
_GROUND_STONE_BAND = "bare_band"


def ground_floor_surround(opening_type: str) -> str:
    """Which surround a ground-storey opening takes.

    Ground-floor surrounds come from the ground floor's own vocabulary, not
    from the ladder of stone frames the upper storeys climb. Two answers, and
    the opening itself says which: a shop light is framed by the devanture, an
    ordinary ground-floor window by a plain stone band. The entrance is not
    here -- it has its own architrave, stated where the entrance is stated.
    """
    if opening_type == "shop_bay":
        return _DEVANTURE_FRAME
    return _GROUND_STONE_BAND


def roundel_in_slot(
    slot_w: float, klass: BuildingClass, *, head_above_floor: float
) -> OpeningGeometry:
    """An oeil-de-boeuf in a narrow special, hung off its neighbours' heads.

    A round window has no sill to lean on and no proportion of its own to
    argue about -- it is as wide as it is tall. What it does have to do is
    belong to the row it sits in, so its crown is put on the same line as the
    heads of the windows either side of it (``head_above_floor``) rather than
    centred in a storey it shares with nothing.
    """
    diameter = min(
        narrow_special_oeil_de_boeuf().to_slot_spec(klass).preferred,
        max(0.0, slot_w - 2.0 * pier_filler().to_slot_spec(klass).minimum),
    )
    diameter = max(0.0, diameter)
    return OpeningGeometry(
        width=diameter,
        height=diameter,
        offset_x=(slot_w - diameter) / 2.0,
        sill=max(0.0, head_above_floor - diameter),
    )


# ---------------------------------------------------------------------------
# Ornament modules -- the repeat interval of a carved or wrought rhythm (A7.2)
# ---------------------------------------------------------------------------
#
# A modillion, a dentil, a course of refends, a balcony bracket, a scroll in a
# garde-corps: each is one unit of a rhythm that repeats along a length of
# frontage, and *how many* of them appear across that length is not a fact
# about the length. It is the density of ornament, which BRIEF.md lists among
# the PROPORTIONAL quantities -- "the scale and density of ornament" -- that
# move with ambition and budget. So the repeat interval is a `Prop`, it is
# resolved per storey by the qualification layers (which is where class and
# `rank_from_principal` live), and the *count* it produces travels in the IR.
#
# What is stated here is the module at FULL ornament: the interval a grand
# building's principal floor gets. Every quieter storey reads out from it
# through `qualify.base.ornament_module`, coarsening as the density falls.
# Before A7.2 all of these were bare literals inside `render/svg/elements.py`
# -- `spacing = 0.5`, `w / 0.35`, `course_h = 0.22` -- so a modest attic and a
# grand entresol carried exactly the same number of brackets per metre and the
# only thing money moved was the size of the wall behind them.
#
# All INFERRED. Only the ordering is contractual: a richer, better-placed
# storey carries a finer rhythm than a meaner one.


def modillion_module() -> Quantity:
    """Spacing of the chunky brackets under a modillioned cornice."""
    return Prop(0.50, "INFERRED -- a modillion and the gap beside it, at full ornament")


def dentil_module() -> Quantity:
    """Spacing of the small blocks in a dentil course."""
    return Prop(0.12, "INFERRED -- a dentil and its gap, at full ornament")


def rustication_course_width() -> Quantity:
    """Length of one drawn block in a rusticated or refended ground storey."""
    return Prop(0.90, "INFERRED -- one stone of a bossage course, at full ornament")


def rustication_course_height() -> Quantity:
    """Height of one drawn course in a rusticated or refended ground storey.

    PROPORTIONAL rather than absolute on purpose: these are the *drawn*
    courses of a socle treatment -- incised refends, or the joints of a
    bossage -- not the bed heights of the structural masonry behind them. A
    grander frontage buys a finer coursing across the same wall.
    """
    return Prop(0.30, "INFERRED -- one course of drawn refends, at full ornament")


def balcony_bracket_module() -> Quantity:
    """Spacing of the consoles carrying a balcony slab."""
    return Prop(1.50, "INFERRED -- the run of slab one console carries, at full ornament")


def ironwork_ornament_module() -> Quantity:
    """Repeat of the ornament hung on a railing's bars.

    The scroll, the wave and the lozenge are the same rhythm wearing three
    dated faces, so they share one module. The BARS are not here and never
    will be: their spacing is `balustrade_child_gap_max`, which is ABSOLUTE,
    and a pattern is a look rather than a licence to widen a gap a child's
    head fits through.
    """
    return Prop(0.32, "INFERRED -- one scroll, wave or lozenge and its neighbour, at full ornament")


def cresting_module() -> Quantity:
    """Repeat of the iron cresting standing along a ridge."""
    return Prop(0.40, "INFERRED -- one upright of ridge cresting and its gap, at full ornament")


#: What a roof covering's own seams run at, by material. ABSOLUTE, and the odd
#: one out in this section: a standing seam is where two tables of zinc are
#: folded together, so the interval is the width of the sheet the works rolled
#: and two men could carry up a ladder. No owner's ambition made the sheet
#: wider. Slate has no vertical fold at all -- its coursing is horizontal
#: overlap, which this elevation does not show -- so what is drawn on a slate
#: comble is a coarser reading of the slope itself.
_ROOF_SEAM_MODULES: Mapping[str, Quantity] = {
    "zinc_roofing": Abs(0.60, "INFERRED -- a zinc table runs 0.5-0.65 m between standing seams"),
}

_ROOF_SEAM_DEFAULT = Abs(
    1.30, "INFERRED -- a slate or tile slope reads at the coarser rhythm of its own planes"
)


def roof_seam_module(material: object) -> Quantity:
    """Interval between the seams drawn down a roof slope, by covering."""
    key = material if isinstance(material, str) else ""
    return _ROOF_SEAM_MODULES.get(key, _ROOF_SEAM_DEFAULT)


def repeats_across(extent: float, module: float, *, minimum: int = 1) -> int:
    """How many repeats of a rhythm of interval ``module`` fill ``extent``.

    The one place a length and a module become a count. It lives here, on the
    qualification side of the IR, precisely so that no consumer has to divide
    a dimension it was handed by a number it made up -- which is what
    `dev/harness/check_renderer_dumb.py` exists to catch and what A7.2 found
    thirteen of.
    """
    if module <= _EPS:
        return minimum
    return max(minimum, int(round(extent / module)))
