"""The Art Deco family as a split grammar.

The skyscraper's massing is the 1916 Zoning Resolution, written as rules in
``deco.toml``: the street wall rises to a multiple of the street's width,
tiers step back on the sky-exposure plane until the floor plate is a quarter
of the lot, and the tower rises to a crown.

The other programmes -- commercial, office, institutional, civic, religious,
works -- are written in their own rule files on the shared vocabulary
(``vocabulary.toml``): each composes its front from blocks and gives each
block its floors, glazing, piers and crest by rules. ``family.py`` composes
the files into one style; the site's ``programme`` picks the productions.

This module holds only the situations the style takes, the drawings the
files name by writer, and the entry points.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, DormerNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import register_writer
from buildings.typologies.deco import ornament  # noqa: F401  (registers the family's writers)
from buildings.typologies.deco.family import VOCABULARY, load_family

HERE = Path(__file__).parent

#: What a deco building can be for. ``skyscraper`` is the setback tower.
PROGRAMMES = ("skyscraper", "commercial", "office", "institutional", "civic", "religious", "works")


@dataclass(frozen=True)
class TowerSite:
    width: float  # frontage, metres
    street_width: float
    year: int
    klass: BuildingClass
    seed: int = 0
    programme: str = "skyscraper"


@dataclass(frozen=True)
class DecoSite:
    """Any programme of the family. ``street_width`` matters to the
    skyscraper (its zoning) and to nothing else."""

    programme: str
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0
    street_width: float = 18.0


def _gable(shape: Shape, suffix: str, pts, paint: str, form: str = "spire") -> GableNode:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return GableNode(
        id=f"{shape.id}{suffix}",
        kind="gable",
        trace=tuple(shape.trace),
        props={"x": min(xs), "y": min(ys), "w": max(xs) - min(xs), "h": max(ys) - min(ys), "form": form,
               "points": tuple(pts), "hoist_beam": None, "wall_material": paint},
    )


def _top_mass(crown: Shape):
    top_tier = [t for t in crown.siblings if t.label == "Tier"][-1]
    return top_tier.children[0].scope


def write_spire(crown: Shape, below, d) -> list:
    """The spire stands on the last tier's mass, as wide as a third of it."""
    mass = _top_mass(crown)
    cx = mass.x + mass.w / 2.0
    half = mass.w * 0.18
    y0 = crown.scope.y
    pts = ((cx - half, y0), (cx - half * 0.5, y0 + 2.5), (cx, y0 + crown.scope.h), (cx + half * 0.5, y0 + 2.5), (cx + half, y0))
    return [
        GableNode(
            id=crown.id,
            kind="gable",
            trace=tuple(crown.trace),
            props={"x": cx - half, "y": y0, "w": 2 * half, "h": crown.scope.h, "form": "spire", "points": pts,
                   "hoist_beam": None, "wall_material": "stucco"},
        )
    ]


def _arch(cx, half, y0, spring, rise, steps=14):
    """A round arch on its jambs, from the ground line of the crown."""
    top = [(cx - half * math.cos(math.pi * i / steps), spring + rise * math.sin(math.pi * i / steps)) for i in range(steps + 1)]
    return [(cx - half, y0), *top, (cx + half, y0)]


#: The Chrysler crown, INFERRED from photographs: five tiers of arches, each
#: a sixth narrower and springing higher, the top one at about one tower
#: width; triangular windows round each arch; the needle above.
_CHRYSLER_TIERS = 5
_CHRYSLER_NARROW = 0.17
_CHRYSLER_SPRING = (0.10, 0.18)  # first spring, rise of the spring per tier (x tower width)


def write_chrysler(crown: Shape, below, d) -> list:
    mass = _top_mass(crown)
    tw, cx, y0 = mass.w, mass.x + mass.w / 2.0, crown.scope.y
    arches_h = crown.scope.h / 1.9
    nodes, tops = [], []
    for k in range(_CHRYSLER_TIERS):
        half = tw * (1.0 - _CHRYSLER_NARROW * k) / 2.0
        spring = y0 + arches_h * (_CHRYSLER_SPRING[0] + _CHRYSLER_SPRING[1] * k)
        rise = half * 0.9
        tops.append((half, spring, rise))
        # A dark reveal under each arch's edge, so the steel arches read as
        # separate rings and not one dome.
        rim = tw * 0.012
        nodes.append(_gable(crown, f"/reveal{k}", _arch(cx, half + rim, y0, spring, rise + rim), "shadow", "bell"))
        nodes.append(_gable(crown, f"/arch{k}", _arch(cx, half, y0, spring, rise), "cast_iron", "bell"))
    band = tw * 0.085
    for k, (half, spring, rise) in enumerate(tops):
        for j in range(7):
            a = math.pi * (j + 1) / 8.0
            ux, uy = math.cos(a), math.sin(a)
            tip = (cx - (half - band * 0.15) * ux, spring + (rise - band * 0.15) * uy)
            r_in_x, r_in_y = half - band * 0.85, rise - band * 0.85
            spread = 0.07
            b1 = (cx - r_in_x * math.cos(a - spread), spring + r_in_y * math.sin(a - spread))
            b2 = (cx - r_in_x * math.cos(a + spread), spring + r_in_y * math.sin(a + spread))
            nodes.append(_gable(crown, f"/window{k}_{j}", [b1, tip, b2], "shadow", "pavilion"))
    half, spring, rise = tops[-1]
    apex = spring + rise
    needle = [(cx - tw * 0.05, apex - 0.3), (cx - tw * 0.02, apex + (crown.scope.y + crown.scope.h - apex) * 0.3),
              (cx, crown.scope.y + crown.scope.h), (cx + tw * 0.02, apex + (crown.scope.y + crown.scope.h - apex) * 0.3), (cx + tw * 0.05, apex - 0.3)]
    nodes.append(_gable(crown, "/needle", needle, "cast_iron"))
    return nodes


def write_mast(crown: Shape, below, d) -> list:
    """The Empire State's mooring mast: a step, a fluted drum, a lantern under
    a dome, and the antenna (INFERRED shares of the last setback's width)."""
    mass = _top_mass(crown)
    m, cx, y0, H = mass.w, mass.x + mass.w / 2.0, crown.scope.y, crown.scope.h

    def box(x_half, ya, yb):
        return [(cx - x_half, ya), (cx - x_half, yb), (cx + x_half, yb), (cx + x_half, ya)]

    step = (y0, y0 + 0.1 * H)
    drum = (step[1], step[1] + 0.3 * H)
    lantern = (drum[1], drum[1] + 0.1 * H)
    nodes = [
        _gable(crown, "/step", box(m * 0.33, *step), "stone", "straight"),
        _gable(crown, "/drum", box(m * 0.21, *drum), "stone", "straight"),
    ]
    for k in range(-2, 3):
        fx = cx + k * m * 0.08
        nodes.append(_gable(crown, f"/fin{k + 2}", [(fx - m * 0.015, drum[0]), (fx - m * 0.015, drum[1] + 0.02 * H), (fx + m * 0.015, drum[1] + 0.02 * H), (fx + m * 0.015, drum[0])], "cast_iron", "pavilion"))
    nodes.append(_gable(crown, "/lantern", box(m * 0.13, *lantern), "render_white", "straight"))
    dome = [(cx - m * 0.13 * math.cos(math.pi * i / 10), lantern[1] + 0.06 * H * math.sin(math.pi * i / 10)) for i in range(11)]
    nodes.append(_gable(crown, "/dome", dome, "cast_iron", "bell"))
    nodes.append(_gable(crown, "/antenna", [(cx - m * 0.025, lantern[1] + 0.05 * H), (cx, y0 + H), (cx + m * 0.025, lantern[1] + 0.05 * H)], "cast_iron"))
    return nodes


def write_clock(crown: Shape, below, d) -> list:
    """The clock tower's gilt cap, and its clock face: the front one of the
    four, drawn in front of the tower's top floors."""
    mass = _top_mass(crown)
    cx, y0, H = mass.x + mass.w / 2.0, crown.scope.y, crown.scope.h
    pts = ornament.crest_points("stepped", mass.x + mass.w * 0.12, y0, mass.w * 0.76, H * 0.7, 3, 0.35, "left")
    nodes = [_gable(crown, "/cap", pts, "plaster_ochre", "step"),
             _gable(crown, "/finial", [(cx - 0.25, y0 + H * 0.7), (cx, y0 + H), (cx + 0.25, y0 + H * 0.7)], "plaster_ochre")]
    face = min(mass.w * 0.55, 5.0)
    nodes.append(DormerNode(id=f"{crown.id}/clock", kind="dormer", trace=tuple(crown.trace),
                            props={"x": cx - face / 2.0, "y": y0 - face - 0.8, "w": face, "h": face, "form": "oeil_de_boeuf"}))
    return nodes


#: The crown's drawing by the crown the architect chose.
_CROWN_WRITERS = {"spire": write_spire, "lantern": write_spire, "chrysler": write_chrysler, "mast": write_mast, "clock": write_clock}


def write_crown(crown: Shape, below, d) -> list:
    return _CROWN_WRITERS[crown.attr("crown")](crown, below, d)


register_writer("deco.spire", write_crown)

FILES = [VOCABULARY, *(HERE / f"{p}.toml" for p in ("commercial", "office", "institutional", "civic", "religious", "works")), HERE / "deco.toml"]
STYLE = load_family(*FILES)


def deco_grammar() -> Grammar:
    return STYLE.grammar()


def derive_deco(site: TowerSite | DecoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_deco(site: TowerSite | DecoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def tiers_for(site: TowerSite) -> list[tuple[str, int, float]]:
    """The massing the law leaves, ``(role, floors, width)`` bottom-up, read
    off the derived tiers -- the rule file is the only statement of it."""
    lot, _ = derive_deco(site)
    return [(t.attrs["tier_role"], t.attrs["floors"], t.attrs["mass_w"]) for t in lot.children if t.label == "Tier"]
