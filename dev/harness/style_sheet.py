#!/usr/bin/env python3
"""Every ruleset on one sheet: one characteristic building per style, each
fitted to its own cell, in a grid.

Run:  python3 dev/harness/style_sheet.py [OUT_DIR]     (default docs/)

Writes ``all_styles.svg`` and, where ``rsvg-convert`` is on the PATH,
``all_styles.png``. The buildings come from the README strips
(``readme_strips.py``), so the sheet and the strips never disagree. Cells are
not at one scale -- a pagoda and a pavilion would not both be visible -- so
each building's caption says how wide it is.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dev" / "harness"))

from readme_strips import _deco_family, strips  # noqa: E402

from buildings.render.svg.render import _MARGIN_M, render  # noqa: E402

# Which of each strip's six buildings stands for the style (default: the third).
PICK = {
    "paris_measured": 1, "haussmann": 1, "deco": 4, "gothic_cathedral": 0,
    "classical": 0, "pagoda": 1, "venice_byzantine": 3, "deco_religious_works": 2,
    "soviet_panel": 3, "tudor": 3, "sanaa": 3, "romanesque": 0, "baroque": 4,
    "victorian": 5, "amsterdam": 0, "miami_deco": 4, "movie_palace": 3,
    "deco_office": 4, "deco_civic": 5, "deco_commercial": 4, "renaissance": 2,
    "second_empire": 4, "beaux_arts": 3, "spanish_colonial": 3, "cairo": 5,
    "shophouse": 4, "pombaline": 0, "chicago": 3, "soho": 2, "venice": 3,
}
COLS = 6
CELL_W, CELL_H = 300.0, 330.0
DRAW_H = 270.0


SHORT = {"venice_byzantine": "Veneto-Byzantine palazzo"}


def _title(t: str) -> str:
    t = t.split(":")[0]
    return re.sub(r"\s*\([^)]*\.(toml|py)[^)]*\)\s*$|\s*\(Python\)$", "", t).replace("&", "&amp;")


def sheet() -> str:
    cells = []
    for name, (title, buildings) in {**strips(), **_deco_family()}.items():
        caption, b = buildings[PICK.get(name, 2)]
        bw, bh = float(b.props["w"]) + 2 * _MARGIN_M, float(b.props["h"]) + 2 * _MARGIN_M
        scale = min((CELL_W - 20) / bw, DRAW_H / bh)
        svg = render(b, width_px=max(1, int(round(bw * scale))))
        w, h = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups())
        cells.append((SHORT.get(name) or _title(title), f"{caption} · {float(b.props['w']):.0f} m wide", svg, w, h))
    rows = (len(cells) + COLS - 1) // COLS
    top = 56
    total_w, total_h = COLS * CELL_W + 20, rows * CELL_H + top + 10
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}">',
        f'<rect width="{total_w:.0f}" height="{total_h:.0f}" fill="#ffffff"/>',
        f'<text x="20" y="36" font-size="22" font-weight="600" font-family="Helvetica, Arial" fill="#111827">'
        f"{len(cells)} rulesets on one split-grammar engine</text>",
    ]
    for k, (title, caption, svg, w, h) in enumerate(cells):
        cx, cy = 10 + (k % COLS) * CELL_W, top + (k // COLS) * CELL_H
        out.append(f'<rect x="{cx + 4}" y="{cy}" width="{CELL_W - 8}" height="{CELL_H - 8}" fill="#F7F7F5" rx="6"/>')
        out.append(svg.replace("<svg ", f'<svg x="{cx + (CELL_W - w) / 2:.1f}" y="{cy + 6 + DRAW_H - h:.1f}" ', 1))
        out.append(
            f'<text x="{cx + CELL_W / 2:.1f}" y="{cy + DRAW_H + 26:.1f}" font-size="13" font-weight="600" '
            f'text-anchor="middle" font-family="Helvetica, Arial" fill="#111827">{title[:44]}</text>'
        )
        out.append(
            f'<text x="{cx + CELL_W / 2:.1f}" y="{cy + DRAW_H + 44:.1f}" font-size="11" text-anchor="middle" '
            f'font-family="Helvetica, Arial" fill="#4B5563">{caption.replace("&", "&amp;")[:52]}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else ROOT / "docs"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "all_styles.svg"
    path.write_text(sheet())
    print(path)
    if shutil.which("rsvg-convert"):
        png = path.with_suffix(".png")
        subprocess.run(["rsvg-convert", "-b", "white", str(path), "-o", str(png)], check=True)
        print(png)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
