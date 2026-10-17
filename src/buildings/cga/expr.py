"""A small, safe expression language for rule files.

Rule files say ``when = "is_bay() and floor != 'parapet'"`` or
``size = "item.h"``. Those strings are Python *expression* syntax, parsed
with ``ast`` and evaluated by a walker that accepts only what a rule needs:

* numbers, strings, booleans, ``None``, lists and tuples;
* arithmetic, comparison, ``and`` / ``or`` / ``not``, ``x if c else y``;
* names, which the caller resolves (a shape's scope, its attributes up the
  tree, the file's parameters, loop variables);
* ``item.h`` and ``item["h"]`` on mappings, ``.x .y .w .h`` on scopes, and
  indexing a list;
* calls to functions the caller hands in, by name, and nothing else;
* f-strings, for descriptions.

No attribute access beyond that, no imports, no lambdas, no comprehensions:
a rule file can compute a number and test a condition, and it cannot reach
into the program running it.
"""

from __future__ import annotations

import ast
import operator
from typing import Any, Callable, Mapping

__all__ = ["Expr", "ExprError"]


class ExprError(ValueError):
    """An expression used syntax a rule may not, or named something unknown."""


_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_CMP = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}
_ALLOWED = (
    ast.Expression, ast.Constant, ast.Name, ast.Load, ast.BinOp, ast.UnaryOp, ast.BoolOp,
    ast.Compare, ast.IfExp, ast.Call, ast.List, ast.Tuple, ast.Subscript, ast.Attribute,
    ast.JoinedStr, ast.FormattedValue, ast.And, ast.Or, ast.Not, ast.USub, ast.UAdd,
    *_BIN, *_CMP,
)
_SCOPE_FIELDS = frozenset({"x", "y", "w", "h"})


class Expr:
    """One parsed expression; call it with a name resolver and functions."""

    __slots__ = ("src", "_tree", "calls")

    def __init__(self, src: str) -> None:
        self.src = src
        try:
            tree = ast.parse(src.strip(), mode="eval")
        except SyntaxError as exc:
            raise ExprError(f"cannot parse {src!r}: {exc.msg}") from exc
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED):
                raise ExprError(f"{type(node).__name__} is not allowed in a rule expression: {src!r}")
            if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
                raise ExprError(f"only named functions may be called: {src!r}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                raise ExprError(f"private attribute {node.attr!r} in {src!r}")
        self._tree = tree.body
        #: Every function this expression calls, so a caller can refuse an
        #: unknown one when the file is loaded rather than when it runs.
        self.calls = frozenset(n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call))

    def __call__(self, lookup: Callable[[str], Any], functions: Mapping[str, Callable[..., Any]]) -> Any:
        return _eval(self._tree, lookup, functions, self.src)

    def __repr__(self) -> str:
        return f"Expr({self.src!r})"


def _eval(node: ast.AST, lookup, functions, src: str) -> Any:
    ev = lambda n: _eval(n, lookup, functions, src)  # noqa: E731
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ("True", "False", "None"):
            return {"True": True, "False": False, "None": None}[node.id]
        return lookup(node.id)
    if isinstance(node, ast.BinOp):
        return _BIN[type(node.op)](ev(node.left), ev(node.right))
    if isinstance(node, ast.UnaryOp):
        v = ev(node.operand)
        return {ast.USub: lambda a: -a, ast.UAdd: lambda a: +a, ast.Not: lambda a: not a}[type(node.op)](v)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = ev(value)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = ev(value)
            if result:
                return result
        return result
    if isinstance(node, ast.Compare):
        left = ev(node.left)
        for op, comp in zip(node.ops, node.comparators):
            right = ev(comp)
            if not _CMP[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        return ev(node.body) if ev(node.test) else ev(node.orelse)
    if isinstance(node, ast.Call):
        fn = functions.get(node.func.id)
        if fn is None:
            raise ExprError(f"unknown function {node.func.id!r} in {src!r}")
        return fn(*[ev(a) for a in node.args])
    if isinstance(node, ast.List):
        return [ev(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(ev(e) for e in node.elts)
    if isinstance(node, ast.Subscript):
        return ev(node.value)[ev(node.slice)]
    if isinstance(node, ast.Attribute):
        value = ev(node.value)
        if isinstance(value, Mapping):
            return value[node.attr]
        if node.attr in _SCOPE_FIELDS and hasattr(value, node.attr):
            return getattr(value, node.attr)
        raise ExprError(f"cannot read .{node.attr} of {type(value).__name__} in {src!r}")
    if isinstance(node, ast.JoinedStr):
        return "".join(ev(v) if not isinstance(v, ast.Constant) else v.value for v in node.values)
    if isinstance(node, ast.FormattedValue):
        value = ev(node.value)
        spec = ev(node.format_spec) if node.format_spec is not None else ""
        return format(value, spec)
    raise ExprError(f"cannot evaluate {type(node).__name__} in {src!r}")  # pragma: no cover
