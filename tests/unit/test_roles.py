"""Unit tests for the roles phase (S4): ``assign_roles`` and ``RoledGrid``.

Gate G4 checks are exercised directly here: a five-storey and a nine-storey
stack get correct roles from the identical predicates (no special-casing),
the base exclusion is load-bearing (a tall ground floor must never win
"tallest"), and removing the mezzanine moves the principal floor's absolute
position by itself, with no code change — the concrete, testable form of the
brief's "removes the balcony up a floor by itself" claim at the level this
phase actually owns (position and role), one layer below where the balcony
itself gets decided (S6).
"""

from __future__ import annotations

import inspect
import re

import pytest

from buildings.quantity import Reg
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import PlacedSlot, SlotKind
from buildings.typologies.paris import roles as roles_module
from buildings.typologies.paris.reglement import Era, RoofEnvelope
from buildings.typologies.paris.roles import Role, RoledGrid, assign_roles
from buildings.typologies.paris.structure import Grid, solve_structure


def _slot(name: str, start: float, width: float, kind: SlotKind = SlotKind.REPEATING) -> PlacedSlot:
    return PlacedSlot(name=name, kind=kind, start=start, width=width)


def _stack(heights: list[float], names: list[str] | None = None) -> tuple[PlacedSlot, ...]:
    names = names or ["storey"] * len(heights)
    slots = []
    cursor = 0.0
    for name, h in zip(names, heights):
        slots.append(_slot(name, cursor, h))
        cursor += h
    return tuple(slots)


def _grid(
    storeys: tuple[PlacedSlot, ...],
    cornice_height: float,
    bays: tuple[PlacedSlot, ...] = (),
    eaves_height: float | None = None,
) -> Grid:
    """A synthetic ``Grid`` built directly, bypassing ``solve_structure`` —
    exactly what S4 must accept, since it is contractually forbidden from
    reading anything but the ``Grid`` itself."""
    from buildings.typologies.paris.reglement import GabaritEnvelope

    envelope = GabaritEnvelope(
        era=Era.SECOND_EMPIRE,
        street_width=18.0,
        facade_height=cornice_height,
        roof_envelope=RoofEnvelope.DIAGONAL_45,
        arc_radius=0.0,
        ridge_height=6.0,
        parcel_depth=15.0,
    )
    return Grid(
        storeys=storeys,
        bays=bays or (_slot("pier_end", 0.0, 0.3, SlotKind.FLEXIBLE),),
        cornice_height=Reg(cornice_height, "test fixture"),
        # These fixtures set the cornice line to say where the stone stops,
        # which is exactly what the eaves line is; ``cornice_height`` remains
        # the legal ceiling, and the two coincide for a fixture that builds
        # right up to it. Passing it explicitly keeps every attic test below
        # asking the question it was written to ask.
        eaves_height=eaves_height if eaves_height is not None else cornice_height,
        envelope=envelope,
        account=("test fixture",),
    )


def _site(**overrides) -> SiteContext:
    defaults = dict(
        street_width=18.0,
        parcel_width=14.0,
        parcel_depth=15.0,
        year=1875,
        klass=BuildingClass.ORDINARY,
        ground=GroundProgramme.RESIDENTIAL,
        corner=False,
        seed=0,
    )
    defaults.update(overrides)
    return SiteContext(**defaults)


def _role_by_index(rg: RoledGrid) -> dict[int, Role]:
    return {rs.index_from_bottom: rs.role for rs in rg.storeys}


# --------------------------------------------------------------------- Base


def test_base_is_the_bottom_slot_unconditionally() -> None:
    g = _grid(_stack([4.0, 3.2, 3.0, 2.8]), cornice_height=20.0)
    rg = assign_roles(g)
    assert rg.storeys[0].role is Role.BASE
    assert rg.storeys[0].index_from_bottom == 0


def test_single_storey_grid_is_just_a_base() -> None:
    g = _grid(_stack([3.5]), cornice_height=20.0)
    rg = assign_roles(g)
    assert len(rg.storeys) == 1
    assert rg.storeys[0].role is Role.BASE


# --------------------------------------------------------------------- Principal / base exclusion


def test_base_exclusion_is_load_bearing() -> None:
    """A Paris ground floor is routinely taller than the noble floor above
    it. 'Tallest slot' without excluding the base would wrongly pick the
    ground floor here — this is the named regression the contract calls
    for."""
    heights = [4.6, 3.4, 3.1, 2.9]  # ground (0) is the tallest slot overall
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert by_idx[0] is Role.BASE
    assert by_idx[1] is Role.PRINCIPAL  # the tallest slot *above* the base
    assert Role.PRINCIPAL not in {by_idx[0]}


def test_principal_is_the_tallest_not_the_first_tall_one() -> None:
    """Principal must be genuinely the tallest habitable slot above base and
    mezzanine, not merely the first slot encountered that looks tall — a
    taller slot placed later in the stack must still win."""
    heights = [3.5, 3.0, 3.6, 2.8, 2.6]  # index 2, not index 1, is tallest
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert by_idx[2] is Role.PRINCIPAL
    assert by_idx[1] is not Role.PRINCIPAL


def test_a_building_whose_etages_are_equal_has_no_piano_nobile() -> None:
    """**A9.4.** This test used to be ``test_principal_ties_break_to_the_lowest``
    and asserted that a tie made the lower slot the noble floor. Daly says a
    tie means there is no noble floor at all.

    His two Troisième Classe buildings have étages equal within 0.07 m —
    3.00 / 3.07 / 3.00 / 2.84 and 3.00 / 3.00 / 2.93 / 3.11 — and no
    compressed level under them either, and the measurement pass records the
    consequence plainly: *"Troisième has neither, and no piano nobile at
    all"*. So "has a principal floor" is a fact about the section, and a
    building that did not build a floor to show off does not get one
    assigned by a tie-break.

    Note what does NOT happen: no rule anywhere tests for the missing role.
    Rank is measured from the first letting floor instead, so ornament still
    thins upward and openings still shorten upward on a section with no peak.
    """
    heights = [3.5, 3.2, 3.2, 2.9]  # indices 1 and 2 tie for tallest above base
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert Role.PRINCIPAL not in set(by_idx.values()), by_idx
    assert by_idx[1] is Role.UPPER
    assert by_idx[2] is Role.UPPER
    # Rank still descends from the first letting floor, so every rank-driven
    # relation downstream keeps working with no special case.
    ranks = {rs.index_from_bottom: rs.rank_from_principal for rs in rg.storeys}
    assert ranks[1] == 0 and ranks[2] == 1 and ranks[3] == 2, ranks


def test_a_distinguished_tallest_etage_is_still_the_piano_nobile() -> None:
    """The other half of the same predicate, so the change above cannot be
    read as "ties are now never principal, therefore nothing is".

    And it is Daly's Première Classe section, to the metre: a ground storey,
    a *low 1er étage* under the noble floor, the noble floor, then the taper.
    125 avenue des Champs-Élysées, from its own printed ladder, is
    4.10 / 3.60 / 3.87 / 3.70 / 3.40. The compressed level there is dressed
    as a full storey rather than as an entresol — the same physical band that
    Deuxième Classe calls an entresol, which is why two independent readers
    of one plate disagreed about which word to use — so this phase names the
    band and declines to have an opinion about the word.
    """
    heights = [3.5, 3.2, 3.6, 2.9]
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert by_idx[2] is Role.PRINCIPAL
    # Shorter than the floor it serves, so it is the compressed level — even
    # though it is taller than the storey above the noble floor, which is
    # exactly the case Daly's nine measured entresols make (2.40-3.12 m in
    # buildings whose topmost étages run down to 2.32 m).
    assert by_idx[1] is Role.MEZZANINE
    assert by_idx[3] is Role.UPPER


def test_no_principal_when_nothing_stands_above_base() -> None:
    g = _grid(_stack([3.5]), cornice_height=20.0)
    rg = assign_roles(g)
    assert Role.PRINCIPAL not in {rs.role for rs in rg.storeys}


# --------------------------------------------------------------------- Mezzanine


def test_mezzanine_directly_above_base_when_markedly_short() -> None:
    # base, a squeezed entresol, then a typical run around ~3.2 m
    heights = [3.6, 2.1, 3.3, 3.1, 2.9]
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert by_idx[1] is Role.MEZZANINE
    assert by_idx[2] is Role.PRINCIPAL  # tallest of what's left, above base+mezzanine


def test_mezzanine_absent_when_the_stack_did_not_produce_one() -> None:
    """Present only if the stack produced one — a run of similar heights
    must not get a phantom mezzanine."""
    heights = [3.6, 3.3, 3.2, 3.0, 2.9]
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    assert Role.MEZZANINE not in {rs.role for rs in rg.storeys}


def test_removing_the_mezzanine_shifts_the_principal_by_itself() -> None:
    """The concrete, structural-level form of the brief's named test: with
    no code change, deleting the short entresol slot moves which absolute
    slot is labelled principal — because identity is derived from the
    stack's shape, never declared against a floor number."""
    with_mezzanine = _grid(_stack([3.6, 2.1, 3.3, 3.0, 2.8]), cornice_height=20.0)
    without_mezzanine = _grid(_stack([3.6, 3.3, 3.0, 2.8]), cornice_height=20.0)

    rg_with = assign_roles(with_mezzanine)
    rg_without = assign_roles(without_mezzanine)

    principal_with = next(rs for rs in rg_with.storeys if rs.role is Role.PRINCIPAL)
    principal_without = next(rs for rs in rg_without.storeys if rs.role is Role.PRINCIPAL)

    assert any(rs.role is Role.MEZZANINE for rs in rg_with.storeys)
    assert not any(rs.role is Role.MEZZANINE for rs in rg_without.storeys)

    # Same relative floor (first of the typical run), but its absolute
    # position — and therefore, later, its balcony height above the
    # pavement — has moved down exactly one slot, purely as a consequence
    # of the stack's shape changing.
    assert principal_with.index_from_bottom == 2
    assert principal_without.index_from_bottom == 1
    assert principal_with.slot.width == pytest.approx(principal_without.slot.width)


# --------------------------------------------------------------------- Attic


def test_attic_is_the_slot_inside_the_roof_envelope() -> None:
    # cornice line at 16.0; the top slot starts at 16.0, i.e. inside the comble
    heights = [3.6, 3.3, 3.1, 2.9, 3.1]
    g = _grid(_stack(heights), cornice_height=16.0)
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    # cumulative starts: 0, 3.6, 6.9, 10.0, 12.9 -> last slot starts at 12.9,
    # below 16.0, so nothing is attic yet with this cornice.
    assert Role.ATTIC not in by_idx.values()

    # Lower the cornice below the last slot's start so it now falls inside
    # the roof envelope.
    g2 = _grid(_stack(heights), cornice_height=12.9)
    rg2 = assign_roles(g2)
    by_idx2 = _role_by_index(rg2)
    assert by_idx2[4] is Role.ATTIC


def test_attic_slot_is_excluded_from_principal_consideration() -> None:
    """A slot inside the roof envelope must never win 'tallest', even if it
    is numerically the tallest slot in the stack — the same exclusion
    principle as the base, applied at the other end of the stack."""
    heights = [3.5, 3.0, 2.8, 4.2]  # last slot is tallest overall
    g = _grid(_stack(heights), cornice_height=9.3)  # cumulative start of slot 3 is 9.3
    rg = assign_roles(g)
    by_idx = _role_by_index(rg)
    assert by_idx[3] is Role.ATTIC
    assert by_idx[3] is not Role.PRINCIPAL
    assert by_idx[1] is Role.PRINCIPAL  # tallest of what remains


def test_single_storey_grid_is_never_its_own_attic() -> None:
    """Base wins over attic even in the degenerate case where the cornice
    line sits at or below pavement level."""
    g = _grid(_stack([3.0]), cornice_height=0.0)
    rg = assign_roles(g)
    assert rg.storeys[0].role is Role.BASE


# --------------------------------------------------------------------- Upper / rank


def test_upper_ranked_upward_from_principal() -> None:
    heights = [3.6, 3.4, 3.1, 2.9, 2.7]
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    principal = next(rs for rs in rg.storeys if rs.role is Role.PRINCIPAL)
    assert principal.rank_from_principal == 0

    uppers = [rs for rs in rg.storeys if rs.role is Role.UPPER]
    assert uppers, "expected at least one upper storey"
    ranks = sorted(rs.rank_from_principal for rs in uppers)
    assert ranks == list(range(1, len(uppers) + 1))


def test_treatment_diminishes_with_rank_is_representable() -> None:
    """Not a rule this phase enforces, but the data must make it
    expressible: rank increases monotonically with height above principal."""
    heights = [3.6, 3.4, 3.1, 2.9, 2.7]
    g = _grid(_stack(heights), cornice_height=20.0)
    rg = assign_roles(g)
    ordered = sorted(rg.storeys, key=lambda rs: rs.index_from_bottom)
    for a, b in zip(ordered, ordered[1:]):
        if a.role is Role.UPPER and b.role is Role.UPPER:
            assert b.rank_from_principal == a.rank_from_principal + 1


# --------------------------------------------------------------------- G4: identical rules at different heights


def test_five_and_nine_storey_stacks_get_correct_roles_from_identical_rules() -> None:
    """No special-casing for the extra storeys: the same predicates, run on
    a 5-storey and a 9-storey stack, both produce exactly one base, at most
    one mezzanine, exactly one principal (tallest above base/mezzanine), and
    every remaining slot ranked as upper."""
    five = _grid(_stack([3.8, 2.2, 3.4, 3.1, 2.9]), cornice_height=30.0)
    nine = _grid(
        _stack([3.8, 2.2, 3.4, 3.3, 3.2, 3.1, 3.0, 2.9, 2.8]), cornice_height=30.0
    )

    for g, n in ((five, 5), (nine, 9)):
        rg = assign_roles(g)
        assert len(rg.storeys) == n
        role_counts = {}
        for rs in rg.storeys:
            role_counts[rs.role] = role_counts.get(rs.role, 0) + 1
        assert role_counts[Role.BASE] == 1
        assert role_counts[Role.MEZZANINE] == 1
        assert role_counts[Role.PRINCIPAL] == 1
        assert role_counts.get(Role.UPPER, 0) == n - 3
        principal = next(rs for rs in rg.storeys if rs.role is Role.PRINCIPAL)
        assert principal.index_from_bottom == 2  # right above base + mezzanine
        # index_from_top is consistent with index_from_bottom for every slot
        for rs in rg.storeys:
            assert rs.index_from_bottom + rs.index_from_top == n - 1


# --------------------------------------------------------------------- Structural bookkeeping


def test_index_from_bottom_and_top_are_consistent() -> None:
    g = _grid(_stack([3.6, 3.3, 3.1, 2.9]), cornice_height=20.0)
    rg = assign_roles(g)
    n = len(rg.storeys)
    for i, rs in enumerate(rg.storeys):
        assert rs.index_from_bottom == i
        assert rs.index_from_top == n - 1 - i


def test_bays_pass_through_unchanged() -> None:
    bays = (
        _slot("pier_end", 0.0, 0.35, SlotKind.FLEXIBLE),
        _slot("bay", 0.35, 3.0, SlotKind.REPEATING),
        _slot("pier_end", 3.35, 0.35, SlotKind.FLEXIBLE),
    )
    g = _grid(_stack([3.6, 3.3, 3.1]), cornice_height=20.0, bays=bays)
    rg = assign_roles(g)
    assert rg.bays == bays == g.bays


def test_grid_field_carries_the_original_grid() -> None:
    g = _grid(_stack([3.6, 3.3, 3.1]), cornice_height=20.0)
    rg = assign_roles(g)
    assert rg.grid is g


def test_slot_is_preserved_verbatim_on_each_roled_storey() -> None:
    g = _grid(_stack([3.6, 3.3, 3.1]), cornice_height=20.0)
    rg = assign_roles(g)
    for slot, roled in zip(g.storeys, rg.storeys):
        assert roled.slot == slot


# --------------------------------------------------------------------- I1: reads Grid and nothing else


def test_assign_roles_takes_only_a_grid() -> None:
    sig = inspect.signature(assign_roles)
    params = list(sig.parameters)
    assert params == ["grid"]


def test_roles_module_imports_nothing_from_site_or_rng() -> None:
    """I1: the roles phase reads structure alone — no ``SiteContext``, no
    year, no class, no RNG. Checked against the actual import statements,
    not prose — several docstrings in this module discuss, in words, what
    this phase must NOT read."""
    source = inspect.getsource(roles_module)
    import_lines = [
        line for line in source.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    joined = "\n".join(import_lines)
    for forbidden in ("SiteContext", "BuildingClass", "DecisionStream", "import random", "buildings.site"):
        assert forbidden not in joined, forbidden


def test_assign_roles_does_not_mutate_the_grid_it_is_given() -> None:
    g = _grid(_stack([3.8, 2.2, 3.4, 3.1, 2.9]), cornice_height=30.0)
    before = g
    assign_roles(g)
    assert g == before  # frozen dataclass, but confirms no in-place surprises


# --------------------------------------------------------------------- Integration with real solve_structure output


def test_integration_with_real_solve_structure_output() -> None:
    site = _site(street_width=20.0, parcel_width=14.0, year=1875, klass=BuildingClass.COMFORTABLE)
    g = solve_structure(site)
    rg = assign_roles(g)

    assert len(rg.storeys) == len(g.storeys)
    assert rg.bays == g.bays
    assert rg.storeys[0].role is Role.BASE
    principals = [rs for rs in rg.storeys if rs.role is Role.PRINCIPAL]
    assert len(principals) == 1
    # the ground floor (base) must never itself be labelled principal
    assert rg.storeys[0].role is not Role.PRINCIPAL


def test_determinism_same_grid_yields_identical_roled_grid() -> None:
    site = _site(street_width=17.3, parcel_width=11.4, year=1881, klass=BuildingClass.COMFORTABLE)
    g = solve_structure(site)
    runs = [assign_roles(g) for _ in range(20)]
    for rg in runs[1:]:
        assert rg == runs[0]


def test_no_rng_is_used_anywhere_in_the_module() -> None:
    source = inspect.getsource(roles_module)
    assert "random" not in source.lower() or "import random" not in source
    assert "DecisionStream" not in source


# ---------------------------------------------------------------------------
# "Markedly below" without a tuned constant — the S7 acceptance regression
# ---------------------------------------------------------------------------


def test_an_entresol_just_above_a_ratio_cutoff_is_still_an_entresol() -> None:
    """The stack the S7 acceptance run produced once S3's storey heights
    were corrected: a comfortable building on a 20 m boulevard, 1865.

    2.47 m is 0.765 of the 3.23 m median, so the old ``< 0.75 * median``
    cutoff read this entresol as an UPPER floor — a 2.47 m upper floor
    sitting directly on a 4.15 m shop front. It is shorter than every
    habitable storey above it, which is what makes it a mezzanine.
    """
    heights = [4.1525, 2.4715, 3.4697, 3.2268, 3.0010]
    rg = assign_roles(_grid(_stack(heights), cornice_height=17.55))
    by_idx = _role_by_index(rg)
    assert by_idx[0] is Role.BASE
    assert by_idx[1] is Role.MEZZANINE
    assert by_idx[2] is Role.PRINCIPAL


def test_a_slot_as_tall_as_the_habitable_run_is_not_a_mezzanine() -> None:
    """A tie is not "markedly below" anything. A slot the same height as the
    storeys above it is a storey, whatever the solver called it."""
    rg = assign_roles(_grid(_stack([3.9, 2.60, 2.60, 2.60]), cornice_height=20.0))
    assert Role.MEZZANINE not in {rs.role for rs in rg.storeys}


def test_the_mezzanine_predicate_carries_no_tuned_ratio() -> None:
    """A cutoff that has to be re-tuned every time the storey heights move
    is not a predicate. If a ratio constant reappears in this module, the
    blind spot above comes back with it."""
    source = inspect.getsource(roles_module)
    body = source.split('"""', 2)[2]
    assert "_MEZZANINE_RATIO" not in body, "the tuned mezzanine cutoff is back"


# ---------------------------------------------------------------------------
# A2.1 — the attic predicate reads the eaves, not the legal ceiling
# ---------------------------------------------------------------------------


def test_attic_is_measured_from_the_eaves_not_from_the_legal_cornice() -> None:
    """The defect A2.1 names, isolated from the structure phase.

    A building whose facade stops below the height its street earns still
    roofs over its own wall: the slot standing on those eaves is in the
    comble. Asked against the LEGAL cornice — 4 m higher here — no storey in
    any Paris building ever started high enough, which is why the role went
    four stages without ever being produced.
    """
    heights = [4.0, 3.4, 3.2, 2.9]  # eaves at 13.5
    g = _grid(_stack(heights + [2.8]), cornice_height=17.5, eaves_height=13.5)
    by_idx = _role_by_index(assign_roles(g))
    assert by_idx[4] is Role.ATTIC
    assert by_idx[3] is not Role.ATTIC

    # The same stack, asked the old question, produces nothing at all.
    old = _grid(_stack(heights + [2.8]), cornice_height=17.5, eaves_height=17.5)
    assert Role.ATTIC not in _role_by_index(assign_roles(old)).values()


def test_the_attic_is_excluded_from_the_habitable_comparisons() -> None:
    """A comble storey is short, and it must not be able to make the slot
    over the base look tall by comparison, nor win 'tallest'."""
    g = _grid(_stack([4.0, 2.2, 3.4, 3.2, 2.4]), cornice_height=12.8, eaves_height=12.8)
    by_idx = _role_by_index(assign_roles(g))
    assert by_idx[4] is Role.ATTIC
    assert by_idx[1] is Role.MEZZANINE  # 2.2 < 3.2, ignoring the 2.4 attic
    assert by_idx[2] is Role.PRINCIPAL


def test_roled_grid_exposes_the_attic_storey_and_its_bays() -> None:
    """The termination phase lights this storey with lucarnes, so it needs
    the storey and the slots it is divided into — read from here rather than
    re-derived from the grid, which is how the two could drift apart."""
    bays = (
        _slot("pier_end", 0.0, 0.4, SlotKind.FLEXIBLE),
        _slot("bay", 0.4, 3.0),
        _slot("special", 3.4, 1.3, SlotKind.FLEXIBLE),
        _slot("bay", 4.7, 3.0),
        _slot("pier_end", 7.7, 0.4, SlotKind.FLEXIBLE),
    )
    g = _grid(_stack([4.0, 3.4, 3.2]), cornice_height=10.6, eaves_height=10.6, bays=bays)
    rg = assign_roles(g)
    assert rg.attic is None  # nothing above the eaves yet
    assert rg.attic_storeys == ()
    assert rg.attic_bays == ()

    g2 = _grid(
        _stack([4.0, 3.4, 3.2, 2.6]), cornice_height=10.6, eaves_height=10.6, bays=bays
    )
    rg2 = assign_roles(g2)
    assert rg2.attic is not None
    assert rg2.attic.role is Role.ATTIC
    assert rg2.attic.index_from_bottom == 3
    assert len(rg2.attic_storeys) == 1
    # The comble is divided on the SAME grid as the facade below it — that is
    # what makes a lucarne line up with the window under it — and only the
    # repeating bays are rooms: no dormer over an end pier or a blind panel.
    assert [b.name for b in rg2.attic_bays] == ["bay", "bay"]
    assert all(b in rg2.bays for b in rg2.attic_bays)


def test_a_real_building_produces_an_attic_through_the_real_phases() -> None:
    """End to end, with no hand-built grid: the structure phase emits a
    storey inside the comble and this phase labels it, with no special case
    for the roof anywhere in between."""
    g = solve_structure(_site(street_width=20.0, parcel_depth=15.0))
    rg = assign_roles(g)
    assert rg.attic is not None
    assert rg.attic.index_from_bottom == len(rg.storeys) - 1
    assert rg.attic.slot.start == pytest.approx(g.eaves_height, abs=1e-9)
    assert rg.attic_bays, "a comble storey with nowhere to put a window"
