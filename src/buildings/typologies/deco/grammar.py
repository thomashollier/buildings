"""The New York Art Deco setback tower as a split grammar.

The massing is the 1916 Zoning Resolution, written as rules in ``deco.toml``:
the street wall rises to a multiple of the street's width, tiers step back on
the sky-exposure plane until the floor plate is a quarter of the lot, and the
tower rises to a spire.

The style is its rule file, ``deco.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import load_style, register_writer

@dataclass(frozen=True)
class TowerSite:
    width: float  # frontage, metres
    street_width: float
    year: int
    klass: BuildingClass
    seed: int = 0

def write_spire(crown: Shape, below, d) -> list:
    """The spire stands on the last tier's mass, as wide as a third of it."""
    top_tier = [t for t in crown.siblings if t.label == "Tier"][-1]
    mass = top_tier.children[0].scope
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

register_writer("deco.spire", write_spire)

STYLE = load_style(Path(__file__).with_name("deco.toml"))


def deco_grammar() -> Grammar:
    return STYLE.grammar()


def derive_deco(site: TowerSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_deco(site: TowerSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def tiers_for(site: TowerSite) -> list[tuple[str, int, float]]:
    """The massing the law leaves, ``(role, floors, width)`` bottom-up, read
    off the derived tiers -- the rule file is the only statement of it."""
    lot, _ = derive_deco(site)
    return [(t.attrs["tier_role"], t.attrs["floors"], t.attrs["mass_w"]) for t in lot.children if t.label == "Tier"]
