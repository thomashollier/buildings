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
from buildings.cga import Shape
from dataclasses import replace

from buildings.ir.nodes import BalconyNode, SocleNode
from buildings.typologies.common import kit
from buildings.typologies.common.rulefile import load_style, register_writer

__all__ = ["STYLE", "derive_haussmann", "generate_haussmann"]

def write_balconette(shape: Shape, below, d) -> list:
    """A balcony slab under a filant, none under a garde-corps; the grown iron
    (rails, bars, rosettes, diagonals) stands on it."""
    nodes = list(below)
    if shape.id.rsplit("/", 1)[-1].startswith("balcon"):
        s = shape.scope
        nodes.insert(0, BalconyNode(id=f"{shape.id}/platform", kind="balcony", trace=tuple(shape.trace),
                                    props={**kit.xywh(s), "continuous": True, "projection": 0.9,
                                           "bracket_count": max(3, round(s.w / 1.4) + 1)}))
    return nodes


register_writer("haussmann.balconette", write_balconette)


def write_rustication(shape: Shape, below, d) -> list:
    """The base's channelled stone: courses the rules state."""
    return [SocleNode(id=shape.id, kind="socle", trace=tuple(shape.trace),
                      props={**kit.xywh(shape.scope), "treatment": shape.attrs["treatment"],
                             "course_columns": shape.attrs["course_columns"], "course_rows": shape.attrs["course_rows"]})]


def write_storey(storey: Shape, below, d) -> list:
    """A storey, its socle laid on the wall before its openings cut it."""
    out = kit.write_storey(storey, below, d)
    node = out[0]
    socles = tuple(c for c in node.children if c.kind == "socle")
    rest = tuple(c for c in node.children if c.kind != "socle")
    return [replace(node, children=socles + rest), *out[1:]]


def write_light(light: Shape, below, d) -> list:
    """A light, with what a two-storey carriage arch states: which register it
    is, how tall its leaves stand, what fills its head."""
    out = kit.write_light(light, below, d)
    extra = {k: light.attrs[k] for k in ("arch_register", "leaf_height", "head_infill") if k in light.attrs}
    if not extra:
        return out
    node = out[0]
    return [replace(node, props={**node.props, **extra}), *out[1:]]


register_writer("haussmann.rustication", write_rustication)
register_writer("haussmann.light", write_light)
register_writer("haussmann.storey", write_storey)

STYLE = load_style(Path(__file__).with_name("haussmann.toml"))


def derive_haussmann(site: SiteContext, *, refine: Callable[[Grammar], Grammar] | None = None):
    return STYLE.derive(site, refine=refine)


def generate_haussmann(
    site: SiteContext, *, refine: Callable[[Grammar], Grammar] | None = None
) -> tuple[BuildingNode, TraceLog]:
    return STYLE.generate(site, refine=refine)
