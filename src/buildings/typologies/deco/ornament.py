"""The Art Deco family's drawings: outlines and panels around shapes the
rules placed.

Nothing here decides anything. Each writer turns one shape, whose place,
size and kind the rule files fixed, into IR:

* ``deco.floor`` -- a floor of a block (the kit's storey), lifting the panels,
  portholes and outlines inserted on it up to the building, where the
  renderer draws them in front of the wall.
* ``deco.panel`` -- a flat painted panel standing proud of the wall: a racing
  stripe, a terrazzo band, a name panel, a marquee, a blade sign. It is
  written as a storey-like wall node of its own paint, because the renderer's
  only rectangle that takes any paint is a storey's wall.
* ``deco.crest`` -- the outline a block's top is finished with: a stepped
  (ziggurat) parapet, a zigzag of chevrons, a Miami fin, a spire, a rounded
  streamline corner. Drawn as a gable outline in the block's wall.
"""

from __future__ import annotations

import math

from buildings.cga import Shape
from buildings.ir.nodes import GableNode, StoreyNode
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import register_writer

__all__ = ["crest_points", "lift"]

#: IR kinds written under a floor or a panel that belong to the building:
#: the renderer draws them only there.
_LIFTED = frozenset({"storey", "gable", "dormer", "special"})


def lift(below) -> tuple[list, list]:
    """Split the nodes under a shape into its own and those that go up."""
    own = [n for n in below if n.kind not in _LIFTED]
    up = [n for n in below if n.kind in _LIFTED]
    return own, up


def write_floor(floor: Shape, below, d) -> list:
    own, up = lift(below)
    return [*kit.write_storey(floor, own, d), *up]


def write_panel(panel: Shape, below, d) -> list:
    own, up = lift(below)
    s = panel.scope
    node = StoreyNode(
        id=panel.id,
        kind="storey",
        trace=tuple(panel.trace),
        children=tuple(own),
        props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "role": "panel",
               "wall_material": panel.attrs["paint"], "on_the_stone_facade": True},
    )
    return [node, *up]


def _stepped(x0, y0, w, h, steps, reach):
    """A ziggurat: ``steps`` equal rises, each narrower, the top ``reach`` of the width."""
    cx = x0 + w / 2.0
    pts = [(x0, y0)]
    for k in range(steps):
        half = w / 2.0 * (1.0 - (1.0 - reach) * k / max(1, steps - 1)) if steps > 1 else w * reach / 2.0
        y = y0 + h * (k + 1) / steps
        pts += [(cx - half, pts[-1][1]), (cx - half, y)]
    left = pts[1:]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    return [pts[0], *left, *right, (x0 + w, y0)]


def _chevrons(x0, y0, w, h, teeth):
    pts = [(x0, y0)]
    tw = w / teeth
    for k in range(teeth):
        pts += [(x0 + tw * k, y0 + h * 0.35), (x0 + tw * (k + 0.5), y0 + h), (x0 + tw * (k + 1), y0 + h * 0.35)]
    return pts + [(x0 + w, y0)]


def crest_points(kind: str, x0: float, y0: float, w: float, h: float, steps: int, reach: float, side: str):
    """The outline of a crest of this kind in this rectangle (left to right)."""
    cx = x0 + w / 2.0
    if kind == "stepped":
        return _stepped(x0, y0, w, h, steps, reach)
    if kind == "chevron":
        return _chevrons(x0, y0, w, h, max(2, steps))
    if kind == "fin":
        # A Miami Beach fin: a low shoulder across the middle of the block,
        # and a narrow slab rising from it, its top rounded.
        shoulder = w * min(0.9, reach * 2.2)
        fin = w * reach / 2.0
        r = fin
        arc = [(cx - fin + r - r * math.cos(a), y0 + h - r + r * math.sin(a)) for a in (math.pi / 2 * i / 6 for i in range(7))]
        left = [(x0, y0), (cx - shoulder / 2, y0), (cx - shoulder / 2, y0 + h * 0.22), (cx - fin, y0 + h * 0.22), *arc[:-1]]
        apex = [(cx, y0 + h)]
        right = [(2 * cx - x, y) for x, y in reversed(left[1:])]
        return [*left, *apex, *right, (x0 + w, y0)]
    if kind == "spire":
        # Stepped shoulders, then a finial: Boston Avenue's tower top.
        base = _stepped(x0, y0, w, h * 0.45, steps, reach)
        mid = len(base) // 2
        return [*base[:mid], (cx, y0 + h), *base[mid:]]
    if kind == "rounded":
        # A streamline corner: the parapet runs on and turns down in a
        # quarter circle at the building's outer edge.
        n = 8
        if side == "right":
            arc = [(x0 + w - h + h * math.sin(math.pi / 2 * i / n), y0 + h * math.cos(math.pi / 2 * i / n)) for i in range(n + 1)]
            return [(x0, y0), (x0, y0 + h), *arc]
        arc = [(x0 + h - h * math.sin(math.pi / 2 * (n - i) / n), y0 + h * math.cos(math.pi / 2 * (n - i) / n)) for i in range(n + 1)]
        return [*arc, (x0 + w, y0 + h), (x0 + w, y0)]
    return [(x0, y0), (x0, y0 + h), (x0 + w, y0 + h), (x0 + w, y0)]


#: The edge each crest is finished with (the renderer's coping by form).
_CREST_FORMS = {"stepped": "step", "chevron": "step", "fin": "straight", "spire": "spire", "rounded": "straight", "flat": "straight"}


def write_crest(crest: Shape, below, d) -> list:
    s = crest.scope
    share = float(crest.attrs.get("share", 1.0))
    w = s.w * share
    x0 = s.x + (s.w - w) / 2.0
    kind = crest.attr("crest")
    pts = crest_points(kind, x0, s.y, w, s.h, int(crest.attr("crest_steps")), float(crest.attr("crest_reach")), crest.attr("side", "left"))
    return [
        GableNode(
            id=crest.id,
            kind="gable",
            trace=tuple(crest.trace),
            props={"x": x0, "y": s.y, "w": w, "h": s.h, "form": _CREST_FORMS[kind], "points": tuple(pts),
                   "hoist_beam": None, "wall_material": crest.attr("crest_paint", None) or crest.attr("wall")},
        ),
        *below,
    ]


register_writer("deco.floor", write_floor)
register_writer("deco.panel", write_panel)
register_writer("deco.crest", write_crest)
