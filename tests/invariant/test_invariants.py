"""Gate G10 — the invariant fuzzer, as a pytest suite.

    "Fuzz across seeds, widths and eras for invariant violations."  — PLAN.md S10

The actual sweep logic (sampling, the per-category checkers, the "does the
fuzzer have teeth" negative controls) lives in ``dev/harness/fuzz.py`` — this
file's sibling and the other half of this task. This module does not
duplicate that logic; it runs the identical sweep once per test session
(``_corpus`` below) and then asserts each named invariant / structural check
individually, so a failure reports as
``test_i3_every_quantity_carries_its_kind FAILED`` rather than as one opaque
"the fuzzer found something" blob — matching the style every other file in
this directory already uses (``test_fitting_sweep.py``,
``test_silhouette_envelope.py``, ``test_block_datums.py``).

Running this module *is* running the fuzzer at full scale (the same
``N_BASE_FULL`` = 75 base situations x 40 categorical combinations = 3000
cases that ``python3 dev/harness/fuzz.py`` uses to write
``dev/logs/fuzz_report.md``): there is deliberately no gap between "the report
says clean" and "pytest says clean". Expect this module to take on the order
of two minutes; that is the cost of a sweep and not a fixture that got lost.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "dev" / "harness"))

import fuzz  # noqa: E402  (dev/harness/fuzz.py, not a pip package)


# ---------------------------------------------------------------------------
# The corpus: run once, every test below reads the same FailureLog.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def corpus() -> tuple["fuzz.FailureLog", dict]:
    log, stats = fuzz.run(fuzz.N_BASE_FULL)
    return log, stats


def _assert_category_empty(log: "fuzz.FailureLog", *categories: str, what: str) -> None:
    hit = {c: log.counts[c] for c in categories if log.counts.get(c)}
    if not hit:
        return
    lines = [f"{what}: {sum(hit.values())} failure(s) across {sorted(hit)}"]
    for category in hit:
        for failure in log.examples[category][:3]:
            lines.append(f"  [{category}] repro={failure.repro}")
            lines.append(f"    {failure.detail.splitlines()[0]}")
    pytest.fail("\n".join(lines))


# ---------------------------------------------------------------------------
# Harness self-check — is this actually a fuzz sweep?
# ---------------------------------------------------------------------------


def test_the_sample_actually_varies_every_input_axis(corpus) -> None:
    """The task's own warning, made a real assertion: a fuzzer that passes
    because it never varied its inputs is not a passing fuzzer."""
    log, stats = corpus
    assert stats["n_cases"] >= 2000, "the sweep did not run at the scale the task asked for"
    _assert_category_empty(log, "fuzzer_not_varying", what="the sample is not varying an input axis")


def test_the_sample_is_deterministic() -> None:
    """I5, applied to the fuzzer itself: the same corpus, twice."""
    a = fuzz.build_cases(30)
    b = fuzz.build_cases(30)
    assert a == b


def test_the_checkers_have_teeth() -> None:
    """Each structural checker must catch a hand-built, deliberately broken
    input — proof that a clean sweep means the design held up, not that the
    checks never fire. Mirrors ``test_the_sweep_could_have_failed`` in
    ``test_silhouette_envelope.py``."""
    log = fuzz.FailureLog()
    fuzz.self_test_checkers_have_teeth(log)
    assert log.total == 0, (
        "at least one checker failed to catch its synthetic violation — "
        f"{dict(log.counts)}"
    )


def test_every_case_generates_without_an_unexpected_exception(corpus) -> None:
    log, stats = corpus
    assert stats["n_other_exception"] == 0, (
        f"{stats['n_other_exception']} case(s) raised something other than "
        "FitInfeasible"
    )
    _assert_category_empty(
        log, "generation_raised", "solve_structure_raised_after_generate_succeeded",
        what="generate() or solve_structure() raised unexpectedly",
    )


# ---------------------------------------------------------------------------
# I1 — phases read strictly backwards
# ---------------------------------------------------------------------------


def test_i1_mutating_a_frozen_object_always_raises(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(log, "I1_mutation_not_raising", what="I1: a mutation did not raise")


# ---------------------------------------------------------------------------
# I2 — a building never samples a block-level fact
# ---------------------------------------------------------------------------


def test_i2_handed_down_datums_survive_unchanged(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log, "I2_datum_not_honoured", "I2_datum_override_raised",
        what="I2: a handed-down block datum was not honoured verbatim",
    )


# ---------------------------------------------------------------------------
# I3 — every quantity carries its kind
# ---------------------------------------------------------------------------


def test_i3_every_quantity_carries_its_kind(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log,
        "I3_absolute_scaled",
        "I3_regulatory_scaled",
        "I3_proportional_not_monotonic",
        "I3_proportional_not_scaling",
        "I3_mixed_arithmetic_not_rigid",
        "I3_rigid_scalar_multiply_silent",
        "I3_absolute_entrance_varies_by_class",
        what="I3: a quantity did not respect its own kind",
    )


# ---------------------------------------------------------------------------
# I4 — every emitted node records the rule that produced it
# ---------------------------------------------------------------------------


def test_i4_every_node_has_a_nonempty_trace(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log, "I4_empty_trace", "I4_blank_rule", "I4_blank_detail",
        what="I4: a node's trace was empty or blank",
    )


# ---------------------------------------------------------------------------
# I5 — same seed + situation identical; different seed differs
# ---------------------------------------------------------------------------


def test_i5_same_seed_and_situation_is_byte_identical(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log,
        "I5_same_seed_differs",
        "I5_same_seed_render_differs",
        "I5_regeneration_raised",
        what="I5: regenerating the identical situation changed the output",
    )


def test_i5_a_different_seed_actually_differs(corpus) -> None:
    log, stats = corpus
    _assert_category_empty(log, "I5_seed_never_varies_output", what="I5: seed never moved the output")
    assert stats["seed_groups_with_variation"] > 0, (
        "no sampled group showed any seed-driven variation at all — either "
        "the RNG is disconnected, or the sample never reached a seed-driven "
        "decision"
    )


# ---------------------------------------------------------------------------
# Renderer + serialisation
# ---------------------------------------------------------------------------


def test_render_never_raises_and_is_deterministic(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(log, "render_raised", "render_not_deterministic", what="render()")


def test_ir_json_roundtrip_is_lossless(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log, "serial_roundtrip_raised", "serial_roundtrip_lossy",
        what="IR JSON round-trip",
    )


# ---------------------------------------------------------------------------
# Structural sanity
# ---------------------------------------------------------------------------


def test_silhouette_lies_within_the_regulatory_envelope(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log,
        "no_silhouette",
        "silhouette_eaves_exceeds_facade_limit",
        "silhouette_overhangs_street",
        "silhouette_exceeds_ceiling",
        "silhouette_breaks_envelope",
        what="silhouette outside its regulatory envelope",
    )


def test_storey_heights_respect_the_1859_minimum(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(log, "storey_below_minimum", what="a storey below its legal minimum")


def test_bays_fill_the_parcel_exactly(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(log, "bay_residual", what="bays did not fill the parcel to 1e-9")


def test_no_nan_negative_or_zero_dimension(corpus) -> None:
    log, _stats = corpus
    _assert_category_empty(
        log,
        "nonfinite_dimension",
        "negative_dimension",
        "zero_width_element",
        "nonfinite_polyline_point",
        what="a NaN/Inf, negative, or (undesigned) zero-width element",
    )


def test_generation_does_not_raise_for_any_case_in_the_sweep(corpus) -> None:
    """The task's own wording, literally: every case in the sweep either
    generates or is honestly refused as ``FitInfeasible`` (a real, load-bearing
    outcome documented throughout ``structure.py`` — a parcel too narrow for
    its own ABSOLUTE entrance is refused, not fabricated) — never a crash."""
    log, stats = corpus
    assert stats["n_ok"] + stats["n_infeasible"] == stats["n_cases"]
    assert stats["n_other_exception"] == 0


def test_report_reflects_the_same_corpus(corpus) -> None:
    """The artifact this task also asks for (``dev/logs/fuzz_report.md``) is
    not a second, independently-maintained account of the sweep — it is
    ``fuzz.write_report`` applied to this exact corpus. Regenerating it here
    is cheap (formatting only, no new cases) and confirms the two never
    drift apart."""
    log, stats = corpus
    report = fuzz.write_report(log, stats)
    assert f"Cases run: **{stats['n_cases']}**" in report
