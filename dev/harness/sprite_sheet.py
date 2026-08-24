#!/usr/bin/env python3
"""Pack every preset into a sprite sheet: uniform cells, no furniture.

Different job from `tile_sheet.py`, which is a contact sheet for a human to
read — captions, a title, a paper-coloured ground. This one is for a consumer:
a grid of identically-sized cells, transparent background, no text, plus a JSON
atlas naming what is in each cell and where its pavement line falls.

Three things are held fixed, and they are the reason this is worth generating
rather than cropping by hand:

**One scale.** `render()` fits a building to `width_px`, so left alone a 9 m
frontage and a 15 m one come out the same size and the class ladder vanishes.
The scale is pinned instead — `PX_PER_M` everywhere — so a metre is a metre
from cell to cell and sprites can be composited into one street.

**One baseline.** Every sprite is bottom-aligned on its cell's pavement line,
which sits at the same offset in every cell. Drop two sprites at the same y and
they stand on the same ground.

**No sky.** `render()` paints a sky rect and a ground band as the first two
elements of the SVG; both are stripped before rasterising, so a sprite is the
building and nothing else and can be composited over anything.

    python3 dev/harness/sprite_sheet.py                 # all presets
    python3 dev/harness/sprite_sheet.py A AC H83 H87    # a subset
    python3 dev/harness/sprite_sheet.py --px 48         # finer
    python3 dev/harness/sprite_sheet.py --cols 5        # grid shape
    python3 dev/harness/sprite_sheet.py --labels        # ...and a keyed copy

``--labels`` writes a SECOND file, ``sprites_labelled.png``, for reading rather
than for consuming. The sheet proper stays bare on purpose: text baked into a
cell travels with the sprite, and the atlas's ``baseline_from_cell_top`` is a
promise about cell geometry that a caption band would quietly break. So the
keyed copy is a separate artifact with its own taller cells, and nothing reads
it back.
"""
from __future__ import annotations

import json
import re
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
GUTTER = 8

#: The keyed copy's own furniture. Only ``--labels`` ever uses any of this.
LABEL_H = 46
PAPER = (250, 249, 246)
INK = (28, 28, 30)
DIM = (120, 120, 126)


def _font(size: int):
    for path in ("/System/Library/Fonts/Helvetica.ttc",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

#: The sky rect and the ground band, which `render()` emits as the first two
#: elements after the stylesheet. Matched on being full-width and anchored at
#: x=0 rather than on their colours, so a repaint of the palette does not
#: silently start baking a sky into every sprite.
_BACKDROP = re.compile(r'<rect x="0" y="[0-9.]+" width="[0-9.]+" height="[0-9.]+" fill="#[0-9A-Fa-f]{6}"/>')


def _walk(node):
    yield node
    for child in getattr(node, "children", ()) or ():
        yield from _walk(child)


def _strip_backdrop(svg: str) -> str:
    """Drop the two background rects, and only those two."""
    head, sep, tail = svg.partition("</style>")
    if not sep:
        raise AssertionError("render() changed shape: no </style> to anchor on")
    stripped, n = _BACKDROP.subn("", tail, count=2)
    if n != 2:
        raise AssertionError(f"expected a sky rect and a ground band, matched {n}")
    return head + sep + stripped


def sprite_for(key: str, tmp: Path) -> tuple[Image.Image, dict]:
    """One preset, rasterised transparent at the pinned scale."""
    lay = layouts.LAYOUTS[key]
    node, _ = generate(lay.site)
    grid = solve_structure(lay.site)

    facade_w = float(node.props.get("w", lay.site.parcel_width))
    total_h = float(node.props.get("h", grid.built_height))
    width_px = int(round(PX_PER_M * (facade_w + 2 * _MARGIN_M)))

    svg, png = tmp / f"{key}.svg", tmp / f"{key}.png"
    svg.write_text(_strip_backdrop(render(node, width_px=width_px)), encoding="utf-8")
    subprocess.run(["rsvg-convert", str(svg), "-o", str(png)], check=True)

    im = Image.open(png).convert("RGBA")
    # Trim the transparent margin `render()` leaves around the drawing, so the
    # sprite's own box is the building's box. `getbbox` is exact here because
    # the backdrop is gone: every remaining pixel belongs to the building.
    box = im.getbbox()
    if box:
        im = im.crop(box)

    # The sprite is TALLER than `total_h_m` and this is not a rounding error:
    # the souches stand above the ridge, so the drawn geometry overshoots the
    # building's stated height by however tall a chimney is. Stated here, read
    # off the IR rather than measured off the pixels, so a consumer aligning by
    # metres has the number instead of discovering it.
    drawn_top = max(
        float(n.props.get("y", 0.0)) + float(n.props.get("h", 0.0))
        for n in _walk(node)
        if n.props.get("h") is not None
    )
    etages = sum(
        1 for st in assign_roles(grid).storeys if st.role.value in ("principal", "upper")
    )
    garrets = sum(1 for st in assign_roles(grid).storeys if st.role.value == "attic")
    return im, {
        "key": key,
        "title": lay.title,
        "etages": etages,
        "garret_storeys": garrets,
        "cornice_built_m": round(grid.built_height, 3),
        "cornice_legal_m": round(float(grid.cornice_height), 3),
        "comble_m": round(float(grid.comble_height), 3),
        "facade_w_m": round(facade_w, 4),
        "total_h_m": round(total_h, 4),
        "drawn_top_m": round(drawn_top, 4),
        "over_ridge_m": round(drawn_top - total_h, 4),
        "year": lay.site.year,
        "street_width_m": lay.site.street_width,
        "klass": lay.site.klass.value,
        "ground": lay.site.ground.value,
        "corner": bool(lay.site.corner),
    }


def _write_keyed_copy(sprites, cell_w, cell_h, cols, out: Path) -> Path:
    """The same grid, on paper, with each cell keyed (``--labels``).

    Deliberately a second file. The sheet proper is a consumable: text baked
    into a cell travels with the sprite, and the atlas promises a fixed
    ``baseline_from_cell_top`` that a caption band would silently move. This
    copy has taller cells and no atlas, and nothing reads it back.
    """
    rows = (len(sprites) + cols - 1) // cols
    tall = cell_h + LABEL_H
    sheet = Image.new("RGB", (cols * cell_w, rows * tall), PAPER)
    draw = ImageDraw.Draw(sheet)
    f_key, f_sub = _font(19), _font(13)

    for i, (key, im, meta) in enumerate(sprites):
        col, row = i % cols, i // cols
        ox = col * cell_w + (cell_w - im.width) // 2
        oy = row * tall + (cell_h - GUTTER // 2 - im.height)
        sheet.paste(im, (ox, oy), im)

        tx, ty = col * cell_w + 10, row * tall + cell_h + 2
        draw.text((tx, ty), f"{key} · {meta['title']}", fill=INK, font=f_key)
        ceiling = meta["cornice_legal_m"]
        pct = 100.0 * meta["cornice_built_m"] / ceiling if ceiling else 0.0
        draw.text(
            (tx, ty + 22),
            f"{meta['etages']} étages · {meta['garret_storeys']} garret · "
            f"cornice {meta['cornice_built_m']:.2f} of {ceiling:.2f} m ({pct:.0f} %) · "
            f"comble {meta['comble_m']:.2f} m · {meta['year']}",
            fill=DIM,
            font=f_sub,
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def build(keys: list[str], out: Path, cols: int | None = None, labels: bool = False) -> Path:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sprites = [(k, *sprite_for(k, tmp)) for k in keys]

        cell_w = max(im.width for _, im, _ in sprites) + GUTTER
        cell_h = max(im.height for _, im, _ in sprites) + GUTTER
        cols = cols or min(5, len(sprites))
        rows = (len(sprites) + cols - 1) // cols

        sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (0, 0, 0, 0))
        atlas = {
            "px_per_m": PX_PER_M,
            "cell": {"w": cell_w, "h": cell_h},
            "cols": cols,
            "rows": rows,
            # Every sprite is bottom-aligned inside its cell, so a cell's
            # pavement is a fixed offset from the cell's top: the cell height
            # less the gutter beneath it.
            "baseline_from_cell_top": cell_h - GUTTER // 2,
            # `h` is the sprite's pixel box; `total_h_m` is the building's
            # stated height to the ridge. They do NOT satisfy
            # h == total_h_m * px_per_m, because the chimneys stand above the
            # ridge — `over_ridge_m` is that difference, per sprite.
            "note": "h(px) covers drawn_top_m, not total_h_m; see over_ridge_m",
            "sprites": [],
        }

        for i, (key, im, meta) in enumerate(sprites):
            col, row = i % cols, i // cols
            # centred horizontally, standing on the cell's pavement line
            x = col * cell_w + (cell_w - im.width) // 2
            y = row * cell_h + (cell_h - GUTTER // 2 - im.height)
            sheet.alpha_composite(im, (x, y))
            atlas["sprites"].append(
                {**meta, "col": col, "row": row,
                 "x": x, "y": y, "w": im.width, "h": im.height}
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out)
        out.with_suffix(".json").write_text(
            json.dumps(atlas, indent=2) + "\n", encoding="utf-8"
        )
        if labels:
            _write_keyed_copy(
                sprites, cell_w, cell_h, cols,
                out.with_name(out.stem + "_labelled" + out.suffix),
            )
        return out


def main(argv: list[str]) -> int:
    global PX_PER_M
    cols = None
    labels = "--labels" in argv
    if labels:
        argv.remove("--labels")
    for flag, cast in (("--px", float), ("--cols", int)):
        if flag in argv:
            i = argv.index(flag)
            value = cast(argv[i + 1])
            del argv[i:i + 2]
            if flag == "--px":
                PX_PER_M = value
            else:
                cols = value
    keys = [a for a in argv if a in layouts.LAYOUTS] or list(layouts.LAYOUTS)
    out = build(keys, ROOT / "dev" / "logs" / "tiles" / "sprites.png", cols, labels)
    print(f"{len(keys)} sprites -> {out.relative_to(ROOT)}")
    print(f"           atlas -> {out.with_suffix('.json').relative_to(ROOT)}")
    if labels:
        keyed = out.with_name(out.stem + "_labelled" + out.suffix)
        print(f"          keyed -> {keyed.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
