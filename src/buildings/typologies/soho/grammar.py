"""SoHo as a split grammar: lofts and rowhouses on the 25-foot lot.

The style is its rule file, ``soho.toml`` beside this module, which chooses
the type from date and programme -- Federal rowhouse, cast-iron loft, brick
store-and-loft -- and holds each type's proportions as a table. This module
holds only the entry points.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from buildings.cga import Grammar
from buildings.ir.nodes import BuildingNode
from buildings.trace import TraceLog
from buildings.cga import Shape
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer
from buildings.typologies.soho.recipes import SohoSite

__all__ = ["STYLE", "soho_grammar", "derive_soho", "generate_soho"]

def write_light(light: Shape, below, d) -> list:
    """The kit's light, glazed as the rules say: double-hung sashes in a dark
    frame, and a moulded archivolt round a round head."""
    from dataclasses import replace

    out = kit.write_light(light, below, d)
    extra = {k: light.attr(k) for k in ("glazing", "sash_cols", "sash_rows", "frame_paint", "frame_w", "bar_w", "archivolt")
             if light.attr(k, None) is not None}
    if not extra or out[0].kind != "opening":
        return out
    return [replace(out[0], props={**out[0].props, **extra}), *out[1:]]


register_writer("soho.light", write_light)

STYLE = load_style(Path(__file__).with_name("soho.toml"))


def soho_grammar() -> Grammar:
    return STYLE.grammar()


def derive_soho(site: SohoSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_soho(site: SohoSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
