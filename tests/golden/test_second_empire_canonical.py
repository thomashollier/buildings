"""Golden-master pinning for the canonical Second Empire situations
(Amendment 9 — "lock the canonical Second Empire case").

Four named situations (``situations.SITUATIONS``) are run end to end through
``generate()`` and the resulting IR tree is compared, node by node, against a
serialised fixture checked into ``tests/golden/data/*.json``. This is the
project's insurance against silent drift: once this style is solidly right,
nothing later — a period port, a refactor of ``qualify``, a change to a
supposedly-unrelated module — should be able to move a canonical Second
Empire building's output without the change being a loud, reviewed act.

**A failure here must be readable.** ``pytest.fail`` below never says "bytes
differ": it walks both trees in parallel and reports the first node id, kind
and prop (or trace entry) that changed, so the failure message already
answers "what moved" without anyone opening a JSON diff by hand.

**Regenerating a golden is a deliberate, visible act, not a silent
overwrite.** Two ways to do it, and both stop short of quietly blessing the
new output as correct:

    UPDATE_SECOND_EMPIRE_GOLDENS=1 python -m pytest tests/golden/test_second_empire_canonical.py

or the standalone script, which does the same thing without pytest:

    python dev/harness/regenerate_second_empire_goldens.py

Either way, the affected ``tests/golden/data/*.json`` files are rewritten
from the current generator output and the pytest run then FAILS on purpose,
naming which fixtures were rewritten — so "the goldens were updated" cannot
be mistaken for "the test passed". Diff the rewritten JSON (or re-run without
the env var) before treating the change as accepted. Nothing here regenerates
a fixture just because it is missing or stale; a missing fixture is a hard
failure with the same instructions in its message.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from buildings.ir.nodes import Node
from buildings.ir.serial import from_json, to_json
from buildings.typologies.paris.generate import generate

from .situations import SITUATIONS

DATA_DIR = Path(__file__).resolve().parent / "data"

#: Set to "1" to deliberately rewrite every golden fixture from the current
#: generator output. See the module docstring: this is a reviewed act, not a
#: silent pass — the test still fails after writing, on purpose.
UPDATE_ENV_VAR = "UPDATE_SECOND_EMPIRE_GOLDENS"


def _golden_path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def _generate(name: str) -> Node:
    site = SITUATIONS[name]
    building, _log = generate(site)
    return building


# ---------------------------------------------------------------------------
# A readable diff: which node, which prop, not "bytes differ"
# ---------------------------------------------------------------------------


def _trace_diffs(old_trace, new_trace, where: str) -> list[str]:
    diffs: list[str] = []
    if len(old_trace) != len(new_trace):
        diffs.append(
            f"{where}: trace entry count changed {len(old_trace)} -> {len(new_trace)}"
        )
        return diffs
    for i, (ot, nt) in enumerate(zip(old_trace, new_trace)):
        if ot.rule != nt.rule:
            diffs.append(f"{where} trace[{i}]: rule {ot.rule!r} -> {nt.rule!r}")
        if dict(ot.inputs) != dict(nt.inputs):
            diffs.append(
                f"{where} trace[{i}] (rule={ot.rule!r}): inputs "
                f"{dict(ot.inputs)!r} -> {dict(nt.inputs)!r}"
            )
        if ot.detail != nt.detail:
            diffs.append(
                f"{where} trace[{i}] (rule={ot.rule!r}): detail changed\n"
                f"    old: {ot.detail!r}\n"
                f"    new: {nt.detail!r}"
            )
    return diffs


def _diff(old: Node, new: Node, path: str = "") -> list[str]:
    """First readable differences between two IR trees, old (golden) vs new
    (freshly generated), reported as ``node id / kind / prop: old -> new``."""
    where = path or f"/{old.id}"
    diffs: list[str] = []

    if old.kind != new.kind:
        diffs.append(f"{where}: kind changed {old.kind!r} -> {new.kind!r}")
    if old.id != new.id:
        diffs.append(f"{where}: id changed {old.id!r} -> {new.id!r}")

    old_props: dict[str, Any] = dict(old.props)
    new_props: dict[str, Any] = dict(new.props)
    for key in sorted(set(old_props) | set(new_props)):
        ov = old_props.get(key, "<absent>")
        nv = new_props.get(key, "<absent>")
        if ov != nv:
            diffs.append(f"{where} (kind={old.kind!r}) prop {key!r}: {ov!r} -> {nv!r}")

    diffs.extend(_trace_diffs(old.trace, new.trace, where))

    if len(old.children) != len(new.children):
        diffs.append(
            f"{where}: child count changed {len(old.children)} -> {len(new.children)} "
            f"({[c.id for c in old.children]!r} vs {[c.id for c in new.children]!r})"
        )
        return diffs  # cannot usefully pair children past a count mismatch

    for oc, nc in zip(old.children, new.children):
        diffs.extend(_diff(oc, nc, path=f"{where}/{oc.id}"))
    return diffs


# ---------------------------------------------------------------------------
# The test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("situation_name", sorted(SITUATIONS))
def test_golden_master_matches(situation_name: str) -> None:
    fresh = _generate(situation_name)
    path = _golden_path(situation_name)

    if os.environ.get(UPDATE_ENV_VAR) == "1":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(to_json(fresh) + "\n")
        pytest.fail(
            f"{UPDATE_ENV_VAR}=1: rewrote {path} from the current generator output. "
            "This is a deliberate update, not a passing test -- diff the fixture "
            "(or inspect it) before treating the new output as correct, then rerun "
            "WITHOUT the env var to confirm the golden now matches."
        )

    if not path.exists():
        pytest.fail(
            f"no golden fixture at {path} for situation {situation_name!r}. Generate "
            f"it deliberately with `{UPDATE_ENV_VAR}=1 python -m pytest "
            f"{Path(__file__).name}` (or `python dev/harness/"
            "regenerate_second_empire_goldens.py`) and review the new file before "
            "committing it -- a missing fixture is never silently created."
        )

    golden = from_json(path.read_text())
    if fresh == golden:
        return

    diffs = _diff(golden, fresh)
    shown = diffs[:20]
    more = f"\n  ... and {len(diffs) - 20} more" if len(diffs) > 20 else ""
    pytest.fail(
        f"IR for situation {situation_name!r} no longer matches its golden master "
        f"({path}).\n"
        f"{len(diffs)} difference(s) (node / prop / trace field, old -> new), "
        f"first {len(shown)}:\n"
        + "\n".join(f"  {d}" for d in shown)
        + more
        + f"\n\nIf this is an intentional change, rerun with {UPDATE_ENV_VAR}=1 to "
        "regenerate the fixture and review the diff before committing."
    )


def test_every_canonical_situation_has_a_golden_fixture() -> None:
    """A gate against the vacuous-sweep failure mode (G2): if a fixture file
    goes missing from disk without the corresponding situation being removed
    from ``SITUATIONS``, the parametrized test above still runs (and fails
    loudly on the missing file) -- but this test additionally pins the COUNT,
    so a ``SITUATIONS`` entry silently deleted alongside its fixture is caught
    too, rather than the sweep quietly shrinking to fewer cases."""
    assert len(SITUATIONS) == 4, (
        "the canonical set changed size -- that is fine, but update this assertion "
        "deliberately (and the module docstring's description of the four cases) "
        "rather than let the golden sweep silently grow or shrink"
    )


def test_golden_fixtures_round_trip_losslessly() -> None:
    """The golden files themselves must be exactly what ``ir.serial`` can
    reproduce -- i.e. loading one and re-serialising it must be a no-op. This
    is what stops a hand-edited or corrupted fixture from silently becoming
    the new "truth": if a fixture doesn't even round-trip through the IR's
    own serialiser, it cannot be trusted to be compared against anything."""
    for name in SITUATIONS:
        path = _golden_path(name)
        if not path.exists():
            continue  # covered, and failed with instructions, by the test above
        node = from_json(path.read_text())
        assert from_json(to_json(node)) == node, (
            f"{path} does not round-trip losslessly through ir.serial -- it may be "
            "stale, hand-edited, or written by a different serialisation version"
        )
