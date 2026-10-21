"""The facade kit: productions and interpreters any facade grammar can reuse.

Everything here reads only a shape's scope and the attributes a style's
rules put on it, never a style's own recipe, so one copy serves SoHo,
Amsterdam, Venice and Chicago. A style supplies the rules (what a bay holds,
how tall a storey is, which storeys get which material) and its signature
productions; the kit supplies the common anatomy of a window and the writing
of IR.

The attributes the kit reads, by label:

* ``Storey``: ``role``, ``wall_material``.
* ``Cell``: ``slot`` (the fitted slot), ``opening_type``, ``head``,
  ``light_width``, ``sill``, ``light_height``, ``surround_kind``,
  ``keystone_present``.
* ``Cornice``: ``cornice_ornament``. ``Entablature``: ``course_kind``.
* ``Column``: ``order``. ``Gable``: ``points``, ``form``, ``hoist_beam``.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

from buildings.cga import Attrs, Derivation, Part, Scope, Shape, X, Y
from buildings.ir.nodes import (
    GableNode,
    BalconyNode,
    BayNode,
    BuildingNode,
    ColumnNode,
    CorniceNode,
    DormerNode,
    IronworkNode,
    KeystoneNode,
    Node,
    OpeningNode,
    RoofNode,
    ShopfrontNode,
    SilhouetteNode,
    SpecialNode,
    StoreyNode,
    StringCourseNode,
    SurroundNode,
)
from buildings.rng import DecisionStream
from buildings.trace import TraceEntry, TraceLog

__all__ = [
    "is_bay",
    "role_from_the_stack",
    "split_cell_around_its_light",
    "split_light_bay",
    "split_light_bay_into_lights",
    "dress_the_light",
    "INTERPRETERS",
    "write_lot",
    "trace_of",
    "log_of",
]


# ===========================================================================
# Reading the tree
# ===========================================================================


def is_bay(shape: Shape) -> bool:
    slot = shape.attrs.get("slot")
    return shape.label == "Cell" and slot is not None and slot.name == "bay"


def ancestors(shape: Shape):
    node = shape.parent
    while node is not None:
        yield node
        node = node.parent


def cell_of(shape: Shape) -> Shape | None:
    if shape.label == "Cell":
        return shape
    return next((a for a in ancestors(shape) if a.label == "Cell"), None)


def trace_of(shape: Shape, *keys: str) -> tuple[TraceEntry, ...]:
    """The rules that made this shape, then the ones that set what it shows."""
    out = list(shape.trace)
    cell = cell_of(shape)
    res = cell.resolution if cell is not None else None
    for key in keys:
        win = res.winners.get(key) if res is not None else None
        if win is not None:
            out.append(TraceEntry(rule=win.rule, phase="qualification", detail=f"{key} = {win.value!r}"))
    return tuple(out)


def xywh(s: Scope) -> dict[str, float]:
    return {"x": s.x, "y": s.y, "w": s.w, "h": s.h}


def _bid(shape: Shape) -> str:
    cell = cell_of(shape)
    return cell.id if cell is not None else shape.id


def _element_id(shape: Shape, name: str) -> str:
    """``<cell>/<name>``, numbered by its light where a cell holds several."""
    light = shape if shape.label == "Light" else shape.parent
    index = light.attrs.get("lights_index") if light is not None else None
    return f"{_bid(shape)}/{name}" if index is None else f"{_bid(shape)}/{name}{index}"


# ===========================================================================
# Rules and productions
# ===========================================================================


def role_from_the_stack(rule: str) -> Callable[[Shape, DecisionStream], Attrs]:
    """Base at the bottom, top at the top, upper between: read off the siblings."""

    def position_in_the_stack(storey: Shape, rng: DecisionStream) -> Attrs:
        """Base at the bottom, top at the top, upper between: read off the siblings."""
        n = len(storey.siblings)
        role = "base" if storey.index == 0 else "top" if storey.index == n - 1 else "upper"
        return Attrs({"role": role}, rule=rule)

    return position_in_the_stack


def split_cell_around_its_light(cell: Shape, d: Derivation) -> None:
    """A bay is cut into a jamb either side of a column of light."""
    a = cell.attrs
    width = min(a["light_width"], cell.scope.w - 0.10)
    jamb = (cell.scope.w - width) / 2.0
    d.split(
        cell,
        X,
        [Part("Jamb", jamb, "jamb_left"), Part("LightBay", width, "light_bay"), Part("Jamb", jamb, "jamb_right")],
    )


def split_light_bay(column: Shape, d: Derivation) -> None:
    """The column of light is cut into breast, light and lintel; a store front
    stands in it on the ground floor."""
    a = column.parent.attrs
    h = column.scope.h
    sill = a["sill"]
    light_h = min(a["light_height"], h - sill)
    d.split(
        column,
        Y,
        [
            Part("Breast", sill, "breast"),
            Part("Light", light_h, "light"),
            Part("Lintel", h - sill - light_h, "lintel"),
        ],
    )
    if a["opening_type"] == "shop_bay":
        d.insert(column, "Shopfront", column.scope, "shopfront")


def split_light_bay_into_lights(column: Shape, d: Derivation) -> None:
    """A column of light holding several lights side by side -- a Chicago
    window, a Gothic polifora: breast, arcade, lintel, and the arcade cut into
    lights with a divider between each pair."""
    a = column.parent.attrs
    h = column.scope.h
    sill = a["sill"]
    light_h = min(a["light_height"], h - sill)
    _breast, arcade, _lintel = d.split(
        column,
        Y,
        [
            Part("Breast", sill, "breast"),
            Part("Arcade", light_h, "arcade"),
            Part("Lintel", h - sill - light_h, "lintel"),
        ],
    )
    fractions = a["lights"]
    divider = a.get("divider_width", 0.12)
    n = len(fractions)
    glass = arcade.scope.w - divider * (n - 1)
    parts: list[Part] = []
    for i, f in enumerate(fractions):
        if i:
            parts.append(Part(a.get("divider", "Mullion"), divider, f"divider{i}"))
        parts.append(Part("Light", glass * f / sum(fractions), f"light{i}", {"lights_index": i}))
    d.split(arcade, X, parts)


def dress_the_light(light: Shape, d: Derivation) -> None:
    """The light carries its surround and its keystone."""
    s = light.scope
    if light.attr("surround_kind") not in (None, "none"):
        d.insert(light, "Surround", s, "surround")
    if light.attr("keystone_present"):
        d.insert(light, "Keystone", Scope(s.x, s.y + s.h, s.w, 0.0), "keystone")


# ===========================================================================
# Interpreters
# ===========================================================================


def write_light(light: Shape, below: Sequence[Node], d) -> list[Node]:
    kind, head = light.attr("opening_type"), light.attr("head")
    s = light.scope
    props: dict[str, object] = {**xywh(s), "opening_type": kind, "head": head}
    if head == "round":
        props["head_rise"] = s.w / 2.0
    elif head == "ogee":
        props["head_rise"] = s.w * 0.75
    if kind == "shop_bay":
        props["pane_max_span"] = 1.8
    return [
        OpeningNode(id=_element_id(light, "opening"), kind="opening", trace=trace_of(light, "opening_type", "head"), props=props),
        *below,
    ]


def write_surround(shape: Shape, below, d) -> list[Node]:
    return [
        SurroundNode(
            id=_element_id(shape, "surround"),
            kind="surround",
            trace=trace_of(shape, "surround_kind"),
            props={**xywh(shape.scope), "surround_kind": shape.attr("surround_kind"), "richness": 0.4},
        )
    ]


def write_keystone(shape: Shape, below, d) -> list[Node]:
    return [
        KeystoneNode(
            id=_element_id(shape, "keystone"),
            kind="keystone",
            trace=trace_of(shape, "keystone_present"),
            props={**xywh(shape.scope), "keystone_kind": "plain"},
        )
    ]


def write_shopfront(shape: Shape, below, d) -> list[Node]:
    return [
        ShopfrontNode(
            id=f"{_bid(shape)}/shopfront",
            kind="shopfront",
            trace=trace_of(shape, "opening_type"),
            props={
                **xywh(shape.scope),
                "shopfront_style": "cast_iron_larger_panes",
                "treatment": "cast_iron_larger_panes",
                "threshold_height": 0.45,
                "fascia_depth": 0.85,
            },
        )
    ]


_BAY_ORDER = ("opening", "shopfront", "surround", "keystone", "balcony", "ironwork")


def write_cell(cell: Shape, below: Sequence[Node], d) -> list[Node]:
    # A colonnette between two lights stands on the storey, like any column;
    # everything else belongs to the bay.
    columns = [n for n in below if n.kind in ("column", "brace")]
    own = [n for n in below if n.kind not in ("column", "brace")]
    return [
        BayNode(
            id=cell.id,
            kind="bay",
            trace=trace_of(cell, "opening_type"),
            children=tuple(sorted(own, key=lambda n: (_BAY_ORDER.index(n.kind), n.id))),
            props={**xywh(cell.scope), "slot_name": cell.attrs["slot"].name, "is_special": False},
        ),
        *columns,
    ]


def write_column(shape: Shape, below, d) -> list[Node]:
    return [
        ColumnNode(
            id=shape.id,
            kind="column",
            trace=tuple(shape.trace) + tuple(shape.parent.trace[:1]),
            props={**xywh(shape.scope), "order": shape.attr("order"),
                   **{k: shape.attrs[k] for k in ("louvre_paint", "paint", "cap_h", "base_h") if k in shape.attrs}},
        )
    ]


def write_entablature(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    return [
        StringCourseNode(
            id=shape.id,
            kind="string_course",
            trace=tuple(shape.trace),
            props={
                "x": s.x,
                "y": s.y + s.h,
                "w": s.w,
                "h": s.h,
                "course_kind": shape.attr("course_kind", "entablature"),
                "projection": s.h,
                "ornament_count": max(2, round(s.w / 0.5)),
            },
        )
    ]


def write_cornice(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    return [
        CorniceNode(
            id=shape.id,
            kind="cornice",
            trace=tuple(shape.trace),
            props={
                **xywh(s),
                "projection": s.h,
                "cornice_ornament": shape.attrs["cornice_ornament"],
                "ornament_count": max(3, round(s.w / 0.9) + 1),
            },
        )
    ]


def write_balcony_with_rail(shape: Shape, below, d) -> list[Node]:
    """A projecting platform and the rail on it: a fire escape, a balconette,
    a loggia's balustrade."""
    s = shape.scope
    return [
        BalconyNode(
            id=f"{shape.id}/platform",
            kind="balcony",
            trace=tuple(shape.trace),
            props={**xywh(s), "continuous": False, "projection": 0.9, "bracket_count": 3},
        ),
        IronworkNode(
            id=f"{shape.id}/rail",
            kind="ironwork",
            trace=tuple(shape.trace),
            props={**xywh(s), "guards": "balcon_filant", "max_gap": 0.11, "ornament_count": 2},
        ),
    ]


def write_storey(storey: Shape, below: Sequence[Node], d) -> list[Node]:
    """A storey and what stands on it. Rails go up to the building, which is
    where the renderer draws railings that are not part of one bay."""
    rails = [n for n in below if n.kind == "ironwork"]
    on_storey = [n for n in below if n.kind != "ironwork"]
    # Draw order: bays, then the lines and columns that stand in front of them.
    rank = {"bay": 0, "string_course": 1, "balcony": 2, "column": 3, "brace": 3, "cornice": 4}
    node = StoreyNode(
        id=storey.id,
        kind="storey",
        trace=tuple(storey.trace),
        children=tuple(sorted(on_storey, key=lambda n: rank.get(n.kind, 9))),
        props={
            **xywh(storey.scope),
            "role": storey.attrs["role"],
            "wall_material": storey.attr("wall_material"),
            "on_the_stone_facade": True,
        },
    )
    return [node, *rails]


def write_roof(roof: Shape, below: Sequence[Node], d) -> list[Node]:
    """A pitched roof seen from the street: one slope from eaves to ridge."""
    s = roof.scope
    eaves, ridge = s.y, s.y + s.h
    pitch = float(roof.attr("pitch", 40.0))
    # A mansard states its two slopes and where the brisis breaks; a plain
    # roof states one pitch and no break.
    lower = float(roof.attr("lower_pitch", pitch))
    upper = float(roof.attr("upper_pitch", pitch))
    brk = float(roof.attr("break_pct", 1.0))
    if brk < 0.995:
        bh = s.h * brk
        x1 = bh / math.tan(math.radians(lower))
        points = ((0.0, eaves), (x1, eaves + bh), (x1 + (s.h - bh) / math.tan(math.radians(upper)), ridge))
    else:
        points = ((0.0, eaves), (s.h / math.tan(math.radians(pitch)), ridge))
    return [
        RoofNode(
            id=roof.id,
            kind="roof",
            trace=tuple(roof.trace),
            props={**xywh(s), "material": roof.attr("roof_material", "slate"), "seam_count": 6, "lower_angle_deg": lower, "upper_angle_deg": upper, "break_pct": brk},
        ),
        SilhouetteNode(
            id=f"{roof.id}/silhouette",
            kind="silhouette",
            trace=tuple(roof.trace),
            props={"x": 0.0, "y": 0.0, "w": s.w, "h": ridge, "eaves_height": eaves, "ridge_height": ridge, "points": points},
        ),
        *below,
    ]


def write_dormer(shape: Shape, below, d) -> list[Node]:
    return [
        DormerNode(
            id=shape.id,
            kind="dormer",
            trace=tuple(shape.trace),
            props={**xywh(shape.scope), "form": shape.attr("dormer_form", "pedimented")},
        )
    ]


def write_chimney(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    # A stack starts inside the roof and stands clear of the ridge.
    return [
        SpecialNode(
            id=shape.id,
            kind="special",
            trace=tuple(shape.trace),
            props={"x": s.x, "y": s.y - 1.2, "w": s.w, "h": s.h + 1.2, "element": "chimney_stack"},
        )
    ]


def _walk(n: Node):
    yield n
    for c in n.children:
        yield from _walk(c)


def write_lot(
    describe: Callable[[Shape], TraceEntry], props: Callable[[Shape], dict] | None = None
):
    """The building node: everything below it, its extent the highest thing
    any of it reaches, and an entry saying which type the situation chose."""

    def write(lot: Shape, below: Sequence[Node], d) -> list[Node]:
        facade = lot.children[0]
        top = max(
            float(n.props["y"]) + float(n.props["h"])
            for top_node in below
            for n in _walk(top_node)
            if "y" in n.props and "h" in n.props and n.kind not in ("silhouette", "building")
        )
        return [
            BuildingNode(
                id=lot.id,
                kind="building",
                trace=tuple(lot.trace) + (describe(lot),),
                children=tuple(below),
                props={
                    "x": 0.0,
                    "y": 0.0,
                    "w": lot.scope.w,
                    "h": top,
                    "eaves_height": facade.scope.h,
                    **(props(lot) if props is not None else {}),
                },
            )
        ]

    return write


def write_stoop(stoop: Shape, below, d) -> list:
    """The stair up to a raised front door, drawn as its stepped profile."""
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


INTERPRETERS = {
    "Light": write_light,
    "Surround": write_surround,
    "Keystone": write_keystone,
    "Shopfront": write_shopfront,
    "Cell": write_cell,
    "Column": write_column,
    "Entablature": write_entablature,
    "Cornice": write_cornice,
    "FireEscape": write_balcony_with_rail,
    "Balconette": write_balcony_with_rail,
    "Storey": write_storey,
    "Roof": write_roof,
    "Dormer": write_dormer,
    "Chimney": write_chimney,
    "Stoop": write_stoop,
}


def log_of(root: Node) -> TraceLog:
    log = TraceLog()
    for node in _walk(root):
        for entry in node.trace:
            log.record(node.id, entry)
    return log
