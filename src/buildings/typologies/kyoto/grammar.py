"""The Kyoto machiya as a split grammar.

A merchant's townhouse on a narrow, very deep lot, taxed by its frontage like
an Amsterdam house, but the answer is horizontal rather than vertical: two
storeys, the upper one **low** (the *zushi-nikai*, a storage loft), a **pent
roof** (*hisashi*) running the width of the front between them, and the
ground floor screened by **koshi** lattices of close-set timber slats. The
upper floor looks out through **mushiko-mado**, slatted windows set in
plaster.

```
Lot      --> insert( Facade | Roof )
Facade   --> rhythm = fit(w){ end | bay* | end }   split(y){ Ground | Loft }
Ground   --> split(x){ Cell* }   Hisashi           the pent roof at its head
Cell     : ground --> a light screened by a koshi; one bay is the sliding door
Cell     : loft   --> a mushiko window, a low slatted opening in the plaster
Light    --> Lattice                               the screen over the light
```

The new move is the **Lattice**: a screen inserted over a light, so the
opening stays an opening (it lets light and air through) while what the
street sees is timber. Change the slat rhythm and nothing else moves.

Numbers are INFERRED round figures for the Meiji-era stock (Sanjo, Nishijin).
"""

from __future__ import annotations

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
from buildings.ir.nodes import BuildingNode, IronworkNode
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
    trace_of,
    write_lot,
    xywh,
)

__all__ = ["MachiyaSite", "kyoto_grammar", "derive_kyoto", "generate_kyoto"]


@dataclass(frozen=True)
class MachiyaSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


_GROUND = 3.1
_LOFT = 2.05  # the low upper storey: a loft, not a floor to live on
_ROOF_RISE = 1.7
_BAY = (1.5, 1.8, 2.1)  # INFERRED -- about one ken between posts
_END = (0.2, 0.3, 0.5)


def _site(shape: Shape) -> MachiyaSite:
    return shape.attr("site")


def _lot(lot: Shape, d: Derivation) -> None:
    """A two-storey front and a tiled roof over it."""
    h = _GROUND + _LOFT
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, h), "facade")
    d.insert(lot, "Roof", Scope(0.0, h, lot.scope.w, _ROOF_RISE), "roof")


def _facade(facade: Shape, d: Derivation) -> None:
    """The posts are fitted once, a ken apart; then the ground and the loft."""
    parts, _ = d.fit(
        facade.scope.w,
        "Cell",
        end=SlotSpec("end", SlotKind.FLEXIBLE, *_END, elasticity=2.0),
        bay=SlotSpec("bay", SlotKind.REPEATING, *_BAY),
    )
    facade.attrs["rhythm"] = parts
    d.split(facade, Y, [Part("Storey", _GROUND, "s0"), Part("Storey", _LOFT, "s1")], id_base=facade.parent.id)


def _storey(storey: Shape, d: Derivation) -> None:
    """A storey is cut at the posts; a tiled pent roof runs along the head of
    the ground floor, and another at the eaves of the loft."""
    d.split(storey, X, [Part("Cell", p.size, f"x{i}", p.attrs) for i, p in enumerate(storey.attr("rhythm"))])
    s = storey.scope
    d.insert(storey, "Cornice", Scope(s.x, s.y + s.h, s.w, 0.9 if storey.index == 0 else 0.7), "hisashi", {"cornice_ornament": "tiled"})


def _light(light: Shape, d: Derivation) -> None:
    """A light on a machiya front is screened: a koshi on the ground floor, a
    mushiko on the loft."""
    dress_the_light(light, d)
    if light.attr("screen_gap", None):
        d.insert(light, "Lattice", light.scope, "lattice")


# ===========================================================================
# Attribute rules
# ===========================================================================


def ground_and_loft(storey: Shape, rng: DecisionStream) -> Attrs:
    """The ground floor is timber, the loft over it plaster."""
    ground = storey.index == 0
    return Attrs(
        {"role": "base" if ground else "loft", "wall_material": "timber_dark" if ground else "plaster_white"},
        rule="kyoto.roles.ground_and_loft",
    )


def end_posts_are_wall(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The end posts are wall."""
    return None if is_bay(cell) else Attrs({"opening_type": "none"}, rule="kyoto.base.end_posts_are_wall")


def a_koshi_between_posts(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """On the ground floor each bay between posts is open, behind a koshi of
    slats a hand apart."""
    if not is_bay(cell) or cell.parent.index != 0:
        return None
    h = cell.scope.h
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w - 0.12, "sill": 0.35,
         "light_height": h - 0.35 - 0.45, "surround_kind": "none", "keystone_present": False, "screen_gap": 0.055},
        rule="kyoto.base.a_koshi_between_posts",
    )


def the_mushiko_window(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """The loft looks out through low slatted windows set in the plaster: one
    to a bay, wide and short, under the eaves."""
    if not is_bay(cell) or cell.parent.index != 1:
        return None
    return Attrs(
        {"opening_type": "window", "head": "flat", "light_width": cell.scope.w * 0.7, "sill": 0.6,
         "light_height": 0.75, "surround_kind": "none", "keystone_present": False, "screen_gap": 0.09},
        rule="kyoto.base.the_mushiko_window",
    )


def the_sliding_door(cell: Shape, rng: DecisionStream) -> Attrs | None:
    """One bay at the side is the door into the passage that runs through the
    house to the back: a sliding timber door, unscreened."""
    if not is_bay(cell) or cell.parent.index != 0:
        return None
    if cell is not [c for c in cell.siblings if is_bay(c)][-1]:
        return None
    return Attrs(
        {"opening_type": "pedestrian_entrance", "head": "flat", "light_width": cell.scope.w - 0.25, "sill": 0.0,
         "light_height": cell.scope.h - 0.5, "screen_gap": None},
        rule="kyoto.base.the_sliding_door",
        specificity=10,
    )


LAYERS = (Layer("base", 0, (end_posts_are_wall, a_koshi_between_posts, the_mushiko_window, the_sliding_door)),)


def write_lattice(shape: Shape, below, d) -> list:
    return [
        IronworkNode(
            id=f"{shape.parent.parent.parent.id}/ironwork",
            kind="ironwork",
            trace=trace_of(shape, "screen_gap"),
            props={**xywh(shape.scope), "guards": "opening", "ironwork_pattern": "timber_lattice",
                   "max_gap": shape.attr("screen_gap"), "ornament_count": 2},
        )
    ]


def _describe(lot: Shape) -> TraceEntry:
    s = _site(lot)
    return TraceEntry(rule="kyoto.machiya", phase="structure", detail=f"machiya, {s.width:.1f} m frontage, {s.year}")


def kyoto_grammar() -> Grammar:
    return Grammar(
        name="kyoto",
        productions=(
            Production("kyoto.lot", "Lot", _lot),
            Production("kyoto.facade", "Facade", _facade),
            Production("kyoto.storey", "Storey", _storey),
            Production("kyoto.cell", "Cell", split_cell_around_its_light, guard=lambda c: c.attrs["opening_type"] != "none"),
            Production("kyoto.light_bay", "LightBay", split_light_bay),
            Production("kyoto.light", "Light", _light),
        ),
        stages=(
            AttributeStage("Storey", (Layer("roles", 0, (ground_and_loft,)),)),
            AttributeStage("Cell", LAYERS),
        ),
        interpreters={
            **INTERPRETERS,
            "Lattice": write_lattice,
            "Lot": write_lot(_describe, lambda lot: {"year": _site(lot).year}),
        },
        overhangs=frozenset({"Cornice"}),
    )


def derive_kyoto(site: MachiyaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    grammar = kyoto_grammar() if refine is None else refine(kyoto_grammar())
    return derive(grammar, Shape("Lot", Scope(0.0, 0.0, site.width, 20.0), "b", attrs={"site": site}), DecisionStream(site.seed))


def generate_kyoto(site: MachiyaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    lot, derivation = derive_kyoto(site, refine=refine)
    (root,) = interpret(lot, derivation)
    return root, log_of(root)
