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

_HEAD_MARGIN = 0.06  # metres of frame reveal around the glass


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
    return y_spring if head_form in ("round", "segmental") else y_top


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

    # ``_HEAD_MARGIN`` — a fixed frame reveal, the glass sitting a few
    # centimetres back of the masonry reveal. This is the one margin left for
    # the renderer to invent, and it no longer stands in for the pier: it is a
    # constant, not a fraction of ``w``, so it does not grow with the opening
    # the way the old 10%-of-bay margin did.
    reveal = min(_HEAD_MARGIN, w * 0.3, h * 0.3)
    body_x = x + reveal
    body_w = max(0.0, w - 2 * reveal)
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
        arched = head_form in ("round", "segmental", "irregular")
        fan_h = head_h if arched else min(head_h, max(0.22, body_w * 0.4), h)
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

    body_bot = y + reveal
    body_top = y + h - (head_h if head_form in ("round", "segmental") else reveal)
    body_top = max(body_bot, body_top)
    canvas.rect(body_x, body_bot, body_w, body_top - body_bot, _C["window"], stroke=_C["window_frame"], stroke_w=0.8)
    springing = _draw_head(canvas, body_x, y + h - reveal, body_w, head_h, head_form, _C["window"])
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
    surround_form = props.get("surround_kind")
    if not surround_form or surround_form == "none":
        return
    pad = 0.05
    fill = _C.get(f"surround_{surround_form}", _C["surround_bare_band"])
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
            stroke=_C["cornice_stroke"],
            stroke_w=0.7,
        )
    if surround_form == "irregular":
        canvas.line(x - pad, y - pad, x + w + pad, y + h + pad, fill, 0.4)


# ---------------------------------------------------------------------------
# Keystones
# ---------------------------------------------------------------------------


def draw_keystone(canvas: Canvas, cx: float, y_top: float, props: Mapping[str, object]) -> None:
    kind = props.get("keystone_kind") or "plain"
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
    canvas.polygon(pts, _C["keystone"], stroke=_C["cornice_stroke"], stroke_w=0.5)
    if kind in ("mascaron", "figurative_caryatid_atlante"):
        canvas.circle(cx, y_top + h * 0.55, w_bot * 0.22, _C["ornament"], stroke=_C["cornice_stroke"], stroke_w=0.4)
    elif kind == "console_volute":
        canvas.circle(cx - w_bot * 0.18, y_top + h * 0.35, w_bot * 0.14, _C["ornament"], stroke=_C["cornice_stroke"], stroke_w=0.3)
        canvas.circle(cx + w_bot * 0.18, y_top + h * 0.35, w_bot * 0.14, _C["ornament"], stroke=_C["cornice_stroke"], stroke_w=0.3)


# ---------------------------------------------------------------------------
# Horizontal lines: cornice, string course, socle
# ---------------------------------------------------------------------------


def draw_cornice(canvas: Canvas, x: float, y: float, w: float, props: Mapping[str, object]) -> None:
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
    if props.get("cornice_ornament") == "modillioned":
        # Modillions: chunky brackets, evenly spread along the run.
        spacing = w / n
        for i in range(n + 1):
            mx = x + i * spacing
            canvas.rect(mx - 0.05, y - shadow_h - 0.08, 0.10, 0.08, _C["cornice"], stroke=_C["cornice_stroke"], stroke_w=0.3)
    else:
        spacing = (w + 2 * overhang) / n
        for i in range(n):
            dx = x - overhang + i * spacing + spacing / 2
            canvas.rect(dx, y - shadow_h - 0.04, 0.06, 0.04, _C["cornice"], stroke=_C["cornice_stroke"], stroke_w=0.3)
    canvas.rect(x - overhang, y, w + 2 * overhang, depth, _C["cornice"], stroke_w=0.0)
    canvas.rect(x - overhang, y, w + 2 * overhang, depth, "none", stroke=_C["cornice_stroke"], stroke_w=0.3)


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
    course_kind = props.get("course_kind") or "bandeau"
    depth = max(0.06, _num(props, "projection", 0.05))
    if course_kind == "entablature":
        overhang = 0.06
        corona = min(depth * 0.30, 0.12)
        canvas.rect(x, y - depth, w, depth, _C["string_course"], stroke_w=0.4)
        canvas.rect(x - overhang, y - corona, w + 2 * overhang, corona, _C["cornice"], stroke_w=0.0)
        canvas.rect(x - overhang, y - corona, w + 2 * overhang, corona, "none", stroke=_C["cornice_stroke"], stroke_w=0.4)
        canvas.line(x, y - depth, x + w, y - depth, "#A09888", 0.8)
        canvas.line(x, y - depth + corona * 0.6, x + w, y - depth + corona * 0.6, "#B8AC98", 0.4)
        return
    canvas.rect(x, y, w, depth, _C["string_course"], stroke_w=0.4)
    canvas.line(x, y, x + w, y, "#A09888", 0.8)
    canvas.line(x, y + depth, x + w, y + depth, "#C8BCA8", 0.4)
    if course_kind == "plat_bande":
        canvas.line(x, y + depth * 0.5, x + w, y + depth * 0.5, "#B8AC98", 0.3)


def draw_socle(canvas: Canvas, x: float, y: float, w: float, h: float, props: Mapping[str, object]) -> None:
    treatment = props.get("treatment") or "flat_incised_refends"
    fill = _C.get(f"socle_{treatment}", _C["wall_ground"])
    canvas.rect(x, y, w, h, fill, stroke_w=0.5)
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
    slab_h = 0.06
    x0, x1 = x - overhang, x + w + overhang
    canvas.rect(x0, y - slab_h, x1 - x0, slab_h, _C["balcony_floor"], stroke=_C["cornice_stroke"], stroke_w=0.5)
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
    fill = _C["roof_zinc"] if material == "zinc_roofing" else _C["roof_slate"]
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
