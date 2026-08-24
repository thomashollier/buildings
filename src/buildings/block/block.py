"""The block: the unit the street is actually made of.

A building on a nineteenth-century Paris street is not autonomous. Its cornice
continues its neighbour's cornice; its string courses and balcony lines run
across the party wall it shares. The block was conceived as one architectural
object with several owners, and the regulation said so explicitly — the
**circulaire du 21 septembre 1855** requires balcony, cornice and entablature
lines to align from building to building within a block.

So this module is not a loop over buildings. It is the thing that resolves the
facts a whole run of buildings has in common, hands them down, and then refuses
to assemble a block whose buildings disagree about them.

The named failure this exists to prevent
----------------------------------------
    "In the previous attempt every building sampled its own street width
    independently — so buildings that were, by construction, on the same street
    disagreed about how wide it was, and their cornice lines did not line up.
    *Nothing errored.* The street simply looked subtly wrong, and the cause was
    a block-level fact being resolved per building."

Two mechanisms, together, make that unrepeatable:

1. **The channel is one-way (I2).** ``BlockDatums`` is resolved here, before a
   single building exists, and handed *down* to ``generate``. ``SiteContext``
   carries no RNG and offers no sampling method, so a building physically
   cannot roll its own street width; it can only be told one.
2. **The seam is audited.** ``check_alignment`` re-reads, out of the finished
   IR and its traces, what every building actually believed and actually built,
   and raises ``BlockDatumViolation`` on any disagreement beyond 1e-9. A
   misalignment that used to be a look now stops the build with the two
   offending values printed. ``solve_block`` calls it on every block it
   assembles, and ``tests/invariant/test_block_datums.py`` proves it has teeth
   by feeding it a deliberately rogue building.

What the block owns
-------------------
Per the brief's own working-through of the open question, the block **always**
owns the subdivision of frontage and who abuts whom — that part is irreducible
under alignment, repetition and independence alike. For Paris it owns, in
addition, the shared horizontal datums: the cornice line, the string courses
and the *balcons filants*. That is the alignment column of the brief's table:

    | Relation      | The block owns            | The building receives  |
    | Alignment     | shared horizontal datums  | constraints to satisfy |
    | Repetition    | the design itself         | an instance            |
    | Independence  | parcel widths, adjacency  | only its lot           |

**No general binding system is built here**, deliberately. The brief defers
that to the second typology port: "designing a general binding system now risks
a mechanism that elegantly solves a problem nobody has." Paris aligns. This
builds alignment, concretely, and keeps the channel one-way so its *contents*
can grow later without its *direction* being renegotiated.

The vertical registration, and why a regime is block-scoped
-----------------------------------------------------------
Handing down one street width and one legal cornice ceiling is enough to make
every building on the run stop its stone face at the same height — provided
they share a class, because ``structure`` scales its facade ambition by class.
It is *not* enough to align the lines in between. A shop with an entresol puts
its noble floor 0.8 m below its neighbour's, and 0.8 m is not a rounding error:
it is precisely the misregistration the 1855 circulaire forbids.

Measured across every era, street width, class and parcel in the sweep, the
storey registration is a pure function of ``(street_width, year, klass,
ground regime)`` — insensitive to parcel width, parcel depth, seed and corner
(``test_registration_depends_only_on_block_facts`` asserts exactly this). What
moves it is the *regime* of the ground floor: commercial (shop / café /
office), residential, or carriage entrance. Those three set different ground
storey heights and different entresol decisions.

So the regime is a **block fact**, and this module says so out loud. A block is
commercial or it is residential; within a commercial block a parcel may be a
shop, a café or an office, and none of those moves a single line. Handing
``solve_block`` a mix of regimes raises ``BlockDatumViolation`` at the seam
rather than producing a street that is subtly out of register — the same
discipline A2.6 asked for where two modules rely on one unstated invariant.

Corners
-------
A corner is **not a module type**. Where the corner is chamfered — the Paris
*pan coupé* — it becomes a **third short facade with its own rhythm**, the join
between two grammars, and it gets its own concept here (``Chamfer``) with its
own bay solve out of the same generic solver. It is deliberately not squeezed
into either facade's row of bays, because it does not fit there.

Geometry
--------
The IR's convention is "origin at pavement level at the **left edge of the
parcel**". Buildings therefore stay in their own parcel-local coordinates, and
the block's ``parcel`` node carries the offset along the frontage. The one
exception is the block's own datum lines and party walls, which are block-scope
objects and are measured from the left end of the run — they belong to no
parcel, which is the whole point of them.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Iterator, Mapping, Sequence

from buildings.ir.nodes import (
    BalconyNode,
    BayNode,
    CorniceNode,
    Node,
    OpeningNode,
    ShopfrontNode,
    StoreyNode,
    StringCourseNode,
)
from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import PlacedSlot, SlotKind, SlotSpec, solve
from buildings.trace import TraceEntry
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.terminate import derive_hip_arris
from buildings.typologies.paris.compose import Layer
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.reglement_adapter import (
    _CITATIONS as _REGLEMENT_CITATIONS,
)
from buildings.typologies.paris.reglement_adapter import (
    balcony_rule,
    era_for_year,
    get_reglement,
)

__all__ = [
    "Block",
    "BlockDatums",
    "BlockDatumViolation",
    "CIRCULAIRE_1855",
    "Chamfer",
    "DATUM_TOLERANCE",
    "GroundRegime",
    "Parcel",
    "block_nodes",
    "chamfer_for",
    "check_alignment",
    "plan_block",
    "resolve_datums",
    "solve_block",
    "subdivide",
]


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------
#
# The 1855 circulaire is the authority for everything this module aligns, and
# it is read out of the regulatory module rather than retyped here — a citation
# duplicated in two files is a citation that can come to disagree with itself.
# ``reglement_adapter._CITATIONS`` is the one table of sources; that it is
# spelled with a leading underscore is a gap in that module's public surface
# (a ``citation(key)`` accessor would be the right shape), not an invitation to
# copy the string.
CIRCULAIRE_1855: str = _REGLEMENT_CITATIONS["1855"]

#: Absolute tolerance for "the same line". A datum is a shared fact, not a
#: nearly-shared one: two buildings either stand on the same cornice line or
#: they do not. 1e-9 is the solver's own residual tolerance, so a line that
#: differs by more than this differs because a *decision* differed, which is
#: exactly what must not happen silently.
DATUM_TOLERANCE: float = 1e-9


class BlockDatumViolation(RuntimeError):
    """A block-level fact was not shared.

    Raised where two buildings on one block disagree about something the block
    owns — the street width, the cornice line, a string course, a balcon
    filant — or where a caller tries to mix ground-floor regimes that would
    put the storey registration out of alignment.

    This exception is the entire point of the module. The failure it names is
    one that previously produced no error at all.
    """


# ---------------------------------------------------------------------------
# INFERRED constants — placeholders, not findings.
#
# Same status as ``quantity._CLASS_SCALE`` (A1.3) and ``structure``'s ambition
# constants: no source in the brief or the regulations gives these numbers.
# Where an ordering or a bound is contractual it is said so; the values
# themselves are provisional pending real design input, and every one of them
# is reported in the trace of the node it produced.
# ---------------------------------------------------------------------------

#: INFERRED. The parcel width a Paris frontage was typically divided into.
#: Only the band matters: haussmannian lots run roughly one to two bays wide at
#: the bottom and four or five at the top.
_TYPICAL_PARCEL_WIDTH: float = 12.0
_MIN_PARCEL_WIDTH: float = 6.5
_MAX_PARCEL_WIDTH: float = 22.0

#: INFERRED. Parcel depth, and how much it varies down a run. Depth does not
#: move any datum (asserted in the invariant tests) — it is here because a
#: parcel has one, not because the block needs it to align anything.
_TYPICAL_PARCEL_DEPTH: float = 18.0
_DEPTH_VARIATION: float = 0.15

#: INFERRED. Frontage was not laid out parcel by parcel: a builder bought two
#: or three lots and put up one elevation across them, which is why a real run
#: reads as clusters of similar widths rather than as noise. Run lengths and
#: the width scale each run works at.
_RUN_LENGTHS: tuple[int, ...] = (1, 2, 3, 4)
_RUN_LENGTH_WEIGHTS: tuple[float, ...] = (0.34, 0.30, 0.22, 0.14)
_RUN_SCALE: tuple[float, float] = (0.84, 1.20)

#: INFERRED. Per-parcel jitter inside a run — the lots one builder bought were
#: similar, not identical.
_PARCEL_JITTER: tuple[float, float] = (0.95, 1.05)

#: INFERRED. Corner lots are usually wider and differently treated (the brief
#: says so of brownstone rows, and it is as true of Paris: the corner building
#: is the one that gets the dome).
_CORNER_WIDTH_BONUS: float = 1.25

#: INFERRED. The party wall is shared, so it is emitted once by the block and
#: sits astride the boundary rather than inside either lot.
_PARTY_WALL_THICKNESS: float = 0.40

#: INFERRED. The *pan coupé*: the chamfer cut across the angle where two
#: streets meet. Paris required corner buildings to be cut back but our sources
#: give no figure, so this is a band, not a citation. Wide enough for one
#: window per floor and rarely wide enough for two — which is exactly why it
#: needs its own rhythm instead of a bay of either facade.
_CHAMFER_WIDTH: tuple[float, float] = (3.0, 4.6)

#: INFERRED. The chamfer's own bay band, and deliberately *not* the facade's
#: (``structure`` uses 2.70 / 3.00 / 3.30 before class scaling). The pan coupé
#: is the join between two grammars: narrower openings, tighter piers, and at
#: most two of them. Widening this band until it matched the facade's would be
#: the exact mistake the brief warns against — treating the corner as a module
#: of the row.
_CHAMFER_BAY: tuple[float, float, float] = (2.20, 2.55, 2.95)
_CHAMFER_END: tuple[float, float, float] = (0.30, 0.55, 1.10)
_CHAMFER_MAX_BAYS: int = 2

#: INFERRED. The reference parcel the block resolves its registration on. Its
#: width, depth and seed are asserted not to matter
#: (``test_registration_depends_only_on_block_facts``); it exists because
#: ``generate`` needs a lot to stand on, not because the datums depend on it.
_REFERENCE_PARCEL_WIDTH: float = 12.0
_REFERENCE_PARCEL_DEPTH: float = 18.0


# ---------------------------------------------------------------------------
# The ground-floor regime — a block fact, not a parcel fact
# ---------------------------------------------------------------------------


class GroundRegime(Enum):
    """What the ground floor of this *run* is for.

    The regime is block-scoped because it is the one remaining thing that moves
    the storey registration. Within a regime the individual programme is a
    parcel fact and moves nothing: a café next to a shop next to an office
    shares every line, because ``structure`` gives all three the same ground
    storey and the same entresol decision.

    Across regimes it moves everything. A residential ground floor is shorter
    than a commercial one and takes no entresol; a carriage entrance is an
    ABSOLUTE 3.30 m clearance that scales with nothing. Any of those next to a
    shop puts the bandeau and the balcon filant out of register by the better
    part of a metre — which is what the 1855 circulaire exists to forbid, and
    what ``check_alignment`` refuses here.
    """

    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"
    CARRIAGE = "carriage"

    @property
    def programmes(self) -> tuple[GroundProgramme, ...]:
        """The ground programmes a parcel on this block may take."""
        return _REGIME_PROGRAMMES[self]

    @property
    def weights(self) -> tuple[float, ...]:
        """INFERRED. How the programmes mix along a run of this regime."""
        return _REGIME_WEIGHTS[self]

    @classmethod
    def of(cls, ground: GroundProgramme) -> GroundRegime:
        """The regime a ground programme belongs to."""
        for regime, programmes in _REGIME_PROGRAMMES.items():
            if ground in programmes:
                return regime
        raise ValueError(f"no regime covers ground programme {ground!r}")


_REGIME_PROGRAMMES: Mapping[GroundRegime, tuple[GroundProgramme, ...]] = {
    GroundRegime.COMMERCIAL: (
        GroundProgramme.SHOP,
        GroundProgramme.CAFE,
        GroundProgramme.OFFICE,
    ),
    GroundRegime.RESIDENTIAL: (GroundProgramme.RESIDENTIAL,),
    GroundRegime.CARRIAGE: (GroundProgramme.CARRIAGE,),
}

_REGIME_WEIGHTS: Mapping[GroundRegime, tuple[float, ...]] = {
    GroundRegime.COMMERCIAL: (0.60, 0.25, 0.15),
    GroundRegime.RESIDENTIAL: (1.0,),
    GroundRegime.CARRIAGE: (1.0,),
}


# ---------------------------------------------------------------------------
# What the block hands down
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BlockDatums:
    """What the block hands DOWN. One-way (I2).

    Every field is a fact about the *run*, resolved once, before any building
    exists. A building receives this object; it never constructs one, never
    samples any of it, and never has a way to.

    ``street_width``
        ONE value for the whole block. The named failure.
    ``cornice_height``
        The legal ceiling on the stone face for that street in that year —
        ``Reglement.facade_height_limit``. Combined with the block's single
        class it makes every eaves line on the run identical.
    ``string_course_levels``
        Heights above the pavement, bottom-up, at which a bandeau runs. On a
        residential run that is one line (under the noble floor); over a
        commercial ground floor it is two (the plat-bande closing the entresol,
        and the bandeau under the noble floor).
    ``balcony_levels``
        Heights above the pavement at which a *balcon filant* runs. Continuous
        balconies only: an individual balconette is a bay-scale decision inside
        one building and does not run across a party wall, so it is not a block
        fact and is not listed here.

    CONTRACTS.md types ``string_course_levels`` as ``tuple[float, float, ...]``,
    which reads as "at least two". A residential run genuinely has one bandeau
    and no entresol line, so the annotation here is the variadic
    ``tuple[float, ...]``; the discrepancy is reported rather than worked
    around.
    """

    street_width: float
    cornice_height: float
    string_course_levels: tuple[float, ...]
    balcony_levels: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "street_width", float(self.street_width))
        object.__setattr__(self, "cornice_height", float(self.cornice_height))
        object.__setattr__(
            self, "string_course_levels", tuple(float(v) for v in self.string_course_levels)
        )
        object.__setattr__(
            self, "balcony_levels", tuple(float(v) for v in self.balcony_levels)
        )
        if self.street_width <= 0.0:
            raise ValueError(f"street_width must be positive, got {self.street_width!r}")
        if self.cornice_height <= 0.0:
            raise ValueError(f"cornice_height must be positive, got {self.cornice_height!r}")
        for name in ("string_course_levels", "balcony_levels"):
            levels = getattr(self, name)
            if any(b <= a for a, b in zip(levels, levels[1:])):
                raise ValueError(
                    f"{name} must be strictly increasing bottom-up, got {levels!r}"
                )

    @property
    def levels(self) -> tuple[float, ...]:
        """Every shared horizontal line, bottom-up, cornice included.

        The 1855 circulaire names balcony, cornice and entablature lines
        together; this is that list, and it is what "the block reads as one
        wall" means numerically.
        """
        return tuple(
            sorted({*self.string_course_levels, *self.balcony_levels, self.cornice_height})
        )


# ---------------------------------------------------------------------------
# Frontage subdivision and adjacency — irreducibly the block's
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Parcel:
    """One lot on the run, and who abuts it.

    ``left_neighbour`` / ``right_neighbour`` are indices into the block's
    ``parcels``, or ``None`` at the ends of the run. They are the adjacency the
    brief calls irreducible: party walls and lot widths are block facts under
    every relation, whether or not anything else is shared.

    A parcel carries no street width, no class and no year. Those are the
    block's, and a parcel that carried a copy of one would be a second place
    for them to disagree.
    """

    width: float
    depth: float
    corner: bool
    left_neighbour: int | None
    right_neighbour: int | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "width", float(self.width))
        object.__setattr__(self, "depth", float(self.depth))
        if self.width <= 0.0:
            raise ValueError(f"parcel width must be positive, got {self.width!r}")
        if self.depth <= 0.0:
            raise ValueError(f"parcel depth must be positive, got {self.depth!r}")

    @property
    def detached(self) -> bool:
        """True where the lot abuts nothing — a single-parcel block."""
        return self.left_neighbour is None and self.right_neighbour is None


@dataclass(frozen=True)
class Chamfer:
    """The *pan coupé*: a third short facade where two streets meet.

    A corner is not a module type, and this is what it is instead. Where the
    angle is cut, the cut face is a facade in its own right: it has its own
    width, its own rhythm, and it carries the block's datums around the corner
    so that the cornice of one street becomes the cornice of the other.

    ``bays`` is solved out of the same generic 1-D solver every facade uses,
    against its own band (``_CHAMFER_BAY``) — narrow openings, tight piers, at
    most two of them. The brief is explicit that the corner "will not fit" into
    the row of bays, and this is the shape of not making it fit: a separate
    budget, separately solved, joined to the two facades only by the datums all
    three share.
    """

    parcel: int
    side: str  # "left" | "right" — which end of the run the corner is at
    width: float
    bays: tuple[PlacedSlot, ...]
    account: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "width", float(self.width))
        object.__setattr__(self, "bays", tuple(self.bays))
        object.__setattr__(self, "account", tuple(self.account))
        if self.side not in ("left", "right"):
            raise ValueError(f"chamfer side must be 'left' or 'right', got {self.side!r}")
        if self.width <= 0.0:
            raise ValueError(f"chamfer width must be positive, got {self.width!r}")


@dataclass(frozen=True)
class Block:
    """A run of frontage, its lots, and the facts they hold in common.

    ``street_width`` appears both here and on ``datums``. That is CONTRACTS.md's
    shape, and two copies of one fact is two places for it to drift, so
    ``__post_init__`` asserts they agree — the A2.6 discipline of stating an
    invariant where two things meet rather than relying on it silently.

    ``chamfers`` is an addition to the contract's three fields, defaulted so
    every construction the contract describes still works positionally. It is
    here because S9's brief requires the corner to have its own concept and a
    chamfer is not expressible as a parcel: it is a third facade belonging to a
    corner *building*, cut out of that building's frontage on this street.
    """

    street_width: float
    parcels: tuple[Parcel, ...]
    datums: BlockDatums
    chamfers: tuple[Chamfer, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "street_width", float(self.street_width))
        object.__setattr__(self, "parcels", tuple(self.parcels))
        object.__setattr__(self, "chamfers", tuple(self.chamfers))
        if not self.parcels:
            raise ValueError("a block has at least one parcel")
        if abs(self.street_width - self.datums.street_width) > DATUM_TOLERANCE:
            raise BlockDatumViolation(
                "Block.street_width and Block.datums.street_width are the same fact "
                f"stored twice and they disagree: {self.street_width!r} vs "
                f"{self.datums.street_width!r}. One street, one width."
            )
        for i, parcel in enumerate(self.parcels):
            expect_left = i - 1 if i > 0 else None
            expect_right = i + 1 if i + 1 < len(self.parcels) else None
            if parcel.left_neighbour != expect_left or parcel.right_neighbour != expect_right:
                raise ValueError(
                    f"parcel {i} declares neighbours "
                    f"({parcel.left_neighbour}, {parcel.right_neighbour}); the run says "
                    f"({expect_left}, {expect_right}). Adjacency is the block's fact."
                )
        for chamfer in self.chamfers:
            if not 0 <= chamfer.parcel < len(self.parcels):
                raise ValueError(f"chamfer names parcel {chamfer.parcel}, which is not on the run")
            if not self.parcels[chamfer.parcel].corner:
                raise ValueError(
                    f"chamfer cuts parcel {chamfer.parcel}, which is not marked as a corner"
                )
        sides = [c.side for c in self.chamfers]
        if len(set(sides)) != len(sides):
            raise ValueError("a run has at most one chamfer at each end")

    # -- layout ---------------------------------------------------------

    @property
    def frontage(self) -> float:
        """The whole run, chamfers included, measured along this street."""
        return math.fsum([p.width for p in self.parcels] + [c.width for c in self.chamfers])

    def chamfer_at(self, side: str) -> Chamfer | None:
        for chamfer in self.chamfers:
            if chamfer.side == side:
                return chamfer
        return None

    @property
    def origins(self) -> tuple[float, ...]:
        """Each parcel's left edge, measured from the left end of the run.

        This is the only place a building's position on the street is decided,
        and it is decided by cumulative width — which is what makes "who abuts
        whom" and "where does it stand" the same fact rather than two.
        """
        left = self.chamfer_at("left")
        x = left.width if left is not None else 0.0
        out: list[float] = []
        for parcel in self.parcels:
            out.append(x)
            x += parcel.width
        return tuple(out)

    def chamfer_origin(self, chamfer: Chamfer) -> float:
        if chamfer.side == "left":
            return 0.0
        origins = self.origins
        return origins[-1] + self.parcels[-1].width

    def junctions(self) -> tuple[tuple[int, int, float], ...]:
        """Every party wall on the run as ``(left parcel, right parcel, x)``.

        Emitted once per junction, not once per building, because a party wall
        is *shared* — it belongs to neither of the two buildings that lean on
        it, which is exactly the sort of fact the block exists to hold.
        """
        origins = self.origins
        return tuple(
            (i, i + 1, origins[i] + self.parcels[i].width)
            for i in range(len(self.parcels) - 1)
        )


# ---------------------------------------------------------------------------
# subdivide — the rhythm of frontage widths along the run
# ---------------------------------------------------------------------------


def subdivide(
    frontage: float,
    rng: DecisionStream,
    *,
    path: str = "block/frontage",
    typical_width: float = _TYPICAL_PARCEL_WIDTH,
    min_width: float = _MIN_PARCEL_WIDTH,
    max_width: float = _MAX_PARCEL_WIDTH,
    depth: float = _TYPICAL_PARCEL_DEPTH,
    depth_variation: float = _DEPTH_VARIATION,
    corner_left: bool = False,
    corner_right: bool = False,
) -> tuple[Parcel, ...]:
    """Divide a run of frontage into lots, and record who abuts whom.

    Parcels were not uniform, and they were not noise either. Frontage was
    bought and built in **runs**: one builder took two or three adjacent lots
    and put up a single elevation across them, which is why a real street reads
    as clusters of similar widths with occasional odd lots between them. That
    is the structure drawn here — a run length and a run-wide width scale, then
    a small per-parcel jitter inside it.

    Every draw is addressed through ``DecisionStream``:
    ``{path}/run/{k}/length``, ``{path}/run/{k}/scale``,
    ``{path}/parcel/{i}/jitter``, ``{path}/parcel/{i}/depth``. Each path's state
    is derived from ``(seed, path)`` alone, so the rhythm is reproducible, one
    parcel can be pinned without disturbing its neighbours, and adding a new
    kind of draw later cannot shift any existing one (I5).

    The widths are then normalised to fill ``frontage`` **exactly** — a block
    with a gap in it is not a block — and clamped into ``[min_width,
    max_width]`` with the residual redistributed among the lots that still have
    room. Corner lots take ``_CORNER_WIDTH_BONUS`` extra, because the corner
    building is the one with something to show on two streets.
    """
    if frontage <= 0.0:
        raise ValueError(f"frontage must be positive, got {frontage!r}")
    if not 0.0 < min_width <= max_width:
        raise ValueError(f"bad width band [{min_width!r}, {max_width!r}]")

    # A frontage shorter than one lot is still a frontage: a leftover sliver
    # between two earlier developments is a real Paris condition, and refusing
    # it would be the band overruling the ground.
    lo = min(min_width, frontage)
    hi = max_width

    n = _parcel_count(frontage, typical_width, lo, hi)

    # -- the run structure ------------------------------------------------
    scales: list[float] = []
    run_index = 0
    while len(scales) < n:
        length = rng.choice(
            f"{path}/run/{run_index}/length", _RUN_LENGTHS, _RUN_LENGTH_WEIGHTS
        )
        scale = rng.uniform(f"{path}/run/{run_index}/scale", *_RUN_SCALE)
        scales.extend([scale] * int(length))
        run_index += 1
    scales = scales[:n]

    weights: list[float] = []
    for i in range(n):
        jitter = rng.uniform(f"{path}/parcel/{i}/jitter", *_PARCEL_JITTER)
        weight = scales[i] * jitter
        if (i == 0 and corner_left) or (i == n - 1 and corner_right):
            weight *= _CORNER_WIDTH_BONUS
        weights.append(weight)

    widths = _fit_widths(weights, frontage, lo, hi)

    parcels: list[Parcel] = []
    for i, width in enumerate(widths):
        factor = rng.uniform(
            f"{path}/parcel/{i}/depth", 1.0 - depth_variation, 1.0 + depth_variation
        )
        parcels.append(
            Parcel(
                width=width,
                depth=depth * factor,
                corner=(i == 0 and corner_left) or (i == n - 1 and corner_right),
                left_neighbour=i - 1 if i > 0 else None,
                right_neighbour=i + 1 if i + 1 < n else None,
            )
        )
    return tuple(parcels)


def _parcel_count(frontage: float, typical: float, lo: float, hi: float) -> int:
    """How many lots a run of this length was divided into.

    Chosen so the average lot lands as close to ``typical`` as the band allows;
    the band wins where they conflict, because a 30 m lot is not a Paris lot
    however tidily it divides the frontage.
    """
    n = max(1, round(frontage / typical))
    while n > 1 and frontage / n < lo:
        n -= 1
    while frontage / n > hi:
        n += 1
    return n


def _fit_widths(
    weights: Sequence[float], frontage: float, lo: float, hi: float
) -> tuple[float, ...]:
    """Turn relative weights into widths that sum to ``frontage`` exactly.

    Clamping and redistribution iterate to a fixed point; the last few
    picometres of residual then go to whichever unclamped lot has the most room
    for them, so the sum is exact rather than nearly exact. The block's own
    invariant test checks that against ``frontage`` at 1e-9.
    """
    n = len(weights)
    total = math.fsum(weights)
    widths = [frontage * w / total for w in weights]

    for _ in range(n + 2):
        clamped = [i for i, w in enumerate(widths) if w < lo - 1e-12 or w > hi + 1e-12]
        if not clamped:
            break
        for i in clamped:
            widths[i] = min(hi, max(lo, widths[i]))
        free = [i for i in range(n) if i not in clamped]
        residual = frontage - math.fsum(widths)
        if not free or abs(residual) < 1e-12:
            break
        share = math.fsum(widths[i] for i in free)
        for i in free:
            widths[i] += residual * (widths[i] / share if share > 0 else 1.0 / len(free))

    residual = frontage - math.fsum(widths)
    if abs(residual) > 0.0:
        headroom = [(hi - w if residual > 0 else w - lo, i) for i, w in enumerate(widths)]
        _, i = max(headroom)
        widths[i] += residual
    return tuple(widths)


# ---------------------------------------------------------------------------
# The chamfer — a third short facade, with its own rhythm
# ---------------------------------------------------------------------------


def chamfer_for(
    parcel: int,
    side: str,
    rng: DecisionStream,
    *,
    path: str = "block/frontage",
) -> Chamfer:
    """Cut the angle, and give the cut face a facade of its own.

    The width is drawn from ``_CHAMFER_WIDTH`` (INFERRED — Paris required the
    corner to be cut but our sources give no figure) and the rhythm is solved
    against ``_CHAMFER_BAY``, a band of its own. Both facts are recorded in the
    ``account`` so the chamfer can say why it is the width it is.
    """
    width = rng.uniform(f"{path}/chamfer/{side}/width", *_CHAMFER_WIDTH)
    end = SlotSpec("pier_end", SlotKind.FLEXIBLE, *_CHAMFER_END, elasticity=2.0)
    bay = SlotSpec("bay", SlotKind.REPEATING, *_CHAMFER_BAY)
    fit = solve(width, end=end, bay=bay, min_bays=1, max_bays=_CHAMFER_MAX_BAYS)
    account = (
        f"pan coupé at the {side} corner of the run, cutting parcel {parcel}: "
        f"{width:.2f} m of frontage (INFERRED band "
        f"[{_CHAMFER_WIDTH[0]:.2f}, {_CHAMFER_WIDTH[1]:.2f}] m — the corner was required "
        "to be cut, but no figure survives in our sources)",
        f"its own rhythm, not the facade's: bay band "
        f"[{_CHAMFER_BAY[0]:.2f}, {_CHAMFER_BAY[1]:.2f}, {_CHAMFER_BAY[2]:.2f}] m against the "
        "facade's 2.70 / 3.00 / 3.30 — a corner is not a module of the row",
        *fit.account,
    )
    return Chamfer(parcel=parcel, side=side, width=width, bays=fit.slots, account=account)


# ---------------------------------------------------------------------------
# Resolving the datums — once, for the whole run, before any building exists
# ---------------------------------------------------------------------------


def resolve_datums(
    street_width: float,
    year: int,
    klass: BuildingClass,
    regime: GroundRegime = GroundRegime.COMMERCIAL,
) -> BlockDatums:
    """Resolve everything the run holds in common. One-way from here down.

    Two of the four facts come straight out of the regulation: the street width
    is given, and the legal cornice ceiling is ``facade_height_limit`` for that
    width in that year.

    The other two — where the bandeaux run, where the balcons filants run — are
    not in any decree. They are consequences of the storey registration, and
    the 1855 circulaire's demand is precisely that the run share one. So the
    block resolves them the way a nineteenth-century block was actually
    designed: it draws **one reference elevation** for the run and registers
    every building to it. That elevation is generated here, from block facts
    only, and the levels are read back off it.

    That this is legitimate rests on a measured fact, asserted in
    ``tests/invariant/test_block_datums.py``: the registration is a pure
    function of ``(street_width, year, klass, regime)`` and is insensitive to
    parcel width, parcel depth, corner and seed. The reference lot is therefore
    not a hidden parameter — change it and nothing moves.

    The 6 m floor under every balcony line is the ordonnance de 1823's, read
    from ``reglement``; it is checked here rather than assumed, because a datum
    that quietly went illegal would propagate to every building on the run.
    """
    if not isinstance(regime, GroundRegime):
        raise ValueError(f"unknown ground regime {regime!r}")
    ceiling = get_reglement(era_for_year(year)).facade_height_limit(float(street_width))
    string_courses, balconies = _reference_lines(float(street_width), int(year), klass, regime)

    threshold = float(balcony_rule([0.0], era_for_year(year)).min_height)
    for level in balconies:
        if level < threshold - 1e-9:
            raise BlockDatumViolation(
                f"block balcony datum at {level:.3f} m is below the {threshold:.2f} m the "
                f"ordinance allows ({_REGLEMENT_CITATIONS['1823']}); a block datum may not "
                "be less legal than the buildings hung on it"
            )
    for level in (*string_courses, *balconies):
        if level > ceiling + 1e-9:
            raise BlockDatumViolation(
                f"block datum at {level:.3f} m stands above the {ceiling:.2f} m legal "
                f"cornice ceiling for a {street_width:.2f} m street"
            )

    return BlockDatums(
        street_width=float(street_width),
        cornice_height=ceiling,
        string_course_levels=string_courses,
        balcony_levels=balconies,
    )


@lru_cache(maxsize=512)
def _reference_lines(
    street_width: float, year: int, klass: BuildingClass, regime: GroundRegime
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """The reference elevation's horizontal lines: (string courses, balconies).

    Cached because it is a pure function of its four block facts and because
    every block on the same street in the same year wants the same answer.
    """
    ceiling = get_reglement(era_for_year(year)).facade_height_limit(street_width)
    provisional = BlockDatums(
        street_width=street_width,
        cornice_height=ceiling,
        string_course_levels=(),
        balcony_levels=(),
    )
    site = SiteContext(
        street_width=street_width,
        parcel_width=_REFERENCE_PARCEL_WIDTH,
        parcel_depth=_REFERENCE_PARCEL_DEPTH,
        year=year,
        klass=klass,
        ground=regime.programmes[0],
        corner=False,
        seed=0,
    )
    reference, _ = generate(site, provisional)
    return _lines_of(reference)


def _lines_of(building: Node) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Read a finished building's shared horizontals back out of its IR.

    String courses and *continuous* balconies only. An individual balconette
    belongs to one bay of one building and does not cross a party wall, so it
    is not a block fact and is deliberately not collected.
    """
    string_courses: set[float] = set()
    balconies: set[float] = set()
    for node in walk(building):
        if node.kind == "string_course":
            string_courses.add(float(node.props["y"]))
        elif node.kind == "balcony" and bool(node.props.get("continuous")):
            balconies.add(float(node.props["y"]))
    return tuple(sorted(string_courses)), tuple(sorted(balconies))


def _cornice_lines_of(building: Node) -> tuple[float, ...]:
    return tuple(
        sorted({float(n.props["y"]) for n in walk(building) if n.kind == "cornice"})
    )


def _street_widths_of(building: Node) -> tuple[float, ...]:
    """Every street width this building's own trace admits to having used.

    Read out of the IR rather than out of the ``SiteContext`` on purpose: the
    question the previous attempt got wrong is not "what were we going to tell
    it" but "what did it actually believe". A trace entry recording
    ``street_width`` is that building's own testimony.
    """
    seen: set[float] = set()
    for node in walk(building):
        for entry in node.trace:
            value = entry.inputs.get("street_width")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                seen.add(float(value))
    return tuple(sorted(seen))


# ---------------------------------------------------------------------------
# The audit at the seam
# ---------------------------------------------------------------------------


def check_alignment(
    buildings: Sequence[Node],
    datums: BlockDatums,
    *,
    tol: float = DATUM_TOLERANCE,
) -> None:
    """Refuse a block whose buildings disagree about a block fact.

    This is the module's reason for existing, so it is worth being blunt about
    what it does. It does not trust that the datums were handed down; it
    re-reads, from the finished IR and the traces on it, four things:

    * what street width every building believed it stood on,
    * where every building stopped its stone face and put its cornice,
    * where its string courses run,
    * where its balcons filants run,

    and it raises ``BlockDatumViolation`` if any of them differs between two
    buildings, or from the datums the block resolved, by more than ``tol``.

    The circulaire du 21 septembre 1855 is the authority: within a block,
    balcony, cornice and entablature lines must align from building to
    building. A block that fails this test is not a stylistic near-miss; it is
    a block that would have been refused permission.
    """
    if not buildings:
        raise ValueError("check_alignment needs at least one building")

    # -- 1. one street width for the whole block --------------------------
    widths: dict[float, list[str]] = {}
    for building in buildings:
        for width in _street_widths_of(building):
            widths.setdefault(width, []).append(building.id)
    if not widths:
        raise BlockDatumViolation(
            "no building on this block recorded the street width it used; the fact "
            "that must be shared cannot be checked, which is the same failure by a "
            "quieter route"
        )
    distinct = sorted(widths)
    if len(distinct) > 1 or abs(distinct[0] - datums.street_width) > tol:
        report = "; ".join(f"{w:.6f} m in {sorted(set(ids))}" for w, ids in sorted(widths.items()))
        raise BlockDatumViolation(
            "buildings on one block disagree about how wide the street is — "
            f"{report}. The block resolved {datums.street_width:.6f} m and handed it "
            "down; a building that used anything else sampled a block-level fact "
            "instead of receiving it (I2). This is the previous attempt's failure, "
            "and it errors now."
        )

    # -- 2. the cornice line continues ------------------------------------
    _same_across(
        buildings,
        lambda b: (round(float(b.props["eaves_height"]), 12),),
        tol,
        "eaves line",
        f"{CIRCULAIRE_1855} — the cornice continues its neighbour's cornice",
    )
    _same_across(
        buildings,
        _cornice_lines_of,
        tol,
        "cornice line",
        f"{CIRCULAIRE_1855} — the cornice continues its neighbour's cornice",
    )
    for building in buildings:
        ceiling = float(building.props["legal_cornice_ceiling"])
        if abs(ceiling - datums.cornice_height) > tol:
            raise BlockDatumViolation(
                f"building {building.id!r} was built against a {ceiling:.6f} m legal "
                f"cornice ceiling; the block handed down {datums.cornice_height:.6f} m"
            )

    # -- 3. the string courses and balcony lines run across ----------------
    for building in buildings:
        string_courses, balconies = _lines_of(building)
        _matches(
            building.id,
            "string course",
            string_courses,
            datums.string_course_levels,
            tol,
        )
        _matches(building.id, "balcon filant", balconies, datums.balcony_levels, tol)


def _same_across(
    buildings: Sequence[Node],
    read,
    tol: float,
    what: str,
    authority: str,
) -> None:
    reference = read(buildings[0])
    for building in buildings[1:]:
        other = read(building)
        if len(other) != len(reference) or any(
            abs(a - b) > tol for a, b in zip(reference, other)
        ):
            raise BlockDatumViolation(
                f"{what} does not continue across the party wall: "
                f"{buildings[0].id!r} has {reference!r}, {building.id!r} has {other!r} "
                f"({authority})"
            )


def _matches(
    node_id: str,
    what: str,
    got: tuple[float, ...],
    expected: tuple[float, ...],
    tol: float,
) -> None:
    if len(got) != len(expected) or any(abs(a - b) > tol for a, b in zip(got, expected)):
        raise BlockDatumViolation(
            f"building {node_id!r} runs its {what} lines at {got!r}; the block's datum "
            f"is {expected!r} ({CIRCULAIRE_1855}). A line that stops at the party wall "
            "is the failure this whole level exists to prevent."
        )


# ---------------------------------------------------------------------------
# plan_block — subdivision, corners and datums, in one place
# ---------------------------------------------------------------------------


def plan_block(
    frontage: float,
    street_width: float,
    year: int,
    *,
    klass: BuildingClass = BuildingClass.ORDINARY,
    regime: GroundRegime = GroundRegime.COMMERCIAL,
    seed: int = 0,
    corner_left: bool = False,
    corner_right: bool = False,
    path: str = "block/frontage",
    rng: DecisionStream | None = None,
    **subdivision,
) -> Block:
    """Lay out a run of frontage and resolve everything it shares.

    Assembling a ``Block`` by hand means getting adjacency, chamfer bookkeeping
    and the datums all consistent at once, and the point of this level is to
    make the wrong thing hard. This does the three in the only order that is
    sound: subdivide the ground, cut the corners out of the corner lots, then
    resolve the datums from block facts alone.

    Note the order matters in one direction only. The datums do not depend on
    the subdivision — they are a function of ``(street_width, year, klass,
    regime)`` — which is what lets them be resolved before any building exists
    and handed down rather than negotiated.
    """
    stream = rng if rng is not None else DecisionStream(seed)
    parcels = list(
        subdivide(
            frontage,
            stream,
            path=path,
            corner_left=corner_left,
            corner_right=corner_right,
            **subdivision,
        )
    )

    chamfers: list[Chamfer] = []
    for side, index in (("left", 0), ("right", len(parcels) - 1)):
        wanted = corner_left if side == "left" else corner_right
        if not wanted or not parcels[index].corner:
            continue
        chamfer = chamfer_for(index, side, stream, path=path)
        remaining = parcels[index].width - chamfer.width
        if remaining < _MIN_PARCEL_WIDTH:
            # The lot is too narrow to give up a pan coupé and still be a
            # facade. Refusing to cut is the honest answer; silently producing
            # a two-metre frontage would not be.
            continue
        parcels[index] = dataclasses.replace(parcels[index], width=remaining)
        chamfers.append(chamfer)

    datums = resolve_datums(street_width, year, klass, regime)
    return Block(
        street_width=float(street_width),
        parcels=tuple(parcels),
        datums=datums,
        chamfers=tuple(chamfers),
    )


# ---------------------------------------------------------------------------
# solve_block — hand the datums down, assemble, audit
# ---------------------------------------------------------------------------


def solve_block(
    block: Block,
    year: int,
    *,
    klass: BuildingClass = BuildingClass.ORDINARY,
    regime: GroundRegime = GroundRegime.COMMERCIAL,
    seed: int = 0,
    grounds: Sequence[GroundProgramme] | None = None,
    path: str = "block",
    layers: Sequence[Layer] | None = None,
) -> tuple[Node, ...]:
    """Generate the whole run, and refuse it if it does not read as one wall.

    The shape of the function is the shape of the invariant:

    1. **Check the block agrees with itself.** ``block.datums`` was resolved for
       some ``(year, klass, regime)``; recompute them from the arguments given
       and raise if they differ. Two modules relying on the same unstated
       invariant is how a roof comes to run past the middle of a parcel (A2.6),
       and the same hazard applies to a datum bundle arriving from elsewhere.
    2. **Choose the parcel programmes.** Within one regime, and only within
       one: a mixed regime moves the registration and is refused by name.
    3. **Hand the datums down and generate.** Each building gets a
       ``SiteContext`` built from block facts plus its own lot. It receives the
       street width; it never chooses it (I2).
    4. **Audit the seam.** ``check_alignment`` re-reads what was actually built.
    5. **Emit the block's own objects.** Party walls, chamfers, and the datum
       lines themselves — the cornice, the bandeaux and the balcons filants
       that run the length of the frontage. Those are block-scope nodes because
       they are block-scope *things*: a balcon filant that stops at the party
       wall is not a balcon filant.

    Returns the run's top-level nodes, left to right: a ``chamfer`` where the
    angle is cut, a ``parcel`` wrapping each building, a ``party_wall`` at each
    junction, and finally the block's datum lines. Buildings stay in
    parcel-local coordinates per the IR convention; the ``parcel`` node carries
    the offset along the frontage. Node ids are prefixed per parcel so the whole
    block is addressable from a single tree.
    """
    stream = DecisionStream(seed)

    # -- 1. the block must agree with itself ------------------------------
    expected = resolve_datums(block.street_width, year, klass, regime)
    if expected != block.datums:
        raise BlockDatumViolation(
            "the datums on this block were not resolved for the situation it is being "
            f"solved in: solving for year={year}, klass={klass.value}, "
            f"regime={regime.value} gives {expected!r}, but the block carries "
            f"{block.datums!r}. A handed-down bundle that no longer matches its "
            "situation is a block fact resolved twice, which is the failure this "
            "level exists to prevent."
        )

    # -- 2. programmes, within one regime ---------------------------------
    if grounds is None:
        programmes = tuple(
            stream.choice(
                f"{path}/parcel/{i}/programme", regime.programmes, regime.weights
            )
            for i in range(len(block.parcels))
        )
    else:
        programmes = tuple(grounds)
        if len(programmes) != len(block.parcels):
            raise ValueError(
                f"{len(programmes)} ground programmes for {len(block.parcels)} parcels"
            )
        stray = {g for g in programmes if GroundRegime.of(g) is not regime}
        if stray:
            names = ", ".join(sorted(g.value for g in stray))
            raise BlockDatumViolation(
                f"a {regime.value} block was handed the ground programme(s) {names}, "
                f"which belong to another regime. The ground regime sets the ground "
                "storey height and the entresol, so mixing regimes moves the bandeau "
                "and the balcon filant out of register by the better part of a metre "
                f"— exactly what {CIRCULAIRE_1855} forbids. Split the run into two "
                "blocks, or choose one regime for it."
            )

    # -- 3. hand the datums down ------------------------------------------
    buildings: list[Node] = []
    parcel_nodes: list[Node] = []
    origins = block.origins
    for i, parcel in enumerate(block.parcels):
        site = SiteContext(
            # Received, not chosen. The building is told the street width; it
            # has no RNG and no way to have an opinion about it (I2).
            street_width=block.datums.street_width,
            parcel_width=parcel.width,
            parcel_depth=parcel.depth,
            year=year,
            klass=klass,
            ground=programmes[i],
            corner=parcel.corner,
            seed=seed * 1_000_003 + i,
        )
        building, _log = generate(site, block.datums, layers=layers)
        building = _reparent(building, f"{path}/p{i}")
        buildings.append(building)
        parcel_nodes.append(
            Node(
                id=f"{path}/p{i}",
                kind="parcel",
                trace=(
                    TraceEntry(
                        rule="paris.block.parcel.placed_on_the_run",
                        phase="block",
                        detail=(
                            f"lot {i} of {len(block.parcels)}: {parcel.width:.2f} m of "
                            f"frontage at x={origins[i]:.2f} m along the run, "
                            f"{parcel.depth:.2f} m deep, "
                            + (
                                "abutting "
                                + " and ".join(
                                    f"lot {n}"
                                    for n in (parcel.left_neighbour, parcel.right_neighbour)
                                    if n is not None
                                )
                                if not parcel.detached
                                else "abutting nothing — a single-lot run"
                            )
                            + ". Frontage subdivision and adjacency are the block's under "
                            "every relation; the building receives its lot."
                        ),
                        inputs={
                            "index": i,
                            "x": round(origins[i], 6),
                            "width": round(parcel.width, 6),
                            "depth": round(parcel.depth, 6),
                            "corner": parcel.corner,
                            "left_neighbour": parcel.left_neighbour,
                            "right_neighbour": parcel.right_neighbour,
                            "street_width": block.datums.street_width,
                            "ground": programmes[i].value,
                            "klass": klass.value,
                        },
                    ),
                ),
                children=(building,),
                props={
                    "x": origins[i],
                    "y": 0.0,
                    "w": parcel.width,
                    "h": float(building.props["h"]),
                    "index": i,
                    "corner": parcel.corner,
                    "depth": parcel.depth,
                    "street_width": block.datums.street_width,
                    "ground": programmes[i].value,
                    "klass": klass.value,
                    "left_neighbour": parcel.left_neighbour,
                    "right_neighbour": parcel.right_neighbour,
                },
            )
        )

    # -- 4. audit the seam -------------------------------------------------
    check_alignment(buildings, block.datums)

    # -- 5. the block's own objects ---------------------------------------
    eaves = float(buildings[0].props["eaves_height"])
    nodes: list[Node] = []
    left = block.chamfer_at("left")
    if left is not None:
        nodes.append(_chamfer_node(block, left, eaves, path, buildings[left.parcel], klass))
    nodes.extend(parcel_nodes)
    right = block.chamfer_at("right")
    if right is not None:
        nodes.append(_chamfer_node(block, right, eaves, path, buildings[right.parcel], klass))
    nodes.extend(_party_wall_nodes(block, eaves, path))
    nodes.extend(_datum_nodes(block, eaves, path))
    return tuple(nodes)


def _reparent(node: Node, prefix: str) -> Node:
    """Re-key a finished subtree under a block-unique prefix.

    ``generate`` names its root ``b`` and every element below it relative to
    that, which is right for one building and ambiguous for eight of them on
    one street. Ids are how an element is pointed at — "read off a render and
    typed back in" — so the block namespaces them rather than letting the run
    contain eight nodes called ``b/s2/x3/balcony``. Nothing else is touched.
    """
    return dataclasses.replace(
        node,
        id=f"{prefix}/{node.id}",
        children=tuple(_reparent(child, prefix) for child in node.children),
    )


def _party_wall_nodes(block: Block, eaves: float, path: str) -> tuple[Node, ...]:
    """One node per junction — shared, so emitted once, by the block.

    A party wall belongs to neither of the buildings that lean on it. Emitting
    it from either side would make it two walls that happen to coincide, and
    two things that happen to coincide are two things that can stop coinciding.
    """
    out: list[Node] = []
    for left, right, x in block.junctions():
        out.append(
            Node(
                id=f"{path}/party_wall/{left}_{right}",
                kind="party_wall",
                trace=(
                    TraceEntry(
                        rule="paris.block.party_wall.shared",
                        phase="block",
                        detail=(
                            f"lots {left} and {right} share one wall at x={x:.2f} m, "
                            f"{_PARTY_WALL_THICKNESS:.2f} m thick (INFERRED), astride the "
                            "boundary. Emitted once by the block because it is one wall, "
                            "not two that agree."
                        ),
                        inputs={"left": left, "right": right, "x": round(x, 6)},
                    ),
                ),
                props={
                    "x": x - _PARTY_WALL_THICKNESS / 2.0,
                    "y": 0.0,
                    "w": _PARTY_WALL_THICKNESS,
                    "h": eaves,
                    "left_parcel": left,
                    "right_parcel": right,
                },
            )
        )
    return tuple(out)


def _chamfer_storeys(
    chamfer: Chamfer, building: Node, path: str, klass: BuildingClass
) -> tuple[Node, ...]:
    """The pan coupé's storeys, bay by bay, opening by opening.

    A4.5's own words are *"a corner is a third short facade with its own
    rhythm"*, and until now only the first half of that was true: the chamfer
    had a rhythm and nothing in it, so every pan coupé in a block rendered as
    a blank unpierced wall between two pierced ones — which reads worse than
    no chamfer at all.

    **Its own rhythm, the same grammar.** The rhythm is the chamfer's:
    ``_CHAMFER_BAY``, narrower than the facade's, solved as its own budget.
    What is *put in* that rhythm is the corner building's own resolved
    facade — the same storey levels, the same opening type, the same head,
    the same sill, the same light height, the same devanture. That is not a
    shortcut around qualification; it is the architectural claim. The cut
    face is a face of one building, not a third building squeezed into the
    angle, so its second floor is that building's second floor and its
    windows are that building's windows. Nothing is decided here that the
    building has not already decided; the only arithmetic is re-centring the
    light in a narrower slot, and narrowing it where the slot cannot carry
    the facade's light with ``pier_filler``'s minimum trumeau either side.

    Storeys standing inside the comble are skipped: the chamfer's own bays
    stop at the eaves, so a storey with no stone facade has nothing to carve
    a narrower rhythm into. What stands above the eaves is the same comble
    the corner building already carries — not a second set of storeys, but a
    roof (``_chamfer_roof``, A6.3): the mass, not more windows in it.
    """
    pier_min = float(catalogue.pier_filler().to_slot_spec(klass).minimum)
    out: list[Node] = []
    for storey in building.children:
        if storey.kind != "storey" or storey.props.get("on_the_stone_facade") is False:
            continue
        model = _representative_bay(storey)
        if model is None:
            continue
        opening_props, shopfront_props = model
        sy, sh = float(storey.props["y"]), float(storey.props["h"])
        sid = f"{path}/s{storey.props['index_from_bottom']}"
        storey_children: list[Node] = []
        socle = next((c for c in storey.children if c.kind == "socle"), None)
        if socle is not None:
            # The bossage turns the corner, for the same reason the cornice
            # does: it is a course of the same wall. A pan coupé whose ground
            # floor stops being rusticated where the facade's starts is a
            # seam, and the seam is the one thing a block may not have.
            storey_children.append(
                Node(
                    id=f"{sid}/socle",
                    kind="socle",
                    trace=(
                        TraceEntry(
                            rule="paris.block.chamfer.the_socle_turns_the_corner",
                            phase="block",
                            detail=(
                                "the corner building's own ground-floor treatment, run "
                                "across the cut face: one course of one wall, not two "
                                "walls that happen to agree."
                            ),
                            inputs={"treatment": socle.props.get("treatment")},
                        ),
                    ),
                    props={
                        **dict(socle.props),
                        "x": 0.0,
                        "y": sy,
                        "w": chamfer.width,
                        "h": sh,
                        # A7.2. The treatment turns the corner; the COUNT
                        # cannot, because it was counted across the facade's
                        # width and this face is narrower. Same course module
                        # — that is what makes it one wall — re-counted over
                        # the frontage this node actually states, so the
                        # stones are the same size on both faces instead of
                        # the same number of them squeezed into a shorter run.
                        "course_columns": _recount(
                            socle.props.get("course_columns"),
                            float(socle.props.get("w") or 0.0),
                            chamfer.width,
                        ),
                    },
                )
            )
        bays: list[Node] = []
        for i, slot in enumerate(chamfer.bays):
            bid = f"{sid}/x{i}"
            pierced: list[Node] = []
            light = _refit_light(opening_props, slot, pier_min)
            if slot.name == "bay" and light is not None:
                pierced.append(
                    OpeningNode(
                        id=f"{bid}/opening",
                        kind="opening",
                        trace=_CHAMFER_OPENING_TRACE,
                        # ``y`` is untouched: the model comes from this very
                        # storey, so the sill it stands on is already the
                        # right height above this floor.
                        props=light,
                    )
                )
                if shopfront_props is not None:
                    pierced.append(
                        ShopfrontNode(
                            id=f"{bid}/shopfront",
                            kind="shopfront",
                            trace=_CHAMFER_OPENING_TRACE,
                            props={
                                **dict(shopfront_props),
                                "x": light["x"],
                                "y": sy,
                                "w": light["w"],
                                "h": sh,
                            },
                        )
                    )
            bays.append(
                BayNode(
                    id=bid,
                    kind="bay",
                    trace=(
                        TraceEntry(
                            rule="paris.block.chamfer.own_rhythm",
                            phase="block",
                            detail=(
                                f"bay {i} of the pan coupé: {slot.width:.2f} m from the "
                                f"chamfer's own band [{_CHAMFER_BAY[0]:.2f}, "
                                f"{_CHAMFER_BAY[1]:.2f}, {_CHAMFER_BAY[2]:.2f}] m "
                                "(INFERRED), not the facade's"
                            ),
                            inputs={
                                "index": i,
                                "width": round(slot.width, 6),
                                "kind": slot.kind.value,
                            },
                        ),
                    ),
                    children=tuple(pierced),
                    props={
                        "x": slot.start,
                        "y": sy,
                        "w": slot.width,
                        "h": sh,
                        # A4.7: `slot_name`, the name every building bay
                        # already uses. A chamfer bay is still a bay, and a
                        # consumer keying on `slot_name` used to read None on
                        # one — silently, because a missing key and "no
                        # opinion" look identical.
                        "slot_name": slot.name,
                    },
                )
            )
        out.append(
            StoreyNode(
                id=sid,
                kind="storey",
                trace=(
                    TraceEntry(
                        rule="paris.block.chamfer.same_storeys_as_the_facade_it_turns_from",
                        phase="block",
                        detail=(
                            f"storey at {sy:.3f} m, {sh:.3f} m high — the corner "
                            "building's own storey, carried onto the cut face. The pan "
                            "coupé is a face of that building, so its floors are that "
                            "building's floors; only the horizontal rhythm is its own."
                        ),
                        inputs={
                            "y": round(sy, 6),
                            "h": round(sh, 6),
                            "storey": storey.id,
                            "role": storey.props.get("role"),
                        },
                    ),
                ),
                children=(*storey_children, *bays),
                props={
                    "x": 0.0,
                    "y": sy,
                    "w": chamfer.width,
                    "h": sh,
                    "role": storey.props.get("role"),
                    "rank_from_principal": storey.props.get("rank_from_principal"),
                    "index_from_bottom": storey.props.get("index_from_bottom"),
                    "within_comble": False,
                    "on_the_stone_facade": True,
                },
            )
        )
    return tuple(out)


_CHAMFER_OPENING_TRACE = (
    TraceEntry(
        rule="paris.block.chamfer.same_openings_as_the_facade_it_turns_from",
        phase="block",
        detail=(
            "the corner building's own opening for this storey — its type, head, "
            "sill and light height unchanged — re-centred in the chamfer's own, "
            "narrower bay, and narrowed only where that bay cannot carry the "
            "facade's light with a minimum trumeau either side. A cut face is a "
            "face of one building: its windows are that building's windows."
        ),
        inputs={},
    ),
)


def _recount(count: object, over: float, across: float, *, minimum: int = 1) -> int:
    """A stated repeat count, re-read over a different length at the same module.

    A7.2 put ornament counts in the IR, which is what stops a consumer
    dividing a width by a spacing of its own. The pan coupé is the one place
    a node's geometry is deliberately restated at another width, so the count
    that came with it has to be restated too — at the SAME module, which is
    the whole point: the stones are the same size on both faces of the
    corner, and there are fewer of them on the shorter one.
    """
    n = int(count or 0)
    if n <= 0 or over <= 0.0:
        return minimum
    return max(minimum, int(round(across * n / over)))


def _representative_bay(
    storey: Node,
) -> tuple[Mapping[str, object], Mapping[str, object] | None] | None:
    """The opening (and devanture, if there is one) this storey repeats.

    An ordinary bay, never a pier, a special or the porte cochère: those are
    answers to something about the *facade's* budget — a gap the rhythm could
    not absorb, an entrance that had to go somewhere — and the chamfer's
    budget is a different one, solved separately. What repeats across a Paris
    storey is its bay, and that is what turns the corner.
    """
    for bay in storey.children:
        if bay.kind != "bay" or bay.props.get("slot_name") != "bay":
            continue
        opening = next((c for c in bay.children if c.kind == "opening"), None)
        if opening is None or opening.props.get("opening_type") in (None, "none"):
            continue
        shop = next((c for c in bay.children if c.kind == "shopfront"), None)
        return opening.props, (shop.props if shop is not None else None)
    return None


def _refit_light(
    opening_props: Mapping[str, object], slot: PlacedSlot, pier_min: float
) -> dict[str, object] | None:
    """The facade's light, centred in one chamfer bay.

    The light keeps its stated height, sill, type and head; only its width
    can move, and only downwards, and only because the chamfer's bay is
    narrower than the facade's. The pier either side is what is left, and it
    is never allowed below ``pier_filler``'s minimum — the same masonry rule
    that governs the facade this turns off, applied to a shorter budget.
    """
    room = slot.width - 2.0 * pier_min
    width = min(float(opening_props["w"]), room)
    if width < float(catalogue.minimum_light_width()):
        return None
    offset = (slot.width - width) / 2.0
    return {
        **dict(opening_props),
        "x": slot.start + offset,
        "w": width,
        "pier_width": offset,
        "slot_x": slot.start,
        "slot_w": slot.width,
    }


def _chamfer_roof(chamfer: Chamfer, path: str, building: Node) -> tuple[Node, ...]:
    """The pan coupé's own comble (A6.3): the corner building's roof, read at
    the chamfer's own width instead of the facade's.

    Not a second roof invented for a third facade — the corner building's
    roof and silhouette, already qualified and already inscribed in its own
    envelope, read straight off ``building.children`` the way
    ``_chamfer_storeys`` already reads its storeys and its openings. Nothing
    about the envelope is re-derived: the eaves, the ridge height, the depth
    profile, the material and the dormer-or-not choice are the building's
    own. A corner is not a second building, so it does not get a second roof
    — it gets the same one, read at its own (narrower) width, which is
    exactly the architectural point a real *pan coupé*'s often-domed cap
    makes: the strongest roof feature on the block, standing over the one
    facade the whole run is named for.

    ``ends`` is forced to ``"hipped"`` rather than copied, though on every
    block this module can build today it already reads that way: a chamfer
    only ever cuts a parcel ``Block`` has itself required to be marked
    ``corner`` (``Block.__post_init__``), and ``site.corner`` is exactly what
    decides a building's own roof ``ends``. The pan coupé is a return on both
    of its sides, never a run continuing into a party wall, so this states
    that directly instead of leaning on an invariant enforced three modules
    away.

    ``()`` where the corner building carries no roof or no silhouette at all
    (a hand-built layer set that omits termination) — a pan coupé standing in
    for a roof nobody built would be inventing one, not turning a corner.

    **A10.4.** ``seam_count`` was already re-counted for the chamfer's own
    (narrower) width, but ``hip_arris`` was still copied verbatim from the
    parent building's props — a run derived from the WIDE facade, stated on a
    roof node now half as wide. Past that node's own mid-span the two hip
    lines (one carried in from each end) had already crossed, drawing a
    bowtie in the sky. ``hip_arris`` is structural, not decorative, exactly
    like ``seam_count``, so it gets the same treatment: re-derived at
    ``chamfer.width`` by calling ``terminate.derive_hip_arris`` again — the
    one function A9.3 made the sole source of this geometry — rather than
    trusted from a copy computed for a different width.
    """
    roof = next((c for c in building.children if c.kind == "roof"), None)
    silhouette = next((c for c in building.children if c.kind == "silhouette"), None)
    if roof is None or silhouette is None:
        return ()
    trace = (
        TraceEntry(
            rule="paris.block.chamfer.roof_turns_the_corner",
            phase="block",
            detail=(
                "the pan coupé's comble is the corner building's own comble, read at "
                f"{chamfer.width:.2f} m of frontage instead of the facade's — same eaves, "
                "same ridge, same envelope, same material, same dormer repertoire. A "
                "corner is not a second building and does not get a second roof; it is "
                "the one place a Paris roof is most visible, and blank sky over the cut "
                "face was the defect (A6.3). Closes hipped at both ends: a pan coupé is "
                "a return on either side, never a run into a party wall."
            ),
            inputs={
                "parcel": chamfer.parcel,
                "side": chamfer.side,
                "chamfer_width": round(chamfer.width, 6),
                "facade_width": round(float(roof.props.get("w", 0.0)), 6),
                "source_roof": roof.id,
                "source_silhouette": silhouette.id,
            },
        ),
    )
    roof_node = Node(
        id=f"{path}/roof",
        kind="roof",
        trace=trace,
        props={
            **dict(roof.props),
            "x": 0.0,
            "w": chamfer.width,
            "ends": "hipped",
            # A7.2: the seams are the covering's own fold and keep their
            # interval; how many of them cross this face is a fact about this
            # face's width, so it is re-counted rather than carried over.
            "seam_count": catalogue.repeats_across(
                chamfer.width,
                float(catalogue.roof_seam_module(roof.props.get("material"))),
                minimum=4,
            ),
            # A10.4: the hip arris is a structural fact about THIS width, the
            # same way the seam count above is — `terminate.derive_hip_arris`
            # is the one function A9.3 made the sole source of this geometry,
            # so it is called again here at `chamfer.width` rather than
            # trusting the copy `**dict(roof.props)` just brought in, which
            # was derived for the parent building's (wider) facade and
            # crosses itself once drawn on a face this much narrower. The
            # depth `profile` itself is not width-derived (a section into the
            # parcel, not across the frontage) and is carried over unchanged.
            "hip_arris": derive_hip_arris(chamfer.width, roof.props.get("profile") or ()),
        },
    )
    silhouette_node = Node(
        id=f"{path}/silhouette",
        kind="silhouette",
        trace=trace,
        props={**dict(silhouette.props), "x": 0.0, "facade_width": chamfer.width, "ends": "hipped"},
    )
    return (roof_node, silhouette_node)


def _chamfer_node(
    block: Block,
    chamfer: Chamfer,
    eaves: float,
    path: str,
    building: Node,
    klass: BuildingClass,
) -> Node:
    """The pan coupé as IR: its own facade, its own bays, its own roof, the
    block's datums.

    Its children are its own storeys — the corner building's floors carried
    round onto the cut face, each divided by the chamfer's own bay rhythm and
    pierced by the same openings the facade repeats (``_chamfer_storeys``) —
    its own roof and silhouette, the corner building's comble read at this
    face's own width (``_chamfer_roof``, A6.3) — and the datum lines carried
    around the corner. The datum half is the architectural point below the
    eaves: what makes a chamfer read as part of the block rather than as a
    gap between two blocks is that the cornice and the bandeaux run across it
    at exactly the heights they run at on both neighbours. Above the eaves
    the same point is the roof's: the corner is the one place a Paris roof is
    most visible, so bare sky there is the one thing a chamfer may not have
    either.
    """
    x0 = block.chamfer_origin(chamfer)
    trace = (
        TraceEntry(
            rule="paris.block.chamfer.pan_coupe",
            phase="block",
            detail=(
                "a corner is not a module type. Where the angle is cut, the cut face is a "
                "third short facade with a rhythm of its own — the join between two "
                "grammars — and it is solved as its own budget, not as a bay of either "
                "neighbour.\n" + "\n".join(f"  · {line}" for line in chamfer.account)
            ),
            inputs={
                "parcel": chamfer.parcel,
                "side": chamfer.side,
                "width": round(chamfer.width, 6),
                "bays": tuple(round(s.width, 6) for s in chamfer.bays),
                "x": round(x0, 6),
            },
        ),
    )
    storeys = _chamfer_storeys(
        chamfer, building, f"{path}/chamfer/{chamfer.side}", klass
    )
    roofscape = _chamfer_roof(chamfer, f"{path}/chamfer/{chamfer.side}", building)
    lines = _datum_nodes(
        block,
        eaves,
        f"{path}/chamfer/{chamfer.side}",
        x0=0.0,
        width=chamfer.width,
        note="carried around the corner: the cornice of one street is the cornice of the other",
    )
    return Node(
        id=f"{path}/chamfer/{chamfer.side}",
        kind="chamfer",
        trace=trace,
        children=(*storeys, *roofscape, *lines),
        props={
            "x": x0,
            "y": 0.0,
            "w": chamfer.width,
            "h": eaves,
            "side": chamfer.side,
            "parcel": chamfer.parcel,
            "bay_count": len(chamfer.bays),
        },
    )


def _datum_nodes(
    block: Block,
    eaves: float,
    path: str,
    *,
    x0: float = 0.0,
    width: float | None = None,
    note: str = "",
) -> tuple[Node, ...]:
    """The shared horizontals, as block-scope elements spanning the frontage.

    Each building already emits its own share of these lines at its own scale,
    and ``check_alignment`` has just proved every one of them coincides. These
    nodes are the *datum* — the single line the buildings are shares of — and
    they exist so that "the cornice continues its neighbour's cornice" is a
    thing in the IR rather than a coincidence a reader has to verify by
    measuring eight separate nodes.
    """
    span = block.frontage if width is None else width
    tail = f" {note}." if note else ""
    out: list[Node] = []

    for i, level in enumerate(block.datums.string_course_levels):
        out.append(
            StringCourseNode(
                id=f"{path}/datum/string_course/{i}",
                kind="string_course",
                trace=(
                    TraceEntry(
                        rule="paris.block.datum.string_course.circulaire_1855",
                        phase="block",
                        detail=(
                            f"a bandeau at {level:.2f} m above the pavement, running the whole "
                            f"{span:.2f} m of frontage. Within a block, entablature lines must "
                            f"align from building to building ({CIRCULAIRE_1855}).{tail}"
                        ),
                        inputs={
                            "level": round(level, 6),
                            "span": round(span, 6),
                            "street_width": block.datums.street_width,
                        },
                    ),
                ),
                props={"x": x0, "y": level, "w": span, "h": 0.0, "datum": True, "scope": "block"},
            )
        )

    for i, level in enumerate(block.datums.balcony_levels):
        out.append(
            BalconyNode(
                id=f"{path}/datum/balcony/{i}",
                kind="balcony",
                trace=(
                    TraceEntry(
                        rule="paris.block.datum.balcony.circulaire_1855",
                        phase="block",
                        detail=(
                            f"a balcon filant at {level:.2f} m above the pavement, running the "
                            f"whole {span:.2f} m of frontage. Within a block, balcony lines "
                            f"must align from building to building ({CIRCULAIRE_1855}).{tail}"
                        ),
                        inputs={
                            "level": round(level, 6),
                            "span": round(span, 6),
                            "street_width": block.datums.street_width,
                        },
                    ),
                ),
                props={
                    "x": x0,
                    "y": level,
                    "w": span,
                    "h": 0.0,
                    "continuous": True,
                    "datum": True,
                    "scope": "block",
                    # A7.2, same reasoning as the cornice datum below: the
                    # consoles under a shared slab run at the module, and the
                    # count over this span is stated rather than divided out
                    # downstream.
                    "bracket_count": catalogue.repeats_across(
                        span, float(catalogue.balcony_bracket_module()), minimum=2
                    ),
                },
            )
        )

    out.append(
        CorniceNode(
            id=f"{path}/datum/cornice",
            kind="cornice",
            trace=(
                TraceEntry(
                    rule="paris.block.datum.cornice.circulaire_1855",
                    phase="block",
                    detail=(
                        f"the cornice line at {eaves:.2f} m, running the whole {span:.2f} m of "
                        f"frontage, under a {block.datums.cornice_height:.2f} m legal ceiling "
                        f"for a {block.datums.street_width:.2f} m street. Within a block, "
                        f"cornice lines must align from building to building "
                        f"({CIRCULAIRE_1855}).{tail}"
                    ),
                    inputs={
                        "level": round(eaves, 6),
                        "legal_cornice_ceiling": block.datums.cornice_height,
                        "span": round(span, 6),
                        "street_width": block.datums.street_width,
                    },
                ),
            ),
            props={
                "x": x0,
                "y": eaves,
                "w": span,
                "h": 0.0,
                "datum": True,
                "scope": "block",
                "legal_cornice_ceiling": block.datums.cornice_height,
                # A7.2. A datum is a line the whole block is a share of, so
                # the dentil rhythm running along it belongs to no single
                # building's ambition and runs at the catalogue's own module.
                # Stated here because a consumer that had to divide the block
                # frontage by a spacing of its own is exactly the decision
                # ``check_renderer_dumb`` forbids.
                "ornament_count": catalogue.repeats_across(
                    span, float(catalogue.dentil_module()), minimum=2
                ),
            },
        )
    )
    return tuple(out)


def block_nodes(nodes: Sequence[Node]) -> Iterator[Node]:
    """Every node of a solved block, depth-first — the block's ``walk``."""
    for node in nodes:
        yield from walk(node)
