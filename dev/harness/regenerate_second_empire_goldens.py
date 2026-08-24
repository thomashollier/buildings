#!/usr/bin/env python3
"""Deliberately regenerate the Second Empire golden-master fixtures.

``tests/golden/test_second_empire_canonical.py`` pins four canonical Second
Empire situations (``tests/golden/situations.py``) against serialised IR
fixtures in ``tests/golden/data/*.json``. This script is the other
documented way to update them (the test module's own
``UPDATE_SECOND_EMPIRE_GOLDENS=1`` env var is the first) — for a reviewer who
wants to regenerate without invoking pytest at all.

Either way the update is a **visible, reviewed act**: this script always
prints exactly what it wrote and where, and it never runs silently as part of
any other command. Diff (or at minimum read) every rewritten file before
committing it — a golden master that gets rewritten unread is not a golden
master, it is a mirror.

Run:  python3 dev/harness/regenerate_second_empire_goldens.py [name ...]

With no arguments, regenerates all four canonical fixtures. With one or more
names, regenerates only those (see ``tests/golden/situations.py`` for the
valid names) — useful when only one situation's output was meant to change
and a reviewer wants the diff confined to it.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "golden"))

from buildings.ir.serial import to_json  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402
from situations import SITUATIONS  # noqa: E402

DATA_DIR = ROOT / "tests" / "golden" / "data"


def main(argv: list[str]) -> int:
    names = argv or sorted(SITUATIONS)
    unknown = [n for n in names if n not in SITUATIONS]
    if unknown:
        print(f"unknown situation name(s): {unknown}", file=sys.stderr)
        print(f"known: {sorted(SITUATIONS)}", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in names:
        site = SITUATIONS[name]
        building, _log = generate(site)
        path = DATA_DIR / f"{name}.json"
        path.write_text(to_json(building) + "\n")
        print(f"wrote {path}  ({site.klass.value}, {site.street_width:.1f} m street, "
              f"{site.ground.value} ground, corner={site.corner}, seed={site.seed})")

    print(
        f"\n{len(names)} fixture(s) rewritten from the current generator output. "
        "This is a deliberate update, not a verified one -- diff the fixtures "
        "before committing, then run `python -m pytest tests/golden/"
        "test_second_empire_canonical.py` (without the env var) to confirm they "
        "now match."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
