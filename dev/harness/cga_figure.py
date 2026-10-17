#!/usr/bin/env python3
"""One figure, three panels: the facade the grammar derives, the shape tree
it derived it as, and the same facade with three local variations applied.

Run:  python3 dev/harness/cga_figure.py OUT_DIR [--grand]

Writes ``cga_figure.svg`` (and ``cga_figure.png`` where ``rsvg-convert`` is
on the PATH). Validation output, like the contact sheets: every facade in it
is drawn by the real renderer from the real IR.
"""
from __future__ import annotations

import argparse
import dataclasses
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dev" / "harness"))

from cga_blast_radius import (  # noqa: E402
    no_keystones_on_the_entrance_axis,
    round_heads_on_the_noble_floor,
    taller_balustrade_on_the_noble_floor,
)

from buildings.render.svg.render import _GROUND_BAND_M, _MARGIN_M, render  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import walk  # noqa: E402
from buildings.typologies.paris.grammar import derive_paris, generate_cga  # noqa: E402

WIDTH_PX = 700

#: label -> (fill, stroke, stroke width). Containers are outlines; the parts a
#: window is made of are filled, so the tree reads as a window at a glance.
STYLE = {
    "Roof": ("#9aa3ad", "#4b5563", 1.2),
    "Storey": ("none", "#111827", 1.6),
    "Cell": ("none", "#6b7280", 0.6),
    "Pier": ("#e7dcc6", "none", 0),
    "Breast": ("#d9c7a3", "none", 0),
    "Lintel": ("#cbb58c", "none", 0),
    "Light": ("#7fa7d1", "none", 0),
    "Surround": ("none", "#7c3aed", 1.0),
    "Keystone": ("none", "#dc2626", 2.4),
    "Rail": ("#f59e0b55", "#b45309", 0.8),
    "Balconette": ("#10b98155", "#047857", 0.8),
    "Shopfront": ("none", "#0e7490", 1.2),
}
DRAW_ORDER = list(STYLE)


def _frame(building):
    facade_w = float(building.props["w"])
    total_h = float(building.props["h"])
    scale = max(1.0, WIDTH_PX / (facade_w + 2 * _MARGIN_M))
    w_px = (facade_w + 2 * _MARGIN_M) * scale
    h_px = (total_h + _MARGIN_M + _GROUND_BAND_M) * scale

    def px(x, y):
        return (x + _MARGIN_M) * scale, (total_h + _GROUND_BAND_M - y) * scale

    return scale, w_px, h_px, px


def _shape_tree_panel(lot, building) -> str:
    scale, w_px, h_px, px = _frame(building)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px:.1f}" height="{h_px:.1f}" '
        f'viewBox="0 0 {w_px:.1f} {h_px:.1f}">',
        f'<rect width="{w_px:.1f}" height="{h_px:.1f}" fill="#fbfaf7"/>',
    ]
    shapes = sorted(
        (s for s in lot.walk() if s.label in STYLE),
        key=lambda s: DRAW_ORDER.index(s.label),
    )
    for s in shapes:
        fill, stroke, sw = STYLE[s.label]
        x0, y1 = px(s.scope.x, s.scope.y)
        x1, y0 = px(s.scope.x + s.scope.w, s.scope.y + s.scope.h)
        if s.label == "Keystone":
            out.append(
                f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y0:.1f}" '
                f'stroke="{stroke}" stroke-width="{sw}"/>'
            )
            continue
        out.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
    # Storey roles down the left margin.
    for st in lot.children[0].children:
        x, y = px(0, st.scope.y + st.scope.h / 2)
        out.append(
            f'<text x="{x - 6:.1f}" y="{y + 4:.1f}" font-size="11" text-anchor="end" '
            f'fill="#111827" font-family="Helvetica, Arial">{st.attrs["role"].value}</text>'
        )
    # Legend.
    ly = 14
    for label in ["Storey", "Cell", "Pier", "Breast", "Light", "Lintel", "Surround", "Keystone", "Rail", "Balconette", "Shopfront", "Roof"]:
        fill, stroke, _ = STYLE[label]
        out.append(
            f'<rect x="{w_px - 112:.1f}" y="{ly - 9}" width="12" height="10" '
            f'fill="{fill if fill != "none" else "#ffffff"}" stroke="{stroke if stroke != "none" else "#999"}"/>'
            f'<text x="{w_px - 95:.1f}" y="{ly}" font-size="10" fill="#111827" '
            f'font-family="Helvetica, Arial">{label}</text>'
        )
        ly += 14
    out.append("</svg>")
    return "\n".join(out)


def _changed_ids(before, after) -> list:
    a = {n.id: n for n in walk(before)}
    b = {n.id: n for n in walk(after)}
    out = []
    for i in sorted(set(a) | set(b)):
        na, nb = a.get(i), b.get(i)
        if na is None or nb is None:
            out.append(na or nb)
        elif dataclasses.replace(na, children=()) != dataclasses.replace(nb, children=()):
            if na.kind not in ("bay", "storey", "building"):
                out.append(nb)
    return out


def _highlight(svg: str, building, nodes) -> str:
    _, _, _, px = _frame(building)
    marks = []
    for n in nodes:
        x, y, w, h = (float(n.props[k]) for k in "xywh")
        x0, y1 = px(x, y)
        x1, y0 = px(x + w, y + max(h, 0.08))
        marks.append(
            f'<rect x="{x0 - 2:.1f}" y="{y0 - 2:.1f}" width="{x1 - x0 + 4:.1f}" '
            f'height="{y1 - y0 + 4:.1f}" fill="none" stroke="#e11d48" stroke-width="1.6" '
            f'stroke-dasharray="4 2"/>'
        )
    return svg.replace("</svg>", "\n".join(marks) + "\n</svg>")


def _caption(text: str, w: float) -> str:
    return (
        f'<text x="{w / 2:.1f}" y="22" font-size="15" text-anchor="middle" fill="#111827" '
        f'font-family="Helvetica, Arial" font-weight="600">{text}</text>'
    )


def _strip_header(svg: str) -> tuple[str, float, float]:
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', svg)
    return svg, float(m.group(1)), float(m.group(2))


def figure(site: SiteContext) -> str:
    building, _ = generate_cga(site)
    lot, _ = derive_paris(site)

    def variations(g):
        return no_keystones_on_the_entrance_axis(
            taller_balustrade_on_the_noble_floor(round_heads_on_the_noble_floor(g))
        )

    varied, _ = generate_cga(site, refine=variations)
    panels = [
        ("Derived by the grammar", render(building, width_px=WIDTH_PX)),
        ("The shape tree it derived", _shape_tree_panel(lot, building)),
        (
            "Three local variations (changes outlined)",
            _highlight(render(varied, width_px=WIDTH_PX), varied, _changed_ids(building, varied)),
        ),
    ]
    gap, top = 24, 36
    sized = [(c, *_strip_header(s)[1:], s) for c, s in panels]
    total_w = sum(w for _, w, _, _ in sized) + gap * (len(sized) + 1)
    total_h = max(h for _, _, h, _ in sized) + top + gap
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}">',
        f'<rect width="{total_w:.0f}" height="{total_h:.0f}" fill="#ffffff"/>',
    ]
    x = gap
    for caption, w, h, svg in sized:
        inner = svg.replace("<svg ", f'<svg x="{x:.1f}" y="{top}" ', 1)
        out.append(f'<g transform="translate({x:.1f},0)">{_caption(caption, w)}</g>')
        out.append(inner)
        x += w + gap
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--grand", action="store_true", help="a grand building on a 30 m avenue")
    args = ap.parse_args(argv)
    site = (
        SiteContext(30.0, 20.0, 18.0, 1868, BuildingClass.GRAND, GroundProgramme.SHOP, seed=3)
        if args.grand
        else SiteContext(20.0, 14.0, 14.0, 1865, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=8)
    )
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    svg_path = out / "cga_figure.svg"
    svg_path.write_text(figure(site))
    print(svg_path)
    if shutil.which("rsvg-convert"):
        png = out / "cga_figure.png"
        subprocess.run(["rsvg-convert", "-b", "white", str(svg_path), "-o", str(png)], check=True)
        print(png)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
