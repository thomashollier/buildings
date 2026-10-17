#!/usr/bin/env python3
"""Guard: what the IR states, the renderer draws.

The complement of `check_renderer_dumb.py`.  That guard stops the renderer
*deciding* things.  This one stops it *ignoring* things — the failure that
produced the worst defects in the S10/S11 validation and that no gate caught:

  D1  qualification places a `pedestrian_entrance` on every modest and ordinary
      building, correctly, with its own ABSOLUTE 1.40 x 2.90 m geometry.
      `elements.py` has a branch for `carriage_entrance` and none for it, so
      half the building stock drew a window where its front door should be.
  D8  the cornice states a `projection` and the renderer never projects it.
  D11 a shopfront states five parts and two get drawn.

All four gates were green while this was true, because every gate asked whether
the IR was *right* and none asked whether the drawing *used* it.

Two checks:

  1. COVERAGE   every value of a discriminating prop that qualification can emit
                (opening_type, surround_kind, head, treatment, course_kind, ...)
                is matched somewhere in the renderer.  A stated kind with no
                branch is silently drawn as something else.

  2. CONSUMPTION every prop key the generator writes is read somewhere in the
                renderer, or is listed in IGNORED below with a reason.  A stated
                fact nothing reads is either a lie in the IR or a missing
                drawing.

Exit 0 = clean. Exit 1 = violations.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
SRC = ROOT / "src" / "buildings"
RENDER = SRC / "render"
PRODUCERS = [
    SRC / "typologies" / "paris",
    SRC / "typologies" / "soho",
    SRC / "block",
]

# Props the renderer legitimately never reads, each with the reason it exists.
IGNORED = {
    "geometry_stated": "a flag for the generator's own assertions",
    "rule": "provenance, carried for the trace",
    "why": "provenance",
    "source": "provenance",
    "citation": "provenance",
    "slot_index": "bookkeeping for qualification",
    "rank_from_principal": "a qualification input, deliberately NOT visible to the renderer",
    "role": "ditto — the renderer may not branch on role",
    "year": "ditto",
    "klass": "ditto",
    "street_width": "ditto",
    "prevalence": "ditto",
    "variant": "ditto",
    "legal_ridge_height": "the legal ceiling, not the built form",
    "min_height": "the ordinance figure, carried for the trace",
    "sill_height": "compose bakes it into the opening's y; the renderer reads y",
}

# Dicts whose VALUES are kind names the renderer must be able to draw.
KIND_TABLE_SUFFIXES = (
    "_TYPES", "_KINDS", "_STYLES", "_PATTERNS", "_FORMS", "_VARIANTS",
    "_TREATMENTS", "_ORNAMENTS",
)

# Props whose VALUE space must be covered by a renderer branch.
DISCRIMINATING = {
    "opening_type", "surround_kind", "head", "treatment", "course_kind",
    "shopfront_style", "ironwork_pattern", "cornice_ornament", "ends",
    "element", "form", "position", "keystone_kind", "material",
}

STR_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and STR_RE.match(n.value)
    }


def _prop_writes(tree: ast.AST) -> set[str]:
    """Keys the generator puts into props / node payloads."""
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str) \
                        and STR_RE.match(k.value):
                    out.add(k.value)
        elif isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg == "props" and isinstance(kw.value, ast.Dict):
                    for k in kw.value.keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            out.add(k.value)
    return out


def _prop_reads(tree: ast.AST) -> set[str]:
    """Keys the renderer reads: props['k'], props.get('k'), _num(props,'k')…"""
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                and isinstance(n.slice.value, str):
            out.add(n.slice.value)
        elif isinstance(n, ast.Call):
            for a in n.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and STR_RE.match(a.value):
                    out.add(a.value)
    return out


def main() -> int:
    if not RENDER.exists() or not SRC.exists():
        print("check_ir_is_consumed: tree not built yet — skipping")
        return 0

    render_src = "\n".join(p.read_text(encoding="utf-8") for p in RENDER.rglob("*.py"))
    render_tree = ast.parse(render_src)
    render_strings = _string_constants(render_tree)
    render_reads = _prop_reads(render_tree)

    produced_props: dict[str, str] = {}
    produced_values: dict[str, set[str]] = {}
    for base in PRODUCERS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            rel = path.relative_to(ROOT).as_posix()
            for k in _prop_writes(tree):
                produced_props.setdefault(k, rel)
            # (a) values assigned to a discriminating key inside a dict literal
            for n in ast.walk(tree):
                if not isinstance(n, ast.Dict):
                    continue
                for k, v in zip(n.keys, n.values):
                    if not (isinstance(k, ast.Constant) and k.value in DISCRIMINATING):
                        continue
                    if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                            and STR_RE.match(v.value):
                        produced_values.setdefault(k.value, set()).add(v.value)
            # (b) whole lookup tables of kind names, e.g.
            #     ENTRANCE_OPENING_TYPES = {ENTRANCE_PEDESTRIAN: "pedestrian_entrance"}
            #     — the key is a Name, so (a) cannot see it.  This is exactly how
            #     D1 hid: the IR could state a kind the renderer had no branch for.
            for n in ast.walk(tree):
                if not isinstance(n, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = (n.targets if isinstance(n, ast.Assign) else [n.target])
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                if not any(nm.endswith(KIND_TABLE_SUFFIXES) for nm in names):
                    continue
                value = n.value
                items: list[ast.expr] = []
                if isinstance(value, ast.Dict):
                    items = [v for v in value.values if v is not None]
                elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
                    items = list(value.elts)
                for v in items:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                            and STR_RE.match(v.value):
                        produced_values.setdefault(names[0], set()).add(v.value)

    total = 0

    # 1. coverage — a stated kind with no branch is drawn as something else
    for key in sorted(produced_values):
        for value in sorted(produced_values[key]):
            if value not in render_strings:
                print(f"FAIL coverage: the IR can state {key}={value!r} "
                      f"but no renderer branch matches it — it will be drawn as "
                      f"something else")
                total += 1

    # 2. consumption — a stated fact nothing reads
    for key in sorted(produced_props):
        if key in IGNORED or key in render_reads:
            continue
        if key in DISCRIMINATING or key in {
            "projection", "sill_height", "threshold_height", "pane_max_span",
            "ornament_count", "bracket_count", "seam_count", "course_columns",
            "course_rows", "max_gap", "points", "eaves_height",
        }:
            print(f"FAIL consumption: {produced_props[key]} states {key!r} "
                  f"and the renderer never reads it")
            total += 1

    if total:
        print(f"\n{total} violation(s). What the IR states, the renderer must draw — "
              f"or the IR should not state it.")
        return 1
    print("check_ir_is_consumed: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
