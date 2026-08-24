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

## Layout

```
src/buildings/
  quantity.py     absolute / proportional / regulatory kinds
  trace.py        which rule produced this element
  rng.py          addressable, decorrelated decision streams
  site.py         the situation
  ir/             node vocabulary + lossless serialisation
  solver/         the fitting solver and its absorption ladder
  typologies/paris/
    reglement.py  the regulations, ported unchanged and sourced
    structure.py  roles.py  chronology.py  catalogue.py
    qualify/  compose.py  terminate.py  generate.py
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
