"""The Paris grammar builds what the phase pipeline builds, byte for byte, and
its sub-parts can be varied without disturbing their neighbours.

The full 3000-situation sweep is ``dev/harness/cga_equivalence.py``; this file
holds the canonical situations and the locality claims.
"""

from __future__ import annotations

import dataclasses
from collections import Counter

import pytest

from buildings.cga import Layer
from buildings.ir.serial import to_json
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.compose import ORDER_OVERRIDE
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.grammar import derive_paris, generate_cga
from buildings.typologies.paris.qualify.context import Properties
from buildings.typologies.paris.roles import Role

SITES = [
    SiteContext(20.0, 12.0, 14.0, 1865, BuildingClass.COMFORTABLE, GroundProgramme.SHOP, seed=1865),
    SiteContext(30.0, 22.0, 18.0, 1868, BuildingClass.GRAND, GroundProgramme.CARRIAGE, seed=3),
    SiteContext(12.0, 9.0, 12.0, 1890, BuildingClass.MODEST, GroundProgramme.SHOP, seed=4),
    SiteContext(14.0, 12.0, 13.0, 1865, BuildingClass.ORDINARY, GroundProgramme.RESIDENTIAL, seed=6),
    SiteContext(18.0, 15.0, 16.0, 1905, BuildingClass.COMFORTABLE, GroundProgramme.CAFE, corner=True, seed=9),
    SiteContext(8.0, 7.0, 10.0, 1835, BuildingClass.ORDINARY, GroundProgramme.OFFICE, seed=11),
]


@pytest.mark.parametrize("site", SITES, ids=lambda s: f"{s.klass.value}-{s.year}-{s.street_width:g}m")
def test_the_grammar_builds_the_pipelines_building(site):
    assert to_json(generate_cga(site)[0]) == to_json(generate(site)[0])


def test_the_window_is_a_tree_of_parts():
    lot, _ = derive_paris(SITES[0])
    labels = Counter(s.label for s in lot.walk())
    for label in ("Facade", "Roof", "Storey", "Cell", "Pier", "LightBay", "Light", "Breast", "Lintel"):
        assert labels[label] > 0, label
    for shape in lot.walk():
        if shape.parent is not None and shape.label != "Facade":
            assert shape.parent.scope.contains(shape.scope), shape


def test_roles_are_read_off_the_stack():
    lot, _ = derive_paris(SITES[0])
    facade = lot.children[0]
    roles = [s.attrs["role"] for s in facade.children]
    assert roles[0] is Role.BASE
    assert roles.count(Role.PRINCIPAL) == 1


def _noble(shape) -> bool:
    return shape.attr("role", None) is Role.PRINCIPAL


def test_an_override_on_the_noble_floor_changes_only_its_openings():
    def round_heads(ctx, rng):
        return Properties({"opening_head": "round"}, rule="variation.round_heads")

    refine = lambda g: g.with_override(  # noqa: E731
        "Cell", Layer("noble", ORDER_OVERRIDE, (round_heads,)), where=_noble
    )
    for site in SITES[:3]:
        before = {n.id: n for n in walk(generate_cga(site)[0])}
        after = {n.id: n for n in walk(generate_cga(site, refine=refine)[0])}
        noble = {i for i, n in before.items() if n.kind == "storey" and n.props["role"] == "principal"}
        assert before.keys() == after.keys()
        changed = [
            i
            for i in before
            if dataclasses.replace(before[i], children=()) != dataclasses.replace(after[i], children=())
        ]
        assert changed
        for i in changed:
            assert after[i].kind == "opening" and "/".join(i.split("/")[:2]) in noble
            assert after[i].props["head"] == "round"
            assert any(e.rule == "variation.round_heads" for e in after[i].trace)


def test_a_look_tweak_on_one_label_touches_only_that_label():
    def plain(g):
        base = g.interpreters["Keystone"]
        return g.with_interpreter(
            "Keystone",
            lambda s, below, d: [
                dataclasses.replace(n, props={**n.props, "keystone_kind": "plain"})
                for n in base(s, below, d)
            ],
        )

    site = SITES[1]
    before = {n.id: n for n in walk(generate_cga(site)[0])}
    after = {n.id: n for n in walk(generate_cga(site, refine=plain)[0])}
    kinds = {
        after[i].kind
        for i in before
        if dataclasses.replace(before[i], children=()) != dataclasses.replace(after[i], children=())
    }
    assert kinds == {"keystone"}


def test_an_axis_override_reaches_every_floor_of_that_axis_and_no_other():
    def no_keystone(ctx, rng):
        return Properties({"keystone_present": False}, rule="variation.plain_axis")

    def entrance_axis(shape):
        slot = shape.attr("slot", None)
        return shape.label != "Storey" and slot is not None and slot.name in catalogue.ENTRANCE_SLOT_NAMES

    site = SITES[1]
    before = [n for n in walk(generate_cga(site)[0]) if n.kind == "keystone"]
    after = [
        n
        for n in walk(
            generate_cga(
                site,
                refine=lambda g: g.with_override(
                    "Cell", Layer("axis", ORDER_OVERRIDE, (no_keystone,)), where=entrance_axis
                ),
            )[0]
        )
        if n.kind == "keystone"
    ]
    removed = {n.id for n in before} - {n.id for n in after}
    assert removed and len({i.split("/")[2] for i in removed}) == 1
