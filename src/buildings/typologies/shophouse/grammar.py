"""The Straits Chinese shophouse as a split grammar.

A narrow front over a covered 'five-foot way': piers at the street line, the
shop recessed behind them in shade, one or two storeys of tall shuttered
windows above, and a tiled roof behind a parapet or over open eaves. The date
picks the style: Early, Southern Chinese, Early and Late Straits Eclectic,
Art Deco, Early Modern. Shophouses come in rows; every unit of a row is cut
the same way and painted by its own owner.

The style is its rule file, ``shophouse.toml`` beside this module; this module
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
from buildings.typologies.common.kit import trace_of, xywh
from buildings.typologies.common.rulefile import load_style, register_writer
import buildings.typologies.sanaa.grammar  # noqa: F401  -- registers the window-and-fanlight production


@dataclass(frozen=True)
class ShophouseSite:
    width: float  # metres of frontage of one unit
    year: int
    klass: BuildingClass
    seed: int = 0
    units: int = 1  # how many units of the row are drawn


def _gable(shape: Shape, pts, form: str, material: str) -> GableNode:
    return GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                     props={**xywh(shape.scope), "form": form, "points": tuple(pts), "hoist_beam": None, "wall_material": material})


def write_jalousie(shape: Shape, below, d) -> list:
    """The timber jalousie shutters closed over a light, or an iron grille."""
    return [
        IronworkNode(
            id=f"{shape.parent.id}/screen",
            kind="ironwork",
            trace=trace_of(shape, "screen_gap"),
            props={**xywh(shape.scope), "guards": "opening", "ironwork_pattern": "timber_lattice",
                   "max_gap": shape.attr("screen_gap"), "ornament_count": 2},
        )
    ]


def write_roof(shape: Shape, below, d) -> list:
    """The near slope of the tiled roof, seen rising behind the front.

    Painted in clay tile."""
    s = shape.scope
    pts = [(s.x, s.y), (s.x, s.y + s.h), (s.x + s.w, s.y + s.h), (s.x + s.w, s.y)]
    return [_gable(shape, pts, "straight", "tile_red")]


def write_crown(shape: Shape, below, d) -> list:
    """What stands on the parapet's middle: a pediment on a Straits Eclectic
    front, a stepped panel on an Art Deco one."""
    s = shape.scope
    cx = s.x + s.w / 2.0
    if shape.attr("crown_form") == "stepped":
        steps = 3
        left = [(s.x, s.y)]
        for k in range(steps):
            x = s.x + s.w / 2.0 * k / steps * 0.9
            left += [(x, s.y + s.h * k / steps), (x, s.y + s.h * (k + 1) / steps)]
        left += [(cx - s.w * 0.08, s.y + s.h)]
    else:
        left = [(s.x, s.y), (s.x, s.y + s.h * 0.15), (cx, s.y + s.h)]
    right = [(2 * cx - x, y) for x, y in reversed(left[:-1])]
    return [_gable(shape, left + right, "straight", shape.attr("wall_material"))]


register_writer("shophouse.jalousie", write_jalousie)
register_writer("shophouse.roof", write_roof)
register_writer("shophouse.crown", write_crown)

STYLE = load_style(Path(__file__).with_name("shophouse.toml"))


def shophouse_grammar() -> Grammar:
    return STYLE.grammar()


def derive_shophouse(site: ShophouseSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_shophouse(site: ShophouseSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def shophouse_kind(year: int) -> str:
    """The style the rule file gives a shophouse of this date."""
    lot, _ = derive_shophouse(ShophouseSite(5.0, year, BuildingClass.ORDINARY))
    return lot.attrs["kind"]
