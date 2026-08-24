"""Invariant sweep for termination (S7 / Gate G7).

Gate G7 asks for two things, and both of them are claims about a *population*
of buildings rather than about one:

- **the silhouette polyline lies within the envelope for every (width × year)
  in a sweep** — a comble that escapes its gabarit at one street width in
  three hundred is exactly the kind of defect a handful of point tests misses;
- **1884+ produces an arc-derived profile and pre-1884 a 45° plane, visible in
  the IR** — the decree's change of geometry has to be legible in the emitted
  polyline itself, not only in a prop that names the era.

### Why this file does not call ``Silhouette.within``

``within`` is the thing under test. Asserting containment by calling it would
only prove that ``terminate`` and ``within`` share an opinion — and they share
a *source*, ``GabaritEnvelope.setback_at``, so they would agree even if that
function were wrong.

So containment here is re-derived from the other side of the envelope:
``GabaritEnvelope.max_height_for_setback(inset)`` — the inverse of
``setback_at``, separate code in ``reglement.py``, ported from the oracle — and
it is evaluated not at the polyline's vertices but at points sampled *along its
segments*. Vertex containment would be a weaker claim than it looks: what the
regulation bounds is the built solid, i.e. the whole line, and only the
convexity of the three envelopes makes the two equivalent. Sampling the
segments removes that (correct, but unstated) assumption from the assertion.

``test_the_sweep_could_have_failed`` closes the loop by pushing real
silhouettes 5 cm forward and confirming this checker rejects them.
"""

from __future__ import annotations

import math

import pytest

from buildings.ir.serial import from_json, to_json
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.generate import generate
from buildings.typologies.paris.reglement import RoofEnvelope, era_for_year, get_reglement
from buildings.typologies.paris.structure import BRISIS_RISE, solve_structure
from buildings.typologies.paris.terminate import (
    _dormer_skirt,
    _shortest_brisis_that_carries_a_lucarne,
)

#: A12.1. The shortest brisis with a garret window still in it — the plumber's
#: skirt, the shortest face worth cutting a hole in a roof for, and the head
#: over it, added up. It is read from the module under test rather than typed
#: out here because it is a BOUND in the assertion below and not the claim:
#: what is being asserted is that a flat terrasse survives only where taking
#: the fold lower would have put the lucarne out of the roof, and a second
#: copy of the three numbers would only test the copy.
_LOWEST_LUCARNE_BEARING_BRISIS = _shortest_brisis_that_carries_a_lucarne(
    float(_dormer_skirt())
)

# The sweep axes. Street widths span the narrow rue (below every height step)
# to the boulevard; years straddle each of the three roof regimes and sit on
# both sides of the 1884 and 1902 hinges; parcel depth matters because the
# comble is cut off where its two opposing slopes meet, so a shallow parcel
# tests a *capped* comble and a deep one an uncapped one.
_STREET_WIDTHS = (6.0, 7.8, 9.75, 12.0, 15.0, 18.0, 20.0, 24.0, 30.0, 40.0)
_YEARS = (1820, 1845, 1855, 1865, 1878, 1883, 1884, 1890, 1898, 1901, 1902, 1912)
_DEPTHS = (8.0, 11.0, 14.0, 22.0)
_PARCEL_WIDTHS = (5.6, 8.0, 12.0, 18.0)
_CLASSES = tuple(BuildingClass)
_GROUNDS = tuple(GroundProgramme)

_TOL = 1e-6


def _site(street: float, year: int, depth: float, i: int) -> SiteContext:
    """One situation. Class, ground, parcel width and seed cycle with the
    index so the corpus covers them without multiplying out to a sweep that
    takes a minute to run."""
    return SiteContext(
        street_width=street,
        parcel_width=_PARCEL_WIDTHS[i % len(_PARCEL_WIDTHS)],
        parcel_depth=depth,
        year=year,
        klass=_CLASSES[i % len(_CLASSES)],
        ground=_GROUNDS[i % len(_GROUNDS)],
        corner=(i % 7 == 0),
        seed=1000 + i,
    )


@pytest.fixture(scope="module")
def corpus():
    """Every (width × year × depth) in the sweep, generated end to end.

    Built once for the module: `generate` runs all five phases, and the point
    of an invariant sweep is the population, not the cost of making it.
    """
    out = []
    i = 0
    for street in _STREET_WIDTHS:
        for year in _YEARS:
            for depth in _DEPTHS:
                s = _site(street, year, depth, i)
                i += 1
                root, _log = generate(s)
                grid = solve_structure(s)
                sil = next(n for n in root.children if n.kind == "silhouette")
                roof = next(n for n in root.children if n.kind == "roof")
                out.append((s, grid.envelope, root, sil, roof))
    return out


# ---------------------------------------------------------------------------
# Containment, re-derived from the inverse of the curve the roof was built from
# ---------------------------------------------------------------------------


def _violations(points, env, tol: float = _TOL, *, anchor: str = "eaves") -> list[str]:
    """Every way this polyline leaves the legal solid, in metres.

    Independent of ``Silhouette.within``: the datum is read off the polyline or
    off the envelope, and every sampled point is tested against
    ``max_height_for_setback`` — the inverse of the curve — rather than against
    ``setback_at``.

    ``anchor`` selects the datum the SLOPES are measured from, and the two
    choices are different questions rather than two spellings of one:

    - ``"eaves"`` — **legality**, and the default (A3.1). The règlement draws
      the comble from the égout du toit: "combles must be inscribed below a
      45° diagonal springing from the eaves". So the curve springs from the
      eaves the building actually has, and a facade that stopped short carries
      the whole roof shape down with it rather than banking the difference.
    - ``"cornice"`` — the strictly weaker query, the same setbacks measured
      from ``env.facade_height``. It is not legality: A2.4 briefly said it was,
      which accepted combles the diagonal from the real eaves forbids, and that
      amendment is retracted. It is asserted here only to confirm the ordering
      between the two has not inverted.

    The **ceiling is not on that axis at all**, and putting it there was the
    other half of the original defect. The top of the legal solid is
    ``env.total_height`` — a height above the pavement — while
    ``env.ridge_height`` is a height above the legal cornice; comparing an
    eaves-relative height against ``ridge_height`` re-anchors a cornice number
    at a lower line and charges the building twice for the facade height it
    declined to build. So both anchorings check the same ceiling, and only the
    slopes move. The headroom comes back to the roof as a *taller top on the
    same curve*, which costs inset, not as a moved springing, which would be
    free and illegal.
    """
    bad: list[str] = []
    on_plane = [y for inset, y in points if abs(inset) <= 1e-6]
    eaves = max(on_plane) if on_plane else 0.0
    datum = eaves if anchor == "eaves" else env.facade_height

    if eaves > env.facade_height + tol:
        bad.append(f"eaves {eaves:.4f} m > facade limit {env.facade_height:.4f} m")

    def check(inset: float, y: float, where: str) -> None:
        if inset < -tol:
            bad.append(f"{where}: inset {inset:+.4f} m overhangs the public way")
            return
        if y > env.total_height + tol:
            bad.append(
                f"{where}: {y:.4f} m above the pavement, the gabarit tops out at "
                f"{env.total_height:.4f} m"
            )
        h = y - datum
        if h <= tol:
            return
        allowed = env.max_height_for_setback(inset)
        if h > allowed + tol:
            bad.append(
                f"{where}: at inset {inset:.4f} m the envelope reaches {allowed:.4f} m, "
                f"point is at {h:.4f} m above the {anchor}"
            )

    for n, (inset, y) in enumerate(points):
        check(inset, y, f"vertex {n} ({inset:.3f}, {y:.3f})")

    # The regulation bounds the built solid, not a set of corners: sample the
    # segments too. (For all three envelopes the legal region is convex, so
    # this cannot fail where the vertices pass — which is precisely why the
    # assertion should not quietly depend on that.)
    for n, ((i0, y0), (i1, y1)) in enumerate(zip(points, points[1:])):
        for k in range(1, 12):
            t = k / 12.0
            check(i0 + (i1 - i0) * t, y0 + (y1 - y0) * t, f"segment {n} at t={t:.2f}")
    return bad


def test_every_silhouette_in_the_sweep_lies_within_its_envelope(corpus) -> None:
    """G7's first clause, over the whole situation space."""
    for s, env, _root, sil, _roof in corpus:
        bad = _violations(sil.props["points"], env)
        assert not bad, (
            f"street {s.street_width} m, year {s.year}, depth {s.parcel_depth} m, "
            f"{s.klass.value}: {bad[:3]}"
        )


def test_every_silhouette_in_the_sweep_is_legal_from_the_cornice_too(corpus) -> None:
    """The weaker query, checked for ordering only (A3.1).

    The test above measures from the built eaves, which is how ``terminate``
    constructs and — since the règlement springs the comble from the égout du
    toit — how legality is asked. This one measures from the legal cornice,
    which is the weaker of the two and is NOT the legal question: it is here to
    confirm the ordering between them has not inverted somewhere, not to catch
    a roof the eaves-anchored pass would have missed.
    """
    for s, env, _root, sil, _roof in corpus:
        bad = _violations(sil.props["points"], env, anchor="cornice")
        assert not bad, (
            f"street {s.street_width} m, year {s.year}, depth {s.parcel_depth} m, "
            f"{s.klass.value}: {bad[:3]}"
        )


def test_the_two_anchorings_are_ordered_and_genuinely_differ(corpus) -> None:
    """A3.1's substance, over the population.

    Two claims. **Ordering:** the slopes measured from the eaves are a strictly
    harder demand than the slopes measured from the legal cornice, so a
    silhouette clean under the legal (eaves) anchoring is clean under the
    weaker one — which is what makes it safe to keep both, and which way round
    they go. **Nothing over the decree's own allowance that is not a room:**
    across the sweep there are buildings leaving a metre and more of cornice
    height unbuilt, and not one of them turns that height into roof. The
    unspent facade allowance is still not a target.

    **A8.5.** This used to assert the opposite: that the unbuilt cornice
    height came back as roof, so the comble stood taller over its own eaves
    than ``ridge_height`` stands over the cornice, by exactly the headroom.
    That is still true of the CEILING (A3.1 — the legal solid does not descend
    with the eaves) and the ceiling is asserted below, but building to it made
    the roof grow by exactly what the facade gave up: the sum never moved, and
    every building in the sweep reached ``total_height``. The gap between what
    is built and what is permitted is the thing being checked now, and it has
    to be real.

    **A15.1** is why the bound is no longer ``ridge_height`` flat. A8.5's
    version of this assertion said the comble never exceeds the decree's own
    allowance sprung from the eaves, and it was true — because the 45° era's
    allowance stands exactly one storey of *chambres de bonne* and the
    generator could not build a second. That made the 1865 comble a constant
    3.20 m over 180 sites against Daly's measured 2.69-7.00 m in the same era.
    A building may now buy a further storey of garret out of its own cornice
    height, so the bound rises by whole rooms — and by nothing else. What is
    asserted here is the harder claim that replaces it: **every centimetre of
    comble above the decree's allowance is a whole storey of chambres de
    bonne, and that storey is in the IR.** The count is read off the STOREYS
    the earlier phases emitted, not off the roof, so a roof that simply grew
    has nothing to point at.
    """
    biggest_gap = 0.0
    left_under_the_ceiling = 0
    for s, env, _root, sil, roof in corpus:
        pts = sil.props["points"]
        eaves = _eaves(sil)
        headroom = env.facade_height - eaves
        assert headroom >= -_TOL, s
        biggest_gap = max(biggest_gap, headroom)
        # Strict clean implies legal clean, never the reverse.
        if not _violations(pts, env):
            assert not _violations(pts, env, anchor="cornice")

        comble = max(y for _i, y in pts) - eaves
        half = s.parcel_depth / 2.0
        depth_limited = env.max_height_for_setback(half)
        ceiling = max(0.0, min(env.ridge_height + headroom, depth_limited))
        # A15.1. How many storeys of garret the decree's own allowance stands,
        # and how many this building actually has — the second read off the
        # IR's storeys rather than off anything the roof says about itself.
        band = float(BRISIS_RISE)
        decree = max(0.0, min(env.ridge_height, depth_limited))
        stands = max(1, int(decree / band + 1e-9)) if decree > 0.0 else 0
        rooms = sum(
            1
            for n in _root.children
            if n.kind == "storey" and n.props.get("within_comble")
        )
        bought = max(0, rooms - stands)
        allowance = max(0.0, min(env.ridge_height + bought * band, depth_limited))
        assert comble <= allowance + 1e-6, (
            f"{s.year}, street {s.street_width} m, depth {s.parcel_depth} m: comble "
            f"{comble:.4f} m over the eaves, past the decree's own comble allowance "
            f"sprung from those eaves plus the {bought} whole storey(s) of chambres "
            f"de bonne this building bought out of its cornice, {allowance:.4f} m "
            f"({env.ridge_height:.4f} m above the cornice, capped by the "
            f"{depth_limited:.4f} m the plot reaches). It holds {rooms} garret "
            f"storey(s) where the decree's allowance stands {stands}"
        )
        assert bought <= 1, (
            f"{s.year}, street {s.street_width} m: {rooms} storeys of garret against "
            f"the {stands} the decree's own allowance stands — the trade is one "
            "storey, not a ladder (A15.1)"
        )
        # And it is under the ceiling, which is a different and larger number
        # wherever the facade stopped short.
        assert comble <= ceiling + _TOL, s
        # Nothing in either bound mentions the class, and the section built
        # inside them does not either (A8.3/A8.5). The GARRET'S WALL sits on a
        # whole number of chambres de bonne, or on the whole comble where
        # there was not one room's worth of height to give — and the fold this
        # phase cuts is at or below it, never above the rooms behind it.
        #
        # **A12.1**: the fold is no longer that wall. Running the terrasson
        # from a storey line put it within 0.30 m of the ridge on the
        # canonical case and flattened the remaining 3.69 m of plot, which is
        # a slab with a nick in it. The fold now comes down the same gabarit
        # until the terrasson reaches the ridge in the middle of the plot, so
        # the claim below is the pair of claims that replaces "the fold is a
        # storey line": it is under the wall, and the section above it is
        # either a terrasson that runs the whole way or a plot deep enough to
        # have earned the flat terrasse it kept.
        if comble > 1e-6:
            grid = solve_structure(s)
            wall = min(grid.brisis_height, comble)
            bands = wall / float(BRISIS_RISE)
            brisis = comble * float(roof.props["break_pct"])
            assert brisis <= comble + 1e-6, s
            assert (
                abs(bands - round(bands)) < 1e-6
                or abs(wall - comble) < 1e-6
            ), (
                f"{s.year}, street {s.street_width} m: the garret's wall stands at "
                f"{wall:.4f} m, which is {bands:.3f} chambres de bonne — the rooms are "
                "whole storeys, not fractions"
            )
            assert brisis <= wall + 1e-6, (
                f"{s.year}, street {s.street_width} m: the section folds at "
                f"{brisis:.4f} m, above the {wall:.4f} m of garret wall behind it"
            )
            ridge_inset = float(roof.props["ridge_setback"])
            if ridge_inset >= half - 1e-6:
                # The terrasson got to the middle of the plot, so the fold is
                # exactly where that line crosses the gabarit. Re-derived from
                # the polyline and from the pitch STRUCTURE gave the terrasson
                # (read off its own two ends), never from a constant restated
                # here: the fold is on the curve, and the chord from it to the
                # ridge has the terrasson's pitch.
                fold_inset = env.setback_at(brisis)
                assert any(
                    abs(i - fold_inset) < 1e-6 and abs(y - eaves - brisis) < 1e-6
                    for i, y in pts
                ), f"{s.year}: the fold is not a vertex of the section"
                wall_inset = env.setback_at(wall)
                if grid.ridge_setback > wall_inset + 1e-6 and comble > wall + 1e-9:
                    pitch = (comble - wall) / (grid.ridge_setback - wall_inset)
                    cut = (comble - brisis) / max(half - fold_inset, 1e-9)
                    assert abs(cut - pitch) < 1e-6, (
                        f"{s.year}, street {s.street_width} m: the terrasson this phase "
                        f"cut runs at {math.degrees(math.atan(cut)):.3f}°, not the "
                        f"{math.degrees(math.atan(pitch)):.3f}° structure gave it"
                    )
            else:
                # A flat terrasse survived. It may only survive where taking
                # the fold lower would have put the lucarne out of the roof —
                # a plot deep enough to earn a deck — or where the fold is
                # still the garret's own wall because the terrasson never had
                # the plot to reach the ridge in.
                assert (
                    abs(brisis - wall) < 1e-6
                    or brisis >= _LOWEST_LUCARNE_BEARING_BRISIS - 1e-6
                ), (
                    f"{s.year}, street {s.street_width} m, depth {s.parcel_depth} m: "
                    f"the section keeps {half - ridge_inset:.2f} m of flat terrasse "
                    f"behind a fold at {brisis:.4f} m, which is neither the garret's "
                    f"wall ({wall:.4f} m) nor a brisis with a lucarne in it"
                )
        if headroom > 0.05 and ceiling > comble + 0.05:
            left_under_the_ceiling += 1
            assert not _violations(pts, env), s
            assert max(y for _i, y in pts) < env.total_height - _TOL, (
                f"{s.year}: the building still reaches its legal total"
            )

        # Nothing may go a centimetre past the CEILING: raise the whole comble
        # to it and then 5 cm further and the eaves-anchored checker must bite,
        # so "the roof came down with the eaves" has not turned into "the top
        # is unguarded".
        if env.ridge_height > 0.5 and depth_limited > ceiling:
            lift = ceiling - comble + 0.05
            over = tuple(
                (i, y + lift) if y > eaves + 1e-9 else (i, y) for i, y in pts
            )
            assert _violations(over, env), (
                f"{s.year}: 5 cm above the gabarit's own top went unnoticed"
            )
    assert biggest_gap > 1.0, (
        "no building in the sweep stopped meaningfully short of its ceiling, so the "
        "sweep cannot have exercised the difference between the two anchorings"
    )
    assert left_under_the_ceiling > 0, (
        "no building in the sweep left any of its comble ceiling unused, so the sweep "
        "cannot have exercised A8.5 at all"
    )
    assert left_under_the_ceiling > len(corpus) // 4, (
        f"only {left_under_the_ceiling} of {len(corpus)} buildings left any of their "
        "comble ceiling unused — A8.5 has to reach the geometry, not only the "
        "predicate that judges it"
    )


def test_the_sweep_could_have_failed(corpus) -> None:
    """The checker is not vacuously true.

    Every silhouette in the corpus, nudged 5 cm forward at its highest comble
    vertex, must be rejected — otherwise the sweep above proves nothing about
    buildings that *do* break out.
    """
    caught = 0
    for _s, env, _root, sil, _roof in corpus:
        pts = list(sil.props["points"])
        eaves = max(y for inset, y in pts if abs(inset) <= 1e-6)
        comble = [n for n, (_i, y) in enumerate(pts) if y > eaves + 1e-6]
        if not comble:
            continue  # no comble at all: nothing to push out
        n = comble[0]  # the lowest comble vertex, where the envelope is tightest
        inset, y = pts[n]
        pts[n] = (inset - 0.05, y)
        assert _violations(tuple(pts), env), "a 5 cm breakout went unnoticed"
        caught += 1
    assert caught > len(corpus) // 2, "most of the corpus should have had a comble to push"


def test_a_taller_facade_than_the_street_earns_is_caught(corpus) -> None:
    """The second clause of containment — the cornice line — bites as well.

    Each silhouette is raised by exactly the headroom it had left plus half a
    metre, which puts its eaves above the height its street earns and nothing
    else wrong. Every one of them must be rejected, and rejected *for that
    reason*: an assertion that merely returned "not legal" could be catching
    the comble clause instead.
    """
    for s, env, _root, sil, _roof in corpus:
        lift = env.facade_height - _eaves(sil) + 0.5
        pts = tuple((i, y + lift) for i, y in sil.props["points"])
        bad = _violations(pts, env)
        assert any("facade limit" in b for b in bad), f"{s.year}: {bad[:3]}"


def _eaves(sil) -> float:
    return max(y for inset, y in sil.props["points"] if abs(inset) <= 1e-6)


# ---------------------------------------------------------------------------
# G7's second clause: the decree's geometry is legible in the polyline
# ---------------------------------------------------------------------------


def _comble_segments(points):
    """The comble part of the polyline as (d_inset, d_height) segments,
    dropping the vertical run up the facade and any zero-length repeats."""
    eaves = max(y for inset, y in points if abs(inset) <= 1e-6)
    above = [(i, y) for i, y in points if y >= eaves - 1e-9]
    segs = []
    for (i0, y0), (i1, y1) in zip(above, above[1:]):
        di, dy = i1 - i0, y1 - y0
        if abs(di) < 1e-9 and abs(dy) < 1e-9:
            continue
        segs.append((di, dy))
    return segs


def test_pre_1884_the_brisis_is_one_straight_45_degree_plane(corpus) -> None:
    """Before Alphand the comble is bounded by a diagonal, so the part of its
    section that follows the gabarit — the brisis — is a single straight run at
    45°, and that is visible in the IR without reading any prop that names the
    era.

    **A8.3.** This used to demand that the WHOLE comble be that one run, and
    it was the assertion standing guard over the defect: a 45° diagonal is a
    legal maximum, the building inside it is a *comble brisé*, and demanding
    one plane demanded that no Second Empire building have a mansard break.
    The brisis is the plane the decree draws; what stands above it is the
    terrasson, and it is asserted here too — shallower, and there.
    """
    seen = 0
    for s, env, _root, sil, roof in corpus:
        if s.year >= 1884:
            continue
        rising = [
            (di, dy) for di, dy in _comble_segments(sil.props["points"]) if dy > 1e-9
        ]
        assert rising, (s.year, s.street_width)
        di, dy = rising[0]
        assert math.isclose(dy, di, rel_tol=1e-6, abs_tol=1e-6), (
            f"{s.year}: brisis slope is {math.degrees(math.atan2(dy, di)):.2f}°, "
            "not the 45° diagonal of the ordonnance"
        )
        # The brisis is ONE run — the diagonal is straight, so nothing may
        # subdivide it — and anything above it is shallower.
        assert len(rising) <= 2, (
            f"{s.year}, street {s.street_width} m: a comble brisé under a diagonal is "
            f"a brisis and a terrasson, got {len(rising)} rising segment(s)"
        )
        for di2, dy2 in rising[1:]:
            assert dy2 / max(di2, 1e-12) < 1.0 - 1e-6, (
                f"{s.year}: the terrasson is not shallower than the brisis it folds "
                f"from ({math.degrees(math.atan2(dy2, di2)):.2f}°)"
            )
        assert env.roof_envelope is RoofEnvelope.DIAGONAL_45
        seen += 1
    assert seen > 0, "the sweep contained no pre-1884 building"


def test_the_second_empire_comble_actually_breaks(corpus) -> None:
    """A8.3, stated positively and on the population.

    Measured before the fix: every pre-1884 roof node stated
    ``lower=45.0, upper=45.0, break_pct=1.00``, so the renderer — correctly
    obeying the IR — drew no break on the whole Haussmann era. The break is
    the single most recognisable thing about a Paris roof, so the IR has to
    state it, and it has to state it as something a consumer can act on: two
    angles that differ, and a fold below the ridge.
    """
    broke = 0
    for s, env, _root, sil, roof in corpus:
        if s.year >= 1884:
            continue
        if roof.props["h"] <= 0.25:
            continue  # a comble with no height to break in
        lower = float(roof.props["lower_angle_deg"])
        upper = float(roof.props["upper_angle_deg"])
        pct = float(roof.props["break_pct"])
        assert 0.0 < pct <= 1.0, (s.year, pct)
        if pct >= 0.995:
            continue  # the fold landed on the ridge: no terrasson to draw
        broke += 1
        assert lower > upper + 1.0, (
            f"{s.year}, street {s.street_width} m: stated {lower:.1f}° / {upper:.1f}° — "
            "a mansard's brisis is steeper than its terrasson, or there is no mansard"
        )
        assert math.isclose(lower, 45.0, abs_tol=0.5), (s.year, lower)
    assert broke > 0, "no Second Empire building in the sweep has a mansard break"


def test_the_break_is_low_enough_to_see_on_an_ordinary_parcel(corpus) -> None:
    """A12.1, stated positively and on the population.

    A8.3 got the break INTO the IR; it did not get it anywhere a viewer could
    see it. Measured before this amendment, every pre-1884 comble on an
    ordinary lot stated its fold at 90.6 % or more of its height, with a
    terrasson of 0.30 m above it and the rest of the plot flat: two angles
    that differ, a fold that is technically below the ridge, and a roof that
    reads as a slab with a nick near the top.

    So the claim is about WHERE the fold is, not merely that there is one.
    On a parcel at least 14 m deep — an ordinary haussmannian lot, deep enough
    that the section has a choice — the terrasson must rise a quarter of a
    storey of garret over the fold. On the one-band comble the whole sweep
    used to hold that is the original claim unchanged, the fold in the lower
    three quarters of the comble; the sweep's own worst case is 67.9 %, and
    Daly's section of 125 Champs-Élysées folds at about two thirds.

    **A15.1** is why it is stated per BAND. A comble standing two storeys of
    *chambres de bonne* has 5.80 m of brisis because it has 5.80 m of rooms,
    and measuring its fold against a flat fraction of the whole comble would
    call a legible 1.30 m terrasson a hairline — the same 1.30 m the one-band
    case leaves, over a roof that is twice as tall. The quarter is A12.1's
    number and the storey is what the fold now has to climb over; a two-band
    comble folding at 90 % is still caught.

    A plot with nothing left over is not held to it and should not be: where
    the terrasson already reaches the middle of the plot there is no flat deck
    to remove, the two opposing slopes simply meet, and a fold at 92 % of a
    3.13 m comble is what the geometry leaves. That is the parcel talking and
    it is the same rule — A12.1's own first stopping condition. It is asked of
    the SECTION (``has_terrasse``) rather than of a depth threshold, because
    **A15.1** made the threshold wrong: a 14 m plot leaves a deck under one
    storey of garret and none under two, since the brisis of a two-storey
    comble alone stands 5.80 m back out of the 7.00 m the plot has.
    """
    seen = 0
    for s, _env, _root, _sil, roof in corpus:
        if s.year >= 1884 or roof.props["h"] <= 0.25:
            continue
        if not roof.props["has_terrasse"]:
            continue
        grid = solve_structure(s)
        bands = max(1, int(grid.brisis_height / float(BRISIS_RISE) + 1e-9))
        allowed = 1.0 - 0.25 / bands
        pct = float(roof.props["break_pct"])
        seen += 1
        assert pct < allowed, (
            f"{s.year}, street {s.street_width} m, depth {s.parcel_depth} m: the fold "
            f"sits at {pct:.1%} of a {roof.props['h']:.2f} m comble standing {bands} "
            f"storey(s) of garret, which is the "
            f"{roof.props['h'] * (1.0 - pct):.2f} m hairline terrasson A12.1 is about"
        )
    assert seen > 0, "the sweep contained no pre-1884 building on an ordinary lot"


def _chord_deviation(points, env, brisis_top: float | None = None) -> float:
    """How far the emitted polyline falls short of the curve it traces, in
    metres: the largest gap between a rising comble segment and the envelope
    at the same height.

    A polyline that merely *touches* the arc at two ends and cuts straight
    across it is still inside the legal solid — containment cannot see the
    difference — but it is no longer the arc, and G7 asks for the arc to be
    visible in the IR. This is the measurement that can tell them apart.

    Measured over the **brisis** only (A8.3). The brisis is the plane that
    follows the gabarit and is the one this test is about; the terrasson above
    it is deliberately a chord, running back inside the envelope to the middle
    of the plot, and folding it into this average would report the roof's own
    shape as an approximation error.
    """
    eaves = max(y for inset, y in points if abs(inset) <= 1e-6)
    worst = 0.0
    for (i0, y0), (i1, y1) in zip(points, points[1:]):
        if y1 - y0 <= 1e-9 or y0 < eaves - 1e-9:
            continue  # the facade, or the flat terrasse across the top
        if brisis_top is not None and y1 > brisis_top + 1e-6:
            continue  # the terrasson: a chord by construction
        for k in range(1, 16):
            t = k / 16.0
            h = (y0 + (y1 - y0) * t) - eaves
            chord = i0 + (i1 - i0) * t
            worst = max(worst, chord - env.setback_at(h))
    return worst


def test_the_polyline_traces_the_arc_instead_of_cutting_across_it(corpus) -> None:
    """The curve is sampled, not approximated by its chord.

    Everything else in this file would pass on a two-point profile: a chord
    lies *inside* the envelope, so containment is happy, and its slope still
    falls from steep to shallow if you give it two segments. Fidelity is the
    claim that survives — the emitted polyline stays within 3 cm of the curve
    the decree draws, everywhere along it. (``terminate`` subdivides until the
    gap at a segment's midpoint is under 2 cm; the margin here covers the rest
    of the segment, not a coarser profile — the sweep's own worst case is
    2.0 cm, where an unrefined profile is off by 15.)
    """
    checked = 0
    for s, env, _root, sil, roof in corpus:
        if env.roof_envelope is RoofEnvelope.DIAGONAL_45:
            continue
        if env.ridge_height < 1.0:
            continue  # a stub of arc is straight at any sampling
        brisis_top = _eaves(sil) + float(roof.props["h"]) * float(roof.props["break_pct"])
        dev = _chord_deviation(sil.props["points"], env, brisis_top)
        assert dev < 0.03, (
            f"{s.year}, street {s.street_width} m, ridge {env.ridge_height:.2f} m: the "
            f"profile cuts up to {dev * 100:.1f} cm inside the arc it is supposed to "
            "trace — that is a chord, not Alphand's circle"
        )
        checked += 1
    assert checked > 0, "no arc comble in the sweep was tall enough to measure"


def test_from_1884_the_comble_is_an_arc_and_says_so_by_being_curved(corpus) -> None:
    """Alphand replaced the diagonal with an arc of a circle. An arc is
    recognisable without being told: it leaves the eaves far steeper than 45°
    and its slope falls monotonically, which a plane cannot do."""
    seen = 0
    for s, env, _root, sil, _roof in corpus:
        if s.year < 1884:
            continue
        rising = [(di, dy) for di, dy in _comble_segments(sil.props["points"]) if dy > 1e-9]
        if len(rising) < 3:
            # A comble capped very low by a shallow parcel can be a stub with
            # too few samples to read a curve off. Only assert on those with
            # enough of the curve built to be curved.
            continue
        angles = [math.degrees(math.atan2(dy, max(di, 1e-12))) for di, dy in rising]
        assert angles[0] > 60.0, (
            f"{s.year}, street {s.street_width} m: the arc springs at "
            f"{angles[0]:.1f}° — a post-1884 comble is near-vertical at the eaves, "
            "which is what lets a storey stand behind it"
        )
        # Strictly falling, i.e. genuinely curved rather than a polygon of one
        # slope. The 1902 oblique is a flat tail, so allow equality only there.
        for a, b in zip(angles, angles[1:]):
            assert b <= a + 1e-6, f"{s.year}: slope rose again ({a:.2f}° -> {b:.2f}°)"
        assert angles[-1] < angles[0] - 1.0, f"{s.year}: profile is not curved at all"
        assert env.roof_envelope in (
            RoofEnvelope.CIRCULAR_ARC,
            RoofEnvelope.EIGHTH_ARC_OBLIQUE,
        )
        seen += 1
    assert seen > 0, "the sweep contained no arc comble tall enough to read"


def test_from_1902_the_arc_is_continued_by_a_45_degree_oblique(corpus) -> None:
    """Bonnier's rule: an eighth of a circle, then a 45° straight. When the
    parcel is deep enough for the ridge to pass the break, that straight tail
    must be in the polyline."""
    seen = 0
    for s, env, _root, sil, roof in corpus:
        if env.roof_envelope is not RoofEnvelope.EIGHTH_ARC_OBLIQUE:
            continue
        h_break = env.arc_radius * math.sin(math.pi / 4)
        eaves = _eaves(sil)
        # A8.3: read on the BRISIS, which is the run that follows the gabarit.
        # Above the fold the section is the terrasson — a chord back to the
        # middle of the plot — and it is not tracing anything.
        brisis = float(roof.props["h"]) * float(roof.props["break_pct"])
        if brisis <= h_break + 0.05:
            continue  # the brisis stops inside the arc, before the oblique
        rising = [
            (di, dy)
            for (i0, y0), (i1, y1) in zip(sil.props["points"], sil.props["points"][1:])
            for di, dy in ((i1 - i0, y1 - y0),)
            if dy > 1e-9 and y0 >= eaves - 1e-9 and y1 <= eaves + brisis + 1e-4
        ]
        assert rising, (s.year, s.street_width)
        tail_angle = math.degrees(math.atan2(rising[-1][1], max(rising[-1][0], 1e-12)))
        assert abs(tail_angle - 45.0) < 0.5, (
            f"{s.year}, street {s.street_width} m, depth {s.parcel_depth} m: the arc "
            f"should be continued by a 45° oblique, the last run of the brisis is "
            f"{tail_angle:.2f}°"
        )
        seen += 1
    assert seen > 0, "no 1902+ building in the sweep got past the break of its arc"


def test_the_three_regimes_are_all_present_in_the_sweep(corpus) -> None:
    """A containment sweep that only ever saw one envelope would be a much
    smaller claim than it appears."""
    envelopes = {env.roof_envelope for _s, env, _r, _sil, _ro in corpus}
    assert envelopes == set(RoofEnvelope), sorted(e.value for e in envelopes)


def test_the_envelope_in_the_ir_is_the_one_the_decree_names(corpus) -> None:
    """The prop the renderer reads and the geometry it is drawn from agree —
    and both come from ``reglement``, not from a date test in ``terminate``."""
    for s, env, _root, sil, roof in corpus:
        expected = get_reglement(era_for_year(s.year)).roof_envelope
        assert env.roof_envelope is expected
        assert sil.props["envelope"] == expected.value
        assert roof.props["envelope"] == expected.value


# ---------------------------------------------------------------------------
# The polyline is a silhouette, and it belongs to this building
# ---------------------------------------------------------------------------


def test_the_polyline_rises_from_the_pavement_and_never_descends(corpus) -> None:
    for s, _env, _root, sil, _roof in corpus:
        pts = sil.props["points"]
        assert pts[0] == (0.0, 0.0), f"{s.year}: silhouette starts at {pts[0]}"
        assert all(b >= a - 1e-9 for (_, a), (_, b) in zip(pts, pts[1:])), s
        assert all(b >= a - 1e-9 for (a, _), (b, _) in zip(pts, pts[1:])), (
            f"{s.year}: the section doubles back on itself"
        )


def test_the_comble_stands_on_the_storeys_and_not_in_the_air(corpus) -> None:
    """The eaves of the silhouette are the top of the built stack — the roof
    springs from the building, not from the height the law would have allowed.

    "The built stack" is the *stone face*: since A2.1 the stack can carry a
    storey standing inside the comble — the chambres de bonne — and that
    storey stands on the eaves rather than raising them. Its own roof is the
    comble this silhouette already draws, so counting it here would ask the
    roof to spring from the top of itself.
    """
    for s, env, root, sil, roof in corpus:
        storeys = [
            n
            for n in root.children
            if n.kind == "storey" and n.props.get("role") != "attic"
        ]
        top = max(float(n.props["y"]) + float(n.props["h"]) for n in storeys)
        eaves = _eaves(sil)
        assert math.isclose(eaves, top, abs_tol=1e-6), (
            f"{s.year}: eaves at {eaves:.4f} m, storeys stop at {top:.4f} m"
        )
        assert math.isclose(float(sil.props["eaves_height"]), eaves, abs_tol=1e-6)
        assert math.isclose(float(roof.props["eaves_height"]), eaves, abs_tol=1e-6)
        # ... and the building never claims a height its street cannot earn.
        assert eaves <= env.facade_height + 1e-6
        assert float(root.props["total_height"]) <= env.facade_height + env.ridge_height + 1e-6


def test_the_roof_node_and_the_silhouette_describe_the_same_roof(corpus) -> None:
    """Two nodes carry the comble — the drawable profile and the section. If
    they could disagree the renderer would have to choose between them, which
    is a composition decision it is not allowed to make."""
    for s, _env, _root, sil, roof in corpus:
        eaves = _eaves(sil)
        section = [(i, round(y - eaves, 6)) for i, y in sil.props["points"] if y > eaves + 1e-9]
        profile = [(i, round(h, 6)) for i, h in roof.props["profile"] if h > 1e-9]
        assert section == profile, s


def test_dormers_stand_inside_the_envelope_too(corpus) -> None:
    """A lucarne is built mass: its head is bound by the same curve. It sits
    as far forward as the gabarit allows at its own head height, so this is
    tight, not slack.

    Its head is measured against the comble that is actually over it — the
    roof node's own height — and against the top of the legal solid. Against
    ``env.ridge_height`` it would be the anchor mix again, comparing a height
    above the eaves with a height above the cornice, and passing only because a
    lucarne is short (A3.1 §3).
    """
    seen = 0
    for s, env, root, sil, roof in corpus:
        eaves = _eaves(sil)
        comble = float(roof.props["h"])
        for node in root.children:
            if node.kind != "dormer":
                continue
            head = float(node.props["y"]) + float(node.props["h"]) - eaves
            inset = float(node.props["setback"])
            assert head <= comble + 1e-6, s
            assert eaves + head <= env.total_height + 1e-6, s
            assert head <= env.max_height_for_setback(inset) + 1e-6, (
                f"{s.year}: dormer head {head:.4f} m above the eaves at inset "
                f"{inset:.4f} m, envelope allows {env.max_height_for_setback(inset):.4f} m"
            )
            seen += 1
    assert seen > 0, "the sweep produced no dormers at all"


def test_the_silhouette_survives_the_ir_and_is_still_legal(corpus) -> None:
    """The renderer sees the serialised tree and nothing else (A1.4): the
    polyline has to come back as points, not as a list of lists that no longer
    compares equal, and it has to still pass containment."""
    for s, env, root, sil, _roof in corpus[::17]:
        back = from_json(to_json(root))
        assert back == root, s
        sil2 = next(n for n in back.children if n.kind == "silhouette")
        assert sil2.props["points"] == sil.props["points"]
        assert not _violations(sil2.props["points"], env), s


def test_seed_and_situation_determine_the_silhouette(corpus) -> None:
    """I5, on the axis this stage owns."""
    for s, _env, _root, sil, roof in corpus[::11]:
        again, _ = generate(s)
        sil2 = next(n for n in again.children if n.kind == "silhouette")
        roof2 = next(n for n in again.children if n.kind == "roof")
        assert sil2.props["points"] == sil.props["points"]
        assert roof2.props["dormer_variant"] == roof.props["dormer_variant"]
        assert roof2.props["material"] == roof.props["material"]


def test_every_element_of_the_roofscape_carries_its_rule(corpus) -> None:
    """I4, over the sweep rather than over one example."""
    for s, _env, root, _sil, _roof in corpus[::5]:
        for node in root.children:
            if node.kind in ("storey",):
                continue
            assert node.trace, f"{s.year}: {node.id} has no trace"
            for entry in node.trace:
                assert entry.rule and entry.detail, node.id


# ---------------------------------------------------------------------------
# The comble is the residue of the rule: change the street, change the roof
# ---------------------------------------------------------------------------


def test_the_street_widens_the_comble_only_once_the_arc_arrives(corpus) -> None:
    """Alphand's radius depends on street width; the 45° diagonal does not.
    So on a deep parcel — deep enough that the parcel is not what caps the
    comble — a wider street buys a taller roof after 1884 and buys nothing
    before it. This is the sweep-level form of the claim that the roof is a
    consequence of the decree and not of taste.
    """
    by_year: dict[int, dict[int, dict[float, float]]] = {}
    allowances: dict[int, dict[float, float]] = {}
    for s, env, _root, sil, _roof in corpus:
        if s.parcel_depth != max(_DEPTHS):
            continue
        allowances.setdefault(s.year, {})[s.street_width] = float(env.ridge_height)
        # Measured over the EAVES. Since A8.5 the comble built over them is
        # what the rooms behind it need and carries nothing of this building's
        # budget, so the eaves-relative number is the clean one to compare
        # across widths — where before it was the cornice-relative one, the
        # eaves-relative height having absorbed the unbuilt facade headroom.
        #
        # **A15.1**: bucketed by how many storeys of chambres de bonne the
        # comble stands, because that is a PROGRAMME decision and the corpus
        # cycles the ground programme with its index. Comparing a two-storey
        # garret on one street against a one-storey garret on another would be
        # measuring the programme and calling it the street.
        rooms = len(solve_structure(s).comble_storeys)
        by_year.setdefault(s.year, {}).setdefault(rooms, {})[s.street_width] = (
            _ridge_above_eaves(sil)
        )

    for year, widths_to_allowance in allowances.items():
        if year >= 1884:
            continue
        # The diagonal itself, first: whatever a building then does under it,
        # the decree's own comble allowance is the same on every street.
        values = {round(v, 9) for v in widths_to_allowance.values()}
        assert len(values) == 1, (
            f"{year}: the 45° gabarit's own comble allowance moved with the street "
            f"({sorted(values)}) — the diagonal knows nothing about street width"
        )

    checked = 0
    for year, by_rooms in by_year.items():
        if year >= 1884:
            # The arc reads the street, so the comparison is across the whole
            # width range and needs no bucket: no post-1884 building trades
            # cornice height for garret (the gabarit already stands the rooms),
            # so there is no programme decision to confound it.
            heights = {w: h for bucket in by_rooms.values() for w, h in bucket.items()}
            widths = sorted(heights)
            lo, hi = heights[widths[0]], heights[widths[-1]]
            assert hi > lo + 0.5, (
                f"{year}: the arc's radius should follow the street, but the comble "
                f"went {lo:.3f} m -> {hi:.3f} m from a {widths[0]} m street to a "
                f"{widths[-1]} m one"
            )
            checked += 1
            continue
        for rooms, heights in by_rooms.items():
            widths = sorted(heights)
            if len(widths) < 2:
                continue
            lo, hi = heights[widths[0]], heights[widths[-1]]
            assert math.isclose(lo, hi, abs_tol=1e-6), (
                f"{year}: a 45° comble over {rooms} storey(s) of garret grew from "
                f"{lo:.3f} m to {hi:.3f} m when the street widened — the diagonal "
                "knows nothing about street width"
            )
            checked += 1
    assert checked > 0


def _ridge_above_eaves(sil) -> float:
    return max(y for _i, y in sil.props["points"]) - _eaves(sil)


def _ridge_above_the_cornice(sil, env) -> float:
    return max(y for _i, y in sil.props["points"]) - env.facade_height
