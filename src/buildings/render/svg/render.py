"""The renderer entry point (S8): ``render(node, ...) -> str``.

This module walks the IR tree and turns it into SVG. Per CONTRACTS.md and the
brief's "the renderer decides nothing arguable", it dispatches on ``node.kind``
(a structural tag: "storey", "bay", "opening", ...) and on values qualification
already resolved (``opening_type``, ``surround_kind``, a dormer's ``form``, an
ironwork ``variant`` name, a roof's ``material``) — never on date, class, role
or street width. Where those facts are needed for a label (``labels=True``),
they are only ever *printed*, never branched on; ``dev/harness/check_renderer_dumb.py``
enforces the branching half of that mechanically.

The comble is drawn from the polyline S7 already computed
(``SilhouetteNode.props["points"]``) and offset by the eaves height it was
built from — nothing here calls into ``reglement`` or re-derives a setback.

What the IR does not yet say
----------------------------
A renderer that decides nothing arguable can only draw what it is told, so
where the IR is silent the drawing is thin, and saying which silences those
are is part of this stage's output rather than an excuse for filling them in
here. Each of these belongs upstream (S3/S6/S7), and none of them is patched
over in this package:

1. ~~An opening has no extent of its own.~~ Fixed (A4.1/A4.2): qualification
   (``catalogue.window_in_slot`` and its siblings) now states each opening's
   own width, height and place within its bay slot, plus the ABSOLUTE
   ``sill_height`` it stands on, and ``compose.py`` resolves those into the
   ``OpeningNode``'s own ``x/y/w/h`` — the light's rectangle, not the cell's.
   This module reads that rectangle directly (``render._draw_bay``,
   ``elements.draw_opening``) rather than inventing a margin and glazing the
   bay; where a hand-built layer set declines to state the geometry,
   ``compose.py`` still falls back to the cell (kept for exactly that case,
   `test_compose` asserts the real Paris stack never uses it).
2. ~~A souche has no visible base.~~ Fixed (A4.4/A6.4/A7.3): A6.4 gave a
   stack an ABSOLUTE head height but had THIS module recompute its base from
   the roof's profile and overwrite whatever the IR's ``y`` said — the same
   offence as A4.1 and A6.8, the renderer discarding a stated fact and
   substituting its own — and it also held the head absolute while the base
   fell with a hipped return, which turned a hip-end souche into a multi-metre
   smokestack. ``terminate.py`` now computes the roof surface at each stack's
   own x as a structural fact (``terminate._roof_surface_height_at``, the
   ridge everywhere mid-block, falling away toward a hipped return's ends)
   and states it directly on the stack's ``y``/``h``, holding the MASONRY
   ABOVE THE SURFACE constant rather than the absolute head height. This
   module draws exactly that rectangle. There is no override left to remove.
3. **A garde-corps with no balcony has no height.** ``balcony_rail_height``
   is only resolved where a balcony is, so a railing guarding a plain window
   above a drop arrives with ``h = 0`` and draws as nothing — even though the
   rule that put it there (``qualify.base.garde_corps_where_a_body_could_fall``)
   is about the drop, not about the balcony. The rail height is ABSOLUTE and
   should come with the railing.
4. ~~A shop bay is given a lean-on sill.~~ Fixed upstream:
   ``qualify.base.ground_floor_of_a_shop`` states
   ``catalogue.shop_threshold_height`` — a step, not a sill — and the
   devanture's two ABSOLUTE bands (that threshold below the light and
   ``shopfront_fascia_depth``'s enseigne board above it) reach this module on
   the ``shopfront`` node's own props. The ``shopfront`` node is now emitted
   per BAY, in the width of the light between its two trumeaux; it used to
   span the whole ground storey and glaze it end to end, which painted out
   every pier qualification had carved and left the shop-bay openings drawn
   over it as misregistered ghost frames (A4.1).
5. **"Hipped" does not say how far the hip runs along the frontage.** The
   silhouette's profile is a section perpendicular to the street — its own
   ``axes`` prop says so — so it measures depth, and on a corner building
   the return is governed by the OTHER street's gabarit and by which of the
   two ends is actually the corner. Neither is in the IR yet. A4.5 changed
   what is drawn in the meantime: the hip arris is now a straight line (a
   real arêtier is a straight timber even under a curved mansard front) at
   the section's own average pitch, rather than the curved section reused
   edge-on — the reuse was what read as an onion dome on a narrow chamfer.
   **A9.3** moved the derivation itself upstream: ``terminate.derive_hip_arris``
   (named ``_hip_arris`` until A10.4 exported it for a second caller)
   computes this straight line once, from the profile, and carries it on the
   roof node's own ``hip_arris`` prop — the one this module's
   ``draw_roof_mass`` reads (``elements.py``'s own copy of the derivation,
   fixed once already at A8.2 to key the pitch to the section's TRUE reach
   rather than a flat run-out's own end, is gone; keeping it here to fix a
   second time was already the wrong shape). ``terminate._roof_surface_height_at``
   reads the identical arris to place every souche, so the roof mass and the
   stacks standing on it cannot disagree about where the tiles are — it is
   still an approximation of geometry the IR does not carry precisely yet
   (item 5's own premise), but it is now approximated in exactly one place.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from buildings.ir.nodes import Node
from buildings.render.svg.canvas import Canvas
from buildings.render.svg.colors import COLORS
from buildings.render.svg import elements as el

__all__ = ["render", "building_extent_m", "draw_building", "render_block"]

_C = COLORS

#: Pixels-per-metre baseline; ``width_px`` rescales from here so a caller's
#: pixel budget is honoured regardless of how wide the facade is in metres.
_BASE_SCALE = 40.0
_MARGIN_M = 1.8
_GROUND_BAND_M = 1.2


def _num(props: Mapping[str, object], key: str, default: float = 0.0) -> float:
    v = props.get(key)
    return float(v) if v is not None else default


def _children_of_kind(node: Node, kind: str) -> list[Node]:
    return [c for c in node.children if c.kind == kind]


def _first_of_kind(node: Node, kind: str) -> Node | None:
    for c in node.children:
        if c.kind == kind:
            return c
    return None


def building_extent_m(node: Node) -> tuple[float, float]:
    """The (width, height) of one building's drawing, in metres — the facade
    width and the full silhouette height (stone plus comble). Exposed so a
    contact sheet can lay out a shared grid without re-deriving anything the
    IR did not already carry on the building's own ``props``."""
    facade_w = _num(node.props, "w", 1.0)
    total_h = _num(node.props, "h", _num(node.props, "eaves_height", 1.0))
    return facade_w, total_h


def render(node: Node | Sequence[Node], *, width_px: int = 1200, labels: bool = False) -> str:
    """Render a ``BuildingNode`` tree, or a solved block's run of nodes, to a
    self-contained SVG string.

    Rendering the same IR twice is byte-identical: nothing here samples
    anything, reads a clock, or depends on iteration order beyond what the IR
    itself fixes (``children`` is a tuple, ``props`` a frozen mapping).

    A4.6: ``node`` used to have to BE a ``BuildingNode`` with ``storey``
    children, so ``block.solve_block()``'s output — a ``parcel`` node
    wrapping a building, or the block's whole tuple of them plus its
    chamfers, party walls and datum lines — fell through every branch below
    and rendered as an empty sky-and-ground SVG. Both now dispatch to
    ``render_block``, which is the one place that draws more than one
    building into a single frontage.
    """
    if not isinstance(node, Node):
        return render_block(node, width_px=width_px, labels=labels)
    if node.kind == "parcel":
        return render_block([node], width_px=width_px, labels=labels)
    building = node
    facade_w = _num(building.props, "w", 1.0)
    total_h = _num(building.props, "h", _num(building.props, "eaves_height", 1.0))

    canvas_w_m = facade_w + 2 * _MARGIN_M
    canvas_h_m = total_h + _MARGIN_M + _GROUND_BAND_M
    scale = max(1.0, width_px / canvas_w_m) if canvas_w_m > 0 else _BASE_SCALE

    canvas = Canvas(
        scale=scale,
        x_origin=_MARGIN_M * scale,
        y_origin=(total_h + _GROUND_BAND_M) * scale,
    )
    canvas_w_px = canvas_w_m * scale
    canvas_h_px = canvas_h_m * scale

    canvas.elements.append(
        f'<rect x="0" y="0" width="{canvas_w_px:.2f}" height="{canvas_h_px:.2f}" fill="{_C["sky"]}"/>'
    )
    ground_y = canvas.y(0.0)
    canvas.elements.append(
        f'<rect x="0" y="{ground_y:.2f}" width="{canvas_w_px:.2f}" '
        f'height="{(canvas_h_px - ground_y):.2f}" fill="{_C["ground"]}"/>'
    )

    draw_building(canvas, building, labels)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w_px:.2f}" '
        f'height="{canvas_h_px:.2f}" viewBox="0 0 {canvas_w_px:.2f} {canvas_h_px:.2f}">\n'
        f'<style>text {{ font-family: "Helvetica Neue", Arial, sans-serif; }}</style>\n'
    )
    svg += "\n".join(canvas.elements)
    svg += "\n</svg>"
    return svg


def draw_building(canvas: Canvas, building: Node, labels: bool = False) -> None:
    """Draw one building's storeys and roofscape into ``canvas`` at its
    current origin — the shared primitive ``render`` and the contact sheet
    both use, so a multi-building sheet draws each building exactly as
    ``render`` would, just offset into its own cell."""
    facade_w = _num(building.props, "w", 1.0)

    # Draw order is depth order: the comble, then whatever stands on its own
    # front face, then the stone facade in front of all of it.
    #
    # The roof mass is drawn BEFORE the storeys, not after. Its own polygon
    # has zero area below the eaves (its first point IS the eaves), so
    # nothing about the wall is hidden by drawing it first — but a cornice
    # sits exactly on that same eaves line, projecting a few centimetres
    # upward into the same band the roof polygon fills, and whichever is
    # drawn second is the one left visible. A photograph shows the cornice
    # standing proud of the roof, not buried under it, so storeys (and the
    # cornice among their children) are drawn last among the two.
    #
    # **A9.3.** Chimneys used to go in BEFORE the roof, on the reasoning that
    # "a souche stands behind the comble" — but a souche does not stand
    # behind the roof surface, it stands ON it and rises clear through it: the
    # masonry drawn is exactly the part standing proud of the tiles
    # (``terminate._souche_visible_height``), which is in front of them, not
    # behind. Drawing it first was HARMLESS only as long as a souche's stated
    # base agreed with the roof mass's own drawn surface at that point, and it
    # had stopped agreeing: `terminate._hip_arris_end` (now `derive_hip_arris`,
    # fixed) keyed the hip run to the full section depth while the roof mass
    # was already keyed to the frontage, so a hip-end souche's stated base
    # could sit up to 1.559 m BELOW the roof surface the mass drew above it —
    # and drawing the stack first meant the roof polygon, painted second,
    # simply covered it: one visible chimney where the IR stated five. Now
    # that both are the same structural fact (``terminate.derive_hip_arris``, read
    # from the roof node's own ``hip_arris`` prop rather than re-derived), the
    # two cannot disagree — but the stack is still drawn AFTER the roof mass,
    # because that is where it belongs: the brick a souche shows is in front
    # of the comble it rises through, not behind it.
    #
    # A7.3: a souche's base is the roof surface it actually emerges from —
    # the ridge mid-block, falling away toward a hipped return's own ends —
    # and that surface is a STRUCTURAL fact ``terminate.py`` computes and
    # states on the stack's own ``y``/``h`` (``terminate._roof_surface_height_at``).
    # This module used to recompute the same figure for itself from the
    # roof's profile and OVERWRITE the IR's ``y`` with it, which is the same
    # offence as A4.1 and A6.8: the IR stated a base and the renderer threw
    # it away and drew its own. There is no override here any more — the
    # rectangle drawn is exactly the one the IR gives.
    roof = _first_of_kind(building, "roof")
    silhouette = _first_of_kind(building, "silhouette")

    if roof is not None and silhouette is not None:
        _draw_roof_from_silhouette(canvas, roof, silhouette, facade_w)

    for special in _children_of_kind(building, "special"):
        element_kind = special.props.get("element")
        if element_kind == "chimney_stack":
            sx = _num(special.props, "x")
            sw = _num(special.props, "w")
            base_y = _num(special.props, "y")
            head_y = base_y + _num(special.props, "h")
            el.draw_chimney(canvas, sx, base_y, sw, max(0.0, head_y - base_y))

    gables = _children_of_kind(building, "gable")
    for gable in gables:
        el.draw_gable_mass(canvas, gable.props, _WALL_PAINT.get(gable.props.get("wall_material") or "stone", _C["wall"]))
    for storey in _children_of_kind(building, "storey"):
        _draw_storey(canvas, storey, facade_w, labels)
    for gable in gables:
        el.draw_gable_coping(canvas, gable.props)
    # Piers that run through several storeys belong to the building, and stand
    # in front of every storey they cross.
    for column in _children_of_kind(building, "column"):
        el.draw_column(canvas, _num(column.props, "x"), _num(column.props, "y"), _num(column.props, "w"), _num(column.props, "h"), column.props)

    for dormer in _children_of_kind(building, "dormer"):
        el.draw_dormer(
            canvas,
            _num(dormer.props, "x"),
            _num(dormer.props, "y"),
            _num(dormer.props, "w"),
            _num(dormer.props, "h"),
            dormer.props,
        )

    # A19.2: the lower garret's openings are windows in the brisis face, not
    # lucarnes standing out of it. A separate kind in the IR, so a separate
    # call here — this module never decides which a row gets.
    for window in _children_of_kind(building, "brisis_window"):
        el.draw_brisis_window(
            canvas,
            _num(window.props, "x"),
            _num(window.props, "y"),
            _num(window.props, "w"),
            _num(window.props, "h"),
            window.props,
        )

    for ironwork in _children_of_kind(building, "ironwork"):
        # Cresting: the only ironwork living directly on the building rather
        # than on a bay. ``draw_ironwork`` reads its own "position" prop.
        el.draw_ironwork(
            canvas,
            _num(ironwork.props, "x"),
            _num(ironwork.props, "y"),
            _num(ironwork.props, "w"),
            _num(ironwork.props, "h"),
            ironwork.props,
        )

    if labels:
        _draw_labels(canvas, building, facade_w)


#: A block's own scope tag, set by ``block.py`` on the datum lines it emits
#: directly (as opposed to the ones a building emits on its own facade).
_BLOCK_SCOPE = "block"
_BLOCK_DATUM_KINDS = frozenset({"cornice", "string_course", "balcony"})


def render_block(nodes: Sequence[Node], *, width_px: int = 1600, labels: bool = False) -> str:
    """Render a solved block's run — ``block.solve_block()``'s output tuple —
    as one continuous frontage (A4.6).

    Per the brief, a block reads as one wall or it has failed at the one
    thing it exists for. Concretely that means three things this function
    does and a lone ``render()`` call cannot:

    1. Every parcel's building is drawn by the SAME ``draw_building`` a lone
       ``render()`` call uses — never a second, divergent way of drawing a
       building — just offset along the frontage by the ``x`` ``block.py``
       already resolved for it (``Block.origins``), so buildings sit flush
       against each other with no per-building margin between them.
    2. A chamfer is drawn as what it is: a third short facade with its own
       rhythm, not a building squeezed to fit and not a gap (A4.5's framing
       for the roof applies to the wall too).
    3. The block's own datum lines — the cornice, the bandeaux, the balcons
       filants the 1855 circulaire requires to align — are drawn ONCE, LAST,
       spanning the whole run. Every building underneath has already drawn
       its own share of the same lines (``check_alignment`` proved they
       coincide before this ever reaches a renderer), so drawing the block's
       copy on top is what makes the seam at every party wall disappear
       instead of reading as a shelf of separately-finished models.
    """
    frontage = [n for n in nodes if n.kind in ("parcel", "chamfer")]
    if not frontage:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"/>'

    datums = [
        n for n in nodes if n.kind in _BLOCK_DATUM_KINDS and n.props.get("scope") == _BLOCK_SCOPE
    ]

    def _height_of(n: Node) -> float:
        if n.kind == "parcel":
            b = _first_of_kind(n, "building")
            return _num(b.props, "h") if b is not None else _num(n.props, "h")
        # chamfer: its own "h" is eaves only (the stone face), same as a
        # building's `eaves_height` versus its `h` — its roof (A6.3) stands
        # above that and is a separate child, so its height is added in.
        h = _num(n.props, "h")
        roof = _first_of_kind(n, "roof")
        return h + _num(roof.props, "h") if roof is not None else h

    x0 = min(_num(n.props, "x") for n in frontage)
    x1 = max(_num(n.props, "x") + _num(n.props, "w") for n in frontage)
    span = max(0.0, x1 - x0)
    max_h = max([_height_of(n) for n in frontage] + [_num(n.props, "y") for n in datums] + [0.0])

    canvas_w_m = span + 2 * _MARGIN_M
    canvas_h_m = max_h + _MARGIN_M + _GROUND_BAND_M
    scale = max(1.0, width_px / canvas_w_m) if canvas_w_m > 0 else _BASE_SCALE
    canvas_w_px = canvas_w_m * scale
    canvas_h_px = canvas_h_m * scale

    canvas = Canvas(scale=scale)
    base_x_origin = (_MARGIN_M - x0) * scale
    y_origin = (max_h + _GROUND_BAND_M) * scale
    canvas.x_origin, canvas.y_origin = base_x_origin, y_origin

    canvas.elements.append(
        f'<rect x="0" y="0" width="{canvas_w_px:.2f}" height="{canvas_h_px:.2f}" fill="{_C["sky"]}"/>'
    )
    ground_y = canvas.y(0.0)
    canvas.elements.append(
        f'<rect x="0" y="{ground_y:.2f}" width="{canvas_w_px:.2f}" '
        f'height="{(canvas_h_px - ground_y):.2f}" fill="{_C["ground"]}"/>'
    )

    # One wall, left to right — each building and chamfer at the frontage
    # offset the block already resolved, nothing here re-laying it out.
    for n in frontage:
        canvas.x_origin = base_x_origin + _num(n.props, "x") * scale
        canvas.y_origin = y_origin
        if n.kind == "parcel":
            b = _first_of_kind(n, "building")
            if b is not None:
                draw_building(canvas, b, labels)
        else:
            _draw_chamfer(canvas, n)

    # Party walls are real, but in a unified block they are not a seam the
    # eye should catch — that unity is the entire point of the circulaire —
    # so this is a hairline, not a divider.
    canvas.x_origin, canvas.y_origin = base_x_origin, y_origin
    for n in nodes:
        if n.kind == "party_wall":
            px = _num(n.props, "x") + _num(n.props, "w") / 2.0
            canvas.line(px, 0.0, px, _num(n.props, "h"), "#B8AE9A", 0.3)

    # The block's own datum lines, drawn LAST across the whole span — see
    # the docstring above for why last is what makes them continuous.
    canvas.x_origin, canvas.y_origin = base_x_origin, y_origin
    for n in datums:
        dx, dy, dw = _num(n.props, "x"), _num(n.props, "y"), _num(n.props, "w", span)
        if n.kind == "cornice":
            el.draw_cornice(canvas, dx, dy, dw, n.props)
        elif n.kind == "string_course":
            el.draw_string_course(canvas, dx, dy, dw, n.props)
        elif n.kind == "balcony":
            el.draw_balcony_slab(canvas, dx, dy, dw, n.props)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w_px:.2f}" '
        f'height="{canvas_h_px:.2f}" viewBox="0 0 {canvas_w_px:.2f} {canvas_h_px:.2f}">\n'
        f'<style>text {{ font-family: "Helvetica Neue", Arial, sans-serif; }}</style>\n'
    )
    svg += "\n".join(canvas.elements)
    svg += "\n</svg>"
    return svg


def _draw_chamfer(canvas: Canvas, chamfer: Node) -> None:
    """A pan coupé: a third short facade, drawn as one — comble included.

    Its storeys go through the SAME ``_draw_storey`` a building's do — which
    is the whole of A4.5's "a corner is a third short facade with its own
    rhythm". It used to have its own private drawing path, and that path had
    no opening branch at all, so every chamfer in a block came out as a blank
    unpierced wall between two pierced ones. There is now nothing for a
    chamfer-specific path to do that a facade's does not already do for
    either the wall or the roof standing on it (A6.3), so there is no
    chamfer-specific drawing logic: only the datum lines ``block.py`` carried
    around the corner are handled directly here, because those are the
    block's nodes hanging on the chamfer rather than the chamfer's own.
    """
    w, h = _num(chamfer.props, "w"), _num(chamfer.props, "h")
    if w <= 1e-9 or h <= 1e-9:
        return
    canvas.rect(0.0, 0.0, w, h, _C["wall"], stroke_w=0.4)

    # Same depth order as `draw_building`: the roof mass goes in before the
    # storeys so the cornice — the last of the storeys' own children — stands
    # proud of it rather than being buried under it (see that function's own
    # docstring for why the order matters, not just that it does).
    roof = _first_of_kind(chamfer, "roof")
    silhouette = _first_of_kind(chamfer, "silhouette")
    if roof is not None and silhouette is not None:
        _draw_roof_from_silhouette(canvas, roof, silhouette, w)

    for child in chamfer.children:
        cx, cy, cw = _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w", w)
        if child.kind == "storey":
            _draw_storey(canvas, child, w, False)
        elif child.kind == "cornice":
            el.draw_cornice(canvas, cx, cy or h, cw, child.props)
        elif child.kind == "string_course":
            el.draw_string_course(canvas, cx, cy, cw, child.props)
        elif child.kind == "balcony":
            el.draw_balcony_slab(canvas, cx, cy, cw, child.props)
    canvas.line(0.0, 0.0, 0.0, h, _C["pier_line"], 0.3)
    canvas.line(w, 0.0, w, h, _C["pier_line"], 0.3)


#: Wall paint keyed by the material a storey states (``wall_material``).
_WALL_PAINT = {
    "stone": _C["wall"],
    "cast_iron": _C["wall_cast_iron"],
    "brick": _C["wall_brick"],
    "brick_dark": _C["wall_brick_dark"],
    "stucco_rose": _C["wall_stucco_rose"],
    "terracotta": _C["wall_terracotta"],
    "brick_london": _C["wall_brick_london"],
    "stucco": _C["wall_stucco"],
    "timber_dark": _C["wall_timber_dark"],
    "plaster_white": _C["wall_plaster_white"],
    "brick_buff": _C["wall_brick_buff"],
    "render_white": _C["wall_render_white"],
    "shadow": _C["wall_shadow"],
}


def _draw_storey(canvas: Canvas, storey: Node, facade_w: float, labels: bool) -> None:
    y = _num(storey.props, "y")
    h = _num(storey.props, "h")

    # A storey standing inside the comble (the chambres de bonne, A2.1) has no
    # stone facade — compose.py emits it with no children for exactly that
    # reason, and its floor level is already inside the roof mass this module
    # just drew. `on_the_stone_facade` is the IR saying so plainly; reading it
    # is not deciding anything, it is the difference between "draw a wall"
    # and "there is no wall here to draw" that qualification already settled.
    if storey.props.get("on_the_stone_facade") is False:
        return

    # Wall paint follows the material the storey states; stone where it states none.
    wall = _WALL_PAINT.get(storey.props.get("wall_material") or "stone", _C["wall"])
    # A storey is as wide as it says: the full frontage, or one tier of a gable.
    sx = _num(storey.props, "x", 0.0)
    sw = _num(storey.props, "w", facade_w)
    canvas.rect(sx, y, sw, h, wall, stroke_w=0.4)

    for child in storey.children:
        if child.kind == "socle":
            el.draw_socle(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), _num(child.props, "h"), child.props)
        elif child.kind == "string_course":
            el.draw_string_course(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), child.props)
        elif child.kind == "balcony":
            el.draw_balcony_slab(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), child.props)
        elif child.kind == "cornice":
            el.draw_cornice(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), child.props)
        elif child.kind == "bay":
            _draw_bay(canvas, child)
    # Columns stand in front of the bays they divide, so they are drawn after.
    for child in storey.children:
        if child.kind == "column":
            el.draw_column(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), _num(child.props, "h"), child.props)

    canvas.line(sx, y, sx + sw, y, _C["outline"], 0.5)

    if labels:
        canvas.text(-0.8, y + h / 2.0, f"{h:.2f}m", size=8, fill="#888888")


_PIER_KINDS = frozenset({"pier_end", "special", "porte_cochere"})


def _rect_of(node: Node, fallback: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """The rectangle a node states, or ``fallback`` where it states none."""
    fx, fy, fw, fh = fallback
    return (
        _num(node.props, "x", fx),
        _num(node.props, "y", fy),
        _num(node.props, "w", fw),
        _num(node.props, "h", fh),
    )


def _draw_bay(canvas: Canvas, bay: Node) -> None:
    x = _num(bay.props, "x")
    y = _num(bay.props, "y")
    w = _num(bay.props, "w")
    h = _num(bay.props, "h")
    slot_name = bay.props.get("slot_name")
    opening = _first_of_kind(bay, "opening")
    if slot_name in _PIER_KINDS and opening is None:
        el.draw_bay_background(canvas, x, y, w, h)
    else:
        canvas.line(x, y, x, y + h, _C["pier_line"], 0.3)
        canvas.line(x + w, y, x + w, y + h, _C["pier_line"], 0.3)

    # A4.1 consumption: an opening's props carry its OWN rectangle — narrower
    # than the bay cell, with the pier and the spandrel qualification already
    # left around it — not the cell's. The storey's own wall fill
    # (``_draw_storey``, drawn before any bay) is what shows through as
    # masonry on every side of it; nothing here re-glazes the cell.
    ox, oy, ow, oh = (
        (_num(opening.props, "x", x), _num(opening.props, "y", y), _num(opening.props, "w", w), _num(opening.props, "h", h))
        if opening is not None
        else (x, y, w, h)
    )

    for child in bay.children:
        if child.kind == "shopfront":
            # The devanture's own bands — the soubassement under the light and
            # the enseigne board over it — in the light's own width. Drawn
            # from the node's rectangle, which stops at the trumeau either
            # side; the storey-wide shopfront that used to glaze the whole
            # frontage, piers included, is gone (A4.1).
            el.draw_shopfront(canvas, _num(child.props, "x"), _num(child.props, "y"), _num(child.props, "w"), _num(child.props, "h"), child.props)
        elif child.kind == "opening":
            # Each opening at its own rectangle: a bay may hold several lights.
            el.draw_opening(canvas, *_rect_of(child, (ox, oy, ow, oh)), child.props)
        elif child.kind == "surround":
            # Wraps the light, not the cell — a moulded architrave sized to
            # the whole bay would float untethered from the window it frames.
            el.draw_surround(canvas, *_rect_of(child, (ox, oy, ow, oh)), child.props)
        elif child.kind == "keystone":
            kx, ky, kw, _kh = _rect_of(child, (ox, oy + oh, ow, 0.0))
            el.draw_keystone(canvas, kx + kw / 2.0, ky, child.props)
        elif child.kind == "balcony":
            el.draw_balcony_slab(canvas, x, _num(child.props, "y"), w, child.props)
        elif child.kind == "ironwork":
            # A12.2: an ironwork node states its OWN rectangle — the light's
            # width for a garde-corps in the reveal, the bay's for a balcon
            # filant's balustrade (compose.py's ``rail_x``/``rail_w``, A6.5).
            # Reading the bay's own x/w here instead, as this used to, drew
            # every garde-corps as wide as the balcony it is not, which is
            # the width half of why four rails read as four balconies.
            el.draw_ironwork(
                canvas,
                _num(child.props, "x", x),
                _num(child.props, "y"),
                _num(child.props, "w", w),
                _num(child.props, "h"),
                child.props,
            )


def _roof_profile(silhouette: Node) -> list[tuple[float, float]]:
    """The comble half of the polyline S7 emitted, re-based to the eaves it
    springs from — arithmetic, not geometry: no setback is recomputed here.

    Shared by the roof mass and the chimneys standing on it (A6.4), so the
    two read the same surface rather than each re-deriving it and risking a
    disagreement about where the tiles are.
    """
    eaves = _num(silhouette.props, "eaves_height")
    points: Sequence[tuple[float, float]] = silhouette.props.get("points") or ()
    return [(inset, y - eaves) for inset, y in points if y >= eaves - 1e-9]


def _draw_roof_from_silhouette(canvas: Canvas, roof: Node, silhouette: Node, facade_w: float) -> None:
    eaves = _num(silhouette.props, "eaves_height")
    profile = _roof_profile(silhouette)
    el.draw_roof_mass(canvas, facade_w, eaves, profile, roof.props)


def _draw_labels(canvas: Canvas, building: Node, facade_w: float) -> None:
    total_h = _num(building.props, "h")
    canvas.text(facade_w / 2.0, -0.6, f"{facade_w:.1f}m", size=9, fill="#666666")
    canvas.text(facade_w + 0.9, total_h + 0.3, f"total {total_h:.1f}m", size=9, fill="#666666", anchor="start")
