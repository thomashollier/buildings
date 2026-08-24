"""Differential test: ported reglement vs. original haussmann implementation.

This test imports the old reglement directly from ../haussmann and asserts
that the ported module produces bit-for-bit identical results across a sweep
of street widths and years. It is a regression test against the known-good
reference implementation.

A1.7: a missing oracle is a HARD FAILURE, not a silent skip. The module used
to guard the import with `pytest.importorskip`, so if `../haussmann` were
ever moved or renamed, all 417 oracle tests below would skip and the suite
would still report green -- precisely the vacuous-gate condition G2 exists to
prevent (a gate that always "passes" because it never actually ran). Set
`HAUSSMANN_ORACLE_OPTIONAL=1` to opt back into the old skip-if-missing
behaviour (e.g. for a checkout that deliberately doesn't have the sibling
repo and isn't trying to satisfy G2).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add the haussmann repo to sys.path for importing the old module
_HAUSSMANN_ROOT = Path(__file__).parent.parent.parent.parent / "haussmann"
if _HAUSSMANN_ROOT.exists():
    sys.path.insert(0, str(_HAUSSMANN_ROOT))

_OPTIONAL = os.environ.get("HAUSSMANN_ORACLE_OPTIONAL") == "1"

if _OPTIONAL:
    # Explicit opt-out: fall back to the old skip-if-missing behaviour.
    old_reglement = pytest.importorskip(
        "core.reglement",
        minversion=None,
        reason="haussmann reference repo not available at ../haussmann "
        "(HAUSSMANN_ORACLE_OPTIONAL=1 set)",
    )
else:
    # Default: a missing oracle is a hard failure, not a silent skip (A1.7).
    try:
        import core.reglement as old_reglement
    except ImportError as exc:
        raise AssertionError(
            "haussmann reference repo not found at "
            f"{_HAUSSMANN_ROOT} -- the oracle differential test cannot run. "
            "This is a HARD FAILURE, not a skip: a missing oracle must not "
            "let the suite report green while 417 oracle tests silently "
            "never ran (the vacuous-gate condition G2 exists to prevent "
            "this). If you deliberately do not have the sibling ../haussmann "
            "checkout, set HAUSSMANN_ORACLE_OPTIONAL=1 to opt into the old "
            "skip-if-missing behaviour instead."
        ) from exc

from buildings.typologies.paris import reglement as new_reglement
from buildings.typologies.paris import reglement_adapter as reglement_adapter_module


class TestDifferentialAgainstHaussmannOracle:
    """Verify the ported module matches the original across all configurations."""

    @pytest.mark.parametrize("street_width", [
        3.0, 5.0, 7.8, 9.0, 9.75, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0,
    ])
    @pytest.mark.parametrize("year", [
        1820, 1840, 1858, 1859, 1870, 1880, 1883, 1884, 1890, 1901, 1902, 1910,
    ])
    def test_facade_height_limit_identical_across_sweep(self, street_width, year):
        """Facade height limit must match for every (street, year) combo."""
        era = new_reglement.era_for_year(year)
        old_era = old_reglement.era_for_year(year)
        assert era.name == old_era.name, f"Era mismatch for year {year}"

        old_reg = old_reglement.get_reglement(old_era)
        new_reg = new_reglement.get_reglement(era)

        old_height = old_reg.facade_height_limit(street_width)
        new_height = new_reg.facade_height_limit(street_width)

        assert new_height == pytest.approx(old_height, abs=1e-9), (
            f"Facade height mismatch at street={street_width}, year={year}: "
            f"old={old_height}, new={new_height}"
        )

    @pytest.mark.parametrize("street_width", [
        3.0, 5.0, 7.8, 9.0, 9.75, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0,
    ])
    @pytest.mark.parametrize("year", [
        1820, 1840, 1858, 1859, 1870, 1880, 1883, 1884, 1890, 1901, 1902, 1910,
    ])
    def test_arc_radius_identical_across_sweep(self, street_width, year):
        """Arc radius must match for every (street, year) combo."""
        era = new_reglement.era_for_year(year)
        old_era = old_reglement.era_for_year(year)
        assert era.name == old_era.name

        old_reg = old_reglement.get_reglement(old_era)
        new_reg = new_reglement.get_reglement(era)

        old_radius = old_reg.arc_radius(street_width)
        new_radius = new_reg.arc_radius(street_width)

        assert new_radius == pytest.approx(old_radius, abs=1e-9), (
            f"Arc radius mismatch at street={street_width}, year={year}: "
            f"old={old_radius}, new={new_radius}"
        )

    @pytest.mark.parametrize("street_width", [
        3.0, 5.0, 7.8, 9.0, 9.75, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0,
    ])
    @pytest.mark.parametrize("year", [
        1820, 1840, 1858, 1859, 1870, 1880, 1883, 1884, 1890, 1901, 1902, 1910,
    ])
    def test_total_height_identical_across_sweep(self, street_width, year):
        """Total height (facade + ridge) must match for every (street, year) combo."""
        era = new_reglement.era_for_year(year)
        old_era = old_reglement.era_for_year(year)
        assert era.name == old_era.name

        old_env = old_reglement.compute_envelope(street_width, old_era, parcel_depth=40.0)
        new_env = new_reglement.compute_envelope(street_width, era, parcel_depth=40.0)

        old_total = old_env.total_height
        new_total = float(new_env.total_height)  # Unwrap the Reg quantity

        assert new_total == pytest.approx(old_total, abs=1e-9), (
            f"Total height mismatch at street={street_width}, year={year}: "
            f"old={old_total}, new={new_total}"
        )

    @pytest.mark.parametrize("year", [1820, 1858, 1859, 1883, 1884, 1901, 1902, 1910])
    def test_era_for_year_identical(self, year):
        """Era lookup must return the same era value (by name)."""
        old_era = old_reglement.era_for_year(year)
        new_era = new_reglement.era_for_year(year)
        # Compare enum names, not identities, since they're from different modules
        assert new_era.name == old_era.name, (
            f"Era name mismatch for year {year}: new={new_era.name}, old={old_era.name}"
        )


class TestDocumentedFigures:
    """Assert the documented regulatory figures from the sources."""

    def test_1884_decree_yields_28_50_m_ceiling(self):
        """The documented 28.50 m ceiling: 20 m facade + 8.50 m comble (1884).

        This is THE key figure from the 1884 Alphand decree. The model was
        not fitted to this number; it is the source constraint. Any divergence
        is a regression.
        """
        env = new_reglement.compute_envelope(
            street_width=30.0,
            era=new_reglement.Era.ALPHAND,
            parcel_depth=40.0,
        )

        # Facade height: 20 m for wide streets (over 20 m) under the 1884 decree
        assert env.facade_height == pytest.approx(20.0, abs=1e-9), (
            f"1884 facade height should be 20.0 m for street width 30 m, "
            f"got {env.facade_height}"
        )

        # Legal ridge height: 8.50 m (the documented arc radius for wide streets)
        assert env.legal_ridge_height == pytest.approx(8.50, abs=1e-9), (
            f"1884 comble height should be 8.50 m, got {env.legal_ridge_height}"
        )

        # Total height: 28.50 m
        total = float(env.total_height)
        assert total == pytest.approx(28.50, abs=1e-9), (
            f"1884 total height should be 28.50 m, got {total}"
        )

    def test_1859_decree_facade_heights(self):
        """The height steps from the 1859 Règlement."""
        reg = new_reglement.get_reglement(new_reglement.Era.SECOND_EMPIRE)

        # The 1859 decree introduces a 20 m facade for wide streets
        assert reg.facade_height_limit(25.0) == pytest.approx(20.0, abs=1e-9)
        assert reg.facade_height_limit(15.0) == pytest.approx(17.55, abs=1e-9)
        assert reg.facade_height_limit(9.0) == pytest.approx(14.62, abs=1e-9)
        assert reg.facade_height_limit(5.0) == pytest.approx(11.70, abs=1e-9)

    def test_1884_decree_facade_heights_raised(self):
        """The 1884 decree raises most steps of the 1859 table."""
        old_reg = new_reglement.get_reglement(new_reglement.Era.SECOND_EMPIRE)
        new_reg = new_reglement.get_reglement(new_reglement.Era.ALPHAND)

        # The 1884 decree raises heights for narrow to medium streets
        # but not for the widest (20 m street still gets capped at 20 m)
        streets_raised = [5.0, 9.0, 12.0]
        for street in streets_raised:
            old_h = old_reg.facade_height_limit(street)
            new_h = new_reg.facade_height_limit(street)
            assert new_h > old_h, (
                f"1884 decree should raise facade height at street width {street}: "
                f"old={old_h}, new={new_h}"
            )

    def test_1823_balcony_rule_minimum_height(self):
        """Balconies may start only at 6 m above the pavement (1823 ordinance)."""
        levels = [0.0, 3.0, 6.0, 9.0, 12.0]
        rule = new_reglement.balcony_rule(levels, new_reglement.Era.SECOND_EMPIRE)

        # Floor at exactly 6.0 m should be eligible
        assert 2 in rule.continuous

        # Floors below 6.0 m should not be eligible
        assert 0 not in rule.continuous and 1 not in rule.continuous

    def test_1823_balcony_rule_max_projection(self):
        """Balcony projection cap is 0.80 m (1823 ordinance)."""
        for era in [
            new_reglement.Era.ROYAL,
            new_reglement.Era.SECOND_EMPIRE,
            new_reglement.Era.ALPHAND,
            new_reglement.Era.BONNIER,
        ]:
            rule = new_reglement.balcony_rule([0.0, 7.0], era)
            assert float(rule.max_projection) == pytest.approx(0.80, abs=1e-9)

    def test_1884_decree_minimum_storey_height(self):
        """Minimum storey height remains 2.60 m under the 1884 decree."""
        reg = new_reglement.get_reglement(new_reglement.Era.ALPHAND)
        assert reg.min_floor_height == pytest.approx(2.60, abs=1e-9)

    def test_pre_1884_comble_is_45_degrees(self):
        """Before 1884, the comble was inscribed below a 45° diagonal."""
        env = new_reglement.compute_envelope(
            street_width=30.0,
            era=new_reglement.Era.SECOND_EMPIRE,
            parcel_depth=20.0,
        )
        assert env.roof_envelope == new_reglement.RoofEnvelope.DIAGONAL_45

        # For a 45° diagonal, inset should equal height
        for h in [0.5, 1.0, 2.0, 3.0]:
            inset = float(env.setback_at(h))
            assert inset == pytest.approx(h, abs=1e-9)

    def test_post_1884_comble_is_circular_arc(self):
        """From 1884 on, the comble follows a circular arc."""
        env = new_reglement.compute_envelope(
            street_width=30.0,
            era=new_reglement.Era.ALPHAND,
            parcel_depth=40.0,
        )
        assert env.roof_envelope == new_reglement.RoofEnvelope.CIRCULAR_ARC

    def test_post_1902_comble_is_eighth_arc_oblique(self):
        """From 1902 on, the comble is an eighth of arc plus a 45° oblique."""
        env = new_reglement.compute_envelope(
            street_width=30.0,
            era=new_reglement.Era.BONNIER,
            parcel_depth=60.0,
        )
        assert env.roof_envelope == new_reglement.RoofEnvelope.EIGHTH_ARC_OBLIQUE


class TestQuantityAnnotations:
    """Verify that wrapped results carry proper citations."""

    def test_total_height_carries_citation(self):
        """The total_height property returns a Reg with a proper citation."""
        env = reglement_adapter_module.compute_envelope(
            street_width=30.0,
            era=reglement_adapter_module.Era.ALPHAND,
            parcel_depth=40.0,
        )
        total_qty = env.total_height

        # Should be a Quantity with a non-empty citation
        from buildings.quantity import Quantity, Kind
        assert isinstance(total_qty, Quantity)
        assert total_qty.kind == Kind.REGULATORY
        assert len(total_qty.why) > 0
        # The citation should mention 1884 Alphand
        assert "1884" in total_qty.why or "Alphand" in total_qty.why

    def test_setback_carries_citation(self):
        """The setback_at method returns a Reg with a proper citation."""
        env = reglement_adapter_module.compute_envelope(
            street_width=30.0,
            era=reglement_adapter_module.Era.ALPHAND,
            parcel_depth=40.0,
        )
        setback_qty = env.setback_at(2.0)

        from buildings.quantity import Quantity, Kind
        assert isinstance(setback_qty, Quantity)
        assert setback_qty.kind == Kind.REGULATORY
        assert len(setback_qty.why) > 0

    def test_balcony_rule_max_projection_carries_citation(self):
        """Balcony projection limit returns a Reg with citation."""
        rule = reglement_adapter_module.balcony_rule([0.0, 7.0], reglement_adapter_module.Era.SECOND_EMPIRE)
        proj_qty = rule.max_projection

        from buildings.quantity import Quantity, Kind
        assert isinstance(proj_qty, Quantity)
        assert proj_qty.kind == Kind.REGULATORY
        assert len(proj_qty.why) > 0
        # Citation should mention 1823
        assert "1823" in proj_qty.why

    def test_balcony_rule_min_height_carries_citation(self):
        """Balcony minimum height returns a Reg with citation."""
        rule = reglement_adapter_module.balcony_rule([0.0, 7.0], reglement_adapter_module.Era.SECOND_EMPIRE)
        height_qty = rule.min_height

        from buildings.quantity import Quantity, Kind
        assert isinstance(height_qty, Quantity)
        assert height_qty.kind == Kind.REGULATORY
        assert len(height_qty.why) > 0
        assert "1823" in height_qty.why
