"""The Brooklyn and Manhattan brownstone row house as a split grammar.

An English basement, a high stoop to the parlour floor, three bays, and the
dress of its date: Italianate hoods on consoles, Neo-Grec incised lintels,
Romanesque rock-face and round arches; a bay front on a wide late lot.

The style is its rule file, ``brownstone.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (the stoop, the hoods and lintels, the grilles, the rock-faced base),
and the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, CorniceNode, GableNode, IronworkNode, Node, SocleNode, StringCourseNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer

LOT = 6.1  # 20 ft


@dataclass(frozen=True)
class BrownstoneSite:
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float = LOT


def write_stoop(stoop: Shape, below, d) -> list[Node]:
    """The stoop seen from the street: a stack of treads, flaring a little at
    the foot where its balustrade scrolls out."""
    s = stoop.scope
    n = max(4, round(s.h / 0.18))
    flare = 0.25
    left = [(s.x - flare, s.y)]
    for k in range(n):
        y1 = s.y + s.h * (k + 1) / n
        x = s.x - flare * max(0.0, 1.0 - 3.0 * (k + 1) / n)
        left += [(left[-1][0], y1), (x, y1)]
    right = [(s.x + s.w - (px - s.x), py) for px, py in reversed(left)]
    return [GableNode(id=stoop.id, kind="gable", trace=tuple(stoop.trace),
                      props={**kit.xywh(s), "form": "stoop", "points": tuple(left + right),
                             "hoist_beam": None, "wall_material": "brick_dark"})]


def write_hood(hood: Shape, below, d) -> list[Node]:
    """An Italianate hood on two consoles, or a Neo-Grec lintel slab with its
    incised line, across the head of an opening."""
    s = hood.scope
    if hood.attr("hood_kind") == "bracketed":
        # The console cornice hangs its frieze below its line: stand it on
        # the head so the frieze sits just over the opening.
        return [CorniceNode(id=hood.id, kind="cornice", trace=tuple(hood.trace),
                            props={"x": s.x, "y": s.y + s.h * 0.75, "w": s.w, "h": s.h, "projection": s.h,
                                   "cornice_ornament": "bracketed", "ornament_count": 2})]
    return [StringCourseNode(id=hood.id, kind="string_course", trace=tuple(hood.trace),
                             props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "course_kind": "plat_bande",
                                    "projection": s.h, "ornament_count": 2})]


def write_cell(cell: Shape, below, d) -> list[Node]:
    """The kit's bay; hoods and lintels belong to the storey's lines, not the bay."""
    lines = [n for n in below if n.kind in ("cornice", "string_course")]
    rest = [n for n in below if n.kind not in ("cornice", "string_course")]
    return [*kit.write_cell(cell, rest, d), *lines]


def write_grille(grille: Shape, below, d) -> list[Node]:
    """Iron bars across a basement window, in its reveal."""
    return [IronworkNode(id=grille.id, kind="ironwork", trace=tuple(grille.trace),
                         props={**kit.xywh(grille.scope), "guards": "window_grille", "max_gap": 0.12,
                                "ironwork_pattern": "renaissance_revival", "ornament_count": 2})]


def write_socle(shape: Shape, below, d) -> list[Node]:
    """Rock-faced brownstone in rough courses."""
    s = shape.scope
    return [SocleNode(id=shape.id, kind="socle", trace=tuple(shape.trace),
                      props={**kit.xywh(s), "treatment": "picturesque_rustication",
                             "course_columns": max(1, round(s.w / 0.9)), "course_rows": max(1, round(s.h / 0.4))})]


def write_storey(storey: Shape, below, d) -> list[Node]:
    """The kit's storey, its rock-face drawn first, under the bays."""
    node, *rest = kit.write_storey(storey, below, d)
    socles = [c for c in node.children if c.kind == "socle"]
    others = [c for c in node.children if c.kind != "socle"]
    return [replace(node, children=tuple(socles + others)), *rest]


register_writer("brownstone.stoop", write_stoop)
register_writer("brownstone.hood", write_hood)
register_writer("brownstone.cell", write_cell)
register_writer("brownstone.grille", write_grille)
register_writer("brownstone.socle", write_socle)
register_writer("brownstone.storey", write_storey)

STYLE = load_style(Path(__file__).with_name("brownstone.toml"))


def brownstone_grammar() -> Grammar:
    return STYLE.grammar()


def derive_brownstone(site: BrownstoneSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_brownstone(site: BrownstoneSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def brownstone_dress(year: int) -> str:
    """The dress the rule file gives a house of this date."""
    lot, _ = derive_brownstone(BrownstoneSite(year, BuildingClass.ORDINARY))
    return lot.attrs["kind"]
