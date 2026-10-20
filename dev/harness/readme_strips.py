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

    from buildings.typologies.baroque.grammar import BaroqueSite, generate_baroque
    from buildings.typologies.beaux_arts.grammar import BeauxArtsSite, generate_beaux_arts
    from buildings.typologies.brownstone.grammar import BrownstoneSite, generate_brownstone
    from buildings.typologies.cairo.grammar import CairoSite, generate_cairo
    from buildings.typologies.classical.grammar import ClassicalSite, generate_classical
    from buildings.typologies.gothic_cathedral.grammar import CathedralSite, generate_gothic_cathedral
    from buildings.typologies.pagoda.grammar import PagodaSite, generate_pagoda
    from buildings.typologies.pombaline.grammar import PombalineSite, generate_pombaline
    from buildings.typologies.renaissance.grammar import RenaissanceSite, generate_renaissance
    from buildings.typologies.romanesque.grammar import RomanesqueSite, generate_romanesque
    from buildings.typologies.sanaa.grammar import SanaaSite, generate_sanaa
    from buildings.typologies.second_empire.grammar import SecondEmpireSite, generate_second_empire
    from buildings.typologies.shophouse.grammar import ShophouseSite, generate_shophouse
    from buildings.typologies.soviet_panel.grammar import PanelSite, generate_soviet_panel
    from buildings.typologies.spanish_colonial.grammar import SpanishSite, generate_spanish_colonial
    from buildings.typologies.tudor.grammar import TudorSite, generate_tudor
    a, c, d, g = generate_amsterdam, generate_chicago, generate_deco, generate_georgian
    return {
        "paris_measured": ("Paris, measured generator (Python)", _paris(generate)),
        "haussmann": ("Paris as a rule file (haussmann.toml)", _paris(generate_haussmann)),
        "amsterdam": ("Amsterdam canal house (amsterdam.toml)", [
            ("1620, step gable", a(CanalSite(6.6, 1620, K.COMFORTABLE))[0]),
            ("1650, raised neck gable", a(CanalSite(7.0, 1650, K.ORDINARY, seed=1))[0]),
            ("1690, neck gable, tarred", a(CanalSite(7.2, 1690, K.COMFORTABLE, seed=1))[0]),
            ("1740, bell gable", a(CanalSite(5.8, 1740, K.ORDINARY, seed=4))[0]),
            ("1760, 5 bays, grand, crest", a(CanalSite(11.0, 1760, K.GRAND, seed=3))[0]),
            ("1800, cornice and dormer", a(CanalSite(7.0, 1800, K.ORDINARY, seed=0))[0]),
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
            ("1380, 11 m, ordinary", generate_venice(PalazzoSite(11.0, 1380, K.ORDINARY, seed=3))[0]),
            ("1400, 14 m, ordinary, attic", generate_venice(PalazzoSite(14.0, 1400, K.ORDINARY, seed=2))[0]),
            ("1410, 16 m, comfortable", generate_venice(PalazzoSite(16.0, 1410, K.COMFORTABLE, seed=0))[0]),
            ("1430, 19 m, grand, tracery", generate_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=4))[0]),
            ("1440, 22 m, grand, two gates", generate_venice(PalazzoSite(22.0, 1440, K.GRAND, seed=0))[0]),
            ("1450, 25 m, grand, third floor", generate_venice(PalazzoSite(25.0, 1450, K.GRAND, seed=5))[0]),
        ]),
        "victorian": ("San Francisco Victorian (victorian.toml)", [
            ("Italianate, 1872, 25 ft", generate_victorian(VictorianSite(1872, K.ORDINARY, 0))[0]),
            ("Italianate, 1878, 20 ft, mirrored", generate_victorian(VictorianSite(1878, K.MODEST, 1, 6.1))[0]),
            ("Stick, 1883, double bay, 30 ft", generate_victorian(VictorianSite(1883, K.COMFORTABLE, 2, 9.1))[0]),
            ("Stick, 1886, side yard", generate_victorian(VictorianSite(1886, K.ORDINARY, 3, 8.2))[0]),
            ("Queen Anne, 1892, extra floor", generate_victorian(VictorianSite(1892, K.ORDINARY, 5))[0]),
            ("Queen Anne, 1895, turret", generate_victorian(VictorianSite(1895, K.GRAND, 1))[0]),
        ]),
        "renaissance": ("Renaissance palazzo (renaissance.toml)", [
            ("1446, Rucellai, 7 bays", generate_renaissance(RenaissanceSite(24.0, 1446, K.ORDINARY, seed=0))[0]),
            ("1450, Rucellai, modest", generate_renaissance(RenaissanceSite(11.5, 1450, K.MODEST, seed=2))[0]),
            ("1445, Medici, grand", generate_renaissance(RenaissanceSite(32.0, 1445, K.GRAND, seed=1))[0]),
            ("1489, Strozzi, grand", generate_renaissance(RenaissanceSite(30.0, 1489, K.GRAND, seed=3))[0]),
            ("1520, Roman, comfortable", generate_renaissance(RenaissanceSite(22.0, 1520, K.COMFORTABLE, seed=0))[0]),
            ("1540, Farnese, grand", generate_renaissance(RenaissanceSite(44.0, 1540, K.GRAND, seed=5))[0]),
        ]),
        "gothic_cathedral": ("Gothic cathedral west front (gothic_cathedral.toml)", [
            ("1163, Notre-Dame, 41 m", generate_gothic_cathedral(CathedralSite(41.0, 1163, K.GRAND, seed=0))[0]),
            ("1145, spires, 30 m", generate_gothic_cathedral(CathedralSite(30.0, 1145, K.ORDINARY, seed=2))[0]),
            ("1220, pinnacles, 46 m", generate_gothic_cathedral(CathedralSite(46.0, 1220, K.GRAND, seed=0))[0]),
            ("1250, flat, 38 m, modest", generate_gothic_cathedral(CathedralSite(38.0, 1250, K.MODEST, seed=3))[0]),
            ("1277, one spire, 40 m", generate_gothic_cathedral(CathedralSite(40.0, 1277, K.COMFORTABLE, seed=2))[0]),
            ("1248, two spires, 60 m", generate_gothic_cathedral(CathedralSite(60.0, 1248, K.GRAND, seed=1))[0]),
        ]),
        "romanesque": ("Romanesque church front (romanesque.toml)", [
            ("1118, Pisan, 35 m, grand", generate_romanesque(RomanesqueSite(35.0, 1118, K.GRAND, seed=0))[0]),
            ("1143, Pisan, 22 m", generate_romanesque(RomanesqueSite(22.0, 1143, K.COMFORTABLE, seed=2))[0]),
            ("1160, Pisan, 14 m, parish", generate_romanesque(RomanesqueSite(14.0, 1160, K.ORDINARY, seed=4))[0]),
            ("1110, battlements, 30 m", generate_romanesque(RomanesqueSite(30.0, 1110, K.COMFORTABLE, seed=1))[0]),
            ("1130, helm roofs, 28 m", generate_romanesque(RomanesqueSite(28.0, 1130, K.GRAND, seed=3))[0]),
            ("1150, battlements, 18 m", generate_romanesque(RomanesqueSite(18.0, 1150, K.MODEST, seed=5))[0]),
        ]),
        "baroque": ("Baroque church front (baroque.toml)", [
            ("1575, Gesu, 35 m, grand", generate_baroque(BaroqueSite(35.0, 1575, K.GRAND, seed=0))[0]),
            ("1590, Gesu type, 18 m", generate_baroque(BaroqueSite(18.0, 1590, K.ORDINARY, seed=1))[0]),
            ("1603, Susanna, 22 m", generate_baroque(BaroqueSite(22.0, 1603, K.COMFORTABLE, seed=0))[0]),
            ("1625, stepped, grand, dome", generate_baroque(BaroqueSite(30.0, 1625, K.GRAND, seed=3))[0]),
            ("1655, towers, dome, 40 m", generate_baroque(BaroqueSite(40.0, 1655, K.GRAND, seed=0))[0]),
            ("1680, broken, 20 m", generate_baroque(BaroqueSite(20.0, 1680, K.ORDINARY, seed=1))[0]),
        ]),
        "classical": ("Classical temple front and Greek Revival (classical.toml)", [
            ("447 BC, Doric octastyle, 31 m", generate_classical(ClassicalSite(31.0, -447, K.GRAND, seed=0))[0]),
            ("449 BC, Doric hexastyle, 14 m", generate_classical(ClassicalSite(14.0, -449, K.COMFORTABLE, seed=0))[0]),
            ("420 BC, Ionic tetrastyle, 8 m", generate_classical(ClassicalSite(8.0, -420, K.MODEST, seed=2))[0]),
            ("16 BC, Corinthian on a podium, 15 m", generate_classical(ClassicalSite(15.0, -16, K.COMFORTABLE, seed=4))[0]),
            ("1836, Doric custom house, 17 m", generate_classical(ClassicalSite(17.0, 1836, K.MODEST, seed=0))[0]),
            ("1852, Corinthian on a block, 40 m", generate_classical(ClassicalSite(40.0, 1852, K.COMFORTABLE, seed=5))[0]),
        ]),
        "second_empire": ("Second Empire civic block (second_empire.toml)", [
            ("1867, 22 m, ordinary", generate_second_empire(SecondEmpireSite(22.0, 1867, K.ORDINARY, seed=0))[0]),
            ("1869, 28 m, end pavilions", generate_second_empire(SecondEmpireSite(28.0, 1869, K.COMFORTABLE, seed=2))[0]),
            ("1872, 30 m, centre pavilion", generate_second_empire(SecondEmpireSite(30.0, 1872, K.MODEST, seed=1))[0]),
            ("1875, 36 m, comfortable", generate_second_empire(SecondEmpireSite(36.0, 1875, K.COMFORTABLE, seed=4))[0]),
            ("1878, 48 m, grand", generate_second_empire(SecondEmpireSite(48.0, 1878, K.GRAND, seed=3))[0]),
            ("1884, 60 m, grand", generate_second_empire(SecondEmpireSite(60.0, 1884, K.GRAND, seed=5))[0]),
        ]),
        "beaux_arts": ("Beaux-Arts and Renaissance Revival (beaux_arts.toml)", [
            ("1885, palazzo, 18 m", generate_beaux_arts(BeauxArtsSite(18.0, 1885, K.ORDINARY, seed=1))[0]),
            ("1890, palazzo, 26 m", generate_beaux_arts(BeauxArtsSite(26.0, 1890, K.COMFORTABLE, seed=2))[0]),
            ("1899, giant order, 24 m", generate_beaux_arts(BeauxArtsSite(24.0, 1899, K.COMFORTABLE, seed=0))[0]),
            ("1902, giant order, 40 m", generate_beaux_arts(BeauxArtsSite(40.0, 1902, K.GRAND, seed=3))[0]),
            ("1907, giant order, 48 m", generate_beaux_arts(BeauxArtsSite(48.0, 1907, K.COMFORTABLE, seed=4))[0]),
            ("1912, palazzo, 34 m", generate_beaux_arts(BeauxArtsSite(34.0, 1912, K.GRAND, seed=5))[0]),
        ]),
        "spanish_colonial": ("Spanish Colonial Revival (spanish_colonial.toml)", [
            ("1918, 12 m, modest", generate_spanish_colonial(SpanishSite(12.0, 1918, K.MODEST, seed=0))[0]),
            ("1922, 18 m, ordinary", generate_spanish_colonial(SpanishSite(18.0, 1922, K.ORDINARY, seed=1))[0]),
            ("1926, 22 m, tower", generate_spanish_colonial(SpanishSite(22.0, 1926, K.COMFORTABLE, seed=2))[0]),
            ("1929, 30 m, tower, loggia", generate_spanish_colonial(SpanishSite(30.0, 1929, K.COMFORTABLE, seed=3))[0]),
            ("1932, 38 m, grand", generate_spanish_colonial(SpanishSite(38.0, 1932, K.GRAND, seed=4))[0]),
            ("1936, 26 m, grand", generate_spanish_colonial(SpanishSite(26.0, 1936, K.GRAND, seed=5))[0]),
        ]),
        "brownstone": ("Brooklyn and Manhattan brownstone (brownstone.toml)", [
            ("Italianate, 1855, 20 ft", generate_brownstone(BrownstoneSite(1855, K.ORDINARY, 0, 6.1))[0]),
            ("Italianate, 1866, 25 ft", generate_brownstone(BrownstoneSite(1866, K.COMFORTABLE, 1, 7.6))[0]),
            ("Neo-Grec, 1874, 18 ft", generate_brownstone(BrownstoneSite(1874, K.MODEST, 2, 5.5))[0]),
            ("Neo-Grec, 1880, 22 ft, bay", generate_brownstone(BrownstoneSite(1880, K.ORDINARY, 3, 6.7))[0]),
            ("Romanesque, 1887, 20 ft", generate_brownstone(BrownstoneSite(1887, K.ORDINARY, 4, 6.1))[0]),
            ("Romanesque, 1890, 25 ft, bay", generate_brownstone(BrownstoneSite(1890, K.GRAND, 5, 7.6))[0]),
        ]),
        "sanaa": ("Sana'a tower house (sanaa.toml)", [
            ("7 m, modest", generate_sanaa(SanaaSite(7.0, 1850, K.MODEST, seed=0))[0]),
            ("8 m, ordinary, paired", generate_sanaa(SanaaSite(8.0, 1880, K.ORDINARY, seed=1))[0]),
            ("9 m, round qamariya, set back", generate_sanaa(SanaaSite(9.0, 1900, K.COMFORTABLE, seed=3))[0]),
            ("10 m, grand, one arch per pair", generate_sanaa(SanaaSite(10.0, 1870, K.GRAND, seed=2))[0]),
            ("8.5 m, Shibam manner", generate_sanaa(SanaaSite(8.5, 1880, K.ORDINARY, seed=4))[0]),
            ("12 m, grand, set-back mafraj", generate_sanaa(SanaaSite(12.0, 1910, K.GRAND, seed=7))[0]),
        ]),
        "cairo": ("Cairo house front (cairo.toml)", [
            ("8 m, modest", generate_cairo(CairoSite(8.0, 1650, K.MODEST, seed=0))[0]),
            ("11 m, ordinary, ablaq", generate_cairo(CairoSite(11.0, 1700, K.ORDINARY, seed=1))[0]),
            ("10 m, ordinary, Rashid brick", generate_cairo(CairoSite(10.0, 1750, K.ORDINARY, seed=2))[0]),
            ("14 m, comfortable, ablaq", generate_cairo(CairoSite(14.0, 1730, K.COMFORTABLE, seed=3))[0]),
            ("13 m, comfortable, Rashid", generate_cairo(CairoSite(13.0, 1780, K.COMFORTABLE, seed=5))[0]),
            ("18 m, grand (Suhaymi)", generate_cairo(CairoSite(18.0, 1648, K.GRAND, seed=4))[0]),
        ]),
        "shophouse": ("Straits shophouse (shophouse.toml)", [
            ("1845, early", generate_shophouse(ShophouseSite(4.6, 1845, K.MODEST, seed=0))[0]),
            ("1875, southern Chinese, row of 2", generate_shophouse(ShophouseSite(5.0, 1875, K.ORDINARY, seed=1, units=2))[0]),
            ("1900, early Straits Eclectic", generate_shophouse(ShophouseSite(5.4, 1900, K.ORDINARY, seed=2))[0]),
            ("1920, late Straits Eclectic", generate_shophouse(ShophouseSite(5.8, 1920, K.GRAND, seed=3))[0]),
            ("1938, Art Deco, row of 3", generate_shophouse(ShophouseSite(4.8, 1938, K.COMFORTABLE, seed=4, units=3))[0]),
            ("1955, early modern", generate_shophouse(ShophouseSite(6.0, 1955, K.ORDINARY, seed=5))[0]),
        ]),
        "pagoda": ("Pagoda (pagoda.toml)", [
            ("4.5 m, three tiers", generate_pagoda(PagodaSite(4.5, 730, K.MODEST, seed=0))[0]),
            ("6.4 m, five tiers (Horyu-ji)", generate_pagoda(PagodaSite(6.4, 700, K.ORDINARY, seed=1))[0]),
            ("8.6 m, grand, mokoshi", generate_pagoda(PagodaSite(8.6, 826, K.GRAND, seed=3))[0]),
            ("9 m, Chinese brick, 7 tiers", generate_pagoda(PagodaSite(9.0, 652, K.ORDINARY, seed=2))[0]),
            ("10 m, seven tiers", generate_pagoda(PagodaSite(10.0, 1644, K.COMFORTABLE, seed=4))[0]),
            ("12 m, Chinese brick, 13 tiers", generate_pagoda(PagodaSite(12.0, 707, K.GRAND, seed=5))[0]),
        ]),
        "pombaline": ("Lisbon Pombaline building (pombaline.toml)", [
            ("rua nobre, 1765, grand", generate_pombaline(PombalineSite(13.0, 1765, K.GRAND, "nobre", 0))[0]),
            ("rua nobre, 1780, comfortable", generate_pombaline(PombalineSite(10.5, 1780, K.COMFORTABLE, "nobre", 1))[0]),
            ("secondary street, 1790", generate_pombaline(PombalineSite(9.0, 1790, K.ORDINARY, "secondary", 2))[0]),
            ("secondary, 1860, azulejos", generate_pombaline(PombalineSite(8.0, 1860, K.ORDINARY, "secondary", 4))[0]),
            ("alley, 1800, modest", generate_pombaline(PombalineSite(6.0, 1800, K.MODEST, "alley", 3))[0]),
            ("rua nobre, 1885, raised", generate_pombaline(PombalineSite(11.5, 1885, K.COMFORTABLE, "nobre", 5))[0]),
        ]),
        "soviet_panel": ("Soviet panel housing (soviet_panel.toml)", [
            ("K-7, 1960, 2 sections", generate_soviet_panel(PanelSite(2, 1960, K.MODEST, 0))[0]),
            ("1-464, 1966, 2 sections", generate_soviet_panel(PanelSite(2, 1966, K.MODEST, 1))[0]),
            ("1-464, 1969, 3 sections", generate_soviet_panel(PanelSite(3, 1969, K.ORDINARY, 2))[0]),
            ("II-49, 1975, 9 floors", generate_soviet_panel(PanelSite(2, 1975, K.ORDINARY, 3))[0]),
            ("P-44, 1982, 17-floor tower", generate_soviet_panel(PanelSite(1, 1982, K.COMFORTABLE, 4))[0]),
            ("P-44, 1988, 14 floors", generate_soviet_panel(PanelSite(2, 1988, K.ORDINARY, 5))[0]),
        ]),
        "tudor": ("English Tudor house (tudor.toml)", [
            ("cottage, 1540", generate_tudor(TudorSite("cottage", 1540, K.MODEST, 0))[0]),
            ("town house, 1560", generate_tudor(TudorSite("town", 1560, K.ORDINARY, 1))[0]),
            ("town house, 1590, two gables", generate_tudor(TudorSite("town", 1590, K.COMFORTABLE, 2, width=10.0))[0]),
            ("manor, 1570", generate_tudor(TudorSite("manor", 1570, K.GRAND, 3))[0]),
            ("cottage, 1600, wide", generate_tudor(TudorSite("cottage", 1600, K.ORDINARY, 4, width=13.0))[0]),
            ("Tudor Revival, 1895", generate_tudor(TudorSite("town", 1895, K.COMFORTABLE, 5))[0]),
        ]),
    }


def _deco_family():
    """The deco family by programme, Miami, the movie palace, Byzantine Venice."""
    from buildings.typologies.deco.grammar import DecoSite, generate_deco
    from buildings.typologies.miami_deco.grammar import MiamiSite, generate_miami_deco
    from buildings.typologies.movie_palace.grammar import PalaceSite, generate_movie_palace
    from buildings.typologies.venice.grammar import PalazzoSite, generate_venice

    def g(*a, **k):
        return generate_deco(DecoSite(*a, **k))[0]

    m = lambda site: generate_miami_deco(site)[0]  # noqa: E731
    p = lambda site: generate_movie_palace(site)[0]  # noqa: E731
    v = lambda site: generate_venice(site)[0]  # noqa: E731
    return {
        "deco_civic": ("Art Deco civic: courthouse, city hall, federal building (civic.toml)", [
            ("1931, county courthouse, ordinary", g("civic", 30.0, 1931, K.ORDINARY, seed=0)),
            ("1936, county courthouse, modest", g("civic", 26.0, 1936, K.MODEST, seed=1)),
            ("1937, federal building, comfortable", g("civic", 38.0, 1937, K.COMFORTABLE, seed=2)),
            ("1939, courthouse, comfortable", g("civic", 34.0, 1939, K.COMFORTABLE, seed=3)),
            ("1937, federal building, grand", g("civic", 42.0, 1937, K.GRAND, seed=0)),
            ("1931, city hall, grand", g("civic", 56.0, 1931, K.GRAND, seed=1)),
        ]),
        "deco_commercial": ("Art Deco commercial: taxpayer, store, department store (commercial.toml)", [
            ("1929, taxpayer, modest", g("commercial", 15.0, 1929, K.MODEST, seed=0)),
            ("1938, taxpayer, ordinary", g("commercial", 18.0, 1938, K.ORDINARY, seed=1)),
            ("1931, variety store", g("commercial", 22.0, 1931, K.COMFORTABLE, seed=2)),
            ("1937, store, streamline", g("commercial", 26.0, 1937, K.ORDINARY, seed=3)),
            ("1929, department store", g("commercial", 48.0, 1929, K.GRAND, seed=0)),
            ("1934, department store, corner", g("commercial", 44.0, 1934, K.GRAND, seed=1)),
        ]),
        "deco_office": ("Art Deco office block (office.toml)", [
            ("1927, modest", g("office", 18.0, 1927, K.MODEST, seed=0)),
            ("1929, ordinary", g("office", 22.0, 1929, K.ORDINARY, seed=1)),
            ("1929, comfortable, granite", g("office", 26.0, 1929, K.COMFORTABLE, seed=2)),
            ("1935, comfortable, streamline", g("office", 26.0, 1935, K.COMFORTABLE, seed=3)),
            ("1930, grand", g("office", 30.0, 1930, K.GRAND, seed=1)),
            ("1927, grand, wings", g("office", 46.0, 1927, K.GRAND, seed=0)),
        ]),
        "deco_institutional": ("Art Deco institutional: school, hospital (institutional.toml)", [
            ("1930, school, modest", g("institutional", 28.0, 1930, K.MODEST, seed=0)),
            ("1938, school, ordinary", g("institutional", 32.0, 1938, K.ORDINARY, seed=1)),
            ("1931, school, comfortable", g("institutional", 36.0, 1931, K.COMFORTABLE, seed=2)),
            ("1936, hospital, comfortable", g("institutional", 46.0, 1936, K.COMFORTABLE, seed=3)),
            ("1929, hospital, grand", g("institutional", 52.0, 1929, K.GRAND, seed=0)),
            ("1940, hospital, grand", g("institutional", 50.0, 1940, K.GRAND, seed=2)),
        ]),
        "deco_religious_works": ("Art Deco churches and public works (religious.toml, works.toml)", [
            ("church, 1930, ordinary", g("religious", 18.0, 1930, K.ORDINARY, seed=1)),
            ("church, 1937, modest", g("religious", 16.0, 1937, K.MODEST, seed=2)),
            ("church, 1929, grand", g("religious", 34.0, 1929, K.GRAND, seed=0)),
            ("intake tower, 1935", g("works", 12.0, 1935, K.COMFORTABLE, seed=0)),
            ("pumping station, 1932", g("works", 30.0, 1932, K.ORDINARY, seed=0)),
            ("power station, 1938, grand", g("works", 44.0, 1938, K.GRAND, seed=2)),
        ]),
        "miami_deco": ("Miami Beach Art Deco hotel (miami_deco.toml)", [
            ("1932, 15 m, ordinary", m(MiamiSite(15.0, 1932, K.ORDINARY, seed=0))),
            ("1935, 18 m, comfortable", m(MiamiSite(18.0, 1935, K.COMFORTABLE, seed=3))),
            ("1936, 16 m, modest", m(MiamiSite(16.0, 1936, K.MODEST, seed=1))),
            ("1937, 20 m, corner", m(MiamiSite(20.0, 1937, K.ORDINARY, seed=2, corner=True))),
            ("1939, 22 m, grand", m(MiamiSite(22.0, 1939, K.GRAND, seed=4))),
            ("1941, 30 m, grand, corner", m(MiamiSite(30.0, 1941, K.GRAND, seed=5, corner=True))),
        ]),
        "movie_palace": ("Art Deco movie palace (movie_palace.toml)", [
            ("1929, 13 m, modest", p(PalaceSite(13.0, 1929, K.MODEST, seed=0))),
            ("1930, 16 m, ordinary", p(PalaceSite(16.0, 1930, K.ORDINARY, seed=4))),
            ("1931, 30 m, comfortable", p(PalaceSite(30.0, 1931, K.COMFORTABLE, seed=2))),
            ("1931, 40 m, grand", p(PalaceSite(40.0, 1931, K.GRAND, seed=3))),
            ("1936, 26 m, ordinary", p(PalaceSite(26.0, 1936, K.ORDINARY, seed=7))),
            ("1939, 44 m, grand", p(PalaceSite(44.0, 1939, K.GRAND, seed=5))),
        ]),
        "venice_byzantine": ("Venetian palazzo: Veneto-Byzantine before 1300, Gothic after (venice.toml)", [
            ("1200, 12 m (Ca' da Mosto)", v(PalazzoSite(12.0, 1200, K.ORDINARY, seed=0))),
            ("1250, 16 m, comfortable", v(PalazzoSite(16.0, 1250, K.COMFORTABLE, seed=1))),
            ("1230, 22 m, comfortable (Loredan type)", v(PalazzoSite(22.0, 1230, K.COMFORTABLE, seed=2))),
            ("1225, 30 m, grand (Fondaco)", v(PalazzoSite(30.0, 1225, K.GRAND, seed=0))),
            ("1380, 11 m, Gothic", v(PalazzoSite(11.0, 1380, K.ORDINARY, seed=3))),
            ("1430, 19 m, Gothic", v(PalazzoSite(19.0, 1430, K.GRAND, seed=4))),
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
    for name, (title, buildings) in {**strips(), **_deco_family()}.items():
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
