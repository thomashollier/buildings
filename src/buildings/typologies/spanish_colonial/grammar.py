"""The Spanish Colonial Revival public building as a split grammar.

Unequal masses -- a bell tower, the main block, a low loggia wing -- in white
stucco under low red tile roofs; small deep windows behind iron grilles, iron
balconies, an arcade, and a carved portal.

The style is its rule file, ``spanish_colonial.toml`` beside this module;
this module holds only the situation it takes, the drawings the file names by
writer (the tile roof, the portal's crest, the grille), and the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode, Node
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer

EAVE = 0.35  # a tile roof's little overhang, INFERRED


@dataclass(frozen=True)
class SpanishSite:
    width: float  # metres of front
    year: int
    klass: BuildingClass
    seed: int = 0


def write_tile_roof(roof: Shape, below, d) -> list[Node]:
    """A low hipped roof of red tile seen from the street: each free end a
    hip at the roof's pitch, an end against a taller neighbour square."""
    s = roof.scope
    run = s.h / math.tan(math.radians(float(roof.attr("pitch"))))
    left_free, right_free = not roof.attr("abut_left"), not roof.attr("abut_right")
    pts: list[tuple[float, float]] = []
    if left_free:
        pts += [(s.x - EAVE, s.y - 0.12), (s.x + min(run, s.w / 2.0), s.y + s.h)]
    else:
        pts += [(s.x, s.y), (s.x, s.y + s.h)]
    if right_free:
        pts += [(s.x + s.w - min(run, s.w / 2.0), s.y + s.h), (s.x + s.w + EAVE, s.y - 0.12)]
    else:
        pts += [(s.x + s.w, s.y + s.h), (s.x + s.w, s.y)]
    # Hips meeting before the ridge make a pyramid: drop the duplicate apex.
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return [GableNode(id=roof.id, kind="gable", trace=tuple(roof.trace),
                      props={**kit.xywh(s), "form": "pavilion", "points": tuple(out),
                             "hoist_beam": None, "wall_material": "tile_red"})]


def write_portal(portal: Shape, below, d) -> list[Node]:
    """The carved frame's outline: up the pilasters, then a crest of scrolls
    stepping in to a finial over the door."""
    s = portal.scope
    top = s.y + s.h - 1.8  # where the frame's straight sides end
    rise = s.y + s.h - top
    half = [
        (0.0, s.y), (0.0, top), (0.08, top + 0.15 * rise), (0.18, top + 0.12 * rise), (0.22, top + 0.32 * rise),
        (0.30, top + 0.36 * rise), (0.33, top + 0.55 * rise), (0.40, top + 0.62 * rise), (0.42, top + 0.82 * rise),
        (0.47, top + 0.86 * rise), (0.5, top + rise),
    ]
    left = [(s.x + s.w * fx, y) for fx, y in half]
    right = [(s.x + s.w - (px - s.x), py) for px, py in reversed(left[:-1])]
    return [GableNode(id=portal.id, kind="gable", trace=tuple(portal.trace),
                      props={**kit.xywh(s), "form": "neck", "points": tuple(left + right),
                             "hoist_beam": None, "wall_material": "terracotta"}),
            *below]


def write_grille(grille: Shape, below, d) -> list[Node]:
    """Wrought-iron bars across the window, in its reveal."""
    return [IronworkNode(id=grille.id, kind="ironwork", trace=tuple(grille.trace),
                         props={**kit.xywh(grille.scope), "guards": "window_grille", "max_gap": 0.14,
                                "ironwork_pattern": "renaissance_revival", "ornament_count": 2})]


register_writer("spanish_colonial.tile_roof", write_tile_roof)
register_writer("spanish_colonial.portal", write_portal)
register_writer("spanish_colonial.grille", write_grille)

STYLE = load_style(Path(__file__).with_name("spanish_colonial.toml"))


def spanish_colonial_grammar() -> Grammar:
    return STYLE.grammar()


def derive_spanish_colonial(site: SpanishSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_spanish_colonial(site: SpanishSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
