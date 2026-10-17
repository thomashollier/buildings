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

## A second typology: SoHo

`src/buildings/typologies/soho/` is New York's cast-iron district on the same
engine. There are three types, chosen by date and programme
(`recipes.recipe_for`):

- **Federal rowhouse** (to c. 1835): brick, three bays, a pitched roof with
  dormers and end chimneys.
- **Cast-iron loft** (1848 to 1880): mostly glass between iron columns, an
  entablature on every floor, and a deep bracketed cornice. Window heads go
  from round to segmental to flat as the date moves.
- **Brick store-and-loft** (1880s): brick piers over a cast-iron storefront,
  with a fire escape.

The grammar has the same shape as Paris. Only the data and two productions
(Column, FireEscape) differ, and the bay rhythm is sized by the engine's own
`fit`. Its numbers are **INFERRED** round figures, not measured like the Paris
ones. `dev/harness/soho_sheet.py` draws a street of them at one scale beside
a Paris immeuble.

The renderer gained three things for it, each keyed by a name the IR states:
`wall_material` (stone, cast iron, brick), a `column` node with an `order`, and
a `bracketed` cornice.

## Three more: Amsterdam, Venice, Chicago

Each was picked because its signature pushes the grammar somewhere the
others do not. All three share `typologies/common/kit.py` (the anatomy of a
window and the writing of IR, which SoHo now uses too), so each style is its
rules plus its signature productions.

| Style | Signature production | What it exercises |
|---|---|---|
| Amsterdam canal house | `Gable --> split(y){ GableTier* \| Crown }`, each tier a narrower storey with its own fit of bays, and an outline drawn around the tiers: step (to 1640), neck with claw scrolls (to 1720), bell (to 1790), or a straight cornice after | a sub-grammar on top of the facade; the outline follows the tiers, never the reverse |
| Venetian Gothic palazzo | `Storey --> split(x){ Wing \| Centre \| Wing }` on every floor; the nobile centre is one cell holding a **polifora**, a row of ogee lights on colonnettes, five on the first nobile and four on the second | a tripartite split inside each storey; multi-light cells |
| Chicago School block | base x2, a uniform shaft, capital x2; **Piers** inserted on the facade that run the whole shaft; every shaft bay a **Chicago window**, sash \| fixed \| sash at 1:2:1 | shapes that span several storeys; the same multi-light cell as Venice, different numbers |

The renderer gained, each keyed by a name the IR states: the `ogee` head,
`gable` nodes (outline, coping, hoisting beam), building-level `column`s, a
storey that may be narrower than the frontage, three more wall paints, and
drawing each bay element at its own rectangle (a bay may now hold several
lights). Paris SVG output is byte-identical before and after.

`python3 dev/harness/soho_sheet.py OUT_DIR --styles` draws all three at one scale.

## Four more: London, Kyoto, New York, Poissy

| Style | Signature | What it exercises |
|---|---|---|
| Georgian London terrace | every window one sash wide, its height set by its floor's ratio (1.75 ground, 2.1 piano nobile, 1.6 second, 1.0 third), a parapet storey hiding the roof | proportion as a per-floor rule, not a per-window one |
| Kyoto machiya | a low loft storey over the ground, tiled pent roofs (`hisashi`) along the front, every light screened by a `Lattice` shape (koshi below, mushiko above) | a screen inserted over a light: the opening stays, the street sees timber |
| New York setback tower | `tiers_for`: the street wall rises to 1.5x the street's width, tiers step back on a 1:4 plane until the mass is half the frontage, then the tower rises; piers per mass, a spire | massing derived from a regulation; widen the street and the whole tower moves |
| Corbusian block | pilotis on the posts' grid, and each floor cut `end \| Ribbon \| end` *ignoring* that grid, the ribbon split into panes; an off-axis roof pavilion with a curved screen | the free facade: the one grammar here whose storeys are deliberately not cut by the facade's rhythm |

Renderer additions: `timber_lattice` screens, `tiled` pent-roof eaves, the
`piloti` order, `spire` and `pavilion` outlines, seven more wall paints.
`python3 dev/harness/soho_sheet.py OUT_DIR --more` draws them (the tower at
its own scale).

## San Francisco and Normandy

| Style | Signature | What it exercises |
|---|---|---|
| San Francisco Victorian | every storey split `BayZone \| EntryZone`; over the basement the bay is three faces whose side share is the type (slanted Italianate 0.2, square Stick 0.07); a stoop; a false front, or a Queen Anne gable with a corner turret on a grand house; paint by seed | one number (side share) separating two types; asymmetric crowning |
| Normandy colombage | the frame as a grammar over the openings: posts at the setting's spacing, never across a light, a post either side of it, braces in end panels, a Saint Andrew's cross in each upstairs breast; town houses jettied (each floor a storey wider than the one below) under a street gable, country houses close-set under a 60 degree thatch with dormers | a structural layer laid over the window grammar; per-floor widths from a rule |

Writing the Normandy rules, the engine caught a genuine conflict (a country
loft's knee wall claimed by both "a window between posts" and "no window")
and refused to pick; the fix was the narrower rule's specificity.

`python3 dev/harness/soho_sheet.py OUT_DIR --sf-normandy` draws them.

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
