"""The absolute / proportional / regulatory split (I3).

Conflating these three kinds is, per the brief, the error that makes
procedural buildings look like toys. A door is as tall as a person whether
the building is grand or modest — it is `Abs`, and it never scales, because
it is the ruler the eye measures everything else against. Bay width and
ornament density are `Prop` — they move together as one coherent shift when
ambition changes. A 6 m minimum balcony height is `Reg` — a number in a law,
unrelated to money or the body, that only changes when the law does.

**The test for classifying a number:** ask what would have to change in the
world for it to change.
- "People would have to be a different size" -> `Abs`
- "The owner would have to be richer" -> `Prop`
- "The law would have to be rewritten" -> `Reg`

`scale_for_class` is the *only* place `Prop` quantities are scaled. Call it
nowhere else, or the "one coherent shift" the brief asks for degrades into a
multiplier sprinkled through the rules, applied twice in one place and
forgotten in another.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from buildings.site import BuildingClass


class Kind(Enum):
    ABSOLUTE = "absolute"  # human body / object that must pass. Never scales.
    PROPORTIONAL = "proportional"  # composition and money. Scales.
    REGULATORY = "regulatory"  # a number in a law. Changes on a date.


# Rigidity ordering for mixed-kind arithmetic: ABSOLUTE > REGULATORY > PROPORTIONAL.
_RIGIDITY: Mapping[Kind, int] = {
    Kind.PROPORTIONAL: 0,
    Kind.REGULATORY: 1,
    Kind.ABSOLUTE: 2,
}


def _most_rigid(a: Kind, b: Kind) -> Kind:
    return a if _RIGIDITY[a] >= _RIGIDITY[b] else b


@dataclass(frozen=True)
class Quantity:
    """A dimension that knows what kind of number it is.

    `why` is the reason for an ABSOLUTE or PROPORTIONAL value, and the
    citation for a REGULATORY one — always populated, because "someone will
    eventually scale a doorway, and nobody will be able to say why the result
    looks wrong" is exactly the failure this field exists to prevent.

    Arithmetic between two `Quantity` of different `Kind` yields a `Quantity`
    of the *most rigid* kind of the two operands (ABSOLUTE > REGULATORY >
    PROPORTIONAL) — e.g. an ABSOLUTE door height plus a PROPORTIONAL lintel
    allowance is itself ABSOLUTE: the combination is only as flexible as its
    least flexible part.

    Scalar `*`/`/` (by a bare `int`/`float`, not another `Quantity`) is
    permitted only on PROPORTIONAL quantities (A1.1). On ABSOLUTE or
    REGULATORY it raises `TypeError` rather than silently scaling — that
    silent scale is exactly how a doorway ends up 35% too tall with no
    grep-able trace of why. Route rigid-quantity scaling through
    `scale_for_class`, which documents itself as a no-op for those kinds.
    """

    value: float
    kind: Kind
    why: str

    def __float__(self) -> float:
        return float(self.value)

    def scaled(self, factor: float) -> Quantity:
        """PROPORTIONAL scales. ABSOLUTE and REGULATORY return self
        unchanged — they are rigid by definition, and stretching them to
        make an arithmetic problem come out even is precisely the move that
        destroys legible scale."""
        if self.kind is Kind.PROPORTIONAL:
            return Quantity(self.value * factor, self.kind, self.why)
        return self

    @property
    def rigid(self) -> bool:
        """True for ABSOLUTE and REGULATORY: these can never absorb slack
        in the fitting solver."""
        return self.kind is Kind.ABSOLUTE or self.kind is Kind.REGULATORY

    def __add__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(
            self.value + other.value,
            _most_rigid(self.kind, other.kind),
            f"({self.why}) + ({other.why})",
        )

    def __radd__(self, other: object) -> Quantity:
        return self.__add__(other)

    def __sub__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        return Quantity(
            self.value - other.value,
            _most_rigid(self.kind, other.kind),
            f"({self.why}) - ({other.why})",
        )

    def __neg__(self) -> Quantity:
        return Quantity(-self.value, self.kind, self.why)

    def __mul__(self, factor: object) -> Quantity:
        if isinstance(factor, Quantity):
            return Quantity(
                self.value * factor.value,
                _most_rigid(self.kind, factor.kind),
                f"({self.why}) * ({factor.why})",
            )
        if isinstance(factor, (int, float)):
            self._require_scalable("*")
            return Quantity(self.value * factor, self.kind, self.why)
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, divisor: object) -> Quantity:
        if isinstance(divisor, Quantity):
            return Quantity(
                self.value / divisor.value,
                _most_rigid(self.kind, divisor.kind),
                f"({self.why}) / ({divisor.why})",
            )
        if isinstance(divisor, (int, float)):
            self._require_scalable("/")
            return Quantity(self.value / divisor, self.kind, self.why)
        return NotImplemented

    def _require_scalable(self, op: str) -> None:
        """A1.1: scalar `*`/`/` on a rigid (ABSOLUTE/REGULATORY) quantity is
        exactly how a doorway gets scaled with no grep-able marker — the
        failure the brief warns about. Only PROPORTIONAL may be scaled by a
        bare number; anything rigid must go through `scale_for_class`, which
        is a documented no-op for rigid kinds rather than a silent multiply."""
        if self.kind is not Kind.PROPORTIONAL:
            raise TypeError(
                f"cannot scale a {self.kind.value.upper()} quantity ({op} by a "
                f"bare number) — {self.kind.value} quantities never scale; "
                "use scale_for_class(quantity, klass), which is a documented "
                "no-op for ABSOLUTE/REGULATORY kinds, instead of multiplying "
                "or dividing directly"
            )


def Abs(value: float, why: str) -> Quantity:
    return Quantity(value, Kind.ABSOLUTE, why)


def Prop(value: float, why: str) -> Quantity:
    return Quantity(value, Kind.PROPORTIONAL, why)


def Reg(value: float, source: str) -> Quantity:
    if not source.strip():
        raise ValueError("Reg quantity requires a non-blank citation source")
    return Quantity(value, Kind.REGULATORY, source)


# INFERRED (A1.3): these scale factors for the PROPORTIONAL family, keyed by
# ambition, are invented placeholders. They appear in neither the brief nor
# any source document — unlike chronology's dates, which are sourced, these
# are a provisional, monotonically increasing ramp pending real design input
# from a later stage (chronology / composition). A later stage should
# REPLACE them with sourced or deliberately-designed figures rather than
# inherit them as if they were a finding. Only two things are contractual
# here: the monotonic ordering across classes, and that ABSOLUTE/REGULATORY
# quantities are always a no-op under this transform. The numbers themselves
# are not.
_CLASS_SCALE: Mapping[BuildingClass, float] = {
    BuildingClass.MODEST: 0.85,
    BuildingClass.ORDINARY: 1.00,
    BuildingClass.COMFORTABLE: 1.15,
    BuildingClass.GRAND: 1.35,
}


def scale_for_class(q: Quantity, klass: BuildingClass) -> Quantity:
    """The ONE place proportional scaling happens. Called nowhere else.

    Delegates to `Quantity.scaled`, which is itself a no-op for ABSOLUTE and
    REGULATORY quantities — so calling this on a rigid quantity is always
    safe and never silently scales something it shouldn't.
    """
    return q.scaled(_CLASS_SCALE[klass])
