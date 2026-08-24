#!/usr/bin/env python3
"""Guard: the renderer decides nothing arguable.

From the brief — "if a renderer is deciding anything a person could argue about,
that decision is in the wrong place."  Concretely the renderer may not branch on
date, class, or role: those are qualification decisions and belong upstream in
the IR.  The renderer reads geometry and kind, and draws.

Also: the renderer does not invent proportion arithmetic. A dimension read from
the IR (x, y, w, h, or spans calculated from them) may not be divided or multiplied
by a literal and used to decide how many of something to draw. That is a proportion
decision and it belongs in qualification — the count should come from the IR, not
from the renderer dividing a bay width by a magic spacing constant.

Exit 0 = clean. Exit 1 = violations found.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "src" / "buildings" / "render"

# Names that, if tested against in the renderer, mean an arguable decision
# has leaked downstream.
FORBIDDEN = {
    "year", "date", "era", "period",
    "klass", "class_", "building_class", "wealth", "richness",
    "role", "floor_type", "storey_role",
    "street_width", "prevalence", "variant",
}
FORBIDDEN_ENUMS = {"Role", "BuildingClass", "Era", "Period", "FloorType"}


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[int, str, str]] = []

    def _names(self, node: ast.AST) -> set[str]:
        out: set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                out.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                out.add(sub.attr)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                out.add(sub.value)
        return out

    def _check(self, node: ast.AST, lineno: int, what: str) -> None:
        names = self._names(node)
        hit = (names & FORBIDDEN) | (names & FORBIDDEN_ENUMS)
        if hit:
            self.violations.append(
                (lineno, what, f"{sorted(hit)} in {ast.unparse(node)[:90]}")
            )

    def visit_If(self, node: ast.If) -> None:
        self._check(node.test, node.lineno, "if")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self._check(node, node.lineno, "compare")
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._check(node.test, node.lineno, "ternary")
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self._check(node.subject, node.lineno, "match")
        self.generic_visit(node)


class ProportionChecker(ast.NodeVisitor):
    """Catch renderer-side proportion arithmetic.

    The offence: take a dimension that came from the IR, divide or multiply it by
    a number the renderer chose, and use the result to decide HOW MANY of
    something to draw.  That is a proportion decision — a person can argue about
    it — so it belongs in qualification, and the count should arrive in the IR.

    Three waves of review each found a different spelling of this:
      A4.3  ornament_weight = _num(props,'richness',0.5); if ornament_weight >= 0.7
      A5.2  n = max(2, int(w / 1.4))          mullions at 1.5 m over 3.45 m bays
      A6.11 spacing = 0.5; n = max(1, int(w / spacing))    modillions

    So this checks the CLASS, not one spelling.  It runs a small taint analysis
    per function:

      * a value is DIMENSIONAL if it comes from IR geometry — a name like w/h/
        span/bay_width, a props read of a geometry key, or anything derived from one
      * a value is CHOSEN-HERE if it is a numeric literal written in this file, or
        a local bound to one (including through a ternary)
      * dimensional / chosen-here  ->  the result is a PROPORTION
      * a proportion reaching int(), round(), ceil(), floor() or range() is a count,
        and that is the violation

    Dividing by something that came from the IR is fine — that is the renderer
    obeying a stated limit rather than inventing one.  So is arithmetic that never
    becomes a count: stroke widths, metres-to-pixels, centring, clamping.
    """

    _COUNT_CALLS = {"int", "round", "ceil", "floor", "range"}
    _GEOMETRY_KEYS = {
        "x", "y", "w", "h", "width", "height", "span", "extent",
        "eaves_height", "cornice_height", "projection",
    }
    _DIM_NAMES = {"x", "y", "w", "h", "width", "height", "span", "extent", "dx", "dy"}
    _DIM_SUFFIXES = ("_x", "_y", "_w", "_h", "_width", "_height", "_span", "_extent")
    _DIM_PREFIXES = ("bay_", "storey_", "opening_", "span_", "facade_", "parcel_",
                     "slot_", "roof_", "chamfer_", "block_")
    # Never a magic multiplier: loop variables and counts already decided elsewhere.
    _NOT_MAGIC = {"i", "j", "k", "idx", "index", "n", "count", "cols", "rows", "steps"}

    def __init__(self) -> None:
        self.violations: list[tuple[int, str, str]] = []
        self._dim: set[str] = set()        # locals holding a dimension
        self._chosen: set[str] = set()     # locals holding a literal chosen here
        self._prop: set[str] = set()       # locals holding a proportion
        self._from_ir: set[str] = set()    # locals read out of the IR

    # -- scope ---------------------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        saved = (self._dim, self._chosen, self._prop, self._from_ir)
        self._dim, self._chosen, self._prop, self._from_ir = set(), set(), set(), set()
        for arg in list(node.args.args) + list(node.args.kwonlyargs):
            if self._name_looks_dimensional(arg.arg):
                self._dim.add(arg.arg)
        self.generic_visit(node)
        self._dim, self._chosen, self._prop, self._from_ir = saved

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)
        # `spacing = 0.5` and `course_w, course_h = 0.9, 0.32` are the same move.
        pairs: list[tuple[str, ast.expr]] = []
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                pairs.append((tgt.id, node.value))
            elif isinstance(tgt, ast.Tuple) and isinstance(node.value, ast.Tuple) \
                    and len(tgt.elts) == len(node.value.elts):
                for t_el, v_el in zip(tgt.elts, node.value.elts):
                    if isinstance(t_el, ast.Name):
                        pairs.append((t_el.id, v_el))
        if not pairs:
            return
        for name, value in pairs:
            self._dim.discard(name); self._chosen.discard(name)
            self._prop.discard(name); self._from_ir.discard(name)
            if self._is_from_ir(value):
                self._from_ir.add(name)
                if self._is_dimensional(value):
                    self._dim.add(name)
            elif self._is_proportion(value):
                self._prop.add(name)
            elif self._is_chosen_here(value):
                self._chosen.add(name)
            elif self._is_dimensional(value):
                self._dim.add(name)

    # -- the check -----------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        if self._func_name(node.func) in self._COUNT_CALLS:
            for arg in node.args:
                found = self._find_proportion(arg)
                if found is not None:
                    self.violations.append((
                        node.lineno,
                        "proportion arithmetic",
                        f"count decided from a dimension and a number chosen here: "
                        f"{ast.unparse(found)[:80]}",
                    ))
                    break
        self.generic_visit(node)

    def _find_proportion(self, node: ast.expr) -> ast.expr | None:
        """The proportion may be nested inside max(), a sum, or a local."""
        for sub in ast.walk(node):
            if isinstance(sub, ast.BinOp) and isinstance(sub.op, (ast.Div, ast.Mult, ast.FloorDiv)):
                if self._is_proportion(sub):
                    return sub
            elif isinstance(sub, ast.Name) and sub.id in self._prop:
                return sub
        return None

    def _is_proportion(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self._prop
        if not (isinstance(node, ast.BinOp)
                and isinstance(node.op, (ast.Div, ast.Mult, ast.FloorDiv))):
            return False
        l, r = node.left, node.right
        # Dividing a dimension by a limit the IR stated is the renderer OBEYING a
        # stated limit, not inventing one — so the exemption applies to the other
        # operand only.  `_num(props,'w') / 0.25` is still the offence: the
        # dividend coming from the IR is exactly what makes it a dimension.
        if self._is_dimensional(l) and self._is_from_ir(r) and not self._is_chosen_here(r):
            return False
        if self._is_dimensional(r) and self._is_from_ir(l) and not self._is_chosen_here(l):
            return False
        return ((self._is_dimensional(l) and self._is_chosen_here(r))
                or (self._is_dimensional(r) and self._is_chosen_here(l)))

    # -- classifiers ---------------------------------------------------------
    def _name_looks_dimensional(self, name: str) -> bool:
        return (name in self._DIM_NAMES
                or name.endswith(self._DIM_SUFFIXES)
                or name.startswith(self._DIM_PREFIXES))

    def _is_dimensional(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self._dim or self._name_looks_dimensional(node.id)
        if isinstance(node, ast.Attribute):
            return self._name_looks_dimensional(node.attr)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            return node.slice.value in self._GEOMETRY_KEYS
        if isinstance(node, ast.Call):
            # _num(props, 'w') / props.get('w') — a geometry key read out of the IR
            for a in node.args:
                if isinstance(a, ast.Constant) and a.value in self._GEOMETRY_KEYS:
                    return True
            return False
        if isinstance(node, ast.BinOp):          # w - 2*inset is still a dimension
            return self._is_dimensional(node.left) or self._is_dimensional(node.right)
        if isinstance(node, ast.IfExp):
            return self._is_dimensional(node.body) or self._is_dimensional(node.orelse)
        return False

    def _is_from_ir(self, node: ast.expr) -> bool:
        """A value the IR stated — a props read, or a local bound to one."""
        if isinstance(node, ast.Name):
            return node.id in self._from_ir
        if isinstance(node, ast.Subscript):
            src = ast.unparse(node.value).lower()
            return "props" in src or "node" in src
        if isinstance(node, ast.Call):
            src = ast.unparse(node.func).lower()
            if src.endswith(".get") and "props" in src:
                return True
            if self._func_name(node.func) in {"_num", "_prop", "_get", "_str", "_flag"}:
                return True
        return False

    def _is_chosen_here(self, node: ast.expr) -> bool:
        """A number written in this file, however it is dressed up."""
        if isinstance(node, ast.Constant):
            return isinstance(node.value, (int, float)) and node.value not in (0, 1)
        if isinstance(node, ast.UnaryOp):
            return self._is_chosen_here(node.operand)
        if isinstance(node, ast.IfExp):          # (0.6 if zinc else 1.3)
            return self._is_chosen_here(node.body) or self._is_chosen_here(node.orelse)
        if isinstance(node, ast.Name):
            if node.id in self._NOT_MAGIC or node.id in self._from_ir:
                return False
            if node.id in self._dim:
                return False
            return node.id in self._chosen or node.id.isupper()
        return False

    def _func_name(self, func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == "math":
                return func.attr
            return func.attr
        return None


def main() -> int:
    if not RENDER.exists():
        print(f"check_renderer_dumb: {RENDER} does not exist yet — skipping")
        return 0

    total = 0
    for path in sorted(RENDER.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"FAIL {rel}: syntax error: {exc}")
            total += 1
            continue

        # Check for branching on upstream facts
        v = Visitor()
        v.visit(tree)
        seen: set[tuple[int, str]] = set()
        for lineno, what, detail in v.violations:
            if (lineno, what) in seen:
                continue
            seen.add((lineno, what))
            print(f"FAIL {rel}:{lineno}: renderer {what} on upstream fact: {detail}")
            total += 1

        # Check for proportion arithmetic
        pc = ProportionChecker()
        pc.visit(tree)
        seen_prop: set[tuple[int, str]] = set()
        for lineno, what, detail in pc.violations:
            if (lineno, what) in seen_prop:
                continue
            seen_prop.add((lineno, what))
            print(f"FAIL {rel}:{lineno}: renderer {what}: {detail}")
            total += 1

    if total:
        print(f"\n{total} renderer-decision violation(s). "
              f"Move the decision into qualification and put the result in the IR.")
        return 1
    print("check_renderer_dumb: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
