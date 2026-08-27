"""Unit tests for the termination phase (S7) and the end-to-end assembly.

The claims worth testing here are not "the roof has a height". They are:

- the comble is **read off** the gabarit and not invented — change the decree
  and the profile changes, with no line of ``terminate.py`` moving;
- ``Silhouette.within`` genuinely *checks containment*, i.e. it can be made to
  return ``False`` by geometry that breaks out of the envelope, in each of the
  three distinct ways the regulation cares about — and it is anchored at the
  **built eaves**, the égout du toit the règlement springs the comble from
  (A3.1), so it refuses a roof that borrows the cornice's shallower setback;
- the headroom a modest facade leaves unspent reaches the roof by tracing the
  **same curve to a taller top**, paid for in inset, and never by moving the
  springing;
- the roofscape hangs off the same bay grid as the facade below it;
- shape and material are separate axes of the ``roof`` feature family, and
  neither is a period test;
- the whole pipeline runs one way, deterministically, with every element
  carrying its rule.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from buildings.ir.nodes import Node
from buildings.ir.serial import from_json, to_json
from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris import chronology
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.reglement import (
    Era,
    RoofEnvelope,
    compute_envelope,
    era_for_year,
)
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris import structure as structure_module
from buildings.typologies.paris.structure import BRISIS_RISE, solve_structure
from buildings.typologies.paris import terminate
from buildings.typologies.paris.terminate import (
    DORMER_ORNAMENT_VARIANTS,
    ROOF_MATERIAL_VARIANTS,
    Silhouette,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def site(**kw) -> SiteContext:
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


def run(s: SiteContext):
    grid = solve_structure(s)
    roled = assign_roles(grid)
    sil, others = terminate.terminate(grid, roled, s, DecisionStream(s.seed))
    return grid, roled, sil, others


def kind(nodes, k: str) -> list[Node]:
    return [n for n in nodes if n.kind == k]


# ---------------------------------------------------------------------------
# The comble is the residue of the rule, not a shape someone picked
# ---------------------------------------------------------------------------


def test_the_profile_is_the_envelope_and_not_a_second_copy_of_it():
    """Every point of the emitted comble sits exactly on ``setback_at``.

    Not merely inside it — *on* it. "Inscribed" means the brisis takes every
    centimetre of floor the gabarit allows, and a brisis that merely happened
    to be inside would mean this phase had invented a slope of its own that
    the envelope tolerates.

    **A8.3.** Asserted on the BRISIS. What stands above the fold is the
    terrasson and then the flat terrasse, and neither is on the curve: the
    terrasson is a straight run at its own pitch and the terrasse is level.
    That is the roof, not an approximation of the envelope, and asking it to
    lie on ``setback_at`` is asking for the envelope back.
    """
    for year in (1840, 1865, 1890, 1905):
        grid, _, sil, _ = run(site(year=year))
        env = grid.envelope
        eaves = sil.props["eaves_height"]
        brisis = grid.brisis_height
        comble = [(i, y) for i, y in sil.props["points"] if y > eaves + 1e-9]
        assert comble, f"{year}: no comble at all"
        on_the_curve = [(i, y) for i, y in comble if y - eaves <= brisis + 1e-9]
        assert on_the_curve, f"{year}: no brisis at all"
        for inset, y in on_the_curve:
            assert inset == pytest.approx(env.setback_at(y - eaves), abs=1e-9)


def test_the_profile_follows_the_arc_where_the_envelope_samples_it_badly():
    """A chord is inside the envelope but it is not the envelope.

    ``slope_profile`` samples uniformly in height, and near the apex of a
    circular arc — where the curve is nearly horizontal — one step in height
    is a long step in inset. Taken literally its last segment cuts tens of
    centimetres inside the arc — 15 cm here, and 37 cm for a comble built all
    the way to the apex of its arc. Containment cannot see that (a chord
    across a convex region stays inside it), so this is the assertion that
    can: at every height, the emitted polyline is within 3 cm of the curve,
    where the unrefined sampling is five times worse.

    Asked of ``_comble_profile`` directly, tracing the envelope to its own top
    — the call whose two heights coincide, which is what "probe the envelope
    as an envelope" means (A8.3). A whole building no longer supplies this
    case: since A8.3 the brisis stops at whole *chambres de bonne* and the
    terrasson takes it the rest of the way, so no BUILT section runs the curve
    into the near-horizontal apex where the sampling goes bad. The machinery
    that handles it is still here and still has to work — a deeper gabarit or
    a taller band would walk straight back into it — so it is exercised at the
    place it lives rather than left untested because today's numbers dodge it.
    """
    from buildings.typologies.paris.terminate import _comble_profile

    grid, _, _sil, _ = run(
        site(year=1890, street_width=40.0, parcel_depth=22.0, klass=BuildingClass.GRAND)
    )
    env = grid.envelope
    assert env.roof_envelope is RoofEnvelope.CIRCULAR_ARC

    def deviation(points):
        worst = 0.0
        for (i0, h0), (i1, h1) in zip(points, points[1:]):
            if h1 - h0 <= 1e-9:
                continue
            for k in range(1, 16):
                t = k / 16.0
                worst = max(
                    worst,
                    (i0 + (i1 - i0) * t) - env.setback_at(h0 + (h1 - h0) * t),
                )
        return worst

    top = env.ridge_height
    half = env.parcel_depth / 2.0
    emitted = [
        (i, h) for i, h in _comble_profile(env, half, top, top) if h <= top + 1e-9
    ]
    raw = [
        (env.setback_at(min(h, top)), min(h, top)) for _i, h in env.slope_profile(24)
    ]
    assert deviation(raw) > 0.1, "the sampling this guards against was harmless after all"
    assert deviation(emitted) < 0.03


def test_a_straight_envelope_gains_no_extra_vertices_from_refinement():
    """Subdivision is driven by the curve, not applied by the metre: the 45°
    diagonal deviates by nothing, so the brisis stays one segment."""
    grid, _, sil, _ = run(site(year=1865))
    assert grid.envelope.roof_envelope is RoofEnvelope.DIAGONAL_45
    eaves = sil.props["eaves_height"]
    brisis = grid.brisis_height
    comble = [(i, y) for i, y in sil.props["points"] if y > eaves + 1e-9]
    on_the_curve = [(i, y) for i, y in comble if y - eaves <= brisis + 1e-9]
    assert len(on_the_curve) == 1, on_the_curve  # the fold, and nothing before it
    # ...and above it, the terrasson and the flat terrasse: three points for a
    # Second Empire comble brisé, and never more (A8.3).
    assert len(comble) <= 3, comble


def test_the_three_regimes_produce_three_visibly_different_profiles():
    """G7's second clause: pre-1884 a 45° plane, 1884+ arc-derived — visible
    in the IR, not in a comment."""
    shapes = {}
    for year in (1865, 1890, 1905):
        grid, _, sil, _ = run(site(year=year))
        eaves = sil.props["eaves_height"]
        comble = [(i, y - eaves) for i, y in sil.props["points"] if y > eaves + 1e-9]
        shapes[year] = comble

    # 1859: a straight diagonal, so the brisis is one segment — the fold and
    # nothing between. Above it the terrasson and the flat terrasse (A8.3).
    diag = shapes[1865]
    assert len(diag) <= 3
    inset, h = diag[0]
    assert inset == pytest.approx(h, abs=1e-9), "pre-1884 brisis is not at 45°"

    # 1884: an arc — many samples, near-vertical at the eaves, and strictly
    # convex, which a straight line is not.
    arc = shapes[1890]
    assert len(arc) > 10
    first_inset, first_h = arc[0]
    assert first_inset < first_h * 0.25, "the 1884 arc should leave the eaves near-vertical"
    slopes = [
        (arc[i + 1][0] - arc[i][0]) / (arc[i + 1][1] - arc[i][1])
        for i in range(len(arc) - 3)
    ]
    assert all(b > a for a, b in zip(slopes, slopes[1:])), "the arc is not curving"

    # 1902: the arc runs onto a 45° oblique, so the profile has a break in it
    # and the final segment is a straight 45°.
    obl = shapes[1905]
    (i0, h0), (i1, h1) = obl[-3], obl[-2]
    assert (i1 - i0) == pytest.approx(h1 - h0, rel=0.02), "the 1902 oblique is not at 45°"


def test_a_wider_street_earns_a_bigger_comble_after_1884_and_not_before():
    """The arc radius depends on street width (1884); the 45° cap does not.

    This is the regulation showing through the geometry: before 1884 the
    comble is capped at a flat ``max_roof_height`` whatever the street, and
    after it the envelope itself grows with the street.
    """
    narrow_1865 = run(site(year=1865, street_width=8.0))[0].envelope
    wide_1865 = run(site(year=1865, street_width=30.0))[0].envelope
    assert narrow_1865.ridge_height == pytest.approx(wide_1865.ridge_height)

    narrow_1890 = run(site(year=1890, street_width=8.0))[0].envelope
    wide_1890 = run(site(year=1890, street_width=30.0))[0].envelope
    assert wide_1890.ridge_height > narrow_1890.ridge_height + 0.5


def test_the_comble_springs_from_the_built_eaves_not_the_legal_ceiling():
    """A building that stopped short of its ceiling carries its roof down
    with it — the diagonal springs from the égout du toit."""
    grid, _, sil, others = run(site(klass=BuildingClass.MODEST))
    assert grid.built_height < float(grid.cornice_height) - 1.0
    assert sil.props["eaves_height"] == pytest.approx(grid.built_height)
    roof = kind(others, "roof")[0]
    assert roof.props["y"] == pytest.approx(grid.built_height)
    # ...and the whole thing still fits under the legal total.
    assert sil.props["ridge_height"] <= grid.envelope.total_height + 1e-9


# ---------------------------------------------------------------------------
# Where the comble folds (A12.1)
# ---------------------------------------------------------------------------


def _comble_of(sil):
    """The comble part of a silhouette as ``(inset, height over the eaves)``."""
    eaves = sil.props["eaves_height"]
    return [(i, y - eaves) for i, y in sil.props["points"] if y > eaves + 1e-9]


def _apron_of(*nodes) -> float:
    """The lucarne apron this comble was solved with, off its own trace.

    **A30.** The apron is the deeper of the plumber's zinc (0.35 m) and the
    cornice standing on the same eaves, and the cornice is a fraction of the
    storey it crowns — so it is not a constant and these tests may not write
    one. ``terminate`` states it on the trace for exactly this reason.
    """
    for node in nodes:
        for entry in (node.trace or ()):
            if entry.inputs and "lucarne_apron" in entry.inputs:
                return float(entry.inputs["lucarne_apron"])
    raise AssertionError("no lucarne_apron on the trace — A30 stopped stating it")


def test_the_fold_is_where_the_terrasson_reaches_the_ridge():
    """A12.1 on the canonical case, with the answer it replaced named.

    A 3.20 m comble on a 16 m parcel used to be traced as ``(2.90, +2.90) →
    (4.311, +3.20) → (8.00, +3.20)``: a 45° brisis for 90.6 % of the height, a
    0.30 m terrasson, and 3.69 m of flat zinc. Every one of those numbers is a
    legal, inscribed, correctly-derived roof, and at facade scale it reads as
    a slab with a nick near the top.

    The section is over-determined once the terrasson's pitch is fixed, so the
    same three numbers are read the other way round — the terrasson arrives at
    the ridge in the middle of the plot, and the brisis folds where that line
    crosses the gabarit. The ridge does not move: the comble height is the
    decree's, and it is what Daly measured (median 3.19 m against 3.20 m).
    """
    s = site(parcel_depth=16.0)
    grid, _, sil, others = run(s)
    env = grid.envelope
    roof = kind(others, "roof")[0]
    comble = _comble_of(sil)

    # The height did not move.
    assert roof.props["h"] == pytest.approx(3.20, abs=0.005)
    assert roof.props["h"] == pytest.approx(grid.comble_height, abs=1e-9)

    # **A30 — on this section the LUCARNE floor now binds, not the ridge.**
    # The fold may not drop below the shortest brisis that carries a lucarne,
    # and A30 corrected the first term of that sum: the apron under a lucarne
    # is the deeper of the plumber's zinc and the cornice crowning the same
    # eaves, not the zinc alone. Here that is 0.502 m rather than 0.350 m, so
    # the floor rises from 1.900 to 2.052 m — above the 1.904 m at which the
    # terrasson would have met the ridge — and the fold stops on the floor.
    #
    # The terrasson therefore tops out just short of mid-depth and leaves a
    # deck. That is A12.1's own third rule doing what it says, not the defect
    # A12.1 removed: the deck it removed was 3.69 m of a 8.0 m half-depth, and
    # this one is 0.55 m. The assertion below pins the difference rather than
    # merely allowing a deck.
    apron = _apron_of(sil, roof)
    assert len(comble) == 3
    (fold_inset, fold_h), (reach_inset, reach_h), (ridge_inset, ridge_h) = comble
    assert ridge_h == pytest.approx(grid.comble_height, abs=1e-9)
    assert reach_h == pytest.approx(grid.comble_height, abs=1e-9)
    assert ridge_inset == pytest.approx(8.0, abs=1e-9)
    assert fold_h == pytest.approx(apron + 1.30 + 0.25, abs=1e-6), (
        "the fold sits on the shortest brisis that carries a lucarne, "
        "measured with the apron A30 corrected"
    )
    assert fold_h == pytest.approx(2.052, abs=0.005)
    assert fold_h / ridge_h == pytest.approx(0.641, abs=0.005)
    # The deck is the small one, not the slab A12.1 was raised on.
    assert 8.0 - reach_inset == pytest.approx(0.546, abs=0.01)
    assert 8.0 - reach_inset < 1.0, "the 3.69 m of flat zinc must not return"

    # ...and the answer this replaced, so a regression to it reads as one.
    assert grid.brisis_height / grid.comble_height == pytest.approx(0.906, abs=0.005)
    assert fold_h < grid.brisis_height - 0.8

    # The fold slid DOWN the envelope; it did not leave it.
    assert fold_inset == pytest.approx(env.setback_at(fold_h), abs=1e-12)

    # Both slopes, as a consumer reads them.
    assert math.degrees(math.atan2(fold_h, fold_inset)) == pytest.approx(45.0, abs=0.01)
    terrasson = math.degrees(
        math.atan2(reach_h - fold_h, reach_inset - fold_inset)
    )
    assert terrasson == pytest.approx(12.0, abs=0.01)
    assert roof.props["lower_angle_deg"] == pytest.approx(45.0, abs=0.01)
    assert roof.props["upper_angle_deg"] == pytest.approx(12.0, abs=0.01)
    assert roof.props["break_pct"] == pytest.approx(fold_h / ridge_h, abs=1e-12)
    assert roof.props["has_terrasse"] is True  # A30: the small deck above
    assert Silhouette(sil.props["points"]).within(env)


def test_the_terrassons_pitch_is_the_one_structure_gave_it():
    """The fold moved; the terrasson did not change its mind about its pitch.

    Read off ``structure``'s own three numbers — the fold it states, the ridge
    it states, and how far back it states the ridge stands — and compared with
    the slope this phase actually cut. A second copy of the pitch constant in
    this module would be the way the two come apart, so there is not one.
    """
    for depth in (11.0, 14.0, 16.0, 22.0):
        for year in (1865, 1890):
            grid, _, sil, others = run(site(parcel_depth=depth, year=year))
            env = grid.envelope
            roof = kind(others, "roof")[0]
            if roof.props["h"] <= grid.brisis_height + 1e-9:
                continue  # no terrasson at all
            wall_inset = env.setback_at(grid.brisis_height)
            if grid.ridge_setback <= wall_inset + 1e-6:
                continue
            stated = (grid.comble_height - grid.brisis_height) / (
                grid.ridge_setback - wall_inset
            )
            comble = _comble_of(sil)
            (fold_inset, fold_h) = comble[-2]
            (top_inset, top_h) = comble[-1]
            if top_h <= fold_h + 1e-9:
                (fold_inset, fold_h), (top_inset, top_h) = comble[-3], comble[-2]
            cut = (top_h - fold_h) / (top_inset - fold_inset)
            assert cut == pytest.approx(stated, abs=1e-9), (
                f"{year}, depth {depth} m: cut {math.degrees(math.atan(cut)):.3f}°, "
                f"structure gave {math.degrees(math.atan(stated)):.3f}°"
            )


def test_the_fold_never_stands_above_the_rooms_behind_it():
    """The brisis is the garret's outside wall, so the section may fold below
    that wall — it is a roof over rooms, not a wall — but never above it."""
    for depth in (8.0, 11.0, 14.0, 16.0, 22.0, 30.0):
        for year in (1830, 1865, 1890, 1905):
            for width in (6.0, 12.0, 20.0, 30.0):
                grid, _, _, others = run(
                    site(parcel_depth=depth, year=year, street_width=width)
                )
                roof = kind(others, "roof")[0]
                fold = roof.props["h"] * roof.props["break_pct"]
                assert fold <= min(grid.brisis_height, grid.comble_height) + 1e-9, (
                    f"{year}, {width} m street, {depth} m parcel: the section folds at "
                    f"{fold:.3f} m, above the {grid.brisis_height:.3f} m of garret wall"
                )


def test_the_lucarne_comes_down_with_the_brisis():
    """A12.1's own constraint: if the brisis shortens the lucarne follows it.

    The face is not a constant and never was (A8.3) — it is the band of brisis
    it stands in, less the plumber's skirt and the head. What changed is which
    brisis: the fold this phase cuts, so a lucarne on a 1.90 m brisis is a
    1.30 m window and not the 2.30 m one a 2.90 m garret wall would carry
    overhanging the fold.
    """
    grid, _, sil, others = run(site(parcel_depth=16.0))
    eaves = sil.props["eaves_height"]
    roof = kind(others, "roof")[0]
    fold = roof.props["h"] * roof.props["break_pct"]
    dormers = kind(others, "dormer")
    assert dormers, "the canonical comble must still carry its lucarnes"
    for d in dormers:
        head = d.props["y"] + d.props["h"] - eaves
        assert head <= fold + 1e-9, (
            f"a lucarne head at {head:.3f} m overhangs a fold at {fold:.3f} m"
        )
    # It is the FOLD it fills, not the garret wall: on the wall it would be
    # a metre taller, and a metre out of the roof.
    #
    # **A30: less the APRON, not less the plumber's zinc.** The zinc is
    # 0.35 m and a constant; the apron is the deeper of it and the cornice
    # crowning the same eaves, which is a fraction of a class-scaled storey.
    # Writing 0.35 here pinned a building whose cornice happened to be
    # shallower than its zinc.
    apron = _apron_of(sil, roof)
    assert apron >= 0.35
    assert dormers[0].props["h"] == pytest.approx(fold - apron - 0.25, abs=0.005)
    assert dormers[0].props["h"] < grid.brisis_height - apron - 0.25 - 0.8


def test_a_parcel_deep_enough_keeps_the_terrasse_it_earns():
    """The flat deck is not abolished; it is moved to the plots that have one.

    A terrasson cannot reach the ridge from a fold that is under the window it
    carries, so on a deep parcel the fold stops at the lucarne, the terrasson
    tops out where it tops out, and the rest of the plot is flat zinc. That is
    the case the amendment leaves alone — and it still folds far lower than
    the garret wall would have.
    """
    grid, _, sil, others = run(site(parcel_depth=22.0, street_width=6.0, year=1830))
    roof = kind(others, "roof")[0]
    fold = roof.props["h"] * roof.props["break_pct"]
    assert roof.props["has_terrasse"] is True
    assert roof.props["ridge_setback"] < 22.0 / 2.0 - 1.0
    # The fold stopped at the shortest brisis with a window in it — measured
    # with A30's apron, the deeper of the plumber's zinc and the cornice, so
    # this is no longer 0.35 + 1.30 + 0.25.
    apron = _apron_of(sil, roof)
    assert fold == pytest.approx(apron + 1.30 + 0.25, abs=1e-6)
    assert fold < grid.brisis_height - 0.5
    # ...and the window is still there.
    assert kind(others, "dormer")
    assert Silhouette(sil.props["points"]).within(grid.envelope)

    # Deeper still and the terrasson could not reach the ridge from the eaves
    # themselves, never mind from a fold: that plot keeps the whole section
    # structure states, garret wall and all, and its deck is the biggest one
    # in the city.
    grid, _, sil, others = run(site(parcel_depth=34.0, street_width=6.0, year=1830))
    roof = kind(others, "roof")[0]
    fold = roof.props["h"] * roof.props["break_pct"]
    assert roof.props["has_terrasse"] is True
    assert fold == pytest.approx(min(grid.brisis_height, grid.comble_height), abs=1e-9)
    assert roof.props["ridge_setback"] == pytest.approx(grid.ridge_setback, abs=1e-9)
    assert kind(others, "dormer")
    assert Silhouette(sil.props["points"]).within(grid.envelope)


def test_lowering_the_fold_did_not_lift_a_single_ridge():
    """The whole amendment, stated as what it must NOT have done.

    The comble height is calibrated against Daly's sixteen measured buildings
    and is not on the table: whatever the fold does, ``roof.h`` is still
    ``grid.comble_height``, which is still the decree's own allowance sprung
    from these eaves.
    """
    for depth in (8.0, 14.0, 22.0):
        for year in (1830, 1865, 1890, 1905):
            for klass in BuildingClass:
                grid, _, sil, others = run(
                    site(parcel_depth=depth, year=year, klass=klass)
                )
                roof = kind(others, "roof")[0]
                assert roof.props["h"] == pytest.approx(grid.comble_height, abs=1e-9)
                assert sil.props["ridge_height"] == pytest.approx(
                    grid.built_height + grid.comble_height, abs=1e-9
                )


# ---------------------------------------------------------------------------
# `within` genuinely checks containment
# ---------------------------------------------------------------------------


def test_within_accepts_the_silhouette_this_phase_builds():
    for year in (1830, 1865, 1890, 1905):
        grid, _, sil, _ = run(site(year=year))
        assert Silhouette(sil.props["points"]).within(grid.envelope)


def test_within_rejects_a_comble_that_breaks_the_slope():
    """Push one point forward of the envelope: it must be caught.

    A containment test that cannot fail on a forward-projecting roof is not
    checking containment, it is checking that a tuple is non-empty.

    The line the point is dragged through is the one springing from the
    building's own **eaves** (A3.1) — the égout du toit, which is where the
    règlement springs the diagonal. The assertion states which line was broken
    rather than merely that something was.
    """
    grid, _, sil, _ = run(site(year=1890))
    env = grid.envelope
    pts = list(sil.props["points"])
    eaves = sil.props["eaves_height"]
    assert Silhouette(tuple(pts)).within(env)

    # A point of the arc, dragged 20 cm forward of the setback the decree
    # requires at that height above the EAVES.
    n = next(i for i, (_i, yy) in enumerate(pts) if yy > eaves + 1e-9)
    inset, y = pts[n]
    legal_inset = env.setback_at(y - eaves)
    assert inset == pytest.approx(legal_inset, abs=1e-9), (
        "this phase builds its comble on the envelope sprung from the eaves, so the "
        "point should be sitting exactly on that line before it is pushed"
    )
    pts[n] = (legal_inset - 0.20, y)
    broken = Silhouette(tuple(pts))
    assert not broken.within(env)
    assert broken.clearance(env) == pytest.approx(-0.20, abs=1e-6)


def test_within_rejects_a_ridge_above_the_legal_comble():
    grid, _, sil, _ = run(site(year=1865))
    env = grid.envelope
    pts = list(sil.props["points"])
    inset, y = pts[-1]
    # Raise the ridge clear of the legal total — the top of the solid the
    # envelope describes, cornice plus comble — keeping it legally set back,
    # so only the height clause can catch this one.
    lift = env.total_height + 1.0 - y
    assert lift > 0.0
    pts[-1] = (inset + lift, y + lift)
    assert not Silhouette(tuple(pts)).within(env)


def test_within_rejects_a_facade_taller_than_its_street_earns():
    grid, _, sil, _ = run(site(year=1865))
    env = grid.envelope
    pts = list(sil.props["points"])
    over = env.facade_height + 2.0
    raised = [(0.0, 0.0), (0.0, over)] + [(i, y - pts[1][1] + over) for i, y in pts[2:]]
    assert not Silhouette(tuple(raised)).within(env)


def test_within_rejects_something_hanging_over_the_street():
    grid, _, sil, _ = run(site(year=1865))
    pts = list(sil.props["points"])
    pts.insert(1, (-0.5, pts[1][1] / 2.0))
    assert not Silhouette(tuple(pts)).within(grid.envelope)


def test_within_is_not_vacuously_true_for_arbitrary_polylines():
    """Belt and braces: a silhouette twice the legal height fails everywhere."""
    for year in (1830, 1865, 1890, 1905):
        grid, _, sil, _ = run(site(year=year))
        env = grid.envelope
        doubled = tuple((i, y * 2.0) for i, y in sil.props["points"])
        assert not Silhouette(doubled).within(env)


def test_clearance_reports_the_margin_it_measures():
    """Each clearance reports the breach of the line *it* measures against.

    The comble this phase builds sits exactly on the envelope sprung from the
    built eaves, so pushing one of its points in by 37 cm is a 37 cm breach of
    that line — which is what ``clearance``, the legal margin, reports exactly.
    Against the weaker cornice line the same point is still 37 cm worse off
    than it was, but it started with the facade's unused headroom in hand, so
    the number that query reports is 37 cm less than the margin it had; the
    assertions below pin both, and pin the ordering between them (A3.1).
    """
    grid, _, sil, _ = run(site(year=1890))
    env = grid.envelope
    s = Silhouette(sil.props["points"])
    assert s.clearance(env) >= -1e-9
    assert s.clearance_from_the_cornice(env) >= -1e-9
    assert s.clearance_from_the_cornice(env) >= s.clearance(env) - 1e-9

    pts = list(s.points)
    mid = len(pts) // 2
    inset, y = pts[mid]
    assert y > s.eaves_height
    # This point sits on the envelope over the built eaves, so a push of 37 cm
    # is a 37 cm breach of that line and nothing else.
    assert inset == pytest.approx(env.setback_at(y - s.eaves_height), abs=1e-9)

    def pushed(by: float) -> Silhouette:
        return Silhouette(tuple(pts[:mid] + [(inset - by, y)] + pts[mid + 1 :]))

    assert pushed(0.37).clearance(env) == pytest.approx(-0.37, abs=1e-6)

    # The cornice line at that height sits further forward by exactly the
    # headroom the facade did not use, so breaching *it* by 20 cm takes that
    # much more of a push — and that query then reports 20 cm, not the total
    # distance the point travelled. It is the weaker line, and it is not the
    # one legality is measured against.
    headroom_here = inset - env.setback_at(y - env.facade_height)
    assert headroom_here > 0.0
    assert pushed(headroom_here + 0.20).clearance_from_the_cornice(
        env
    ) == pytest.approx(-0.20, abs=1e-6)


# ---------------------------------------------------------------------------
# A3.1 — containment springs from the built eaves; the headroom comes back
# as a taller top on the same curve, not as a moved springing
# ---------------------------------------------------------------------------


def _comble_sprung_from_the_cornice(env, eaves: float) -> Silhouette:
    """A facade stopping short at ``eaves``, carrying a comble whose slope is
    reckoned from the LEGAL CORNICE — ridge at ``env.total_height``, set back
    only ``setback_at(env.ridge_height)``.

    This is the shape A2.4 made ``within`` accept, and it is illegal (A3.1):
    the règlement springs the diagonal from the égout du toit, so a roof that
    starts at ``eaves`` and reaches ``total_height`` must be set back by
    ``setback_at(total_height - eaves)``, which is more. A building that
    stopped its stone short does not get to bank the difference.
    """
    return Silhouette(
        (
            (0.0, 0.0),
            (0.0, eaves),
            (env.setback_at(env.ridge_height), env.facade_height + env.ridge_height),
        )
    )


def test_within_refuses_a_comble_sprung_from_the_cornice_rather_than_the_eaves():
    """The retraction of A2.4, stated as the case it used to get wrong.

    A comfortable 1865 building on a 20 m street stops short of the height its
    street earns. A comble reaching ``env.total_height`` from those eaves is
    legal *only* if it is inscribed below the 45° diagonal springing from the
    eaves — i.e. set back by ``setback_at(total_height - eaves)``. Take the
    shallower setback the cornice line would allow and the roof stands in space
    the decree forbids, and ``within`` must say so.

    A2.4 anchored ``within`` at the cornice and accepted exactly this shape.
    That amendment is retracted; the eaves-anchored behaviour it replaced was
    legally right all along.
    """
    grid, _, _sil, _ = run(site(year=1865, klass=BuildingClass.COMFORTABLE))
    env = grid.envelope
    eaves = grid.built_height
    headroom = env.facade_height - eaves
    # A fixture tripwire, not a claim: this case is only worth running while
    # the building actually stops short, because that gap IS the difference
    # between the two anchorings. The figure moved from 1.0028 to 0.7020 when
    # A16.2 repriced the garret trade from 4.01 m to the band's own height,
    # and it will move again the next time that price is derived differently.
    assert headroom == pytest.approx(0.7020, abs=1e-3), (
        f"the harness case moved: headroom is now {headroom:.4f} m"
    )
    assert headroom > 0.0

    sprung_from_the_cornice = _comble_sprung_from_the_cornice(env, eaves)
    assert sprung_from_the_cornice.ridge_height == pytest.approx(
        env.total_height, abs=1e-9
    )

    assert not sprung_from_the_cornice.within(env), (
        "`within` accepted a comble the 45° diagonal from the real eaves forbids — "
        "that is the A2.4 behaviour, and it is retracted"
    )
    assert sprung_from_the_cornice.clearance(env) < -0.5
    # The weaker query is what it always was, and it is kept only to report
    # that gap. It is not legality.
    assert sprung_from_the_cornice.within_the_gabarit_from_the_cornice(env)

    # The lawful shape reaching the same ridge height: same springing, same
    # curve, taller top — and it costs the extra inset the decree charges.
    honest_setback = env.setback_at(env.total_height - eaves)
    lawful = Silhouette(((0.0, 0.0), (0.0, eaves), (honest_setback, env.total_height)))
    assert lawful.within(env)
    assert honest_setback > env.setback_at(env.ridge_height)


def test_within_implies_the_cornice_query_and_never_the_reverse():
    """The two anchors are ordered, which is what makes it safe to keep both.

    The eaves sit at or below the cornice and ``setback_at`` is non-decreasing,
    so every setback ``within`` demands is at least the one the cornice query
    asks for. The legality test is therefore the harder of the two, which is
    the right way round: anything that passes only the weaker one is a comble
    standing where the diagonal from its own eaves forbids.
    """
    saw_a_gap = False
    for year in (1830, 1865, 1890, 1905):
        for klass in BuildingClass:
            grid, _, sil, _ = run(site(year=year, klass=klass))
            env = grid.envelope
            s = Silhouette(sil.props["points"])
            assert s.within(env)
            assert s.within_the_gabarit_from_the_cornice(env)
            assert s.clearance_from_the_cornice(env) >= s.clearance(env) - 1e-9

            # ...and the implication is strict somewhere: a comble sprung from
            # the cornice passes the weak query and fails legality.
            if env.facade_height - grid.built_height > 0.25 and env.ridge_height > 0.5:
                cheating = _comble_sprung_from_the_cornice(env, grid.built_height)
                assert cheating.within_the_gabarit_from_the_cornice(env)
                assert not cheating.within(env)
                saw_a_gap = True
    assert saw_a_gap, "no building in this set left any headroom to argue about"


def test_within_still_refuses_a_roof_above_the_legal_total():
    """The eaves anchoring is not the only clause: the ceiling is
    ``env.total_height``, and a centimetre past it is still illegal."""
    for year in (1830, 1865, 1890, 1905):
        grid, _, _sil, _ = run(site(year=year, klass=BuildingClass.MODEST))
        env = grid.envelope
        eaves = grid.built_height
        # Set back by exactly what the eaves-sprung envelope demands at that
        # height, so the slope clause is satisfied and only the ceiling can
        # catch this one.
        top = env.total_height + 0.10
        over = Silhouette(
            ((0.0, 0.0), (0.0, eaves), (env.setback_at(top - eaves), top))
        )
        assert over.points[-1][0] >= env.setback_at(top - eaves) - 1e-9, year
        assert not over.within(env), year


_SWEEP_WIDTHS = (6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0, 24.0, 30.0, 34.0, 40.0)
_SWEEP_YEARS = (1830, 1860, 1875, 1890, 1905)


def test_every_silhouette_in_the_s7_sweep_is_inscribed_from_its_own_eaves():
    """A3.1's acceptance condition, over the sweep A2.4 named.

    Widths 6–40 m x 1830/1860/1875/1890/1905, every class: every point of every
    silhouette is inscribed below the envelope springing from that building's
    own eaves, which is the legal question. The weaker cornice query follows
    from it and is checked only to confirm the ordering did not invert.

    The sweep has to contain buildings that stopped short of their ceiling, or
    the two lines coincide everywhere and nothing here is being exercised.
    """
    seen = 0
    headroom_seen = 0.0
    for i, width in enumerate(_SWEEP_WIDTHS):
        for j, year in enumerate(_SWEEP_YEARS):
            klass = list(BuildingClass)[(i + j) % len(BuildingClass)]
            grid, _, sil, _ = run(site(street_width=width, year=year, klass=klass))
            env = grid.envelope
            s = Silhouette(sil.props["points"])
            assert s.within(env), (
                f"{width} m / {year} / {klass.value}: outside the envelope sprung from "
                f"its own eaves by {s.clearance(env):+.4f} m"
            )
            assert s.within_the_gabarit_from_the_cornice(env), (
                f"{width} m / {year} / {klass.value}: the weaker query failed where the "
                f"stronger one passed, so the ordering has inverted "
                f"({s.clearance_from_the_cornice(env):+.4f} m)"
            )
            headroom_seen = max(headroom_seen, env.facade_height - grid.built_height)
            seen += 1
    assert seen == len(_SWEEP_WIDTHS) * len(_SWEEP_YEARS)
    assert headroom_seen > 1.0, (
        "the sweep never produced a building that stopped short of its ceiling, so "
        "it cannot have exercised the difference between the two anchorings"
    )


def test_the_comble_this_phase_builds_stops_below_the_top_of_the_legal_solid():
    """A8.5, asked of the BUILDING and not of the predicate.

    The canonical case is the one the amendments name: a comfortable 1865
    immeuble on a 20 m boulevard, eaves at 16.85 m against a 17.55 m legal
    cornice, gabarit topping out at 20.75 m. Its ridge stands at 20.05 m —
    0.70 m of legal solid it had no use for.

    That gap is the whole of A8.5. The comble used to reach 20.75 m, because
    it was carried up to the ceiling and the ceiling recovers the cornice
    height the facade declined (A3.1). So the roof grew by exactly what the
    stone gave up, the sum never moved, and every building in Paris came out
    at ``legal_total_height`` whatever its class. What is built now is the
    decree's own comble allowance sprung from these eaves, which is the same
    roof a building that HAD reached its ceiling would carry, just lower down.

    A3.1 itself is untouched and still asserted here: the springing is the
    eaves, the ceiling over them still contains the recovered headroom, and
    the comble stays under it.
    """
    grid, _, sil, others = run(site())
    env = grid.envelope
    eaves = grid.built_height
    headroom = env.facade_height - eaves
    assert headroom == pytest.approx(0.7020, abs=1e-3), (
        f"the canonical case moved: headroom is now {headroom:.4f} m"
    )

    ridge = sil.props["ridge_height"]
    assert ridge == pytest.approx(eaves + env.ridge_height, abs=1e-9)
    # The answer this replaced, named so a regression to it reads as one.
    #
    # Stated as the exact relation rather than as "short by more than a
    # metre". The margin used to be 1.0028 m and A16.2 brought it to 0.7020,
    # which would have taken a crude ``> 1.0`` threshold down with it — and a
    # threshold that has to be relaxed whenever a price is corrected was never
    # measuring the claim. The claim is that the roof did NOT recover the
    # cornice height the facade declined, so what the gabarit has left over
    # its ridge is exactly the headroom the stone gave up, to the millimetre.
    assert env.total_height - ridge == pytest.approx(headroom, abs=1e-9), (
        "the comble grew into the height the facade declined — that is the "
        "pre-A8.5 behaviour, where every building came out at its ceiling"
    )
    assert grid.comble_ceiling - grid.comble_height == pytest.approx(
        headroom, abs=1e-9
    )
    assert ridge < env.total_height
    assert grid.comble_ceiling == pytest.approx(env.ridge_height + headroom, abs=1e-9)

    roof = kind(others, "roof")[0]
    assert roof.props["h"] == pytest.approx(grid.comble_height, abs=1e-9)
    assert roof.props["ridge_height"] == pytest.approx(ridge, abs=1e-9)
    # A8.3: the ridge stands where the terrasson got to. It is NOT
    # ``setback_at(comble_height)``: that is where the BRISIS would have
    # reached the ridge had the roof been one plane, which is the envelope
    # restated as a roof.
    #
    # **A12.1**: on this parcel it gets to the middle. The terrasson used to
    # top out at 4.31 m back and leave 2.69 m of flat zinc, which is the same
    # section read the other way round — fold near the ridge, then flatten —
    # and it put the fold at 90.6 % of a 3.20 m comble. The comble is the same
    # height either way; only one of them is a comble brisé.
    assert roof.props["ridge_setback"] == pytest.approx(env.parcel_depth / 2.0, abs=1e-9)
    assert roof.props["ridge_setback"] > env.setback_at(grid.comble_height) + 1.0
    assert roof.props["ridge_setback"] > grid.ridge_setback + 1.0
    assert roof.props["has_terrasse"] is False

    # ...and it is legal, measured from the eaves it actually springs from.
    assert Silhouette(sil.props["points"]).within(env)


def test_the_comble_is_the_decrees_own_across_the_situation_space():
    """Not one case. Wherever the parcel is not what caps the roof, the comble
    over the eaves is exactly the comble the decree allows over the cornice —
    no more (A8.5: it used to swallow the unbuilt facade headroom) and no less
    (A3.1: it must not be shortened by that headroom either).

    **A15.1** adds the one lawful way past that allowance and no other: a
    whole further storey of *chambres de bonne*, bought out of the cornice
    height, and visible as a storey in the grid. So the bound rises by whole
    rooms and by nothing continuous, and the unbuilt headroom is still not a
    target — which is the half of A8.5 that had to survive."""
    seen = 0
    for width in _SWEEP_WIDTHS:
        for year in _SWEEP_YEARS:
            for klass in BuildingClass:
                s = site(street_width=width, year=year, klass=klass, parcel_depth=30.0)
                grid, _, sil, _ = run(s)
                env = grid.envelope
                headroom = env.facade_height - grid.built_height
                comble = sil.props["ridge_height"] - grid.built_height
                if env.max_height_for_setback(15.0) < env.ridge_height - 1e-9:
                    continue  # the parcel, not the gabarit, is what stopped it
                bought = grid.extra_garret_storeys * float(BRISIS_RISE)
                assert bought in (0.0, float(BRISIS_RISE)), grid.extra_garret_storeys
                if bought:
                    # It was bought, so the stone gave it up: the roof stands
                    # one more whole room and the cornice one fewer.
                    assert len(grid.comble_storeys) == (
                        1 + structure_module._garret_storeys_the_decree_stands(
                            env, s.parcel_depth
                        )
                    )
                assert comble <= env.ridge_height + bought + 1e-9, (
                    f"{width} m / {year} / {klass.value}: the comble overran the "
                    "decree's own allowance sprung from these eaves, plus the "
                    f"{grid.extra_garret_storeys} whole storey(s) of chambres de "
                    "bonne this building bought out of its cornice"
                )
                assert comble == pytest.approx(grid.comble_height, abs=1e-9)
                assert comble <= grid.comble_ceiling + 1e-9
                if headroom > 0.25 and env.max_height_for_setback(15.0) > (
                    env.ridge_height + headroom
                ):
                    seen += 1
                    assert grid.comble_ceiling == pytest.approx(
                        env.ridge_height + headroom, abs=1e-9
                    ), (
                        f"{width} m / {year} / {klass.value}: the ceiling did not rise "
                        "with the unbuilt headroom, so A3.1 has been undone too"
                    )
                    # The roof was not built to its ceiling — A8.5's whole
                    # substance. A building that bought a storey of garret has
                    # spent part of the gap on rooms, so the margin left is
                    # smaller; what may never happen, in either case, is the
                    # roof arriving AT the line.
                    assert grid.comble_ceiling > comble + (0.10 if bought else 0.25), (
                        f"{width} m / {year} / {klass.value}: the roof was built to "
                        f"its own ceiling ({comble:.3f} m against "
                        f"{grid.comble_ceiling:.3f} m)"
                    )
                    # And it stopped where the ROOMS stopped: a whole number of
                    # chambres de bonne, or the plot.
                    assert comble >= grid.brisis_height - 1e-9
                    bands = grid.brisis_height / float(BRISIS_RISE)
                    assert (
                        abs(bands - round(bands)) < 1e-6
                        or abs(grid.brisis_height - comble) < 1e-6
                    ), (width, year, klass, grid.brisis_height)
    assert seen > 20, f"only {seen} situations left any headroom unspent"


def test_the_taller_top_is_the_same_curve_carried_higher():
    """A3.1 §2, as geometry rather than as a height.

    The recovered headroom must not change *what* the comble is, only how far
    up it runs. So the profile this phase emits for the taller top and the
    profile the envelope would trace for the shorter one are points on one
    curve, sprung from one place: the shorter profile is what the taller one
    looks like below the shorter one's ridge, to the last decimal.

    That is what ``slope_profile(top=...)`` is for, and it is why the taller
    top costs inset — the price the règlement charges for height. It is also
    why the recovery is only ever *partial*: the curve itself may run out (an
    1884 arc goes horizontal at its apex and cannot be carried higher at any
    price) or the plot may, and either one stops the top below the gabarit
    while the springing stays exactly where it was.
    """
    from buildings.typologies.paris.terminate import _comble_profile

    carried_far = 0
    under_the_ceiling = 0
    for year in (1865, 1890, 1905):
        # A deep parcel, so it is the gabarit and the curve — not the plot —
        # that decide where the taller top lands.
        grid, _, _sil, _ = run(
            site(year=year, klass=BuildingClass.MODEST, parcel_depth=30.0)
        )
        env = grid.envelope
        half = env.parcel_depth / 2.0
        headroom = env.facade_height - grid.built_height
        assert headroom > 0.25, f"{year}: nothing to recover"

        # The CEILING, carried on the same curve, against the envelope's own
        # top. A8.5 moved what gets BUILT off the ceiling, but the ceiling is
        # still what A3.1 is about and it is still the thing this test traces.
        tall = _comble_profile(env, half, grid.comble_ceiling)
        short = _comble_profile(env, half, env.ridge_height)

        # Both spring from the same point — the eaves, at (0, 0).
        assert tall[0] == (0.0, 0.0)
        assert short[0] == (0.0, 0.0)

        # Both are on the same curve: every point satisfies `setback_at` at its
        # own height above that one springing.
        for profile in (tall, short):
            for inset, h in profile[:-1]:
                assert inset == pytest.approx(env.setback_at(h), abs=1e-9), year

        # The taller top is higher, and it paid for it in inset.
        tall_ridge_h = max(h for _i, h in tall)
        short_ridge_h = max(h for _i, h in short)
        if tall_ridge_h <= short_ridge_h + 1e-9:
            # The curve itself ran out — an 1884 arc goes horizontal at its
            # apex and cannot be carried higher at any price — so there is no
            # taller top to compare. The docstring names this case; it is not
            # a failure, it is the reason the recovery is only ever partial.
            assert grid.comble_height == pytest.approx(short_ridge_h, abs=1e-9), year
            continue
        assert env.setback_at(tall_ridge_h) > env.setback_at(short_ridge_h), year

        # It lands exactly where the ceiling, the curve and the plot let it —
        # never above the gabarit's own top reckoned over these eaves.
        assert tall_ridge_h == pytest.approx(
            min(env.ridge_height + headroom, env.max_height_for_setback(half)),
            abs=1e-9,
        ), year
        # And the comble this building actually carries is never above it,
        # which is the A8.5 half: the recovery is a ceiling, not a height.
        assert grid.comble_height <= tall_ridge_h + 1e-9, year
        if grid.comble_height < tall_ridge_h - 0.20:
            under_the_ceiling += 1
        if tall_ridge_h > short_ridge_h + 0.20:
            carried_far += 1

    assert carried_far, (
        "no era in this set carried the headroom any appreciable distance, so the "
        "mechanism is not being exercised at all"
    )
    assert under_the_ceiling, (
        "no era in this set left any of its comble ceiling unbuilt, so A8.5 is not "
        "being exercised either"
    )


def test_the_parcel_and_not_the_facade_is_what_shortens_a_comble():
    """The one thing allowed to stop the roof below the gabarit is the plot.

    On a shallow parcel the comble's two opposing slopes meet before the legal
    top, and the ridge sits there. That is geometry; a facade's unspent
    ambition is not, and must not be able to do the same thing.
    """
    from buildings.typologies.paris.reglement import era_for_year, get_reglement

    reg = get_reglement(era_for_year(1865))
    reached = None
    for klass in BuildingClass:
        grid, _, sil, _ = run(site(parcel_depth=5.0, klass=klass))
        env = grid.envelope
        here = env.max_height_for_setback(2.5)
        assert here < reg.max_roof_height - 0.2, (
            "on this plot the decree, not the plot, is what stops the roof, so the "
            "test is not measuring the plot"
        )
        # The plot decides, and it decides the same thing for every class: what
        # the owner spent on stone has no vote (A8.5 and A2.3 both).
        assert grid.comble_height == pytest.approx(here, abs=1e-9), klass
        assert sil.props["ridge_height"] == pytest.approx(
            grid.built_height + here, abs=1e-9
        )
        assert Silhouette(sil.props["points"]).within(env)
        if reached is not None:
            assert here == pytest.approx(reached, abs=1e-9), klass
        reached = here


def test_lowering_the_facade_ambition_moves_the_eaves_and_not_the_roofline(monkeypatch):
    """The separation A2.3 asked for, now visible on the silhouette.

    ``_FACADE_AMBITION`` buys stone. It has no opinion about the roof: moving
    it moves the eaves down and takes the whole comble down with them, shape
    and height together, unchanged.

    **A8.5** is that this test used to assert the ridge stayed put while the
    comble stretched to reach it. That is what a ceiling read as a height does
    — the roof grows by exactly what the stone gives up — and it is why every
    building came out at its legal total. The coupling A2.3 wanted removed was
    ambition deciding the SHAPE of the roof, and it is removed: the envelope,
    the comble over the eaves and the fold in it are all identical before and
    after, and only the line they all sit on has moved.
    """
    from buildings.typologies.paris import structure as structure_mod

    s = site(klass=BuildingClass.COMFORTABLE, parcel_depth=30.0)
    before_grid, _, before_sil, _ = run(s)

    monkeypatch.setitem(
        structure_mod._FACADE_AMBITION, BuildingClass.COMFORTABLE, 0.70
    )
    after_grid, _, after_sil, _ = run(s)

    drop = before_grid.built_height - after_grid.built_height
    assert drop > 1.0
    # The roof is the same roof, moved down with the wall it stands on.
    assert after_grid.comble_height == pytest.approx(
        before_grid.comble_height, abs=1e-9
    )
    assert after_grid.brisis_height == pytest.approx(
        before_grid.brisis_height, abs=1e-9
    )
    assert before_sil.props["ridge_height"] - after_sil.props["ridge_height"] == (
        pytest.approx(drop, abs=1e-9)
    )
    # Its CEILING did not come down with it (A3.1) — that is the whole of the
    # difference between the two, and it is now visible as slack.
    assert after_grid.comble_ceiling > before_grid.comble_ceiling + 1.0
    assert after_grid.envelope.ridge_height == pytest.approx(
        before_grid.envelope.ridge_height, abs=1e-9
    )


def test_eaves_are_read_off_the_polyline_not_stored_beside_it():
    s = Silhouette(((0.0, 0.0), (0.0, 12.0), (2.0, 14.0)))
    assert s.eaves_height == pytest.approx(12.0)
    assert s.ridge_height == pytest.approx(14.0)


def test_a_silhouette_needs_at_least_two_points():
    with pytest.raises(ValueError):
        Silhouette(((0.0, 0.0),))


# ---------------------------------------------------------------------------
# The roofscape hangs off the same grid as the facade
# ---------------------------------------------------------------------------


def test_one_dormer_per_bay_per_band_and_none_over_the_end_piers():
    """A8.3. One lucarne per bay, in one row per band of brisis.

    The bays are the repeating bays AND the entrance's — a porte cochère is a
    ground-floor fact, and four storeys up the same column carries ordinary
    windows like any other, so leaving it out put a hole in the middle of
    every roof in Paris. The end piers and the narrow specials still carry
    none: a lucarne over a 1.35 m blind panel is a window into the party wall.
    """
    from buildings.typologies.paris import catalogue as cat
    from buildings.typologies.paris.structure import BRISIS_RISE

    grid, _, _, others = run(site())
    lit = [
        i
        for i, b in enumerate(grid.bays)
        if b.name == "bay" or b.name in cat.ENTRANCE_SLOT_NAMES
    ]
    assert any(grid.bays[i].name in cat.ENTRANCE_SLOT_NAMES for i in lit), (
        "this fixture is supposed to have an entrance in the run"
    )
    dormers = kind(others, "dormer")
    rows = max(1, int(grid.brisis_height / float(BRISIS_RISE) + 1e-9))
    assert [d.props["bay_index"] for d in dormers] == lit * rows
    # Every row stands on the same grid, and the rows are stacked a whole
    # chambre de bonne apart — the bands the brisis is made of.
    heights = sorted({round(d.props["y"], 6) for d in dormers})
    assert len(heights) == rows
    for a, b in zip(heights, heights[1:]):
        assert b - a == pytest.approx(float(BRISIS_RISE), abs=1e-9)


def test_dormers_are_centred_on_their_bays():
    grid, _, _, others = run(site())
    for d in kind(others, "dormer"):
        slot = grid.bays[d.props["bay_index"]]
        centre = d.props["x"] + d.props["w"] / 2.0
        assert centre == pytest.approx(slot.start + slot.width / 2.0, abs=1e-9)


def test_a_dormer_stands_exactly_where_the_envelope_lets_it():
    """Its face is tangent to the gabarit at its own head — as far forward as
    the law permits, which is where a builder would want it."""
    for year in (1865, 1890, 1905):
        grid, _, _, others = run(site(year=year))
        env = grid.envelope
        eaves = grid.built_height
        for d in kind(others, "dormer"):
            head = d.props["y"] + d.props["h"] - eaves
            assert d.props["setback"] == pytest.approx(env.setback_at(head), abs=1e-9)


def test_a_comble_too_short_for_a_lucarne_gets_none_and_says_why():
    """Absence is a result too, and it carries a rule like anything else."""
    # A narrow street before 1859 earns a very small comble.
    grid, roled, _, others = run(site(year=1830, street_width=6.0, parcel_depth=1.2))
    assert not kind(others, "dormer")
    absent = [n for n in others if n.props.get("absence") == "dormer"]
    assert len(absent) == 1
    assert absent[0].trace
    assert "will not fit" in absent[0].trace[0].detail or "no comble" in absent[0].trace[0].detail


def test_dormers_take_the_grid_of_the_storey_they_light():
    """A2.1's coupling, from this side.

    A lucarne is a window and a window belongs to a room. Where the comble
    holds a habitable storey — the chambres de bonne — the dormers are that
    storey's windows and take its bay grid; where it does not, they light a
    garret. Either way the grid is the one shared bay solve read off ``roled``,
    never a rhythm invented here, and each dormer says which storey it lights
    rather than leaving the reader to guess.
    """
    seen_attic = seen_garret = False
    cases = [
        site(),                                            # a comble with a floor in it
        site(year=1860, street_width=6.0, parcel_depth=4.0),  # a comble too shallow for one
    ]
    for s in cases:
        grid, roled, _, others = run(s)
        attic = [st for st in roled.storeys if st.role is Role.ATTIC]
        expected = attic[0].index_from_bottom if attic else None
        seen_attic |= bool(attic)
        seen_garret |= not attic

        from buildings.typologies.paris import catalogue as cat

        dormers = kind(others, "dormer")
        bays = [
            i
            for i, b in enumerate(roled.bays)
            if b.name == "bay" or b.name in cat.ENTRANCE_SLOT_NAMES
        ]
        assert dormers, s
        assert [d.props["bay_index"] for d in dormers[: len(bays)]] == bays
        assert len(dormers) % len(bays) == 0
        # The LOWEST row is the one standing in front of the storey S3 emitted;
        # a row above it stands in front of comble volume that has not been
        # divided into a storey yet, and says so by naming none (A8.3).
        for d in dormers[: len(bays)]:
            assert d.props["lights_storey_index"] == expected
            assert d.trace[0].inputs["lights_storey_index"] == expected
        for d in dormers[len(bays) :]:
            assert d.props["lights_storey_index"] is None

    assert seen_attic and seen_garret, (
        "both states have to be exercised: a comble with a chambre de bonne in it, and "
        "one too shallow to hold one"
    )


def test_the_dormer_grid_is_the_shared_bay_grid_and_not_a_second_solve():
    """The bays a dormer stands over are literally the grid's slots, over the
    whole situation space — so the roof cannot drift out of step with the
    facade under it however the storeys above the cornice come out."""
    for year in (1830, 1865, 1890, 1905):
        for klass in BuildingClass:
            grid, roled, _, others = run(site(year=year, klass=klass))
            assert roled.bays == grid.bays
            from buildings.typologies.paris import catalogue as cat

            for d in kind(others, "dormer"):
                slot = roled.bays[d.props["bay_index"]]
                assert slot.name == "bay" or slot.name in cat.ENTRANCE_SLOT_NAMES
                centre = d.props["x"] + d.props["w"] / 2.0
                assert centre == pytest.approx(slot.start + slot.width / 2.0, abs=1e-9)


# ---------------------------------------------------------------------------
# A2.6 — the two parcel-depth limits are one invariant, and it is asserted
# ---------------------------------------------------------------------------


def test_an_envelope_from_a_different_parcel_is_refused_loudly():
    """The S9 hazard, constructed.

    ``compute_envelope`` depth-limits the ridge from its own ``parcel_depth``;
    this phase closes the terrasse from ``site.parcel_depth``. Hand the two
    different numbers — which is exactly what a ``BlockDatums`` path that
    resolves depth differently would do — and the roof used to run past the
    middle of the parcel with a clean silhouette and a clean trace. It must
    now stop, and say which two numbers disagreed.
    """
    deep = site(parcel_depth=22.0)
    grid = solve_structure(deep)
    roled = assign_roles(grid)
    assert grid.envelope.parcel_depth == pytest.approx(22.0)

    shallow = site(parcel_depth=8.0)
    with pytest.raises(ValueError) as exc:
        terminate.terminate(grid, roled, shallow, DecisionStream(shallow.seed))
    message = str(exc.value)
    assert "8.0" in message and "22.0" in message
    assert "parcel" in message


def test_a_comble_that_runs_past_the_middle_of_the_parcel_is_refused():
    """The other half of the invariant, which the datum check cannot see.

    An envelope can agree perfectly about the parcel and still never have been
    depth-limited by it — built by hand, or by some future path that forgets.
    Its two opposing slopes have already met by the time the ridge is reached,
    so the roof continues through itself and out over the courtyard.
    """
    s = site(parcel_depth=8.0, year=1890, street_width=30.0)
    grid = solve_structure(s)
    env = grid.envelope
    half = s.parcel_depth / 2.0
    reachable = env.max_height_for_setback(half)
    assert env.ridge_height <= reachable + 1e-3, "the pipeline itself already breaks this"

    runaway = dataclasses.replace(env, ridge_height=reachable + 1.5)
    with pytest.raises(ValueError) as exc:
        terminate._comble_profile(runaway, half)
    assert "halfway back" in str(exc.value)

    # ...and the same envelope with the ridge left where the decree put it is
    # accepted, so the guard is about the breach and not about the call.
    assert terminate._comble_profile(env, half)


def test_the_depth_guards_accept_every_envelope_the_pipeline_builds():
    """A guard that is too tight is a guard that gets deleted. Sweep the
    situation space, including the shallow parcels where the ridge sits exactly
    on the depth limit and the envelope's own millimetre of rounding is the
    only thing in play."""
    for depth in (3.0, 4.5, 6.0, 8.0, 11.0, 14.0, 22.0, 30.0):
        for year in (1830, 1860, 1875, 1890, 1905):
            for width in (6.0, 12.0, 20.0, 40.0):
                s = site(parcel_depth=depth, year=year, street_width=width)
                grid = solve_structure(s)
                terminate._comble_profile(grid.envelope, depth / 2.0)


def test_chimney_stacks_stand_on_the_joints_of_the_bay_grid():
    grid, _, _, others = run(site())
    souches = [n for n in others if n.props.get("element") == "chimney_stack"]
    assert len(souches) >= 2
    # Both party walls, and one pier between each adjacent pair of bays.
    bays = [b for b in grid.bays if b.name == "bay"]
    assert len(souches) == 2 + max(0, len(bays) - 1)
    for s in souches:
        assert s.props["x"] >= -1e-9
        assert s.props["x"] + s.props["w"] <= math.fsum(b.width for b in grid.bays) + 1e-9


def test_every_stack_clears_the_ridge():
    grid, _, sil, others = run(site())
    ridge = sil.props["ridge_height"]
    for s in [n for n in others if n.props.get("element") == "chimney_stack"]:
        assert s.props["y"] + s.props["h"] > ridge


def test_a_stack_starts_where_it_comes_out_of_the_roof_not_at_the_eaves():
    """A4.4. ``y``/``h`` carried the souche's full extent in SECTION — from
    the eaves to its head — so a consumer drawing the rectangle it was given
    painted a full-height bar down the face of every comble. A souche is
    masonry from the cellar up; what there is to draw is the part standing
    clear of the roof, and the IR has to say where that starts.
    """
    for over in (dict(), dict(parcel_depth=22.0), dict(year=1890), dict(street_width=9.0)):
        grid, _, sil, others = run(site(**over))
        ridge = sil.props["ridge_height"]
        eaves = grid.eaves_height
        stacks = [n for n in others if n.props.get("element") == "chimney_stack"]
        assert stacks
        for s in stacks:
            base = float(s.props["base_height"])
            assert base == pytest.approx(float(s.props["y"]), abs=1e-9)
            assert base == pytest.approx(ridge, abs=1e-6), (
                f"{over}: the stack emerges at {base:.3f} m, not at the ridge "
                f"{ridge:.3f} m"
            )
            assert base > eaves + 1e-9, (
                f"{over}: the stack still starts at the eaves ({eaves:.3f} m), which "
                "is the full-height-bar bug A4.4 names"
            )
            # ...and what is hidden is reported, so nobody adds it back.
            assert float(s.props["hidden_in_the_comble"]) == pytest.approx(
                base - eaves, abs=1e-9
            )
            assert float(s.props["h"]) == pytest.approx(
                float(s.props["head_height"]) - base, abs=1e-9
            )
            assert 0.0 < float(s.props["h"]) < float(sil.props["h"]), (
                "the visible stack is either nothing or the whole roof again"
            )


def test_a_corner_building_hips_its_comble_and_a_mid_block_one_does_not():
    _, _, mid, _ = run(site(corner=False))
    _, _, corner, _ = run(site(corner=True))
    assert mid.props["ends"] == "party_wall"
    assert corner.props["ends"] == "hipped"


# ---------------------------------------------------------------------------
# A7.3 — a souche's base is the roof surface beneath it, not the ridge
# ---------------------------------------------------------------------------


def test_roof_surface_is_the_ridge_everywhere_mid_block():
    """No returns, no fall-away: the front slope is one flat band the whole
    frontage wide, so the surface is the ridge at every x."""
    profile = [(0.0, 0.0), (3.0, 4.0)]
    for x in (0.0, 2.0, 8.0, 16.0):
        assert terminate._roof_surface_height_at(
            x, 16.0, 4.0, "party_wall", profile
        ) == pytest.approx(4.0)


def test_roof_surface_falls_away_toward_a_hipped_return():
    """A hipped corner comble's surface is not flat along the frontage: it
    falls away toward the ends, so the surface directly under a stack
    standing at the very corner (run=0) is the eaves, not the ridge, and it
    rises back to the ridge away from the return."""
    profile = [(0.0, 0.0), (3.0, 4.0)]
    facade_w, ridge_h = 10.0, 4.0
    at_corner = terminate._roof_surface_height_at(0.0, facade_w, ridge_h, "hipped", profile)
    at_quarter = terminate._roof_surface_height_at(
        facade_w / 4.0, facade_w, ridge_h, "hipped", profile
    )
    at_mid = terminate._roof_surface_height_at(facade_w / 2.0, facade_w, ridge_h, "hipped", profile)
    assert at_corner == pytest.approx(0.0)
    assert at_corner < at_quarter < at_mid
    assert at_mid == pytest.approx(ridge_h)


def test_a_hip_end_souche_emerges_from_the_surface_not_the_ridge():
    """The A7.3 defect, literally: a souche standing near a hipped return's
    own end must emerge from the surface actually beneath it (which has
    fallen well clear of the ridge there), not float above tiles the return
    never draws that high."""
    grid, _, sil, others = run(site(corner=True))
    ridge = sil.props["ridge_height"]
    eaves = grid.eaves_height
    stacks = sorted(
        (n for n in others if n.props.get("element") == "chimney_stack"),
        key=lambda n: n.props["x"],
    )
    assert len(stacks) >= 3, "need at least one party-wall stack at each end plus one between"
    end_stacks = [stacks[0], stacks[-1]]
    for s in end_stacks:
        base = float(s.props["base_height"])
        assert base < ridge - 1e-6, "a hip-end stack must not still be based at the ridge"
        assert base >= eaves - 1e-6
        assert s.props["emerges_from"] == "hip return"


def test_a_souches_visible_height_is_constant_along_a_hipped_frontage():
    """A7.3's own fix: what stays constant is the masonry showing above the
    LOCAL surface, not the stack's absolute head height. A souche whose base
    has fallen with the hip must not grow into a smokestack to keep reaching
    the ridge's own head height — every stack on the same building shows the
    same visible height, whatever the local surface is doing beneath it."""
    _, _, _, others = run(site(corner=True))
    stacks = [n for n in others if n.props.get("element") == "chimney_stack"]
    assert len({round(float(s.props["h"]), 6) for s in stacks}) == 1, (
        "every souche on one building must show the same visible height"
    )
    visible = float(terminate._souche_visible_height())
    for s in stacks:
        assert float(s.props["h"]) == pytest.approx(visible)
        assert 0.5 - 1e-6 <= float(s.props["h"]) <= 1.5 + 1e-6, (
            "a souche shows roughly 0.5-1.5 m of brick above the tiles"
        )


def test_no_souche_stands_taller_than_a_real_smokestack():
    """The literal regression this amendment exists to stop: a hip-end souche
    that keeps the ridge's absolute head height while its base falls away
    grows into a multi-metre pole standing clear of the roof. Sweep corners
    across the situation space and check no stack's visible extent ever
    exceeds what a souche showing constant brick over its own surface can
    produce."""
    visible = float(terminate._souche_visible_height())
    for year in (1830, 1865, 1900):
        for width in (8.0, 16.0, 30.0):
            _, _, _, others = run(site(corner=True, street_width=width, year=year))
            for s in [n for n in others if n.props.get("element") == "chimney_stack"]:
                assert float(s.props["h"]) == pytest.approx(visible), (
                    "a souche's drawn height must never grow past its constant "
                    "showing above the surface, on any parcel"
                )


def test_the_hip_fix_does_not_move_a_mid_block_souche():
    """Mid-block (or the flat ridge run of a hipped frontage still inside its
    own returns) the surface IS the ridge, so nothing about the A4.4 base
    moves — only the hip's own ends are affected."""
    grid, _, sil, others = run(site(corner=False))
    ridge = sil.props["ridge_height"]
    for s in [n for n in others if n.props.get("element") == "chimney_stack"]:
        assert float(s.props["base_height"]) == pytest.approx(ridge, abs=1e-6)
        assert s.props["emerges_from"] == "ridge"


# ---------------------------------------------------------------------------
# A9.3 — one hip arris, derived once, in this module, and nowhere else
#
# A8 fixed the RENDERER's own copy of this geometry (``elements._hip_arris``)
# to key the pitch to the section's TRUE reach rather than ``profile[-1]``,
# which can run on flat for however much of the parcel's depth a terrasse or
# a curve's own flattening leaves spare. This module's own copy — the one
# placing every souche — was never given the same fix, so the two disagreed
# by up to 1.559 m: a hip-end souche's stated base could sit well below the
# roof surface the renderer actually drew above it, and the chimney it
# belonged to vanished under the roof mass drawn on top of it. The tests
# below exercise ``terminate.derive_hip_arris`` directly — the ONE place this is
# now derived — and the consequences of getting it right: the roof node's
# own ``hip_arris`` prop must reproduce exactly the surface every souche
# stands on, and a lucarne must not stand where that surface has fallen
# below its own head.
# ---------------------------------------------------------------------------


def stated_fold(roof) -> float | None:
    """The fold height a roof node states, read the way production reads it.

    A19.1. Tests that want the roof surface must ask with the SAME fold the
    phase used to build it; recomputing a foldless one here and comparing is
    the two-independent-opinions defect this module's history is made of.
    """
    props = roof.props
    lower, upper = props.get("lower_angle_deg"), props.get("upper_angle_deg")
    pct, ridge = props.get("break_pct"), props.get("h")
    if None in (lower, upper, pct, ridge):
        return None
    if abs(float(lower) - float(upper)) <= 1.0 or float(pct) >= 0.995:
        return None
    return float(ridge) * float(pct)


def test_a_hip_arris_never_follows_the_curve_of_the_section():
    """A4.5, as A19.1 restates it. The hip return used to reuse the curved
    depth-section verbatim as the frontage-wise arris — convex, calibrated
    against the parcel's depth rather than the frontage's width — which is
    what bulged into an onion dome on a narrow chamfer.

    A4.5's fix was "one straight line at the section's average pitch". The
    straightness was right; the singleness was not, and A19.1 replaces it with
    one straight segment per PLANE. So the invariant this test defends is no
    longer a point count — it is that no segment ever follows the curve, which
    is what the onion dome was made of.

    Stated as: the arris is never OUTSIDE the section it belongs to. A curve
    that starts near-vertical (a post-1884 arc) stands further out than its own
    chord everywhere between the knots, so an arris that tracked it would fail
    this; a chord cannot."""
    # A convex section: near-vertical at the eaves, flattening to the ridge.
    curved = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]

    def section_run_at(height):
        prev_x, prev_h = curved[0]
        for x, h in curved[1:]:
            if height <= h:
                span = h - prev_h
                t = (height - prev_h) / span if span > 1e-12 else 0.0
                return prev_x + t * (x - prev_x)
            prev_x, prev_h = x, h
        return curved[-1][0]

    for fold in (None, 3.4):
        arris = terminate.derive_hip_arris(30.0, curved, fold)
        assert arris[0] == (0.0, 0.0)
        # every knot at or INSIDE the section's own run at that height
        for run, height in arris[1:]:
            assert run <= section_run_at(height) + 1e-9, (
                f"fold={fold}: the arris stands at {run:.3f} m where the section "
                f"is only {section_run_at(height):.3f} m in — that is the onion dome"
            )
        # ...and monotone, so it is a rafter and not a scribble
        assert [k[0] for k in arris] == sorted(k[0] for k in arris)
        assert [k[1] for k in arris] == sorted(k[1] for k in arris)


def test_a_hip_breaks_where_the_roof_breaks():
    """A19.1. A mansard is two planes, so its arêtier is two timbers meeting at
    the fold — not one timber at the average of the two pitches.

    The average is what made the fold vanish. On the post-1884 corner preset
    the brisis break was drawn across 1.00 m of a 15 m frontage where the
    geometry puts it across 9.68 m, so the roof read as a plain cone instead of
    a steep skirt under a small pyramidal cap."""
    # A steep brisis to 3.0 m in 1.0 m of run, then a shallow terrasson.
    mansard = [(0.0, 0.0), (1.0, 3.0), (7.0, 4.0)]

    plain = terminate.derive_hip_arris(30.0, mansard)
    folded = terminate.derive_hip_arris(30.0, mansard, 3.0)
    assert len(plain) == 2, "no stated fold, one plane, one timber"
    assert len(folded) == 3, "a stated fold puts a knot in the rafter"
    assert folded[1] == pytest.approx((1.0, 3.0))

    # The fold's consequence: near the eaves the folded hip stands much higher
    # than the averaged one, which is what keeps the break out on the frontage
    # instead of collapsing it toward the apex.
    at_run = 0.8
    on_plain = terminate._arris_height_at(plain, at_run)
    on_folded = terminate._arris_height_at(folded, at_run)
    assert on_folded > on_plain + 0.5, (
        f"folded {on_folded:.3f} m vs averaged {on_plain:.3f} m at {at_run} m in"
    )

    # And on a frontage too narrow to reach the fold, the hip is still on the
    # brisis and is still straight — a pavilion peak on the steep plane.
    narrow = terminate.derive_hip_arris(1.2, mansard, 3.0)
    assert len(narrow) == 2
    assert narrow[-1] == pytest.approx((0.6, 1.8))


def test_a_return_deeper_than_the_frontage_stops_at_mid_frontage():
    """The IR's profile is a section perpendicular to the street, so its
    insets are depths. Two returns still have to fit side by side in the
    frontage there is; where the section outruns it, the arris stops rather
    than being squeezed or clamped into a spike."""
    deep = [(0.0, 0.0), (2.0, 3.0), (9.0, 5.0)]
    arris = terminate.derive_hip_arris(8.0, deep)
    assert arris[-1][0] == pytest.approx(4.0)
    assert arris[-1][1] < 5.0
    assert all(a[0] <= 4.0 + 1e-9 for a in arris)
    assert [a[0] for a in arris] == sorted(a[0] for a in arris)


def test_a_hip_reaches_full_height_before_the_sections_flat_run_out():
    """A comble whose section climbs to its full height and then runs FLAT
    (a zinc terrasse, closing the gap out to half the PARCEL's depth — a fact
    about the depth, not the frontage) must not have that flat run-out
    averaged into the hip's own pitch: ``full_h / full_run`` computed across
    the WHOLE section, terrasse included, understates the true climb by
    however far the terrasse ran on — on an ordinary Paris parcel, most of
    the section. This is the exact shape of the A9.3 defect: this module's
    own ``_hip_arris_end`` used to do exactly this (``profile[-1]``, the full
    9.0 m section run, rather than the frontage-scaled true reach), which is
    why a hip-end souche's stated base could sit up to 1.559 m below the roof
    surface the renderer actually drew.
    """
    # Climbs to full height (3.0) at run=3.0, then a 6 m flat terrasse tail
    # out to run=9.0 — the same shape ``_comble_profile`` produces on a deep
    # parcel with a shallow ridge (A2.6's "flat zinc terrasse closes the top").
    terraced = [(0.0, 0.0), (3.0, 3.0), (9.0, 3.0)]

    # Old (buggy) formula: full_h/full_run * half = 3.0/9.0*4.0 = 1.333 — well
    # short of the 3.0 m the comble actually reaches by run=3.0. The frontage
    # here (half=4.0) has room to spare past the TRUE reach (3.0), so the hip
    # must be fully risen, not still climbing.
    arris = terminate.derive_hip_arris(8.0, terraced)
    assert arris[-1] == pytest.approx((3.0, 3.0)), (
        "the hip must reach full height at the section's own true reach (3.0 m), "
        "not the flat run-out's own end (9.0 m) or a fraction of the ridge "
        f"averaged over it — got {arris[-1]}"
    )

    # A frontage too narrow even for the TRUE reach still climbs at the
    # section's real (undiluted) pitch, not the terrasse-diluted one: at
    # half=1.5 m (pitch 1.0, since the section climbs 3.0 m in 3.0 m of run)
    # the hip should stand at 1.5 m, not 3.0/9.0*1.5 = 0.5 m.
    narrow = terminate.derive_hip_arris(3.0, terraced)
    assert narrow[-1][0] == pytest.approx(1.5)
    assert narrow[-1][1] == pytest.approx(1.5), (
        f"expected the section's own pitch (1.0) over the true reach, got {narrow[-1]}"
    )


def test_a_hip_with_no_flat_run_out_is_unchanged():
    """Where the profile's own last point IS the true reach (no terrasse, no
    curve flattening early) — a straight 45° pre-1884 comble with the ridge
    reached exactly at the parcel's own depth limit, or a post-1884 arc that
    only flattens at its final sampled vertex — the true-reach fix must
    change nothing: ``rise_run`` collapses to ``full_run``."""
    curved = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]
    assert terminate.derive_hip_arris(30.0, curved) == ((0.0, 0.0), (6.0, 4.0))
    narrow = terminate.derive_hip_arris(5.0, curved)
    assert narrow[-1][1] == pytest.approx(4.0 * 2.5 / 6.0)


def test_the_roof_node_states_the_one_hip_arris_the_renderer_reads():
    """The roof node's own ``hip_arris`` prop must exist on a corner building
    and be the identical thing ``derive_hip_arris`` computes from that same roof's
    profile — there is no second, renderer-side copy left to disagree with
    it (A9.3)."""
    grid, _, _sil, others = run(site(corner=True))
    roof = kind(others, "roof")[0]
    assert roof.props["hip_arris"], "a corner building must state a hip arris"
    assert roof.props["hip_arris"] == terminate.derive_hip_arris(
        float(roof.props["w"]), roof.props["profile"], stated_fold(roof)
    )

    mid_grid, _, _mid_sil, mid_others = run(site(corner=False))
    mid_roof = kind(mid_others, "roof")[0]
    assert mid_roof.props["hip_arris"] == (), "mid-block states no arris to draw"


def test_every_souches_base_falls_exactly_on_the_stated_hip_arris():
    """The literal fix: reading the roof node's own ``hip_arris`` at a
    souche's own x must reproduce that souche's stated ``base_height``
    exactly, so a renderer drawing the mass from ``hip_arris`` alone can
    never bury a stack the IR says should still be showing brick above the
    tiles."""
    grid, _, sil, others = run(site(corner=True))
    roof = kind(others, "roof")[0]
    facade_w = float(roof.props["w"])
    ridge_h = float(roof.props["h"])
    arris = roof.props["hip_arris"]
    stacks = [n for n in others if n.props.get("element") == "chimney_stack"]
    assert len(stacks) >= 3
    for s in stacks:
        centre = float(s.props["x"]) + float(s.props["w"]) / 2.0
        run_len = min(centre, facade_w - centre)
        height = terminate._arris_height_at(arris, run_len)
        expected = ridge_h if height is None else height
        assert float(s.props["base_height"]) == pytest.approx(
            grid.eaves_height + expected, abs=1e-6
        ), "the souche's base must fall exactly on the roof node's own stated hip_arris"


def test_no_hip_end_souche_sits_more_than_a_metre_and_a_half_below_the_surface():
    """The literal regression measured in A9.3: before the fix, a hip-end
    souche's stated base sat up to 1.559 m below the roof surface the
    renderer actually drew there. Sweep corner frontages and check the two
    can no longer drift apart at all — not "less far apart", not at all,
    because they are now one computation."""
    for pw in (8.0, 12.0, 16.0, 20.0, 26.0):
        grid, _, sil, others = run(site(corner=True, parcel_width=pw))
        roof = kind(others, "roof")[0]
        facade_w = float(roof.props["w"])
        ridge_h = float(roof.props["h"])
        arris = roof.props["hip_arris"]
        for s in [n for n in others if n.props.get("element") == "chimney_stack"]:
            centre = float(s.props["x"]) + float(s.props["w"]) / 2.0
            run_len = min(centre, facade_w - centre)
            height = terminate._arris_height_at(arris, run_len)
            expected = ridge_h if height is None else height
            drift = abs(float(s.props["base_height"]) - (grid.eaves_height + expected))
            assert drift < 1e-6, f"PW={pw}: souche base drifted {drift:.3f} m from the surface"


def test_a_surface_at_the_capped_mid_span_of_a_narrow_hip_is_the_peak_not_the_ridge():
    """A9.3's own subtler half of the same bug. Where the frontage is too
    narrow for the hip to ever reach the full ridge height (the two returns
    meet at a single peak — a pavilion, not a dome), the surface at that
    exact mid-span IS the peak the arris reaches there, not the ridge height
    the comble never actually attains along this frontage. The previous form
    of ``_roof_surface_height_at`` answered ``ridge_h`` at ``run == arris_run``
    unconditionally, which is only correct when the arris genuinely reaches
    the ridge (the uncapped case) — in the capped case it silently invented
    height the roof does not have."""
    # A frontage narrower than the section's own true reach (rise_run=6.0):
    # the two hips meet at half=2.5 before the ridge, at height 4.0*2.5/6.0.
    profile = [(0.0, 0.0), (1.0, 2.0), (3.0, 3.4), (6.0, 4.0)]
    facade_w, ridge_h = 5.0, 4.0
    peak = 4.0 * 2.5 / 6.0
    assert peak < ridge_h - 1e-6, "the setup must actually be the capped/pavilion case"

    at_mid = terminate._roof_surface_height_at(
        facade_w / 2.0, facade_w, ridge_h, "hipped", profile
    )
    assert at_mid == pytest.approx(peak), (
        f"a pavilion's own peak ({peak:.3f} m) was reported as the unreached ridge "
        f"({ridge_h:.3f} m) instead"
    )


def test_the_exact_pw8_repro_is_a_deliberate_pavilion_not_a_missing_ridge():
    """The exact A8/A9.3 repro: ``PW=8`` on a 20 m street is narrower than the
    rise-run (4.311 m half-frontage needed), so the two hips meet before
    reaching the ridge. That is not a defect to paper over — a real hipped
    corner too narrow for a flat ridge run comes to a single pavilion peak,
    not a dome and not a ridge stretched to a width the parcel does not have.
    What this asserts is that the choice is deliberate and internally
    consistent: the stated ``hip_arris`` genuinely falls short of the full
    ridge height, and every souche on this frontage emerges from that lower
    peak rather than from a ridge the building never built.
    """
    grid, _, sil, others = run(site(corner=True, street_width=20.0, parcel_width=8.0))
    roof = kind(others, "roof")[0]
    ridge_h = float(roof.props["h"])
    arris = roof.props["hip_arris"]
    assert arris, "a corner building always states an arris, even a capped one"
    assert arris[-1][1] < ridge_h - 1e-6, (
        "PW=8 must still be the capped/pavilion case this repro names"
    )
    for s in [n for n in others if n.props.get("element") == "chimney_stack"]:
        assert float(s.props["base_height"]) < grid.eaves_height + ridge_h - 1e-6, (
            "no souche on a pavilion this narrow may emerge at the ridge height, "
            "which this frontage never reaches"
        )


def test_a_lucarne_never_stands_where_the_hip_has_already_fallen_below_its_head():
    """A9.3: 'end lucarnes overhang the hip into the sky'. A dormer placed at
    the mid-block height needs the LOCAL roof surface at its own bay to stand
    at least that tall; near a hipped return's own ends the surface has
    already fallen well clear of the ridge, and a dormer built to the
    mid-block height there would stand in the sky beyond the hip's own arris,
    not on a slope that reaches that high. Every dormer this phase actually
    emits on a corner building must clear the local surface at its own
    position; where a bay's position cannot, a ``special`` node says so
    instead.

    **A19.1 moved this test's site from a 16 m parcel to a 10 m one.** Giving
    the hip its fold made it steeper near the eaves, which raised the roof
    surface over the end bays — so on a 16 m frontage every lucarne now clears
    the hip and nothing is skipped, and the test stopped exercising the defect
    it exists for. That is the correction working, not the guard becoming
    unnecessary: at 10 m the returns still meet before the end bays, and the
    clipping still fires. The site moved; the assertion did not weaken.

    **A26 moved it back to 16 m, for the mirror of the same reason.** The bay
    band came in to 2.00 / 2.60 / 3.20, so a frontage of any given width now
    carries more and narrower bays. At 10 m that puts every dormer inboard of
    where the hip has fallen and nothing is skipped again; at 16 m the extra
    bays reach out far enough that the end ones are clipped, which is the
    condition this test needs. Third time this site has moved and the reason
    has been the same every time: the defect lives where the outermost bay
    meets the hip, and anything that changes the bay grid changes which
    frontage width puts a bay there. The assertion has never moved."""
    grid, roled, sil, others = run(site(corner=True, street_width=20.0, parcel_width=16.0))
    roof = kind(others, "roof")[0]
    facade_w = float(roof.props["w"])
    ridge_h = float(roof.props["h"])
    ends = roof.props["ends"]
    profile = roof.props["profile"]
    assert ends == "hipped"

    dormers = kind(others, "dormer")
    assert dormers, "this situation should have lucarnes to test with"
    for d in dormers:
        centre = float(d.props["x"]) + float(d.props["w"]) / 2.0
        head = float(d.props["y"]) - grid.eaves_height + float(d.props["h"])
        local_surface = terminate._roof_surface_height_at(
            centre, facade_w, ridge_h, ends, profile, stated_fold(roof)
        )
        assert head <= local_surface + 1e-6, (
            f"a lucarne at x={centre:.3f} m needs a head of {head:.3f} m over the "
            f"eaves but the roof surface there is only {local_surface:.3f} m — it "
            "overhangs the hip into the sky"
        )

    skipped = [
        n for n in others
        if n.kind == "special"
        and n.trace
        and n.trace[0].rule == "paris.terminate.dormer.clipped_by_the_hip"
    ]
    assert skipped, (
        "a 16 m hipped frontage should have at least one end bay the hip has already "
        "fallen below — if none were skipped this test's own site stopped exercising "
        "the defect it was written for"
    )


# ---------------------------------------------------------------------------
# Dating: two FASHION axes, and geometry on neither of them (A2.5)
# ---------------------------------------------------------------------------


def test_the_dormer_and_material_axes_are_disjoint_and_cover_the_catalogue():
    catalogued = {v.name for v in chronology.variants_for("roof")}
    assert set(DORMER_ORNAMENT_VARIANTS) | set(ROOF_MATERIAL_VARIANTS) == catalogued
    assert not (set(DORMER_ORNAMENT_VARIANTS) & set(ROOF_MATERIAL_VARIANTS))


def test_a_zinc_roof_can_carry_a_pedimented_dormer():
    """The two axes are independent, so the combination must be reachable.

    Under a single weighted draw over all five ``roof`` variants it would be
    impossible, which is the bug this partition exists to prevent.
    """
    seen = set()
    for seed in range(40):
        _, _, _, others = run(site(year=1865, seed=seed))
        roof = kind(others, "roof")[0]
        seen.add((roof.props["dormer_variant"], roof.props["material"]))
    assert any(
        shape == "pedimented_dormers" and material == "zinc_roofing"
        for shape, material in seen
    )


def test_the_treatment_can_lag_the_envelope():
    """The 1884 envelope switch is a step; the dormer fashion is a ramp.

    A building of 1890 is legally obliged to use the arc and is *not* obliged
    to give up pedimented dormers, and the brief's straggler is exactly that.
    Assert the combination occurs rather than that it is forbidden.
    """
    combos = set()
    for seed in range(60):
        grid, _, _, others = run(site(year=1890, seed=seed))
        roof = kind(others, "roof")[0]
        combos.add((grid.envelope.roof_envelope, roof.props["dormer_variant"]))
    assert all(env is RoofEnvelope.CIRCULAR_ARC for env, _ in combos)
    assert {"pedimented_dormers", "varied_dormers_iron_cresting"} <= {
        name for _, name in combos
    }


def test_cresting_belongs_to_the_variant_not_to_the_year():
    """Two buildings of the same year differ in cresting exactly when they
    differ in comble treatment — which is the claim "never from a period
    test" made falsifiable."""
    for seed in range(60):
        _, _, _, others = run(site(year=1895, seed=seed))
        roof = kind(others, "roof")[0]
        has_crest = any(n.kind == "ironwork" for n in others)
        expected = DORMER_ORNAMENT_VARIANTS[roof.props["dormer_variant"]].cresting
        assert has_crest == expected


def test_varied_dormer_shapes_only_where_the_variant_offers_variety():
    forms_by_variant: dict[str, set[str]] = {}
    for year in (1865, 1900):
        for seed in range(30):
            _, _, _, others = run(site(year=year, seed=seed))
            roof = kind(others, "roof")[0]
            variant = roof.props["dormer_variant"]
            forms_by_variant.setdefault(variant, set()).update(
                d.props["form"] for d in kind(others, "dormer")
            )
    assert forms_by_variant["pedimented_dormers"] == {"pedimented"}
    assert len(forms_by_variant["varied_dormers_iron_cresting"]) > 1


# ---------------------------------------------------------------------------
# A2.5 — the fashion axis may not name, imply, or contradict a comble geometry
# ---------------------------------------------------------------------------


def test_the_geometry_vocabulary_is_read_off_reglement_and_not_typed_out():
    """Add a fourth envelope to the decree table and this guard widens by
    itself. A hand-maintained word list would silently stop covering it."""
    for envelope in RoofEnvelope:
        for word in envelope.value.split("_"):
            assert word in terminate._GEOMETRY_WORDS
            assert envelope in terminate._GEOMETRY_WORDS[word]


def test_no_catalogued_roof_variant_names_a_comble_geometry():
    """The load-bearing half of A2.5, over what is actually shipped.

    Every ``roof`` variant — repertoire and material alike — and every dormer
    form must be innocent of comble-geometry vocabulary. This is what makes
    the contradiction at 1885/comfortable structurally impossible rather than
    merely absent today.
    """
    for name, repertoire in DORMER_ORNAMENT_VARIANTS.items():
        assert terminate._geometry_claimed_by(name) == frozenset(), name
        for form in repertoire.dormer_forms:
            assert terminate._geometry_claimed_by(form) == frozenset(), form
    for name in ROOF_MATERIAL_VARIANTS:
        assert terminate._geometry_claimed_by(name) == frozenset(), name
    for variant in chronology.variants_for("roof"):
        assert terminate._geometry_claimed_by(variant.name) == frozenset(), variant.name


def test_the_import_guard_rejects_a_geometry_named_repertoire(monkeypatch):
    """...and it is not vacuous: give it back the name it used to have and it
    fails, naming the geometry the fashion axis was caught spelling."""
    doctored = dict(DORMER_ORNAMENT_VARIANTS)
    doctored["diagonal_45_pedimented_dormers"] = doctored.pop("pedimented_dormers")
    monkeypatch.setattr(terminate, "DORMER_ORNAMENT_VARIANTS", doctored)
    with pytest.raises(RuntimeError) as exc:
        terminate._check_no_geometry_on_the_fashion_axis()
    assert "diagonal_45_pedimented_dormers" in str(exc.value)
    assert "diagonal_45" in str(exc.value)

    # A dormer *form* is a name that travels downstream too, so it is checked
    # with the same vocabulary.
    monkeypatch.setattr(
        terminate,
        "DORMER_ORNAMENT_VARIANTS",
        {
            "plain_dormers": terminate._DormerRepertoire(
                dormer_forms=("circular_arc_lucarne",), cresting=False, source="test"
            )
        },
    )
    with pytest.raises(RuntimeError, match="circular_arc_lucarne"):
        terminate._check_no_geometry_on_the_fashion_axis()


def _with_a_geometry_named_variant(monkeypatch, claimed_name: str):
    """Put a variant naming a comble geometry back into the catalogue, so the
    runtime assertion has something to catch.

    The roof catalogue is narrowed to that one repertoire (plus the material
    axis, which is drawn separately), so the draw is forced and the test is
    about the assertion rather than about which way a weighted choice fell.
    """
    real = chronology.variants_for
    renamed = tuple(
        dataclasses.replace(v, name=claimed_name)
        for v in real("roof")
        if v.name == "pedimented_dormers"
    ) + tuple(v for v in real("roof") if v.name in ROOF_MATERIAL_VARIANTS)
    assert len(renamed) == 2

    def patched(feature: str):
        return renamed if feature == "roof" else real(feature)

    monkeypatch.setattr(chronology, "variants_for", patched)
    doctored = dict(DORMER_ORNAMENT_VARIANTS)
    doctored[claimed_name] = doctored.pop("pedimented_dormers")
    monkeypatch.setattr(terminate, "DORMER_ORNAMENT_VARIANTS", doctored)


def test_a_drawn_variant_that_contradicts_the_decree_raises(monkeypatch):
    """A2.5's assertion, exercised.

    1885/comfortable is the case the amendment names: the envelope is an arc
    by decree, and class lag still offers the older dormer repertoire. That is
    a legitimate building. It only becomes a contradiction if the repertoire
    *claims* a geometry — so put the old name back and confirm the claim is
    caught, against the envelope actually in force.
    """
    _with_a_geometry_named_variant(monkeypatch, "diagonal_45_pedimented_dormers")
    s = site(year=1885, klass=BuildingClass.COMFORTABLE)
    grid = solve_structure(s)
    assert grid.envelope.roof_envelope is RoofEnvelope.CIRCULAR_ARC
    roled = assign_roles(grid)

    with pytest.raises(RuntimeError) as exc:
        terminate.terminate(grid, roled, s, DecisionStream(s.seed))
    assert "diagonal_45" in str(exc.value)
    assert "circular_arc" in str(exc.value)


def test_a_drawn_variant_naming_the_geometry_in_force_is_not_a_contradiction(monkeypatch):
    """The assertion checks *contradiction*, not the mere presence of a word.

    The same doctored variant, on a year whose decree really does give a 45°
    comble, passes — which is what distinguishes this runtime check from the
    import-time naming rule that also (and separately) forbids it.
    """
    _with_a_geometry_named_variant(monkeypatch, "diagonal_45_pedimented_dormers")
    s = site(year=1865)
    grid = solve_structure(s)
    assert grid.envelope.roof_envelope is RoofEnvelope.DIAGONAL_45
    roled = assign_roles(grid)
    _sil, others = terminate.terminate(grid, roled, s, DecisionStream(s.seed))
    roof = kind(others, "roof")[0]
    assert roof.props["dormer_variant"] == "diagonal_45_pedimented_dormers"


def test_the_1885_comfortable_case_is_a_building_and_not_a_contradiction():
    """The case that produced A2.5, now that the names are honest.

    The law gives this building an arc; class lag gives it the older, plainer
    lucarnes. Both are true at once and nothing raises — the straggler is the
    common case, and it was never the building that was wrong.
    """
    seen = set()
    for seed in range(60):
        grid, _, _sil, others = run(
            site(year=1885, klass=BuildingClass.COMFORTABLE, seed=seed)
        )
        assert grid.envelope.roof_envelope is RoofEnvelope.CIRCULAR_ARC
        roof = kind(others, "roof")[0]
        assert roof.props["envelope"] == "circular_arc"
        seen.add(roof.props["dormer_variant"])
    assert "pedimented_dormers" in seen, (
        "class lag no longer reaches this case, so it no longer tests the split"
    )


def test_the_roof_node_states_the_geometry_and_the_fashion_separately():
    """The IR carries both facts and does not let one be inferred from the
    other: the envelope comes from the decree, the repertoire from the date."""
    for year in (1865, 1890, 1905):
        grid, _, _sil, others = run(site(year=year))
        roof = kind(others, "roof")[0]
        assert roof.props["envelope"] == grid.envelope.roof_envelope.value
        assert roof.props["dormer_variant"] in DORMER_ORNAMENT_VARIANTS
        rules = {e.rule for e in roof.trace}
        assert "paris.terminate.roof.geometry_is_not_on_the_fashion_axis" in rules


def test_no_period_name_appears_in_this_phase_at_all():
    """The automated harness greps the whole source tree; this pins the one
    file S7 owns, so a regression fails a unit test and not just a script."""
    import pathlib

    src = (
        pathlib.Path(__file__).resolve().parents[2]
        / "src/buildings/typologies/paris/terminate.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("Era.", "SECOND_EMPIRE", "ALPHAND", "BONNIER", "era_for_year"):
        assert forbidden not in src, f"terminate.py branches on {forbidden}"


# ---------------------------------------------------------------------------
# The end-to-end assembly
# ---------------------------------------------------------------------------


def test_generate_runs_all_phases_into_one_tree():
    building, log = generate(site())
    kinds = {n.kind for n in walk(building)}
    assert {"building", "storey", "bay", "opening", "roof", "dormer", "silhouette"} <= kinds
    phases = {e.phase for n in walk(building) for e in n.trace}
    assert phases == {"structure", "roles", "qualification", "termination"}
    assert len(log.all_ids()) == len(list(walk(building)))


def test_every_element_records_the_rule_that_produced_it():
    building, _ = generate(site())
    for node in walk(building):
        assert node.trace, f"{node.id} has no trace (I4)"
        for entry in node.trace:
            assert entry.rule.strip()
            assert entry.detail.strip()


def test_seed_and_situation_determine_the_output():
    a, _ = generate(site(seed=4))
    b, _ = generate(site(seed=4))
    assert to_json(a) == to_json(b)
    c, _ = generate(site(seed=5))
    assert to_json(c) != to_json(a)


def test_the_whole_tree_round_trips_through_json():
    building, _ = generate(site())
    assert from_json(to_json(building)) == building


def test_termination_never_reaches_back_into_an_earlier_phase():
    """I1, made concrete: run termination against a grid, then run the whole
    pipeline against the same situation, and the comble must be identical.

    If termination read anything qualification produced, the two would be
    free to differ.
    """
    s = site()
    _, _, sil_alone, others_alone = run(s)
    building, _ = generate(s)
    sil_full = next(n for n in walk(building) if n.kind == "silhouette")
    assert sil_full.props["points"] == sil_alone.props["points"]
    roof_full = next(n for n in walk(building) if n.kind == "roof")
    assert roof_full.props["dormer_variant"] == kind(others_alone, "roof")[0].props["dormer_variant"]


def test_adding_the_roof_did_not_disturb_the_facades_decisions():
    """I5's real content: the streams are addressable, so a decision added in
    one phase must not shift a decision in another."""
    from buildings.typologies.paris.compose import qualify_building

    s = site()
    facade_only, _ = qualify_building(s)
    full, _ = generate(s)
    by_id = {n.id: n for n in walk(full)}
    for node in walk(facade_only):
        assert node.id in by_id
        if node.kind == "building":
            # The root gains the roof's facts (`total_height`, `envelope`, ...)
            # by design; everything it already said must survive unchanged.
            assert dict(node.props).items() <= dict(by_id[node.id].props).items() or all(
                by_id[node.id].props[k] == v
                for k, v in node.props.items()
                if k != "h"
            )
            continue
        assert by_id[node.id].props == node.props


def test_the_building_node_reports_both_heights():
    s = site()
    grid = solve_structure(s)
    building, _ = generate(s)
    assert building.props["eaves_height"] == pytest.approx(grid.built_height)
    assert building.props["total_height"] == pytest.approx(
        grid.built_height + grid.comble_height
    )
    assert building.props["h"] == building.props["total_height"]
    # ...and the total stops short of the legal one (A8.5). The comble is the
    # decree's own allowance sprung from these eaves; the cornice height the
    # facade declined is still legal volume overhead — `comble_ceiling` carries
    # it, per A3.1 — but nothing was built in it, so the two totals differ by
    # exactly that headroom.
    assert building.props["total_height"] < building.props["legal_total_height"]
    assert building.props["legal_total_height"] == pytest.approx(
        grid.envelope.total_height
    )
    assert (
        building.props["legal_total_height"] - building.props["total_height"]
    ) == pytest.approx(grid.unused_facade_headroom, abs=1e-9)
    assert grid.comble_height == pytest.approx(grid.envelope.ridge_height)
    assert grid.comble_ceiling == pytest.approx(
        grid.envelope.ridge_height + grid.unused_facade_headroom
    )
    assert grid.unused_facade_headroom > 0.5


def test_block_datums_reach_the_structure_phase_through_generate():
    class Datums:
        street_width = 24.0
        cornice_height = 18.5
        string_course_levels = ()
        balcony_levels = ()

    # The site agrees with the block about the street (A4.8) and disagrees
    # with nothing: what is under test is that the block's *cornice* reaches
    # the structure phase, and 18.5 m is not what a 24 m street yields.
    building, _ = generate(site(street_width=24.0), Datums())
    assert building.props["legal_cornice_ceiling"] == pytest.approx(18.5)


def test_a_grand_building_on_a_boulevard_is_taller_than_a_modest_one():
    grand, _ = generate(site(klass=BuildingClass.GRAND))
    modest, _ = generate(site(klass=BuildingClass.MODEST))
    assert grand.props["total_height"] > modest.props["total_height"]


@pytest.mark.parametrize("year", [1820, 1858, 1859, 1883, 1884, 1901, 1902, 1913])
@pytest.mark.parametrize("ground", list(GroundProgramme))
def test_the_pipeline_survives_the_situation_space(year, ground):
    s = site(year=year, ground=ground, parcel_width=13.0)
    building, log = generate(s)
    sil = next(n for n in walk(building) if n.kind == "silhouette")
    grid = solve_structure(s)
    assert Silhouette(sil.props["points"]).within(grid.envelope)
    assert era_for_year(year) in set(Era)


# ===========================================================================
# A15.2 — a two-storey garret carries two rows of lucarnes
# ===========================================================================


def test_a_two_storey_garret_gives_both_its_storeys_windows():
    """**The one thing A15.2 lets anyone assert about the second mode.**

    The rate at which a comble takes two storeys of *chambres de bonne* is
    INFERRED and must not be calibrated — Daly's 3-of-9 is drawn from a
    quantity his own measurement pass marks INSUFFICIENT. What IS contractual
    is that both modes occur and that the second one is *visible*: a garret
    standing two storeys of rooms has two rows of windows in its brisis,
    because the brisis is the rooms' outside wall and a wall with rooms behind
    it and no windows in it is the bare-zinc defect A8.3 named.

    **A19.2 renamed this test and widened what it counts.** It used to require
    two rows of *lucarnes*, which is not what either deep-comble plate shows:
    the row under the eaves is a lucarne and the storey below has its windows
    in the plane of the brisis. So what is contractual is that both storeys are
    LIT and that each says which storey it lights — not that both are lucarnes.
    The strength is unchanged: a row with no openings still fails.

    Asserted mid-block, where the roof surface is one flat band the whole
    frontage wide. On a hipped corner the surface falls away toward the
    returns and A9.3's own check drops the lucarnes that would stand over the
    sky beyond the hip — which is a different rule, tested with A9.3.
    """
    seen = 0
    for depth in (18.0, 22.0, 30.0):
        for street in (15.0, 20.0, 30.0):
            s = site(
                street_width=street, parcel_width=14.0, parcel_depth=depth,
                year=1865, klass=BuildingClass.COMFORTABLE,
                ground=GroundProgramme.SHOP, corner=False,
            )
            grid, _roled, _sil, others = run(s)
            if grid.extra_garret_storeys == 0:
                continue
            seen += 1
            assert len(grid.comble_storeys) == 2, grid.comble_storeys
            # Both kinds count: A19.2 puts the lower storey's openings in the
            # brisis face and keeps the register under the eaves a lucarne.
            lit_nodes = [
                n for n in others if n.kind in ("dormer", "brisis_window")
            ]
            rows = {n.trace[0].inputs["row"] for n in lit_nodes}
            assert rows == {0, 1}, (
                f"{street} m street, {depth} m plot: a garret of "
                f"{len(grid.comble_storeys)} storeys carries openings in rows "
                f"{sorted(rows)} — the second storey has no windows"
            )
            # ...and the split is by row, never mixed within one.
            by_row: dict[int, set[str]] = {}
            for n in lit_nodes:
                by_row.setdefault(n.trace[0].inputs["row"], set()).add(n.kind)
            assert by_row[0] == {"brisis_window"}, by_row
            assert by_row[1] == {"dormer"}, by_row
            # Each row lights its own storey, and says which.
            lit = {
                n.trace[0].inputs["row"]: (
                    n.props.get("lights_storey_index")
                    if n.kind == "dormer"
                    else n.trace[0].inputs.get("lights_storey_index")
                )
                for n in lit_nodes
            }
            assert lit[0] is not None and lit[1] is not None
            assert lit[1] == lit[0] + 1, lit
            # Both rows stand ON the brisis, under the fold this phase cut.
            fold = grid.brisis_height
            for n in lit_nodes:
                head = n.props["y"] - grid.built_height + n.props["h"]
                assert head <= fold + 1e-6, (street, depth, n.kind, head, fold)
    assert seen > 0, "no two-storey garret in the sweep — A15.1 is unreachable"


# ---------------------------------------------------------------------------
# A19.2 — the brisis carries a storey, and it is not a row of dormers
# ---------------------------------------------------------------------------


def _comble_openings(others):
    return (
        [n for n in others if n.kind == "dormer"],
        [n for n in others if n.kind == "brisis_window"],
    )


def test_a_one_band_comble_is_all_lucarnes():
    """The majority case, and the one A19.2 must not disturb. A comble standing
    one band of brisis has a single garret storey, that storey IS the register
    under the eaves, and its openings are lucarnes exactly as before."""
    grid, _roled, _sil, others = run(site(parcel_depth=11.0))
    dormers, windows = _comble_openings(others)
    assert dormers, "a one-band comble should still carry lucarnes"
    assert windows == [], (
        "a comble with one garret storey has no row BELOW the register under "
        "the eaves, so nothing here is a window in the face"
    )


def test_the_lower_garret_row_is_a_window_and_the_top_row_is_a_lucarne():
    """A19.2, asked of a comble that actually stands two bands.

    The split is by ROW and not by taste: the register under the eaves is the
    lucarne, every row below it is a window in the slope. So the two kinds must
    both appear, and the windows must all sit lower than the lucarnes."""
    grid, _roled, _sil, others = run(
        site(street_width=22.0, parcel_width=11.0, parcel_depth=16.0,
             klass=BuildingClass.GRAND)
    )
    dormers, windows = _comble_openings(others)
    assert dormers, "the top row must still be lucarnes"
    assert windows, (
        "a comble standing two bands must put its lower storey's windows in "
        "the brisis face — this situation was chosen because it stands two"
    )
    lowest_dormer = min(float(d.props["y"]) for d in dormers)
    highest_window = max(float(w.props["y"]) for w in windows)
    assert highest_window < lowest_dormer, (
        f"a brisis window at {highest_window:.3f} m stands at or above a "
        f"lucarne at {lowest_dormer:.3f} m — the rows have crossed"
    )


def test_a_brisis_window_is_flush_and_railed_and_states_its_own_railing():
    """It is a hole in a wall, so it carries what a hole in a wall carries: a
    garde-corps, and the count of bars in it. The count is stated in the IR
    because a renderer choosing a bar spacing is a renderer deciding — the
    thing ``check_renderer_dumb`` exists to forbid, and the thing that put two
    opinions about one railing in two modules the last six times."""
    grid, _roled, _sil, others = run(
        site(street_width=22.0, parcel_width=11.0, parcel_depth=16.0,
             klass=BuildingClass.GRAND)
    )
    _dormers, windows = _comble_openings(others)
    assert windows
    for w in windows:
        assert w.props.get("garde_corps") is True
        assert int(w.props["bar_count"]) >= 2, w.props
        # Flush with the slope: it states the roof's own setback at its head,
        # so a consumer places it ON the brisis instead of guessing an offset.
        assert float(w.props["setback"]) > 0.0
        assert float(w.props["h"]) > 0.0 and float(w.props["w"]) > 0.0
