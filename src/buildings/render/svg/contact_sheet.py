"""Contact sheet (S8): many buildings, one grid, one glance.

Per the brief, a contact sheet is "the cheapest way to catch the single broken
outlier among many" — so every building in the sheet is drawn at the SAME
scale, standing on the SAME ground line within its cell, in a cell of the SAME
size. An outlier — a roof that broke out of its envelope, a facade with no
bays, a storey stack that came out one module too tall — reads immediately as
a shape that does not match its neighbours, without comparing numbers.

This module draws no *building* geometry of its own: every building is drawn
by ``render.draw_building``, the same function ``render()`` uses, so a contact
sheet is never a second, divergent code path for what one building looks like.
It only lays out the shared grid and the per-cell pixel chrome (background,
ground band, caption), which is why those are written directly in pixel space
rather than through the metre-based ``Canvas`` conversion a building is drawn
with — that conversion is reset per cell, once, right before the building it
belongs to is drawn.
"""

from __future__ import annotations

import math
from typing import Sequence

from buildings.ir.nodes import Node
from buildings.render.svg.canvas import Canvas
from buildings.render.svg.colors import COLORS
from buildings.render.svg.render import building_extent_m, draw_building

__all__ = ["render_contact_sheet"]

_C = COLORS
_MARGIN_M = 1.2
_GROUND_BAND_M = 0.5
_LABEL_BAND_M = 0.5
_CELL_GAP_M = 0.5


def _raw_rect(canvas: Canvas, x_px: float, y_px: float, w_px: float, h_px: float, fill: str, stroke: str | None = None, stroke_w: float = 0.4) -> None:
    s = stroke or "none"
    canvas.elements.append(
        f'<rect x="{x_px:.2f}" y="{y_px:.2f}" width="{w_px:.2f}" height="{h_px:.2f}" '
        f'fill="{fill}" stroke="{s}" stroke-width="{stroke_w}"/>'
    )


def _raw_text(canvas: Canvas, x_px: float, y_px: float, label: str, size: float = 9.0, fill: str = "#555555") -> None:
    canvas.elements.append(
        f'<text x="{x_px:.2f}" y="{y_px:.2f}" font-family="Helvetica Neue, Arial, sans-serif" '
        f'font-size="{size}" fill="{fill}" text-anchor="middle">{label}</text>'
    )


def render_contact_sheet(
    nodes: Sequence[Node],
    *,
    cols: int | None = None,
    width_px: int = 1800,
    labels: bool = False,
) -> str:
    """Render ``nodes`` (each a ``BuildingNode``) into one grid SVG.

    ``cols`` defaults to a near-square layout. Every cell is the same size —
    the widest facade and the tallest silhouette among ``nodes``, plus a fixed
    margin — and every building's pavement line sits at the same height within
    its cell, so scale and baseline are shared across the whole sheet and
    nothing about the layout depends on which building is being looked at.
    """
    n = len(nodes)
    if n == 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"/>'

    extents = [building_extent_m(node) for node in nodes]
    max_w = max(w for w, _ in extents)
    max_h = max(h for _, h in extents)

    cols = cols or max(1, round(math.sqrt(n)))
    rows = math.ceil(n / cols)

    cell_w_m = max_w + 2 * _MARGIN_M
    cell_h_m = max_h + _MARGIN_M + _GROUND_BAND_M + _LABEL_BAND_M

    sheet_w_m = cols * cell_w_m + (cols + 1) * _CELL_GAP_M
    sheet_h_m = rows * cell_h_m + (rows + 1) * _CELL_GAP_M
    scale = max(1.0, width_px / sheet_w_m)

    sheet_w_px = sheet_w_m * scale
    sheet_h_px = sheet_h_m * scale
    canvas = Canvas(scale=scale)

    _raw_rect(canvas, 0, 0, sheet_w_px, sheet_h_px, "#F2EFE8")

    for index, (node, (facade_w, total_h)) in enumerate(zip(nodes, extents)):
        row, col = divmod(index, cols)
        cell_x0_m = _CELL_GAP_M + col * (cell_w_m + _CELL_GAP_M)
        cell_y0_m = _CELL_GAP_M + row * (cell_h_m + _CELL_GAP_M)

        cell_x0_px = cell_x0_m * scale
        cell_y0_px = cell_y0_m * scale
        cell_w_px = cell_w_m * scale
        cell_h_px = cell_h_m * scale
        label_h_px = _LABEL_BAND_M * scale
        ground_h_px = _GROUND_BAND_M * scale

        _raw_rect(canvas, cell_x0_px, cell_y0_px, cell_w_px, cell_h_px, "#FFFFFF", stroke="#B8AE9A", stroke_w=0.6)
        _raw_rect(canvas, cell_x0_px, cell_y0_px + label_h_px, cell_w_px, cell_h_px - label_h_px - ground_h_px, _C["sky"])
        _raw_rect(canvas, cell_x0_px, cell_y0_px + cell_h_px - ground_h_px, cell_w_px, ground_h_px, _C["ground"])
        _raw_text(canvas, cell_x0_px + cell_w_px / 2.0, cell_y0_px + label_h_px * 0.75, f"#{index}  {facade_w:.1f}×{total_h:.1f} m")

        pavement_y_m = cell_y0_m + cell_h_m - _GROUND_BAND_M
        canvas.x_origin = (cell_x0_m + _MARGIN_M) * scale
        canvas.y_origin = pavement_y_m * scale
        draw_building(canvas, node, labels)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w_px:.2f}" '
        f'height="{sheet_h_px:.2f}" viewBox="0 0 {sheet_w_px:.2f} {sheet_h_px:.2f}">\n'
        f'<style>text {{ font-family: "Helvetica Neue", Arial, sans-serif; }}</style>\n'
    )
    svg += "\n".join(canvas.elements)
    svg += "\n</svg>"
    return svg
