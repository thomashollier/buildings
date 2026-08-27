"""S6 phase 4 — layered composition, conflict detection, emission and "why?".

Three things are load-bearing here and each has its own section:

* the resolution truth table, because "later layer wins, specificity breaks
  ties" is the whole of the composition semantics and it should be readable as
  a table rather than inferred from behaviour;
* the conflict, because silently picking a winner is how this design becomes
  nondeterministic-looking and unbeatable to debug;
* ``explain``, because the brief says to build the "why" tooling first and the
  only way to know it works is to read its output.
"""

from __future__ import annotations

import pytest

from buildings.ir.nodes import Node
from buildings.ir.serial import from_json, to_json
from buildings.rng import DecisionStream
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.compose import (
    Layer,
    ORDER_OVERRIDE,
    RuleConflict,
    explain,
    find_node,
    paris_layers,
    qualify_building,
    qualify_from_grid,
    resolve,
)
from buildings.typologies.paris.qualify.context import Properties, contexts_for
from buildings.typologies.paris.roles import assign_roles
from buildings.typologies.paris.structure import solve_structure

from tests.unit.test_qualify import _ctx, _grid, _site, WITHOUT_MEZZANINE, WITH_MEZZANINE

RNG = DecisionStream(3)


def _rule(key: str, value: object, rid: str, spec: int):
    def r(ctx, rng):
        return Properties({key: value}, rule=rid, specificity=spec)

    r.__doc__ = f"test rule {rid}."
    r.__name__ = rid.replace(".", "_")
    return r


def _silent(rid: str = "test.silent"):
    def r(ctx, rng):
        return None

    r.__doc__ = "a rule with no opinion."
    r.__name__ = "silent"
    return r


# ===========================================================================
# The resolution truth table
# ===========================================================================

K = "opening_type"

TRUTH_TABLE = [
    # (description, layers, expected winning value, expected winning rule id)
    (
        "one layer, one rule",
        [Layer("base", 0, (_rule(K, "a", "r.a", 0),))],
        "a",
        "r.a",
    ),
    (
        "one layer, specificity breaks the tie",
        [Layer("base", 0, (_rule(K, "a", "r.a", 0), _rule(K, "b", "r.b", 10)))],
        "b",
        "r.b",
    ),
    (
        "specificity is compared, not rule order in the tuple",
        [Layer("base", 0, (_rule(K, "b", "r.b", 10), _rule(K, "a", "r.a", 0)))],
        "b",
        "r.b",
    ),
    (
        "later layer wins",
        [
            Layer("base", 0, (_rule(K, "a", "r.a", 0),)),
            Layer("period", 10, (_rule(K, "b", "r.b", 0),)),
        ],
        "b",
        "r.b",
    ),
    (
        "layer order beats specificity: a broad late rule beats a narrow early one",
        [
            Layer("base", 0, (_rule(K, "a", "r.a", 999),)),
            Layer("period", 10, (_rule(K, "b", "r.b", 0),)),
        ],
        "b",
        "r.b",
    ),
    (
        "equal order, different specificity: specificity decides",
        [
            Layer("one", 5, (_rule(K, "a", "r.a", 0),)),
            Layer("two", 5, (_rule(K, "b", "r.b", 1),)),
        ],
        "b",
        "r.b",
    ),
    (
        "the layers are sorted by order, not by the sequence they arrive in",
        [
            Layer("period", 10, (_rule(K, "b", "r.b", 0),)),
            Layer("base", 0, (_rule(K, "a", "r.a", 0),)),
        ],
        "b",
        "r.b",
    ),
    (
        "a silent rule is skipped, not treated as an opinion",
        [Layer("base", 0, (_rule(K, "a", "r.a", 0), _silent()))],
        "a",
        "r.a",
    ),
    (
        "the override layer is just the top layer",
        [
            Layer("base", 0, (_rule(K, "a", "r.a", 999),)),
            Layer("override", ORDER_OVERRIDE, (_rule(K, "z", "user.z", 0),)),
        ],
        "z",
        "user.z",
    ),
]


@pytest.mark.parametrize(
    "description,layers,expected,expected_rule",
    TRUTH_TABLE,
    ids=[row[0] for row in TRUTH_TABLE],
)
def test_resolution_truth_table(description, layers, expected, expected_rule):
    res = resolve(_ctx(), layers, RNG)
    assert res.values[K] == expected, description
    assert res.provenance[K] == expected_rule, description


def test_disjoint_keys_merge_rather_than_compete():
    res = resolve(
        _ctx(),
        [
            Layer("base", 0, (_rule("opening_type", "window", "r.o", 0),)),
            Layer("period", 10, (_rule("keystone_kind", "mascaron", "r.k", 0),)),
        ],
        RNG,
    )
    assert res.values == {"opening_type": "window", "keystone_kind": "mascaron"}
    assert res.provenance == {"opening_type": "r.o", "keystone_kind": "r.k"}


def test_a_key_nobody_claimed_is_absent_not_none():
    res = resolve(_ctx(), [Layer("base", 0, (_rule(K, "a", "r.a", 0),))], RNG)
    assert "balcony_present" not in res.values
    assert res.get("balcony_present") is None
    assert "no rule had an opinion" in res.why("balcony_present")


# ===========================================================================
# Conflicts are raised, never resolved
# ===========================================================================


def test_equal_order_and_equal_specificity_is_a_conflict():
    layers = [Layer("base", 0, (_rule(K, "a", "r.a", 10), _rule(K, "b", "r.b", 10)))]
    with pytest.raises(RuleConflict) as excinfo:
        resolve(_ctx(), layers, RNG)
    message = str(excinfo.value)
    assert "r.a" in message and "r.b" in message
    assert K in message
    assert "'a'" in message and "'b'" in message


def test_a_conflict_across_two_layers_of_equal_order_also_raises():
    layers = [
        Layer("one", 7, (_rule(K, "a", "r.a", 3),)),
        Layer("two", 7, (_rule(K, "b", "r.b", 3),)),
    ]
    with pytest.raises(RuleConflict, match="one|two"):
        resolve(_ctx(), layers, RNG)


def test_a_conflict_raises_even_when_the_two_rules_agree_on_the_value():
    """Agreement is not authorship. Picking one of two equally-entitled rules
    to record in the trace is still a silent pick, and I4 asks the trace to
    name *the* rule that produced the property."""
    layers = [Layer("base", 0, (_rule(K, "same", "r.a", 0), _rule(K, "same", "r.b", 0)))]
    with pytest.raises(RuleConflict):
        resolve(_ctx(), layers, RNG)


def test_the_shipped_paris_stack_has_no_conflicts_anywhere_in_a_sweep():
    """The truth table proves the mechanism; this proves the rule set actually
    shipped never trips it, across classes, programmes, corners and a century."""
    layers = paris_layers()
    for year in (1825, 1848, 1860, 1875, 1884, 1895, 1901):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                site = _site(year=year, klass=klass, ground=ground, parcel_width=13.0)
                roled = assign_roles(solve_structure(site))
                for row in contexts_for(roled, site):
                    for ctx in row:
                        resolve(ctx, layers, RNG)  # must not raise


def test_a_rule_returning_the_wrong_type_is_refused_loudly():
    def bad(ctx, rng):
        return {"opening_type": "window"}

    with pytest.raises(TypeError, match="returns Properties or None"):
        resolve(_ctx(), [Layer("base", 0, (bad,))], RNG)


def test_layers_must_be_named():
    with pytest.raises(ValueError, match="non-empty"):
        Layer("", 0, ())


# ===========================================================================
# Rules cannot read each other, so their order cannot matter
# ===========================================================================


def test_rule_order_within_a_layer_does_not_matter():
    site = _site(year=1878, klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    roled = assign_roles(solve_structure(site))
    layers = paris_layers()
    reversed_layers = tuple(
        Layer(ly.name, ly.order, tuple(reversed(ly.rules))) for ly in layers
    )
    for row in contexts_for(roled, site):
        for ctx in row:
            a = resolve(ctx, layers, DecisionStream(site.seed))
            b = resolve(ctx, reversed_layers, DecisionStream(site.seed))
            assert a.values == b.values
            assert a.provenance == b.provenance


# ===========================================================================
# A storey never lays out — it fills the one grid
# ===========================================================================


def test_every_storey_fills_the_same_horizontal_grid():
    """...and the comble storey fills it too, without being on the facade.

    A storey standing inside the roof carries no stone and so no bay node
    (A2.1). That is not an exemption from the shared grid: the same slots
    become its rooms and its lucarnes, through ``RoledGrid.attic_bays``, and
    this asserts that rather than letting the empty storey quietly narrow the
    claim to "every storey that happens to have bays".
    """
    s = _site(year=1872, ground=GroundProgramme.SHOP)
    node, _ = qualify_building(s)
    roled = assign_roles(solve_structure(s))
    columns = None
    empty = 0
    for storey in node.children:
        bays = [c for c in storey.children if c.kind == "bay"]
        xs = [(round(b.props["x"], 12), round(b.props["w"], 12)) for b in bays]
        if storey.props.get("within_comble"):
            assert xs == [], "a comble storey has no stone frontage to lay out"
            empty += 1
            continue
        if columns is None:
            columns = xs
        assert xs == columns, "a storey drifted out of alignment — it laid itself out"
    assert columns
    if empty:
        attic = [(round(b.start, 12), round(b.width, 12)) for b in roled.attic_bays]
        assert attic, "the comble storey was emitted with no rooms at all"
        assert set(attic) <= set(columns), (
            "the comble is divided on a rhythm of its own, not on the one grid"
        )


def test_every_child_sits_inside_the_slot_that_owns_it():
    """Inside, which is what the name says — not identical to.

    This test used to assert ``child.x == bay.x and child.w == bay.w`` for
    every child, and it passed, and that was the bug: an opening whose
    rectangle IS its bay's rectangle is a glazed slot, and a wall of glazed
    slots is a curtain wall (A4.1). The claim worth making is containment:
    nothing a bay owns may hang out of it into the pier or the neighbour.
    """
    node, _ = qualify_building(_site(year=1872, ground=GroundProgramme.SHOP))
    seen_narrower = False
    for storey in node.children:
        for bay in (c for c in storey.children if c.kind == "bay"):
            x0, w = float(bay.props["x"]), float(bay.props["w"])
            for child in bay.children:
                cx, cw = float(child.props["x"]), float(child.props["w"])
                assert cx >= x0 - 1e-9, f"{child.id} starts left of its bay"
                assert cx + cw <= x0 + w + 1e-9, f"{child.id} runs past its bay"
                if child.kind == "opening" and cw < w - 1e-9:
                    seen_narrower = True
    assert seen_narrower, (
        "every opening filled its whole bay — there is no masonry between the "
        "windows, which is the curtain wall this test exists to catch"
    )


def _facade_openings(node):
    for storey in node.children:
        if storey.kind != "storey":
            continue
        for bay in storey.children:
            if bay.kind != "bay":
                continue
            for child in bay.children:
                if child.kind == "opening":
                    yield storey, bay, child


_CORPUS = (
    dict(year=1830, klass=BuildingClass.MODEST),
    dict(year=1862, ground=GroundProgramme.SHOP),
    dict(year=1871, klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.CAFE),
    dict(year=1888, klass=BuildingClass.GRAND, ground=GroundProgramme.CARRIAGE, parcel_width=16.0),
    dict(year=1899, klass=BuildingClass.COMFORTABLE, corner=True),
)


def test_the_facade_is_stone_with_holes_in_it_not_a_curtain_wall():
    """A4.1, stated as the thing a Parisian would flinch at.

    Every opening must leave masonry on all four sides of itself inside its
    own bay: a pier either side, a spandrel below the sill, a course over the
    lintel. The one exception is deliberate and named — an opening walked
    through rather than leaned on has nothing below it, because that is what
    walking through it means.
    """
    def is_walked_through(storey, opening) -> bool:
        # Either entrance (A6.1) — a carriage arch or a pedestrian door. You
        # walk, or drive, through a door: there is nothing under it, because
        # that is what going through it means.
        if opening.props["opening_type"] in set(catalogue.ENTRANCE_OPENING_TYPES.values()):
            return True
        # A porte-fenêtre: a balcon filant runs along this storey, so the
        # window opens onto a floor you step out on. Read off the emitted
        # balcony rather than off the sill it produced, so the exception is
        # tied to its reason and not to its consequence.
        #
        # **A21.4 dropped the ``rank_from_principal == 0`` that used to stand
        # beside this.** It was the same redundant guess the production rule
        # carried: the reason is the balcony, and a storey with a continuous
        # one is stepped out onto wherever it sits. Keeping the rank here
        # would have made the test disagree with the rule it checks.
        return any(
            c.kind == "balcony" and c.props.get("continuous") for c in storey.children
        )

    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        for storey, bay, opening in _facade_openings(node):
            kind = opening.props["opening_type"]
            bx, bw = float(bay.props["x"]), float(bay.props["w"])
            ox, ow = float(opening.props["x"]), float(opening.props["w"])
            sy, sh = float(storey.props["y"]), float(storey.props["h"])
            oy, oh = float(opening.props["y"]), float(opening.props["h"])
            where = f"{over} {opening.id} ({kind})"
            assert ox >= bx - 1e-9 and ox + ow <= bx + bw + 1e-9, (
                f"{where}: the opening runs out of its own slot"
            )
            assert ox > bx + 1e-9, f"{where}: no pier on the left"
            assert ox + ow < bx + bw - 1e-9, f"{where}: no pier on the right"
            if kind == "carriage_entrance":
                # This used to be the exception — the one opening that WAS
                # its slot, edge to edge, because phase 1 placed a slot
                # exactly one carriage wide and the arch stood on nothing. A
                # slot is a piece of wall everywhere else on the frontage,
                # and it is one here too now: the clear width a carriage
                # needs, plus the jamb the arch lands on either side.
                assert ow == pytest.approx(
                    float(catalogue.door_carriage_entrance().preferred), abs=1e-9
                ), f"{where}: the clear opening is no longer a carriage wide"
                assert bw - ow == pytest.approx(
                    2.0 * float(catalogue.carriage_jamb_width()), abs=1e-9
                ), f"{where}: the jambs either side of the arch are not the catalogue's"
            assert oy + oh < sy + sh - 1e-9, f"{where}: nothing over the lintel"
            assert oy >= sy - 1e-9, f"{where}: the opening starts below the floor"
            if not is_walked_through(storey, opening):
                assert oy > sy + 1e-9, f"{where}: the opening starts at the floor"
            assert ow > 0.0 and oh > 0.0, f"{where}: degenerate opening"


def test_no_opening_in_the_paris_stack_falls_back_to_its_bays_rectangle():
    """``qualify_from_grid`` keeps a fallback for a hand-built layer set that
    names an ``opening_type`` and states no geometry. The real stack must
    never reach it — if it does, some slot has grown an opening no rule sizes
    and the curtain wall is back for that column only, which is far harder to
    see than the whole facade being wrong."""
    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        for _storey, _bay, opening in _facade_openings(node):
            assert opening.props["geometry_stated"] is True, (
                f"{over} {opening.id} ({opening.props['opening_type']}) fell back to "
                "its bay's rectangle"
            )


def test_the_masonry_the_ir_reports_is_the_masonry_the_geometry_leaves():
    """``pier_width`` and ``lintel_height`` are conveniences, and a
    convenience that can disagree with the geometry it summarises is a second
    source of truth. Checked rather than trusted."""
    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        for storey, bay, o in _facade_openings(node):
            assert float(o.props["pier_width"]) == pytest.approx(
                float(o.props["x"]) - float(bay.props["x"]), abs=1e-9
            )
            assert float(o.props["lintel_height"]) == pytest.approx(
                float(storey.props["h"])
                - float(o.props["sill_height"])
                - float(o.props["h"]),
                abs=1e-9,
            )
            assert float(o.props["y"]) == pytest.approx(
                float(storey.props["y"]) + float(o.props["sill_height"]), abs=1e-9
            )


def test_the_ornament_that_frames_an_opening_is_stated_at_the_opening():
    """A surround and a keystone belong to the light, and the IR has to say so.

    Both nodes used to carry the *cell's* rectangle — the surround the whole
    bay, the keystone the storey's ceiling line — and ``render._draw_bay``
    substituted the opening's before drawing either, with a comment explaining
    why the stated one could not be right ("a moulded architrave sized to the
    whole bay would float untethered from the window it frames"). That is one
    fact under two names with the drawn one chosen downstream: the exact shape
    of A4.3, and the same shape as the whole-frontage devanture in A5.1.

    So it is asserted against the opening in the same bay. A consumer that is
    not this renderer — a quantity take-off, a second backend — reads these
    props and gets the architrave the drawing shows.
    """
    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        for storey in node.children:
            if storey.kind != "storey":
                continue
            for bay in storey.children:
                if bay.kind != "bay":
                    continue
                opening = next((c for c in bay.children if c.kind == "opening"), None)
                if opening is None:
                    continue
                ox, oy = float(opening.props["x"]), float(opening.props["y"])
                ow, oh = float(opening.props["w"]), float(opening.props["h"])
                for child in bay.children:
                    if child.kind == "surround":
                        got = tuple(float(child.props[k]) for k in ("x", "y", "w", "h"))
                        assert got == pytest.approx((ox, oy, ow, oh), abs=1e-9), (
                            f"{over} {child.id}: the surround frames "
                            f"{got} and the light it frames is {(ox, oy, ow, oh)}"
                        )
                    if child.kind == "keystone":
                        assert float(child.props["x"]) == pytest.approx(ox, abs=1e-9)
                        assert float(child.props["w"]) == pytest.approx(ow, abs=1e-9)
                        # The crown of the arch, not the ceiling of the room.
                        assert float(child.props["y"]) == pytest.approx(oy + oh, abs=1e-9), (
                            f"{over} {child.id}: the keystone floats "
                            f"{float(child.props['y']) - (oy + oh):.3f} m off its own head"
                        )


def test_across_a_whole_facade_the_noble_floor_carries_the_tallest_openings():
    """The relation A4.1 asks for, read off the emitted building rather than
    off one rule: ordinary windows shorten as they move up from the floor the
    building shows off, with no rule counting storeys.

    **A21.4 split this into the two claims it was always making**, because
    widening the porte-fenêtre to every filant put a walked-through opening at
    the top of the wall and the single sequence stopped holding: heights came
    out ``{0: 2.76, 1: 2.15, 2: 2.48}``, the top storey's window taller than
    the one below it despite standing in a shorter storey.

    That is not the hierarchy failing — it is two different objects being
    compared in one list. A porte-fenêtre is not an ordinary window; this
    module says so everywhere else ("somebody leans on a sill; somebody steps
    over a threshold"). So:

    * ordinary windows — the ones with a sill to lean on — still fall off
      upward, which is the taper doing its work; and
    * the noble floor still carries the TALLEST opening on the facade, which
      is what this test's own name claims and its body never actually checked.

    Both are asserted below. Neither is weaker than what it replaced.
    """
    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        by_rank: dict[int, float] = {}
        tallest_at: dict[int, float] = {}
        for storey, _bay, o in _facade_openings(node):
            if o.props["opening_type"] != "window":
                continue
            rank = int(storey.props["rank_from_principal"])
            if rank < 0:
                continue  # the base and the entresol are their own programme
            tallest_at[rank] = max(tallest_at.get(rank, 0.0), float(o.props["h"]))
            # Ordinary windows only: one with no sill is walked through, and a
            # sequence mixing the two measures a change of kind, not a taper.
            if float(o.props.get("sill_height") or 0.0) > 1e-9:
                by_rank.setdefault(rank, float(o.props["h"]))
        heights = [by_rank[r] for r in sorted(by_rank)]
        assert heights == sorted(heights, reverse=True), (
            f"{over}: window heights do not fall off upward: {by_rank}"
        )
        assert tallest_at, over
        assert max(tallest_at, key=lambda r: (tallest_at[r], -r)) == 0, (
            f"{over}: the noble floor does not carry the tallest opening on the "
            f"facade: {tallest_at}"
        )


def test_a_grand_facade_reads_as_grand_because_of_what_did_not_change():
    """Two facades, same street, same year, same programme, different money.

    The windows must be much bigger and the carriage entrance must not be. If
    both scaled together the two buildings would be photographs of one
    building at two distances, which is the brief's own diagnosis of why
    procedural buildings look like toys.
    """
    widths = {}
    tall = {}
    doors = {}
    for klass in (BuildingClass.MODEST, BuildingClass.GRAND):
        node, _ = qualify_building(
            _site(klass=klass, ground=GroundProgramme.CARRIAGE, parcel_width=16.0, year=1875)
        )
        for storey, _bay, o in _facade_openings(node):
            if o.props["opening_type"] == "window" and int(
                storey.props["rank_from_principal"]
            ) == 0:
                widths[klass] = float(o.props["w"])
                tall[klass] = float(o.props["h"])
            if o.props["opening_type"] == "carriage_entrance":
                doors[klass] = (float(o.props["w"]), float(o.props["h"]))
    assert len(tall) == 2 and len(doors) == 2, f"fixture missed something: {tall} {doors}"
    # **A9.4.** Daly's sixteen buildings split the window in two: the opening
    # WIDTH is 1.04-1.30 m and non-monotonic across the classes (so ABSOLUTE),
    # while the opening HEIGHT at the noble floor is 2.92 / 2.24 / 2.09 m (so
    # PROPORTIONAL). This used to assert only that the grand window's AREA was
    # half again the modest one's, which one number could satisfy by scaling
    # both directions together — the "photographs of one building at two
    # distances" failure. Three assertions now, and the first is the new one.
    assert widths[BuildingClass.MODEST] == pytest.approx(widths[BuildingClass.GRAND]), widths
    assert tall[BuildingClass.GRAND] > 1.25 * tall[BuildingClass.MODEST], tall
    assert doors[BuildingClass.MODEST] == pytest.approx(doors[BuildingClass.GRAND]), doors


def test_storey_scope_properties_are_the_same_in_every_bay_of_a_row():
    """The emitter takes storey-scope properties from the leftmost cell. That
    is only safe because the rules producing them read no horizontal fact —
    asserted here rather than assumed."""
    storey_keys = (
        "socle_present",
        "socle_treatment",
        "shopfront_present",
        "shopfront_variant",
        "ground_treatment",
        "cornice_present",
        "cornice_projection",
        "string_course_present",
        "string_course_kind",
        "balcony_present",
        "balcony_continuous",
        "balcony_projection",
    )
    layers = paris_layers()
    for site in (
        _site(year=1866, ground=GroundProgramme.SHOP),
        _site(year=1893, klass=BuildingClass.GRAND, ground=GroundProgramme.CARRIAGE),
        _site(year=1835, klass=BuildingClass.MODEST, corner=True),
    ):
        roled = assign_roles(solve_structure(site))
        for row in contexts_for(roled, site):
            resolutions = [resolve(c, layers, DecisionStream(site.seed)) for c in row]
            for key in storey_keys:
                values = {r.values.get(key) for r in resolutions}
                assert len(values) == 1, f"{key} varies across a row: {values}"


# ===========================================================================
# I4 — every emitted node records its rule
# ===========================================================================


def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def test_every_emitted_node_has_a_non_empty_trace_naming_a_rule():
    for site in (
        _site(year=1830, klass=BuildingClass.MODEST),
        _site(year=1862, ground=GroundProgramme.SHOP),
        _site(year=1888, klass=BuildingClass.GRAND, ground=GroundProgramme.CARRIAGE, parcel_width=15.0),
        _site(year=1899, klass=BuildingClass.COMFORTABLE, corner=True),
    ):
        node, _ = qualify_building(site)
        for n in _walk(node):
            assert n.trace, f"{n.id} has an empty trace"
            for entry in n.trace:
                assert entry.rule.strip()
                assert entry.detail.strip()
                assert entry.phase in ("structure", "roles", "qualification", "termination")


def test_node_ids_are_unique_and_addressable():
    node, log = qualify_building(_site(year=1872, ground=GroundProgramme.SHOP))
    ids = [n.id for n in _walk(node)]
    assert len(ids) == len(set(ids))
    for i in ids:
        assert find_node(node, i) is not None
    # ...and the log knows about every node that carries qualification entries
    logged = set(log.all_ids())
    assert logged <= set(ids)
    assert logged, "the trace log is empty"


def test_the_trace_log_and_the_node_agree():
    node, log = qualify_building(_site(year=1872, ground=GroundProgramme.SHOP))
    for n in _walk(node):
        recorded = log.explain(n.id)
        if recorded:
            assert [e.rule for e in recorded] == [e.rule for e in n.trace]


# ===========================================================================
# "Why is this here?"
# ===========================================================================


def test_explain_reads_like_an_answer_a_person_can_use():
    site = _site(year=1872, klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    node, _ = qualify_building(site)

    balcony = next(
        (n for n in _walk(node) if n.kind == "balcony"), None
    )
    assert balcony is not None, "this fixture should produce a balcony"
    text = explain(node, balcony.id)

    # the element, and where it is
    assert balcony.id in text
    assert "extent:" in text
    # the rule, named, and the reason in prose
    assert "paris.qualify.base.balcony.ordonnance_1823" in text
    assert "at least 6 m above the pavement" in text
    # the facts the rule was looking at
    assert "level_above_pavement=" in text
    # where it sits in the building
    assert "inside:" in text


def test_explain_shows_what_was_overruled_as_well_as_what_won():
    site = _site(year=1872, klass=BuildingClass.GRAND, ground=GroundProgramme.SHOP)
    node, _ = qualify_building(site)
    # A surround on an upper floor: the ground storey's frames come from the
    # shopfront vocabulary in the BASE layer since A6.7, so the class layer's
    # affordability ladder — the overruling rule this test is about — never
    # bids on them.
    # ...and it must be a surround on an ORDINARY bay. The narrow special has
    # its own vocabulary, so the class layer does not bid on it either, and
    # picking whichever surround came first made this test a hostage to the
    # bay solve — it started failing when A8.6 changed the rhythm, on a
    # building whose ordinary bays were all still there.
    surround = next(
        n
        for storey in node.children
        if int(storey.props["rank_from_principal"]) > 0
        for bay in storey.children
        if bay.kind == "bay" and bay.props.get("slot_name") == "bay"
        for n in bay.children
        if n.kind == "surround"
    )
    text = explain(node, surround.id)
    assert "paris.qualify.klass.surround" in text
    assert "overruled" in text
    assert "paris.qualify.base.surround.diminishes_with_rank" in text


def test_explain_on_a_missing_id_says_so_and_lists_what_exists():
    node, _ = qualify_building(_site())
    text = explain(node, "b/s99/x99")
    assert "no node" in text
    assert "known ids:" in text
    assert "b/s0" in text


def test_resolution_why_names_the_winner_its_layer_and_the_field():
    layers = [
        Layer("base", 0, (_rule(K, "a", "r.a", 0),)),
        Layer("class", 20, (_rule(K, "b", "r.b", 0),)),
    ]
    text = resolve(_ctx(), layers, RNG).why(K)
    assert "r.b" in text and "'class'" in text
    assert "overruled" in text and "r.a" in text


# ===========================================================================
# Determinism and serialisation
# ===========================================================================


def test_seed_plus_situation_is_deterministic():
    site = _site(year=1887, klass=BuildingClass.GRAND, ground=GroundProgramme.SHOP)
    first, _ = qualify_building(site)
    second, _ = qualify_building(site)
    assert to_json(first) == to_json(second)


def test_a_different_seed_is_a_different_building_but_the_same_shape():
    a, _ = qualify_building(_site(seed=1, year=1893, ground=GroundProgramme.SHOP))
    b, _ = qualify_building(_site(seed=2, year=1893, ground=GroundProgramme.SHOP))
    assert [n.id for n in _walk(a)] == [n.id for n in _walk(b)]


def test_the_emitted_facade_round_trips_through_json_losslessly():
    node, _ = qualify_building(
        _site(year=1893, klass=BuildingClass.GRAND, ground=GroundProgramme.CARRIAGE, parcel_width=15.0)
    )
    assert from_json(to_json(node)) == node


def test_the_whole_building_is_hashable():
    """A1.5: the block and trace layers will want nodes in a set."""
    node, _ = qualify_building(_site())
    assert len({node, node}) == 1


# ===========================================================================
# The mezzanine experiment, end to end through the emitter
# ===========================================================================


def _lowest_balconied_rank(heights: list[float]) -> int:
    site = _site()
    roled = assign_roles(_grid(heights, [0.5, 3.0, 3.0, 3.0, 3.0, 0.5]))
    node, _ = qualify_from_grid(roled, site)
    for storey in node.children:
        if any(c.kind == "balcony" for c in _walk(storey)):
            return storey.props["rank_from_principal"]
    raise AssertionError("no balcony anywhere in this building")


def test_the_emitted_facade_moves_its_balcony_when_the_mezzanine_goes():
    """Not just the rule in isolation — the balcony *node* moves, and nothing
    else about the rule set changed."""
    assert _lowest_balconied_rank(WITH_MEZZANINE) == 0
    assert _lowest_balconied_rank(WITHOUT_MEZZANINE) == 1


# ===========================================================================
# User overrides are a layer, and nothing else
# ===========================================================================


def test_a_user_override_wins_and_is_traced_like_any_other_rule():
    def all_windows_are_round(ctx, rng):
        """The owner wanted round-headed windows throughout."""
        if ctx.slot_name != "bay":
            return None
        return Properties(
            {"opening_head": "round"},
            rule="user.override.round_heads",
            specificity=0,
        )

    site = _site(year=1872, ground=GroundProgramme.SHOP)
    node, _ = qualify_building(site, layers=paris_layers(overrides=(all_windows_are_round,)))
    openings = [n for n in _walk(node) if n.kind == "opening" and n.props.get("head")]
    assert openings
    # Asked of the slots the override actually claims — the bays. The entrance
    # is its own slot and this rule declines it, which is the sparse-properties
    # mechanism working rather than the override failing: A6.1 puts a door on
    # every frontage now, and a rule that says "bay" does not mean "door".
    in_bays = [
        o for _s, b, o in _facade_openings(node) if b.props["slot_name"] == "bay"
    ]
    assert in_bays
    assert {o.props["head"] for o in in_bays} == {"round"}
    entrances = [
        o
        for _s, _b, o in _facade_openings(node)
        if o.props["opening_type"] in set(catalogue.ENTRANCE_OPENING_TYPES.values())
    ]
    assert len(entrances) == 1
    assert entrances[0].props["head"] != "round"
    text = explain(node, openings[0].id)
    assert "user.override.round_heads" in text
    assert "The owner wanted round-headed windows throughout." in text


def test_an_override_that_ties_with_a_shipped_rule_still_raises():
    """There is no privileged override channel. An override is a rule, and a
    rule that cannot say why it is more specific gets the same answer as any
    other."""
    tie = _rule("opening_type", "z", "user.tie", 0)
    layers = (Layer("base", 0, (_rule("opening_type", "a", "r.a", 0), tie)),)
    with pytest.raises(RuleConflict):
        resolve(_ctx(), layers, RNG)


# ===========================================================================
# Anti-vacuity: the rules shipped must actually be reachable
# ===========================================================================


def _sweep_sites():
    import random

    rnd = random.Random(4)
    # 480 rather than 240 since A8.6: the bay pitch is bounded by the masonry
    # instead of scaling with the class, so a given parcel is much less likely
    # to leave a remainder that needs a narrow special — the rhythm now
    # absorbs what the class factor used to make awkward. The sweep is widened
    # rather than the thresholds below it lowered; the tests that count
    # specials must still be counting enough of them to prove anything.
    #
    # **A26 reaches the bottom of the range, and the reason is a finding rather
    # than a fixture tweak.** With the bay band at 2.00 / 2.60 / 3.20 the
    # rhythm reaches so much further that **no parcel of 6 m or more needs a
    # narrow special at all** — measured, this sweep produced exactly zero
    # special bays across 480 buildings where it used to produce hundreds.
    # Raising the *count* does not help: 960 buildings over the same range
    # still produce zero, because the cause is reachability and not sampling.
    # What still produces a special is a parcel too narrow to carry one more
    # whole bay, and those now start below 6 m.
    #
    # So the sweep is stratified rather than merely stretched: a share of the
    # sites is drawn from 4.0-7.0 m, the band where the leftover exists at all,
    # and the rest from the range it always used. 4.0 m is comfortably above
    # the 3.44 m at which a carriage entrance and two minimum piers stop
    # fitting, so every site is still a building this generator can build, and
    # this sweep refuses none of them.
    #
    # Measured, so that the shares are chosen and not guessed: 480 buildings
    # over 6-26 m give 0 special columns; 480 over 4.5-26 m give 15; 960 over
    # 4.0-26 m give 49; and 480 with a 45 % narrow share gave 62, clearing
    # every threshold below with margin and without the sweep getting slower.
    # Same discipline as at A8.6: widen the sweep, never lower the thresholds.
    #
    # **A27 widened it once more, for the third time and the same cause.** The
    # entrance now stands IN the repeating pool and takes the frontage's own
    # pitch, so the leftover it used to leave beside itself — 2.35 m of door in
    # a run of 2.6 m bays left 0.25 m of slack every time — is gone, and with
    # it a share of the narrow specials that slack used to buy. Measured, the
    # 480 / 45 % sweep fell from 62 special columns to 34, under the threshold
    # of 50 below. The property those tests assert never wavered: the longest
    # run of identical storeys in a special column stayed at 2 throughout,
    # which is the thing under test. Only the sample fell.
    #
    # So: 720 sites at a 60 % narrow share, measured at 69 special columns.
    # 480 / 65 % gives 55, which clears 50 by too little to be worth having;
    # 960 / 45 % gives 62 and costs twice the runtime. This choice also leaves
    # 288 wide-band sites against the 264 the sweep drew before, so the two
    # rule-coverage tests that share this generator sample the ordinary end of
    # the range no more thinly than they did.
    for _ in range(720):
        yield SiteContext(
            street_width=rnd.uniform(6.0, 32.0),
            parcel_width=(
                rnd.uniform(4.0, 7.0) if rnd.random() < 0.60
                else rnd.uniform(6.0, 26.0)
            ),
            parcel_depth=rnd.uniform(8.0, 25.0),
            year=rnd.randint(1800, 1914),
            klass=rnd.choice(list(BuildingClass)),
            ground=rnd.choice(list(GroundProgramme)),
            corner=rnd.random() < 0.3,
            seed=rnd.randint(0, 10**6),
        )


def test_every_shipped_rule_fires_somewhere_in_a_sweep():
    """A rule that never fires is a rule nobody has tested, and a rule set
    full of them looks like coverage without being any. G4/G5 used the same
    discipline; this is its S6 equivalent."""
    from buildings.solver.fitting import FitInfeasible

    layers = paris_layers()
    fired = {r.__name__: 0 for ly in layers for r in ly.rules}
    for site in _sweep_sites():
        try:
            roled = assign_roles(solve_structure(site))
        except FitInfeasible:
            continue
        rng = DecisionStream(site.seed)
        for row in contexts_for(roled, site):
            for ctx in row:
                for ly in layers:
                    for rule in ly.rules:
                        if rule(ctx, rng) is not None:
                            fired[rule.__name__] += 1
    never = sorted(name for name, n in fired.items() if n == 0)
    assert not never, f"unreachable rules: {never}"


def test_every_named_form_in_the_vocabulary_is_actually_produced():
    """The catalogue of named forms is not aspirational — a sweep produces
    every one of them, so none is a string nothing can reach."""
    from buildings.solver.fitting import FitInfeasible

    seen = {"opening_type": set(), "surround_kind": set(), "string_course_kind": set()}
    layers = paris_layers()
    for site in _sweep_sites():
        try:
            roled = assign_roles(solve_structure(site))
        except FitInfeasible:
            continue
        rng = DecisionStream(site.seed)
        for row in contexts_for(roled, site):
            for ctx in row:
                res = resolve(ctx, layers, rng)
                for key in seen:
                    if key in res.values:
                        seen[key].add(res.values[key])
    assert seen["opening_type"] >= {
        "none",
        "window",
        "shop_bay",
        "carriage_entrance",
        "blind_panel",
        "oeil_de_boeuf",
    }
    assert seen["surround_kind"] >= {"none", "bare_band", "moulded_architrave", "pedimented"}
    assert seen["string_course_kind"] >= {"bandeau", "bandeau_sculpte", "plat_bande"}


def test_resolve_returns_a_properties_as_the_contract_says():
    res = resolve(_ctx(), paris_layers(), RNG)
    assert isinstance(res, Properties)
    assert res.rule == "paris.compose.resolve"
    assert set(res.values) <= set(res.provenance)


# ===========================================================================
# A2.1's downstream consequence — a storey in the comble is not a facade
# ===========================================================================


#: Elements placed at the TOP of the storey they belong to, whose ``h`` is a
#: projection out of the wall rather than a height up it.
_CROWNS = {"cornice", "keystone", "string_course"}


def _attic_storeys(node):
    return [c for c in node.children if c.props.get("within_comble")]


def _descendants(node):
    yield node
    for child in node.children:
        yield from _descendants(child)


def test_a_storey_inside_the_comble_carries_nothing_on_the_stone_facade():
    """The defect A2.1 introduced, stated as the building it produced.

    Making ``Role.ATTIC`` reachable put a storey above the eaves, and the
    composition phase then treated it like any other row of the facade: a
    full-width stone storey with an opening, a surround, a keystone, a balcon
    filant and its ironwork, occupying exactly the volume the roof node
    occupies — a balconied window wall drawn inside the mansard, lit a second
    time by the lucarnes on the slope above it.

    Nothing consumed ``within_comble``; it was recorded in the trace and
    ignored. It is consumed here.
    """
    s = _site(year=1872, ground=GroundProgramme.SHOP, parcel_depth=16.0)
    node, log = qualify_building(s)
    attics = _attic_storeys(node)
    assert attics, "this situation was chosen because it has a storey in its comble"

    for storey in attics:
        assert storey.props["role"] == "attic"
        assert storey.props["on_the_stone_facade"] is False
        assert storey.children == (), (
            f"{storey.id} composed {[c.kind for c in storey.children]} on a storey "
            "that has no stone in front of it"
        )
        # ...and it is still a storey of the building, at its real level, with
        # a trace saying why it is empty rather than silently missing.
        assert storey.props["h"] > 0.0
        rules = {e.rule for e in storey.trace}
        assert "paris.compose.storey.inside_the_comble_carries_no_facade" in rules
        assert log.explain(storey.id)


def test_the_facade_below_the_comble_is_untouched_by_the_suppression():
    """The storeys behind the stone are composed exactly as before — the
    suppression is a statement about where there is no stone, not a new
    opinion about the facade."""
    s = _site(year=1872, ground=GroundProgramme.SHOP, parcel_depth=16.0)
    node, _ = qualify_building(s)
    facade = [c for c in node.children if not c.props.get("within_comble")]
    assert len(facade) >= 3
    for storey in facade:
        assert storey.props["on_the_stone_facade"] is True
        assert [c for c in storey.children if c.kind == "bay"], storey.id
    kinds = {n.kind for st in facade for n in _descendants(st)}
    assert {"opening", "surround"} <= kinds


def test_no_facade_element_anywhere_stands_inside_a_comble():
    """Over the situation space, not over one building: no emitted element of
    the stone facade — opening, surround, keystone, balcony, ironwork, cornice,
    string course, socle, shopfront — has its floor at or above the eaves."""
    from buildings.solver.fitting import FitInfeasible

    stone = {
        "opening",
        "surround",
        "keystone",
        "balcony",
        "ironwork",
        "cornice",
        "string_course",
        "socle",
        "shopfront",
        "bay",
    }
    seen_attics = 0
    for site in _sweep_sites():
        try:
            grid = solve_structure(site)
        except FitInfeasible:
            continue
        roled = assign_roles(grid)
        node, _ = qualify_from_grid(roled, site)
        attics = _attic_storeys(node)
        seen_attics += len(attics)
        for n in _descendants(node):
            if n.kind not in stone:
                continue
            y = float(n.props["y"])
            h = float(n.props["h"])
            if n.kind in _CROWNS:
                # A cornice, a keystone and a string course are placed at the
                # TOP of the storey they belong to, and their `h` is a
                # projection rather than a height. The topmost facade storey's
                # crown therefore sits exactly on the eaves, which is where a
                # cornice belongs.
                assert y <= grid.eaves_height + 1e-9, (
                    f"{n.kind} {n.id} crowns a wall at {y:.3f} m, above the eaves at "
                    f"{grid.eaves_height:.3f} m"
                )
            else:
                assert y + h <= grid.eaves_height + 1e-9, (
                    f"{n.kind} {n.id} runs from {y:.3f} m to {y + h:.3f} m, through the "
                    f"eaves at {grid.eaves_height:.3f} m and into the comble"
                )
    assert seen_attics > 50, (
        f"only {seen_attics} storeys in the sweep stood in a comble — the claim needs "
        "buildings that actually have one"
    )


def test_the_attic_is_lit_by_lucarnes_and_not_twice_over():
    """The whole pipeline: the attic's windows exist, once, on the roof.

    Before the fix the same room had a full-height window wall on the stone
    plane AND a row of dormers over it. The count that matters is that the
    lucarnes are there and the openings are not.
    """
    from buildings.typologies.paris.generate import generate

    s = _site(year=1872, ground=GroundProgramme.SHOP, parcel_depth=16.0)
    root, _ = generate(s)
    attics = [c for c in root.children if c.props.get("within_comble")]
    assert attics
    dormers = [c for c in root.children if c.kind == "dormer"]
    assert dormers, "the attic has to be lit by something"
    for storey in attics:
        assert not [n for n in _descendants(storey) if n.kind == "opening"]
    for d in dormers:
        assert d.props["lights_storey_index"] == attics[0].props["index_from_bottom"]


# ===========================================================================
# Amendment 6 — the door, the leftover, the railings and the shop's frame
# ===========================================================================


def _entrance_openings(node):
    kinds = set(catalogue.ENTRANCE_OPENING_TYPES.values())
    return [o for _s, _b, o in _facade_openings(node) if o.props["opening_type"] in kinds]


def test_every_building_has_exactly_one_entrance():
    """A6.1, and it is the whole of A6.1.

    The census across a block used to read
    ``{window: 108, shop_bay: 27, blind_panel: 27, oeil_de_boeuf: 3}`` — ten
    immeubles and not one way in. Asserted over a wide sweep rather than over
    the canonical case, because the defect's whole character was that it was
    invisible on any single facade you happened to look at: the drawing is
    well-formed, the trace is complete, and there is simply no door.
    """
    checked = 0
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        doors = _entrance_openings(node)
        assert len(doors) == 1, f"{site}: {[d.id for d in doors]}"
        checked += 1
    assert checked > 150


def test_the_entrance_is_on_the_ground_storey_and_reaches_the_pavement():
    """A door you cannot step through is not a door. Its sill is the
    pavement, and it stands on the storey a person arrives at."""
    for over in _CORPUS:
        node, _ = qualify_building(_site(**over))
        (door,) = _entrance_openings(node)
        storey = next(s for s in node.children if any(door is o for o in _walk(s)))
        assert int(storey.props["index_from_bottom"]) == 0, over
        assert float(door.props["y"]) == pytest.approx(float(storey.props["y"]), abs=1e-9)
        assert float(door.props["sill_height"]) == pytest.approx(0.0, abs=1e-9)


def test_the_entrance_is_absolute_in_width_and_in_height():
    """A5.5's rule, held to across A6.1's two doors.

    Both entrances are set by what passes through them, so between a modest
    frontage and a grand one on the same street the door of a given kind is
    the SAME size — while the windows are half again as big. That contrast is
    what the eye reads as scale, and it is the reason the door can serve as
    the ruler the facade is measured against.

    **A14.1** made the height half of that conditional and the width half
    absolute. A two-storey arch's opening rectangle is the HOLE — the leaves
    plus the carved tympanum over them — so the door inside it is
    ``leaf_height``, and that is the figure this compares. The width is
    compared unconditionally, which is the point: the arch may rise two
    storeys and may not widen by a millimetre while doing it.
    """
    by_kind: dict[str, set[tuple[float, float]]] = {}
    tall = 0
    # ``(seed 5, a shop below)`` is the combination that reaches the
    # two-storey arch on this sweep, and it is in here on purpose: an
    # absolute-size assertion that never met the one form designed to be
    # taller would be asserting nothing about A14 at all.
    for klass in BuildingClass:
        for street in (8.0, 20.0):
            for ground in (GroundProgramme.RESIDENTIAL, GroundProgramme.SHOP):
                for seed in (11, 5):
                    node, _ = qualify_building(
                        _site(
                            klass=klass,
                            street_width=street,
                            parcel_width=16.0,
                            ground=ground,
                            seed=seed,
                        )
                    )
                    (door,) = _entrance_openings(node)
                    leaf = door.props.get("leaf_height")
                    tall += leaf is not None
                    height = float(leaf if leaf is not None else door.props["h"])
                    by_kind.setdefault(door.props["opening_type"], set()).add(
                        (round(float(door.props["w"]), 9), round(height, 9))
                    )
    assert tall > 0, "the sweep never reached a two-storey arch"
    assert len(by_kind) == 2, "the sweep should reach both doors"
    for kind, sizes in by_kind.items():
        assert len(sizes) == 1, f"{kind} changed size with the class or the street: {sizes}"


def test_which_entrance_follows_the_class_and_the_street_not_a_coin():
    """The choice is a stated relation, held in the catalogue, and it moves
    only with the two facts it claims to read."""
    wide, narrow = 20.0, 8.0
    assert (
        catalogue.entrance_for(BuildingClass.GRAND, wide).kind
        == catalogue.ENTRANCE_CARRIAGE
    )
    assert (
        catalogue.entrance_for(BuildingClass.GRAND, narrow).kind
        == catalogue.ENTRANCE_PEDESTRIAN
    ), "a carriage cannot draw out of the traffic on an 8 m street"
    assert (
        catalogue.entrance_for(BuildingClass.MODEST, wide).kind
        == catalogue.ENTRANCE_PEDESTRIAN
    ), "a modest household keeps no carriage, however wide the street"
    # Same situation, same answer, every time: no RNG anywhere in the choice.
    for _ in range(5):
        assert catalogue.entrance_for(BuildingClass.COMFORTABLE, 14.0).kind == (
            catalogue.entrance_for(BuildingClass.COMFORTABLE, 14.0).kind
        )


def test_the_entrance_stands_where_the_positional_rule_puts_it():
    """A6.1: "placed by a positional rule — centre, or a stated offset".

    The rule is the middle of the interior run, or half a place left of it
    where the run has no middle; the narrow specials the solver inserted are
    allowed to push it one further place out, and when they do they sit on
    the *other* side, which is the composition answering the offset.
    """
    for site in _sweep_sites():
        try:
            grid = solve_structure(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        interior = [s for s in grid.bays if s.name != "pier_end"]
        doors = [s for s in interior if s.name in catalogue.ENTRANCE_SLOT_NAMES]
        assert len(doors) == 1, site
        place = interior.index(doors[0])
        n_special = sum(1 for s in interior if s.is_special)
        off_axis = abs(2 * place - (len(interior) - 1)) / 2.0
        assert off_axis <= 0.5 + n_special, (
            f"{site}: entrance {off_axis} place(s) off the axis of "
            f"{len(interior)} with {n_special} special(s)"
        )


def test_a_lone_special_answers_the_entrance_from_the_other_side():
    """The brief's own example of a symmetry constraint: "when it sits
    off-centre the composition should answer it — putting the narrow special
    on the opposite side"."""
    seen = 0
    for site in _sweep_sites():
        try:
            grid = solve_structure(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        interior = [s for s in grid.bays if s.name != "pier_end"]
        specials = [i for i, s in enumerate(interior) if s.is_special]
        if len(specials) != 1:
            continue
        door = next(
            i for i, s in enumerate(interior) if s.name in catalogue.ENTRANCE_SLOT_NAMES
        )
        axis = (len(interior) - 1) / 2.0
        if abs(door - axis) < 1e-9:
            continue  # the door is on the axis; there is no offset to answer
        assert (door - axis) * (specials[0] - axis) < 0.0, (
            f"{site}: door at {door}, special at {specials[0]}, axis {axis} — "
            "the special took the same side as the entrance"
        )
        seen += 1
    assert seen > 5, "the sweep never produced an off-centre door with a lone special"


def _special_columns(node):
    """opening_type down each narrow-special column of one facade."""
    columns: dict[int, list[str]] = {}
    for _storey, bay, opening in _facade_openings(node):
        if bay.props.get("is_special"):
            columns.setdefault(round(float(bay.props["x"]), 6), []).append(
                opening.props["opening_type"]
            )
    return [v for _k, v in sorted(columns.items())]


def test_the_leftover_special_is_not_a_column_of_blind_panels():
    """A6.2. A blind panel is legitimate; five of them stacked pavement to
    cornice is a walled-up building."""
    seen = 0
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for column in _special_columns(node):
            if len(column) < 3:
                continue
            seen += 1
            assert len(set(column)) > 1, (
                f"{site}: a special column of {len(column)} storeys carries "
                f"{column[0]!r} on every one of them"
            )
    assert seen > 20, "the sweep never produced a tall special column"


def test_the_special_vocabulary_is_offered_by_storey():
    """The ground storey is solid; the top of the wall may take a roundel; the
    storeys between may take a narrow light. Read off the emitted facades
    across a whole block-sized sweep rather than off the rule."""
    ground: set[str] = set()
    seen: set[str] = set()
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for storey, bay, opening in _facade_openings(node):
            if not bay.props.get("is_special"):
                continue
            seen.add(opening.props["opening_type"])
            if int(storey.props["index_from_bottom"]) == 0:
                ground.add(opening.props["opening_type"])
    assert {"blind_panel", "narrow_window", "oeil_de_boeuf"} <= seen
    assert ground == {"blind_panel"}, f"the ground storey's leftover is wall: {ground}"


def test_no_ironwork_is_emitted_with_nothing_to_see():
    """A6.6. Three ``IronworkNode``s used to arrive with ``h = 0.000`` — a
    rule emitting an element that cannot be seen is a rule putting a lie in
    the IR. Either give it height or do not emit it."""
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for n in _descendants(node):
            if n.kind == "ironwork":
                assert float(n.props["h"]) > 1e-9, f"{site}: {n.id} draws nothing"
                assert float(n.props["w"]) > 1e-9, f"{site}: {n.id} draws nothing"


def test_a_garde_corps_is_as_wide_as_what_it_guards():
    """A6.5. A railing in front of a window is the window's width; a railing
    on a balcon filant is the balcony's. What it may never be is 3.450 m of
    ironwork drawn across two solid masonry piers in front of a 1.322 m
    light."""
    checked = 0
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for _storey, bay, opening in _facade_openings(node):
            rails = [c for c in bay.children if c.kind == "ironwork"]
            if not rails:
                continue
            (rail,) = rails
            guards = rail.props["guards"]
            if guards == "opening":
                assert float(rail.props["x"]) == pytest.approx(
                    float(opening.props["x"]), abs=1e-9
                ), f"{site}: {rail.id} does not start at the light it guards"
                assert float(rail.props["w"]) == pytest.approx(
                    float(opening.props["w"]), abs=1e-9
                ), f"{site}: {rail.id} is not as wide as the light it guards"
                checked += 1
            else:
                assert guards == "balcon_filant"
                assert float(rail.props["w"]) == pytest.approx(
                    float(bay.props["w"]), abs=1e-9
                ), f"{site}: a filant's balustrade stops short of its own slab"
    assert checked > 50


def test_no_pediment_ever_lands_over_a_shop_light():
    """A6.7. Ground-floor surrounds come from the ground floor's own
    vocabulary: a devanture is framed by its joinery, and an ordinary
    ground-floor window by a plain band of stone. A pediment is an
    entablature on consoles over an opening in a wall, and a shopfront has
    neither."""
    seen_devanture = 0
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for storey in node.children:
            if storey.kind != "storey" or int(storey.props["index_from_bottom"]) != 0:
                continue
            for bay in storey.children:
                if bay.kind != "bay":
                    continue
                opening = next((c for c in bay.children if c.kind == "opening"), None)
                for child in bay.children:
                    if child.kind != "surround":
                        continue
                    kind = child.props["surround_kind"]
                    assert kind != "pedimented", f"{site}: {child.id} over a ground-floor light"
                    if opening is not None and opening.props["opening_type"] == "shop_bay":
                        assert kind == catalogue.ground_floor_surround("shop_bay")
                        seen_devanture += 1
    assert seen_devanture > 20


# ===========================================================================
# A7.2 — the count arrives in the IR
# ===========================================================================


#: Every ornamented node kind, and the count key it must state. A consumer
#: that cannot find one of these has to divide a dimension by a spacing of its
#: own, which is the whole class of defect A7.2 removed.
_COUNTED = {
    ("cornice", "ornament_count"),
    ("socle", "course_columns"),
    ("socle", "course_rows"),
    ("balcony", "bracket_count"),
    ("ironwork", "ornament_count"),
}


def test_every_ornamented_node_states_how_many():
    """Thirteen counts used to be decided inside ``render/svg/elements.py``,
    from a dimension the IR handed it and a spacing it had chosen. They are
    qualification's now, so every node that carries a rhythm must arrive with
    the count already on it."""
    seen = set()
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for n in _descendants(node):
            for kind, key in _COUNTED:
                if n.kind != kind:
                    continue
                assert key in n.props, f"{site}: {n.id} states no {key}"
                assert int(n.props[key]) >= 1, f"{site}: {n.id} counts {n.props[key]}"
                seen.add((kind, key))
    assert seen == _COUNTED, f"the sweep never exercised {_COUNTED - seen}"


def test_a_count_is_counted_across_the_extent_its_own_node_states():
    """A count is only meaningful against a length, and the length has to be
    the node's own. A balconette is the light's width, not the bay's, so the
    consoles it states are the consoles a light's width of slab needs — a
    count taken across the bay and drawn across the light would be the same
    two-numbers-for-one-fact drift A4.7 found, wearing arithmetic."""
    checked = 0
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        for _storey, bay, opening in _facade_openings(node):
            for child in bay.children:
                if child.kind != "balcony" or child.props.get("continuous"):
                    continue
                assert float(child.props["w"]) == pytest.approx(
                    float(opening.props["w"]), abs=1e-9
                )
                per_metre = int(child.props["bracket_count"]) / float(child.props["w"])
                assert per_metre <= 4.0, (
                    f"{site}: {child.id} crowds {child.props['bracket_count']} consoles "
                    f"into {child.props['w']:.3f} m"
                )
                checked += 1
    assert checked > 20


def test_the_frontage_of_a_richer_owner_carries_more_ornament_per_metre():
    """Ordering only, on the IR rather than on the modules: the point of
    putting the count upstream is that a grand facade and a modest one now
    differ in how finely they are worked and not only in how big they are."""
    per_metre = {}
    for klass in (BuildingClass.MODEST, BuildingClass.GRAND):
        courses = width = 0.0
        for seed in range(8):
            site = SiteContext(
                street_width=20.0, parcel_width=13.0, parcel_depth=14.0,
                year=1865, klass=klass, ground=GroundProgramme.SHOP,
                corner=False, seed=seed,
            )
            node, _ = qualify_building(site)
            for n in _descendants(node):
                if n.kind != "socle":
                    continue
                courses += int(n.props["course_rows"])
                width += float(n.props["h"])
        per_metre[klass] = courses / width
    assert per_metre[BuildingClass.GRAND] > per_metre[BuildingClass.MODEST], per_metre


# ===========================================================================
# A7.5 — a special column varies up the facade
# ===========================================================================


def test_no_special_column_reads_as_a_stack_of_one_element():
    """A7.5, measured on whole buildings rather than on the helper. Before
    the cap, 19-30% of special columns (depending on the sweep) carried three
    or four identical storeys — worst case four ``blind_panel`` under a
    single oeil-de-boeuf, which is A6.2's walled-up frontage with a hat on.
    """
    columns = 0
    worst = 1
    for site in _sweep_sites():
        try:
            node, _ = qualify_building(site)
        except (FitInfeasible, catalogue.EntranceCannotFit):
            continue
        by_x: dict[float, list[str]] = {}
        for storey in node.children:
            if storey.kind != "storey":
                continue
            for bay in storey.children:
                if bay.kind != "bay" or not bay.props.get("is_special"):
                    continue
                opening = next(
                    (c for c in bay.children if c.kind == "opening"), None
                )
                by_x.setdefault(round(float(bay.props["x"]), 6), []).append(
                    str(opening.props["opening_type"]) if opening is not None else "none"
                )
        for x, column in by_x.items():
            if len(column) < 2:
                continue
            columns += 1
            run = longest = 1
            for a, b in zip(column, column[1:]):
                run = run + 1 if a == b else 1
                longest = max(longest, run)
            assert longest <= 2, f"{site}: the special column at x={x} reads {column}"
            worst = max(worst, longest)
    assert columns > 50, f"the sweep found too few special columns: {columns}"
    assert worst == 2, "no column ever reached the cap — the sweep proves nothing"


# ===========================================================================
# A9.2 — above the ground floor, the column over a carriage arch is a bay
# ===========================================================================


def test_the_column_over_a_carriage_arch_is_an_ordinary_bay_above_the_pavement():
    """**A9.2's second requirement.** A porte cochère is a ground-floor fact.

    The slot phase 1 places for it stands in the bay run for the full height
    of the facade, and while it was 3.80 m wide — the old INFERRED 3.00 m
    clear plus two jambs, against a stated 3.40 m maximum for a bay — that
    slot was a scar the width of a carriage running from pavement to cornice.
    At Daly's printed 2.60 m clear the slot is exactly 3.40 m, so it sits
    inside the band the masonry states and the column reads as what it is:
    the widest bay on the frontage, and an ordinary one.

    Asserted the way the eye reads it, which is not the slot width but the
    window in it: on every storey above the base, the opening over the arch
    must be the same kind, the same size and the same shape as the openings
    in the ordinary bays beside it.
    """
    site = _site(
        klass=BuildingClass.GRAND, ground=GroundProgramme.CARRIAGE,
        parcel_width=16.0, street_width=20.0, year=1865,
    )
    node, _ = qualify_building(site)
    grid = solve_structure(site)

    door_index = next(
        i for i, s in enumerate(grid.bays) if s.name in catalogue.ENTRANCE_SLOT_NAMES
    )
    assert grid.bays[door_index].name == catalogue.ENTRANCE_CARRIAGE
    # The slot itself fits inside the structural band a bay is held to.
    from buildings.typologies.paris import structure

    assert (
        float(structure._BAY_PITCH_MIN)
        <= grid.bays[door_index].width
        <= float(structure._BAY_PITCH_MAX) + 1e-9
    ), grid.bays[door_index].width

    checked = 0
    for storey in node.children:
        if storey.kind != "storey" or storey.props.get("role") == "base":
            continue
        bays = [c for c in storey.children if c.kind == "bay"]
        if len(bays) < 2:
            continue
        openings = {}
        for i, bay in enumerate(bays):
            op = next((c for c in bay.children if c.kind == "opening"), None)
            if op is not None:
                openings[i] = op
        over_the_door = openings.get(door_index)
        neighbours = [op for i, op in openings.items() if i != door_index]
        if over_the_door is None or not neighbours:
            continue
        checked += 1
        assert over_the_door.props["opening_type"] == "window", storey.props.get("role")
        for other in neighbours:
            if other.props["opening_type"] != "window":
                continue
            assert float(over_the_door.props["w"]) == pytest.approx(
                float(other.props["w"]), abs=1e-9
            ), "the window over the arch is a different width from its neighbours'"
            assert float(over_the_door.props["h"]) == pytest.approx(
                float(other.props["h"]), abs=1e-9
            ), "the window over the arch is a different height from its neighbours'"
            assert over_the_door.props.get("surround_kind") == other.props.get(
                "surround_kind"
            ), "the column over the arch is dressed differently from the wall beside it"
    assert checked >= 2, "no storey above the base carried both an arch column and a bay"


def _dormer_count_and_door(**site_kwargs) -> tuple[int, str]:
    """How many lucarnes this building carries, and which door it has."""
    from buildings.typologies.paris.generate import generate, walk

    s = SiteContext(parcel_depth=18.0, year=1865, seed=7, **site_kwargs)
    node, _ = generate(s)
    count = sum(1 for n in walk(node) if n.kind == "dormer")
    door = next(
        b.name for b in solve_structure(s).bays if b.name in catalogue.ENTRANCE_SLOT_NAMES
    )
    return count, door


def test_the_lucarne_count_is_the_comble_s_own_and_never_the_class_s():
    """**A9.1, closed at A10.3 — and, as with D6, the model was right and the
    metric was wrong.**

    **A15.1 adds the ground programme to the bucket key**, and it is not a
    loosening: the comble now stands one or two storeys of *chambres de bonne*
    and a second row of lucarnes goes with the second storey, so a shop
    frontage and a residential one on the same parcel legitimately carry
    different roofscapes. That is a PROGRAMME difference — which floors the
    trade took out of the stone and where the households went — and the claim
    being asserted here is untouched by it: within one programme, the four
    classes get the same roofscape exactly.

    A comble is floor rather than show. Before A9.1 the dormer count on one
    16 m frontage read 5 / 5 / 4 / 4 down the class ladder — the modest
    building got the biggest roofscape, which is backwards — and two things
    were doing it, neither of them about the comble: the bay pitch carried a
    class trend (gone; Daly's sixteen buildings are non-monotonic in it) and
    the carriage entrance took 3.80 m of frontage where a bay may take
    3.40 m (Daly's printed 2.600 m clear width makes the slot exactly
    3.40 m).

    A10.3 measured a residual fall on 9 of 21 class/frontage combinations
    (12 m: 4/4/3/3, 18 m: 6/6/5/5, 20 m: 7/7/6/6) and read it as the defect
    surviving. It is not the defect, and the giveaway is that those counts
    are **the axis counts of the same frontages, digit for digit**: the
    roofscape is not falling, the frontage under it is, and it is falling for
    the one reason A10.2 prices — the two richer classes have a porte cochère
    and the two poorer ones a porte piétonne, and an arch takes 1.05 m more
    frontage than a door. The comble does not know where the carriages go in;
    it counts the axes it is standing on.

    So the contract here is stated the sharp way rather than as "must not
    fall": **the lucarne count is a function of the comble's own frontage —
    the axes, the street the gabarit is drawn from, and whether the roof
    hips — and class does not appear in it at all.** Two buildings of any two
    classes on one parcel with one door get the same roofscape, exactly, not
    "give or take one".
    """
    buckets: dict[tuple[float, float, bool, str], dict[BuildingClass, int]] = {}
    for parcel in (10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0):
        for street in (10.0, 20.0, 30.0):
            for corner in (False, True):
                for ground in (
                    GroundProgramme.RESIDENTIAL,
                    GroundProgramme.SHOP,
                    GroundProgramme.CARRIAGE,
                ):
                    for klass in BuildingClass:
                        count, door = _dormer_count_and_door(
                            street_width=street, parcel_width=parcel,
                            klass=klass, ground=ground, corner=corner,
                        )
                        key = (parcel, street, corner, door, ground)
                        buckets.setdefault(key, {})[klass] = count
    assert buckets
    ladder = list(BuildingClass)
    for (parcel, street, corner, door, ground), by_class in sorted(
        buckets.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3], kv[0][4].value)
    ):
        counts = set(by_class.values())
        if not corner:
            assert len(counts) == 1, (
                f"a {parcel:.0f} m frontage on a {street:.0f} m street "
                f"(mid-block, {door}, {ground.value}) carries "
                f"{sorted(counts)} lucarnes depending on class — a comble is floor, "
                "not show, and class must not appear in its roofscape"
            )
            continue
        # **A30 — the hipped corner is the one exemption, and it is geometry
        # rather than show.** A lucarne's apron is the deeper of the plumber's
        # zinc and the cornice standing on the same eaves
        # (``terminate._lucarne_apron``); a cornice is
        # ``_CORNICE_FRACTION x the storey it crowns``, and storey heights are
        # class-scaled, so a grander building's lucarne sets its foot higher.
        # Mid-block that costs nothing. On a hip the roof surface falls away
        # toward the returns, so a foot set higher genuinely runs out of roof
        # on the outer bays and those lucarnes are not drawn.
        #
        # That is the comble answering to the FACADE's real height, which is
        # what "floor, not show" permits — the alternative was to let the
        # cornice go on cutting the lucarnes (H83 overlapped by 0.152 m) or to
        # spend ``_DORMER_FACE_MINIMUM``, a window an adult has to see out of
        # standing. Measured at the time of writing: 7 of 182 buckets split,
        # every one a corner, always by exactly 2.
        #
        # The residual claim is the one A9.1 actually cared about, and it is
        # asserted rather than skipped: **the roofscape never grows as the
        # building gets grander.** The original defect was a 16 m frontage
        # reading 5 / 5 / 4 / 4 down the ladder — the modest building with the
        # biggest roofscape. A deeper cornice can only ever take lucarnes off
        # a hip, never add them.
        seen = [by_class[k] for k in ladder if k in by_class]
        assert seen == sorted(seen, reverse=True), (
            f"a {parcel:.0f} m frontage on a {street:.0f} m street "
            f"(corner, {door}, {ground.value}) carries {seen} lucarnes down the "
            f"class ladder {[k.name for k in ladder if k in by_class]} — on a hip "
            "the count may fall as the cornice deepens, but it must never RISE: "
            "that is A9.1's original defect, the modest building with the "
            "biggest roofscape"
        )

    # The exact case A9.1 names, which used to read 5 / 5 / 4 / 4.
    reference = [
        _dormer_count_and_door(
            street_width=20.0, parcel_width=16.0,
            klass=klass, ground=GroundProgramme.RESIDENTIAL,
        )[0]
        for klass in BuildingClass
    ]
    assert len(set(reference)) == 1, f"A9.1's reference case is still class-dependent: {reference}"


def test_the_roofscape_has_no_rhythm_of_its_own():
    """**A10.3.** Why the count above cannot be class-dependent: it is not a
    count at all, it is whole rows of one lucarne per window axis.

    Mid-block the number of dormers is an exact multiple of the number of
    lit bays — the axes ``RoledGrid.lit_bays`` names, entrance column
    included — because ``terminate`` hangs one lucarne on each of them per
    band of brisis. A roofscape that invented its own spacing could not
    satisfy this, and would be free to drift with anything it liked,
    including the purse.

    A10.3's residual is therefore not reachable by changing the comble: the
    only way the count moves is if the axis count moves, and A10.2's test
    shows the axis count is a function of the frontage and the door.
    """
    from buildings.typologies.paris.generate import generate, walk
    from buildings.typologies.paris.roles import assign_roles

    checked = 0
    for parcel in (10.0, 14.0, 16.0, 20.0):
        for street in (10.0, 20.0, 30.0):
            for klass in BuildingClass:
                s = SiteContext(
                    street_width=street, parcel_width=parcel, parcel_depth=18.0,
                    year=1865, klass=klass, ground=GroundProgramme.RESIDENTIAL,
                    corner=False, seed=7,
                )
                node, _ = generate(s)
                count = sum(1 for n in walk(node) if n.kind == "dormer")
                axes = len(assign_roles(solve_structure(s)).lit_bays)
                assert axes > 0
                assert count % axes == 0, (
                    f"{count} lucarnes over {axes} axes on a {parcel:.0f} m frontage: "
                    "the roofscape has invented a rhythm of its own"
                )
                checked += 1
    assert checked == 48


# ===========================================================================
# A13 — what the base block emits
# ===========================================================================


def _a13_building(seed: int):
    return qualify_building(
        _site(
            street_width=22.0,
            parcel_width=14.0,
            parcel_depth=18.0,
            year=1865,
            klass=BuildingClass.COMFORTABLE,
            ground=GroundProgramme.SHOP,
            seed=seed,
        )
    )[0]


def _a13_storeys(building):
    return {
        s.props["role"]: s
        for s in building.children
        if s.kind == "storey"
    }


def test_the_base_block_emits_two_storeys_of_one_socle():
    """A13.1 in the IR: the entresol carries the base's stone, in its own
    rectangle, with the same treatment, and the trace says why it is there."""
    for seed in range(6):
        storeys = _a13_storeys(_a13_building(seed))
        socles = {
            role: next((c for c in st.children if c.kind == "socle"), None)
            for role, st in storeys.items()
        }
        assert socles["base"] is not None
        assert socles["mezzanine"] is not None, "the base stops short of the entresol"
        assert socles["mezzanine"].props["treatment"] == socles["base"].props["treatment"]
        # Its own rectangle — the entresol's, stacked on the ground floor's,
        # with no gap and no overlap between them.
        base, mezz = socles["base"].props, socles["mezzanine"].props
        assert float(mezz["y"]) == pytest.approx(float(base["y"]) + float(base["h"]))
        assert float(mezz["h"]) > 0.0
        rules = {e.rule for e in socles["mezzanine"].trace}
        assert "paris.qualify.base.socle.carries_the_wall" in rules
        assert any("entresol" in e.detail for e in socles["mezzanine"].trace), (
            "the entresol's socle does not say which form of entresol it faces"
        )


def test_the_band_that_crowns_the_base_hangs_where_a_reader_can_see_it():
    """A13.1's emphasis, end to end. The crowning course is emitted at the top
    of the commercial base — the level ``block.py`` aligns the whole street on
    — and it is deeper than the line inside the base."""
    building = _a13_building(3)
    storeys = _a13_storeys(building)
    courses = {
        role: next((c for c in st.children if c.kind == "string_course"), None)
        for role, st in storeys.items()
    }
    inside = courses["mezzanine"]
    crown = courses["principal"]
    assert inside is not None and crown is not None
    top_of_base = float(storeys["mezzanine"].props["y"]) + float(
        storeys["mezzanine"].props["h"]
    )
    assert float(crown.props["y"]) == pytest.approx(top_of_base)
    assert crown.props["course_kind"] == "entablature"
    assert float(crown.props["h"]) > float(inside.props["h"])


def test_the_devanture_states_its_bands_once_and_stays_in_the_rez_de_chaussee():
    """A17.2. A13 had the shopfront framework span the rez-de-chaussée and the
    entresol, splitting its soubassement and its enseigne board between the
    two registers so that neither landed at the storey line. No plate shows
    such a framework — 77 and 120 bd de Sébastopol both close the devanture at
    a full-width entablature — so the shopfront stands in one storey and
    carries both of its bands there.

    Swept over every seed, because the invented form used to be drawn about
    half the time."""
    for seed in range(24):
        storeys = _a13_storeys(_a13_building(seed))
        ground = [
            c
            for bay in storeys["base"].children
            for c in bay.children
            if c.kind == "shopfront"
        ]
        assert ground, f"seed {seed}: the ground floor sells nothing"
        for node in ground:
            assert float(node.props["threshold_height"]) > 0.0, node.id
            assert float(node.props["fascia_depth"]) > 0.0, (
                f"{node.id}: the devanture lost the signboard that closes it"
            )
        # And the entresol carries no devanture at all — neither a framework
        # of its own nor the upper half of the one below it.
        upper = [
            c
            for bay in storeys["mezzanine"].children
            for c in bay.children
            if c.kind == "shopfront"
        ]
        assert upper == [], (
            f"seed {seed}: the devanture reached the entresol again"
        )
        # What is up there is glazed stone: openings, and no shop bay.
        mezz_shops = [
            c
            for bay in storeys["mezzanine"].children
            for c in bay.children
            if c.kind == "opening" and c.props.get("opening_type") == "shop_bay"
        ]
        assert mezz_shops == [], f"seed {seed}: entresol bays are shop glass"


def test_no_part_of_the_base_block_is_emitted_without_extent():
    """A10.5, over both entresol head forms. Whatever the base block emits, it has
    extent: nothing here is a zero-width node standing in for an absence."""
    for seed in range(12):
        storeys = _a13_storeys(_a13_building(seed))
        for role in ("base", "mezzanine"):
            for node in _descendants(storeys[role]):
                if node.props.get("absence") is not None:
                    continue
                for key in ("w", "h"):
                    value = node.props.get(key)
                    if value is None:
                        continue
                    if key == "h" and node.kind == "keystone":
                        continue  # documented line-at-the-crown
                    assert float(value) > 0.0, f"{node.id} ({node.kind}) has {key}=0"


# ===========================================================================
# A14 — the two-storey arched entrance, in the IR
# ===========================================================================
#
# The arch is ONE architectural object drawn across TWO registers of the grid.
# The wall of a storey is a course of masonry, and a rectangle handed across
# the joint between two
# of them would be painted over by the storey it trespasses into. So what
# follows asserts that the two registers stack into one arch — same width, same
# jambs, no gap — and that the census that counts entrances still finds one.


_A14_SITE = dict(
    street_width=22.0,
    parcel_width=14.0,
    parcel_depth=18.0,
    year=1865,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
)


def _a14_building(**over):
    """A commercial boulevard frontage whose entrance rises through the
    entresol, and the two register nodes of its arch."""
    node, _ = qualify_building(_site(**dict(_A14_SITE, **over)))
    lower = upper = None
    for _storey, _bay, opening in _facade_openings(node):
        register = opening.props.get("arch_register")
        if register == "leaves":
            lower = opening
        elif register == "arch_head":
            upper = opening
    assert lower is not None and upper is not None, (
        "this situation was chosen because its entrance takes the two-storey arch"
    )
    return node, lower, upper


def _a14_seed() -> int:
    for seed in range(64):
        node, _ = qualify_building(_site(**dict(_A14_SITE, seed=seed)))
        if any(
            o.props.get("arch_register") == "leaves"
            for _s, _b, o in _facade_openings(node)
        ):
            return seed
    raise AssertionError("no seed in 64 produced a two-storey arch")


def test_the_two_registers_of_one_arch_stack_into_one_opening():
    """Same width, same jambs, and the upper register's floor is the lower
    one's ceiling to the last bit. If these three drift the drawing shows two
    stacked holes instead of one arch, and no amount of care in the renderer
    can put that back together."""
    _node, lower, upper = _a14_building(seed=_a14_seed())
    assert float(upper.props["w"]) == pytest.approx(float(lower.props["w"]), abs=1e-9)
    assert float(upper.props["x"]) == pytest.approx(float(lower.props["x"]), abs=1e-9)
    assert float(upper.props["y"]) == pytest.approx(
        float(lower.props["y"]) + float(lower.props["h"]), abs=1e-9
    )
    assert float(lower.props["sill_height"]) == pytest.approx(0.0, abs=1e-9)
    assert float(upper.props["sill_height"]) == pytest.approx(0.0, abs=1e-9)
    # The lower register keeps no lintel band: the arch carries the floor
    # structure up into the entresol, which is what the form buys.
    assert float(lower.props["lintel_height"]) == pytest.approx(0.0, abs=1e-9)


def test_the_head_is_round_and_carries_its_rise_into_the_ir():
    """The renderer's own fallback head depth is
    ``min(0.5, max(0.15, w * 0.30))`` — on a 2.60 m arch a 0.50 m bow where a
    semicircle was decided. So the rise travels stated, and it is half the
    span because that is what "round" means."""
    _node, _lower, upper = _a14_building(seed=_a14_seed())
    assert upper.props["head"] == "round"
    assert float(upper.props["head_rise"]) == pytest.approx(
        float(upper.props["w"]) / 2.0, abs=1e-9
    )
    assert float(upper.props["head_rise"]) <= float(upper.props["h"]) + 1e-9


def test_nothing_crosses_the_arch():
    """**A20.1**, and the exact inverse of what this used to assert.

    A14.1 put a balconette in the arch's upper register, in its own words: "the
    entresol's opening in that bay is inside the arch — a balconette with
    ironwork". No plate shows one. ``daly_detail_56`` draws this object at full
    scale — 2 et 4 bd de Sébastopol, the 5.01 m entrance — as one joinery
    assembly inside one frame with an unbroken architrave up both sides;
    ``daly_elevation_52`` draws the carriage form at 39 rue Neuve des Mathurins
    as leaves running into a carved tympanum inside a single archivolt. Nothing
    crosses either.

    A rail across a *porte cochère* would also be a rail across the way in.
    """
    node, _lower, upper = _a14_building(seed=_a14_seed())
    bay = next(
        b
        for s in node.children if s.kind == "storey"
        for b in s.children if b.kind == "bay"
        and any(c is upper for c in b.children)
    )
    assert [c for c in bay.children if c.kind == "ironwork"] == [], (
        "the arch's head carries a railing — that is the A14.1 balconette, "
        "and A20.1 retracted it"
    )
    assert [c for c in bay.children if c.kind == "balcony"] == []


def test_the_agrafe_stands_at_the_crown_of_the_arch():
    """A sculpted keystone at the head, named by the same dated draw as every
    other carved stone on the frontage — one building, one sculptor."""
    node, _lower, upper = _a14_building(seed=_a14_seed())
    bay = next(
        b
        for s in node.children if s.kind == "storey"
        for b in s.children if b.kind == "bay"
        and any(c is upper for c in b.children)
    )
    (agrafe,) = [c for c in bay.children if c.kind == "keystone"]
    assert float(agrafe.props["y"]) == pytest.approx(
        float(upper.props["y"]) + float(upper.props["h"]), abs=1e-9
    )
    assert agrafe.props["keystone_kind"]


def test_the_upper_register_is_not_counted_as_a_second_entrance():
    """A6.1 is "exactly one entrance", and the arch's upper light is the top
    of the one door rather than a second one. If it carried an entrance
    ``opening_type`` the census would find two, and the invariant that has
    caught every missing-door defect in this project would start passing for
    the wrong reason."""
    node, _lower, upper = _a14_building(seed=_a14_seed())
    assert len(_entrance_openings(node)) == 1
    assert upper.props["opening_type"] not in set(
        catalogue.ENTRANCE_OPENING_TYPES.values()
    )
    assert upper.props["opening_type"] == catalogue.ENTRANCE_ARCH_HEAD_OPENING


def test_the_arch_keys_are_absent_on_every_other_opening():
    """A node carrying ``arch_register: None`` is a node claiming to have been
    asked a question it was never asked — and it would put three empty keys on
    every window in every golden master. Stated where true, absent elsewhere."""
    node, lower, upper = _a14_building(seed=_a14_seed())
    for _s, _b, opening in _facade_openings(node):
        if opening is lower or opening is upper:
            continue
        for key in ("arch_register", "leaf_height", "head_rise"):
            assert key not in opening.props, f"{opening.id} carries {key}"
    for over in _CORPUS:
        plain, _ = qualify_building(_site(**over))
        for _s, _b, opening in _facade_openings(plain):
            assert "arch_register" not in opening.props, opening.id
