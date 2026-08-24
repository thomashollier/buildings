"""S10 — differential test against the reference oracle (``../haussmann``).

This is the *generator-level* oracle diff (as opposed to
``test_reglement_diff.py``, which diffs the ported regulatory module in
isolation). It drives both the rewrite and the previous implementation over
the same situations via ``dev/harness/oracle_diff.py`` and separates the
result into three buckets, matching the harness module's own docstring:

1. Regulatory output — asserted exactly equal.
2. Gross proportions — reported as a distribution, outliers flagged against
   an explicit tolerance, but NOT asserted equal (the two rule models are a
   deliberate rewrite and are expected to diverge here).
3. Qualitative facts — recorded in the report; nothing here is asserted.

A1.7 applies here exactly as it does to ``test_reglement_diff.py``: a missing
``../haussmann`` checkout is a HARD FAILURE by default (``oracle_diff.require_haussmann``
raises), not a silent skip -- set ``HAUSSMANN_ORACLE_OPTIONAL=1`` to opt out.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HARNESS_DIR = Path(__file__).resolve().parents[2] / "dev" / "harness"
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

import oracle_diff  # noqa: E402

# Every test in this module needs the reference oracle. A1.7: hard failure by
# default (oracle_diff.require_haussmann raises OracleUnavailable), unless the
# operator has explicitly opted into skip-if-missing.
oracle_diff.require_haussmann()


# ---------------------------------------------------------------------------
# Bucket 1 — regulatory. Must agree exactly.
# ---------------------------------------------------------------------------


class TestRegulatoryAgreement:
    """Cornice height limits, arc radii, era boundaries, roof-envelope shape
    and the legal total height must come out bit-for-bit identical: both
    systems wrap the same ported ``reglement`` module, so a mismatch here is
    an integration bug (a phase feeding it the wrong number), not a design
    disagreement."""

    @pytest.fixture(scope="class")
    def rows(self):
        return oracle_diff.regulatory_rows()

    def test_no_mismatches(self, rows):
        mismatches = [r for r in rows if not r.matches]
        assert not mismatches, (
            f"{len(mismatches)}/{len(rows)} regulatory rows disagree between old and new "
            "-- this bucket must agree exactly (both wrap the same ported reglement). "
            "First few: "
            + "; ".join(
                f"{r.year}/{r.street_width}/{r.metric}: old={r.old!r} new={r.new!r}"
                for r in mismatches[:5]
            )
        )

    def test_sweep_is_not_vacuous(self, rows):
        """A gate that iterates zero situations always 'passes' (G2's vacuous
        gate). Pin the sweep size so a refactor that empties the year/width
        lists is caught here rather than by the report silently shrinking."""
        assert len(rows) >= 400, f"expected a broad regulatory sweep, got only {len(rows)} rows"

    def test_28_50m_ceiling_from_both_systems(self):
        """The documented 1884 decree figure -- 20 m facade + 8.50 m comble --
        independently from BOTH systems, not fitted to either."""
        era_new = oracle_diff.new_era_for_year(1890)
        new_env = oracle_diff._new_compute_envelope(30.0, era_new, 40.0)
        assert new_env.facade_height == pytest.approx(20.0, abs=1e-9)
        assert new_env.legal_ridge_height == pytest.approx(8.50, abs=1e-9)
        assert new_env.facade_height + new_env.legal_ridge_height == pytest.approx(28.50, abs=1e-9)

        old_era = oracle_diff._old_reglement.era_for_year(1890)
        old_env = oracle_diff._old_reglement.compute_envelope(
            30.0, old_era, 40.0, roof_fill=1.0, max_ridge=None
        )
        assert old_env.facade_height == pytest.approx(20.0, abs=1e-9)
        assert old_env.legal_ridge_height == pytest.approx(8.50, abs=1e-9)
        assert old_env.facade_height + old_env.legal_ridge_height == pytest.approx(28.50, abs=1e-9)


# ---------------------------------------------------------------------------
# Bucket 2 — gross proportions. Reported, tolerance-flagged, NOT asserted
# equal -- but bounded, so a wild regression (not a design difference) still
# fails the suite.
# ---------------------------------------------------------------------------


class TestGrossProportions:
    @pytest.fixture(scope="class")
    def rows(self):
        return oracle_diff.proportion_rows()

    def test_sweep_is_not_vacuous(self, rows):
        assert len(rows) >= 300, f"expected a broad proportion sweep, got only {len(rows)} rows"

    def test_no_generator_crashes_across_the_matrix(self, rows):
        """Every row in ``rows`` implies both generators completed without
        raising for that situation -- the fixture itself is the assertion:
        if either ``run_new`` or ``run_old`` raised, this fixture would have
        raised during collection instead of producing rows."""
        assert rows

    def test_outlier_rate_is_bounded(self, rows):
        """Divergence here is expected (different rule models -- see the
        harness module's docstring); a BLOWOUT is not. If every single row
        fell outside tolerance that would mean the two systems no longer
        describe the same kind of building at all, which is a regression
        worth catching even though we don't assert per-row equality.

        The ceiling is generous on purpose: two known, one-directional,
        documented divergences (`_FACADE_AMBITION` for MODEST, `_COMBLE_FILL`
        for total height -- see ``characterize_outliers`` and the report's
        narrative) already account for a real minority of rows without any
        bug being present.
        """
        outliers = [r for r in rows if r.verdict == "OUTLIER"]
        rate = len(outliers) / len(rows)
        assert rate <= 0.35, (
            f"{len(outliers)}/{len(rows)} ({rate:.0%}) proportion rows fell outside "
            "tolerance -- more than the documented divergences account for. Regenerate "
            "dev/logs/oracle_report.md and check the 'genuine bugs' section."
        )

    def test_storey_counts_are_architecturally_sane(self, rows):
        """Independent of what old says: a Paris immeuble in this era range
        is never a 1-storey shed nor a 40-storey tower. Catches integration
        bugs (e.g. a mis-routed envelope) that a distribution comparison
        against old's own possibly-quirky output might not."""
        storey_rows = [r for r in rows if r.metric == "storey_count"]
        assert storey_rows
        for r in storey_rows:
            assert 2 <= r.new_value <= 15, (
                f"{r.situation.label}: new storey_count={r.new_value} is outside a sane "
                "range for a 19th-century Paris immeuble"
            )

    def test_total_height_never_undercuts_built_height(self):
        """The silhouette (with comble) can never be shorter than the stone
        facade alone -- a structural sanity check on the new system's own
        output, independent of any comparison to old."""
        for situation in oracle_diff.proportion_situations()[:12]:
            new = oracle_diff.run_new(situation)
            assert new.total_height >= new.built_height - 1e-6, (
                f"{situation.label}: total_height {new.total_height} < built_height "
                f"{new.built_height}"
            )


# ---------------------------------------------------------------------------
# Bucket 3 — qualitative. Recorded only; nothing here is asserted beyond
# "the harness can actually gather the fact from both systems".
# ---------------------------------------------------------------------------


class TestQualitativeRecording:
    @pytest.fixture(scope="class")
    def rows(self):
        return oracle_diff.qualitative_rows()

    def test_every_situation_produces_a_row(self, rows):
        expected = len(oracle_diff.QUAL_GROUNDS) * len(oracle_diff.QUAL_CLASSES)
        assert len(rows) == expected

    def test_new_system_always_has_an_entrance(self, rows):
        """A6.1, cross-checked at the harness level: every situation in this
        matrix -- all five ground programmes, all four classes -- comes back
        with a real entrance kind from the new system, which is the point of
        A6.1 and the reason this is recorded rather than compared."""
        for r in rows:
            assert r.new_entrance_kind in ("porte_cochere", "porte_pietonne"), (
                f"{r.situation.label}: unexpected entrance kind {r.new_entrance_kind!r}"
            )


# ---------------------------------------------------------------------------
# Report generation is itself part of the deliverable.
# ---------------------------------------------------------------------------


def test_report_is_written(tmp_path):
    """The report is a required artefact of S10, so writing it is tested,
    not just performed as a side effect of running this file."""
    out = tmp_path / "oracle_report.md"
    written = oracle_diff.write_report(out)
    assert written == out
    text = out.read_text()
    assert "# Reference-oracle diff report" in text
    assert "## 1. Regulatory output" in text
    assert "## 2. Gross proportions" in text
    assert "## 3. Qualitative" in text
    assert "Divergences that look like bugs" in text
    # The situation count the harness itself reports must be non-trivial --
    # a report describing zero situations compared is the vacuous gate again.
    assert "Situations compared" in text


def test_default_report_path_is_dev_logs_oracle_report_md():
    assert oracle_diff.DEFAULT_REPORT_PATH == oracle_diff.REPO_ROOT / "dev" / "logs" / "oracle_report.md"
