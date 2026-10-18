"""The Normandy half-timbered house as a split grammar.

The frame is a grammar laid over the openings: posts at the setting's
spacing, never across a light, braces in the end panels, a Saint Andrew's
cross under every upstairs window. A jettied town house under a street gable,
or a close-set country house under thatch.

The style is its rule file, ``normandy.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, BraceNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.rulefile import load_style, register_writer
from buildings.typologies.common.kit import xywh

@dataclass(frozen=True)
class NormandySite:
    setting: str  # "town" | "country"
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float | None = None

    @property
    def frontage(self) -> float:
        return self.width if self.width is not None else (6.2 if self.setting == "town" else 14.0)

def write_brace(shape: Shape, below, d) -> list:
    return [BraceNode(id=shape.id, kind="brace", trace=tuple(shape.trace), props={**xywh(shape.scope), "direction": shape.attrs["direction"]})]


def write_gable(gable: Shape, below, d) -> list:
    s = gable.scope
    pts = ((s.x - 0.3, s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + 0.3, s.y))
    return [
        GableNode(id=gable.id, kind="gable", trace=tuple(gable.trace),
                  props={**xywh(s), "form": "front_gable", "points": pts, "hoist_beam": None, "wall_material": "plaster_ochre"}),
        *below,
    ]

register_writer("normandy.brace", write_brace)
register_writer("normandy.gable", write_gable)

STYLE = load_style(Path(__file__).with_name("normandy.toml"))


def normandy_grammar() -> Grammar:
    return STYLE.grammar()


def derive_normandy(site: NormandySite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_normandy(site: NormandySite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
