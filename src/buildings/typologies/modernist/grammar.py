"""The Corbusian modernist block as a split grammar.

Le Corbusier's "five points" (1926) are a grammar written as a manifesto,
and every one of them is a rule about what may be split from what:

* **pilotis** -- the building stands on posts, so the ground storey is open
  and its posts are the structure's own grid;
* **the free facade** -- because the posts carry the floors, the front
  carries nothing, so its openings need not line up with anything;
* **the ribbon window** -- one strip of glass the length of each floor,
  ignoring the structural bays entirely;
* **the roof garden** -- the roof is a terrace with a pavilion on it,
  placed where the plan wants it, not on an axis.

```
Lot      --> insert( Facade | Pavilion )
Facade   --> grid = fit(w){ end | bay* | end }       the posts' grid
             split(y){ Pilotis | Floor* }
Pilotis  --> Piloti* on the grid; one glazed entrance, recessed
Floor    --> split(x){ end | Ribbon | end }           NOT by the grid: the free facade
Ribbon   --> split(x){ Light | Mullion | Light ... }  one strip, many panes
Pavilion --> off-axis, with a curved screen wall
```

The signature move is the Floor rule: every other grammar in this repository
cuts a storey by the facade's rhythm, so its windows stand on its bays. This
one deliberately does not, and the ribbon runs across the posts' grid.

Numbers are INFERRED round figures for the type (Villa Savoye, the Pessac
houses, Weissenhof), not measured plates.
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
from buildings.ir.nodes import BuildingNode, GableNode
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

__all__ = ["VillaSite", "modernist_grammar", "derive_modernist", "generate_modernist"]


@dataclass(frozen=True)
class VillaSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


_PILOTIS = 3.1
_FLOOR = 3.0
_PANE = 1.2  # INFERRED -- one sliding pane of the ribbon
_PILOTI_W = 0.32
_PAVILION = (0.38, 2.7)  # share of the frontage, height


def _floors(site: VillaSite) -> int:
    return {BuildingClass.MODEST: 1, BuildingClass.ORDINARY: 2, BuildingClass.COMFORTABLE: 2, BuildingClass.GRAND: 3}[site.klass]


def _site(shape: Shape) -> VillaSite:
    return shape.attr("site")


def _slot(name: str, start: float, size: float) -> PlacedSlot:
    return PlacedSlot(name, SlotKind.REPEATING if name == "bay" else SlotKind.FLEXIBLE, start, size)


def _lot(lot: Shape, d: Derivation) -> None:
    """The block stands on its posts, and a pavilion stands on its roof, off
    the axis, where the plan wants it."""
    h = _PILOTIS + _floors(_site(lot)) * _FLOOR
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, h), "facade")
    share, ph = _PAVILION
    pw = lot.scope.w * share
    d.insert(lot, "Pavilion", Scope(lot.scope.w * 0.52, h, pw, ph), "pavilion")


def _facade(facade: Shape, d: Derivation) -> None:
    """The posts' grid is fitted once; the pilotis and the floors are cut."""
    parts, _ = d.fit(
        facade.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.3, 0.6, 1.2, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, 4.2, 4.8, 5.6),
    )
    facade.attrs["grid"] = parts
    heights = [_PILOTIS] + [_FLOOR] * _floors(_site(facade))
    d.split(facade, Y, [Part("Storey", h, f"s{i}") for i, h in enumerate(heights)], id_base=facade.parent.id)


def _storey(storey: Shape, d: Derivation) -> None:
    """The pilotis storey is cut by the posts' grid and has a post on every
    grid line. A floor above is cut by nothing of the kind: a wall at each
    end and one ribbon between."""
    s = storey.scope
    if storey.attrs["role"] == "pilotis":
        grid = storey.attr("grid")
        d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(grid)])
        x = s.x
        for i, p in enumerate(grid[:-1]):
            x += p.size
            d.insert(storey, "Column", Scope(x - _PILOTI_W / 2.0, s.y, _PILOTI_W, s.h), f"piloti{i}", {"order": "piloti"})
        return
    end = 0.7
    ribbon = s.w - 2 * end
    d.split(
        storey,
        X,
        [
            Part("Cell", end, "x0", {"slot": _slot("end", s.x, end)}),
            Part("Cell", ribbon, "x1", {"slot": _slot("bay", s.x + end, ribbon)}),
            Part("Cell", end, "x2", {"slot": _slot("end", s.x + end + ribbon, end)}),
        ],
    )


def _pavilion(pavilion: Shape, d: Derivation) -> None:
    """The pavilion is one more floor, short, with its own strip of glass."""
    s = pavilion.scope
    d.insert(pavilion, "Storey", s, "storey", {"role": "pavilion"})


def _light_bay(column: Shape, d: Derivation) -> None:
    if column.parent.attrs.get("lights"):
        split_light_bay_into_lights(column, d)
    else:
        split_light_bay(column, d)


# ===========================================================================
# Attribute rules
# ===========================================================================


def pilotis_floors_pavilion(storey: Shape, rng: DecisionStream) -> Attrs | None:
    """The bottom storey is the pilotis, open and in shadow; the floors over it
    are white render; a pavilion knows what it is."""
    if storey.attrs.get("role") == "pavilion":
        return Attrs({"wall_material": "render_white"}, rule="modernist.roles.pavilion")
    role = "pilotis" if storey.index == 0 else "floor"
    return Attrs(
        {"role": role, "wall_material": "shadow" if role == "pilotis" else "render_white"},
        rule="modernist.roles.pilotis_floors_pavilion",
    )


def the_ground_is_open(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Under the pilotis there is no wall to open: only the glazed entrance,
    set back in the shadow, in one bay of the grid."""
    storey = cell.parent
    if storey.attrs.get("role") != "pilotis":
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    if not is_bay(cell) or cell is not bays[len(bays) // 2]:
        return Attrs({"opening_type": "none"}, rule="modernist.base.the_ground_is_open")
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w * 0.7, "sill": 0.0,
         "light_height": h - 0.35, "lights": (1.0, 1.0, 1.0), "divider": "Mullion", "divider_width": 0.06,
         "surround_kind": "none", "keystone_present": False},
        rule="modernist.base.the_glazed_entrance",
    )


def the_ribbon_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A floor's middle cell is one strip of glass its whole length, cut into
    sliding panes; the ends are wall."""
    storey = cell.parent
    if storey.attrs.get("role") not in ("floor", "pavilion"):
        return None
    if not is_bay(cell):
        return Attrs({"opening_type": "none"}, rule="modernist.base.end_walls")
    panes = max(2, round(cell.scope.w / _PANE))
    pavilion = storey.attrs.get("role") == "pavilion"
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w, "sill": 0.9 if not pavilion else 0.6,
         "light_height": 1.1 if not pavilion else 1.4, "lights": (1.0,) * panes, "divider": "Mullion",
         "divider_width": 0.05, "surround_kind": "none", "keystone_present": False},
        rule="modernist.base.the_ribbon_window",
    )


LAYERS = (Layer("base", 0, (the_ground_is_open, the_ribbon_window)),)


def write_pavilion(pavilion: Shape, below, d) -> list:
    """The pavilion's curved screen wall, bellying out beside the box it
    shelters: the one free curve on an otherwise orthogonal front."""
    s = pavilion.scope
    bulge = s.h * 0.55
    curve = [(s.x - bulge * math.sin(math.pi * k / 12), s.y + s.h * k / 12) for k in range(13)]
    return [
        GableNode(
            id=f"{pavilion.id}/screen",
            kind="gable",
            trace=tuple(pavilion.trace),
            props={"x": s.x - bulge, "y": s.y, "w": bulge, "h": s.h, "form": "pavilion", "points": tuple(curve),
                   "hoist_beam": None, "wall_material": "render_white"},
        ),
        *below,
    ]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="modernist.five_points", phase="structure", detail=f"Corbusian block, {s.width:.1f} m, {s.year}, {_floors(s)} floor(s) on pilotis")


def modernist_grammar() -> Grammar:
    return Grammar(
        name="modernist",
        productions=(
            Production("modernist.lot", "Lot", _lot),
            Production("modernist.facade", "Facade", _facade),
            Production("modernist.storey", "Storey", _storey),
            Production("modernist.pavilion", "Pavilion", _pavilion),
            Production("modernist.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("modernist.light_bay", "LightBay", _light_bay),
            Production("modernist.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (pilotis_floors_pavilion,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Pavilion": write_pavilion,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
    )


def derive_modernist(site: VillaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = modernist_grammar() if refine is None else refine(modernist_grammar())
    return derive(grammar, Shape("Lot", Scope(0.0, 0.0, site.width, 30.0), "b", attrs={"site": site}), DecisionStream(site.seed))


def generate_modernist(site: VillaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_modernist(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
