"""The Venetian Gothic palazzo as a split grammar.

Every storey cut wing | centre | wing; the nobile centre a polifora of ogee
lights on colonnettes; the water gate below. Before 1300 the older
Veneto-Byzantine casa-fondaco: a portico and an arcade across the whole
front, between two corner towers, crenellated on the grandest.

The style is its rule file, ``venice.toml`` beside this module; this module
holds only the situation it takes, the crenellation the file names by
writer, and the entry points.
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


@dataclass(frozen=True)
class PalazzoSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


#: The Fondaco's merlons, INFERRED from photographs: a low band, then
#: merlons about as wide as the gaps between them, each pointed at its top.
MERLON_W = 0.7
MERLON_BAND = 0.25


def write_crenellation(merlons: Shape, below, d) -> list:
    """A row of pointed merlons standing on the cornice, as one outline."""
    s = merlons.scope
    n = max(2, round(s.w / (2 * MERLON_W)))
    pitch = s.w / n
    body = (s.h - MERLON_BAND) * 0.6
    pts = [(s.x, s.y), (s.x, s.y + MERLON_BAND)]
    for k in range(n):
        x0 = s.x + k * pitch + (pitch - MERLON_W) / 2.0
        top = s.y + MERLON_BAND + body
        pts += [(x0, s.y + MERLON_BAND), (x0, top), (x0 + MERLON_W / 2.0, s.y + s.h), (x0 + MERLON_W, top), (x0 + MERLON_W, s.y + MERLON_BAND)]
    pts += [(s.x + s.w, s.y + MERLON_BAND), (s.x + s.w, s.y)]
    return [GableNode(id=merlons.id, kind="gable", trace=tuple(merlons.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "step", "points": tuple(pts),
                             "hoist_beam": None, "wall_material": "stone"})]


register_writer("venice.crenellation", write_crenellation)

STYLE = load_style(Path(__file__).with_name("venice.toml"))


def venice_grammar() -> Grammar:
    return STYLE.grammar()


def derive_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
