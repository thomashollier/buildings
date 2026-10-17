"""The Corbusian block as a split grammar.

Pilotis on the posts' grid, ribbon windows that ignore it (the free facade),
and an off-axis roof pavilion with a curved screen.

The style is its rule file, ``modernist.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer and
the entry points.
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
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class VillaSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


def write_pavilion(pavilion: Shape, below, d) -> list:
    """The pavilion's curved screen wall, bellying out beside the box it
    shelters: the one free curve on an otherwise orthogonal front."""
    s = pavilion.scope
    bulge = s.h * 0.55
    curve = [(s.x - bulge * math.sin(math.pi * k / 12), s.y + s.h * k / 12) for k in range(13)]
    return [
        GableNode(
            id=f"{pavilion.id}/screen",
            kind="gable",
            trace=tuple(pavilion.trace),
            props={"x": s.x - bulge, "y": s.y, "w": bulge, "h": s.h, "form": "pavilion", "points": tuple(curve),
                   "hoist_beam": None, "wall_material": "render_white"},
        ),
        *below,
    ]

register_writer("modernist.pavilion", write_pavilion)

STYLE = load_style(Path(__file__).with_name("modernist.toml"))


def modernist_grammar() -> Grammar:
    return STYLE.grammar()


def derive_modernist(site: VillaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_modernist(site: VillaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
