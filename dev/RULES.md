# Rule files

A style can be written as a TOML file instead of a Python module. The file
says how each shape is split (`[[production]]`) and what each shape is given
(`[[rule]]`). It is loaded by `typologies/common/rulefile.py` into the same
`Grammar` a hand-written module builds, and derived by the same engine.

Four styles are now rule files: `georgian/georgian.toml`, `kyoto/kyoto.toml`,
`modernist/modernist.toml` and `venice/venice.toml`. Before the Python
versions were replaced, each rule file was checked byte for byte against its
Python original: 144 Georgian, 120 Kyoto, 120 Modernist and 96 Venetian
situations, all identical. The module beside each file now holds only its site
type, any special drawing the file names, and `generate_*` / `derive_*`.

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
| `{ fit = "x", end = "end", bay = "bay", as = "rhythm", max_bays = 5 }` | Sizes a run with the fitting solver. `end` and `bay` name `[min, preferred, max]` params. |
| `{ insert = "Cornice", at = [x, y, w, h], name = "cornice", attrs = {...} }` | Adds a child that does not partition its parent. |
| `{ each = "joints(grid, x)", do = [...] }` | Repeats operations with `item` and `i` bound. |
| `{ set = {...} }`, `{ let = {...} }` | Writes the shape in hand; binds names for later operations. |
| `{ call = "kit.split_cell_around_its_light" }` | Runs a named Python production: the shared window anatomy. |

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

Functions: `min max abs round len sum fsum float int range column(rows, key)`,
`step(table, value)` (a regulation's step table), `geometric(first, ratio, n)`,
`bay_centres(parts, start)`,
`sin cos pi()`, `is_bay() is_first_bay() is_last_bay() is_middle_bay()`,
`has(name) in_parent(label) index_of(label) joints(parts, start)`.

The expression language is Python expression syntax, checked before it is run.
It allows arithmetic, comparisons, `and` / `or` / `not`, `a if c else b`,
literals, lists and tuples, indexing, `item.h` on tables, and f-strings. It
allows no imports, lambdas, comprehensions or attribute access beyond that.
An unknown function name is refused when the file is loaded.

## What stays in Python

- **The engine and the shared kit:** window anatomy and IR writers.
- **Drawings a file names by writer:** a gable outline, a lattice, a pavilion
  screen.
- **The other six styles.** They have not been converted yet. Amsterdam,
  Victorian, Normandy and Chicago would each need one or two more named
  writers or functions (the gable outline, the stoop, post placement around a
  light), and Paris still runs on its own Python.

The locality guarantees are the engine's, so they hold for rule files
unchanged. A rule can write only its own shape, and a part must stay inside
its parent unless its label is a declared overhang. Scoped overrides
(`with_override`, `with_interpreter`) apply to a rule-file style exactly as to
any other.
