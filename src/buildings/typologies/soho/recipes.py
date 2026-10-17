"""What SoHo was built under, as numbers with their kinds.

Three building types stand on the same 25-foot Manhattan lot, and which one a
situation gets is a matter of date and programme, not taste:

* **Federal rowhouse** (to c. 1835). A dwelling of two full storeys and a
  half-storey in a pitched roof, brick, three bays, the door to one side under
  a fanlight. The roof, its dormers and the end chimneys are what the date
  gives it.
* **Cast-iron loft** (c. 1850-1880). A warehouse-and-store whose whole front
  is a kit of iron columns and entablatures bolted to the brick behind: glass
  between columns, an entablature at every floor, a deep bracketed cornice and
  a flat roof. Italianate round arches give way to segmental and then flat
  heads as the date moves.
* **Brick store-and-loft** (c. 1880-1895, and the cheaper lofts before). Brick
  piers with stone lintels over a cast-iron storefront, more and narrower
  windows, a pressed-metal cornice, and the fire escape the 1867 and 1880s
  laws put on the street front.

Status of the numbers: these are **INFERRED** -- typical dimensions of the
surviving SoHo stock (Landmarks Preservation Commission district report,
1973; Gayle and Gillon, *Cast-Iron Architecture in New York*, 1974), read
as round figures, not measured plates. The Paris typology's numbers are
answerable to Daly; these are answerable to nothing yet, and say so. What
the grammar demonstrates is that a second typology is *data* on the same
engine; calibrating it would be its own piece of work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from buildings.quantity import Abs, Prop, Quantity, Reg
from buildings.site import BuildingClass

__all__ = ["Programme", "SohoSite", "Recipe", "recipe_for", "LOT_WIDTH"]

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


@dataclass(frozen=True)
class Recipe:
    """One building type's vocabulary and proportions."""

    name: str
    wall_material: str  # "brick" | "cast_iron"
    ground_material: str
    ground_storey: Quantity
    first_upper: Quantity
    taper: float  # metres lost per storey going up
    upper_storeys: int
    # The bay module and the end pier, as (min, preferred, max).
    bay_pitch: tuple[float, float, float]
    end_pier: tuple[float, float, float]
    #: How much of its bay the light takes. The single number that most
    #: separates a cast-iron front (mostly glass) from a brick one.
    window_share: Quantity
    sill: Quantity
    head_gap: Quantity  # wall over the light: lintel, spandrel, entablature
    columns: bool
    entablature_every_floor: bool
    cornice_projection: Quantity
    cornice_ornament: str  # "bracketed" | "modillioned"
    pitched_roof: bool
    fire_escape: bool
    shopfront: bool
    door_side: str  # "left" | "right"


def _federal(site: SohoSite) -> Recipe:
    return Recipe(
        name="federal_rowhouse",
        wall_material="brick",
        ground_material="brick",
        ground_storey=Abs(3.35, "INFERRED -- a raised parlour floor over its basement"),
        first_upper=Abs(3.05, "INFERRED -- the chamber floor"),
        taper=0.0,
        upper_storeys=1,
        bay_pitch=(1.9, 2.1, 2.5),
        end_pier=(0.6, 0.85, 1.3),
        window_share=Prop(0.46, "INFERRED -- a 6-over-6 sash in a load-bearing brick wall"),
        sill=Abs(0.80, "a sill at a body's waist"),
        head_gap=Abs(0.55, "INFERRED -- a splayed stone lintel and the brick over it"),
        columns=False,
        entablature_every_floor=False,
        cornice_projection=Abs(0.35, "INFERRED -- a wooden dentilled eaves cornice"),
        cornice_ornament="modillioned",
        pitched_roof=True,
        fire_escape=False,
        shopfront=False,
        door_side="left",
    )


def _cast_iron(site: SohoSite) -> Recipe:
    grand = site.klass is BuildingClass.GRAND
    return Recipe(
        name="cast_iron_loft",
        wall_material="cast_iron",
        ground_material="cast_iron",
        ground_storey=Abs(5.4 if grand else 4.9, "INFERRED -- a store with a mezzanine-height ceiling"),
        first_upper=Abs(4.5 if grand else 4.2, "INFERRED -- a loft lit from the street end only"),
        taper=0.15,
        upper_storeys=5 if site.year >= 1870 else 4,
        bay_pitch=(2.3, 2.55, 2.9),
        end_pier=(0.3, 0.42, 0.7),
        window_share=Prop(0.70, "INFERRED -- iron carries the front, so the front is glass"),
        sill=Abs(0.75, "a sill at a body's waist"),
        head_gap=Abs(0.70, "INFERRED -- the entablature and the spandrel under it"),
        columns=True,
        entablature_every_floor=True,
        cornice_projection=Abs(1.0, "INFERRED -- a cast or pressed bracketed cornice"),
        cornice_ornament="bracketed",
        pitched_roof=False,
        fire_escape=not grand,
        shopfront=True,
        door_side="right",
    )


def _brick_loft(site: SohoSite) -> Recipe:
    return Recipe(
        name="brick_store_and_loft",
        wall_material="brick",
        ground_material="cast_iron",
        ground_storey=Abs(4.6, "INFERRED -- a cast-iron storefront under brick"),
        first_upper=Abs(3.8, "INFERRED"),
        taper=0.10,
        upper_storeys=5,
        bay_pitch=(1.7, 1.95, 2.3),
        end_pier=(0.45, 0.6, 0.9),
        window_share=Prop(0.52, "INFERRED -- brick piers between stone-linteled windows"),
        sill=Abs(0.80, "a sill at a body's waist"),
        head_gap=Abs(0.55, "INFERRED -- a stone lintel and a brick course"),
        columns=False,
        entablature_every_floor=False,
        cornice_projection=Abs(0.85, "INFERRED -- a pressed-metal bracketed cornice"),
        cornice_ornament="bracketed",
        pitched_roof=False,
        fire_escape=True,
        shopfront=True,
        door_side="right",
    )


def recipe_for(site: SohoSite) -> Recipe:
    """Date and programme choose the type; money only chooses within it."""
    if site.programme is Programme.DWELLING:
        if site.year > 1840:
            raise ValueError("only the Federal dwelling is modelled; it stops being built c. 1835")
        return _federal(site)
    if 1848 <= site.year < 1880 and site.klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
        return _cast_iron(site)
    if site.year < 1848:
        raise ValueError("lofts on this street are a product of the 1850s; none before c. 1848")
    return _brick_loft(site)
