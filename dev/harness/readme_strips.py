#!/usr/bin/env python3
"""The README's strips: six buildings from each ruleset, one scale per strip.

Run:  python3 dev/harness/readme_strips.py [OUT_DIR]     (default docs/strips)

Each strip shows six situations of one style side by side, standing on one
ground line at one scale, so what changes between them -- date, money, width,
street -- reads as proportion. Every facade is drawn by the real renderer from
the real IR. Writes ``<style>.png`` where ``rsvg-convert`` is on the PATH, and
``<style>.svg`` otherwise.
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
from buildings.site import BuildingClass as K  # noqa: E402
from buildings.site import GroundProgramme as G  # noqa: E402
from buildings.site import SiteContext  # noqa: E402

STRIP_H = 360.0  # px for the tallest building of a strip


def _paris(gen):
    return [
        ("1835, 9 m street, modest", gen(SiteContext(9.0, 9.0, 12.0, 1835, K.MODEST, G.RESIDENTIAL, seed=1))[0]),
        ("1865, 20 m boulevard, comfortable shop", gen(SiteContext(20.0, 14.0, 14.0, 1865, K.COMFORTABLE, G.SHOP, seed=8))[0]),
        ("1868, 30 m avenue, grand", gen(SiteContext(30.0, 20.0, 18.0, 1868, K.GRAND, G.CARRIAGE, seed=3))[0]),
        ("1875, 14 m street, ordinary", gen(SiteContext(14.0, 12.0, 13.0, 1875, K.ORDINARY, G.RESIDENTIAL, seed=6))[0]),
        ("1890, 12 m street, modest shop", gen(SiteContext(12.0, 10.0, 12.0, 1890, K.MODEST, G.SHOP, seed=4))[0]),
        ("1900, 24 m street, grand cafe", gen(SiteContext(24.0, 16.0, 16.0, 1900, K.GRAND, G.CAFE, seed=9))[0]),
    ]


def strips():
    from buildings.typologies.amsterdam.grammar import CanalSite, generate_amsterdam
    from buildings.typologies.chicago.grammar import OfficeSite, generate_chicago
    from buildings.typologies.deco.grammar import TowerSite, generate_deco
    from buildings.typologies.georgian.grammar import TerraceSite, generate_georgian
    from buildings.typologies.kyoto.grammar import MachiyaSite, generate_kyoto
    from buildings.typologies.modernist.grammar import VillaSite, generate_modernist
    from buildings.typologies.normandy.grammar import NormandySite, generate_normandy
    from buildings.typologies.paris.generate import generate
    from buildings.typologies.paris.rules import generate_haussmann
    from buildings.typologies.soho.grammar import generate_soho
    from buildings.typologies.soho.recipes import Programme as P
    from buildings.typologies.soho.recipes import SohoSite
    from buildings.typologies.venice.grammar import PalazzoSite, generate_venice
    from buildings.typologies.victorian.grammar import VictorianSite, generate_victorian

    a, c, d, g = generate_amsterdam, generate_chicago, generate_deco, generate_georgian
    return {
        "paris_measured": ("Paris, measured generator (Python)", _paris(generate)),
        "haussmann": ("Paris as a rule file (haussmann.toml)", _paris(generate_haussmann)),
        "amsterdam": ("Amsterdam canal house (amsterdam.toml)", [
            ("1620, step gable", a(CanalSite(6.6, 1620, K.COMFORTABLE))[0]),
            ("1635, narrow, step gable", a(CanalSite(5.2, 1635, K.ORDINARY))[0]),
            ("1670, neck gable", a(CanalSite(7.2, 1670, K.COMFORTABLE))[0]),
            ("1700, wide, neck gable", a(CanalSite(8.0, 1700, K.GRAND))[0]),
            ("1750, bell gable", a(CanalSite(5.8, 1750, K.ORDINARY))[0]),
            ("1800, straight cornice", a(CanalSite(7.0, 1800, K.ORDINARY))[0]),
        ]),
        "chicago": ("Chicago School office block (chicago.toml)", [
            ("1890, modest, 3 bays", c(OfficeSite(20.5, 1890, K.MODEST, seed=0))[0]),
            ("1892, ordinary", c(OfficeSite(20.5, 1892, K.ORDINARY, seed=1))[0]),
            ("1895, comfortable", c(OfficeSite(20.5, 1895, K.COMFORTABLE, seed=2))[0]),
            ("1898, grand, 4 bays", c(OfficeSite(27.0, 1898, K.GRAND, seed=3))[0]),
            ("1905, comfortable, 2 bays", c(OfficeSite(14.5, 1905, K.COMFORTABLE, seed=4))[0]),
            ("1908, grand, 5 bays", c(OfficeSite(33.0, 1908, K.GRAND, seed=5))[0]),
        ]),
        "deco": ("New York setback tower, 1916 zoning (deco.toml)", [
            ("9 m street, modest", d(TowerSite(30.0, 9.0, 1927, K.MODEST, seed=0))[0]),
            ("12 m street, ordinary", d(TowerSite(30.0, 12.0, 1928, K.ORDINARY, seed=1))[0]),
            ("18 m street, comfortable", d(TowerSite(36.0, 18.0, 1929, K.COMFORTABLE, seed=2))[0]),
            ("18 m street, grand", d(TowerSite(36.0, 18.0, 1929, K.GRAND, seed=3))[0]),
            ("24 m street, grand", d(TowerSite(42.0, 24.0, 1930, K.GRAND, seed=4))[0]),
            ("30 m street, grand, wide lot", d(TowerSite(50.0, 30.0, 1931, K.GRAND, seed=5))[0]),
        ]),
        "georgian": ("Georgian London terrace (georgian.toml)", [
            ("1760, 2 bays", g(TerraceSite(5.6, 1760, K.MODEST))[0]),
            ("1775, 3 bays", g(TerraceSite(7.0, 1775, K.ORDINARY))[0]),
            ("1790, 3 bays", g(TerraceSite(7.6, 1790, K.COMFORTABLE))[0]),
            ("1800, 3 bays, wider", g(TerraceSite(8.6, 1800, K.COMFORTABLE))[0]),
            ("1810, 4 bays", g(TerraceSite(10.2, 1810, K.GRAND))[0]),
            ("1825, 5 bays", g(TerraceSite(12.0, 1825, K.GRAND))[0]),
        ]),
        "kyoto": ("Kyoto machiya (kyoto.toml)", [
            ("4.5 m, 1850", generate_kyoto(MachiyaSite(4.5, 1850, K.MODEST))[0]),
            ("5.5 m, 1865", generate_kyoto(MachiyaSite(5.5, 1865, K.ORDINARY))[0]),
            ("6.4 m, 1890", generate_kyoto(MachiyaSite(6.4, 1890, K.ORDINARY))[0]),
            ("7.5 m, 1895", generate_kyoto(MachiyaSite(7.5, 1895, K.COMFORTABLE))[0]),
            ("9.0 m, 1900", generate_kyoto(MachiyaSite(9.0, 1900, K.COMFORTABLE))[0]),
            ("11 m, 1910", generate_kyoto(MachiyaSite(11.0, 1910, K.GRAND))[0]),
        ]),
        "modernist": ("Corbusian block (modernist.toml)", [
            ("12 m, modest", generate_modernist(VillaSite(12.0, 1927, K.MODEST))[0]),
            ("15 m, ordinary", generate_modernist(VillaSite(15.0, 1928, K.ORDINARY))[0]),
            ("19 m, comfortable", generate_modernist(VillaSite(19.0, 1929, K.COMFORTABLE))[0]),
            ("22 m, comfortable", generate_modernist(VillaSite(22.0, 1930, K.COMFORTABLE))[0]),
            ("24 m, grand", generate_modernist(VillaSite(24.0, 1931, K.GRAND))[0]),
            ("30 m, grand", generate_modernist(VillaSite(30.0, 1933, K.GRAND))[0]),
        ]),
        "normandy": ("Normandy half-timbered house (normandy.toml)", [
            ("town, 1550, narrow", generate_normandy(NormandySite("town", 1550, K.ORDINARY, width=5.2))[0]),
            ("town, 1620", generate_normandy(NormandySite("town", 1620, K.COMFORTABLE))[0]),
            ("town, 1650, wide", generate_normandy(NormandySite("town", 1650, K.GRAND, width=8.0))[0]),
            ("country, 1680, small", generate_normandy(NormandySite("country", 1680, K.MODEST, width=10.0))[0]),
            ("country, 1700", generate_normandy(NormandySite("country", 1700, K.ORDINARY))[0]),
            ("country, 1750, long", generate_normandy(NormandySite("country", 1750, K.COMFORTABLE, width=18.0))[0]),
        ]),
        "soho": ("SoHo, New York (soho.toml)", [
            ("Federal rowhouse, 1825", generate_soho(SohoSite(1, 1825, P.DWELLING, K.ORDINARY))[0]),
            ("cast-iron loft, 1858", generate_soho(SohoSite(1, 1858, P.LOFT, K.COMFORTABLE))[0]),
            ("cast-iron loft, 1866, 2 lots", generate_soho(SohoSite(2, 1866, P.LOFT, K.GRAND))[0]),
            ("cast-iron loft, 1875, 2 lots", generate_soho(SohoSite(2, 1875, P.LOFT, K.COMFORTABLE))[0]),
            ("brick store-and-loft, 1886", generate_soho(SohoSite(1, 1886, P.LOFT, K.ORDINARY))[0]),
            ("brick store-and-loft, 1890, 2 lots", generate_soho(SohoSite(2, 1890, P.LOFT, K.MODEST, seed=2))[0]),
        ]),
        "venice": ("Venetian Gothic palazzo (venice.toml)", [
            ("11 m, ordinary", generate_venice(PalazzoSite(11.0, 1380, K.ORDINARY))[0]),
            ("14 m, ordinary", generate_venice(PalazzoSite(14.0, 1400, K.ORDINARY))[0]),
            ("16 m, comfortable", generate_venice(PalazzoSite(16.0, 1410, K.COMFORTABLE))[0]),
            ("19 m, grand", generate_venice(PalazzoSite(19.0, 1430, K.GRAND))[0]),
            ("22 m, grand", generate_venice(PalazzoSite(22.0, 1440, K.GRAND))[0]),
            ("25 m, grand", generate_venice(PalazzoSite(25.0, 1450, K.GRAND))[0]),
        ]),
        "victorian": ("San Francisco Victorian (victorian.toml)", [
            ("Italianate, 1872", generate_victorian(VictorianSite(1872, K.ORDINARY, 0))[0]),
            ("Italianate, 1878", generate_victorian(VictorianSite(1878, K.COMFORTABLE, 1))[0]),
            ("Stick, 1883", generate_victorian(VictorianSite(1883, K.ORDINARY, 2))[0]),
            ("Stick, 1886", generate_victorian(VictorianSite(1886, K.COMFORTABLE, 3))[0]),
            ("Queen Anne, 1892", generate_victorian(VictorianSite(1892, K.ORDINARY, 0))[0]),
            ("Queen Anne, turret, 1895", generate_victorian(VictorianSite(1895, K.GRAND, 1))[0]),
        ]),
    }


def strip(title: str, buildings) -> str:
    tallest = max(float(b.props["h"]) for _c, b in buildings)
    px_per_m = STRIP_H / (tallest + 3.0)
    panels = []
    for caption, building in buildings:
        width_px = (float(building.props["w"]) + 2 * _MARGIN_M) * px_per_m
        svg = render(building, width_px=max(1, int(round(width_px))))
        w, h = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups())
        panels.append((caption, svg, w, h))
    gap, top, bottom = 14, 34, 30
    # Each building gets a slot at least as wide as its caption, so a narrow
    # tower's label does not run into its neighbour's.
    slots = [max(w, len(caption) * 6.4 + 8) for caption, _svg, w, _h in panels]
    total_w = sum(slots) + gap * (len(panels) + 1)
    max_h = max(p[3] for p in panels)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{max_h + top + bottom:.0f}" '
        f'viewBox="0 0 {total_w:.0f} {max_h + top + bottom:.0f}">',
        f'<rect width="{total_w:.0f}" height="{max_h + top + bottom:.0f}" fill="#ffffff"/>',
        f'<text x="{gap}" y="22" font-size="15" font-weight="600" font-family="Helvetica, Arial" fill="#111827">{title}</text>',
    ]
    x = gap
    for (caption, svg, w, h), slot in zip(panels, slots):
        out.append(svg.replace("<svg ", f'<svg x="{x + (slot - w) / 2:.1f}" y="{top + max_h - h:.1f}" ', 1))
        out.append(
            f'<text x="{x + slot / 2:.1f}" y="{top + max_h + 20:.1f}" font-size="11" text-anchor="middle" '
            f'font-family="Helvetica, Arial" fill="#374151">{caption}</text>'
        )
        x += slot + gap
    out.append("</svg>")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else ROOT / "docs" / "strips"
    out.mkdir(parents=True, exist_ok=True)
    for name, (title, buildings) in strips().items():
        path = out / f"{name}.svg"
        path.write_text(strip(title, buildings))
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-b", "white", str(path), "-o", str(path.with_suffix(".png"))], check=True)
            path.unlink()  # the PNG is what the README shows; the SVG is large
            path = path.with_suffix(".png")
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
