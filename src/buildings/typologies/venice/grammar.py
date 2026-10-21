"""The Venetian Gothic palazzo as a split grammar.

Every storey cut wing | centre | wing; the nobile centre a polifora of ogee
lights on colonnettes in a dentilled stone frame; the water gate below.
Before 1300 the older Veneto-Byzantine casa-fondaco: a portico and an arcade
grouped centre and wings, between two corner towers on the grand fondaco,
crenellated there.

The style is its rule file, ``venice.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points. The writers place what the rules decided -- where an arch
springs from its capital, how many corbels carry a balcony -- so that the
renderer only draws. The polifora's tracery is not drawn here: the rules
grow it (``venice.tracery``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import (
    BalconyNode,
    BuildingNode,
    ColumnNode,
    GableNode,
    IronworkNode,
    KeystoneNode,
    OpeningNode,
    SocleNode,
    SpecialNode,
    StringCourseNode,
    SurroundNode,
)
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class PalazzoSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


# --- arches -----------------------------------------------------------------------

# How far each head rises (``head_rise_share``, ``head_max_share``) is the
# rule file's: the tracery the rules grow over the arches has to clear them.


def _light_span(light: Shape) -> tuple[float, float]:
    """The x and width of the glass a Light shows: its own scope, or a narrower
    pane centred in it where the rules state ``glass_width``."""
    s = light.scope
    gw = light.attr("glass_width", None)
    if gw is not None and gw < s.w:
        return s.x + (s.w - gw) / 2.0, float(gw)
    return s.x, s.w


def head_rise(light: Shape) -> float:
    """How far a light's arched head rises above its springing."""
    share = STYLE.params["head_rise_share"].get(light.attr("head", "flat"))
    if share is None:
        return 0.0
    _x, w = _light_span(light)
    return min(w * share, light.scope.h * STYLE.params["head_max_share"])


#: A bottle-glass roundel (rui) as drawn.
RONDEL = 0.24


def finial_height(width: float) -> float:
    """The fleuron over an ogee's tip, by the span it crowns."""
    return min(0.32, 0.2 * width)


def write_light(light: Shape, below, d) -> list:
    """The opening, with the geometry of its head stated: the rise, the finial
    over an ogee, the stone band round an arch, a gate's grille."""
    kind, head = light.attr("opening_type"), light.attr("head")
    s = light.scope
    x, w = _light_span(light)
    props: dict[str, object] = {"x": x, "y": s.y, "w": w, "h": s.h, "opening_type": kind, "head": head}
    rise = head_rise(light)
    if rise > 0.0:
        props["head_rise"] = rise
    if head == "ogee" and light.attr("finial", False):
        props["head_finial"] = "fleuron"
        props["finial_h"] = finial_height(w)
    if light.attr("archivolt", None):
        props["archivolt"] = light.attr("archivolt")
        if light.attr("archivolt") == "extradosed":
            # The moulding runs down the stilt to the capital the arch springs from.
            props["archivolt_stilt"] = float(light.attr("stilt", 0.0))
    glazing = light.attr("glazing", None)
    if kind == "window" and glazing:
        props["glazing"] = glazing
        if glazing == "rondel":
            # Bottle-glass roundels, drawn a little larger than the real 12 cm
            # so that they read at the scale of a whole front.
            props["rondel_cols"] = max(2, round(w / RONDEL))
            props["rondel_rows"] = max(2, round((s.h - rise) / RONDEL))
    if kind == "water_gate":
        # An iron grille across the lunette, its bars about 0.3 m apart.
        props["grille_bars"] = max(3, round(w / 0.3))
    return [
        OpeningNode(id=kit._element_id(light, "opening"), kind="opening", trace=kit.trace_of(light, "opening_type", "head"), props=props),
        *below,
    ]


def write_colonnette(shape: Shape, below, d) -> list:
    """A colonnette between two lights. It stands on the arcade's floor and
    stops where the arches spring (less any stilt): the capital carries them.
    Its capital is wider than its shaft; in a Byzantine arcade a patera sits
    in the spandrel over it."""
    s = shape.scope
    siblings = shape.siblings
    i = siblings.index(shape)
    # Where the two arches either side differ (a graded arcade), both spring
    # from the capital at the bigger one's springing; the smaller is stilted.
    left = max(siblings[i - 1], siblings[i + 1], key=head_rise)
    rise = head_rise(left)
    stilt = float(shape.attr("stilt", 0.0))
    top = s.y + s.h - rise - stilt
    cap_w = max(s.w, float(shape.attr("capital_width", s.w)))
    cx = s.x + s.w / 2.0
    nodes: list = [
        ColumnNode(
            id=shape.id,
            kind="column",
            trace=tuple(shape.trace) + tuple(shape.parent.trace[:1]),
            props={"x": cx - cap_w / 2.0, "y": s.y, "w": cap_w, "h": max(0.2, top - s.y), "order": shape.attr("order"), "shaft_width": s.w},
        )
    ]
    if shape.attr("spandrel_patera", False) and rise > 0.0:
        # The spandrel narrows as the arches rise; at three quarters of the
        # rise the gap between them (a semicircle of radius R) is the
        # colonnette plus R - sqrt(R^2 - (0.72 R)^2) a side.
        _lx, lw = _light_span(left)
        r_arch = lw / 2.0
        up = 0.72 * rise
        gap = s.w + 2.0 * (r_arch - math.sqrt(max(0.0, r_arch * r_arch - up * up)))
        band = min(0.14, lw * 0.09)  # the arch's stone band, as drawn
        radius = min(0.26, 0.42 * (gap - 2.0 * band))
        nodes.append(
            KeystoneNode(
                id=f"{shape.id}/patera",
                kind="keystone",
                trace=tuple(shape.trace),
                props={"x": cx - radius, "y": top + stilt + up, "w": 2.0 * radius, "h": 0.0, "keystone_kind": "patera"},
            )
        )
    return nodes


def write_surround(shape: Shape, below, d) -> list:
    """A light's stone frame. A dentilled panel round an ogee runs up past the
    finial; its dentils are about 0.22 m apart."""
    s = shape.scope
    x, y, w, h = s.x, s.y, s.w, s.h
    if shape.parent is not None and shape.parent.label == "Light":
        light = shape.parent
        x, w = _light_span(light)
        if light.attr("head", "flat") == "ogee" and light.attr("finial", False):
            h += finial_height(w) + 0.06
    kind = shape.attr("surround_kind")
    return [
        SurroundNode(
            id=kit._element_id(shape, "surround") if shape.parent.label == "Light" else shape.id,
            kind="surround",
            trace=kit.trace_of(shape, "surround_kind"),
            props={"x": x, "y": y, "w": w, "h": h, "surround_kind": kind, "ornament_count": max(3, round((w + 0.3) / 0.22))},
        )
    ]


def write_balconette(shape: Shape, below, d) -> list:
    """A balcony: a stone balustrade of colonnettes about 0.2 m apart on a
    slab carried by corbels (two or three under a wing poggiolo, four to eight
    under a polifora), projecting about half a metre; or, put in later, an
    iron rail on a thin slab."""
    s = shape.scope
    if shape.attr("rail", "stone") == "plutei":
        return _plutei(shape)
    stone = shape.attr("rail", "stone") == "stone"
    corbels = 2 if s.w < 1.6 else (3 if s.w < 2.6 else max(4, min(8, round(s.w / 1.1) + 1)))
    platform = {**kit.xywh(s), "continuous": False, "projection": 0.5 if stone else 0.35, "bracket_count": corbels}
    rail = {**kit.xywh(s), "guards": "balcon_filant", "ornament_count": 2}
    if stone:
        platform.update({"bracket_drop": 0.34, "slab_depth": 0.14, "slab_kind": "stone"})
        rail.update({"max_gap": 0.2, "ironwork_pattern": "stone_balustrade"})
    else:
        rail.update({"max_gap": 0.11})
    return [
        BalconyNode(id=f"{shape.id}/platform", kind="balcony", trace=tuple(shape.trace), props=platform),
        IronworkNode(id=f"{shape.id}/rail", kind="ironwork", trace=tuple(shape.trace), props=rail),
    ]


def _plutei(shape: Shape) -> list:
    """A Veneto-Byzantine loggia's parapet: a solid marble slab (pluteus) under
    each arch, between posts standing under the colonnettes, on the loggia's
    floor -- no projecting balcony and no balusters."""
    s = shape.scope
    arcade = next((c for c in shape.siblings if c.label == "Arcade"), None)
    lights = [c for c in arcade.children if c.label == "Light"] if arcade is not None else []
    cols = [c for c in arcade.children if c.label != "Light"] if arcade is not None else []
    edges = [s.x] + [c.scope.x + c.scope.w / 2.0 for c in cols] + [s.x + s.w]
    post = min((c.scope.w for c in cols), default=0.2) * 0.8
    return [IronworkNode(id=f"{shape.id}/rail", kind="ironwork", trace=tuple(shape.trace),
                         props={**kit.xywh(s), "h": 0.9, "guards": "balcon_filant", "ironwork_pattern": "pluteus",
                                "panel_count": max(1, len(lights)), "panel_edges": tuple(edges), "post_w": post})]


def write_tracery(shape: Shape, below, d) -> list:
    """The tracery of a polifora is grown by the rules (``venice.tracery``):
    its stone comes up from the grown outlines below. This states only what
    shows through what the stone leaves open -- the dark of the portego
    behind the arcade, from the arches' springing to the frame's head -- and
    it goes first in the bay, behind the arches."""
    s = shape.scope
    band = OpeningNode(id=f"{shape.id}/band", kind="opening", trace=tuple(shape.trace),
                       props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "opening_type": "open_arch", "head": "flat"})
    return [band, *below]


def write_course(shape: Shape, below, d) -> list:
    """A string course: a stone band in the top of its storey, its dentils
    about 0.3 m apart along its lower edge."""
    (node,) = kit.write_entablature(shape, below, d)
    return [replace(node, props={**node.props, "y": shape.scope.y, "ornament_count": max(4, round(shape.scope.w / 0.3))})]


def write_frieze(shape: Shape, below, d) -> list:
    """The Byzantine band between the floors: paterae and formelle in turn,
    one every 1.3 m or so."""
    s = shape.scope
    return [
        StringCourseNode(
            id=shape.id,
            kind="string_course",
            trace=tuple(shape.trace),
            props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "course_kind": "paterae", "projection": s.h, "ornament_count": max(3, round(s.w / 1.3))},
        )
    ]


def write_base_course(shape: Shape, below, d) -> list:
    """The Istrian base course along the water, broken where a gate (and its
    frame) comes down to the water; blocks about 1.1 m long, two courses."""
    s = shape.scope
    storey = shape.parent
    gaps = sorted(
        (lt.scope.x - 0.25, lt.scope.x + lt.scope.w + 0.25)
        for lt in storey.walk()
        if lt.label == "Light" and lt.attr("opening_type", None) == "water_gate"
    )
    runs, x0 = [], s.x
    for a, b in gaps:
        if a > x0 + 1e-6:
            runs.append((x0, a))
        x0 = max(x0, b)
    if s.x + s.w > x0 + 1e-6:
        runs.append((x0, s.x + s.w))
    rows = int(shape.attr("rows", 2))
    nodes = [
        SocleNode(
            id=f"{shape.id}{k}",
            kind="socle",
            trace=tuple(shape.trace),
            props={"x": a, "y": s.y, "w": b - a, "h": s.h, "treatment": "istrian_course", "course_rows": rows,
                   "course_columns": max(1, round((b - a) / 1.1)), "tide_h": min(TIDE_BAND, s.h * 0.4)},
        )
        for k, (a, b) in enumerate(runs)
    ]
    # At each gate, Istrian steps go down from its threshold into the water.
    for k, (a, b) in enumerate(gaps):
        nodes.append(SocleNode(id=f"{shape.id}/steps{k}", kind="socle", trace=tuple(shape.trace),
                               props={"x": a + 0.1, "y": s.y - STEPS_DEPTH, "w": b - a - 0.2, "h": STEPS_DEPTH,
                                      "treatment": "water_steps", "course_rows": 3, "step_spread": 0.08, "dry_h": 0.18}))
    return nodes


#: The weed-dark foot of the stone, and how deep a gate's steps go under the water drawn.
TIDE_BAND = 0.22
STEPS_DEPTH = 0.6


def write_column(shape: Shape, below, d) -> list:
    """A corner of Istrian stone: a strip whose inner edge is cut in a saw
    tooth about 0.3 m long, or quoins of long and short blocks about 0.45 m
    high (the short ones three fifths as wide)."""
    (node,) = kit.write_column(shape, below, d)
    order, h = shape.attr("order"), shape.scope.h
    extra: dict[str, object] = {}
    if shape.attr("side", None):
        extra["side"] = shape.attr("side")
    if order == "dentil_strip":
        extra.update({"course_rows": max(2, round(h / 0.3)), "tooth_depth": 0.1})
    elif order == "quoins":
        extra.update({"course_rows": max(2, round(h / 0.45)), "short_w": shape.scope.w * 0.6})
    return [replace(node, props={**node.props, **extra})]


def write_cell(cell: Shape, below, d) -> list:
    """A bay as the kit writes it, except that a balcony is no part of the bay:
    its slab goes to the storey, drawn as wide as the balcony is rather than
    as the bay, and its rail stands in front of the colonnettes it guards, so
    it goes up to the building with the other railings."""
    # The tracery's stone stands in front of the storey: it goes up to the building.
    stone = [n for n in below if n.kind == "gable"]
    bay, *rest = kit.write_cell(cell, [n for n in below if n.kind != "gable"], d)
    out = tuple(n for n in bay.children if n.kind in ("ironwork", "balcony"))
    if out:
        bay = replace(bay, children=tuple(n for n in bay.children if n.kind not in ("ironwork", "balcony")))
    # What a polifora's tracery leaves open lies behind its arches: it goes first.
    web = tuple(n for n in bay.children if n.id.endswith("/tracery/band"))
    if web:
        bay = replace(bay, children=web + tuple(n for n in bay.children if n not in web))
    return [bay, *rest, *out, *stone]


def write_storey(storey: Shape, below, d) -> list:
    """A storey as the kit writes it, except that the tracery's stone, which
    stands in front of it, goes up to the building."""
    stone = [n for n in below if n.kind == "gable"]
    return [*kit.write_storey(storey, [n for n in below if n.kind != "gable"], d), *stone]


def write_roof(roof: Shape, below, d) -> list:
    """A low hipped roof of coppi seen from the canal: its front slope, the
    hips running back from the ends at the same pitch."""
    s = roof.scope
    inset = min(s.w * 0.4, s.h / math.tan(math.radians(float(roof.attr("pitch", 24.0)))))
    pts = ((s.x, s.y), (s.x + inset, s.y + s.h), (s.x + s.w - inset, s.y + s.h), (s.x + s.w, s.y))
    return [GableNode(id=roof.id, kind="gable", trace=tuple(roof.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "pavilion", "points": pts,
                             "hoist_beam": None, "wall_material": "tile_red"})]


def write_fumaiolo(shape: Shape, below, d) -> list:
    """A Venetian chimney: a stack rising from the roof to a funnel head
    (fumaiolo a imbuto)."""
    s = shape.scope
    return [
        SpecialNode(
            id=shape.id,
            kind="special",
            trace=tuple(shape.trace),
            props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "element": "fumaiolo", "head_h": 0.9, "head_w": s.w * 2.2},
        )
    ]


#: The Fondaco's merlons, at Ruskin's scale: about 1.8 m wide with a gap of
#: about 0.6 of that between them, on a low band; each stepped twice at its
#: shoulders and ending in a point (as restored in 1869).
MERLON_W = 1.8
MERLON_GAP = 0.6
MERLON_BAND = 0.3


def write_crenellation(merlons: Shape, below, d) -> list:
    """A row of stepped, pointed merlons standing on the cornice, as one outline."""
    s = merlons.scope
    n = max(2, round((s.w + MERLON_GAP * MERLON_W) / (MERLON_W * (1.0 + MERLON_GAP))))
    pitch = s.w / n
    body = s.h - MERLON_BAND
    step = MERLON_W * 0.14
    pts = [(s.x, s.y), (s.x, s.y + MERLON_BAND)]
    for k in range(n):
        x0 = s.x + k * pitch + (pitch - MERLON_W) / 2.0
        b = s.y + MERLON_BAND
        pts += [
            (x0, b), (x0, b + body * 0.45),
            (x0 + step, b + body * 0.45), (x0 + step, b + body * 0.62),
            (x0 + 2 * step, b + body * 0.62), (x0 + 2 * step, b + body * 0.74),
            (x0 + MERLON_W / 2.0, s.y + s.h),
            (x0 + MERLON_W - 2 * step, b + body * 0.74), (x0 + MERLON_W - 2 * step, b + body * 0.62),
            (x0 + MERLON_W - step, b + body * 0.62), (x0 + MERLON_W - step, b + body * 0.45),
            (x0 + MERLON_W, b + body * 0.45), (x0 + MERLON_W, b),
        ]
    pts += [(s.x + s.w, s.y + MERLON_BAND), (s.x + s.w, s.y)]
    return [GableNode(id=merlons.id, kind="gable", trace=tuple(merlons.trace),
                      props={"x": s.x, "y": s.y, "w": s.w, "h": s.h, "form": "step", "points": tuple(pts),
                             "hoist_beam": None, "wall_material": "stone"})]


register_writer("venice.crenellation", write_crenellation)
register_writer("venice.light", write_light)
register_writer("venice.colonnette", write_colonnette)
register_writer("venice.surround", write_surround)
register_writer("venice.balconette", write_balconette)
register_writer("venice.tracery", write_tracery)
register_writer("venice.course", write_course)
register_writer("venice.frieze", write_frieze)
register_writer("venice.base_course", write_base_course)
register_writer("venice.cell", write_cell)
register_writer("venice.fumaiolo", write_fumaiolo)
register_writer("venice.roof", write_roof)
register_writer("venice.column", write_column)
register_writer("venice.storey", write_storey)

STYLE = load_style(Path(__file__).with_name("venice.toml"))


def venice_grammar() -> Grammar:
    return STYLE.grammar()


def derive_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
