"""The Amsterdam canal house as a split grammar.

A narrow, deep, tall brick house on a canal lot, taxed by its frontage, so it
is three bays wide at most and grows up instead. Its signature is the top:
the street front does not stop at a cornice but rises into a **gable that is a
grammar of its own** -- tiers that narrow as they climb, each holding fewer
windows, and an outline whose shape tells its date:

```
Lot      --> insert( Facade | Gable )
Facade   --> rhythm = fit(width){ end | bay* | end }   split(y){ Storey* }
Storey   --> split(x){ Cell* }
Gable    : form by date -- step (to 1640), neck (to 1720), bell (to 1790), none after
Gable    --> split(y){ GableTier* | Crown }
GableTier--> insert( Storey ) narrower than the tier below, its own fit of bays
Crown    : the hoisting beam, at the apex
```

The outline is the gable's own interpreter: it reads the tiers the grammar
placed and draws the steps, the claw-piece scrolls of a neck gable or the
S-curve shoulders of a bell gable around them. Change the outline and no
window moves; change a tier and the outline follows it.

Numbers are INFERRED from the surviving canal-house stock (Herengracht,
Keizersgracht), round figures, not measured plates.
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
from buildings.ir.nodes import BuildingNode, GableNode, Node
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

__all__ = ["CanalSite", "gable_form", "amsterdam_grammar", "derive_amsterdam", "generate_amsterdam"]


@dataclass(frozen=True)
class CanalSite:
    width: float  # metres of canal frontage
    year: int
    klass: BuildingClass
    seed: int = 0


_BAY = (1.45, 1.75, 2.15)  # INFERRED -- a tall cross-window and its pier
_END = (0.35, 0.55, 0.9)
_SHARE = 0.62  # INFERRED -- a brick front with big windows: light for a deep house
_GROUND = 3.7  # INFERRED -- a raised ground floor over a half-basement
_FIRST = 3.3
_TAPER = 0.93
_UPPERS = 3


def gable_form(year: int) -> str:
    """The gable's outline follows fashion, and fashion follows the date."""
    if year < 1640:
        return "step"
    if year < 1720:
        return "neck"
    if year < 1790:
        return "bell"
    return "straight"


#: Per form: (height, width as a share of the frontage) for each tier, and the
#: crown over the last one. INFERRED.
_TIERS = {
    "step": ([(2.6, 0.80), (2.4, 0.56), (2.1, 0.32)], 0.0),
    "neck": ([(2.8, 0.56), (2.3, 0.44)], 1.2),
    "bell": ([(3.0, 0.52)], 1.6),
    "straight": ([], 0.0),
}


def _site(shape: Shape) -> CanalSite:
    return shape.attr("site")


# ===========================================================================
# Productions
# ===========================================================================


def _rhythm(width: float, d: Derivation, min_bays: int = 1, *, gable: bool = False):
    """The bays a width holds. A gable tier may squeeze its piers and bays
    harder than the facade under it: it is a loft, not a reception room."""
    end, bay = ((0.2, 0.45, 0.9), (1.2, 1.75, 2.15)) if gable else (_END, _BAY)
    parts, _ = d.fit(
        width,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *end, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *bay),
        min_bays=min_bays,
        max_bays=3,
    )
    return parts


def _lot(lot: Shape, d: Derivation) -> None:
    """A facade on the lot and, unless the date has put a cornice there, a
    gable on the facade."""
    heights = [_GROUND] + [_FIRST * _TAPER**i for i in range(_UPPERS)]
    lot.attrs["storey_heights"] = heights
    facade_h = math.fsum(heights)
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, facade_h), "facade")
    form = gable_form(_site(lot).year)
    tiers, crown = _TIERS[form]
    if tiers:
        h = math.fsum(t for t, _ in tiers) + crown
        d.insert(lot, "Gable", Scope(0.0, facade_h, lot.scope.w, h), "gable", {"form": form})


def _facade(facade: Shape, d: Derivation) -> None:
    """Three bays at most, fitted once; then the storeys."""
    facade.attrs["rhythm"] = _rhythm(facade.scope.w, d, min_bays=2)
    d.split(
        facade,
        Y,
        [Part("Storey", h, f"s{i}") for i, h in enumerate(facade.attr("storey_heights"))],
        id_base=facade.parent.id,
    )


def _storey(storey: Shape, d: Derivation) -> None:
    """A storey is cut by its rhythm; the top storey of a house with no gable
    carries the cornice."""
    rhythm = storey.attrs.get("rhythm") or storey.attr("rhythm")
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(rhythm)])
    s = storey.scope
    if storey.attrs["role"] == "top" and gable_form(_site(storey).year) == "straight":
        d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 0.6), "cornice", {"cornice_ornament": "modillioned"})


def _gable(gable: Shape, d: Derivation) -> None:
    """The gable is cut into its tiers, bottom-up, and the crown over them."""
    tiers, crown = _TIERS[gable.attrs["form"]]
    parts = [Part("GableTier", h, f"tier{i}", {"share": w}) for i, (h, w) in enumerate(tiers)]
    if crown:
        parts.append(Part("Crown", crown, "crown"))
    d.split(gable, Y, parts)


def _gable_tier(tier: Shape, d: Derivation) -> None:
    """Each tier holds a storey narrower than the one below, centred, with as
    many windows as its own width fits."""
    s = tier.scope
    w = s.w * tier.attrs["share"]
    x = s.x + (s.w - w) / 2.0
    d.insert(
        tier,
        "Storey",
        Scope(x, s.y, w, s.h),
        "storey",
        {"role": "gable", "rhythm": _rhythm(w, d, gable=True)},
    )


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_stack_says_where_you_are(storey: Shape, rng: DecisionStream) -> Attrs | None:
    """Base at the bottom, top at the top, upper between. A gable storey
    already knows what it is."""
    if "role" in storey.attrs:
        return None
    n = len(storey.siblings)
    role = "base" if storey.index == 0 else "top" if storey.index == n - 1 else "upper"
    return Attrs({"role": role}, rule="amsterdam.roles.position_in_the_stack")


def brick(storey: Shape, rng: DecisionStream) -> Attrs:
    """The whole front is the same dark brick, gable and all."""
    return Attrs({"wall_material": "brick_dark"}, rule="amsterdam.base.brick")


def _storey_of(cell: Shape) -> Shape:
    return cell.parent


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The ends of the frontage are wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="amsterdam.base.end_piers_are_wall")


def a_bay_holds_a_tall_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Every bay holds a tall window under a stone lintel: a deep house is lit
    from its two ends, so the front is as much glass as brick can carry."""
    if not is_bay(cell):
        return None
    h = cell.scope.h
    sill = 0.55 if _storey_of(cell).attrs["role"] != "gable" else 0.45
    return Attrs(
        {
            "opening_type": "window",
            "head": "flat",
            "light_width": _SHARE * cell.scope.w,
            "sill": sill,
            "light_height": h - sill - 0.45,
            "surround_kind": "moulded_architrave",
            "keystone_present": False,
        },
        rule="amsterdam.base.a_bay_holds_a_tall_window",
    )


def the_door_up_the_stoop(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The door is in the bay beside the stair down to the street, up a stoop
    over the half-basement, under a transom light."""
    storey = _storey_of(cell)
    if storey.attrs["role"] != "base" or not is_bay(cell):
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    if cell is not bays[0]:
        return None
    h = cell.scope.h
    return Attrs(
        {
            "opening_type": "pedestrian_entrance",
            "head": "flat",
            "light_width": 1.05,
            "sill": 0.45,
            "light_height": h - 0.45 - 0.35,
        },
        rule="amsterdam.base.the_door_up_the_stoop",
        specificity=10,
    )


def the_attic_hatch(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The top tier of a gable is the loft, and its middle opening is the
    hatch goods are hoisted through: a door in the air, not a window."""
    storey = _storey_of(cell)
    if storey.attrs["role"] != "gable" or not is_bay(cell):
        return None
    tier = storey.parent
    if tier.index != len([s for s in tier.siblings if s.label == "GableTier"]) - 1:
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    if cell is not bays[len(bays) // 2]:
        return None
    h = cell.scope.h
    return Attrs(
        {"opening_type": "pedestrian_entrance", "light_height": h - 0.45 - 0.25, "head": "flat"},
        rule="amsterdam.base.the_attic_hatch",
        specificity=10,
    )


LAYERS = (Layer("base", 0, (end_piers_are_wall, a_bay_holds_a_tall_window, the_door_up_the_stoop, the_attic_hatch)),)


# ===========================================================================
# Interpretation: the gable's outline
# ===========================================================================


def _curve(x0, y0, x1, y1, profile, steps=10):
    return [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * profile(i / steps)) for i in range(1, steps + 1)]


def _outline(gable: Shape) -> tuple[list[tuple[float, float]], tuple[float, float]]:
    """The left half of the outline, eaves to apex, from the tiers as placed;
    and the hoisting beam's foot."""
    form = gable.attrs["form"]
    tiers = [c for c in gable.children if c.label == "GableTier"]
    storeys = [c.children[0] for c in tiers]
    crown = next((c for c in gable.children if c.label == "Crown"), None)
    g = gable.scope
    cx = g.x + g.w / 2.0
    pts: list[tuple[float, float]] = [(g.x, g.y)]
    if form == "step":
        for st in storeys:
            pts += [(st.scope.x, pts[-1][1]), (st.scope.x, st.scope.y + st.scope.h)]
        top = storeys[-1].scope
        apex_y = top.y + top.h
        pts.append((cx, apex_y))
        return pts, (cx, apex_y - 0.75)
    first = storeys[0].scope
    if form == "neck":
        # A claw piece: a concave scroll from the eaves up into the neck.
        pts += _curve(g.x, g.y, first.x, g.y + first.h * 0.8, lambda t: math.sin(t * math.pi / 2.0))
        for st in storeys:
            pts += [(st.scope.x, max(pts[-1][1], st.scope.y)), (st.scope.x, st.scope.y + st.scope.h)]
        top = storeys[-1].scope.y + storeys[-1].scope.h
        apex = top + crown.scope.h
        pts += [(storeys[-1].scope.x - 0.12, top), (cx, apex)]
        return pts, (cx, top - 0.1)
    # bell: an S-curve shoulder, then a segmental crown.
    pts += _curve(g.x, g.y, first.x, first.y + first.h * 0.85, lambda t: 0.5 - 0.5 * math.cos(math.pi * t))
    top = first.y + first.h
    pts.append((first.x, top))
    rise = crown.scope.h
    half = first.w / 2.0
    pts += [(cx - half * math.cos(a), top + rise * math.sin(a)) for a in (math.pi * i / 16 for i in range(1, 9))]
    return pts, (cx, top + 0.1)


def write_gable(gable: Shape, below, d) -> list[Node]:
    left, beam = _outline(gable)
    cx = gable.scope.x + gable.scope.w / 2.0
    right = [(2 * cx - x, y) for x, y in reversed(left[:-1])]
    return [
        GableNode(
            id=gable.id,
            kind="gable",
            trace=tuple(gable.trace)
            + (TraceEntry(rule="amsterdam.gable_form", phase="period", detail=f"form = {gable.attrs['form']!r}"),),
            props={
                **{"x": gable.scope.x, "y": gable.scope.y, "w": gable.scope.w, "h": gable.scope.h},
                "form": gable.attrs["form"],
                "points": tuple(left + right),
                "hoist_beam": beam,
                "wall_material": "brick_dark",
            },
        ),
        *below,
    ]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(
        rule="amsterdam.canal_house",
        phase="structure",
        detail=f"canal house, {s.width:.1f} m frontage, {s.year}, {gable_form(s.year)} gable",
    )


def amsterdam_grammar() -> Grammar:
    return Grammar(
        name="amsterdam",
        productions=(
            Production("amsterdam.lot", "Lot", _lot),
            Production("amsterdam.facade", "Facade", _facade),
            Production("amsterdam.storey", "Storey", _storey),
            Production("amsterdam.gable", "Gable", _gable),
            Production("amsterdam.gable_tier", "GableTier", _gable_tier),
            Production("amsterdam.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("amsterdam.light_bay", "LightBay", split_light_bay),
            Production("amsterdam.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (the_stack_says_where_you_are, brick)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Gable": write_gable,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        overhangs=frozenset({"Cornice"}),
    )


def derive_amsterdam(site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = amsterdam_grammar() if refine is None else refine(amsterdam_grammar())
    axiom = Shape("Lot", Scope(0.0, 0.0, site.width, 40.0), "b", attrs={"site": site})
    return derive(grammar, axiom, DecisionStream(site.seed))


def generate_amsterdam(
    site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_amsterdam(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
