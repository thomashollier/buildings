"""Invariant sweep for the structure phase (S3 / Gate G3).

Two things earn a sweep rather than a handful of point tests:

- **The envelope is a step function of street width**, because the
  regulation is a step table (``Reglement.height_steps``). A continuous ramp
  anywhere in the sweep means the regulatory arithmetic leaked a smooth
  interpolation somewhere it should not have one.
- **Every structural invariant** (exact fill, ceiling >= built, no role
  vocabulary, determinism) should hold at *every* point in a wide situation
  space, not just the handful of examples the unit tests happen to construct.

No RNG axis: ``solve_structure`` samples nothing (I2/I5) — seed is not even
a parameter — so there is nothing to vary except the situation itself.
"""

from __future__ import annotations

import re

import pytest

from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import FitInfeasible
from buildings.typologies.paris.reglement import era_for_year, get_reglement
from buildings.typologies.paris.structure import solve_structure

_ROLE_WORDS = re.compile(r"\b(base|mezzanine|principal|noble|upper|attic)\b", re.IGNORECASE)

_YEARS = (1800, 1830, 1859, 1860, 1883, 1884, 1888, 1901, 1902, 1910)
_CLASSES = tuple(BuildingClass)
_GROUNDS = tuple(GroundProgramme)

# Widths and parcels realistic enough that every declared vocabulary can
# make them (see test_structure.py for the narrow/grand and
# narrow/carriage combinations that are genuinely, honestly infeasible —
# those are excluded here, not swept past).
_STREET_WIDTHS = [round(6.0 + 0.4 * i, 2) for i in range(86)]  # 6.0 .. 40.0
_PARCEL_WIDTHS = (6.0, 8.0, 10.0, 14.0, 20.0, 28.0)


def _site(street, parcel, year, klass, ground) -> SiteContext:
    return SiteContext(
        street_width=street,
        parcel_width=parcel,
        parcel_depth=14.0,
        year=year,
        klass=klass,
        ground=ground,
    )


def test_cornice_height_is_a_step_function_of_street_width() -> None:
    """For every era, sweeping street width at fine resolution produces only
    the plateaus in that era's ``height_steps`` table — never a value in
    between two of them."""
    for year in _YEARS:
        reg = get_reglement(era_for_year(year))
        legal_plateaus = {round(h, 6) for _, h in reg.height_steps}

        seen = set()
        for width in _STREET_WIDTHS:
            g = solve_structure(_site(width, 14.0, year, BuildingClass.ORDINARY, GroundProgramme.RESIDENTIAL))
            seen.add(round(g.cornice_height.value, 6))

        assert seen <= legal_plateaus, (year, seen - legal_plateaus)


def test_cornice_height_never_decreases_with_wider_streets() -> None:
    for year in _YEARS:
        prev = 0.0
        for width in _STREET_WIDTHS:
            g = solve_structure(_site(width, 14.0, year, BuildingClass.ORDINARY, GroundProgramme.RESIDENTIAL))
            assert g.cornice_height.value >= prev - 1e-9
            prev = g.cornice_height.value


def test_structural_invariants_hold_across_the_situation_space() -> None:
    n = 0
    for year in _YEARS:
        for klass in _CLASSES:
            for ground in _GROUNDS:
                for parcel in _PARCEL_WIDTHS:
                    if ground is GroundProgramme.CARRIAGE and parcel < 8.0:
                        continue  # honestly infeasible: no room for a carriage door
                    if klass is BuildingClass.GRAND and parcel < 6.0:
                        continue  # honestly infeasible: not even one grand bay fits
                    for street in (7.0, 12.0, 20.0, 32.0):
                        n += 1
                        site = _site(street, parcel, year, klass, ground)
                        g = solve_structure(site)

                        # exact fill, both axes. Vertically the budget is the
                        # facade: a storey standing inside the comble (A2.1)
                        # stands ON the eaves and is not part of what filled
                        # them, so the sum that must match ``built_height`` is
                        # the storeys below the roof.
                        assert sum(s.width for s in g.bays) == pytest.approx(parcel, abs=1e-9)
                        facade = [
                            s for i, s in enumerate(g.storeys) if not g.stands_in_the_roof(i)
                        ]
                        assert sum(s.width for s in facade) == pytest.approx(
                            g.built_height, abs=1e-9
                        )
                        assert g.built_height == pytest.approx(g.eaves_height, abs=1e-9)
                        # every slot is on exactly one side of the eaves line,
                        # and the stack is contiguous across it
                        assert sum(s.width for s in g.storeys) == pytest.approx(
                            g.storeys[-1].start + g.storeys[-1].width, abs=1e-9
                        )

                        # ceiling vs built
                        assert g.built_height <= g.cornice_height.value + 1e-6

                        # no role vocabulary anywhere in the output
                        for slot in (*g.storeys, *g.bays):
                            assert not _ROLE_WORDS.search(slot.name)
                        for line in g.account:
                            assert not _ROLE_WORDS.search(line)

                        # determinism
                        g2 = solve_structure(site)
                        assert g2 == g
    assert n > 100  # the sweep actually ran, not vacuously skipped everything


def test_built_height_is_below_ceiling_for_modest_and_near_it_for_grand() -> None:
    for street in (20.0, 25.0, 32.0):
        for year in (1870, 1888, 1905):
            modest = solve_structure(_site(street, 14.0, year, BuildingClass.MODEST, GroundProgramme.RESIDENTIAL))
            grand = solve_structure(_site(street, 14.0, year, BuildingClass.GRAND, GroundProgramme.RESIDENTIAL))
            assert modest.built_height < modest.cornice_height.value
            assert grand.built_height <= grand.cornice_height.value + 1e-6
            assert modest.built_height < grand.built_height


def test_datums_are_honoured_exactly_across_a_sweep() -> None:
    import types

    for cornice in (11.70, 14.62, 17.55, 18.0, 20.0, 28.5):
        datums = types.SimpleNamespace(
            street_width=20.0, cornice_height=cornice, string_course_levels=(), balcony_levels=()
        )
        # The site and the datum must agree about the street (A4.8); what is
        # under test is the *cornice*, which the block may legitimately hold
        # at a neighbour's line rather than at the règlement's ceiling.
        site = _site(20.0, 14.0, 1888, BuildingClass.ORDINARY, GroundProgramme.RESIDENTIAL)
        g = solve_structure(site, datums=datums)
        assert g.cornice_height.value == cornice
        assert g.envelope.facade_height == cornice
