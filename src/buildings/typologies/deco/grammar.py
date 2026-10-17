"""The New York Art Deco setback tower as a split grammar.

The purest case in this repository of a style that *is* a regulation. The
1916 Zoning Resolution let a building rise straight up from the street line
only to a multiple of the street's width; above that it had to stay behind a
sloping **sky-exposure plane**, stepping back as it climbed; and once its
floor plate was down to a quarter of the lot it could rise without limit. The
"wedding cake" is what that law looks like built:

```
Lot      --> split(y){ Tier* | Crown }      the tiers are the law, worked out below
Tier     --> insert( Mass ) narrower than the tier below, centred
Mass     --> rhythm = fit(w){ end | bay* | end }   split(y){ Storey* }   Pier*
Storey   --> split(x){ Cell* }
Cell     --> paired windows over a dark spandrel
Crown    --> Spire
```

How the tiers come out of the law (``tiers_for``): the street wall rises to
``district x street width``; every tier above it is set back on each side by
``rise / plane``; tiers keep stepping until the mass is no wider than half
the frontage (a quarter of a square lot), and that width rises as the tower,
as tall as the money goes. Change the street width and the whole massing
moves; nobody chose a setback.

Numbers are INFERRED round figures; the district multiplier and plane ratio
are the shape of the 1916 rules, simplified to one district.
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
from buildings.quantity import Reg
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

__all__ = ["TowerSite", "tiers_for", "deco_grammar", "derive_deco", "generate_deco"]


@dataclass(frozen=True)
class TowerSite:
    width: float  # frontage, metres
    street_width: float
    year: int
    klass: BuildingClass
    seed: int = 0


DISTRICT = Reg(1.5, "Zoning Resolution 1916 -- a 1.5-times height district (simplified)")
PLANE = Reg(4.0, "Zoning Resolution 1916 -- the sky-exposure plane, rise per unit of setback (simplified)")
TOWER_SHARE = Reg(0.5, "Zoning Resolution 1916 -- a tower over 25% of the lot, half of a square frontage")
_STOREY = 3.7
_GROUND = 5.4
_TIER_FLOORS = 3
_PIER = 0.55


def _tower_floors(site: TowerSite) -> int:
    return {BuildingClass.MODEST: 6, BuildingClass.ORDINARY: 10, BuildingClass.COMFORTABLE: 14, BuildingClass.GRAND: 20}[site.klass]


def tiers_for(site: TowerSite) -> list[tuple[str, int, float]]:
    """The massing the law leaves: ``(role, floors, width)`` bottom-up."""
    wall_h = float(DISTRICT) * site.street_width
    base_floors = max(2, 1 + int((wall_h - _GROUND) // _STOREY))
    tiers = [("street_wall", base_floors, site.width)]
    width = site.width
    while True:
        width -= 2.0 * (_TIER_FLOORS * _STOREY) / float(PLANE)
        if width <= float(TOWER_SHARE) * site.width:
            break
        tiers.append(("setback", _TIER_FLOORS, width))
    # Once a step would take the mass under the quarter-lot, the tower takes
    # exactly what the law allows and rises.
    tower_w = min(tiers[-1][2], float(TOWER_SHARE) * site.width)
    tiers.append(("tower", _tower_floors(site), tower_w))
    tiers.append(("crown", 2, tower_w * 0.72))
    tiers.append(("crown", 2, tower_w * 0.48))
    return tiers


def _site(shape: Shape) -> TowerSite:
    return shape.attr("site")


def _lot(lot: Shape, d: Derivation) -> None:
    """The lot is cut into the tiers the zoning envelope leaves, and a spire."""
    parts = []
    for i, (role, floors, width) in enumerate(tiers_for(_site(lot))):
        h = floors * _STOREY + (_GROUND - _STOREY if i == 0 else 0.0)
        parts.append(Part("Tier", h, f"tier{i}", {"tier_role": role, "floors": floors, "mass_w": width}))
    used = math.fsum(p.size for p in parts)
    parts.append(Part("Crown", 9.0, "spire"))
    parts.append(Part("Sky", lot.scope.h - used - 9.0, "sky"))
    d.split(lot, Y, parts)


def _tier(tier: Shape, d: Derivation) -> None:
    """Each tier stands a mass as wide as the law allows, centred."""
    w = tier.attrs["mass_w"]
    s = tier.scope
    d.insert(tier, "Mass", Scope(s.x + (s.w - w) / 2.0, s.y, w, s.h), "mass")


def _mass(mass: Shape, d: Derivation) -> None:
    """A mass is fitted with bays, cut into floors, and has a pier stood on
    every frame line, its full height."""
    parts, _ = d.fit(
        mass.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, 0.5, 0.9, 1.6, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, 2.6, 3.1, 3.6),
    )
    mass.attrs["rhythm"] = parts
    tier = mass.parent
    floors = tier.attrs["floors"]
    heights = [_STOREY] * floors
    if tier.index == 0:
        heights[0] = _GROUND
    d.split(mass, Y, [Part("Storey", h, f"s{i}") for i, h in enumerate(heights)], id_base=f"{mass.parent.id}")
    x, edges = mass.scope.x, []
    for p in parts:
        edges.append((x, x + p.size, p.attrs["slot"].name))
        x += p.size
    lines = [e[1] for e, f in zip(edges, edges[1:]) if e[2] == "bay" and f[2] == "bay"]
    y0 = mass.scope.y + (_GROUND if tier.index == 0 else 0.0)
    for i, cx in enumerate(lines):
        d.insert(mass, "Pier", Scope(cx - _PIER / 2.0, y0, _PIER, mass.scope.y + mass.scope.h - y0), f"pier{i}", {"order": "pilaster"})


def _storey(storey: Shape, d: Derivation) -> None:
    """A floor is cut by its mass's rhythm; the top floor of each tier is
    capped with a coping where the next tier steps back."""
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(storey.attr("rhythm"))])
    if storey.index == len([x for x in storey.siblings if x.label == "Storey"]) - 1:
        s = storey.scope
        d.insert(storey, "Entablature", Scope(s.x, s.y + s.h - 0.45, s.w, 0.45), "coping", {"course_kind": "entablature"})


def _light_bay(column: Shape, d: Derivation) -> None:
    if column.parent.attrs.get("lights"):
        split_light_bay_into_lights(column, d)
    else:
        split_light_bay(column, d)


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_tier_says_what_you_are(storey: Shape, rng: DecisionStream) -> Attrs:
    """A floor takes its tier's role; the shop floor at the bottom is stone."""
    tier = storey.ancestor("Tier")
    ground = tier.index == 0 and storey.index == 0
    return Attrs(
        {"role": "base" if ground else tier.attrs["tier_role"], "wall_material": "stone" if ground else "brick_buff"},
        rule="deco.roles.the_tier_says_what_you_are",
    )


def end_piers_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """Corners are wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="deco.base.end_piers_are_wall")


def paired_windows_over_a_spandrel(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """A bay holds a pair of windows; under them a dark spandrel, so the piers
    read as the only continuous lines on the front."""
    if not is_bay(cell):
        return None
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w - _PIER - 0.2, "sill": 0.95,
         "light_height": h - 0.95 - 0.45, "lights": (1.0, 1.0), "divider": "Mullion", "divider_width": 0.18,
         "surround_kind": "none", "keystone_present": False},
        rule="deco.base.paired_windows_over_a_spandrel",
    )


def shops_and_the_lobby(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The street floor is shops, and its middle bay the lobby door."""
    storey = cell.parent
    if not is_bay(cell) or storey.attrs.get("role") != "base":
        return None
    bays = [c for c in cell.siblings if is_bay(c)]
    h = cell.scope.h
    if cell is bays[len(bays) // 2]:
        return Attrs(
            {"opening_type": "pedestrian_entrance", "head": "flat", "light_width": 2.2, "sill": 0.0,
             "light_height": h - 1.0, "lights": None, "surround_kind": "moulded_architrave"},
            rule="deco.base.the_lobby_door",
            specificity=20,
        )
    return Attrs(
        {"opening_type": "shop_bay", "head": "flat", "light_width": cell.scope.w - 0.5, "sill": 0.45,
         "light_height": h - 0.45 - 1.0, "lights": None},
        rule="deco.base.shops_on_the_street",
        specificity=10,
    )


LAYERS = (Layer("base", 0, (end_piers_are_wall, paired_windows_over_a_spandrel, shops_and_the_lobby)),)


def write_spire(crown: Shape, below, d) -> list:
    """The spire stands on the last tier's mass, as wide as a third of it."""
    top_tier = [t for t in crown.siblings if t.label == "Tier"][-1]
    mass = top_tier.children[0].scope
    cx = mass.x + mass.w / 2.0
    half = mass.w * 0.18
    y0 = crown.scope.y
    pts = ((cx - half, y0), (cx - half * 0.5, y0 + 2.5), (cx, y0 + crown.scope.h), (cx + half * 0.5, y0 + 2.5), (cx + half, y0))
    return [
        GableNode(
            id=crown.id,
            kind="gable",
            trace=tuple(crown.trace),
            props={"x": cx - half, "y": y0, "w": 2 * half, "h": crown.scope.h, "form": "spire", "points": pts,
                   "hoist_beam": None, "wall_material": "stucco"},
        )
    ]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    tiers = tiers_for(s)
    return TraceEntry(
        rule="deco.tiers_for",
        phase="regulation",
        detail=(
            f"setback tower on a {s.street_width:.0f} m street: street wall "
            f"{float(DISTRICT) * s.street_width:.1f} m ({DISTRICT.why}), "
            f"{sum(1 for t in tiers if t[0] == 'setback')} setback tier(s) on a 1:{float(PLANE):g} plane, "
            f"tower {tiers[-3][2]:.1f} m wide x {tiers[-3][1]} floors"
        ),
    )


def deco_grammar() -> Grammar:
    return Grammar(
        name="deco",
        productions=(
            Production("deco.lot", "Lot", _lot),
            Production("deco.tier", "Tier", _tier),
            Production("deco.mass", "Mass", _mass),
            Production("deco.storey", "Storey", _storey),
            Production("deco.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("deco.light_bay", "LightBay", _light_bay),
            Production("deco.light", "Light", dress_the_light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (the_tier_says_what_you_are,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Pier": INTERPRETERS["Column"],
            "Crown": write_spire,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
    )


def _axiom(site: TowerSite) -> Shape:
    return Shape("Lot", Scope(0.0, 0.0, site.width, 260.0), "b", attrs={"site": site})


def derive_deco(site: TowerSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = deco_grammar() if refine is None else refine(deco_grammar())
    return derive(grammar, _axiom(site), DecisionStream(site.seed))


def generate_deco(site: TowerSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_deco(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
