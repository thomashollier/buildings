"""The Kyoto machiya as a split grammar.

A low loft over a timber ground floor, tiled pent roofs along the front, and
every light screened by a Lattice shape: koshi below, mushiko above.

The style is its rule file, ``kyoto.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BuildingNode, IronworkNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common.kit import trace_of, xywh
from buildings.typologies.common.rulefile import load_style, register_writer


@dataclass(frozen=True)
class MachiyaSite:
    width: float
    year: int
    klass: BuildingClass
    seed: int = 0


def write_lattice(shape: Shape, below, d) -> list:
    return [
        IronworkNode(
            id=f"{shape.parent.parent.parent.id}/ironwork",
            kind="ironwork",
            trace=trace_of(shape, "screen_gap"),
            props={**xywh(shape.scope), "guards": "opening", "ironwork_pattern": "timber_lattice",
                   "max_gap": shape.attr("screen_gap"), "ornament_count": 2},
        )
    ]

register_writer("kyoto.lattice", write_lattice)

STYLE = load_style(Path(__file__).with_name("kyoto.toml"))


def kyoto_grammar() -> Grammar:
    return STYLE.grammar()


def derive_kyoto(site: MachiyaSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_kyoto(site: MachiyaSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
