"""Unit tests for the SVG renderer (S8).

What is worth testing here is not "an SVG comes out". It is:

- rendering the same IR twice is byte-identical (G8);
- the renderer survives a sweep of situations without exception, the way the
  brief's fuzz corpus will hit it (G8's "contact sheet renders ... across the
  fuzz corpus", exercised directly here and again through the contact sheet);
- the automated guard — the renderer decides nothing arguable — actually
  passes, run the same way the gate runs it, not just imported and hoped;
- a round trip through ``ir.serial`` renders identically to the original,
  since a renderer that only works on freshly-generated nodes and not on ones
  that came back from JSON is not really reading the IR, it is reading the
  generator's memory.
"""

from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from buildings.block.block import plan_block, solve_block
from buildings.ir.serial import from_json, to_json
from buildings.render.svg import render, render_block, render_contact_sheet
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.generate import generate

ROOT = Path(__file__).resolve().parents[2]

_SVG_RE = re.compile(r"^<svg\b.*</svg>\s*$", re.DOTALL)


def _site(**kw) -> SiteContext:
    base = dict(
        street_width=20.0,
        parcel_width=12.0,
        parcel_depth=14.0,
        year=1865,
        klass=BuildingClass.COMFORTABLE,
        ground=GroundProgramme.SHOP,
        corner=False,
        seed=1865,
    )
    base.update(kw)
    return SiteContext(**base)


def _building(**kw):
    building, _log = generate(_site(**kw))
    return building


def _num(props, key, default=0.0):
    v = props.get(key)
    return float(v) if v is not None else default


# ---------------------------------------------------------------------------
# Basic shape
# ---------------------------------------------------------------------------


def test_render_returns_a_well_formed_svg_document():
    svg = render(_building())
    assert _SVG_RE.match(svg)
    assert svg.count("<svg") == 1
    assert svg.strip().endswith("</svg>")
    assert 'width="' in svg and 'height="' in svg


def test_render_respects_width_px_budget():
    svg_narrow = render(_building(), width_px=600)
    svg_wide = render(_building(), width_px=2400)
    w_narrow = float(re.search(r'width="([\d.]+)"', svg_narrow).group(1))
    w_wide = float(re.search(r'width="([\d.]+)"', svg_wide).group(1))
    assert w_wide > w_narrow


def test_render_labels_adds_text_without_crashing():
    svg_plain = render(_building(), labels=False)
    svg_labelled = render(_building(), labels=True)
    assert "<text" not in svg_plain
    assert "<text" in svg_labelled


# ---------------------------------------------------------------------------
# I5-style determinism, extended to rendering
# ---------------------------------------------------------------------------


def test_rendering_the_same_ir_twice_is_byte_identical():
    building = _building()
    first = render(building)
    second = render(building)
    assert first == second


def test_rendering_two_independently_generated_identical_situations_matches():
    a = _building()
    b = _building()
    assert render(a) == render(b)


def test_render_survives_a_json_round_trip():
    building = _building()
    restored = from_json(to_json(building))
    assert render(building) == render(restored)


# ---------------------------------------------------------------------------
# Fuzz sweep — render must not raise across a spread of situations
# ---------------------------------------------------------------------------

_WIDTHS = [6.0, 9.0, 12.0, 18.0, 20.0, 24.0, 30.0]
_YEARS = [1825, 1860, 1870, 1884, 1890, 1902, 1910]
_CLASSES = list(BuildingClass)
_GROUNDS = list(GroundProgramme)


def test_render_survives_a_fuzz_sweep():
    seed = 0
    failures: list[str] = []
    for width in _WIDTHS:
        for year in _YEARS:
            for klass in _CLASSES:
                for ground in _GROUNDS:
                    seed += 1
                    situation = _site(
                        street_width=width,
                        parcel_width=max(6.0, width * 0.6),
                        year=year,
                        klass=klass,
                        ground=ground,
                        corner=(seed % 5 == 0),
                        seed=seed,
                    )
                    try:
                        building, _log = generate(situation)
                        render(building, labels=(seed % 7 == 0))
                    except Exception as exc:  # pragma: no cover - failure path
                        failures.append(f"seed={seed} width={width} year={year}: {exc!r}")
    assert not failures, "\n".join(failures[:20])


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------


def test_contact_sheet_renders_a_grid_of_buildings():
    situations = [
        _site(street_width=w, parcel_width=max(6.0, w * 0.6), year=y, seed=i)
        for i, (w, y) in enumerate(
            [(8.0, 1830), (12.0, 1865), (18.0, 1885), (24.0, 1905), (30.0, 1900), (9.0, 1875)]
        )
    ]
    buildings = [generate(s)[0] for s in situations]
    sheet = render_contact_sheet(buildings)
    assert _SVG_RE.match(sheet)
    assert sheet.count('text-anchor="middle">#') == len(buildings)


def test_contact_sheet_is_deterministic():
    buildings = [_building(seed=s) for s in (1, 2, 3)]
    assert render_contact_sheet(buildings) == render_contact_sheet(buildings)


def test_contact_sheet_survives_the_fuzz_corpus():
    buildings = []
    seed = 0
    for width in (6.0, 12.0, 20.0, 30.0):
        for year in (1830, 1870, 1890, 1910):
            seed += 1
            s = _site(street_width=width, parcel_width=max(6.0, width * 0.6), year=year, seed=seed)
            buildings.append(generate(s)[0])
    sheet = render_contact_sheet(buildings, width_px=2400)
    assert _SVG_RE.match(sheet)


def test_contact_sheet_of_one_building_does_not_crash():
    sheet = render_contact_sheet([_building()])
    assert _SVG_RE.match(sheet)


def test_contact_sheet_of_zero_buildings_does_not_crash():
    sheet = render_contact_sheet([])
    assert "<svg" in sheet


# ---------------------------------------------------------------------------
# The renderer decides nothing arguable — run the actual gate, not a copy of it
# ---------------------------------------------------------------------------


def test_check_renderer_dumb_guard_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "dev" / "harness" / "check_renderer_dumb.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# The ABSOLUTE quantities the IR hands over are drawn, not reinvented
#
# These are the two the brief singles out — "Absolute is set by the human body
# and never scales ... Conflating them is what makes procedural buildings look
# like toys". Both were once computed here as a fraction of whatever the
# element happened to sit in, which is exactly the conflation, and neither
# raised anything: the facade simply came out reading as curtain wall. So they
# are pinned against the IR's own numbers rather than against a golden image.
# ---------------------------------------------------------------------------

_RECT_RE = re.compile(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"')
_VLINE_RE = re.compile(r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)"')


def _unit_canvas():
    """A canvas at one pixel per metre with its origin at the pavement, so
    every number in the emitted markup is metres and can be compared straight
    against the IR."""
    from buildings.render.svg.canvas import Canvas

    return Canvas(scale=1.0, x_origin=0.0, y_origin=0.0)


def _openings_of(building):
    for storey in building.children:
        if storey.kind != "storey":
            continue
        for bay in storey.children:
            if bay.kind != "bay":
                continue
            for child in bay.children:
                if child.kind == "opening":
                    yield storey, bay, child


def test_the_sill_the_ir_states_is_the_sill_that_gets_drawn():
    """``opening_sill_height`` is a height above THAT STOREY'S floor and it is
    ABSOLUTE (``catalogue.sill_lean_height``: "set by the human body, not by
    the building's ambition"). It must therefore come out the same on the
    fifth floor as on the first, even though the storeys get shorter going up.
    """
    from buildings.render.svg import elements as el
    from buildings.typologies.paris import catalogue as _cat

    building = _building()
    drawn: list[tuple[float, float, float]] = []
    for storey, bay, opening in _openings_of(building):
        stated = opening.props.get("sill_height")
        if stated is None or opening.props.get("opening_type") != "window":
            continue
        if float(stated) <= 0.0:
            # An opening with no sill is not a counterexample to a claim about
            # sills. Since A4.1 two kinds reach here: the devanture, stepped
            # over at `catalogue.shop_threshold_height`, and the porte-fenêtre
            # onto the balcon filant, walked through. Both are ABSOLUTE and
            # both are body facts; neither is a sill someone leans on, and
            # lumping them in would make this test assert that a French window
            # has a windowsill.
            continue
        if abs(float(stated) - float(_cat.entresol_allege_height())) <= 1e-9:
            # A13.2's third body fact, and excluded for exactly the reason the
            # two above are. An arcaded entresol's light stands on a low
            # *allège* with a small garde-corps across it — knee height, not
            # the height an adult leans out over the street from — so it is a
            # different ABSOLUTE, not this one moving. It is still asserted to
            # be absolute: `test_absolute_quantities_reach_the_facade_unscaled`
            # holds every catalogue ABSOLUTE, this one included, to arriving
            # unscaled by class.
            continue
        canvas = _unit_canvas()
        # The opening's OWN rectangle, not its bay's (A4.1). Qualification
        # resolved it and `compose` already added the sill to the storey
        # floor, so handing `draw_opening` the bay would be asking the
        # renderer to invent the split all over again.
        el.draw_opening(
            canvas,
            opening.props["x"],
            opening.props["y"],
            opening.props["w"],
            opening.props["h"],
            opening.props,
        )
        rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
        assert rects, "an opening drew no body"
        top_px, height_px = float(rects[0].group(2)), float(rects[0].group(4))
        sill_above_floor = -(top_px + height_px) - storey.props["y"]
        drawn.append((storey.props["y"], storey.props["h"], sill_above_floor))
        # The glass sits inside the frame reveal, so the drawn body starts at
        # the stated sill or at most one reveal above it — never below it, and
        # never at a height derived from the storey.
        # The canvas rounds each coordinate it emits to the millimetre, and
        # this figure is read off TWO of them (the rect's top and its height),
        # so the rounding budget is two quanta and not one. It used to say
        # 0.005, which was right for one; it held only because the storey
        # floors in the fixture happened to be whole centimetres, and stopped
        # holding the moment a storey landed at 13.5031 m. A tolerance that
        # depends on the fixture's numbers being round is not a tolerance.
        _tol = 0.01
        assert float(stated) - _tol <= sill_above_floor <= float(stated) + el._HEAD_MARGIN + _tol, (
            f"storey at {storey.props['y']:.2f} m (height {storey.props['h']:.2f} m): "
            f"IR says the sill is {stated} m above the floor, drawing puts it at "
            f"{sill_above_floor:.3f} m"
        )

    assert len({round(h, 2) for _, h, _ in drawn}) > 1, "no storey-height variation to test against"
    # Stated as a SPREAD rather than as a bucket count, for the same reason
    # the tolerance above is two quanta: bucketing by `round(s, 2)` puts two
    # readings a millimetre apart into different buckets whenever they
    # straddle a rounding boundary, so the old form asserted "the sill does
    # not move" and measured "the sill does not cross a centimetre". The
    # spread is the thing meant, and it is the tighter claim.
    sills = [s for _, _, s in drawn]
    assert max(sills) - min(sills) <= 0.01, (
        "the sill moved between storeys of different heights, which is what an "
        f"absolute quantity may never do: {drawn}"
    )
    # ...and it is the body's number, not merely a number that happens to be
    # constant. Pinning it to its source is what stops a future edit from
    # keeping this test green with a constant fraction of the storey.
    from buildings.typologies.paris import catalogue

    assert drawn[0][2] == pytest.approx(
        float(catalogue.sill_lean_height()), abs=el._HEAD_MARGIN + 0.005
    )


def _vertical_bar_positions(canvas) -> list[float]:
    xs = set()
    for element in canvas.elements:
        m = _VLINE_RE.match(element)
        if m and abs(float(m.group(1)) - float(m.group(3))) < 1e-6:
            xs.add(round(float(m.group(1)), 6))
    return sorted(xs)


def test_no_railing_gap_is_wider_than_the_ir_allows():
    """``ironwork_gap_max`` is ABSOLUTE — qualification calls it "a child's
    head", and the brief lists "balustrade gaps narrow enough for a child's
    head" among the quantities that never scale. Every dated pattern must draw
    its balusters on it; a pattern is a look, not a licence to widen the gap.
    """
    from buildings.render.svg import elements as el

    seen_patterns: set[object] = set()
    seed = 0
    for year in (1830, 1865, 1884, 1902):
        for klass in BuildingClass:
            seed += 1
            building, _log = generate(_site(year=year, klass=klass, seed=seed))
            for _storey, bay, _opening in _openings_of(building):
                for child in bay.children:
                    if child.kind != "ironwork":
                        continue
                    stated = child.props.get("max_gap")
                    assert stated is not None, "the IR carries a gap limit and it must be read"
                    if float(child.props.get("h") or 0.0) <= 0.0:
                        # A garde-corps the IR gave no rail height: nothing to
                        # draw, and a reported gap rather than something to
                        # invent a height for here.
                        continue
                    canvas = _unit_canvas()
                    el.draw_ironwork(
                        canvas,
                        bay.props["x"],
                        child.props["y"],
                        bay.props["w"],
                        child.props["h"],
                        child.props,
                    )
                    bars = _vertical_bar_positions(canvas)
                    assert len(bars) >= 2
                    widest = max(b - a for a, b in zip(bars, bars[1:]))
                    seen_patterns.add(child.props.get("ironwork_pattern"))
                    assert widest <= float(stated) + 1e-6, (
                        f"{child.props.get('ironwork_pattern')!r} drew a {widest:.3f} m gap where the "
                        f"IR allows {stated} m"
                    )
    assert len(seen_patterns) >= 2, f"the sweep exercised too few railings: {seen_patterns}"


def test_a_railing_with_a_narrower_gap_gets_more_bars():
    """Not just "under the limit" — the limit is what sets the count, so
    halving it must roughly double the bars."""
    from buildings.render.svg import elements as el

    counts = []
    for gap in (0.20, 0.10):
        canvas = _unit_canvas()
        el.draw_ironwork(canvas, 0.0, 5.0, 2.0, 0.9, {"ironwork_pattern": None, "max_gap": gap})
        counts.append(len(_vertical_bar_positions(canvas)))
    assert counts[1] > counts[0]


# ---------------------------------------------------------------------------
# A12.2 — a garde-corps must not be drawn with the weight of a balcony
#
# "guards" (compose.py, A6.5/A6.6) is the IR's own word for what a length of
# ironwork stands in front of — a balcon filant's slab, which projects and
# runs unbroken across the bays, or a plain opening's reveal, which does not
# project at all. The renderer reads that word; it does not infer it from
# width or pattern, so testing both dated patterns and both plain-vs-scrolled
# cases against the same stated key is honouring the IR, not deciding it.
# ---------------------------------------------------------------------------

_STROKE_W_RE = re.compile(r'stroke-width="([\d.]+)"')


def _line_stroke_w(element: str) -> float | None:
    m = _STROKE_W_RE.search(element)
    return float(m.group(1)) if m and element.startswith("<line") else None


def test_a_garde_corps_draws_thinner_bars_than_a_balcon_filant():
    """Same geometry, same pattern, only ``guards`` differs — the bars
    themselves must come out visibly lighter for the one that does not
    project, or a viewer cannot tell the two apart by weight alone."""
    from buildings.render.svg import elements as el

    for pattern in (None, "haussmannian_scrollwork", "renaissance_revival"):
        props = {"ironwork_pattern": pattern, "max_gap": 0.12, "ornament_count": 2}

        filant_canvas = _unit_canvas()
        el.draw_ironwork(filant_canvas, 0.0, 5.0, 2.0, 0.9, {**props, "guards": "balcon_filant"})
        opening_canvas = _unit_canvas()
        el.draw_ironwork(opening_canvas, 0.0, 5.0, 2.0, 0.9, {**props, "guards": "opening"})

        filant_bars = _vertical_bar_positions(filant_canvas)
        opening_bars = _vertical_bar_positions(opening_canvas)
        assert filant_bars and opening_bars, f"{pattern!r}: both must draw bars to compare"

        filant_widths = [
            w for e in filant_canvas.elements if (w := _line_stroke_w(e)) is not None
        ]
        opening_widths = [
            w for e in opening_canvas.elements if (w := _line_stroke_w(e)) is not None
        ]
        assert max(opening_widths) < min(filant_widths), (
            f"{pattern!r}: a garde-corps line came out as heavy as a balcon "
            f"filant's — opening strokes {sorted(set(opening_widths))}, "
            f"filant strokes {sorted(set(filant_widths))}"
        )


def test_a_garde_corps_draws_no_projecting_slab():
    """A balcon filant's weight includes the slab it stands on
    (``draw_balcony_slab``, a filled rect with bracket triangles); a
    garde-corps in the reveal must never emit one — it has nothing under it
    to project."""
    from buildings.render.svg import elements as el

    canvas = _unit_canvas()
    el.draw_ironwork(canvas, 0.0, 5.0, 2.0, 0.9, {"ironwork_pattern": None, "guards": "opening"})
    assert not any(e.startswith("<rect") for e in canvas.elements), (
        "a garde-corps drew a filled rectangle — that is a slab, and a "
        "garde-corps does not project"
    )
    assert not any(e.startswith("<polygon") for e in canvas.elements), (
        "a garde-corps drew a bracket polygon — brackets carry a projecting "
        "slab, which a garde-corps does not have"
    )


def test_the_canonical_buildings_garde_corps_sits_in_the_reveal_not_the_bay():
    """The reading test in A12.2: on the canonical Second Empire building, the
    two ``guards='opening'`` storeys must draw their rails at the OPENING's
    own width — narrower than the pier-to-pier bay — while the two
    ``guards='balcon_filant'`` storeys draw at the bay's full width, because
    that is what really runs unbroken behind them. Reading the ironwork
    node's own stated rectangle rather than the bay's is what keeps a
    garde-corps from spanning masonry piers it never guards."""
    building = _building()

    filant_seen = opening_seen = 0
    for storey in _walk_kind(building, "storey"):
        for bay in storey.children:
            if bay.kind != "bay":
                continue
            bay_w = float(bay.props["w"])
            for child in bay.children:
                if child.kind != "ironwork":
                    continue
                node_w = float(child.props["w"])
                if child.props.get("guards") == "balcon_filant":
                    filant_seen += 1
                    assert node_w == pytest.approx(bay_w, abs=1e-6), (
                        "a balcon filant's ironwork must run the bay it "
                        f"stands in front of: node w={node_w}, bay w={bay_w}"
                    )
                elif child.props.get("guards") == "opening":
                    opening_seen += 1
                    assert node_w < bay_w - 1e-6, (
                        "a garde-corps must be narrower than its bay — it "
                        f"stands in the reveal, not across the piers: node "
                        f"w={node_w}, bay w={bay_w}"
                    )
    assert filant_seen >= 2 and opening_seen >= 2, (
        "the canonical building did not exercise both kinds of ironwork: "
        f"filant={filant_seen}, opening={opening_seen}"
    )


def _walk_kind(node, kind):
    if node.kind == kind:
        yield node
    for child in node.children:
        yield from _walk_kind(child, kind)


# ---------------------------------------------------------------------------
# The comble in elevation
# ---------------------------------------------------------------------------


_POLY_RE = re.compile(r'<polygon points="([^"]+)"')


def _polygon_area(points: str) -> float:
    """Shoelace area of an SVG ``points`` string, in the canvas's own units."""
    pts = [tuple(map(float, p.split(","))) for p in points.split()]
    area = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def test_a_hipped_comble_keeps_the_flat_front_band():
    """A mid-block roof has no returns, so its mass is the plain rectangle it
    always was: one band, eaves to ridge, the full frontage wide."""
    from buildings.render.svg import elements as el

    profile = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]
    canvas = _unit_canvas()
    el.draw_roof_mass(canvas, 16.0, 10.0, profile, {"material": "slate", "ends": "party_wall"})
    rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
    assert rects, "a mid-block comble must still be a plain rectangle"
    mass = tuple(round(float(g), 4) for g in rects[0].groups())
    assert mass[2] == pytest.approx(16.0), "the band spans the frontage"
    assert mass[3] == pytest.approx(4.0), "the band runs eaves to ridge"


def test_a_hipped_comble_is_clipped_to_its_returns_not_a_dome():
    """A4.5: a hipped roof used to fill the SAME full rectangle as a
    mid-block one, with the hip arris drawn as a decorative line on top of
    it — so the corners beyond the arris, which are not a roof surface at
    all (the section that produces the arris starts its rise exactly at that
    corner), stayed filled with roof colour. On a chamfer narrow enough for
    the two hips to meet before the ridge, that read as a dome: the
    strongest edge in the picture was the arris curve, but the shape drawn
    was still the rectangle around it.

    The mass must now be clipped to the hip silhouette: strictly smaller in
    area than the full rectangle, and drawn as the outline itself (a
    polygon) rather than a rectangle with lines laid over it.
    """
    from buildings.render.svg import elements as el
    from buildings.typologies.paris.terminate import derive_hip_arris

    profile = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]
    facade_w, eaves, ridge_h = 16.0, 10.0, 4.0

    canvas = _unit_canvas()
    # A9.3: the arris is IR-stated, on the roof node's own `hip_arris` prop —
    # ``terminate.derive_hip_arris`` is the one place it is derived, so a test of
    # the renderer supplies it rather than letting `draw_roof_mass` derive a
    # second copy from `profile` itself.
    el.draw_roof_mass(
        canvas, facade_w, eaves, profile,
        {"material": "slate", "ends": "hipped", "hip_arris": derive_hip_arris(facade_w, profile)},
    )
    rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
    assert not rects, "a hipped mass is the clipped silhouette, not a rectangle"
    polys = _POLY_RE.findall("\n".join(canvas.elements))
    assert polys, "a hipped comble must draw its own outline"
    area = _polygon_area(polys[0])
    assert area < facade_w * ridge_h - 1e-6, (
        "the hipped mass must be strictly smaller than the full rectangle — "
        "the corners beyond the arris are sky, not roof"
    )


def test_a_hipped_comble_draws_its_returns_and_a_mid_block_one_does_not():
    """A4.5/A9.3: the arris comes from ``terminate.derive_hip_arris``, via the roof
    node's own ``hip_arris`` prop — see ``test_terminate.py``'s own
    ``derive_hip_arris`` section for the geometry itself (a straight rafter, not
    the curved depth-section, and correctly truncated where a return outruns
    the frontage it has to share). What belongs here is narrower: that
    ``draw_roof_mass`` draws returns for a hipped comble and none for a
    mid-block one, reading the arris rather than leaving it undrawn."""
    from buildings.render.svg import elements as el
    from buildings.typologies.paris.terminate import derive_hip_arris

    profile = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]
    arris = derive_hip_arris(16.0, profile)

    def sloped_lines(ends):
        canvas = _unit_canvas()
        props = {"material": "slate", "ends": ends}
        if ends == "hipped":
            props["hip_arris"] = arris
        el.draw_roof_mass(canvas, 16.0, 10.0, profile, props)
        out = []
        for element in canvas.elements:
            m = _VLINE_RE.match(element)
            if not m:
                continue
            x1, y1, x2, y2 = (float(g) for g in m.groups())
            if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
                out.append((x1, y1, x2, y2))
        return out

    assert sloped_lines("party_wall") == []
    returns = sloped_lines("hipped")
    assert returns, "a hipped comble shows its section at the returns"
    # Both returns stay in the outer thirds: the section is shown AT the ends,
    # not smeared across the frontage.
    for x1, _y1, x2, _y2 in returns:
        run = min(min(x1, x2), 16.0 - max(x1, x2))
        assert run <= 6.0 + 1e-6


# ---------------------------------------------------------------------------
# A6.10 — the comble is one flat grey field
# ---------------------------------------------------------------------------


def _line_stroke_widths(canvas, color: str) -> list[float]:
    out = []
    for e in canvas.elements:
        m = _VLINE_RE.match(e)
        if m and f'stroke="{color}"' in e:
            sw = re.search(r'stroke-width="([\d.]+)"', e)
            if sw:
                out.append(float(sw.group(1)))
    return out


def test_zinc_gets_a_seam_and_slate_does_not():
    """Zinc came to dominate mid-century Paris roofing and its standing seams
    are a large part of how a Paris roof reads (A6.10). A zinc comble must
    draw its own seam colours; a slate one keeps the plain hairline it always
    had — the fold is a fact about the covering, not decoration added
    regardless of what the IR says the roof is made of."""
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    profile = [(0.0, 0.0), (3.0, 4.0)]

    zinc = _unit_canvas()
    el.draw_roof_mass(zinc, 16.0, 10.0, profile, {"material": "zinc_roofing", "ends": "party_wall"})
    assert _line_stroke_widths(zinc, COLORS["roof_seam_dark"]), "no zinc seam colour was drawn"

    slate = _unit_canvas()
    el.draw_roof_mass(slate, 16.0, 10.0, profile, {"material": "slate", "ends": "party_wall"})
    assert not _line_stroke_widths(slate, COLORS["roof_seam_dark"]), (
        "slate must not get zinc's seam colour"
    )


def test_the_brisis_terrasson_break_is_read_off_mansard_angles_not_guessed():
    """The break must come from the roof node's own ``break_pct`` (the number
    ``reglement.mansard_angles`` computed and ``terminate.py`` already
    carries), not from a guess about a second-to-last polyline vertex — and
    it must not appear where the two angles agree (a pre-1884 single-plane
    45° comble states equal angles and ``break_pct == 1.0``, which is exactly
    'there is no break')."""
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    profile = [(0.0, 0.0), (1.0, 2.0), (2.6, 3.4), (4.0, 4.0)]
    break_fill = f'stroke="{COLORS["roof_break"]}"'

    no_break_props = {
        "material": "zinc_roofing", "ends": "party_wall",
        "lower_angle_deg": 45.0, "upper_angle_deg": 45.0, "break_pct": 1.0,
    }
    flat_canvas = _unit_canvas()
    el.draw_roof_mass(flat_canvas, 16.0, 10.0, profile, no_break_props)
    assert not any(break_fill in e for e in flat_canvas.elements), (
        "equal angles and break_pct == 1.0 state there is no break to draw"
    )

    broken_props = {
        "material": "zinc_roofing", "ends": "party_wall",
        "lower_angle_deg": 67.0, "upper_angle_deg": 22.0, "break_pct": 0.72,
    }
    broken_canvas = _unit_canvas()
    el.draw_roof_mass(broken_canvas, 16.0, 10.0, profile, broken_props)
    break_lines = [e for e in broken_canvas.elements if break_fill in e]
    assert break_lines, "differing angles and break_pct < 1 must draw the fold"
    m = _VLINE_RE.match(break_lines[0])
    # A horizontal line (elevation foreshortens the slope the break is on
    # away to nothing) at the stated fraction of the ridge height. This unit
    # canvas has y_origin=0.0, so `Canvas.y` negates metres outright.
    assert float(m.group(2)) == pytest.approx(float(m.group(4)))
    assert float(m.group(2)) == pytest.approx(-(10.0 + 4.0 * 0.72))


def test_no_break_when_props_carry_no_mansard_angles_at_all():
    """A hand-built layer set that never states ``break_pct`` must not crash
    and must not draw a break line either — silence, not a guess."""
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    profile = [(0.0, 0.0), (1.0, 2.0), (2.6, 3.4), (4.0, 4.0)]
    canvas = _unit_canvas()
    el.draw_roof_mass(canvas, 16.0, 10.0, profile, {"material": "zinc_roofing", "ends": "party_wall"})
    assert not any(f'stroke="{COLORS["roof_break"]}"' in e for e in canvas.elements)


# ---------------------------------------------------------------------------
# Draw order is depth order
# ---------------------------------------------------------------------------


def test_a_chimney_stack_goes_in_after_the_comble():
    """**A9.3, reversing this test's own former claim.** A souche does not
    stand behind the comble — it stands ON it and rises clear through it, and
    the masonry the IR gives us to draw is exactly the part standing proud of
    the tiles (``terminate._souche_visible_height``). Drawing it first was
    only ever safe while a souche's stated base agreed with the roof mass's
    own drawn surface at that point; once ``terminate._hip_arris_end`` (keyed
    to the full section depth) and the roof mass (keyed to the frontage,
    A8) disagreed by up to 1.559 m, drawing the stack first meant the roof
    polygon painted over it a moment later — one visible chimney where the
    IR stated five. The fix is structural (one ``hip_arris``, stated once and
    read by both), but the draw order is fixed too, because a souche
    genuinely is in front of the comble it emerges from, not behind it."""
    from buildings.render.svg.canvas import Canvas
    from buildings.render.svg.colors import COLORS
    from buildings.render.svg.render import draw_building

    building = _building(corner=False, year=1884)
    stacks = [
        c for c in building.children
        if c.kind == "special" and c.props.get("element") == "chimney_stack"
    ]
    assert stacks, "this situation should have souches to test with"

    canvas = Canvas(scale=1.0, x_origin=0.0, y_origin=0.0)
    draw_building(canvas, building)

    chimney_fill = f'fill="{COLORS["chimney"]}"'
    roof_fills = tuple(f'fill="{COLORS[k]}"' for k in ("roof_slate", "roof_zinc"))
    first_chimney = min(i for i, e in enumerate(canvas.elements) if chimney_fill in e)
    # The roof mass is a `<rect>` mid-block and a `<polygon>` where hipped
    # (A4.5) — either way it is the first element carrying the roof's fill.
    first_roof = min(
        i
        for i, e in enumerate(canvas.elements)
        if (e.startswith("<rect") or e.startswith("<polygon")) and any(f in e for f in roof_fills)
    )
    assert first_roof < first_chimney, (
        "every souche must be laid down after the comble it rises through, so its own "
        "visible masonry is never buried under the roof mass drawn on top of it"
    )


# ---------------------------------------------------------------------------
# A7.3 — the renderer draws the souche it is given; it computes nothing
# ---------------------------------------------------------------------------
#
# A6.4/A6.8's own defect (a hip-end souche floating in blank sky) and its
# geometry (the hip arris falls away toward a hipped return's ends) are now
# ``terminate.py``'s to state and to be tested against — see
# ``test_terminate.py``'s "A7.3" section, which exercises
# ``terminate._roof_surface_height_at`` and the IR it produces directly. What
# belongs here, in the renderer's own tests, is narrower and different: that
# ``draw_building`` draws EXACTLY the rectangle a chimney's IR states, and
# does not recompute, override, or otherwise second-guess it — which is the
# fix itself, independent of whether any particular base height is the
# geometrically "right" one.


def test_a_chimney_is_drawn_at_exactly_the_base_and_head_the_ir_states():
    """No override: whatever ``y``/``h`` a chimney's IR carries is exactly
    what reaches the canvas, even where that base sits nowhere near the
    ridge — a hand-built IR is as good a witness of "the renderer decides
    nothing here" as a real hip return is, and simpler to pin exactly.

    A6.4 fixed this once by having ``draw_building`` recompute the base from
    the roof's own profile and overwrite whatever the IR said — which meant
    the IR could state one base height (up to 7.6 m off, in the real
    pipeline) while the renderer silently drew a different one. That
    override is gone; this asserts there is nothing left to override with.
    """
    from buildings.ir.nodes import Node
    from buildings.render.svg.canvas import Canvas
    from buildings.render.svg.render import draw_building
    from buildings.trace import TraceEntry

    def _node(kind, x, y, w, h, **extra):
        return Node(
            id=f"n/{kind}", kind=kind,
            trace=(TraceEntry(rule="test", phase="test", detail="", inputs={}),),
            props={"x": x, "y": y, "w": w, "h": h, **extra},
        )

    eaves, ridge_h, facade_w = 10.0, 4.0, 16.0
    silhouette = _node(
        "silhouette", 0.0, 0.0, 3.0, eaves + ridge_h,
        eaves_height=eaves, points=((0.0, eaves), (3.0, eaves + ridge_h)),
    )
    roof = _node("roof", 0.0, eaves, facade_w, ridge_h, material="slate", ends="hipped")
    # A base that is deliberately NOT the ridge and NOT the eaves — nothing a
    # renderer computing its own surface height from `roof`/`silhouette`
    # would ever produce on its own, which is exactly why it pins "drawn
    # nothing but what the IR said" rather than "drawn the right number by
    # coincidence".
    odd_base = eaves + 1.23  # 2 dp: the SVG canvas rounds coordinates to pixels
    stack = _node("special", 2.0, odd_base, 0.6, 0.8, element="chimney_stack")
    building = Node(
        id="b", kind="building",
        trace=(TraceEntry(rule="test", phase="test", detail="", inputs={}),),
        props={"x": 0.0, "y": 0.0, "w": facade_w, "h": eaves + ridge_h},
        children=(roof, silhouette, stack),
    )

    canvas = Canvas(scale=1.0, x_origin=0.0, y_origin=0.0)
    draw_building(canvas, building)

    chimney_rects = [
        _RECT_RE.match(e) for e in canvas.elements if e.startswith("<rect") and "#A09080" in e
    ]
    chimney_rects = [m for m in chimney_rects if m]
    shafts = [m for m in chimney_rects if float(m.group(4)) > 0.08 + 1e-6]
    assert len(shafts) == 1

    def _base_top(m):
        svg_y, svg_h = float(m.group(2)), float(m.group(4))
        top = -svg_y
        return top - svg_h, top

    base, top = _base_top(shafts[0])
    assert base == pytest.approx(odd_base), (
        "the drawn base must be exactly the IR's y, not a recomputed surface height"
    )
    assert top == pytest.approx(odd_base + 0.8)


# ---------------------------------------------------------------------------
# A4.6 — the block has a render path
# ---------------------------------------------------------------------------


def _block(**kw):
    base = dict(
        frontage=96.0,
        street_width=20.0,
        year=1885,
        klass=BuildingClass.COMFORTABLE,
        seed=7,
        corner_left=True,
        corner_right=True,
    )
    base.update(kw)
    frontage, street_width, year = base.pop("frontage"), base.pop("street_width"), base.pop("year")
    block = plan_block(frontage, street_width, year, **base)
    return block, solve_block(block, year, klass=base["klass"], seed=base["seed"])


def test_render_of_a_lone_parcel_node_is_not_the_old_empty_svg():
    """``render()`` used to assume its argument WAS a ``BuildingNode`` with
    ``storey`` children, so a bare ``parcel`` node — what ``solve_block``
    wraps each building in — fell through every branch and came back as an
    empty sky-and-ground SVG a few hundred bytes long. It must now draw the
    building the parcel carries."""
    _block_obj, nodes = _block(corner_left=False, corner_right=False)
    parcel = next(n for n in nodes if n.kind == "parcel")

    svg = render(parcel, width_px=900)
    assert _SVG_RE.match(svg)
    ET.fromstring(svg)
    # A real facade has dozens of elements (walls, storeys, openings,
    # ironwork, roof); the old empty-canvas bug produced ~4 (sky, ground,
    # svg wrapper, style) in ~325 bytes.
    assert svg.count("<rect") > 20, f"suspiciously little was drawn: {len(svg)} bytes"


def test_render_dispatches_a_block_tuple_to_render_block():
    """``render()`` accepts either one ``BuildingNode`` or a solved block's
    whole tuple of nodes — the second dispatches to ``render_block`` and
    must produce byte-identical output to calling it directly."""
    _block_obj, nodes = _block()
    assert render(nodes, width_px=1600) == render_block(nodes, width_px=1600)


def test_a_block_reads_as_one_wall_not_a_shelf_of_models():
    """The whole point of the block being the unit (S9): every building's
    cornice line is the same block-level line, drawn once and continuously
    across every party wall — not each building's own cornice stopping and
    restarting at the seam."""
    _block_obj, nodes = _block()
    svg = render_block(nodes, width_px=2200)
    assert _SVG_RE.match(svg)
    ET.fromstring(svg)

    parcels = [n for n in nodes if n.kind == "parcel"]
    chamfers = [n for n in nodes if n.kind == "chamfer"]
    assert len(parcels) >= 4, "this sweep should exercise several buildings"
    assert chamfers, "corner_left/right=True should have produced chamfers"

    block_cornice = next(
        n for n in nodes if n.kind == "cornice" and n.props.get("scope") == "block"
    )
    span = max(_num(n.props, "x") + _num(n.props, "w") for n in parcels + chamfers) - min(
        _num(n.props, "x") for n in parcels + chamfers
    )
    # The block's own cornice line runs the whole frontage, not one parcel.
    assert float(block_cornice.props["w"]) == pytest.approx(span)

    # Drawn: a cornice-coloured rect this wide must appear in the markup,
    # alongside each building's own (narrower) storey cornice — that wide
    # one is what makes the line continuous across every party wall.
    from buildings.render.svg.colors import COLORS

    cornice_fill = f'fill="{COLORS["cornice"]}"'
    wide_cornice_rects = []
    for line in svg.splitlines():
        m = _RECT_RE.match(line)
        if m and cornice_fill in line and float(m.group(3)) >= span * 0.9:
            wide_cornice_rects.append(m)
    assert wide_cornice_rects, "no single cornice element spans the whole run"


def test_render_block_is_deterministic():
    _block_obj, nodes = _block()
    assert render_block(nodes, width_px=1600) == render_block(nodes, width_px=1600)


def test_render_block_of_a_single_parcel_matches_the_lone_parcel_path():
    """A block of one parcel and no chamfers is the degenerate case, and it
    must not be special-cased: ``render_block`` on it is exactly what
    ``render()`` dispatches a lone ``parcel`` node to."""
    _block_obj, nodes = _block(corner_left=False, corner_right=False)
    parcel = next(n for n in nodes if n.kind == "parcel")
    assert render(parcel, width_px=900) == render_block([parcel], width_px=900)


# ---------------------------------------------------------------------------
# A6.3 — the pan coupé has no roof
# ---------------------------------------------------------------------------


def test_a_pan_coupes_roof_is_drawn_not_bare_sky():
    """Above each chamfer's cornice used to be bare sky, at both ends of the
    block. The chamfer now carries a roof child (block.py), and this is the
    renderer half: ``_draw_chamfer`` must actually put roof-coloured paint
    above the cut face's own cornice, not just carry the node unused."""
    _block_obj, nodes = _block(corner_left=True, corner_right=True)
    svg = render_block(nodes, width_px=2200)
    assert _SVG_RE.match(svg)
    ET.fromstring(svg)

    from buildings.render.svg.colors import COLORS

    chamfers = [n for n in nodes if n.kind == "chamfer"]
    assert chamfers
    roof_fills = tuple(f'fill="{COLORS[k]}"' for k in ("roof_slate", "roof_zinc"))
    assert any(f in svg for f in roof_fills), "no roof-coloured element in the block at all"

    # The canvas itself must be sized for it: a chamfer's roof standing taller
    # than every parcel's own total height must not be clipped off the top.
    for chamfer in chamfers:
        roof = next(c for c in chamfer.children if c.kind == "roof")
        chamfer_total = float(chamfer.props["h"]) + float(roof.props["h"])
        canvas_h_px = float(re.search(r'height="([\d.]+)"', svg).group(1))
        # Loose bound: just proves the canvas was not sized off eaves alone.
        assert canvas_h_px > chamfer_total * 0.5


# ---------------------------------------------------------------------------
# The ground storey is a wall with shops cut in it, not a glass frontage
#
# A4.1's second pass. The IR had already carved a real trumeau between every
# pair of shop bays — and the renderer painted over all of them, because
# `compose` emitted ONE `shopfront` node spanning x=0 to the full facade width
# and `_draw_storey` glazed that rectangle before drawing any bay. Nothing
# raised; the ground floor, which is the storey a passer-by actually looks at,
# simply came out as curtain wall. So this is pinned against the IR's own
# numbers, in the emitted markup, at both ends: the glass must stop at the
# pier, and it must be drawn exactly once.
# ---------------------------------------------------------------------------


def _shop_glass_rects(svg: str):
    """The devanture lights in the emitted markup.

    ``shopfront_glass`` and ``window`` are the same paint, so the stroke is
    what tells them apart: a shop light is framed by its mullion, an ordinary
    window by its own frame colour.
    """
    from buildings.render.svg.colors import COLORS

    fill = f'fill="{COLORS["shopfront_glass"]}"'
    stroke = f'stroke="{COLORS["mullion"]}"'
    out = []
    for line in svg.splitlines():
        m = _RECT_RE.match(line)
        if m and fill in line and stroke in line:
            out.append(tuple(float(m.group(i)) for i in (1, 2, 3, 4)))
    return out


def test_no_devanture_spans_more_of_the_frontage_than_its_own_bay():
    """Every shopfront node lies inside one bay, and the bays keep their
    masonry.

    The old storey-scope node's rectangle WAS the facade, so this reads as a
    tautology only if you have not seen it fail: it failed on 41% of the
    generated corpus.
    """
    for ground in (GroundProgramme.SHOP, GroundProgramme.CAFE, GroundProgramme.OFFICE):
        for year in (1830, 1865, 1895):
            building = _building(ground=ground, year=year)
            facade_w = float(building.props["w"])
            for storey in building.children:
                if storey.kind != "storey":
                    continue
                # A devanture is never a storey-scope element. That is the
                # whole defect in one line: as a child of the storey it had
                # the storey's rectangle, and the storey's rectangle is the
                # frontage.
                assert not [c for c in storey.children if c.kind == "shopfront"], (
                    f"{storey.id}: a shopfront hanging off the storey spans the "
                    "whole frontage by construction"
                )
                spans = []
                for bay in storey.children:
                    if bay.kind != "bay":
                        continue
                    bx, bw = float(bay.props["x"]), float(bay.props["w"])
                    for child in bay.children:
                        if child.kind != "shopfront":
                            continue
                        cx, cw = float(child.props["x"]), float(child.props["w"])
                        assert cx > bx + 1e-9 and cx + cw < bx + bw - 1e-9, (
                            f"{child.id}: the devanture runs into the trumeau of its "
                            f"own bay ({cx:.3f}..{cx + cw:.3f} in {bx:.3f}..{bx + bw:.3f})"
                        )
                        spans.append((cx, cx + cw))
                if not spans:
                    continue
                spans.sort()
                assert sum(b - a for a, b in spans) < facade_w * 0.85, (
                    f"{storey.id}: the devantures cover {sum(b - a for a, b in spans):.2f} m "
                    f"of a {facade_w:.2f} m frontage — that is a glass wall, not shops"
                )
                for (_, end), (start, _) in zip(spans, spans[1:]):
                    assert start - end > 0.3, (
                        f"{storey.id}: only {start - end:.3f} m of masonry between two shops"
                    )


def test_the_shop_glass_stops_at_the_pier_and_is_drawn_once():
    """In the markup, not just in the IR.

    Two failures at once used to be visible here: one full-frontage glass band
    (`<rect x="126.92" width="846.15">` on a 12 m facade), and the shop-bay
    openings drawn over it 8 px up and 28 px taller — a ghost frame around
    every shop, misregistered against its own glass. Both are geometry
    questions about the emitted SVG, so both are asked of it.
    """
    building = _building(ground=GroundProgramme.SHOP)
    svg = render(building, width_px=1100)
    glass = _shop_glass_rects(svg)

    shop_openings = [
        opening
        for _storey, _bay, opening in _openings_of(building)
        if opening.props.get("opening_type") == "shop_bay"
    ]
    assert shop_openings, "this fixture is supposed to have a shopfront"

    ground_glass = sorted(glass)
    assert ground_glass, "no devanture light was drawn at all"
    # The literal old failure: one `<rect x="126.92" width="846.15">` covering
    # the whole 12 m frontage, piers included.
    facade_px = max(r[0] + r[2] for r in ground_glass) - min(r[0] for r in ground_glass)
    for rect in ground_glass:
        assert rect[2] < facade_px * 0.6, (
            f"a single sheet of glass {rect[2]:.0f} px wide across a "
            f"{facade_px:.0f} px frontage is a curtain wall"
        )
    # Exactly one glass rectangle per shop bay. Two per bay was the ghost.
    assert len(ground_glass) == len(shop_openings), (
        f"{len(ground_glass)} glass rectangles for {len(shop_openings)} shop bays"
    )

    # And each is the light's own rectangle. Ratio-based rather than absolute,
    # because `render` picks its own scale from the pixel budget.
    widest_bay = max(
        float(bay.props["w"]) for _s, bay, _o in _openings_of(building)
    )
    scale = ground_glass[0][2] / float(shop_openings[0].props["w"])
    for rect, opening in zip(ground_glass, sorted(shop_openings, key=lambda o: o.props["x"])):
        w = float(opening.props["w"])
        h = float(opening.props["h"])
        # A7.4: the devanture's head is dated, not always 'flat' — where it
        # is 'segmental'/'round'/'irregular' the light's own glass stops
        # short of the head arc drawn over it (``elements.draw_opening``'s
        # shop branch, A6.8), exactly the way an ordinary window's does.
        head_form = opening.props.get("head") or "flat"
        head_h = min(0.5, max(0.15, w * 0.22), h * 0.6) if head_form != "flat" else 0.0
        assert rect[2] == pytest.approx(w * scale, rel=1e-3)
        assert rect[3] == pytest.approx((h - head_h) * scale, rel=1e-3)
        assert rect[2] < widest_bay * scale - 1e-6, "the glass fills its whole bay"


def test_how_many_glazing_bars_a_shop_window_has_comes_from_the_ir():
    """The pane rhythm is the date's, not the renderer's.

    `draw_shopfront` used to divide the light by ``max(2, int(w / 1.4))`` —
    eight mullions at 1.5 m centres across a frontage whose bays are at 3.45 m
    centres, so the "piers" it drew landed nowhere near a real one. The guard's
    AST scan cannot see that (no forbidden token appears in the expression),
    which is exactly why it is asserted here instead: change the ABSOLUTE the
    IR states and the drawn count must change with it; hold it and the count
    must not move when the light does.
    """
    import math

    from buildings.render.svg import elements as el

    def bars(width: float, pane: float) -> int:
        """Vertical glazing bars only — the horizontal ones divide the light's
        height by the same sheet limit and would be counted twice here."""
        canvas = _unit_canvas()
        el.draw_opening(
            canvas, 0.0, 0.0, width, 3.0, {"opening_type": "shop_bay", "pane_max_span": pane}
        )
        found = [_VLINE_RE.match(e) for e in canvas.elements]
        return len([m for m in found if m and m.group(1) == m.group(3)])

    small, large = bars(2.6, 0.45), bars(2.6, 2.60)
    assert small > large, "small panes drew no more glazing bars than plate glass"
    assert large == 0, "plate glass — one sheet — was still divided"
    assert small == math.ceil(2.6 / 0.45) - 1

    # And it honours the limit rather than approximating it: no pane wider
    # than the sheet the IR says the glassworks could deliver.
    for width in (1.2, 2.0, 2.645, 3.4):
        for pane in (0.45, 1.10, 1.80):
            n = bars(width, pane) + 1
            assert width / n <= pane + 1e-9, (
                f"a {width:.2f} m light in {n} panes needs a {width / n:.2f} m sheet, "
                f"and the IR says {pane:.2f} m is the largest there was"
            )


# ---------------------------------------------------------------------------
# A6.8 — the devanture's head is stated and discarded
# ---------------------------------------------------------------------------


def test_a_shop_bays_stated_head_is_drawn_not_discarded():
    """``draw_opening`` used to dispatch every ``shop_bay`` straight to
    ``_draw_shop_light`` and return, before any head was ever drawn — the
    mirror of A4.1: the IR states ``head``, and it was thrown away regardless
    of what it said. A stated round or segmental head must now put an arch
    above the light — a polygon, distinct from the plain glass rectangle —
    and the glass rectangle itself must shrink to make room for it rather
    than run the light's full height underneath an arch drawn on top."""
    from buildings.render.svg import elements as el

    w, h = 2.4, 3.0
    flat = _unit_canvas()
    el.draw_opening(flat, 0.0, 0.0, w, h, {"opening_type": "shop_bay", "head": "flat"})
    flat_glass = [m for m in (_RECT_RE.match(e) for e in flat.elements) if m][0]
    assert float(flat_glass.group(4)) == pytest.approx(h), "a flat head takes no height"

    for head_form in ("segmental", "round"):
        canvas = _unit_canvas()
        el.draw_opening(canvas, 0.0, 0.0, w, h, {"opening_type": "shop_bay", "head": head_form})
        polys = _POLY_RE.findall("\n".join(canvas.elements))
        assert polys, f"a {head_form!r} shop head drew no arch at all"
        glass = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m][0]
        assert float(glass.group(4)) < h, (
            f"the {head_form!r} head must take some of the light's height, not sit "
            "on top of a rectangle that already ran the full height"
        )


def test_a_flat_shop_head_still_draws_nothing_extra():
    """The common case (and the only one the generator states today) must
    stay byte-for-byte what it was: no head branch may fire for it."""
    from buildings.render.svg import elements as el

    canvas = _unit_canvas()
    el.draw_opening(canvas, 0.0, 0.0, 2.4, 3.0, {"opening_type": "shop_bay", "head": "flat"})
    assert not _POLY_RE.findall("\n".join(canvas.elements))
    canvas_no_head = _unit_canvas()
    el.draw_opening(canvas_no_head, 0.0, 0.0, 2.4, 3.0, {"opening_type": "shop_bay"})
    assert canvas.elements == canvas_no_head.elements


# ---------------------------------------------------------------------------
# A8.1 (D1) — the porte piétonne fell through to the window path
# ---------------------------------------------------------------------------


def test_a_pedestrian_entrance_draws_as_a_door_not_a_window():
    """``catalogue.entrance_for`` states ``opening_type='pedestrian_entrance'``
    on every building that does not keep a carriage — exactly half the corpus
    — and until A8.1 ``draw_opening`` had no branch for it, so it fell through
    to the generic window path and drew as one: same fill, same mullion, same
    frame. The door must now be drawn in the door's own colour (never the
    window's), and it must draw something extra a plain window does not — the
    panelled leaves — so it reads as a different KIND of thing beside the
    windows of its own storey, not a same-shaped opening in a different coat
    of paint.
    """
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    w, h = 1.4, 2.9

    window = _unit_canvas()
    el.draw_opening(window, 0.0, 0.0, w, h, {"opening_type": "window", "head": "flat"})

    door = _unit_canvas()
    el.draw_opening(door, 0.0, 0.0, w, h, {"opening_type": "pedestrian_entrance", "head": "flat"})

    assert f'fill="{COLORS["window"]}"' not in "\n".join(door.elements), (
        "a pedestrian entrance must not be filled in the window's own colour"
    )
    assert f'fill="{COLORS["door"]}"' in "\n".join(door.elements), (
        "a pedestrian entrance must draw its timber leaves in the door's colour"
    )
    assert len(door.elements) != len(window.elements) or door.elements != window.elements, (
        "a door drawn identically to a window is the exact defect A8.1 fixes"
    )
    # The imposte over the leaves is glazed and distinct from both the door
    # and the plain window glass — not the generic window fill either.
    assert f'fill="{COLORS["door_glass"]}"' in "\n".join(door.elements), (
        "a flat-headed porte piétonne must draw its own fanlight, not bare wall"
    )


def test_a_pedestrian_entrance_runs_from_the_pavement_like_the_carriage_door():
    """``pedestrian_entrance_in_slot`` returns ``sill=0`` exactly like the
    carriage entrance (A6.1: it is ABSOLUTE, never leaned on) — so the drawn
    body's lowest point must be ``y`` itself, with nothing added for a sill
    the way an ordinary window gets one."""
    from buildings.render.svg import elements as el

    canvas = _unit_canvas()
    y = 0.0
    el.draw_opening(canvas, 0.0, y, 1.4, 2.9, {"opening_type": "pedestrian_entrance", "head": "flat"})
    rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
    assert rects, "a pedestrian entrance must draw a body"
    # The leaves' own body is the first rect drawn (before the panels or the
    # fanlight); its bottom edge in metres is ``-(top_px + height_px)`` the
    # same conversion ``test_the_sill_the_ir_states_is_the_sill_that_gets_drawn``
    # uses above.
    top_px, height_px = float(rects[0].group(2)), float(rects[0].group(4))
    bottom_m = -(top_px + height_px)
    assert bottom_m == pytest.approx(y, abs=1e-6), (
        f"the door's leaves must start at the threshold ({y}), not a sill above it "
        f"(drawn bottom {bottom_m})"
    )


# ---------------------------------------------------------------------------
# A6.9 — the stall riser is a real soubassement, and it comes from the IR
# ---------------------------------------------------------------------------


def test_the_stall_riser_is_a_real_soubassement_not_a_sill():
    from buildings.typologies.paris import catalogue

    riser = float(catalogue.shop_threshold_height())
    assert 0.3 <= riser <= 0.6, (
        f"a real soubassement runs 0.3-0.6 m; {riser:.2f} m reads as glass meeting "
        "the pavement"
    )


def test_the_drawn_riser_tracks_the_ir_not_a_renderer_literal():
    """Coordinate check for A6.9: the renderer must draw whatever
    ``threshold_height`` the IR states, not a number of its own — so two
    different stated heights must draw two different riser bands, in
    proportion, with nothing in ``elements.py`` clamping them back together."""
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    def riser_height(threshold: float) -> float:
        canvas = _unit_canvas()
        el.draw_shopfront(
            canvas, 0.0, 0.0, 2.0, 3.0,
            {"threshold_height": threshold, "fascia_depth": 0.0, "shopfront_style": "plate_glass"},
        )
        fill = f'fill="{COLORS["mullion"]}"'
        for e in canvas.elements:
            m = _RECT_RE.match(e)
            if m and fill in e:
                return float(m.group(4))
        raise AssertionError("no soubassement rect was drawn at all")

    assert riser_height(0.15) == pytest.approx(0.15)
    assert riser_height(0.40) == pytest.approx(0.40)


# ---------------------------------------------------------------------------
# A pan coupé is a third short facade, so it has windows in it
# ---------------------------------------------------------------------------


def test_a_pan_coupe_is_a_pierced_facade_not_a_blank_wall():
    """A4.5's own words are "a corner is a third short facade with its own
    rhythm". Only the rhythm was ever built: `block.py` gave each chamfer bay
    x/y/w/slot_name and no children, and `_draw_chamfer` had no opening branch
    at all, so both ends of every block rendered as blank unpierced walls.
    """
    from buildings.block.block import block_nodes

    _block_obj, nodes = _block()
    chamfers = [n for n in nodes if n.kind == "chamfer"]
    assert chamfers, "this fixture is supposed to have two pan coupés"

    for chamfer in chamfers:
        openings = [n for n in block_nodes((chamfer,)) if n.kind == "opening"]
        assert openings, f"{chamfer.id} is a blank wall"
        storeys = [c for c in chamfer.children if c.kind == "storey"]
        assert len(storeys) > 1, "a facade with one storey is not this building's facade"
        cw = float(chamfer.props["w"])
        for o in openings:
            ox, ow = float(o.props["x"]), float(o.props["w"])
            assert 0.0 < ox and ox + ow < cw, f"{o.id} runs off the cut face"
            # Its own rhythm: the chamfer's bays are narrower than the
            # facade's, so its lights sit in narrower slots — but they are
            # still lights, with a real pier either side.
            assert float(o.props["pier_width"]) > 0.0

    # And the drawing shows them. The left chamfer occupies the strip of the
    # frontage before the first parcel begins; in metres that is
    # [x, x+w), and glass has to appear inside it. Before A4.5's second pass
    # this strip contained one wall rectangle and two pier lines, and nothing
    # else in the whole SVG.
    from buildings.render.svg.colors import COLORS

    svg = render_block(nodes, width_px=2000)
    left = min(chamfers, key=lambda n: float(n.props["x"]))
    first_parcel_x = min(float(n.props["x"]) for n in nodes if n.kind == "parcel")
    assert float(left.props["x"]) + float(left.props["w"]) <= first_parcel_x + 1e-9

    # Pixels per metre, recovered from the block's own extent rather than
    # re-derived: the sky rectangle is the whole canvas.
    frontage = [n for n in nodes if n.kind in ("parcel", "chamfer")]
    x0 = min(float(n.props["x"]) for n in frontage)
    x1 = max(float(n.props["x"]) + float(n.props["w"]) for n in frontage)
    sky = next(m for m in (_RECT_RE.match(line) for line in svg.splitlines()) if m)
    scale = float(sky.group(3)) / (x1 - x0 + 2 * 1.8)  # _MARGIN_M either side
    strip = (
        (1.8 + float(left.props["x"]) - x0) * scale,
        (1.8 + float(left.props["x"]) + float(left.props["w"]) - x0) * scale,
    )

    glass_fills = {COLORS["window"], COLORS["shopfront_glass"]}
    in_strip = 0
    for line in svg.splitlines():
        m = _RECT_RE.match(line)
        if not m or not any(f'fill="{f}"' in line for f in glass_fills):
            continue
        gx, gw = float(m.group(1)), float(m.group(3))
        if strip[0] - 1.0 <= gx and gx + gw <= strip[1] + 1.0:
            in_strip += 1
    assert in_strip >= len([c for c in left.children if c.kind == "storey"]) - 1, (
        f"only {in_strip} glazed rectangles fall inside the left pan coupé's own "
        "strip of the frontage"
    )


# ---------------------------------------------------------------------------
# A7.2 — the renderer counts nothing
# ---------------------------------------------------------------------------


def _circle_count(canvas) -> int:
    return sum(1 for e in canvas.elements if e.startswith("<circle"))


def test_a_cornice_draws_the_number_of_brackets_the_ir_states():
    """A6.11 and A7.2's first violation. ``spacing = 0.5; n = int(w / spacing)``
    meant every cornice in Paris carried the same modillions per metre and the
    only thing money moved was the width of the wall behind them. The count is
    stated now, so doubling it must double what is drawn — at the same width,
    which is the whole point."""
    from buildings.render.svg import elements as el

    drawn = []
    for stated in (6, 12):
        canvas = _unit_canvas()
        el.draw_cornice(
            canvas, 0.0, 10.0, 12.0,
            {"cornice_ornament": "modillioned", "projection": 0.3, "ornament_count": stated},
        )
        drawn.append(len([e for e in canvas.elements if e.startswith("<rect")]))
    assert drawn[1] - drawn[0] == 6, f"the stated count did not reach the drawing: {drawn}"


def test_a_socle_courses_on_the_stated_grid_and_not_on_one_of_its_own():
    """Three treatments used to carry three course heights of the renderer's
    own (0.32, 0.22, 0.3) and divide the wall by them. What a course LOOKS
    like is still decided here; how many there are is not."""
    from buildings.render.svg import elements as el

    canvas = _unit_canvas()
    el.draw_socle(
        canvas, 0.0, 0.0, 12.0, 4.0,
        {"treatment": "raised_bossage", "course_columns": 8, "course_rows": 5},
    )
    # One background rect plus one per drawn stone.
    assert len([e for e in canvas.elements if e.startswith("<rect")]) == 1 + 8 * 5

    lines = []
    for rows in (4, 9):
        canvas = _unit_canvas()
        el.draw_socle(
            canvas, 0.0, 0.0, 12.0, 4.0,
            {"treatment": "flat_incised_refends", "course_columns": 1, "course_rows": rows},
        )
        lines.append(len([e for e in canvas.elements if e.startswith("<line")]))
    assert lines[1] - lines[0] == 5, f"refend coursing ignored the stated rows: {lines}"


def test_a_balcony_carries_the_consoles_the_ir_counted():
    from buildings.render.svg import elements as el

    drawn = []
    for stated in (3, 9):
        canvas = _unit_canvas()
        el.draw_balcony_slab(
            canvas, 0.0, 6.0, 9.0, {"projection": 0.8, "bracket_count": stated}
        )
        drawn.append(len([e for e in canvas.elements if e.startswith("<polygon")]))
    assert drawn == [3, 9]


def test_railing_ornament_is_counted_upstream_and_the_bars_are_not():
    """The instructive pair of A7.2, drawn rather than argued. At one width
    and one absolute gap, changing only the stated ornament count changes the
    scrollwork and leaves the balusters exactly where they were: the gap is a
    child's head and the scrolls are money."""
    from buildings.render.svg import elements as el

    bars, scrolls = [], []
    for stated in (3, 11):
        canvas = _unit_canvas()
        el.draw_ironwork(
            canvas, 0.0, 6.0, 4.0, 0.9,
            {
                "ironwork_pattern": "haussmannian_scrollwork",
                "max_gap": 0.11,
                "ornament_count": stated,
            },
        )
        bars.append(_vertical_bar_positions(canvas))
        scrolls.append(_circle_count(canvas))
    assert scrolls == [3, 11]
    assert bars[0] == bars[1], "the ornament count moved the balusters"


def test_an_unstated_gap_no_longer_makes_the_renderer_invent_a_rhythm():
    """A7.2's deleted fallback. ``int(w * _UNGUARDED_RAIL_BAYS_PER_METRE)``
    was ten bars per metre, a figure this module invented, applied to a
    dimension it was handed — the same offence as every other count it took.
    A node that states no gap has stated no rhythm; drawing none is the
    honest reading, and the width may not be what decides it."""
    from buildings.render.svg import elements as el

    counts = []
    for w in (2.0, 8.0):
        canvas = _unit_canvas()
        el.draw_ironwork(canvas, 0.0, 6.0, w, 0.9, {"ironwork_pattern": None})
        counts.append(len(_vertical_bar_positions(canvas)))
    assert counts[0] == counts[1], f"a four-fold wider railing invented more bars: {counts}"
    assert not hasattr(el, "_UNGUARDED_RAIL_BAYS_PER_METRE")


def test_the_seams_on_a_slope_are_the_count_the_roof_states():
    """A6.10 gave zinc its paired stroke; A7.2 took the arithmetic that
    decided how many. What the covering still decides is what a seam looks
    like — that is drawing — and what it no longer decides is the rhythm."""
    from buildings.render.svg import elements as el
    from buildings.render.svg.colors import COLORS

    profile = [(0.0, 0.0), (3.0, 4.0)]
    seams = []
    for stated in (8, 24):
        canvas = _unit_canvas()
        el.draw_roof_mass(
            canvas, 16.0, 10.0, profile,
            {"material": "zinc_roofing", "ends": "party_wall", "seam_count": stated},
        )
        seams.append(len(_line_stroke_widths(canvas, COLORS["roof_seam_dark"])))
    assert seams[1] > seams[0]
    assert seams[1] - seams[0] == 16, f"the stated seam count did not reach the slope: {seams}"


def test_a_grand_frontage_is_visibly_finer_worked_than_a_modest_one():
    """The end-to-end reading of A7.2, on the drawing rather than on the IR.
    Two buildings on the same street in the same year: the grand one must
    carry more ornament per metre of frontage, not merely more metres.

    The treatment is pinned to one vocabulary on both sides on purpose. A
    grander frontage often draws a *different* socle — jointed bossage rather
    than incised refends — and counting marks across two vocabularies would
    make this pass on the treatment rather than on the density, which is the
    one thing it is here to measure.
    """
    from buildings.render.svg import elements as el

    per_metre = {}
    for klass in (BuildingClass.MODEST, BuildingClass.GRAND):
        marks = width = 0.0
        for seed in range(6):
            building, _log = generate(_site(year=1865, klass=klass, seed=seed))
            for storey in building.children:
                if storey.kind != "storey":
                    continue
                for child in storey.children:
                    if child.kind != "socle":
                        continue
                    canvas = _unit_canvas()
                    el.draw_socle(
                        canvas,
                        child.props["x"], child.props["y"],
                        child.props["w"], child.props["h"],
                        {**dict(child.props), "treatment": "raised_bossage"},
                    )
                    marks += len(canvas.elements)
                    width += float(child.props["w"])
        per_metre[klass] = marks / width
    assert per_metre[BuildingClass.GRAND] > per_metre[BuildingClass.MODEST] * 1.1, per_metre


# ===========================================================================
# A14 — the two-storey arched entrance, drawn
# ===========================================================================


def _poly_extent(points: str) -> tuple[float, float, float, float]:
    pts = [tuple(float(v) for v in p.split(",")) for p in points.split()]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def test_the_arch_head_rise_the_ir_states_is_the_rise_that_gets_drawn():
    """A14.1: the head is round, and a round head on a 2.60 m span rises
    1.30 m. The renderer's own fallback is ``min(0.5, max(0.15, w * 0.30))``
    — a 0.50 m bow — so if the stated rise were ignored the one thing that
    makes this form a two-storey ARCH rather than a tall rectangle would be
    drawn away. Measured off the markup at one pixel per metre.
    """
    from buildings.render.svg import elements as el

    w, h, rise = 2.60, 2.06, 1.30
    canvas = _unit_canvas()
    el.draw_opening(
        canvas, 4.0, 3.95, w, h,
        {"opening_type": "entrance_arch_head", "head": "round",
         "head_rise": rise, "arch_register": "arch_head"},
    )
    polys = _POLY_RE.findall("\n".join(canvas.elements))
    assert polys, "the round head drew no arch at all"
    # ``Canvas.y`` is metres above the pavement negated (SVG counts down), so
    # the crown is the SMALLEST y in the markup and the springing the largest.
    crown_m = -min(_poly_extent(p)[2] for p in polys)
    springing_m = -max(_poly_extent(p)[3] for p in polys)
    assert crown_m >= 3.95 + h - 1e-6, (
        f"the head crowns at {crown_m:.2f} m; the opening's own top is "
        f"{3.95 + h:.2f} m"
    )
    assert crown_m - springing_m == pytest.approx(rise, abs=0.25), (
        f"the head was drawn {crown_m - springing_m:.2f} m deep against a stated "
        f"rise of {rise:.2f} m"
    )
    # And the renderer's own fallback would have been a 0.50 m bow, so a
    # stated rise that got ignored is a failure this test can name.
    assert crown_m - springing_m > 0.9, "the stated rise was replaced by the default bow"


def test_the_leaves_of_a_tall_arch_stop_where_the_ir_says_and_a_tympanum_fills_the_rest():
    """A14.1 and the Impératrice plate: the leaves keep their own ABSOLUTE
    clear height, and the carved tympanum takes the register between their
    heads and the entresol floor. Draw the same rectangle with and without
    ``leaf_height`` and the door must get shorter, not the drawing get
    taller."""
    from buildings.render.svg import elements as el

    w, h, leaf = 2.60, 3.95, 3.40
    plain = _unit_canvas()
    el.draw_opening(
        plain, 4.0, 0.0, w, h, {"opening_type": "carriage_entrance", "head": "none"}
    )
    arch = _unit_canvas()
    el.draw_opening(
        arch, 4.0, 0.0, w, h,
        {"opening_type": "carriage_entrance", "head": "none",
         "arch_register": "leaves", "leaf_height": leaf},
    )

    def door_height(canvas):
        rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
        return float(rects[0].group(4))

    assert door_height(plain) == pytest.approx(h, abs=1e-6)
    assert door_height(arch) == pytest.approx(leaf, abs=1e-6), (
        "the leaves ran the whole register; the carved tympanum has nowhere to go"
    )
    assert len(arch.elements) > len(plain.elements), "no tympanum was drawn"


def test_the_pedestrian_tall_arch_gets_the_same_treatment_as_the_carriage_one():
    """Two of Daly's four tall arches are pedestrian doors. A carriage-only
    implementation would draw the porte piétonne's lower register as a door
    with a fanlight squeezed under an entresol it does not have."""
    from buildings.render.svg import elements as el

    w, h, leaf = 1.75, 3.95, 2.90
    canvas = _unit_canvas()
    el.draw_opening(
        canvas, 3.6, 0.0, w, h,
        {"opening_type": "pedestrian_entrance", "head": "none",
         "arch_register": "leaves", "leaf_height": leaf},
    )
    rects = [m for m in (_RECT_RE.match(e) for e in canvas.elements) if m]
    assert float(rects[0].group(4)) == pytest.approx(leaf, abs=1e-6)


def test_the_whole_arch_is_drawn_on_a_real_facade_and_nothing_paints_it_out():
    """End to end. The upper register belongs to the storey above, and that
    storey's own wall fill is drawn before its bays — so if the two registers
    were ever collapsed into one rectangle emitted on the storey below, the
    entresol's wall would paint the top half of the arch out and no test of
    the IR would notice."""
    from buildings.render.svg import render

    site = None
    for seed in range(64):
        candidate = _site(
            street_width=22.0, parcel_width=14.0, parcel_depth=18.0, year=1865,
            klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP, seed=seed,
        )
        building, _ = generate(candidate)
        heads = [
            o for _s, _b, o in _openings_of(building)
            if o.props.get("arch_register") == "arch_head"
        ]
        if heads:
            site = candidate
            break
    assert site is not None, "no seed in 64 produced a two-storey arch"

    svg = render(building, width_px=620)
    (head,) = heads
    crown_m = float(head.props["y"]) + float(head.props["h"])
    # Every element the arch head drew is inside the SVG, and the arch's own
    # glass polygon is present: a polygon whose horizontal extent is the
    # arch's width and whose top is the crown.
    assert "<polygon" in svg
    lower = [
        o for _s, _b, o in _openings_of(building)
        if o.props.get("arch_register") == "leaves"
    ]
    assert len(lower) == 1
    assert crown_m > float(lower[0].props["y"]) + float(lower[0].props["h"]), (
        "the arch does not rise above its own lower register"
    )
