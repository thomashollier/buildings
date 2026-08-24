"""The colour palette (S8).

Ported from ``../haussmann/backends/svg.py::COLORS`` and
``svg_elements.py::_C``, merged into one table. Nothing here is a decision —
it is paint, and every kind of paint below is keyed by a name the IR already
put on a node (``opening_type``, ``surround_kind``, ``ironwork`` family names,
``keystone_kind``, ``socle`` treatment, roof material), never by date, class or
role. Which key gets used is decided upstream; this module only says what
colour that key gets drawn in.
"""

from __future__ import annotations

COLORS: dict[str, str] = {
    "wall": "#E8DCC8",
    "wall_ground": "#D4C9B5",
    "window": "#4A6078",
    "window_frame": "#3A4A5A",
    "surround_bare_band": "#D8CCBA",
    "surround_moulded_architrave": "#C8B8A0",
    "surround_pedimented": "#C0AE92",
    "surround_irregular": "#CBBFA8",
    "balcony_rail": "#2C2C2C",
    "balcony_floor": "#5A5A5A",
    "cornice": "#C0B49E",
    "cornice_stroke": "#6B5B4C",
    "string_course": "#D8CDB8",
    "roof_zinc": "#7A8088",
    "roof_slate": "#5C6268",
    "roof_slope": "#6A7078",
    "roof_seam_light": "#9BA1A8",
    "roof_seam_dark": "#565C63",
    "roof_break": "#40464C",
    "dormer": "#888E96",
    "dormer_window": "#4A6078",
    "chimney": "#A09080",
    "keystone": "#B8A890",
    "ornament": "#C0B098",
    "door": "#5A4030",
    "door_dark": "#4A3020",
    "door_panel": "#6B5040",
    "door_glass": "#5A6878",
    "shop_door": "#6B5040",
    "pier": "#DDD4C4",
    "pier_edge": "#DDD4C4",
    "pier_line": "#C0B4A0",
    "mullion": "#B0A080",
    "sill": "#C8B8A0",
    "lintel": "#C8B8A0",
    "recess": "#B8AE9A",
    "recess_stroke": "#A09888",
    "handle": "#888888",
    "iron": "#3A3A3A",
    "iron_light": "#555555",
    "socle_flat_incised_refends": "#CFC4AF",
    "socle_raised_bossage": "#C7B99F",
    "socle_picturesque_rustication": "#BDAD8E",
    "shopfront_glass": "#4A6078",
    "shopfront_signage": "#C8B8A0",
    "awning": "#8B2020",
    "sky": "#D6E8F0",
    "ground": "#8A9A7A",
    "outline": "#4A4038",
}
