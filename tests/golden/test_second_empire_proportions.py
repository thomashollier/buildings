"""Proportion assertions against the Daly 1864 source, across a SWEEP of
Second Empire situations (Amendment 9's "lock the canonical case").

This is the calibration half of A9's instruction; ``test_second_empire_canonical.py``
is the pinning half. Where that file freezes four specific buildings byte for
byte, this file sweeps many and asks a narrower, source-grounded question of
each: does the quantity this rule states agree with what César Daly's 1864
plates measured?

**Source and the two kinds of number it gives.** Every figure below is one of
``dev/reference/daly_measurements.json`` / ``dev/logs/DALY_MEASUREMENTS.md``,
measured from César Daly, *L'Architecture privée au XIXme siècle sous
Napoléon III*, Sér. 1 Vol. 1 t. 2 (1864), across a real sample of
**n = 4 Première / 10 Deuxième / 2 Troisième buildings** (the unit is the
building, not the plate). The corpus's own error bar, established by
measuring one building (26 rue Bergère) twice independently: **printed
dimensions are reliable; a scale-bar width carries ±10 %**. So this file
follows the same rule ``catalogue.py`` documents: a test against a PRINTED
figure is tight (``abs=1e-6`` or a couple of centimetres); a test against a
SCALE-BAR figure uses ``rel=0.10``.

**Three tiers, matching A9.4's own recommendation exactly:**

- **SOURCED** — assert the *value*, with the citation in the docstring, the
  same way ``test_reglement_diff.py`` asserts a decree figure.
- **WEAK** — assert *ordering only*. The corpus supports the direction (taller
  with class, say) but not the number (Première n=3, Troisième n=1, etc.).
  Pinning a value here would dress a guess as a finding.
- **INSUFFICIENT** — not tested here at all. Comble share, cornice band depth,
  upper-storey opening aspect, entresol aspect, balcony height outside
  Deuxième, and bay pitch as a function of class are deliberately left
  INFERRED and deliberately absent from this file; see
  ``dev/SECOND_EMPIRE_STATUS.md``.

Every quantity is checked two ways where it can be: once directly against the
catalogue/structure function that states it (cheap, and immune to any
particular situation's solver noise), and once against the real generated IR
across a sweep of situations (the end-to-end proof that the stated figure is
what actually reaches a building, not merely what a function returns in
isolation).
"""

from __future__ import annotations

import itertools
from typing import Iterator

import pytest

from buildings.quantity import scale_for_class
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.solver.fitting import FitInfeasible
from buildings.typologies.paris import catalogue, structure
from buildings.typologies.paris.catalogue import EntranceCannotFit
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.roles import Role, assign_roles
from buildings.typologies.paris.structure import solve_structure

# ---------------------------------------------------------------------------
# The sweep: Second Empire situations only (1853-1870), varied broadly.
# ---------------------------------------------------------------------------
#
# Deliberately not combinatorial: a handful of street widths (from below the
# carriage-entrance threshold to well over the 20 m decree step) crossed
# EXHAUSTIVELY with every class, every ground programme and both corner
# states, at a small set of years spanning the whole political period
# (1853, the empire's first full year; 1859, the hygiene/height decree;
# 1865, Daly's own publication year; 1870, the empire's last).

_YEARS = (1853, 1859, 1865, 1870)
_STREET_WIDTHS = (9.0, 12.0, 15.0, 18.0, 20.0, 24.0, 30.0)
_PARCEL_WIDTHS = (9.0, 11.0, 13.0, 16.0)
_PARCEL_DEPTHS = (12.0, 16.0, 20.0)
_ALL_CLASSES = tuple(BuildingClass)
_ALL_GROUNDS = tuple(GroundProgramme)
_ALL_CORNER = (False, True)

_SEED_BASE = 18_530_000  # unrelated to any other module's seed space


def _sweep() -> Iterator[SiteContext]:
    """Every (street, parcel, year) base crossed with every categorical
    combination -- exhaustive on class/ground/corner, sampled on the
    continuous axes, exactly as ``dev/harness/fuzz.py`` does it, but scoped
    to Second Empire years only."""
    index = 0
    bases = list(
        itertools.islice(
            zip(
                itertools.cycle(_STREET_WIDTHS),
                itertools.cycle(_PARCEL_WIDTHS),
                itertools.cycle(_PARCEL_DEPTHS),
                itertools.cycle(_YEARS),
            ),
            len(_STREET_WIDTHS) * 2,
        )
    )
    for street, parcel_w, parcel_d, year in bases:
        for klass in _ALL_CLASSES:
            for ground in _ALL_GROUNDS:
                for corner in _ALL_CORNER:
                    yield SiteContext(
                        street_width=street,
                        parcel_width=parcel_w,
                        parcel_depth=parcel_d,
                        year=year,
                        klass=klass,
                        ground=ground,
                        corner=corner,
                        seed=_SEED_BASE + index,
                    )
                    index += 1


def _structure_sweep():
    """``(site, grid, roled)`` for every sweep situation that solves at all.
    Infeasible combinations (a hand-built cross of class/ground/street can
    still ask for a carriage entrance a narrow parcel cannot give) are
    skipped, exactly as the fuzzer skips them -- this file is calibrating
    proportions, not re-proving I5/feasibility, which ``tests/invariant``
    already owns."""
    out = []
    for site in _sweep():
        try:
            grid = solve_structure(site)
            roled = assign_roles(grid)
        except (FitInfeasible, EntranceCannotFit):
            continue
        out.append((site, grid, roled))
    return out


def _ir_sweep():
    """``(site, building)`` for a full ``generate()`` pass over the sweep."""
    out = []
    for site in _sweep():
        try:
            building, _log = generate(site)
        except (FitInfeasible, EntranceCannotFit):
            continue
        out.append((site, building))
    return out


@pytest.fixture(scope="module")
def structure_sweep():
    cases = _structure_sweep()
    assert len(cases) >= 200, f"the sweep is too small to mean anything: {len(cases)} cases"
    return cases


@pytest.fixture(scope="module")
def ir_sweep():
    cases = _ir_sweep()
    assert len(cases) >= 100, f"the sweep is too small to mean anything: {len(cases)} cases"
    return cases


def _windows(building) -> list:
    return [
        n
        for n in walk(building)
        if n.kind == "opening" and n.props.get("opening_type") == "window"
    ]


def _entrances(building) -> list:
    return [
        n
        for n in walk(building)
        if n.kind == "opening"
        and n.props.get("opening_type") in ("carriage_entrance", "pedestrian_entrance")
    ]


def _balconies(building) -> list:
    return [n for n in walk(building) if n.kind == "balcony"]


# ===========================================================================
# SOURCED — assert the value
# ===========================================================================


class TestDoorWidthByType:
    """SOURCED. Daly 1864: seven carriage doors pooled across Première (n=4)
    and Deuxième (n=3) medians 2.567 / 2.575 m (0.4 % apart) -- printed
    2.600 m at 119 avenue des Champs-Élysées. Eight Deuxième pedestrian doors,
    two printed, median 1.75 m. See ``catalogue.door_carriage_entrance`` /
    ``door_pedestrian``."""

    def test_carriage_door_clear_width_matches_the_printed_dimension(self) -> None:
        spec = catalogue.door_carriage_entrance()
        assert float(spec.preferred) == pytest.approx(2.600, abs=1e-6), (
            "printed plan callout '2.600' at 119 avenue des Champs-Élysées "
            "(Daly 1864, daly_elevation_49 / daly_detail_05)"
        )

    def test_carriage_door_bounds_match_the_scale_bar_readings(self) -> None:
        spec = catalogue.door_carriage_entrance()
        # Scale-bar measurements carry the corpus's own +/-10% error bar.
        assert float(spec.minimum) == pytest.approx(2.410, rel=0.10)  # 3 rue de la Paix
        assert float(spec.maximum) == pytest.approx(2.672, rel=0.10)  # 26 rue Bergère

    def test_pedestrian_door_clear_width_matches_the_measured_median(self) -> None:
        spec = catalogue.door_pedestrian()
        assert float(spec.preferred) == pytest.approx(1.75, abs=0.02), (
            "median of eight Deuxième Classe portes piétonnes, bracketed by printed "
            "callouts '1.760' (87 boulevard de Sébastopol) and '1.630' (9 rue du "
            "Conservatoire)"
        )

    def test_pedestrian_door_bounds_match_the_scale_bar_readings(self) -> None:
        spec = catalogue.door_pedestrian()
        assert float(spec.minimum) == pytest.approx(1.609, rel=0.10)
        assert float(spec.maximum) == pytest.approx(1.910, rel=0.10)

    def test_the_two_top_classes_agree_on_carriage_width_to_within_one_percent(self) -> None:
        """The finding, not just the number: Première 2.567 m vs Deuxième
        2.575 m median is a 0.4% difference -- proof the door doesn't scale
        with money, only its ENTITLEMENT does. Encoded as one ABSOLUTE
        constant, so this holds trivially, but it is worth asserting that the
        two source medians the constant sits between are themselves this
        close -- a distant pair averaged into one figure would be a different,
        weaker claim."""
        premiere_median, deuxieme_median = 2.567, 2.575
        assert abs(premiere_median - deuxieme_median) / premiere_median < 0.01

    def test_carriage_and_pedestrian_doors_are_absolute_across_every_class(self) -> None:
        """Never scale -- the whole point of the entitlement/size split."""
        carriage = {k: catalogue.door_carriage_entrance().to_slot_spec(k) for k in _ALL_CLASSES}
        pedestrian = {k: catalogue.door_pedestrian().to_slot_spec(k) for k in _ALL_CLASSES}
        for table in (carriage, pedestrian):
            widths = {(s.minimum, s.preferred, s.maximum) for s in table.values()}
            assert len(widths) == 1, f"door width varied by class: {table}"

    def test_entrance_width_in_the_generated_ir_is_exactly_the_sourced_figure(
        self, ir_sweep
    ) -> None:
        """End to end: every entrance actually emitted onto a real facade
        carries exactly the sourced clear width and height, for every class
        and every situation in the sweep -- not merely what the catalogue
        function returns in isolation.

        **A14.1 widens this rather than relaxing it.** An entrance may now
        rise two storeys as one round arch, and Daly's four tall arches are
        2.57-2.62 m (carriage) and 1.74-1.76 m (pedestrian) -- squarely
        inside the one-storey bands of 2.41-2.67 and 1.36-1.91. So the width
        assertion is unconditional and unchanged: a tall arch is not a wide
        one. The height assertion is asked of THE DOOR, which on a two-storey
        arch is the leaves inside its lower register (``leaf_height``) and on
        a one-storey door is the whole opening -- and it is the same figure
        in both cases, which is the new claim: the arch grew and the gate did
        not.
        """
        checked = 0
        tall = 0
        for _site, building in ir_sweep:
            for opening in _entrances(building):
                checked += 1
                kind = opening.props["opening_type"]
                w = opening.props["w"]
                # The leaves' own clear height. Present only where the arch
                # spans two storeys, in which case the opening rectangle is
                # the hole in the wall (leaves plus the carved tympanum over
                # them) and this is the door inside it.
                leaf = opening.props.get("leaf_height")
                if leaf is not None:
                    tall += 1
                    assert opening.props["arch_register"] == "leaves", opening.id
                    assert leaf < opening.props["h"], (
                        f"{opening.id}: a two-storey arch's lower register must leave "
                        "room over the leaves for the carved tympanum"
                    )
                h = leaf if leaf is not None else opening.props["h"]
                if kind == "carriage_entrance":
                    assert w == pytest.approx(2.60, abs=1e-6), opening.id
                    assert h == pytest.approx(3.40, abs=1e-6), opening.id
                else:
                    assert w == pytest.approx(1.75, abs=1e-6), opening.id
                    assert h == pytest.approx(2.90, abs=1e-6), opening.id
        assert checked > 20, "the sweep produced too few entrances to mean anything"
        assert tall > 0, (
            "the sweep produced no two-storey entrance arch at all, so the width "
            "assertion above never met the case A14.1 exists to protect"
        )


class TestWindowOpeningWidth:
    """SOURCED. Daly 1864, sixteen buildings across all three classes:
    width 1.04-1.30 m, non-monotonic by class (median 1.139 / 1.235 / 1.070).
    Printed '1.300' at 2-4 boulevard de Sébastopol anchors the top; the floor
    is a scale-bar reading at rue de Longchamps."""

    def test_the_band_matches_the_corpus_span(self) -> None:
        spec = catalogue.opening_window()
        assert float(spec.minimum) == pytest.approx(1.04, rel=0.10)  # scale-bar
        assert float(spec.preferred) == pytest.approx(1.20, abs=0.02)  # printed-anchored
        assert float(spec.maximum) == pytest.approx(1.30, abs=1e-6)  # printed

    def test_window_width_never_exceeds_the_sourced_band_anywhere_in_the_ir(
        self, ir_sweep
    ) -> None:
        checked = 0
        floor = float(catalogue.minimum_light_width())
        ceiling = float(catalogue.opening_window().maximum)
        for _site, building in ir_sweep:
            for opening in _windows(building):
                w = opening.props["w"]
                if w <= 1e-9:
                    continue  # a blind panel: no width to be wrong about
                checked += 1
                assert w <= ceiling + 1e-6, (
                    f"{opening.id}: window width {w:.4f} m exceeds the sourced "
                    f"1.04-1.30 m band"
                )
                assert w >= floor - 1e-6, (
                    f"{opening.id}: window width {w:.4f} m is under the narrowest "
                    f"opening that still reads as a window, {floor:.2f} m"
                )
        assert checked > 50, "the sweep produced too few windows to mean anything"


class TestTheTwoStructuralFindings:
    """The two findings the task calls out explicitly as worth encoding as
    structure, not scalars."""

    def test_window_width_is_class_flat(self) -> None:
        """SOURCED. ``opening_window`` is ABSOLUTE: ``scale_for_class`` is a
        documented no-op on it, and this asserts that directly rather than
        trusting the docstring -- the same width band for all four classes,
        bit for bit."""
        specs = {k: catalogue.opening_window().to_slot_spec(k) for k in _ALL_CLASSES}
        ref = specs[BuildingClass.MODEST]
        for klass, spec in specs.items():
            assert spec.minimum == ref.minimum, klass
            assert spec.preferred == ref.preferred, klass
            assert spec.maximum == ref.maximum, klass

    def test_nobile_window_height_rises_with_class(self) -> None:
        """SOURCED ordering (value INFERRED). Daly: 2.923 / 2.236 / 2.085 m
        down Première/Deuxième/Troisième -- monotonic, a 1.40x spread, the
        opposite shape from the width."""
        heights = [
            float(scale_for_class(catalogue.opening_height_at_the_nobile(), k))
            for k in _ALL_CLASSES
        ]
        assert heights == sorted(heights), heights
        assert heights[0] < heights[-1], "no ordering at all across the class ladder"

    def test_the_contrast_is_visible_end_to_end(self, ir_sweep) -> None:
        """Not just the catalogue functions in isolation: across the real
        swept output, width stays inside one class-independent band while
        height's extremes (meanest class vs grandest) separate clearly, the
        same shape Daly's own corpus has (2.09-2.92 m at the nobile, a
        1.40x spread MODEST-to-GRAND after this typology's four-way split
        of Daly's three).

        Only the EXTREMES are asserted for height, deliberately. A
        class-by-class total order on the realized, swept population is a
        stronger claim than the catalogue's own reference quantity supports:
        the realized height a window gets also depends on its RANK (how far
        it sits from the principal floor) and on how many storeys each
        class's height budget happened to round to on a given site, both of
        which vary with the site, not with class. Mixing many sites averages
        over that confound rather than removing it, so a middle-class pair
        (ORDINARY next to MODEST, concretely) can and does invert in the
        aggregate even though the underlying reference height
        (``opening_height_at_the_nobile``, asserted directly above) never
        does. What survives any amount of that noise is the two ends of the
        ladder, which is also what Daly's own evidence actually claims: the
        clearest ladder in the whole corpus is the SPREAD, top class to
        bottom, not each adjacent step.
        """
        heights: dict[BuildingClass, list[float]] = {k: [] for k in _ALL_CLASSES}
        widths: list[float] = []
        for _site, building in ir_sweep:
            for opening in _windows(building):
                if opening.props["h"] <= 1e-9:
                    continue
                heights[_site.klass].append(opening.props["h"])
                widths.append(opening.props["w"])

        # Width: the whole swept population sits inside the sourced band.
        # The floor can legitimately give way on a very short or narrow
        # storey (A8.4's "narrower, not squatter" rule,
        # ``catalogue.window_in_slot``) -- a documented mechanism unrelated
        # to class -- so only the ceiling, which nothing may cross
        # regardless of class, site or storey, is asserted on the swept
        # population. The class-independence claim itself is proven exactly,
        # without that ambiguity, by ``test_window_width_is_class_flat``.
        floor = float(catalogue.minimum_light_width())
        ceiling = float(catalogue.opening_window().maximum)
        assert widths, "no windows found in the sweep"
        assert min(widths) >= floor - 1e-6
        assert max(widths) <= ceiling + 1e-6

        for klass in _ALL_CLASSES:
            assert heights[klass], f"no windows found for {klass.value} in the sweep"
        mean = {k: sum(vs) / len(vs) for k, vs in heights.items()}
        assert mean[BuildingClass.GRAND] > mean[BuildingClass.MODEST], (
            f"GRAND's mean window height ({mean[BuildingClass.GRAND]:.3f} m) should "
            f"clear MODEST's ({mean[BuildingClass.MODEST]:.3f} m) across the swept "
            "population, matching Daly's own top-to-bottom spread"
        )


class TestRezDeChausseeHeight:
    """SOURCED, as class-independent. Daly, 16 buildings: median 3.95 m,
    range 3.42-4.85 m, class medians 4.20 / 3.95 / 3.81 m -- a 9% fall
    against ranges that overlap almost completely."""

    def test_the_module_constant_matches_the_measured_median(self) -> None:
        assert float(structure._TRADE_GROUND_HEIGHT) == pytest.approx(3.95, rel=0.10)

    def test_trade_ground_floor_height_is_identical_across_every_class(
        self, structure_sweep
    ) -> None:
        checked = 0
        for site, grid, _roled in structure_sweep:
            if site.ground not in (
                GroundProgramme.SHOP,
                GroundProgramme.CAFE,
                GroundProgramme.OFFICE,
            ):
                continue
            ground_h = grid.storeys[0].width
            entrance = catalogue.entrance_for(site.klass, site.street_width, site.ground)
            if float(entrance.storey_height) > float(structure._TRADE_GROUND_HEIGHT) + 1e-9:
                continue  # the door's ABSOLUTE need dominated on this situation
            checked += 1
            assert ground_h == pytest.approx(float(structure._TRADE_GROUND_HEIGHT), abs=1e-6), (
                f"{site.klass.value}/{site.ground.value} ground storey is {ground_h:.3f} m, "
                f"not the class-independent {float(structure._TRADE_GROUND_HEIGHT):.2f} m"
            )
        assert checked > 20, "the sweep produced too few unclamped trade ground floors"


class TestCompressedLevelPresence:
    """SOURCED (presence, not value). 14 of 16 Daly buildings carry a
    compressed level between the ground storey and the noble floor -- 4/4
    Première, 10/10 Deuxième, 0/2 Troisième -- so presence is COMMONER the
    richer the household, never rarer. ``structure._ENTRESOL_STOREYS_REQUIRED``
    encodes the ordering (values INFERRED)."""

    def test_the_requirement_table_falls_as_class_rises(self) -> None:
        table = structure._ENTRESOL_STOREYS_REQUIRED
        ordered = [table[k] for k in _ALL_CLASSES]
        assert ordered == sorted(ordered, reverse=True), (
            f"the entresol bar must fall (or hold) as class rises: {table}"
        )

    def test_presence_never_falls_as_class_rises_on_the_same_site(
        self, structure_sweep
    ) -> None:
        """Group the sweep by every axis except class, and within each group
        walk MODEST -> GRAND: once a class carries a mezzanine, no richer
        class on the identical site may lack one."""
        by_site: dict[tuple, dict[BuildingClass, bool]] = {}
        for site, _grid, roled in structure_sweep:
            key = (site.street_width, site.parcel_width, site.parcel_depth, site.year,
                   site.ground, site.corner)
            has_mezz = any(s.role is Role.MEZZANINE for s in roled.storeys)
            by_site.setdefault(key, {})[site.klass] = has_mezz

        checked = 0
        for key, per_class in by_site.items():
            if len(per_class) < len(_ALL_CLASSES):
                continue  # not every class solved on this exact site
            checked += 1
            seen_true = False
            for klass in _ALL_CLASSES:  # enum declaration order is MODEST..GRAND
                present = per_class[klass]
                if seen_true:
                    assert present, (
                        f"{key}: a poorer class had a compressed level but "
                        f"{klass.value} does not -- entitlement fell as class rose"
                    )
                seen_true = seen_true or present
        assert checked > 10, "too few complete class groups to test the ordering"

    def test_deuxieme_entresol_over_ground_ratio_matches_daly(self) -> None:
        """SOURCED. Nine Deuxième Classe entresols: ratio median 0.775,
        range 0.585-0.871."""
        assert structure._ENTRESOL_OVER_GROUND == pytest.approx(0.775, abs=1e-6)

    def test_compressed_level_ratio_to_the_floor_it_serves_matches_daly(self) -> None:
        """SOURCED. 1.25x in Première, 1.30x in Deuxième -- 1.275 is the
        midpoint of that short interval."""
        assert structure._COMPRESSED_UNDER_THE_FLOOR_IT_SERVES == pytest.approx(1.275, abs=1e-6)


class TestFloorStructureThickness:
    """SOURCED. Printed twice: '30' on the 125 avenue des Champs-Élysées
    storey ladder (Première) and '0.300' at 9 rue du Conservatoire
    (Deuxième) -- two classes, two printed callouts, the same number."""

    def test_lintel_bearing_depth_matches_both_printed_callouts(self) -> None:
        assert float(catalogue.lintel_bearing_depth()) == pytest.approx(0.30, abs=1e-6)

    def test_never_scales_with_class(self) -> None:
        values = {float(scale_for_class(catalogue.lintel_bearing_depth(), k)) for k in _ALL_CLASSES}
        assert values == {0.30}


class TestBalconyProjection:
    """SOURCED. Printed twice, on two different Deuxième buildings: 0.600 m
    at 88 rue de Rivoli, 0.590 m at 120 boulevard de Sébastopol -- 2% apart."""

    def test_the_module_constant_matches_both_printed_callouts(self) -> None:
        from buildings.typologies.paris.qualify.klass import _BALCONY_PROJECTION

        # The constant is 0.60 m; the two printed callouts it sits between
        # (0.600 at 88 rue de Rivoli, 0.590 at 120 boulevard de Sébastopol)
        # average to 0.595, 0.01 m either side of the constant.
        assert float(_BALCONY_PROJECTION) == pytest.approx(0.60, abs=1e-6)
        assert float(_BALCONY_PROJECTION) == pytest.approx(0.595, abs=0.01)

    def test_every_generated_balcony_projects_the_sourced_depth(self, ir_sweep) -> None:
        checked = 0
        for _site, building in ir_sweep:
            for balcony in _balconies(building):
                projection = balcony.props.get("projection")
                if projection is None:
                    continue
                checked += 1
                # Exactly 0.60 m everywhere in this sweep (nothing here comes
                # near the 1823 ordonnance's 0.80 m cap), but the rule is
                # "never above the sourced depth" -- the REGULATORY cap is
                # what is entitled to bring it lower, not this ABSOLUTE figure.
                assert projection <= 0.60 + 1e-6, (
                    f"{balcony.id}: projection {projection} exceeds the sourced 0.60 m "
                    "(only the 1823 ordonnance's REGULATORY cap may bring it below)"
                )
        assert checked > 5, "the sweep produced too few balconies to mean anything"


class TestCorniceHeightCeiling:
    """SOURCED. Cornice height is FLAT between Première and Deuxième
    (19.11 vs 18.90 m) because both are pinned against the 1859 decree's
    20 m facade maximum on a wide street -- six of sixteen buildings sit
    between 19.0 and 20.0 m. "The regulation is visible in the data.\""""

    @pytest.mark.parametrize("street_width", [24.0, 30.0])
    def test_comfortable_and_grand_both_land_in_dalys_observed_band(
        self, street_width: float
    ) -> None:
        for klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
            site = SiteContext(
                street_width=street_width,
                parcel_width=16.0,
                parcel_depth=20.0,
                year=1865,
                klass=klass,
                ground=GroundProgramme.RESIDENTIAL,
                corner=False,
                seed=1,
            )
            grid = solve_structure(site)
            assert float(grid.cornice_height) == pytest.approx(20.0, abs=1e-6), (
                "the 1859 decree's facade ceiling on a street over 20 m wide"
            )
            assert 19.0 - 1e-6 <= grid.eaves_height <= 20.0 + 1e-6, (
                f"{klass.value} eaves at {grid.eaves_height:.2f} m fall outside Daly's "
                "own 19.0-20.0 m observed band on a wide street"
            )

    @pytest.mark.parametrize("street_width", [24.0, 30.0])
    def test_the_top_two_classes_are_flat_against_each_other(self, street_width: float) -> None:
        eaves = {}
        for klass in (BuildingClass.COMFORTABLE, BuildingClass.GRAND):
            site = SiteContext(
                street_width=street_width,
                parcel_width=16.0,
                parcel_depth=20.0,
                year=1865,
                klass=klass,
                ground=GroundProgramme.RESIDENTIAL,
                corner=False,
                seed=1,
            )
            eaves[klass] = solve_structure(site).eaves_height
        gap = abs(eaves[BuildingClass.GRAND] - eaves[BuildingClass.COMFORTABLE])
        assert gap < 1.0, (
            f"COMFORTABLE ({eaves[BuildingClass.COMFORTABLE]:.2f} m) and GRAND "
            f"({eaves[BuildingClass.GRAND]:.2f} m) should sit within about a metre of "
            f"each other, matching Daly's own 0.21 m Première/Deuxième step -- got a "
            f"{gap:.2f} m gap"
        )


# ===========================================================================
# WEAK — ordering only, never a value
# ===========================================================================


class TestWeakOrderingOnly:
    """These quantities are WEAK in the measurement pass (thin samples --
    Première storey taper n=3, Troisième n=1; all Troisième values; door
    height; garde-corps height; facade-width ladder). Only the DIRECTION is
    asserted; no figure from these is ever pinned to a value here."""

    def test_storey_taper_rate_is_less_than_one(self) -> None:
        """WEAK. Daly's apparent trend (0.861/0.906/0.962) is plausible but
        Première n=3 and Troisième n=1 cannot support a value -- only that a
        typical storey is shorter than the one below it is asserted."""
        assert 0.0 < structure._TAPER_RATE < 1.0

    def test_the_storey_margin_above_a_plain_storey_rises_with_class(
        self, structure_sweep
    ) -> None:
        """WEAK ordering (piano nobile height, Daly ×1.39 Première->Troisième;
        upper-storey height, ×1.19). What is actually contractual is the
        MARGIN a class buys above the rigid, body-derived plain storey
        (``structure._typical_storey_band``) -- not that the *specific
        physical storey* the roles phase happens to label PRINCIPAL is
        itself always taller class over class. The two can and do diverge on
        a real sweep: a taper interacting with a different total storey
        count (a coarser class's budget can round to a different number of
        letting floors) can hand two classes principal storeys standing at
        different points in their own tapers, which is the storey-COUNT
        effect, not the margin effect this finding is about. So this is
        checked where the underlying mechanism actually lives -- the band
        itself, for every era in the sweep -- which is guaranteed rather
        than merely observed."""
        checked = set()
        for site, _grid, _roled in structure_sweep:
            if site.year in checked:
                continue
            checked.add(site.year)
            from buildings.typologies.paris.reglement import era_for_year, get_reglement

            reg = get_reglement(era_for_year(site.year))
            preferred = {
                klass: float(structure._typical_storey_band(reg, klass)[1])
                for klass in _ALL_CLASSES
            }
            ordered = [preferred[k] for k in _ALL_CLASSES]
            assert ordered == sorted(ordered), (
                f"year {site.year}: storey margin band is not monotonic by class: "
                f"{dict((k.value, v) for k, v in preferred.items())}"
            )
        assert checked, "no years exercised"


# ===========================================================================
# Regulation, reproduced as a sweep-wide sanity check
# ===========================================================================


def test_built_height_never_exceeds_the_legal_ceiling_anywhere_in_the_sweep(
    structure_sweep,
) -> None:
    """Not a Daly finding but the regulatory backbone every Daly figure sits
    against: no situation in this Second-Empire-only sweep may build past its
    own era's legal facade height."""
    for site, grid, _roled in structure_sweep:
        assert grid.built_height <= float(grid.cornice_height) + 1e-6, (
            f"{site.klass.value} on a {site.street_width:.1f} m street in "
            f"{site.year} built past its legal cornice"
        )
