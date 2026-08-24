#!/usr/bin/env python3
"""Gate G10 — the invariant fuzzer.

    "Fuzz across seeds, widths and eras for invariant violations."  — PLAN.md S10

This sweeps the cross product street width x parcel width x year x class x
ground programme x corner/mid-block x seed, sampled sensibly rather than
combinatorially (PLAN.md explicitly asks for "a few thousand cases, not a
combinatorial explosion"), and asserts the five invariants named in the brief
plus the structural sanity checks S10 lists.

Design of the sample (see ``build_cases``)
-------------------------------------------
The categorical axes (class x ground x corner = 4 x 5 x 2 = 40 combinations)
are covered EXHAUSTIVELY, because there are only 40 of them and exhaustive
coverage is what "every ground programme" and "all four building classes"
in the brief actually ask for. The continuous axes (street width, parcel
width, year) are covered by a small set of "base situations" — a handful of
named regulatory-boundary points (the 1859/1883/1884/1901/1902 hinges; the
narrowest and widest streets and parcels the brief names) unioned with a
deterministic pseudo-random fill of the rest of the range. Each base
situation is then crossed with all 40 categorical combinations, so the
category coverage is exhaustive at every one of the swept continuous points,
not merely somewhere in the corpus.

``N_BASE=75`` base situations x 40 categorical combinations = 3000 cases,
which is squarely "a few thousand" without being a combinatorial explosion
(the naive full cross product, at even a modest 10 values per continuous
axis, would be 10^3 x 40 = 40,000).

Every seed used anywhere in this file is derived from ``FUZZ_SEED`` (a fixed
integer, not wall-clock time or ``os.urandom``), so the whole sample and every
sub-check is reproducible byte-for-byte across runs — the fuzzer obeys the
same I5 discipline it is checking for.

Run:  python3 dev/harness/fuzz.py [--quick]

``--quick`` shrinks ``N_BASE`` for a fast smoke run during development; the
full run (no flag) is what produces the report at ``dev/logs/fuzz_report.md``.
"""
from __future__ import annotations

import argparse
import dataclasses
import math
import random
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from buildings.block.block import BlockDatums  # noqa: E402
from buildings.ir.nodes import Node  # noqa: E402
from buildings.ir.serial import from_json, to_json  # noqa: E402
from buildings.quantity import Abs, Prop, Reg, scale_for_class  # noqa: E402
from buildings.render.svg.render import render  # noqa: E402
from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.solver.fitting import FitInfeasible  # noqa: E402
from buildings.typologies.paris import catalogue  # noqa: E402
from buildings.typologies.paris.generate import generate, walk  # noqa: E402
from buildings.typologies.paris.reglement import era_for_year, get_reglement  # noqa: E402
from buildings.typologies.paris.structure import solve_structure  # noqa: E402

REPORT_PATH = ROOT / "dev" / "logs" / "fuzz_report.md"

# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

FUZZ_SEED = 20140713  # fixed, not wall-clock: the whole sample must be
                       # reproducible, per I5, and so must this harness.

STREET_LO, STREET_HI = 6.0, 40.0
PARCEL_LO, PARCEL_HI = 5.0, 30.0
YEAR_LO, YEAR_HI = 1820, 1910

# Named regulatory-boundary points, folded into the continuous sample rather
# than swept separately: a fuzzer that only ever lands on round numbers is
# less likely to trip on a step function than one that is guaranteed to sit
# exactly on every one of its steps at least once.
EXPLICIT_STREETS: tuple[float, ...] = (6.0, 7.8, 9.75, 12.0, 15.0, 18.0, 20.0, 24.0, 30.0, 40.0)
EXPLICIT_PARCELS: tuple[float, ...] = (5.0, 6.0, 6.5, 7.0, 8.0, 10.0, 14.0, 20.0, 30.0)
EXPLICIT_YEARS: tuple[int, ...] = (
    1820, 1830, 1859, 1860, 1865, 1878, 1883, 1884, 1888, 1898, 1901, 1902, 1910,
)

N_BASE_FULL = 75  # x 40 categorical combinations = 3000 cases
N_BASE_QUICK = 8  # x 40 = 320 cases, for a fast dev smoke run

DETERMINISM_STRIDE = 6  # 1 in 6 cases gets the extra "regenerate, byte-diff" check
I2_STRIDE = 7  # 1 in 7 cases gets the extra "block-datum override" check
RENDER_STRIDE = 10  # 1 in 10 cases gets the extra (pricier) serial round-trip check;
                    # render() itself is cheap and runs on every case (see check_render)

_ALL_CLASSES = tuple(BuildingClass)
_ALL_GROUNDS = tuple(GroundProgramme)
_ALL_CORNER = (False, True)


@dataclasses.dataclass(frozen=True)
class Case:
    index: int
    street_width: float
    parcel_width: float
    parcel_depth: float
    year: int
    klass: BuildingClass
    ground: GroundProgramme
    corner: bool
    seed: int

    def site(self) -> SiteContext:
        return SiteContext(
            street_width=self.street_width,
            parcel_width=self.parcel_width,
            parcel_depth=self.parcel_depth,
            year=self.year,
            klass=self.klass,
            ground=self.ground,
            corner=self.corner,
            seed=self.seed,
        )

    def label(self) -> str:
        return (
            f"street={self.street_width:.2f} parcel={self.parcel_width:.2f} "
            f"depth={self.parcel_depth:.2f} year={self.year} klass={self.klass.value} "
            f"ground={self.ground.value} corner={self.corner} seed={self.seed}"
        )


def _base_tuples(n_base: int) -> list[tuple[float, float, float, int]]:
    """``n_base`` (street_width, parcel_width, parcel_depth, year) tuples,
    deterministic, boundary-anchored, filling the rest by fixed-seed draw."""
    rng = random.Random(FUZZ_SEED)
    out: list[tuple[float, float, float, int]] = []

    n_explicit = max(len(EXPLICIT_STREETS), len(EXPLICIT_PARCELS), len(EXPLICIT_YEARS))
    for i in range(n_explicit):
        street = EXPLICIT_STREETS[i % len(EXPLICIT_STREETS)]
        parcel = EXPLICIT_PARCELS[i % len(EXPLICIT_PARCELS)]
        year = EXPLICIT_YEARS[i % len(EXPLICIT_YEARS)]
        depth = round(rng.uniform(8.0, 26.0), 2)
        out.append((street, parcel, depth, year))

    while len(out) < n_base:
        street = round(rng.uniform(STREET_LO, STREET_HI), 2)
        parcel = round(rng.uniform(PARCEL_LO, PARCEL_HI), 2)
        depth = round(rng.uniform(8.0, 26.0), 2)
        year = rng.randint(YEAR_LO, YEAR_HI)
        out.append((street, parcel, depth, year))
    return out[:n_base]


def build_cases(n_base: int) -> list[Case]:
    """The full corpus: every base situation x every categorical combination.

    Deterministic in the strong sense: calling this twice with the same
    ``n_base`` yields byte-identical output (asserted by
    ``test_case_sample_is_deterministic`` below), because the only source of
    randomness is ``random.Random(FUZZ_SEED)``, seeded fresh here every call.
    """
    bases = _base_tuples(n_base)
    cases: list[Case] = []
    index = 0
    for street, parcel, depth, year in bases:
        for klass in _ALL_CLASSES:
            for ground in _ALL_GROUNDS:
                for corner in _ALL_CORNER:
                    cases.append(
                        Case(
                            index=index,
                            street_width=street,
                            parcel_width=parcel,
                            parcel_depth=depth,
                            year=year,
                            klass=klass,
                            ground=ground,
                            corner=corner,
                            seed=FUZZ_SEED + index,
                        )
                    )
                    index += 1
    return cases


# ---------------------------------------------------------------------------
# Failure bookkeeping
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Failure:
    category: str
    detail: str
    repro: str


class FailureLog:
    """Every distinct failure, grouped by category, capped per category so a
    systemic bug reports once loudly rather than three thousand times."""

    CAP_PER_CATEGORY = 8

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.examples: dict[str, list[Failure]] = defaultdict(list)

    def add(self, category: str, detail: str, repro: str) -> None:
        self.counts[category] += 1
        bucket = self.examples[category]
        if len(bucket) < self.CAP_PER_CATEGORY:
            bucket.append(Failure(category, detail, repro))

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def __bool__(self) -> bool:
        return self.total > 0


# ---------------------------------------------------------------------------
# I1 — phases read strictly backwards: frozen, mutation raises
# ---------------------------------------------------------------------------


def check_frozen_mutation(log: FailureLog, site: SiteContext, root: Node, repro: str) -> None:
    """Attempt to mutate every frozen thing this pipeline hands between
    phases, and record it as a failure if any attempt *succeeds*."""

    def _expect_raises(what: str, fn) -> None:
        try:
            fn()
        except Exception:
            return
        log.add("I1_mutation_not_raising", f"{what} did not raise on mutation", repro)

    _expect_raises("SiteContext.street_width", lambda: setattr(site, "street_width", 999.0))
    _expect_raises("SiteContext.seed", lambda: setattr(site, "seed", 999))

    _expect_raises("BuildingNode.id", lambda: setattr(root, "id", "mutated"))
    _expect_raises("BuildingNode.trace", lambda: setattr(root, "trace", ()))
    _expect_raises("BuildingNode.props item", lambda: root.props.__setitem__("w", -1.0))
    _expect_raises("BuildingNode.children append", lambda: root.children.append(root))

    # Sample a handful of descendant kinds too, not only the root, so a bug
    # confined to one node subclass's __post_init__ cannot hide behind the
    # root happening to be a BuildingNode.
    seen_kinds: set[str] = set()
    for node in walk(root):
        if node.kind in seen_kinds:
            continue
        seen_kinds.add(node.kind)
        _expect_raises(f"{node.kind}.id", lambda n=node: setattr(n, "id", "mutated"))
        _expect_raises(
            f"{node.kind}.props item", lambda n=node: n.props.__setitem__("w", -1.0)
        )
        if len(seen_kinds) > 12:
            break


def check_frozen_intermediate_structures(log: FailureLog, site: SiteContext, repro: str) -> None:
    """Phase-1/2 intermediates (``Grid``, ``RoledGrid``) must be frozen too —
    I1 is about every phase boundary, not only the final IR."""
    from buildings.typologies.paris.roles import assign_roles

    grid = solve_structure(site)
    roled = assign_roles(grid)

    def _expect_raises(what: str, fn) -> None:
        try:
            fn()
        except Exception:
            return
        log.add("I1_mutation_not_raising", f"{what} did not raise on mutation", repro)

    _expect_raises("Grid.eaves_height", lambda: setattr(grid, "eaves_height", 0.0))
    _expect_raises("Grid.storeys", lambda: setattr(grid, "storeys", ()))
    _expect_raises("RoledGrid.storeys", lambda: setattr(roled, "storeys", ()))


# ---------------------------------------------------------------------------
# I2 — a building never samples a block-level fact
# ---------------------------------------------------------------------------


def check_i2_datum_survives(log: FailureLog, case: Case, natural_ceiling: float) -> None:
    """Hand the building a block cornice deliberately DIFFERENT from what it
    would have computed for itself, and confirm the handed-down number is
    what actually gets built to — never silently recomputed.

    The offset is added (never subtracted), so the new ceiling is always
    >= the natural one: this can only ever grant more room, never make an
    otherwise-feasible case infeasible, so a ``FitInfeasible`` here is a
    real bug, not a sampling accident.
    """
    offset_ceiling = natural_ceiling + 0.50
    datums = BlockDatums(
        street_width=case.street_width,
        cornice_height=offset_ceiling,
        string_course_levels=(),
        balcony_levels=(),
    )
    site = case.site()
    repro = f"{case.label()} datums=BlockDatums(cornice_height={offset_ceiling:.4f})"
    try:
        root, _log = generate(site, datums)
    except Exception as exc:  # pragma: no cover - reported, not raised
        log.add(
            "I2_datum_override_raised",
            f"{type(exc).__name__}: {exc}",
            repro,
        )
        return

    got_ceiling = float(root.props["legal_cornice_ceiling"])
    if abs(got_ceiling - offset_ceiling) > 1e-9:
        log.add(
            "I2_datum_not_honoured",
            f"handed down cornice_height={offset_ceiling:.6f} m but building's "
            f"legal_cornice_ceiling={got_ceiling:.6f} m — the datum was recomputed, "
            "not received",
            repro,
        )
        return

    eaves = float(root.props["eaves_height"])
    if eaves > offset_ceiling + 1e-6:
        log.add(
            "I2_datum_not_honoured",
            f"built eaves {eaves:.6f} m exceeds the handed-down ceiling "
            f"{offset_ceiling:.6f} m",
            repro,
        )

    # Every trace entry that records a street width must record the datum's,
    # never a recomputed one (this is exactly what block.check_alignment
    # audits at the block level; here it is checked at the single-building
    # level that I2 actually names).
    for node in walk(root):
        for entry in node.trace:
            sw = entry.inputs.get("street_width")
            if isinstance(sw, (int, float)) and not isinstance(sw, bool):
                if abs(float(sw) - case.street_width) > 1e-9:
                    log.add(
                        "I2_datum_not_honoured",
                        f"node {node.id!r} trace records street_width={sw!r}, "
                        f"expected the handed-down {case.street_width!r}",
                        repro,
                    )


# ---------------------------------------------------------------------------
# I3 — every quantity carries its kind
# ---------------------------------------------------------------------------


def check_i3_quantity_kinds(log: FailureLog) -> None:
    """Direct, case-independent check of the ABSOLUTE/PROPORTIONAL/REGULATORY
    split — run once, not per fuzzed case, because it is a property of the
    quantity system and the catalogue, not of any one situation."""
    repro = "quantity.py direct check (Abs/Prop/Reg + scale_for_class)"

    # ABSOLUTE and REGULATORY are no-ops under scale_for_class, for every class.
    absolute = Abs(3.30, "test absolute")
    regulatory = Reg(2.60, "test regulatory citation")
    for klass in _ALL_CLASSES:
        got_abs = scale_for_class(absolute, klass)
        if float(got_abs) != 3.30:
            log.add(
                "I3_absolute_scaled",
                f"Abs(3.30) scaled to {float(got_abs)} under class {klass.value}",
                repro,
            )
        got_reg = scale_for_class(regulatory, klass)
        if float(got_reg) != 2.60:
            log.add(
                "I3_regulatory_scaled",
                f"Reg(2.60) scaled to {float(got_reg)} under class {klass.value}",
                repro,
            )

    # PROPORTIONAL scales, and monotonically with class (the one contractual
    # ordering _CLASS_SCALE promises — MODEST < ORDINARY < COMFORTABLE < GRAND).
    proportional = Prop(1.00, "test proportional")
    scaled = {klass: float(scale_for_class(proportional, klass)) for klass in _ALL_CLASSES}
    ordered = [scaled[k] for k in _ALL_CLASSES]  # enum declaration order is the ambition order
    if ordered != sorted(ordered):
        log.add(
            "I3_proportional_not_monotonic",
            f"scale_for_class ordering broke: {scaled}",
            repro,
        )
    if len(set(ordered)) < 2:
        log.add(
            "I3_proportional_not_scaling",
            f"PROPORTIONAL quantity scaled identically across every class: {scaled}",
            repro,
        )

    # Mixed-kind arithmetic yields the most rigid kind.
    mixed = absolute + proportional
    if not mixed.rigid:
        log.add(
            "I3_mixed_arithmetic_not_rigid",
            f"Abs + Prop produced a non-rigid kind: {mixed.kind}",
            repro,
        )

    # Scalar */÷ on a rigid quantity must raise (A1.1) rather than silently scale.
    for rigid_q, name in ((absolute, "Abs"), (regulatory, "Reg")):
        try:
            rigid_q * 2.0
        except TypeError:
            pass
        else:
            log.add(
                "I3_rigid_scalar_multiply_silent",
                f"{name} * 2.0 did not raise TypeError",
                repro,
            )

    # Integration-level check: the catalogue's entrance is ABSOLUTE and must
    # be identical across every class *for a given door kind*. Class is
    # allowed to change WHICH door a building gets (carriage vs. pedestrian
    # — a real, class-driven categorical decision, `catalogue.entrance_for`'s
    # own documented behaviour) without that being a violation of I3; what
    # I3 forbids is the ABSOLUTE dimensions of one door kind moving with
    # class, so dimensions are grouped by the resulting kind before compared.
    for street in (7.0, 12.0, 20.0, 32.0):
        for ground in (GroundProgramme.CARRIAGE, GroundProgramme.RESIDENTIAL):
            by_kind: dict[str, set[tuple[float, float]]] = defaultdict(set)
            for klass in _ALL_CLASSES:
                entrance = catalogue.entrance_for(klass, street, ground)
                by_kind[entrance.kind].add(
                    (round(float(entrance.slot_width), 9), round(float(entrance.storey_height), 9))
                )
            for kind, dims in by_kind.items():
                if len(dims) != 1:
                    log.add(
                        "I3_absolute_entrance_varies_by_class",
                        f"street={street} ground={ground.value} kind={kind}: "
                        f"(slot_width, storey_height) varies across class: {dims}",
                        repro,
                    )


# ---------------------------------------------------------------------------
# I4 — every emitted node records the rule that produced it
# ---------------------------------------------------------------------------


def check_i4_trace(log: FailureLog, root: Node, repro: str) -> None:
    for node in walk(root):
        if not node.trace:
            # Unreachable in practice — Node.__post_init__ already refuses to
            # construct an empty-trace node — but checked directly anyway,
            # because I4 is exactly the claim that this cannot happen and a
            # fuzzer that trusted the constructor to enforce its own contract
            # would not actually be testing it.
            log.add("I4_empty_trace", f"node {node.id!r} (kind={node.kind}) has empty trace", repro)
            continue
        for entry in node.trace:
            if not entry.rule or not entry.rule.strip():
                log.add("I4_blank_rule", f"node {node.id!r} has a trace entry with a blank rule", repro)
            if not entry.detail or not entry.detail.strip():
                log.add(
                    "I4_blank_detail",
                    f"node {node.id!r} rule {entry.rule!r} has a blank detail",
                    repro,
                )


# ---------------------------------------------------------------------------
# I5 — same seed + situation ⇒ identical output; different seed differs
# ---------------------------------------------------------------------------


def check_i5_same_seed_identical(log: FailureLog, case: Case, root: Node, repro: str) -> None:
    site = case.site()
    try:
        root2, _log2 = generate(site)
    except Exception as exc:  # pragma: no cover - reported, not raised
        log.add("I5_regeneration_raised", f"{type(exc).__name__}: {exc}", repro)
        return
    if root2 != root:
        log.add("I5_same_seed_differs", "regenerating the identical situation changed the IR", repro)
        return
    if render(root) != render(root2):
        log.add("I5_same_seed_render_differs", "identical IR rendered to different SVG", repro)


def check_render(log: FailureLog, root: Node, repro: str) -> str | None:
    """Render never raises, and renders the same node twice identically.

    Cheap (~3 ms), so run on every case in the sweep, not a subset: the
    renderer is one of only two named entry points in this task and
    deserves the same breadth of coverage ``generate`` gets, not a thinner
    sample of it. Returns the rendered SVG so a caller doing the (pricier)
    serial round-trip check does not have to render a third time.
    """
    try:
        svg1 = render(root)
    except Exception as exc:  # pragma: no cover - reported, not raised
        log.add("render_raised", f"{type(exc).__name__}: {exc}", repro)
        return None
    svg2 = render(root)
    if svg1 != svg2:
        log.add("render_not_deterministic", "rendering the same node twice differed", repro)
    return svg1


def check_serial_roundtrip(log: FailureLog, root: Node, repro: str) -> None:
    try:
        back = from_json(to_json(root))
    except Exception as exc:  # pragma: no cover - reported, not raised
        log.add("serial_roundtrip_raised", f"{type(exc).__name__}: {exc}", repro)
        return
    if back != root:
        log.add("serial_roundtrip_lossy", "from_json(to_json(root)) != root", repro)


# ---------------------------------------------------------------------------
# Structural sanity
# ---------------------------------------------------------------------------

_NUMERIC_DIM_KEYS = ("w", "h")


#: Node kinds/keys where a zero dimension is a deliberate design choice, not
#: a defect, discovered by running this exact check over a corpus and reading
#: the source at each kind it flagged (see the fuzz report's own working
#: notes): a ``keystone`` is drawn as the stone at the crown of the arch — a
#: line at the head of the light, not a volume, so ``h`` is 0.0 by
#: construction (``compose.py``, the ``KeystoneNode`` literal ``"h": 0.0``);
#: a ``special`` node whose ``props["absence"]`` is set (e.g.
#: ``b/roof/no_dormers``) is an explicit "nothing stands here, and here is
#: why" marker the trace facility uses to record a *refusal* — I4 wants the
#: refusal traced as much as a feature, and a marker for it has no height by
#: definition.
def _zero_dimension_is_by_design(node: Node, key: str) -> bool:
    if key == "h" and node.kind == "keystone":
        return True
    if key == "h" and node.kind == "special" and node.props.get("absence") is not None:
        return True
    return False


def check_no_nan_negative_zero(log: FailureLog, root: Node, repro: str) -> None:
    for node in walk(root):
        for key in _NUMERIC_DIM_KEYS:
            if key not in node.props:
                continue
            value = node.props[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            fvalue = float(value)
            if math.isnan(fvalue) or math.isinf(fvalue):
                log.add(
                    "nonfinite_dimension",
                    f"node {node.id!r} (kind={node.kind}) has {key}={fvalue!r}",
                    repro,
                )
            elif fvalue < 0.0:
                log.add(
                    "negative_dimension",
                    f"node {node.id!r} (kind={node.kind}) has {key}={fvalue!r}",
                    repro,
                )
            elif fvalue == 0.0 and node.kind not in ("silhouette",) and not _zero_dimension_is_by_design(node, key):
                log.add(
                    "zero_width_element",
                    f"node {node.id!r} (kind={node.kind}) has {key}=0.0",
                    repro,
                )
        points = node.props.get("points")
        if isinstance(points, tuple):
            for i, y in points:
                if not all(math.isfinite(v) for v in (i, y)):
                    log.add(
                        "nonfinite_polyline_point",
                        f"node {node.id!r} silhouette has a non-finite point ({i!r}, {y!r})",
                        repro,
                    )


def check_bays_fill_parcel_exactly(log: FailureLog, case: Case, grid, repro: str) -> None:
    total = math.fsum(b.width for b in grid.bays)
    if abs(total - case.parcel_width) > 1e-9:
        log.add(
            "bay_residual",
            f"bays sum to {total:.12f} m, parcel is {case.parcel_width:.12f} m "
            f"(residual {total - case.parcel_width:.3e})",
            repro,
        )


def check_storey_minimum(log: FailureLog, case: Case, grid, repro: str) -> None:
    """The 1859 minimum (or the pre-1859 human floor) applies to ordinary
    habitable storeys and to any storey standing inside the comble — never
    to the ground floor or the entresol, both of which have their own,
    separately-asserted height rules (``structure._ground_height_quantity``,
    ``structure._entresol_height``, and the entresol's explicit exemption
    from this very minimum)."""
    reg = get_reglement(era_for_year(case.year))
    minimum = reg.min_floor_height if reg.min_floor_height > 0.0 else 2.20
    tol = 1e-6
    for slot in grid.storeys:
        if slot.name in ("ground", "entresol"):
            continue
        if slot.width < minimum - tol:
            log.add(
                "storey_below_minimum",
                f"storey {slot.name!r} at {slot.width:.4f} m is below the "
                f"{minimum:.2f} m minimum ({reg.decree if reg.min_floor_height > 0 else 'pre-1859 human floor'})",
                repro,
            )


def check_silhouette_within_envelope(log: FailureLog, case: Case, root: Node, envelope, repro: str) -> None:
    """A cut-down version of ``tests/invariant/test_silhouette_envelope.py``'s
    ``_violations``: re-derives containment from ``max_height_for_setback``
    (the inverse of the curve the roof was built from) rather than calling
    ``Silhouette.within``, and samples along segments, not only at vertices."""
    silhouette = next((n for n in root.children if n.kind == "silhouette"), None)
    if silhouette is None:
        log.add("no_silhouette", "building has no silhouette child node", repro)
        return
    points = silhouette.props["points"]
    on_plane = [y for inset, y in points if abs(inset) <= 1e-6]
    eaves = max(on_plane) if on_plane else 0.0
    tol = 1e-6

    if eaves > envelope.facade_height + tol:
        log.add(
            "silhouette_eaves_exceeds_facade_limit",
            f"eaves {eaves:.4f} m > facade limit {envelope.facade_height:.4f} m",
            repro,
        )

    def _check(inset: float, y: float, where: str) -> None:
        if inset < -tol:
            log.add("silhouette_overhangs_street", f"{where}: inset {inset:+.4f} m", repro)
            return
        if y > envelope.total_height + tol:
            log.add(
                "silhouette_exceeds_ceiling",
                f"{where}: {y:.4f} m above pavement, gabarit tops out at "
                f"{envelope.total_height:.4f} m",
                repro,
            )
        h = y - eaves
        if h <= tol:
            return
        allowed = envelope.max_height_for_setback(inset)
        if h > allowed + tol:
            log.add(
                "silhouette_breaks_envelope",
                f"{where}: at inset {inset:.4f} m envelope allows {allowed:.4f} m, "
                f"point is at {h:.4f} m above the eaves",
                repro,
            )

    for n, (inset, y) in enumerate(points):
        _check(inset, y, f"vertex {n} ({inset:.3f},{y:.3f})")
    for n, ((i0, y0), (i1, y1)) in enumerate(zip(points, points[1:])):
        for k in range(1, 6):
            t = k / 6.0
            _check(i0 + (i1 - i0) * t, y0 + (y1 - y0) * t, f"segment {n} t={t:.2f}")


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------


def self_test_checkers_have_teeth(log: FailureLog) -> list[str]:
    """Prove the checkers can fail, by feeding each one a synthetic,
    deliberately-broken input and confirming it is caught.

    Per the task brief: "A fuzzer that finds nothing on a first run of an
    unproven design is more likely broken than the design is perfect."  A
    clean 3000-case run is exactly the situation that warrants suspicion, and
    the honest response to "maybe every checker is vacuously true" is not to
    assert harder on real output but to show each checker *can* fail, on
    input built by hand rather than by ``generate``. This mirrors the
    codebase's own discipline (``test_the_sweep_could_have_failed`` in
    ``tests/invariant/test_silhouette_envelope.py``) rather than inventing a
    new one.

    Any checker that fails to catch its synthetic violation is a serious
    harness bug and is logged into the real failure log, not just noted.
    """
    from buildings.solver.fitting import PlacedSlot, SlotKind

    notes: list[str] = []

    def _fired(name: str, probe_log: FailureLog) -> None:
        ok = probe_log.total > 0
        notes.append(f"`{name}`: {'PASS (caught the injected violation)' if ok else 'FAIL — did not fire'}")
        if not ok:
            log.add(
                "checker_missing_teeth",
                f"{name} did not fire on a deliberately broken synthetic input — "
                "this checker may be vacuously true on the real corpus too",
                "self_test_checkers_have_teeth()",
            )

    # -- check_bays_fill_parcel_exactly: bays that sum to the wrong width ---
    probe = FailureLog()
    import types

    bad_bays_grid = types.SimpleNamespace(
        bays=(
            PlacedSlot("pier_end", SlotKind.FLEXIBLE, 0.0, 0.40),
            PlacedSlot("bay", SlotKind.REPEATING, 0.40, 3.00),
        )
    )
    fake_case = Case(0, 20.0, 12.0, 18.0, 1865, BuildingClass.ORDINARY, GroundProgramme.SHOP, False, 0)
    check_bays_fill_parcel_exactly(probe, fake_case, bad_bays_grid, "synthetic")
    _fired("check_bays_fill_parcel_exactly (bays sum wrong)", probe)

    # -- check_storey_minimum: a habitable storey 30 cm under the minimum ---
    probe = FailureLog()
    reg = get_reglement(era_for_year(1865))
    bad_storeys_grid = types.SimpleNamespace(
        storeys=(
            PlacedSlot("ground", SlotKind.FIXED, 0.0, 4.00),
            PlacedSlot("storey", SlotKind.REPEATING, 4.00, reg.min_floor_height - 0.30),
        )
    )
    check_storey_minimum(probe, fake_case, bad_storeys_grid, "synthetic")
    _fired("check_storey_minimum (storey under the 1859 minimum)", probe)

    # -- check_no_nan_negative_zero: a NaN width and a negative height -------
    from buildings.ir.nodes import BuildingNode
    from buildings.trace import TraceEntry

    bad_node = BuildingNode(
        id="synthetic",
        kind="building",
        trace=(TraceEntry(rule="synthetic.rule", phase="structure", detail="synthetic"),),
        props={"w": float("nan"), "h": -1.0},
    )
    probe = FailureLog()
    check_no_nan_negative_zero(probe, bad_node, "synthetic")
    _fired("check_no_nan_negative_zero (NaN width + negative height)", probe)

    # -- check_silhouette_within_envelope: a point pushed outside the arc ----
    site = SiteContext(20.0, 12.0, 18.0, 1888, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=0)
    real_root, _ = generate(site)
    real_grid = solve_structure(site)
    real_sil = next(n for n in real_root.children if n.kind == "silhouette")
    bad_points = tuple(
        (i, y + 5.0) if n == len(real_sil.props["points"]) // 2 else (i, y)
        for n, (i, y) in enumerate(real_sil.props["points"])
    )
    bad_sil = dataclasses.replace(real_sil, props={**dict(real_sil.props), "points": bad_points})
    bad_root = dataclasses.replace(
        real_root,
        children=tuple(bad_sil if n.kind == "silhouette" else n for n in real_root.children),
    )
    probe = FailureLog()
    check_silhouette_within_envelope(probe, fake_case, bad_root, real_grid.envelope, "synthetic")
    _fired("check_silhouette_within_envelope (point pushed 5 m above the envelope)", probe)

    # -- I4: the type system itself refuses an empty-trace node -------------
    # Not a probe against the *checker* (which cannot even see such a node,
    # per its own docstring) but against the guarantee the checker leans on:
    # Node.__post_init__ raising is what makes I4_empty_trace unreachable in
    # practice, and that claim is only worth trusting if it is tested here
    # rather than assumed.
    try:
        BuildingNode(id="x", kind="building", trace=(), props={})
    except ValueError:
        notes.append("`Node.__post_init__` (I4): PASS (raises on empty trace, as documented)")
    else:
        notes.append("`Node.__post_init__` (I4): FAIL — constructed a node with an empty trace")
        log.add(
            "checker_missing_teeth",
            "Node(trace=()) did not raise — I4's type-level guarantee is gone",
            "self_test_checkers_have_teeth()",
        )

    return notes


def _self_check_sample(log: FailureLog, cases: list[Case]) -> list[str]:
    """The fuzzer's own tripwire: confirm the sample really does vary every
    axis the brief asks for, and that building it twice is deterministic.

    Per the task brief: "A fuzzer that finds nothing on a first run of an
    unproven design is more likely broken than the design is perfect — say so
    if that happens, and double-check the fuzzer is actually varying its
    inputs and actually asserting." This is that double-check, made explicit
    and reported rather than merely trusted.
    """
    notes: list[str] = []
    streets = {c.street_width for c in cases}
    parcels = {c.parcel_width for c in cases}
    years = {c.year for c in cases}
    classes = {c.klass for c in cases}
    grounds = {c.ground for c in cases}
    corners = {c.corner for c in cases}
    seeds = {c.seed for c in cases}

    notes.append(f"distinct street widths: {len(streets)} (range {min(streets):.2f}-{max(streets):.2f})")
    notes.append(f"distinct parcel widths: {len(parcels)} (range {min(parcels):.2f}-{max(parcels):.2f})")
    notes.append(f"distinct years: {len(years)} (range {min(years)}-{max(years)})")
    notes.append(f"classes present: {sorted(k.value for k in classes)}")
    notes.append(f"ground programmes present: {sorted(g.value for g in grounds)}")
    notes.append(f"corner values present: {sorted(corners)}")
    notes.append(f"distinct seeds: {len(seeds)} of {len(cases)} cases")

    # Thresholds scale with the sample size actually requested: a `--quick`
    # smoke run with N_BASE_QUICK=8 base situations genuinely cannot produce
    # 20 distinct street widths, and that is not the same failure as a full
    # run collapsing onto a handful of values. Capped at the values the full
    # run is expected to clear.
    n_base = max(1, len(cases) // 40)
    min_distinct = min(20, max(3, round(n_base * 0.6)))
    min_years = min(10, max(3, round(n_base * 0.4)))

    if classes != set(_ALL_CLASSES):
        log.add("fuzzer_not_varying", f"not all classes present: {sorted(k.value for k in classes)}", "build_cases()")
    if grounds != set(_ALL_GROUNDS):
        log.add("fuzzer_not_varying", f"not all ground programmes present: {sorted(g.value for g in grounds)}", "build_cases()")
    if corners != {False, True}:
        log.add("fuzzer_not_varying", f"corner axis not varied: {sorted(corners)}", "build_cases()")
    if len(streets) < min_distinct:
        log.add("fuzzer_not_varying", f"only {len(streets)} distinct street widths (want >= {min_distinct})", "build_cases()")
    if len(parcels) < min_distinct:
        log.add("fuzzer_not_varying", f"only {len(parcels)} distinct parcel widths (want >= {min_distinct})", "build_cases()")
    if len(years) < min_years:
        log.add("fuzzer_not_varying", f"only {len(years)} distinct years (want >= {min_years})", "build_cases()")
    if len(seeds) != len(cases):
        log.add("fuzzer_not_varying", "seeds are not all distinct", "build_cases()")

    # Determinism of the sample-builder itself.
    cases2 = build_cases(len(_base_tuples(len(cases) // 40)))
    if cases != cases2:
        log.add("fuzzer_sample_nondeterministic", "build_cases() gave different output on a second call", "build_cases()")

    return notes


def run(n_base: int) -> tuple[FailureLog, dict[str, Any]]:
    log = FailureLog()
    cases = build_cases(n_base)

    notes = _self_check_sample(log, cases)
    notes.append("")
    notes.append("Checker negative controls (synthetic broken input, not from `generate()`):")
    notes.extend(self_test_checkers_have_teeth(log))

    check_i3_quantity_kinds(log)

    n_ok = 0
    n_infeasible = 0
    n_other_exception = 0
    mutation_checked = 0
    seed_variation_samples: dict[tuple, set[str]] = defaultdict(set)

    t0 = time.time()
    for case in cases:
        site = case.site()
        repro = case.label()
        try:
            root, gen_log = generate(site)
        except FitInfeasible as exc:
            n_infeasible += 1
            log.add(
                "generation_infeasible",
                f"{exc}",
                repro,
            )
            continue
        except Exception as exc:
            n_other_exception += 1
            log.add(
                "generation_raised",
                f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=6)}",
                repro,
            )
            continue

        n_ok += 1

        check_i4_trace(log, root, repro)
        check_no_nan_negative_zero(log, root, repro)
        check_render(log, root, repro)

        try:
            grid = solve_structure(site)
        except Exception as exc:  # pragma: no cover - reported, not raised
            log.add("solve_structure_raised_after_generate_succeeded", f"{type(exc).__name__}: {exc}", repro)
            grid = None
        if grid is not None:
            check_bays_fill_parcel_exactly(log, case, grid, repro)
            check_storey_minimum(log, case, grid, repro)
            check_silhouette_within_envelope(log, case, root, grid.envelope, repro)

        if mutation_checked < 40:
            check_frozen_mutation(log, site, root, repro)
            check_frozen_intermediate_structures(log, site, repro)
            mutation_checked += 1

        if case.index % DETERMINISM_STRIDE == 0:
            check_i5_same_seed_identical(log, case, root, repro)

        if case.index % RENDER_STRIDE == 0:
            check_serial_roundtrip(log, root, repro)

        if case.index % I2_STRIDE == 0 and grid is not None:
            check_i2_datum_survives(log, case, float(grid.cornice_height))

        # I5's other half: across the (street, parcel, depth, year) group this
        # case belongs to, seed must actually move something. Grouped by the
        # base tuple + categorical combo, sampled thinly (every 40th case,
        # i.e. once per base tuple) so this stays cheap.
        if case.index % 40 == 0:
            group_key = (case.street_width, case.parcel_width, case.parcel_depth, case.year)
            for extra_seed in range(5):
                alt_site = dataclasses.replace(site, seed=FUZZ_SEED * 7 + extra_seed)
                try:
                    alt_root, _ = generate(alt_site)
                except FitInfeasible:
                    continue
                seed_variation_samples[group_key].add(render(alt_root))

    elapsed = time.time() - t0

    distinct_per_group = [len(v) for v in seed_variation_samples.values()]
    if seed_variation_samples and max(distinct_per_group, default=0) <= 1 and sum(
        1 for n in distinct_per_group if n > 1
    ) == 0:
        log.add(
            "I5_seed_never_varies_output",
            "across every sampled group, changing the seed never changed the "
            "rendered output — either the RNG is disconnected from the "
            "pipeline, or this corpus never exercises a seed-driven decision",
            f"{len(seed_variation_samples)} groups sampled",
        )

    stats = {
        "n_cases": len(cases),
        "n_ok": n_ok,
        "n_infeasible": n_infeasible,
        "n_other_exception": n_other_exception,
        "elapsed_s": elapsed,
        "notes": notes,
        "seed_groups_with_variation": sum(1 for n in distinct_per_group if n > 1),
        "seed_groups_sampled": len(distinct_per_group),
    }
    return log, stats


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_CATEGORY_TITLES: dict[str, str] = {
    "generation_infeasible": "generate() refused (FitInfeasible)",
    "generation_raised": "generate() raised an unexpected exception",
    "solve_structure_raised_after_generate_succeeded": "solve_structure() raised where generate() had just succeeded",
    "I1_mutation_not_raising": "I1 — mutation of a frozen object did not raise",
    "I2_datum_override_raised": "I2 — generate() with a datum override raised",
    "I2_datum_not_honoured": "I2 — the handed-down block datum was not honoured verbatim",
    "I3_absolute_scaled": "I3 — an ABSOLUTE quantity scaled under scale_for_class",
    "I3_regulatory_scaled": "I3 — a REGULATORY quantity scaled under scale_for_class",
    "I3_proportional_not_monotonic": "I3 — PROPORTIONAL scaling was not monotonic in class",
    "I3_proportional_not_scaling": "I3 — PROPORTIONAL quantity did not scale at all",
    "I3_mixed_arithmetic_not_rigid": "I3 — Abs + Prop was not the most-rigid kind",
    "I3_rigid_scalar_multiply_silent": "I3 — scalar multiply of a rigid Quantity did not raise",
    "I3_absolute_entrance_varies_by_class": "I3 — an ABSOLUTE catalogue entrance varied by class",
    "I4_empty_trace": "I4 — node has an empty trace",
    "I4_blank_rule": "I4 — trace entry has a blank rule id",
    "I4_blank_detail": "I4 — trace entry has a blank detail",
    "I5_same_seed_differs": "I5 — regenerating the same seed+situation changed the IR",
    "I5_same_seed_render_differs": "I5 — regenerating the same seed+situation changed the render",
    "I5_regeneration_raised": "I5 — regenerating an identical situation raised",
    "I5_seed_never_varies_output": "I5 — seed never changed rendered output across the sample",
    "render_raised": "render(node) raised an exception",
    "render_not_deterministic": "rendering the same node twice gave different output",
    "serial_roundtrip_raised": "IR JSON round-trip raised",
    "serial_roundtrip_lossy": "IR JSON round-trip lost information",
    "no_silhouette": "structural — building has no silhouette node",
    "silhouette_eaves_exceeds_facade_limit": "structural — eaves line exceeds the legal facade limit",
    "silhouette_overhangs_street": "structural — silhouette overhangs the public way",
    "silhouette_exceeds_ceiling": "structural — silhouette exceeds the legal total height",
    "silhouette_breaks_envelope": "structural — silhouette breaks the regulatory envelope",
    "bay_residual": "structural — bays do not fill the parcel exactly (residual >= 1e-9)",
    "storey_below_minimum": "structural — a storey is below the 1859 (or human) minimum height",
    "nonfinite_dimension": "structural — NaN/Inf dimension",
    "negative_dimension": "structural — negative dimension",
    "zero_width_element": "structural — zero-width element",
    "nonfinite_polyline_point": "structural — non-finite silhouette point",
    "fuzzer_not_varying": "harness self-check — sample is not varying an input axis",
    "fuzzer_sample_nondeterministic": "harness self-check — build_cases() is not deterministic",
}


def write_report(log: FailureLog, stats: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Invariant fuzzer report")
    lines.append("")
    lines.append(f"Cases run: **{stats['n_cases']}**")
    lines.append(
        f"- generated successfully: {stats['n_ok']}\n"
        f"- refused as infeasible (`FitInfeasible`): {stats['n_infeasible']}\n"
        f"- raised an unexpected exception: {stats['n_other_exception']}\n"
        f"- wall time: {stats['elapsed_s']:.1f} s"
    )
    lines.append("")
    lines.append("## Harness self-check (is the fuzzer actually fuzzing?)")
    lines.append("")
    for note in stats["notes"]:
        lines.append(f"- {note}" if note else "")
    lines.append(
        f"- seed-variation groups sampled: {stats['seed_groups_sampled']}, of which "
        f"{stats['seed_groups_with_variation']} showed >1 distinct rendered output "
        "across 5 alternate seeds"
    )
    lines.append("")

    if not log:
        lines.append("## Result: NO FAILURES FOUND")
        lines.append("")
        lines.append(
            "Every case in the sweep generated without raising, every I1-I5 check "
            "held, and every structural sanity check held. Per the task brief: a "
            "fuzzer that finds nothing on the first run of an unproven design is "
            "more likely broken than the design is perfect, so this result should "
            "be treated with suspicion rather than as a clean bill of health. The "
            "harness self-check above is the evidence that the sample really is "
            "varying every input axis and that assertions really are running "
            "(rather than, say, silently catching everything and asserting "
            "nothing) — read it before trusting this line."
        )
        lines.append("")
        return "\n".join(lines)

    lines.append(f"## Result: {log.total} FAILURE(S) across {len(log.counts)} categories")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---|")
    for category, count in log.counts.most_common():
        title = _CATEGORY_TITLES.get(category, category)
        lines.append(f"| {title} | {count} |")
    lines.append("")

    lines.append("## Failures by category, with minimal reproducing input")
    lines.append("")
    for category, count in log.counts.most_common():
        title = _CATEGORY_TITLES.get(category, category)
        lines.append(f"### {title} ({count} occurrence(s))")
        lines.append("")
        for failure in log.examples[category]:
            lines.append(f"- **repro**: `{failure.repro}`")
            detail_lines = failure.detail.splitlines() or [""]
            lines.append(f"  **detail**: {detail_lines[0]}")
            for extra in detail_lines[1:]:
                lines.append(f"    {extra}")
        if count > len(log.examples[category]):
            lines.append(f"  - ...and {count - len(log.examples[category])} more, not shown")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="small smoke-test run")
    args = parser.parse_args(argv)

    n_base = N_BASE_QUICK if args.quick else N_BASE_FULL
    log, stats = run(n_base)

    report = write_report(log, stats)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nReport written to {REPORT_PATH}")

    return 1 if log else 0


if __name__ == "__main__":
    raise SystemExit(main())
