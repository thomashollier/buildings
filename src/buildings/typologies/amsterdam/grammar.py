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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, CorniceNode, GableNode, IronworkNode, KeystoneNode, Node
from buildings.site import BuildingClass
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.common import kit
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


def _volute_r(a: float, ch: float) -> float:
    return min(0.34, 0.3 * ch, 0.26 * a)


def _scroll(ledge: float, y0: float, x1: float, ch: float) -> Pts:
    """A claw piece's outline, from its foot on the ledge to the tier wall at
    ``ch`` up: round a volute at the outer foot, then a hollow (cavetto) sweep
    rising into the wall -- a carved scroll, not a quarter circle."""
    rv = _volute_r(x1 - ledge, ch)
    cx, cy = ledge + rv, y0 + rv
    curl = [(cx + rv * math.cos(t), cy + rv * math.sin(t)) for t in (math.pi * (1.5 - k / 10) for k in range(11))]
    p0 = curl[-1]
    p1 = (x1, y0 + ch)
    sweep = _bezier(p0, (p0[0] + (p1[0] - p0[0]) * 0.55, p0[1] + 0.02), (p1[0] - 0.02, p0[1] + (p1[1] - p0[1]) * 0.4), p1, 14)
    return [(cx, y0), *curl, *sweep]


def _spiral_band(cx: float, cy: float, r: float, band: float) -> Pts:
    """A spiral of one and a half turns as a band ``band`` wide: the volute
    carved on a scroll's foot."""
    turns = [k / 18 for k in range(28)]
    outer = [(cx + (r - r * 0.55 * t) * math.cos(math.pi * (0.5 - 2 * t)), cy + (r - r * 0.55 * t) * math.sin(math.pi * (0.5 - 2 * t))) for t in turns]
    inner = [(cx + (r - band - r * 0.55 * t) * math.cos(math.pi * (0.5 - 2 * t)), cy + (r - band - r * 0.55 * t) * math.sin(math.pi * (0.5 - 2 * t))) for t in turns]
    return outer + list(reversed(inner))


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
        curve = _scroll(ledge, by, st.x, ch)
        pts += curve + [(st.x, st.y + st.h)]
        trim.append((f"claw{i}", [*curve, (st.x, by)]))
        # Carved in it: the volute's eye and its spiral at the foot, an
        # acanthus leaf rising along the scroll's back, a small curl where the
        # scroll meets the tier above.
        rv = _volute_r(a, ch)
        cx_v, cy_v = ledge + rv, by + rv
        trim.append((f"volute{i}", _spiral_band(cx_v, cy_v, rv * 0.78, rv * 0.18)))
        trim.append((f"eye{i}", _disc(cx_v + rv * 0.08, cy_v - rv * 0.05, rv * 0.24)))
        leaf = _scroll(ledge + rv * 1.2, by + rv * 0.6, st.x - a * 0.12, ch * 0.62)
        trim.append((f"leaf{i}", [*leaf, (st.x - a * 0.12, by + rv * 0.6)]))
        rt = min(0.13, a * 0.08)
        trim.append((f"curl{i}", _disc(st.x - rt * 1.1, by + ch - rt * 0.2, rt)))
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
        kind = gable.attrs["top"]
        if kind == "dormer_arched":
            # A round-headed dormer under a moulded arch.
            half = cx - (ox - 0.08)
            arc = [(cx - half * math.cos(t), top + 0.12 + (crown.h - 0.12) * math.sin(t)) for t in (math.pi / 2 * k / 10 for k in range(1, 11))]
            left = [(ox, g.y), (ox, top), (ox - 0.08, top), (ox - 0.08, top + 0.12), *arc]
        elif kind == "dormer_flat":
            # A flat-topped dormer under its own little cornice.
            left = [(ox, g.y), (ox, top), (ox - 0.14, top), (ox - 0.14, top + 0.22), (cx, top + 0.22)]
        else:
            left = [(ox, g.y), (ox, top), (ox - 0.08, top), (ox - 0.08, top + 0.12), (cx, apex)]
        trim = []
        if kind in ("dormer_arched", "dormer_flat"):
            # Scrolled cheeks against the dormer's sides, on the cornice.
            cheek = _bezier((ox - 0.42, g.y), (ox - 0.1, g.y + 0.02), (ox, g.y + 0.2), (ox, g.y + 0.75), 10)
            trim.append(("cheek", [(ox - 0.42, g.y), *cheek, (ox, g.y)]))
            trim.append(("cheek_curl", _disc(ox - 0.3, g.y + 0.12, 0.1)))
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
    """A wrought-iron wall anchor's forged end, in the form the rules gave it."""
    s = anchor.scope
    return [IronworkNode(id=anchor.id, kind="ironwork", trace=tuple(anchor.trace),
                         props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "guards": "wall", "ironwork_pattern": "wall_anchor",
                                "anchor_form": anchor.attr("anchor_form", "bar")})]


#: What a window or door light states beyond its rectangle, as the rules set it.
_LIGHT_STATED = ("glazing", "frame_paint", "frame_w", "bar_w", "sash_cols", "sash_rows", "came_count",
                 "transom_at", "shutter_paint", "fanlight_h", "fanlight_bars", "fanlight_pattern")
_ARCH_STATED = ("relieving_arch_rise", "relieving_ring", "relieving_reach")


def write_light(light: Shape, below, d) -> list[Node]:
    """The kit's opening, with what the rules said of its glazing, its door's
    fanlight, and the relieving arch over its head: the arch's bricks one
    ``voussoir`` each along its ring."""
    opening, *rest = kit.write_light(light, below, d)
    props = dict(opening.props)
    for key in _LIGHT_STATED:
        value = light.attr(key, None)
        if value is not None and value != "":
            props[key] = value
    if light.attr("relieving_arch", False) and light.attr("opening_type") == "window":
        for key in _ARCH_STATED:
            props[key] = light.attr(key)
        span = light.scope.w + 2.0 * float(light.attr("relieving_reach"))
        props["voussoirs"] = max(5, round(span * 1.15 / float(STYLE.params["voussoir"])))
    return [replace(opening, props=props), *rest]


def write_keystone(shape: Shape, below, d) -> list[Node]:
    """The keystone at the crown of the relieving arch over its window."""
    s = shape.scope
    rise = float(shape.attr("relieving_arch_rise", 0.0)) if shape.attr("relieving_arch", False) else 0.0
    return [KeystoneNode(id=kit._element_id(shape, "keystone"), kind="keystone", trace=kit.trace_of(shape, "keystone_present"),
                         props={"x": s.x, "y": s.y + rise - 0.04, "w": s.w, "h": 0.0, "keystone_kind": "plain"})]


def write_cornice(shape: Shape, below, d) -> list[Node]:
    """The lijst: its profile and its count of consoles or dentils as the
    rules set them, as deep as the builder made it."""
    s = shape.scope
    return [CorniceNode(id=shape.id, kind="cornice", trace=tuple(shape.trace),
                        props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "projection": s.h,
                               "cornice_ornament": shape.attrs["cornice_ornament"],
                               "ornament_count": int(shape.attrs["ornament_count"])})]


register_writer("amsterdam.gable", write_gable)
register_writer("amsterdam.anchor", write_anchor)
register_writer("amsterdam.stoop", write_stoop)
register_writer("amsterdam.light", write_light)
register_writer("amsterdam.keystone", write_keystone)
register_writer("amsterdam.cornice", write_cornice)

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
