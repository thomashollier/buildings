"""The Paris immeuble as a rule file, beside the measured generator.

``haussmann.toml`` writes the Haussmann building the way every other style in
this repository is written: the regulations as step tables, the class as an
ambition, storeys and bays fitted, the vocabulary laid on by rules. It is not
the measured generator (``generate.py``) and does not claim its numbers; it
is the same *kind* of description as Georgian or Venice, so the styles can be
read, compared and edited side by side.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from buildings.cga import Grammar
from buildings.ir.nodes import BuildingNode
from buildings.site import SiteContext
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import load_style

__all__ = ["STYLE", "derive_haussmann", "generate_haussmann"]

STYLE = load_style(Path(__file__).with_name("haussmann.toml"))


def derive_haussmann(site: SiteContext, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_haussmann(
    site: SiteContext, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
