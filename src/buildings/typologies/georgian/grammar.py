"""The Georgian London terrace house as a split grammar.

Built to the Building Act of 1774's "rates" and to a Palladian rule of
proportion, and the signature is **the window's shape by floor**. Every
window on the front is the same width, so the axes read straight up the
house; what changes from floor to floor is the *height*, and it changes by
ratio, not by taste:

```
ground      1 : 1.75   over a rusticated stucco base, the door under a fanlight
first       1 : 2.1    the piano nobile, tall to the floor, a railing across each
second      1 : 1.6
third       1 : 1      square, under the cornice
parapet                a plain wall that hides the roof
```

```
Lot      --> insert( Facade )
Facade   --> rhythm = fit(w){ end | bay* | end }   split(y){ Storey* | Parapet }
Storey   : the floor's aspect ratio, read off its place in the stack
Cell     --> split(x){ Jamb | LightBay | Jamb }      light height = width x ratio
```

Numbers are INFERRED round figures for a second-rate house (Bedford Square,
Gower Street), not measured plates.
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

__all__ = ["TerraceSite", "georgian_grammar", "derive_georgian", "generate_georgian"]


@dataclass(frozen=True)
class TerraceSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


#: Storey heights by floor, and the window's height-to-width ratio on each:
#: the one table this style is. INFERRED.
_FLOORS = (
    ("ground", 3.5, 1.75),
    ("first", 4.1, 2.1),
    ("second", 3.3, 1.6),
    ("third", 2.7, 1.0),
)
_PARAPET = 1.0
_BAY = (1.9, 2.2, 2.7)
_END = (0.5, 0.7, 1.2)
_WINDOW_W = 1.05  # ABSOLUTE -- one sash width, the same on every floor


def _site(shape: Shape) -> TerraceSite:
    return shape.attr("site")


def _lot(lot: Shape, d: Derivation) -> None:
    """The house front is its four floors and the parapet over them."""
    h = math.fsum(f[1] for f in _FLOORS) + _PARAPET
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, h), "facade")


def _facade(facade: Shape, d: Derivation) -> None:
    """Three bays on a second-rate front, fitted once; four floors and a
    parapet."""
    parts, _ = d.fit(
        facade.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *_END, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *_BAY),
        max_bays=5,
    )
    facade.attrs["rhythm"] = parts
    floors = [Part("Storey", h, f"s{i}", {"floor": name, "ratio": r}) for i, (name, h, r) in enumerate(_FLOORS)]
    floors.append(Part("Storey", _PARAPET, f"s{len(_FLOORS)}", {"floor": "parapet"}))
    d.split(facade, Y, floors, id_base=facade.parent.id)


def _storey(storey: Shape, d: Derivation) -> None:
    """A floor is cut by the rhythm; a band marks the top of the stucco base,
    and the cornice runs under the parapet."""
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(storey.attr("rhythm"))])
    s = storey.scope
    if storey.attrs["floor"] == "ground":
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - 0.18, s.w, 0.18), "band", {"course_kind": "bandeau"})
    if storey.attrs["floor"] == "third":
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 0.4), "cornice", {"cornice_ornament": "modillioned"})


def _light_bay(column: Shape, d: Derivation) -> None:
    """The light, and on the piano nobile a railing across its foot."""
    split_light_bay(column, d)
    a = column.parent.attrs
    if a.get("railing"):
        s = column.scope
        d.insert(column, "Balconette", Scope(s.x, s.y + a["sill"], s.w, 0.9), "railing")


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_floor_and_its_material(storey: Shape, rng: DecisionStream) -> Attrs:
    """Its floor names its role; the base is stucco, the rest London stock."""
    floor = storey.attrs["floor"]
    return Attrs(
        {"role": floor, "wall_material": "stucco" if floor == "ground" else "brick_london"},
        rule="georgian.roles.the_floor_and_its_material",
    )


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The party-wall ends, and the whole parapet, are wall."""
    if is_bay(cell) and cell.parent.attrs["floor"] != "parapet":
        return None
    return Attrs({"opening_type": "none"}, rule="georgian.base.wall")


def the_window_of_its_floor(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Every window is one sash wide; its height is that width times the ratio
    its floor is built to, so the proportion is the floor's, not the window's."""
    storey = cell.parent
    if not is_bay(cell) or storey.attrs["floor"] == "parapet":
        return None
    h = storey.scope.h
    height = min(_WINDOW_W * storey.attrs["ratio"], h - 0.3)
    nobile = storey.attrs["floor"] == "first"
    sill = 0.1 if nobile else max(0.25, (h - height) * 0.55)
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": _WINDOW_W, "sill": sill,
         "light_height": height, "surround_kind": "none", "keystone_present": storey.attrs["floor"] == "ground",
         "railing": nobile},
        rule="georgian.base.the_window_of_its_floor",
    )


def the_fanlit_door(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The door is in the outer bay, under a semicircular fanlight in a
    rusticated arch."""
    storey = cell.parent
    if not is_bay(cell) or storey.attrs["floor"] != "ground":
        return None
    if cell is not [c for c in cell.siblings if is_bay(c)][0]:
        return None
    return Attrs(
        {"opening_type": "pedestrian_entrance", "head": "round", "light_width": 1.1, "sill": 0.0,
         "light_height": 3.0, "surround_kind": "moulded_architrave", "keystone_present": True, "railing": False},
        rule="georgian.base.the_fanlit_door",
        specificity=10,
    )


LAYERS = (Layer("base", 0, (end_piers_are_wall, the_window_of_its_floor, the_fanlit_door)),)


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="georgian.terrace_house", phase="structure", detail=f"Georgian terrace house, {s.width:.1f} m, {s.year}")


def georgian_grammar() -> Grammar:
    return Grammar(
        name="georgian",
        productions=(
            Production("georgian.lot", "Lot", _lot),
            Production("georgian.facade", "Facade", _facade),
            Production("georgian.storey", "Storey", _storey),
            Production("georgian.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("georgian.light_bay", "LightBay", _light_bay),
            Production("georgian.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (the_floor_and_its_material,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={**INTERPRETERS, "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year})},
        overhangs=frozenset({"Cornice"}),
    )


def derive_georgian(site: TerraceSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = georgian_grammar() if refine is None else refine(georgian_grammar())
    return derive(grammar, Shape("Lot", Scope(0.0, 0.0, site.width, 40.0), "b", attrs={"site": site}), DecisionStream(site.seed))


def generate_georgian(site: TerraceSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_georgian(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
