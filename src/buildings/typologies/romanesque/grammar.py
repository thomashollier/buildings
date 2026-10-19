"""The Romanesque church front as a split grammar.

Round arches stacked in tiers. The master mason (the seed) builds one of two
fronts: the Pisan screen -- a blind arcade over the portals, then open
galleries of small arches on colonnettes, tier over tier, the aisles' roofs
sloping in beside the nave's -- or the fortress front between two square
towers, its portal a nest of round orders, an oculus over it, and the towers
rising in stages under Lombard bands to battlements or helm roofs.

The style is its rule file, ``romanesque.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer (a gallery's arcade, a blind arch, a portal's orders, a corbel table,
the tops), and the entry points.
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
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class RomanesqueSite:
    width: float  # metres across the front
    year: int
    klass: BuildingClass
    seed: int = 0  # the master mason: Pisan screen or fortress front


def _lift(fn):
    """Outlines drawn inside a bay or a storey stand on the building, which is
    where the renderer draws outlines."""

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


def _semi(x0: float, x1: float, y: float, steps: int = 12):
    """A semicircular arch from springing to springing."""
    c, r = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    return [(c - r * math.cos(math.pi * i / steps), y + r * math.sin(math.pi * i / steps)) for i in range(steps + 1)]


def _rect(x, y, w, h):
    return [(x, y), (x, y + h), (x + w, y + h), (x + w, y)]


def write_gallery(gallery: Shape, below, d) -> list:
    """An open gallery: the dark wall behind, the arcade's spandrel band over
    the colonnettes the rules stood, and the plinth they stand on."""
    s = gallery.scope
    a = gallery.attrs
    wall = a["marble"]
    base, spring = s.y + a["plinth"], s.y + a["spring"]
    half = a["post_w"] / 2.0
    centres = [s.x + half, *(p["x"] + p["w"] / 2.0 for p in a["posts"]), s.x + s.w - half]
    band = [(s.x, s.y + s.h), (s.x + s.w, s.y + s.h), (s.x + s.w, spring)]
    for left, right in zip(reversed(centres[:-1]), reversed(centres[1:])):
        band += [(right, spring), *reversed(_semi(left, right, spring))]
    band += [(s.x, spring)]
    return [
        _node(gallery, "/back", _rect(s.x, base, s.w, spring - base), "gallery_back", "shadow"),
        _node(gallery, "/arcade", band, "arcade", wall),
        _node(gallery, "/plinth", _rect(s.x, s.y, s.w, a["plinth"]), "plinth", wall),
        *below,
    ]


def write_blind_arch(arch: Shape, below, d) -> list:
    """A blind arch over a bay, and the Pisan lozenge in its tympanum."""
    s = arch.scope
    nodes = [_node(arch, "", _semi(s.x, s.x + s.w, s.y, 16), "archivolt")]
    if arch.attrs["lozenge"]:
        cx, cy, r = s.x + s.w / 2.0, s.y + s.w * 0.24, s.w * 0.16
        nodes.append(_node(arch, "/lozenge", [(cx - r, cy), (cx, cy + r), (cx + r, cy), (cx, cy - r), (cx - r, cy)], "lozenge"))
    return nodes


def write_portal(portal: Shape, below, d) -> list:
    """A portal of round orders stepping in to a plain tympanum over the door."""
    s = portal.scope
    a = portal.attrs
    x0, x1 = s.x + a["margin"], s.x + s.w - a["margin"]
    spring = s.y + a["spring"]
    nodes = [_node(portal, "/wall", _rect(s.x, s.y, s.w, s.h), "portal_wall")]
    for k in range(a["rings"] + 1):
        lx, rx = x0 + k * a["ring_w"], x1 - k * a["ring_w"]
        inner = k == a["rings"]
        nodes.append(_node(portal, "/tympanum" if inner else f"/ring{k}", [(lx, s.y), *_semi(lx, rx, spring), (rx, s.y)], "archivolt",
                           "terracotta" if inner else ("brick_buff", "stone")[k % 2]))
    lx, rx = x0 + a["rings"] * a["ring_w"], x1 - a["rings"] * a["ring_w"]
    nodes.append(_node(portal, "/lintel", [(lx, spring), (rx, spring)], "lintel"))
    return [*nodes, *below]


def write_corbel_table(band: Shape, below, d) -> list:
    """A Lombard band: a row of small round arches hanging under a string
    course, as many as the rules give it."""
    s = band.scope
    n = band.attrs["arches"]
    step = s.w / n
    pts = [(s.x, s.y + s.h)]
    for k in range(n):
        lx = s.x + k * step
        pts += [(lx, s.y + s.h - step * 0.5), *_semi(lx, lx + step, s.y + s.h - step * 0.5, 6)[1:]]
    pts.append((s.x + s.w, s.y + s.h))
    return [_node(band, "", pts, "corbel_table")]


def write_top(top: Shape, below, d) -> list:
    """What ends a mass: battlements, a helm roof over a gable, a gable, or
    the sloping shoulder of an aisle roof."""
    s = top.scope
    kind = top.attrs["top"]
    wall = top.attr("wall_material")
    cx = s.x + s.w / 2.0
    if kind == "battlements":
        n = top.attrs["merlons"]
        step = s.w / (2 * n - 1)
        nodes = [_node(top, "/parapet", _rect(s.x, s.y, s.w, s.h * 0.45), "parapet", wall)]
        for k in range(n):
            nodes.append(_node(top, f"/merlon{k}", _rect(s.x + 2 * k * step, s.y + s.h * 0.45, step, s.h * 0.55), "merlon", wall))
        return nodes
    if kind == "helm":
        return [
            _node(top, "/roof", [(s.x, s.y), (cx, s.y + s.h), (s.x + s.w, s.y)], "spire", "lead_roof"),
            _node(top, "", [(s.x, s.y), (cx, s.y + s.h * 0.32), (s.x + s.w, s.y)], "front_gable", wall),
        ]
    if kind == "shoulder_left":
        return [_node(top, "", [(s.x, s.y), (s.x + s.w, s.y + s.h), (s.x + s.w, s.y)], "front_gable", wall)]
    if kind == "shoulder_right":
        return [_node(top, "", [(s.x, s.y), (s.x, s.y + s.h), (s.x + s.w, s.y)], "front_gable", wall)]
    # A gable, an oculus in it.
    r = min(s.w, s.h) * 0.14
    oculus = [(cx + r * math.cos(2 * math.pi * i / 20), s.y + s.h * 0.36 + r * math.sin(2 * math.pi * i / 20)) for i in range(21)]
    return [_node(top, "", [(s.x, s.y), (cx, s.y + s.h), (s.x + s.w, s.y)], "front_gable", wall), _node(top, "/oculus", oculus, "tracery", "shadow")]


register_writer("romanesque.storey", _lift(kit.write_storey))
register_writer("romanesque.cell", _lift(kit.write_cell))
register_writer("romanesque.gallery", write_gallery)
register_writer("romanesque.blind_arch", write_blind_arch)
register_writer("romanesque.portal", write_portal)
register_writer("romanesque.corbel_table", write_corbel_table)
register_writer("romanesque.top", write_top)

STYLE = load_style(Path(__file__).with_name("romanesque.toml"))


def romanesque_grammar() -> Grammar:
    return STYLE.grammar()


def derive_romanesque(site: RomanesqueSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_romanesque(site: RomanesqueSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def front_type(site: RomanesqueSite) -> str:
    """The front the rule file gives this church: pisan or fortress."""
    lot, _ = derive_romanesque(site)
    return lot.attrs["kind"]
