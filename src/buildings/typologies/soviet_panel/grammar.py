"""Soviet prefabricated panel housing as a split grammar.

The facade is a grid of identical factory panels, one room-panel per bay per
floor. The building is a run of sections, each a staircase with flats either
side; the date picks the series (the Khrushchyovka K-7 and 1-464 of five
storeys and no lift, the Brezhnev-era II-49 and P-44 of nine to seventeen
with a lift room on the roof). Balconies and loggias stack up the same bays,
the staircase's windows sit half a floor off the rooms', and every entrance
has its concrete canopy.

The style is its rule file, ``soviet_panel.toml`` beside this module; this
module holds only the situation it takes, the drawings the file names by
writer, and the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BalconyNode, BuildingNode, StoreyNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.kit import xywh
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class PanelSite:
    sections: int  # stairwells (podyezdy) along the block: its width
    year: int
    klass: BuildingClass
    seed: int = 0


def write_panel(panel: Shape, below, d) -> list:
    """A panel is a storey one bay wide: its own wall, its own joints. The
    parapet of a balcony or loggia on it stands in front of it, so it goes up
    to the building to be drawn after the panel."""
    fronts = [n for n in below if n.kind == "storey"]
    rest = [n for n in below if n.kind != "storey"]
    return [*kit.write_storey(panel, rest, d), *fronts]


def write_parapet(parapet: Shape, below, d) -> list:
    """The solid front of a balcony or a loggia: a panel of its own, and under
    a balcony the slab it stands on."""
    s = parapet.scope
    out = [StoreyNode(id=parapet.id, kind="storey", trace=tuple(parapet.trace),
                      props={**xywh(s), "role": "balcony_front", "wall_material": parapet.attrs["front_paint"],
                             "on_the_stone_facade": True})]
    if parapet.attrs["projects"]:
        out.insert(0, BalconyNode(id=f"{parapet.id}/slab", kind="balcony", trace=tuple(parapet.trace),
                                  props={**xywh(s), "continuous": False, "projection": 1.0, "bracket_count": 2}))
    return out


register_writer("soviet_panel.panel", write_panel)
register_writer("soviet_panel.parapet", write_parapet)

STYLE = load_style(Path(__file__).with_name("soviet_panel.toml"))


def soviet_panel_grammar() -> Grammar:
    return STYLE.grammar()


def derive_soviet_panel(site: PanelSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_soviet_panel(site: PanelSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)


def series_for(year: int) -> str:
    """The series the rule file builds in this year."""
    lot, _ = derive_soviet_panel(PanelSite(1, year, BuildingClass.ORDINARY))
    return lot.attrs["series"]
