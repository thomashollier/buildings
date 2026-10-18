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
  column(rows, key) every_other(items) sin cos pi()`;
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

## What stays in Python

- **The engine and the shared kit:** window anatomy and IR writers.
- **Drawings a file names by writer:** Amsterdam's gable outline (step, neck,
  bell), the Victorian false-front gable, turret cone and stoop, Normandy's
  braces and gable, Kyoto's lattice, the Corbusian pavilion screen, the Art
  Deco spire. These are outlines drawn around shapes the rules placed, not
  decisions.
- **The measured Paris generator.** By design, it reads Daly through its own
  pipeline. `haussmann.toml` is the rule-file Paris.

The locality guarantees are the engine's, so they hold for rule files
unchanged. A rule can write only its own shape, and a part must stay inside
its parent unless its label is a declared overhang. Scoped overrides
(`with_override`, `with_interpreter`) apply to a rule-file style exactly as to
any other.
