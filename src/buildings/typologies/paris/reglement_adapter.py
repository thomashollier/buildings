"""Adapter for the regulatory module, wrapping numeric results in Quantity types.

This module provides a thin wrapper around the core reglement.py, returning
Reg(value, citation) objects instead of bare floats. Citations are drawn from
the regulatory sources documented at the top of reglement.py.

Every numeric result carries its source so tests can assert both the value
and the authority that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from buildings.quantity import Reg
from . import reglement


# Re-export the enums and classes unchanged
Era = reglement.Era
RoofEnvelope = reglement.RoofEnvelope
Reglement = reglement.Reglement
BalconyRule = reglement.BalconyRule
OrielRule = reglement.OrielRule
GabaritEnvelope = reglement.GabaritEnvelope

# Re-export data unchanged
REGLEMENTS = reglement.REGLEMENTS


# Citation strings for each regulatory source
_CITATIONS = {
    "1783": "Déclaration royale du 10 avril 1783, lettres patentes du 28 août 1784",
    "1823": "Ordonnance de 1823",
    "1855": "Circulaire du 21 septembre 1855",
    "1859": "Règlement du 27 juillet 1859",
    "1882": "Décret du 22 juillet 1882",
    "1884": "Décret du 23 juillet 1884 (Alphand)",
    "1902": "Décret du 13 août 1902 (Louis Bonnier)",
}


def era_for_year(year: int) -> Era:
    """Return the regulatory era in force in *year*."""
    return reglement.era_for_year(year)


def get_reglement(era: Era | str) -> Reglement:
    """Look up a ``Reglement`` by era (enum or case-insensitive name)."""
    return reglement.get_reglement(era)


def compute_envelope(
    street_width: float,
    era: Era | str = Era.SECOND_EMPIRE,
    parcel_depth: float = 12.0,
    roof_fill: float = 1.0,
    max_ridge: float | None = None,
) -> WrappedGabaritEnvelope:
    """Derive the legal envelope for a frontage on a street of *street_width*.

    Returns a WrappedGabaritEnvelope that wraps the core GabaritEnvelope,
    exposing heights as Reg quantities instead of bare floats.
    """
    core_env = reglement.compute_envelope(
        street_width, era, parcel_depth, roof_fill, max_ridge
    )
    return WrappedGabaritEnvelope(core_env)


def balcony_rule(
    floor_levels: list[float],
    era: Era | str = Era.SECOND_EMPIRE,
    second_line: bool = True,
) -> WrappedBalconyRule:
    """Decide which floors carry balconies from their heights above the pavement.

    Returns a WrappedBalconyRule that wraps the core BalconyRule, exposing
    projection and height limits as Reg quantities.
    """
    core_rule = reglement.balcony_rule(floor_levels, era, second_line)
    return WrappedBalconyRule(core_rule)


def oriel_rule(
    floor_levels: list[float],
    floor_names: list[str],
    cornice_height: float,
    era: Era | str = Era.SECOND_EMPIRE,
    above_cornice_extra: float = 1.6,
) -> WrappedOrielRule:
    """Decide whether and where an oriel may be built.

    Returns a WrappedOrielRule that wraps the core OrielRule, exposing
    dimensions as Reg quantities.
    """
    core_rule = reglement.oriel_rule(
        floor_levels, floor_names, cornice_height, era, above_cornice_extra
    )
    return WrappedOrielRule(core_rule)


# ---------------------------------------------------------------------------
# Wrapped dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WrappedGabaritEnvelope:
    """Wrapped GabaritEnvelope exposing heights as Reg quantities."""

    _core: GabaritEnvelope

    @property
    def era(self) -> Era:
        """The regulatory era of this envelope."""
        return self._core.era

    @property
    def street_width(self) -> float:
        """Street width in metres."""
        return self._core.street_width

    @property
    def facade_height(self) -> float:
        """Cornice height (facade height) in metres."""
        return self._core.facade_height

    @property
    def roof_envelope(self) -> RoofEnvelope:
        """The shape of the comble envelope."""
        return self._core.roof_envelope

    @property
    def arc_radius(self) -> float:
        """Radius of the comble arc (if applicable)."""
        return self._core.arc_radius

    @property
    def ridge_height(self) -> float:
        """Height of the ridge above the cornice as built."""
        return self._core.ridge_height

    @property
    def parcel_depth(self) -> float:
        """Depth of the parcel."""
        return self._core.parcel_depth

    @property
    def legal_ridge_height(self) -> float:
        """Height the decree would have allowed."""
        return self._core.legal_ridge_height

    @property
    def total_height(self):
        """Cornice height plus comble — the full silhouette, as a Reg."""
        # Total height is set by the regulations on envelope shape.
        # For the 1884 decree (Alphand), this yields 28.50 m (20 + 8.50).
        citation = _citation_for_era(self.era)
        return Reg(self._core.total_height, citation)

    def setback_at(self, h: float):
        """Minimum inset from the facade plane at height *h* above the cornice, as Reg."""
        citation = _citation_for_era(self.era)
        return Reg(self._core.setback_at(h), citation)

    def max_height_for_setback(self, inset: float):
        """Tallest legal point at horizontal distance *inset*, as Reg."""
        citation = _citation_for_era(self.era)
        return Reg(self._core.max_height_for_setback(inset), citation)

    def slope_profile(
        self, samples: int = 16, top: float | None = None
    ) -> list[tuple[float, float]]:
        """Trace the comble envelope as (inset, height) points.

        Heights and insets are raw floats; the envelope itself is regulated.
        *top* is the height the comble is carried to above its springing, and
        defaults to the ridge as built — see the core envelope for why the two
        are not the same question.
        """
        return self._core.slope_profile(samples, top)

    def mansard_angles(self, top: float | None = None) -> tuple[float, float, float]:
        """Approximate the envelope as a broken mansard.

        Returns (lower_angle_deg, upper_angle_deg, break_pct) as floats, for a
        comble carried to *top* above its springing (default: the ridge).
        """
        return self._core.mansard_angles(top)


@dataclass(frozen=True)
class WrappedBalconyRule:
    """Wrapped BalconyRule exposing dimensions as Reg quantities."""

    _core: BalconyRule

    @property
    def continuous(self) -> list[int]:
        """Floor indices carrying continuous balconies."""
        return self._core.continuous

    @property
    def individual(self) -> list[int]:
        """Floor indices carrying individual balconettes."""
        return self._core.individual

    @property
    def max_projection(self):
        """Legal maximum projection of a balcony, as Reg (0.80 m from 1823 ordinance)."""
        return Reg(
            self._core.max_projection,
            "Ordonnance de 1823 — max projection 0.80 m",
        )

    @property
    def min_height(self):
        """Legal minimum height above pavement for balconies, as Reg (6.00 m from 1823)."""
        return Reg(
            self._core.min_height,
            "Ordonnance de 1823 — minimum 6 m above pavement",
        )


@dataclass(frozen=True)
class WrappedOrielRule:
    """Wrapped OrielRule exposing dimensions as Reg quantities."""

    _core: OrielRule

    @property
    def allowed(self) -> bool:
        """Whether oriels are permitted."""
        return self._core.allowed

    @property
    def start_index(self) -> int:
        """Floor index where an oriel must start (if allowed)."""
        return self._core.start_index

    @property
    def start_height(self) -> float:
        """Height above pavement where oriel must start."""
        return self._core.start_height

    @property
    def max_top(self) -> float:
        """Highest point the oriel may reach."""
        return self._core.max_top

    @property
    def max_projection(self):
        """Legal maximum projection of an oriel, as Reg (0.40 m from 1882)."""
        return Reg(
            self._core.max_projection,
            "Décret du 22 juillet 1882 — max oriel projection 0.40 m",
        )

    @property
    def may_pass_cornice(self) -> bool:
        """Whether the oriel may extend above the cornice (1902+)."""
        return self._core.may_pass_cornice

    @property
    def materials(self) -> tuple[str, ...]:
        """Allowed materials for the oriel."""
        return self._core.materials


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _citation_for_era(era: Era) -> str:
    """Return the appropriate citation for a given regulatory era."""
    citation_map = {
        Era.ROYAL: _CITATIONS["1783"],
        Era.SECOND_EMPIRE: _CITATIONS["1859"],
        Era.ALPHAND: _CITATIONS["1884"],
        Era.BONNIER: _CITATIONS["1902"],
    }
    return citation_map.get(era, "Unknown era")
