"""Coordinate conversion and drawing primitives (S8).

Ported from ``../haussmann/backends/svg.py::SVGContext``. The IR's geometry
convention (``ir/nodes.py``) is metres, origin at pavement level at the left
edge of the parcel, +x right, +y up. SVG is pixels, origin top-left, +y down.
This module is the one place that conversion happens; every drawing function
in ``elements.py`` works in metres and calls through here.

Nothing here reads a node. It knows nothing about storeys, roles, dates or
classes — only how to turn a rectangle, a line, a polygon or a label, given in
metres, into SVG markup at some pixel scale and origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Canvas:
    """Accumulates SVG element strings and converts metres to pixels.

    ``x_origin``/``y_origin`` are in PIXELS, not metres — they are the pixel
    position of this canvas's own (0, 0) (pavement, facade plane), so a
    contact sheet can move them per cell without touching ``scale``.
    """

    elements: list[str] = field(default_factory=list)
    scale: float = 40.0  # pixels per metre
    x_origin: float = 0.0
    y_origin: float = 0.0

    def px(self, metres: float) -> float:
        return metres * self.scale

    def x(self, m: float) -> float:
        return self.x_origin + self.px(m)

    def y(self, m: float) -> float:
        """Metres above the pavement -> SVG y (top-down)."""
        return self.y_origin - self.px(m)

    def rect(
        self,
        x_m: float,
        y_m: float,
        w_m: float,
        h_m: float,
        fill: str,
        stroke: str | None = None,
        stroke_w: float = 0.5,
        rx: float = 0.0,
        opacity: float = 1.0,
        dash: str | None = None,
    ) -> None:
        sx, sw, sh = self.x(x_m), self.px(w_m), self.px(h_m)
        sy = self.y(y_m + h_m)  # SVG y is the TOP of the rect
        s = stroke or "none"
        extra = f' rx="{rx:.2f}"' if rx else ""
        if opacity < 1.0:
            extra += f' opacity="{opacity}"'
        if dash:
            extra += f' stroke-dasharray="{dash}"'
        self.elements.append(
            f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{sw:.2f}" height="{sh:.2f}" '
            f'fill="{fill}" stroke="{s}" stroke-width="{stroke_w}"{extra}/>'
        )

    def line(
        self,
        x1_m: float,
        y1_m: float,
        x2_m: float,
        y2_m: float,
        stroke: str = "#4A4038",
        stroke_w: float = 1.0,
        dash: str | None = None,
    ) -> None:
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.elements.append(
            f'<line x1="{self.x(x1_m):.2f}" y1="{self.y(y1_m):.2f}" '
            f'x2="{self.x(x2_m):.2f}" y2="{self.y(y2_m):.2f}" '
            f'stroke="{stroke}" stroke-width="{stroke_w}"{extra}/>'
        )

    def polygon(
        self,
        points_m: list[tuple[float, float]],
        fill: str,
        stroke: str = "#4A4038",
        stroke_w: float = 0.5,
    ) -> None:
        pts = " ".join(f"{self.x(px):.2f},{self.y(py):.2f}" for px, py in points_m)
        self.elements.append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_w}"/>'
        )

    def circle(
        self,
        cx_m: float,
        cy_m: float,
        r_m: float,
        fill: str,
        stroke: str = "#4A4038",
        stroke_w: float = 0.5,
    ) -> None:
        self.elements.append(
            f'<circle cx="{self.x(cx_m):.2f}" cy="{self.y(cy_m):.2f}" '
            f'r="{self.px(r_m):.2f}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_w}"/>'
        )

    def text(
        self,
        x_m: float,
        y_m: float,
        label: str,
        size: float = 10.0,
        fill: str = "#666666",
        anchor: str = "middle",
    ) -> None:
        self.elements.append(
            f'<text x="{self.x(x_m):.2f}" y="{self.y(y_m):.2f}" '
            f'font-family="Helvetica Neue, Arial, sans-serif" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}">{_escape(label)}</text>'
        )


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
