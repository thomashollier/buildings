"""SoHo as a split grammar: the same engine as Paris, different rules.

```
Lot      --> insert( Facade | Roof? )
Facade   --> rhythm = fit(frontage){ end | bay* | end }       the generic solver
             split(y){ Storey* }                               from the recipe
Storey   :  role from its siblings (base / upper / top)
Storey   --> split(x){ Cell* } by the facade's rhythm
             Column* Entablature? Cornice? FireEscape?
Cell     :  vocabulary, period and class layers
Cell     :  opening --> split(x){ Jamb | LightBay | Jamb }
LightBay --> split(y){ Breast | Light | Lintel }   Shopfront?
Light    --> Surround? Keystone?
Roof     --> Dormer* Chimney*
```

Compared with Paris the *shape* of the grammar is nearly the same: a facade
cut into storeys, storeys cut by one rhythm, a cell cut around its light. What
differs is the data -- a 7.6 m lot instead of a 12-20 m parcel, glass taking
70% of a bay instead of 45%, a column on every pier, an entablature on every
floor, a flat roof behind a deep cornice -- and two productions Paris has no
use for, Column and FireEscape. That is the point of the exercise.

Unlike Paris, the bay rhythm here is sized by the engine's own ``fit``
operator, not by a typology size function.
"""

from __future__ import annotations

import math
from typing import Callable

from buildings.cga import (
    Attrs,
    AttributeStage,
    Derivation,
    Grammar,
    Layer,
    Part,
    Production,
    Scope,
    Shape,
    X,
    Y,
    derive,
    interpret,
)
from buildings.ir.nodes import BuildingNode
from buildings.rng import DecisionStream
from buildings.site import BuildingClass
from buildings.solver.fitting import SlotKind, SlotSpec
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common.kit import (
    INTERPRETERS,
    dress_the_light,
    is_bay,
    log_of,
    split_cell_around_its_light,
    split_light_bay,
    write_lot,
)
from buildings.typologies.soho.recipes import Recipe, SohoSite, recipe_for

__all__ = ["soho_grammar", "derive_soho", "generate_soho"]

_COLUMN_W = 0.36  # INFERRED -- an engaged iron column on a loft front
_ENTABLATURE = 0.42  # INFERRED -- the iron entablature crowning each floor
_DOOR_W = 1.15  # ABSOLUTE -- a door a person and a parcel pass through
_FIRE_ESCAPE_RAIL = 0.95  # ABSOLUTE -- a guard a body leans on
_ROOF_RISE = 3.0  # INFERRED -- a half-storey garret under a 40 degree roof
_DORMER = (1.15, 1.9)  # INFERRED -- a pedimented dormer, w x h
_CHIMNEY = (0.7, 1.4)  # INFERRED -- a party-wall chimney stack, w x height over ridge


def _recipe(shape: Shape) -> Recipe:
    return shape.attr("recipe")


def _site(shape: Shape) -> SohoSite:
    return shape.attr("site")


# ===========================================================================
# Productions
# ===========================================================================


def _lot(lot: Shape, d: Derivation) -> None:
    """A facade stands on the lot; a dwelling of its date also has a roof."""
    r = _recipe(lot)
    heights = [float(r.ground_storey)] + [
        float(r.first_upper) * float(r.taper) ** i for i in range(r.upper_storeys)
    ]
    lot.attrs["storey_heights"] = heights
    facade_h = math.fsum(heights)
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, facade_h), "facade")
    if r.pitched_roof:
        d.insert(lot, "Roof", Scope(0.0, facade_h, lot.scope.w, _ROOF_RISE), "roof")


def _facade(facade: Shape, d: Derivation) -> None:
    """The frontage is fitted with one rhythm of bays, then cut into storeys."""
    r = _recipe(facade)
    parts, result = d.fit(
        facade.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *r.end_pier, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *r.bay_pitch),
        min_bays=2,
    )
    facade.attrs["rhythm"] = parts
    heights = facade.attr("storey_heights")
    d.split(
        facade,
        Y,
        [Part("Storey", h, f"s{i}") for i, h in enumerate(heights)],
        id_base=facade.parent.id,
    )


def _storey(storey: Shape, d: Derivation) -> None:
    """A storey is cut by the facade's rhythm; columns stand on its piers, an
    entablature crowns it, and the top one carries the cornice."""
    r = _recipe(storey)
    cells = d.split(
        storey,
        X,
        [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(storey.attr("rhythm"))],
    )
    s = storey.scope
    role = storey.attrs["role"]
    if r.columns:
        edges = [cells[0].scope.x + cells[0].scope.w / 2.0] + [
            c.scope.x for c in cells[1:]
        ] + [cells[-1].scope.x + cells[-1].scope.w / 2.0]
        for i, cx in enumerate(edges):
            w = min(_COLUMN_W, cells[0].scope.w if i in (0, len(edges) - 1) else _COLUMN_W)
            top = s.h - (_ENTABLATURE if role != "top" or True else 0.0)
            d.insert(storey, "Column", Scope(cx - w / 2.0, s.y, w, top), f"column{i}")
    if role == "base" or (r.entablature_every_floor and role != "top"):
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - _ENTABLATURE, s.w, _ENTABLATURE), "entablature")
    if role == "top" and not r.pitched_roof:
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, float(r.cornice_projection)), "cornice", {"cornice_ornament": r.cornice_ornament})
    if role == "top" and r.pitched_roof:
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, float(r.cornice_projection)), "cornice", {"cornice_ornament": r.cornice_ornament})
    if r.fire_escape and role != "base":
        bays = [c for c in cells if _is_bay(c)]
        if len(bays) >= 2:
            mid = len(bays) // 2
            left, right = bays[mid - 1], bays[mid]
            x0 = left.scope.x + left.scope.w * 0.08
            x1 = right.scope.x + right.scope.w * 0.92
            d.insert(storey, "FireEscape", Scope(x0, s.y, x1 - x0, _FIRE_ESCAPE_RAIL), "fire_escape")


def _roof(roof: Shape, d: Derivation) -> None:
    """A pitched roof carries a dormer over each outer window axis and a
    chimney stack on each party wall."""
    s = roof.scope
    facade = roof.parent.children[0]
    bays = [c for c in facade.children[-1].children if _is_bay(c)]
    for i, axis in enumerate((bays[0], bays[-1]) if len(bays) > 1 else bays):
        dw, dh = _DORMER
        cx = axis.scope.x + axis.scope.w / 2.0
        d.insert(roof, "Dormer", Scope(cx - dw / 2.0, s.y + 0.35, dw, dh), f"dormer{i}")
    cw, ch = _CHIMNEY
    for i, x in enumerate((0.15, s.w - 0.15 - cw)):
        d.insert(roof, "Chimney", Scope(x, s.y + s.h, cw, ch), f"chimney{i}")


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_stack_says_where_you_are(storey: Shape, rng: DecisionStream) -> Attrs:
    """Base at the bottom, top at the top, upper between: read off the siblings."""
    n = len(storey.siblings)
    role = "base" if storey.index == 0 else "top" if storey.index == n - 1 else "upper"
    return Attrs({"role": role}, rule="soho.roles.position_in_the_stack")


def iron_order_follows_money(storey: Shape, rng: DecisionStream) -> Attrs | None:
    """A grand iron front is Corinthian; an ordinary one is a plain Doric."""
    if not _recipe(storey).columns:
        return None
    grand = _site(storey).klass is BuildingClass.GRAND
    return Attrs({"order": "corinthian" if grand else "doric"}, rule="soho.class.iron_order")


_is_bay = is_bay


def _door_cell(cell: Shape) -> bool:
    if cell.parent.attrs["role"] != "base" or not _is_bay(cell):
        return False
    bays = [c for c in cell.siblings if _is_bay(c)]
    return cell is (bays[0] if _recipe(cell).door_side == "left" else bays[-1])


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The end of the frontage is wall: party wall and pier, no opening."""
    if _is_bay(cell):
        return None
    return Attrs({"opening_type": "none"}, rule="soho.base.end_piers_are_wall")


def a_bay_holds_a_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Every bay above the street holds a window, its share of the bay set by
    what the front is made of."""
    if not _is_bay(cell):
        return None
    r = _recipe(cell)
    h = cell.scope.h
    return Attrs(
        {
            "opening_type": "window",
            "head": "flat",
            "light_width": float(r.window_share) * cell.scope.w,
            "sill": float(r.sill),
            "light_height": h - float(r.sill) - float(r.head_gap),
            "surround_kind": "moulded_architrave" if r.wall_material == "brick" else "none",
            "keystone_present": r.name == "federal_rowhouse",
        },
        rule="soho.base.a_bay_holds_a_window",
    )


def the_ground_floor_is_a_store(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """On a store-and-loft the ground floor is a store: glass from a low
    bulkhead to a transom and sign band, between the columns."""
    if not _is_bay(cell) or cell.parent.attrs["role"] != "base" or not _recipe(cell).shopfront:
        return None
    h = cell.scope.h
    return Attrs(
        {
            "opening_type": "shop_bay",
            "head": "flat",
            "light_width": cell.scope.w * 0.86,
            "sill": 0.45,
            "light_height": h - 0.45 - 0.85,
            "surround_kind": "none",
            "keystone_present": False,
        },
        rule="soho.base.the_ground_floor_is_a_store",
        specificity=10,
    )


def the_door(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """One bay of the ground floor is the door: to the stair at the side of a
    loft, or under a fanlight to one side of a rowhouse."""
    if not _door_cell(cell):
        return None
    federal = _recipe(cell).name == "federal_rowhouse"
    h = cell.scope.h
    return Attrs(
        {
            "opening_type": "pedestrian_entrance",
            "head": "round" if federal else "flat",
            "light_width": _DOOR_W,
            "sill": 0.0,
            "light_height": min(h - 0.35, 2.95 if federal else h - 0.85),
            "surround_kind": "moulded_architrave" if federal else "none",
            "keystone_present": federal,
        },
        rule="soho.base.the_door",
        specificity=20,
    )


def iron_heads_of_their_date(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """An iron front's window heads follow its date: Italianate round arches
    to the early 1860s, segmental to the early 1870s, flat after."""
    r = _recipe(cell)
    if r.name != "cast_iron_loft" or not _is_bay(cell) or cell.parent.attrs["role"] == "base":
        return None
    year = _site(cell).year
    head = "round" if year < 1862 else "segmental" if year < 1872 else "flat"
    return Attrs({"head": head}, rule="soho.period.iron_heads_of_their_date")


SOHO_LAYERS = (
    Layer("base", 0, (end_piers_are_wall, a_bay_holds_a_window, the_ground_floor_is_a_store, the_door)),
    Layer("period", 10, (iron_heads_of_their_date,)),
)


# ===========================================================================
# Interpretation
# ===========================================================================


def _describe(lot: Shape) -> TraceEntry:
    site, r = _site(lot), _recipe(lot)
    return TraceEntry(
        rule="soho.recipes.recipe_for",
        phase="structure",
        detail=f"{r.name}: {site.lots} lot(s), {site.year}, {site.programme.value}, {site.klass.value}",
    )


def materials_of_the_front(storey: Shape, rng: DecisionStream) -> Attrs:
    """A store front is iron whatever the floors over it are made of."""
    r = _recipe(storey)
    return Attrs(
        {"wall_material": r.ground_material if storey.attrs.get("role") == "base" or storey.index == 0 else r.wall_material},
        rule="soho.base.materials_of_the_front",
    )



def soho_grammar() -> Grammar:
    return Grammar(
        name="soho",
        productions=(
            Production("soho.lot", "Lot", _lot),
            Production("soho.facade", "Facade", _facade),
            Production("soho.storey", "Storey", _storey),
            Production("soho.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("soho.light_bay", "LightBay", split_light_bay),
            Production("soho.light", "Light", dress_the_light),
            Production("soho.roof", "Roof", _roof),
        ),
        stages=(
            AttributeStage(
                "Storey",
                (
                    Layer("roles", 0, (the_stack_says_where_you_are, materials_of_the_front)),
                    Layer("class", 20, (iron_order_follows_money,)),
                ),
            ),
            AttributeStage("Cell", SOHO_LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        # A cornice oversails the wall it crowns, and a chimney stands clear
        # of the roof it rises through: both are declared, nothing else is.
        overhangs=frozenset({"Cornice", "Chimney"}),
    )


def _axiom(site: SohoSite) -> Shape:
    r = recipe_for(site)
    return Shape(
        "Lot",
        Scope(0.0, 0.0, site.frontage, 40.0),
        "b",
        attrs={"site": site, "recipe": r},
    )


def derive_soho(
    site: SohoSite, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[Shape, Derivation]:
    grammar = soho_grammar()
    if refine is not None:
        grammar = refine(grammar)
    return derive(grammar, _axiom(site), DecisionStream(site.seed))


def generate_soho(
    site: SohoSite, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_soho(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
