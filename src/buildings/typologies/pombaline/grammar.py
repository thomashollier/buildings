"""The Lisbon Pombaline building as a split grammar.

After the 1755 earthquake the Baixa was rebuilt to standard elevations
(Eugenio dos Santos, Carlos Mardel, under the Marquis of Pombal): the street's
rank set the floors and the richness, and every window above the shops is the
same width on the same axis. A stone ground floor of arched or square shop
doors, balcony doors on the first floor, windows of one width above, a
mansard with trapeira dormers -- stucco at first, azulejo tiles later.

The style is its rule file, ``pombaline.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, GableNode, IronworkNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.kit import xywh
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class PombalineSite:
    width: float
    year: int
    klass: BuildingClass
    street: str = "nobre"  # "nobre" (rua nobre) | "secondary" | "alley" (travessa)
    seed: int = 0


def write_roof(roof: Shape, below, d) -> list:
    """The mansard seen from the street: its tiled face between the party
    walls, and the fold where the steep lower slope meets the upper one."""
    s = roof.scope
    fold = s.y + roof.attrs["fold"]
    face = ((s.x, s.y), (s.x, s.y + s.h), (s.x + s.w, s.y + s.h), (s.x + s.w, s.y))
    return [
        GableNode(id=roof.id, kind="gable", trace=tuple(roof.trace),
                  props={**xywh(s), "form": "mansard", "points": face, "hoist_beam": None,
                         "wall_material": roof.attrs["roof_paint"]}),
        GableNode(id=f"{roof.id}/fold", kind="gable", trace=tuple(roof.trace),
                  props={"x": s.x, "y": fold, "w": s.w, "h": 0.0, "form": "mansard_fold",
                         "points": ((s.x, fold), (s.x + s.w, fold)), "hoist_beam": None,
                         "wall_material": roof.attrs["roof_paint"]}),
        *below,
    ]


def write_rail(rail: Shape, below, d) -> list:
    """An iron guard set in the reveal of a balcony door with no balcony."""
    return [IronworkNode(id=rail.id, kind="ironwork", trace=tuple(rail.trace),
                         props={**xywh(rail.scope), "guards": "garde_corps", "max_gap": 0.11, "ornament_count": 2})]


register_writer("pombaline.roof", write_roof)
register_writer("pombaline.rail", write_rail)

STYLE = load_style(Path(__file__).with_name("pombaline.toml"))


def pombaline_grammar() -> Grammar:
    return STYLE.grammar()


def derive_pombaline(site: PombalineSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_pombaline(site: PombalineSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
