"""The Beaux-Arts / Renaissance-Revival civic building as a split grammar.

A rusticated base under either a giant order through two or three storeys
(colonnade, end pavilions, attic, a sculpture group over the centre) or a
palazzo's storey-by-storey front under one heavy cornice; the seed and the
date choose.

The style is its rule file, ``beaux_arts.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (the rusticated base, the podium steps, the sculpture group), and the
entry points.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, Node, SocleNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class BeauxArtsSite:
    width: float  # metres of front
    year: int
    klass: BuildingClass
    seed: int = 0


def write_storey(storey: Shape, below, d) -> list[Node]:
    """The kit's storey, with its rustication drawn first, under the bays."""
    node, *rest = kit.write_storey(storey, below, d)
    socles = [c for c in node.children if c.kind == "socle"]
    others = [c for c in node.children if c.kind != "socle"]
    return [replace(node, children=tuple(socles + others)), *rest]


def write_socle(shape: Shape, below, d) -> list[Node]:
    """Rustication: blocks about 1.4 m long in 0.55 m courses."""
    s = shape.scope
    return [SocleNode(id=shape.id, kind="socle", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "treatment": shape.attr("rustication"),
                             "course_columns": max(1, round(s.w / 1.4)), "course_rows": max(1, round(s.h / 0.55))})]


def write_flight(shape: Shape, below, d) -> list[Node]:
    """The podium steps seen from the front, each step down a little wider."""
    s = shape.scope
    n = max(3, round(s.h / 0.17))
    splay = s.w * 0.12
    left = [(s.x, s.y)]
    for k in range(n):
        y1 = s.y + s.h * (k + 1) / n
        left += [(s.x + splay * k / n, y1), (s.x + splay * (k + 1) / n, y1)]
    right = [(s.x + s.w - (px - s.x), py) for px, py in reversed(left)]
    return [GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "form": "stoop", "points": tuple(left + right),
                             "hoist_beam": None, "wall_material": "stone"})]


# The left half of a sculpture group on its plinth, as shares of its box:
# a reclining figure at the corner, a seated one, then the standing figure
# at the centre (Grand Central's Mercury between Hercules and Minerva).
_GROUP = (
    (0.0, 0.0), (0.0, 0.16), (0.04, 0.16), (0.07, 0.26), (0.14, 0.30), (0.18, 0.38),
    (0.22, 0.36), (0.26, 0.50), (0.30, 0.58), (0.33, 0.56), (0.36, 0.52), (0.40, 0.62),
    (0.43, 0.76), (0.46, 0.84), (0.47, 0.92), (0.50, 1.0),
)


def write_sculpture(shape: Shape, below, d) -> list[Node]:
    """A sculpture group standing on the attic over the centre, as one block."""
    s = shape.scope
    left = [(s.x + s.w * fx, s.y + s.h * fy) for fx, fy in _GROUP]
    right = [(s.x + s.w - (px - s.x), py) for px, py in reversed(left[:-1])]
    return [GableNode(id=shape.id, kind="gable", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "form": "spire", "points": tuple(left + right),
                             "hoist_beam": None, "wall_material": "stone"})]


register_writer("beaux_arts.storey", write_storey)
register_writer("beaux_arts.socle", write_socle)
register_writer("beaux_arts.flight", write_flight)
register_writer("beaux_arts.sculpture", write_sculpture)

STYLE = load_style(Path(__file__).with_name("beaux_arts.toml"))


def beaux_arts_grammar() -> Grammar:
    return STYLE.grammar()


def derive_beaux_arts(site: BeauxArtsSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_beaux_arts(site: BeauxArtsSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def manner(site: BeauxArtsSite) -> str:
    """``giant`` or ``palazzo``: the manner the rule file gives this site."""
    lot, _ = derive_beaux_arts(site)
    return lot.attrs["mode"]
