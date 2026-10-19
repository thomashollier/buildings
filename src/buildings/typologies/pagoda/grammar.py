"""The pagoda as a split grammar.

Tiers of storeys on a stone podium, each narrower than the one below and
each under its own roof, and a finial on top. In the Japanese timber manner
(Horyu-ji, Yakushi-ji, To-ji) the eaves are very deep, on brackets, their
corners turned up, the walls white plaster between timber posts, and a
bronze sorin of nine rings crowns it; in the Chinese brick manner (the Big
and Small Wild Goose Pagodas) the tiers are many and tall, the eaves shallow
corbelled courses, each face lit by one arched opening between pilasters.

The style is its rule file, ``pagoda.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer,
and the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.kit import trace_of, xywh
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class PagodaSite:
    width: float  # metres: the wall of the first tier, one face
    year: int
    klass: BuildingClass
    seed: int = 0


def _gable(shape: Shape, suffix: str, pts, form: str, material: str) -> GableNode:
    return GableNode(id=f"{shape.id}/{suffix}", kind="gable", trace=tuple(shape.trace),
                     props={**xywh(shape.scope), "form": form, "points": tuple(pts), "hoist_beam": None, "wall_material": material})


def write_eave(shape: Shape, below, d) -> list:
    """One tier's roof seen from the front: the shadowed soffit of the eaves
    over the bracket zone, and the tiled roof over it -- a straight drip line
    that turns up at the corners, a concave slope rising to the foot of the
    tier above (or, on the top tier, to the finial)."""
    s = shape.scope
    cx = s.x + s.w / 2.0
    a = shape.attr("wall_w") / 2.0
    b = shape.attr("next_w") / 2.0
    reach = s.w / 2.0 - a
    y_wall, y_eave, y_top = s.y, s.y + shape.attr("bracket_h"), s.y + s.h
    up = shape.attr("upturn")
    lip = shape.attr("lip")
    tip = cx - a - reach
    out: list = []
    if y_eave - y_wall > 1e-6:
        soffit = [(cx - a, y_wall), (tip + reach * 0.08, y_eave - (y_eave - y_wall) * 0.15), (tip + reach * 0.08, y_eave)]
        soffit += [(2 * cx - x, y) for x, y in reversed(soffit)]
        out.append(_gable(shape, "soffit", soffit, "spire", "timber_dark"))
    left = [(tip + reach * 0.35, y_eave)]
    # The drip line curls up into the corner.
    left += [(tip + reach * 0.35 * (1 - t), y_eave + up * t * t) for t in (0.25, 0.5, 0.75, 1.0)]
    top_of_tip = y_eave + up + lip
    left.append((tip, top_of_tip))
    steps = 10
    left += [(tip + (cx - b - tip) * i / steps, top_of_tip + (y_top - top_of_tip) * (i / steps) ** 1.8) for i in range(1, steps + 1)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    out.append(_gable(shape, "roof", left + right, "spire", shape.attr("roof_material")))
    return out


def write_finial(shape: Shape, below, d) -> list:
    """The finial: a bronze sorin -- a base, an upturned bowl, nine rings on a
    mast, a flame and a jewel -- or the short gourd of a brick pagoda."""
    s = shape.scope
    cx = s.x + s.w / 2.0
    half = s.w / 2.0
    y = s.y
    left: list[tuple[float, float]] = []

    def band(hw: float, h: float) -> None:
        nonlocal y
        left.extend([(cx - hw, y), (cx - hw, y + h)])
        y += h

    if shape.attr("finial_form") == "sorin":
        rings = int(shape.attr("rings"))
        band(half * 0.75, s.h * 0.06)            # roban, the base
        band(half * 0.95, s.h * 0.05)            # fukubachi, the bowl
        band(half * 0.6, s.h * 0.03)             # ukebana
        ring_h = s.h * 0.55 / rings
        for _ in range(rings):                   # kurin, the rings on the mast
            band(half, ring_h * 0.35)
            band(half * 0.18, ring_h * 0.65)
        flame = s.h * 0.18                       # suien, the water flame
        left.extend([(cx - half * 0.7, y + flame * 0.4), (cx - half * 0.2, y + flame)])
        y += flame
        band(half * 0.12, s.h * 0.04)            # ryusha
        r = (s.y + s.h - y) / 2.0                # hoju, the jewel
        left.extend([(cx - r * math.sin(math.pi * k / 6), y + r - r * math.cos(math.pi * k / 6)) for k in range(1, 6)])
    else:
        band(half * 0.8, s.h * 0.2)              # a drum
        r = s.h * 0.25                           # the gourd
        left.extend([(cx - r * math.sin(math.pi * k / 6), y + r - r * math.cos(math.pi * k / 6)) for k in range(1, 7)])
        y += 2 * r
        band(half * 0.2, s.y + s.h - y)
    left.append((cx, s.y + s.h))
    right = [(2 * cx - x, yy) for x, yy in reversed(left[:-1])]
    return [_gable(shape, "finial", left + right, "spire", shape.attr("finial_material"))]


def write_rail(shape: Shape, below, d) -> list:
    """The railing round a tier's balcony, along the roof below it."""
    return [
        IronworkNode(id=shape.id, kind="ironwork", trace=tuple(shape.trace),
                     props={**xywh(shape.scope), "guards": "opening", "max_gap": shape.attr("rail_gap"), "ornament_count": 2})
    ]


def write_lattice(shape: Shape, below, d) -> list:
    """The lattice of a window between posts (renji-mado)."""
    return [
        IronworkNode(id=f"{shape.parent.id}/lattice", kind="ironwork", trace=trace_of(shape, "screen_gap"),
                     props={**xywh(shape.scope), "guards": "opening", "ironwork_pattern": "timber_lattice",
                            "max_gap": shape.attr("screen_gap"), "ornament_count": 2})
    ]


register_writer("pagoda.eave", write_eave)
register_writer("pagoda.finial", write_finial)
register_writer("pagoda.rail", write_rail)
register_writer("pagoda.lattice", write_lattice)

STYLE = load_style(Path(__file__).with_name("pagoda.toml"))


def pagoda_grammar() -> Grammar:
    return STYLE.grammar()


def derive_pagoda(site: PagodaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_pagoda(site: PagodaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
