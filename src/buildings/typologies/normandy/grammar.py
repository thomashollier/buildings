"""The Normandy half-timbered house as a split grammar.

*Colombage*: an oak frame whose members show on the face of the wall, the
panels between them filled with *torchis* (clay and straw) rendered ochre.
The signature is that **the frame is a grammar laid over the openings**:
posts at a fixed spacing across every storey, a post either side of every
window, the posts that would cross a window left out, a brace in each end
panel, and a Saint Andrew's cross in the breast under each upper window.
Two settings of the same grammar:

* **town** (Rouen, Honfleur, 15th-17th c.): narrow, three storeys, each
  storey **jettied** out past the one below on its joists, the gable to the
  street;
* **country** (Pays d'Auge, 16th-18th c.): long and low, posts close-set
  (*colombage serre*), a knee-wall loft, a steep thatched roof with dormers.

```
Lot      --> insert( Facade | Gable | Roof )
Facade   --> split(y){ Floor* }
Floor    --> insert( Storey ) as wide as its jetty allows
Storey   --> rhythm = fit(w){ end | bay* | end }  split(x){ Cell* }  Plate
Cell     : opening --> split(x){ Jamb | LightBay | Jamb }  Post* at the spacing, around the light
Cell     : wall    --> Post* and a Brace
LightBay --> split(y){ Breast | Light | Lintel }   Cross in the breast, upstairs
Gable    --> Storey (the loft), King post, Braces
```

Numbers are INFERRED round figures for the type, not measured plates.
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
from buildings.ir.nodes import BraceNode, BuildingNode, GableNode
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
    xywh,
)

__all__ = ["NormandySite", "normandy_grammar", "derive_normandy", "generate_normandy"]


@dataclass(frozen=True)
class NormandySite:
    setting: str  # "town" | "country"
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float | None = None

    @property
    def frontage(self) -> float:
        return self.width if self.width is not None else (6.2 if self.setting == "town" else 14.0)


_POST = 0.15  # INFERRED -- an oak post's face
_JETTY = 0.25  # INFERRED -- how far a jettied storey stands out past the one below
_PLATE = 0.18
#: Setting -> storey heights bottom-up, post spacing, bay band.
_SETTINGS = {
    "town": ((3.1, 2.8, 2.6), 0.55, (1.3, 1.6, 2.0)),
    "country": ((2.7, 1.3), 0.36, (1.8, 2.2, 2.8)),
}
_GABLE = 4.2  # INFERRED -- a 55-60 degree town gable over a 6 m front
_ROOF = 5.6  # INFERRED -- a thatched Pays d'Auge roof, about 60 degrees


def _site(shape: Shape) -> NormandySite:
    return shape.attr("site")


def _setting(shape: Shape) -> str:
    return _site(shape).setting


# ===========================================================================
# Productions
# ===========================================================================


def _lot(lot: Shape, d: Derivation) -> None:
    """The frame's storeys, and over them a gable to the street in town or a
    great thatched roof in the country."""
    heights, _spacing, _band = _SETTINGS[_setting(lot)]
    h = math.fsum(heights)
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, h), "facade")
    if _setting(lot) == "town":
        d.insert(lot, "Gable", Scope(0.0, h, lot.scope.w, _GABLE), "gable")
    else:
        d.insert(lot, "Roof", Scope(0.0, h, lot.scope.w, _ROOF), "roof", {"pitch": 60.0, "roof_material": "thatch", "dormer_form": "flat_lucarne"})


def _facade(facade: Shape, d: Derivation) -> None:
    """The storeys, bottom-up; in town each stands out past the one below."""
    heights, _s, _b = _SETTINGS[_setting(facade)]
    d.split(facade, Y, [Part("Floor", h, f"floor{i}") for i, h in enumerate(heights)])


def _floor(floor: Shape, d: Derivation) -> None:
    """A floor holds a storey as wide as its jetties allow: the top one the
    whole front, each one under it a jetty narrower on either side."""
    n = len([f for f in floor.siblings if f.label == "Floor"])
    inset = _JETTY * (n - 1 - floor.index) if _setting(floor) == "town" else 0.0
    s = floor.scope
    d.insert(floor, "Storey", Scope(s.x + inset, s.y, s.w - 2 * inset, s.h), "storey", {"floor_index": floor.index})


def _rhythm(width: float, band, d: Derivation):
    parts, _ = d.fit(
        width,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.45, 0.8, 1.6, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *band),
    )
    return parts


def _storey(storey: Shape, d: Derivation) -> None:
    """A storey is fitted with its own bays, framed top and bottom by plates;
    a jettied storey's sill beam shows its joist ends."""
    s = storey.scope
    _heights, _spacing, band = _SETTINGS[_setting(storey)]
    if storey.attrs.get("role") == "loft" and _setting(storey) == "town":
        band = (0.9, 1.2, 1.6)
    parts = _rhythm(s.w, band, d)
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(parts)])
    d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - _PLATE, s.w, _PLATE), "plate", {"course_kind": "timber_beam"})


def _posts(cell: Shape, d: Derivation, light: Scope | None) -> None:
    """Posts at the frame's spacing across the cell, a post either side of
    the light, and none across it."""
    s = cell.scope
    spacing = _SETTINGS[_setting(cell)][1]
    xs = []
    x = s.x
    while x < s.x + s.w - _POST * 0.5:
        if light is None or not (light.x - _POST < x < light.x + light.w):
            xs.append(x)
        x += spacing
    if light is not None:
        xs += [light.x - _POST, light.x + light.w]
    last = cell.index == len([c for c in cell.siblings if c.label == "Cell"]) - 1
    if last:
        xs.append(s.x + s.w - _POST)
    for i, px in enumerate(sorted(set(round(v, 6) for v in xs))):
        px = min(max(px, s.x), s.x + s.w - _POST)
        d.insert(cell, "Post", Scope(px, s.y, _POST, s.h - _PLATE), f"post{i}", {"order": "timber"})


def _framed_cell(cell: Shape, d: Derivation) -> None:
    """A cell with a window: the window's anatomy, then the frame around it."""
    split_cell_around_its_light(cell, d)
    _posts(cell, d, cell.children[1].scope)


def _frame_wall(cell: Shape, d: Derivation) -> None:
    """A cell with no window is all frame: posts, and a brace from the foot
    of the corner post up into the panel, mirrored at the two ends."""
    _posts(cell, d, None)
    s = cell.scope
    first = cell.index == 0
    w = min(s.w, 1.2)
    x = s.x if first else s.x + s.w - w
    d.insert(cell, "Brace", Scope(x, s.y, w, s.h - _PLATE), "brace", {"direction": "falling" if first else "rising"})


def _light_bay(column: Shape, d: Derivation) -> None:
    """Under an upstairs window the breast is filled with a Saint Andrew's cross."""
    split_light_bay(column, d)
    breast = column.children[0]
    if column.attr("role") != "ground" and breast.scope.h > 0.3:
        b = breast.scope
        d.insert(column, "Brace", b, "cross_up", {"direction": "rising"})
        d.insert(column, "Brace", b, "cross_down", {"direction": "falling"})


def _gable(gable: Shape, d: Derivation) -> None:
    """The town gable: a loft storey in it with a window, a king post up to
    the ridge and a brace each side of it."""
    s = gable.scope
    w = s.w * 0.42
    d.insert(gable, "Storey", Scope(s.x + (s.w - w) / 2.0, s.y, w, 1.9), "loft", {"role": "loft"})
    cx = s.x + s.w / 2.0
    d.insert(gable, "Post", Scope(cx - _POST / 2.0, s.y + 1.9, _POST, s.h * 0.55 - 1.9 + 1.0), "king_post", {"order": "timber"})
    d.insert(gable, "Brace", Scope(s.x + s.w * 0.12, s.y, s.w * 0.17, 1.9), "brace_left", {"direction": "rising"})
    d.insert(gable, "Brace", Scope(s.x + s.w * 0.71, s.y, s.w * 0.17, 1.9), "brace_right", {"direction": "falling"})


def _roof(roof: Shape, d: Derivation) -> None:
    """A thatched roof carries a dormer over every other window axis of the
    floor below, and a brick chimney at one end."""
    s = roof.scope
    facade = roof.parent.children[0]
    ground = facade.children[0].children[0]
    bays = [c for c in ground.children if is_bay(c)]
    for i, axis in enumerate(bays[::2]):
        cx = axis.scope.x + axis.scope.w / 2.0
        d.insert(roof, "Dormer", Scope(cx - 0.6, s.y + 0.4, 1.2, 1.7), f"dormer{i}")
    d.insert(roof, "Chimney", Scope(s.w * 0.78, s.y + s.h, 0.8, 1.2), "chimney")


# ===========================================================================
# Attribute rules
# ===========================================================================


def floor_role(storey: Shape, rng: DecisionStream) -> Attrs:
    """Ground, upper or loft, and ochre torchis between the timbers."""
    if storey.attrs.get("role") == "loft":
        return Attrs({"wall_material": "plaster_ochre"}, rule="normandy.roles.loft")
    i = storey.attrs.get("floor_index", 0)
    n_floors = len(_SETTINGS[_setting(storey)][0])
    role = "ground" if i == 0 else "loft" if (_setting(storey) == "country" and i == n_floors - 1) else "upper"
    return Attrs({"role": role, "wall_material": "plaster_ochre"}, rule="normandy.roles.floor_role")


def end_panels_are_frame(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The end panels are frame and infill."""
    if is_bay(cell):
        return None
    return Attrs({"opening_type": "none"}, rule="normandy.base.end_panels_are_frame")


def the_knee_wall_is_blind(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A country loft's knee wall has no windows: its light comes from the
    dormers. Narrower than a window between posts, so it wins."""
    if not (cell.attr("role") == "loft" and _setting(cell) == "country"):
        return None
    return Attrs({"opening_type": "none"}, rule="normandy.base.the_knee_wall_is_blind", specificity=10)


def a_window_between_posts(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A bay holds a casement between two posts, under the plate."""
    if not is_bay(cell):
        return None
    h = cell.scope.h
    role = cell.attr("role")
    sill = 0.9 if role != "loft" else 0.4
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": min(cell.scope.w * 0.55, 1.0), "sill": sill,
         "light_height": max(0.6, h - sill - 0.45 - _PLATE), "surround_kind": "none", "keystone_present": False},
        rule="normandy.base.a_window_between_posts",
    )


def the_door(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """On the ground floor one bay is the door: in town the shop's, at the
    side; in the country the house's, in the middle."""
    if not is_bay(cell) or cell.attr("role") != "ground":
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    door = bays[0] if _setting(cell) == "town" else bays[len(bays) // 2]
    if cell is not door:
        return None
    return Attrs(
        {"opening_type": "pedestrian_entrance", "head": "flat", "light_width": 0.95, "sill": 0.0,
         "light_height": min(2.2, cell.scope.h - 0.4)},
        rule="normandy.base.the_door",
        specificity=10,
    )


def the_shop_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A town house's ground floor is a shop: wide openings between the posts."""
    if not is_bay(cell) or cell.attr("role") != "ground" or _setting(cell) != "town":
        return None
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "light_width": cell.scope.w * 0.8, "sill": 0.6, "light_height": h - 0.6 - 0.55},
        rule="normandy.base.the_shop_window",
        specificity=5,
    )


LAYERS = (Layer("base", 0, (end_panels_are_frame, the_knee_wall_is_blind, a_window_between_posts, the_door, the_shop_window)),)


# ===========================================================================
# Interpretation
# ===========================================================================


def write_brace(shape: Shape, below, d) -> list:
    return [BraceNode(id=shape.id, kind="brace", trace=tuple(shape.trace), props={**xywh(shape.scope), "direction": shape.attrs["direction"]})]


def write_gable(gable: Shape, below, d) -> list:
    s = gable.scope
    pts = ((s.x - 0.3, s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.3, s.y))
    return [
        GableNode(id=gable.id, kind="gable", trace=tuple(gable.trace),
                  props={**xywh(s), "form": "front_gable", "points": pts, "hoist_beam": None, "wall_material": "plaster_ochre"}),
        *below,
    ]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="normandy.colombage", phase="structure", detail=f"Normandy half-timbered house, {s.setting}, {s.frontage:.1f} m, {s.year}")


def normandy_grammar() -> Grammar:
    return Grammar(
        name="normandy",
        productions=(
            Production("normandy.lot", "Lot", _lot),
            Production("normandy.facade", "Facade", _facade),
            Production("normandy.floor", "Floor", _floor),
            Production("normandy.storey", "Storey", _storey),
            Production("normandy.framed_cell", "Cell", _framed_cell, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("normandy.frame_wall", "Cell", _frame_wall, guard=lambda c: c.attrs["opening_type"] == "none"),
            Production("normandy.light_bay", "LightBay", _light_bay),
            Production("normandy.light", "Light", dress_the_light),
            Production("normandy.gable", "Gable", _gable),
            Production("normandy.roof", "Roof", _roof),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (floor_role,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Post": INTERPRETERS["Column"],
            "Brace": write_brace,
            "Gable": write_gable,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        overhangs=frozenset({"Chimney"}),
    )


def derive_normandy(site: NormandySite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = normandy_grammar() if refine is None else refine(normandy_grammar())
    return derive(grammar, Shape("Lot", Scope(0.0, 0.0, site.frontage, 30.0), "b", attrs={"site": site}), DecisionStream(site.seed))


def generate_normandy(site: NormandySite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_normandy(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
