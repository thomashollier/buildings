"""The pinned canonical Second Empire situations (Amendment 9's "lock the
canonical case" instruction).

Four named ``SiteContext`` values, chosen to cover the shapes of building the
operator asked to see solid before anything branches out: an ordinary
mid-block immeuble on a typical Haussmann boulevard, a grand one on a wide
avenue (wide enough to hit the 1859 decree's 20 m facade ceiling — see
``test_second_empire_proportions.py``'s cornice-flatness test), a modest one
on a narrow commercial street (narrow enough that it never qualifies for a
carriage entrance — ``_CARRIAGE_STREET_MINIMUM`` is 12.0 m and this sits right
at it with a shop ground floor, so it is the pedestrian-door, no-entresol-easily
case), and a corner.

Every seed is a fixed literal, chosen once and never regenerated arbitrarily —
changing a seed here is exactly the kind of "intentional change" the golden
master's ``UPDATE_SECOND_EMPIRE_GOLDENS`` env var exists to make visible.

This module is imported by both the golden-master test
(``test_second_empire_canonical.py``) and the proportion sweep
(``test_second_empire_proportions.py``) so the two never describe the
canonical case in two different words.
"""

from __future__ import annotations

from buildings.site import BuildingClass, GroundProgramme, SiteContext

__all__ = ["SITUATIONS"]

SITUATIONS: dict[str, SiteContext] = {
    # An ordinary immeuble, mid-block, on a typical ~20 m Second Empire
    # boulevard. The plain, most-common case: residential ground floor, no
    # corner, well inside every regulatory step.
    "midblock_ordinary_20m_boulevard": SiteContext(
        street_width=20.0,
        parcel_width=14.0,
        parcel_depth=18.0,
        year=1865,
        klass=BuildingClass.ORDINARY,
        ground=GroundProgramme.RESIDENTIAL,
        corner=False,
        seed=18650001,
    ),
    # A grand building on a wide (>20 m) avenue -- wide enough to clear the
    # 1859 decree's 20 m facade-height step, which is exactly the situation
    # Daly's own grandest plates (avenue des Champs-Élysées) were drawn on.
    "grand_30m_avenue": SiteContext(
        street_width=30.0,
        parcel_width=18.0,
        parcel_depth=22.0,
        year=1865,
        klass=BuildingClass.GRAND,
        ground=GroundProgramme.RESIDENTIAL,
        corner=False,
        seed=18650002,
    ),
    # A modest building over a shop, on a narrow street. 12.0 m sits exactly
    # at ``_CARRIAGE_STREET_MINIMUM`` and MODEST is not in ``_CARRIAGE_CLASSES``
    # either, so this is doubly a pedestrian-door case -- the commonest Paris
    # entrance, on the commonest kind of street.
    "modest_12m_street_shop": SiteContext(
        street_width=12.0,
        parcel_width=10.0,
        parcel_depth=14.0,
        year=1865,
        klass=BuildingClass.MODEST,
        ground=GroundProgramme.SHOP,
        corner=False,
        seed=18650003,
    ),
    # A corner building: its own short chamfer facade, a shop ground floor,
    # comfortable class -- inside ``_CARRIAGE_CLASSES`` so it also exercises
    # the porte-cochère path at a middling street width.
    "corner_comfortable_18m_shop": SiteContext(
        street_width=18.0,
        parcel_width=13.0,
        parcel_depth=16.0,
        year=1865,
        klass=BuildingClass.COMFORTABLE,
        ground=GroundProgramme.SHOP,
        corner=True,
        seed=18650004,
    ),
}
