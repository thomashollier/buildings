"""The Chicago School office block as a split grammar.

Base, a uniform shaft, capital; piers on the facade running the whole shaft;
every shaft bay a Chicago window, sash | fixed | sash at 1:2:1.

The style is its rule file, ``chicago.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
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
class OfficeSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0



STYLE = load_style(Path(__file__).with_name("chicago.toml"))


def chicago_grammar() -> Grammar:
    return STYLE.grammar()


def derive_chicago(site: OfficeSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_chicago(site: OfficeSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
