"""Tests for the regulatory model in :mod:`buildings.typologies.paris.reglement`.

The numbers asserted here are the ones the decrees actually state, so a
failure means the model has drifted from the law it claims to encode.
"""

from __future__ import annotations

import math

import pytest

from buildings.typologies.paris.reglement import (
    Era,
    RoofEnvelope,
    balcony_rule,
    compute_envelope,
    era_for_year,
    get_reglement,
)


# ---------------------------------------------------------------------------
# Height tables
# ---------------------------------------------------------------------------

class TestHeightTables:
    """Facade height as a function of street width, per decree."""

    @pytest.mark.parametrize("street,expected", [
        (5.0, 11.70),    # under 7.80 m — six toises
        (7.80, 11.70),   # boundary belongs to the lower step
        (9.00, 14.62),   # 7.80–9.75 m — sept toises trois pieds
        (12.0, 17.55),   # over 9.75 m — neuf toises
        (30.0, 17.55),   # the 20 m step does not exist before 1859
    ])
    def test_royal_1783_table(self, street, expected):
        assert get_reglement(Era.ROYAL).facade_height_limit(street) == expected

    @pytest.mark.parametrize("street,expected", [
        (5.0, 11.70),
        (9.00, 14.62),
        (12.0, 17.55),
        (20.0, 17.55),
        (25.0, 20.00),   # 1859 adds 20 m for the new wide percées
    ])
    def test_second_empire_1859_table(self, street, expected):
        assert get_reglement(Era.SECOND_EMPIRE).facade_height_limit(street) == expected

    @pytest.mark.parametrize("street,expected", [
        (5.0, 12.0),
        (9.00, 15.0),
        (12.0, 18.0),
        (25.0, 20.0),
    ])
    def test_alphand_1884_table(self, street, expected):
        """The 1884 decree raises every step."""
        assert get_reglement(Era.ALPHAND).facade_height_limit(street) == expected

    def test_1884_raises_every_step_above_1859(self):
        old = get_reglement(Era.SECOND_EMPIRE)
        new = get_reglement(Era.ALPHAND)
        for street in (5.0, 9.0, 12.0, 25.0):
            assert new.facade_height_limit(street) >= old.facade_height_limit(street)

    def test_compute_envelope_defaults_to_1859(self):
        assert compute_envelope(30.0).facade_height == 20.00
        assert compute_envelope(12.0).facade_height == 17.55
        assert compute_envelope(8.0).facade_height == 14.62
        assert compute_envelope(5.0).facade_height == 11.70

    def test_compute_envelope_takes_an_era(self):
        assert compute_envelope(12.0, Era.ALPHAND).facade_height == 18.0
        assert compute_envelope(12.0, "SECOND_EMPIRE").facade_height == 17.55


class TestEraLookup:
    @pytest.mark.parametrize("year,era", [
        (1800, Era.ROYAL),
        (1858, Era.ROYAL),
        (1859, Era.SECOND_EMPIRE),
        (1870, Era.SECOND_EMPIRE),
        (1884, Era.ALPHAND),
        (1901, Era.ALPHAND),
        (1902, Era.BONNIER),
        (1913, Era.BONNIER),
    ])
    def test_era_for_year(self, year, era):
        assert era_for_year(year) == era

    def test_get_reglement_accepts_name_or_enum(self):
        assert get_reglement("ALPHAND").era == Era.ALPHAND
        assert get_reglement("alphand").era == Era.ALPHAND
        assert get_reglement(Era.ALPHAND).era == Era.ALPHAND

    def test_unknown_era_lists_the_valid_ones(self):
        with pytest.raises(KeyError, match="SECOND_EMPIRE"):
            get_reglement("napoleon")


# ---------------------------------------------------------------------------
# Roof envelope geometry
# ---------------------------------------------------------------------------

class TestRoofEnvelope:

    def test_1884_ceiling_is_28_50(self):
        """20 m of facade plus an 8.50 m comble — the documented ceiling."""
        env = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0)
        assert env.facade_height == 20.0
        assert env.legal_ridge_height == pytest.approx(8.50, abs=1e-6)
        assert float(env.total_height) == pytest.approx(28.50, abs=1e-6)

    def test_pre_1884_comble_is_a_45_degree_diagonal(self):
        env = compute_envelope(30.0, Era.SECOND_EMPIRE, parcel_depth=20.0)
        assert env.roof_envelope == RoofEnvelope.DIAGONAL_45
        # Inscribed below a 45° diagonal: one metre in per metre up.
        for h in (0.5, 1.0, 2.5):
            assert float(env.setback_at(h)) == pytest.approx(h)
        lower, upper, _ = env.mansard_angles()
        assert lower == 45.0 and upper == 45.0

    def test_a_steeper_than_45_comble_is_illegal_before_1884(self):
        """A near-vertical face sits outside the diagonal envelope."""
        env = compute_envelope(30.0, Era.SECOND_EMPIRE, parcel_depth=20.0)
        h = 2.0
        near_vertical_inset = h / math.tan(math.radians(80))
        assert near_vertical_inset < float(env.setback_at(h))

    def test_1884_arc_starts_near_vertical_and_flattens(self):
        env = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0)
        assert env.roof_envelope == RoofEnvelope.CIRCULAR_ARC
        r = env.arc_radius
        # Near the eaves the arc gives away almost no depth...
        assert float(env.setback_at(0.1 * r)) < 0.1 * r
        # ...and it is horizontal by the time it reaches the apex.
        assert float(env.setback_at(r)) == pytest.approx(r)

    def test_1884_arc_permits_more_comble_than_the_diagonal(self):
        """This is the extra storey the 1884 decree was understood to allow."""
        old = compute_envelope(30.0, Era.SECOND_EMPIRE, parcel_depth=40.0)
        new = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0)
        assert new.legal_ridge_height > old.legal_ridge_height

    def test_1902_arc_runs_onto_a_45_degree_oblique(self):
        env = compute_envelope(30.0, Era.BONNIER, parcel_depth=60.0)
        assert env.roof_envelope == RoofEnvelope.EIGHTH_ARC_OBLIQUE
        h_break = env.arc_radius * math.sin(math.pi / 4)
        # Past the eighth of arc, height and inset advance together — 45°.
        a = float(env.setback_at(h_break + 1.0))
        b = float(env.setback_at(h_break + 2.0))
        assert b - a == pytest.approx(1.0)

    def test_1902_allows_a_taller_ridge_on_a_deep_parcel(self):
        """'Dans le cas d'une grande parcelle, la hauteur au centre peut
        donc être très élevée' — the opening Sauvage used at rue Vavin."""
        shallow = compute_envelope(30.0, Era.BONNIER, parcel_depth=8.0)
        deep = compute_envelope(30.0, Era.BONNIER, parcel_depth=60.0)
        assert deep.legal_ridge_height > shallow.legal_ridge_height

    def test_setback_is_monotonic_for_every_era(self):
        for era in Era:
            env = compute_envelope(30.0, era, parcel_depth=40.0)
            prev = -1.0
            for i in range(40):
                s = float(env.setback_at(i * 0.25))
                assert s >= prev - 1e-9
                prev = s

    def test_setback_and_max_height_are_inverse(self):
        for era in Era:
            env = compute_envelope(30.0, era, parcel_depth=40.0)
            for h in (0.5, 1.5, 3.0):
                if h > env.legal_ridge_height:
                    continue
                assert float(env.max_height_for_setback(float(env.setback_at(h)))) == pytest.approx(h, abs=1e-6)

    def test_shallow_parcel_limits_the_ridge(self):
        wide = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0)
        narrow = compute_envelope(30.0, Era.ALPHAND, parcel_depth=6.0)
        assert narrow.legal_ridge_height < wide.legal_ridge_height

    def test_roof_fill_and_max_ridge_only_lower_the_comble(self):
        full = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0)
        half = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0, roof_fill=0.5)
        capped = compute_envelope(30.0, Era.ALPHAND, parcel_depth=40.0, max_ridge=2.0)
        assert half.ridge_height == pytest.approx(full.ridge_height * 0.5)
        assert capped.ridge_height == 2.0
        # The legal ceiling is recorded whatever the builder chose to do.
        assert capped.legal_ridge_height == full.legal_ridge_height


class TestSlopeProfile:

    def test_profile_starts_at_the_eaves_and_reaches_the_ridge(self):
        for era in Era:
            env = compute_envelope(30.0, era, parcel_depth=20.0)
            pts = env.slope_profile()
            assert pts[0] == (0.0, 0.0)
            assert pts[-1][1] == pytest.approx(env.ridge_height, abs=1e-3)

    def test_profile_is_monotonic(self):
        for era in Era:
            pts = compute_envelope(30.0, era, parcel_depth=20.0).slope_profile()
            for (i0, h0), (i1, h1) in zip(pts, pts[1:]):
                assert i1 >= i0 - 1e-9
                assert h1 >= h0 - 1e-9

    def test_diagonal_profile_is_two_points_a_curve_is_many(self):
        assert len(compute_envelope(30.0, Era.SECOND_EMPIRE, parcel_depth=20.0).slope_profile()) == 2
        assert len(compute_envelope(30.0, Era.ALPHAND, parcel_depth=20.0).slope_profile()) > 5


# ---------------------------------------------------------------------------
# The 1823 balcony ordinance
# ---------------------------------------------------------------------------

class TestBalconyRule:

    def test_nothing_below_six_metres(self):
        rule = balcony_rule([0.0, 3.0, 5.9], Era.SECOND_EMPIRE)
        assert rule.continuous == []
        assert rule.individual == []

    def test_first_line_lands_on_the_noble_floor_with_an_entresol(self):
        # ground 4.0 + entresol 2.8 puts the noble floor at 6.8 m
        levels = [0.0, 4.0, 6.8, 10.5, 13.9, 17.0]
        rule = balcony_rule(levels, Era.SECOND_EMPIRE)
        assert rule.continuous[0] == 2

    def test_without_an_entresol_the_line_moves_up_a_storey(self):
        # ground 3.2 leaves the second storey at 3.2 m — below the limit
        levels = [0.0, 3.2, 6.15, 8.95, 11.65]
        rule = balcony_rule(levels, Era.SECOND_EMPIRE)
        assert rule.continuous[0] == 2

    def test_second_line_is_the_topmost_eligible_floor(self):
        levels = [0.0, 4.0, 6.8, 10.5, 13.9, 17.0]
        rule = balcony_rule(levels, Era.SECOND_EMPIRE)
        assert rule.continuous == [2, 5]

    def test_second_line_can_be_suppressed(self):
        levels = [0.0, 4.0, 6.8, 10.5, 13.9, 17.0]
        assert balcony_rule(levels, Era.SECOND_EMPIRE, second_line=False).continuous == [2]

    def test_individual_balconies_only_appear_late(self):
        levels = [0.0, 4.0, 6.8, 10.5, 13.9, 17.0]
        assert balcony_rule(levels, Era.SECOND_EMPIRE).individual == []
        assert balcony_rule(levels, Era.ALPHAND).individual == [3, 4]

    def test_projection_cap_is_eighty_centimetres(self):
        for era in Era:
            assert float(balcony_rule([0.0, 7.0], era).max_projection) == 0.80
