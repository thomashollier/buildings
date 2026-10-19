"""The Sana'a tower house as a split grammar.

A narrow tower of five to eight storeys: dark stone storeys at the foot with
few, small openings, brick storeys over them banded by white gypsum friezes,
every window a rectangular light under a fanlight (the qamariya), the mafraj
on top with the largest windows, and a crenellated white parapet. The seed
stands for the family: how windows are grouped, a round or an arched
qamariya, a set-back mafraj, or a plain mud tower in the manner of Shibam.

The style is its rule file, ``sanaa.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer and
production, and the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Derivation, Grammar, Part, Shape, X, Y
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.kit import xywh
from buildings.typologies.common.rulefile import load_style, register_production, register_writer


@dataclass(frozen=True)
class SanaaSite:
    width: float  # metres of street front
    year: int
    klass: BuildingClass
    seed: int = 0


def _row(row: Shape, d: Derivation, fractions, divider: float, first_index: int, attrs: dict | None = None) -> None:
    """Cut a row into lights side by side, a plain mullion between each pair."""
    n = len(fractions)
    glass = row.scope.w - divider * (n - 1)
    parts: list[Part] = []
    for i, f in enumerate(fractions):
        if i:
            parts.append(Part("Mullion", divider, f"mullion{first_index + i}"))
        parts.append(Part("Light", glass * f / sum(fractions), f"light{first_index + i}", {**(attrs or {}), "lights_index": first_index + i}))
    d.split(row, X, parts)


def split_window_and_fanlight(column: Shape, d: Derivation) -> None:
    """A window column cut bottom-up into breast, lights, a transom band, a
    row of fanlights over them (or one fanlight over the whole group), and
    the lintel. Each fanlight is a light of its own with its own head."""
    a = column.parent.attrs
    h = column.scope.h
    sill = a["sill"]
    light_h = min(a["light_height"], h - sill)
    fan_type = a.get("fan_type")
    lights = tuple(a.get("lights") or (1.0,))
    divider = a.get("divider_width", 0.2)
    if not fan_type:
        _breast, row, _lintel = d.split(
            column, Y, [Part("Breast", sill, "breast"), Part("Row", light_h, "row"), Part("Lintel", h - sill - light_h, "lintel")]
        )
        _row(row, d, lights, divider, 0)
        return
    gap = a["fan_gap"]
    fan_h = min(a["fan_height"], h - sill - light_h - gap)
    _breast, row, _transom, fans, _lintel = d.split(
        column,
        Y,
        [
            Part("Breast", sill, "breast"),
            Part("Row", light_h, "row"),
            Part("Transom", gap, "transom"),
            Part("Fans", fan_h, "fans"),
            Part("Lintel", h - sill - light_h - gap - fan_h, "lintel"),
        ],
    )
    _row(row, d, lights, divider, 0)
    over = (1.0,) if a.get("fan_shared") else lights
    if fan_type == "qamariya":
        # A qamariya is not glazing in a frame but a gypsum tracery screen:
        # a shape of its own, drawn as its outline and its tracery.
        n = len(over)
        glass = fans.scope.w - divider * (n - 1)
        parts: list[Part] = []
        for i in range(n):
            if i:
                parts.append(Part("Mullion", divider, f"fan_mullion{i}"))
            parts.append(Part("Qamariya", glass / n, f"qamariya{i}"))
        d.split(fans, X, parts)
        return
    fan_attrs = {"opening_type": fan_type, "head": a.get("fan_head", "round"), "surround_kind": a.get("fan_surround", "none"), "keystone_present": False,
                "screen_gap": None}
    _row(fans, d, over, divider, len(lights), fan_attrs)


def _arc(cx: float, cy: float, r: float, a0: float, a1: float, steps: int = 12) -> list[tuple[float, float]]:
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / steps), cy + r * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]


def write_qamariya(shape: Shape, below, d) -> list:
    """The qamariya: a half-round (or round) light of alabaster or coloured
    glass set in gypsum tracery -- its outline, an inner ring, and the spokes
    between the two, as one outline in front of the wall."""
    s = shape.scope
    spokes = int(shape.attr("fan_spokes"))
    if shape.attr("fan_head") == "circle":
        r = min(s.w, s.h) / 2.0
        cx, cy = s.x + s.w / 2.0, s.y + s.h / 2.0
        outer = _arc(cx, cy, r, math.pi, -math.pi, 24)
        pts = list(outer)
        for k in range(spokes * 2 + 1):
            a = math.pi - 2 * math.pi * k / (spokes * 2)
            inner = (cx + 0.45 * r * math.cos(a), cy + 0.45 * r * math.sin(a))
            pts += [inner, (cx + r * math.cos(a), cy + r * math.sin(a)), inner]
        pts.append(outer[0])
    else:
        r = min(s.w / 2.0, s.h)
        cx, y0 = s.x + s.w / 2.0, s.y
        pts = [(cx - r, y0), *_arc(cx, y0, r, math.pi, 0.0, 16), (cx + r, y0)]
        for k in range(spokes + 1):
            a = math.pi * k / spokes
            inner = (cx + 0.42 * r * math.cos(a), y0 + 0.42 * r * math.sin(a))
            pts += [inner, (cx + r * math.cos(a), y0 + r * math.sin(a)), inner]
        pts.append((cx - r, y0))
    # The renderer draws only one outline in front of the wall: the stair's.
    return [GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                      props={**xywh(s), "form": "stoop", "points": tuple(pts), "hoist_beam": None, "wall_material": "plaster_white"})]


def lift(write, kinds=("gable",)):
    """A writer whose outlines (gable nodes, and any other kind named) are
    carried up past it to the building, where they are drawn, instead of
    being kept as its own."""

    def lifted(shape: Shape, below, d) -> list:
        up = [n for n in below if n.kind in kinds]
        return [*write(shape, [n for n in below if n.kind not in kinds], d), *up]

    lifted.__doc__ = write.__doc__
    return lifted


write_cell = lift(kit.write_cell)
write_storey = lift(kit.write_storey)


def write_zigzag(shape: Shape, below, d) -> list:
    """The carved gypsum band between two floors, drawn as a running row of
    lozenges between two lines."""
    s = shape.scope
    return [
        IronworkNode(
            id=shape.id,
            kind="ironwork",
            trace=tuple(shape.trace),
            props={**xywh(s), "guards": "frieze", "ironwork_pattern": "lozenge_palmette", "max_gap": s.w,
                   "ornament_count": max(2, round(s.w / shape.attr("lozenge_w")))},
        )
    ]


def write_parapet(shape: Shape, below, d) -> list:
    """The white parapet over a roof terrace: a low wall, then a row of
    pointed merlons, each a little gable of its own."""
    s = shape.scope
    wall = shape.attr("wall_h")
    n = max(2, round(s.w / shape.attr("merlon_w")))
    m = s.w / n
    top = s.y + wall
    pts = [(s.x, s.y), (s.x, top)]
    for i in range(n):
        x0 = s.x + i * m
        pts += [(x0 + m * 0.18, top), (x0 + m * 0.18, top + (s.h - wall) * 0.45), (x0 + m * 0.5, s.y + s.h),
                (x0 + m * 0.82, top + (s.h - wall) * 0.45), (x0 + m * 0.82, top)]
    pts += [(s.x + s.w, top), (s.x + s.w, s.y)]
    return [
        GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                  props={**xywh(s), "form": "straight", "points": tuple(pts), "hoist_beam": None,
                         "wall_material": shape.attr("wall_material")}),
    ]


register_production("sanaa.window_and_fanlight", split_window_and_fanlight)
register_writer("sanaa.zigzag", write_zigzag)
register_writer("sanaa.qamariya", write_qamariya)
register_writer("sanaa.cell", write_cell)
register_writer("sanaa.storey", write_storey)
register_writer("sanaa.parapet", write_parapet)

STYLE = load_style(Path(__file__).with_name("sanaa.toml"))


def sanaa_grammar() -> Grammar:
    return STYLE.grammar()


def derive_sanaa(site: SanaaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_sanaa(site: SanaaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
