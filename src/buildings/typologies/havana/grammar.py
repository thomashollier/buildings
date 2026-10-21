"""Old Havana (La Habana Vieja) as a split grammar.

Colonial, neoclassical and eclectic street fronts, the manner by date and
the dress by the builder; the mediopuntos, rejas and balusters are grown.

The style is its rule file, ``havana.toml`` beside this module; this module
holds only the situation it takes, the balcony writer, and the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BalconyNode, BuildingNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class HavanaSite:
    width: float  # metres of street front
    year: int
    klass: BuildingClass
    seed: int = 0
    plaza: bool = False  # the front faces a plaza (where portales stand)


def write_balcony(shape: Shape, below, d) -> list:
    """A balcony's slab on its brackets, and the grown railing on it."""
    s = shape.scope
    return [
        BalconyNode(id=f"{shape.id}/platform", kind="balcony", trace=tuple(shape.trace),
                    props={**kit.xywh(s), "continuous": s.w > 2.5, "projection": 0.8,
                           "bracket_count": max(2, round(s.w / 1.2) + 1)}),
        *below,
    ]


register_writer("havana.balcony", write_balcony)

STYLE = load_style(Path(__file__).with_name("havana.toml"))


def havana_grammar() -> Grammar:
    return STYLE.grammar()


def derive_havana(site: HavanaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_havana(site: HavanaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def havana_manner(year: int, seed: int = 0) -> str:
    """The manner the rule file draws for a front of this date and builder."""
    lot, _ = derive_havana(HavanaSite(12.0, year, BuildingClass.ORDINARY, seed))
    return lot.attrs["manner"]
