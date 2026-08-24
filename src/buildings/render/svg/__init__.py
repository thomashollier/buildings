"""SVG rendering (S8): ``render(node, ...) -> str`` per CONTRACTS.md, plus a
contact sheet for the fuzz corpus. See ``render.py`` for the entry point and
its docstring for what "the renderer decides nothing arguable" means here.
"""

from __future__ import annotations

from buildings.render.svg.contact_sheet import render_contact_sheet
from buildings.render.svg.render import render, render_block

__all__ = ["render", "render_block", "render_contact_sheet"]
