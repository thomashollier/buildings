"""The Georgian London terrace house as a split grammar.

Every window one sash wide, its height set by its floor's ratio: 1.75 on the
ground floor, 2.1 on the piano nobile, 1.6 above, square at the top.

The style is its rule file, ``georgian.toml`` beside this module; this module
holds only the situation it takes and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar
from buildings.ir.nodes import BuildingNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import load_style


@dataclass(frozen=True)
class TerraceSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0



STYLE = load_style(Path(__file__).with_name("georgian.toml"))


def georgian_grammar() -> Grammar:
    return STYLE.grammar()


def derive_georgian(site: TerraceSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_georgian(site: TerraceSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
