"""``grow``: a parametric L-system run inside one shape's scope."""

from __future__ import annotations

import math
import textwrap

import pytest

from buildings.cga import Grammar, OutsideParent, Production, Scope, Shape, derive
from buildings.cga.lsystem import (
    Draw,
    GrowConflict,
    GrowError,
    Interpretation,
    LRule,
    LSystem,
    derive_string,
    grow,
    interpret_string,
    parse_modules,
    parse_pattern,
)
from buildings.cga.expr import Expr
from buildings.ir.serial import to_json
from buildings.rng import DecisionStream
from buildings.site import BuildingClass as K
from buildings.typologies.cairo.grammar import CairoSite, derive_cairo, generate_cairo
from buildings.typologies.common.rulefile import RuleFileError, load_style

FN = {"max": max, "min": min, "round": round}


def _no_names(name):
    raise KeyError(name)


def _rule(rid, pred, to, when=None, weight=None, left=None, right=None):
    symbol, formals = parse_pattern(pred)
    return LRule(
        rid, symbol, formals, parse_modules(to),
        when=Expr(when) if when else None,
        weight=Expr(weight) if weight is not None else None,
        left=parse_pattern(left) if left else None,
        right=parse_pattern(right) if right else None,
    )


def _system(axiom, rules, interpret=(), ignore=()):
    return LSystem("t", parse_modules(axiom), tuple(rules), {i.symbol: i for i in interpret}, frozenset(ignore))


def _grow(system, n, seed=0, stream=""):
    g = derive_string(system, n, params={}, lookup=_no_names, functions=FN, rng=DecisionStream(seed), stream=stream)
    return " ".join(str(m) for m in g.string), g


# --- syntax ------------------------------------------------------------------


def test_modules_parse_with_expression_arguments_and_branches():
    mods = parse_modules("A(x, max(1, y)) [ B ] + C(2)")
    assert [m.symbol for m in mods] == ["A", "[", "B", "]", "+", "C"]
    assert [a.src for a in mods[0].args] == ["x", "max(1, y)"]
    assert parse_pattern("Cell(a, b, p)") == ("Cell", ("a", "b", "p"))
    for bad in ("A [ B", "A ] B", "A(x", "A(,x)"):
        with pytest.raises(GrowError):
            parse_modules(bad)
    for bad in ("A B", "A(x + 1)", "A(x, x)"):
        with pytest.raises(GrowError):
            parse_pattern(bad)
    # Arguments are rule expressions: what a rule may not say, a module may not.
    with pytest.raises(GrowError):
        parse_modules("A(lambda: 1)")


# --- rewriting ---------------------------------------------------------------


def test_parametric_rules_rewrite_in_parallel_and_record_their_generation():
    s = _system("A(3)", [_rule("t.down", "A(n)", "B(n) A(n - 1)", when="n > 0")])
    text, g = _grow(s, 5)
    assert text == "B(3) B(2) B(1) A(0)"
    assert [m.born for m in g.string] == [1, 2, 3, 3]
    assert [m.by for m in g.string] == ["t.down"] * 4


def test_context_sensitive_rules_beat_context_free_ones_and_look_past_branches_and_ignored_symbols():
    s = _system(
        "B A I [ X ] A",
        [_rule("t.plain", "A", "P"), _rule("t.after_b", "A", "Q", left="B"), _rule("t.before_nothing", "X", "Y", right="A")],
        ignore=("I",),
    )
    text, _ = _grow(s, 1)
    # The first A follows B; the second A's left context skips the branch and
    # the ignored I and reaches the first A, so it is not after a B.
    assert text == "B Q I [ X ] P"
    # Right context never leaves the branch: X has nothing after it.


def test_stochastic_rules_draw_by_weight_from_the_seed_and_only_from_it():
    s = _system("F F F F F F F F", [_rule("t.a", "F", "a", weight="1"), _rule("t.b", "F", "b", weight="1")])
    first, g = _grow(s, 1, seed=3, stream="k")
    assert _grow(s, 1, seed=3, stream="k")[0] == first  # deterministic
    assert {_grow(s, 1, seed=k, stream="k")[0] for k in range(8)} != {first}  # the seed matters
    assert len(g.choices) == 8 and all("over" in c for c in g.choices)
    # A weight of zero is never drawn.
    never = _system("F F F F F F", [_rule("t.a", "F", "a", weight="1"), _rule("t.b", "F", "b", weight="0")])
    assert _grow(never, 1, seed=11)[0] == "a a a a a a"


def test_competing_rules_without_weights_raise_like_competing_productions():
    s = _system("F", [_rule("t.a", "F", "a"), _rule("t.b", "F", "b")])
    with pytest.raises(GrowConflict):
        _grow(s, 1)


def test_runaway_growth_is_refused():
    s = _system("F", [_rule("t.double", "F", "F F")])
    with pytest.raises(GrowError):
        _grow(s, 17)
    with pytest.raises(GrowError):
        _grow(s, 16)  # 65536 modules


# --- interpretation ----------------------------------------------------------


def _interp(symbol_formals, *steps):
    symbol, formals = parse_pattern(symbol_formals)
    return Interpretation(symbol, formals, tuple(steps))


def _draw(verb, **kw):
    fields = {k: (Expr(v) if isinstance(v, str) else [Expr(x) for x in v]) for k, v in kw.pop("fields").items()}
    return Draw(verb, fields=fields, **kw)


def test_cells_split_repeat_and_inset_and_branches_forget_their_changes():
    s = _system(
        "Sx [ Dot ] [ In [ Dot ] ] Rx(3) [ Dot ] Dot",
        [],
        [
            _interp("Sx", _draw("split", axis="x", fields={"weights": "[1, 3]"})),
            _interp("Rx(n)", _draw("repeat", axis="y", fields={"n": "n"})),
            _interp("In", _draw("inset", fields={"inset": "0.5"})),
            _interp("Dot", _draw("place", label="Dot", fields={"at": ["0", "0", "cw", "ch"]})),
        ],
    )
    marks = interpret_string(s, parse_modules_eval(s), Scope(0.0, 0.0, 4.0, 3.0), params={}, lookup=_no_names, functions=FN)
    got = [(m.scope.x, m.scope.y, m.scope.w, m.scope.h) for m in marks]
    assert got == [
        (0.0, 0.0, 1.0, 3.0),  # first part of the split
        (1.5, 0.5, 2.0, 2.0),  # second part, inset inside its branch
        (0.0, 0.0, 4.0, 1.0),  # the repeat draws its branch in each third
        (0.0, 1.0, 4.0, 1.0),
        (0.0, 2.0, 4.0, 1.0),
        (0.0, 0.0, 4.0, 3.0),  # the inset was forgotten at its ']'
    ]


def parse_modules_eval(system):
    return derive_string(system, 0, params={}, lookup=_no_names, functions=FN).string


def test_a_mark_outside_its_cell_is_refused():
    s = _system("Sx [ Big ] [ ]", [], [
        _interp("Sx", _draw("split", axis="x", fields={"weights": "[1, 1]"})),
        _interp("Big", _draw("place", label="Big", fields={"at": ["0", "0", "cw * 1.5", "ch"]})),
    ])
    with pytest.raises(OutsideParent):
        interpret_string(s, parse_modules_eval(s), Scope(0.0, 0.0, 2.0, 1.0), params={}, lookup=_no_names, functions=FN)


def test_lines_are_bars_when_square_to_the_cell_and_slants_otherwise():
    s = _system("L", [], [_interp("L",
        _draw("line", label="Bar", slant="Slant", fields={"line": ["0", "ch / 2", "cw", "ch / 2"], "width": "0.1"}),
        _draw("line", label="Bar", slant="Slant", fields={"line": ["0", "ch", "cw", "0"], "width": "0.1"}),
    )])
    bar, slant = interpret_string(s, parse_modules_eval(s), Scope(1.0, 1.0, 2.0, 1.0), params={}, lookup=_no_names, functions=FN)
    assert bar.label == "Bar" and (bar.scope.x, bar.scope.y, bar.scope.w, bar.scope.h) == (1.0, 1.45, 2.0, 0.1)
    assert slant.label == "Slant" and slant.attrs["direction"] == "falling" and slant.scope == Scope(1.0, 1.0, 2.0, 1.0)


# --- in a derivation ---------------------------------------------------------


def test_grow_inserts_traced_children_through_the_engine():
    s = _system("Q(2)", [_rule("t.quarter", "Q(n)", "Rx(2) [ Ry(2) [ Q(n - 1) ] ]", when="n > 0")], [
        _interp("Rx(k)", _draw("repeat", axis="x", fields={"n": "k"})),
        _interp("Ry(k)", _draw("repeat", axis="y", fields={"n": "k"})),
        _interp("Q(n)", _draw("place", label="Dot", fields={"at": ["cw / 4", "ch / 4", "cw / 2", "ch / 2"]})),
    ])

    def body(shape, d):
        grow(d, shape, s, generations=2, params={}, lookup=_no_names, functions=FN)

    g = Grammar("t", (Production("t.panel", "Panel", body),))
    panel, _ = derive(g, Shape("Panel", Scope(0.0, 0.0, 4.0, 4.0), "p"), DecisionStream(0))
    dots = panel.children
    assert len(dots) == 16 and {c.label for c in dots} == {"Dot"}
    assert all(panel.scope.contains(c.scope) for c in dots)
    assert len({c.id for c in dots}) == 16
    for c in dots:
        grown = [e for e in c.trace if e.inputs.get("lsystem") == "t"]
        assert grown and grown[0].inputs["generation"] == 2 and grown[0].rule == "t.quarter"
    assert any(e.rule == "t" and "2 generation" in e.detail for e in panel.trace)


_TOML = """
[style]
name = "growtest"
site = ["width", "seed"]
axiom = { w = "width", h = 2 }
describe = { rule = "growtest.style", detail = "'growtest'" }

[emit]
Dot = "kit.column"

[[production]]
id = "growtest.lot"
label = "Lot"
do = [ { grow = "growtest.grid", generations = "depth", params = { pad = "0.01" }, as = "growth", seed = "'house'" } ]

[[lsystem]]
id = "growtest.grid"
axiom = "Q(w, h)"
rules = [ { id = "growtest.halve", pred = "Q(a, b)", when = "a > 0.2", to = "Rx(2) [ Q(a / 2, b) ]" } ]
interpret = [
  { module = "Rx(k)", repeat = "x", n = "k" },
  { module = "Q(a, b)", place = "Dot", at = ["pad", "pad", "cw - 2 * pad", "ch - 2 * pad"], attrs = { order = "timber" } },
]
"""


def _style(tmp_path, text):
    p = tmp_path / "growtest.toml"
    p.write_text(textwrap.dedent(text))
    return load_style(p)


class _Site:
    def __init__(self, width, seed=0):
        self.width, self.seed = width, seed


def test_a_rule_file_grows_with_expressions_for_generations_and_params(tmp_path):
    style = _style(tmp_path, _TOML.replace('"depth"', '"3"'))
    lot, _ = style.derive(_Site(2.0))
    dots = [c for c in lot.children if c.label == "Dot"]
    assert len(dots) == 8
    assert lot.attrs["growth"]["generations"] == 3 and lot.attrs["growth"]["marks"] == 8
    building, _ = style.generate(_Site(2.0))
    assert to_json(style.generate(_Site(2.0))[0]) == to_json(building)
    columns = [n for n in building.children if n.kind == "column"]
    assert len(columns) == 8 and all(any(e.inputs.get("lsystem") == "growtest.grid" for e in n.trace) for n in columns)


def test_a_rule_file_refuses_a_bad_lsystem_when_it_is_loaded(tmp_path):
    with pytest.raises(RuleFileError, match="unknown function"):
        _style(tmp_path, _TOML.replace('"Rx(2) [ Q(a / 2, b) ]"', '"Rx(2) [ Q(evil(a), b) ]"'))
    with pytest.raises(RuleFileError, match="no \\[\\[lsystem\\]\\]"):
        _style(tmp_path, _TOML.replace('grow = "growtest.grid"', 'grow = "growtest.nothing"'))
    with pytest.raises(RuleFileError, match="unknown key"):
        _style(tmp_path, _TOML.replace('as = "growth"', 'as = "growth", colour = "red"'))
    with pytest.raises(RuleFileError, match="exactly one verb"):
        _style(tmp_path, _TOML.replace('repeat = "x", n = "k"', 'repeat = "x", n = "k", inset = "1"'))


# --- the Cairo mashrabiya ----------------------------------------------------


def _lattices(site):
    lot, _ = derive_cairo(site)
    return [s for s in lot.walk() if s.label == "Lattice"]


def test_every_cairo_lattice_is_grown_inside_its_screen_and_traced_to_the_lsystem():
    for site in (CairoSite(8.0, 1650, K.MODEST, seed=0), CairoSite(13.0, 1780, K.COMFORTABLE, seed=5)):
        lattices = _lattices(site)
        assert lattices
        for lat in lattices:
            assert lat.attrs["growth"]["lsystem"] == "cairo.mashrabiya"
            assert lat.children and all(lat.scope.contains(c.scope) for c in lat.children)
            for c in lat.children:
                assert any(e.inputs.get("lsystem") == "cairo.mashrabiya" and "generation" in e.inputs for e in c.trace)
    building, _ = generate_cairo(CairoSite(13.0, 1780, K.COMFORTABLE, seed=5))
    assert to_json(generate_cairo(CairoSite(13.0, 1780, K.COMFORTABLE, seed=5))[0]) == to_json(building)


def test_size_and_money_set_the_generations_and_the_seed_the_pattern():
    def oriel_generations(klass):
        lat = next(s for s in _lattices(CairoSite(14.0, 1700, klass, seed=0)) if "oriel" in s.id)
        return lat.attrs["growth"]["generations"]

    # A modest turner works to twice the mesh: a generation short.
    assert oriel_generations(K.MODEST) < oriel_generations(K.COMFORTABLE)
    # A bigger screen takes more generations to reach the same mesh.
    lats = [s for s in _lattices(CairoSite(14.0, 1700, K.COMFORTABLE, seed=0)) if s.attr("screen_gap") == 0.06]
    small = min(lats, key=lambda s: min(s.scope.w, s.scope.h))  # an oriel's panel, 0.6 m across
    large = max(lats, key=lambda s: min(s.scope.w, s.scope.h))  # the qa'a window, 1.2 m
    assert small.attrs["growth"]["generations"] < large.attrs["growth"]["generations"]
    # Across families, the seed chooses among the patterns.
    rules = set()
    for seed in range(8):
        for lat in _lattices(CairoSite(14.0, 1700, K.COMFORTABLE, seed=seed)):
            rules |= {c.split(" -> ")[1].split(" ")[0] for c in lat.attrs["growth"]["choices"]}
    assert {"cairo.mashrabiya.square_grid", "cairo.mashrabiya.maymuni"} <= rules
    assert {"cairo.mashrabiya.square_grid_under_a_wheel", "cairo.mashrabiya.maymuni_under_a_wheel"} & rules


# --- shaped cells, outlines and piercings ------------------------------------

from buildings.cga.lsystem import head_outline  # noqa: E402
from buildings.typologies.common.rulefile import _lsystem  # noqa: E402

FN2 = {**FN, "len": len}


def _area(pts):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:]))) / 2.0


def _grown(spec, scope, n=0, params=None):
    s = _lsystem({"id": "t", **spec}, "test")
    string = derive_string(s, n, params=params or {}, lookup=_no_names, functions=FN2).string
    return interpret_string(s, string, scope, params=params or {}, lookup=_no_names, functions=FN2)


def test_head_outline_is_the_renderers_head():
    from buildings.render.svg.elements import _head_outline

    for form in ("round", "pointed", "ogee"):
        ours, theirs = head_outline(1.0, 2.0, 0.9, 0.7, form), _head_outline(1.0, 2.0, 0.9, 0.7, form)
        assert len(ours) == len(theirs)
        assert [c for p in ours for c in p] == pytest.approx([c for p in theirs for c in p])


def test_an_arch_cell_is_outlined_by_its_head_and_a_cell_over_arches_by_their_extrados():
    light = _grown({"axiom": "L", "interpret": [{"module": "L", "do": [{"arch": "'ogee'", "rise": "0.75"}, {"outline": "Light"}]}]},
                   Scope(0.0, 0.0, 1.0, 3.0))
    (mark,) = light
    pts = mark.attrs["points"]
    assert pts[0] == pts[-1] and max(y for _x, y in pts) == pytest.approx(3.0)
    # The outline is the head's: the tip at the middle, the springing 0.75 down.
    assert (0.5, 3.0) in pts and (0.0, 2.25) in pts
    web = _grown({"axiom": "W", "interpret": [{"module": "W", "do": [
        {"over": "'pointed'", "span": "1.0", "pitch": "1.2", "count": "2", "rise": "0.8", "band": "0.1"},
        {"outline": "Web"}]}]}, Scope(0.0, 0.0, 2.2, 1.5))
    (mark,) = web
    pts = mark.attrs["points"]
    # Over the colonnette between the arches the web comes down to the springing.
    assert min(y for x, y in pts if 1.05 < x < 1.15) == pytest.approx(0.0)
    # Over each tip it stands on the extrados: the rise plus the band.
    assert min(y for x, y in pts if abs(x - 0.5) < 1e-6) == pytest.approx(0.9)
    with pytest.raises(GrowError, match="rise out of its cell"):
        _grown({"axiom": "W", "interpret": [{"module": "W", "over": "'ogee'", "span": "1.0", "rise": "2.0"}]}, Scope(0.0, 0.0, 1.0, 1.0))


def test_a_ring_places_round_cells_about_a_centre_with_their_angle_bound():
    marks = _grown({"axiom": "R [ F ]", "interpret": [
        {"module": "R", "ring": "4", "radius": "1.0", "size": "0.5", "start": "90"},
        {"module": "F", "place": "Foil", "at": ["0", "0", "cw", "ch"], "attrs": {"angle": "= angle", "radius": "= cr"}},
    ]}, Scope(-2.0, -2.0, 4.0, 4.0))
    assert [m.attrs["angle"] for m in marks] == [90.0, 180.0, 270.0, 360.0]
    assert [(round(m.scope.x + 0.25, 9), round(m.scope.y + 0.25, 9)) for m in marks] == [(0.0, 1.0), (-1.0, 0.0), (0.0, -1.0), (1.0, 0.0)]
    assert all(m.attrs["radius"] == 0.25 for m in marks)


_RING = {"axiom": "E [ R [ F ] H ]", "interpret": [
    {"module": "E", "do": [{"round": "1.0", "at": ["cw / 2", "ch / 2"]}, {"outline": "Ring"}]},
    {"module": "R", "ring": "4", "radius": "0.4", "size": "0.68"},
    {"module": "F", "pierce": "cr"},
    {"module": "H", "pierce": "0.26"},
]}


def test_an_outline_is_cut_by_its_piercings_into_one_simple_polygon_with_a_slit():
    (ring,) = _grown(_RING, Scope(0.0, 0.0, 2.0, 2.0))
    pts = ring.attrs["points"]
    assert pts[0] == pts[-1] == (1.0, 2.0)  # from the top of the rim
    # What is left is the disc less the quatrefoil: less than the disc less its
    # heart, more than the disc less the heart and four whole foils.
    assert math.pi * (1 - 4 * 0.34**2 - 0.26**2) < _area(pts) < math.pi * (1 - 0.26**2)
    # Sharp cusps between the foils, on the diagonals, nearer than the foils reach.
    reach = sorted(math.hypot(x - 1.0, y - 1.0) for x, y in pts if math.hypot(x - 1.0, y - 1.0) < 0.99)
    assert reach[-1] == pytest.approx(0.74, abs=1e-3) and reach[0] < 0.5
    # A single disc pierced about its centre: the annulus.
    (annulus,) = _grown({"axiom": "E [ H ]", "interpret": [
        {"module": "E", "do": [{"round": "1.0", "at": ["1", "1"]}, {"outline": "Ring"}]},
        {"module": "H", "pierce": "0.5"}]}, Scope(0.0, 0.0, 2.0, 2.0))
    assert _area(annulus.attrs["points"]) == pytest.approx(math.pi * 0.75, rel=0.01)


def test_an_opening_centred_on_an_edge_is_halved_by_it():
    # A round cell centred on its cell's left edge keeps the half inside.
    (half,) = _grown({"axiom": "E [ H ]", "interpret": [
        {"module": "E", "do": [{"round": "0.5", "at": ["0", "1"]}, {"outline": "Ring"}]},
        {"module": "H", "pierce": "0.25"}]}, Scope(0.0, 0.0, 1.0, 2.0))
    assert half.scope.x == pytest.approx(0.0) and half.scope.w == pytest.approx(0.5)
    assert _area(half.attrs["points"]) == pytest.approx(math.pi * (0.25 - 0.0625) / 2, rel=0.01)
    # A web pierced by a disc centred on its edge is bitten by it.
    (web,) = _grown({"axiom": "W [ H ]", "interpret": [
        {"module": "W", "outline": "Web"}, {"module": "H", "pierce": "0.5", "at": ["0", "1"]}]}, Scope(0.0, 0.0, 1.0, 2.0))
    assert _area(web.attrs["points"]) == pytest.approx(2.0 - math.pi * 0.25 / 2, rel=0.01)


def test_round_cells_fit_and_piercings_stay_inside_what_they_cut():
    # Fitted: shrunk from 1.0 until it clears the arch under it by 0.05.
    (eye,) = _grown({"axiom": "W [ E ]", "interpret": [
        {"module": "W", "over": "'round'", "span": "2.0", "rise": "1.0"},
        {"module": "E", "do": [{"round": "1.0", "at": ["cw / 2", "ch - 0.1 - r"], "fit": "0.05"}, {"outline": "Eye"}]}]},
        Scope(0.0, 0.0, 2.0, 2.5))
    r = eye.scope.w / 2.0
    assert r < 1.0 and 2.4 - 2 * r - 1.0 >= 0.05 - 1e-9 and 2.4 - 2 * (r + 0.01) - 1.0 < 0.05
    with pytest.raises(GrowError, match="no outline"):
        _grown({"axiom": "H", "interpret": [{"module": "H", "pierce": "0.1"}]}, Scope(0.0, 0.0, 1.0, 1.0))
    with pytest.raises(OutsideParent, match="breaks"):
        _grown({"axiom": "W [ H ]", "interpret": [{"module": "W", "outline": "Web"}, {"module": "H", "pierce": "0.6"}]},
               Scope(0.0, 0.0, 1.0, 1.0))
    with pytest.raises(GrowError, match="middle"):
        # Four foils that overlap in a ring round a middle none of them covers.
        _grown({"axiom": "W [ R [ F ] ]", "interpret": [{"module": "W", "outline": "Web"},
               {"module": "R", "ring": "4", "radius": "0.25", "size": "0.4"}, {"module": "F", "pierce": "cr"}]},
               Scope(0.0, 0.0, 1.0, 1.0))


def test_a_rule_file_checks_the_shaping_verbs_when_it_is_loaded(tmp_path):
    with pytest.raises(RuleFileError, match="unknown key"):
        _style(tmp_path, _TOML.replace('repeat = "x", n = "k"', 'ring = "k", radius = "1", size = "1", n = "k"'))
    with pytest.raises(RuleFileError, match="needs"):
        _style(tmp_path, _TOML.replace('repeat = "x", n = "k"', 'ring = "k", radius = "1"'))
    with pytest.raises(RuleFileError, match=r"'at' is \[x, y\]"):
        _style(tmp_path, _TOML.replace('repeat = "x", n = "k"', 'round = "k", at = ["0", "0", "1"]'))


# --- the Venetian tracery ----------------------------------------------------


def test_venetian_tracery_is_grown_with_half_oculi_against_the_jambs():
    from buildings.typologies.venice.grammar import PalazzoSite, derive_venice

    lot, _ = derive_venice(PalazzoSite(19.0, 1430, K.GRAND, seed=4))
    (tracery,) = [s for s in lot.walk() if s.label == "Tracery"]
    n = tracery.attr("lights_n")
    stones = [c for c in tracery.children if c.label == "TraceryStone"]
    assert len(stones) == 2 * (n + 1)  # a web and a ring per oculus, n - 1 whole and two halves
    rules = {e.rule for c in stones for e in c.trace}
    assert {"venice.tracery.halved_by_the_left_jamb", "venice.tracery.halved_by_the_right_jamb", "venice.tracery.oculus"} <= rules
    rings = [c for c in stones if c.trace[-1].detail.split(": ")[1].startswith("Eye")]
    halves = [c for c in rings if c.scope.w < 0.6 * max(r.scope.w for r in rings)]
    assert len(halves) == 2 and {round(h.scope.x, 6) for h in halves} & {round(tracery.scope.x, 6)}
    # Generation 3 on a grand house's broad lights; 2 elsewhere.
    grew = next(e for e in tracery.trace if e.inputs.get("lsystem") == "venice.tracery")
    assert grew.inputs["generations"] == 3
    lot2, _ = derive_venice(PalazzoSite(16.0, 1430, K.COMFORTABLE, seed=1))
    t2 = next(s for s in lot2.walk() if s.label == "Tracery")
    assert next(e for e in t2.trace if e.inputs.get("lsystem") == "venice.tracery").inputs["generations"] == 2
