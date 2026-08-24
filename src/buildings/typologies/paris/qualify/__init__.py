"""Phase 3 — qualification: a read-only context in, sparse properties out.

The package is split by *layer*, not by feature, because the layer is the unit
of composition. Swapping the period bundle for another city's should not
require touching the base vocabulary, and a rule file organised by feature
(``balconies.py``, ``cornices.py``) would put four layers' opinions about a
balcony in one place and make that impossible.

- ``context`` — ``QualContext``, ``Properties``, the property vocabulary, and
  the builder that turns a roled grid into the fact set every rule sees.
- ``base`` — what a Paris frontage is, before date or money.
- ``period`` — the same frontage, dated, via ``chronology``'s date windows.
- ``klass`` — the same frontage, with money in it, via ``scale_for_class``.

The site layer and the layering machinery itself live one level up, in
``buildings.typologies.paris.compose``.
"""

from __future__ import annotations

from buildings.typologies.paris.qualify.context import (
    PROPERTY_KEYS,
    Properties,
    QualContext,
    Rule,
    contexts_for,
    storey_contexts_for,
)

__all__ = [
    "QualContext",
    "Properties",
    "Rule",
    "PROPERTY_KEYS",
    "contexts_for",
    "storey_contexts_for",
]
