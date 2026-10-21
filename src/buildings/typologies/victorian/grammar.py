"""The San Francisco Victorian as a split grammar.

Bay-window zone | entry zone on every floor, a three-faced bay whose side
share separates the slanted Italianate from the square Stick, a stoop, and a
false front or a Queen Anne gable and turret.

The style is its rule file, ``victorian.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, SocleNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer

LOT = 7.62  # 25 ft


@dataclass(frozen=True)
class VictorianSite:
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float = LOT



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
                         "hoist_beam": None, "wall_material": top.attr("paint")}),
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


register_writer("victorian.top", write_top)
register_writer("victorian.turret", write_turret)
def write_stoop(stoop: Shape, below, d) -> list:
    """The wooden stair up to the parlour door, seen front-on: a stack of
    treads between two strings, a newel post at the foot of each (R-1)."""
    s = stoop.scope
    n = int(stoop.attrs.get("risers", 12))
    rise = s.h / n
    string, newel_w, newel_h = 0.09, 0.2, 1.05
    nodes = []

    def piece(suffix, x0, y0, x1, y1):
        nodes.append(GableNode(id=f"{stoop.id}/{suffix}", kind="gable", trace=tuple(stoop.trace),
                               props={"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "form": "stoop",
                                      "points": ((x0, y0), (x0, y1), (x1, y1), (x1, y0)),
                                      "hoist_beam": None, "wall_material": "stone"}))

    for k in range(n):
        y0 = s.y + k * rise
        piece(f"tread{k}", s.x + string, y0 + 0.012, s.x + s.w - string, y0 + rise)
    # The strings rise to the door, a railing above them; newels at the foot.
    piece("string_l", s.x, s.y, s.x + string, s.y + s.h + 0.9)
    piece("string_r", s.x + s.w - string, s.y, s.x + s.w, s.y + s.h + 0.9)
    piece("newel_l", s.x - newel_w / 2.0, s.y, s.x + newel_w / 2.0, s.y + newel_h)
    piece("newel_r", s.x + s.w - newel_w / 2.0, s.y, s.x + s.w + newel_w / 2.0, s.y + newel_h)
    return nodes


def write_fence(fence: Shape, below, d) -> list:
    """A board fence and gate across a side yard, in the house's paint."""
    s = fence.scope
    h = 1.8
    return [GableNode(id=fence.id, kind="gable", trace=tuple(fence.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": h, "form": "stoop",
                             "points": ((s.x, s.y), (s.x, s.y + h), (s.x + s.w, s.y + h), (s.x + s.w, s.y)),
                             "hoist_beam": None, "wall_material": fence.attr("paint")})]


def write_porch_shade(shade: Shape, below, d) -> list:
    """The shade inside a recessed entry porch, laid on the wall before the
    door in it is drawn."""
    return [SocleNode(id=shade.id, kind="socle", trace=tuple(shade.trace),
                      props={**kit.xywh(shade.scope), "treatment": "porch", "paint": "porch_shadow"})]


def write_storey(storey: Shape, below, d) -> list:
    """A storey, its porch shade laid on the wall before its openings."""
    out = kit.write_storey(storey, below, d)
    node = out[0]
    socles = tuple(c for c in node.children if c.kind == "socle")
    rest = tuple(c for c in node.children if c.kind != "socle")
    return [replace(node, children=socles + rest), *out[1:]]


register_writer("victorian.porch_shade", write_porch_shade)
register_writer("victorian.storey", write_storey)
register_writer("victorian.stoop", write_stoop)
register_writer("victorian.fence", write_fence)

STYLE = load_style(Path(__file__).with_name("victorian.toml"))


def victorian_grammar() -> Grammar:
    return STYLE.grammar()


def derive_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_victorian(site: VictorianSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def victorian_type(year: int, seed: int = 0) -> str:
    """The type the rule file draws for a house of this date and builder."""
    lot, _ = derive_victorian(VictorianSite(year, BuildingClass.ORDINARY, seed))
    return lot.attrs["kind"]
