#!/usr/bin/env python3
"""Guard: no rule outside reglement.py may branch on a period/era enum.

The brief is explicit — "the moment a rule reads `period == SECOND_EMPIRE` the
enum is back and the straggler building has become unrepresentable."  Chronology
must be expressed as date windows on feature variants, never as a period test.

`reglement.py` is exempt: regulation genuinely IS a step function on decree
dates, and Era there is the documented hinge set (1859/1884/1902).

Exit 0 = clean. Exit 1 = violations found.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "buildings"

# Files where comparing against an era/period enum is legitimate.
EXEMPT = {
    "typologies/paris/reglement.py",   # the ported regulatory core
    "typologies/paris/reglement_adapter.py",
}

PERIOD_NAMES = {"era", "period", "epoch", "style_period"}
PERIOD_ENUMS = {"Era", "Period", "StylePeriod"}


class Visitor(ast.NodeVisitor):
    def __init__(self, relpath: str) -> None:
        self.relpath = relpath
        self.violations: list[tuple[int, str]] = []

    def _names(self, node: ast.AST) -> set[str]:
        out: set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                out.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                out.add(sub.attr)
        return out

    def visit_Compare(self, node: ast.Compare) -> None:
        names = self._names(node)
        lowered = {n.lower() for n in names}
        if (lowered & PERIOD_NAMES) or (names & PERIOD_ENUMS):
            if any(isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn))
                   for op in node.ops):
                self.violations.append(
                    (node.lineno, ast.unparse(node)[:100])
                )
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        names = {n.lower() for n in self._names(node.subject)}
        if names & PERIOD_NAMES:
            self.violations.append(
                (node.lineno, f"match on {ast.unparse(node.subject)[:60]}")
            )
        self.generic_visit(node)


def main() -> int:
    if not SRC.exists():
        print(f"check_no_period_branching: {SRC} does not exist yet — skipping")
        return 0

    total = 0
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        if rel in EXEMPT:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"FAIL {rel}: syntax error: {exc}")
            total += 1
            continue
        v = Visitor(rel)
        v.visit(tree)
        for lineno, snippet in v.violations:
            print(f"FAIL {rel}:{lineno}: period-enum branching: {snippet}")
            total += 1

    if total:
        print(f"\n{total} period-branching violation(s). "
              f"Use chronology date windows instead.")
        return 1
    print("check_no_period_branching: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
