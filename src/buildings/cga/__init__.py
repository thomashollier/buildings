"""A split-grammar engine: shapes with scopes, productions that split them,
layered attribute rules, and an interpretation pass that writes IR.

Nothing in this package knows about Paris. A typology supplies a ``Grammar``
-- see ``typologies/paris/grammar.py`` -- and this package derives it.
"""

from buildings.cga.derive import (
    Derivation,
    Grammar,
    OutsideParent,
    SplitMismatch,
    derive,
    interpret,
)
from buildings.cga.rules import (
    Attrs,
    AttributeStage,
    Candidate,
    Layer,
    Production,
    ProductionConflict,
    RuleConflict,
    ScopedLayer,
    everywhere,
    resolve_layers,
    under,
)
from buildings.cga.shape import X, Y, Attributes, LockedAttributes, Part, Scope, Shape
from buildings.cga.lsystem import GrowConflict, GrowError, LSystem, grow

__all__ = [
    "Attrs",
    "Attributes",
    "AttributeStage",
    "Candidate",
    "Derivation",
    "Grammar",
    "GrowConflict",
    "GrowError",
    "LSystem",
    "grow",
    "Layer",
    "LockedAttributes",
    "OutsideParent",
    "Part",
    "Production",
    "ProductionConflict",
    "RuleConflict",
    "ScopedLayer",
    "Scope",
    "Shape",
    "SplitMismatch",
    "X",
    "Y",
    "derive",
    "everywhere",
    "under",
    "interpret",
    "resolve_layers",
]
