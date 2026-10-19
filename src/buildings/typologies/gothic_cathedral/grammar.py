"""The Gothic cathedral west front as a split grammar.

Three registers over three portals, the whole divided into three by four
buttresses: the portals (the central one widest) of nested pointed arches;
the gallery of kings; the rose over the central portal between pairs of
lancets; an open gallery; and the twin towers, flat-topped, pinnacled or
spired.

The style is its rule file, ``gothic_cathedral.toml`` beside this module;
this module holds only the situation it takes, the drawings the file names
by writer (a portal's rings, the rose's tracery, a pointed arch, a tower's
top, the nave's gable), and the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class CathedralSite:
    width: float  # metres across the west front
    year: int  # when the front was begun
    klass: BuildingClass  # the chapter's means: how deep the portals, how tall the towers
    seed: int = 0  # the master mason


def _lift(fn):
    """Outlines drawn inside a bay or a storey stand on the building, which is
    where the renderer draws outlines."""

    def write(shape: Shape, below, d):
        outlines = [n for n in below if n.kind == "gable"]
        rest = [n for n in below if n.kind != "gable"]
        return [*fn(shape, rest, d), *outlines]

    return write


def _node(shape: Shape, suffix: str, pts, form: str, material: str = "stone") -> GableNode:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return GableNode(
        id=f"{shape.id}{suffix}",
        kind="gable",
        trace=tuple(shape.trace),
        props={"x": min(xs), "y": min(ys), "w": max(xs) - min(xs), "h": max(ys) - min(ys), "form": form,
               "points": tuple(pts), "hoist_beam": None, "wall_material": material},
    )


def pointed(x0: float, x1: float, y: float, rise: float, steps: int = 10):
    """A two-centred pointed arch from springing to springing, the centres on
    the springing line: left haunch, apex, right haunch."""
    a = (x1 - x0) / 2.0
    rise = max(rise, a)  # never flatter than a semicircle
    r = (a * a + rise * rise) / (2 * a)
    t_end = math.acos(max(-1.0, min(1.0, (a - r) / r)))
    # The angle runs from pi (springing) down to t_end (apex); sin is positive there.
    left = [(x0 + r + r * math.cos(t), y + r * math.sin(t)) for t in (math.pi + (t_end - math.pi) * i / steps for i in range(steps + 1))]
    right = [(x0 + x1 - px, py) for px, py in reversed(left[:-1])]
    return left + right


def _circle(cx: float, cy: float, r: float, steps: int = 24):
    return [(cx + r * math.cos(2 * math.pi * i / steps), cy + r * math.sin(2 * math.pi * i / steps)) for i in range(steps + 1)]


def write_portal(portal: Shape, below, d) -> list:
    """A portal: the wall it is cut in, its gablet where it has one, its
    rings stepping in to the tympanum over the door, as the rules sized them."""
    s = portal.scope
    a = portal.attrs
    x0, x1 = s.x + a["margin"], s.x + s.w - a["margin"]
    spring = s.y + a["spring"]
    nodes = [_node(portal, "/wall", [(s.x, s.y), (s.x, s.y + s.h), (s.x + s.w, s.y + s.h), (s.x + s.w, s.y)], "portal_wall")]
    if a["gablet"]:
        foot = spring + a["rise"] * 0.45
        nodes.append(_node(portal, "/gablet", [(s.x + 0.05, foot), ((s.x + s.x + s.w) / 2.0, s.y + s.h), (s.x + s.w - 0.05, foot)], "gablet"))
    ring_w = a["ring_w"]
    materials = ("brick_buff", "stone")
    for k in range(a["rings"] + 1):
        lx, rx = x0 + k * ring_w, x1 - k * ring_w
        rise = a["rise"] * (rx - lx) / (x1 - x0)
        arch = pointed(lx, rx, spring, rise)
        inner = k == a["rings"]
        pts = [(lx, s.y), *arch, (rx, s.y)]
        nodes.append(_node(portal, f"/ring{k}" if not inner else "/tympanum", pts, "archivolt",
                           "terracotta" if inner else materials[k % 2]))
    # The lintel the tympanum stands on.
    lx, rx = x0 + a["rings"] * ring_w, x1 - a["rings"] * ring_w
    nodes.append(_node(portal, "/lintel", [(lx, spring), (rx, spring)], "lintel"))
    return [*nodes, *below]


def write_rose(rose: Shape, below, d) -> list:
    """The rose's tracery over its glass: an eye, spokes to the rim, and a
    ring of cusped circles between them, as many as the rules give it."""
    s = rose.scope
    cx, cy = s.x + s.w / 2.0, s.y + s.h / 2.0
    r = min(s.w, s.h) / 2.0 * 0.92  # the glass the opening draws
    n = rose.attrs["spokes"]
    eye = r * 0.22
    nodes = [_node(rose, "/eye", _circle(cx, cy, eye), "tracery"), _node(rose, "/rim", _circle(cx, cy, r * 0.97, 36), "tracery")]
    for k in range(n):
        t = 2 * math.pi * k / n
        nodes.append(_node(rose, f"/spoke{k}", [(cx + eye * math.cos(t), cy + eye * math.sin(t)), (cx + r * math.cos(t), cy + r * math.sin(t))], "tracery"))
        tm = t + math.pi / n
        rc = r * 0.68
        nodes.append(_node(rose, f"/cusp{k}", _circle(cx + rc * math.cos(tm), cy + rc * math.sin(tm), r * math.sin(math.pi / n) * 0.55, 12), "tracery"))
    return nodes


def write_arch(arch: Shape, below, d) -> list:
    """A pointed relieving arch over a group of lancets."""
    s = arch.scope
    return [_node(arch, "", pointed(s.x, s.x + s.w, s.y, s.h - 0.05), "archivolt")]


def write_tower_top(top: Shape, below, d) -> list:
    """What crowns a tower: a parapet over a flat terrace; a parapet with a
    pinnacle at each corner; or an octagonal spire between pinnacles."""
    s = top.scope
    kind = top.attr("top")
    para = top.attrs["parapet_h"]
    cx = s.x + s.w / 2.0
    nodes = [_node(top, "/parapet", [(s.x, s.y), (s.x, s.y + para), (s.x + s.w, s.y + para), (s.x + s.w, s.y)], "parapet")]
    # The parapet is an open arcade: a row of small pointed openings.
    n = max(3, round(s.w / 1.6))
    step = s.w / n
    for k in range(n):
        lx = s.x + k * step + step * 0.22
        nodes.append(_node(top, f"/parapet{k}", [(lx, s.y + para * 0.2), *pointed(lx, lx + step * 0.56, s.y + para * 0.5, step * 0.4, 4), (lx + step * 0.56, s.y + para * 0.2)], "tracery", "shadow"))
    if kind in ("pinnacles", "spire"):
        pw = s.w * 0.14
        ph = top.attrs["pinnacle_h"]
        for side, px in (("l", s.x), ("r", s.x + s.w - pw)):
            nodes.append(_node(top, f"/pinnacle_{side}", [(px, s.y + para), (px, s.y + para + ph * 0.35), (px + pw / 2.0, s.y + para + ph), (px + pw, s.y + para + ph * 0.35), (px + pw, s.y + para)], "spire"))
    if kind == "spire":
        base = s.y + para
        half = s.w * 0.36
        apex = s.y + s.h
        nodes.append(_node(top, "/spire", [(cx - half, base), (cx - half * 0.92, base + (apex - base) * 0.08), (cx, apex), (cx + half * 0.92, base + (apex - base) * 0.08), (cx + half, base)], "spire"))
        # The spire's faces: the arrises of an octagon seen square, and the
        # bands of its openwork.
        for k, f in enumerate((0.25, 0.45, 0.65)):
            yy = base + (apex - base) * f
            hw = half * 0.92 * (1 - (yy - base) / (apex - base))
            nodes.append(_node(top, f"/band{k}", [(cx - hw, yy), (cx + hw, yy)], "tracery"))
        nodes.append(_node(top, "/arris", [(cx, base + (apex - base) * 0.08), (cx, apex)], "tracery"))
    return nodes


def write_nave_gable(gable: Shape, below, d) -> list:
    """The nave roof's gable between the towers, an oculus in it."""
    s = gable.scope
    cx = s.x + s.w / 2.0
    return [
        _node(gable, "", [(s.x, s.y), (cx, s.y + s.h), (s.x + s.w, s.y)], "front_gable"),
        _node(gable, "/oculus", _circle(cx, s.y + s.h * 0.38, min(s.w, s.h) * 0.12, 20), "tracery", "shadow"),
    ]


register_writer("gothic.storey", _lift(kit.write_storey))
register_writer("gothic.cell", _lift(kit.write_cell))
register_writer("gothic.portal", write_portal)
register_writer("gothic.rose", write_rose)
register_writer("gothic.arch", write_arch)
register_writer("gothic.tower_top", write_tower_top)
register_writer("gothic.nave_gable", write_nave_gable)

STYLE = load_style(Path(__file__).with_name("gothic_cathedral.toml"))


def gothic_cathedral_grammar() -> Grammar:
    return STYLE.grammar()


def derive_gothic_cathedral(site: CathedralSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_gothic_cathedral(site: CathedralSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
