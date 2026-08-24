"""Tests for :mod:`buildings.typologies.paris.chronology` (and, since it owns
no separate test file per the stage brief, :mod:`buildings.typologies.paris.catalogue`
too).

The gate this stage answers to (G5) asks for five things: zero period-enum
branching, class lag producing genuinely different availability, prevalence
continuous vs. legality a step, windows always containing the year they were
returned for, and every source populated (INFERRED where the date was
guessed). Each gets its own test class below.
"""

from __future__ import annotations

import random
import subprocess
import sys
from pathlib import Path

import pytest

from buildings.quantity import Kind, scale_for_class
from buildings.rng import DecisionStream
from buildings.site import BuildingClass
from buildings.solver.fitting import SlotKind
from buildings.typologies.paris import catalogue, chronology
from buildings.typologies.paris.chronology import (
    ElementDate,
    Variant,
    available,
    legal,
    prevalence,
    raised_comble,
    variants_for,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Variant construction
# ---------------------------------------------------------------------------


class TestVariant:
    def test_requires_non_blank_source(self):
        with pytest.raises(ValueError):
            Variant(
                feature="ironwork",
                name="x",
                earliest=1820,
                peak_from=1830,
                peak_to=1840,
                latest=1850,
                source="   ",
            )

    def test_requires_ordered_window(self):
        with pytest.raises(ValueError):
            Variant(
                feature="ironwork",
                name="x",
                earliest=1850,
                peak_from=1830,  # before earliest -- invalid
                peak_to=1840,
                latest=1860,
                source="test",
            )

    def test_rejects_a_ramp_too_short_to_be_a_fashion(self):
        """A two-year rise is a step function wearing a ramp's clothes: at
        the whole years every caller samples at, it jumps 0.5. The Variant
        constructor refuses it rather than leaving it to a reviewer to
        notice."""
        with pytest.raises(ValueError, match="ramps must be at least"):
            Variant(
                feature="ironwork",
                name="cliff",
                earliest=1895,
                peak_from=1897,  # 2-year rise
                peak_to=1902,
                latest=1930,
                source="test",
            )

    def test_rejects_a_fall_too_short_to_be_a_fashion(self):
        with pytest.raises(ValueError, match="ramps must be at least"):
            Variant(
                feature="ironwork",
                name="cliff",
                earliest=1850,
                peak_from=1870,
                peak_to=1900,
                latest=1903,  # 3-year fall
                source="test",
            )

    def test_every_catalogued_variant_satisfies_the_ramp_floor(self):
        for feature in chronology.FEATURES:
            for v in variants_for(feature):
                assert v.peak_from - v.earliest >= chronology.MIN_RAMP_YEARS
                assert v.latest - v.peak_to >= chronology.MIN_RAMP_YEARS

    def test_class_lag_defaults_empty_and_is_immutable(self):
        v = Variant(
            feature="ironwork",
            name="x",
            earliest=1820,
            peak_from=1835,
            peak_to=1845,
            latest=1860,
            source="test",
        )
        assert dict(v.class_lag) == {}
        with pytest.raises(TypeError):
            v.class_lag["oops"] = 1  # MappingProxyType is read-only


# ---------------------------------------------------------------------------
# The catalogue's five families
# ---------------------------------------------------------------------------


class TestCatalogueContents:
    @pytest.mark.parametrize("feature", list(chronology.FEATURES))
    def test_every_feature_has_variants(self, feature):
        assert len(variants_for(feature)) >= 2

    def test_no_unknown_feature_keys(self):
        assert set(chronology.FEATURES) == {
            "ironwork",
            "socle",
            "keystone",
            "roof",
            "shopfront",
        }

    def test_every_source_is_non_blank(self):
        for feature in chronology.FEATURES:
            for v in variants_for(feature):
                assert v.source.strip(), f"{feature}/{v.name} has a blank source"

    def test_inferred_dates_are_marked(self):
        """Every variant window below decade granularity is a guess; BRIEF.md
        asks that guesses be marked. Assert every catalogued variant's source
        says so somewhere."""
        for feature in chronology.FEATURES:
            for v in variants_for(feature):
                assert "INFERRED" in v.source, (
                    f"{feature}/{v.name}: source does not mark inferred dates: "
                    f"{v.source!r}"
                )


# ---------------------------------------------------------------------------
# A2.5 — this catalogue dates fashion. It does not date the decree.
# ---------------------------------------------------------------------------


class TestTheCatalogueDatesFashionOnly:
    """The `roof` family used to name comble geometries, and geometry is not a
    fashion: it is a step function on a decree date, it carries no class lag,
    and `reglement.py` owns it. Two chronologies were being forced through one
    mechanism, which is the failure this module's whole docstring is about —
    one level down from where it was expecting it.

    The mechanical guard lives in ``terminate`` (it is the consumer that has to
    hold the two apart); these assert the catalogue's own side of the bargain,
    so that a rename here fails here.
    """

    def test_no_roof_variant_names_a_comble_geometry(self):
        from buildings.typologies.paris.terminate import _geometry_claimed_by

        for v in variants_for("roof"):
            claimed = _geometry_claimed_by(v.name)
            assert claimed == frozenset(), (
                f"roof/{v.name} spells the comble geometry "
                f"{sorted(e.value for e in claimed)} into a fashion variant. Geometry "
                "arrives on the decree date and does not lag by class; this catalogue "
                "may date the dormers, the cresting and the covering, and nothing else."
            )

    def test_no_variant_of_any_family_names_a_comble_geometry(self):
        """Not just the roof family: a `socle` or `keystone` variant would be
        just as wrong, and just as easy to write."""
        from buildings.typologies.paris.terminate import _geometry_claimed_by

        for feature in chronology.FEATURES:
            for v in variants_for(feature):
                assert _geometry_claimed_by(v.name) == frozenset(), f"{feature}/{v.name}"

    def test_the_roof_family_still_covers_the_briefs_three_stages(self):
        """Renaming must not have quietly dropped one of the brief's steps.

        BRIEF.md's roof sentence has three dormer stages and a material, and
        after the rename all four are still there — plainer dormers, pedimented
        dormers, varied dormers with cresting, and zinc.
        """
        assert {v.name for v in variants_for("roof")} == {
            "small_plain_dormers",
            "pedimented_dormers",
            "varied_dormers_iron_cresting",
            "zinc_roofing",
        }

    def test_the_pedimented_dormer_outlives_the_envelope_that_carried_it(self):
        """The retention the brief calls the common case.

        The 1884 decree replaced the 45° comble with an arc. It said nothing
        about lucarnes, and this catalogue must not pretend it did: pedimented
        dormers are still available — to a grand building on schedule, and to a
        modest one well past that — after the geometry under them has changed.
        """
        for klass in BuildingClass:
            names = {v.name for v, _w in available("roof", 1890, klass)}
            assert "pedimented_dormers" in names, klass

        modest = {v.name for v, _w in available("roof", 1900, BuildingClass.MODEST)}
        assert "pedimented_dormers" in modest, (
            "a modest builder should still be fitting the old lucarne in 1900 — that "
            "is the straggler, and it is the whole reason the axes are separate"
        )


# ---------------------------------------------------------------------------
# Gate G5.3 — prevalence is continuous, legality is a step
# ---------------------------------------------------------------------------


class TestPrevalenceIsContinuous:
    @pytest.mark.parametrize("feature", list(chronology.FEATURES))
    def test_no_jump_larger_than_the_sampling_step(self, feature):
        """Sampled finely (0.1 yr) rather than at whole years, so a variant
        with a genuinely short ramp (a handful of years) does not read as a
        false discontinuity -- only an actual jump in the *function*, not
        the coarseness of an integer year, should fail this."""
        step = 0.1
        for v in variants_for(feature):
            for klass in BuildingClass:
                prev = None
                year = 1800.0
                while year <= 1930.0:
                    cur = prevalence(v, year, klass)
                    assert 0.0 <= cur <= 1.0
                    if prev is not None:
                        assert abs(cur - prev) <= 0.05, (
                            f"{feature}/{v.name}/{klass}: jump {prev}->{cur} "
                            f"at year {year}"
                        )
                    prev = cur
                    year += step

    @pytest.mark.parametrize("feature", list(chronology.FEATURES))
    def test_no_whole_year_jump_beyond_the_ramp_floor(self, feature):
        """The bound that actually matters, because whole years are what
        callers sample at. A linear ramp of length L must step by 1/L, so
        the only way to bound the step is to bound L from below -- which is
        what MIN_RAMP_YEARS does. Asserting the exact consequence here
        makes the number falsifiable instead of decorative."""
        bound = 1.0 / chronology.MIN_RAMP_YEARS
        for v in variants_for(feature):
            for klass in BuildingClass:
                previous = None
                for year in range(1700, 2001):
                    current = prevalence(v, year, klass)
                    if previous is not None:
                        assert abs(current - previous) <= bound + 1e-9, (
                            f"{feature}/{v.name}/{klass}: {previous}->{current} "
                            f"across year {year}"
                        )
                    previous = current

    @pytest.mark.parametrize("feature", list(chronology.FEATURES))
    def test_curve_actually_rises_and_falls_for_every_class(self, feature):
        """A flat or constant curve would be a step in disguise.

        Sampled over each *class's own* lagged window, not over a fixed
        calendar span: a curve whose window the sample never reaches looks
        flat without being flat, and that sampling artifact should not be
        allowed to either pass or fail this."""
        for v in variants_for(feature):
            for klass in BuildingClass:
                earliest, _pf, _pt, latest = v.window_for(klass)
                values = [
                    prevalence(v, year, klass)
                    for year in range(earliest - 5, latest + 6)
                ]
                assert min(values) == 0.0
                assert max(values) == 1.0
                # genuinely a ramp, not a cliff: some intermediate value
                # strictly between the floor and the ceiling must occur.
                assert any(0.0 < x < 1.0 for x in values)

    def test_only_one_documented_variant_is_out_of_reach_in_the_working_range(self):
        """Adoption lag can legitimately push a late fashion past the end of
        the modelled century for the bottom of the class ladder -- that is
        the brief's "ten to twenty years later, if ever". What must not
        happen is that being true of a whole swathe of the catalogue
        because a lag number was invented to make it so. This pins the
        exception list: exactly one (variant, class) pair never appears
        between 1820 and 1910, and it is there by arithmetic (1893 + the
        brief's own 20-year upper bound = 1913), not by fiat."""
        unreachable = {
            (v.name, klass.name)
            for feature in chronology.FEATURES
            for v in variants_for(feature)
            for klass in BuildingClass
            if max(prevalence(v, year, klass) for year in range(1820, 1911)) == 0.0
        }
        assert unreachable == {("whiplash_art_nouveau", "MODEST")}
        v = next(
            x for x in variants_for("ironwork") if x.name == "whiplash_art_nouveau"
        )
        assert v.window_for(BuildingClass.MODEST)[0] == 1913
        assert v.class_lag[BuildingClass.MODEST] <= 20  # the brief's own bracket

    def test_plateau_holds_at_exactly_one(self):
        v = variants_for("ironwork")[1]  # haussmannian_scrollwork
        for year in range(v.peak_from, v.peak_to + 1):
            assert prevalence(v, year, BuildingClass.GRAND) == 1.0

    def test_zero_outside_window(self):
        v = variants_for("ironwork")[0]
        assert prevalence(v, v.earliest - 50, BuildingClass.GRAND) == 0.0
        assert prevalence(v, v.latest + 50, BuildingClass.GRAND) == 0.0


class TestLegalityIsAStep:
    def test_oriels_illegal_in_1881_and_legal_in_1882(self):
        """BRIEF.md states this one outright: 'Oriels are illegal in 1881
        and legal in 1882.' The décret is du 22 juillet 1882, and
        reglement.py's own source list gives the same date.

        An earlier version of this module read the year off
        `reglement.era_for_year`, whose four-way *envelope* split does not
        begin `Era.ALPHAND` until the 1884 height-table decree, and so
        answered 1884 -- and an earlier version of this test asserted that
        1884 behaviour, which turned a violated source into a green suite.
        The switch year now lives on the switch, which is the same fix this
        whole module applies one level up: put the date on the thing it
        belongs to instead of forcing two chronologies through one enum."""
        assert legal("oriel", 1881) is False
        assert legal("oriel", 1882) is True

    def test_oriel_legality_has_exactly_one_transition(self):
        """A step, not a ramp and not a flicker: one change of value across
        the whole modelled span, at the decree year."""
        transitions = [
            year for year in range(1800, 1921) if legal("oriel", year) != legal("oriel", year - 1)
        ]
        assert transitions == [1882]

    def test_switch_dates_agree_with_reglement_where_it_can_have_an_opinion(self):
        """The guard that stops the decree table and the ported regulatory
        core drifting apart. It runs at import; this re-runs it explicitly
        so the assertion is visible in the suite rather than implicit in a
        successful import."""
        chronology._check_switches_against_reglement()

    def test_oriels_step_is_binary_not_continuous(self):
        # every year returns exactly True or False -- no in-between value is
        # even representable, which is the point.
        for year in range(1860, 1910):
            result = legal("oriel", year)
            assert result in (True, False)

    def test_unrestricted_feature_is_always_legal(self):
        """The five fashion families have no legal gate at all -- only
        prevalence governs them."""
        for feature in chronology.FEATURES:
            for year in (1820, 1860, 1884, 1902):
                assert legal(feature, year) is True

    def test_individual_balconies_step(self):
        assert legal("balcony_individual", 1883) is False
        assert legal("balcony_individual", 1884) is True


# ---------------------------------------------------------------------------
# Gate G5.2 — class lag is real
# ---------------------------------------------------------------------------


class TestClassLag:
    def test_grand_and_modest_differ_in_1885(self):
        year = 1885
        for feature in chronology.FEATURES:
            grand = available(feature, year, BuildingClass.GRAND)
            modest = available(feature, year, BuildingClass.MODEST)
            grand_names = {v.name for v, _ in grand}
            modest_names = {v.name for v, _ in modest}
            grand_weights = {v.name: w for v, w in grand}
            modest_weights = {v.name: w for v, w in modest}
            same_names = grand_names == modest_names
            same_weights = same_names and all(
                abs(grand_weights[n] - modest_weights[n]) < 1e-9 for n in grand_names
            )
            assert not (same_names and same_weights), (
                f"{feature} in {year}: GRAND and MODEST are identical "
                f"({grand_names}, {grand_weights}) -- class lag not wired up"
            )

    def test_no_lag_exceeds_the_only_bracket_the_source_gives(self):
        """BRIEF.md's one quantitative statement about adoption lag is 'ten
        to twenty years later, if ever'. Every lag in the catalogue must sit
        inside that bracket for the class it slows the most. A larger number
        would be inventing evidence -- and a 60-year lag, which an earlier
        draft used to keep Art Nouveau off modest streets, is a conclusion
        smuggled in as a parameter."""
        for feature in chronology.FEATURES:
            for v in variants_for(feature):
                for klass, lag in v.class_lag.items():
                    assert 0 <= lag <= 20, (feature, v.name, klass, lag)
                assert v.class_lag[BuildingClass.GRAND] == 0
                # monotonic down the ladder: grander adopts sooner
                assert (
                    v.class_lag[BuildingClass.GRAND]
                    <= v.class_lag[BuildingClass.COMFORTABLE]
                    <= v.class_lag[BuildingClass.ORDINARY]
                    <= v.class_lag[BuildingClass.MODEST]
                )

    def test_modest_lags_behind_grand_on_a_specific_variant(self):
        # whiplash art nouveau: earliest 1895 for GRAND. In 1897 GRAND has
        # already started ramping; MODEST (elite lag, big) has not arrived.
        v = next(
            x for x in variants_for("ironwork") if x.name == "whiplash_art_nouveau"
        )
        year = 1897
        assert prevalence(v, year, BuildingClass.GRAND) > 0.0
        assert prevalence(v, year, BuildingClass.MODEST) == 0.0

    def test_retention_modest_keeps_it_after_grand_has_moved_on(self):
        # scrollwork's GRAND window ends at `latest`; MODEST's window (lag
        # applied to both ends, not just the start) extends past it -- the
        # brief's "retains superseded forms long after they have gone from
        # the boulevards".
        v = next(
            x for x in variants_for("ironwork") if x.name == "haussmannian_scrollwork"
        )
        year = v.latest + 1  # strictly past GRAND's own window
        assert prevalence(v, year, BuildingClass.GRAND) == 0.0
        assert prevalence(v, year, BuildingClass.MODEST) > 0.0


# ---------------------------------------------------------------------------
# Gate G5.4 — windows always contain the year they were returned for
# ---------------------------------------------------------------------------


class TestAvailableWindowProperty:
    def test_returned_variants_and_weights_are_valid(self):
        rng = random.Random(12345)
        for _ in range(500):
            feature = rng.choice(chronology.FEATURES)
            year = rng.randint(1800, 1930)
            klass = rng.choice(list(BuildingClass))
            for v, weight in available(feature, year, klass):
                earliest, _pf, _pt, latest = v.window_for(klass)
                assert earliest <= year <= latest, (
                    f"{feature}/{v.name}/{klass}/{year}: window "
                    f"[{earliest},{latest}] does not contain {year}"
                )
                assert 0.0 <= weight <= 1.0

    def test_no_variants_far_outside_any_window(self):
        for feature in chronology.FEATURES:
            assert available(feature, 1000, BuildingClass.GRAND) == []

    def test_every_returned_weight_is_strictly_positive(self):
        """Membership is `weight > 0`, not the closed window. The closed
        window admits the two endpoint years where the ramp is exactly 0,
        and a zero-weight member is a variant nobody built that year."""
        for feature in chronology.FEATURES:
            for klass in BuildingClass:
                for year in range(1750, 1961):
                    for v, weight in available(feature, year, klass):
                        assert weight > 0.0, (feature, v.name, klass, year)

    def test_result_can_be_fed_straight_to_decisionstream_choice(self):
        """The docstring invites callers to do exactly this, so the suite
        has to actually do it. `random.choices` raises ValueError on a
        weight vector summing to zero, which is what a list of endpoint
        variants used to produce."""
        stream = DecisionStream(20260820)
        for feature in chronology.FEATURES:
            for klass in BuildingClass:
                for year in range(1820, 1911):
                    options = available(feature, year, klass)
                    chosen = stream.choice(
                        f"{feature}/{klass.name}/{year}",
                        [v for v, _ in options],
                        [w for _, w in options],
                    )
                    assert chosen in [v for v, _ in options]

    def test_catalogue_covers_every_class_across_the_working_range(self):
        """Class lag shifts both ends of a window later, which is what
        models retention -- but it also means a lagged class can fall off
        the *front* of the catalogue. It must not: a modest building of
        1825 has old-fashioned ironwork, not an absence of ironwork. The
        open-front anchor variant in each family is what pays for this."""
        empty = [
            (feature, klass.name, year)
            for feature in chronology.FEATURES
            for klass in BuildingClass
            for year in range(1820, 1911)
            if not available(feature, year, klass)
        ]
        assert empty == []

    def test_a_modest_1825_facade_gets_the_superseded_form_not_nothing(self):
        for feature in chronology.FEATURES:
            options = available(feature, 1825, BuildingClass.MODEST)
            assert options, feature
            best = options[0][0]
            assert best is variants_for(feature)[0], (
                f"{feature}: a modest 1825 building should be showing the "
                f"family's oldest form, got {best.name}"
            )


# ---------------------------------------------------------------------------
# Gate G5.6 — observation date vs. construction date
# ---------------------------------------------------------------------------


class TestObservationDate:
    def test_element_date_carries_two_years(self):
        d = ElementDate(building_year=1860, observed=1898)
        assert d.building_year == 1860
        assert d.observed == 1898
        assert d.altered is True

    def test_unaltered_element_is_not_altered(self):
        d = ElementDate(building_year=1860, observed=1860)
        assert d.altered is False

    def test_raised_comble_names_the_rivoli_mechanism(self):
        d = raised_comble(building_year=1870, roof_observed_year=1888)
        assert d.altered is True
        assert "raised" in d.reason.lower()

    def test_1860_bones_1885_roof_1898_shopfront(self):
        """The brief's own example: one facade, three genuinely different
        observation dates, each pulling a different available() answer than
        the building's bare construction year would."""
        building_year = 1860
        roof_date = raised_comble(building_year, 1885)
        shopfront_date = ElementDate(building_year=building_year, observed=1898)

        bones_roof = available("roof", building_year, BuildingClass.GRAND)
        actual_roof = available("roof", roof_date.observed, BuildingClass.GRAND)
        assert {v.name for v, _ in bones_roof} != {v.name for v, _ in actual_roof}

        bones_shopfront = available("shopfront", building_year, BuildingClass.GRAND)
        actual_shopfront = available(
            "shopfront", shopfront_date.observed, BuildingClass.GRAND
        )
        assert {v.name for v, _ in bones_shopfront} != {
            v.name for v, _ in actual_shopfront
        }


# ---------------------------------------------------------------------------
# Gate G5.1 — zero period-enum branching (the AST-scan harness)
# ---------------------------------------------------------------------------


class TestNoPeriodBranching:
    def test_harness_passes_clean(self):
        script = REPO_ROOT / "dev" / "harness" / "check_no_period_branching.py"
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# catalogue.py — absolute vs. proportional
# ---------------------------------------------------------------------------


class TestCatalogueAbsoluteProportional:
    def test_carriage_entrance_is_absolute(self):
        m = catalogue.door_carriage_entrance()
        assert m.minimum.kind is Kind.ABSOLUTE
        assert m.preferred.kind is Kind.ABSOLUTE
        assert m.maximum.kind is Kind.ABSOLUTE

    def test_carriage_entrance_does_not_change_under_scale_for_class(self):
        m = catalogue.door_carriage_entrance()
        widths = {klass: m.to_slot_spec(klass).preferred for klass in BuildingClass}
        assert len(set(widths.values())) == 1, widths

    def test_pedestrian_door_does_not_change_under_scale_for_class(self):
        m = catalogue.door_pedestrian()
        widths = {klass: m.to_slot_spec(klass).preferred for klass in BuildingClass}
        assert len(set(widths.values())) == 1, widths

    def test_bay_width_does_change_under_scale_for_class(self):
        m = catalogue.standard_bay()
        widths = {klass: m.to_slot_spec(klass).preferred for klass in BuildingClass}
        assert len(set(widths.values())) == len(BuildingClass), widths
        assert (
            widths[BuildingClass.MODEST]
            < widths[BuildingClass.ORDINARY]
            < widths[BuildingClass.GRAND]
        )

    def test_carriage_door_slot_is_fixed_and_rigid(self):
        spec = catalogue.door_carriage_entrance().to_slot_spec(BuildingClass.GRAND)
        assert spec.kind is SlotKind.FIXED
        assert spec.rigid is True

    def test_storey_minimum_is_regulatory_and_matches_reglement(self):
        from buildings.typologies.paris import reglement

        q = catalogue.storey_minimum_height(1870)
        assert q.kind is Kind.REGULATORY
        assert float(q) == reglement.get_reglement(
            reglement.era_for_year(1870)
        ).min_floor_height

    def test_storey_minimum_is_260_from_1859(self):
        assert float(catalogue.storey_minimum_height(1870)) == 2.60
        assert float(catalogue.storey_minimum_height(1830)) == 0.0

    def test_absolute_quantities_reject_scalar_scaling(self):
        """A1.1: scaling a rigid quantity directly (bypassing scale_for_class)
        must raise -- exercised here on the catalogue's own absolute figures,
        since that is exactly the "someone will eventually scale a doorway"
        failure the contract calls out by name."""
        with pytest.raises(TypeError):
            catalogue.door_carriage_entrance().preferred * 1.35

    def test_standard_bay_is_repeating_kind_for_the_solver(self):
        spec = catalogue.standard_bay().to_slot_spec(BuildingClass.ORDINARY)
        assert spec.kind is SlotKind.REPEATING

    def test_bounds_bracket_preferred_for_every_class(self):
        modules = [
            catalogue.facade_end(),
            catalogue.pier_filler(),
            catalogue.opening_window(),
            catalogue.standard_bay(),
            catalogue.door_pedestrian(),
            catalogue.door_carriage_entrance(),
            catalogue.narrow_special_half_bay(),
            catalogue.narrow_special_blind_panel(),
            catalogue.narrow_special_oeil_de_boeuf(),
        ]
        for m in modules:
            for klass in BuildingClass:
                spec = m.to_slot_spec(klass)
                assert spec.minimum <= spec.preferred <= spec.maximum, (m.name, klass)


# ===========================================================================
# A9.2 / A9.4 — what Daly 1864 calibrated, and what it deliberately did not
# ===========================================================================
#
# The measurement pass over César Daly's 77 plates
# (`dev/reference/daly_measurements.json`) sorted every quantity it could read
# into SOURCED, WEAK and INSUFFICIENT. A9.4 permits exactly eleven of them to
# stop being INFERRED. The tests below hold the catalogue to both halves of
# that: the promoted figures must carry a citation naming the source, the
# plate and whether the reading was printed or scale-bar; and the quantities
# the corpus could not carry must still say INFERRED, because the marker is
# the only thing telling a later stage which numbers are still open.


class TestDalyCalibration:
    def test_the_carriage_door_is_the_printed_dimension(self):
        """**A9.2.** Daly measures seven carriage doors across the two top
        classes — Première 2.410 / 2.534 / **2.600 printed** / 2.619, median
        2.567; Deuxième 2.570 / 2.575 / 2.672, median 2.575. The two medians
        agree to 0.4 %, which is the finding: a carriage door does not scale
        with money because a carriage does not.

        The clear width is the printed 2.600 m and not the 3.00 m INFERRED
        figure it replaces, which was 15 % over every door in the corpus.
        """
        spec = catalogue.door_carriage_entrance()
        assert float(spec.preferred) == pytest.approx(2.60)
        why = spec.preferred.why
        assert "SOURCED" in why
        assert "Daly 1864" in why
        assert "Champs-Élysées" in why
        assert catalogue.PRINTED in why
        # And the whole band sits inside what Daly measured, 2.41-2.672 m.
        assert float(spec.minimum) == pytest.approx(2.41)
        assert 2.60 <= float(spec.maximum) <= 2.75

    def test_the_carriage_door_is_still_absolute_after_being_sourced(self):
        """Being measured did not make it negotiable. A9.2's instruction is
        "SOURCED at 2.60 m ... keep it ABSOLUTE", and the reason the two go
        together is the corpus itself: the figure is the same in both classes
        that have the door at all."""
        spec = catalogue.door_carriage_entrance()
        assert all(
            b.kind is Kind.ABSOLUTE for b in (spec.minimum, spec.preferred, spec.maximum)
        )
        widths = {k: spec.to_slot_spec(k).preferred for k in BuildingClass}
        assert len(set(widths.values())) == 1, widths

    def test_the_pedestrian_door_is_sourced_by_its_own_door_type(self):
        """The apparent door-width class ladder (2.57 / 1.78 / 1.36 m) is a
        ladder of *which door*, not of how big a door is. So each door type
        carries its own measured band, and the pedestrian one is Daly's eight
        Deuxième Classe portes piétonnes: 1.61-1.91 m, median 1.75 m, with
        printed callouts at 1.760 and 1.630."""
        spec = catalogue.door_pedestrian()
        assert float(spec.preferred) == pytest.approx(1.75)
        assert 1.61 <= float(spec.minimum) <= 1.62
        assert 1.90 <= float(spec.maximum) <= 1.92
        for bound in (spec.minimum, spec.preferred, spec.maximum):
            assert bound.kind is Kind.ABSOLUTE
            assert "SOURCED" in bound.why and "Daly 1864" in bound.why

    def test_the_window_splits_into_an_absolute_width_and_a_proportional_height(self):
        """**The project's central distinction, demonstrated from a period
        source.** One aperture, two kinds of number:

        * WIDTH — 1.04-1.30 m across all sixteen buildings, class medians
          1.139 / 1.235 / 1.070, which is *non-monotonic*: there is no ladder
          in it at all. ABSOLUTE.
        * HEIGHT at the noble floor — 2.923 / 2.236 / 2.085 m, monotonic, a
          1.40× spread. PROPORTIONAL.

        Asserted as kinds and as behaviour under ``scale_for_class``, not as
        two numbers, because it is the kinds that carry the finding.
        """
        width = catalogue.opening_window()
        for bound in (width.minimum, width.preferred, width.maximum):
            assert bound.kind is Kind.ABSOLUTE, bound
            assert "SOURCED" in bound.why and "Daly 1864" in bound.why
        widths = {k: width.to_slot_spec(k).preferred for k in BuildingClass}
        assert len(set(widths.values())) == 1, widths
        assert 1.04 <= float(width.preferred) <= 1.30

        height = catalogue.opening_height_at_the_nobile()
        assert height.kind is Kind.PROPORTIONAL
        ladder = [
            float(scale_for_class(height, k))
            for k in (
                BuildingClass.MODEST,
                BuildingClass.ORDINARY,
                BuildingClass.COMFORTABLE,
                BuildingClass.GRAND,
            )
        ]
        assert ladder == sorted(ladder) and len(set(ladder)) == 4, ladder
        # Daly's own measured span at the noble floor, 2.085-2.923 m, is what
        # the four classes have to be bracketed by. The ORDERING is sourced;
        # the values are not, which is why this is a containment and not an
        # equality.
        assert 2.0 <= ladder[0] and ladder[-1] <= 3.3, ladder

    def test_the_floor_structure_over_an_opening_is_printed_twice(self):
        """Daly prints 0.30 m on two buildings in two classes: the repeated
        '30' on the 125 avenue des Champs-Élysées storey ladder and the
        '0.300' closing the window chain at 9 rue du Conservatoire. Two
        printed callouts on one number is the signature of an ABSOLUTE."""
        q = catalogue.lintel_bearing_depth()
        assert float(q) == pytest.approx(0.30)
        assert q.kind is Kind.ABSOLUTE
        assert "SOURCED" in q.why and catalogue.PRINTED in q.why

    def test_every_sourced_citation_names_source_plate_and_kind_of_reading(self):
        """A9.4's own requirement about the citations themselves: each names
        Daly 1864, the plate or building it came from, and whether the figure
        was printed or scale-bar measured — the latter carrying the ±10 % the
        corpus established by measuring 26 rue Bergère twice and by finding a
        2.99 m scale-bar reading against a printed 2.600 m."""
        promoted = [
            catalogue.door_carriage_entrance().minimum,
            catalogue.door_carriage_entrance().preferred,
            catalogue.door_carriage_entrance().maximum,
            catalogue.door_pedestrian().minimum,
            catalogue.door_pedestrian().preferred,
            catalogue.door_pedestrian().maximum,
            catalogue.opening_window().minimum,
            catalogue.opening_window().preferred,
            catalogue.opening_window().maximum,
            catalogue.lintel_bearing_depth(),
        ]
        for q in promoted:
            assert "SOURCED" in q.why, q
            assert catalogue.DALY_1864 in q.why, q
            assert (catalogue.PRINTED in q.why) or (catalogue.SCALE_BAR in q.why), q

    def test_the_quantities_daly_could_not_carry_are_still_inferred(self):
        """**The half of A9.4 that is easiest to get wrong.** The measurement
        pass marks six quantities INSUFFICIENT — comble share, cornice band
        depth, upper-storey opening aspect, entresol opening aspect, balcony
        height above pavement outside Deuxième, and bay pitch as a function of
        class — and recommending a thin number as sourced is the one failure
        mode that would make the whole exercise counterproductive.

        These are the catalogue's figures in that territory. They must still
        say INFERRED, and this test exists so that a later pass adding
        citations has to come back and read the source register first.
        """
        still_open = [
            catalogue.standard_bay().preferred,       # bay pitch: non-monotonic by class
            catalogue.pier_filler().preferred,        # no plate measures a trumeau
            catalogue.facade_end().preferred,         # nor an edge pier
            catalogue.sill_lean_height(),
            catalogue.shop_threshold_height(),
            catalogue.shopfront_fascia_depth(),
            catalogue.carriage_clear_height(),
            catalogue.carriage_jamb_width(),
        ]
        for q in still_open:
            assert "INFERRED" in q.why, q
            assert "SOURCED" not in q.why, q


class TestTheCarriageEntranceIsAnEntitlement:
    """A9.2. The class signal in a Paris entrance is *whether the building
    gets a carriage arch*, not how wide the arch is.

    Daly: Première 4 of 4 buildings have one, Deuxième 3 of 10, Troisième
    0 of 2. Ordering only is contractual — the exact membership is this
    typology's four classes read onto Daly's three.
    """

    def test_entitlement_never_falls_as_class_rises(self):
        ladder = [
            BuildingClass.MODEST,
            BuildingClass.ORDINARY,
            BuildingClass.COMFORTABLE,
            BuildingClass.GRAND,
        ]
        for street in (12.0, 16.0, 20.0, 30.0):
            got = [
                catalogue.entrance_for(k, street).kind == catalogue.ENTRANCE_CARRIAGE
                for k in ladder
            ]
            assert got == sorted(got), (street, got)

    def test_the_bottom_of_the_ladder_never_gets_one_and_the_top_always_does(self):
        for street in (12.0, 20.0, 30.0):
            assert (
                catalogue.entrance_for(BuildingClass.MODEST, street).kind
                == catalogue.ENTRANCE_PEDESTRIAN
            )
            assert (
                catalogue.entrance_for(BuildingClass.GRAND, street).kind
                == catalogue.ENTRANCE_CARRIAGE
            )

    def test_a_street_too_narrow_for_a_carriage_refuses_one_to_every_class(self):
        """The other half of the decision, and it is not about money: a
        carriage has to draw out of the traffic and turn in off the roadway."""
        for k in BuildingClass:
            assert (
                catalogue.entrance_for(k, 8.0).kind == catalogue.ENTRANCE_PEDESTRIAN
            )

    def test_both_doors_take_less_frontage_than_a_bay_may_be(self):
        """**D6, closed.** The entrance is a FIXED slot standing in the bay
        run for the full height of the facade, so a slot wider than a bay may
        be is a window the building does not get on every floor. The carriage
        slot was 3.00 m clear plus two 0.40 m jambs = 3.80 m, against the
        3.40 m maximum ``structure`` states for a bay. At Daly's printed
        2.60 m it is exactly 3.40 m and fits."""
        from buildings.typologies.paris import structure

        assert float(catalogue.carriage_slot_width()) <= float(structure._BAY_PITCH_MAX) + 1e-9
        assert float(catalogue.pedestrian_slot_width()) <= float(structure._BAY_PITCH_MAX) + 1e-9
