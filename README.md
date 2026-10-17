# buildings

A procedural building generator that derives form from **constraints** rather
than from taste.

Buildings of a place and a period look alike because they were built under the
same rules, not because their architects followed a style guide. Street width
capped the height. An ordinance capped how far a balcony could project and how
low it could hang. A decree fixed the shape of the roof above the cornice. What
we call "the Haussmann building" is the residue of those rules meeting a
programme.

**If you model the constraints, the style comes out for free — and it varies
correctly when the inputs vary.**

## What it does

You describe a *situation*, not a building:

```python
from buildings.site import SiteContext, BuildingClass, GroundProgramme
from buildings.typologies.paris.generate import generate

site = SiteContext(
    street_width=20.0,      # metres — handed down by the block
    parcel_width=12.0,
    parcel_depth=18.0,
    year=1865,
    klass=BuildingClass.COMFORTABLE,
    ground=GroundProgramme.SHOP,
    seed=7,
)
building, trace = generate(site)
```

There is no slider for roof angle, because nobody chose the roof angle. Widen
the street and the building gets taller *in steps*, because the rule was a step
table. Move the date past the 1884 decree and the roofline changes shape. Take
away the mezzanine and the balcony jumps up a floor by itself — because the
balcony rule is about height above the pavement, not about which floor it is.

Every element can name the rule that produced it:

```python
trace.explain(node.id)   # -> the ordinance, the reason, the inputs
```

## Design

Four phases, each reading strictly backwards, never mutating what an earlier
phase read:

1. **Structure** — the fitting solver fills budgets with slots. Storeys into a
   height budget, bays into a width. Purely quantitative: no names, no meaning.
2. **Roles** — identity is *derived* by positional predicate, not declared. The
   principal floor is the tallest habitable slot above the base; you never say a
   building *has* one.
3. **Qualification** — rules map a read-only context to properties. "A balcony
   where the floor is at least 6 m above the pavement" is the actual 1823
   ordinance, expressed as a rule rather than a list of floor numbers.
4. **Composition** — rule sets layer: base vocabulary, period, class, site.
   Later layers win; specificity breaks ties.

Three things hold it together:

- **Every quantity carries its kind.** *Absolute* is set by the human body and
  never scales — a carriage entrance must admit a carriage. *Proportional* is
  compositional and scales with money. *Regulatory* is a number in a law and
  changes on a date. Conflating them is what makes procedural buildings look
  like toys: the grand building reads as grand precisely because its doorway is
  only a little bigger while its windows are much bigger.
- **Chronology is date windows on feature variants**, never a period enum on the
  building. Legality is a step function; fashion is a distribution. Availability
  depends on `(feature, year, class)`, because a feature reaches modest streets
  ten to twenty years after the boulevards — so a grand and a modest building
  both built in 1885 are not stylistic contemporaries.
- **The block is the unit, not the building.** The block owns frontage
  subdivision, adjacency, and the shared horizontal datums the 1855 circulaire
  required. Buildings *receive* those facts; they never sample them.

The output is a **structured description**, not a mesh. Renderers consume it. If
a renderer is deciding anything a person could argue about, that decision is in
the wrong place.

## The five invariants

Asserted by tests in `tests/invariant/`, not aspirations. Each has a named test
that must exist and pass. Stated once here and once in `dev/PLAN.md`.

| # | Invariant | Enforced by |
|---|---|---|
| **I1** | Phases read strictly backwards; no phase mutates what an earlier phase read | Frozen dataclasses, `test_phase_isolation` |
| **I2** | A building never samples a block-level fact — it *receives* it | `SiteContext` holds no RNG, `test_no_block_sampling` |
| **I3** | Every quantity carries its kind (absolute / proportional / regulatory) | `Quantity` newtype, `test_quantity_kinds` |
| **I4** | Every emitted element records the rule that produced it | `Node.trace` non-empty, `test_trace_completeness` |
| **I5** | Seed + situation ⇒ identical output, always | `test_determinism`, fuzz harness |

Three standing guards back them, run as scripts rather than tests so they can
be pointed at the tree from anywhere:

```bash
python3 dev/harness/check_ir_is_consumed.py        # nothing emitted is ignored downstream
python3 dev/harness/check_no_period_branching.py   # no `if period ==` anywhere
python3 dev/harness/check_renderer_dumb.py         # the renderer decides nothing arguable
```

## The construction ladder

Phase 1 fills an exact budget with typed slots — storeys into a height budget,
bays into a width. One generic 1-D solver serves both axes and knows nothing
about Paris (`src/buildings/solver/fitting.py`).

**The vocabulary.** Count **axes**, measure **pitch**. An *axis* is the vertical
line of openings up the facade — the thing you count. *Pitch* is axis to axis,
centre to centre. Each pitch is filled by one **window** plus one **pier**, so
`window + pier = pitch` exactly. The solver's repeating module is measured
centreline-to-centreline of the filler — half-pier, opening, half-pier — which
is why `N` bays is *exactly* `N × pitch` and the only special case is the two
ends. (Avoid the word "bay" in prose: it names the solver's module, a vestigial
catalogue entry, and colloquially the opening itself.)

**Choosing the count.** The solver walks candidate counts outward from the one
that fills the budget most nearly, and takes the first the declared bounds
permit — closest to preferred, whether that means one more axis at a narrower
pitch or one fewer at a wider one. It does *not* floor the division. Flooring
discards up to a whole axis and then has to hide the remainder: on a 15.0 m
frontage with a carriage entrance it chose 3 axes and inflated every pitch to
3.367 m to absorb 2.5 m of slack, where 4 axes sit near the preferred pitch.

**Absorbing what is left.** Residue goes into the most elastic thing available,
and *that ordering is the solver*:

| rung | | absorbs by |
|---|---|---|
| 1 | `WIDEN_ENDS` | the two end piers — they exist to be adjusted |
| 2 | `WIDEN_FILLER` | the pier thickens; the opening does not move |
| 3 | `WIDEN_BAY` | the opening itself stretches — visible past a few percent |
| 4 | `INSERT_SPECIAL` | a narrow half-bay, blind panel or œil-de-bœuf |
| 5 | `ADD_MODULE` | one more axis |

`rigid=True` slots carry ABSOLUTE quantities and **never** absorb — a carriage
entrance must admit a carriage, and stretching a doorway to make the arithmetic
work is the move that destroys scale.

**An entrance is an opening in an ordinary axis, exactly like a window.** The
ABSOLUTE quantity is the *clear opening* — the body or the vehicle that has to
pass — not the strip of frontage around it. So a slot the solver is told to
place at an index may be declared a member of the repeating pool: it takes one
of the modules, at the pitch, and the masonry beside it then differs from the
masonry between two windows by exactly what the two openings differ by. The
opening plus a jamb either side is that slot's **minimum**, and where the pitch
falls under it the solver refuses and the caller re-solves with the slot given a
module of its own. That is the only exception, and it is conditioned on
**width** rather than on the slot being a door: at the 2.00–3.20 m band a
pedestrian door needs 2.35 m and effectively never triggers it, a carriage arch
needs 3.04 m and usually does. Before this, the entrance was the one rigid
element in an elastic run, and the wall next to the biggest hole in the facade
came out *thinner* than the wall between two windows.

Two placements are deliberate. `INSERT_SPECIAL` sits *below* `ADD_MODULE` and is
tried first: five good axes plus one narrow one reads better than six squeezed
ones, so the leftover is treated as architecturally meaningful rather than as
padding. And **parity belongs to the composition, not to one rung** — a central
feature means something stands *on* the axis, satisfied either by an odd
interior run or by an even one with a lone central special. Constrain only the
`ADD_MODULE` increment and the count still walks 1, 2, 3, 4 as the budget grows,
putting the axis on a pier half the time.

Since the count is chosen by closeness, **rung 5 is now reachable only where
parity forbids the closest count** — if one more axis were the better answer, it
is already the count that was chosen. The rung is subsumed, not removed, and the
ordering is unchanged.

**Known limit.** Every end pier is one width and every interior pier another:
`_absorb` returns two scalars. A facade whose piers vary — narrower toward the
middle, or the inverse — is not expressible. The seam for that change is
`_absorb`, the single place that decides where residue goes.

## Layout

```
src/buildings/
  quantity.py     absolute / proportional / regulatory kinds
  trace.py        which rule produced this element
  rng.py          addressable, decorrelated decision streams
  site.py         the situation
  ir/             node vocabulary + lossless serialisation
  solver/         the fitting solver and its absorption ladder
  cga/            the split-grammar engine: shapes, split/fit/insert, scoped overrides
  typologies/paris/
    reglement.py  the regulations, ported unchanged and sourced
    structure.py  roles.py  chronology.py  catalogue.py
    qualify/  compose.py  terminate.py  generate.py
    grammar.py    the same building as a split grammar (dev/CGA.md)
  block/          frontage subdivision, adjacency, shared datums
  render/svg/     the renderer, which decides nothing arguable
tests/
  unit/  invariant/  oracle/
dev/              the plan, the harness, and the reference corpus
```

## Running

```bash
python3 -m pytest tests/ -q                          # the suite
python3 dev/harness/first_building.py                # one building, fully traced
python3 dev/harness/contact_sheets.py                # visual sweeps
python3 dev/harness/check_no_period_branching.py     # guard
python3 dev/harness/check_renderer_dumb.py           # guard
python3 dev/harness/cga_equivalence.py               # grammar == pipeline, 3000 cases
python3 dev/harness/cga_blast_radius.py              # local changes stay local
open dev/reference/review.html                       # reference corpus selection
```

Python 3.11+. No runtime dependencies.

## Scope

First and only typology is Paris, 1820–1902. Deliberately not in this stage: a
second typology, a rule DSL, a general binding system for block relation, a 3-D
backend, or an override system separate from rule layering.

Interiors, structure, services and photoreal materials are out of scope
permanently. This does one vocabulary well.

See `dev/PLAN.md` for the stage sequence, `dev/CONTRACTS.md` for the interface
contract, and `dev/reference/SOURCES.md` for the primary sources every number is
answerable to.
