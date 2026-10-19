"""The Miami Beach Art Deco hotel as a split grammar.

A three- or four-storey hotel on Ocean Drive: side | centre | side, the
centre raised in a fin carrying the name, eyebrows over every window, racing
stripes, portholes, glass block, and a rounded corner on a corner lot.

The style is its rule file, ``miami_deco.toml``, composed with the Art Deco
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
class MiamiSite:
    width: float  # metres of frontage on the street
    year: int
    klass: BuildingClass
    seed: int = 0
    corner: bool = False  # a corner lot: the corner is rounded


STYLE = load_family(VOCABULARY, Path(__file__).with_name("miami_deco.toml"))


def miami_deco_grammar() -> Grammar:
    return STYLE.grammar()


def derive_miami_deco(site: MiamiSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_miami_deco(site: MiamiSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
