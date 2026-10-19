"""The English Tudor house as a split grammar.

A frame of oak laid over the openings, as in Normandy, but English: close
studding or square panels with lozenges, jettied storeys, steep gables with
dark bargeboards and chevroned infill, wide mullioned-and-transomed windows
glazed in diamond leaded panes, oriels, and tall clustered brick chimneys.
A cottage under thatch, a town house gabled to the street, a manor with
cross-gabled wings; from the 1840s the Tudor Revival, its ground floor brick.

The style is its rule file, ``tudor.toml`` beside this module; this module
holds only the situation it takes, the drawings the file names by writer, and
the entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from buildings.cga import Grammar, Shape
from buildings.ir.nodes import BalconyNode, BraceNode, BuildingNode, GableNode
from buildings.site import BuildingClass
from buildings.trace import TraceLog
from buildings.typologies.common import kit
from buildings.typologies.common.kit import xywh
from buildings.typologies.common.rulefile import load_style, register_writer

FRONTAGE = {"cottage": 10.0, "town": 6.0, "manor": 20.0}


@dataclass(frozen=True)
class TudorSite:
    kind: str  # "cottage" | "town" | "manor"
    year: int
    klass: BuildingClass
    seed: int = 0
    width: float | None = None

    @property
    def frontage(self) -> float:
        return self.width if self.width is not None else FRONTAGE[self.kind]


def _lifting(writer):
    """A writer that hands the outlines drawn inside its shape (leaded
    panes) up to the building, where outlines are drawn, and writes the rest
    as ``writer`` would."""

    def write(shape: Shape, below, d) -> list:
        outlines = [n for n in below if n.kind == "gable"]
        rest = [n for n in below if n.kind != "gable"]
        return [*writer(shape, rest, d), *outlines]

    return write


def write_brace(shape: Shape, below, d) -> list:
    return [BraceNode(id=shape.id, kind="brace", trace=tuple(shape.trace),
                      props={**xywh(shape.scope), "direction": shape.attrs["direction"]})]


def write_gable(gable: Shape, below, d) -> list:
    """The gable's outline: the steep triangle over the eaves, standing a
    little past the wall on its bargeboards."""
    s = gable.scope
    eave = gable.attrs["verge_reach"]
    pts = ((s.x - eave, s.y), (s.x + s.w / 2.0, s.y + s.h), (s.x + s.w + eave, s.y))
    return [
        GableNode(id=gable.id, kind="gable", trace=tuple(gable.trace),
                  props={**xywh(s), "form": "front_gable", "points": pts, "hoist_beam": None,
                         "wall_material": gable.attrs["infill_paint"]}),
        *below,
    ]


def write_leading(lead: Shape, below, d) -> list:
    """The lead cames of a diamond-paned light: two families of diagonals,
    each a straight line clipped to the light."""
    s = lead.scope
    pw, ph = lead.attrs["pane_w"], lead.attrs["pane_h"]
    k = ph / pw
    run = s.h / k
    out = []
    n = int((s.w + run) / pw) + 2
    for j in range(-1, n):
        xj = s.x + (j + 0.5) * pw
        # Rising from (xj, bottom), falling from (xj, bottom) back to the left.
        for name, (x0, x1), rise in (("r", (max(s.x, xj), min(s.x + s.w, xj + run)), 1.0),
                                    ("f", (max(s.x, xj - run), min(s.x + s.w, xj)), -1.0)):
            if x1 - x0 < 0.02:
                continue
            y0 = s.y + k * (x0 - xj) * rise
            y1 = s.y + k * (x1 - xj) * rise
            out.append(GableNode(
                id=f"{lead.id}/{name}{j + 1}", kind="gable", trace=tuple(lead.trace),
                props={"x": x0, "y": min(y0, y1), "w": x1 - x0, "h": abs(y1 - y0), "form": "came",
                       "points": ((x0, y0), (x1, y1)), "hoist_beam": None, "wall_material": "plaster_white"}))
    return out


def write_oriel(oriel: Shape, below, d) -> list:
    """The bracketed sill an oriel window stands out on."""
    return [BalconyNode(id=oriel.id, kind="balcony", trace=tuple(oriel.trace),
                        props={**xywh(oriel.scope), "continuous": False, "projection": 0.5, "bracket_count": 3})]


def write_roof(roof: Shape, below, d) -> list:
    """A roof hipped at both ends: the plain roof, closing on its hips."""
    node, *rest = kit.write_roof(roof, below, d)
    run, h = roof.attrs["hip_run"], roof.scope.h
    hipped = type(node)(id=node.id, kind=node.kind, trace=node.trace, children=node.children,
                        props={**node.props, "ends": "hipped", "hip_arris": ((0.0, 0.0), (run, h))})
    return [hipped, *rest]


register_writer("tudor.roof", write_roof)
register_writer("tudor.storey", _lifting(kit.write_storey))
register_writer("tudor.cell", _lifting(kit.write_cell))
register_writer("tudor.brace", write_brace)
register_writer("tudor.gable", write_gable)
register_writer("tudor.leading", write_leading)
register_writer("tudor.oriel", write_oriel)

STYLE = load_style(Path(__file__).with_name("tudor.toml"))


def tudor_grammar() -> Grammar:
    return STYLE.grammar()


def derive_tudor(site: TudorSite, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_tudor(site: TudorSite, *, refine: Callable[[Grammar], Grammar] | None = None) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
