"""The San Francisco Victorian as a split grammar.

A timber row house on the 25-foot lot of the 1870s-1890s, and its signature is
the **bay window**: a three-sided projection stacked up the front over a
raised basement, beside a column for the stair and the door. In elevation a
bay's front face reads at full width and its two angled faces foreshortened,
so a slanted bay and a square one differ in exactly one number, how much of
the bay its side faces take.

```
Lot      --> insert( Facade | Top )
Facade   --> split(y){ Basement | Parlour | Chamber }
Storey   --> split(x){ BayZone | EntryZone }                 the bay on the downhill side
BayZone  : above the basement --> split(x){ Face | Face | Face }   side | front | side
EntryZone: parlour --> the door at the top of the stoop
Top      : Italianate, Stick --> a false front with a bracketed cornice
           Queen Anne       --> a front gable, and on a grand house a corner turret
Stoop    : the stair from the pavement to the parlour door
```

The date chooses the type -- **Italianate** to 1880 (slanted bays, segmental
hoods), **Stick** to 1888 (square bays, flat heads, sticks at the corners),
**Queen Anne** after (a gable, a turret, more glass) -- and the seed chooses
the paint.

Numbers are INFERRED round figures for the type (Alamo Square, the Mission),
not measured plates.
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
from buildings.solver.fitting import PlacedSlot, SlotKind
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

__all__ = ["VictorianSite", "victorian_type", "victorian_grammar", "derive_victorian", "generate_victorian"]

LOT = 7.62  # 25 ft


@dataclass(frozen=True)
class VictorianSite:
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float = LOT


def victorian_type(year: int) -> str:
    if year < 1880:
        return "italianate"
    if year < 1888:
        return "stick"
    return "queen_anne"


#: How much of the bay zone each angled face takes, as seen from the street:
#: a slanted bay at 45 degrees shows its sides at about 0.7 of their width, a
#: square bay only its corner boards.
_SIDE_SHARE = {"italianate": 0.2, "stick": 0.07, "queen_anne": 0.2}
_HEIGHTS = (2.1, 3.6, 3.3)  # raised basement, parlour floor, chamber floor
_BAY_ZONE = 0.55  # the bay's share of the front
_PAINTS = ("clapboard_sage", "clapboard_blue", "clapboard_cream", "clapboard_rose")


def _site(shape: Shape) -> VictorianSite:
    return shape.attr("site")


def _type(shape: Shape) -> str:
    return victorian_type(_site(shape).year)


def _slot(name: str, start: float, size: float) -> PlacedSlot:
    return PlacedSlot(name, SlotKind.REPEATING if name == "bay" else SlotKind.FLEXIBLE, start, size)


def _cells(zone: Shape, d: Derivation, widths: list[tuple[str, float, dict]]) -> None:
    x = zone.scope.x
    parts = []
    for i, (name, w, attrs) in enumerate(widths):
        parts.append(Part("Cell", w, f"x{i}", {"slot": _slot(name, x, w), **attrs}))
        x += w
    d.split(zone, X, parts)


# ===========================================================================
# Productions
# ===========================================================================


def _lot(lot: Shape, d: Derivation) -> None:
    """The house front, what crowns it, and the stoop up to the door."""
    h = math.fsum(_HEIGHTS)
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, h), "facade")
    kind = _type(lot)
    top_h = 1.6 if kind != "queen_anne" else 3.4
    turret = kind == "queen_anne" and _site(lot).klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND)
    bw = lot.scope.w * _BAY_ZONE
    # With a turret over the bay, the gable crowns only the entry side: the
    # asymmetry is the point of the type.
    gx = bw if turret else 0.0
    d.insert(lot, "Top", Scope(gx, h, lot.scope.w - gx, top_h), "top", {"kind": kind})
    if turret:
        d.insert(lot, "Turret", Scope(0.15, h - _HEIGHTS[2], bw - 0.3, _HEIGHTS[2] + 2.6 + 3.2), "turret")
    entry_x = lot.scope.w * _BAY_ZONE
    d.insert(lot, "Stoop", Scope(entry_x + 0.25, 0.0, lot.scope.w - entry_x - 0.5, _HEIGHTS[0]), "stoop")


def _facade(facade: Shape, d: Derivation) -> None:
    """Basement, parlour, chamber."""
    d.split(facade, Y, [Part("Storey", h, f"s{i}") for i, h in enumerate(_HEIGHTS)], id_base=facade.parent.id)


def _storey(storey: Shape, d: Derivation) -> None:
    """Every floor is cut the same way: the bay's zone and the entry's. A
    cornice crowns the bay on each floor it projects from."""
    w = storey.scope.w
    bay = w * _BAY_ZONE
    zone_bay, _zone_entry = d.split(storey, X, [Part("BayZone", bay, "bay_zone"), Part("EntryZone", w - bay, "entry")])
    if storey.attrs["role"] != "basement":
        s = zone_bay.scope
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - 0.32, s.w, 0.32), "bay_cornice", {"course_kind": "entablature"})


def _bay_zone(zone: Shape, d: Derivation) -> None:
    """Over the basement the bay projects: three faces, its angled sides as
    wide as the type makes them, a corner board at every arris."""
    w = zone.scope.w
    if zone.attr("role") == "basement":
        _cells(zone, d, [("end", w * 0.3, {}), ("bay", w * 0.4, {}), ("end", w * 0.3, {})])
        return
    side = w * _SIDE_SHARE[_type(zone)]
    _cells(zone, d, [("bay", side, {"face": "side"}), ("bay", w - 2 * side, {"face": "front"}), ("bay", side, {"face": "side"})])
    s = zone.scope
    for i, x in enumerate((s.x, s.x + side, s.x + w - side, s.x + w)):
        cw = 0.14
        d.insert(zone, "Column", Scope(min(max(x - cw / 2.0, s.x), s.x + w - cw), s.y, cw, s.h - 0.32), f"corner{i}", {"order": "corner_board"})


def _entry_zone(zone: Shape, d: Derivation) -> None:
    """The entry column: the door on the parlour floor, a window over it, a
    small window into the basement under the stoop."""
    w = zone.scope.w
    _cells(zone, d, [("end", 0.3, {}), ("bay", w - 0.6, {}), ("end", 0.3, {})])


def _top(top: Shape, d: Derivation) -> None:
    """A Queen Anne front ends in a gable with a window in it; the others in
    a false front, a parapet of boards over a bracketed cornice."""
    s = top.scope
    if top.attrs["kind"] == "queen_anne":
        w = min(s.w * 0.36, 1.8) if s.w > 5 else s.w * 0.5
        d.insert(top, "Storey", Scope(s.x + (s.w - w) / 2.0, s.y + 0.35, w, 1.9), "attic", {"role": "attic"})
        return
    d.insert(top, "Storey", s, "false_front", {"role": "parapet"})


def _turret(turret: Shape, d: Derivation) -> None:
    """A corner turret rises out of the bay through the chamber floor and a
    storey of its own, under a conical roof."""
    s = turret.scope
    d.insert(turret, "Storey", Scope(s.x, s.y + _HEIGHTS[2], s.w, 2.6), "storey", {"role": "turret"})


def _storey_extra(storey: Shape, d: Derivation) -> None:
    """A storey that is not one of the facade's three: the false front, the
    gable's attic, the turret's room."""
    role = storey.attrs["role"]
    s = storey.scope
    if role == "parapet":
        _cells(storey, d, [("end", s.w, {})])
        d.insert(storey, "Entablature", Scope(s.x, s.y, s.w, 0.5), "frieze", {"course_kind": "entablature"})
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 0.6), "cornice", {"cornice_ornament": "bracketed"})
        return
    w = s.w
    _cells(storey, d, [("end", w * 0.2, {}), ("bay", w * 0.6, {}), ("end", w * 0.2, {})])


def _storey_any(storey: Shape, d: Derivation) -> None:
    if storey.attrs["role"] in ("parapet", "attic", "turret"):
        _storey_extra(storey, d)
    else:
        _storey(storey, d)


# ===========================================================================
# Attribute rules
# ===========================================================================


def floor_and_paint(storey: Shape, rng: DecisionStream) -> Attrs:
    """Basement, parlour, chamber -- or the role a crowning storey was given --
    and one paint for the whole house, chosen by its seed."""
    role = storey.attrs.get("role") or ("basement", "parlour", "chamber")[storey.index]
    paint = _PAINTS[_site(storey).seed % len(_PAINTS)]
    return Attrs({"role": role, "wall_material": paint}, rule="victorian.roles.floor_and_paint")


def wall_where_nothing_opens(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Ends are boarded wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="victorian.base.wall")


def a_tall_sash(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Every face and every opening bay holds a tall sash: segmental-headed
    under a hood in the Italianate, flat in the Stick, flat with a big upper
    pane in the Queen Anne. The front face of a bay is wide enough for a pair."""
    if not is_bay(cell):
        return None
    kind = _type(cell)
    h = cell.scope.h
    role = cell.attr("role")
    if role == "basement":
        return Attrs({"opening_type": "window", "head": "flat", "light_width": cell.scope.w * 0.8, "sill": 0.8,
                      "light_height": 0.8, "surround_kind": "none", "keystone_present": False},
                     rule="victorian.base.basement_light")
    sill = 0.55 if role in ("parlour", "chamber") else 0.4
    head_gap = 0.55 if role in ("parlour", "chamber") else 0.35
    face = cell.attrs.get("face")
    # A sash is a sash: one window's width, wherever it stands; only the bay's
    # front face is wide enough to take a pair.
    width = min(cell.scope.w - 0.3, 1.1) if face != "front" else cell.scope.w - 0.45
    out = {"opening_type": "window", "head": "segmental" if kind == "italianate" else "flat",
           "light_width": max(0.3, width), "sill": sill, "light_height": h - sill - head_gap,
           "surround_kind": "moulded_architrave" if kind != "queen_anne" else "none",
           "keystone_present": kind == "italianate"}
    if face == "front" and cell.scope.w > 2.2:
        out.update({"lights": (1.0, 1.0), "divider": "Mullion", "divider_width": 0.16})
    return Attrs(out, rule="victorian.base.a_tall_sash")


def the_door_at_the_top_of_the_stoop(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The parlour floor's entry bay is the front door, under a transom."""
    if not is_bay(cell) or cell.attr("role") != "parlour" or cell.parent.label != "EntryZone":
        return None
    kind = _type(cell)
    return Attrs({"opening_type": "pedestrian_entrance", "head": "segmental" if kind == "italianate" else "flat",
                  "light_width": 1.1, "sill": 0.0, "light_height": cell.scope.h - 0.45, "lights": None},
                 rule="victorian.base.the_door_at_the_top_of_the_stoop", specificity=10)


def _light_bay(column: Shape, d: Derivation) -> None:
    from buildings.typologies.common.kit import split_light_bay_into_lights

    if column.parent.attrs.get("lights"):
        split_light_bay_into_lights(column, d)
    else:
        split_light_bay(column, d)


LAYERS = (Layer("base", 0, (wall_where_nothing_opens, a_tall_sash, the_door_at_the_top_of_the_stoop)),)


# ===========================================================================
# Interpretation
# ===========================================================================


def write_top(top: Shape, below, d) -> list:
    if top.attrs["kind"] != "queen_anne":
        return list(below)
    s = top.scope
    pts = ((s.x - (0.25 if s.x <= 0 else 0.0), s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.25, s.y))
    return [
        GableNode(id=top.id, kind="gable", trace=tuple(top.trace),
                  props={**{"x": s.x, "y": s.y, "w": s.w, "h": s.h}, "form": "front_gable", "points": pts,
                         "hoist_beam": None, "wall_material": _PAINTS[_site(top).seed % len(_PAINTS)]}),
        *below,
    ]


def write_turret(turret: Shape, below, d) -> list:
    s = turret.scope
    room = turret.children[0].scope
    y0 = room.y + room.h
    pts = ((s.x - 0.2, y0), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.2, y0))
    return [
        *below,
        GableNode(id=f"{turret.id}/roof", kind="gable", trace=tuple(turret.trace),
                  props={"x": s.x, "y": y0, "w": s.w, "h": s.y + s.h - y0, "form": "spire", "points": pts,
                         "hoist_beam": None, "wall_material": "shadow"}),
    ]


def write_stoop(stoop: Shape, below, d) -> list:
    """The stair up to the parlour door, drawn as its stepped profile."""
    s = stoop.scope
    n = 8
    pts = [(s.x, s.y)]
    for k in range(n):
        x = s.x + s.w * k / n
        y = s.y + s.h * (k + 1) / n
        pts += [(x, y), (x + s.w / n, y)]
    pts += [(s.x + s.w, s.y)]
    return [GableNode(id=stoop.id, kind="gable", trace=tuple(stoop.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "stoop", "points": tuple(pts),
                             "hoist_beam": None, "wall_material": "stone"})]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="victorian.victorian_type", phase="period",
                      detail=f"San Francisco {victorian_type(s.year)} row house, {s.year}, {s.klass.value}")


def victorian_grammar() -> Grammar:
    return Grammar(
        name="victorian",
        productions=(
            Production("victorian.lot", "Lot", _lot),
            Production("victorian.facade", "Facade", _facade),
            Production("victorian.storey", "Storey", _storey_any),
            Production("victorian.bay_zone", "BayZone", _bay_zone),
            Production("victorian.entry_zone", "EntryZone", _entry_zone),
            Production("victorian.top", "Top", _top),
            Production("victorian.turret", "Turret", _turret),
            Production("victorian.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("victorian.light_bay", "LightBay", _light_bay),
            Production("victorian.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (floor_and_paint,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Top": write_top,
            "Turret": write_turret,
            "Stoop": write_stoop,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        overhangs=frozenset({"Cornice"}),
    )


def derive_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = victorian_grammar() if refine is None else refine(victorian_grammar())
    return derive(grammar, Shape("Lot", Scope(0.0, 0.0, site.width, 30.0), "b", attrs={"site": site}), DecisionStream(site.seed))


def generate_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_victorian(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
