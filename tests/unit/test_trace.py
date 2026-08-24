from __future__ import annotations

import pytest

from buildings.trace import TraceEntry, TraceLog


def test_trace_entry_defaults_to_empty_inputs() -> None:
    e = TraceEntry(rule="paris.qualify.balcony.ordonnance_1823", phase="qualification", detail="balcony placed")
    assert dict(e.inputs) == {}


def test_trace_entry_inputs_is_read_only() -> None:
    e = TraceEntry(
        rule="r",
        phase="structure",
        detail="d",
        inputs={"street_width": 18.0},
    )
    with pytest.raises(TypeError):
        e.inputs["street_width"] = 99.0  # type: ignore[index]


def test_trace_entry_is_frozen() -> None:
    e = TraceEntry(rule="r", phase="structure", detail="d")
    with pytest.raises(Exception):
        e.rule = "other"  # type: ignore[misc]


def test_trace_log_record_and_explain() -> None:
    log = TraceLog()
    e1 = TraceEntry(rule="paris.structure.storey.solve", phase="structure", detail="height budget filled")
    e2 = TraceEntry(rule="paris.roles.principal.tallest", phase="roles", detail="tallest habitable slot")
    log.record("storey/2", e1)
    log.record("storey/2", e2)

    explanation = log.explain("storey/2")
    assert explanation == [e1, e2]


def test_trace_log_explain_unknown_id_returns_empty() -> None:
    log = TraceLog()
    assert log.explain("does/not/exist") == []


def test_trace_log_all_ids() -> None:
    log = TraceLog()
    log.record("a", TraceEntry(rule="r1", phase="structure", detail="d1"))
    log.record("b", TraceEntry(rule="r2", phase="roles", detail="d2"))
    assert set(log.all_ids()) == {"a", "b"}


def test_trace_log_explain_returns_a_copy() -> None:
    log = TraceLog()
    log.record("a", TraceEntry(rule="r1", phase="structure", detail="d1"))
    result = log.explain("a")
    result.append(TraceEntry(rule="r2", phase="structure", detail="d2"))
    assert len(log.explain("a")) == 1
