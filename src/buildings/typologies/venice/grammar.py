"""The Venetian Gothic palazzo as a split grammar.

A merchant's house on a canal, c. 1350-1450, and its signature is horizontal:
the front is **tripartite**, two walled wings either side of a centre that is
mostly opening. The centre is the *portego*, the long hall running through the
house, and on the piano nobile it opens to the canal through a **polifora**: a
row of ogee-arched lights on colonnettes with a balcony across them. The
ground floor centre is the water gate.

```
Lot      --> insert( Facade )
Facade   --> split(y){ Storey* }                   water storey, two nobile floors, mezzanine
Storey   --> split(x){ Wing | Centre | Wing }      the tripartite front
Wing     --> rhythm = fit(w){ end | bay* | end }   single ogee windows, a balconette each
Centre   : nobile --> one Cell holding a polifora  split(x){ Light | Column | Light ... }
Centre   : water  --> the gate between two lights
```

Compared with the other grammars the new move is the tripartite split
*inside every storey*: the same three sections are cut on each floor, so the
wings line up and the centre reads as one vertical band of openings.

Numbers are INFERRED round figures for the type (Ca' Foscari, Ca' d'Oro,
Palazzo Pisani-Moretta), not measured plates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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
from buildings.solver.fitting import PlacedSlot, SlotKind, SlotSpec
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common.kit import (
    INTERPRETERS,
    dress_the_light,
    is_bay,
    log_of,
    split_cell_around_its_light,
    split_light_bay,
    split_light_bay_into_lights,
    write_lot,
)

__all__ = ["PalazzoSite", "venice_grammar", "derive_venice", "generate_venice"]


@dataclass(frozen=True)
class PalazzoSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


#: Storey heights, bottom-up: water storey, piano nobile, second nobile,
#: mezzanine under the roof. The first nobile is the tallest: it is the floor
#: the house was built to show. INFERRED.
_HEIGHTS = (4.6, 5.8, 5.0, 2.9)
_CENTRE_SHARE = 0.40  # INFERRED -- the portego's share of the front
_WING_BAY = (1.8, 2.2, 2.8)
_WING_END = (0.5, 0.9, 1.4)


def _site(shape: Shape) -> PalazzoSite:
    return shape.attr("site")


def _role(shape: Shape) -> str:
    return shape.attr("role")


# ===========================================================================
# Productions
# ===========================================================================


def _lot(lot: Shape, d: Derivation) -> None:
    """The palazzo stands its whole front on the canal."""
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, math.fsum(_HEIGHTS)), "facade")


def _facade(facade: Shape, d: Derivation) -> None:
    """Four storeys, the piano nobile the tallest."""
    d.split(facade, Y, [Part("Storey", h, f"s{i}") for i, h in enumerate(_HEIGHTS)], id_base=facade.parent.id)


def _storey(storey: Shape, d: Derivation) -> None:
    """Every storey is cut the same way: wing, centre, wing. A string course
    crowns each one; the top carries a dentilled cornice."""
    w = storey.scope.w
    centre = w * _CENTRE_SHARE
    wing = (w - centre) / 2.0
    d.split(storey, X, [Part("Wing", wing, "wing_left"), Part("Centre", centre, "centre"), Part("Wing", wing, "wing_right")])
    s = storey.scope
    if _role(storey) == "attic":
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 0.45), "cornice", {"cornice_ornament": "modillioned"})
    else:
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - 0.16, s.w, 0.16), "string_course", {"course_kind": "bandeau"})


def _wing(wing: Shape, d: Derivation) -> None:
    """A wing is wall with single windows in it, fitted to its own width."""
    parts, _ = d.fit(
        wing.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *_WING_END, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *_WING_BAY),
        max_bays=3,
    )
    d.split(wing, X, [Part(p.label, p.size, f"x{i}", p.attrs) for i, p in enumerate(parts)])


def _centre(centre: Shape, d: Derivation) -> None:
    """The centre is the portego's end: on the nobile floors one wide cell for
    the polifora, on the water storey the gate between two lights, under the
    roof a row of small windows."""
    w = centre.scope.w
    role = _role(centre)
    if role == "nobile":
        end = 0.45
        widths = [("end", end), ("bay", w - 2 * end), ("end", end)]
    else:
        n = 3
        end = 0.4
        bay = (w - 2 * end) / n
        widths = [("end", end)] + [("bay", bay)] * n + [("end", end)]
    parts = []
    cursor = centre.scope.x
    for i, (name, size) in enumerate(widths):
        slot = PlacedSlot(name, SlotKind.REPEATING if name == "bay" else SlotKind.FLEXIBLE, cursor, size)
        parts.append(Part("Cell", size, f"x{i}", {"slot": slot}))
        cursor += size
    d.split(centre, X, parts)


def _light_bay(column: Shape, d: Derivation) -> None:
    """A light bay with several lights becomes an arcade; any light bay on a
    nobile floor gets a balcony across its foot."""
    a = column.parent.attrs
    if a.get("lights"):
        split_light_bay_into_lights(column, d)
    else:
        split_light_bay(column, d)
    if a.get("balcony"):
        s = column.scope
        d.insert(column, "Balconette", Scope(s.x, s.y + a["sill"], s.w, 0.9), "balcony")


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_storey_knows_its_floor(storey: Shape, rng: DecisionStream) -> Attrs:
    """Water storey at the bottom, mezzanine at the top, nobile between."""
    n = len(storey.siblings)
    role = "water" if storey.index == 0 else "attic" if storey.index == n - 1 else "nobile"
    return Attrs({"role": role, "wall_material": "stucco_rose"}, rule="venice.roles.the_storey_knows_its_floor")


def _in_centre(cell: Shape) -> bool:
    return cell.parent.label == "Centre"


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Ends of a section are wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="venice.base.end_piers_are_wall")


def an_ogee_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A wing bay holds one tall ogee-headed light in a stone frame, with a
    balconette on the nobile floors."""
    if not is_bay(cell):
        return None
    role = _role(cell)
    h = cell.scope.h
    if role == "attic":
        return Attrs(
            {"opening_type": "window", "head": "flat", "light_width": 0.75, "sill": 0.9, "light_height": 0.95,
             "surround_kind": "moulded_architrave", "keystone_present": False},
            rule="venice.base.mezzanine_lights",
        )
    if role == "water":
        return Attrs(
            {"opening_type": "window", "head": "round", "light_width": 0.9, "sill": 1.6, "light_height": 1.6,
             "surround_kind": "moulded_architrave", "keystone_present": False},
            rule="venice.base.water_storey_lights",
        )
    return Attrs(
        {"opening_type": "window", "head": "ogee", "light_width": 1.1, "sill": 0.15, "light_height": h - 0.15 - 1.2,
         "surround_kind": "moulded_architrave", "keystone_present": False, "balcony": True},
        rule="venice.base.an_ogee_window",
    )


def the_polifora(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """On a nobile floor the centre is one opening of many ogee lights on
    colonnettes: five on a grand house, four otherwise, and the second nobile
    one fewer than the first."""
    if not (is_bay(cell) and _in_centre(cell) and _role(cell) == "nobile"):
        return None
    grand = _site(cell).klass is BuildingClass.GRAND
    first = cell.parent.parent.index == 1
    n = (5 if grand else 4) - (0 if first else 1)
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "head": "ogee", "light_width": cell.scope.w, "sill": 0.15,
         "light_height": h - 0.15 - 1.2, "lights": (1.0,) * n, "divider": "Column", "divider_width": 0.24,
         "order": "corinthian", "surround_kind": "none", "balcony": True},
        rule="venice.base.the_polifora",
        specificity=10,
    )


def the_water_gate(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The middle of the water storey is the gate the boats come in by."""
    if not (is_bay(cell) and _in_centre(cell) and _role(cell) == "water"):
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    if cell is not bays[len(bays) // 2]:
        return None
    return Attrs(
        {"opening_type": "pedestrian_entrance", "head": "round", "light_width": cell.scope.w * 0.8, "sill": 0.0,
         "light_height": cell.scope.h - 0.7, "surround_kind": "moulded_architrave"},
        rule="venice.base.the_water_gate",
        specificity=20,
    )


LAYERS = (Layer("base", 0, (end_piers_are_wall, an_ogee_window, the_polifora, the_water_gate)),)


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="venice.palazzo", phase="structure", detail=f"Gothic palazzo, {s.width:.1f} m on the canal, {s.year}, {s.klass.value}")


def venice_grammar() -> Grammar:
    return Grammar(
        name="venice",
        productions=(
            Production("venice.lot", "Lot", _lot),
            Production("venice.facade", "Facade", _facade),
            Production("venice.storey", "Storey", _storey),
            Production("venice.wing", "Wing", _wing),
            Production("venice.centre", "Centre", _centre),
            Production("venice.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("venice.light_bay", "LightBay", _light_bay),
            Production("venice.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (the_storey_knows_its_floor,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={**INTERPRETERS, "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year})},
        overhangs=frozenset({"Cornice"}),
    )


def derive_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = venice_grammar() if refine is None else refine(venice_grammar())
    axiom = Shape("Lot", Scope(0.0, 0.0, site.width, 40.0), "b", attrs={"site": site})
    return derive(grammar, axiom, DecisionStream(site.seed))


def generate_venice(
    site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_venice(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
