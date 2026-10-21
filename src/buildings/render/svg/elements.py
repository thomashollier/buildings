"""Element-level drawing (S8), ported from
``../haussmann/backends/svg.py`` and ``svg_elements.py``.

Every function here takes a ``Canvas`` and the ``props`` mapping already sitting
on one IR node, and draws it. Nothing here samples anything, and nothing here
asks *whether* an element exists or *which* dated variant it is — that is
qualification's job (S6) and it is already answered by the string sitting in
``props``. What is decided here is purely graphical: padding, proportion,
which SVG primitives approximate "a moulded architrave" versus "a bare band".
That is drawing, not composition, and it is the one kind of decision a
renderer is allowed to make (see the module guard,
``dev/harness/check_renderer_dumb.py``).

None of the props keys read below are named after one of the guard's
forbidden tokens (``year``, ``klass``, ``role``, ``era``, ``period``,
``variant``, ``richness``, ``street_width``, ...) — not because a local
variable hides them from the guard (A4.3: that was tried, it is not an
acceptable pattern, and it has been removed), but because every resolved
decision this module reads is composed and named upstream for what it is
(``cornice_ornament``, ``ironwork_pattern``, ``shopfront_style``, ...), so the
raw generic key never reaches here to be branched on.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from buildings.render.svg.canvas import Canvas
from buildings.render.svg.colors import COLORS

_C = COLORS


#: The stone colours a trim node (cornice, course, surround, keystone, door
#: frame) is drawn in, which a stated ``paint`` replaces: a brownstone front's
#: hoods are its own stone, its cornice dark.
_TRIM_KEYS = ("cornice", "ornament", "string_course", "keystone", "istrian", "gable_coping", "surround_bare_band",
              "surround_moulded_architrave", "surround_pedimented", "door", "door_dark")


def _palette(props: Mapping[str, object]) -> Mapping[str, str]:
    paint = _C.get(str(props.get("paint")))
    if paint is None:
        return _C
    keep_door = {k: _C[k] for k in ("door", "door_dark")}
    return {**_C, **{k: paint for k in _TRIM_KEYS}, **keep_door}


def _get(props: Mapping[str, object], key: str, default: object = None) -> object:
    return props[key] if key in props and props[key] is not None else default


def _num(props: Mapping[str, object], key: str, default: float = 0.0) -> float:
    v = props.get(key)
    return float(v) if v is not None else default


def _count(props: Mapping[str, object], key: str, minimum: int) -> int:
    """How many repeats of a rhythm to draw — read, never derived (A7.2).

    Before A7.2 every ornament in this module worked out its own count by
    dividing a dimension the IR handed it by a spacing it had chosen itself:
    ``spacing = 0.5; n = max(1, int(w / spacing))`` for the modillions,
    ``int(w / 0.35)`` for the scrollwork, ``course_h = 0.22`` for the
    picturesque rustication. Thirteen of them. Each one is the density of
    ornament, which the brief lists among the PROPORTIONAL quantities that
    move with ambition and budget — so each was a decision about how rich a
    building looks, taken by the last thing in the pipeline, identically for
    every building in Paris. The interval is qualification's now, and what
    arrives here is the count it produced over this element's own extent.

    ``minimum`` is not a spacing in disguise and never touches a dimension:
    it is the floor below which the ornament stops reading as a rhythm at
    all — two brackets, four uprights — and it is what a hand-built node that
    states no count gets. Such a node is drawing the plainest version of
    itself, which is the honest answer to an IR that did not say.
    """
    stated = props.get(key)
    if stated is None:
        return minimum
    return max(minimum, int(stated))


# ---------------------------------------------------------------------------
# Bay background — the wall a slot is cut into, before anything is drawn on it
# ---------------------------------------------------------------------------


def draw_bay_background(canvas: Canvas, x: float, y: float, w: float, h: float) -> None:
    """Plain wall fill for a slot with no opening (a pier, a blind bay)."""
    canvas.rect(x, y, w, h, _C["pier"], stroke=_C["pier_line"], stroke_w=0.3)


# ---------------------------------------------------------------------------
# Openings
# ---------------------------------------------------------------------------


def _arch_points(x0: float, x1: float, y_spring: float, rise: float, steps: int = 16):
    cx = (x0 + x1) / 2.0
    r = (x1 - x0) / 2.0
    pts = []
    for i in range(steps + 1):
        t = i / steps
        angle = math.pi * t
        pts.append((cx - r * math.cos(angle), y_spring + rise * math.sin(angle)))
    return pts


def _draw_head(
    canvas: Canvas,
    x: float,
    y_top: float,
    w: float,
    head_h: float,
    head_form: str,
    fill: str,
    stroke: str | None = None,
) -> float:
    """Draw the top of an opening per its head form; returns the springing
    height (top of the rectangular body, below the head).

    ``stroke`` defaults to the ordinary window frame colour, but a caller
    framing something that is not joinery — a devanture's segmental relief
    over plate glass, say — passes its own, so the head reads as part of the
    opening it caps rather than as a window dropped onto a shopfront.
    """
    line = stroke if stroke is not None else _C["window_frame"]
    y_spring = y_top - head_h
    if head_form == "round":
        pts = _arch_points(x, x + w, y_spring, head_h)
        canvas.polygon(pts, fill, stroke=line, stroke_w=0.6)
    elif head_form == "segmental":
        pts = _arch_points(x, x + w, y_spring, head_h * 0.55)
        canvas.polygon(pts, fill, stroke=line, stroke_w=0.6)
    elif head_form in ("ogee", "pointed"):
        canvas.polygon(_head_outline(x, y_spring, w, head_h, head_form), fill, stroke=line, stroke_w=0.6)
    elif head_form == "irregular":
        # A head the mason did not square — drawn as a skewed lintel, not a
        # decision about why it is skewed.
        canvas.polygon(
            [(x, y_spring), (x + w, y_spring - head_h * 0.3), (x + w, y_spring), (x, y_spring)],
            fill,
            stroke=line,
            stroke_w=0.6,
        )
        canvas.line(x, y_spring, x + w, y_spring - head_h * 0.3, line, 0.6)
    # "flat" and anything unrecognised: no separate head, the body runs to y_top.
    return y_spring if head_form in _ARCHED else y_top


#: Head forms that rise from a springing line, rather than run flat.
_ARCHED = ("round", "segmental", "ogee", "pointed")


def _ogee_points(x: float, y_spring: float, w: float, rise: float, steps: int = 14):
    """The left half of an ogee, springing to apex: it leaves the springing
    vertically, curves in like any arch (convex), turns about two thirds of
    the way up and runs concave into the apex, where it meets its mirror in
    a sharp point. A cubic whose first control point stands over the
    springing and whose second stands under the apex."""
    half = w / 2.0
    pts = []
    for i in range(steps + 1):
        t = i / steps
        across = 3 * t * t - 2 * t ** 3
        up = 3 * t * (1 - t) ** 2 * 0.50 + 3 * t * t * (1 - t) * 0.12 + t ** 3
        pts.append((x + half * across, y_spring + rise * up))
    return pts


def _pointed_points(x: float, y_spring: float, w: float, rise: float, steps: int = 10):
    """The left half of a pointed arch: an arc struck from the opposite
    springing (equilateral), scaled to the stated rise."""
    k = rise / (w * math.sin(math.pi / 3.0))
    pts = []
    for i in range(steps + 1):
        a = (math.pi / 3.0) * i / steps
        pts.append((x + w - w * math.cos(a), y_spring + k * w * math.sin(a)))
    return pts


def _head_outline(x: float, y_spring: float, w: float, rise: float, head_form: str) -> list[tuple[float, float]]:
    """The head's outline from one springing over the top to the other."""
    if head_form == "round":
        return _arch_points(x, x + w, y_spring, rise)
    if head_form == "segmental":
        return _arch_points(x, x + w, y_spring, rise * 0.55)
    if head_form in ("ogee", "pointed"):
        left = _ogee_points(x, y_spring, w, rise) if head_form == "ogee" else _pointed_points(x, y_spring, w, rise)
        right = [(x + w - (px - x), py) for px, py in reversed(left[:-1])]
        return [(x, y_spring), *left, *right, (x + w, y_spring)]
    return [(x, y_spring), (x + w, y_spring)]


def _height_on(outline: Sequence[tuple[float, float]], at_x: float) -> float:
    """Where an outline (left to right over the top) stands at ``at_x``."""
    for (x0, y0), (x1, y1) in zip(outline, outline[1:]):
        if min(x0, x1) - 1e-9 <= at_x <= max(x0, x1) + 1e-9 and abs(x1 - x0) > 1e-12:
            return y0 + (y1 - y0) * (at_x - x0) / (x1 - x0)
    return max(y for _x, y in outline)


def _draw_head_band(canvas: Canvas, x: float, y_spring: float, w: float, rise: float, head_form: str, band_kind: str, stilt: float = 0.0) -> None:
    """The stone band an arch is turned in: the head's outline and the same
    outline struck a band wider, filled between. A dentilled band carries a
    second, outer line. An extradosed archivolt is a thin raised moulding
    round the extrados, carried down the stilt to the impost it springs from."""
    if rise <= 1e-9 or head_form not in _ARCHED:
        return
    band = min(0.14, w * 0.09)
    inner = _head_outline(x, y_spring, w, rise, head_form)
    outer = _head_outline(x - band, y_spring, w + 2 * band, rise + band, head_form)
    if band_kind == "extradosed":
        foot = y_spring - stilt
        ring = [(x - band, foot), *outer, (x + w + band, foot)]
        hole = [(x, foot), *inner, (x + w, foot)]
        canvas.polygon(ring + list(reversed(hole)), _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
        mould = band * 0.45
        rim = _head_outline(x - band - mould, y_spring, w + 2 * (band + mould), rise + band + mould, head_form)
        rim = [(x - band - mould, foot), *rim, (x + w + band + mould, foot)]
        for (x0, y0), (x1, y1) in zip(rim, rim[1:]):
            canvas.line(x0, y0, x1, y1, _C["istrian_line"], 0.9)
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            canvas.line(x0, y0, x1, y1, _C["istrian"], 0.6)
        return
    canvas.polygon(outer + list(reversed(inner)), _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
    if band_kind == "dentil":
        outer2 = _head_outline(x - band * 0.45, y_spring, w + band * 0.9, rise + band * 0.45, head_form)
        for (x0, y0), (x1, y1) in zip(outer2, outer2[1:]):
            canvas.line(x0, y0, x1, y1, _C["istrian_line"], 0.3, dash="1,1")


def _draw_finial(canvas: Canvas, cx: float, y_tip: float, height: float) -> None:
    """The carved fleuron on an ogee's tip: a short stalk and a pointed leaf."""
    if height <= 1e-9:
        return
    half = height * 0.32
    canvas.polygon(
        [(cx, y_tip), (cx + half, y_tip + height * 0.45), (cx, y_tip + height), (cx - half, y_tip + height * 0.45)],
        _C["istrian"],
        stroke=_C["istrian_line"],
        stroke_w=0.4,
    )


def draw_opening(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """Draw one opening. ``(x, y, w, h)`` is the LIGHT's own rectangle —
    qualification (``catalogue.window_in_slot`` and its siblings) has already
    carved the real pier either side and the spandrel above and below out of
    the bay slot that carries it (A4.1), and ``compose.py`` has already added
    ``sill_height`` (ABSOLUTE) to the storey floor to get ``y``. Neither of
    those numbers is re-derived, re-added or second-guessed here: this
    function's whole job is what happens *inside* the rectangle it is given —
    the head form, the glazing bars, the door panels — which is drawing, not
    proportion.
    """
    opening_kind = props.get("opening_type")
    head_form = props.get("head") or "flat"

    if opening_kind == "none" or w <= 1e-9 or h <= 1e-9:
        return
    if opening_kind == "blind_panel":
        canvas.rect(x, y, w, h, _C["wall_ground"], stroke=_C["pier_line"], stroke_w=0.4)
        canvas.rect(x + w * 0.2, y + h * 0.25, w * 0.6, h * 0.5, "none", stroke=_C["pier_line"], stroke_w=0.4)
        return
    if opening_kind == "oeil_de_boeuf":
        cx, cy = x + w / 2.0, y + h / 2.0
        r = min(w, h) / 2.0 * 0.92
        _draw_roundel(canvas, cx, cy, r)
        return
    if opening_kind in ("open_arch", "water_gate"):
        # An arch with nothing glazed in it -- a portico bay, a water gate:
        # the dark of the space behind, under its head. A gate's lunette
        # carries the iron grille the IR counts out.
        rise = min(_num(props, "head_rise", 0.0), h)
        springing = y + h - rise
        canvas.rect(x, y, w, springing - y, _C["void"], stroke=_C["void"], stroke_w=0.3)
        if rise > 1e-9:
            canvas.polygon(_head_outline(x, springing, w, rise, head_form), _C["void"], stroke=_C["void"], stroke_w=0.3)
        bars = _count(props, "grille_bars", 0)
        if bars > 1:
            outline = _head_outline(x, springing, w, rise, head_form)
            canvas.line(x, springing, x + w, springing, _C["iron"], 0.7)
            for i in range(1, bars):
                bx = x + w * i / bars
                canvas.line(bx, springing, bx, _height_on(outline, bx), _C["iron"], 0.5)
        _draw_head_band(canvas, x, springing, w, rise, head_form, str(props.get("archivolt") or "plain"), _num(props, "archivolt_stilt", 0.0))
        if props.get("head_finial"):
            _draw_finial(canvas, x + w / 2.0, y + h, _num(props, "finial_h", 0.0))
        return
    if opening_kind == "tracery_band":
        # The stone band of a traceried polifora; its quatrefoils are their
        # own openings, drawn over it.
        canvas.rect(x, y, w, h, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
        return
    if opening_kind == "quatrefoil":
        # Four lobes in a ring, centred in the rectangle the IR gives it.
        cx, cy = x + w / 2.0, y + h / 2.0
        ring = min(w, h) * 0.46
        lobe = ring * 0.42
        canvas.circle(cx, cy, ring, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.5)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            canvas.circle(cx + dx * (ring - lobe) * 0.92, cy + dy * (ring - lobe) * 0.92, lobe, _C["window"], stroke=_C["window"], stroke_w=0.2)
        return
    if opening_kind == "shop_bay":
        # A4.1's mirror image (A6.8): the head is a fact `head_form` already
        # states — round, segmental, irregular, the same vocabulary an
        # ordinary window uses — and dispatching straight to the glass used
        # to discard it before it was ever drawn, no matter what qualification
        # had put there. A devanture's head sits over the light the same way
        # a window's does: the body runs from `y` to the springing, the head
        # from the springing to `y + h`, and only the fill and frame colour
        # differ (glass, mullion, not sash bar and window frame).
        head_h = 0.0
        if head_form in ("round", "segmental", "irregular"):
            head_h = min(0.5, max(0.15, w * 0.22), h * 0.6)
        _draw_shop_light(canvas, x, y, w, h - head_h, props)
        if head_h > 1e-9:
            _draw_head(
                canvas, x, y + h, w, head_h, head_form, _C["shopfront_glass"], stroke=_C["mullion"]
            )
        return

    # A28: the glass fills the opening. There used to be a ``_HEAD_MARGIN`` of
    # 0.06 m here — "the one margin left for the renderer to invent" — set in
    # from all four masonry reveals, so a 1.300 m opening drew 1.180 m of blue
    # and the facade measured 0.120 m narrower than the catalogue's own
    # ABSOLUTE says a croisée is. 1.300 m is the MASONRY OPENING (Daly's
    # measured quantity, and SOURCED), the IR states that rectangle, and a
    # renderer that quietly keeps a tenth of it is deciding the width of a
    # window — which is the one thing this file may not do. The frame is drawn
    # by the stroke on the body and by the sash bars, not by a hole in the
    # geometry.
    body_x = x
    body_w = w
    # A14.1: where the IR states how far the head rises, that IS the head's
    # depth — a round arch turned on the opening's own span rises half of it,
    # which is what the word "round" means, and the figure travels stated
    # (``head_rise``) because it is geometry and not a graphical choice. The
    # fallback below is the renderer's own long-standing default for the
    # openings whose head is a flourish rather than a dimension; nothing that
    # states no rise moves by a millimetre.
    stated_rise = _num(props, "head_rise", 0.0)
    head_h = stated_rise if stated_rise > 1e-9 else min(0.5, max(0.15, body_w * 0.30))
    head_h = min(head_h, h)

    # A14.1: which register of a two-storey entrance arch this rectangle is,
    # read straight off the IR. "leaves" is the rez-de-chaussée — the leaves
    # with the carved tympanum panel standing on them and NO head, because the
    # head is a storey up; the head register is drawn by its own branch below.
    arch_register = props.get("arch_register")

    if opening_kind == "carriage_entrance":
        # ``carriage_entrance_in_slot`` already returns ``sill=0`` — the door
        # runs from the pavement, so ``y`` IS the threshold with nothing to add.
        body_bot = y
        body_top = y + h - head_h if head_form in ("round", "segmental") else y + h
        if arch_register == "leaves":
            body_top = y + _leaf_top(props, h)
        canvas.rect(body_x, body_bot, body_w, body_top - body_bot, _C["door"], stroke_w=1.0)
        springing = _draw_head(canvas, body_x, y + h, body_w, head_h, head_form, _C["door"])
        if arch_register == "leaves":
            springing = body_top
            _draw_tympanum(
                canvas, body_x, body_top, body_w, y + h - body_top, joinery=True
            )
        cx = body_x + body_w / 2.0
        canvas.line(cx, body_bot, cx, springing, _C["door_dark"], 1.4)
        _draw_door_panels(canvas, body_x, body_bot, body_w, springing - body_bot)
        return

    if opening_kind == "entrance_arch_head":
        # A14.1, the upper register of the two-storey arch: the light behind
        # the balconette, the round head over it, and the moulded archivolt
        # following the curve. The garde-corps across it is its own IR node
        # (compose.py hangs it in this light's width) and is drawn after this,
        # so the ironwork lands in front of the glass exactly as it does at
        # the Impératrice.
        #
        # The jambs run down out of this rectangle into the register below
        # without a joint: there is no sill here and nothing is drawn across
        # the bottom edge, which is what makes two stacked rectangles read as
        # one arch cut through two storeys.
        springing = y + h - head_h
        # A20.1: read, never chosen here. A carriage arch is filled in the
        # leaves' own timber, so the opening reads as ONE SOLID DOOR from the
        # threshold to the crown — which is what 39 rue Neuve des Mathurins
        # draws, its carved panel standing on the leaves and the arch closing
        # over both. A pedestrian one is glazed: 2 et 4 bd de Sébastopol puts
        # an overlight there, because a stairhall has to get its light
        # somewhere and a carriage passage does not.
        infill = props.get("head_infill") or "glazed"
        # A20.4: a glazed imposte is glazed in the BUILDING's own glass. It used
        # to take `door_glass`, a grey-blue that appears nowhere else on the
        # facade, so the head read as a pale blank panel in a foreign material
        # rather than as a light over a door.
        fill = _C["door"] if infill == "tympanum" else _C["window"]
        canvas.rect(
            body_x, y, body_w, max(0.0, springing - y),
            fill, stroke=_C["door_dark"], stroke_w=0.8,
        )
        _draw_head(
            canvas, body_x, y + h, body_w, head_h, head_form,
            fill, stroke=_C["door_dark"],
        )
        _draw_archivolt(canvas, body_x, springing, body_w, head_h)
        # The impost the arch springs from, across the light's own width —
        # the line that says the curve starts HERE and not at the joint
        # between the two storeys, which is a whole register lower down.
        canvas.line(x, springing, x + w, springing, _C["cornice_stroke"], 0.7)
        cx = body_x + body_w / 2.0
        canvas.line(cx, y, cx, springing, _C["door_dark"], 0.8)

        # A20.4: the iron grille across a glazed imposte, radiating from the
        # springing's mid-point the way a fanlight's bars do. The COUNT is the
        # IR's (`head_bar_count`); nothing is chosen here.
        bars = _count(props, "head_bar_count", 0)
        if infill != "tympanum" and bars > 1 and head_h > 1e-9:
            import math

            radius = body_w / 2.0
            for i in range(1, bars):
                angle = math.pi * i / bars
                canvas.line(
                    cx,
                    springing,
                    cx - radius * math.cos(angle),
                    springing + min(head_h, radius) * math.sin(angle),
                    _C["iron"],
                    0.5,
                )
        return

    if opening_kind == "pedestrian_entrance":
        # A8.1 (D1): the porte piétonne fell through to the generic window
        # path below and drew as a window — exactly half the building stock
        # (``catalogue.entrance_for``: every street under 12 m, every modest
        # and ordinary building) had no visible door at all. This is the
        # ruler the eye measures the facade against, so it needs its own
        # drawing: a panelled timber leaf, not glass in a frame.
        #
        # ``pedestrian_entrance_in_slot`` returns ``sill=0`` exactly like the
        # carriage entrance — the door runs from the pavement, so ``y`` IS
        # the threshold. ``qualify.base`` states a flat head "with the
        # imposte under it" (the fanlight over the leaves), so a flat head
        # gets its own glazed band rather than nothing; an arched head (a
        # hand-built node could still state one) puts the glass IN the arch
        # instead, the way a real arched doorway with a fan light over it
        # does.
        arched = head_form in ("round", "segmental", "irregular", "ogee")
        fan_h = head_h if arched else min(head_h, max(0.22, body_w * 0.4), h)
        if props.get("fanlight_h"):
            # A fanlight as tall as the IR says, its bars as many as it says.
            fan_h = min(_num(props, "fanlight_h"), h)
            body_top = y + h - fan_h
            canvas.rect(body_x, y, body_w, body_top - y, _C["door"], stroke=_C["door_dark"], stroke_w=1.0)
            _draw_door_panels(canvas, body_x, y, body_w, body_top - y)
            canvas.line(body_x + body_w / 2.0, y, body_x + body_w / 2.0, body_top, _C["door_dark"], 1.4)
            draw_fanlight(canvas, body_x, body_top, body_w, fan_h, props)
            return
        body_bot = y
        body_top = y + h - fan_h
        # A14.1: on the lower register of a two-storey arch there is no
        # fanlight in this rectangle — the leaves stop where the IR says they
        # stop and the carved tympanum takes the rest, with the imposte and
        # the fan a storey above inside the arch.
        if arch_register == "leaves":
            body_top = y + _leaf_top(props, h)
        canvas.rect(body_x, body_bot, body_w, body_top - body_bot, _C["door"], stroke=_C["door_dark"], stroke_w=1.0)
        _draw_door_panels(canvas, body_x, body_bot, body_w, body_top - body_bot)
        if arch_register == "leaves":
            _draw_tympanum(
                canvas, body_x, body_top, body_w, y + h - body_top, joinery=True
            )
        elif arched:
            _draw_head(canvas, body_x, y + h, body_w, fan_h, head_form, _C["door_glass"], stroke=_C["door_dark"])
        else:
            canvas.rect(body_x, body_top, body_w, fan_h, _C["door_glass"], stroke=_C["door_dark"], stroke_w=0.8)
        cx = body_x + body_w / 2.0
        canvas.line(cx, body_bot, cx, body_top, _C["door_dark"], 1.4)
        return

    # A28: vertically too. The reveal was applied on all four sides, so the
    # glass lost 0.120 m of height as well as of width; the light now runs
    # from the stated sill to the stated head.
    body_bot = y
    body_top = y + h - (head_h if head_form in _ARCHED else 0.0)
    body_top = max(body_bot, body_top)
    glazing = props.get("glazing")
    if props.get("relieving_arch_rise"):
        draw_relieving_arch(canvas, x, y + h, w, props)
    glass = _GLASS_FILL.get(str(glazing), _C["window"])
    canvas.rect(body_x, body_bot, body_w, body_top - body_bot, glass, stroke=_C["window_frame"], stroke_w=0.8)
    springing = _draw_head(canvas, body_x, y + h, body_w, head_h, head_form, glass)
    if glazing in GLAZINGS:
        draw_glazing(canvas, body_x, body_bot, body_w, springing - body_bot, props)
    if props.get("archivolt"):
        _draw_head_band(canvas, body_x, springing, body_w, head_h, head_form, str(props.get("archivolt")), _num(props, "archivolt_stilt", 0.0))
    if props.get("head_finial"):
        _draw_finial(canvas, body_x + body_w / 2.0, y + h, _num(props, "finial_h", 0.0))
    if glazing in GLAZINGS:
        return
    mid_x = body_x + body_w / 2.0
    canvas.line(mid_x, body_bot, mid_x, springing, _C["window_frame"], 0.6)
    transom_y = body_bot + (springing - body_bot) * 0.62
    canvas.line(body_x, transom_y, body_x + body_w, transom_y, _C["window_frame"], 0.5)


def _panes_across(span: float, pane_max: float) -> int:
    """How many equal panes a light ``span`` metres across divides into so
    that no single sheet of glass exceeds ``pane_max``.

    The same converter as ``_bays_for_gap``, and for the same reason: the
    limit is an ABSOLUTE the IR states (``pane_max_span`` — the largest sheet
    the glassworks of that decade could deliver), and this turns the metre
    into the count that honours it, rounding UP because rounding down is the
    direction that breaks it. It is not a rhythm chosen here.
    """
    if pane_max <= 1e-9 or span <= 1e-9:
        return 1
    return max(1, math.ceil(span / pane_max - 1e-9))


def _draw_shop_light(
    canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]
) -> None:
    """The glass of a devanture, and only the glass.

    Its rectangle is the opening's own — the trumeau either side is masonry
    the storey already drew and nothing here reaches into it. The glazing
    bars come from ``pane_max_span``: a shop window's subdivision is the
    manufacturing limit of its decade, which S5 resolved along with the
    devanture's form, so the count is converted here and not chosen here.
    """
    canvas.rect(x, y, w, h, _C["shopfront_glass"], stroke=_C["mullion"], stroke_w=1.2)
    pane_max = _num(props, "pane_max_span", 0.0)
    if pane_max <= 1e-9:
        return
    cols = _panes_across(w, pane_max)
    rows = _panes_across(h, pane_max)
    for i in range(1, cols):
        bx = x + i * w / cols
        canvas.line(bx, y, bx, y + h, _C["mullion"], 0.6)
    for j in range(1, rows):
        by = y + j * h / rows
        canvas.line(x, by, x + w, by, _C["mullion"], 0.5)


def _leaf_top(props: Mapping[str, object], h: float) -> float:
    """How far up its register a two-storey arch's leaves reach, in metres.

    ``leaf_height`` is the door's ABSOLUTE clear height — the same number the
    one-storey door has, because what passes through the gate did not change
    when the arch got taller. It is read, never derived: the whole point of
    A14 is that the leaves stay put while the arch grows, and a renderer
    taking a fraction of the register would make the leaves grow with it.
    Falls back to the whole rectangle for a hand-built node that states no
    leaf height, which is the plainest honest reading of "a door".
    """
    stated = _num(props, "leaf_height", 0.0)
    if stated <= 1e-9:
        return h
    return min(stated, h)


def _draw_tympanum(
    canvas: Canvas, x: float, y: float, w: float, h: float, *, joinery: bool = False
) -> None:
    """The carved panel standing on the leaves of a two-storey arch (A14.1).

    At the Avenue de l'Impératrice this is a band of rosettes between two
    mouldings, filling the gap between the tops of the leaves and the
    entresol floor. Drawn as the moulded panel it is — a framed field with a
    carved centre — and not as a row of anything: how many rosettes would be
    ornament density, which is a decision, and nothing here is entitled to
    take one.

    **A20.1: on an entrance it is JOINERY, and it is drawn in the leaves' own
    timber.** It used to take the stone palette everywhere, which put a pale
    masonry band across the opening between the leaves and the arch — the
    "masonry piece between the RdC and the entresol" the operator reported, and
    the reason the door did not read as one door. Both plates draw it as part
    of the door: at 2 et 4 bd de Sébastopol the carved overpanel above the
    leaves is wood, inside the same frame and the same tone as them; at 39 rue
    Neuve des Mathurins the carved tympanum sits inside the archivolt over
    leaves it is continuous with. Neither is stone, and neither spans anything
    the door does not.
    """
    if h <= 1e-9 or w <= 1e-9:
        return
    field = _C["door"] if joinery else _C["ornament"]
    centre = _C["door_dark"] if joinery else _C["keystone"]
    edge = _C["door_dark"] if joinery else _C["cornice_stroke"]
    canvas.rect(x, y, w, h, field, stroke=edge, stroke_w=0.7)
    inset = min(h * 0.22, w * 0.06)
    canvas.rect(
        x + inset, y + inset, max(0.0, w - 2 * inset), max(0.0, h - 2 * inset),
        centre, stroke=edge, stroke_w=0.4,
    )
    cx, cy = x + w / 2.0, y + h / 2.0
    canvas.circle(cx, cy, max(0.0, min(h, w) * 0.16), field, stroke=edge, stroke_w=0.4)


def _draw_archivolt(canvas: Canvas, x: float, y_spring: float, w: float, rise: float) -> None:
    """The moulded band following the curve of an arch head.

    Two concentric arcs struck from the same centre as the head itself, so
    the moulding sits on the opening rather than near it. This is what a
    ``moulded_architrave`` becomes when the opening it frames is round, and
    it is why the head register of a two-storey arch states no rectangular
    surround: a stone frame boxing in a semicircle is a drawing of a mistake.
    """
    if rise <= 1e-9 or w <= 1e-9:
        return
    # Shallow enough that the agrafe at the crown — its own IR node, drawn
    # after this — breaks through the band and reads as the stone that locks
    # the arch, which is what it is on the plate.
    band = min(rise * 0.10, w * 0.05)
    outer = _arch_points(x - band, x + w + band, y_spring, rise + band)
    inner = list(reversed(_arch_points(x, x + w, y_spring, rise)))
    canvas.polygon(
        outer + inner, _C["surround_moulded_architrave"], stroke=_C["cornice_stroke"], stroke_w=0.6
    )


def _draw_door_panels(canvas: Canvas, x: float, y: float, w: float, h: float) -> None:
    panel_w = w * 0.35
    for dx in (x + (w / 2 - panel_w) / 2, x + w / 2 + (w / 2 - panel_w) / 2):
        for frac in (0.12, 0.45):
            canvas.rect(dx, y + h * frac, panel_w, h * 0.22, _C["door_panel"], stroke=_C["door_dark"], stroke_w=0.5)


def _draw_roundel(canvas: Canvas, cx: float, cy: float, r: float, steps: int = 24) -> None:
    pad = r * 0.18
    outer = [
        (cx + (r + pad) * math.cos(2 * math.pi * i / steps), cy + (r + pad) * math.sin(2 * math.pi * i / steps))
        for i in range(steps + 1)
    ]
    canvas.polygon(outer, _C["surround_bare_band"], stroke=_C["window_frame"], stroke_w=0.6)
    glass = [
        (cx + r * math.cos(2 * math.pi * i / steps), cy + r * math.sin(2 * math.pi * i / steps))
        for i in range(steps + 1)
    ]
    canvas.polygon(glass, _C["window"], stroke=_C["window_frame"], stroke_w=0.5)
    canvas.line(cx - r, cy, cx + r, cy, _C["window_frame"], 0.4)
    canvas.line(cx, cy - r, cx, cy + r, _C["window_frame"], 0.4)


# ---------------------------------------------------------------------------
# Surrounds
# ---------------------------------------------------------------------------


def draw_surround(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    C = _palette(props)
    surround_form = props.get("surround_kind")
    if not surround_form or surround_form == "none":
        return
    if surround_form == "dentil_panel":
        _draw_dentil_panel(canvas, x, y, w, h, _count(props, "ornament_count", 3))
        return
    if surround_form in ("door_pilasters", "door_pediment", "door_scrolls"):
        _draw_door_frame(canvas, x, y, w, h, surround_form, props)
        return
    pad = 0.05
    fill = C.get(f"surround_{surround_form}", C["surround_bare_band"])
    stroke_w = {"bare_band": 0.5, "moulded_architrave": 0.9, "pedimented": 0.9, "irregular": 0.6}.get(
        surround_form, 0.5
    )
    canvas.rect(x - pad, y - pad, w + 2 * pad, h + 2 * pad, "none", stroke=fill, stroke_w=stroke_w * 2.0)
    if surround_form == "moulded_architrave":
        canvas.rect(x - pad * 1.6, y - pad * 1.6, w + 3.2 * pad, h + 3.2 * pad, "none", stroke=fill, stroke_w=0.6)
    if surround_form == "pedimented":
        ped_w = w * 0.85
        ped_x = x + (w - ped_w) / 2.0
        ped_h = 0.18
        top = y + h + pad
        canvas.polygon(
            [(ped_x, top), (ped_x + ped_w / 2.0, top + ped_h), (ped_x + ped_w, top)],
            fill,
            stroke=C["cornice_stroke"],
            stroke_w=0.7,
        )
    if surround_form == "irregular":
        canvas.line(x - pad, y - pad, x + w + pad, y + h + pad, fill, 0.4)


def _draw_dentil_panel(canvas: Canvas, x: float, y: float, w: float, h: float, n: int) -> None:
    """A rectangular frame of white stone round an opening (the Venetian
    "cornice a riquadro"): jambs, a sill, and a head band with a row of
    dentils along its lower edge -- ``n`` of them, the IR's count."""
    band = 0.15
    stone, edge = _C["istrian"], _C["istrian_line"]
    canvas.rect(x - band, y - 0.06, band, h + band + 0.06, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x + w, y - 0.06, band, h + band + 0.06, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x - band, y + h, w + 2 * band, band, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x - band, y - 0.06, w + 2 * band, 0.06, stone, stroke=edge, stroke_w=0.4)
    step = (w + 2 * band) / n
    for i in range(n):
        canvas.rect(x - band + (i + 0.25) * step, y + h - 0.07, step * 0.5, 0.07, stone, stroke=edge, stroke_w=0.25)


# ---------------------------------------------------------------------------
# Keystones
# ---------------------------------------------------------------------------


def draw_keystone(canvas: Canvas, cx: float, y_top: float, props: Mapping[str, object]) -> None:
    C = _palette(props)
    kind = props.get("keystone_kind") or "plain"
    if kind == "patera":
        # A carved roundel set in a spandrel, centred where the IR puts it and
        # as wide as it says.
        r = _num(props, "w", 0.4) / 2.0
        canvas.circle(cx, y_top, r, C["istrian"], stroke=C["istrian_line"], stroke_w=0.5)
        canvas.circle(cx, y_top, r * 0.55, C["ornament"], stroke=C["istrian_line"], stroke_w=0.3)
        return
    w_top, w_bot, h = 0.12, 0.20, 0.18
    if kind == "console_volute":
        w_bot, h = 0.24, 0.24
    elif kind in ("mascaron", "figurative_caryatid_atlante"):
        w_bot, h = 0.28, 0.30
    pts = [
        (cx - w_top / 2, y_top + h),
        (cx + w_top / 2, y_top + h),
        (cx + w_bot / 2, y_top),
        (cx - w_bot / 2, y_top),
    ]
    canvas.polygon(pts, C["keystone"], stroke=C["cornice_stroke"], stroke_w=0.5)
    if kind in ("mascaron", "figurative_caryatid_atlante"):
        canvas.circle(cx, y_top + h * 0.55, w_bot * 0.22, C["ornament"], stroke=C["cornice_stroke"], stroke_w=0.4)
    elif kind == "console_volute":
        canvas.circle(cx - w_bot * 0.18, y_top + h * 0.35, w_bot * 0.14, C["ornament"], stroke=C["cornice_stroke"], stroke_w=0.3)
        canvas.circle(cx + w_bot * 0.18, y_top + h * 0.35, w_bot * 0.14, C["ornament"], stroke=C["cornice_stroke"], stroke_w=0.3)


# ---------------------------------------------------------------------------
# Horizontal lines: cornice, string course, socle
# ---------------------------------------------------------------------------


def draw_cornice(canvas: Canvas, x: float, y: float, w: float, props: Mapping[str, object]) -> None:
    C = _palette(props)
    projection = _num(props, "projection", 0.1)
    depth = max(0.08, projection * 0.5)
    overhang = 0.10
    shadow_h = 0.04
    canvas.rect(x - overhang, y - shadow_h, w + 2 * overhang, shadow_h, "#B0A898", stroke_w=0.0)
    # A4.3: which bracket style to draw is read straight off the resolved
    # decision (``compose.py`` already turned the richness float into this
    # string, at the one threshold a person could argue about) — no float,
    # no threshold, and no local variable standing in for a forbidden key.
    # A7.2: how many brackets is `ornament_count`, stated for whichever of the
    # two vocabularies this cornice carries. The renderer used to hold a
    # spacing for each (0.5 m of modillion, 0.12 m of dentil) and divide the
    # frontage by it, so a modest attic cornice and a grand entresol's carried
    # the same brackets per metre and only the wall behind them changed size.
    n = _count(props, "ornament_count", 2)
    if props.get("cornice_ornament") == "corbelled_eave":
        _draw_corbelled_eave(canvas, x, y, w, max(0.3, projection), n)
        return
    if props.get("cornice_ornament") == "tiled":
        # A pent roof of clay tiles: a sloped band from the wall out to the
        # drip, its courses read as lines along it.
        reach = max(0.3, projection)
        rise = reach * 0.45
        canvas.polygon(
            [(x - reach * 0.5, y), (x + w + reach * 0.5, y), (x + w, y + rise), (x, y + rise)],
            C["tile"],
            stroke=C["tile_line"],
            stroke_w=0.6,
        )
        for k in range(1, 4):
            ty = y + rise * k / 4.0
            inset = reach * 0.5 * (1 - k / 4.0)
            canvas.line(x - inset, ty, x + w + inset, ty, C["tile_line"], 0.4)
        return
    if props.get("cornice_ornament") == "bracketed":
        # A deep crowning cornice on scrolled brackets, the frieze between
        # them: the console's size is the cornice's own stated depth.
        frieze = depth * 1.3
        canvas.rect(x, y - frieze, w, frieze, C["cornice"], stroke=C["cornice_stroke"], stroke_w=0.4)
        spacing = w / max(1, n - 1)
        bw = min(0.30, spacing * 0.3)
        for i in range(n):
            bx = x + i * spacing
            canvas.polygon(
                [(bx - bw / 2, y), (bx + bw / 2, y), (bx + bw / 4, y - frieze * 1.15), (bx - bw / 4, y - frieze * 1.15)],
                C["ornament"],
                stroke=C["cornice_stroke"],
                stroke_w=0.4,
            )
        lip = min(projection * 0.35, 0.35)
        canvas.rect(x - lip, y, w + 2 * lip, depth * 0.45, C["cornice"], stroke=C["cornice_stroke"], stroke_w=0.4)
        canvas.rect(x - lip * 1.2, y + depth * 0.45, w + 2.4 * lip, depth * 0.3, C["cornice"], stroke=C["cornice_stroke"], stroke_w=0.5)
        return
    if props.get("cornice_ornament") in ("console_pair", "dentilled_lijst"):
        _draw_lijst(canvas, x, y, w, projection, n, str(props.get("cornice_ornament")))
        return
    if props.get("cornice_ornament") == "dentil_eave":
        _draw_dentil_eave(canvas, x, y, w, max(0.3, projection), n)
        return
    if props.get("cornice_ornament") == "modillioned":
        # Modillions: chunky brackets, evenly spread along the run.
        spacing = w / n
        for i in range(n + 1):
            mx = x + i * spacing
            canvas.rect(mx - 0.05, y - shadow_h - 0.08, 0.10, 0.08, C["cornice"], stroke=C["cornice_stroke"], stroke_w=0.3)
    else:
        spacing = (w + 2 * overhang) / n
        for i in range(n):
            dx = x - overhang + i * spacing + spacing / 2
            canvas.rect(dx, y - shadow_h - 0.04, 0.06, 0.04, C["cornice"], stroke=C["cornice_stroke"], stroke_w=0.3)
    canvas.rect(x - overhang, y, w + 2 * overhang, depth, C["cornice"], stroke_w=0.0)
    canvas.rect(x - overhang, y, w + 2 * overhang, depth, "none", stroke=C["cornice_stroke"], stroke_w=0.3)


def _draw_corbelled_eave(canvas: Canvas, x: float, y: float, w: float, reach: float, n: int) -> None:
    """A Venetian eaves cornice: a dentilled stone band on the wall, ``n``
    stone corbels on it carrying a moulded corona, and the tile eave over all,
    the whole as deep as the IR's projection."""
    stone, edge = _C["istrian"], _C["istrian_line"]
    band = reach * 0.2
    canvas.rect(x, y, w, band, stone, stroke=edge, stroke_w=0.4)
    spacing = w / max(1, n - 1)
    for i in range(n):
        bx = x + i * spacing
        canvas.polygon(
            [(bx - 0.06, y + band), (bx + 0.06, y + band), (bx + 0.12, y + reach * 0.62), (bx - 0.12, y + reach * 0.62)],
            stone, stroke=edge, stroke_w=0.4,
        )
    canvas.rect(x - reach * 0.3, y + reach * 0.62, w + reach * 0.6, reach * 0.18, stone, stroke=edge, stroke_w=0.5)
    canvas.rect(x - reach * 0.45, y + reach * 0.8, w + reach * 0.9, reach * 0.2, _C["roof_coppi"], stroke=_C["roof_coppi_line"], stroke_w=0.5)


def draw_brace(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """A diagonal timber across its own rectangle, rising left to right or
    falling, as the IR says."""
    stroke = float(props.get("stroke_w", 2.2))
    color = _C.get(str(props.get("paint")), _C["timber"])
    if props.get("direction") == "rising":
        canvas.line(x, y, x + w, y + h, color, stroke)
    else:
        canvas.line(x, y + h, x + w, y, color, stroke)


def draw_column(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """An engaged column or pilaster standing on a pier, ``(x, y, w, h)`` being
    its own rectangle. ``order`` says what its capital is; nothing here
    decides where it stands or how wide it is."""
    if w <= 1e-9 or h <= 1e-9:
        return
    order = props.get("order") or "pilaster"
    if order == "timber":
        # A post of a timber frame: oak, dark, square-edged, no base or cap.
        canvas.rect(x, y, w, h, _C["timber"], stroke_w=0.0)
        return
    if order == "louvre":
        # A slat or stile of a painted louvered leaf; its paint is the rule's.
        canvas.rect(x, y, w, h, _C.get(f"louvre_{props.get('louvre_paint') or 'green'}", _C["timber"]), stroke_w=0.0)
        return
    if order == "louvre_panel":
        # A panel of a painted leaf: the leaf's paint, its moulding a darker line.
        canvas.rect(x, y, w, h, _C.get(f"louvre_{props.get('louvre_paint') or 'green'}", _C["timber"]), stroke=_C["scuri_line"], stroke_w=0.4)
        return
    if order == "iron":
        # A bar or rail of wrought or cast iron.
        canvas.rect(x, y, w, h, _C["iron"], stroke_w=0.0)
        return
    if order == "corner_board":
        # The painted board that closes a timber-clad corner.
        canvas.rect(x, y, w, h, _C["wall_clapboard_cream"], stroke=_C["column_stroke"], stroke_w=0.3)
        return
    if order in ("colonnette", "byzantine"):
        _draw_colonnette(canvas, x, y, w, h, _num(props, "shaft_width", w * 0.6), order)
        return
    if order == "arris":
        # The plain stone arris of a tower standing a little forward.
        canvas.rect(x, y, w, h, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.5)
        canvas.line(x + w * 0.5, y, x + w * 0.5, y + h, _C["istrian_line"], 0.3)
        return
    if order == "dentil_strip":
        # A strip of white stone up a corner, its inner edge dentilled.
        canvas.rect(x, y, w, h, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
        teeth = _count(props, "course_rows", 0)
        if teeth > 1:
            # The saw-tooth (dente di sega) along the edge facing the wall.
            inner = x + w if props.get("side") == "left" else x
            out = 1.0 if props.get("side") == "left" else -1.0
            tooth = h / teeth
            depth = _num(props, "tooth_depth", 0.0)
            pts = [(inner, y)]
            for i in range(teeth):
                pts += [(inner + out * depth, y + (i + 0.5) * tooth), (inner, y + (i + 1) * tooth)]
            canvas.polygon(pts, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
            return
        canvas.line(x + w * 0.5, y, x + w * 0.5, y + h, _C["istrian_line"], 1.2, dash="1.2,1.4")
        return
    if order == "quoins":
        # Istrian quoins up a corner: long and short blocks in turn, the short
        # ones as wide as the IR's ``short_w``; ``course_rows`` of them.
        n = _count(props, "course_rows", 2)
        short = _num(props, "short_w", w)
        left = props.get("side") == "left"
        for i in range(n):
            bw = w if i % 2 == 0 else short
            bx = x if left else x + w - bw
            canvas.rect(bx, y + h * i / n, bw, h / n, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
        return
    if order == "piloti":
        # A round concrete post: no base, no capital, a shadow down one side.
        canvas.rect(x, y, w, h, _C["wall_render_white"], stroke=_C["column_stroke"], stroke_w=0.4)
        canvas.rect(x + w * 0.62, y, w * 0.38, h, "#D8D6D0", stroke_w=0.0)
        return
    base_h = _num(props, "base_h", min(0.12, h * 0.05))
    cap_h = _num(props, "cap_h", min(0.30, h * 0.09) if order == "corinthian" else min(0.14, h * 0.05))
    shaft_w = w * (0.78 if order != "pilaster" else 0.9)
    sx = x + (w - shaft_w) / 2.0
    stone = _C.get(str(props.get("paint")), _C["column"])
    canvas.rect(x, y, w, base_h, stone, stroke=_C["column_stroke"], stroke_w=0.4)
    canvas.rect(sx, y + base_h, shaft_w, h - base_h - cap_h, stone, stroke=_C["column_stroke"], stroke_w=0.4)
    if order != "pilaster":
        # Fluting reads as two hairlines on a shaft this narrow.
        for f in (0.33, 0.67):
            fx = sx + shaft_w * f
            canvas.line(fx, y + base_h + 0.05, fx, y + h - cap_h - 0.05, _C["column_stroke"], 0.25)
    if order == "corinthian":
        canvas.polygon(
            [(sx, y + h - cap_h), (sx + shaft_w, y + h - cap_h), (x + w, y + h), (x, y + h)],
            _C["ornament"],
            stroke=_C["column_stroke"],
            stroke_w=0.4,
        )
        canvas.line(x + w * 0.2, y + h - cap_h * 0.45, x + w * 0.8, y + h - cap_h * 0.45, _C["column_stroke"], 0.3)
    else:  # doric and pilaster: a plain block capital
        canvas.rect(x, y + h - cap_h, w, cap_h, stone, stroke=_C["column_stroke"], stroke_w=0.4)


def _draw_colonnette(canvas: Canvas, x: float, y: float, w: float, h: float, shaft_w: float, order: str) -> None:
    """A colonnette whose top is the springing of the arches it carries: a
    smooth round shaft as wide as the IR says, on a small base, under a
    capital as wide as the column's own rectangle -- a flared foliage capital
    under a thin abacus (Gothic), or a basket capital under an impost block
    (Byzantine). No fluting: these are not a classical order."""
    shaft_w = min(shaft_w, w)
    stone, edge = _C["column"], _C["column_stroke"]
    base_h = min(0.14, h * 0.05)
    cap_h = min(0.42, h * 0.12)
    sx = x + (w - shaft_w) / 2.0
    base_w = min(w, shaft_w * 1.45)
    canvas.rect(x + (w - base_w) / 2.0, y, base_w, base_h, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(sx, y + base_h, shaft_w, h - base_h - cap_h, stone, stroke=edge, stroke_w=0.4)
    canvas.line(sx + shaft_w * 0.72, y + base_h, sx + shaft_w * 0.72, y + h - cap_h, "#B9B1A0", 0.4)
    top = y + h
    if order == "byzantine":
        impost = cap_h * 0.32
        canvas.polygon(
            [(sx, top - cap_h), (sx + shaft_w, top - cap_h), (x + w * 0.88, top - impost), (x + w * 0.12, top - impost)],
            _C["ornament"], stroke=edge, stroke_w=0.4,
        )
        canvas.line(x + w * 0.25, top - cap_h * 0.55, x + w * 0.75, top - cap_h * 0.55, edge, 0.3)
        canvas.rect(x, top - impost, w, impost, _C["istrian"], stroke=edge, stroke_w=0.4)
    else:
        abacus = cap_h * 0.22
        canvas.polygon(
            [(sx, top - cap_h), (sx + shaft_w, top - cap_h), (x + w, top - abacus), (x, top - abacus)],
            _C["ornament"], stroke=edge, stroke_w=0.4,
        )
        canvas.rect(x, top - abacus, w, abacus, _C["istrian"], stroke=edge, stroke_w=0.4)


#: How each gable form finishes along its edge: the coping's weight.
_GABLE_COPING_W = {
    "step": 1.6,
    "neck": 1.2,
    "bell": 1.2,
    "straight": 1.0,
    "spire": 0.8,
    "pavilion": 0.6,
    "front_gable": 1.4,
    "stoop": 0.5,
}


def draw_gable_mass(canvas: Canvas, props: Mapping[str, object], wall: str) -> None:
    """The gable's outline, filled with its wall, drawn under the storeys that
    stand in it -- the scrolls, claws and crown are whatever the outline the
    IR states encloses beyond those storeys."""
    pts = [(float(a), float(b)) for a, b in (props.get("points") or ())]
    if len(pts) >= 3:
        canvas.polygon(pts, wall, stroke_w=0.0)


def draw_outline_edge(canvas: Canvas, props: Mapping[str, object], color: str) -> None:
    """A thin line round a painted outline, where it states an edge."""
    pts = [(float(a), float(b)) for a, b in (props.get("points") or ())]
    if not color or len(pts) < 2:
        return
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        canvas.line(x0, y0, x1, y1, color, 0.35)


def draw_gable_coping(canvas: Canvas, props: Mapping[str, object]) -> None:
    """The stone edge along the gable's outline, and the hoisting beam."""
    pts = [(float(a), float(b)) for a, b in (props.get("points") or ())]
    form = props.get("form") or "straight"
    width = _GABLE_COPING_W.get(form, 1.0)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        canvas.line(x0, y0, x1, y1, _C["gable_coping"], width + 0.8)
        canvas.line(x0, y0, x1, y1, _C["cornice_stroke"], 0.3)
    beam = props.get("hoist_beam")
    if beam:
        bx, by = (float(v) for v in beam)
        canvas.rect(bx - 0.09, by, 0.18, 0.55, _C["hoist_beam"], stroke_w=0.0)
        canvas.line(bx, by, bx, by - 1.2, _C["iron"], 0.4)


def draw_string_course(canvas: Canvas, x: float, y: float, w: float, props: Mapping[str, object]) -> None:
    """One horizontal line of the facade, in the band the IR stated for it.

    ``y`` is the LINE the course marks — a floor level, and the datum a whole
    block is aligned on (``block.py`` reads exactly this number). Which side
    of that line the moulding's mass sits on is what its *kind* means, and
    the kind is a decision qualification already took:

    * a **bandeau** (and its carved cousin) is a sill band for the storey
      above it, so its mass stands on the line;
    * a **plat_bande** is the same, thinner, with a scored joint;
    * an **entablature** CROWNS the block beneath it — the commercial base,
      whose top is exactly this line (A13.1) — so its mass hangs under the
      line, with a projecting corona along the top. Drawn above the line it
      would be invisible behind the balcon filant of the floor it is not part
      of, which is where the base's strongest horizontal used to disappear.

    The band's depth is the node's own (``projection``, which ``compose`` also
    puts in ``h``). This function used to draw ``2 x`` that number, so the IR
    stated one band and the drawing showed another — A4.1's defect in
    miniature. The catalogue's fractions absorbed the factor when it went, so
    no existing course moved.
    """
    C = _palette(props)
    course_kind = props.get("course_kind") or "bandeau"
    depth = max(0.06, _num(props, "projection", 0.05))
    if course_kind == "dentil":
        # A white stone band at the floor line, a row of dentils under it.
        n = _count(props, "ornament_count", 4)
        canvas.rect(x, y, w, depth, C["istrian"], stroke=C["istrian_line"], stroke_w=0.4)
        step = w / n
        for i in range(n):
            canvas.rect(x + (i + 0.3) * step, y - 0.07, step * 0.4, 0.07, C["istrian"], stroke=C["istrian_line"], stroke_w=0.25)
        return
    if course_kind == "paterae":
        # A band of carved paterae and square formelle in turn, standing on
        # the line the IR gives and as deep as it says.
        n = _count(props, "ornament_count", 3)
        canvas.rect(x, y, w, depth, C["istrian"], stroke=C["istrian_line"], stroke_w=0.4)
        step = w / n
        for i in range(n):
            cx, cy = x + (i + 0.5) * step, y + depth / 2.0
            if i % 2 == 0:
                r = min(depth * 0.36, step * 0.3)
                canvas.circle(cx, cy, r, C["ornament"], stroke=C["istrian_line"], stroke_w=0.4)
                canvas.circle(cx, cy, r * 0.5, C["istrian"], stroke=C["istrian_line"], stroke_w=0.3)
            else:
                side = min(depth * 0.62, step * 0.5)
                canvas.rect(cx - side / 2.0, cy - side / 2.0, side, side, C["ornament"], stroke=C["istrian_line"], stroke_w=0.4)
        return
    if course_kind == "timber_beam":
        # The sill beam a jettied storey stands on, its joist ends showing.
        canvas.rect(x, y - depth, w, depth, C["timber"], stroke_w=0.0)
        n = _count(props, "ornament_count", 2)
        for i in range(n + 1):
            jx = x + w * i / n
            canvas.rect(jx - 0.05, y - depth - 0.08, 0.10, 0.08, C["timber"], stroke_w=0.0)
        return
    if course_kind == "entablature":
        overhang = 0.06
        corona = min(depth * 0.30, 0.12)
        canvas.rect(x, y - depth, w, depth, C["string_course"], stroke_w=0.4)
        canvas.rect(x - overhang, y - corona, w + 2 * overhang, corona, C["cornice"], stroke_w=0.0)
        canvas.rect(x - overhang, y - corona, w + 2 * overhang, corona, "none", stroke=C["cornice_stroke"], stroke_w=0.4)
        canvas.line(x, y - depth, x + w, y - depth, "#A09888", 0.8)
        canvas.line(x, y - depth + corona * 0.6, x + w, y - depth + corona * 0.6, "#B8AC98", 0.4)
        return
    canvas.rect(x, y, w, depth, C["string_course"], stroke_w=0.4)
    canvas.line(x, y, x + w, y, "#A09888", 0.8)
    canvas.line(x, y + depth, x + w, y + depth, "#C8BCA8", 0.4)
    if course_kind == "plat_bande":
        canvas.line(x, y + depth * 0.5, x + w, y + depth * 0.5, "#B8AC98", 0.3)


def draw_socle(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    treatment = props.get("treatment") or "flat_incised_refends"
    fill = _C.get(f"socle_{treatment}", _C["wall_ground"])
    if treatment == "water_steps":
        # Stone steps going down into the canal at a gate: ``course_rows``
        # treads, each a little wider than the one over it, the lower ones
        # under the water line and showing through it.
        rows = _count(props, "course_rows", 1)
        spread = _num(props, "step_spread", 0.0)
        for r in range(rows):
            top = y + h - h * r / rows
            grow = spread * (r + 1)
            canvas.rect(x - grow, top - h / rows, w + 2 * grow, h / rows, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)
        canvas.rect(x - spread * rows, y, w + 2 * spread * rows, h - _num(props, "dry_h", 0.0), _C["water"], stroke_w=0.0, opacity=0.55)
        return
    if treatment in ("zocalo", "porch"):
        # A painted band at a wall's foot, or the shade inside a recessed
        # porch: one flat field in the paint the IR states.
        canvas.rect(x, y, w, h, _C.get(str(props.get("paint")), fill), stroke_w=0.0)
        return
    if treatment == "istrian_course":
        # Courses of white stone, the joints of each course breaking those
        # of the one below.
        canvas.rect(x, y, w, h, fill, stroke=_C["istrian_line"], stroke_w=0.4)
        tide = _num(props, "tide_h", 0.0)
        if tide > 1e-9:
            # The wet, weed-dark foot the tide leaves on the stone.
            canvas.rect(x, y, w, tide, _C["wet_stone"], stroke_w=0.0)
        cols = _count(props, "course_columns", 1)
        rows = _count(props, "course_rows", 1)
        for r in range(rows):
            ry = y + h * r / rows
            if r:
                canvas.line(x, ry, x + w, ry, _C["istrian_line"], 0.3)
            shift = 0.5 if r % 2 else 0.0
            for c in range(1, cols + 1):
                jx = x + w * (c - shift) / cols
                if x < jx < x + w:
                    canvas.line(jx, ry, jx, ry + h / rows, _C["istrian_line"], 0.3)
        return
    canvas.rect(x, y, w, h, _C.get(str(props.get("paint")), fill), stroke_w=0.5)
    # A7.2: the coursing of a socle is how finely the ground storey is worked,
    # and that is ornament density, not a fact about how big the wall is. So
    # the number of stones across and courses up arrives stated — this module
    # used to carry a different course height per treatment (0.32, 0.22, 0.3)
    # and divide the wall by it, which meant every rusticated ground floor in
    # Paris was coursed identically whatever it cost. What is still decided
    # here is what a course LOOKS like: a jointed block, a jittered line, a
    # straight incision. That is drawing.
    cols = _count(props, "course_columns", 1)
    rows = _count(props, "course_rows", 1)
    course_w = w / cols
    course_h = h / rows
    if treatment == "raised_bossage":
        for r in range(rows):
            for c in range(cols):
                cx = x + c * course_w + 0.03
                cy = y + r * course_h + 0.03
                canvas.rect(cx, cy, max(0.0, course_w - 0.06), max(0.0, course_h - 0.06), fill, stroke="#B8A898", stroke_w=0.4)
    elif treatment == "picturesque_rustication":
        for i in range(1, rows):
            ly = y + i * course_h
            jitter = 0.02 if i % 2 else -0.02
            canvas.line(x, ly + jitter, x + w, ly - jitter, "#A89878", 0.5)
    else:
        for i in range(1, rows):
            ly = y + i * course_h
            canvas.line(x, ly, x + w, ly, "#B8A898", 0.4)


# ---------------------------------------------------------------------------
# Balconies and ironwork
# ---------------------------------------------------------------------------


def draw_balcony_slab(canvas: Canvas, x: float, y: float, w: float, props: Mapping[str, object]) -> None:
    """The projecting floor and its brackets. The railing itself is a
    separate ``IronworkNode`` sibling — see ``draw_ironwork``."""
    projection = _num(props, "projection", 0.0)
    overhang = max(0.05, projection * 0.2)
    slab_h = _num(props, "slab_depth", 0.06)
    x0, x1 = x - overhang, x + w + overhang
    stone = props.get("slab_kind") == "stone"
    canvas.rect(x0, y - slab_h, x1 - x0, slab_h, _C["istrian"] if stone else _C["balcony_floor"], stroke=_C["cornice_stroke"], stroke_w=0.5)
    drop = _num(props, "bracket_drop", 0.0)
    if drop > 1e-9:
        # Stone corbels, as deep as the IR says, under the slab's run.
        n = _count(props, "bracket_count", 2)
        step = (w - 0.2) / (n - 1) if n > 1 else 0.0
        for i in range(n):
            bx = x + 0.1 + i * step
            canvas.polygon(
                [(bx - 0.11, y - slab_h), (bx + 0.11, y - slab_h), (bx + 0.05, y - slab_h - drop), (bx - 0.05, y - slab_h - drop)],
                _C["istrian"],
                stroke=_C["istrian_line"],
                stroke_w=0.4,
            )
        return
    # A7.2: how many consoles carry this run of slab is stated. It used to be
    # one every 1.5 m of whatever width the node happened to be, which is a
    # spacing this module chose and a density money should have.
    n_brackets = _count(props, "bracket_count", 2)
    step = w / (n_brackets - 1) if n_brackets > 1 else 0.0
    for i in range(n_brackets):
        bx = x + i * step
        canvas.polygon(
            [(bx - 0.04, y - slab_h), (bx + 0.04, y - slab_h), (bx, y - slab_h - 0.10)],
            _C["cornice"],
            stroke=_C["cornice_stroke"],
            stroke_w=0.3,
        )


def _railing_bars(
    canvas: Canvas,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    n: int,
    color: str = _C["iron"],
    stroke_w: float = 0.8,
) -> None:
    step = (x1 - x0) / n if n else 0.0
    for i in range(n + 1):
        bx = x0 + i * step
        canvas.line(bx, y0, bx, y1, color, stroke_w)


def _bays_for_gap(w: float, gap_max: float) -> int:
    """How many equal bays a railing ``w`` metres wide divides into so that no
    gap between two balusters exceeds ``gap_max``.

    ``gap_max`` is the IR's ``max_gap`` and it is ABSOLUTE — the qualification
    layer calls it "a child's head", and the brief lists "balustrade gaps
    narrow enough for a child's head" among the quantities that never scale.
    So this function does not choose a spacing; it converts a metre the IR
    already decided into the count of bars that honours it, and it always
    rounds the count UP, because rounding down is the one direction that
    breaks the rule.

    **A7.2 kept this division and deleted the one beside it**, and the pair is
    worth reading together, because they look identical and are opposites. The
    line below divides a width by a limit the IR *stated*: that is the drawing
    obeying an absolute, and the count is not a decision at all — it is the
    only count that satisfies the number qualification handed down. What used
    to sit here was a fallback, ``int(w * _UNGUARDED_RAIL_BAYS_PER_METRE)``,
    reached when the IR stated no gap: ten bars per metre, a figure this file
    invented, applied to a dimension this file was given. Same shape, and the
    exact offence the module guard exists to catch.

    So an unstated gap now gets one bay — the two end bars and nothing between
    them. Every railing this typology emits carries ``ironwork_gap_max``
    (``qualify.base.garde_corps_where_a_body_could_fall`` sets the presence
    and the gap in the same breath, so a node cannot have one without the
    other), and a hand-built node that states no gap has stated no rhythm.
    Drawing none is the honest reading of that; inventing one is not.
    """
    if gap_max <= 1e-9:
        return 1
    return max(1, math.ceil(w / gap_max - 1e-9))


def draw_ironwork(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    if h <= 1e-9 or w <= 1e-9:
        return
    # A4.3: read under its own name, not the generic "variant" the guard
    # treats as forbidden — compose.py already resolved which dated pattern
    # this is; this is drawing it, not deciding it.
    pattern = props.get("ironwork_pattern")
    ridge_position = props.get("position")
    if ridge_position == "ridge":
        _draw_cresting(canvas, x, y, w, h, pattern, _count(props, "ornament_count", 4))
        return
    if pattern == "stone_balustrade":
        _draw_stone_balustrade(canvas, x, y, w, h, _bays_for_gap(w, _num(props, "max_gap", 0.0)))
        return
    if pattern == "pluteus":
        _draw_plutei(canvas, x, y, w, h, props)
        return
    if pattern == "wall_anchor":
        draw_wall_anchor(canvas, x, y, w, h, str(props.get("anchor_form") or "bar"))
        return

    # A12.2: "guards" is the IR's own word (compose.py, A6.5/A6.6) for what
    # this length of railing stands in front of — a balcon filant's slab, or
    # a plain opening's reveal — read here, not inferred from its width or
    # its pattern. A balcon filant PROJECTS: its balustrade stands on a slab
    # (drawn separately — see ``draw_balcony_slab``) and runs unbroken across
    # the bays, so it is drawn at full weight: a dark capping rail, heavy
    # bars. A garde-corps does not project — it is a light rail set within
    # the opening reveal — so every line below is thinner and lighter, and
    # the capping rail loses the weight that would otherwise read as a
    # parapet coping rather than a window rail.
    projects = props.get("guards") == "balcon_filant"
    # **A21.3: one iron, two weights.** A12.2 gave the garde-corps a lighter
    # COLOUR as well as lighter lines, which made the same wrought iron read as
    # two different metals on one facade — a filant in black over windows
    # railed in grey. What differs between them is depth, not material: a
    # filant stands on a slab in front of the wall and a garde-corps sits in
    # the reveal behind it, so the weights stay apart and the colour does not.
    bar_color = _C["iron"]
    bar_w = 0.8 if projects else 0.4
    cap_color = "#2A2A2A"
    cap_w = 1.6 if projects else 0.5
    hairline_w = 0.9 if projects else 0.45
    accent_w = 0.7 if projects else 0.35
    thick_accent_w = 1.4 if projects else 0.6
    ornament_stroke_w = 0.5 if projects else 0.3
    ornament_line_w = 0.8 if projects else 0.4

    # The baluster rhythm belongs to the IR, not to the pattern: whatever a
    # garde-corps looks like, the gap between its bars is the same absolute
    # number, and every pattern below draws its bars on THIS count. What the
    # pattern decides is the ornament hung on them — scrolls, waves, lozenges,
    # a paired emphasis — which is drawing.
    gap_max = _num(props, "max_gap", 0.0)
    n_bays = _bays_for_gap(w, gap_max)
    # A7.2. The ornament hung on those bars is the other kind of number: a
    # scroll, a wave and a lozenge are ornament density, which is
    # PROPORTIONAL, so how many of them run along this railing is decided
    # upstream and stated. Two rhythms, two kinds, one railing — and the
    # reason the bar count above is still worked out here while this one is
    # not.
    n_ornaments = _count(props, "ornament_count", 2)

    if pattern == "timber_lattice":
        # A koshi screen: close-set timber slats between two rails, the slat
        # count read off the stated gap like any other barrier's.
        canvas.rect(x, y, w, h, "none", stroke=_C["timber"], stroke_w=0.8)
        step = w / max(1, n_bays)
        for i in range(1, n_bays):
            sx = x + i * step
            canvas.line(sx, y, sx, y + h, _C["timber"], 1.1)
        canvas.line(x, y + h * 0.82, x + w, y + h * 0.82, _C["timber"], 0.6)
        return

    top_y = y + h
    canvas.line(x, top_y, x + w, top_y, cap_color, cap_w)
    canvas.line(x, y + 0.03, x + w, y + 0.03, bar_color, hairline_w)

    if pattern == "haussmannian_scrollwork":
        _railing_bars(canvas, x, x + w, y + 0.03, top_y - 0.04, n_bays, bar_color, bar_w)
        canvas.line(x, y + h * 0.5, x + w, y + h * 0.5, bar_color, accent_w)
        n_scrolls = n_ornaments
        step = w / n_scrolls
        for i in range(n_scrolls):
            cx = x + (i + 0.5) * step
            r = min(0.06, step * 0.25)
            canvas.circle(cx, y + h * 0.5 + 0.10, r, bar_color, stroke=bar_color, stroke_w=ornament_stroke_w)
    elif pattern == "renaissance_revival":
        _railing_bars(canvas, x, x + w, y + 0.03, top_y, n_bays, bar_color, bar_w)
        for frac in (0.30, 0.70):
            canvas.line(x, y + h * frac, x + w, y + h * frac, bar_color, accent_w)
        # The paired emphasis is ornament laid over the bars, so it thickens
        # every other one rather than replacing the rhythm with its own —
        # widening a gap to make a pair is exactly what the limit forbids.
        for i in range(0, n_bays + 1, 2):
            bx = x + i * (w / n_bays)
            canvas.line(bx, y + 0.03, bx, top_y, bar_color, thick_accent_w)
    elif pattern == "whiplash_art_nouveau":
        mid_y = y + h * 0.5
        n_waves = n_ornaments
        step = w / n_waves
        for i in range(n_waves):
            wx = x + i * step
            pts = [(wx + t * step, mid_y + 0.08 * math.sin(t * math.pi * 2)) for t in (k / 8 for k in range(9))]
            for j in range(len(pts) - 1):
                canvas.line(pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], bar_color, ornament_line_w)
        _railing_bars(canvas, x, x + w, y + 0.03, top_y, n_bays, bar_color, bar_w)
    elif pattern == "lozenge_palmette":
        _railing_bars(canvas, x, x + w, y + 0.03, top_y, n_bays, bar_color, bar_w)
        n = n_ornaments
        step = w / n
        for i in range(n):
            cx = x + (i + 0.5) * step
            r = min(0.07, step * 0.3)
            mid_y = y + h * 0.5
            canvas.polygon(
                [(cx, mid_y + r), (cx + r, mid_y), (cx, mid_y - r), (cx - r, mid_y)],
                "none",
                stroke=bar_color,
                stroke_w=ornament_stroke_w,
            )
    else:
        # No dated pattern reached this cell — plain vertical bars, on the
        # same gap the IR states, because the gap is not a matter of pattern.
        _railing_bars(canvas, x, x + w, y + 0.03, top_y, n_bays, bar_color, bar_w)


def _draw_stone_balustrade(canvas: Canvas, x: float, y: float, w: float, h: float, n_bays: int) -> None:
    """A balustrade of white stone: a plinth, a colonnette on every joint of
    the IR's baluster rhythm, end posts, and a heavy handrail."""
    stone, edge = _C["istrian"], _C["istrian_line"]
    plinth, rail, post = 0.12, 0.14, 0.16
    canvas.rect(x, y, w, plinth, stone, stroke=edge, stroke_w=0.4)
    step = w / n_bays
    for i in range(1, n_bays):
        bx = x + i * step
        canvas.rect(bx - 0.055, y + plinth, 0.11, h - plinth - rail, stone, stroke=edge, stroke_w=0.3)
        canvas.rect(bx - 0.075, y + h - rail - 0.06, 0.15, 0.06, stone, stroke=edge, stroke_w=0.25)
    canvas.rect(x, y, post, h - rail, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x + w - post, y, post, h - rail, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x - 0.04, y + h - rail, w + 0.08, rail, stone, stroke=edge, stroke_w=0.5)


def _draw_cresting(
    canvas: Canvas, x: float, y: float, w: float, h: float, pattern: object, n: int
) -> None:
    """Iron cresting along a ridge — the same four dated patterns, read as a
    silhouette against the sky instead of bars between a floor and a rail.

    ``n`` is the IR's ``ornament_count`` (A7.2). Cresting guards nobody, so
    unlike a garde-corps it has no absolute gap to honour and its rhythm is
    ornament and nothing else — which is exactly why the ``int(w / 0.4)`` this
    used to run on was a decision and not an obedience.
    """
    step = w / n
    for i in range(n):
        cx = x + (i + 0.5) * step
        if pattern == "whiplash_art_nouveau":
            canvas.line(cx - step * 0.3, y, cx, y + h, _C["iron"], 1.0)
            canvas.line(cx, y + h, cx + step * 0.3, y, _C["iron"], 1.0)
        elif pattern == "lozenge_palmette":
            r = min(step * 0.35, h * 0.5)
            canvas.polygon([(cx, y), (cx + r, y + h / 2), (cx, y + h), (cx - r, y + h / 2)], "none", stroke=_C["iron"], stroke_w=0.7)
        else:
            canvas.line(cx, y, cx, y + h, _C["iron"], 1.2)
    canvas.line(x, y, x + w, y, _C["iron"], 1.0)


# ---------------------------------------------------------------------------
# Shopfront
# ---------------------------------------------------------------------------


def draw_shopfront(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """A devanture, minus its glass: the soubassement under the light and the
    enseigne board over it, in the light's own width.

    ``(x, y, w, h)`` is one shop's column of the frontage — the width of the
    light between its two trumeaux, from the pavement to the floor above —
    and ``threshold_height``/``fascia_depth`` are the two ABSOLUTE bands the
    catalogue sized (a step up from the street; a board sized by lettering a
    person reads from across it). What is between them is the light, and the
    light is the ``opening`` node's rectangle, drawn by ``draw_opening``. So
    this function never touches the glass and never touches the masonry
    either side of it.

    Before A4.1's second pass this was ONE node spanning the whole ground
    storey, x=0 to the full facade width, and it filled that rectangle with
    glass: every trumeau qualification had carved between two shops was
    painted over, the ground floor read as a curtain wall, and the shop-bay
    openings drawn afterwards showed as ghost frames misregistered against
    the band beneath them. There is no whole-frontage devanture to draw.
    """
    # A4.3: same rename as the ironwork pattern above — "shopfront_style" is
    # what S5 resolved, not the generic "variant" the guard forbids.
    treatment = props.get("shopfront_style")
    if w <= 1e-9 or h <= 1e-9:
        return
    threshold = min(_num(props, "threshold_height", 0.0), h)
    fascia = min(_num(props, "fascia_depth", 0.0), max(0.0, h - threshold))

    if threshold > 1e-9:
        # The soubassement: the step and the boarded plinth the glass sits on.
        canvas.rect(x, y, w, threshold, _C["mullion"], stroke_w=0.0)
    if fascia <= 1e-9:
        return

    board_y = y + h - fascia
    canvas.rect(x, board_y, w, fascia, _C["shopfront_signage"], stroke=_C["mullion"], stroke_w=0.6)

    if treatment == "timber_small_panes":
        # A painted fascia between pilasters: a plain board with a beaded
        # edge top and bottom.
        canvas.line(x, board_y + fascia * 0.14, x + w, board_y + fascia * 0.14, _C["mullion"], 0.5)
        canvas.line(x, board_y + fascia * 0.86, x + w, board_y + fascia * 0.86, _C["mullion"], 0.5)
    elif treatment == "cast_iron_larger_panes":
        # The iron lintel over the opening reads as a deep flat band under
        # the board it carries.
        canvas.rect(x, board_y, w, fascia * 0.34, _C["lintel"], stroke=_C["mullion"], stroke_w=0.5)
    elif treatment == "devanture_elaborate":
        # Carved joinery: a moulded cornice over the board, returning past
        # the light onto the trumeau either side the way a real one does.
        canvas.rect(x - 0.06, y + h - fascia * 0.30, w + 0.12, fascia * 0.30, _C["sill"], stroke=_C["mullion"], stroke_w=0.6)
        for cx in (x + w * 0.16, x + w * 0.84):
            canvas.circle(cx, board_y + fascia * 0.42, min(0.07, fascia * 0.24), _C["ornament"], stroke=_C["mullion"], stroke_w=0.4)
    # "plate_glass": the board and nothing on it — the whole point of the
    # form is that the glass, not the joinery, is what there is to see.


# ---------------------------------------------------------------------------
# Roof: comble mass from its own profile, dormers, chimneys
# ---------------------------------------------------------------------------


def draw_roof_mass(
    canvas: Canvas,
    facade_w: float,
    eaves: float,
    profile: Sequence[tuple[float, float]],
    props: Mapping[str, object],
) -> None:
    """Draw the comble from the (inset, height-over-eaves) profile S7 already
    computed — read here, never re-derived.

    The front slope is the same flat, foreshortened band in both cases, and
    that is geometry rather than a simplification: an elevation looks along
    the depth axis, so the whole of the comble's run back into the parcel
    collapses onto the line between the eaves and the ridge. The 45°
    diagonal, the 1884 arc and the 1902 oblique are the same band from here —
    the "same rectangle" ``terminate.py`` names.

    What ``ends`` changes is how the comble CLOSES. Between party walls it
    closes on them and there is nothing more to see. On a corner it is hipped,
    so it returns, and the section S7 emitted becomes visible along those
    returns — at the two ends of the frontage, not smeared across the whole of
    it. ``terminate.py`` decides which from the site and hands the answer over
    as ``ends``; this function only reads it.
    """
    if not profile:
        return
    material = props.get("material") or "slate"
    fill = {"zinc_roofing": _C["roof_zinc"], "thatch": _C["roof_thatch"]}.get(str(material), _C["roof_slate"])
    ends = props.get("ends")

    pts = [(float(inset), float(h)) for inset, h in profile]
    ridge_h = pts[-1][1]
    if ridge_h <= 1e-9:
        return

    # The returns, if there are any. Empty is the mid-block case, and every
    # step below then reduces to the plain band.
    #
    # A9.3: read off the roof node's own `hip_arris`, not recomputed from
    # `profile` here. `terminate.derive_hip_arris` is now the only place this
    # geometry is derived — this module used to keep its own copy (fixed at
    # A8.2 to key the pitch to the section's true reach rather than
    # `profile[-1]`), while `terminate.py` kept an unfixed one to place every
    # souche, and the two disagreed by up to 1.559 m. There is nothing left
    # to derive here. (A10.4: a THIRD caller now exists — `block._chamfer_roof`
    # calls the same function again, at the chamfer's own narrower width,
    # rather than trusting a `hip_arris` copied from the parent building's
    # wider one — but this module still only ever reads the prop.)
    arris = (
        [(float(a), float(b)) for a, b in (props.get("hip_arris") or ())]
        if ends == "hipped"
        else []
    )

    # A6.10: the brisis/terrasson break, read off the ROOF NODE's own
    # ``mansard_angles`` — ``break_pct`` and the two slope angles it broke
    # into — rather than guessed from a second-to-last polyline vertex. The
    # silhouette's points are a section sampled for legality, not for where a
    # real mansard's plane changes; a curve refined for tolerance can (and
    # does) carry an extra vertex nowhere near the actual break, or drop the
    # one point that was it. ``reglement.mansard_angles`` is the one place
    # that number is computed, terminate.py already carries it on every roof
    # (``lower_angle_deg``/``upper_angle_deg``/``break_pct``), and reading it
    # here is consuming a stated fact, not re-deriving the geometry: a 45°
    # pre-1884 comble states equal angles and a break at 100% of its height,
    # which is this function's own test for "there is no break to draw".
    break_h = None
    lower_deg, upper_deg = props.get("lower_angle_deg"), props.get("upper_angle_deg")
    break_pct = props.get("break_pct")
    if lower_deg is not None and upper_deg is not None and break_pct is not None:
        if abs(float(lower_deg) - float(upper_deg)) > 1.0 and float(break_pct) < 0.995:
            break_h = ridge_h * float(break_pct)

    _draw_roof_front_face(
        canvas,
        facade_w,
        eaves,
        ridge_h,
        arris,
        fill,
        material,
        break_h,
        _count(props, "seam_count", 4),
    )

    if break_h is not None:
        # The fold where the steep brisis meets the flatter terrasson: drawn
        # assertively (its own colour, the heaviest stroke on the roof) so it
        # reads as a change of plane, not another coursing line. It runs only
        # across the front slope, inside a return that height is on the hip.
        inset_at_break = _arris_run_at(arris, break_h)
        if inset_at_break < facade_w - inset_at_break - 1e-6:
            by = eaves + break_h
            canvas.line(inset_at_break, by, facade_w - inset_at_break, by, _C["roof_break"], 1.0)
            canvas.line(
                inset_at_break, by + 0.035, facade_w - inset_at_break, by + 0.035, _C["roof_seam_light"], 0.4
            )

    if arris:
        _draw_hip_arrises(canvas, facade_w, eaves, ridge_h, arris)


def _arris_height_at(arris: list[tuple[float, float]], run: float) -> float | None:
    """How high the hip arris stands over the eaves at ``run`` metres in from
    the end of the frontage — ``None`` past the arris, where the front slope
    reaches the ridge unbroken."""
    if not arris or run < 0.0 or run > arris[-1][0]:
        return None
    prev_x, prev_h = arris[0]
    for ax, ah in arris[1:]:
        if run <= ax:
            span = ax - prev_x
            t = (run - prev_x) / span if span > 1e-12 else 1.0
            return prev_h + t * (ah - prev_h)
        prev_x, prev_h = ax, ah
    return arris[-1][1]


def _arris_run_at(arris: list[tuple[float, float]], height: float) -> float:
    """How far in from the end of the frontage the hip arris stands at
    ``height`` over the eaves — 0.0 with no returns, i.e. the front slope
    starts at the party wall."""
    if not arris:
        return 0.0
    prev_x, prev_h = arris[0]
    for ax, ah in arris[1:]:
        if height <= ah:
            span = ah - prev_h
            t = (height - prev_h) / span if span > 1e-12 else 1.0
            return prev_x + t * (ax - prev_x)
        prev_x, prev_h = ax, ah
    return arris[-1][0]


def _roof_silhouette(
    facade_w: float, ridge_h: float, arris: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """The comble's own outline, local to the eaves (0,0) at either corner.

    With no returns this is the plain rectangle a mid-block roof always was.
    With returns (A4.5) the outline follows the hip arris up from each corner
    instead of squaring off at the full ridge height — the fix this function
    exists for. A rectangle drawn regardless of the arris is what used to make
    a narrow, steeply-hipped corner roof read as an onion dome: the arris was
    drawn as a decorative line, but the flat corners of the rectangle it sat
    inside stayed filled with roof colour on both sides of that line, so the
    strongest edge in the picture — the curve — was never actually the
    silhouette's boundary. It is now.
    """
    if not arris:
        return [(0.0, 0.0), (0.0, ridge_h), (facade_w, ridge_h), (facade_w, 0.0)]

    pts = [(0.0, 0.0)] + list(arris)
    top_run, top_h = arris[-1]
    if top_h < ridge_h - 1e-6:
        # The two hips meet before the ridge: one peak, no flat ridge run —
        # a pavilion roof, not a dome, because the outline stops rising the
        # moment the mirrored arris says it should.
        pts += [(facade_w - run, h) for run, h in reversed(arris[:-1])]
    else:
        # The arris reaches the ridge with running room to spare: a flat
        # ridge segment between the two hip heads, same as a real mansard.
        pts.append((facade_w - top_run, ridge_h))
        pts += [(facade_w - run, h) for run, h in reversed(arris[:-1])]
    pts.append((facade_w, 0.0))
    return pts


def _draw_roof_front_face(
    canvas: Canvas,
    facade_w: float,
    eaves: float,
    ridge_h: float,
    arris: list[tuple[float, float]],
    fill: str,
    material: str = "slate",
    break_h: float | None = None,
    n_seams: int = 4,
) -> None:
    """The comble's mass in elevation: a band from the eaves to the ridge.

    With no returns the band is the whole rectangle. With returns, the mass
    is clipped to the hip silhouette (``_roof_silhouette``) rather than left
    as a rectangle with a curve drawn on top of it (A4.5) — what is beyond
    the arris, toward the untouched corner of the old rectangle, was never a
    roof surface: the section the arris comes from starts its rise exactly at
    that corner, so past the curve there is nothing there but sky.

    The seams inside the mass run down the slope, away from the viewer, in
    the direction elevation foreshortens to nothing, so they project as
    verticals — each one starts at the eaves and stops where the front slope
    does (the arris, inside a return; the ridge, outside it). A6.10: on zinc
    (the material that came to dominate mid-century) each is drawn as a
    paired light/dark stroke — the standing seam itself and the shadow it
    casts — rather than the single hairline every material got before, which
    is what read as one flat grey field regardless of covering. Slate keeps
    the plain hairline: its coursing is horizontal overlap, not a vertical
    fold, and this elevation is not the view that shows it. Where
    ``break_h`` names a real brisis/terrasson break, each seam changes tone
    at it — a fact about the fold, not a second decision about the seam.
    """
    if arris:
        outline = [(x, eaves + y) for x, y in _roof_silhouette(facade_w, ridge_h, arris)]
        canvas.polygon(outline, fill, stroke=_C["roof_slope"], stroke_w=0.6)
    else:
        # No returns: the silhouette IS the rectangle, so draw it as one —
        # unchanged from before A4.5, byte for byte, on every mid-block roof.
        canvas.rect(0.0, eaves, facade_w, ridge_h, fill, stroke=_C["roof_slope"], stroke_w=0.6)

    zinc = material == "zinc_roofing"
    # A7.2: how many seams cross this slope is stated. A zinc table runs
    # 0.5-0.65 m and a slate slope reads at a coarser rhythm — both facts
    # about the covering, both now in ``catalogue.roof_seam_module``, and the
    # count they produce over this roof's own width is what arrives here. What
    # is still decided below is what a seam LOOKS like: zinc's paired
    # light/dark stroke for the standing fold and the shadow beside it, slate's
    # plain hairline. That is drawing.
    for i in range(1, n_seams):
        sx = i * facade_w / n_seams
        run = min(sx, facade_w - sx)
        stop = _arris_height_at(arris, run)
        top = eaves + (ridge_h if stop is None else stop)
        if top <= eaves + 1e-9:
            continue
        mid = eaves + break_h if break_h is not None and break_h < (top - eaves) - 1e-9 else top
        if zinc:
            canvas.line(sx, eaves, sx, mid, _C["roof_seam_dark"], 0.5)
            canvas.line(sx + 0.025, eaves, sx + 0.025, mid, _C["roof_seam_light"], 0.25)
            if mid < top - 1e-9:
                canvas.line(sx, mid, sx, top, _C["roof_seam_dark"], 0.35)
                canvas.line(sx + 0.025, mid, sx + 0.025, top, _C["roof_seam_light"], 0.18)
        else:
            canvas.line(sx, eaves, sx, mid, _C["roof_slope"], 0.3)
            if mid < top - 1e-9:
                canvas.line(sx, mid, sx, top, _C["roof_slope"], 0.2)


def _draw_hip_arrises(
    canvas: Canvas, facade_w: float, eaves: float, ridge_h: float, arris: list[tuple[float, float]]
) -> None:
    """The two hip arrises, and the ridge between their heads.

    This is the whole of what "hipped" adds to the elevation. The arris is the
    edge where the front slope stops and the return begins, so it is drawn as
    a line and not as another mass: the mass behind it is the same comble.
    """
    for sign in (1.0, -1.0):
        base = 0.0 if sign > 0 else facade_w
        prev_x, prev_h = base + sign * arris[0][0], eaves + arris[0][1]
        for run, h in arris[1:]:
            nx, nh = base + sign * run, eaves + h
            canvas.line(prev_x, prev_h, nx, nh, _C["roof_slope"], 0.9)
            prev_x, prev_h = nx, nh

    top_run, top_h = arris[-1]
    if top_h < ridge_h - 1e-6:
        # The two hips met before the ridge: the section runs back further
        # than half the frontage, so there is no separate ridge line to draw
        # along the front — the band's own top edge is the ridge.
        return
    canvas.line(top_run, eaves + ridge_h, facade_w - top_run, eaves + ridge_h, _C["roof_slope"], 0.9)


_DORMER_FORMS = frozenset({"flat_lucarne", "pedimented", "round_arched", "segmental", "oeil_de_boeuf"})


def draw_dormer(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    form = props.get("form") or "flat_lucarne"
    cx = x + w / 2.0

    if form == "oeil_de_boeuf":
        _draw_roundel(canvas, cx, y + h * 0.55, min(w, h) * 0.42)
        return

    body_h = h * 0.72
    win_pad = w * 0.18
    canvas.rect(x, y, w, body_h, _C["dormer"], stroke_w=0.6)
    canvas.rect(x + win_pad, y + h * 0.08, w - 2 * win_pad, body_h - h * 0.10, _C["dormer_window"], stroke_w=0.5)
    canvas.line(cx, y + h * 0.08, cx, y + body_h - h * 0.02, _C["window_frame"], 0.4)
    cap_y = y + body_h

    if form == "pedimented":
        ped_h = h * 0.18
        overhang = w * 0.12
        canvas.polygon(
            [(x - overhang, cap_y), (cx, cap_y + ped_h), (x + w + overhang, cap_y)],
            _C["dormer"],
            stroke_w=0.6,
        )
    elif form == "round_arched":
        arch_h = h * 0.16
        pts = _arch_points(x - w * 0.06, x + w * 1.06, cap_y, arch_h)
        canvas.polygon(pts, _C["dormer"], stroke_w=0.6)
    elif form == "segmental":
        arch_h = h * 0.13
        pts = _arch_points(x - w * 0.06, x + w * 1.06, cap_y, arch_h * 0.6)
        canvas.polygon(pts, _C["dormer"], stroke_w=0.6)
    else:  # flat_lucarne
        cap_h = h * 0.20
        overhang = w * 0.06
        canvas.rect(x - overhang, cap_y, w + 2 * overhang, cap_h, _C["roof_zinc"], stroke_w=0.6)


def draw_brisis_window(
    canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]
) -> None:
    """A window in the plane of the brisis (A19.2).

    Everything a lucarne has except the parts that make it a lucarne: a
    surround, a light and a garde-corps, and NO cheeks, no roof of its own and
    no shadow onto the slope. It is a hole in a wall, and the wall happens to
    be the roof.

    Drawn flush, which is the whole distinction being made: a lucarne is
    ``draw_dormer``'s body standing proud of the tiles, this is an opening
    reading as depth behind them.
    """
    canvas.rect(x, y, w, h, _C["dormer"], stroke_w=0.6)
    pad = w * 0.12
    glass_h = h * 0.86
    canvas.rect(
        x + pad, y + h * 0.07, w - 2 * pad, glass_h - h * 0.07,
        _C["dormer_window"], stroke=_C["window_frame"], stroke_w=0.5,
    )
    canvas.line(x + w / 2.0, y + h * 0.07, x + w / 2.0, y + glass_h, _C["window_frame"], 0.4)
    if props.get("garde_corps"):
        # The individual railing both plates put across the lower row's lights.
        rail_y = y + h * 0.07
        rail_h = h * 0.30
        canvas.rect(x + pad, rail_y, w - 2 * pad, rail_h, None, stroke=_C["iron"], stroke_w=0.5)
        bars = _count(props, "bar_count", 6)
        for i in range(1, bars):
            bx = x + pad + (w - 2 * pad) * i / bars
            canvas.line(bx, rail_y, bx, rail_y + rail_h, _C["iron"], 0.3)


def draw_chimney(canvas: Canvas, x: float, y: float, w: float, h: float) -> None:
    canvas.rect(x, y, w, h, _C["chimney"], stroke_w=0.6)
    cap_w = w * 1.2
    canvas.rect(x + w / 2.0 - cap_w / 2.0, y + h, cap_w, 0.08, _C["chimney"], stroke_w=0.6)


def draw_fumaiolo(canvas: Canvas, x: float, y: float, w: float, h: float, head_w: float, head_h: float) -> None:
    """A Venetian chimney: a plastered stack to a funnel head (fumaiolo a
    imbuto) as wide and as deep as the IR says, with a rim on top."""
    if w <= 1e-9 or h <= 1e-9:
        return
    head_h = min(head_h, h * 0.5)
    neck = y + h - head_h
    canvas.rect(x, y, w, neck - y, _C["wall_chimney_brick"], stroke=_C["outline"], stroke_w=0.4)
    cx = x + w / 2.0
    canvas.polygon(
        [(x, neck), (x + w, neck), (cx + head_w / 2.0, y + h), (cx - head_w / 2.0, y + h)],
        _C["wall_chimney_brick"], stroke=_C["outline"], stroke_w=0.4,
    )
    canvas.rect(cx - head_w / 2.0 - 0.04, y + h, head_w + 0.08, 0.1, _C["istrian"], stroke=_C["istrian_line"], stroke_w=0.4)


# ---------------------------------------------------------------------------
# Settings, glazing and the smaller carved and wrought details a lot states
# ---------------------------------------------------------------------------

#: The settings a lot can state under its front (``ground``).
SETTINGS = frozenset({"canal", "quay"})


def draw_setting(canvas: Canvas, width_px: float, height_px: float, setting: str) -> None:
    """The band under the building, across the whole drawing: canal water
    lapping the front, or a brick quay along the canal with its stone edge
    and the water beyond. Its courses and ripples are drawing, not measure."""
    x0 = -canvas.x_origin / canvas.scale
    x1 = (width_px - canvas.x_origin) / canvas.scale
    bottom = (canvas.y_origin - height_px) / canvas.scale
    water_top = 0.0
    if setting == "quay":
        kerb = -0.62
        canvas.rect(x0, kerb, x1 - x0, -kerb, _C["quay_brick"], stroke_w=0.0)
        for jy, dash in ((-0.2, "5,1.2"), (-0.41, "5,1.2")):
            canvas.line(x0, jy, x1, jy, _C["quay_joint"], 0.6)
            canvas.line(x0, jy + 0.1, x1, jy + 0.1, _C["quay_joint"], 0.3, dash=dash)
        canvas.rect(x0, kerb - 0.12, x1 - x0, 0.12, _C["quay_kerb"], stroke=_C["istrian_line"], stroke_w=0.4)
        water_top = kerb - 0.12
    canvas.rect(x0, bottom, x1 - x0, water_top - bottom, _C["water"], stroke_w=0.0)
    canvas.line(x0, water_top, x1, water_top, _C["water_dark"], 1.2)
    for depth, dash in ((0.18, "14,7"), (0.42, "9,12"), (0.7, "16,10"), (0.98, "7,13")):
        if water_top - depth > bottom:
            canvas.line(x0, water_top - depth, x1, water_top - depth, _C["water_light"], 0.7, dash=dash)


#: The glazing a light can state (``glazing``), each drawn in its own way.
GLAZINGS = frozenset({"sash", "cross_leaded", "rondel", "scuri"})
#: What shows through a light of each glazing.
_GLASS_FILL = {"cross_leaded": _C["glass_leaded"], "rondel": _C["rondel"]}
#: Joinery paint (``frame_paint``).
_FRAME_PAINT = {"white": _C["frame_white"], "ochre": _C["frame_ochre"]}
#: Shutter paint (``shutter_paint``).
_SHUTTER_PAINT = {"red": _C["shutter_red"], "green": _C["shutter_green"]}


def _lattice(canvas: Canvas, x: float, y: float, w: float, h: float, n: int, color: str) -> None:
    """Diamond leading across a light: ``n`` cames each way."""
    if n < 2 or w <= 1e-9 or h <= 1e-9:
        return
    pitch = (w + h) / n
    for k in range(1, n):
        c = k * pitch
        # x' + y' = c, and its mirror x' + (h - y') = c
        ax, ay = max(0.0, c - h), min(c, h)
        bx, by = min(c, w), c - min(c, w)
        canvas.line(x + ax, y + ay, x + bx, y + by, color, 0.3)
        canvas.line(x + ax, y + h - ay, x + bx, y + h - by, color, 0.3)


def draw_glazing(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """What fills a light below its springing, as the IR states it: sashes of
    small panes in painted frames; a cross window with leaded lights (its
    lower lights perhaps shuttered); bottle-glass roundels; or closed wooden
    shutters (scuri). Every count and every bar width is the IR's."""
    kind = props.get("glazing")
    paint = _FRAME_PAINT.get(str(props.get("frame_paint")), _C["window_frame"])
    frame = _num(props, "frame_w", 0.0)
    bar = _num(props, "bar_w", 0.0)
    if h <= 1e-9 or w <= 1e-9:
        return
    if kind == "sash":
        cols = _count(props, "sash_cols", 1)
        rows = _count(props, "sash_rows", 1)
        canvas.rect(x, y, w, h, paint, stroke=_C["window_frame"], stroke_w=0.4)
        sash_h = (h - 2 * frame - bar) / 2.0
        pane_w = (w - 2 * frame - (cols - 1) * bar) / cols
        pane_h = (sash_h - (rows - 1) * bar) / rows
        for s in range(2):
            sy = y + frame + s * (sash_h + bar)
            for i in range(cols):
                for j in range(rows):
                    canvas.rect(x + frame + i * (pane_w + bar), sy + j * (pane_h + bar), pane_w, pane_h, _C["window"], stroke_w=0.0)
        return
    if kind == "cross_leaded":
        cames = _count(props, "came_count", 0)
        shutters = _SHUTTER_PAINT.get(str(props.get("shutter_paint")))
        transom = y + h * _num(props, "transom_at", 0.6)
        canvas.rect(x, y, w, h, paint, stroke=_C["window_frame"], stroke_w=0.4)
        half = (w - 2 * frame - bar) / 2.0
        for i in range(2):
            lx = x + frame + i * (half + bar)
            upper_y = transom + bar / 2.0
            upper_h = y + h - frame - upper_y
            canvas.rect(lx, upper_y, half, upper_h, _C["glass_leaded"], stroke_w=0.0)
            _lattice(canvas, lx, upper_y, half, upper_h, cames, _C["came"])
            lower_h = transom - bar / 2.0 - (y + frame)
            if shutters is not None:
                canvas.rect(lx, y + frame, half, lower_h, shutters, stroke=_C["door_dark"], stroke_w=0.4)
                canvas.line(lx, y + frame, lx + half, y + frame + lower_h, _C["door_dark"], 0.3)
            else:
                canvas.rect(lx, y + frame, half, lower_h, _C["glass_leaded"], stroke_w=0.0)
                _lattice(canvas, lx, y + frame, half, lower_h, cames, _C["came"])
        return
    if kind == "rondel":
        cols = _count(props, "rondel_cols", 1)
        rows = _count(props, "rondel_rows", 1)
        pw, ph = w / cols, h / rows
        r = min(pw, ph) * 0.46
        for i in range(cols):
            for j in range(rows):
                canvas.circle(x + (i + 0.5) * pw, y + (j + 0.5) * ph, r, _C["rondel"], stroke=_C["rondel_line"], stroke_w=0.3)
        return
    if kind == "scuri":
        canvas.rect(x, y, w, h, _C["scuri"], stroke=_C["scuri_line"], stroke_w=0.5)
        canvas.line(x + w / 2.0, y, x + w / 2.0, y + h, _C["scuri_line"], 0.6)
        inset = min(w * 0.08, 0.08)
        for i in range(2):
            lx = x + i * w / 2.0 + inset
            for lo, hi in ((0.06, 0.45), (0.53, 0.94)):
                canvas.rect(lx, y + h * lo, w / 2.0 - 2 * inset, h * (hi - lo), "none", stroke=_C["scuri_line"], stroke_w=0.35)


def draw_relieving_arch(canvas: Canvas, x: float, y_top: float, w: float, props: Mapping[str, object]) -> None:
    """A segmental brick relieving arch over a window head: as far past the
    jambs, as high and as deep in its ring as the IR says, in ``voussoirs``
    bricks."""
    rise = _num(props, "relieving_arch_rise", 0.0)
    ring = _num(props, "relieving_ring", 0.0)
    reach = _num(props, "relieving_reach", 0.0)
    n = _count(props, "voussoirs", 2)
    if rise <= 1e-9 or ring <= 1e-9:
        return
    half = w / 2.0 + reach
    radius = (half * half + rise * rise) / (2.0 * rise)
    cx, cy = x + w / 2.0, y_top + rise - radius
    a0 = math.asin(min(1.0, half / radius))
    angles = [math.pi / 2.0 + a0 - 2.0 * a0 * k / 24 for k in range(25)]
    inner = [(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in angles]
    outer = [(cx + (radius + ring) * math.cos(a), cy + (radius + ring) * math.sin(a)) for a in angles]
    canvas.polygon(inner + list(reversed(outer)), _C["arch_brick"], stroke=_C["arch_brick_line"], stroke_w=0.4)
    for k in range(1, n):
        a = math.pi / 2.0 + a0 - 2.0 * a0 * k / n
        canvas.line(cx + radius * math.cos(a), cy + radius * math.sin(a), cx + (radius + ring) * math.cos(a), cy + (radius + ring) * math.sin(a), _C["arch_brick_line"], 0.3)


def draw_fanlight(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """The glazed light over a door, in its painted frame, its bars radiating
    from the transom's middle or standing upright, as many as the IR says."""
    paint = _FRAME_PAINT.get(str(props.get("frame_paint")), _C["door_dark"])
    canvas.rect(x, y, w, h, paint, stroke=_C["door_dark"], stroke_w=0.6)
    frame = _num(props, "frame_w", 0.0)
    gx, gy, gw, gh = x + frame, y + frame, w - 2 * frame, h - 2 * frame
    canvas.rect(gx, gy, gw, gh, _C["window"], stroke_w=0.0)
    bars = _count(props, "fanlight_bars", 0)
    weight = 0.9
    if props.get("fanlight_pattern") == "radiating":
        # Spokes from the middle of the transom to points spread evenly
        # round the light's other three edges, and a hub over them.
        perimeter = 2 * gh + gw
        for i in range(1, bars):
            t = perimeter * i / bars
            if t < gh:
                px, py = gx, gy + t
            elif t < gh + gw:
                px, py = gx + (t - gh), gy + gh
            else:
                px, py = gx + gw, gy + gh - (t - gh - gw)
            canvas.line(gx + gw / 2.0, gy, px, py, paint, weight)
        canvas.circle(gx + gw / 2.0, gy, min(gw, gh) * 0.22, paint, stroke=_C["door_dark"], stroke_w=0.3)
        return
    for i in range(1, bars):
        bx = gx + gw * i / bars
        canvas.line(bx, gy, bx, gy + gh, paint, weight)


def _draw_door_frame(canvas: Canvas, x: float, y: float, w: float, h: float, kind: str, props: Mapping[str, object]) -> None:
    """A door's carved frame: a pilaster each side and an entablature over
    the fanlight; under a pediment, or a scrolled crest, where the IR says."""
    C = _palette(props)
    stone, edge = C["gable_coping"], C["cornice_stroke"]
    pil, ent = 0.17, 0.26
    canvas.rect(x - pil, y, pil, h, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x + w, y, pil, h, stone, stroke=edge, stroke_w=0.4)
    for px in (x - pil, x + w):
        canvas.rect(px - 0.02, y + h - 0.1, pil + 0.04, 0.1, stone, stroke=edge, stroke_w=0.3)
    top = y + h
    canvas.rect(x - pil - 0.04, top, w + 2 * pil + 0.08, ent, stone, stroke=edge, stroke_w=0.4)
    canvas.rect(x - pil - 0.1, top + ent, w + 2 * pil + 0.2, 0.08, stone, stroke=edge, stroke_w=0.5)
    crown = top + ent + 0.08
    if kind == "door_pediment":
        canvas.polygon([(x - pil - 0.1, crown), (x + w / 2.0, crown + 0.42), (x + w + pil + 0.1, crown)], stone, stroke=edge, stroke_w=0.6)
    elif kind == "door_scrolls":
        cx, half = x + w / 2.0, w / 2.0 + pil
        pts = [(cx - half, crown)] + [(cx - half * math.cos(math.pi * k / 12), crown + 0.34 * math.sin(math.pi * k / 12)) for k in range(1, 12)] + [(cx + half, crown)]
        canvas.polygon(pts, stone, stroke=edge, stroke_w=0.5)
        for side in (-1.0, 1.0):
            canvas.circle(cx + side * (half - 0.1), crown + 0.1, 0.09, C["ornament"], stroke=edge, stroke_w=0.4)


def _draw_plutei(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    """A parapet of solid marble slabs (plutei) between small posts, one slab
    under each arch: each carved with a framed roundel and its cross."""
    n = _count(props, "panel_count", 1)
    post = _num(props, "post_w", 0.0)
    marble, edge = _C["marble"], _C["marble_line"]
    pitch = w / n
    canvas.rect(x, y, w, h, marble, stroke=edge, stroke_w=0.4)
    for i in range(n + 1):
        px = x + i * pitch - post / 2.0
        canvas.rect(max(x, px), y, post, h, _C["istrian"], stroke=edge, stroke_w=0.4)
    for i in range(n):
        px = x + i * pitch + post / 2.0
        pw = pitch - post
        inset = min(pw, h) * 0.12
        canvas.rect(px + inset, y + inset, pw - 2 * inset, h - 2 * inset, "none", stroke=edge, stroke_w=0.35)
        r = min(pw, h) * 0.26
        cx, cy = px + pw / 2.0, y + h / 2.0
        canvas.circle(cx, cy, r, _C["ornament"], stroke=edge, stroke_w=0.35)
        canvas.line(cx - r, cy, cx + r, cy, edge, 0.3)
        canvas.line(cx, cy - r, cx, cy + r, edge, 0.3)
    canvas.rect(x - 0.03, y + h - 0.08, w + 0.06, 0.08, _C["istrian"], stroke=edge, stroke_w=0.4)


def draw_wall_anchor(canvas: Canvas, x: float, y: float, w: float, h: float, form: str) -> None:
    """The forged end of a wall anchor (muuranker) in its rectangle: an S, a
    fleur-de-lis, a saltire or a plain bar, as the IR names it."""
    iron, wt = _C["iron"], 1.5
    cx, cy = x + w / 2.0, y + h / 2.0
    if form == "s":
        rx, ry = w * 0.45, h * 0.25
        top = [(cx + rx * math.cos(a), y + h * 0.75 + ry * math.sin(a)) for a in (math.pi * (0.15 + 1.35 * k / 12) for k in range(13))]
        low = [(cx + rx * math.cos(a), y + h * 0.25 + ry * math.sin(a)) for a in (math.pi * (0.5 - 1.35 * k / 12) for k in range(13))]
        line = top + low[1:]
        for (x0, y0), (x1, y1) in zip(line, line[1:]):
            canvas.line(x0, y0, x1, y1, iron, wt)
        return
    if form == "fleur":
        canvas.line(cx, y, cx, y + h, iron, wt)
        for sy, sign in ((y + h, -1.0), (y, 1.0)):
            for side in (-1.0, 1.0):
                pts = [(cx, sy + sign * h * 0.22)] + [(cx + side * w * 0.45 * math.sin(math.pi * k / 8), sy + sign * h * (0.22 - 0.2 * math.sin(math.pi * k / 16))) for k in range(1, 9)]
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    canvas.line(x0, y0, x1, y1, iron, wt * 0.8)
        canvas.line(cx - w * 0.3, cy, cx + w * 0.3, cy, iron, wt)
        return
    if form == "x":
        canvas.line(x, y, x + w, y + h, iron, wt)
        canvas.line(x, y + h, x + w, y, iron, wt)
        canvas.circle(cx, cy, min(w, h) * 0.09, iron, stroke=iron, stroke_w=0.3)
        return
    canvas.line(cx, y, cx, y + h, iron, wt)


def _draw_lijst(canvas: Canvas, x: float, y: float, w: float, projection: float, n: int, kind: str) -> None:
    """A canal house's straight cornice (lijst), hanging from the line it
    crowns: a frieze, and over it a corona as deep as the IR's projection.
    ``console_pair``: a few big carved consoles (``n``) with festoons between;
    ``dentilled_lijst``: the plain later lijst, a row of ``n`` dentils."""
    depth = max(0.08, projection * 0.5)
    stone, edge = _C["cornice"], _C["cornice_stroke"]
    frieze = depth * 1.2
    canvas.rect(x, y - frieze, w, frieze, stone, stroke=edge, stroke_w=0.4)
    lip = min(projection * 0.35, 0.35)
    if kind == "console_pair":
        spacing = (w - 0.3) / max(1, n - 1)
        for i in range(n):
            bx = x + 0.15 + i * spacing
            canvas.polygon([(bx - 0.13, y), (bx + 0.13, y), (bx + 0.08, y - frieze * 1.25), (bx - 0.08, y - frieze * 1.25)], _C["ornament"], stroke=edge, stroke_w=0.5)
            canvas.circle(bx, y - 0.11, 0.08, _C["ornament"], stroke=edge, stroke_w=0.4)
            canvas.circle(bx, y - frieze * 1.25 + 0.06, 0.05, _C["ornament"], stroke=edge, stroke_w=0.3)
        for i in range(n - 1):
            a, b = x + 0.15 + i * spacing + 0.18, x + 0.15 + (i + 1) * spacing - 0.18
            if b - a > 0.3:
                sag = [(a + (b - a) * k / 10, y - frieze * 0.25 - frieze * 0.45 * math.sin(math.pi * k / 10)) for k in range(11)]
                for (x0, y0), (x1, y1) in zip(sag, sag[1:]):
                    canvas.line(x0, y0, x1, y1, edge, 0.6)
    else:
        step = w / n
        for i in range(n):
            canvas.rect(x + (i + 0.25) * step, y - 0.1, step * 0.5, 0.09, stone, stroke=edge, stroke_w=0.25)
    canvas.rect(x - lip, y, w + 2 * lip, depth * 0.5, stone, stroke=edge, stroke_w=0.5)
    canvas.rect(x - lip * 0.6, y + depth * 0.5, w + 1.2 * lip, depth * 0.22, stone, stroke=edge, stroke_w=0.4)


def _draw_dentil_eave(canvas: Canvas, x: float, y: float, w: float, reach: float, n: int) -> None:
    """A Venetian stone cornice with no corbels: a band of ``n`` dentils (dente
    di sega) under a moulded corona, the tile edge just showing over it."""
    stone, edge = _C["istrian"], _C["istrian_line"]
    band = reach * 0.4
    canvas.rect(x, y, w, band, stone, stroke=edge, stroke_w=0.4)
    step = w / n
    for i in range(n):
        tx = x + i * step
        canvas.polygon([(tx, y + band), (tx + step / 2.0, y + band * 0.35), (tx + step, y + band)], _C["istrian_line"], stroke=edge, stroke_w=0.2)
    canvas.rect(x - reach * 0.25, y + band, w + reach * 0.5, reach * 0.35, stone, stroke=edge, stroke_w=0.5)
    canvas.rect(x - reach * 0.35, y + band + reach * 0.35, w + reach * 0.7, reach * 0.25, _C["roof_coppi"], stroke=_C["roof_coppi_line"], stroke_w=0.5)
