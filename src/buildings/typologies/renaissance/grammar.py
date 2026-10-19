"""The Renaissance palazzo as a split grammar.

Three storeys under a crowning cornice, every one cut by one rhythm of bays.
The family's architect (the seed) and the date choose how the front is
dressed: superimposed pilasters, one order a floor (Rucellai); rustication
graded from rough to smooth as it climbs (Medici, Strozzi); or the Roman
palazzo's plain wall, rusticated quoins and aedicule windows (Farnese). The
piani nobili of the Florentine types open in bifore, two round-arched lights
under one arch.

The style is its rule file, ``renaissance.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (the arch over a bifora, a window's pediment, rustication), and the
entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, SocleNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class RenaissanceSite:
    width: float  # metres of street frontage
    year: int
    klass: BuildingClass
    seed: int = 0  # the family and its architect


def _lift(fn):
    """Outlines drawn inside a bay or a storey stand on the building, which is
    where the renderer draws outlines."""

    def write(shape: Shape, below, d):
        outlines = [n for n in below if n.kind == "gable"]
        rest = [n for n in below if n.kind != "gable"]
        return [*fn(shape, rest, d), *outlines]

    return write


def write_storey(storey: Shape, below, d) -> list:
    """A storey, its rustication laid on the wall before the windows cut it."""
    out = _lift(kit.write_storey)(storey, below, d)
    node = out[0]
    socles = tuple(c for c in node.children if c.kind == "socle")
    rest = tuple(c for c in node.children if c.kind != "socle")
    return [replace(node, children=socles + rest), *out[1:]]


def write_rustication(shape: Shape, below, d) -> list:
    """Coursed stone over a rectangle: its courses and blocks the rules state."""
    s = shape.scope
    return [
        SocleNode(
            id=shape.id,
            kind="socle",
            trace=tuple(shape.trace),
            props={
                **kit.xywh(s),
                "treatment": shape.attrs["treatment"],
                "course_columns": shape.attrs["course_columns"],
                "course_rows": shape.attrs["course_rows"],
            },
        )
    ]


def _outline(shape: Shape, suffix: str, pts, form: str) -> GableNode:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return GableNode(
        id=f"{shape.id}{suffix}",
        kind="gable",
        trace=tuple(shape.trace),
        props={"x": min(xs), "y": min(ys), "w": max(xs) - min(xs), "h": max(ys) - min(ys), "form": form,
               "points": tuple(pts), "hoist_beam": None, "wall_material": "stone"},
    )


def _arc(cx: float, cy: float, r: float, a0: float, a1: float, steps: int = 16):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / steps), cy + r * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]


def write_archivolt(shape: Shape, below, d) -> list:
    """The round arch over a bifora, struck on its whole width from the
    springing of its two lights, and the oculus in the tympanum between."""
    s = shape.scope
    cx, r = s.x + s.w / 2.0, s.w / 2.0
    band = shape.attrs["band"]
    nodes = [
        _outline(shape, "", _arc(cx, s.y, r, math.pi, 0.0), "archivolt"),
        _outline(shape, "/extrados", _arc(cx, s.y, r + band, math.pi, 0.0), "archivolt"),
    ]
    oculus = shape.attrs["oculus"]
    if oculus > 0:
        cy = s.y + r - band - oculus * 1.1
        nodes.append(_outline(shape, "/oculus", _arc(cx, cy, oculus, 0.0, 2 * math.pi, 20), "archivolt"))
    return nodes


def write_pediment(shape: Shape, below, d) -> list:
    """A window's pediment: its cornice, and a triangle or a segment over it."""
    s = shape.scope
    base = s.y + s.h * 0.3
    nodes = [_outline(shape, "/cornice", [(s.x, s.y), (s.x + s.w, s.y), (s.x + s.w, base), (s.x, base), (s.x, s.y)], "pediment")]
    if shape.attr("pediment") == "triangular":
        pts = [(s.x, base), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w, base)]
    else:
        # A segment of a circle through both ends and the crown.
        half, rise = s.w / 2.0, s.y + s.h - base
        r = (half * half + rise * rise) / (2 * rise)
        cy = s.y + s.h - r
        a = math.asin(half / r)
        pts = _arc(s.x + half, cy, r, math.pi / 2 + a, math.pi / 2 - a)
    nodes.append(_outline(shape, "", pts, "pediment"))
    return nodes


register_writer("renaissance.storey", write_storey)
register_writer("renaissance.cell", _lift(kit.write_cell))
register_writer("renaissance.rustication", write_rustication)
register_writer("renaissance.archivolt", write_archivolt)
register_writer("renaissance.pediment", write_pediment)

STYLE = load_style(Path(__file__).with_name("renaissance.toml"))


def renaissance_grammar() -> Grammar:
    return STYLE.grammar()


def derive_renaissance(site: RenaissanceSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_renaissance(site: RenaissanceSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def palazzo_type(site: RenaissanceSite) -> str:
    """The dress the rule file gives this palazzo: rucellai, medici, strozzi or farnese."""
    lot, _ = derive_renaissance(site)
    return lot.attrs["kind"]
