"""The Venetian Gothic palazzo as a split grammar.

Every storey cut wing | centre | wing; the nobile centre a polifora of ogee
lights on colonnettes; the water gate below.

The style is its rule file, ``venice.toml`` beside this module; this module
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
class PalazzoSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0



STYLE = load_style(Path(__file__).with_name("venice.toml"))


def venice_grammar() -> Grammar:
    return STYLE.grammar()


def derive_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_venice(site: PalazzoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
