"""The end-to-end assembly: a situation in, one building and its trace out.

This is the whole pipeline in one function, and it is deliberately thin. Every
decision already belongs to a phase; ``generate`` only hands each phase the
frozen output of the last and staples the results into a single tree.

```
SiteContext ─▶ [1 STRUCTURE] ─▶ Grid ─▶ [2 ROLES] ─▶ RoledGrid
                                                        │
                                          [3 QUALIFICATION + 4 COMPOSITION]
                                                        │
                                                        ▼
                                              [5 TERMINATION] ─▶ BuildingNode
```

### Strictly backwards (I1)

Each arrow is one-way, and the type system does most of the enforcing: ``Grid``,
``RoledGrid``, ``QualContext``, ``Properties`` and every ``Node`` are frozen, and
``Node.props`` / ``TraceEntry.inputs`` are frozen mappings rather than dicts, so
a later phase cannot reach back and edit what an earlier one read even by
accident. The remaining discipline is this function's: it never passes a phase
anything a later phase produced. ``terminate`` gets ``grid`` and ``roled`` — the
same objects qualification was given, not something qualification returned — so
if qualification were deleted tomorrow the comble would be identical.

The one thing shared across phases is the ``DecisionStream``, and it is shared
on purpose: it is addressable, not sequential. Qualification draws on
``"facade/ironwork/variant"`` and termination on ``"roof/dormers/variant"``, and
because each path's state is derived from ``(seed, path)`` alone, adding a
decision to one phase cannot shift a decision in the other (I5).

### The trace is the deliverable

The brief's first-week acceptance is "one real building's elevation end to end
through all four phases, with a trace explaining every element". So the building
node returned here carries the *structure* and *roles* phases' reasoning as well
as qualification's — those two phases emit no nodes of their own, and without
this their account would be discarded the moment the grid was consumed, leaving
"why is this storey 4.08 m tall?" unanswerable from the IR alone. Everything a
``TraceLog`` holds is also on the nodes themselves, so a serialised tree with no
generator attached can still answer the question.

``dev/harness/first_building.py`` is that acceptance run as a script.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Sequence

from buildings.ir.nodes import BuildingNode, Node
from buildings.rng import DecisionStream
from buildings.site import SiteContext
from buildings.trace import TraceEntry, TraceLog
from buildings.typologies.paris.compose import Layer, explain, find_node, qualify_from_grid
from buildings.typologies.paris.roles import RoledGrid, assign_roles
from buildings.typologies.paris.structure import Grid, solve_structure
from buildings.typologies.paris.terminate import terminate

__all__ = ["generate", "explain", "find_node", "walk"]


# ``BlockDatums`` lives in ``buildings.block``, which S9 has not built yet.
# ``from __future__ import annotations`` makes every annotation in this file a
# string that is never evaluated (PEP 563), so the signature below is legal
# today; at runtime ``datums`` is only forwarded to ``solve_structure``, which
# reads it by plain attribute access. Same arrangement as ``structure.py``.


def walk(node: Node):
    """Every node in the tree, depth-first, parents before children."""
    yield node
    for child in node.children:
        yield from walk(child)


def _structure_entries(site: SiteContext, grid: Grid) -> tuple[TraceEntry, ...]:
    """The structure phase's reasoning, kept on the building it produced.

    ``Grid.account`` is the solver's own step-by-step record — the absorption
    ladder, the taper, the porte cochère — and it is the only place the
    building's *dimensions* are explained. It is preserved verbatim rather than
    summarised: a paraphrase would be a second opinion about what the solver
    did, and the point of an account is that it is not one.
    """
    ceiling = float(grid.cornice_height)
    built = grid.built_height
    return (
        TraceEntry(
            rule="paris.structure.solve_structure",
            phase="structure",
            detail=(
                f"legal cornice ceiling {ceiling:.2f} m for a {grid.envelope.street_width:.2f} m "
                f"street; built to {built:.2f} m ({built / ceiling:.0%} of it) — the law says "
                f"how tall you may build, programme and money say how tall you did.\n"
                + "\n".join(f"  · {line}" for line in grid.account)
            ),
            inputs={
                "street_width": grid.envelope.street_width,
                "legal_cornice_ceiling": ceiling,
                "cornice_citation": grid.cornice_height.why,
                "built_height": round(built, 6),
                "storey_count": len(grid.storeys),
                "bay_slot_count": len(grid.bays),
                "envelope": grid.envelope.roof_envelope.value,
            },
        ),
    )


def _roles_entries(roled: RoledGrid) -> tuple[TraceEntry, ...]:
    """The roles phase's reasoning: which slot became what, and why it could
    only have been that one."""
    stack = ", ".join(
        f"{s.index_from_bottom}:{s.role.value}@{s.slot.start:.2f}m×{s.slot.width:.2f}m"
        f"(rank {s.rank_from_principal:+d})"
        for s in roled.storeys
    )
    principal = next((s for s in roled.storeys if s.rank_from_principal == 0), None)
    return (
        TraceEntry(
            rule="paris.roles.assign_roles",
            phase="roles",
            detail=(
                f"identity derived from the stack, never declared — {stack}. "
                + (
                    f"The principal floor is index {principal.index_from_bottom} because it is "
                    f"the tallest habitable slot ({principal.slot.width:.2f} m) above the base "
                    f"and the mezzanine; the base exclusion is what stops the "
                    f"{roled.storeys[0].slot.width:.2f} m ground floor taking the title."
                    if principal is not None
                    else "No slot qualified as principal."
                )
            ),
            inputs={
                "roles": tuple(s.role.value for s in roled.storeys),
                "heights": tuple(round(s.slot.width, 4) for s in roled.storeys),
            },
        ),
    )


def generate(
    site: SiteContext,
    datums: BlockDatums | None = None,
    *,
    layers: Sequence[Layer] | None = None,
) -> tuple[BuildingNode, TraceLog]:
    """Situation in; one ``BuildingNode`` tree and its ``TraceLog`` out.

    ``datums``, when given, are the block's handed-down facts — one street
    width and one cornice line for the whole block (I2). They are passed
    straight to the structure phase, which is the only phase entitled to read
    them; nothing downstream re-derives a block fact.

    ``layers`` overrides the qualification rule stack. A user override is a
    ``Layer`` with the highest order and nothing else — there is no parallel
    override channel here either.
    """
    rng = DecisionStream(site.seed)

    # ---- 1. STRUCTURE ----------------------------------------------------
    grid = solve_structure(site, datums)

    # ---- 2. ROLES --------------------------------------------------------
    roled = assign_roles(grid)

    # ---- 3+4. QUALIFICATION, over the composed layers --------------------
    building, log = qualify_from_grid(roled, site, layers=layers, rng=rng)

    # ---- 5. TERMINATION --------------------------------------------------
    # Handed `grid` and `roled` — the frozen output of phases 1 and 2 — and
    # not the qualified tree. The comble is a consequence of the envelope and
    # the storey stack; it is not a consequence of what colour the railings
    # came out.
    silhouette, roofscape = terminate(grid, roled, site, rng)

    # ---- assembly --------------------------------------------------------
    extra: tuple[Node, ...] = (*roofscape, silhouette)
    for node in extra:
        for descendant in walk(node):
            for entry in descendant.trace:
                log.record(descendant.id, entry)

    eaves = grid.built_height
    total_height = float(silhouette.props["ridge_height"])
    facade_w = math.fsum(b.width for b in grid.bays)

    trace = (
        *_structure_entries(site, grid),
        *_roles_entries(roled),
        *building.trace,
    )
    for entry in trace:
        log.record(building.id, entry)

    root = dataclasses.replace(
        building,
        trace=trace,
        children=(*building.children, *extra),
        props={
            **dict(building.props),
            # The building's extent now includes what stands on it, so `h` is
            # the whole silhouette. The stone facade is still readable as
            # `eaves_height`, because "how tall is the facade" and "how tall is
            # the building" are different questions and the pre-1884 comble is
            # the difference between them.
            "h": total_height,
            "w": facade_w,
            "eaves_height": eaves,
            "total_height": total_height,
            "legal_cornice_ceiling": float(grid.cornice_height),
            "legal_total_height": grid.envelope.total_height,
            "envelope": grid.envelope.roof_envelope.value,
            "parcel_depth": site.parcel_depth,
            "ground": site.ground.value,
            "seed": site.seed,
        },
    )
    return root, log
