"""The Islamic Cairo house front as a split grammar.

A mostly blind stone ground floor entered by a bent entrance under a pointed
or stalactite (muqarnas) hood; the upper floors standing out over it on
timber beams, with wooden mashrabiya oriels on corbels and latticed windows
between them; a crenellated top. The seed stands for the family: Cairo stone
or the striped brick of Rashid (Rosetta), striped (ablaq) masonry or plain,
and where the oriels go.

The style is its rule file, ``cairo.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer,
and the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.kit import trace_of, xywh
from buildings.typologies.common.rulefile import load_style, register_writer
from buildings.typologies.sanaa.grammar import lift  # also registers the qamariya


@dataclass(frozen=True)
class CairoSite:
    width: float  # metres of street front
    year: int
    klass: BuildingClass
    seed: int = 0


def _gable(shape: Shape, pts, form: str, material: str) -> GableNode:
    return GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                     props={**xywh(shape.scope), "form": form, "points": tuple(pts), "hoist_beam": None, "wall_material": material})


def write_lattice(shape: Shape, below, d) -> list:
    """A mashrabiya screen of turned timber over a light."""
    return [
        IronworkNode(
            id=f"{shape.parent.id}/lattice",
            kind="ironwork",
            trace=trace_of(shape, "screen_gap"),
            props={**xywh(shape.scope), "guards": "opening", "ironwork_pattern": "timber_lattice",
                   "max_gap": shape.attr("screen_gap"), "ornament_count": 2},
        )
    ]


def write_corbel(shape: Shape, below, d) -> list:
    """The stone corbel an oriel stands on: courses stepping out as they rise."""
    s = shape.scope
    n = int(shape.attr("corbel_steps"))
    cx = s.x + s.w / 2.0
    left = []
    for k in range(n):
        half = s.w / 2.0 * (shape.attr("corbel_foot") + (1 - shape.attr("corbel_foot")) * k / (n - 1))
        left += [(cx - half, s.y + s.h * k / n), (cx - half, s.y + s.h * (k + 1) / n)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    return [_gable(shape, left + right, "stoop", "stone")]


def write_hood(shape: Shape, below, d) -> list:
    """The hood over the portal: a pointed niche, its head either stepped in
    tiers of stalactite cells (muqarnas) or one plain pointed arch."""
    s = shape.scope
    cx = s.x + s.w / 2.0
    spring = s.y + s.h * shape.attr("hood_spring")
    pts = [(s.x, s.y), (s.x, spring)]
    if shape.attr("hood_form") == "muqarnas":
        tiers = int(shape.attr("hood_tiers"))
        step = (s.w / 2.0) / (tiers + 1)
        rise = (s.y + s.h - spring) / tiers
        x = s.x
        for k in range(tiers):
            y0 = spring + rise * k
            # Each tier a row of hanging cells: it drops a little pendant,
            # then steps in to carry the tier above.
            pts += [(x + step * 0.5, y0 - rise * 0.25), (x + step, y0), (x + step, y0 + rise)]
            x += step
        pts.append((cx, s.y + s.h))
    else:
        steps = 8
        for i in range(1, steps + 1):
            t = i / steps
            pts.append((s.x + (s.w / 2.0) * (1 - (1 - t) ** 2), spring + (s.y + s.h - spring) * t))
    right = [(2 * cx - x, y) for x, y in reversed(pts[:-1])]
    return [_gable(shape, pts + right, "stoop", "stone")]


def write_cresting(shape: Shape, below, d) -> list:
    """The crenellated top: a band of wall, then stepped merlons."""
    s = shape.scope
    wall = shape.attr("wall_h")
    n = max(2, round(s.w / shape.attr("merlon_w")))
    m = s.w / n
    rise = s.h - wall
    top = s.y + wall
    pts = [(s.x, s.y), (s.x, top)]
    for i in range(n):
        x0 = s.x + i * m
        pts += [(x0 + m * 0.12, top), (x0 + m * 0.12, top + rise * 0.4), (x0 + m * 0.24, top + rise * 0.4),
                (x0 + m * 0.24, top + rise * 0.72), (x0 + m * 0.36, top + rise * 0.72), (x0 + m * 0.5, s.y + s.h),
                (x0 + m * 0.64, top + rise * 0.72), (x0 + m * 0.76, top + rise * 0.72), (x0 + m * 0.76, top + rise * 0.4),
                (x0 + m * 0.88, top + rise * 0.4), (x0 + m * 0.88, top)]
    pts += [(s.x + s.w, top), (s.x + s.w, s.y)]
    return [_gable(shape, pts, "straight", shape.attr("wall_material"))]


register_writer("cairo.lattice", write_lattice)
register_writer("cairo.corbel", write_corbel)
register_writer("cairo.hood", write_hood)
register_writer("cairo.cresting", write_cresting)
register_writer("cairo.cell", lift(kit.write_cell))
# An oriel's box is a storey of its own, standing in front of the wall: it
# is carried up to the building beside the storey it projects from.
register_writer("cairo.storey", lift(kit.write_storey, ("gable", "storey")))

STYLE = load_style(Path(__file__).with_name("cairo.toml"))


def cairo_grammar() -> Grammar:
    return STYLE.grammar()


def derive_cairo(site: CairoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_cairo(site: CairoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
