"""The Art Deco movie palace front as a split grammar.

The auditorium's front: a bank of doors under a projecting marquee, a tall
central panel (mosaic, flutes or glass) over it, a vertical blade sign, and
on a bigger lot shop bays either side in a commercial block.

The style is its rule file, ``movie_palace.toml``, composed with the Art Deco
family's shared vocabulary (``deco/vocabulary.toml``) by
``deco/family.py``; this module holds only the situation it takes and the
entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar
from buildings.ir.nodes import BuildingNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.deco import ornament  # noqa: F401  (registers the family's writers)
from buildings.typologies.deco.family import VOCABULARY, load_family


@dataclass(frozen=True)
class PalaceSite:
    width: float  # metres of frontage on the street
    year: int
    klass: BuildingClass
    seed: int = 0  # the architect: which panel, which sign


STYLE = load_family(VOCABULARY, Path(__file__).with_name("movie_palace.toml"))


def movie_palace_grammar() -> Grammar:
    return STYLE.grammar()


def derive_movie_palace(site: PalaceSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_movie_palace(site: PalaceSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
