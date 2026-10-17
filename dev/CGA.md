# The building as a split grammar

`src/buildings/cga/` is a generic split-grammar engine (CGA-style: shapes with
scopes, productions that split them). `src/buildings/typologies/paris/grammar.py`
is the Paris immeuble written on it. `generate_cga(site)` returns the same
`(BuildingNode, TraceLog)` as `generate(site)`, and the IR is **byte-identical**
on the fuzzer's 3000 situations.

The point is locality. You can refine one sub-part's look or rule, or vary it
on one floor, one axis or one building, without the change rippling into parts
it never named.

## The engine

| Concept | What it is |
|---|---|
| `Shape` | A label, a `Scope` (x, y, w, h in the facade plane), attributes, children, and a trace. |
| `Production` | `label [: guard] --> body`. At most one fires per shape. Two at the same priority raise. |
| `split(axis, parts)` | Cut a shape into consecutive children. The parts must add up to the extent (`SplitMismatch`). |
| `fit(...)` | Size a repeat with the fitting solver: CGA's `{~w : Bay}*`, but done properly (closest count, absorption ladder). |
| `insert(label, scope)` | Add a child that does not partition its parent, such as a roof, a keystone or a rail. |
| `AttributeStage` | Layered rules that give a shape properties: later layer wins, then specificity, and ties raise. This moved here from `compose.py` unchanged. |
| `interpreters` | Per label, how a finished shape writes IR, bottom-up. This is the grammar's "turtle". |

Order is fixed. Shapes expand depth-first, and **all siblings of a split are
attributed before any of them expands**, so a rule can read its siblings. This
is how a storey learns it is the principal floor without anyone numbering
floors.

### What keeps a change local

1. **Write isolation.** A shape's attributes are locked except during its own
   attribute stage and its own production. A rule that reaches sideways raises
   `LockedAttributes`.
2. **Containment.** A child must lie inside its parent's scope (`OutsideParent`)
   unless its label is declared in `Grammar.overhangs`. Paris declares none.
3. **One entry per edit.** `with_production`, `with_interpreter`, `with_stage`
   and `with_override` each replace or add exactly one thing and leave the rest
   of the grammar as it was.
4. **Addressed overrides.** `with_override(label, layer, where=selector)` adds a
   layer that runs only on the shapes the selector picks. It is resolved with
   the normal layers, so precedence, tie detection and the "who it beat" trace
   all still apply. `with_interpreter(label, fn, where=...)` does the same for
   looks. Selectors read the tree: `under("b/s2")`,
   `lambda s: s.attr("role") is Role.PRINCIPAL`, a slot name, a site fact.

## The Paris grammar

```
Lot      --> insert( Facade | Roof )                  sizes from structure.solve_structure
Facade   --> split(y){ Storey* }
Storey   :  role from its siblings                    (attribute stage)
Storey   :  !within_comble --> split(x){ Cell* }      the facade's one rhythm
Cell     :  base, period, class, site, override layers  (attribute stage)
Cell     :  opening --> split(x){ Pier | LightBay | Pier }  [+ Rail on a balcon filant]
Cell     :  blind   --> Surround? Keystone? [Rail]
LightBay --> split(y){ Breast | Light | Lintel }  Shopfront? Balconette?
Light    --> Surround? Keystone? Rail?
Roof     :  terminal; interpreted by terminate()
```

Each sub-part's **presence** is decided by the production that inserts it, and
its **look** by its own interpreter, which sees its own scope. The element
functions (`emit_opening`, `emit_surround`, `emit_keystone`, `emit_rail`, ...)
live in `compose.py` and are shared with the pipeline, so there is one copy of
each.

## Checking it

```bash
python3 dev/harness/cga_equivalence.py            # grammar vs the recorded pipeline, 3000 cases
python3 dev/harness/cga_equivalence.py --pipeline # the pipeline vs its own recording (refactor guard)
python3 dev/harness/cga_blast_radius.py           # local changes stay local, 300 cases
python3 dev/harness/cga_figure.py OUT_DIR         # facade | shape tree | variations
```

`cga_blast_radius.py` applies four changes and diffs every IR node:

| Change | Kind | Touched |
|---|---|---|
| Keystones drawn at 40% width | look, everywhere | keystones only |
| Round heads on the noble floor | rule override, one floor | that floor's openings only |
| Balustrade 15% taller on the noble floor | look, one floor | that floor's ironwork only |
| No keystones on the entrance axis | rule override, one axis | that column's keystones only |

It also runs a negative control (the same override with no address), which the
checker must flag. It does.

## Not done yet

- **Sizes still come from `structure.py`.** The Lot production calls
  `solve_structure` as its size function: decree height steps, class ambition,
  entresol, garrets, and the bay solve with entrance placement. Turning that
  into declared split specs (`fit` calls with Paris `SlotSpec`s, a Facade
  production that chooses its storeys) is the next step. It is also what a San
  Francisco grammar would need to write from scratch.
- **Storey-wide elements** (socle, string course, balcon filant, cornice) are
  still written by one Storey interpreter (`emit_storey_elements`). They should
  become inserted shapes like the cell's parts.
- **The roof is one terminal** interpreted by `terminate()`. Dormers, brisis
  windows and stacks are natural children of it (the L-system study already
  has them as an open L-system against the gabarit).
- **`generate` is still the pipeline.** Once the above lands, `generate` can
  delegate to the grammar and the pipeline can retire. The recording in
  `dev/logs/cga_reference.json` is the bar either way.
