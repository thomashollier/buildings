"""Unit tests for the structure phase (S3): ``solve_structure`` and ``Grid``.

Gate G3 checks are exercised directly here: the grid carries no role
vocabulary, height moves in steps rather than continuously, the bay grid is
solved exactly once, ceiling and built height are genuinely different for a
modest building, datums are received rather than resampled, and the whole
thing is deterministic.
"""

from __future__ import annotations

import inspect
import math
import re
import types

import pytest

from buildings.quantity import Kind
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import FitInfeasible
from buildings.typologies.paris import catalogue, structure
from buildings.typologies.paris.structure import Grid, solve_structure


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


def _datums(street_width: float, cornice_height: float) -> object:
    """A minimal stand-in for ``buildings.block.BlockDatums`` (S9, not yet
    built). Structure.py accesses datums by attribute only (duck typing),
    exactly so a fixture like this — and, later, the real dataclass —
    satisfies it identically."""
    return types.SimpleNamespace(
        street_width=street_width,
        cornice_height=cornice_height,
        string_course_levels=(),
        balcony_levels=(),
    )


# --------------------------------------------------------------------- G3.1


def test_grid_is_unnamed() -> None:
    """No field, slot name, or account string names a role."""
    forbidden = re.compile(r"\b(base|mezzanine|principal|noble|upper|attic)\b", re.IGNORECASE)

    field_names = {f.name for f in __import__("dataclasses").fields(Grid)}
    assert not any(forbidden.search(name) for name in field_names)

    g = solve_structure(_site())
    for slot in (*g.storeys, *g.bays):
        assert not forbidden.search(slot.name), slot.name
    for line in g.account:
        assert not forbidden.search(line), line


def test_structure_source_has_no_role_vocabulary_outside_the_docstring() -> None:
    """The stronger, source-level version of the same rule: grep the file,
    excluding the module docstring's one explicit discussion of what S4
    does with this output."""
    source = inspect.getsource(structure)
    # Strip the module docstring (the first triple-quoted block) before
    # grepping, since it explicitly names S4's vocabulary as documentation.
    body = source.split('"""', 2)[2]
    forbidden = re.compile(r"\b(base|mezzanine|principal|noble|upper|attic)\b", re.IGNORECASE)
    hits = [line for line in body.splitlines() if forbidden.search(line) and not line.strip().startswith("#")]
    assert hits == [], hits


# --------------------------------------------------------------------- G3.2


def test_cornice_height_moves_in_steps_not_continuously() -> None:
    """Sweeping street width must produce a small number of plateaus, not a
    smooth ramp — the regulation is a step table."""
    values = []
    for i in range(0, 341):  # 6.0 m .. 40.0 m at 0.1 m
        width = 6.0 + i * 0.1
        g = solve_structure(_site(street_width=width, parcel_width=12.0, year=1870))
        values.append(round(g.cornice_height.value, 6))

    plateaus = sorted(set(values))
    # The Second Empire table has 4 steps (7.80 / 9.75 / 20.00 / inf).
    assert len(plateaus) <= 6, plateaus
    # Every point in the sweep is exactly one of the plateau values — the
    # defining property of a step function, not merely "few distinct values".
    assert set(values) == set(plateaus)


def test_cornice_height_uses_the_regulatory_table_directly() -> None:
    from buildings.typologies.paris.reglement import Era, get_reglement

    reg = get_reglement(Era.SECOND_EMPIRE)
    g = solve_structure(_site(street_width=25.0, year=1870))
    assert g.cornice_height.value == reg.facade_height_limit(25.0)
    assert g.cornice_height.kind is Kind.REGULATORY
    assert g.cornice_height.why  # non-blank citation


# --------------------------------------------------------------------- G3.3


def test_bay_grid_is_solved_once_per_building() -> None:
    """There is exactly one call to the horizontal solve; every storey
    later decorates the same ``Grid.bays`` tuple rather than getting its own."""
    g = solve_structure(_site())
    # Grid does not expose a per-storey bay grid at all — there is only
    # ever the one shared tuple.
    assert not hasattr(g, "storey_bays")
    assert isinstance(g.bays, tuple) and len(g.bays) > 0


def test_source_calls_solve_exactly_twice() -> None:
    """One call per axis: bays (horizontal) and storeys (vertical). A
    second horizontal call would be the bug this gate exists to catch."""
    source = inspect.getsource(structure)
    calls = re.findall(r"(?<!_)\bsolve\(\s*\n", source)
    assert len(calls) == 2, calls


# --------------------------------------------------------------------- G3.4


def test_ceiling_and_built_height_are_separate_for_a_modest_building() -> None:
    g = solve_structure(
        _site(street_width=25.0, klass=BuildingClass.MODEST, year=1888, parcel_width=14.0)
    )
    assert g.built_height < g.cornice_height.value - 0.5, (g.built_height, g.cornice_height.value)


def test_grand_building_builds_close_to_the_ceiling() -> None:
    g = solve_structure(
        _site(street_width=25.0, klass=BuildingClass.GRAND, year=1888, parcel_width=14.0)
    )
    assert g.built_height <= g.cornice_height.value + 1e-6
    assert g.built_height > g.cornice_height.value * 0.9


def test_built_height_never_exceeds_the_legal_ceiling() -> None:
    for klass in BuildingClass:
        g = solve_structure(_site(street_width=20.0, klass=klass, year=1890, parcel_width=14.0))
        assert g.built_height <= g.cornice_height.value + 1e-6


def test_ambition_is_monotonic_by_class() -> None:
    """Only the ordering across classes is contractual (A1.3-style)."""
    built = {}
    for klass in BuildingClass:
        g = solve_structure(_site(street_width=25.0, klass=klass, year=1888, parcel_width=14.0))
        built[klass] = g.built_height
    assert (
        built[BuildingClass.MODEST]
        <= built[BuildingClass.ORDINARY]
        <= built[BuildingClass.COMFORTABLE]
        <= built[BuildingClass.GRAND]
    )


def test_built_height_equals_the_storeys_standing_below_the_roof() -> None:
    """``built_height`` is a question asked of the storeys, not a number
    stored beside them — and the question is where the *stone face* stops.

    Under A2.1 the stack can carry a slot standing inside the comble, so
    "the sum of the storeys" is no longer the same question as "the height
    of the facade". The comble storey stands on the eaves, it does not raise
    them, and every reader downstream (the silhouette springs from
    ``built_height``) means the facade.
    """
    g = solve_structure(_site())
    facade = [s for i, s in enumerate(g.storeys) if not g.stands_in_the_roof(i)]
    assert g.built_height == pytest.approx(sum(s.width for s in facade), abs=1e-9)
    assert g.built_height == pytest.approx(g.eaves_height, abs=1e-9)
    # ...and the comble storey really is excluded rather than absent.
    assert g.comble_storeys, "this situation was chosen because it has a comble storey"
    assert sum(s.width for s in g.storeys) > g.built_height + 1e-6


# --------------------------------------------------------------------- G3.5


def test_datums_cornice_height_is_received_exactly_not_recomputed() -> None:
    """The cornice datum is a fact the block resolved and the building
    receives, not a number it recomputes.

    16.40 m is deliberately not what the règlement yields for a 20 m street
    in 1888 (asserted below), so the assertion can only pass by the datum
    being taken as given — a block may hold its cornice at a neighbour's line
    rather than at the ceiling the law would allow, and that is the whole
    reason the datum exists. The site and the datum agree about the *street*,
    which is a different fact and, since A4.8, one they must agree about.
    """
    site = _site(street_width=20.0, year=1888)
    datums = _datums(street_width=20.0, cornice_height=16.40)
    g = solve_structure(site, datums=datums)
    assert g.cornice_height.value == 16.40
    assert g.envelope.facade_height == 16.40
    from buildings.typologies.paris.reglement import Era, get_reglement

    assert get_reglement(Era.ALPHAND).facade_height_limit(20.0) != 16.40


def test_without_datums_the_site_street_width_is_used() -> None:
    from buildings.typologies.paris.reglement import Era, get_reglement

    reg = get_reglement(Era.ALPHAND)
    g = solve_structure(_site(street_width=25.0, year=1888))
    assert g.cornice_height.value == reg.facade_height_limit(25.0)


def test_the_street_width_the_block_resolved_is_the_one_the_envelope_uses() -> None:
    site = _site(street_width=25.0, year=1888)
    datums = _datums(street_width=25.0, cornice_height=20.0)
    g = solve_structure(site, datums=datums)
    assert g.envelope.street_width == 25.0


def test_a_site_that_disagrees_with_its_block_about_the_street_is_refused() -> None:
    """A4.8. This test used to assert the opposite — that a site claiming a
    6 m street and a datum claiming 25 m produced a 25 m envelope — and called
    that "the datum drives the envelope". It did, silently, while the trace
    and every consumer of ``SiteContext`` went on reading 6 m: one street
    under two widths, which is precisely the second source of truth this
    project exists to remove.

    It is rewritten rather than deleted because the underlying claim is still
    worth making; what changed is that the disagreement is now the thing being
    asserted about. There is no legitimate reason for the two to differ — a
    street has one width, the block resolves it, the building receives it (I2)
    — so the only correct behaviour is to refuse.
    """
    site = _site(street_width=6.0, year=1888)
    datums = _datums(street_width=25.0, cornice_height=20.0)
    with pytest.raises(ValueError, match="same fact stored twice"):
        solve_structure(site, datums=datums)


# --------------------------------------------------------------------- G3.6


def test_determinism_same_site_same_seed_identical_grid() -> None:
    site = _site(street_width=17.3, parcel_width=11.4, year=1881, klass=BuildingClass.COMFORTABLE)
    runs = [solve_structure(site) for _ in range(50)]
    for g in runs[1:]:
        assert g == runs[0]


def test_no_rng_is_used_anywhere_in_the_module() -> None:
    """S3 takes no ``rng`` parameter and samples nothing (I2/I5): every
    quantity is a pure function of ``site`` and ``datums``."""
    sig = inspect.signature(solve_structure)
    assert "rng" not in sig.parameters
    source = inspect.getsource(structure)
    assert "DecisionStream" not in source
    assert "import random" not in source


# --------------------------------------------------------------------- other structural properties


def test_bays_sum_exactly_to_the_parcel_width() -> None:
    for width in (4.2, 6.0, 8.4, 11.0, 14.7, 20.3, 30.0):
        g = solve_structure(_site(parcel_width=width, street_width=18.0))
        assert sum(s.width for s in g.bays) == pytest.approx(width, abs=1e-9)


def test_storeys_are_bottom_up_and_start_at_zero() -> None:
    g = solve_structure(_site())
    assert g.storeys[0].start == 0.0
    cursor = 0.0
    for slot in g.storeys:
        assert slot.start == pytest.approx(cursor, abs=1e-9)
        cursor += slot.width


def test_typical_storeys_taper_shorter_going_up() -> None:
    g = solve_structure(_site(street_width=30.0, parcel_width=16.0, klass=BuildingClass.GRAND, year=1888))
    typical = [s for s in g.storeys if s.name == "storey"]
    assert len(typical) >= 3
    heights = [s.width for s in typical]
    assert heights == sorted(heights, reverse=True)
    assert heights[0] > heights[-1]  # a genuine taper, not a flat coincidence


def test_ground_floor_is_the_bottom_slot() -> None:
    g = solve_structure(_site())
    assert g.storeys[0].name == "ground"


def test_carriage_ground_floor_is_absolute_and_rigid() -> None:
    """Both figures are the catalogue's, not this module's.

    They used to be neither: ``structure`` carried its own ``Abs(3.30)`` for
    the storey and its own ``Abs(3.00)`` for the slot, and the first of those
    was 0.40 m short of the two quantities it claimed to be about
    (``carriage_clear_height`` 3.40 + ``lintel_bearing_depth`` 0.30), so the
    porte cochère came out capped at 3.00 m clear in a storey that was
    supposed to be sized for it. Asserting against the catalogue rather than
    against a literal is the point: a third copy of the number cannot drift
    from the other two if there is no third copy.
    """
    g = solve_structure(_site(ground=GroundProgramme.CARRIAGE, parcel_width=12.0))
    ground = g.storeys[0]
    assert ground.name == "ground"
    assert ground.width == pytest.approx(float(catalogue.carriage_storey_height()), abs=1e-9)
    assert ground.width == pytest.approx(
        float(catalogue.carriage_clear_height()) + float(catalogue.lintel_bearing_depth()),
        abs=1e-9,
    )
    door = [s for s in g.bays if s.name == "porte_cochere"]
    assert len(door) == 1
    # The SLOT is a piece of wall: the clear opening plus the jamb the arch
    # lands on either side. It is wider than the door by exactly two jambs.
    assert door[0].width == pytest.approx(float(catalogue.carriage_slot_width()), abs=1e-9)
    assert door[0].width == pytest.approx(
        float(catalogue.door_carriage_entrance().preferred)
        + 2.0 * float(catalogue.carriage_jamb_width()),
        abs=1e-9,
    )


def test_carriage_width_is_absolute_and_never_class_scaled() -> None:
    widths = set()
    for klass in BuildingClass:
        g = solve_structure(_site(ground=GroundProgramme.CARRIAGE, parcel_width=12.0, klass=klass))
        door = [s for s in g.bays if s.name == "porte_cochere"][0]
        widths.add(round(door.width, 9))
    assert widths == {round(float(catalogue.carriage_slot_width()), 9)}


def test_pre_1859_has_no_hygiene_minimum_but_a_human_one_applies() -> None:
    """Before 1859 the texts impose no storey minimum, which does not mean a
    storey may be any height: a person has to stand up in it.

    The entresol is deliberately not in this list. It is exempt from the
    habitable minimum — that exemption is the whole reason it can exist —
    and it is not a room anyone lives in, so it is held below the figure a
    habitable storey is held above. The comble storey IS a room people live
    in, and is held to it."""
    g = solve_structure(_site(year=1800, street_width=9.0, ground=GroundProgramme.SHOP))
    habitable = [s for s in g.storeys if s.name in ("storey", "comble")]
    assert habitable
    assert all(s.width >= 2.20 - 1e-9 for s in habitable)
    entresols = [s for s in g.storeys if s.name == "entresol"]
    assert all(s.width < 2.20 for s in entresols)


# ------------------------------------------------- the regulatory storey minimum
#
# The 2.60 m minimum of the 1859 règlement is a REGULATORY quantity: it may
# not be bent by an INFERRED taper constant, by a rounding pass, or by
# anything else this module does after the solver has answered. Nothing
# asserted it before, which is how a 2.596 m storey shipped green.


def _reg_for(year: int):
    from buildings.typologies.paris.reglement import era_for_year, get_reglement

    return get_reglement(era_for_year(year))


def test_post_1859_storeys_never_fall_below_the_regulatory_minimum() -> None:
    """Every typical storey of every post-1859 grid, across a sweep wide
    enough to reach the tight budgets where the taper has least room."""
    for year in (1860, 1875, 1885, 1900, 1912):
        reg = _reg_for(year)
        assert reg.min_floor_height == pytest.approx(2.60)  # the rule under test
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for i in range(0, 35):
                    street = 6.0 + i * 1.0
                    g = solve_structure(
                        _site(
                            street_width=street,
                            parcel_width=12.0,
                            year=year,
                            klass=klass,
                            ground=ground,
                        )
                    )
                    for slot in g.storeys:
                        if slot.name != "storey":
                            continue
                        assert slot.width >= reg.min_floor_height - 1e-9, (
                            year, klass, ground, street, slot.width,
                        )


def test_the_1860_modest_carriage_case_that_bent_the_1859_minimum() -> None:
    """Regression, stated as the exact situation that produced a 2.596 m
    storey against a 2.60 m floor — and the account that narrated both."""
    site = SiteContext(
        street_width=9.8,
        parcel_width=12.0,
        parcel_depth=15.0,
        year=1860,
        klass=BuildingClass.MODEST,
        ground=GroundProgramme.CARRIAGE,
    )
    g = solve_structure(site)
    minimum = _reg_for(1860).min_floor_height
    typical = [s for s in g.storeys if s.name == "storey"]
    assert typical
    assert min(s.width for s in typical) >= minimum - 1e-9
    # and the trace does not contradict itself: no height the taper reports
    # is below the minimum the account states two lines earlier
    taper_line = [a for a in g.account if a.startswith("taper")][0]
    reported = [float(x) for x in re.findall(r"\d+\.\d+", taper_line.split("->")[1])]
    assert reported and all(h >= minimum - 1e-3 for h in reported), taper_line


#: An independent, deliberately crude architectural bound on a typical
#: habitable storey of a Paris immeuble de rapport, owned by this test and
#: NOT derived from anything in ``structure``. The canonical section runs
#: roughly 3.6 m at the étage noble down to 2.9 m under the cornice; 4.00 m
#: is well clear of anything real, so a storey above it is a parameterisation
#: fault whatever the module's own band happens to say. This is the assertion
#: the S7 acceptance gate failed on: the module's band said 4.79 m was fine.
_NO_PARIS_STOREY_IS_TALLER_THAN = 4.00


def test_taper_stays_inside_the_band_declared_to_the_solver() -> None:
    """The solver guarantees no slot outside [minimum, maximum]. Downstream
    phases read ``Grid.storeys``, not ``FitResult``, so the guarantee has to
    survive the taper — including the upper bound.

    Two bounds, deliberately: the band ``structure`` actually declares (read
    from the module, so this cannot drift out of step with it the way the
    re-derived literals here previously did), and an architectural bound this
    test owns outright. The first checks the taper honours its contract; the
    second checks the contract is worth honouring.
    """
    for year in (1800, 1860, 1888, 1905):
        reg = _reg_for(year)
        for klass in BuildingClass:
            band_lo, _pref, band_hi = structure._typical_storey_band(reg, klass)
            lo, hi = float(band_lo), float(band_hi)
            assert lo >= max(reg.min_floor_height, 2.20) - 1e-9, (year, klass, lo)
            assert hi <= _NO_PARIS_STOREY_IS_TALLER_THAN, (year, klass, hi)
            for i in range(0, 35):
                g = solve_structure(
                    _site(street_width=6.0 + i * 1.0, parcel_width=12.0, year=year, klass=klass)
                )
                for slot in g.storeys:
                    if slot.name != "storey":
                        continue
                    assert lo - 1e-9 <= slot.width <= hi + 1e-9, (year, klass, slot.width, lo, hi)
                    assert slot.width <= _NO_PARIS_STOREY_IS_TALLER_THAN, (year, klass, slot.width)


def test_the_taper_never_changes_the_total_it_was_given() -> None:
    for klass in BuildingClass:
        for street in (7.0, 9.0, 12.0, 21.0, 30.0):
            g = solve_structure(_site(street_width=street, klass=klass, year=1888))
            ceiling = float(g.cornice_height)
            assert g.built_height <= ceiling + 1e-9
            facade = [s for i, s in enumerate(g.storeys) if not g.stands_in_the_roof(i)]
            assert g.built_height == pytest.approx(
                math.fsum(s.width for s in facade), abs=1e-9
            )


# ------------------------------------------------------------- _taper_heights


@pytest.mark.parametrize(
    "n,total,minimum,maximum",
    [
        (6, 6 * 2.61, 2.60, 3.02),
        (8, 8 * 2.62, 2.60, 3.02),
        (10, 10 * 2.63, 2.60, 3.02),  # the 10 cm violation the verifier probed
        (5, 5 * 2.25, 2.20, 2.90),
        (4, 4 * 3.50, 2.60, 3.55),  # tight against the ceiling instead
        (3, 3 * 2.60, 2.60, 3.02),  # no room at all: every entry on the floor
        (3, 3 * 3.55, 2.60, 3.55),  # no room at all: every entry on the ceiling
        (1, 3.10, 2.60, 3.55),
        (2, 2 * 2.60, 2.60, 2.60),  # degenerate band
    ],
)
def test_taper_heights_postconditions(n, total, minimum, maximum) -> None:
    heights = structure._taper_heights(n, total, minimum, maximum=maximum)
    assert len(heights) == n
    assert math.fsum(heights) == pytest.approx(total, abs=1e-9)
    assert all(h >= minimum - 1e-9 for h in heights), heights
    assert all(h <= maximum + 1e-9 for h in heights), heights
    assert heights == sorted(heights, reverse=True), heights


def test_taper_heights_tapers_when_the_band_leaves_room() -> None:
    heights = structure._taper_heights(5, 5 * 3.00, 2.60, maximum=3.55)
    assert heights[0] > heights[-1]
    assert all(a >= b for a, b in zip(heights, heights[1:]))


def test_taper_heights_refuses_a_total_its_band_cannot_hold() -> None:
    with pytest.raises(ValueError):
        structure._taper_heights(4, 4 * 2.00, 2.60, maximum=3.55)  # below the floor
    with pytest.raises(ValueError):
        structure._taper_heights(4, 4 * 4.00, 2.60, maximum=3.55)  # above the ceiling


# ------------------------------------------- where the squeezed storey belongs


def test_the_squeezed_storey_sits_directly_above_the_ground_floor() -> None:
    """A compressed slot is only legitimate in one position — immediately over
    the ground floor, which is what the word *entresol* means. At the top of
    the stack it would be an unjustified short storey.

    Under A2.2 the slot is the entresol, reserved by programme before the
    budget is filled, so the position is guaranteed by *where it was
    reserved* rather than restored afterwards.

    **A9.4 changed what "compressed" is measured against**, and the old
    reading of this test — "shorter than the legal storey minimum it is
    exempt from" — is one Daly refutes: his nine measured Deuxième Classe
    entresols are 2.40-3.12 m and six of them clear the 1859 decree's 2.60 m.
    A Paris entresol is short relative to the floor it serves, by a ratio Daly
    also measures (1.25× in Première Classe, 1.30× in Deuxième), and that is
    what is asserted here now.
    """
    seen = 0
    for year in (1800, 1870, 1890, 1910):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for i in range(0, 35):
                    g = solve_structure(
                        _site(
                            street_width=6.0 + i * 1.0,
                            parcel_width=12.0,
                            year=year,
                            klass=klass,
                            ground=ground,
                        )
                    )
                    squeezed = [j for j, s in enumerate(g.storeys) if s.name == "entresol"]
                    assert len(squeezed) <= 1
                    if squeezed:
                        seen += 1
                        assert squeezed[0] == 1, [s.name for s in g.storeys]
                        assert g.storeys[0].name == "ground"
                        over = [
                            s.width
                            for s in g.storeys
                            if s.name not in ("ground", "entresol", "comble")
                        ]
                        assert over and g.storeys[1].width <= max(over) / 1.275 + 1e-9, (
                            year, klass, ground, g.storeys[1].width, over
                        )
    assert seen > 0, "no grid in the sweep produced a squeezed storey at all"


def test_a_squeezed_storey_is_never_the_top_of_the_stack() -> None:
    for klass in BuildingClass:
        for ground in GroundProgramme:
            for street in (7.0, 8.5, 10.0, 14.0, 21.0, 30.0):
                g = solve_structure(
                    _site(street_width=street, klass=klass, ground=ground, year=1870)
                )
                if len(g.storeys) > 2:
                    assert g.storeys[-1].name != "entresol"
                    assert not g.storeys[-1].is_special


# -------------------------------------------- narrow parcels with an entrance


def test_narrow_carriage_parcels_are_solved_not_refused() -> None:
    """A 3 m porte cochère on a 6 m parcel is ordinary Paris, not an exotic
    input: the entrance is itself an element of the run, so the facade may
    consist of it, its piers and a narrow special, with no full bay at all."""
    for klass in BuildingClass:
        for i in range(0, 21):
            width = 5.0 + i * 0.25
            g = solve_structure(
                _site(parcel_width=width, klass=klass, ground=GroundProgramme.CARRIAGE)
            )
            assert sum(s.width for s in g.bays) == pytest.approx(width, abs=1e-9)
            door = [s for s in g.bays if s.name == "porte_cochere"]
            assert len(door) == 1
            assert door[0].width == pytest.approx(
                float(catalogue.carriage_slot_width()), abs=1e-9
            )


def test_a_parcel_too_narrow_for_the_entrance_says_so_in_its_own_terms() -> None:
    """Below the entrance plus its two thinnest piers there is no facade.
    That refusal is a fact about an ABSOLUTE quantity, so it is stated as
    one rather than surfacing as a list of solver bounds."""
    with pytest.raises(FitInfeasible) as excinfo:
        solve_structure(_site(ground=GroundProgramme.CARRIAGE, parcel_width=3.1))
    message = str(excinfo.value)
    assert "porte cochère" in message
    assert f"{float(catalogue.carriage_slot_width()):.2f} m" in message


def test_roof_envelope_switches_geometry_across_1884() -> None:
    from buildings.typologies.paris.reglement import RoofEnvelope

    pre = solve_structure(_site(year=1883, street_width=22.0))
    post = solve_structure(_site(year=1884, street_width=22.0))
    assert pre.envelope.roof_envelope is RoofEnvelope.DIAGONAL_45
    assert post.envelope.roof_envelope is RoofEnvelope.CIRCULAR_ARC


def test_account_is_non_empty_and_narrates_every_decision() -> None:
    g = solve_structure(_site())
    assert len(g.account) > 5
    joined = " ".join(g.account)
    for marker in (
        "cornice ceiling",
        "facade ambition",
        "comble CEILING",
        "comble BUILT",
        "comble section",
        "bay pitch",
        "ground floor",
        "entresol",
        "comble holds",
        "taper",
        "budget",
    ):
        assert marker in joined, marker


def test_infeasible_situations_raise_rather_than_silently_degrade() -> None:
    with pytest.raises(FitInfeasible):
        solve_structure(_site(ground=GroundProgramme.CARRIAGE, parcel_width=3.0))


# ---------------------------------------------------------------------------
# The S7 acceptance failure: ambition may buy the margin, never the storey
# ---------------------------------------------------------------------------
#
# S7's first-week acceptance run failed on architectural plausibility, and the
# cause was here. The typical-storey band was
# ``scale_for_class(Prop(3.10 .. 3.55))``, so COMFORTABLE preferred 4.08 m and
# GRAND 4.79 m, and a 16.32 m facade on a 20 m boulevard came out as FOUR
# storeys of 4.37 / 4.08 / 4.00 / 3.86 where a Paris immeuble of 1865 carries
# five. The class factor was paying for the joists as well as the ceiling rose.
#
# The brief classifies "storey height above its legal minimum" as the
# PROPORTIONAL quantity — the margin, not the storey. These tests assert that
# reading directly, so the earlier form cannot come back unnoticed.


def test_only_the_margin_above_a_plain_storey_scales_with_class() -> None:
    """The rigid core of a storey — a room and the floor structure over it —
    is the same for a modest building and a grand one. Only what is bought
    above it moves, so the spread across classes is a fraction of a metre and
    not the 1.35/0.85 = 1.59x that scaling the whole height would give."""
    reg = _reg_for(1875)
    plain = float(structure._PLAIN_STOREY_HEIGHT)
    pref = {
        klass: float(structure._typical_storey_band(reg, klass)[1]) for klass in BuildingClass
    }

    # Monotonic in ambition (the only contractual part of A1.3's ordering).
    assert (
        pref[BuildingClass.MODEST]
        < pref[BuildingClass.ORDINARY]
        < pref[BuildingClass.COMFORTABLE]
        < pref[BuildingClass.GRAND]
    )
    # Every class sits above the plain storey — the margin is what varies.
    assert all(v > plain for v in pref.values())
    # And the whole storey is NOT what scaled: the grand/modest ratio of the
    # storey is far below the grand/modest ratio of the class factor.
    from buildings.quantity import Prop, scale_for_class

    factor_ratio = float(scale_for_class(Prop(1.0, "x"), BuildingClass.GRAND)) / float(
        scale_for_class(Prop(1.0, "x"), BuildingClass.MODEST)
    )
    storey_ratio = pref[BuildingClass.GRAND] / pref[BuildingClass.MODEST]
    assert storey_ratio < 1.0 + 0.5 * (factor_ratio - 1.0), (storey_ratio, factor_ratio)


def test_every_class_prefers_an_architecturally_real_storey_height() -> None:
    """A typical Paris habitable storey runs roughly 2.8-3.5 m whoever owns
    the building. Under the earlier band GRAND preferred 4.19 m and topped
    out at 4.79 m, which is not a storey in an immeuble de rapport."""
    for year in (1800, 1860, 1888, 1905):
        reg = _reg_for(year)
        for klass in BuildingClass:
            _lo, pref, most = structure._typical_storey_band(reg, klass)
            assert 2.80 <= float(pref) <= 3.50, (year, klass, float(pref))
            assert float(most) <= _NO_PARIS_STOREY_IS_TALLER_THAN, (year, klass, float(most))


def test_the_rez_de_chaussee_does_not_scale_with_class_at_all() -> None:
    """**A9.4, and it replaces a test that asserted the opposite.**

    This used to read "a grand shopfront buys street presence above a plain
    storey" and asserted a strict MODEST < ORDINARY < COMFORTABLE < GRAND
    ladder in the ground storey. Daly measures sixteen rez-de-chaussée and
    there is no ladder to assert: 3.42-4.85 m overall, class medians
    4.20 / 3.95 / 3.81 m — a 9 % fall from top to bottom, the wrong way
    round for the old test, against ranges that overlap almost completely
    (the Deuxième range alone contains every value in every other class).
    The measurement pass calls it the most stable absolute in the corpus
    after the door and recommends it SOURCED *as class-independent*.

    So the assertion is now the stronger one — the four heights are
    identical, not merely ordered — and the band it must sit in is Daly's own
    measured range rather than an invented one.
    """
    heights = {}
    for klass in BuildingClass:
        g = solve_structure(_site(ground=GroundProgramme.SHOP, klass=klass))
        heights[klass] = g.storeys[0].width
    values = set(round(h, 9) for h in heights.values())
    assert len(values) == 1, f"the rez-de-chaussée moved with class: {heights}"
    for klass, h in heights.items():
        # Daly 1864, 16 buildings: 3.42-4.85 m.
        assert 3.42 <= h <= 4.85, (klass, h)


def test_a_residential_ground_floor_does_not_scale_with_class_either() -> None:
    """The same kind of number, and Daly's finding is about the kind.

    No plate in the corpus measures a residential ground storey — Daly's are
    commercial frontages — so its height stays INFERRED. What carries across
    is that a ground storey is a room and a doorway and neither got bigger
    when the owner did, so this one is ABSOLUTE too and the four classes get
    one answer.
    """
    heights = {
        klass: solve_structure(
            _site(ground=GroundProgramme.RESIDENTIAL, klass=klass, street_width=8.0)
        ).storeys[0].width
        for klass in BuildingClass
    }
    assert len(set(round(h, 9) for h in heights.values())) == 1, heights


def test_the_first_week_acceptance_section_is_a_paris_section() -> None:
    """The exact case the S7 gate failed on: 20 m street, 1865, comfortable,
    shop. A 16-17 m facade on a boulevard carries FIVE levels, the ground
    floor is the tallest, and the storey under the cornice is the shortest
    habitable one — not a 3.86 m floor on the end of a 3.5%-per-storey ramp.
    """
    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=14.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    heights = [s.width for s in g.storeys]
    assert len(heights) >= 5, heights
    assert heights[0] == max(heights), heights  # the base is the tallest slot
    # A commercial ground floor is allowed to be taller than a habitable
    # storey — that is its programme — but not by a whole storey.
    assert heights[0] <= 4.60, heights

    typical = [s.width for s in g.storeys if s.name == "storey"]
    assert all(h <= _NO_PARIS_STOREY_IS_TALLER_THAN for h in typical), typical
    assert len(typical) >= 3, typical
    # The storey under the cornice is the shortest of the habitable run, and
    # by a real margin rather than a 3.5% shave.
    assert typical[-1] == min(typical), typical
    assert typical[-1] <= 0.92 * typical[0], typical
    # The band is Daly's own: the nine measured Deuxième Classe buildings put
    # their storey under the cornice at 2.32-3.52 m about a median of 2.99 m.
    # It was written as 2.60-3.10 while the entresol's held-down height was
    # being thrown away (A9.4); with that 0.30 m standing in the storeys it
    # was reserved from (A16.2) the top of this stack is 3.12 m, which is
    # inside Daly and outside a round number. The 1859 minimum is the floor.
    assert 2.60 <= typical[-1] <= 3.52, typical


def test_five_levels_are_reachable_and_the_stack_grows_with_the_street() -> None:
    """Systematic, not one seed: the earlier band could never put more than
    five slots in a stack anywhere in Paris, because its storeys were a
    metre too tall. A wide street must reach six."""
    counts = set()
    for street in (6.0, 10.0, 14.0, 20.0, 26.0, 34.0):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                g = solve_structure(
                    _site(street_width=street, parcel_width=12.0, klass=klass, ground=ground)
                )
                counts.add(len(g.storeys))
    assert max(counts) >= 6, sorted(counts)


def test_the_taper_is_a_diminution_not_a_ramp() -> None:
    """A real section steps down markedly from the noble floor to the storey
    under the cornice. The rate is read off that section (~(2.9/3.6)**(1/3));
    the earlier 0.965 gave 4.08 -> 4.00 -> 3.86, which is a ramp."""
    assert structure._TAPER_RATE <= 0.94
    heights = structure._taper_heights(4, 4 * 3.10, 2.60, maximum=3.90)
    assert heights[-1] <= 0.85 * heights[0], heights


def test_the_squeezed_storey_is_always_read_as_a_mezzanine_by_the_roles_phase() -> None:
    """S3's vocabulary and S4's predicate have to agree about what a
    compressed intermediate storey is. When they drifted apart, a 2.47 m
    entresol over a 4.15 m shop front was labelled an UPPER floor. This is
    the explicit tie between the two, so the drift cannot recur silently."""
    from buildings.typologies.paris.roles import Role, assign_roles

    seen = 0
    for year in (1800, 1870, 1890, 1910):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for i in range(0, 35):
                    g = solve_structure(
                        _site(street_width=6.0 + i * 1.0, parcel_width=12.0, year=year,
                              klass=klass, ground=ground)
                    )
                    rg = assign_roles(g)
                    for rs in rg.storeys:
                        if rs.slot.name != "entresol":
                            continue
                        seen += 1
                        assert rs.role is Role.MEZZANINE, (
                            year, klass, ground, [s.width for s in g.storeys],
                            [r.role.value for r in rg.storeys],
                        )
    assert seen > 0, "no grid in the sweep produced a squeezed storey at all"


# ===========================================================================
# A2.1 — the comble holds a storey, so Role.ATTIC is reachable
# ===========================================================================
#
# Across 1200 random situations the role tally used to read base 1200 /
# principal 1200 / upper 2536 / mezzanine 607 / attic 0: the contract declared
# a role the system could not produce. A Paris comble is not empty roof — the
# chambres de bonne are in it, lit by the lucarnes the termination phase
# already emits — so where the roof has the height and the depth for a room
# this phase puts a storey in it.


def _comble_storey(g: Grid):
    combles = g.comble_storeys
    return combles[0] if combles else None


def test_the_comble_holds_a_storey_where_it_has_the_room_for_one() -> None:
    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=15.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    comble = _comble_storey(g)
    assert comble is not None
    # It stands ON the eaves, not on the legal cornice and not in the air.
    assert comble.start == pytest.approx(g.eaves_height, abs=1e-9)
    assert comble.start == pytest.approx(g.built_height, abs=1e-9)
    # A person can stand up in it...
    assert comble.width >= 2.20 - 1e-9
    # ...and it is inside the roof over it, not through it. The roof over it is
    # `Grid.comble_height` — what the gabarit leaves above these eaves — and NOT
    # `envelope.ridge_height`, which is a height above the LEGAL cornice and
    # would deduct the unbuilt facade headroom from the garret a second time
    # (A3.1).
    assert comble.width <= g.comble_height + 1e-9
    assert comble.start + comble.width <= g.envelope.total_height + 1e-9


def test_the_comble_ceiling_over_the_eaves_is_the_gabarit_and_not_the_ridge_allowance() -> None:
    """A3.1, in the phase that sizes the garret — asserted on the CEILING,
    which is what A3.1 was ever about.

    ``envelope.ridge_height`` is a height above the LEGAL cornice. Reading it
    as a height above the eaves — which is what this module used to do, and
    said so in a docstring calling itself "deliberately conservative" — takes
    the cornice height the facade declined to build and deducts it from the
    legal solid as well. The solid's top does not descend with the eaves: the
    ceiling on the comble is that top reckoned from those eaves, capped only
    by the plot.

    **A8.5** is that a ceiling is not a height. See the test below.
    """
    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=14.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    env = g.envelope
    # A16.2 moved this number and did not move the claim: the facade now fills
    # the budget it was granted instead of losing the 0.30 m its entresol gave
    # back, so it stands 0.30 m higher and there is 0.30 m less of it unspent.
    # What A3.1 asserts is the RELATION under it, which is unchanged.
    assert g.unused_facade_headroom == pytest.approx(0.702, abs=1e-3)
    assert g.comble_ceiling == pytest.approx(
        env.ridge_height + g.unused_facade_headroom, abs=1e-9
    )
    assert g.eaves_height + g.comble_ceiling == pytest.approx(env.total_height, abs=1e-9)
    # The old answer, named, so a regression to it fails here rather than three
    # phases downstream in a silhouette that is merely shorter than it should be.
    # Under it the ceiling WAS the ridge allowance: every metre the facade
    # declined was deducted from the roof as well, so this difference was zero.
    assert g.comble_ceiling > env.ridge_height + 0.5


def test_the_comble_that_is_built_is_the_decrees_comble_not_the_ceiling() -> None:
    """A8.5. The ceiling above is a limit; what gets built is not it.

    Building to the ceiling meant the roof grew by exactly the cornice height
    the facade declined, so the two moved in lockstep and the sum never moved:
    ``eaves + comble == legal_total_height`` in every class, and the poorer the
    building the bigger its hat. Both harnesses found it independently — the
    sweep in the class table below, the oracle in 22 of its 29 proportion
    outliers, all ``total_height_m`` and all new > old.

    What is built is the decree's own comble allowance, sprung from the eaves
    this building actually has. So it is a function of the street, the era and
    the plot and of nothing about the owner, the ceiling above it goes unused,
    and the class shows up in the TOTAL through the stone underneath.
    """
    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=14.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    env = g.envelope
    assert g.comble_height == pytest.approx(env.ridge_height, abs=1e-9)
    # Strictly under the ceiling, and under it by exactly the height the stone
    # face declined to spend — which is the whole of A8.5's claim and a
    # stronger statement than the round margin that used to stand here (the
    # margin narrowed at A16.2 only because the facade now builds higher).
    assert g.comble_height < g.comble_ceiling - 1e-9
    assert g.comble_ceiling - g.comble_height == pytest.approx(
        g.unused_facade_headroom, abs=1e-9
    )
    assert g.eaves_height + g.comble_height < env.total_height - 0.5


def test_the_comble_is_the_same_on_every_class_and_the_total_is_not() -> None:
    """A8.5's own repro table, asserted.

    Measured before the fix, on one site with only the class varying: comble
    7.73 / 5.80 / 4.40 / 3.34 m — *inversely* proportional to class — with
    ``total_height == legal_total_height`` in all four. Both facts are the
    same bug. A comble is floor rather than show, so it does not vary with
    ambition at all; a facade is show, so it does; and the total therefore
    rises with the class, which is what "a modest building is shorter" means.
    """
    combles, totals = [], []
    for klass in BuildingClass:
        g = solve_structure(
            _site(street_width=20.0, parcel_width=16.0, parcel_depth=16.0,
                  year=1865, klass=klass, ground=GroundProgramme.RESIDENTIAL)
        )
        combles.append(round(g.comble_height, 9))
        totals.append(g.built_height + g.comble_height)
        assert g.built_height + g.comble_height < g.envelope.total_height - 1e-6, (
            f"{klass}: the building still reaches its legal total"
        )
    assert len(set(combles)) == 1, f"the comble varied with ambition: {combles}"
    assert totals == sorted(totals), f"totals not increasing with class: {totals}"
    assert totals[-1] - totals[0] > 3.0, totals


def test_the_two_anchors_meet_at_one_named_conversion_and_nowhere_else() -> None:
    """A3.1 §3: nothing computed above the cornice is applied at the eaves
    without an explicit conversion.

    ``_above_the_cornice_to_above_the_eaves`` is that boundary, and it is the
    only crossing. It adds exactly the cornice height the facade left unspent,
    it is the identity when the facade reached its ceiling, and it refuses —
    loudly — to convert for eaves standing *above* the cornice, which would
    silently shorten the very heights it exists to raise.
    """
    from buildings.typologies.paris.structure import (
        _above_the_cornice_to_above_the_eaves as convert,
    )

    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=14.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    env = g.envelope

    # It is exactly the drop from the legal cornice to the built eaves.
    assert convert(0.0, env, g.eaves_height) == pytest.approx(
        g.unused_facade_headroom, abs=1e-12
    )
    assert convert(env.ridge_height, env, g.eaves_height) == pytest.approx(
        g.comble_ceiling, abs=1e-9
    )

    # A facade that reached its ceiling has the two anchors in one place, and
    # the conversion is then the identity — which is why the defect was
    # invisible in the only case anyone checked by hand.
    assert convert(env.ridge_height, env, env.facade_height) == pytest.approx(
        env.ridge_height, abs=1e-12
    )

    # And the direction is asserted, not assumed.
    with pytest.raises(AssertionError):
        convert(env.ridge_height, env, env.facade_height + 0.5)


def test_the_garret_stands_behind_the_brisis_and_not_under_the_whole_comble() -> None:
    """Where the garret's ceiling is: the fold, not the ridge (A8.3).

    A *chambre de bonne* is the room behind the steep lower slope. What is
    over its ceiling is terrasson — roof, not headroom — so measuring the
    garret against the ridge made it taller than the storeys below it on any
    comble with a real terrasson on top.
    """
    g = solve_structure(
        _site(street_width=8.0, parcel_width=12.0, parcel_depth=12.0, year=1865,
              klass=BuildingClass.GRAND, ground=GroundProgramme.SHOP)
    )
    comble = _comble_storey(g)
    assert comble is not None
    assert g.unused_facade_headroom > 0.10
    assert comble.width <= g.brisis_height + 1e-9, (
        "the garret's ceiling stands above the fold its roof breaks at"
    )
    assert g.brisis_height <= g.comble_height + 1e-9


def test_the_comble_height_is_the_decrees_allowance_capped_by_the_plot() -> None:
    """Swept: the comble over the eaves is always exactly the smaller of the
    decree's own comble allowance, the height where the two opposing slopes
    meet, and the legal ceiling over these eaves.

    A8.5: the facade budget may not lengthen it either, which is the direction
    that was actually wrong. Nothing in this expression mentions the class."""
    for year in (1800, 1860, 1885, 1905):
        for klass in BuildingClass:
            for depth in (5.0, 8.0, 14.0, 22.0, 30.0):
                for street in (7.0, 12.0, 20.0, 32.0):
                    g = solve_structure(
                        _site(street_width=street, parcel_width=12.0,
                              parcel_depth=depth, year=year, klass=klass)
                    )
                    env = g.envelope
                    allowance = min(
                        env.ridge_height,
                        env.max_height_for_setback(depth / 2.0),
                        g.comble_ceiling,
                    )
                    assert g.comble_height <= allowance + 1e-9, (
                        year, klass, depth, street
                    )
                    assert g.comble_height >= g.brisis_height - 1e-9
                    assert g.comble_height <= g.comble_ceiling + 1e-9


def test_the_comble_does_not_vary_with_class_anywhere_in_the_situation_space() -> None:
    """A8.5, swept rather than shown on one site. Two buildings on the same
    street, era and plot carry the same comble whatever was spent on the stone
    under it, and the taller of the two is always the grander."""
    for year in (1800, 1860, 1885, 1905):
        for depth in (8.0, 14.0, 22.0):
            for street in (7.0, 12.0, 20.0, 32.0):
                grids = [
                    solve_structure(
                        _site(street_width=street, parcel_width=12.0,
                              parcel_depth=depth, year=year, klass=klass)
                    )
                    for klass in BuildingClass
                ]
                combles = {round(g.comble_height, 9) for g in grids}
                assert len(combles) == 1, (year, depth, street, combles)
                totals = [g.built_height + g.comble_height for g in grids]
                assert totals == sorted(totals), (year, depth, street, totals)


def test_a_comble_too_shallow_for_a_room_holds_no_storey() -> None:
    """The other half of the predicate, and it has to be reachable too: on a
    shallow parcel the two opposing slopes meet before there is a room's
    width of floor under full height, and the roof is then just a roof."""
    shallow = solve_structure(
        _site(street_width=12.0, parcel_width=10.0, parcel_depth=5.0, year=1875)
    )
    assert shallow.comble_storeys == ()
    assert shallow.built_height == pytest.approx(
        sum(s.width for s in shallow.storeys), abs=1e-9
    )
    deep = solve_structure(
        _site(street_width=12.0, parcel_width=10.0, parcel_depth=15.0, year=1875)
    )
    assert deep.comble_storeys, "the same building on a deep parcel does get one"


def test_the_comble_storey_is_never_outside_the_roof_over_it() -> None:
    """Swept: whatever the era, class, street and parcel, a storey standing in
    the comble stays under the ridge and keeps a room's depth of floor at its
    own ceiling. Both are the conditions it was emitted under, asserted on the
    grid that was actually returned."""
    seen = 0
    for year in (1800, 1860, 1885, 1905):
        for klass in BuildingClass:
            for depth in (6.0, 9.0, 14.0, 22.0):
                for street in (7.0, 12.0, 20.0, 32.0):
                    g = solve_structure(
                        _site(street_width=street, parcel_width=12.0,
                              parcel_depth=depth, year=year, klass=klass)
                    )
                    comble = _comble_storey(g)
                    if comble is None:
                        continue
                    seen += 1
                    env = g.envelope
                    # Under the roof that stands over it (A3.1: that is the
                    # gabarit's top reckoned from these eaves, not the ridge
                    # height re-anchored at them) and under the legal top.
                    assert comble.width <= g.comble_height + 1e-9
                    assert comble.start + comble.width <= env.total_height + 1e-9
                    floor_depth = depth - 2.0 * env.setback_at(comble.width)
                    assert floor_depth >= float(structure._COMBLE_ROOM_DEPTH) - 1e-6, (
                        year, klass, depth, street, comble.width, floor_depth,
                    )
    assert seen > 0, "no situation in the sweep put a storey in its comble"


def test_role_attic_is_reachable_and_both_answers_occur() -> None:
    """The A2.1 tally, re-run. ``ATTIC`` must appear — and the shallow case
    must still produce buildings without one, or the predicate has stopped
    being a predicate.

    **A15.1**: and a comble built to stand two bands of brisis holds TWO of
    them, so all three answers have to occur. A roof with two rows of lucarnes
    and one room behind them was the state this amendment found."""
    from buildings.typologies.paris.roles import Role, assign_roles

    with_attic = 0
    without_attic = 0
    two_attics = 0
    for year in (1820, 1865, 1890, 1910):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for depth in (5.0, 8.0, 14.0, 20.0):
                    for street in (8.0, 14.0, 22.0, 30.0):
                        g = solve_structure(
                            _site(street_width=street, parcel_width=12.0,
                                  parcel_depth=depth, year=year, klass=klass,
                                  ground=ground)
                        )
                        roles = [rs.role for rs in assign_roles(g).storeys]
                        n_attic = roles.count(Role.ATTIC)
                        # One storey of chambres de bonne per BAND of brisis
                        # the section stands, and never more: the rooms and
                        # the roof over them are one arithmetic (A15.1). The
                        # 45° gabarit stands one band and buys a second; the
                        # 1884 and 1902 arcs stand two and three of their own,
                        # which is what those decrees were for.
                        bands = max(
                            1,
                            int(g.brisis_height / float(structure.BRISIS_RISE) + 1e-9),
                        )
                        assert n_attic <= bands, (roles, g.brisis_height)
                        assert bands <= (
                            structure._garret_storeys_the_decree_stands(
                                g.envelope, depth
                            )
                            + g.extra_garret_storeys
                        ), (roles, g.brisis_height)
                        if n_attic >= 2:
                            two_attics += 1
                        if n_attic:
                            with_attic += 1
                            # the attic is the top of the stack and nothing else
                            assert roles[-1] is Role.ATTIC
                            assert Role.BASE in roles
                        else:
                            without_attic += 1
    assert with_attic > 0, "Role.ATTIC is still unreachable"
    assert without_attic > 0, "every comble now holds a storey — the test is vacuous"
    assert two_attics > 0, (
        "no comble in the sweep held two storeys of chambres de bonne — the mode "
        "Daly's 4.72-7.00 m combles are is unreachable again (A15.1)"
    )
    assert any(
        solve_structure(
            _site(street_width=22.0, parcel_width=12.0, parcel_depth=20.0,
                  year=1865, klass=klass, ground=GroundProgramme.SHOP)
        ).extra_garret_storeys == 1
        for klass in BuildingClass
    ), "the 45° era never reaches the two-storey mode (A15.1)"


def test_the_attic_is_derived_from_the_eaves_not_from_the_legal_ceiling() -> None:
    """The reason the role was dead: the predicate asked whether a storey
    started above the LEGAL cornice, and nothing ever did. A building that
    stops below its legal ceiling still roofs over its own wall."""
    from buildings.typologies.paris.roles import Role, assign_roles

    g = solve_structure(
        _site(street_width=20.0, parcel_width=12.0, parcel_depth=15.0,
              year=1865, klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    comble = _comble_storey(g)
    assert comble is not None
    # The situation that used to defeat the old predicate: the slot inside the
    # roof starts BELOW the legal cornice, because the facade declined to
    # spend its last metre of ambition.
    assert comble.start < float(g.cornice_height) - 0.5
    assert Role.ATTIC in {rs.role for rs in assign_roles(g).storeys}


# ===========================================================================
# A2.2 — the entresol is a programme decision, not leftover budget
# ===========================================================================


def _entresol_rate(klass: BuildingClass, ground: GroundProgramme) -> float:
    hits = total = 0
    for year in (1820, 1860, 1875, 1890, 1905):
        for i in range(0, 57):
            g = solve_structure(
                _site(street_width=6.0 + i * 0.5, parcel_width=13.0,
                      parcel_depth=15.0, year=year, klass=klass, ground=ground)
            )
            total += 1
            hits += any(s.name == "entresol" for s in g.storeys)
    return hits / total


def test_the_entresol_rate_rises_with_class_over_a_shop() -> None:
    """A2.2, stated as the measurement that failed.

    The old rate by class was 42 / 64 / 57 / 43 %: not monotonic, because the
    slot appeared wherever the class factor happened to squeeze the budget
    into an awkward remainder. On a boulevard an entresol over a shop is MORE
    common the richer the building, and now it is.
    """
    rates = {klass: _entresol_rate(klass, GroundProgramme.SHOP) for klass in BuildingClass}
    assert (
        rates[BuildingClass.MODEST]
        < rates[BuildingClass.ORDINARY]
        < rates[BuildingClass.COMFORTABLE]
        < rates[BuildingClass.GRAND]
    ), rates
    assert rates[BuildingClass.GRAND] > 0.5, rates


def test_a_residential_ground_floor_largely_does_not_get_an_entresol() -> None:
    """A hall and a stair have no use for a half-storey over them. The rate
    has to be low for every class — and, in particular, it must not rise when
    the height budget happens to leave an awkward remainder."""
    for klass in BuildingClass:
        assert _entresol_rate(klass, GroundProgramme.RESIDENTIAL) < 0.05, klass
        assert _entresol_rate(klass, GroundProgramme.CARRIAGE) < 0.05, klass


def test_a_commercial_ground_floor_is_what_asks_for_one() -> None:
    """The three trades ask; the other two do not. Same street, same class,
    same year — only the programme differs."""
    got = {}
    for ground in GroundProgramme:
        g = solve_structure(
            _site(street_width=30.0, parcel_width=13.0, year=1875,
                  klass=BuildingClass.GRAND, ground=ground)
        )
        got[ground] = any(s.name == "entresol" for s in g.storeys)
    assert got[GroundProgramme.SHOP]
    assert got[GroundProgramme.CAFE]
    assert got[GroundProgramme.OFFICE]
    assert not got[GroundProgramme.RESIDENTIAL]
    assert not got[GroundProgramme.CARRIAGE]


def test_no_storey_is_ever_a_leftover_special_any_more() -> None:
    """The mechanism, not just the outcome: the vertical solve is offered no
    ``special`` at all, so there is nothing the budget can leave over. If a
    slot ever comes back marked special on this axis, an entresol is being
    produced by arithmetic again."""
    for year in (1800, 1870, 1890, 1910):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for i in range(0, 29):
                    g = solve_structure(
                        _site(street_width=6.0 + i * 1.0, parcel_width=12.0,
                              year=year, klass=klass, ground=ground)
                    )
                    assert not any(s.is_special for s in g.storeys), [
                        s.name for s in g.storeys
                    ]


def test_the_entresol_is_decided_before_the_budget_is_filled() -> None:
    """The decision is a pure function of programme, class and the facade
    target — computable without solving anything — and the grid agrees with
    it every time. That is what "decided before the budget is filled" means
    operationally."""
    from buildings.typologies.paris.reglement import (
        compute_envelope,
        era_for_year,
        get_reglement,
    )

    checked = 0
    for year in (1820, 1875, 1905):
        reg = get_reglement(era_for_year(year))
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for street in (8.0, 12.0, 20.0, 30.0):
                    site = _site(street_width=street, parcel_width=13.0,
                                 year=year, klass=klass, ground=ground)
                    ceiling = reg.facade_height_limit(street)
                    # A15.1: the garret trade is taken first and changes what
                    # the ambition is a fraction OF, so the budget this
                    # prediction uses is the one the fill will actually see.
                    # Still computable without solving anything, which is the
                    # claim: two pure functions in sequence, not a budget read
                    # back off a solved grid.
                    envelope = compute_envelope(
                        street, era_for_year(year), site.parcel_depth
                    )
                    extra, _garret_why = structure._a_second_storey_of_chambres_de_bonne(
                        envelope, ground, ceiling, site.parcel_depth
                    )
                    ceiling -= structure._facade_given_up_for_a_bought_garret(extra)
                    band = structure._typical_storey_band(reg, klass)
                    entresol = float(structure._entresol_height(float(band[0])))
                    wanted, _why = structure._wants_an_entresol(
                        ground,
                        klass,
                        budget=ceiling * structure._FACADE_AMBITION[klass],
                        ground_height=float(
                            structure._ground_height_quantity(
                                ground,
                                klass,
                                catalogue.entrance_for(klass, street, ground),
                            )
                        ),
                        entresol_height=entresol,
                        storey_preferred=float(band[1]),
                    )
                    g = solve_structure(site)
                    assert any(s.name == "entresol" for s in g.storeys) is wanted
                    checked += 1
    assert checked > 100


def test_the_entresol_is_compressed_against_the_floor_it_serves_not_the_statute() -> None:
    """**A9.4, and it replaces a test asserting something Daly refutes.**

    This used to read "the entresol is shorter than the storey minimum it is
    exempt from", on the reasoning that a slot reaching the habitable minimum
    would simply be a storey. Daly measures nine Deuxième Classe entresols:
    **2.40-3.12 m, median 2.98 m** — six of the nine stand ABOVE the 1859
    decree's 2.60 m minimum, and the tallest is half a metre above it. A
    Paris entresol is not a slot squeezed under a legal floor.

    What it IS short of is the floor it serves. Daly gives that ratio too:
    the noble floor is 1.25× the compressed level in Première Classe and
    1.30× in Deuxième. So this asserts the relation the source actually
    measured, over the same sweep, plus the two measured bands the height and
    the ground-floor ratio have to land in.
    """
    for year in (1800, 1875, 1905):
        for klass in BuildingClass:
            g = solve_structure(
                _site(street_width=30.0, parcel_width=13.0, year=year,
                      klass=klass, ground=GroundProgramme.SHOP)
            )
            entresol = next((s for s in g.storeys if s.name == "entresol"), None)
            if entresol is None:
                continue
            over = [
                s.width
                for s in g.storeys
                if s.name not in ("ground", "entresol", "comble")
            ]
            assert over, (year, klass)
            # Shorter than the floor it serves, by Daly's own measured ratio.
            assert entresol.width <= max(over) / 1.275 + 1e-9, (year, klass, entresol.width, over)
            # And, where the section could afford it, inside Daly's measured
            # entresol/ground band of 0.585-0.871.
            ratio = entresol.width / g.storeys[0].width
            assert ratio <= 0.871 + 1e-9, (year, klass, ratio)


# ===========================================================================
# A2.3 — facade ambition and comble fill are different decisions
# ===========================================================================


def test_only_the_facade_carries_an_ambition_constant() -> None:
    """A8.5. The pair used to be ``_FACADE_AMBITION`` and ``_COMBLE_FILL`` —
    one fraction of the legal ceiling each. Splitting them was right and
    keeping the comble on a fraction at all was not: with the roof taking
    0.99 of whatever the facade left over it, the two fractions summed to a
    constant and every building came out at its legal total.

    So there is exactly ONE ambition constant now, it belongs to the stone,
    and the comble is a height rather than a share."""
    assert hasattr(structure, "_FACADE_AMBITION")
    assert not hasattr(structure, "_COMBLE_FILL"), (
        "the comble is back on a fraction of the legal solid"
    )
    assert not hasattr(structure, "_AMBITION_FRACTION"), (
        "the one constant that did both jobs is back"
    )
    # Facade ambition is a class table and only its ordering is contractual.
    amb = structure._FACADE_AMBITION
    assert (
        amb[BuildingClass.MODEST]
        < amb[BuildingClass.ORDINARY]
        < amb[BuildingClass.COMFORTABLE]
        < amb[BuildingClass.GRAND]
        <= 1.0
    )
    # And the comble's own figure is a body, not a fraction: the chambre de
    # bonne behind the brisis, ABSOLUTE, identical for every class.
    assert structure.BRISIS_RISE.kind is Kind.ABSOLUTE
    assert 2.0 < float(structure.BRISIS_RISE) < 4.0


def test_moving_facade_ambition_does_not_move_the_roofline(monkeypatch) -> None:
    """The defect A2.3 names: one number decided both, so a change intended
    to affect facade ambition silently moved the roof."""
    site = _site(street_width=22.0, parcel_width=13.0, parcel_depth=16.0,
                 year=1875, klass=BuildingClass.MODEST)
    before = solve_structure(site)
    monkeypatch.setitem(structure._FACADE_AMBITION, BuildingClass.MODEST, 0.60)
    after = solve_structure(site)
    assert after.built_height < before.built_height - 0.5  # the facade moved...
    assert after.envelope.ridge_height == pytest.approx(  # ...and the roof did not
        before.envelope.ridge_height, abs=1e-9
    )


def test_a_modest_building_no_longer_gets_a_shallower_garret() -> None:
    """Backwards for where the servants actually lived: under the shared
    constant a MODEST comble was filled to 0.74 and a GRAND one to 0.99. The
    comble is the same roof on the same street whoever owns the building.

    Three things say that, and they are asserted rather than the one
    consequence that used to stand in for them (four identical garret heights,
    which only held because every comble was capped at ``ridge_height`` and
    stopped holding the moment the unbuilt facade headroom was given back to
    the roof — A3.1):

    * the comble the DECREE gives is class-blind — ``legal_ridge_height`` and
      ``ridge_height`` are one number for all four;
    * the comble each class BUILDS is that same number, so moving
      ``_FACADE_AMBITION`` moves the eaves and nothing else about the roof;
    * every class gets a garret storey, which is the specific damage the
      shared constant did.

    **A8.5** changed the third consequence this test used to check. The tops
    were once identical across classes — the roof recovered whatever the
    facade declined, so all four reached the gabarit — and that identity was
    the defect, not the property. The roofline is now the same SHAPE at
    different heights, which is what "moving ambition moves the eaves" means
    when the sum is allowed to move too.
    """
    ridges = {}
    legal = {}
    tops = {}
    over_the_eaves = {}
    combles = {}
    for klass in BuildingClass:
        g = solve_structure(
            _site(street_width=22.0, parcel_width=30.0, parcel_depth=30.0,
                  year=1875, klass=klass)
        )
        ridges[klass] = g.envelope.ridge_height
        legal[klass] = g.envelope.legal_ridge_height
        tops[klass] = g.eaves_height + g.comble_height
        over_the_eaves[klass] = g.comble_height
        combles[klass] = [s.width for s in g.comble_storeys]
    assert len(set(round(v, 9) for v in ridges.values())) == 1, ridges
    assert len(set(round(v, 9) for v in legal.values())) == 1, legal
    # A parcel deep enough that nothing is depth-limited: every class carries
    # the decree's own comble, and the tops differ by exactly the stone.
    assert len(set(round(v, 9) for v in over_the_eaves.values())) == 1, over_the_eaves
    assert len(set(round(v, 9) for v in tops.values())) == 4, tops
    for klass in BuildingClass:
        assert over_the_eaves[klass] == pytest.approx(ridges[klass], abs=1e-9), (
            klass, over_the_eaves
        )
        assert combles[klass], (klass, combles)

    # On a parcel too shallow for that, the roof is cut off where its own two
    # slopes meet — by the plot, never by what the owner spent on the facade.
    for klass in BuildingClass:
        g = solve_structure(
            _site(street_width=22.0, parcel_width=13.0, parcel_depth=16.0,
                  year=1875, klass=klass)
        )
        expected = min(
            g.envelope.ridge_height,
            g.envelope.max_height_for_setback(16.0 / 2.0),
        )
        assert g.comble_height == pytest.approx(expected, abs=1e-9), klass


# ------------------------------------------- rounding the facade target


def test_budget_candidates_are_the_heights_whole_storeys_can_fill() -> None:
    """Nearest first, never above the legal ceiling, ties to the taller
    stack. The target is a target; the section is built of whole storeys."""
    # reserved 4.0, storeys in [2.6, 3.6]: the reachable windows are
    # [6.6, 7.6], [9.2, 11.2], [11.8, 14.8], ...
    got = structure._budget_candidates(
        target=8.4, ceiling=100.0, reserved=4.0,
        storey_minimum=2.6, storey_maximum=3.6, max_storeys=4,
    )
    assert got[0] == pytest.approx(9.2)  # 0.8 up beats 0.8 down, taller wins
    assert all(v <= 100.0 for v in got)
    # inside a window the target is reachable exactly
    got2 = structure._budget_candidates(
        target=10.0, ceiling=100.0, reserved=4.0,
        storey_minimum=2.6, storey_maximum=3.6, max_storeys=4,
    )
    assert got2[0] == pytest.approx(10.0)


def test_budget_candidates_never_round_up_past_the_legal_ceiling() -> None:
    got = structure._budget_candidates(
        target=8.4, ceiling=8.5, reserved=4.0,
        storey_minimum=2.6, storey_maximum=3.6, max_storeys=4,
    )
    assert got, "there is a reachable height below the ceiling"
    assert all(v <= 8.5 + 1e-9 for v in got)
    assert got[0] == pytest.approx(7.6)  # the top of the one-storey window


def test_a_ceiling_that_cannot_hold_one_storey_offers_nothing() -> None:
    assert structure._budget_candidates(
        target=5.0, ceiling=5.0, reserved=4.0,
        storey_minimum=2.6, storey_maximum=3.6, max_storeys=4,
    ) == []


def test_the_facade_never_rounds_up_past_the_legal_ceiling_anywhere() -> None:
    for year in (1800, 1860, 1885, 1905):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                for i in range(0, 29):
                    g = solve_structure(
                        _site(street_width=6.0 + i * 1.0, parcel_width=12.0,
                              year=year, klass=klass, ground=ground)
                    )
                    assert g.built_height <= float(g.cornice_height) + 1e-6, (
                        year, klass, ground, g.built_height, float(g.cornice_height),
                    )


# ===========================================================================
# A6.1 — the entrance, on every frontage, in phase 1
# ===========================================================================


def test_every_grid_carries_exactly_one_entrance_slot() -> None:
    """A6.1 in the phase that places it. The entrance used to be reachable
    only through ``GroundProgramme.CARRIAGE``, so every shop, café, office and
    residential frontage in the city came out of phase 1 sealed."""
    checked = 0
    for street in (7.0, 12.0, 20.0, 30.0):
        for width in (7.0, 9.5, 12.0, 16.0, 22.0):
            for klass in BuildingClass:
                for ground in GroundProgramme:
                    site = _site(
                        street_width=street,
                        parcel_width=width,
                        klass=klass,
                        ground=ground,
                    )
                    try:
                        g = solve_structure(site)
                    except FitInfeasible:
                        continue
                    doors = [
                        s for s in g.bays if s.name in catalogue.ENTRANCE_SLOT_NAMES
                    ]
                    assert len(doors) == 1, (street, width, klass, ground, [s.name for s in g.bays])
                    checked += 1
    assert checked > 200


def test_the_entrance_slot_is_absolute_and_does_not_scale_with_the_class() -> None:
    """The door is the ruler, and A27 moved which part of it is the ruler.

    This test used to assert that the entrance SLOT comes out at exactly
    ``catalogue.entrance_slot_width`` — "the clear opening plus the jamb its
    head lands on either side, and both are ABSOLUTE". That was the rigid-slot
    behaviour, and it is the thing A27 removed on purpose: a slot pinned to its
    own width while everything beside it is elastic made the masonry next to
    the biggest hole in the facade the THINNEST masonry on the frontage.

    What is ABSOLUTE is the **clear opening** — the body or the vehicle that
    has to pass — and ``entrance_slot_width`` is now what it always described
    itself as, the *minimum* the slot may be. The slot itself takes the
    frontage's own pitch where the pitch will hold it. So the claim under test
    is unchanged in substance and sharper in statement:

    * the opening does not move with the class — not by a millimetre;
    * the slot does not move with the class either;
    * the slot is never narrower than the opening plus its two jambs;
    * and the bays beside it DO move with the class, which is the contrast the
      absolute/proportional split exists to produce.
    """
    slots: dict[str, set[float]] = {}
    clears: dict[str, set[float]] = {}
    bays: set[float] = set()
    for klass in BuildingClass:
        g = solve_structure(_site(street_width=20.0, parcel_width=18.0, klass=klass))
        (door,) = [s for s in g.bays if s.name in catalogue.ENTRANCE_SLOT_NAMES]
        ground_h = g.storeys[0].width
        slots.setdefault(door.name, set()).add(round(door.width, 9))
        clears.setdefault(door.name, set()).add(
            round(catalogue.entrance_in_slot(door.name, door.width, ground_h).width, 9)
        )
        # The same door cut in the narrowest slot the catalogue will admit. If
        # the opening is ABSOLUTE these two are the same number whatever the
        # slot did, which is the whole claim: the slot grew, the door did not.
        floor = float(catalogue.entrance_slot_width(door.name))
        assert door.width >= floor - 1e-9, (door.name, door.width, floor)
        clears[door.name].add(
            round(catalogue.entrance_in_slot(door.name, floor, ground_h).width, 9)
        )
        bays |= {round(s.width, 9) for s in g.bays if s.name == "bay"}
    for name, seen in clears.items():
        assert len(seen) == 1, f"{name}'s clear opening moved: {seen}"
    for name, seen in slots.items():
        assert len(seen) == 1, f"{name} changed width with the class: {seen}"
    assert len(bays) > 1, "the ordinary bays should be moving even though the door is not"


def test_the_ground_storey_is_tall_enough_for_the_door_standing_in_it() -> None:
    """A programme's want and a door's ABSOLUTE need are two claims on the
    ground storey's height, and the door's is a floor under it: a storey that
    could not hold its own entrance is a storey the catalogue would refuse."""
    for street in (7.0, 14.0, 26.0):
        for klass in BuildingClass:
            for ground in GroundProgramme:
                site = _site(street_width=street, parcel_width=14.0, klass=klass, ground=ground)
                try:
                    g = solve_structure(site)
                except FitInfeasible:
                    continue
                (door,) = [s for s in g.bays if s.name in catalogue.ENTRANCE_SLOT_NAMES]
                ground_slot = g.storeys[0]
                assert ground_slot.width >= float(
                    catalogue.entrance_storey_height(door.name)
                ) - 1e-9, (street, klass, ground, door.name, ground_slot.width)
                # And the catalogue agrees: it cuts the opening rather than
                # raising, which is the same claim asked of the other module.
                catalogue.entrance_in_slot(door.name, door.width, ground_slot.width)


def test_a_parcel_too_narrow_for_its_entrance_is_refused_not_shrunk() -> None:
    """A5.5's rule, generalised by A6.1: the door does not get smaller so the
    parcel can have one. The refusal names the entrance, not a bounds vector."""
    with pytest.raises(FitInfeasible, match="entrance"):
        solve_structure(_site(parcel_width=1.5, klass=BuildingClass.MODEST))


# ===========================================================================
# A9.1 / A9.2 / A9.4 — Daly 1864 against the section and the bay run
# ===========================================================================


def test_the_1859_ceiling_is_visible_in_the_two_top_classes() -> None:
    """**A9.4 — the regulation is visible in the data, and the model must
    reproduce it.**

    Daly's cornice heights above the pavement are 19.11 / 18.90 / 15.79 m
    down the class ladder. The step between the two TOP classes is 0.21 m —
    nothing, well inside the corpus's own 0.2-0.4 m error on a storey height
    — while the step down to the bottom class is 3.1 m and is real. Six of
    the sixteen buildings sit between 19.0 and 20.0 m, and they are not a
    class ladder at that end: they are a queue against the 1859 decree's 20 m
    facade maximum for a wide street.

    This is the most direct evidence the project has that the REGULATORY
    quantity is doing real work, so it is asserted three ways: the ceiling is
    the decree's own 20 m, the two upper classes both build into Daly's
    19.0-20.0 m band, and neither of them crosses the line.

    **A15.1 — which buildings queue.** The run is a residential one, where it
    used to be commercial, and that is Daly's own correlation rather than a
    convenience. His six cornices between 19.0 and 20.0 m all belong to
    buildings with a PLAIN mansard over them (2.69-3.45 m of comble); the two
    that put a second storey of *chambres de bonne* in the roof — 1 and 2-4
    boulevard de Sébastopol, 6.80 m and 7.00 m — sit at 17.55 m and 17.52 m, a
    metre and a half below the queue, because the legal solid does not move and
    the roof took its rooms out of the stone. A run making that trade is not in
    the queue and never was: it queues against a line one *chambre de bonne*
    lower, which is a fact about the same decree and is asserted in the A15
    block at the end of this file. What is measured here is the queue itself,
    on a run that is not trading.
    """
    ceiling = None
    built = {}
    for klass in BuildingClass:
        g = solve_structure(
            _site(street_width=30.0, parcel_width=16.0, parcel_depth=15.0,
                  year=1865, klass=klass, ground=GroundProgramme.RESIDENTIAL)
        )
        ceiling = float(g.cornice_height)
        built[klass] = g.eaves_height

    # The 1859 règlement's facade maximum for a street over 20 m.
    assert ceiling == pytest.approx(20.00)

    # Both upper classes come to rest against the ceiling rather than at a
    # height their purses chose. Daly's own two top classes sit 0.89 m and
    # 1.10 m under it (19.11 and 18.90 against 20.00), so "pinned" means
    # within about a metre and a half, not exactly on the line — a section is
    # built of whole storeys and the last one either fits or does not.
    top = (BuildingClass.COMFORTABLE, BuildingClass.GRAND)
    for klass in top:
        assert ceiling - 1.5 <= built[klass] <= ceiling, (klass, built[klass])
        # And inside the band Daly measured for those two classes, 18.53-21.05 m.
        assert 18.5 <= built[klass] <= 21.1, (klass, built[klass])
    # Flat at the top: the two upper classes are closer to each other than
    # either is to the class below, which is the shape of Daly's ladder.
    assert (
        built[BuildingClass.GRAND] - built[BuildingClass.COMFORTABLE]
        < built[BuildingClass.COMFORTABLE] - built[BuildingClass.ORDINARY]
    ), built
    # And nothing anywhere crosses the decree.
    for klass, h in built.items():
        assert h <= ceiling + 1e-9, (klass, h)


def _axes_and_door(**site_kwargs) -> tuple[int, str]:
    """How many window axes this frontage carries, and which door it has.

    An axis is a repeating bay or the entrance column — above the ground
    storey the entrance column is an ordinary bay carrying an ordinary
    window, which is what ``RoledGrid.lit_bays`` states and what
    ``qualify.base.over_the_entrance`` puts there.
    """
    g = solve_structure(_site(parcel_depth=18.0, year=1865, **site_kwargs))
    axes = sum(
        1 for s in g.bays if s.name == "bay" or s.name in catalogue.ENTRANCE_SLOT_NAMES
    )
    door = next(s.name for s in g.bays if s.name in catalogue.ENTRANCE_SLOT_NAMES)
    return axes, door


def test_the_axis_count_is_a_function_of_frontage_and_door_only() -> None:
    """**A9.1/A9.2/D6, closed at A10.2 — and the model was right, the metric
    was wrong.**

    A10.2 measured GRAND carrying fewer openings than MODEST on some
    frontages and read it as the D6 defect surviving. It is not. Every
    surviving case is a **door**, and the door is not a class scaling — it is
    an entitlement, which is exactly what Daly's corpus says distinguishes
    the classes (a carriage entrance in 4 of 4 Première, 3 of 10 Deuxième,
    0 of 2 Troisième). A building with a carriage arch has spent 3.40 m of
    its frontage on a hole a vehicle drives through, where a pedestrian door
    spends 2.35 m; on a 12, 18 or 20 m parcel that 1.05 m really is one axis,
    and a generator that hid it would be lying about a trade a real owner
    made.

    So the comparison is the thing that had to change: **like with like, same
    door**. And once it is stated that way the contract available is far
    sharper than the "never falls as class rises" it replaces —

        the axis count is a pure function of (frontage, entrance kind).

    Class does not appear in it. Neither does the street width, nor the
    ground programme except through the door it names. That is the strongest
    form of "money must not buy a blanker wall" this system can state, it is
    exact rather than an inequality, and it is what the two ABSOLUTE
    decisions behind D6 bought: the bay pitch carries no class trend (A9.4 —
    Daly's sixteen buildings are non-monotonic in it, 2.81 / 2.85 / 2.54 m)
    and the edge pier is ABSOLUTE (A9.1 — 0.35 m of extra pier over two ends
    is a whole axis on a 20 m frontage). Measured before those two changes
    the count fell on 21 of 32 situations.

    The cost of the door is asserted separately, and bounded, in
    ``test_a_carriage_arch_costs_one_axis_at_most_and_the_class_costs_none``.
    """
    buckets: dict[tuple[float, str], set[int]] = {}
    for parcel in (8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0):
        for street in (10.0, 16.0, 20.0, 30.0):
            for ground in GroundProgramme:
                for klass in BuildingClass:
                    axes, door = _axes_and_door(
                        street_width=street, parcel_width=parcel,
                        klass=klass, ground=ground,
                    )
                    buckets.setdefault((parcel, door), set()).add(axes)
    assert buckets, "the sweep produced no buildings"
    for (parcel, door), counts in sorted(buckets.items()):
        assert len(counts) == 1, (
            f"a {parcel:.0f} m frontage with a {door} carries {sorted(counts)} axes "
            "depending on class, street or programme — the axis count must be a "
            "function of the frontage and the door alone"
        )


def test_a_carriage_arch_costs_one_axis_at_most_and_the_class_costs_none() -> None:
    """**A10.2, the other half: what the door costs, said out loud.**

    The test above proves class buys no axis. This one prices the door, with
    the class held fixed so that nothing else can be blamed: the same
    building on the same parcel, once with a porte piétonne and once with a
    porte cochère (``GroundProgramme.CARRIAGE`` names the door outright, for
    every class).

    A carriage arch costs **one axis or none, never two**. It cannot cost
    two: 3.40 - 2.35 = 1.05 m, and the narrowest bay this module will place
    is 2.70 m, so the frontage a carriage entrance takes over a pedestrian
    one is less than half a bay.

    And the loss is real where it happens: on a 12 m frontage the pedestrian
    building gets four axes and the carriage building three, which is what
    Paris looks like. It is recorded here rather than smoothed away.
    """
    priced = 0
    for parcel in (8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0):
        for klass in BuildingClass:
            walked, door_w = _axes_and_door(
                street_width=10.0, parcel_width=parcel,
                klass=klass, ground=GroundProgramme.RESIDENTIAL,
            )
            assert door_w == catalogue.ENTRANCE_PEDESTRIAN, (parcel, klass, door_w)
            driven, door_c = _axes_and_door(
                street_width=10.0, parcel_width=parcel,
                klass=klass, ground=GroundProgramme.CARRIAGE,
            )
            assert door_c == catalogue.ENTRANCE_CARRIAGE, (parcel, klass, door_c)
            assert walked - 1 <= driven <= walked, (
                f"a {parcel:.0f} m {klass.value} frontage carries {walked} axes with a "
                f"porte piétonne and {driven} with a porte cochère; an arch may cost "
                "one axis, never two and never none-but-negative"
            )
            priced += 1

    # The arithmetic that makes "never two" true, stated rather than trusted.
    #
    # A26: the figure was 1.05 m, from a 3.40 m carriage slot against a 2.35 m
    # pedestrian one. The carriage slot is now 3.04 m, because the A26 bay
    # ceiling of 3.20 m would not admit 3.40 and the jamb came in to 0.22 m
    # (PROVISIONAL — see ``catalogue.carriage_jamb_width``). So the arch costs
    # 0.69 m of frontage rather than 1.05 m. The *relation* is what this test
    # is about and it holds more comfortably than before: the difference is
    # still under one bay, which is why an arch can never cost two axes.
    extra = float(catalogue.carriage_slot_width()) - float(
        catalogue.pedestrian_slot_width()
    )
    assert extra == pytest.approx(0.69, abs=1e-9), extra
    assert extra < float(structure._BAY_PITCH_MIN), (extra, structure._BAY_PITCH_MIN)
    assert priced == 32

    # Three frontages on which the arch really does cost the axis, pinned as
    # door effects rather than class ones: it costs it to a MODEST building
    # with a carriage entrance exactly as much as to a GRAND one. That is the
    # whole of the residual, and it is the part of A10.2 that matters.
    #
    # A26 moved *which* three frontages those are, and moved the counts on all
    # of them, for two compounding reasons: the bay band came in to
    # 2.00 / 2.60 / 3.20 so every frontage carries more axes than it did, and
    # the carriage slot came in to 3.04 m so the arch costs 0.69 m rather than
    # 1.05 m. 12.0 m used to be an arch-costs-an-axis width and is no longer
    # one — at 4 axes either way the 0.69 m no longer crosses a bay boundary —
    # so it is replaced here by 10.0 m, which is. The claim under test is
    # unchanged; only the widths that witness it have moved.
    #
    # **A27 moved one of them again, for the same species of reason.** The
    # pedestrian entrance now stands IN the rhythm, so it takes the frontage's
    # own pitch rather than its own 2.35 m — which is more frontage, and on
    # roughly one width in ten it is enough more to cost the pedestrian
    # building an axis. 20.0 m is one of those: the walked count fell from 8 to
    # 7 and met the driven count there, so the width stopped witnessing
    # anything. 20.5 m witnesses it instead. Measured over 8-22 m at half-metre
    # steps the arch costs exactly one axis at 10.0, 12.5, 18.0 and 20.5 m and
    # nothing anywhere else, identically for MODEST and GRAND — which is the
    # claim, and it survived A27 intact.
    for parcel, walked_expected, driven_expected in (
        (10.0, 4, 3), (18.0, 7, 6), (20.5, 8, 7)
    ):
        for klass in (BuildingClass.MODEST, BuildingClass.GRAND):
            walked, _ = _axes_and_door(
                street_width=10.0, parcel_width=parcel,
                klass=klass, ground=GroundProgramme.RESIDENTIAL,
            )
            driven, _ = _axes_and_door(
                street_width=10.0, parcel_width=parcel,
                klass=klass, ground=GroundProgramme.CARRIAGE,
            )
            assert (walked, driven) == (walked_expected, driven_expected), (
                parcel, klass, walked, driven
            )


# ------------------------------------------------------------------- A10.1
# The bay-pitch band is ABSOLUTE and stated. A9 guarded its ceiling and left
# its floor unguarded, which let a stated bound be silently crossed on one
# side while it was enforced on the other. These four tests say what the
# floor is a floor UNDER, and check it there.


def test_the_bay_pitch_floor_names_the_repeating_bay() -> None:
    """**A10.1.** The floor is a statement about a *rhythm* — the module the
    solver lays down over and over — not about every slot standing in the
    run. Two slots are deliberately below it, and both say so:

    * the narrow special, whose whole band (1.10-1.80 m) lies under the
      floor, because being narrower than a bay is its definition;
    * the entrance, 2.35 m for a porte piétonne.

    The reason it is stated rather than fixed is that the entrance's 2.35 m
    is not free to move. 1.75 m of it is Daly's SOURCED median of eight
    measured doors, and the jambs either side are 0.30 m.

    **A26 — the floor moved to 2.00 m and the rule did not.** The operator set
    the band at 2.00 / 2.60 / 3.20. That happens to put the porte piétonne's
    2.35 m slot *above* the floor rather than below it, so the illustration
    this test used to lean on — a door under the floor, and the dishonest jamb
    it would take to lift it over — no longer applies to that door. What the
    rule is about is unchanged and still has a witness: the narrow special's
    whole band lies under the floor, because being narrower than a bay is what
    a narrow special is. That is asserted directly below instead, which is the
    stronger statement anyway: it does not depend on which of two doors the
    arithmetic happens to put where.
    """
    assert "REPEATING" in structure._BAY_PITCH_MIN.why, structure._BAY_PITCH_MIN.why
    assert float(structure._BAY_PITCH_MIN) == 2.00
    assert "OPERATOR-SET" in structure._BAY_PITCH_MIN.why

    # The narrow special: a slot that is *defined* by being under the floor,
    # and the reason the floor has to name the repeating bay rather than every
    # slot in the run.
    special_hi = 1.80
    assert special_hi < float(structure._BAY_PITCH_MIN), special_hi

    pedestrian = float(catalogue.pedestrian_slot_width())
    assert pedestrian == pytest.approx(2.35, abs=1e-9), pedestrian
    # The entrance is a one-off standing in the rhythm, not a member of it, so
    # it is bounded by its own two checks and not by this floor — which is the
    # whole content of A10.1 and stays true whichever side of the floor the
    # door lands on. Recorded here because it has just changed sides.
    assert pedestrian > float(structure._BAY_PITCH_MIN), pedestrian


def test_the_bay_pitch_floor_holds_over_every_repeating_bay() -> None:
    """**A10.1.** What the floor DOES apply to, checked where it applies.

    Every repeating bay the solver returns, over a dense sweep of frontages,
    streets, programmes and classes, lies inside the ABSOLUTE band — and the
    slots that are not bays are outside it on purpose, so the sweep is only
    meaningful if it distinguishes them.
    """
    lo, hi = float(structure._BAY_PITCH_MIN), float(structure._BAY_PITCH_MAX)
    seen = 0
    for parcel in [round(6.0 + 0.25 * i, 2) for i in range(0, 65)]:
        for street in (8.0, 12.0, 20.0, 30.0):
            for ground in (GroundProgramme.RESIDENTIAL, GroundProgramme.CARRIAGE):
                for klass in (BuildingClass.MODEST, BuildingClass.GRAND):
                    try:
                        g = solve_structure(
                            _site(street_width=street, parcel_width=parcel,
                                  parcel_depth=18.0, year=1865, klass=klass,
                                  ground=ground)
                        )
                    except FitInfeasible:
                        continue
                    for s in g.bays:
                        if s.name != "bay":
                            continue
                        seen += 1
                        assert lo - 1e-9 <= s.width <= hi + 1e-9, (
                            parcel, street, klass, s.width
                        )
    assert seen > 500, seen


def test_a_bay_narrower_than_the_floor_is_refused() -> None:
    """**A10.1.** The floor bites, exactly as ``_BAY_PITCH_MAX``'s tripwire
    does. Widen what a bay may narrow to below the band and the postcondition
    catches it rather than letting a warehouse rhythm out of the phase."""
    original = structure._bay_pitch_band

    def narrow(klass):
        return (1.20, 1.30, 1.40)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(structure, "_bay_pitch_band", narrow)
        with pytest.raises(RuntimeError, match="a repeating bay came back"):
            solve_structure(
                _site(street_width=20.0, parcel_width=18.0, parcel_depth=18.0,
                      year=1865, klass=BuildingClass.GRAND,
                      ground=GroundProgramme.RESIDENTIAL)
            )
    assert structure._bay_pitch_band is original


def test_an_entrance_too_narrow_to_carry_a_light_is_refused() -> None:
    """**A10.1.** The entrance's own lower bound, which is not the bay
    floor.

    What constrains a one-off column standing in the rhythm is what the
    column has to do: carry a light with a pier either side on every storey
    above the pavement. That width is the narrow special's own minimum,
    1.10 m, which this phase already states once. Below it the entrance
    column goes blank all the way up and the frontage carries a full-height
    blind stripe through its middle — the sideways twin of the D6 defect the
    3.40 m tripwire catches.
    """
    from buildings.quantity import Abs
    from buildings.solver.fitting import SlotKind

    tiny = catalogue.ModuleSpec(
        name="door_pedestrian",
        slot_kind=SlotKind.FIXED,
        minimum=Abs(0.40, "a test's absurdly narrow door"),
        preferred=Abs(0.40, "a test's absurdly narrow door"),
        maximum=Abs(0.40, "a test's absurdly narrow door"),
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(catalogue, "door_pedestrian", lambda: tiny)
        # 0.40 + 2 x 0.30 = 1.00 m, under the 1.10 m a column needs to hold a
        # light — and still nowhere near the 2.70 m bay floor, which is the
        # point: these are two different bounds over two different things.
        assert float(catalogue.pedestrian_slot_width()) == pytest.approx(1.00)
        with pytest.raises(RuntimeError, match="narrowest strip that carries a light"):
            solve_structure(
                _site(street_width=8.0, parcel_width=16.0, parcel_depth=18.0,
                      year=1865, klass=BuildingClass.MODEST,
                      ground=GroundProgramme.RESIDENTIAL)
            )


def test_the_bay_rhythm_is_the_same_for_every_class() -> None:
    """A9.4. Daly's bay pitches are 2.81 / 2.85 / 2.54 m by class — Deuxième
    ABOVE Première, so non-monotonic — with within-class spread of 1.5× in
    both top classes, larger than any difference between them. Première alone
    runs 2.32 to 3.49 m. The measurement pass marks bay pitch INSUFFICIENT as
    a class discriminator, and A8.6's residual one-third trend is gone.

    **A26 — the figure is now OPERATOR-SET, not INFERRED.** It was 2.80 m and
    agreed with two independent corpus medians of 2.80 m, which is what
    "INFERRED and corroborated" meant here. The operator set it at 2.60 m. It
    no longer equals either median, so the citation says OPERATOR-SET and this
    test holds it to that instead — a number that agrees with a source and a
    number taken from one were always different things, and so is a number
    that used to agree with one.

    The class finding is untouched and is what this test is actually for: the
    band is identical for every class, because Daly's pitches are 2.81 / 2.85 /
    2.54 m and there is no ladder in them.
    """
    bands = {klass: structure._bay_pitch_band(klass) for klass in BuildingClass}
    assert len(set(bands.values())) == 1, bands
    assert "OPERATOR-SET" in structure._BAY_PITCH_PREFERRED.why
    assert "INFERRED" not in structure._BAY_PITCH_PREFERRED.why
    lo, pref, hi = bands[BuildingClass.GRAND]
    assert lo <= pref <= hi
    # Daly's corpus range, as the band the resting pitch still has to lie in —
    # the operator moved the figure, not out of the range the plates show.
    assert 2.09 <= pref <= 3.49


def test_the_compressed_level_is_a_class_marker_and_the_nobile_follows_it() -> None:
    """**A9.4 — the structural finding, asserted as structure.**

    Fourteen of Daly's sixteen buildings carry a compressed storey between
    the ground floor and the noble floor: 4 of 4 Première (dressed as a low
    *1er étage*, 3.20-3.60 m), 10 of 10 Deuxième (dressed as an entresol,
    2.40-3.12 m), **0 of 2 Troisième**. The two Troisième buildings have no
    compressed level and no piano nobile either — their étages are equal
    within 0.07 m.

    So the presence of the compressed level is a categorical class marker,
    which is what ``_ENTRESOL_STOREYS_REQUIRED`` states, and where it appears
    the roles phase must read it as the compressed level rather than as an
    étage. Both halves here.
    """
    from buildings.typologies.paris.roles import Role, assign_roles

    # The bar for buying one falls as class rises — the ordering is the
    # contract, and it is what makes the compressed level commoner the richer
    # the building, which is Daly's 4/4 against 0/2.
    required = [
        structure._ENTRESOL_STOREYS_REQUIRED[k]
        for k in (
            BuildingClass.MODEST,
            BuildingClass.ORDINARY,
            BuildingClass.COMFORTABLE,
            BuildingClass.GRAND,
        )
    ]
    assert required == sorted(required, reverse=True), required

    seen = 0
    for klass in BuildingClass:
        g = solve_structure(
            _site(street_width=30.0, parcel_width=16.0, parcel_depth=18.0,
                  year=1865, klass=klass, ground=GroundProgramme.SHOP)
        )
        rg = assign_roles(g)
        compressed = [rs for rs in rg.storeys if rs.slot.name == "entresol"]
        if not compressed:
            continue
        seen += 1
        assert compressed[0].role is Role.MEZZANINE, (klass, compressed[0].role)
        # And it is compressed against the floor it serves, not against the
        # statute: Daly's nine entresols are 2.40-3.12 m and six of them
        # clear the 1859 decree's 2.60 m minimum.
        nobile = next(rs for rs in rg.storeys if rs.role is Role.PRINCIPAL)
        assert compressed[0].slot.width < nobile.slot.width
        assert 2.40 <= compressed[0].slot.width <= 3.12, (klass, compressed[0].slot.width)
    assert seen >= 2, "the sweep produced no compressed level to read"


def test_the_entresol_is_a_ratio_of_the_shop_below_it() -> None:
    """A9.4, quantity 8 of the eleven: Daly's nine Deuxième Classe entresols
    give an entresol/ground ratio with median **0.775** (range 0.585-0.871).
    It is stated as a ratio and not as a height because that is the shape the
    evidence has — the nine heights span 2.40-3.12 m and the nine ground
    storeys under them 3.42-4.85 m, and the ratio is tighter than either.

    The product of an ABSOLUTE ground storey and a ratio is ABSOLUTE, so the
    compressed storey does not move with class any more than the shop under
    it does. Daly agrees: it is a Deuxième-only quantity precisely because
    the PRESENCE of the storey is the class marker, never its height.
    """
    assert structure._ENTRESOL_OVER_GROUND == pytest.approx(0.775)
    q = structure._entresol_height(3.95)
    assert q.kind is Kind.ABSOLUTE
    assert "SOURCED" in q.why and "Daly 1864" in q.why
    assert float(q) == pytest.approx(3.95 * 0.775)
    # And the ratio holds for whatever ground storey it is handed.
    assert float(structure._entresol_height(4.40)) == pytest.approx(4.40 * 0.775)


def test_the_comfortable_section_lands_inside_daly_s_deuxieme_distribution() -> None:
    """**A9.4, quantity 7 of the eleven.** Daly's Deuxième Classe is the only
    class whose storey-height distribution the corpus is strong enough to
    state — ten buildings, against four Première (three of them with
    source-flagged uncertain floor lines) and two Troisième. It reads:

        rez-de-chaussée   3.42-4.85 m   median 3.95
        entresol          2.40-3.12 m   median 2.98
        piano nobile      3.20-4.36 m   median 3.83
        étages above      2.32-3.83 m   median 3.07

    This typology's four classes straddle Daly's three, and COMFORTABLE is
    the one that sits where Deuxième does. So its whole section has to land
    inside those four bands — asserted as containment and not as equality,
    because the measurement pass marks the distribution usable and the
    individual values ±0.2-0.4 m.
    """
    from buildings.typologies.paris.roles import Role, assign_roles

    g = solve_structure(
        _site(street_width=30.0, parcel_width=16.0, parcel_depth=18.0, year=1865,
              klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP)
    )
    rg = assign_roles(g)
    by_role = {}
    for rs in rg.storeys:
        by_role.setdefault(rs.role, []).append(rs.slot.width)

    assert 3.42 <= by_role[Role.BASE][0] <= 4.85, by_role[Role.BASE]
    assert by_role.get(Role.MEZZANINE), "the Deuxième-shaped section lost its entresol"
    assert 2.40 <= by_role[Role.MEZZANINE][0] <= 3.12, by_role[Role.MEZZANINE]
    assert 3.20 <= by_role[Role.PRINCIPAL][0] <= 4.36, by_role[Role.PRINCIPAL]
    for h in by_role[Role.UPPER]:
        assert 2.32 <= h <= 3.83, (h, by_role[Role.UPPER])


def test_the_noble_floor_is_taller_the_grander_the_building_at_the_top_of_the_ladder() -> None:
    """**A9.4, quantity 5 — the ORDERING only, and only where the model has
    it.** Daly calls the piano nobile height "THE CLEAREST LADDER IN THE
    CORPUS": 4.23 / 3.83 / 3.04 m, monotonic, with a Première-to-Troisième gap
    (1.2 m) six times the duplicate-reading error.

    The model reproduces it over the top three classes and between the bottom
    and the top. It does NOT reproduce it between MODEST and ORDINARY, and
    that is a real defect rather than a tolerance: the facade ambition
    fraction steps up faster than the storey band does, so the extra budget
    buys ORDINARY a fourth letting storey instead of taller ones, and four
    storeys divided out of a bigger budget are shorter than three divided out
    of a smaller one. Asserting the part that holds — rather than the whole
    ladder — is what keeps this test honest about a known gap instead of
    quietly ratifying it; the gap is written up with the amendment.

    **A15.1**: on an ordinary 15 m plot, where this used to be measured on an
    18 m one. A plot deep enough to buy a second storey of garret is a
    building spending cornice height on rooms in the roof rather than on
    étages — a different question, with its own tests at the end of this file
    — and MODEST on that plot comes out with two equal letting storeys and no
    piano nobile at all, which is what Daly's Troisième Classe does too.
    """
    from buildings.typologies.paris.roles import Role, assign_roles

    nobile = {}
    for klass in BuildingClass:
        rg = assign_roles(
            solve_structure(
                _site(street_width=20.0, parcel_width=16.0, parcel_depth=15.0,
                      year=1865, klass=klass, ground=GroundProgramme.SHOP)
            )
        )
        principal = next((rs for rs in rg.storeys if rs.role is Role.PRINCIPAL), None)
        assert principal is not None, klass
        nobile[klass] = principal.slot.width

    assert nobile[BuildingClass.ORDINARY] < nobile[BuildingClass.COMFORTABLE]
    assert nobile[BuildingClass.COMFORTABLE] < nobile[BuildingClass.GRAND]
    assert nobile[BuildingClass.MODEST] < nobile[BuildingClass.GRAND]
    # Daly's own span at the noble floor, 3.04-4.23 m, as the band every
    # class has to sit inside even where the ladder between two of them is
    # not reproduced.
    for klass, h in nobile.items():
        assert 2.90 <= h <= 4.40, (klass, h)


def test_a_building_can_come_out_with_no_noble_floor_and_that_is_the_modest_one() -> None:
    """**A9.4's structural finding, reachable and reached.**

    Daly's two Troisième Classe buildings have no compressed level and no
    piano nobile: their étages are equal within 0.07 m. "Has a principal
    floor" is therefore a fact about the section, and the roles phase says so
    with one word — the principal is the *uniquely* tallest habitable slot —
    rather than with a class branch.

    Swept over 480 situations the branch fires on 42 of them, and 30 of those
    42 are MODEST: the noble floor disappears at the bottom of the ladder,
    which is where Daly finds it missing. The mechanism is the taper meeting
    the storey band's own maximum — when the lower étages all come to rest on
    the same ceiling, no floor stands out — and nothing anywhere reads the
    class to produce it.
    """
    from buildings.typologies.paris.roles import Role, assign_roles

    without = {}
    total = 0
    for street in (6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0):
        for parcel in (10.0, 14.0, 18.0):
            for klass in BuildingClass:
                for ground in GroundProgramme:
                    rg = assign_roles(
                        solve_structure(
                            _site(street_width=street, parcel_width=parcel,
                                  parcel_depth=18.0, year=1865, klass=klass,
                                  ground=ground)
                        )
                    )
                    total += 1
                    if any(rs.role is Role.PRINCIPAL for rs in rg.storeys):
                        continue
                    without[klass] = without.get(klass, 0) + 1
                    # No role is missing downstream: rank still descends from
                    # the first letting floor, so ornament and opening shape
                    # keep working with no test for an absent principal.
                    ranks = sorted(
                        rs.rank_from_principal
                        for rs in rg.storeys
                        if rs.role in (Role.UPPER, Role.ATTIC)
                    )
                    assert ranks[0] == 0, ranks

    assert without, "the no-noble-floor section is unreachable"
    # It disappears at the BOTTOM of the ladder, and the whole ladder says so:
    # the count falls, strictly at the top and never rising, as the class does.
    # A15.1 is why this is asserted as an ordering rather than as "more MODEST
    # than every other class put together": on a run that gave a storey of
    # cornice height to a second storey of chambres de bonne, ORDINARY's
    # remaining budget lands on equal étages too, by exactly the mechanism
    # this test names — the taper meeting the storey band's own maximum. The
    # ladder is the claim; the arithmetic margin was a consequence of it.
    ladder = [
        without.get(k, 0)
        for k in (
            BuildingClass.MODEST,
            BuildingClass.ORDINARY,
            BuildingClass.COMFORTABLE,
            BuildingClass.GRAND,
        )
    ]
    assert ladder == sorted(ladder, reverse=True), (
        f"the noble floor is not disappearing at the bottom of the ladder: {without}"
    )
    assert ladder[0] > ladder[-1], without
    assert ladder[0] == max(ladder), without
    # A minority of buildings, not a majority — Daly's own 2 of 16.
    assert sum(without.values()) < total * 0.25, (sum(without.values()), total)


# ===========================================================================
# A15.1 / A15.2 — how many storeys of chambres de bonne the roof holds
# ===========================================================================
#
# Measured over 180 sites, the 1865 comble was 3.20 m for every street width,
# parcel width, parcel depth, class and ground programme in the sweep: one
# value, because the 45° gabarit's own comble allowance stands exactly one
# band of garret and the storey count was read off that allowance. Daly's nine
# 1864 commercial buildings run 2.69-7.00 m in the same era, and the
# measurement pass says why in as many words — the corpus mixes plain mansards
# with combles holding two full storeys.
#
# The storey count is now a decision. What these assert is that BOTH MODES
# OCCUR, that the second one is bought out of the cornice rather than granted,
# and that nothing about the decision reads the class. **The RATE is INFERRED
# and is deliberately not asserted anywhere** (A15.2): Daly's 3-of-9 comes
# from a quantity his own measurement pass marks INSUFFICIENT, out of a
# corpus with a known publication bias.


def _trade_site(**overrides):
    # A boulevard over 20 m: the 1859 tables' top step, and the only one whose
    # legal cornice still stands a trade floor, an entresol and three letting
    # storeys after a band of it has gone to the garret.
    defaults = dict(
        street_width=30.0, parcel_width=14.0, parcel_depth=18.0, year=1865,
        klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
    )
    defaults.update(overrides)
    return _site(**defaults)


def test_the_45_degree_comble_is_no_longer_one_number() -> None:
    """The defect A15.1 names, asserted as a population fact.

    Swept across the same axes that produced the constant — street, parcel
    width, parcel depth, class and ground programme — the 1865 comble must
    reach both modes and span a real range. The numbers are not pinned: what
    is contractual is that a single value is gone and that the spread is of
    the order Daly measured (2.69-7.00 m, a factor of 2.6), not of the order
    float noise is.
    """
    heights = set()
    for street in (6.0, 9.75, 15.0, 20.0, 30.0, 40.0):
        for depth in (8.0, 11.0, 14.0, 22.0):
            for klass in BuildingClass:
                for ground in GroundProgramme:
                    g = solve_structure(
                        _site(street_width=street, parcel_width=12.0,
                              parcel_depth=depth, year=1865, klass=klass,
                              ground=ground)
                    )
                    heights.add(round(g.comble_height, 6))
    assert len(heights) > 1, f"the 1865 comble is still one number: {heights}"
    lo, hi = min(heights), max(heights)
    assert hi / lo > 1.5, (
        f"the 1865 comble runs {lo:.2f}-{hi:.2f} m, a factor of {hi / lo:.2f}; "
        "Daly's nine buildings of the same era run 2.69-7.00 m, a factor of 2.6, "
        "and two of the four commercial varieties are unreachable without a "
        "spread of that order (A15.1)"
    )
    band = float(structure.BRISIS_RISE)
    assert any(h < 2.0 * band for h in heights), "no one-storey garret in the sweep"
    assert any(h > 2.0 * band for h in heights), "no two-storey garret in the sweep"


def test_the_second_storey_of_garret_is_bought_out_of_the_cornice() -> None:
    """A15.1's mechanism: the legal solid does not move, so the roof takes its
    extra band of rooms out of the stone under it.

    Two buildings identical but for the ground programme. The one that puts a
    second storey of *chambres de bonne* in its roof fills a legal ceiling one
    whole ``BRISIS_RISE`` lower, and neither of them reaches the gabarit's own
    top — which is A8.5 still holding.
    """
    band = float(structure.BRISIS_RISE)
    bought = solve_structure(_trade_site())
    plain = solve_structure(_trade_site(ground=GroundProgramme.RESIDENTIAL))
    assert bought.extra_garret_storeys == 1
    assert plain.extra_garret_storeys == 0
    assert len(bought.comble_storeys) == 2
    assert len(plain.comble_storeys) == 1
    assert bought.envelope.facade_height == plain.envelope.facade_height
    # The roof grew by a whole room and by nothing else.
    assert bought.comble_height - plain.comble_height == pytest.approx(band, abs=0.2)
    env = bought.envelope
    for g in (bought, plain):
        assert g.eaves_height + g.comble_height < env.total_height - 1e-6, (
            "the building reached its legal total — A8.5"
        )
    # And the stone paid for it: the ceiling the fill was held under is one
    # band lower, and it shows in the account rather than only in the numbers.
    assert any("buys the second out of the cornice" in line for line in bought.account)
    assert bought.eaves_height < plain.eaves_height
    # The other half of A9.4's "the regulation is visible in the data": a run
    # that bought a storey of garret queues against a line one chambre de bonne
    # below the decree's own, and the two upper classes come to rest on THAT
    # line exactly as they come to rest on the 20 m one when they have not
    # traded. Daly: 19.0-20.0 m for his plain mansards, 17.52 and 17.55 m for
    # his two two-storey garrets — 2.5 m apart, one storey of stone.
    lowered = float(bought.cornice_height) - band
    for klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
        g = solve_structure(_trade_site(klass=klass))
        assert g.extra_garret_storeys == 1
        assert lowered - 1.5 <= g.eaves_height <= lowered + 1e-9, (klass, g.eaves_height)


def test_a_shallow_parcel_will_not_build_the_second_storey_of_garret() -> None:
    """A15.1 by name: *on a shallow parcel the 45° diagonals meet before the
    second storey fits, and it must not be built.*

    Derived rather than declared, and asserted where it belongs. What the
    depth changes is the SECTION: deep lots build the two storeys of chambres
    de bonne their cornice paid for, shallow ones build one and never a bare
    band with nothing behind it. Monotone in the depth, and both answers
    occur.

    **A16.1 changed the other half of this.** It used to assert
    ``{extra_garret_storeys} == {1}`` for every depth in the sweep — one
    decision for the whole run, the cornice being a block fact — which is
    exactly how a 10 m lot came to pay for a band it was then refused. The
    depth now gates the purchase as well as the section, so what is asserted
    here is the section's own behaviour and
    ``test_the_facade_never_pays_for_a_garret_band_the_parcel_refuses``
    asserts the reconciliation.
    """
    built = {
        d: solve_structure(_trade_site(parcel_depth=d))
        for d in (6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0, 30.0)
    }
    rooms = [len(built[d].comble_storeys) for d in sorted(built)]
    assert rooms == sorted(rooms), rooms
    assert set(rooms) == {0, 1, 2}, rooms
    combles = [round(built[d].comble_height, 6) for d in sorted(built)]
    assert combles == sorted(combles), combles
    assert combles[-1] > combles[0] + 1.0, combles
    # The shallow lot's roof stops where the two slopes meet, not where a
    # cornice somewhere else paid for it to stop.
    shallow = built[8.0]
    assert len(shallow.comble_storeys) < 2
    assert shallow.comble_height <= shallow.envelope.max_height_for_setback(4.0) + 1e-9


# ===========================================================================
# A16 — the garret trade is mispriced and unconditional
# ===========================================================================


def test_the_facade_never_pays_for_a_garret_band_the_parcel_refuses() -> None:
    """**A16.1**, and it is the whole of it: a band bought is a band built.

    The fault, measured before the fix: on a 10 m or 12 m parcel a shop under
    a 20.00 m ceiling gave up a band of cornice height and received exactly
    ONE storey of garret — the storey a residential building on the same lot
    gets for nothing — so the facade came out at 15.99 m (80 %) against the
    residential 19.20 m (96 %) with the same roof.

    Two functions held independent opinions about one fact. The assertion is
    therefore about the two agreeing, over a sweep that crosses the depth at
    which the second band gets its floor (about 12.20 m at 1865), and it is
    stated as an implication rather than as a pair of numbers: **if the
    cornice was lowered, the rooms are there**.
    """
    seen_bought = seen_refused = 0
    for depth in (6.0, 8.0, 10.0, 11.0, 12.0, 12.5, 13.0, 14.0, 16.0, 20.0, 30.0):
        for klass in BuildingClass:
            g = solve_structure(_trade_site(parcel_depth=depth, klass=klass))
            plain = solve_structure(
                _trade_site(parcel_depth=depth, klass=klass,
                            ground=GroundProgramme.RESIDENTIAL)
            )
            if g.extra_garret_storeys:
                seen_bought += 1
                # Paid for, and received: the rooms the cornice bought exist.
                assert len(g.comble_storeys) >= 1 + g.extra_garret_storeys, (
                    depth, klass, len(g.comble_storeys)
                )
                assert len(g.comble_storeys) > len(plain.comble_storeys), (depth, klass)
                assert g.eaves_height < plain.eaves_height
            else:
                seen_refused += 1
                # Nothing was given up, so the facade keeps the whole ceiling
                # its ambition asks for — the shallow lot is not punished for
                # a trade it was never offered.
                assert g.eaves_height == pytest.approx(plain.eaves_height, abs=0.75), (
                    depth, klass, g.eaves_height, plain.eaves_height
                )
    assert seen_bought and seen_refused, (seen_bought, seen_refused)


def test_the_buyer_and_the_holder_are_one_function() -> None:
    """A16.1 structurally, not just by outcome. The purchase reads the parcel
    through the same function the section clamps against, so the two cannot
    drift apart again — which is what the previous five instances of this
    fault (A4.1, A6.8, A7.3, A9.3, A10.4) all needed and none of them got
    from an adjusted number."""
    from buildings.typologies.paris.reglement import compute_envelope, era_for_year

    params = inspect.signature(
        structure._a_second_storey_of_chambres_de_bonne
    ).parameters
    assert "parcel_depth" in params, "the buyer cannot ask what it cannot see"

    for depth in (6.0, 9.0, 12.0, 12.5, 18.0, 30.0):
        env = compute_envelope(30.0, era_for_year(1865), depth)
        holds = structure._extra_garret_storeys_the_parcel_holds(env, depth)
        bought, _why = structure._a_second_storey_of_chambres_de_bonne(
            env, GroundProgramme.SHOP, 20.0, depth
        )
        assert bought <= holds, (depth, bought, holds)
        # And the section, handed a number of its own, clamps to the same one.
        brisis, _ridge, _inset = structure._comble_section(env, 17.10, depth, 4)
        band = float(structure.BRISIS_RISE)
        stands = structure._garret_storeys_the_decree_stands(env, depth)
        assert brisis <= (stands + holds) * band + 1e-9, (depth, brisis)


def test_a_band_of_garret_costs_the_facade_one_band_and_nothing_more() -> None:
    """**A16.2.** The band is priced at what it is.

    Before the fix the observed drop was 4.01 m of a 20.00 m ceiling — a
    whole étage plus half of another, and two étages out of the stack. Daly's
    two two-storey garrets sit at cornices of 17.52 and 17.55 m under the
    same decree, about 2.5 m below their short-comble neighbours at
    19.5-20.0 m: one storey of stone, not two.

    Asserted as the relation and not as a figure: the deduction is
    ``_facade_given_up_for_a_bought_garret``, which is one ``BRISIS_RISE``
    per band and is composed of the room and its plate rather than restated;
    the traded facade queues against the ceiling one band lower exactly as an
    untraded one queues against its own; and the stack loses ONE étage.
    """
    band = float(structure.BRISIS_RISE)
    assert structure._facade_given_up_for_a_bought_garret(1) == pytest.approx(band)
    assert structure._facade_given_up_for_a_bought_garret(2) == pytest.approx(2 * band)
    assert structure._facade_given_up_for_a_bought_garret(0) == 0.0

    for klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
        bought = solve_structure(_trade_site(klass=klass, parcel_depth=18.0))
        plain = solve_structure(_trade_site(klass=klass, parcel_depth=11.0))
        assert bought.extra_garret_storeys == 1
        assert plain.extra_garret_storeys == 0
        assert float(bought.cornice_height) == float(plain.cornice_height)
        fraction = structure._FACADE_AMBITION[klass]
        # The ceiling came down by one band; the ambition is a fraction of the
        # ceiling this building is allowed, so the facade comes down by that
        # fraction of a band — one storey of stone, never two.
        given_up = plain.eaves_height - bought.eaves_height
        assert given_up == pytest.approx(fraction * band, abs=0.05), (klass, given_up)
        assert given_up < float(structure._PLAIN_STOREY_HEIGHT) + 0.30, (klass, given_up)
        # One étage, not two.
        etages = lambda g: len(  # noqa: E731
            [s for s in g.storeys if s.name not in ("ground", "entresol", "comble")]
        )
        assert etages(plain) - etages(bought) == 1, (klass, etages(plain), etages(bought))
        # And the trade is visible where Daly sees it: in the roof.
        assert len(bought.comble_storeys) == len(plain.comble_storeys) + 1


def test_the_facade_fills_the_budget_it_was_granted() -> None:
    """**A16.2**, the other half of the 4.01 m: 0.41 m of it was height the
    facade was granted, reserved for an entresol the section then held down,
    and given to nobody.

    A9.4's relation stands — the compressed storey is shorter than the floor
    it serves, by Daly's measured ratio — but it is settled WITH the storeys
    it serves rather than applied to them afterwards, so the height it gives
    up stands in those storeys and the stone face reaches the height it was
    granted. The two facts A9.4 asserts are re-asserted here over the same
    sweep, because neither may be lost to the settlement.
    """
    for year in (1800, 1875, 1905):
        for klass in BuildingClass:
            for street in (12.0, 18.0, 30.0):
                g = solve_structure(
                    _site(street_width=street, parcel_width=13.0, year=year,
                          klass=klass, ground=GroundProgramme.SHOP)
                )
                entresol = next((s for s in g.storeys if s.name == "entresol"), None)
                if entresol is None:
                    continue
                over = [
                    s.width for s in g.storeys
                    if s.name not in ("ground", "entresol", "comble")
                ]
                # A9.4: shorter than the floor it serves, by Daly's ratio...
                assert entresol.width <= max(over) / 1.275 + 1e-9, (year, klass, street)
                # ...and inside Daly's measured entresol/ground band.
                assert entresol.width / g.storeys[0].width <= 0.871 + 1e-9
                # A16.2: and nothing vanished. The stone face stops exactly
                # where the height a whole-storey stack can fill puts it.
                assert g.eaves_height == pytest.approx(
                    math.fsum(s.width for s in g.storeys if s.name != "comble"),
                    abs=1e-9,
                )
                assert any(
                    line.startswith("facade target ")
                    and f"rounded to {g.eaves_height:.2f} m" in line
                    for line in g.account
                ), (year, klass, street, g.eaves_height)


def test_the_canonical_second_empire_stack_is_reachable() -> None:
    """**A16.3.** The operator's statement of the standard, which is exactly
    Daly's five canonical buildings:

        RdC · entresol · 1er (balcon filant) · 2e · 3e · 4e (balcon filant) ·
        comble, with the cornice in the 19-20 m band.

    Daly: 63 bd de Sébastopol 19.72, 77 bd de Sébastopol 19.48, 120 bd de
    Sébastopol 19.98, 39 rue Neuve des Mathurins 19.82, 6 bd Saint-Germain
    19.05 — 4 of the 9 commercial buildings and 11 of the 16 overall, the
    commonest real configuration in the corpus. Before A16 the generator
    returned three étages at 15.99 m and could not reach it at all.

    The parcel is part of the situation and not a detail: a lot deep enough
    to hold a second band of garret is offered the trade and takes it (that
    is C1, and Daly's 2-4 bd de Sébastopol), so the maximal stack is the
    shallower lot, where the height has nowhere to go but the stone.
    """
    site = _site(
        street_width=22.0, parcel_width=14.0, parcel_depth=11.0, year=1865,
        klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
    )
    g = solve_structure(site)
    names = [s.name for s in g.storeys]
    assert names == ["ground", "entresol", "storey", "storey", "storey", "storey",
                     "comble"], names
    assert float(g.cornice_height) == pytest.approx(20.0, abs=1e-9)
    assert 19.05 <= g.eaves_height <= 19.98, g.eaves_height
    assert g.eaves_height / float(g.cornice_height) >= 0.95
    # The five buildings carry one row of lucarnes over one storey of garret:
    # this is the stack that keeps its height in the stone.
    assert g.extra_garret_storeys == 0
    assert len(g.comble_storeys) == 1


def test_the_canonical_stack_hangs_its_filants_on_the_1er_and_the_4e() -> None:
    """A16.3's stack is a stack of ROLES, and the balcony rule — *the noble
    floor and the top of the wall* — is correct and untouched. What was wrong
    was the stack under it: with three étages the upper filant landed on the
    3e. With four it lands on the 4e, which is what Daly's five buildings
    show and what the operator's statement of the standard says.
    """
    from buildings.typologies.paris.generate import generate, walk
    from buildings.typologies.paris.roles import assign_roles

    site = _site(
        street_width=22.0, parcel_width=14.0, parcel_depth=11.0, year=1865,
        klass=BuildingClass.COMFORTABLE, ground=GroundProgramme.SHOP,
    )
    grid = solve_structure(site)
    graded = assign_roles(grid)
    roles = [s.role.value for s in graded.storeys]
    assert roles == ["base", "mezzanine", "principal", "upper", "upper", "upper",
                     "attic"], roles

    building, _log = generate(site)
    filants = sorted(
        {
            round(float(n.props["y"]), 6)
            for n in walk(building)
            if n.kind == "balcony" and bool(n.props.get("continuous"))
        }
    )
    assert len(filants) == 2, filants
    floors = [round(s.slot.start, 6) for s in graded.storeys]
    # The noble floor — the 1er, over the entresol — and the top of the wall,
    # which in a four-étage stack is the 4e and not the 3e.
    assert filants[0] == pytest.approx(floors[2], abs=1e-6), (filants, floors)
    assert filants[1] == pytest.approx(floors[5], abs=1e-6), (filants, floors)


def test_the_garret_storey_count_never_reads_the_class() -> None:
    """A9.1's retraction, which A15.2 leaves standing: comble share is not a
    function of class. So the decision takes no class argument and produces
    the same roof for all four classes on one situation — the money is in the
    stone underneath, which is where the brief puts it."""
    for fn in (
        structure._a_second_storey_of_chambres_de_bonne,
        structure._garret_storeys_the_parcel_holds,
        structure._garret_storeys_the_decree_stands,
        structure._the_decrees_own_comble_allowance,
    ):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"klass", "class_", "building_class"}, fn.__name__
    grids = [solve_structure(_trade_site(klass=k)) for k in BuildingClass]
    assert len({g.extra_garret_storeys for g in grids}) == 1
    assert len({round(g.comble_height, 9) for g in grids}) == 1
    assert len({len(g.comble_storeys) for g in grids}) == 1
    tops = [g.built_height + g.comble_height for g in grids]
    assert tops == sorted(tops), tops


def test_every_band_of_brisis_with_a_room_behind_it_gets_a_storey() -> None:
    """The comble is *chambres de bonne*, so the rooms and the roof are one
    arithmetic: a section standing N whole bands of brisis holds N storeys
    wherever the plot has a room's depth of floor behind each of them, and the
    stack stays contiguous through the eaves line like any other run of
    storeys."""
    seen_two = 0
    for year in (1865, 1890, 1905):
        for depth in (8.0, 14.0, 22.0):
            g = solve_structure(_trade_site(year=year, parcel_depth=depth))
            combles = g.comble_storeys
            if not combles:
                continue
            band = float(structure.BRISIS_RISE)
            bands = max(1, int(g.brisis_height / band + 1e-9))
            assert len(combles) <= bands, (year, depth, len(combles), bands)
            if len(combles) >= 2:
                seen_two += 1
            cursor = g.eaves_height
            for slot in combles:
                assert slot.start == pytest.approx(cursor, abs=1e-9)
                cursor += slot.width
                assert slot.width >= float(structure._HUMAN_MIN_STOREY_HEIGHT) - 1e-9
    assert seen_two > 0, "no situation in the sweep held two storeys of garret"
