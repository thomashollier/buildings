"""The San Francisco Victorian as a split grammar.

Bay-window zone | entry zone on every floor, a three-faced bay whose side
share separates the slanted Italianate from the square Stick, a stoop, and a
false front or a Queen Anne gable and turret.

The style is its rule file, ``victorian.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import load_style, register_writer

LOT = 7.62  # 25 ft


@dataclass(frozen=True)
class VictorianSite:
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float = LOT

_PAINTS = ("clapboard_sage", "clapboard_blue", "clapboard_cream", "clapboard_rose")


def _site(shape: Shape) -> "VictorianSite":
    return shape.attr("site")


def write_top(top: Shape, below, d) -> list:
    if top.attrs["kind"] != "queen_anne":
        return list(below)
    s = top.scope
    pts = ((s.x - (0.25 if s.x <= 0 else 0.0), s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.25, s.y))
    return [
        GableNode(id=top.id, kind="gable", trace=tuple(top.trace),
                  props={**{"x": s.x, "y": s.y, "w": s.w, "h": s.h}, "form": "front_gable", "points": pts,
                         "hoist_beam": None, "wall_material": _PAINTS[_site(top).seed % len(_PAINTS)]}),
        *below,
    ]


def write_turret(turret: Shape, below, d) -> list:
    s = turret.scope
    room = turret.children[0].scope
    y0 = room.y + room.h
    pts = ((s.x - 0.2, y0), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.2, y0))
    return [
        *below,
        GableNode(id=f"{turret.id}/roof", kind="gable", trace=tuple(turret.trace),
                  props={"x": s.x, "y": y0, "w": s.w, "h": s.y + s.h - y0, "form": "spire", "points": pts,
                         "hoist_beam": None, "wall_material": "shadow"}),
    ]


def write_stoop(stoop: Shape, below, d) -> list:
    """The stair up to the parlour door, drawn as its stepped profile."""
    s = stoop.scope
    n = 8
    pts = [(s.x, s.y)]
    for k in range(n):
        x = s.x + s.w * k / n
        y = s.y + s.h * (k + 1) / n
        pts += [(x, y), (x + s.w / n, y)]
    pts += [(s.x + s.w, s.y)]
    return [GableNode(id=stoop.id, kind="gable", trace=tuple(stoop.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "stoop", "points": tuple(pts),
                             "hoist_beam": None, "wall_material": "stone"})]

register_writer("victorian.top", write_top)
register_writer("victorian.turret", write_turret)
register_writer("victorian.stoop", write_stoop)

STYLE = load_style(Path(__file__).with_name("victorian.toml"))


def victorian_grammar() -> Grammar:
    return STYLE.grammar()


def derive_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def victorian_type(year: int) -> str:
    """The type the rule file gives a house of this date."""
    lot, _ = derive_victorian(VictorianSite(year, BuildingClass.ORDINARY))
    return lot.attrs["kind"]
