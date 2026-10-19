"""The Second Empire civic block as a split grammar.

Ranges and pavilions on a rusticated basement, storeys framed by (paired)
columns, and a mansard whose pavilions rise above the ranges in a curve the
architect chose.

The style is its rule file, ``second_empire.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (the roofline, the flight of steps, the rusticated basement), and the
entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode, Node, SocleNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class SecondEmpireSite:
    width: float  # metres of front
    year: int
    klass: BuildingClass
    seed: int = 0


# ---------------------------------------------------------------------------
# Drawings the rule file names
# ---------------------------------------------------------------------------


def write_storey(storey: Shape, below, d) -> list[Node]:
    """The kit's storey, with its rustication drawn first, under the bays."""
    node, *rest = kit.write_storey(storey, below, d)
    socles = [c for c in node.children if c.kind == "socle"]
    others = [c for c in node.children if c.kind != "socle"]
    return [replace(node, children=tuple(socles + others)), *rest]


def write_socle(shape: Shape, below, d) -> list[Node]:
    """Rusticated masonry: blocks about 1.2 m long in 0.5 m courses."""
    s = shape.scope
    return [
        SocleNode(
            id=shape.id,
            kind="socle",
            trace=tuple(shape.trace),
            props={**kit.xywh(s), "treatment": shape.attr("rustication"),
                   "course_columns": max(1, round(s.w / 1.2)), "course_rows": max(1, round(s.h / 0.5))},
        )
    ]


def write_flight(shape: Shape, below, d) -> list[Node]:
    """A splayed flight of steps seen from the front: each step down wider."""
    s = shape.scope
    n = max(3, round(s.h / 0.17))
    splay = s.w * 0.18
    left = [(s.x, s.y)]
    for k in range(n):
        y1 = s.y + s.h * (k + 1) / n
        left += [(s.x + splay * k / n, y1), (s.x + splay * (k + 1) / n, y1)]
    right = [(s.x + s.w - (px - s.x), py) for px, py in reversed(left)]
    return [GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "form": "stoop", "points": tuple(left + right),
                             "hoist_beam": None, "wall_material": "stone"})]


def _profile(name: str, t: float) -> float:
    """How far in the brisis has come at height share ``t``: a straight
    slope, bowed out (steep at the foot, rolling in at the top, the Louvre's),
    or flared (sweeping out at the foot)."""
    if name == "convex":
        return 1.0 - math.cos(t * math.pi / 2.0)
    if name == "concave":
        return math.sin(t * math.pi / 2.0)
    return t


def _section_outline(x0, w, y0, h, brisis, pitch_low, pitch_high, profile, left, right):
    """One section's roof as a height profile, left to right. ``left`` and
    ``right`` are ``None`` for a hipped return, or how far the roof runs on
    at full height into the neighbour it abuts."""
    hb = h * brisis
    ib = hb / math.tan(math.radians(pitch_low))
    it = (h - hb) / math.tan(math.radians(pitch_high))
    # The top keeps at least a metre of flat (or the hips meet early).
    spare = w / 2.0 - 0.5
    if ib + it > spare:
        it = max(0.0, spare - ib)
    side = [(ib * _profile(profile, k / 10.0), hb * k / 10.0) for k in range(11)] + [(ib + it, h)]
    pts: list[tuple[float, float]] = []
    if left is None:
        pts += [(x0 + dx, y0 + dy) for dx, dy in side]
    else:
        pts.append((x0 - left, y0 + h))
    if right is None:
        pts += [(x0 + w - dx, y0 + dy) for dx, dy in reversed(side)]
    else:
        pts.append((x0 + w + right, y0 + h))
    return pts, (x0 + ib + it, w - 2 * (ib + it))


def _height_at(pts, x):
    if x < pts[0][0] - 1e-9 or x > pts[-1][0] + 1e-9:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 - 1e-9 <= x <= x1 + 1e-9:
            if x1 - x0 < 1e-9:
                return max(y0, y1)
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def skyline(outlines) -> list[tuple[float, float]]:
    """The highest of several roof outlines at every point: one silhouette."""
    xs = sorted({round(x, 6) for pts in outlines for x, _ in pts})
    lo, hi = xs[0], xs[-1]
    grid = sorted(set(xs) | {round(lo + 0.05 * k, 6) for k in range(int((hi - lo) / 0.05) + 1)})
    out = []
    for x in grid:
        ys = [y for y in (_height_at(p, x) for p in outlines) if y is not None]
        if ys:
            out.append((x, max(ys)))
    # Drop points in line with their neighbours.
    keep = [out[0]]
    for a, b in zip(out[1:], out[2:]):
        p = keep[-1]
        if abs((a[1] - p[1]) * (b[0] - p[0]) - (b[1] - p[1]) * (a[0] - p[0])) > 1e-6:
            keep.append(a)
    keep.append(out[-1])
    return keep


def write_roofline(roof: Shape, below, d) -> list[Node]:
    """The mansard as one silhouette: each section's roof, hipped where it
    stands free and running on into the pavilion it meets, the pavilions
    taller, all under one outline; iron cresting along each pavilion's top."""
    kinds, sizes = roof.attr("kinds"), roof.attr("sizes")
    y0 = roof.scope.y
    profile = roof.attr("roof_profile")
    outlines, crests = [], []
    x = 0.0
    for i, (kind, w) in enumerate(zip(kinds, sizes)):
        h = roof.attr("range_h") if kind == "range" else roof.attr("pavilion_h")
        # A range abutting a pavilion runs on into it; pavilions and free
        # ends are hipped.
        left = sizes[i - 1] / 2.0 if (kind == "range" and i > 0) else None
        right = sizes[i + 1] / 2.0 if (kind == "range" and i < len(kinds) - 1) else None
        pts, (tx, tw) = _section_outline(x, w, y0, h, roof.attr("brisis"), roof.attr("pitch_low"),
                                         roof.attr("pitch_high"), profile if kind != "range" else "straight", left, right)
        outlines.append(pts)
        if kind != "range" and tw > 0.5:
            crests.append((tx, y0 + h, tw))
        x += w
    sky = skyline(outlines)
    nodes: list[Node] = [
        GableNode(id=roof.id, kind="gable", trace=tuple(roof.trace),
                  props={**kit.xywh(roof.scope), "form": "pavilion", "points": tuple(sky),
                         "hoist_beam": None, "wall_material": "slate"})
    ]
    for k, (cx, cy, cw) in enumerate(crests):
        nodes.append(IronworkNode(id=f"{roof.id}/cresting{k}", kind="ironwork", trace=tuple(roof.trace),
                                  props={"x": cx, "y": cy, "w": cw, "h": 0.6, "position": "ridge",
                                         "ironwork_pattern": "lozenge_palmette", "ornament_count": max(2, round(cw / 0.45))}))
    return nodes + list(below)


def write_pediment(shape: Shape, below, d) -> list[Node]:
    """A low triangular pediment over the entrance pavilion's cornice."""
    s = shape.scope
    pts = ((s.x - 0.25, s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.25, s.y))
    return [GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "form": "front_gable", "points": pts,
                             "hoist_beam": None, "wall_material": shape.attr("stone")})]


register_writer("second_empire.pediment", write_pediment)
register_writer("second_empire.roofline", write_roofline)
register_writer("second_empire.flight", write_flight)
register_writer("second_empire.socle", write_socle)
register_writer("second_empire.storey", write_storey)

STYLE = load_style(Path(__file__).with_name("second_empire.toml"))


def second_empire_grammar() -> Grammar:
    return STYLE.grammar()


def derive_second_empire(site: SecondEmpireSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_second_empire(site: SecondEmpireSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
