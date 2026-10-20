"""The Amsterdam canal house as a split grammar.

A narrow brick front on a stone plinth, up a stoop to a tall bel-etage,
rising into a gable of narrowing tiers whose outline -- step, raised neck,
neck, bell, or a dormer over a straight cornice -- the date makes likely and
the builder (the seed) chooses.

The style is its rule file, ``amsterdam.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer (the
gable's outline and its stone trim, and the stoop), and the entry points.
Nothing here decides; it draws around the shapes the rules placed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode, Node
from buildings.site import BuildingClass
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common.rulefile import load_style, register_writer

@dataclass(frozen=True)
class CanalSite:
    width: float  # metres of canal frontage
    year: int
    klass: BuildingClass
    seed: int = 0

STEP_RISE = 1.2  # one step of a stepped gable: about two to a storey (Herengracht 203)
CAP_H = 0.14  # the stone cap on a step, the coping band on a bell
PEDIMENT_OVERHANG = 0.15
RAIL_H = 0.9  # an iron stoop railing over the treads and the landing
LANDING_T = 0.22  # the landing's stone slab

Pts = list[tuple[float, float]]


def _bezier(p0, p1, p2, p3, steps=12) -> Pts:
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _mirror(left: Pts, cx: float) -> Pts:
    """The whole outline from its left half (eaves to apex), the apex once."""
    return left + [(2 * cx - x, y) for x, y in reversed(left[:-1])]


def _flip(poly: Pts, cx: float) -> Pts:
    return [(2 * cx - x, y) for x, y in reversed(poly)]


def _disc(cx: float, cy: float, r: float, n: int = 12) -> Pts:
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _inset(line: Pts, d: float) -> Pts:
    """A polyline moved ``d`` to its right: inward, for a left half climbing to the apex."""
    out = []
    for i, (x, y) in enumerate(line):
        a = line[max(0, i - 1)]
        b = line[min(len(line) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        out.append((x + d * dy / n, y - d * dx / n))
    return out


def _parts(gable: Shape):
    storeys = [c.children[0].scope for c in gable.children if c.label == "GableTier"]
    crown = next((c.scope for c in gable.children if c.label == "Crown"), None)
    return storeys, crown


def _step(gable: Shape):
    """Few, large steps beside each tier, a top block over the last, and a
    stone cap on every tread."""
    g = gable.scope
    cx = g.x + g.w / 2.0
    storeys, crown = _parts(gable)
    pts: Pts = [(g.x, g.y)]
    treads: list[tuple[float, float, float]] = []
    for st in storeys:
        x0, y0 = pts[-1][0], st.y
        n = max(1, round(st.h / STEP_RISE))
        for k in range(1, n + 1):
            y = y0 + st.h * k / n
            xa, xb = x0 + (st.x - x0) * (k - 1) / n, x0 + (st.x - x0) * k / n
            pts += [(xa, y), (xb, y)]
            treads.append((xa, xb, y))
    top_x = cx - g.w * float(gable.attrs["cap"]) / 2.0
    base = storeys[-1].y + storeys[-1].h
    apex = base + crown.h
    # The top block steps in from the last tier, then rises.
    treads[-1] = (treads[-1][0], top_x, base)
    pts += [(top_x, base), (top_x, apex), (cx, apex)]
    trim = []
    for i, (xa, xb, y) in enumerate(treads):
        trim.append((f"cap{i}", [(xa - 0.06, y), (xb, y), (xb, y + CAP_H), (xa - 0.06, y + CAP_H)]))
    # The top block's own cap, the full width of the block.
    trim.append(("cap_top", [(top_x - 0.08, apex), (2 * cx - top_x + 0.08, apex), (2 * cx - top_x + 0.08, apex + CAP_H), (top_x - 0.08, apex + CAP_H)]))
    beam = (cx, base + 0.05)
    return pts, beam, trim


def _neck(gable: Shape):
    """For each tier, a ledge at its foot and a convex claw piece of stone
    filling the corner against the tier above; a pediment over the neck."""
    g = gable.scope
    cx = g.x + g.w / 2.0
    storeys, crown = _parts(gable)
    pts: Pts = [(g.x, g.y)]
    trim = []
    bx, by = g.x, g.y
    for i, st in enumerate(storeys):
        ledge = bx + (st.x - bx) * 0.1
        a, ch = st.x - ledge, min(1.5, 0.55 * st.h)
        curve = [(st.x - a * math.cos(t), by + ch * math.sin(t)) for t in (math.pi / 2 * k / 12 for k in range(13))]
        pts += curve + [(st.x, st.y + st.h)]
        trim.append((f"claw{i}", [(ledge, by), *curve[1:], (st.x, by)]))
        # Carved in it: an inner leaf, and a volute against the tier above.
        inner = [(st.x - 0.62 * a * math.cos(t), by + 0.62 * ch * math.sin(t)) for t in (math.pi / 2 * k / 10 for k in range(11))]
        trim.append((f"leaf{i}", [(st.x - 0.62 * a, by), *inner[1:], (st.x, by)]))
        rv = min(0.2, ch * 0.14)
        trim.append((f"volute{i}", _disc(st.x - rv * 1.1, by + ch - rv * 0.9, rv)))
        # The scroll's curl at its foot.
        r = min(0.2, a * 0.12)
        trim.append((f"curl{i}", _disc(ledge + r * 1.1, by + r * 1.1, r)))
        bx, by = st.x, st.y + st.h
    top = storeys[-1].y + storeys[-1].h
    nx = storeys[-1].x - PEDIMENT_OVERHANG
    apex = top + crown.h
    pts += [(nx, top), (nx, top + 0.2), (cx, apex)]
    pediment = [(nx, top), (2 * cx - nx, top), (2 * cx - nx, top + 0.2), (cx, apex), (nx, top + 0.2)]
    trim.append(("pediment", pediment))
    beam = (cx, top - 0.5)
    return pts, beam, trim


def _bell(gable: Shape):
    """One continuous outline: a curl at the foot, concave, then convex,
    closing to a segmental cap; the whole edged with a stone band."""
    g = gable.scope
    cx = g.x + g.w / 2.0
    storeys, crown = _parts(gable)
    st = storeys[0]
    foot = g.w * float(gable.attrs["foot"]) / 2.0
    cap = g.w * float(gable.attrs["cap"]) / 2.0
    cap_h = min(0.6, crown.h * 0.5)
    body = g.h - cap_h
    y0 = g.y

    def side_of(waist: float) -> Pts:
        p0 = (cx - foot, y0)
        m = (cx - waist, y0 + body * 0.38)
        lower = _bezier(p0, (cx - foot + (foot - waist) * 0.55, y0 + body * 0.04), (cx - waist, y0 + body * 0.14), m)
        upper = _bezier(m, (cx - waist, y0 + body * 0.80), (cx - cap - (waist - cap) * 0.55, y0 + body), (cx - cap, y0 + body), 16)
        return [p0, *lower, *upper]

    # The waist stands clear of the attic storey it holds, band and all: the
    # outline is drawn around the storey, never through it.
    waist = (foot + cap) / 2.0
    clear = st.w / 2.0 + 0.3

    def half_at(pts: Pts, y: float) -> float:
        """The outline's half-width where it last crosses height ``y``."""
        out = foot
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if min(ya, yb) <= y <= max(ya, yb) and ya != yb:
                out = cx - (xa + (xb - xa) * (y - ya) / (yb - ya))
        return out

    while half_at(side_of(waist), st.y + st.h) < clear and waist < foot:
        waist += 0.05
    side = side_of(waist)
    arc = [(cx - cap * math.cos(t), y0 + body + cap_h * math.sin(t)) for t in (math.pi / 2 * k / 8 for k in range(1, 9))]
    pts: Pts = [(g.x, g.y), *side, *arc]
    edge = side + arc
    band = edge + list(reversed(_inset(edge, 0.22)))
    trim = [("band_l", band), ("band_r", _flip(band, cx))]
    r = 0.22
    trim.append(("curl", _disc(cx - foot + r * 0.6, y0 + r * 1.1, r)))
    beam = (cx, st.y + st.h - 0.05)
    return pts, beam, trim


def _lijst(gable: Shape):
    """Over a straight cornice: a dormer under a small pediment, or a raised
    crest (verhoogde lijst) curling up from the cornice; each holds the hatch."""
    g = gable.scope
    cx = g.x + g.w / 2.0
    storeys, crown = _parts(gable)
    st = storeys[0]
    top = st.y + st.h
    apex = top + crown.h
    if gable.attrs["top"] == "crest":
        foot = st.x - 0.9
        scroll = _bezier((foot, g.y), (st.x - 0.15, g.y + 0.05), (st.x, g.y + st.h * 0.3), (st.x, g.y + st.h * 0.8))
        half = cx - st.x
        arc = [(cx - half * (1 - k / 8), top + crown.h * (1 - (1 - k / 8) ** 2)) for k in range(1, 9)]
        left = [(foot, g.y), *scroll, (st.x, top), *arc]
        trim = [("curl", _disc(foot + 0.25, g.y + 0.3, 0.2))]
    else:
        ox = st.x - 0.12
        left = [(ox, g.y), (ox, top), (ox - 0.08, top), (ox - 0.08, top + 0.12), (cx, apex)]
        trim = []
    beam = (cx, top - 0.45)
    return left, beam, trim


_OUTLINES = {"step": _step, "raised_neck": _neck, "neck": _neck, "bell": _bell, "straight": _lijst}


def write_gable(gable: Shape, below, d) -> list[Node]:
    form = gable.attrs["form"]
    left, beam, trim = _OUTLINES[form](gable)
    cx = gable.scope.x + gable.scope.w / 2.0
    trace = tuple(gable.trace) + (TraceEntry(rule="amsterdam.gable_form", phase="period", detail=f"form = {form!r}"),)
    s = gable.scope

    def node(suffix: str, points: Pts, material: str, hoist) -> GableNode:
        return GableNode(
            id=gable.id if not suffix else f"{gable.id}/{suffix}",
            kind="gable",
            trace=trace,
            props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": form, "points": tuple(points), "hoist_beam": hoist, "wall_material": material},
        )

    wall, stone = gable.attrs["wall"], gable.attrs["trim"]
    out = [node("", _mirror(left, cx), stone if form == "straight" else wall, beam)]
    for suffix, poly in trim:
        out.append(node(suffix, poly, stone, None))
        # A piece of trim off the axis has its pair across it.
        if min(x for x, _ in poly) < cx - 1e-6 and max(x for x, _ in poly) < cx + 1e-6 and not suffix.startswith("band"):
            out.append(node(suffix + "_r", _flip(poly, cx), stone, None))
    # The hood over the hoisting beam's end.
    bx, by = beam
    out.append(node("hood", [(bx - 0.35, by + 0.58), (bx + 0.35, by + 0.58), (bx, by + 0.9)], "timber_dark", None))
    return [*out, *below]


def write_stoop(stoop: Shape, below, d) -> list[Node]:
    """The stoop: a stone landing in front of the door at the bel-etage floor,
    a flight of treads parallel to the front coming down to the street (two
    for a door in the middle), and an iron railing along both. The souterrain
    door under the landing is a window bay's business, not this drawing's."""
    s = stoop.scope
    a = stoop.attrs
    side, dx, dw, n = a["side"], float(a["door_x"]), float(a["door_w"]), int(a["treads"])
    top = s.y + s.h
    if side == "first":
        landing = (s.x, dx + dw)
        flights = [(dx + dw, s.x + s.w, +1)]
    elif side == "last":
        landing = (dx, s.x + s.w)
        flights = [(s.x, dx, -1)]
    else:
        landing = (dx, dx + dw)
        flights = [(s.x, dx, -1), (dx + dw, s.x + s.w, +1)]
    trace = tuple(stoop.trace)
    nodes: list[Node] = []

    def gable(suffix: str, pts: Pts) -> GableNode:
        return GableNode(id=f"{stoop.id}/{suffix}", kind="gable", trace=trace,
                         props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "stoop", "points": tuple(pts),
                                "hoist_beam": None, "wall_material": "stone"})

    def rail(suffix: str, x0: float, x1: float, y: float) -> IronworkNode:
        return IronworkNode(id=f"{stoop.id}/{suffix}", kind="ironwork", trace=trace,
                            props={"x": min(x0, x1), "y": y, "w": abs(x1 - x0), "h": RAIL_H, "guards": "balcon_filant",
                                   "max_gap": 0.12, "ornament_count": 1})

    lx0, lx1 = landing
    nodes.append(gable("landing", [(lx0, top - LANDING_T), (lx1, top - LANDING_T), (lx1, top), (lx0, top)]))
    nodes.append(rail("landing_rail", lx0, lx1, top))
    for f, (fx0, fx1, way) in enumerate(flights):
        # From the landing's edge down to the street: n treads, n + 1 rises.
        start = fx0 if way > 0 else fx1
        run = (fx1 - fx0) / n
        rise = s.h / (n + 1)
        pts: Pts = [(start, s.y)]
        for k in range(n):
            y = top - rise * (k + 1)
            xa, xb = start + way * run * k, start + way * run * (k + 1)
            pts += [(xa, y), (xb, y)]
            nodes.append(rail(f"flight{f}_rail{k}", xa, xb, y))
        pts.append((start + way * run * n, s.y))
        nodes.append(gable(f"flight{f}", pts))
    return nodes


def write_anchor(anchor: Shape, below, d) -> list[Node]:
    """A wrought-iron wall anchor's visible bar."""
    s = anchor.scope
    return [IronworkNode(id=anchor.id, kind="ironwork", trace=tuple(anchor.trace),
                         props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "guards": "balcon_filant", "max_gap": 0.5, "ornament_count": 1})]


register_writer("amsterdam.gable", write_gable)
register_writer("amsterdam.anchor", write_anchor)
register_writer("amsterdam.stoop", write_stoop)

STYLE = load_style(Path(__file__).with_name("amsterdam.toml"))


def amsterdam_grammar() -> Grammar:
    return STYLE.grammar()


def derive_amsterdam(site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_amsterdam(site: CanalSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def gable_form(year: int, seed: int = 0, width: float = 6.6, klass: BuildingClass = BuildingClass.ORDINARY) -> str:
    """The gable form the rule file gives a house of this date, width, class and builder."""
    lot, _ = derive_amsterdam(CanalSite(width, year, klass, seed))
    return lot.attrs["form"]
