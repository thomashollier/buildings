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
from typing import Callable, Sequence

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
from buildings.ir.nodes import (
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
from buildings.site import BuildingClass
from buildings.solver.fitting import SlotKind, SlotSpec
from buildings.trace import TraceEntry, TraceLog
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
        float(r.first_upper) - i * r.taper for i in range(r.upper_storeys)
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
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, float(r.cornice_projection)), "cornice")
    if role == "top" and r.pitched_roof:
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, float(r.cornice_projection)), "cornice")
    if r.fire_escape and role != "base":
        bays = [c for c in cells if _is_bay(c)]
        if len(bays) >= 2:
            mid = len(bays) // 2
            left, right = bays[mid - 1], bays[mid]
            x0 = left.scope.x + left.scope.w * 0.08
            x1 = right.scope.x + right.scope.w * 0.92
            d.insert(storey, "FireEscape", Scope(x0, s.y, x1 - x0, _FIRE_ESCAPE_RAIL), "fire_escape")


def _cell(cell: Shape, d: Derivation) -> None:
    """A bay is cut into a jamb either side of a column of light."""
    a = cell.attrs
    width = min(a["light_width"], cell.scope.w - 0.10)
    jamb = (cell.scope.w - width) / 2.0
    d.split(
        cell,
        X,
        [Part("Jamb", jamb, "jamb_left"), Part("LightBay", width, "light_bay"), Part("Jamb", jamb, "jamb_right")],
    )


def _light_bay(column: Shape, d: Derivation) -> None:
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


def _light(light: Shape, d: Derivation) -> None:
    """The light carries its surround and its keystone."""
    a = light.attr("surround_kind"), light.attr("keystone_present")
    s = light.scope
    if a[0] not in (None, "none"):
        d.insert(light, "Surround", s, "surround")
    if a[1]:
        d.insert(light, "Keystone", Scope(s.x, s.y + s.h, s.w, 0.0), "keystone")


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


def _is_bay(cell: Shape) -> bool:
    slot = cell.attrs.get("slot")
    return cell.label == "Cell" and slot is not None and slot.name == "bay"


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


def _trace(shape: Shape, *keys: str) -> tuple[TraceEntry, ...]:
    """The rules that made this shape, then the ones that set what it shows."""
    out = list(shape.trace)
    cell = shape if shape.label == "Cell" else next(
        (a for a in _ancestors(shape) if a.label == "Cell"), None
    )
    res = cell.resolution if cell is not None else None
    for key in keys:
        win = res.winners.get(key) if res is not None else None
        if win is not None:
            out.append(
                TraceEntry(rule=win.rule, phase="qualification", detail=f"{key} = {win.value!r}")
            )
    return tuple(out)


def _ancestors(shape: Shape):
    node = shape.parent
    while node is not None:
        yield node
        node = node.parent


def _xywh(s: Scope) -> dict[str, float]:
    return {"x": s.x, "y": s.y, "w": s.w, "h": s.h}


def _bid(shape: Shape) -> str:
    cell = shape if shape.label == "Cell" else next(a for a in _ancestors(shape) if a.label == "Cell")
    return cell.id


def _write_light(light: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
    a = light.attr("opening_type"), light.attr("head")
    s = light.scope
    props: dict[str, object] = {**_xywh(s), "opening_type": a[0], "head": a[1]}
    if a[1] == "round":
        props["head_rise"] = s.w / 2.0
    if a[0] == "shop_bay":
        props["pane_max_span"] = 1.8
    return [OpeningNode(id=f"{_bid(light)}/opening", kind="opening", trace=_trace(light, "opening_type", "head"), props=props), *below]


def _write_surround(shape: Shape, below, d) -> list[Node]:
    return [
        SurroundNode(
            id=f"{_bid(shape)}/surround",
            kind="surround",
            trace=_trace(shape, "surround_kind"),
            props={**_xywh(shape.scope), "surround_kind": shape.attr("surround_kind"), "richness": 0.4},
        )
    ]


def _write_keystone(shape: Shape, below, d) -> list[Node]:
    return [
        KeystoneNode(
            id=f"{_bid(shape)}/keystone",
            kind="keystone",
            trace=_trace(shape, "keystone_present"),
            props={**_xywh(shape.scope), "keystone_kind": "plain"},
        )
    ]


def _write_shopfront(shape: Shape, below, d) -> list[Node]:
    return [
        ShopfrontNode(
            id=f"{_bid(shape)}/shopfront",
            kind="shopfront",
            trace=_trace(shape, "opening_type"),
            props={
                **_xywh(shape.scope),
                "shopfront_style": "cast_iron_larger_panes",
                "treatment": "cast_iron_larger_panes",
                "threshold_height": 0.45,
                "fascia_depth": 0.85,
            },
        )
    ]


_ORDER = ("opening", "shopfront", "surround", "keystone")


def _write_cell(cell: Shape, below: Sequence[Node], d) -> list[Node]:
    return [
        BayNode(
            id=cell.id,
            kind="bay",
            trace=_trace(cell, "opening_type"),
            children=tuple(sorted(below, key=lambda n: _ORDER.index(n.kind))),
            props={**_xywh(cell.scope), "slot_name": cell.attrs["slot"].name, "is_special": False},
        )
    ]


def _write_column(shape: Shape, below, d) -> list[Node]:
    return [
        ColumnNode(
            id=shape.id,
            kind="column",
            trace=tuple(shape.trace) + tuple(shape.parent.trace[:1]),
            props={**_xywh(shape.scope), "order": shape.attr("order")},
        )
    ]


def _write_entablature(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    return [
        StringCourseNode(
            id=shape.id,
            kind="string_course",
            trace=tuple(shape.trace),
            props={"x": s.x, "y": s.y + s.h, "w": s.w, "h": s.h, "course_kind": "entablature", "projection": s.h},
        )
    ]


def _write_cornice(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    r = _recipe(shape)
    return [
        CorniceNode(
            id=shape.id,
            kind="cornice",
            trace=tuple(shape.trace),
            props={
                **_xywh(s),
                "projection": s.h,
                "cornice_ornament": r.cornice_ornament,
                "ornament_count": max(3, round(s.w / 0.9) + 1),
            },
        )
    ]


def _write_fire_escape(shape: Shape, below, d) -> list[Node]:
    s = shape.scope
    return [
        BalconyNode(
            id=f"{shape.id}/platform",
            kind="balcony",
            trace=tuple(shape.trace),
            props={**_xywh(s), "continuous": False, "projection": 0.9, "bracket_count": 3},
        ),
        IronworkNode(
            id=f"{shape.id}/rail",
            kind="ironwork",
            trace=tuple(shape.trace),
            props={**_xywh(s), "guards": "balcon_filant", "max_gap": 0.11, "ornament_count": 2},
        ),
    ]


def _write_storey(storey: Shape, below: Sequence[Node], d) -> list[Node]:
    r = _recipe(storey)
    material = r.ground_material if storey.attrs["role"] == "base" else r.wall_material
    rails = [n for n in below if n.kind == "ironwork"]
    on_storey = [n for n in below if n.kind != "ironwork"]
    # Draw order: bays, then the lines and columns that stand in front of them.
    rank = {"bay": 0, "string_course": 1, "balcony": 2, "column": 3, "cornice": 4}
    node = StoreyNode(
        id=storey.id,
        kind="storey",
        trace=tuple(storey.trace),
        children=tuple(sorted(on_storey, key=lambda n: rank.get(n.kind, 9))),
        props={
            **_xywh(storey.scope),
            "role": storey.attrs["role"],
            "wall_material": material,
            "on_the_stone_facade": True,
        },
    )
    return [node, *rails]


def _write_roof(roof: Shape, below: Sequence[Node], d) -> list[Node]:
    s = roof.scope
    eaves, ridge = s.y, s.y + s.h
    run = s.h / math.tan(math.radians(40.0))
    return [
        RoofNode(
            id=roof.id,
            kind="roof",
            trace=tuple(roof.trace),
            props={**_xywh(s), "material": "slate", "seam_count": 6, "lower_angle_deg": 40.0, "upper_angle_deg": 40.0, "break_pct": 1.0},
        ),
        SilhouetteNode(
            id=f"{roof.id}/silhouette",
            kind="silhouette",
            trace=tuple(roof.trace),
            props={"x": 0.0, "y": 0.0, "w": s.w, "h": ridge, "eaves_height": eaves, "ridge_height": ridge, "points": ((0.0, eaves), (run, ridge))},
        ),
        *below,
    ]


def _write_dormer(shape: Shape, below, d) -> list[Node]:
    return [DormerNode(id=shape.id, kind="dormer", trace=tuple(shape.trace), props={**_xywh(shape.scope), "form": "pedimented"})]


def _write_chimney(shape: Shape, below, d) -> list[Node]:
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


def _write_lot(lot: Shape, below: Sequence[Node], d) -> list[Node]:
    site = _site(lot)
    r = _recipe(lot)
    facade = lot.children[0]
    eaves = facade.scope.h
    top = eaves + (_ROOF_RISE + _CHIMNEY[1] if r.pitched_roof else float(r.cornice_projection))
    return [
        BuildingNode(
            id=lot.id,
            kind="building",
            trace=tuple(lot.trace)
            + (
                TraceEntry(
                    rule="soho.recipes.recipe_for",
                    phase="structure",
                    detail=f"{r.name}: {site.lots} lot(s), {site.year}, {site.programme.value}, {site.klass.value}",
                ),
            ),
            children=tuple(below),
            props={"x": 0.0, "y": 0.0, "w": lot.scope.w, "h": top, "eaves_height": eaves, "year": site.year},
        )
    ]


# ===========================================================================
# The grammar
# ===========================================================================


def soho_grammar() -> Grammar:
    return Grammar(
        name="soho",
        productions=(
            Production("soho.lot", "Lot", _lot),
            Production("soho.facade", "Facade", _facade),
            Production("soho.storey", "Storey", _storey),
            Production("soho.cell", "Cell", _cell, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("soho.light_bay", "LightBay", _light_bay),
            Production("soho.light", "Light", _light),
            Production("soho.roof", "Roof", _roof),
        ),
        stages=(
            AttributeStage(
                "Storey",
                (
                    Layer("roles", 0, (the_stack_says_where_you_are,)),
                    Layer("class", 20, (iron_order_follows_money,)),
                ),
            ),
            AttributeStage("Cell", SOHO_LAYERS),
        ),
        interpreters={
            "Light": _write_light,
            "Surround": _write_surround,
            "Keystone": _write_keystone,
            "Shopfront": _write_shopfront,
            "Cell": _write_cell,
            "Column": _write_column,
            "Entablature": _write_entablature,
            "Cornice": _write_cornice,
            "FireEscape": _write_fire_escape,
            "Storey": _write_storey,
            "Roof": _write_roof,
            "Dormer": _write_dormer,
            "Chimney": _write_chimney,
            "Lot": _write_lot,
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
    log = TraceLog()

    def _walk(n: Node):
        yield n
        for c in n.children:
            yield from _walk(c)

    for node in _walk(root):
        for entry in node.trace:
            log.record(node.id, entry)
    return root, log
