"""The Baroque church front as a split grammar.

Two orders: a wide lower one across nave and chapels, a narrower upper one
over the nave, joined by great volutes and crowned by a pediment. Each order
is cut into planes that step forward toward the centre -- pilasters on the
back planes, columns on the front ones -- and the date turns the flat Gesu
front into the stepped and broken fronts of the seventeenth century; a rich
late front may trade its volutes for twin bell towers and show a dome behind.

The style is its rule file, ``baroque.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer
(volutes, pediments, the dome, a bell tower's cap), and the entry points.
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
class BaroqueSite:
    width: float  # metres across the lower order
    year: int
    klass: BuildingClass
    seed: int = 0  # the architect


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


def _ellipse(cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, steps=20):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / steps), cy + ry * math.sin(a0 + (a1 - a0) * i / steps)) for i in range(steps + 1)]


def _spiral(cx, cy, r, turns=1.5, steps=30, flip=1.0):
    return [(cx + flip * r * (1 - i / steps * 0.8) * math.cos(2 * math.pi * turns * i / steps),
             cy + r * (1 - i / steps * 0.8) * math.sin(2 * math.pi * turns * i / steps)) for i in range(steps + 1)]


def _pediment(shape: Shape, suffix: str, x, y, w, h, form: str, material: str = "stone") -> list:
    """A pediment over (x, y, w): triangular, segmental, or broken open at the
    apex round a cartouche."""
    cx = x + w / 2.0
    if form == "segmental":
        half = w / 2.0
        r = (half * half + h * h) / (2 * h)
        a = math.asin(min(1.0, half / r))
        return [_node(shape, suffix, _ellipse(cx, y + h - r, r, r, math.pi / 2 + a, math.pi / 2 - a, 20), "pediment", material)]
    if form == "broken":
        g = w * 0.13
        at = y + h * (1 - g / (w / 2.0))
        pts = [(x, y), (cx - g, at), (cx - g, at - h * 0.28), (cx + g, at - h * 0.28), (cx + g, at), (x + w, y)]
        cart = _ellipse(cx, at - h * 0.05, g * 0.7, h * 0.3, 0, 2 * math.pi, 16)
        return [_node(shape, suffix, pts, "pediment", material), _node(shape, f"{suffix}/cartouche", cart, "cartouche", material)]
    return [_node(shape, suffix, [(x, y), (cx, y + h), (x + w, y)], "pediment", material)]


def write_crown(crown: Shape, below, d) -> list:
    """The pediment over the upper order."""
    s = crown.scope
    return _pediment(crown, "", s.x, s.y, s.w, s.h, crown.attrs["form"])


def write_dressing(dressing: Shape, below, d) -> list:
    """What caps an opening: a pediment, a pediment nested in another (the
    Gesu's portal), or the round head of a niche."""
    s = dressing.scope
    form = dressing.attrs["form"]
    if form == "niche":
        return [_node(dressing, "", _ellipse(s.x + s.w / 2.0, s.y, s.w / 2.0, s.h, math.pi, 0.0, 14), "niche")]
    if form == "nested":
        return [*_pediment(dressing, "", s.x, s.y, s.w, s.h, "triangular"),
                *_pediment(dressing, "/inner", s.x + s.w * 0.12, s.y, s.w * 0.76, s.h * 0.55, "segmental")]
    return _pediment(dressing, "", s.x, s.y, s.w, s.h, form)


def write_volute(volute: Shape, below, d) -> list:
    """A great scroll from the lower order's cornice up to the upper order's
    flank: an S-curve wound into an eye at its foot and a curl at its head."""
    s = volute.scope
    left = volute.attrs["side"] == "left"
    # Drawn for the left side; the right is its mirror.
    def m(px, py):
        return (px, py) if left else (2 * s.x + s.w - px, py)
    curve = []
    for i in range(21):
        t = i / 20
        curve.append(m(s.x + s.w - s.w * t, s.y + 0.2 * s.h + 0.8 * s.h * (0.5 + 0.5 * math.cos(math.pi * t))))
    body = [m(s.x, s.y), m(s.x, s.y + 0.2 * s.h), *reversed(curve), m(s.x + s.w, s.y)]
    r = min(0.14 * s.w, 0.2 * s.h)
    eye = _spiral(*m(s.x + r * 1.05, s.y + 0.2 * s.h - r * 0.05), r, flip=1.0 if left else -1.0)
    curl = _spiral(*m(s.x + s.w - r * 0.5, s.y + s.h - r * 0.5), r * 0.5, flip=-1.0 if left else 1.0)
    return [_node(volute, "", body, "volute"), _node(volute, "/eye", eye, "volute"), _node(volute, "/curl", curl, "volute")]


def write_dome(dome: Shape, below, d) -> list:
    """The dome over the crossing, seen over the front: drum, cupola, lantern."""
    s = dome.scope
    a = dome.attrs
    cx = s.x + s.w / 2.0
    drum_top = s.y + a["drum"]
    foot = s.y + a["foot"]
    cup_h = a["cupola"]
    lw = s.w * 0.16
    lantern_y = drum_top + cup_h * 0.96
    nodes = [
        _node(dome, "/drum", [(s.x, foot), (s.x, drum_top), (s.x + s.w, drum_top), (s.x + s.w, foot)], "drum"),
        _node(dome, "/cupola", _ellipse(cx, drum_top, s.w / 2.0 * 0.94, cup_h, 0.0, math.pi, 24), "cupola", "lead_roof"),
    ]
    for k, f in enumerate((-0.6, -0.25, 0.25, 0.6)):
        bx = cx + f * s.w / 2.0 * 0.94
        nodes.append(_node(dome, f"/rib{k}", [(bx, drum_top), (cx + f * lw / 2.0, lantern_y)], "rib"))
    for k, f in enumerate((-0.7, -0.35, 0.0, 0.35, 0.7)):
        wx = cx + f * s.w / 2.0
        wy = foot + (drum_top - foot) * 0.3
        nodes.append(_node(dome, f"/window{k}", [(wx - s.w * 0.035, wy), (wx - s.w * 0.035, wy + (drum_top - foot) * 0.4), (wx + s.w * 0.035, wy + (drum_top - foot) * 0.4), (wx + s.w * 0.035, wy)], "window", "shadow"))
    top = s.y + s.h
    nodes += [
        _node(dome, "/lantern", [(cx - lw / 2.0, lantern_y), (cx - lw / 2.0, top - (top - lantern_y) * 0.45), (cx + lw / 2.0, top - (top - lantern_y) * 0.45), (cx + lw / 2.0, lantern_y)], "lantern"),
        _node(dome, "/lantern_cap", _ellipse(cx, top - (top - lantern_y) * 0.45, lw / 2.0, (top - lantern_y) * 0.3, 0.0, math.pi, 10), "cupola", "lead_roof"),
        _node(dome, "/cross", [(cx, top - (top - lantern_y) * 0.15), (cx, top)], "cross"),
    ]
    return nodes


def write_cap(cap: Shape, below, d) -> list:
    """A bell tower's cap: a small cupola on a drum, a finial over it."""
    s = cap.scope
    cx = s.x + s.w / 2.0
    drum = s.h * 0.3
    return [
        _node(cap, "/drum", [(s.x + s.w * 0.08, s.y), (s.x + s.w * 0.08, s.y + drum), (s.x + s.w * 0.92, s.y + drum), (s.x + s.w * 0.92, s.y)], "drum"),
        _node(cap, "", _ellipse(cx, s.y + drum, s.w * 0.42, s.h * 0.45, 0.0, math.pi, 16), "cupola", "lead_roof"),
        _node(cap, "/finial", [(cx, s.y + drum + s.h * 0.45), (cx, s.y + s.h)], "cross"),
    ]


register_writer("baroque.storey", _lift(kit.write_storey))
register_writer("baroque.cell", _lift(kit.write_cell))
register_writer("baroque.crown", write_crown)
register_writer("baroque.dressing", write_dressing)
register_writer("baroque.volute", write_volute)
register_writer("baroque.dome", write_dome)
register_writer("baroque.cap", write_cap)

STYLE = load_style(Path(__file__).with_name("baroque.toml"))


def baroque_grammar() -> Grammar:
    return STYLE.grammar()


def derive_baroque(site: BaroqueSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_baroque(site: BaroqueSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
