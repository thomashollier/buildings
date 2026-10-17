#!/usr/bin/env python3
"""A street of SoHo types at one scale, beside a Paris immeuble for contrast.

Run:  python3 dev/harness/soho_sheet.py OUT_DIR [--styles]

``--styles`` draws the Amsterdam, Venice and Chicago grammars instead, and
``--more`` the Georgian, Kyoto, Corbusian and Art Deco ones (the tower at its
own scale, since at one scale everything else would vanish beside it).

Every facade is drawn by the real renderer from the real IR, at the same
pixels per metre, standing on one ground line, so the proportions compare.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.render.svg.render import _MARGIN_M, render  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.grammar import generate_cga  # noqa: E402
from buildings.typologies.soho.grammar import generate_soho  # noqa: E402
from buildings.typologies.soho.recipes import Programme, SohoSite  # noqa: E402

PX_PER_M = 26.0


def _styles():
    from buildings.typologies.amsterdam.grammar import CanalSite, generate_amsterdam
    from buildings.typologies.chicago.grammar import OfficeSite, generate_chicago
    from buildings.typologies.venice.grammar import PalazzoSite, generate_venice

    return [
        ("Amsterdam, 1625: step gable", generate_amsterdam(CanalSite(6.6, 1625, BuildingClass.COMFORTABLE))[0]),
        ("Amsterdam, 1670: neck gable", generate_amsterdam(CanalSite(7.2, 1670, BuildingClass.COMFORTABLE))[0]),
        ("Amsterdam, 1750: bell gable", generate_amsterdam(CanalSite(5.8, 1750, BuildingClass.ORDINARY))[0]),
        ("Venice, 1430: Gothic palazzo", generate_venice(PalazzoSite(19.0, 1430, BuildingClass.GRAND))[0]),
        ("Chicago, 1895: base, shaft, capital", generate_chicago(OfficeSite(20.5, 1895, BuildingClass.COMFORTABLE))[0]),
    ]

STREET = [
    ("Federal rowhouse, 1825", generate_soho(SohoSite(1, 1825, Programme.DWELLING, BuildingClass.ORDINARY))[0]),
    ("Cast-iron loft, 1858", generate_soho(SohoSite(1, 1858, Programme.LOFT, BuildingClass.COMFORTABLE))[0]),
    ("Cast-iron loft, 1872, three lots", generate_soho(SohoSite(3, 1872, Programme.LOFT, BuildingClass.GRAND))[0]),
    ("Brick store-and-loft, 1886", generate_soho(SohoSite(1, 1886, Programme.LOFT, BuildingClass.ORDINARY))[0]),
    ("Brick store-and-loft, 1888, two lots", generate_soho(SohoSite(2, 1888, Programme.LOFT, BuildingClass.ORDINARY, seed=2))[0]),
    (
        "For contrast: Paris, 1865",
        generate_cga(SiteContext(20.0, 14.0, 14.0, 1865, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=8))[0],
    ),
]


def _more_styles():
    from buildings.typologies.deco.grammar import TowerSite, generate_deco
    from buildings.typologies.georgian.grammar import TerraceSite, generate_georgian
    from buildings.typologies.kyoto.grammar import MachiyaSite, generate_kyoto
    from buildings.typologies.modernist.grammar import VillaSite, generate_modernist

    return [
        ("London, 1790: Georgian terrace", generate_georgian(TerraceSite(7.6, 1790, BuildingClass.COMFORTABLE))[0]),
        ("Kyoto, 1890: machiya", generate_kyoto(MachiyaSite(6.4, 1890, BuildingClass.ORDINARY))[0]),
        ("Poissy, 1929: Corbusian block", generate_modernist(VillaSite(19.0, 1929, BuildingClass.COMFORTABLE))[0]),
        ("New York, 1929: setback tower (own scale)", generate_deco(TowerSite(36.0, 18.0, 1929, BuildingClass.GRAND))[0]),
    ]


def _sf_normandy():
    from buildings.typologies.normandy.grammar import NormandySite, generate_normandy
    from buildings.typologies.victorian.grammar import VictorianSite, generate_victorian

    return [
        ("San Francisco, 1875: Italianate", generate_victorian(VictorianSite(1875, BuildingClass.ORDINARY, 0))[0]),
        ("San Francisco, 1885: Stick", generate_victorian(VictorianSite(1885, BuildingClass.ORDINARY, 1))[0]),
        ("San Francisco, 1892: Queen Anne", generate_victorian(VictorianSite(1892, BuildingClass.ORDINARY, 2))[0]),
        ("San Francisco, 1895: Queen Anne, turret", generate_victorian(VictorianSite(1895, BuildingClass.GRAND, 3))[0]),
        ("Rouen, 1620: jettied town house", generate_normandy(NormandySite("town", 1620, BuildingClass.COMFORTABLE))[0]),
        ("Pays d'Auge, 1700: thatched house", generate_normandy(NormandySite("country", 1700, BuildingClass.ORDINARY))[0]),
    ]


def sheet(street=None, *, own_scale: frozenset[str] = frozenset()) -> str:
    panels = []
    for caption, building in street or STREET:
        scale = PX_PER_M if caption not in own_scale else 900.0 / float(building.props["h"])
        width_px = (float(building.props["w"]) + 2 * _MARGIN_M) * scale
        svg = render(building, width_px=int(round(width_px)))
        w, h = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups())
        panels.append((caption, svg, w, h))
    gap, top, bottom = 18, 30, 40
    total_w = sum(p[2] for p in panels) + gap * (len(panels) + 1)
    max_h = max(p[3] for p in panels)
    total_h = max_h + top + bottom
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {total_h:.0f}">',
        f'<rect width="{total_w:.0f}" height="{total_h:.0f}" fill="#ffffff"/>',
    ]
    x = gap
    for caption, svg, w, h in panels:
        y = top + (max_h - h)  # stand every building on the same ground line
        out.append(svg.replace("<svg ", f'<svg x="{x:.1f}" y="{y:.1f}" ', 1))
        out.append(
            f'<text x="{x + w / 2:.1f}" y="{top + max_h + 24:.1f}" font-size="13" text-anchor="middle" '
            f'font-family="Helvetica, Arial" fill="#111827">{caption}</text>'
        )
        x += w + gap
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    styles = "--styles" in argv
    more = "--more" in argv
    sfn = "--sf-normandy" in argv
    argv = [a for a in argv if a not in ("--styles", "--more", "--sf-normandy")]
    out = Path(argv[0]) if argv else ROOT / "dev" / "logs"
    out.mkdir(parents=True, exist_ok=True)
    if sfn:
        path = out / "sf_normandy_sheet.svg"
        path.write_text(sheet(_sf_normandy()))
    elif more:
        street = _more_styles()
        path = out / "more_styles_sheet.svg"
        path.write_text(sheet(street, own_scale=frozenset({street[-1][0]})))
    else:
        path = out / ("styles_sheet.svg" if styles else "soho_sheet.svg")
        path.write_text(sheet(_styles() if styles else None))
    print(path)
    if shutil.which("rsvg-convert"):
        png = path.with_suffix(".png")
        subprocess.run(["rsvg-convert", "-b", "white", str(path), "-o", str(png)], check=True)
        print(png)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
