# Rule files

A style can be written as a TOML file instead of a Python module. The file
says how each shape is split (`[[production]]`) and what each shape is given
(`[[rule]]`). It is loaded by `typologies/common/rulefile.py` into the same
`Grammar` a hand-written module builds, and derived by the same engine.

Every style is a rule file: Amsterdam, Chicago, Art Deco, Georgian, Kyoto,
Modernist, Normandy, SoHo, Venice, Victorian, and Paris (`haussmann.toml`).
Each of the first ten was checked byte for byte against its Python original
before the Python was replaced, refusals included:

| Style | Situations | | Style | Situations |
|---|---:|---|---|---:|
| Georgian | 144 | | Chicago | 120 |
| Kyoto | 120 | | Art Deco | 80 |
| Modernist | 120 | | Amsterdam | 96 |
| Venice | 96 | | SoHo | 448 |
| Victorian | 240 | | Normandy | 120 |

All identical. The module beside each file holds only its site type, the
drawings the file names by writer, and `generate_*` / `derive_*`. Helpers that
tests use (`gable_form`, `victorian_type`, `tiers_for`, `recipe_for`) are
read back from a derivation, so the rule file is the only statement of them.

Paris has a rule file too, `paris/haussmann.toml` (`typologies/paris/rules.py`).
Unlike the four above it is **not** a port. The measured generator stays as it
is, with its Daly figures and its 3000-case reference. The rule file writes
the Haussmann building the way the other styles are written: the 1783, 1859
and 1884 height steps as tables, class as an ambition, storeys tapering and
bays fitted, and the vocabulary laid on by rules. It agrees with the measured
generator on shape and differs in detail.
`python3 dev/harness/soho_sheet.py OUT_DIR --paris` draws the two side by side.
A test holds it to the decree: the stone never rises above the legal cornice.

## Two kinds of string

- **Geometry and conditions are always expressions:** `at`, `size`, `budget`,
  `when`, `let`, `repeat`, `each`.
- **Values in `set` and `attrs` are literals unless they start with `=`.** So
  `opening_type = "window"` is the word *window*, and
  `light_height = "= h - sill - 0.45"` is computed.

## Sections

```toml
[style]
name = "georgian"
site = ["width", "year", "klass", "seed"]   # site fields made available as names
axiom = { w = "width", h = 40 }             # the Lot's scope
overhangs = ["Cornice"]                     # labels allowed outside their parent
describe = { rule = "georgian.terrace_house", phase = "structure",
             detail = "f'Georgian terrace house, {width:.1f} m, {year}'" }

[lot_props]                                 # extra props on the building node
year = "= year"

[params]                                    # named numbers, lists, tables
window_w = 1.05
floors = [ { name = "ground", h = 3.5, ratio = 1.75 }, ... ]

[emit]                                      # labels written by a named writer
Lattice = "kyoto.lattice"

[[layer]]                                   # rule layers and their order
name = "base"
order = 0
```

## Productions

```toml
[[production]]
id = "georgian.storey"           # the rule id every shape it makes is traced to
label = "Storey"                 # which shapes it expands
when = "role != 'parapet'"       # optional guard
priority = 0                     # optional; equal priorities that both match raise
doc = "..."                      # the summary the trace quotes
let = { centre = "w * 0.4" }     # optional names for the body
do = [ ...operations... ]
```

| Operation | Does |
|---|---|
| `{ split = "x", parts = [ {label, size, name, attrs, slot} ... ] }` | Cuts the shape into consecutive parts. The sizes must add up. `slot = "bay"` / `"end"` marks a part as a window bay or a wall end. A part may be `{ repeat = "list", ... }`, with `item` and `i` bound and `{n}` as its position in the name. |
| `{ split = "x", by = "rhythm" }` | Cuts by a fitted run stored earlier, on this shape or an ancestor. |
| `{ fit = "x", end = "end", bay = "bay", as = "rhythm", max_bays = 5 }` | Sizes a run with the fitting solver. `end` and `bay` are expressions giving `[min, preferred, max]`, usually a param's name. `budget` defaults to the shape's extent. |
| `{ insert = "Cornice", at = [x, y, w, h], name = "cornice", attrs = {...} }` | Adds a child that does not partition its parent. |
| `{ each = "joints(grid, x)", do = [...] }` | Repeats operations with `item` and `i` bound. |
| `{ set = {...} }`, `{ let = {...} }` | Writes the shape in hand; binds names for later operations. |
| `{ call = "kit.split_cell_around_its_light" }` | Runs a named Python production: the shared window anatomy. |
| `{ refuse = "message" }` | Declines a situation the style does not model (with a `when`), raising `Refused`, a `ValueError`. |
| `{ grow = "lsystem.id", generations = "n", params = {...} }` | Grows a `[[lsystem]]` inside the shape: see "Growing ornament" below. |

Any operation may carry its own `when`.

## Rules

```toml
[[rule]]
id = "georgian.base.the_window_of_its_floor"
label = "Cell"
layer = "base"
specificity = 0                  # within a layer, higher wins; a tie raises
when = "is_bay() and floor != 'parapet'"
let = { height = "min(window_w * ratio, h - 0.3)" }
set = { opening_type = "window", light_height = "= height" }
```

## Names and functions

A name resolves to the first of these that has it:

1. a local (`let`, `item`, `i`);
2. the shape itself: `x y w h`, `index` (among all its siblings), `nth` and
   `count` (among siblings with the same label), `label`, `parent` (the
   parent's scope);
3. a `[params]` entry;
4. an attribute of the shape or of the nearest ancestor that has it. This is
   how a cell reads its storey's `role`, or a site field such as `year`.

Functions:

- arithmetic and lists: `min max abs round len sum fsum float int range
  column(rows, key) every_other(items) sin cos pi() sqrt log2 ceil floor`;
- regulation and proportion: `step(table, value)` (a step table read the way
  a decree is), `stepping(start, step, floor)` (a setback law's widths),
  `geometric(first, ratio, n)` (storeys that taper);
- where a shape stands: `is_bay() is_first_bay() is_last_bay()
  is_middle_bay() is_last(label) has(name) in_parent(label) index_of(label)
  child(label)`;
- runs and frames: `joints(parts, start) starts(sizes, start)
  bay_centres(parts, start) bay_spans(parts, start) bay_axes(id)
  frame_lines(parts, start, width, ends) column_lines(parts, start, width)
  frame_posts(x, w, spacing, post, light, last) size_of(part)`.

The expression language is Python expression syntax, checked before it is run.
It allows arithmetic, comparisons, `and` / `or` / `not`, `a if c else b`,
literals, lists and tuples, indexing, `item.h` on tables, and f-strings. It
allows no imports, lambdas, comprehensions or attribute access beyond that.
When the file is loaded, the loader refuses:

- an unknown function name;
- an unknown section or key, which would otherwise be silently ignored;
- an attribute that shares its name with a parameter. A name resolves to the
  parameter first, so the attribute would be written and never read. This is
  exactly the mistake converting Amsterdam produced, before the check existed.

## Growing ornament: `grow` and `[[lsystem]]`

Productions place things; they do not grow them. Self-similar ornament (a
lattice, tracery) used to be drawn by a Python writer around a shape the
rules placed. `grow` lets a rule file grow it instead: a production hands
**one shape's scope** to a parametric L-system, which rewrites a string of
modules for some generations and is then drawn as **nested cells** inside
that scope. The engine is in `src/buildings/cga/lsystem.py`.

```toml
[[production]]
id = "cairo.lattice"
label = "Lattice"
do = [ { grow = "cairo.mashrabiya",            # the [[lsystem]] id
         generations = "3 + halvings",         # an expression
         params = { bar = "lattice_spindle", side = "min(w, h)", halvings = "max(0, round(log2(side / 0.09)) - 2)" },
         seed = "role",                        # optional: the random stream's key (default: the shape's id)
         as = "growth",                        # optional: store a summary attribute
         name = "g" } ]                        # optional: child ids are <shape>/g0, g1, ...

[[lsystem]]
id = "cairo.mashrabiya"
axiom = "Screen(w, h)"
ignore = []                                    # symbols context matching looks past
rules = [
  { id = "cairo.mashrabiya.framed", pred = "Screen(a, b)", to = "Frame Inset [ Body(a, b) ]" },
  { id = "...square_grid", pred = "Body(a, b)", when = "b <= 1.6 * a", weight = 2, to = "Field(a, b, 0)" },
  { id = "...maymuni",     pred = "Body(a, b)", when = "b <= 1.6 * a", weight = 1, to = "Field(a, b, 1)" },
  { id = "...quartered",   pred = "Cell(a, b, p)", when = "min(a, b) > 2.4 * bead", to = "Rx(2) [ Ry(2) [ Cell(a / 2, b / 2, p) ] ]" },
  # context: { pred = "A", left = "B(x)", right = "C", to = "..." }
]
interpret = [
  { module = "Rx(n)", repeat = "x", n = "n" },
  { module = "Inset", inset = "frame" },
  { module = "Cell(a, b, p)", do = [
      { line = ["0", "ch / 2", "cw", "ch / 2"], width = "bar", straight = "Spindle", slant = "Slant", attrs = { order = "timber" } },
      { place = "Bead", at = ["cw / 2 - bead / 2", "ch / 2 - bead / 2", "bead", "bead"], attrs = { order = "timber" } },
  ] },
]
```

**Modules.** `Name(expr, ...)` or a one-character symbol (`+`, `-`, ...),
and `[` `]` for a branch. Arguments in the axiom and in successors are rule
expressions (the same whitelisted language, checked when the file loads);
they see the rule's formal parameters, the grow's `params`, then the grown
shape's names (`w`, `h`, attributes up the tree, `[params]`).

**Rewriting.** Every module is rewritten in parallel, each generation. Of the
rules whose predecessor (symbol and arity), `left`/`right` context and `when`
match, context-sensitive rules beat context-free ones. If more than one is
left, all must carry a `weight` and one is drawn from the site's seed at a
path naming the L-system, the `seed` key, the generation, the symbol and its
occurrence: deterministic, and independent of every other decision. Several
matches without weights raise `GrowConflict` (a tie is a defect, as between
productions). A module no rule matches is copied. Left context looks past
whole branches and out of its own; right context stays in its branch.
Limits: 16 generations, 50 000 modules, 20 000 marks.

**Interpretation.** The state is a cell, starting as the grown shape's scope.
Per symbol, `interpret` gives one step or a `do` list of steps:

| Step | Does |
|---|---|
| `{ split = "x", weights = "[a, b]" }` | cuts the cell by weights; each following `[ ... ]` draws in the next part |
| `{ repeat = "y", n = "k" }` | cuts the cell into `k` equal parts; the following `[ ... ]` draws once in each |
| `{ inset = "d" }` or `"[l, b, r, t]"` | shrinks the cell (forgotten at the branch's `]`) |
| `{ place = "Label", at = [x, y, w, h], attrs = {...} }` | a rectangle, in cell-local metres |
| `{ line = [x0, y0, x1, y1], width = "t", straight = "Bar", slant = "Slant" }` | a bar square to the cell (`straight`), or a diagonal across its box (`slant`, with `direction` rising or falling) |
| `{ over = "form", span = "s", rise = "r", pitch = "p", count = "k", start = "x", spring = "y", band = "b", finial = "f" }` | the cell stands over a row of `k` arches (`form` round, pointed or ogee, as the renderer turns them), `s` wide at pitch `p` from `x`, springing at `y` (default 0) and rising `r`, their stone band `b` and fleuron `f` included: its floor becomes their extrados |
| `{ arch = "form", rise = "r" }` | the cell is an arch: its ceiling becomes the head over its full width, springing `r` below its top |
| `{ round = "r", at = [cx, cy], fit = "c" }` | the cell becomes a disc of radius `r` about `(cx, cy)`; with `fit`, `r` shrinks by 1 cm until the disc clears the cell's floor and ceiling by `c` (`at` sees the trial `r`) |
| `{ ring = "n", radius = "d", size = "s", start = "deg" }` | `n` round cells `s` across, set about the cell's centre at distance `d` from angle `deg` (default 90, the top); the following `[ ... ]` draws once in each, with `angle` bound |
| `{ outline = "Label", attrs = {...} }` | the cell's own shape (with its profile, or round) as a polygon mark, cut by every `pierce` made after it in its branch |
| `{ pierce = "r", at = [cx, cy] }` | cuts a disc (default: about the cell's centre) out of the nearest `outline` drawn before it in its branch or an enclosing one |
| `{ polygon = "Label", points = "[[x, y], ...]", attrs = {...} }` | a polygon in cell-local metres |

Any step may carry `when` and `each` (with `item` and `i` bound). Names in a
step: `cw` and `ch` (the cell's size), `cr` in a round cell (its radius),
names its cell binds (`angle`), the module's formal parameters, then as
above. A `[` with no pending part draws in a copy of the cell. Parts cut from
a profiled cell keep the profile over their own width.

**Outlines and piercings.** An outline is drawn where it was made, once the
string is interpreted, with every piercing of it cut out: piercings that
overlap open as one (a quatrefoil: four foils round a heart), which must be
star-shaped about the middle of their centres, and must stay inside the
outline (`OutsideParent`) -- except that one centred on the outline's left
or right edge is a bite out of that edge, and a round outline centred on the
edge of the rectangle it was made in is halved by it (a half oculus against
a jamb). Each outline is emitted as one simple polygon (an inner opening is
reached by a slit from the top), its `points` in the mark's attributes;
`[emit] Label = "grow.stone"` draws it as stone standing in front of the
wall, and what it leaves open shows whatever is behind it.

**What it guarantees.** Every mark becomes a child shape of the grown one,
inserted by the engine, so the engine's `OutsideParent` check applies; a mark
must also lie inside the cell its module draws in. Each child's trace has the
engine's `insert` entry and one naming the L-system, the rule that wrote its
module and the generation it was written in; the grown shape carries one
entry for the whole growth (generations, the final string, every stochastic
choice and what it beat). The children's labels are written by whatever
`[emit]` names (`kit.column` for timber, `grow.slant` for a diagonal brace,
`grow.stone` for an outline), so nothing new reaches the renderer.

The Venetian Gothic tracery (`venice.tracery` in `venice.toml`) is grown with
these: the band over a polifora stands `over` its arches and is cut at their
tips; over every colonnette an oculus (an `outline` pierced by a `round`
eye, itself outlined and pierced by a `ring` of foils round a heart), and
against each jamb half of one -- a context rule, `Jamb < Oculus` -- with a
third generation drawing the foils out into a cusped quatrefoil on a grand
house's broad lights.

## What stays in Python

- **The engine and the shared kit:** window anatomy and IR writers.
- **Drawings a file names by writer:** Amsterdam's gable outline (step, neck,
  bell), the Victorian false-front gable, turret cone and stoop, Normandy's
  braces and gable, Kyoto's lattice (Cairo's mashrabiya and Venice's tracery are grown, above), the Corbusian pavilion screen, the Art
  Deco spire. These are outlines drawn around shapes the rules placed, not
  decisions.
- **The measured Paris generator.** By design, it reads Daly through its own
  pipeline. `haussmann.toml` is the rule-file Paris.

The locality guarantees are the engine's, so they hold for rule files
unchanged. A rule can write only its own shape, and a part must stay inside
its parent unless its label is a declared overhang. Scoped overrides
(`with_override`, `with_interpreter`) apply to a rule-file style exactly as to
any other.
