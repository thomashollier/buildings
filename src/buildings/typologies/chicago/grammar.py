"""The Chicago School office block as a split grammar.

A steel frame with a skin on it, c. 1890-1910, and its signature is
**vertical and tripartite**: Sullivan's column of base, shaft and capital.
The base is two tall storeys of shops; the shaft is many identical floors
with nothing to tell them apart; the capital is a top floor of arched lights,
an attic of roundels and a deep cornice. The frame shows through as **piers
that run the whole height of the shaft**, and every bay between them is a
**Chicago window**: a wide fixed pane between two narrow sashes.

```
Lot      --> insert( Facade )
Facade   --> rhythm = fit(w){ end | bay* | end }     the frame's bays, about 6 m
             split(y){ Storey* }                       base x2, shaft x N, capital x2
             Pier*                                     one per frame line, base top to capital
Storey   : base | shaft | capital | attic             read off the stack
Cell     : shaft --> split(x){ Sash | Fixed | Sash }  the Chicago window, 1:2:1
Cell     : capital --> two round-arched lights; attic --> a roundel
```

The new move here is the Pier: a shape inserted on the *facade* that spans a
run of storeys, so the vertical reads through the horizontal floors rather
than being drawn floor by floor.

Numbers are INFERRED round figures for the type (Reliance, Carson Pirie
Scott, the Gage group), not measured plates.
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
    split_light_bay_into_lights,
    write_lot,
)

__all__ = ["OfficeSite", "chicago_grammar", "derive_chicago", "generate_chicago"]


@dataclass(frozen=True)
class OfficeSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


_BAY = (5.4, 6.1, 6.8)  # INFERRED -- the frame's bay: about 20 feet
_END = (0.7, 1.0, 1.5)
_BASE = (5.6, 4.4)  # shops, then their mezzanine
_SHAFT_STOREY = 3.75  # every shaft floor the same: the point of a shaft
_CAPITAL = (3.9, 2.4)  # the arcaded top floor, the attic
_PIER = 0.8


def _site(shape: Shape) -> OfficeSite:
    return shape.attr("site")


def _shaft_floors(site: OfficeSite) -> int:
    """Height is what the money and the elevator allow: a grand building
    climbs higher, and later buildings climb higher than early ones."""
    base = {BuildingClass.MODEST: 6, BuildingClass.ORDINARY: 7, BuildingClass.COMFORTABLE: 9, BuildingClass.GRAND: 11}
    return base[site.klass] + (2 if site.year >= 1900 else 0)


# ===========================================================================
# Productions
# ===========================================================================


def _lot(lot: Shape, d: Derivation) -> None:
    """The block stands on its whole lot."""
    heights = [*_BASE, *([_SHAFT_STOREY] * _shaft_floors(_site(lot))), *_CAPITAL]
    lot.attrs["storey_heights"] = heights
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, math.fsum(heights)), "facade")


def _facade(facade: Shape, d: Derivation) -> None:
    """The frame's bays are fitted once; the storeys are cut; and a pier is
    stood on every frame line, from the top of the base to the foot of the
    capital."""
    parts, _ = d.fit(
        facade.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *_END, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *_BAY),
    )
    facade.attrs["rhythm"] = parts
    heights = facade.attr("storey_heights")
    storeys = d.split(facade, Y, [Part("Storey", h, f"s{i}") for i, h in enumerate(heights)], id_base=facade.parent.id)
    bottom = storeys[len(_BASE)].scope.y
    top = storeys[-len(_CAPITAL)].scope.y
    # Frame lines: the middle of each end pier, and every joint between bays.
    edges, x = [], facade.scope.x
    for p in parts:
        edges.append((x, x + p.size, p.attrs["slot"].name))
        x += p.size
    lines = [(edges[0][0] + edges[0][1]) / 2.0]
    lines += [e[1] for e, f in zip(edges, edges[1:]) if e[2] == "bay" and f[2] == "bay"]
    lines.append((edges[-1][0] + edges[-1][1]) / 2.0)
    for i, cx in enumerate(lines):
        w = min(_PIER, parts[0].size) if i in (0, len(lines) - 1) else _PIER
        d.insert(facade, "Pier", Scope(cx - w / 2.0, bottom, w, top - bottom), f"pier{i}", {"order": "pilaster"})


def _storey(storey: Shape, d: Derivation) -> None:
    """A storey is cut by the frame; a belt course closes the base and opens
    the capital; the attic carries the cornice."""
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(storey.attr("rhythm"))])
    s = storey.scope
    role = storey.attrs["role"]
    n = len([x for x in storey.siblings if x.label == "Storey"])
    if storey.index == len(_BASE) - 1 or storey.index == n - len(_CAPITAL) - 1:
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - 0.5, s.w, 0.5), "belt", {"course_kind": "entablature"})
    if role == "attic":
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 1.5), "cornice", {"cornice_ornament": "bracketed"})


def _light_bay(column: Shape, d: Derivation) -> None:
    """A bay of several lights becomes a row of them."""
    if column.parent.attrs.get("lights"):
        split_light_bay_into_lights(column, d)
    else:
        split_light_bay(column, d)


# ===========================================================================
# Attribute rules
# ===========================================================================


def base_shaft_capital(storey: Shape, rng: DecisionStream) -> Attrs:
    """Two storeys of base, two of capital, and the shaft between."""
    stack = [s for s in storey.siblings if s.label == "Storey"]
    n, i = len(stack), storey.index
    if i < len(_BASE):
        role, material = "base", "stone"
    elif i == n - 1:
        role, material = "attic", "terracotta"
    elif i >= n - len(_CAPITAL):
        role, material = "capital", "terracotta"
    else:
        role, material = "shaft", "terracotta"
    return Attrs({"role": role, "wall_material": material}, rule="chicago.roles.base_shaft_capital")


def _role(cell: Shape) -> str:
    return cell.parent.attrs["role"]


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The corners are wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="chicago.base.end_piers_are_wall")


def the_chicago_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A shaft bay is almost all glass: a fixed pane twice the width of the
    sash either side of it, under a spandrel."""
    if not is_bay(cell) or _role(cell) != "shaft":
        return None
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w - _PIER - 0.3, "sill": 0.8,
         "light_height": h - 0.8 - 0.75, "lights": (1.0, 2.0, 1.0), "divider": "Mullion", "divider_width": 0.14,
         "surround_kind": "none", "keystone_present": False},
        rule="chicago.base.the_chicago_window",
    )


def shops_in_the_base(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The base is shops, and the floor over them is their showroom: glass
    between the piers, full width."""
    if not is_bay(cell) or _role(cell) != "base":
        return None
    h = cell.scope.h
    ground = cell.parent.index == 0
    return Attrs(
        {"opening_type": "shop_bay" if ground else "window", "head": "flat", "light_width": cell.scope.w - 0.9,
         "sill": 0.45 if ground else 0.6, "light_height": h - (0.45 + 0.9 if ground else 0.6 + 0.9),
         "lights": None if ground else (1.0, 2.0, 1.0), "divider": "Mullion", "divider_width": 0.14,
         "surround_kind": "none", "keystone_present": False},
        rule="chicago.base.shops_in_the_base",
    )


def the_way_in(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The office entrance is the middle bay of the ground floor, under a
    round arch the full height of the shop storey."""
    if not is_bay(cell) or cell.parent.index != 0:
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    if cell is not bays[len(bays) // 2]:
        return None
    return Attrs(
        {"opening_type": "pedestrian_entrance", "head": "round", "light_width": 2.6, "sill": 0.0,
         "light_height": cell.scope.h - 0.6, "lights": None, "surround_kind": "moulded_architrave"},
        rule="chicago.base.the_way_in",
        specificity=10,
    )


def the_arcaded_capital(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The capital's floor opens in round-arched pairs; the attic over it in
    roundels, one to a bay."""
    if not is_bay(cell) or _role(cell) not in ("capital", "attic"):
        return None
    h = cell.scope.h
    if _role(cell) == "attic":
        return Attrs(
            {"opening_type": "oeil_de_boeuf", "head": "flat", "light_width": 1.1, "sill": 0.3,
             "light_height": 1.1, "lights": None, "surround_kind": "none", "keystone_present": False},
            rule="chicago.base.attic_roundels",
        )
    return Attrs(
        {"opening_type": "window", "head": "round", "light_width": cell.scope.w - _PIER - 0.8, "sill": 0.8,
         "light_height": h - 0.8 - 0.4, "lights": (1.0, 1.0), "divider": "Column", "divider_width": 0.3,
         "order": "doric", "surround_kind": "none", "keystone_present": False},
        rule="chicago.base.the_arcaded_capital",
    )


LAYERS = (Layer("base", 0, (end_piers_are_wall, the_chicago_window, shops_in_the_base, the_way_in, the_arcaded_capital)),)


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(
        rule="chicago.office_block",
        phase="structure",
        detail=f"Chicago School office block, {s.width:.1f} m, {s.year}, {s.klass.value}: {_shaft_floors(s)} shaft floors",
    )


def chicago_grammar() -> Grammar:
    return Grammar(
        name="chicago",
        productions=(
            Production("chicago.lot", "Lot", _lot),
            Production("chicago.facade", "Facade", _facade),
            Production("chicago.storey", "Storey", _storey),
            Production("chicago.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("chicago.light_bay", "LightBay", _light_bay),
            Production("chicago.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (base_shaft_capital,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Pier": INTERPRETERS["Column"],
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        overhangs=frozenset({"Cornice"}),
    )


def derive_chicago(site: OfficeSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = chicago_grammar() if refine is None else refine(chicago_grammar())
    axiom = Shape("Lot", Scope(0.0, 0.0, site.width, 120.0), "b", attrs={"site": site})
    return derive(grammar, axiom, DecisionStream(site.seed))


def generate_chicago(
    site: OfficeSite, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_chicago(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
