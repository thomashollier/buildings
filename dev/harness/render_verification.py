#!/usr/bin/env python3
"""Generate reference SVGs for visual verification and regression testing.

Renders a harness building facade and a 10-parcel corner block, both at 1865 Paris
(Comfortable class, commercial ground floor). These are the canonical test cases
for visual inspection of the renderer output.

The SVGs are written to dev/logs/ for comparison with git, screenshots, or previous
renders during iterative development of the qualification and rendering layers.

Exit 0 = success.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.block.block import GroundRegime, plan_block, solve_block  # noqa: E402
from buildings.render.svg.render import render  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402

LOGS = ROOT / "dev" / "logs"


def render_facade() -> None:
    """Render the harness building: 1865 Paris, comfortable class, shop ground floor."""
    site = SiteContext(
        street_width=20.0,
        parcel_width=12.0,
        parcel_depth=14.0,
        year=1865,
        klass=BuildingClass.COMFORTABLE,
        ground=GroundProgramme.SHOP,
        corner=False,
        seed=1865,
    )
    building, _log = generate(site)
    svg = render(building, width_px=1100, labels=False)
    (LOGS / "render_verification_facade.svg").write_text(svg)


def render_block() -> None:
    """Render a 10-parcel corner block: 1865 Paris, comfortable class, commercial ground."""
    block = plan_block(
        frontage=120.0,
        street_width=20.0,
        year=1865,
        klass=BuildingClass.COMFORTABLE,
        regime=GroundRegime.COMMERCIAL,
        seed=42,
        corner_left=True,
        corner_right=True,
    )
    print(f"parcels: {len(block.parcels)}, chamfers: {len(block.chamfers)}")
    nodes = solve_block(
        block,
        year=1865,
        klass=BuildingClass.COMFORTABLE,
        regime=GroundRegime.COMMERCIAL,
        seed=42,
    )
    svg = render(nodes, width_px=2400, labels=False)
    (LOGS / "render_verification_block.svg").write_text(svg)


if __name__ == "__main__":
    render_facade()
    render_block()
    print("wrote render_verification_facade.svg and render_verification_block.svg")
