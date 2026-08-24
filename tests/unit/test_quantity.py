from __future__ import annotations

import pytest

from buildings.quantity import Abs, Kind, Prop, Quantity, Reg, scale_for_class
from buildings.site import BuildingClass


def test_constructors_set_kind() -> None:
    a = Abs(2.0, "door height, human body")
    p = Prop(3.0, "bay width, composition")
    r = Reg(0.80, "1823 ordonnance, projection limit")
    assert a.kind is Kind.ABSOLUTE
    assert p.kind is Kind.PROPORTIONAL
    assert r.kind is Kind.REGULATORY


def test_reg_empty_source_raises() -> None:
    with pytest.raises(ValueError):
        Reg(1.0, "")


def test_reg_whitespace_only_source_raises() -> None:
    # A1.2: the guard must be `if not source.strip()`, not just falsiness.
    with pytest.raises(ValueError):
        Reg(6.0, "   ")
    with pytest.raises(ValueError):
        Reg(6.0, "\t\n")


def test_class_scale_factors_documented_as_inferred() -> None:
    # A1.3: the class scale factors are an invented placeholder, not a
    # sourced finding -- like chronology marks inferred dates, the module
    # source must mark them INFERRED so a later stage knows to replace
    # rather than inherit them.
    import inspect

    from buildings import quantity

    source = inspect.getsource(quantity)
    marker_index = source.index("_CLASS_SCALE: Mapping")
    preceding_comment = source[:marker_index]
    assert "INFERRED" in preceding_comment


def test_float_conversion() -> None:
    assert float(Abs(2.1, "x")) == 2.1


def test_scaled_absolute_and_regulatory_unchanged() -> None:
    a = Abs(2.0, "door")
    r = Reg(0.8, "1823 ordonnance")
    assert a.scaled(2.0) == a
    assert r.scaled(2.0) == r


def test_scaled_proportional_scales() -> None:
    p = Prop(3.0, "bay width")
    scaled = p.scaled(1.5)
    assert scaled.value == pytest.approx(4.5)
    assert scaled.kind is Kind.PROPORTIONAL


def test_rigid_property() -> None:
    assert Abs(1.0, "x").rigid is True
    assert Reg(1.0, "y").rigid is True
    assert Prop(1.0, "z").rigid is False


@pytest.mark.parametrize(
    "kind_a,kind_b,expected",
    [
        (Kind.ABSOLUTE, Kind.PROPORTIONAL, Kind.ABSOLUTE),
        (Kind.PROPORTIONAL, Kind.ABSOLUTE, Kind.ABSOLUTE),
        (Kind.ABSOLUTE, Kind.REGULATORY, Kind.ABSOLUTE),
        (Kind.REGULATORY, Kind.PROPORTIONAL, Kind.REGULATORY),
        (Kind.PROPORTIONAL, Kind.REGULATORY, Kind.REGULATORY),
        (Kind.ABSOLUTE, Kind.ABSOLUTE, Kind.ABSOLUTE),
        (Kind.PROPORTIONAL, Kind.PROPORTIONAL, Kind.PROPORTIONAL),
    ],
)
def test_addition_yields_most_rigid_kind(kind_a: Kind, kind_b: Kind, expected: Kind) -> None:
    q1 = Quantity(1.0, kind_a, "a")
    q2 = Quantity(2.0, kind_b, "b")
    result = q1 + q2
    assert result.kind is expected
    assert result.value == pytest.approx(3.0)


def test_subtraction_yields_most_rigid_kind() -> None:
    q1 = Quantity(5.0, Kind.PROPORTIONAL, "a")
    q2 = Quantity(2.0, Kind.ABSOLUTE, "b")
    result = q1 - q2
    assert result.kind is Kind.ABSOLUTE
    assert result.value == pytest.approx(3.0)


def test_scalar_multiplication_preserves_kind() -> None:
    p = Prop(2.0, "bay")
    result = p * 3
    assert result.kind is Kind.PROPORTIONAL
    assert result.value == pytest.approx(6.0)
    assert (3 * p).value == pytest.approx(6.0)


def test_scalar_division_on_proportional_preserves_kind() -> None:
    p = Prop(6.0, "bay")
    result = p / 2
    assert result.kind is Kind.PROPORTIONAL
    assert result.value == pytest.approx(3.0)


# --- A1.1: scalar * and / on a rigid (ABSOLUTE/REGULATORY) quantity must
# raise, not silently scale. This is the I3 hole named in Amendment 1:
# `Abs(2.60, "a carriage must pass") * 1.35` used to return an ABSOLUTE 3.51
# -- a scaled doorway with no grep-able marker that it happened.


@pytest.mark.parametrize(
    "make",
    [lambda: Abs(2.60, "a carriage must pass"), lambda: Reg(6.0, "1823 ordonnance")],
    ids=["absolute", "regulatory"],
)
def test_scalar_multiplication_on_rigid_quantity_raises(make) -> None:
    q = make()
    with pytest.raises(TypeError, match="scale_for_class"):
        q * 1.35
    with pytest.raises(TypeError, match="scale_for_class"):
        1.35 * q


@pytest.mark.parametrize(
    "make",
    [lambda: Abs(2.60, "a carriage must pass"), lambda: Reg(6.0, "1823 ordonnance")],
    ids=["absolute", "regulatory"],
)
def test_scalar_division_on_rigid_quantity_raises(make) -> None:
    q = make()
    with pytest.raises(TypeError, match="scale_for_class"):
        q / 2.0


def test_rigid_scalar_error_names_the_kind() -> None:
    with pytest.raises(TypeError, match="ABSOLUTE"):
        Abs(2.60, "a carriage must pass") * 1.35
    with pytest.raises(TypeError, match="REGULATORY"):
        Reg(6.0, "1823 ordonnance") * 1.35


def test_quantity_quantity_multiplication_still_legal_for_rigid_kinds() -> None:
    # A1.1 only restricts *scalar* (bare number) arithmetic. Quantity *
    # Quantity, whatever the kinds, is unaffected -- it already goes through
    # the most-rigid-wins rule and carries its own `why`.
    a = Abs(2.0, "door")
    r = Reg(3.0, "law")
    result = a * r
    assert result.kind is Kind.ABSOLUTE
    assert result.value == pytest.approx(6.0)


def test_negation_preserves_kind() -> None:
    a = Abs(2.0, "x")
    assert (-a).value == pytest.approx(-2.0)
    assert (-a).kind is Kind.ABSOLUTE


def test_scale_for_class_only_touches_proportional() -> None:
    p = Prop(3.0, "bay width")
    a = Abs(2.0, "door")
    r = Reg(0.8, "1823 ordonnance")

    grand = scale_for_class(p, BuildingClass.GRAND)
    modest = scale_for_class(p, BuildingClass.MODEST)
    assert grand.value > modest.value

    assert scale_for_class(a, BuildingClass.GRAND) == a
    assert scale_for_class(r, BuildingClass.GRAND) == r


def test_scale_for_class_monotonic_across_classes() -> None:
    p = Prop(1.0, "bay width")
    ordered = [
        scale_for_class(p, k).value
        for k in (
            BuildingClass.MODEST,
            BuildingClass.ORDINARY,
            BuildingClass.COMFORTABLE,
            BuildingClass.GRAND,
        )
    ]
    assert ordered == sorted(ordered)
    assert len(set(ordered)) == len(ordered)


def test_quantity_equality_compares_all_fields() -> None:
    assert Abs(1.0, "door") == Abs(1.0, "door")
    assert Abs(1.0, "door") != Abs(1.0, "window")
    assert Abs(1.0, "door") != Prop(1.0, "door")
