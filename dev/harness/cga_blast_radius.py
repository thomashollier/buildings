#!/usr/bin/env python3
"""Blast radius: a local change to the grammar changes only what it addresses.

The reason for writing the building as a shape grammar is that a sub-part can
be refined -- its look, its rule, a variation on one floor or one axis --
without the change rippling into parts it never named. This harness checks
that claim the only way it can be checked: apply a change, derive a few
hundred buildings with and without it, diff every IR node, and confirm that
every node that moved is one the change addressed.

Each scenario states the change and, separately, what it is *allowed* to
touch. A node that changed outside that allowance is a leak, and any leak
fails the run.

Run:  python3 dev/harness/cga_blast_radius.py [--cases N]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dev" / "harness"))

from cga_equivalence import site_of  # noqa: E402
from fuzz import build_cases  # noqa: E402

from buildings.cga import Grammar, Layer, Shape  # noqa: E402
from buildings.ir.nodes import Node  # noqa: E402
from buildings.ir.serial import to_json  # noqa: E402
from buildings.typologies.paris import catalogue  # noqa: E402
from buildings.typologies.paris.compose import ORDER_OVERRIDE  # noqa: E402
from buildings.typologies.paris.generate import walk  # noqa: E402
from buildings.typologies.paris.grammar import generate_cga  # noqa: E402
from buildings.typologies.paris.qualify.context import Properties  # noqa: E402
from buildings.typologies.paris.roles import Role  # noqa: E402


# --- selectors ---------------------------------------------------------------


def on_the_noble_floor(shape: Shape) -> bool:
    return shape.attr("role", None) is Role.PRINCIPAL


def on_the_entrance_axis(shape: Shape) -> bool:
    slot = shape.attr("slot", None)
    return shape.label != "Storey" and slot is not None and slot.name in catalogue.ENTRANCE_SLOT_NAMES


# --- the changes ---------------------------------------------------------------


def narrow_keystones(g: Grammar) -> Grammar:
    """LOOK, everywhere: every keystone drawn at 40% of the light it locks."""
    base = g.interpreters["Keystone"]

    def write(shape, below, d):
        out = []
        for node in base(shape, below, d):
            x, w = node.props["x"], node.props["w"]
            out.append(
                dataclasses.replace(node, props={**node.props, "x": x + 0.3 * w, "w": 0.4 * w})
            )
        return out

    return g.with_interpreter("Keystone", write)


def round_heads_on_the_noble_floor(g: Grammar) -> Grammar:
    """RULE, one floor: the étage noble's windows take round heads."""

    def round_heads(ctx, rng):
        return Properties({"opening_head": "round"}, rule="variation.noble_floor_round_heads")

    return g.with_override(
        "Cell", Layer("noble-floor heads", ORDER_OVERRIDE, (round_heads,)), where=on_the_noble_floor
    )


def taller_balustrade_on_the_noble_floor(g: Grammar) -> Grammar:
    """LOOK, one floor: the noble floor's railings drawn 15% taller."""
    base = g.interpreters["Rail"]

    def write(shape, below, d):
        return [
            dataclasses.replace(n, props={**n.props, "h": n.props["h"] * 1.15})
            for n in base(shape, below, d)
        ]

    return g.with_interpreter("Rail", write, where=on_the_noble_floor)


def no_keystones_on_the_entrance_axis(g: Grammar) -> Grammar:
    """RULE, one axis: nothing over the door's column carries a keystone."""

    def no_keystone(ctx, rng):
        return Properties({"keystone_present": False}, rule="variation.entrance_axis_plain")

    return g.with_override(
        "Cell", Layer("entrance axis", ORDER_OVERRIDE, (no_keystone,)), where=on_the_entrance_axis
    )


def round_heads_everywhere_but_claimed_for_one_floor(g: Grammar) -> Grammar:
    """NEGATIVE CONTROL: the same override with its address left off, judged
    against the noble-floor allowance. The checker must report leaks here, or
    it is not checking anything."""

    def round_heads(ctx, rng):
        return Properties({"opening_head": "round"}, rule="variation.noble_floor_round_heads")

    return g.with_override("Cell", Layer("unaddressed", ORDER_OVERRIDE, (round_heads,)))


# --- what each change may touch --------------------------------------------------


def _storey_of(node_id: str) -> str:
    return "/".join(node_id.split("/")[:2])


def _column_of(node_id: str) -> str | None:
    parts = node_id.split("/")
    return parts[2] if len(parts) > 2 and parts[2].startswith("x") else None


@dataclass
class Scenario:
    name: str
    refine: Callable[[Grammar], Grammar]
    allowed: Callable[[Node, dict], bool]
    must_leak: bool = False


def _noble_storeys(root: Node) -> set[str]:
    return {n.id for n in walk(root) if n.kind == "storey" and n.props.get("role") == "principal"}


def _entrance_columns(root: Node) -> set[str]:
    cols = set()
    for n in walk(root):
        if n.kind == "bay" and n.props.get("slot_name") in catalogue.ENTRANCE_SLOT_NAMES:
            cols.add(_column_of(n.id))
    return cols


SCENARIOS = [
    Scenario(
        "keystone drawing, everywhere (look)",
        narrow_keystones,
        lambda n, f: n.kind == "keystone",
    ),
    Scenario(
        "round heads on the noble floor (rule override, one floor)",
        round_heads_on_the_noble_floor,
        lambda n, f: n.kind == "opening" and _storey_of(n.id) in f["noble"],
    ),
    Scenario(
        "taller balustrade on the noble floor (look, one floor)",
        taller_balustrade_on_the_noble_floor,
        lambda n, f: n.kind == "ironwork" and _storey_of(n.id) in f["noble"],
    ),
    Scenario(
        "no keystones on the entrance axis (rule override, one axis)",
        no_keystones_on_the_entrance_axis,
        lambda n, f: n.kind == "keystone" and _column_of(n.id) in f["entrance"],
    ),
    Scenario(
        "negative control: an override with no address",
        round_heads_everywhere_but_claimed_for_one_floor,
        lambda n, f: n.kind == "opening" and _storey_of(n.id) in f["noble"],
        must_leak=True,
    ),
]


# --- the diff ------------------------------------------------------------------


def _index(root: Node) -> dict[str, tuple[Node, str]]:
    out = {}
    for n in walk(root):
        own = dataclasses.replace(n, children=())
        out[n.id] = (n, json.dumps(json.loads(to_json(own)), sort_keys=True))
    return out


def run(scenario: Scenario, cases) -> dict:
    changed_kinds: Counter = Counter()
    leaks: list[str] = []
    buildings_changed = 0
    for case in cases:
        site = site_of(case)
        before, _ = generate_cga(site)
        after, _ = generate_cga(site, refine=scenario.refine)
        facts = {"noble": _noble_storeys(before), "entrance": _entrance_columns(before)}
        a, b = _index(before), _index(after)
        moved = False
        for node_id in sorted(set(a) | set(b)):
            old, new = a.get(node_id), b.get(node_id)
            if old is not None and new is not None and old[1] == new[1]:
                continue
            node = (old or new)[0]
            if node.kind in ("bay", "storey", "building"):
                # A container changes only because a child did; the child is
                # what is judged. Its own props are compared above.
                if old is not None and new is not None and (
                    dataclasses.replace(old[0], children=()).props
                    == dataclasses.replace(new[0], children=()).props
                ):
                    continue
            moved = True
            changed_kinds[f"{node.kind}{'' if old and new else ' (removed)' if old else ' (added)'}"] += 1
            if not scenario.allowed(node, facts):
                leaks.append(f"case {case.index}: {node_id} ({node.kind})")
        buildings_changed += moved
    return {
        "buildings": len(cases),
        "buildings_changed": buildings_changed,
        "changed": dict(changed_kinds),
        "leaks": leaks,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=300)
    args = ap.parse_args(argv)
    cases = build_cases(75)
    cases = cases[:: max(1, len(cases) // args.cases)][: args.cases]

    failed = False
    for scenario in SCENARIOS:
        r = run(scenario, cases)
        if scenario.must_leak:
            status = (
                f"checker caught {len(r['leaks'])} leaked nodes, as it must"
                if r["leaks"]
                else "CHECKER BLIND: the control did not leak"
            )
        else:
            status = "contained" if not r["leaks"] else f"LEAKED ({len(r['leaks'])} nodes)"
        print(f"\n{scenario.name}\n  {scenario.refine.__doc__.strip()}")
        print(
            f"  {r['buildings_changed']}/{r['buildings']} buildings changed; nodes changed: "
            + (", ".join(f"{k} x{v}" for k, v in sorted(r["changed"].items())) or "none")
        )
        print(f"  {status}")
        if not scenario.must_leak:
            for leak in r["leaks"][:5]:
                print(f"    leak: {leak}")
        failed |= bool(r["leaks"]) != scenario.must_leak
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
