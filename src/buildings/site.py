"""The situation a building answers to.

`SiteContext` is the whole of what a building is told about the world it sits
in. It is deliberately inert: no RNG, no method that samples, no way to derive
a fact the block should have handed down. `street_width` in particular is
*received*, never chosen — a building that rolled its own street width would
violate I2 (a building never samples a block-level fact) even if the roll were
seeded identically every time. If a fact belongs to the block, the block
computes it and puts it on this dataclass; this module only carries it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BuildingClass(Enum):
    """How much money was behind the building. Drives PROPORTIONAL scaling
    only (see `quantity.scale_for_class`) — never ABSOLUTE or REGULATORY
    quantities, which is the whole point of the three-kind split."""

    MODEST = "modest"
    ORDINARY = "ordinary"
    COMFORTABLE = "comfortable"
    GRAND = "grand"


class GroundProgramme(Enum):
    """What the ground floor is for. Affects the base module (shopfront vs.
    carriage door vs. plain residential entrance) without touching anything
    above it."""

    RESIDENTIAL = "residential"
    SHOP = "shop"
    CAFE = "cafe"
    CARRIAGE = "carriage"
    OFFICE = "office"


@dataclass(frozen=True)
class SiteContext:
    """The situation, in full, as handed to a building.

    Frozen and hashable by construction (all fields are themselves hashable):
    a `SiteContext` can be used as a dict key, compared by value, and passed
    between phases without risk of one phase mutating what an earlier phase
    already read (I1). It carries no RNG and offers no sampling method —
    `street_width` is a fact received from the block, never rolled here (I2).
    """

    street_width: float
    parcel_width: float
    parcel_depth: float
    year: int
    klass: BuildingClass
    ground: GroundProgramme
    corner: bool = False
    seed: int = 0
