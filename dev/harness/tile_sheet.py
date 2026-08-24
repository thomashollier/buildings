#!/usr/bin/env python3
"""Tile every preset into one sheet at a CONSISTENT scale.

The point of this sheet is comparison, so two things matter more than looking
tidy:

**One scale throughout.** `render()` fits a building to `width_px`, so a 9 m
frontage and a 24 m one come out the same size on screen and the class ladder
becomes invisible. Here the scale is pinned instead: `render()` computes
`scale = width_px / (facade_w + 2*MARGIN)`, so asking for
`width_px = PX_PER_M * (facade_w + 2*MARGIN)` gives exactly `PX_PER_M`
everywhere, and a metre is a metre from tile to tile.

**One ground line.** Buildings are bottom-aligned on a shared pavement, so
height differences read directly. A building that stops short of its ceiling
should look short.

    python3 dev/harness/tile_sheet.py            # all presets
    python3 dev/harness/tile_sheet.py A C1 C4    # a subset
    python3 dev/harness/tile_sheet.py --px 26    # coarser/finer
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dev" / "harness"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import layouts  # noqa: E402
from buildings.render.svg import render  # noqa: E402
from buildings.render.svg.render import _MARGIN_M  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402
from buildings.typologies.paris.roles import assign_roles  # noqa: E402
from buildings.typologies.paris.structure import solve_structure  # noqa: E402

PX_PER_M = 34.0
PAD = 22
LABEL_H = 74
BG = (250, 249, 246)
INK = (28, 28, 30)
DIM = (120, 120, 126)


def _font(size: int):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tile_for(key: str, tmp: Path) -> tuple[Image.Image, list[str]]:
    """Render one preset at the pinned scale; return the image and its caption."""
    lay = layouts.LAYOUTS[key]
    grid = solve_structure(lay.site)
    roled = assign_roles(grid)
    node, _ = generate(lay.site)

    facade_w = float(node.props.get("w", lay.site.parcel_width))
    width_px = int(round(PX_PER_M * (facade_w + 2 * _MARGIN_M)))

    svg = tmp / f"{key}.svg"
    png = tmp / f"{key}.png"
    svg.write_text(render(node, width_px=width_px), encoding="utf-8")
    subprocess.run(["rsvg-convert", str(svg), "-o", str(png)], check=True)

    etages = sum(1 for s in roled.storeys if s.role.value in ("principal", "upper"))
    attics = sum(1 for s in roled.storeys if s.role.value == "attic")
    has_ent = any(s.role.value == "mezzanine" for s in roled.storeys)
    ceiling = float(grid.cornice_height)
    caption = [
        f"{key} · {lay.title}",
        f"street {lay.site.street_width:.0f} m · parcel {lay.site.parcel_width:.0f}×"
        f"{lay.site.parcel_depth:.0f} m · {lay.site.year} · {lay.site.klass.value}"
        f" · {lay.site.ground.value}" + (" · corner" if lay.site.corner else ""),
        f"{etages} étages{' + entresol' if has_ent else ''} · "
        f"{attics} garret storey{'s' if attics != 1 else ''} · "
        f"cornice {grid.built_height:.2f} of {ceiling:.2f} m "
        f"({100 * grid.built_height / ceiling:.0f}%) · comble {float(grid.comble_height):.2f} m",
    ]
    return Image.open(png).convert("RGB"), caption


def build(keys: list[str], out: Path) -> Path:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tiles = [(k, *tile_for(k, tmp)) for k in keys]

        cell_w = max(im.width for _, im, _ in tiles) + PAD
        cell_h = max(im.height for _, im, _ in tiles) + PAD
        cols = min(4, len(tiles))
        rows = (len(tiles) + cols - 1) // cols

        W = cols * cell_w + PAD
        H = rows * (cell_h + LABEL_H) + PAD + 46
        sheet = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(sheet)
        f_t, f_s, f_h = _font(19), _font(14), _font(15)

        d.text((PAD, 14),
               f"Paris preset layouts — one scale throughout, {PX_PER_M:.0f} px per metre, "
               f"common ground line", fill=INK, font=f_h)

        for i, (key, im, cap) in enumerate(tiles):
            cx = PAD + (i % cols) * cell_w
            cy = 46 + (i // cols) * (cell_h + LABEL_H)
            # bottom-align on a shared ground line so heights compare directly
            ox = cx + (cell_w - PAD - im.width) // 2
            oy = cy + (cell_h - im.height)
            sheet.paste(im, (ox, oy))
            ty = cy + cell_h + 6
            d.text((cx, ty), cap[0], fill=INK, font=f_t)
            d.text((cx, ty + 24), cap[1], fill=DIM, font=f_s)
            d.text((cx, ty + 42), cap[2], fill=DIM, font=f_s)

        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out)
        return out


def main(argv: list[str]) -> int:
    global PX_PER_M
    if "--px" in argv:
        i = argv.index("--px")
        PX_PER_M = float(argv[i + 1])
        del argv[i:i + 2]
    keys = [a for a in argv if a in layouts.LAYOUTS] or list(layouts.LAYOUTS)
    out = build(keys, ROOT / "dev" / "logs" / "tiles" / "presets.png")
    print(f"{len(keys)} presets -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
