# Build Plan — Constraint-Derived Architecture

Derived from `../haussmann/BRIEF.md`. This plan is the execution contract: it
names what gets built, in what order, what each stage may depend on, and how
each stage is verified before the next begins.

Source repo (reference oracle, and source of two ports): `../haussmann/`
Target repo (this one, ground-up rewrite): `.`

---

## 0. What we are actually building

A generator that takes a **situation** (street width, parcel, year, class,
ground-floor programme) and emits a **structured description** of the building
that would have stood there. Not a mesh. Not a parameterised model. A
description whose every element can name the rule that produced it.

First and only typology in this stage: **Paris, 1820–1902.**

### The five invariants (from the first commit, asserted by tests)

| # | Invariant | Enforced by |
|---|---|---|
| I1 | Phases read strictly backwards; no phase mutates what an earlier phase read | Frozen dataclasses + `test_phase_isolation` |
| I2 | A building never samples a block-level fact — it receives it | `SiteContext` has no RNG; `test_no_block_sampling` |
| I3 | Every quantity carries its kind (absolute / proportional / regulatory) | `Quantity` newtype; `test_quantity_kinds` |
| I4 | Every emitted element records the rule that produced it | `Node.trace` non-null; `test_trace_completeness` |
| I5 | Seed + situation ⇒ identical output, always | `test_determinism`, fuzz harness |

These are not aspirations. Each has a named test that must exist and pass
before the stage that introduces it is considered done.

---

## 1. Architecture

```
src/buildings/
  quantity.py        Absolute / Proportional / Regulatory kinds + arithmetic
  trace.py           RuleId, TraceEntry, TraceLog — "which rule made this?"
  rng.py             Addressable, decorrelated decision streams
  site.py            SiteContext — the situation (immutable, no RNG)
  ir/
    nodes.py         IR node vocabulary
    serial.py        JSON round-trip from day one
  solver/
    fitting.py       Generic 1-D budget solver, absorption ladder, parity-aware
  typologies/paris/
    reglement.py     PORTED UNCHANGED from ../haussmann/core/reglement.py
    structure.py     Phase 1 — envelope, storey stack, bay grid
    roles.py         Phase 2 — derived role predicates
    chronology.py    Date windows, prevalence curves, class adoption lag
    catalogue.py     Module catalogue + dimensional limits
    qualify/         Phase 3 — context → properties rules
      base.py        base vocabulary layer
      period.py      period layer (date-window driven)
      klass.py       class layer
    compose.py       Phase 4 — layered rule sets, specificity tie-break
    terminate.py     Comble inscribed in envelope; silhouette polyline
  block/
    block.py         Frontage subdivision, adjacency, handed-down datums
  render/svg/        PORTED from ../haussmann/backends/, decisions stripped out
```

### The phase pipeline (I1)

```
SiteContext ─▶ [1 STRUCTURE] ─▶ Grid ─▶ [2 ROLES] ─▶ RoledGrid
                                                        │
                                                        ▼
                                              [3 QUALIFICATION] ─▶ IR
                                                        ▲
                                              [4 COMPOSITION] layers
                                                        │
                                              [5 TERMINATION] ─▶ IR + silhouette
                                                        │
                                                        ▼
                                                   [6 RENDER]
```

Each arrow is one-way. Phase *n* receives frozen output of phase *n-1* and may
not reach back. Block hands down to building; never the reverse (I2).

### The three number kinds (I3)

Every dimension is constructed as exactly one of:

- `Abs(v, why)` — set by the human body or an object that must pass. Never
  scales. **Cannot absorb slack in the solver.**
- `Prop(v, why)` — compositional; scales with class/ambition under one
  explicit transform.
- `Reg(v, source)` — a number in a law. Carries a citation. Changes on a date.
  Asserted against its source by test.

The `scale_for_class()` transform touches `Prop` only, in exactly one place.

### Addressability (I5)

`rng.py` gives each decision an independent stream keyed by a stable path
(`"bay/3/opening/surround"`), not a shared sequence. Pinning one decision, or
adding a new kind of decision later, must not shift any other.

---

## 2. Stage sequence, dependencies, and verification gates

Stages run in dependency order. **A stage is not done until its gate passes.**

### S0 — Foundations
*Depends on: nothing.*

Build `quantity.py`, `trace.py`, `rng.py`, `site.py`, `ir/nodes.py`,
`ir/serial.py`.

The trace facility is built **before the second rule exists** — the brief is
explicit that deferring it is how this approach dies.

**Gate G0:**
- `Quantity` arithmetic preserves/rejects kind mixing correctly
- IR JSON round-trips losslessly for every node type
- RNG: same path + seed ⇒ same value; adding a new path shifts nothing else
- `SiteContext` is frozen and hashable

### S1 — Fitting solver
*Depends on: S0.*

Generic 1-D solver: fill a budget with typed slots (`fixed`, `repeating`,
`flexible`; each with min/preferred/max). Implements the **absorption ladder**
in order: widen ends → widen filler → widen bay → insert narrow special → add
module (parity-aware: +2 when the composition has a central feature).

Returns the grid **and an account of what it did**, for the trace.

Centreline bay units: `N` modules is exactly `N × width`; only the two ends are
special. Absolute-kind slots are rigid and never absorb.

**Gate G1:**
- Exhaustive sweep: for widths 4.0–40.0 m at 0.05 m steps and 8 seeds, the
  solver terminates, sums exactly to budget (±1e-9), and never violates a
  min/max
- Absolute slots never change width across the whole sweep
- Ladder rung used is recorded and monotonic in slack
- Parity: with a central feature, module count changes by 2, never 1

### S2 — Regulatory port
*Depends on: S0. Parallel with S1.*

Port `../haussmann/core/reglement.py` **unchanged** in behaviour. Adapt only
imports and wrap returned numbers in `Reg` with their citation. Port
`test_reglement.py` alongside it.

**Gate G2:**
- Ported module reproduces the old module's output bit-for-bit across a sweep
  of (street_width × year) — differential test against `../haussmann`
- The documented 28.50 m ceiling (20 m facade + 8.50 m comble, 1884) is
  asserted from the source, not fitted
- Every `Reg` value has a non-empty citation string

### S3 — Structure phase
*Depends on: S1, S2.*

Envelope from regulation → cornice height + roof envelope. Storeys fill the
height budget via the solver. Bays fill the parcel width via the same solver,
**solved once per building**. Output is an unnamed grid: no roles, no meaning.

**Gate G3:**
- Grid contains zero role/name information (asserted structurally)
- Widening the street increases height **in steps**, not continuously
- Bay grid is identical across all storeys of a building (single solve)

### S4 — Roles phase
*Depends on: S3.*

Derived predicates only, reading structure alone:
- **Base** — bottom slot, unconditional
- **Mezzanine** — directly above base, height markedly below median habitable
- **Principal** — *tallest* habitable slot above base and mezzanine (ties → lowest)
- **Upper** — between principal and attic, ranked upward
- **Attic** — inside the roof envelope

**Gate G4:**
- 5-storey and 9-storey buildings get correct roles from identical rules, no
  special-casing
- Base exclusion verified: a ground floor taller than the noble floor must not
  be labelled principal
- Removing the mezzanine moves the balcony up a floor **by itself** (the brief's
  named test)

### S5 — Chronology
*Depends on: S0. Parallel with S3/S4.*

Date windows on feature *variants*, not periods on buildings. Each variant:
earliest year, peak-prevalence window, latest year. A building of year Y sees
variants whose windows contain Y, weighted by prevalence at Y.

Two distinct mechanisms, never conflated:
- **Legality** — step function, sourced, binary (oriels illegal 1881, legal 1882)
- **Fashion** — distribution: ramp, peak, decline

Availability is a function of `(feature, year, class)` — adoption lags down the
class ladder. Elements carry their own dates (observation date ≠ construction
date): 1860 bones, 1885 roof, 1898 shopfront.

Feature families modelled: ironwork, socle, keystone sculpture, roof, shopfront.

**Gate G5:**
- `grep` finds **zero** occurrences of period-enum branching in rule code
  (`period ==`, `era ==` outside `reglement.py`) — automated check
- Two buildings of the same year and different class differ in available variants
- Prevalence curves are continuous; legality is a step — asserted separately

### S6 — Qualification + composition
*Depends on: S4, S5.*

Rules map a read-only **context** to properties. Context is exactly the fact set
named in the brief: structure (own dims, level above pavement, index from bottom
and top, total count), role (+ rank vs principal), horizontal (index from left
and centre, is-centre, distance from entrance, edge/inserted special, slot kind),
building (date, class, street width, corner/mid-block), envelope (cornice height,
within-comble).

Layers stack: base vocabulary → period → class → site. Later wins; specificity
breaks ties. User overrides are simply a top layer.

A storey never lays out; it **fills** the shared grid.

**Gate G6:**
- Context is frozen; any rule mutating it raises
- "Balcony where floor ≥ 6 m above pavement" is expressed as the ordinance, not
  a floor list — and asserted against `reglement.balcony_rule`
- Layer override + specificity resolution has an explicit truth table test
- Every emitted node has a non-null trace naming its rule (I4)

### S7 — Termination
*Depends on: S3, S6.*

Comble inscribed in the regulatory envelope. Silhouette emitted as a **polyline
in the IR**, not derived by the renderer.

**Gate G7:**
- Silhouette polyline lies within the envelope for every (width × year) in a sweep
- 1884+ produces an arc-derived profile; pre-1884 a 45° plane — visible in the IR

### S8 — Renderer port
*Depends on: S7.*

Port element renderers from `../haussmann/backends/svg*.py`. **Move composition
decisions out of the renderer on the way across.** The renderer decides nothing
arguable.

**Gate G8:**
- Automated scan: renderer contains no conditional on date, class, or role
- Rendering the same IR twice is byte-identical
- Contact sheet renders without exception across the fuzz corpus

### S9 — Block
*Depends on: S3 (channel from S0).*

The block owns frontage subdivision and adjacency **under every relation** —
that is the irreducible part. For Paris it additionally owns shared horizontal
datums (cornice, string courses, balcony lines) per the 1855 circulaire.
Strictly one-way: block hands down resolved decisions.

Corner is its own short facade, **not a module type**.

No general binding system — deferred to the second typology port, per the brief.

**Gate G9:**
- Buildings on one block share exactly one street-width value — the previous
  attempt's named failure; asserted directly
- Cornice lines across a block are equal to within 1e-9
- A block reads as one wall in the contact sheet (visual gate, S11)

### S10 — Validation harness
*Depends on: S8.*

- **Oracle diff** — keep `../haussmann` running; diff the same situations
- **Regulatory assertions** — documented figures against their sources
- **Fuzz** — sweep seeds × widths × eras for invariant violations
- **Contact sheets** — 20 seeds in one grid, the cheapest outlier detector

### S11 — Reference corpus + VLM check
*Runs in parallel from the start.*

Per the brief, reference photographs ship **before** rules do. Scrape a corpus
of Paris building types, key each to its situation (street width, date, class,
mid-block/corner) where known, and build a review page so the operator can
**select which images become the VLM ground-truth set**. Generated output is
then rendered alongside the kept set.

Two limits respected explicitly in the harness:
- Photographs support qualitative comparison, **not measurement**
- A visual check is a tripwire, not a passing grade — "looks wrong" is strong
  evidence, "looks right" is weak. Systematic 3 % error belongs to assertions.

---

## 3. Deliberately not in this stage

Per the brief: no second typology, no rule DSL or parser, no general binding
system for block relation, no 3-D backend, no override system separate from
rule layering.

---

## 4. First-week acceptance

Reproduce **one real building's elevation** end to end through all four phases,
with a trace explaining every element, before generalising anything. If the
phase model is wrong, this surfaces it in days rather than after rules have been
built on top of it.

---

## 5. Execution harness

The stages above are executed by workflow scripts in `dev/workflows/`, with
agent role definitions in `dev/agents/` and verification scripts in
`dev/harness/`. Model tier per agent is chosen by task difficulty and recorded
in each workflow's `meta`:

| Tier | Used for |
|---|---|
| `haiku` | mechanical ports, scaffolding, file moves, contact-sheet assembly |
| `sonnet` | ordinary implementation, tests, scraping, review page |
| `opus` | fitting solver, rule-model architecture, adversarial verification |

Every stage is followed by an independent **verifier** agent that did not write
the code, running the stage's gate. A gate failure sends the stage back rather
than proceeding — the workflow encodes this as a repair loop, bounded.
