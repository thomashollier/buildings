export const meta = {
  name: 'buildings-s3-s5',
  description: 'Stages S3-S5: structure phase, derived roles, chronology date-windows',
  whenToUse: 'Second build wave. Requires S0-S2 gates green.',
  phases: [
    { title: 'Structure+Chronology', detail: 'S3 and S5 are independent — built in parallel' },
    { title: 'Roles', detail: 'S4 derived role predicates, reads structure only' },
    { title: 'Gate', detail: 'independent verification of all three stages' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PREAMBLE = `You are implementing one stage of a ground-up rewrite of a procedural building
generator for 19th-century Paris. Thesis: **model the constraints and the style comes out for free.**

## Binding documents — read before writing code
- \`${ROOT}/dev/PLAN.md\` — stage sequence and gates
- \`${ROOT}/dev/CONTRACTS.md\` — **frozen interface contract**, code against it exactly\n  **Read \`Amendment 1\` at the END of that file — it is binding and overrides anything earlier that conflicts.**
- \`${OLD}/BRIEF.md\` — design rationale; read the sections named in your stage

## Already built and available to you (S0-S2, gates passed)
- \`buildings.quantity\` — Kind/Quantity/Abs/Prop/Reg/scale_for_class
- \`buildings.trace\` — RuleId/TraceEntry/TraceLog
- \`buildings.rng\` — DecisionStream, addressable per-path streams
- \`buildings.site\` — SiteContext, BuildingClass, GroundProgramme
- \`buildings.ir.nodes\` / \`buildings.ir.serial\`
- \`buildings.solver.fitting\` — solve(), the absorption ladder
- \`buildings.typologies.paris.reglement\` (+ \`reglement_adapter\`)

**Read the actual source of these before using them.** Do not guess their behaviour, and do not
reimplement anything they already do — especially not the fitting solver.

## The contract is frozen
Do not rename or re-shape a signature from CONTRACTS.md. If one is genuinely wrong, implement the
rest and report the problem. Do not silently adapt.

## Working rules
- Python 3.11, \`from __future__ import annotations\`, public dataclasses \`frozen=True\`, stdlib only.
- \`cd ${ROOT} && python3 -m pytest tests/ -q\` must pass before you finish — yours and everyone else's.
- Only touch the files your stage owns.

## Invariants you must uphold
I1 phases read strictly backwards; no phase mutates what an earlier one read
I2 a building never samples a block-level fact, it receives it
I3 every quantity carries its kind
I4 every emitted element records the rule that produced it
I5 seed + situation yields identical output, always
`

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['stage', 'passed', 'checks'],
  properties: {
    stage: { type: 'string' },
    passed: { type: 'boolean', description: 'true ONLY if every check passed' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'passed', 'evidence'],
        properties: {
          name: { type: 'string' },
          passed: { type: 'boolean' },
          evidence: { type: 'string', description: 'concrete output/numbers, not a claim' },
        },
      },
    },
    failures: { type: 'array', items: { type: 'string' } },
    contract_problems: { type: 'array', items: { type: 'string' } },
  },
}

function verifier(stage, gate, implReport) {
  return agent(
    `You are an INDEPENDENT VERIFIER for stage ${stage} of the project at \`${ROOT}\`.
You did NOT write this code. Find out whether it actually works. Do not be agreeable.

Read \`${ROOT}/dev/CONTRACTS.md\` for the contract, and the relevant part of \`${OLD}/BRIEF.md\`.

The implementer reported:
---
${(implReport || '(no report)').slice(0, 3000)}
---
That is a claim to be checked, not evidence.

${gate}

Write your own throwaway check scripts under \`${ROOT}/dev/logs/\` (prefix \`verify_${stage}_\`) and
RUN them. Also run \`cd ${ROOT} && python3 -m pytest tests/ -q\`. Evidence means actual output and
actual numbers; "the code looks correct" is not evidence.

\`passed: true\` ONLY if every check passed. A skipped test did not pass. Be precise in \`failures\`.`,
    { label: `verify:${stage}`, phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  )
}

// ---------------------------------------------------------------- Round A
phase('Structure+Chronology')

const [structureReport, chronologyReport] = await parallel([
  () => agent(
    `${PREAMBLE}

## Files you own
\`src/buildings/typologies/paris/structure.py\`, \`tests/unit/test_structure.py\`,
\`tests/invariant/test_envelope_steps.py\`

## Stage S3 — Structure phase

Read BRIEF.md sections "The rule model" (phase 1) and "Build order → 2 — Structure phase".

Build \`solve_structure(site, datums=None) -> Grid\` per CONTRACTS.md.

Three things happen here and nothing else:

1. **Envelope from regulation.** Use \`reglement\`/\`reglement_adapter\` — do not re-derive any
   regulatory arithmetic yourself. Get the cornice height limit from street width and year, and the
   roof envelope (45° plane pre-1884, arc post-1884).

2. **Separate the ceiling from what was built.** This is a named lesson from the previous attempt:
   "The law says how tall you *may* build. Economics and programme say how tall you *did*.
   Conflating them makes every building a maximal building, which is wrong and looks it."
   So compute the legal ceiling, then compute the ACTUAL built height from class and programme,
   and keep both visible on the \`Grid\`. Grand buildings on wide streets build near the limit;
   modest ones do not.

3. **Fill budgets with the S1 solver.** Storeys into the height budget; bays into the parcel width.
   The bay grid is solved **ONCE per building** and every storey later decorates that same grid —
   openings align vertically because that is load-bearing masonry, not a preference. Per-role storey
   height comes from RELATIONS (a preferred range, a minimum from the 1859 règlement's 2.60 m, and
   "shorter than the one below"), not from stored per-floor values. A taper is a relation, not a
   magic number.

**The output is an unnamed grid.** No roles, no names, no meaning — those come in S4. If you find
yourself writing the word "principal" or "mezzanine" in this file, you are doing S4's job.
\`Grid\` must contain no field naming a role.

If \`datums\` is provided the building RECEIVES those block-level facts (street width, cornice
height) and must not recompute or resample them (I2).

Record trace entries for every decision.`,
    { label: 'impl:S3-structure', phase: 'Structure+Chronology', model: 'sonnet' }
  ),

  () => agent(
    `${PREAMBLE}

## Files you own
\`src/buildings/typologies/paris/chronology.py\`, \`src/buildings/typologies/paris/catalogue.py\`,
\`tests/unit/test_chronology.py\`

## Stage S5 — Chronology

Read BRIEF.md section "Chronology: features appearing and disappearing" **in full**. It is the
densest part of the brief and the design is easy to get subtly wrong.

Build \`chronology.py\` per CONTRACTS.md: \`Variant\`, \`prevalence\`, \`available\`, \`legal\`.

The core move: **attach the date to the feature VARIANT, not to the building.**

1. **Two chronologies that do not align.** Regulation changes on decree dates (1859, 1884, 1902);
   style changes on political and cultural ones (c. 1848, 1853, 1870). A single period enum cannot
   carry both and its boundaries will be wrong for one of them.

2. **Date windows, not periods.** Each variant carries earliest / peak-from / peak-to / latest.
   A building of year Y sees the variants whose windows contain Y, weighted by prevalence at Y.
   Periods survive as documentation labels only. **The moment a rule reads \`period == SECOND_EMPIRE\`
   the enum is back and the straggler building — the one that kept its outdated ironwork for twenty
   years, which is MOST buildings — has become unrepresentable.**
   \`${ROOT}/dev/harness/check_no_period_branching.py\` enforces this by AST scan. Run it.

3. **Two mechanisms, never conflated.**
   - \`legal()\` is a STEP function, sourced, binary. Oriels illegal 1881, legal 1882.
     Delegate to \`reglement\` where the regulation already models it — do not duplicate it.
   - \`prevalence()\` is a DISTRIBUTION: a continuous ramp, peak and decline in [0,1].
     Mascarons do not appear on a date; they grow common through the 1870s and elaborate through
     the 1890s.
   Conflating them gives streets where every facade of a given year is suddenly identical.

4. **Adoption lags down the class ladder.** Availability is a function of
   \`(feature, year, class)\`, not \`(feature, year)\`. A feature appears on grand frontages first and
   reaches modest streets ten to twenty years later, if ever — and modest buildings RETAIN
   superseded forms long after they have gone from the boulevards. So a grand and a modest building
   both built in 1885 are not stylistic contemporaries. Model the lag AND the retention.

5. **Construction date is not observation date.** Elements carry their own dates alongside the
   building's: a facade seen in 1900 may have 1860 bones, an 1885 roof and an 1898 shopfront.
   Combles were demonstrably raised after 1884 — the cornice line held while owners heightened
   roofs. Provide a way to express this.

Populate the five feature families with real variants and real date windows, taken from BRIEF.md's
"The feature families worth dating" section — ironwork, socle, keystone sculpture, roof, shopfront.
Put the source in each variant's \`source\` field. Where BRIEF.md gives a date, use it; where you
infer one, MARK IT AS INFERRED in the source string. The brief is explicit: "mark clearly the ones
you inferred because the source was silent."

\`catalogue.py\` holds the module catalogue and dimensional limits: openings, filler/piers, ends,
doors (incl. the carriage entrance as an ABSOLUTE quantity), narrow specials. Every dimension is an
\`Abs\`/\`Prop\`/\`Reg\` — a carriage entrance must admit a carriage and does not scale with the
building; bay width and window aspect are proportional; the 2.60 m storey minimum is regulatory.`,
    { label: 'impl:S5-chronology', phase: 'Structure+Chronology', model: 'sonnet' }
  ),
])

// ---------------------------------------------------------------- Round B
phase('Roles')

const rolesReport = await agent(
  `${PREAMBLE}

## Files you own
\`src/buildings/typologies/paris/roles.py\`, \`tests/unit/test_roles.py\`

## Stage S4 — Roles phase

Read BRIEF.md "The rule model" (phase 2) and "Paris: the specifics to pin down first → Role predicates".

Build \`Role\`, \`RoledStorey\`, \`RoledGrid\`, \`assign_roles(grid) -> RoledGrid\` per CONTRACTS.md.

**Identity is DERIVED, never declared.** You never say a building *has* a principal floor — you say
what makes a floor principal, and the label falls out. This is what removes the fixed floor
enumeration: a five-storey and a nine-storey building get correct roles from the same rules with no
special case for the extra storeys, because nothing enumerates positions any more.

Predicates, exactly:
- **Base** — the bottom slot. Unconditional.
- **Mezzanine** — a slot directly above the base whose height falls markedly below the median
  habitable storey. Present only if the stack produced one.
- **Principal** — the **TALLEST** habitable slot above the base and mezzanine. NOT "the first tall
  one": tallest is what the étage noble actually is. Ties break to the lowest.
- **Upper** — every slot between principal and attic, ranked upward from the principal.
- **Attic** — the slot inside the roof envelope.

**The base exclusion is load-bearing**: a Paris ground floor is often taller than the noble floor,
so "tallest slot" without qualification picks the wrong one. Write a test that would catch this.

\`assign_roles\` reads the \`Grid\` and NOTHING ELSE — not SiteContext, not the year, not the class.
If you need a fact that is not in \`Grid\`, that is a signal S3 should have produced it; report that
rather than reaching around it (I1).

The structure report from S3:
---
${(structureReport || '(none)').slice(0, 1500)}
---`,
  { label: 'impl:S4-roles', phase: 'Roles', model: 'sonnet' }
)

// ---------------------------------------------------------------- Gate
phase('Gate')

const verdicts = await parallel([
  () => verifier('S3', `## Gate G3
1. **The grid is unnamed.** Inspect \`Grid\` and its slots — assert NO field, attribute or string
   value names a role (base/mezzanine/principal/noble/upper/attic). Grep structure.py for those
   words. Any hit outside a comment is a failure.
2. **Height moves in STEPS, not continuously.** Sweep street width 6→40 m at 0.1 m for a fixed year
   and class; collect cornice height; assert the result is a step function (a small number of
   distinct plateaus), not a smooth ramp. Report the plateau values and count. A continuous ramp is
   a hard failure — the regulation was a step table.
3. **One bay solve per building.** Assert the bay grid is byte-identical across every storey.
   Grep for any second call to \`solve()\` on the horizontal axis.
4. **Ceiling vs built are separate.** Confirm \`Grid\` exposes both the legal limit and the actual
   built height, and that they genuinely differ for a MODEST building on a wide street. If every
   building is maximal, that is a failure.
5. **Datums are received, not resampled.** Call \`solve_structure\` with explicit \`datums\` and
   assert the returned cornice height equals the handed-down value exactly (I2).
6. Determinism: same site + seed, 50 runs, identical Grid.`, structureReport),

  () => verifier('S4', `## Gate G4
1. **Same rules, different heights.** Build a 5-storey and a 9-storey stack; assert both get correct
   roles from identical code with no special-casing. Grep roles.py for hardcoded indices
   (\`== 2\`, \`[4]\`, \`floor_3\`) — any position enumeration is a failure.
2. **The base exclusion.** Construct a stack whose GROUND floor is the tallest slot overall.
   Assert PRINCIPAL is NOT assigned to it. This is the load-bearing case; if it passes trivially,
   check the test is actually exercising it.
3. **Tallest, not first-tall.** Construct a stack where the first tall storey is NOT the tallest.
   Assert PRINCIPAL lands on the tallest. Assert ties break to the LOWEST.
4. **The brief's named test — mezzanine removal.** Build two otherwise-identical stacks, one with a
   mezzanine and one without. Assert the principal floor (and hence anything keyed to its height
   above the pavement) moves BY ITSELF, with no rule mentioning mezzanines. Report the actual level
   above pavement in both cases.
5. **Phase isolation (I1).** Grep roles.py for imports of SiteContext, year, class, reglement,
   chronology. There must be none — it reads \`Grid\` only.`, rolesReport),

  () => verifier('S5', `## Gate G5
1. **Zero period branching.** Run \`python3 ${ROOT}/dev/harness/check_no_period_branching.py\`.
   It must exit 0. Paste its output.
2. **Class lag is real.** For the same year (say 1885), assert a GRAND and a MODEST building get
   DIFFERENT available variant sets or materially different weights. Show the actual variant lists.
   If they are identical, the class axis is not wired up — failure.
3. **Fashion is continuous, legality is a step.** Sample \`prevalence()\` across 1820-1910 at 1-year
   steps for several variants: assert no discontinuity larger than a small epsilon, and assert the
   curve actually rises and falls (a flat or constant curve is a failure). Separately assert
   \`legal()\` IS a step — e.g. oriels false in 1881, true in 1882.
4. **Windows contain the year.** Property-check: for 500 random (feature, year, class), every
   returned variant satisfies \`earliest <= year <= latest\` after class lag, and weights are in [0,1].
5. **Inferred dates are marked.** Grep the variant table: every \`source\` is non-empty, and any date
   not traceable to BRIEF.md is explicitly marked inferred. List any bare/placeholder sources.
6. **Observation date.** Confirm there is a working mechanism for an element to carry its own date
   distinct from the building's (the 1860-bones/1885-roof/1898-shopfront case). Demonstrate it.
7. **Absolute/proportional in the catalogue.** Assert the carriage entrance is an ABSOLUTE quantity
   and does NOT change under \`scale_for_class\`, while bay width DOES.`, chronologyReport),
])

const final = verdicts.filter(Boolean)
const failed = final.filter((v) => !v.passed)
log(`Wave 2 gates: ${final.length - failed.length}/3 passed`)

// ---------------------------------------------------------------- Repair
if (failed.length) {
  phase('Gate')
  const repaired = await parallel(failed.map((v) => () =>
    agent(
      `${PREAMBLE}

## Stage ${v.stage} FAILED its verification gate at \`${ROOT}\`. Fix the root cause.

### Defects found by the independent verifier
${(v.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Full check results
${(v.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

Fix the underlying design or logic error, not the symptom. **Do not weaken or delete a test to make
it pass** — if a test is genuinely wrong, say so explicitly and explain why. Re-run the failing
checks yourself, plus the full suite, before finishing.`,
      { label: `repair:${v.stage}`, phase: 'Gate', model: 'opus' }
    )
  ))
  log(`Repaired ${repaired.filter(Boolean).length} stage(s) — re-verify in the next wave's preflight`)
  return { wave: 'S3-S5', verdicts: final, repaired: repaired.filter(Boolean).length, failedStages: failed.map((v) => v.stage) }
}

return { wave: 'S3-S5', verdicts: final, repaired: 0, failedStages: [] }
