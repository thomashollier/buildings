"""The SoHo situation, and which type it gets.

Three building types stand on the same 25-foot Manhattan lot -- Federal
rowhouse, cast-iron loft, brick store-and-loft -- and which one a situation
gets is a matter of date and programme, not taste. The choice and each type's
proportions live in ``soho.toml``; ``recipe_for`` reads them back from a
derivation so there is one statement of them.

Status of the numbers: INFERRED round figures for the surviving stock (LPC
district report, 1973; Gayle and Gillon, 1974), not measured plates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace

from buildings.quantity import Reg
from buildings.site import BuildingClass

__all__ = ["Programme", "SohoSite", "recipe_for", "LOT_WIDTH"]

#: The Commissioners' Plan lot: 25 feet. A frontage is a whole number of them.
LOT_WIDTH = Reg(7.62, "Commissioners' Plan of 1811 -- the 25 ft x 100 ft Manhattan lot")


class Programme(Enum):
    DWELLING = "dwelling"
    LOFT = "loft"  # store on the ground floor, lofts above


@dataclass(frozen=True)
class SohoSite:
    """The situation: how many lots, when, for what, and how much money."""

    lots: int
    year: int
    programme: Programme
    klass: BuildingClass
    seed: int = 0

    @property
    def frontage(self) -> float:
        return self.lots * float(LOT_WIDTH)


def recipe_for(site: SohoSite) -> SimpleNamespace:
    """The type the rule file chooses, with its table of proportions.

    Raises ``ValueError`` for a situation the file refuses."""
    from buildings.typologies.soho.grammar import derive_soho

    lot, _ = derive_soho(site)
    return SimpleNamespace(name=lot.attrs["type"], **lot.attrs["r"])
