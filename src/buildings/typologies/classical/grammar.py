"""The classical temple front as a split grammar.

A pedimented portico of four, six or eight columns on a stepped base or a
podium, every proportion set by its order from one module, the column's
diameter: the spacing of the columns, their height, the entablature's depth,
the pediment's slope. The same grammar writes the ancient temple and its
Greek Revival use, a custom house or a bank whose portico stands across a
plain block with windows.

The style is its rule file, ``classical.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (triglyphs, Ionic volutes, the pediment, a stair's treads), and the
entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, SocleNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class ClassicalSite:
    width: float  # metres of frontage: the portico's, or the whole block's
    year: int  # negative for BC: an ancient temple before 1000, a Greek Revival building after
    klass: BuildingClass  # how many columns the front can afford
    seed: int = 0  # the architect: the order, and for a revival building its layout


def _lift(fn):
    """Outlines drawn inside a storey stand on the building, which is where
    the renderer draws outlines."""

    def write(shape: Shape, below, d):
        outlines = [n for n in below if n.kind == "gable"]
        rest = [n for n in below if n.kind != "gable"]
        return [*fn(shape, rest, d), *outlines]

    return write


def _node(shape: Shape, suffix: str, pts, form: str, material: str = "stone") -> GableNode:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return GableNode(
        id=f"{shape.id}{suffix}",
        kind="gable",
        trace=tuple(shape.trace),
        props={"x": min(xs), "y": min(ys), "w": max(xs) - min(xs), "h": max(ys) - min(ys), "form": form,
               "points": tuple(pts), "hoist_beam": None, "wall_material": material},
    )


def write_pediment(ped: Shape, below, d) -> list:
    """The pediment: the raking cornices and the tympanum inside them."""
    s = ped.scope
    cx = s.x + s.w / 2.0
    band = ped.attrs["raking"]
    inner_h = s.h - band * 1.8
    inner_half = inner_h / s.h * s.w / 2.0
    return [
        _node(ped, "", [(s.x, s.y), (cx, s.y + s.h), (s.x + s.w, s.y)], "front_gable"),
        _node(ped, "/tympanum", [(cx - inner_half, s.y + band * 0.4), (cx, s.y + band * 0.4 + inner_h), (cx + inner_half, s.y + band * 0.4)], "tympanum", ped.attrs["tympanum"]),
    ]


def write_triglyph(t: Shape, below, d) -> list:
    """A triglyph: a block with two whole grooves and a half one either side."""
    s = t.scope
    nodes = [_node(t, "", [(s.x, s.y), (s.x, s.y + s.h), (s.x + s.w, s.y + s.h), (s.x + s.w, s.y)], "triglyph")]
    for k, f in enumerate((1 / 3, 2 / 3)):
        nodes.append(_node(t, f"/groove{k}", [(s.x + s.w * f, s.y + s.h * 0.1), (s.x + s.w * f, s.y + s.h * 0.95)], "triglyph"))
    return nodes


def write_volutes(v: Shape, below, d) -> list:
    """An Ionic capital seen from the front: the echinus and a volute at each end."""
    s = v.scope
    r = s.h * 0.5
    nodes = [_node(v, "/abacus", [(s.x + r, s.y + s.h), (s.x + s.w - r, s.y + s.h)], "volute")]
    for side, cx, flip in (("l", s.x + r, -1.0), ("r", s.x + s.w - r, 1.0)):
        pts = [(cx + flip * r * (1 - i / 24 * 0.85) * math.cos(2 * math.pi * 1.5 * i / 24 + math.pi / 2),
                s.y + r + r * (1 - i / 24 * 0.85) * math.sin(2 * math.pi * 1.5 * i / 24 + math.pi / 2)) for i in range(25)]
        nodes.append(_node(v, f"/{side}", pts, "volute"))
    return nodes


def write_treads(t: Shape, below, d) -> list:
    """A flight of steps seen from the front: a tread line at every riser."""
    return [SocleNode(id=t.id, kind="socle", trace=tuple(t.trace),
                      props={**kit.xywh(t.scope), "treatment": "flat_incised_refends", "course_columns": 1, "course_rows": t.attrs["risers"]})]


register_writer("classical.storey", _lift(kit.write_storey))
register_writer("classical.pediment", write_pediment)
register_writer("classical.triglyph", write_triglyph)
register_writer("classical.volutes", write_volutes)
register_writer("classical.treads", write_treads)

STYLE = load_style(Path(__file__).with_name("classical.toml"))


def classical_grammar() -> Grammar:
    return STYLE.grammar()


def derive_classical(site: ClassicalSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_classical(site: ClassicalSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def portico_of(site: ClassicalSite) -> dict:
    """The order, column count and module the rule file gives this front."""
    lot, _ = derive_classical(site)
    a = lot.attrs
    return {"order": a["column_order"], "columns": a["columns"], "module": a["module"], "use": a["use"]}
