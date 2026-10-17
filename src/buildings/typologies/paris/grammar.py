"""The Paris immeuble as a split grammar.

The same building ``generate`` produces, derived as a tree of shapes by the
generic engine in ``buildings.cga`` instead of by a fixed pipeline:

```
Lot      --> paris.lot.envelope     insert( Facade | Roof )
Facade   --> paris.facade.storeys   split(y){ Storey* }
Storey   :  roles from the stack    (attribute stage, reads its siblings)
Storey   :  !within_comble
         --> paris.storey.bays      split(x){ Cell* }     -- the facade's one rhythm
Cell     :  base, period, class, site, override layers   (attribute stage)
Roof     :  terminal; interpreted by the termination phase
```

What moved and what did not
---------------------------
The grammar is the *shape* of the building: what is split into what, which
rules give which shape its properties, and what each shape writes into the
IR. The *sizes* still come from the Paris arithmetic in ``structure.py`` --
the decree's height steps, the class's ambition, the entresol, the garrets,
the bay solve with its entrance placement -- called once by the Lot rule as
its size function. That arithmetic is Paris law, not pipeline, and it is the
next thing to turn into declared split specs; see ``dev/CGA.md``.

Everything the old phases did *between* those numbers now happens here:

* **Roles** are an attribute stage on Storey whose single rule reads the
  shape's siblings -- the context query an L-system would express as a signal
  up and down the stack. Nothing numbers a floor.
* **Qualification** is an attribute stage on Cell running the unchanged
  rule layers, resolved by the engine's layering (later layer wins,
  specificity breaks ties, a tie raises).
* **Emission** is interpretation: each label's interpreter writes the nodes
  ``compose`` used to write in one long loop, by calling the same functions.

The acceptance bar is ``dev/harness/cga_equivalence.py``: on the fuzzer's
3000 situations the IR below the root is identical to the pipeline's.
"""

from __future__ import annotations

import dataclasses
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
from buildings.ir.nodes import BuildingNode, Node
from buildings.rng import DecisionStream
from buildings.site import SiteContext
from buildings.solver.fitting import PlacedSlot
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.paris.compose import (
    BAY_ELEMENT_ORDER,
    _assert_one_entrance,
    _storey_inside_the_comble,
    balconette_present,
    building_props,
    emit_balconette,
    emit_bay_node,
    emit_keystone,
    emit_opening,
    emit_rail,
    emit_shopfront,
    emit_storey,
    emit_storey_elements,
    emit_surround,
    keystone_present,
    on_the_filant,
    opening_geometry,
    opening_present,
    paris_layers,
    qualification_entry,
    rail_present,
    rail_rect,
    resolve,
    shopfront_present,
    surround_present,
)
from buildings.typologies.paris.generate import _roles_entries, _structure_entries, walk
from buildings.typologies.paris.qualify.context import QualContext, contexts_for
from buildings.typologies.paris.reglement import compute_envelope, era_for_year
from buildings.typologies.paris.roles import (
    Role,
    RoledGrid,
    RoledStorey,
    _find_mezzanine,
    _find_principal,
    _rank_anchor,
)
from buildings.typologies.paris.structure import solve_structure
from buildings.typologies.paris.terminate import terminate

__all__ = ["paris_grammar", "derive_paris", "generate_cga"]


# ===========================================================================
# Reading the tree
# ===========================================================================


def _slot(shape: Shape, axis: str) -> PlacedSlot:
    """The shape's run along ``axis``, as the slot the Paris functions read.

    Position and size are the SHAPE's -- the split put it there -- and only the
    slot's name and kind are carried from the size function, because those are
    what the part was called, not where it went."""
    named: PlacedSlot = shape.attrs["slot"]
    return PlacedSlot(
        name=named.name,
        kind=named.kind,
        start=shape.scope.start(axis),
        width=shape.scope.extent(axis),
        is_special=named.is_special,
    )


def _roled_storey(storey: Shape) -> RoledStorey:
    return RoledStorey(
        slot=_slot(storey, Y),
        role=storey.attrs["role"],
        rank_from_principal=storey.attrs["rank_from_principal"],
        index_from_bottom=storey.attrs["index_from_bottom"],
        index_from_top=storey.attrs["index_from_top"],
    )


def _roled_grid(facade: Shape) -> RoledGrid:
    """The roled stack, read off the Facade's Storey children."""
    grid = facade.attr("grid")
    return RoledGrid(
        storeys=tuple(_roled_storey(s) for s in facade.children),
        bays=tuple(grid.bays),
        grid=grid,
    )


class _Facts:
    """Per-derivation memo of what the whole facade knows once its storeys are
    roled: the roled grid and the context of every cell. Computed on first
    use, after the Facade split has attributed every Storey."""

    def __init__(self, site: SiteContext) -> None:
        self.site = site
        self._roled: dict[str, RoledGrid] = {}
        self._cells: dict[str, tuple[tuple[QualContext, ...], ...]] = {}

    def roled(self, facade: Shape) -> RoledGrid:
        if facade.id not in self._roled:
            self._roled[facade.id] = _roled_grid(facade)
        return self._roled[facade.id]

    def cells(self, facade: Shape) -> tuple[tuple[QualContext, ...], ...]:
        if facade.id not in self._cells:
            self._cells[facade.id] = contexts_for(self.roled(facade), self.site)
        return self._cells[facade.id]

    def context(self, storey: Shape, column: int) -> QualContext:
        return self.cells(storey.ancestor("Facade"))[storey.index][column]


# ===========================================================================
# Productions
# ===========================================================================


def _lot_envelope(lot: Shape, d: Derivation) -> None:
    """The legal solid is solved for its storeys and bays, and a facade and a
    roof are stood inside it."""
    grid = solve_structure(lot.attr("site"), lot.attr("datums"))
    lot.attrs["grid"] = grid
    facade_h = math.fsum(s.width for s in grid.storeys)
    d.insert(lot, "Facade", Scope(0.0, 0.0, lot.scope.w, facade_h), "facade")
    d.insert(
        lot,
        "Roof",
        Scope(0.0, grid.built_height, lot.scope.w, grid.comble_height),
        "roof",
    )


def _facade_storeys(facade: Shape, d: Derivation) -> None:
    """The facade is cut into storeys bottom-up, garrets included: a storey in
    the comble is a floor of the building even where it is not one of the
    stone face."""
    grid = facade.attr("grid")
    parts = [Part("Storey", s.width, f"s{i}", {"slot": s}) for i, s in enumerate(grid.storeys)]
    d.split(facade, Y, parts, id_base=facade.parent.id)


def _storey_bays(storey: Shape, d: Derivation) -> None:
    """A stone storey is cut by the facade's one rhythm, so every opening
    stands on the axis of the one below it."""
    grid = storey.attr("grid")
    parts = [Part("Cell", b.width, f"x{i}", {"slot": b}) for i, b in enumerate(grid.bays)]
    d.split(storey, X, parts)


# --- inside a cell -----------------------------------------------------------
#
# A cell is refined into its masonry and its light, and each thing applied to
# the light is a shape of its own. Presence is decided by the production that
# inserts the shape (reading the cell's resolved properties); what the shape
# looks like is decided by its own interpreter, which sees its own scope and
# nothing it does not name. So the rule for a keystone and the drawing of a
# keystone both live on Keystone, and a change to either cannot move a window.
#
#   Cell     : opening   --> split(x){ offset: Pier | width: LightBay | rest: Pier }
#   Cell     : blind     --> Surround? Keystone?          (on the cell itself)
#   Cell     : filant    --> Rail                          (the bay's run of balustrade)
#   LightBay             --> split(y){ sill: Breast | height: Light | rest: Lintel }
#                            Shopfront? Balconette?
#   Light                --> Surround? Keystone? Rail?     (garde-corps / barre d'appui)


def _cell(shape: Shape) -> Shape:
    return shape if shape.label == "Cell" else shape.ancestor("Cell")


def _rect(scope: Scope) -> tuple[float, float, float, float]:
    return (scope.x, scope.y, scope.w, scope.h)


def _cell_light(cell: Shape, d: Derivation) -> None:
    """A cell with an opening is cut into a pier either side of a column of
    light, at the offset and width qualification resolved for it."""
    res = cell.resolution
    offset_x, width, _sill, _height, _ = opening_geometry(_slot(cell, X), cell.scope.h, res)
    rest = cell.scope.w - offset_x - width
    d.split(
        cell,
        X,
        [
            Part("Pier", offset_x, "pier_left"),
            Part("LightBay", width, "light_bay"),
            Part("Pier", rest, "pier_right"),
        ],
    )
    _cell_balustrade(cell, d)


def _cell_blind(cell: Shape, d: Derivation) -> None:
    """A cell with no opening is wall; what is applied to it is applied to the
    whole cell."""
    res = cell.resolution
    if surround_present(res):
        d.insert(cell, "Surround", cell.scope, "surround")
    if keystone_present(res):
        s = cell.scope
        d.insert(cell, "Keystone", Scope(s.x, s.y + s.h, s.w, 0.0), "keystone")
    _cell_balustrade(cell, d)


def _cell_balustrade(cell: Shape, d: Derivation) -> None:
    """On a balcon filant, this cell's length of the balustrade runs the whole
    bay, piers included, because the slab in front of them does."""
    res = cell.resolution
    if rail_present(res) and on_the_filant(res):
        rect = rail_rect(_slot(cell, X), cell.scope.y, _rect(cell.scope), res)
        d.insert(cell, "Rail", Scope(*rect), "balustrade")


def _light_bay(column: Shape, d: Derivation) -> None:
    """The column of light is cut into the breast wall under the sill, the
    light, and the lintel over it; a shopfront and a balconette stand in it."""
    cell = _cell(column)
    res = cell.resolution
    _offset_x, _width, sill, height, _ = opening_geometry(_slot(cell, X), cell.scope.h, res)
    d.split(
        column,
        Y,
        [
            Part("Breast", sill, "breast"),
            Part("Light", height, "light"),
            Part("Lintel", column.scope.h - sill - height, "lintel"),
        ],
    )
    if shopfront_present(res):
        d.insert(column, "Shopfront", column.scope, "shopfront")
    if balconette_present(res):
        s = column.scope
        rail_h = float(res.get("balcony_rail_height", 0.0) or 0.0)
        d.insert(column, "Balconette", Scope(s.x, s.y, s.w, rail_h), "balconette")


def _light(light: Shape, d: Derivation) -> None:
    """What the light carries: its architrave, its keystone, and the railing
    across it."""
    res = _cell(light).resolution
    s = light.scope
    if surround_present(res):
        d.insert(light, "Surround", s, "surround")
    if keystone_present(res):
        d.insert(light, "Keystone", Scope(s.x, s.y + s.h, s.w, 0.0), "keystone")
    if rail_present(res) and not on_the_filant(res):
        cell = _cell(light)
        rect = rail_rect(_slot(cell, X), cell.scope.y, _rect(s), res)
        d.insert(light, "Rail", Scope(*rect), "rail")


# ===========================================================================
# Attribute rules
# ===========================================================================


def the_stack_says_who_you_are(storey: Shape, rng: DecisionStream) -> Attrs:
    """A storey's role is read off its siblings: base at the bottom, mezzanine
    if the slot over it is markedly shorter than what stands above, principal if
    it is uniquely the tallest habitable slot over those two, attic inside the
    roof, upper otherwise -- and its rank is its distance from the principal."""
    grid = storey.attr("grid")
    stack = storey.siblings
    slots = tuple(_slot(s, Y) for s in stack)
    n = len(slots)
    in_roof = [grid.stands_in_the_roof(i) for i in range(n)]
    mezzanine = _find_mezzanine(slots, in_roof)
    principal = _find_principal(slots, 0, mezzanine, in_roof)
    anchor = principal if principal is not None else _rank_anchor(slots, 0, mezzanine, in_roof)
    i = storey.index
    if i == 0:
        role = Role.BASE
    elif i == mezzanine:
        role = Role.MEZZANINE
    elif i == principal:
        role = Role.PRINCIPAL
    elif in_roof[i]:
        role = Role.ATTIC
    else:
        role = Role.UPPER
    return Attrs(
        values={
            "role": role,
            "rank_from_principal": i - anchor if anchor is not None else 0,
            "index_from_bottom": i,
            "index_from_top": n - 1 - i,
            "within_comble": in_roof[i],
        },
        rule="paris.roles.assign_roles",
    )


# ===========================================================================
# Interpretation
# ===========================================================================


def _ingredients(facts: _Facts, shape: Shape):
    """What every cell element is written from: the cell's id, slot, storey
    band, resolution and context."""
    cell = _cell(shape)
    storey = cell.parent
    return (
        cell.id,
        _slot(cell, X),
        storey.scope.y,
        storey.scope.h,
        cell.resolution,
        facts.context(storey, cell.index),
    )


def _interpret_light(facts: _Facts):
    def write(light: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, bay, y, h, res, ctx = _ingredients(facts, light)
        return [emit_opening(bid, bay, y, h, res, ctx), *below]

    return write


def _interpret_shopfront(facts: _Facts):
    def write(shape: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, bay, y, h, res, ctx = _ingredients(facts, shape)
        s_res = _cell(shape).parent.children[0].resolution
        return [emit_shopfront(bid, bay, y, h, res, ctx, s_res)]

    return write


def _interpret_surround(facts: _Facts):
    def write(shape: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, _bay, _y, _h, res, ctx = _ingredients(facts, shape)
        return [emit_surround(bid, _rect(shape.scope), res, ctx)]

    return write


def _interpret_keystone(facts: _Facts):
    def write(shape: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, _bay, _y, _h, res, ctx = _ingredients(facts, shape)
        # The keystone's scope is the head line of what it locks, and it is
        # written against that rectangle: its parent, the light or the cell.
        return [emit_keystone(bid, _rect(shape.parent.scope), res, ctx)]

    return write


def _interpret_balconette(facts: _Facts):
    def write(shape: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, _bay, y, _h, res, ctx = _ingredients(facts, shape)
        light = next(c for c in shape.parent.children if c.label == "Light").scope
        return [emit_balconette(bid, _rect(light), y, res, ctx)]

    return write


def _interpret_rail(facts: _Facts):
    def write(shape: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, _bay, _y, _h, res, ctx = _ingredients(facts, shape)
        return [emit_rail(bid, _rect(shape.scope), res, ctx)]

    return write


def _interpret_cell(facts: _Facts):
    def write(cell: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        bid, bay, y, h, res, ctx = _ingredients(facts, cell)
        # Drawn in one stated order, whichever sub-shape each element came from.
        ordered = sorted(below, key=lambda n: BAY_ELEMENT_ORDER.index(n.kind))
        return [emit_bay_node(bid, bay, y, h, res, ctx, ordered)]

    return write


def _interpret_storey(facts: _Facts):
    def write(storey: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        facade_w = math.fsum(b.width for b in storey.attr("grid").bays)
        ctx = facts.context(storey, 0)
        roled = _roled_storey(storey)
        if storey.attrs["within_comble"]:
            return [_storey_inside_the_comble(TraceLog(), storey.id, roled, ctx, facade_w)]
        s_res = storey.children[0].resolution
        elements = emit_storey_elements(
            storey.id, storey.scope.y, storey.scope.h, facade_w, s_res, ctx
        )
        return [emit_storey(storey.id, roled, ctx, s_res, facade_w, [*elements, *below])]

    return write


def _interpret_facade(facts: _Facts):
    def write(facade: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        _assert_one_entrance(below, facts.roled(facade), facts.site)
        return list(below)

    return write


def _interpret_roof(facts: _Facts):
    def write(roof: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        facade = roof.parent.children[0]
        silhouette, roofscape = terminate(roof.attr("grid"), facts.roled(facade), facts.site, d.rng)
        return [*roofscape, silhouette]

    return write


def _interpret_lot(facts: _Facts, layers: Sequence[Layer]):
    def write(lot: Shape, below: Sequence[Node], d: Derivation) -> list[Node]:
        site = facts.site
        grid = lot.attrs["grid"]
        facade = lot.children[0]
        roled = facts.roled(facade)
        facade_w = math.fsum(b.width for b in grid.bays)
        storeys = [n for n in below if n.kind == "storey"]
        silhouette = next(n for n in below if n.kind == "silhouette")
        total_height = float(silhouette.props["ridge_height"])
        # The root carries exactly the pipeline's account, so the IR is
        # byte-identical to it. The derivation's own record -- which
        # production made and expanded each shape -- stays on the shape tree
        # (``derive_paris``), where it describes something that exists.
        trace = (
            *_structure_entries(site, grid),
            *_roles_entries(roled),
            qualification_entry(len(storeys), grid.bays, facade_w, layers, site, roled),
        )
        props = {
            **building_props(site, facade_w, roled),
            "h": total_height,
            "w": facade_w,
            "eaves_height": grid.built_height,
            "total_height": total_height,
            "legal_cornice_ceiling": float(grid.cornice_height),
            "legal_total_height": grid.envelope.total_height,
            "envelope": grid.envelope.roof_envelope.value,
            "parcel_depth": site.parcel_depth,
            "ground": site.ground.value,
            "seed": site.seed,
        }
        return [
            BuildingNode(id=lot.id, kind="building", trace=trace, children=tuple(below), props=props)
        ]

    return write


# ===========================================================================
# The grammar
# ===========================================================================


def paris_grammar(site: SiteContext, layers: Sequence[Layer] | None = None) -> Grammar:
    layers = tuple(paris_layers() if layers is None else layers)
    facts = _Facts(site)
    return Grammar(
        name="paris",
        productions=(
            Production("paris.lot.envelope", "Lot", _lot_envelope),
            Production("paris.facade.storeys", "Facade", _facade_storeys),
            Production(
                "paris.storey.bays",
                "Storey",
                _storey_bays,
                guard=lambda s: not s.attrs["within_comble"],
            ),
            Production(
                "paris.cell.light",
                "Cell",
                _cell_light,
                guard=lambda c: opening_present(c.resolution),
            ),
            Production(
                "paris.cell.blind",
                "Cell",
                _cell_blind,
                guard=lambda c: not opening_present(c.resolution),
            ),
            Production("paris.light_bay", "LightBay", _light_bay),
            Production("paris.light", "Light", _light),
        ),
        stages=(
            AttributeStage(
                "Storey",
                (Layer("roles", 0, (the_stack_says_who_you_are,)),),
            ),
            AttributeStage(
                "Cell",
                layers,
                context=lambda cell: facts.context(cell.parent, cell.index),
                resolver=resolve,
            ),
        ),
        interpreters={
            "Cell": _interpret_cell(facts),
            "Light": _interpret_light(facts),
            "Shopfront": _interpret_shopfront(facts),
            "Surround": _interpret_surround(facts),
            "Keystone": _interpret_keystone(facts),
            "Balconette": _interpret_balconette(facts),
            "Rail": _interpret_rail(facts),
            "Storey": _interpret_storey(facts),
            "Facade": _interpret_facade(facts),
            "Roof": _interpret_roof(facts),
            "Lot": _interpret_lot(facts, layers),
        },
    )


def _axiom(site: SiteContext, datums) -> Shape:
    envelope = compute_envelope(
        site.street_width, era_for_year(site.year), site.parcel_depth, roof_fill=1.0, max_ridge=None
    )
    return Shape(
        "Lot",
        Scope(0.0, 0.0, site.parcel_width, envelope.total_height),
        "b",
        attrs={"site": site, "datums": datums},
    )


def derive_paris(
    site: SiteContext,
    datums=None,
    *,
    layers: Sequence[Layer] | None = None,
    refine: Callable[[Grammar], Grammar] | None = None,
) -> tuple[Shape, Derivation]:
    """The derived shape tree itself, for inspection and drawing.

    ``refine`` edits the grammar before it runs -- ``with_override``,
    ``with_interpreter``, ``with_production`` -- which is how a local variation
    is stated without touching the rules it does not name."""
    grammar = paris_grammar(site, layers)
    if refine is not None:
        grammar = refine(grammar)
    return derive(grammar, _axiom(site, datums), DecisionStream(site.seed))


def generate_cga(
    site: SiteContext,
    datums=None,
    *,
    layers: Sequence[Layer] | None = None,
    refine: Callable[[Grammar], Grammar] | None = None,
) -> tuple[BuildingNode, TraceLog]:
    """``generate``'s contract, derived by the grammar: a situation in, one
    ``BuildingNode`` tree and its ``TraceLog`` out."""
    lot, derivation = derive_paris(site, datums, layers=layers, refine=refine)
    (root,) = interpret(lot, derivation)
    log = TraceLog()
    for node in walk(root):
        for entry in node.trace:
            log.record(node.id, entry)
    return root, log
