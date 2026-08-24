"""Phase 4 — composition by layering, and the emission of the qualified facade.

Four things live here, in this order:

1. ``Layer`` and ``resolve`` — the layering machinery itself. Base vocabulary,
   then period, then class, then site, then whatever the user overrode. Later
   layers win; specificity breaks ties *within* a layer; **equal order and
   equal specificity is a conflict and raises**.
2. The site layer's own rules. CONTRACTS.md gave S6 four rule files
   (``base``, ``period``, ``klass``, and the context) and no ``site`` module,
   so the two site rules live next to the layer assembly they belong to rather
   than being smuggled into a file named for something else.
3. ``qualify_building`` — walking the resolved grid and emitting IR nodes,
   every one of them carrying the rules that produced it (I4).
4. ``explain`` — the "why is this here?" path, in prose a human reads.

### Why raise on a tie

Silent tie-breaking is how a rule system becomes unbeatable to debug. Two
rules at the same order and the same specificity both claiming
``opening_type`` is not a near-miss to be resolved by declaration order or by
``dict`` insertion order — it is an author who has not decided which rule is
the more specific one, and the only useful thing the machine can do is say so,
name both rules, and stop. The brief's warning about this design is precisely
that it "presents as nondeterminism"; a raised exception with two rule ids in
it is the cheapest possible cure.

### What this phase composes, and what it does not (A2.1)

A facade is stone. Since A2.1 the storey stack can carry a slot standing
*inside the comble* — the chambres de bonne — and that slot has no stone
frontage at all: it is walled by the roof and lit by the lucarnes the
termination phase puts on it. So ``qualify_from_grid`` emits it as a storey of
the building and composes nothing on it. Left to the ordinary path it produced
a full-width window wall, with surrounds, keystones, a balcon filant and its
ironwork, in exactly the volume the roof node occupies and lit a second time by
the dormers over it.

That test is deliberately *not* a rule in the layer stack. A rule can be
overruled by a later layer, and "there is no stone here" is not a taste a class
or a period is entitled to disagree with — it is the geometric fact
``Grid.stands_in_the_roof`` answers and ``roles.py`` turns into ``ATTIC``, read
once, by the phase that decides what gets emitted at all.

### The one thing this phase asserts about the building (A6.1)

Emission is otherwise a transcription: whatever the rules resolved is what
gets emitted, and this file has no opinions. There is exactly one exception,
and it is ``_assert_one_entrance``. Every Paris immeuble has a way in, and a
facade with none is well-formed, fully traced, inside its gabarit and wrong —
the defect survived nine stages and a whole block of ten buildings precisely
because no geometric check asks "can anybody get in?". So this phase counts
the entrances it emitted and raises if the answer is not one.

### Why layers restate rather than patch

A rule reads the context and nothing else — never another rule's output (I1,
phases read strictly backwards, and within a phase rules are unordered by
construction). So a later layer that wants a *different* ornament density does
not multiply the base layer's answer; it computes its own from the same shared
relation (``base.ornament_for_rank``). That is a real cost — the expression is
written twice — and it is the price of the property being resolvable without
knowing which rules ran, in which order, and whether any of them was skipped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from buildings.ir.nodes import (
    BalconyNode,
    BayNode,
    BuildingNode,
    CorniceNode,
    IronworkNode,
    KeystoneNode,
    Node,
    OpeningNode,
    ShopfrontNode,
    SocleNode,
    StoreyNode,
    StringCourseNode,
    SurroundNode,
)
from buildings.rng import DecisionStream
from buildings.site import SiteContext
from buildings.trace import RuleId, TraceEntry, TraceLog
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.reglement_adapter import era_for_year, get_reglement
from buildings.typologies.paris.roles import RoledGrid, assign_roles
from buildings.typologies.paris.structure import solve_structure
from buildings.typologies.paris.qualify.base import (
    BASE_RULES,
    SPEC_EXACT,
    SPEC_ROLE,
)
from buildings.typologies.paris.qualify.context import (
    Properties,
    QualContext,
    Rule,
    contexts_for,
)
from buildings.typologies.paris.qualify.klass import CLASS_RULES
from buildings.typologies.paris.qualify.period import PERIOD_RULES

__all__ = [
    "Layer",
    "Candidate",
    "Resolution",
    "RuleConflict",
    "NoEntrance",
    "resolve",
    "SITE_RULES",
    "paris_layers",
    "qualify_building",
    "qualify_from_grid",
    "explain",
    "find_node",
]

_EPS = 1e-9

#: A4.3 — the ornament tier is a composition decision, not a rendering one.
#: INFERRED, same status as the other unmeasured constants in this file: the
#: *direction* (richer cornices get modillions) is what the brief asks for;
#: nobody has measured the exact crossover.
_CORNICE_MODILLION_THRESHOLD = 0.7

#: The layer orders. Spaced by ten so a bundle can be slipped between two of
#: them without renumbering the rest.
ORDER_BASE = 0
ORDER_PERIOD = 10
ORDER_CLASS = 20
ORDER_SITE = 30
ORDER_OVERRIDE = 40


# ===========================================================================
# 1. The layering machinery
# ===========================================================================


@dataclass(frozen=True)
class Layer:
    """One rule set, and where it sits in the stack.

    A user override is a ``Layer`` like any other, with the highest ``order``.
    There is deliberately no second mechanism for overriding: a parallel
    "force this value" channel would sit outside the trace and outside the
    conflict check, which is exactly where unexplainable output comes from.
    """

    name: str
    order: int
    rules: tuple[Rule, ...]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Layer.name must be non-empty — it appears in every conflict message")
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True)
class Candidate:
    """One rule's opinion about one property — winners and losers alike.

    Losers are kept. "Which rule *nearly* set this, and why did it lose?" is
    the second question anybody debugging a rule set asks, and answering it
    from a discarded value is impossible.
    """

    key: str
    value: object
    rule: RuleId
    layer: str
    order: int
    specificity: int
    func: object = None  # the rule callable, for its docstring

    @property
    def summary(self) -> str:
        """The rule's own account of itself — its docstring's opening
        paragraph, unwrapped. The first *line* is not enough: a rule whose
        summary wraps would be quoted mid-sentence in every trace it appears
        in, which is precisely the sort of small illegibility that makes
        people stop reading the trace."""
        doc = getattr(self.func, "__doc__", None)
        if not doc:
            return ""
        lines: list[str] = []
        for raw in doc.strip().splitlines():
            line = raw.strip()
            if not line:
                break
            lines.append(line)
        return " ".join(lines)


class RuleConflict(Exception):
    """Two rules at the same order and specificity claimed one property.

    Never resolved by picking; always raised. The message names the property,
    every tied rule, and its layer, because that is the whole content of the
    fix: one of them must be made more specific, or they must be merged.
    """


@dataclass(frozen=True)
class Resolution(Properties):
    """The result of layering: values, plus who won each of them and who lost.

    A ``Properties`` in its own right, so it satisfies the frozen contract's
    ``resolve(...) -> Properties`` signature and can be handed anywhere a
    rule's output can. ``rule`` is the resolver itself; the per-property
    authorship — which is what I4 actually needs — is in ``provenance``.
    """

    winners: Mapping[str, Candidate] = field(default_factory=dict)
    candidates: tuple[Candidate, ...] = ()

    def __post_init__(self) -> None:
        Properties.__post_init__(self)
        object.__setattr__(self, "winners", dict(self.winners))
        object.__setattr__(self, "candidates", tuple(self.candidates))

    @property
    def provenance(self) -> Mapping[str, RuleId]:
        """Property key -> the ``RuleId`` that produced its surviving value."""
        return {k: c.rule for k, c in self.winners.items()}

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def why(self, key: str) -> str:
        """Human-readable account of one property: the winner, and the field."""
        if key not in self.winners:
            others = ", ".join(sorted(self.values)) or "(nothing)"
            return f"{key}: no rule had an opinion. Resolved keys: {others}"
        win = self.winners[key]
        lines = [
            f"{key} = {win.value!r}",
            f"  set by {win.rule}",
            f"    layer {win.layer!r} (order {win.order}), specificity {win.specificity}",
        ]
        if win.summary:
            lines.append(f"    {win.summary}")
        losers = [c for c in self.candidates if c.key == key and c is not win]
        if losers:
            lines.append("  overruled:")
            for c in sorted(losers, key=lambda c: (-c.order, -c.specificity)):
                lines.append(
                    f"    {c.rule} -> {c.value!r} "
                    f"(layer {c.layer!r} order {c.order}, specificity {c.specificity})"
                )
        return "\n".join(lines)


def resolve(
    ctx: QualContext, layers: Sequence[Layer], rng: DecisionStream
) -> Resolution:
    """Layer the rule sets over one context cell.

    Later layer wins. Within a layer, higher ``specificity`` wins. Equal order
    AND equal specificity is a CONFLICT — raise, never silently pick.

    Every rule sees the same frozen ``ctx``; none of them sees another's
    output. That is what makes the result independent of the order the rules
    happen to be listed in, and it is checked directly by
    ``test_compose.test_rule_order_within_a_layer_does_not_matter``.
    """
    candidates: list[Candidate] = []
    for layer in sorted(layers, key=lambda ly: ly.order):
        for rule in layer.rules:
            props = rule(ctx, rng)
            if props is None:
                continue
            if not isinstance(props, Properties):
                raise TypeError(
                    f"rule {getattr(rule, '__name__', rule)!r} in layer "
                    f"{layer.name!r} returned {type(props).__name__}; a rule "
                    "returns Properties or None (no opinion)"
                )
            for key, value in props.values.items():
                candidates.append(
                    Candidate(
                        key=key,
                        value=value,
                        rule=props.rule,
                        layer=layer.name,
                        order=layer.order,
                        specificity=props.specificity,
                        func=rule,
                    )
                )

    winners: dict[str, Candidate] = {}
    for key in sorted({c.key for c in candidates}):
        for_key = [c for c in candidates if c.key == key]
        top = max((c.order, c.specificity) for c in for_key)
        tied = [c for c in for_key if (c.order, c.specificity) == top]
        if len(tied) > 1:
            detail = "\n".join(
                f"    {c.rule}  (layer {c.layer!r}, order {c.order}, "
                f"specificity {c.specificity})  ->  {c.value!r}"
                for c in tied
            )
            raise RuleConflict(
                f"property {key!r} was claimed by {len(tied)} rules at the same "
                f"order ({top[0]}) and the same specificity ({top[1]}):\n{detail}\n"
                "  Nothing here is arbitrary enough to break the tie, and picking "
                "one silently would make this facade look nondeterministic. Either "
                "raise the specificity of the rule that is genuinely narrower, or "
                "merge the two into one rule with one id."
            )
        winners[key] = tied[0]

    return Resolution(
        values={k: c.value for k, c in winners.items()},
        rule="paris.compose.resolve",
        specificity=max((c.specificity for c in winners.values()), default=0),
        winners=winners,
        candidates=tuple(candidates),
    )


# ===========================================================================
# 2. The site layer
# ===========================================================================


def corner_earns_emphasis(ctx: QualContext, rng: DecisionStream) -> Properties | None:
    """A corner parcel puts its best surround on the axis of the noble floor.

    This is not corner *treatment* in the block sense — "a corner is its own
    short facade, not a module type", and building that short facade is S9's
    job. It is only the one thing a corner changes about the frontage in hand:
    it is seen from two streets, so the money goes where both see it.

    Applicability: a corner parcel, on the centre bay of the noble floor.
    ``SPEC_EXACT`` — narrower than anything the class layer says about
    surrounds, and in a later layer besides.
    """
    if not ctx.corner or not ctx.is_centre_bay or ctx.rank_from_principal != 0:
        return None
    return Properties(
        {"surround_kind": "pedimented", "surround_richness": 1.0},
        rule="paris.qualify.site.corner.earns_emphasis",
        specificity=SPEC_EXACT,
    )


def the_street_the_law_favours(
    ctx: QualContext, rng: DecisionStream
) -> Properties | None:
    """On a street the gabarit grants its tallest facade, the bandeau is carved.

    The threshold is not a number chosen here — it is read off the height-step
    table in force in ``ctx.year``: a frontage that earns the top step of the
    table is on a percée, and a percée frontage is a display frontage. Widen
    the street past a step and this changes by itself; rewrite the table in
    ``reglement.py`` and it changes too.

    Applicability: the noble floor of such a frontage, **where the line under
    it is a bandeau and not the entablature crowning a two-storey commercial
    base** (A13.1). ``SPEC_ROLE`` — the base layer's string-course rule is at the
    same rung but in an earlier layer, so order decides and there is no tie.

    The exclusion is not a special case, it is the same reasoning A6.7 made
    about surrounds: this rule carves a *bandeau*, and where the noble floor
    stands on a two-storey commercial base the line under it is not a bandeau
    — it is that base's own crowning entablature, already the strongest
    horizontal on the lower facade. Renaming it here would be a later layer
    overruling a rule that was right about what kind of moulding is there.
    """
    if ctx.rank_from_principal != 0 or (
        ctx.crowns_the_base_block and ctx.has_an_entresol
    ):
        return None
    reg = get_reglement(era_for_year(ctx.year))
    earned = reg.facade_height_limit(ctx.street_width)
    tallest = reg.height_steps[-1][1]
    if earned < tallest - _EPS:
        return None
    return Properties(
        {"string_course_kind": "bandeau_sculpte"},
        rule="paris.qualify.site.street.the_law_favours",
        specificity=SPEC_ROLE,
    )


SITE_RULES: tuple[Rule, ...] = (corner_earns_emphasis, the_street_the_law_favours)


def paris_layers(overrides: Sequence[Rule] = ()) -> tuple[Layer, ...]:
    """The Paris stack: base vocabulary, period, class, site, user overrides.

    ``overrides`` is simply the top layer. Passing rules here is the *only*
    supported way to override, which is why it is a plain rule tuple and not
    a settings mapping: an override that cannot state its own applicability
    and cannot be traced is the table this project exists to get rid of.
    """
    return (
        Layer("base", ORDER_BASE, BASE_RULES),
        Layer("period", ORDER_PERIOD, PERIOD_RULES),
        Layer("class", ORDER_CLASS, CLASS_RULES),
        Layer("site", ORDER_SITE, SITE_RULES),
        Layer("override", ORDER_OVERRIDE, tuple(overrides)),
    )


# ===========================================================================
# 3. Emission
# ===========================================================================
#
# A storey never lays out. Every x and w below is read off `grid.bays`, every
# y and h off `grid.storeys` — the one grid phase 1 solved for the whole
# facade. Nothing here computes a position, which is why no storey can drift
# out of vertical alignment with the one below it: there is no second answer
# for it to drift towards.

#: Facts about the cell that every trace entry carries, so a reader can see
#: what the rule was looking at without going back to the generator.
def _cell_inputs(ctx: QualContext, *, storey_scope: bool = False) -> dict[str, object]:
    facts: dict[str, object] = {
        "level_above_pavement": round(ctx.level_above_pavement, 4),
        "storey_height": round(ctx.slot_h, 4),
        "role": ctx.role.value,
        "rank_from_principal": ctx.rank_from_principal,
        "year": ctx.year,
        "klass": ctx.klass.value,
    }
    if not storey_scope:
        # Omitted for storey-scope elements on purpose: the representative
        # context is the leftmost cell of the row, and printing "slot=pier_end"
        # beside a balcony that runs the full frontage would be worse than
        # printing nothing — it would be a fact the rule demonstrably did not
        # read, offered as if it had.
        # A4.7: `slot_name` everywhere. This used to be spelled `slot` here
        # and `slot_name` in props, which is one fact under two names — and a
        # reader grepping the trace for the name they saw in the IR found
        # nothing.
        facts["slot_name"] = ctx.slot_name
        facts["bay_index_from_left"] = ctx.bay_index_from_left
    return facts


def _entries(
    res: Resolution,
    ctx: QualContext,
    keys: Sequence[str],
    *,
    storey_scope: bool = False,
) -> tuple[TraceEntry, ...]:
    """One trace entry per property this node actually consumed (I4).

    Keys with no winner are skipped rather than faked; a node whose keys were
    all silent gets an empty tuple, and ``Node.__post_init__`` will refuse it
    — which is the correct outcome, because such a node had no reason to be
    emitted in the first place.

    Each entry also carries the rules it *beat*. The node then answers both
    questions a person actually has — "which rule put this here?" and "what
    else nearly did?" — from the serialised IR alone, with no access to the
    run that produced it.
    """
    out: list[TraceEntry] = []
    for key in keys:
        win = res.winners.get(key)
        if win is None:
            continue
        detail = f"{key} = {win.value!r}"
        if win.summary:
            detail = f"{detail} — {win.summary}"
        overruled = tuple(
            f"{c.rule} -> {c.value!r} (layer {c.layer}, specificity {c.specificity})"
            for c in res.candidates
            if c.key == key and c is not win
        )
        inputs: dict[str, object] = {
            **_cell_inputs(ctx, storey_scope=storey_scope),
            "layer": win.layer,
            "specificity": win.specificity,
        }
        if overruled:
            inputs["overruled"] = overruled
        out.append(
            TraceEntry(rule=win.rule, phase="qualification", detail=detail, inputs=inputs)
        )
    return tuple(out)


def _record(log: TraceLog, node_id: str, entries: Sequence[TraceEntry]) -> None:
    for entry in entries:
        log.record(node_id, entry)


def _storey_inside_the_comble(
    log: TraceLog,
    sid: str,
    storey,
    ctx: QualContext,
    facade_w: float,
) -> StoreyNode:
    """The chambres de bonne, as this phase sees them: a storey of the
    building that is not a storey of the *facade*.

    It is emitted rather than skipped — it is a real floor, at a real level,
    with a role derived like every other, and a reader counting the storeys of
    the building must find it — but it carries no children, because a facade
    is stone and there is none here. The elements this storey does have are
    the lucarnes, and they are emitted by the termination phase off the very
    same bay grid (``RoledGrid.attic_bays``), so nothing is lost and nothing
    is drawn twice.

    Since A2.1 put a storey in the comble, this is the flag ``within_comble``
    finally being *consumed* rather than merely recorded: for four stages it
    was a fact in the trace that changed nothing, and the first building with
    an attic in it drew a balconied window wall inside its own mansard.
    """
    entries = (
        TraceEntry(
            rule="paris.roles.assign_roles",
            phase="roles",
            detail=(
                f"role {storey.role.value!r} at rank {storey.rank_from_principal} "
                f"from the principal floor — derived from position and height, "
                f"not declared; floor level {storey.slot.start:.3f} m, storey height "
                f"{storey.slot.width:.3f} m"
            ),
            inputs={
                "index_from_bottom": storey.index_from_bottom,
                "index_from_top": storey.index_from_top,
                "within_comble": ctx.within_comble,
            },
        ),
        TraceEntry(
            rule="paris.compose.storey.inside_the_comble_carries_no_facade",
            phase="qualification",
            detail=(
                f"this storey stands inside the comble — its floor at "
                f"{storey.slot.start:.3f} m is the top of the stone face, not a level "
                f"behind it — so nothing on the stone facade is composed on it: no "
                f"opening, no surround, no keystone, no "
                f"balcon filant, no cornice. What encloses it is the roof, and its "
                f"windows are the lucarnes the termination phase stands on that roof, "
                f"one per bay of this very storey's grid. Emitted empty rather than "
                f"omitted, because it is still a floor of the building and still has "
                f"the role the stack gave it."
            ),
            inputs={
                "within_comble": ctx.within_comble,
                "role": storey.role.value,
                "level_above_pavement": round(storey.slot.start, 4),
                "storey_height": round(storey.slot.width, 4),
                "lit_by": "dormer",
            },
        ),
    )
    _record(log, sid, entries)
    return StoreyNode(
        id=sid,
        kind="storey",
        trace=entries,
        children=(),
        props={
            "x": 0.0,
            "y": storey.slot.start,
            "w": facade_w,
            "h": storey.slot.width,
            "role": storey.role.value,
            "rank_from_principal": storey.rank_from_principal,
            "index_from_bottom": storey.index_from_bottom,
            "within_comble": True,
            "on_the_stone_facade": False,
            "enclosed_by": "comble",
            "lit_by": "dormer",
        },
    )


class NoEntrance(Exception):
    """A facade was composed with no way into the building, or with two.

    A6.1's assertion, and it is an exception rather than a warning because
    the defect it names went undetected across nine stages and a whole block
    of ten immeubles: ``{window: 108, shop_bay: 27, blind_panel: 27,
    oeil_de_boeuf: 3}`` and not one door. Nothing downstream would have
    noticed — the facade is well-formed, the trace is complete, the
    silhouette fits the gabarit — because "there is a way in" is not a
    property any geometric check asks about. So it is asked here, once, of
    the emitted tree, by counting the openings that ARE entrances.
    """


def _assert_one_entrance(
    storey_nodes: Sequence[Node], roled: RoledGrid, site: SiteContext
) -> None:
    """Exactly one entrance per building. Always. Counted, not assumed.

    Counted off the emitted nodes rather than off the grid, deliberately: the
    grid having a door slot and the facade having a door in it are two
    different claims, and the second is the one a person standing on the
    pavement can check. A rule set that names the slot and then declines to
    fill it would pass the phase-1 postcondition and fail here.
    """
    entrances = [
        n
        for n in _walk_all(storey_nodes)
        if n.kind == "opening"
        and n.props.get("opening_type") in set(catalogue.ENTRANCE_OPENING_TYPES.values())
    ]
    if len(entrances) == 1:
        return
    census: dict[object, int] = {}
    for n in _walk_all(storey_nodes):
        if n.kind == "opening":
            key = n.props.get("opening_type")
            census[key] = census.get(key, 0) + 1
    slots = [s.name for s in roled.bays]
    raise NoEntrance(
        f"a building has exactly one entrance; this facade has {len(entrances)} "
        f"({[n.id for n in entrances]}). Every Paris immeuble has a way in — a porte "
        f"cochère on the grander streets, a porte piétonne on the modest ones — and "
        f"phase 1 places a FIXED slot for it on every frontage by a positional rule. "
        f"Bay slots: {slots}. Opening census: {census}. Situation: "
        f"{site.klass.value}, {site.ground.value}, {site.street_width:.2f} m street, "
        f"{site.parcel_width:.2f} m parcel."
    )


def _walk_all(nodes: Sequence[Node]):
    for node in nodes:
        yield from _walk(node)


def qualify_from_grid(
    roled: RoledGrid,
    site: SiteContext,
    *,
    layers: Sequence[Layer] | None = None,
    rng: DecisionStream | None = None,
) -> tuple[BuildingNode, TraceLog]:
    """Qualify an already-solved, already-roled grid and emit the facade.

    Split out from ``qualify_building`` so a test can hand in a grid it built
    by hand — which is how the mezzanine experiment is run without having to
    persuade the solver to produce two stacks that differ in exactly one
    storey.
    """
    layers = tuple(paris_layers() if layers is None else layers)
    rng = DecisionStream(site.seed) if rng is None else rng
    log = TraceLog()

    cells = contexts_for(roled, site)
    bays = roled.bays
    facade_w = math.fsum(b.width for b in bays)

    building_id = "b"
    storey_nodes: list[Node] = []

    for row_i, row in enumerate(cells):
        storey = roled.storeys[row_i]
        sid = f"{building_id}/s{row_i}"
        y = storey.slot.start
        h = storey.slot.width

        if row[0].within_comble:
            # A storey standing inside the comble has no stone frontage to
            # qualify. The wall around it is the roof this phase does not
            # emit, and its windows are the lucarnes the termination phase
            # stands on that roof — so composing a facade storey here would
            # put a full-width window wall, with its surrounds, its keystones
            # and its balcon filant, inside the mansard, in exactly the volume
            # the roof node already occupies, lit twice over.
            #
            # This is *not* a rule in the layered stack, deliberately. A rule
            # can be overruled by a later layer, and "there is no stone here"
            # is not a taste a class or a period may disagree with; it is the
            # same geometric fact `roles.py` turned into ATTIC, read once, in
            # the phase that decides what gets emitted at all. What the comble
            # storey *does* carry is decided where its elements are actually
            # emitted, on the roof.
            storey_nodes.append(_storey_inside_the_comble(log, sid, storey, row[0], facade_w))
            continue

        resolutions = [resolve(ctx, layers, rng) for ctx in row]
        # Storey-scope properties come from rules whose applicability reads no
        # horizontal fact, so every cell in the row agrees about them; the
        # leftmost is the representative. `test_compose` asserts the agreement
        # rather than trusting it.
        s_res = resolutions[0]
        s_ctx = row[0]

        # Storey-scope nodes. Each is recorded in the log as it is created —
        # `_storey_child` below is the single place that happens, so no node
        # can be emitted without its entries landing in the log too.
        children: list[Node] = []

        def _storey_child(node: Node) -> None:
            _record(log, node.id, node.trace)
            children.append(node)

        if s_res.get("socle_present"):
            keys = (
                "socle_present",
                "socle_treatment",
                # A13.1: the socle runs through the entresol where there is
                # one, so the storey that has one says which form it took.
                # The trace then answers "why is there stone up here?" and
                # "why is there no railing on it?" from the serialised IR
                # alone, which is the whole point of carrying the decision.
                "entresol_treatment",
                "ornament_course_width",
                "ornament_course_height",
            )
            _storey_child(
                SocleNode(
                    id=f"{sid}/socle",
                    kind="socle",
                    trace=_entries(s_res, s_ctx, keys, storey_scope=True),
                    props={
                        "x": 0.0,
                        "y": y,
                        "w": facade_w,
                        "h": h,
                        "treatment": s_res.get("socle_treatment"),
                        # A7.2. How many drawn stones across and how many
                        # courses up, stated here rather than left to the
                        # renderer to get from the wall's size and a course
                        # height of its own choosing. The interval is the
                        # ornament dial's (``ornament_course_*``); the extent
                        # is this node's own; the count is what a consumer
                        # needs and the only one of the three it cannot
                        # legitimately work out for itself.
                        "course_columns": catalogue.repeats_across(
                            facade_w,
                            float(s_res.get("ornament_course_width") or 0.0),
                        ),
                        "course_rows": catalogue.repeats_across(
                            h, float(s_res.get("ornament_course_height") or 0.0)
                        ),
                    },
                )
            )

        # A devanture is emitted per BAY, below, not here. It used to be a
        # storey-scope node spanning x=0 to the full facade width, which meant
        # the renderer glazed the entire ground storey in one rectangle and
        # painted out the 0.80 m trumeau qualification had just carved between
        # every pair of shops (A4.1). A shop is a hole in a wall, and the wall
        # between two of them is the same masonry as the wall between two
        # windows: there is no "shopfront" that is a property of the whole
        # frontage, only one devanture per bay that has one.

        if s_res.get("string_course_present"):
            keys = ("string_course_present", "string_course_kind", "string_course_projection")
            depth = float(s_res.get("string_course_projection", 0.0) or 0.0)
            _storey_child(
                StringCourseNode(
                    id=f"{sid}/string_course",
                    kind="string_course",
                    trace=_entries(s_res, s_ctx, keys, storey_scope=True),
                    props={
                        "x": 0.0,
                        "y": y,
                        "w": facade_w,
                        "h": depth,
                        "course_kind": s_res.get("string_course_kind"),
                        "projection": depth,
                    },
                )
            )

        if s_res.get("balcony_present") and s_res.get("balcony_continuous"):
            keys = (
                "balcony_present",
                "balcony_continuous",
                "balcony_projection",
                "balcony_min_height",
                "balcony_rail_height",
                "ornament_bracket_module",
            )
            _storey_child(
                BalconyNode(
                    id=f"{sid}/balcony",
                    kind="balcony",
                    trace=_entries(s_res, s_ctx, keys, storey_scope=True),
                    props={
                        "x": 0.0,
                        "y": y,
                        "w": facade_w,
                        "h": float(s_res.get("balcony_rail_height", 0.0) or 0.0),
                        "continuous": True,
                        "projection": s_res.get("balcony_projection"),
                        "min_height": s_res.get("balcony_min_height"),
                        # A7.2: how many consoles carry this run of slab.
                        "bracket_count": catalogue.repeats_across(
                            facade_w,
                            float(s_res.get("ornament_bracket_module") or 0.0),
                            minimum=2,
                        ),
                    },
                )
            )

        if s_res.get("cornice_present"):
            depth = float(s_res.get("cornice_projection", 0.0) or 0.0)
            richness = float(s_res.get("cornice_richness") or 0.0)
            # Which of the two bracket vocabularies this cornice carries, and
            # therefore which of the two ornament modules its rhythm runs at.
            # One cornice draws one of them, so one count is stated, not two.
            ornament = (
                "modillioned" if richness >= _CORNICE_MODILLION_THRESHOLD else "plain"
            )
            module_key = (
                "ornament_modillion_module"
                if ornament == "modillioned"
                else "ornament_dentil_module"
            )
            keys = (
                "cornice_present",
                "cornice_projection",
                "cornice_richness",
                module_key,
            )
            _storey_child(
                CorniceNode(
                    id=f"{sid}/cornice",
                    kind="cornice",
                    trace=_entries(s_res, s_ctx, keys, storey_scope=True),
                    props={
                        "x": 0.0,
                        "y": y + h,
                        "w": facade_w,
                        "h": depth,
                        "projection": depth,
                        # A4.3: the renderer used to smuggle this exact 0.7
                        # threshold past the guard by renaming the richness
                        # float into a local before comparing it. The number
                        # is a decision a person could argue about — this is
                        # where it belongs. What crosses now is a resolved
                        # decision (which brackets of the cornice look like
                        # modillions), not the number the decision was made
                        # from; the renderer reads the string and draws.
                        "cornice_ornament": ornament,
                        # A7.2: and how many of them. The renderer used to
                        # hold a spacing of its own for each vocabulary
                        # (0.5 m of modillion, 0.12 m of dentil) and divide
                        # the facade by it, so every cornice in Paris carried
                        # the same brackets per metre whatever it cost. The
                        # interval is the ornament dial's now, and what
                        # crosses is the count it produced over THIS width.
                        "ornament_count": catalogue.repeats_across(
                            facade_w,
                            float(s_res.get(module_key) or 0.0),
                            minimum=2,
                        ),
                    },
                )
            )

        for col_i, (ctx, res) in enumerate(zip(row, resolutions)):
            bay = bays[col_i]
            bid = f"{sid}/x{col_i}"
            bay_children: list[Node] = []

            # The rectangle the opening-attached ornament belongs to. It is
            # the LIGHT's, not the cell's, and it is set below once the
            # opening's own geometry is known; a bay with no opening keeps the
            # cell, which is all a surround on a blind pier could mean.
            #
            # This used to stay at the cell for every bay, and `render`
            # substituted the opening's rectangle before drawing a surround or
            # a keystone — "a moulded architrave sized to the whole bay would
            # float untethered from the window it frames", says the renderer,
            # correctly. So the IR stated one rectangle, the renderer drew
            # another, and the node's own props were a number nobody used: one
            # fact under two names, with the drawn one decided downstream
            # (A4.7's offence, A4.3's shape). The light's rectangle is stated
            # here now, so the two agree and the renderer is reading rather
            # than correcting.
            light = (bay.start, y, bay.width, h)

            opening = res.get("opening_type")
            if opening not in (None, "none"):
                keys = (
                    "opening_type",
                    "opening_head",
                    "opening_width",
                    "opening_height",
                    "opening_offset_x",
                    "opening_sill_height",
                    # A14.1: which register of a two-storey entrance arch this
                    # is, how far its round head rises over the springing, and
                    # how much of the lower register the leaves themselves
                    # take. All three are ``None`` on every other opening in
                    # Paris, and ``_entries`` states only what a rule set.
                    "entrance_arch_register",
                    "opening_head_rise",
                    "entrance_leaf_height",
                )
                # The LIGHT's extent, not the cell's (A4.1). Qualification
                # resolved the opening's own width, height and place within
                # the slot — that is a decision about proportion, and the
                # brief is explicit that a renderer may not take it. All this
                # does is add the slot's origin to numbers stated relative to
                # it. Nothing is decided here; nothing may be.
                #
                # Where a rule declined to state the geometry the opening
                # falls back to its slot, which is the old curtain-wall
                # behaviour, kept only so a hand-built layer set that names
                # an opening_type and nothing else still emits a node instead
                # of raising. `test_compose` asserts the fallback is unused by
                # the real Paris stack.
                o_w = res.get("opening_width")
                o_h = res.get("opening_height")
                o_x = res.get("opening_offset_x")
                o_sill = res.get("opening_sill_height")
                stated = o_w is not None and o_h is not None
                width = float(o_w) if o_w is not None else bay.width
                height = float(o_h) if o_h is not None else h
                offset_x = float(o_x) if o_x is not None else 0.0
                sill = float(o_sill) if o_sill is not None else 0.0
                light = (bay.start + offset_x, y + sill, width, height)
                bay_children.append(
                    OpeningNode(
                        id=f"{bid}/opening",
                        kind="opening",
                        trace=_entries(res, ctx, keys),
                        props={
                            "x": bay.start + offset_x,
                            "y": y + sill,
                            "w": width,
                            "h": height,
                            "opening_type": opening,
                            "head": res.get("opening_head"),
                            "sill_height": sill,
                            # The masonry the slot keeps: a real pier either
                            # side of the light, and the wall left over the
                            # head. Carried because they are what makes the
                            # facade stone rather than glass, and a consumer
                            # that has to subtract two rectangles to discover
                            # them will eventually subtract them wrongly.
                            "pier_width": offset_x,
                            "lintel_height": max(0.0, h - sill - height),
                            "slot_x": bay.start,
                            "slot_w": bay.width,
                            "geometry_stated": stated,
                            # How big a single sheet of glass the date could
                            # supply. Only a devanture has one — an ordinary
                            # window's glazing bars are joinery, but a shop
                            # window's are the manufacturing limit of the
                            # decade, which is a fact about the date and not
                            # a rhythm the renderer may invent (A4.3's spirit:
                            # the renderer used to divide the whole frontage
                            # into 1.5 m panes that landed nowhere near the
                            # structural bays).
                            "pane_max_span": res.get("shopfront_pane_max_span"),
                            # A14.1, and stated only where a rule stated it.
                            # Three keys that describe one two-storey entrance
                            # arch and are meaningless on every other opening
                            # in Paris, so they are absent there rather than
                            # present and null: a node carrying
                            # ``arch_register: None`` is a node claiming to
                            # have been asked a question it was never asked,
                            # and it would put the same three empty keys on
                            # every window in every golden master.
                            #
                            # * ``head_rise`` — how far the ROUND head rises
                            #   over its springing. Half the span, because
                            #   that is what round means; stated because the
                            #   renderer's own fallback is
                            #   ``min(0.5, max(0.15, w * 0.30))``, which on a
                            #   2.60 m arch draws a 0.50 m bow where a
                            #   semicircle was decided.
                            # * ``arch_register`` — which of the arch's two
                            #   registers this rectangle is. One arch across
                            #   two storeys of one grid, and the fact that
                            #   the two rectangles are one object is stated
                            #   on both rather than inferred from adjacency,
                            #   exactly as A13's absorbed devanture states
                            #   ``entresol_treatment`` on both of its own.
                            # * ``leaf_height`` — the door inside the lower
                            #   register. The SAME clear height a one-storey
                            #   door has: what passes through the gate did
                            #   not change when the arch grew.
                            **{
                                prop: res.get(key)
                                for prop, key in (
                                    ("head_rise", "opening_head_rise"),
                                    ("arch_register", "entrance_arch_register"),
                                    ("leaf_height", "entrance_leaf_height"),
                                )
                                if res.get(key) is not None
                            },
                        },
                    )
                )

                if opening == "shop_bay" and res.get("shopfront_present"):
                    # The devanture that is NOT the glass: the soubassement
                    # under the light and the enseigne board over it, both of
                    # them ABSOLUTE bands the catalogue sized, standing in the
                    # same width of frontage as the light between the same two
                    # trumeaux. The light itself is the opening above — one
                    # rectangle, emitted once — so there is nothing here for
                    # the two to disagree about.
                    keys = (
                        "shopfront_present",
                        "shopfront_variant",
                        "ground_treatment",
                        # A13.2: which register of the framework this is, and
                        # why it carries a soubassement, a signboard, or
                        # neither.
                        "entresol_treatment",
                    )
                    bay_children.append(
                        ShopfrontNode(
                            id=f"{bid}/shopfront",
                            kind="shopfront",
                            trace=_entries(res, ctx, keys),
                            props={
                                "x": bay.start + offset_x,
                                "y": y,
                                "w": width,
                                "h": h,
                                # Named for what it is, not the generic slot
                                # name the renderer's forbidden-token guard
                                # treats specially (A4.3) — "shopfront_variant"
                                # is exactly what S5 (chronology) already
                                # resolved this to, so keying it under that
                                # name lets the renderer read it directly
                                # instead of routing around the guard through
                                # a renamed local.
                                "shopfront_style": s_res.get("shopfront_variant"),
                                "treatment": s_res.get("ground_treatment"),
                                "threshold_height": sill,
                                "fascia_depth": max(0.0, h - sill - height),
                            },
                        )
                    )

            surround = res.get("surround_kind")
            if surround not in (None, "none"):
                keys = ("surround_kind", "surround_richness")
                bay_children.append(
                    SurroundNode(
                        id=f"{bid}/surround",
                        kind="surround",
                        trace=_entries(res, ctx, keys),
                        props={
                            # The light's rectangle: an architrave frames the
                            # opening, and the masonry either side of it is
                            # the pier, which is not something a surround is
                            # applied to.
                            "x": light[0],
                            "y": light[1],
                            "w": light[2],
                            "h": light[3],
                            "surround_kind": surround,
                            "richness": res.get("surround_richness"),
                        },
                    )
                )

            if res.get("keystone_present"):
                keys = ("keystone_present", "keystone_kind")
                bay_children.append(
                    KeystoneNode(
                        id=f"{bid}/keystone",
                        kind="keystone",
                        trace=_entries(res, ctx, keys),
                        props={
                            # A keystone is the stone at the crown of the
                            # arch, so it stands on the head of the LIGHT.
                            # This used to say `y + h` — the storey's ceiling
                            # — which put it a whole lintel above the opening
                            # it locks, and left the renderer to move it back
                            # down to `oy + oh` before drawing it.
                            "x": light[0],
                            "y": light[1] + light[3],
                            "w": light[2],
                            "h": 0.0,
                            "keystone_kind": res.get("keystone_kind"),
                        },
                    )
                )

            if res.get("balcony_present") and not res.get("balcony_continuous"):
                if opening in ("window", "shop_bay"):
                    keys = (
                        "balcony_present",
                        "balcony_continuous",
                        "balcony_projection",
                        "balcony_min_height",
                        "balcony_rail_height",
                        "ornament_bracket_module",
                    )
                    bay_children.append(
                        BalconyNode(
                            id=f"{bid}/balcony",
                            kind="balcony",
                            trace=_entries(res, ctx, keys),
                            props={
                                # A balconette stands in front of the window
                                # it belongs to, not in front of the bay: the
                                # masonry pier either side of the light is
                                # wall, and a slab that ran across it would be
                                # a balcon filant by another name. Same
                                # reasoning as the garde-corps below, which
                                # stands on this slab and must agree with it.
                                "x": light[0],
                                "y": y,
                                "w": light[2],
                                "h": float(res.get("balcony_rail_height", 0.0) or 0.0),
                                "continuous": False,
                                "projection": res.get("balcony_projection"),
                                "min_height": res.get("balcony_min_height"),
                                # A7.2, and counted across the slab this node
                                # actually states — a balconette is the
                                # light's width, so it carries the consoles a
                                # light's width of slab needs and not the
                                # bay's.
                                "bracket_count": catalogue.repeats_across(
                                    light[2],
                                    float(res.get("ornament_bracket_module") or 0.0),
                                    minimum=2,
                                ),
                            },
                        )
                    )

            # A6.5 and A6.6. Ironwork is as wide as the thing it guards, and
            # it is exactly two things:
            #
            # * **A garde-corps guards an OPENING.** It stands in the light's
            #   own width, in front of the allège under it. It used to be
            #   emitted at the BAY's rectangle — 3.45 m of railing drawn
            #   across two solid masonry piers in front of a 1.322 m window,
            #   which is A6.5's complaint exactly.
            # * **A balustrade guards a BALCONY.** Where the balcon filant
            #   runs, the drop it guards is the slab's, and the slab runs the
            #   whole storey — so this bay's length of that balustrade really
            #   does run the whole bay, piers included, because the balcony
            #   in front of them does. A row of window-width panels with the
            #   gaps between them opening onto the same 8 m drop is not a
            #   railing; it is a hazard drawn to look like one.
            #
            # A6.6: the height is the railing's OWN ``ironwork_height`` — an
            # ABSOLUTE, the height a body leans against — and no longer
            # ``balcony_rail_height``, which exists only on the floors the
            # 1823 ordonnance permits a balcony on, so every railing below
            # 6 m (the mezzanine's included) arrived with ``h = 0.000`` and
            # drew nothing. An element with no height is not emitted at all:
            # either give it height or do not put it in the IR.
            rail_h = float(res.get("ironwork_height", 0.0) or 0.0)
            on_the_filant = bool(
                res.get("balcony_present") and res.get("balcony_continuous")
            )
            # A14.1: the entresol register of a two-storey entrance arch is a
            # balconette with ironwork set INSIDE the arch, so the railing
            # guards that light exactly as a garde-corps guards a window's.
            # Named through the catalogue's constant rather than spelled here,
            # because the string is also the renderer's branch and the
            # qualification rule's output, and three spellings of one kind is
            # how the three drift apart.
            guards_an_opening = opening in (
                "window",
                "narrow_window",
                "shop_bay",
                catalogue.ENTRANCE_ARCH_HEAD_OPENING,
            )
            if res.get("ironwork_present") and rail_h > _EPS and (
                on_the_filant or guards_an_opening
            ):
                keys = (
                    "ironwork_present",
                    "ironwork_variant",
                    "ironwork_gap_max",
                    "ironwork_height",
                    "ornament_ironwork_module",
                )
                rail_x, rail_w = (
                    (bay.start, bay.width) if on_the_filant else (light[0], light[2])
                )
                bay_children.append(
                    IronworkNode(
                        id=f"{bid}/ironwork",
                        kind="ironwork",
                        trace=_entries(res, ctx, keys),
                        props={
                            "x": rail_x,
                            "y": y,
                            "w": rail_w,
                            "h": rail_h,
                            # What this length of railing is guarding, which
                            # is also why it is the width it is. Read, not
                            # inferred: a consumer that had to work out which
                            # of the two it was by comparing widths would get
                            # it wrong on the day an opening filled its bay.
                            "guards": "balcon_filant" if on_the_filant else "opening",
                            # Named "ironwork_pattern" rather than the generic
                            # "variant" S5 resolved it under (A4.3) — the
                            # renderer's guard forbids branching on a raw
                            # "variant" key, and this is a resolved pattern
                            # name, not a decision the renderer is making.
                            "ironwork_pattern": res.get("ironwork_variant"),
                            "max_gap": res.get("ironwork_gap_max"),
                            # A7.2, and the distinction the amendment calls
                            # instructive. There are TWO rhythms in a
                            # garde-corps and they are different kinds of
                            # number. The BARS run on ``max_gap``, which is
                            # ABSOLUTE — a child's head — and the consumer
                            # divides by it because it is honouring a limit
                            # the IR stated, which is not the same act as
                            # inventing one. The ORNAMENT hung on those bars
                            # — the scrolls, the waves, the lozenges — is
                            # ornament density, which is PROPORTIONAL, so its
                            # count is decided here and travels stated.
                            "ornament_count": catalogue.repeats_across(
                                rail_w,
                                float(res.get("ornament_ironwork_module") or 0.0),
                                minimum=2,
                            ),
                        },
                    )
                )

            bay_trace = (
                TraceEntry(
                    rule="paris.structure.solve_structure",
                    phase="structure",
                    detail=(
                        f"slot {bay.name!r} ({bay.kind.value}) at x={bay.start:.3f} m, "
                        f"w={bay.width:.3f} m — one horizontal solve for the whole "
                        "facade, so this bay is at the same x on every storey"
                    ),
                    inputs={
                        "slot_name": bay.name,
                        "is_special": bay.is_special,
                        "distance_from_entrance": ctx.distance_from_entrance,
                        "is_centre_bay": ctx.is_centre_bay,
                    },
                ),
            )
            _record(log, bid, bay_trace)
            for child in bay_children:
                _record(log, child.id, child.trace)

            bay_children_sorted = tuple(bay_children)
            storey_bay = BayNode(
                id=bid,
                kind="bay",
                trace=bay_trace,
                children=bay_children_sorted,
                props={
                    "x": bay.start,
                    "y": y,
                    "w": bay.width,
                    "h": h,
                    "slot_name": bay.name,
                    "is_special": bay.is_special,
                    "ornament_density": res.get("ornament_density"),
                },
            )
            children.append(storey_bay)

        storey_trace = (
            TraceEntry(
                rule="paris.roles.assign_roles",
                phase="roles",
                detail=(
                    f"role {storey.role.value!r} at rank {storey.rank_from_principal} "
                    f"from the principal floor — derived from position and height, "
                    f"not declared; floor level {y:.3f} m, storey height {h:.3f} m"
                ),
                inputs={
                    "index_from_bottom": storey.index_from_bottom,
                    "index_from_top": storey.index_from_top,
                    "within_comble": s_ctx.within_comble,
                },
            ),
        )
        _record(log, sid, storey_trace)

        storey_nodes.append(
            StoreyNode(
                id=sid,
                kind="storey",
                trace=storey_trace,
                children=tuple(children),
                props={
                    "x": 0.0,
                    "y": y,
                    "w": facade_w,
                    "h": h,
                    "role": storey.role.value,
                    "rank_from_principal": storey.rank_from_principal,
                    "index_from_bottom": storey.index_from_bottom,
                    "ornament_density": s_res.get("ornament_density"),
                    "within_comble": False,
                    "on_the_stone_facade": True,
                },
            )
        )

    _assert_one_entrance(storey_nodes, roled, site)

    building_trace = (
        TraceEntry(
            rule="paris.compose.qualify_building",
            phase="qualification",
            detail=(
                f"{len(storey_nodes)} storey(s) filling one shared grid of "
                f"{len(bays)} horizontal slot(s) across {facade_w:.3f} m of frontage; "
                f"layers applied, in order: "
                + ", ".join(f"{ly.name}({ly.order})" for ly in sorted(layers, key=lambda l: l.order))
            ),
            inputs={
                "year": site.year,
                "klass": site.klass.value,
                "ground": site.ground.value,
                "street_width": site.street_width,
                "parcel_width": site.parcel_width,
                "corner": site.corner,
                "seed": site.seed,
                "cornice_height": float(roled.grid.cornice_height),
            },
        ),
    )
    _record(log, building_id, building_trace)

    return (
        BuildingNode(
            id=building_id,
            kind="building",
            trace=building_trace,
            children=tuple(storey_nodes),
            props={
                "x": 0.0,
                "y": 0.0,
                "w": facade_w,
                "h": math.fsum(s.slot.width for s in roled.storeys),
                "year": site.year,
                "klass": site.klass.value,
                "street_width": site.street_width,
                "corner": site.corner,
            },
        ),
        log,
    )


def qualify_building(
    site: SiteContext,
    *,
    layers: Sequence[Layer] | None = None,
    rng: DecisionStream | None = None,
) -> tuple[BuildingNode, TraceLog]:
    """Situation in, qualified facade out. Phases 1 -> 2 -> 3/4, in that order."""
    grid = solve_structure(site)
    roled = assign_roles(grid)
    return qualify_from_grid(roled, site, layers=layers, rng=rng)


# ===========================================================================
# 4. "Why is this here?"
# ===========================================================================


def find_node(root: Node, node_id: str) -> Node | None:
    """Depth-first search for a node by id. Ids are stable dotted paths
    (``b/s2/x3/balcony``), so they can be read off a render and typed back in."""
    if root.id == node_id:
        return root
    for child in root.children:
        found = find_node(child, node_id)
        if found is not None:
            return found
    return None


def explain(root: Node, node_id: str) -> str:
    """Why is this element here? — answered from the IR alone.

    The brief is blunt about this one: "Build the 'why' tooling first, not
    last... Defer that and you will spend weeks bisecting rule sets by hand
    and conclude the approach was a mistake." So this reads the node's own
    ``trace`` — the durable record every node carries (I4) — rather than
    needing the generator, the seed, or the run that produced it. Hand
    somebody a serialised IR and they can still ask it this question.
    """
    node = find_node(root, node_id)
    if node is None:
        available = ", ".join(sorted(n.id for n in _walk(root)))
        return f"no node {node_id!r} in this tree.\nknown ids: {available}"

    lines = [f"{node.id}  ({node.kind})"]
    extent = {k: node.props.get(k) for k in ("x", "y", "w", "h") if k in node.props}
    if extent:
        lines.append(
            "  extent: "
            + ", ".join(
                f"{k}={v:.3f} m" if isinstance(v, float) else f"{k}={v}"
                for k, v in extent.items()
            )
        )
    other = {k: v for k, v in node.props.items() if k not in ("x", "y", "w", "h")}
    if other:
        lines.append("  props: " + ", ".join(f"{k}={v!r}" for k, v in sorted(other.items())))
    lines.append("  why:")
    for i, entry in enumerate(node.trace, start=1):
        lines.append(f"    {i}. [{entry.phase}] {entry.rule}")
        lines.append(f"       {entry.detail}")
        if entry.inputs:
            lines.append(
                "       given: "
                + ", ".join(f"{k}={v!r}" for k, v in sorted(entry.inputs.items()))
            )
    ancestry = _ancestry(root, node_id)
    if len(ancestry) > 1:
        lines.append("  inside: " + " -> ".join(n.id for n in ancestry[:-1]))
    return "\n".join(lines)


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _ancestry(root: Node, node_id: str) -> list[Node]:
    if root.id == node_id:
        return [root]
    for child in root.children:
        path = _ancestry(child, node_id)
        if path:
            return [root, *path]
    return []
