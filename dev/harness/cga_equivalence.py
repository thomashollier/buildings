#!/usr/bin/env python3
"""The CGA port's acceptance bar: same buildings, case for case.

The shape-tree engine (``buildings.cga``) and the Paris grammar written on it
(``typologies/paris/grammar.py``) must reproduce what the phase pipeline
(``typologies/paris/generate.py``) builds. This sweeps the fuzzer's own corpus
-- 3000 situations, every class x ground x corner at 75 base points -- and
compares the two trees.

Two fingerprints per building:

* **geometry** -- every node's id, kind, props and children, traces stripped.
  This is "the same building" and must match on every case.
* **full** -- the same plus every trace entry. The grammar names its own
  structural rules, so the building's root trace differs by design; everything
  below the root must still match.

Run:
    python3 dev/harness/cga_equivalence.py --snapshot   # record the pipeline
    python3 dev/harness/cga_equivalence.py              # compare the grammar
    python3 dev/harness/cga_equivalence.py --quick      # 400 cases

The snapshot is hashes only (``dev/logs/cga_reference.json``), so it can be
taken once from the pipeline and checked against long after the pipeline is
gone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "dev" / "harness"))

from fuzz import build_cases  # noqa: E402

from buildings.ir.serial import to_json  # noqa: E402
from buildings.site import SiteContext  # noqa: E402

REFERENCE = ROOT / "dev" / "logs" / "cga_reference.json"


def _strip(obj, *, root: bool):
    """The JSON tree with traces removed (everywhere, or only on the root)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "trace" and (root or obj.get("kind") == "building"):
                continue
            out[k] = _strip(v, root=root)
        return out
    if isinstance(obj, list):
        return [_strip(v, root=root) for v in obj]
    return obj


def fingerprints(root) -> tuple[str, str]:
    tree = json.loads(to_json(root))
    geom = json.dumps(_strip(tree, root=True), sort_keys=True)
    full = json.dumps(_strip(tree, root=False), sort_keys=True)
    return (
        hashlib.sha256(geom.encode()).hexdigest()[:20],
        hashlib.sha256(full.encode()).hexdigest()[:20],
    )


def site_of(case) -> SiteContext:
    return SiteContext(
        street_width=case.street_width,
        parcel_width=case.parcel_width,
        parcel_depth=case.parcel_depth,
        year=case.year,
        klass=case.klass,
        ground=case.ground,
        corner=case.corner,
        seed=case.seed,
    )


def run(generator, cases) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for case in cases:
        try:
            root, _ = generator(site_of(case))
            out[str(case.index)] = list(fingerprints(root))
        except Exception as exc:  # a refusal is part of the behaviour
            out[str(case.index)] = [f"raised:{type(exc).__name__}"] * 2
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument(
        "--pipeline",
        action="store_true",
        help="compare the phase pipeline itself (a refactor guard), not the grammar",
    )
    args = ap.parse_args(argv)

    cases = build_cases(75)
    if args.quick:
        cases = cases[::7]

    t0 = time.time()
    if args.snapshot:
        from buildings.typologies.paris.generate import generate

        ref = run(generate, cases)
        REFERENCE.write_text(json.dumps(ref, indent=0, sort_keys=True))
        print(f"snapshot: {len(ref)} cases in {time.time() - t0:.0f}s -> {REFERENCE}")
        return 0

    if args.pipeline:
        from buildings.typologies.paris.generate import generate as generate_cga
    else:
        from buildings.typologies.paris.grammar import generate_cga

    ref = json.loads(REFERENCE.read_text())
    got = run(generate_cga, cases)
    geom_bad = [k for k in got if got[k][0] != ref[k][0]]
    full_bad = [k for k in got if got[k][1] != ref[k][1]]
    raised = sum(1 for v in got.values() if v[0].startswith("raised:"))
    print(
        f"{len(got)} cases in {time.time() - t0:.0f}s ({raised} refused): "
        f"geometry differs on {len(geom_bad)}, traces below the root differ on {len(full_bad)}"
    )
    for k in (geom_bad or full_bad)[:10]:
        print(f"  case {k}: reference {ref[k]} grammar {got[k]}")
    return 1 if geom_bad or full_bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
