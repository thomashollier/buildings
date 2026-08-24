from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from buildings.site import BuildingClass, GroundProgramme, SiteContext


def _make_site(**overrides: object) -> SiteContext:
    defaults = dict(
        street_width=18.0,
        parcel_width=12.0,
        parcel_depth=20.0,
        year=1875,
        klass=BuildingClass.ORDINARY,
        ground=GroundProgramme.SHOP,
    )
    defaults.update(overrides)
    return SiteContext(**defaults)  # type: ignore[arg-type]


def test_site_context_frozen() -> None:
    site = _make_site()
    with pytest.raises(dataclasses.FrozenInstanceError):
        site.street_width = 30.0  # type: ignore[misc]


def test_site_context_hashable() -> None:
    site = _make_site()
    d = {site: "a"}
    assert d[site] == "a"
    assert hash(site) == hash(_make_site())


def test_site_context_equality_by_value() -> None:
    assert _make_site() == _make_site()
    assert _make_site(street_width=20.0) != _make_site()


def test_site_context_defaults() -> None:
    site = _make_site()
    assert site.corner is False
    assert site.seed == 0


def test_building_class_members() -> None:
    assert {c.value for c in BuildingClass} == {"modest", "ordinary", "comfortable", "grand"}


def test_ground_programme_members() -> None:
    assert {g.value for g in GroundProgramme} == {
        "residential",
        "shop",
        "cafe",
        "carriage",
        "office",
    }


def test_site_module_never_imports_random_or_rng() -> None:
    """I2: a building never samples a block-level fact — enforced here by
    static analysis of the module that defines the situation itself."""
    src_path = Path(__file__).resolve().parents[2] / "src" / "buildings" / "site.py"
    tree = ast.parse(src_path.read_text())
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".")[0])
            imported_names.update(alias.name for alias in node.names)
    forbidden = {"random", "rng", "DecisionStream"}
    assert not (imported_names & forbidden), imported_names & forbidden


def test_site_context_has_no_sampling_methods() -> None:
    """SiteContext exposes only its declared fields — no method that could
    sample a value at construction or access time."""
    field_names = {f.name for f in dataclasses.fields(SiteContext)}
    public_attrs = {
        name
        for name in dir(SiteContext)
        if not name.startswith("_") and name not in field_names
    }
    assert public_attrs == set()
