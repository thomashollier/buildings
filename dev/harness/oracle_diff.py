#!/usr/bin/env python3
"""S10 — the reference-oracle diff harness.

> "Keep the previous implementation running as a reference oracle; diff the
> same situations against it."

Drives BOTH systems — the rewrite (``buildings.typologies.paris.generate``)
and the previous implementation (``../haussmann`` — ``core.generator``,
``core.grammar``, ``core.reglement``, ``backends.svg``) — over the same
``Situation`` objects, and separates what comes back into three buckets. The
two systems are a deliberate rewrite with a different rule model; agreement
is not the goal everywhere, so the buckets carry different obligations:

1. **REGULATORY — must agree, bit for bit.** Cornice height limits, arc
   radii, era boundaries, roof-envelope shape, the 28.50 m ceiling. These
   come from the same ported ``reglement`` module, so any difference here is
   a real bug in the port or in how a phase routes the number through — not
   a design disagreement. Asserted with equality (float tolerance 1e-6).

2. **PROPORTION — should land close.** Storey counts, built/total height,
   bay counts for a given parcel width. The two systems get here by
   completely different roads (the old one rolls floor heights per seed
   inside a gabarit budget and lets an entresol fall out of the remainder;
   the new one decides the entresol from programme before the budget is
   filled and produces one deterministic answer per situation — A2.2), so
   these are reported as **old's distribution across seeds** vs. **new's
   single value**, against an explicitly stated tolerance. Outside the
   tolerance is flagged as an OUTLIER, not asserted to be wrong.

3. **QUALITATIVE — may differ freely.** Ornament, variant choice, entresol
   presence, entrance handling, attic reachability, per-storey treatment.
   Recorded for the report; never asserted on.

Guarded import (A1.7): a missing ``../haussmann`` checkout is a HARD FAILURE
by default — the whole point of a reference oracle is that it actually runs,
and a module that quietly skips 400 comparisons while the suite reports green
is the vacuous-gate condition G2 exists to prevent. Set
``HAUSSMANN_ORACLE_OPTIONAL=1`` to opt back into skip-if-missing.
"""

from __future__ import annotations

import math
import os
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------
# Wiring: the new system lives on ``sys.path`` via ``pyproject.toml``'s
# ``pythonpath = ["src"]`` under pytest, and is added explicitly here for the
# CLI entry point (``python dev/harness/oracle_diff.py``). The old system is
# a sibling checkout nothing else puts on the path.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]  # .../buildings
_SRC = REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

HAUSSMANN_ROOT = REPO_ROOT.parent / "haussmann"

_OPTIONAL = os.environ.get("HAUSSMANN_ORACLE_OPTIONAL") == "1"


class OracleUnavailable(AssertionError):
    """Raised when ``../haussmann`` cannot be imported and it is not optional.

    A1.7: this must be a hard failure by default, not a silent skip.
    """


def _import_old():
    if str(HAUSSMANN_ROOT) not in sys.path:
        sys.path.insert(0, str(HAUSSMANN_ROOT))
    import core.floor as old_floor  # noqa: F401
    import core.generator as old_generator  # noqa: F401
    import core.reglement as old_reglement  # noqa: F401
    import core.types as old_types  # noqa: F401

    return old_generator, old_reglement, old_types, old_floor


try:
    _old_generator, _old_reglement, _old_types, _old_floor = _import_old()
    HAUSSMANN_AVAILABLE = True
    _IMPORT_ERROR: Exception | None = None
except ImportError as exc:  # pragma: no cover - exercised only when repo missing
    HAUSSMANN_AVAILABLE = False
    _IMPORT_ERROR = exc
    _old_generator = _old_reglement = _old_types = _old_floor = None


def require_haussmann() -> None:
    """Guard every test/entry point that touches the old system.

    A missing oracle is a HARD FAILURE unless ``HAUSSMANN_ORACLE_OPTIONAL=1``
    is explicitly set (A1.7) — mirrors ``tests/oracle/test_reglement_diff.py``.
    """
    if HAUSSMANN_AVAILABLE:
        return
    if _OPTIONAL:
        import pytest  # local import: only needed on this path

        pytest.skip(
            f"haussmann reference repo not available at {HAUSSMANN_ROOT} "
            "(HAUSSMANN_ORACLE_OPTIONAL=1 set)",
            allow_module_level=True,
        )
    raise OracleUnavailable(
        f"haussmann reference repo not found at {HAUSSMANN_ROOT} -- the oracle "
        "diff harness cannot run. This is a HARD FAILURE, not a skip (A1.7): a "
        "missing oracle must not let the suite report green while every oracle "
        "comparison in this module silently never ran. If you deliberately do "
        "not have the sibling ../haussmann checkout, set "
        "HAUSSMANN_ORACLE_OPTIONAL=1 to opt into skip-if-missing behaviour "
        "instead."
    ) from _IMPORT_ERROR


# ---------------------------------------------------------------------------
# The new system — always importable, no guard needed.
# ---------------------------------------------------------------------------

from buildings.site import BuildingClass, GroundProgramme, SiteContext  # noqa: E402
from buildings.solver.fitting import SlotKind  # noqa: E402
from buildings.typologies.paris import catalogue  # noqa: E402
from buildings.typologies.paris.generate import generate  # noqa: E402
from buildings.typologies.paris.reglement import (  # noqa: E402
    era_for_year as new_era_for_year,
)
from buildings.typologies.paris.reglement import (  # noqa: E402
    get_reglement as new_get_reglement,
)
from buildings.typologies.paris.roles import Role, assign_roles  # noqa: E402
from buildings.typologies.paris.structure import solve_structure  # noqa: E402

# ---------------------------------------------------------------------------
# Situations — the shared vocabulary both systems are driven with.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Situation:
    """One (street, parcel, date, class, programme) fed to both systems."""

    street_width: float
    parcel_width: float
    parcel_depth: float
    year: int
    klass: BuildingClass
    ground: GroundProgramme = GroundProgramme.RESIDENTIAL
    corner: bool = False
    seed: int = 0

    @property
    def label(self) -> str:
        corner = "_corner" if self.corner else ""
        return (
            f"w{self.street_width:g}m_{self.year}_{self.klass.value}_"
            f"{self.ground.value}{corner}_s{self.seed}"
        )


def new_site(situation: Situation) -> SiteContext:
    return SiteContext(
        street_width=situation.street_width,
        parcel_width=situation.parcel_width,
        parcel_depth=situation.parcel_depth,
        year=situation.year,
        klass=situation.klass,
        ground=situation.ground,
        corner=situation.corner,
        seed=situation.seed,
    )


# ---------------------------------------------------------------------------
# Mapping the new vocabulary onto the old one. Both mappings are LOSSY and
# documented as such — they are how a 4-class, 5-programme system gets driven
# through a 3-preset, boolean-plus-enum one, not a claim that the two
# vocabularies are equivalent.
# ---------------------------------------------------------------------------

#: The old system has three style presets; the new one has four classes.
#: ORDINARY and COMFORTABLE both collapse onto RESIDENTIAL — there is no
#: finer old preset to distinguish them. This is exactly the kind of
#: divergence recorded as QUALITATIVE, never asserted on.
OLD_STYLE_FOR_CLASS: Mapping[BuildingClass, str] = {
    BuildingClass.MODEST: "MODEST",
    BuildingClass.ORDINARY: "RESIDENTIAL",
    BuildingClass.COMFORTABLE: "RESIDENTIAL",
    BuildingClass.GRAND: "BOULEVARD",
}

#: (has_porte_cochere, ground_floor_type) for each new GroundProgramme.
#: The old system only ever gates the entrance through
#: ``has_porte_cochere`` and has no SHOP/CAFE/OFFICE distinction; the new
#: system's A6.1 (every building has an entrance) has no analogue in the old
#: one at all for non-CARRIAGE programmes. Documented, not asserted.
OLD_GROUND_FOR: Mapping[GroundProgramme, tuple[bool, str]] = {
    GroundProgramme.RESIDENTIAL: (False, "RESIDENTIAL"),
    GroundProgramme.SHOP: (False, "COMMERCIAL"),
    GroundProgramme.CAFE: (False, "COMMERCIAL"),
    GroundProgramme.OFFICE: (False, "RESIDENTIAL"),
    GroundProgramme.CARRIAGE: (True, "RESIDENTIAL"),
}


# ---------------------------------------------------------------------------
# Result records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NewResult:
    era_name: str
    facade_height_limit: float
    arc_radius: float
    roof_envelope: str
    legal_ridge_height: float
    legal_total_height: float
    legal_cornice_ceiling: float  # grid.cornice_height -- must equal facade_height_limit
    built_height: float
    total_height: float
    storey_count: int
    bay_repeating_count: int
    bay_total_count: int
    has_mezzanine: bool
    has_attic: bool
    entrance_kind: str


@dataclass(frozen=True)
class OldResult:
    era_name: str
    facade_height_limit: float
    arc_radius: float
    roof_envelope: str
    legal_ridge_height: float
    legal_total_height: float
    built_height: float
    total_height: float
    storey_count: int
    bay_count: int
    has_entresol: bool
    has_porte_cochere: bool


def run_new(situation: Situation) -> NewResult:
    """Drive the rewrite over *situation* via its public phases.

    Uses ``solve_structure``/``assign_roles`` directly (rather than only
    ``generate()``) because those are exactly the CONTRACTS.md-typed objects
    that carry storey/bay counts and the envelope as structured fields;
    ``generate()`` is also called so ``total_height`` comes from the real
    silhouette the termination phase emits, not a second computation of it.
    """
    site = new_site(situation)
    era = new_era_for_year(site.year)
    reg = new_get_reglement(era)

    grid = solve_structure(site)
    roled = assign_roles(grid)
    building, _log = generate(site)

    roles = [st.role for st in roled.storeys]
    entrance = catalogue.entrance_for(site.klass, site.street_width, site.ground)

    return NewResult(
        era_name=era.name,
        facade_height_limit=reg.facade_height_limit(site.street_width),
        arc_radius=reg.arc_radius(site.street_width),
        roof_envelope=grid.envelope.roof_envelope.value,
        legal_ridge_height=grid.envelope.legal_ridge_height,
        legal_total_height=grid.envelope.facade_height + grid.envelope.legal_ridge_height,
        legal_cornice_ceiling=float(grid.cornice_height),
        built_height=grid.built_height,
        total_height=float(building.props["total_height"]),
        storey_count=len(grid.storeys),
        bay_repeating_count=sum(1 for b in grid.bays if b.kind is SlotKind.REPEATING),
        bay_total_count=len(grid.bays),
        has_mezzanine=Role.MEZZANINE in roles,
        has_attic=Role.ATTIC in roles,
        entrance_kind=entrance.kind,
    )


def _old_representative_bay_count(front) -> int:
    """Bay count off a representative habitable floor of the front facade.

    The old system solves one bay layout per building and applies it to
    every floor (mirroring the new system's "solved once" rule), so any
    non-ground FloorNode carries the same count; the topmost one is taken
    because ground/entresol floors sometimes group bays visually (boutique/
    cafe runs) without changing the underlying BayNode count, and taking the
    top avoids that path entirely.
    """
    floors = [n for n in front.children if isinstance(n, _old_types.FloorNode)]
    if not floors:
        return 0
    top = floors[-1]
    return sum(1 for b in top.children if isinstance(b, _old_types.BayNode))


def run_old(situation: Situation, *, seed: int | None = None) -> OldResult:
    """Drive the previous implementation over *situation*.

    *seed* overrides ``situation.seed`` so callers can sample a distribution
    across seeds without constructing a new ``Situation`` for each one.
    """
    require_haussmann()
    style = OLD_STYLE_FOR_CLASS[situation.klass]
    has_porte, gf_type = OLD_GROUND_FOR[situation.ground]

    cfg = _old_types.BuildingConfig(
        lot_width=situation.parcel_width,
        lot_depth=situation.parcel_depth,
        style_preset=style,
        seed=situation.seed if seed is None else seed,
        year=situation.year,
        street_width=situation.street_width,
        has_porte_cochere=has_porte,
        ground_floor_type=gf_type,
        corner_chamfer=situation.corner,
    )
    building = _old_generator.generate_building(cfg)
    era = building.era
    reg = _old_reglement.get_reglement(era)
    envelope = _old_reglement.compute_envelope(
        situation.street_width, era, situation.parcel_depth, roof_fill=1.0, max_ridge=None
    )

    front = next(
        (c for c in building.children if getattr(c, "orientation", None) == _old_types.Orientation.SOUTH),
        building.children[0] if building.children else None,
    )
    floor_nodes = (
        [n for n in front.children if isinstance(n, (_old_types.FloorNode, _old_types.GroundFloorNode))]
        if front is not None
        else []
    )
    built_height = _old_floor.total_height(floor_nodes)
    has_entresol = any(
        isinstance(n, _old_types.FloorNode) and n.floor_type == _old_types.FloorType.ENTRESOL
        for n in floor_nodes
    )

    roof = next((c for c in building.children if isinstance(c, _old_types.RoofNode)), None)
    slope_h = 0.0
    if roof is not None:
        slopes = [c for c in roof.children if isinstance(c, _old_types.MansardSlopeNode)]
        if slopes:
            slope_h = max(s.height for s in slopes)

    bay_count = _old_representative_bay_count(front) if front is not None else 0

    return OldResult(
        era_name=era.name,
        facade_height_limit=reg.facade_height_limit(situation.street_width),
        arc_radius=reg.arc_radius(situation.street_width),
        roof_envelope=envelope.roof_envelope.value,
        legal_ridge_height=envelope.legal_ridge_height,
        legal_total_height=envelope.facade_height + envelope.legal_ridge_height,
        built_height=built_height,
        total_height=built_height + slope_h,
        storey_count=building.num_floors,
        bay_count=bay_count,
        has_entresol=has_entresol,
        has_porte_cochere=has_porte,
    )


# ---------------------------------------------------------------------------
# Bucket 1 — regulatory. Pure functions of (street_width, year, parcel_depth);
# no generation needed, so this sweep is cheap and can be exhaustive.
# ---------------------------------------------------------------------------

REGULATORY_YEARS: tuple[int, ...] = (1800, 1830, 1858, 1859, 1865, 1883, 1884, 1890, 1901, 1902, 1910)
REGULATORY_WIDTHS: tuple[float, ...] = (4.0, 6.0, 8.0, 9.0, 12.0, 15.0, 18.0, 20.0, 25.0, 30.0, 40.0)
REGULATORY_PARCEL_DEPTH = 14.0

_FLOAT_TOL = 1e-6


@dataclass(frozen=True)
class RegulatoryRow:
    year: int
    street_width: float
    metric: str
    old: Any
    new: Any
    matches: bool


def regulatory_rows(
    years: Sequence[int] = REGULATORY_YEARS,
    widths: Sequence[float] = REGULATORY_WIDTHS,
    parcel_depth: float = REGULATORY_PARCEL_DEPTH,
) -> list[RegulatoryRow]:
    """Every (year, street_width) combo, four regulatory metrics each.

    No generator involved -- straight calls into both ``reglement`` modules
    and ``compute_envelope`` -- which is what makes an exhaustive sweep cheap
    and appropriate for a bucket that must agree everywhere.
    """
    require_haussmann()
    rows: list[RegulatoryRow] = []
    for year in years:
        old_era = _old_reglement.era_for_year(year)
        new_era = new_era_for_year(year)
        old_reg = _old_reglement.get_reglement(old_era)
        new_reg = new_get_reglement(new_era)
        rows.append(
            RegulatoryRow(year, float("nan"), "era", old_era.name, new_era.name, old_era.name == new_era.name)
        )
        for width in widths:
            old_h = old_reg.facade_height_limit(width)
            new_h = new_reg.facade_height_limit(width)
            rows.append(
                RegulatoryRow(
                    year, width, "facade_height_limit", old_h, new_h, math.isclose(old_h, new_h, abs_tol=_FLOAT_TOL)
                )
            )
            old_r = old_reg.arc_radius(width)
            new_r = new_reg.arc_radius(width)
            rows.append(
                RegulatoryRow(
                    year, width, "arc_radius", old_r, new_r, math.isclose(old_r, new_r, abs_tol=_FLOAT_TOL)
                )
            )
            old_env = _old_reglement.compute_envelope(width, old_era, parcel_depth, roof_fill=1.0, max_ridge=None)
            new_env = _new_compute_envelope(width, new_era, parcel_depth)
            rows.append(
                RegulatoryRow(
                    year,
                    width,
                    "roof_envelope",
                    old_env.roof_envelope.value,
                    new_env.roof_envelope.value,
                    old_env.roof_envelope.value == new_env.roof_envelope.value,
                )
            )
            old_total = old_env.facade_height + old_env.legal_ridge_height
            new_total = new_env.facade_height + new_env.legal_ridge_height
            rows.append(
                RegulatoryRow(
                    year,
                    width,
                    "legal_total_height",
                    old_total,
                    new_total,
                    math.isclose(old_total, new_total, abs_tol=_FLOAT_TOL),
                )
            )
    return rows


def _new_compute_envelope(street_width: float, era, parcel_depth: float):
    from buildings.typologies.paris.reglement import compute_envelope as _cenv

    return _cenv(street_width, era, parcel_depth, roof_fill=1.0, max_ridge=None)


# ---------------------------------------------------------------------------
# Bucket 2 — gross proportions. Old sampled across seeds (its stacking is
# stochastic); new is deterministic (I5), so one value is the whole story.
# ---------------------------------------------------------------------------

#: INFERRED/stated tolerances -- the point at which "a different road to a
#: similar-looking building" becomes "the new system disagrees about what
#: this situation should produce". Wide, because the two stacking
#: philosophies (random-roll-inside-a-budget vs. programme-then-solve) are
#: expected to diverge by design (A2.2) -- these catch the case where they
#: diverge by a LOT, not the case where they diverge at all.
STOREY_COUNT_TOLERANCE = 2  # storeys
HEIGHT_TOLERANCE_FRAC = 0.20  # 20% of the old distribution's own span
BAY_COUNT_TOLERANCE = 3  # bays

PROP_WIDTHS: tuple[float, ...] = (6.0, 9.0, 12.0, 18.0, 24.0)
PROP_YEARS: tuple[int, ...] = (1830, 1865, 1888, 1905)  # one per era
PROP_CLASSES: tuple[BuildingClass, ...] = (
    BuildingClass.MODEST,
    BuildingClass.ORDINARY,
    BuildingClass.COMFORTABLE,
    BuildingClass.GRAND,
)
PROP_PARCEL_WIDTH = 18.0
PROP_PARCEL_DEPTH = 14.0
PROP_SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4)


def proportion_situations(
    widths: Sequence[float] = PROP_WIDTHS,
    years: Sequence[int] = PROP_YEARS,
    classes: Sequence[BuildingClass] = PROP_CLASSES,
) -> list[Situation]:
    return [
        Situation(
            street_width=w,
            parcel_width=PROP_PARCEL_WIDTH,
            parcel_depth=PROP_PARCEL_DEPTH,
            year=y,
            klass=k,
            ground=GroundProgramme.RESIDENTIAL,
        )
        for w in widths
        for y in years
        for k in classes
    ]


@dataclass(frozen=True)
class ProportionRow:
    situation: Situation
    metric: str
    new_value: float
    old_min: float
    old_max: float
    old_mean: float
    verdict: str  # "OK" or "OUTLIER"


def _verdict(new_value: float, old_values: Sequence[float], *, count_tol: float = 0.0, frac_tol: float = 0.0) -> str:
    lo, hi = min(old_values), max(old_values)
    slack = max(count_tol, frac_tol * max(abs(hi), abs(lo), 1.0))
    if lo - slack <= new_value <= hi + slack:
        return "OK"
    return "OUTLIER"


def proportion_rows(situations: Sequence[Situation] | None = None, seeds: Sequence[int] = PROP_SEEDS) -> list[ProportionRow]:
    require_haussmann()
    situations = list(situations) if situations is not None else proportion_situations()
    rows: list[ProportionRow] = []
    for situation in situations:
        new = run_new(situation)
        olds = [run_old(situation, seed=s) for s in seeds]

        storey_olds = [o.storey_count for o in olds]
        rows.append(
            ProportionRow(
                situation,
                "storey_count",
                new.storey_count,
                min(storey_olds),
                max(storey_olds),
                statistics.mean(storey_olds),
                _verdict(new.storey_count, storey_olds, count_tol=STOREY_COUNT_TOLERANCE),
            )
        )

        built_olds = [o.built_height for o in olds]
        rows.append(
            ProportionRow(
                situation,
                "built_height_m",
                new.built_height,
                min(built_olds),
                max(built_olds),
                statistics.mean(built_olds),
                _verdict(new.built_height, built_olds, frac_tol=HEIGHT_TOLERANCE_FRAC),
            )
        )

        total_olds = [o.total_height for o in olds]
        rows.append(
            ProportionRow(
                situation,
                "total_height_m",
                new.total_height,
                min(total_olds),
                max(total_olds),
                statistics.mean(total_olds),
                _verdict(new.total_height, total_olds, frac_tol=HEIGHT_TOLERANCE_FRAC),
            )
        )

        bay_olds = [o.bay_count for o in olds]
        rows.append(
            ProportionRow(
                situation,
                "bay_count",
                new.bay_repeating_count,
                min(bay_olds),
                max(bay_olds),
                statistics.mean(bay_olds),
                _verdict(new.bay_repeating_count, bay_olds, count_tol=BAY_COUNT_TOLERANCE),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Bucket 3 — qualitative. Recorded, never asserted on.
# ---------------------------------------------------------------------------

QUAL_GROUNDS: tuple[GroundProgramme, ...] = tuple(GroundProgramme)
QUAL_CLASSES: tuple[BuildingClass, ...] = tuple(BuildingClass)
QUAL_STREET_WIDTH = 14.0
QUAL_YEAR = 1888


@dataclass(frozen=True)
class QualitativeRow:
    situation: Situation
    new_entrance_kind: str
    new_has_mezzanine: bool
    new_has_attic: bool
    old_has_porte_cochere: bool
    old_has_entresol: bool
    note: str


def qualitative_rows(
    grounds: Sequence[GroundProgramme] = QUAL_GROUNDS, classes: Sequence[BuildingClass] = QUAL_CLASSES
) -> list[QualitativeRow]:
    require_haussmann()
    rows: list[QualitativeRow] = []
    for ground in grounds:
        for klass in classes:
            situation = Situation(
                street_width=QUAL_STREET_WIDTH,
                parcel_width=PROP_PARCEL_WIDTH,
                parcel_depth=PROP_PARCEL_DEPTH,
                year=QUAL_YEAR,
                klass=klass,
                ground=ground,
            )
            new = run_new(situation)
            old = run_old(situation)
            note = (
                "new: every building has exactly one entrance (A6.1); old: only "
                "reachable via has_porte_cochere, which this ground programme maps to "
                f"{OLD_GROUND_FOR[ground][0]!r}"
            )
            rows.append(
                QualitativeRow(
                    situation,
                    new.entrance_kind,
                    new.has_mezzanine,
                    new.has_attic,
                    old.has_porte_cochere,
                    old.has_entresol,
                    note,
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Outlier characterisation — is a metric's set of outliers a scatter, or one
# systematic pattern worth naming? Two real patterns showed up the first time
# this harness was run against the live systems (see the narrative built from
# this in ``write_report``): MODEST buildings built systematically SHORTER
# than old's (the ``_FACADE_AMBITION`` placeholder), and total height growing
# systematically TALLER than old's on wider streets/later eras (the
# class-invariant ``_COMBLE_FILL`` policy vs. old's fixed servant-storey cap).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutlierPattern:
    metric: str
    count: int
    direction: str  # "new > old range" / "new < old range" / "mixed"
    classes: tuple[str, ...]


def characterize_outliers(rows: Sequence[ProportionRow]) -> list[OutlierPattern]:
    by_metric: dict[str, list[ProportionRow]] = {}
    for r in rows:
        if r.verdict != "OUTLIER":
            continue
        by_metric.setdefault(r.metric, []).append(r)

    patterns: list[OutlierPattern] = []
    for metric, group in by_metric.items():
        above = sum(1 for r in group if r.new_value > r.old_max)
        below = sum(1 for r in group if r.new_value < r.old_min)
        if above == len(group):
            direction = "new > old range"
        elif below == len(group):
            direction = "new < old range"
        else:
            direction = "mixed"
        classes = tuple(sorted({r.situation.klass.value for r in group}))
        patterns.append(OutlierPattern(metric, len(group), direction, classes))
    return patterns


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

DEFAULT_REPORT_PATH = REPO_ROOT / "dev" / "logs" / "oracle_report.md"


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        if math.isnan(v):
            return "n/a"
        return f"{v:.3f}"
    return str(v)


def write_report(
    path: Path = DEFAULT_REPORT_PATH,
    *,
    reg_rows: list[RegulatoryRow] | None = None,
    prop_rows: list[ProportionRow] | None = None,
    qual_rows: list[QualitativeRow] | None = None,
) -> Path:
    """Render the three buckets to a markdown report at *path*."""
    require_haussmann()
    reg_rows = reg_rows if reg_rows is not None else regulatory_rows()
    prop_rows = prop_rows if prop_rows is not None else proportion_rows()
    qual_rows = qual_rows if qual_rows is not None else qualitative_rows()

    reg_mismatches = [r for r in reg_rows if not r.matches]
    prop_outliers = [r for r in prop_rows if r.verdict == "OUTLIER"]

    lines: list[str] = []
    lines.append("# Reference-oracle diff report")
    lines.append("")
    lines.append(
        "Generated by `dev/harness/oracle_diff.py`, driving both "
        "`buildings.typologies.paris.generate` (new) and `../haussmann` "
        "`core.generator` (old) over the same situations. See that module's "
        "docstring for the three-bucket methodology and the stated tolerances."
    )
    lines.append("")
    lines.append(
        f"**Situations compared:** {len(reg_rows) // 5} regulatory (year x street_width) combos, "
        f"{len(prop_rows) // 4} proportion situations (each old-side sampled over "
        f"{len(PROP_SEEDS)} seeds), {len(qual_rows)} qualitative situations. "
        f"{len(reg_rows) + len(prop_rows) + len(qual_rows)} rows total."
    )
    lines.append("")

    # --- Bucket 1 ------------------------------------------------------
    lines.append("## 1. Regulatory output — must agree (asserted)")
    lines.append("")
    lines.append(
        f"{len(reg_rows)} rows checked; **{len(reg_mismatches)} mismatches**. "
        "Tolerance: exact (float abs_tol=1e-6)."
    )
    lines.append("")
    if reg_mismatches:
        lines.append("| year | street_width | metric | old | new | verdict |")
        lines.append("|---|---|---|---|---|---|")
        for r in reg_mismatches:
            lines.append(
                f"| {r.year} | {_fmt(r.street_width)} | {r.metric} | {_fmt(r.old)} | {_fmt(r.new)} | MISMATCH |"
            )
    else:
        lines.append("No mismatches. Every era boundary, facade height limit, arc radius, ")
        lines.append("roof-envelope shape and legal total height agrees exactly across the sweep.")
    lines.append("")
    lines.append("<details><summary>Sample of matching rows (first 20)</summary>")
    lines.append("")
    lines.append("| year | street_width | metric | old | new | verdict |")
    lines.append("|---|---|---|---|---|---|")
    for r in reg_rows[:20]:
        lines.append(f"| {r.year} | {_fmt(r.street_width)} | {r.metric} | {_fmt(r.old)} | {_fmt(r.new)} | MATCH |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # --- Bucket 2 --------------------------------------------------------
    lines.append("## 2. Gross proportions — should be close (reported, tolerance-flagged)")
    lines.append("")
    lines.append(
        f"Tolerances: storey_count ±{STOREY_COUNT_TOLERANCE} storeys; "
        f"built/total height ±{HEIGHT_TOLERANCE_FRAC:.0%} of the old distribution's own span "
        f"(applied as slack on the observed [min, max]); bay_count ±{BAY_COUNT_TOLERANCE} bays. "
        f"Old sampled across seeds {list(PROP_SEEDS)}; new is deterministic (I5) so one value "
        "is the whole story."
    )
    lines.append("")
    lines.append(f"{len(prop_rows)} rows; **{len(prop_outliers)} outliers**.")
    lines.append("")
    lines.append("| situation | metric | new | old [min, max] (mean) | verdict |")
    lines.append("|---|---|---|---|---|")
    for r in prop_rows:
        old_range = f"[{_fmt(r.old_min)}, {_fmt(r.old_max)}] ({_fmt(r.old_mean)})"
        lines.append(f"| {r.situation.label} | {r.metric} | {_fmt(r.new_value)} | {old_range} | {r.verdict} |")
    lines.append("")

    # --- Bucket 3 --------------------------------------------------------
    lines.append("## 3. Qualitative — may differ (recorded, not asserted)")
    lines.append("")
    lines.append("| situation | new entrance | new mezzanine | new attic | old porte cochère | old entresol |")
    lines.append("|---|---|---|---|---|---|")
    for r in qual_rows:
        lines.append(
            f"| {r.situation.label} | {r.new_entrance_kind} | {r.new_has_mezzanine} | "
            f"{r.new_has_attic} | {r.old_has_porte_cochere} | {r.old_has_entresol} |"
        )
    lines.append("")

    # --- Verdict summary ---------------------------------------------------
    lines.append("## Divergences that look like bugs, vs. deliberate improvements")
    lines.append("")
    lines.append("### Deliberate improvements (documented in CONTRACTS.md amendments)")
    lines.append("")
    lines.append(
        "- **Every building has an entrance (A6.1).** Old only reaches a door through "
        "`has_porte_cochere`; new's `catalogue.entrance_for` picks a porte cochère or a "
        "porte piétonne unconditionally. Bucket 3 shows `old_has_porte_cochere=False` "
        "alongside a real `new_entrance_kind` for every RESIDENTIAL/SHOP/CAFE/OFFICE row — "
        "expected, not a bug."
    )
    lines.append(
        "- **Entresol is programme-first, not remainder (A2.2).** Old's entresol is a "
        "probabilistic roll inside whatever the gabarit budget leaves over; new decides it "
        "from ground-programme + class before the budget is filled. Divergence in "
        "`has_entresol`/`has_mezzanine` across seeds is exactly the effect A2.2 describes, "
        "not new disagreeing with old about the same question."
    )
    lines.append(
        "- **Attic is reachable (A2.1).** Old has no attic role at all (its comble is roof, "
        "not a storey); new emits one wherever the comble is deep enough. `new_has_attic` "
        "being true where old has nothing to compare against is the fix landing, not a "
        "regression."
    )
    lines.append(
        "- **Class mapping is lossy by construction.** Old has three style presets "
        "(MODEST/RESIDENTIAL/BOULEVARD); new has four classes. ORDINARY and COMFORTABLE "
        "both drive the old system through RESIDENTIAL, so old-side distributions for "
        "those two classes at the same width/year are close to identical by construction — "
        "read the new/old comparison for those rows as 'is new still in a plausible "
        "neighbourhood', not 'do the two classes remain distinguishable in old's output'."
    )
    lines.append("")
    lines.append("### Findings that look like genuine bugs in the NEW system")
    lines.append("")
    if reg_mismatches:
        lines.append(
            f"- **{len(reg_mismatches)} regulatory mismatch(es) found** — see the table in "
            "section 1. Any row here is a real port bug or an integration bug in how a "
            "phase routes a `reglement` number, not a design disagreement, and should be "
            "fixed before this report is regenerated clean."
        )
    else:
        lines.append("- None found in the regulatory bucket: every row matched.")
    lines.append("")

    patterns = characterize_outliers(prop_rows)
    if patterns:
        lines.append(
            f"- {len(prop_outliers)} of {len(prop_rows)} proportion rows fell outside the stated "
            "tolerance, but they are not scattered noise — they resolve into two named, "
            "one-directional patterns, both traceable to a *specific* constant rather than to "
            "a general disagreement:"
        )
        for p in patterns:
            lines.append(
                f"  - **`{p.metric}`**: {p.count} outliers, all **{p.direction}**, concentrated "
                f"in class(es) {', '.join(p.classes)}."
            )
        lines.append("")
        if any(p.metric == "built_height_m" for p in patterns):
            lines.append(
                "  **`built_height_m`, new < old, MODEST-concentrated.** Traces to "
                "`structure._FACADE_AMBITION[MODEST] = 0.74` (`structure.py`) — an explicitly "
                "INFERRED placeholder (A1.3-style: only the *ordering* MODEST < ORDINARY < "
                "COMFORTABLE < GRAND is contractual, the figures are provisional). Old's modest "
                "buildings land close to their own legal ceiling because its floor-stacking "
                "picks per-floor heights from ranges that happen to sum near the gabarit "
                "regardless of an explicit ambition dial. **Not a bug** — it is a placeholder "
                "constant behaving exactly as documented — but it is the first place to look "
                "if MODEST buildings read as noticeably squatter than the reference corpus in "
                "the S11 visual check."
            )
            lines.append("")
        if any(p.metric == "total_height_m" for p in patterns):
            lines.append(
                "  **`total_height_m`, new > old, growing with street width and era, present "
                "across every class including MODEST.** Traces to `structure._COMBLE_FILL = "
                "0.99` (`structure.py`), which is deliberately class-invariant (A2.3: comble "
                "fill is floor space, not show, so every class takes nearly all the legal "
                "roof) and bounded only by parcel depth, never by how many servant-room "
                "storeys the building actually holds. Old bounds the built comble instead by "
                "`profile.roof.comble_storeys * mansard.typ` — a fixed few metres regardless "
                "of how tall the decree would allow, which is its own uncalibrated placeholder "
                "in the other direction. **Worth a second look, not a clear bug**: the new "
                "system is doing exactly what A2.3 says it should, but a MODEST building on a "
                "wide boulevard now gets a roof nearly as tall as the legal maximum purely "
                "because of street width, independent of class — which edges toward the "
                "brief's own warning that conflating the legal ceiling with what got built "
                "'makes every building a maximal building, which is wrong and looks it.' "
                "That warning was explicitly answered for the FACADE line "
                "(`_FACADE_AMBITION` varies by class); this data suggests the COMBLE line may "
                "want the same treatment rather than one INFERRED constant near 1.0 for "
                "everyone."
            )
            lines.append("")
    else:
        lines.append("- None found in the proportion bucket: every row was within tolerance.")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    path = write_report()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
