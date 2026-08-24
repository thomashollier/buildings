"""Phase 3, part one — the read-only fact set every qualification rule sees.

The brief's complaint about tables is not that they are files. It is that they
are keyed by a *closed enumeration of positions* — "balconies on floors 2 and
5" — so the condition under which a row applies is never written down. Such a
table cannot be composed with anything, argued with, or carried to another
city, because it does not say *why*.

The cure is two-sided and both sides live here:

* **Identity is derived.** ``Role`` and ``rank_from_principal`` arrive already
  computed by phase 2 (``roles.assign_roles``), from positional predicates.
  Nothing in this file or in any rule enumerates a floor number.
* **Applicability is explicit.** A rule states the condition it applies under
  in the vocabulary of this context — "the floor is at least 6 m above the
  pavement" — and that condition *is* the 1823 ordonnance, which is the whole
  point.

``QualContext`` is **read-only, complete before qualification begins, and never
mutated by it** (I1: phases read strictly backwards). It is a frozen
dataclass, so any attempted write raises ``FrozenInstanceError``.

If a rule needs a fact that is not on this list, the correct move is to extend
this dataclass deliberately — not to have the rule import ``SiteContext``, or
reach into the ``Grid``, or take a second argument. Three fields below are
exactly such deliberate extensions to the list CONTRACTS.md froze; each one is
marked ``EXTENSION`` with the rule that could not be written without it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping

from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.trace import FrozenMapping, RuleId
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.roles import Role, RoledGrid

__all__ = [
    "QualContext",
    "Properties",
    "Rule",
    "PROPERTY_KEYS",
    "contexts_for",
    "storey_contexts_for",
]

#: Geometric tolerance. Slot arithmetic is exact to ~1e-12 out of the solver;
#: this is loose enough to absorb that and tight enough never to blur two
#: genuinely different levels.
_EPS = 1e-9


# ---------------------------------------------------------------------------
# The property vocabulary
# ---------------------------------------------------------------------------
#
# A `Properties` payload is SPARSE — an absent key means "no opinion", which is
# exactly how layering works. The failure mode of a sparse mapping keyed by
# strings is the typo: `"balcony_projeciton"` is silently no opinion, nothing
# is emitted, and there is no error to follow. So the vocabulary is closed and
# checked at construction. Extending it is a one-line, greppable, deliberate
# act — the same discipline the context itself is held to.

PROPERTY_KEYS: frozenset[str] = frozenset(
    {
        # what occupies the slot
        "opening_type",  # "window" | "narrow_window" | "shop_bay" |
        #                  "carriage_entrance" | "pedestrian_entrance" |
        #                  "blind_panel" | "oeil_de_boeuf" | "none"
        "opening_head",  # "flat" | "segmental" | "round" | "irregular"
        # The opening's OWN rectangle, stated within the bay slot that carries
        # it. An opening is not a bay: between the two there is a pier either
        # side (``opening_offset_x``), a spandrel below the sill and a course
        # of masonry over the lintel. Without these three the only thing a
        # consumer can do is glaze the whole slot, and a facade of glazed
        # slots is a curtain wall.
        "opening_width",  # metres — PROPORTIONAL for a window, ABSOLUTE for a door
        "opening_height",  # metres — same
        "opening_offset_x",  # metres from the slot's left edge; this IS the pier
        # Metres from the storey's floor to the underside of the opening.
        # Normally ABSOLUTE — ``catalogue.sill_lean_height``, the height a
        # body leans on — and there is deliberately no second key holding a
        # "resolved" position beside it: one fact, one name. Where an opening
        # has no sill (a carriage arch, a devanture stepped over, a
        # porte-fenêtre onto the balcon filant) this is that opening's own
        # bottom edge and the trace says which body fact put it there.
        "opening_sill_height",
        # A14.1. How far a ROUND or segmental head rises over its springing,
        # in metres. Only an opening whose head is a stated curve rather than
        # a drawn flourish carries one: on a two-storey entrance arch the
        # rise IS half the span (``catalogue.round_arch_rise``), which is the
        # difference between a semicircle and the 0.50 m bow the renderer
        # picks for itself out of ``min(0.5, max(0.15, w * 0.30))``. Where no
        # rule states it the renderer keeps its own graphical default, which
        # is what every ordinary window has always had.
        "opening_head_rise",
        # A14.1. Which register of a two-storey entrance arch this cell is:
        # ``"leaves"`` (the rez-de-chaussee -- the leaves and the carved
        # tympanum over them) or ``"arch_head"`` (the entresol -- the
        # balconette, the light and the round head with its agrafe). ``None``
        # on every other cell in Paris. One arch, two registers, exactly as
        # A13's absorbed devanture is one framework in two: the fact that
        # they are one object is stated on both of them, so neither the
        # renderer nor a reader of the IR has to infer it from adjacency.
        "entrance_arch_register",
        # A14.1. The leaves' own clear height inside the lower register, in
        # metres -- the SAME height the one-storey door has, because what
        # passes through the gate did not change. What is left between it and
        # the register's ceiling is the carved tympanum panel.
        "entrance_leaf_height",
        # the frame around it
        "surround_kind",  # "none" | "bare_band" | "moulded_architrave" |
        #                   "pedimented" | "irregular"
        "surround_richness",  # 0..1
        # the 1823 ordonnance
        "balcony_present",
        "balcony_continuous",  # balcon filant vs. individual balconette
        "balcony_projection",  # metres
        "balcony_min_height",  # metres — the regulatory threshold that decided it
        "balcony_rail_height",  # metres — ABSOLUTE, a body leaning on it
        # garde-corps and railings
        "ironwork_present",
        "ironwork_variant",
        "ironwork_gap_max",  # metres — ABSOLUTE, a child's head
        # Metres from the storey's floor to the top of the railing. ABSOLUTE —
        # the height a body leans against — and the garde-corps's OWN fact,
        # not the balcony's. It used to be read off ``balcony_rail_height``,
        # which only exists where the 1823 ordonnance permits a balcony, so
        # every railing below 6 m arrived in the IR with ``h = 0.000`` and
        # drew nothing (A6.6). A rule that emits an element which cannot be
        # seen is a rule putting a lie in the IR.
        "ironwork_height",
        # sculpture over the opening
        "keystone_present",
        "keystone_kind",
        # the ground floor
        "socle_present",
        "socle_treatment",
        # A13.2. Which of the two forms Daly draws the entresol in, where the
        # base block has one: ``"absorbed"`` (the devanture spans the whole
        # base and the entresol is glazed inside its framework — 77 bd de
        # Sébastopol) or ``"arcaded"`` (arched openings in the base's own
        # coursing, standing on the shopfront's entablature — 120 bd de
        # Sébastopol). One fact about the frontage, resolved once, read by
        # every rule that has to know whether the entresol is stone or glass.
        "entresol_treatment",
        "shopfront_present",
        "shopfront_variant",
        "shopfront_pane_max_span",
        "ground_treatment",
        # the horizontal lines
        "cornice_present",
        "cornice_projection",
        "cornice_richness",  # 0..1
        "string_course_present",
        "string_course_kind",
        "string_course_projection",  # metres
        # the overall dial
        "ornament_density",  # 0..1
        # How finely that dial is worked, as the repeat interval of each
        # rhythm on the frontage, in metres (A7.2). "The scale and density of
        # ornament" is on the brief's PROPORTIONAL list, so how many
        # modillions run under a cornice, how many refends cross a socle and
        # how many scrolls run along a garde-corps move with ambition and
        # rank like everything else on that list — and the count they produce
        # travels in the IR. Before A7.2 all six were literals in the
        # renderer, which meant a modest attic and a grand entresol carried
        # the same ornament per metre and only the wall behind it changed
        # size. The BALUSTER gap is deliberately not here: it is ABSOLUTE (a
        # child's head) and lives in ``ironwork_gap_max``.
        "ornament_modillion_module",  # metres between cornice brackets
        "ornament_dentil_module",  # metres between dentils
        "ornament_course_width",  # metres — one drawn stone of a socle course
        "ornament_course_height",  # metres — one drawn course of a socle
        "ornament_bracket_module",  # metres between balcony consoles
        "ornament_ironwork_module",  # metres between scrolls, waves, lozenges
    }
)


# ---------------------------------------------------------------------------
# The context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QualContext:
    """The read-only fact set every rule sees.

    Complete before qualification begins; NEVER mutated by it. One instance
    describes one *cell* of the facade grid: a storey slot crossed with a
    horizontal slot. That is deliberate — the brief's phrasing of phase 3 is
    "for this slot, on a floor of this role, what occupies it?", and a cell is
    precisely the subject of that question. A storey has no rhythm of its own;
    it has a *filling* of the one grid solved in phase 1, which is why nothing
    downstream can drift out of vertical alignment.
    """

    # -- structure (phase 1) ------------------------------------------------
    slot_h: float  # this storey's height, metres
    slot_w: float  # this horizontal slot's width, metres
    level_above_pavement: float  # this storey's floor level, metres
    index_from_bottom: int
    index_from_top: int
    storey_count: int

    # -- role (phase 2) -----------------------------------------------------
    role: Role
    rank_from_principal: int  # 0 on the principal floor, +1 upward

    # -- horizontal (phase 1, the one shared bay solve) ---------------------
    bay_index_from_left: int
    bay_index_from_centre: int  # signed, in slots, relative to the centre slot
    is_centre_bay: bool  # the facade centreline falls strictly inside this slot
    distance_from_entrance: int  # in slots; 0 IS the entrance
    is_edge_special: bool
    is_inserted_special: bool
    slot_kind: SlotKind

    # -- building -----------------------------------------------------------
    year: int
    klass: BuildingClass
    street_width: float
    corner: bool

    # -- envelope -----------------------------------------------------------
    cornice_height: float  # the LEGAL ceiling, metres

    #: This storey sits inside the roof envelope — above the top of the stone
    #: face, in the comble, where the *chambres de bonne* are.
    #:
    #: An ENVELOPE fact, and derived as one: ``Grid.stands_in_the_roof``,
    #: asked of the grid's geometry. Not read off ``Role.ATTIC``, which would
    #: invert the direction the brief states — the slot lies within the
    #: comble, and *therefore* the role is attic, never the other way round.
    #: The two agree by construction because both call the same predicate.
    within_comble: bool

    # -- EXTENSIONS to the frozen list, each with the rule that forced it ---

    #: EXTENSION 1 — what the ground floor is *for*.
    #:
    #: CONTRACTS.md's "building" group carries date, class, street width and
    #: corner, but not the ground programme, and no shopfront rule can be
    #: written without it: whether the base carries a devanture, a porte
    #: cochère or plain masonry is not derivable from any geometric fact on
    #: this list. It is an input to the whole system (``SiteContext.ground``),
    #: so the alternative was a rule importing ``SiteContext`` — precisely the
    #: reaching-around the brief warns against. Handed down, never sampled.
    ground: GroundProgramme

    #: EXTENSION 2 — the *name* phase 1 gave this horizontal slot.
    #:
    #: The brief's own wording for this group is "the slot's kind (opening,
    #: filler, special)", but ``SlotKind`` is the solver's three-way
    #: (FIXED/REPEATING/FLEXIBLE) and does not carry that distinction: an end
    #: pier and a narrow special are both FLEXIBLE. Without the module name a
    #: rule can only recover "this is a pier" as ``bay_index_from_left == 0``
    #: — a position index, i.e. exactly the closed enumeration this design
    #: exists to remove. The name is phase-1 data, read not invented.
    slot_name: str  # "pier_end" | "bay" | "special" | one of
    #                 ``catalogue.ENTRANCE_SLOT_NAMES``

    #: EXTENSION 3 — how many storeys sit inside the comble.
    #:
    #: Needed by any rule about the *top of the wall*: the cornice crowns the
    #: topmost habitable storey, and the second balcon filant runs along it.
    #: ``within_comble`` answers that for the slot in hand but cannot answer
    #: "is the storey above me the roof?", and ``index_from_top`` counts every
    #: storey including combles. This is one envelope-level integer that makes
    #: ``is_topmost_habitable`` derivable; the alternative was putting the
    #: predicate itself in the context, which would have been a rule wearing a
    #: fact's clothes.
    storeys_within_comble: int

    #: EXTENSION 4 — how many storeys make up the commercial base.
    #:
    #: One (the rez-de-chaussée alone) or two (with an entresol over it).
    #: A13's whole claim is that the base is ``RdC + entresol``, and no rule
    #: about the entresol can be written without being able to ask, *from the
    #: rez-de-chaussée as well as from the entresol*, whether the frontage has
    #: one: the devanture that absorbs an entresol is stated on the ground
    #: storey and has to know it is spanning two levels. ``Role.MEZZANINE``
    #: answers that question on one of the two rows and not on the other,
    #: which is exactly the asymmetry an envelope-level count removes. Same
    #: species as ``storeys_within_comble``, and derived the same way — read
    #: off the roled stack, once, before any rule fires.
    storeys_in_the_base_block: int

    #: EXTENSION 5 — the ceiling of that base, metres above the pavement.
    #:
    #: The line the strong string course runs along, and the top of an
    #: absorbed devanture's framework. It is a *height above the pavement*,
    #: like the 1823 ordonnance's own threshold, so the rules that read it
    #: read a level and not a floor number — take the entresol out of the
    #: stack and the crowning course drops to the top of the ground storey by
    #: itself, with no rule change at all.
    base_block_top: float

    # -- derived readers ----------------------------------------------------
    #
    # Pure functions of the fields above — no new facts, just the phrasings
    # rules actually reach for. Kept here so that "the top of this storey" is
    # spelled the same way everywhere and cannot drift.

    @property
    def top_of_slot(self) -> float:
        """Height of this storey's ceiling above the pavement, metres."""
        return self.level_above_pavement + self.slot_h

    @property
    def is_topmost_habitable(self) -> bool:
        """True on the highest storey below the roof — the one the cornice
        crowns. Derived: count down from the top past the comble storeys."""
        return (
            not self.within_comble
            and self.index_from_top == self.storeys_within_comble
        )

    @property
    def stands_in_the_base_block(self) -> bool:
        """This storey is part of the commercial base — the rez-de-chaussée,
        and the entresol over it where one exists (A13.1).

        Asked of the role rather than of the index, because the base and the
        compressed level over it are exactly what ``roles.assign_roles``
        derives; ``storeys_in_the_base_block`` is the same two storeys
        counted, and the two agree by construction because ``contexts_for``
        counts them off the same roles.
        """
        return self.role in (Role.BASE, Role.MEZZANINE)

    @property
    def has_an_entresol(self) -> bool:
        """Does the commercial base carry a compressed level over its shop?"""
        return self.storeys_in_the_base_block > 1

    @property
    def crowns_the_base_block(self) -> bool:
        """This storey's floor IS the top of the commercial base — the line
        that divides commerce from residence (A13.1).

        A height above the pavement compared against a height above the
        pavement, in the same idiom as ``balcony_ordonnance_1823``: the first
        storey standing on the base, whether the base is two levels or one.
        """
        return (
            not self.stands_in_the_base_block
            and self.base_block_top > _EPS
            and abs(self.level_above_pavement - self.base_block_top) <= _EPS
        )

    @property
    def is_entrance(self) -> bool:
        return self.distance_from_entrance == 0

    @property
    def is_special(self) -> bool:
        return self.is_edge_special or self.is_inserted_special


# ---------------------------------------------------------------------------
# What a rule returns
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Properties:
    """What a rule returns. Sparse: unset keys mean "no opinion".

    ``rule`` is the stable dotted id that produced these values and is what
    survives into the trace (I4). ``specificity`` breaks ties *within* a layer
    and is by convention ``10 × (number of independent conditions the rule's
    applicability tests)`` — see ``qualify.base`` for the scale in use.
    """

    values: Mapping[str, object]
    rule: RuleId
    specificity: int = 0

    def __post_init__(self) -> None:
        if not self.rule or not self.rule.strip():
            raise ValueError("Properties.rule must be a non-empty RuleId (I4)")
        unknown = sorted(set(self.values) - PROPERTY_KEYS)
        if unknown:
            raise ValueError(
                f"rule {self.rule!r} set unknown property key(s) {unknown}. "
                "An unrecognised key would silently read as 'no opinion' and "
                "emit nothing. Add it to qualify.context.PROPERTY_KEYS if it "
                "is genuinely new vocabulary."
            )
        object.__setattr__(self, "values", FrozenMapping(self.values))


Rule = Callable[[QualContext, DecisionStream], "Properties | None"]


# ---------------------------------------------------------------------------
# Building the context grid
# ---------------------------------------------------------------------------


def _centre_slot_index(bays: tuple[PlacedSlot, ...]) -> int:
    """Index of the horizontal slot the facade centreline falls in.

    Half-open, so exactly one slot always wins even when the axis lands on a
    joint (which it does on every symmetric even run); ``is_centre_bay``
    below is the stricter question and answers False for both neighbours in
    that case.
    """
    if not bays:
        return 0
    total = math.fsum(s.width for s in bays)
    mid = total / 2.0
    for i, s in enumerate(bays):
        if s.start - _EPS <= mid < s.start + s.width - _EPS:
            return i
    return len(bays) - 1


def _entrance_slot_index(bays: tuple[PlacedSlot, ...], centre: int) -> int:
    """Which slot the front door is in.

    Since A6.1 phase 1 places an explicit FIXED entrance slot on **every**
    building — a porte cochère or a porte piétonne, chosen from class and
    street width — so on any grid this system produced there is nothing to
    decide here: the slot's name says so, and it is read.

    The fallback below survives for a hand-built grid that carries no
    entrance slot at all (a chamfer's short facade, a test fixture): the
    entrance is then taken to be the bay nearest the axis, which is the
    Parisian norm and is what keeps ``distance_from_entrance`` meaningful
    instead of undefined. Read here, once, as a *fact* of the context, rather
    than left to a rule: it must be complete before qualification begins.
    """
    for i, s in enumerate(bays):
        if s.name in catalogue.ENTRANCE_SLOT_NAMES:
            return i
    candidates = [i for i, s in enumerate(bays) if s.name == "bay"]
    if not candidates:
        return centre
    return min(candidates, key=lambda i: (abs(i - centre), i))


def _special_flags(bays: tuple[PlacedSlot, ...]) -> tuple[list[bool], list[bool]]:
    """Split the special slots into edge and inserted.

    A special is an *edge* special when nothing but end pieces stand between
    it and its side of the run — the solver's "lone special answering an
    off-centre entrance" case. Otherwise it was inserted into the middle of
    the run, which is the case that puts it on the centreline. Asked
    positionally, of the run itself, so it stays true whatever names phase 1
    used.
    """
    n = len(bays)
    interior = [i for i, s in enumerate(bays) if s.name != "pier_end"]
    first = interior[0] if interior else -1
    last = interior[-1] if interior else -1
    edge = [False] * n
    inserted = [False] * n
    for i, s in enumerate(bays):
        if not s.is_special:
            continue
        if i == first or i == last:
            edge[i] = True
        else:
            inserted[i] = True
    return edge, inserted


def contexts_for(
    roled: RoledGrid, site: SiteContext
) -> tuple[tuple[QualContext, ...], ...]:
    """Every cell of the facade grid, as ``[storey][horizontal slot]``.

    Reads phases 1 and 2 and the situation, and nothing else (I1). Runs no
    RNG, takes no decisions beyond the two documented derivations above, and
    returns frozen objects — so the whole fact set really is complete before
    the first rule fires.
    """
    bays = roled.bays
    cornice_height = float(roled.grid.cornice_height)
    centre = _centre_slot_index(bays)
    entrance = _entrance_slot_index(bays, centre)
    edge_flags, inserted_flags = _special_flags(bays)
    # Asked of the envelope, once, and reused for every cell of the row — the
    # same predicate phase 2 turned into ``Role.ATTIC``, so a rule keyed to
    # the role and a rule keyed to the comble can never disagree about which
    # storeys are in the roof.
    in_comble = [
        roled.grid.stands_in_the_roof(st.index_from_bottom) for st in roled.storeys
    ]
    n_comble = sum(1 for flag in in_comble if flag)
    n_storeys = len(roled.storeys)
    # A13.1: the commercial base, read off the roled stack once. The base
    # block is the rez-de-chaussée and the compressed level over it — the two
    # roles phase 2 already derived — and its ceiling is the top of the
    # highest of them. Where a hand-built grid names neither, the block is
    # empty and its top is 0.0, which ``crowns_the_base_block`` refuses rather
    # than reading as "the pavement crowns the base".
    base_block = [
        st for st in roled.storeys if st.role in (Role.BASE, Role.MEZZANINE)
    ]
    n_base_block = len(base_block)
    base_block_top = (
        max(st.slot.start + st.slot.width for st in base_block) if base_block else 0.0
    )

    grid: list[tuple[QualContext, ...]] = []
    for st in roled.storeys:
        row: list[QualContext] = []
        for i, bay in enumerate(bays):
            row.append(
                QualContext(
                    slot_h=st.slot.width,
                    slot_w=bay.width,
                    level_above_pavement=st.slot.start,
                    index_from_bottom=st.index_from_bottom,
                    index_from_top=st.index_from_top,
                    storey_count=n_storeys,
                    role=st.role,
                    rank_from_principal=st.rank_from_principal,
                    bay_index_from_left=i,
                    bay_index_from_centre=i - centre,
                    is_centre_bay=(
                        bay.start + _EPS
                        < math.fsum(s.width for s in bays) / 2.0
                        < bay.start + bay.width - _EPS
                    ),
                    distance_from_entrance=abs(i - entrance),
                    is_edge_special=edge_flags[i],
                    is_inserted_special=inserted_flags[i],
                    slot_kind=bay.kind,
                    year=site.year,
                    klass=site.klass,
                    street_width=site.street_width,
                    corner=site.corner,
                    cornice_height=cornice_height,
                    within_comble=in_comble[st.index_from_bottom],
                    ground=site.ground,
                    slot_name=bay.name,
                    storeys_within_comble=n_comble,
                    storeys_in_the_base_block=n_base_block,
                    base_block_top=base_block_top,
                )
            )
        grid.append(tuple(row))
    return tuple(grid)


def storey_contexts_for(
    roled: RoledGrid, site: SiteContext
) -> tuple[QualContext, ...]:
    """One representative context per storey — the leftmost cell of each row.

    Storey-scope properties (socle, cornice, string course, the balcon filant,
    the shopfront) come from rules whose applicability reads no horizontal
    fact, so every cell in a row returns the same answer for them and the
    leftmost is as good as any. ``test_compose`` asserts that invariance
    directly rather than trusting the claim, which is the point of stating it
    as an invariant instead of a convention.
    """
    return tuple(row[0] for row in contexts_for(roled, site))
