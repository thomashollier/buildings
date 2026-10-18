"""The Amsterdam canal house as a split grammar.

A narrow brick front rising into a gable of narrowing tiers, its outline by
date: step to 1640, neck to 1720, bell to 1790, a straight cornice after.

The style is its rule file, ``amsterdam.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, Node
from buildings.site import BuildingClass
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common.rulefile import load_style, register_writer

@dataclass(frozen=True)
class CanalSite:
    width: float  # metres of canal frontage
    year: int
    klass: BuildingClass
    seed: int = 0

def _curve(x0, y0, x1, y1, profile, steps=10):
    return [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * profile(i / steps)) for i in range(1, steps + 1)]


def _outline(gable: Shape) -> tuple[list[tuple[float, float]], tuple[float, float]]:
    """The left half of the outline, eaves to apex, from the tiers as placed;
    and the hoisting beam's foot."""
    form = gable.attrs["form"]
    tiers = [c for c in gable.children if c.label == "GableTier"]
    storeys = [c.children[0] for c in tiers]
    crown = next((c for c in gable.children if c.label == "Crown"), None)
    g = gable.scope
    cx = g.x + g.w / 2.0
    pts: list[tuple[float, float]] = [(g.x, g.y)]
    if form == "step":
        for st in storeys:
            pts += [(st.scope.x, pts[-1][1]), (st.scope.x, st.scope.y + st.scope.h)]
        top = storeys[-1].scope
        apex_y = top.y + top.h
        pts.append((cx, apex_y))
        return pts, (cx, apex_y - 0.75)
    first = storeys[0].scope
    if form == "neck":
        # A claw piece: a concave scroll from the eaves up into the neck.
        pts += _curve(g.x, g.y, first.x, g.y + first.h * 0.8, lambda t: math.sin(t * math.pi / 2.0))
        for st in storeys:
            pts += [(st.scope.x, max(pts[-1][1], st.scope.y)), (st.scope.x, st.scope.y + st.scope.h)]
        top = storeys[-1].scope.y + storeys[-1].scope.h
        apex = top + crown.scope.h
        pts += [(storeys[-1].scope.x - 0.12, top), (cx, apex)]
        return pts, (cx, top - 0.1)
    # bell: an S-curve shoulder, then a segmental crown.
    pts += _curve(g.x, g.y, first.x, first.y + first.h * 0.85, lambda t: 0.5 - 0.5 * math.cos(math.pi * t))
    top = first.y + first.h
    pts.append((first.x, top))
    rise = crown.scope.h
    half = first.w / 2.0
    pts += [(cx - half * math.cos(a), top + rise * math.sin(a)) for a in (math.pi * i / 16 for i in range(1, 9))]
    return pts, (cx, top + 0.1)


def write_gable(gable: Shape, below, d) -> list[Node]:
    left, beam = _outline(gable)
    cx = gable.scope.x + gable.scope.w / 2.0
    right = [(2 * cx - x, y) for x, y in reversed(left[:-1])]
    return [
        GableNode(
            id=gable.id,
            kind="gable",
            trace=tuple(gable.trace)
            + (TraceEntry(rule="amsterdam.gable_form", phase="period", detail=f"form = {gable.attrs['form']!r}"),),
            props={
                **{"x": gable.scope.x, "y": gable.scope.y, "w": gable.scope.w, "h": gable.scope.h},
                "form": gable.attrs["form"],
                "points": tuple(left + right),
                "hoist_beam": beam,
                "wall_material": "brick_dark",
            },
        ),
        *below,
    ]

register_writer("amsterdam.gable", write_gable)

STYLE = load_style(Path(__file__).with_name("amsterdam.toml"))


def amsterdam_grammar() -> Grammar:
    return STYLE.grammar()


def derive_amsterdam(site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_amsterdam(site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def gable_form(year: int) -> str:
    """The gable form the rule file gives a house of this date."""
    lot, _ = derive_amsterdam(CanalSite(6.6, year, BuildingClass.ORDINARY))
    return lot.attrs["form"]
