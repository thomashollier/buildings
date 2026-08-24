export const meta = {
  name: 'buildings-amendment-2',
  description: 'Correct the six rule-model design defects the S7 verifier found, before the renderer and block waves',
  whenToUse: 'Between waves 3 and 4. These are design defects, not code defects — the brief predicted them.',
  phases: [
    { title: 'Correct', detail: 'structure/roles side (opus) and termination/chronology side (opus)' },
    { title: 'Gate', detail: 'independent re-verification of every amendment item' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PRE = `Project at \`${ROOT}\` — a constraint-derived procedural building generator for
19th-century Paris. Stages S0-S7 are built; the suite reports 985 passed.

**Read \`Amendment 2\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** It is binding and overrides
anything earlier that conflicts. Also read \`${ROOT}/dev/PLAN.md\` and the relevant parts of
\`${OLD}/BRIEF.md\`.

These are **design** defects, not coding slips. The brief predicted them: the rule model is
"the most elegant part of the document and the part most likely to be wrong... Treat the first
typology as its test." You are that correction. If an amendment item is itself wrong, say so in
your report rather than forcing it through.

Python 3.11, \`from __future__ import annotations\`, frozen dataclasses, stdlib only.
The suite must be green when you finish, with new tests added for each item you implement.
**Do not weaken an existing test** to accommodate a change — if one genuinely encodes the old wrong
behaviour, delete it deliberately and say so explicitly in your report, with the reason.
`

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['passed', 'checks'],
  properties: {
    passed: { type: 'boolean' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'passed', 'evidence'],
        properties: { name: { type: 'string' }, passed: { type: 'boolean' }, evidence: { type: 'string' } },
      },
    },
    failures: { type: 'array', items: { type: 'string' } },
    design_problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Correct')

const [structReport, termReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/structure.py\`, \`roles.py\`,
\`qualify/context.py\`, and their tests.

Implement **A2.1, A2.2, A2.3**.

### A2.1 — make Role.ATTIC reachable. This is the big one.
Right now the role tally over 1200 situations is base 1200 / principal 1200 / upper 2536 /
mezzanine 607 / **attic 0**. \`structure.py\` never builds a storey above the cornice, so
\`within_comble\` is always False and every qualification rule keyed to ATTIC is dead code.

A Paris comble is not empty roof — it holds the *chambres de bonne*, lit by the dormers
\`terminate.py\` already emits. So: when the comble has enough clear height for a habitable storey,
emit a storey slot INSIDE the roof envelope, set \`within_comble\` True for it, and let
\`assign_roles\` label it ATTIC by the existing predicate ("the slot inside the roof envelope").
Where the comble is too shallow, no attic storey — and ATTIC legitimately does not appear.

Keep the role predicates derived. Do NOT special-case: the attic must fall out of "is this slot
inside the roof envelope?", exactly as the brief's predicate says.

Coordinate with the other agent: dormer count/placement should follow the attic storey's bay grid.
Expose what they need on the Grid/RoledGrid rather than having them recompute it.

### A2.2 — the entresol is a programme decision, not leftover budget
Measured rate by class: modest 42%, ordinary 64%, comfortable 57%, grand 43% — not monotonic,
because a mezzanine only appears where the class factor squeezed the budget enough to leave a short
slot. That is the right element for the wrong reason. On a boulevard an entresol over a shop is
MORE common the richer the building.

Decide the entresol from PROGRAMME — the ground-floor use (SHOP/CAFE/OFFICE want one, RESIDENTIAL
largely does not) and class — **before** the height budget is filled, then have the solver
accommodate it. After your change the rate must rise monotonically with class for a shop ground
floor, and be low for RESIDENTIAL. Write a test asserting exactly that.

### A2.3 — split the overloaded constant
\`_AMBITION_FRACTION\` is passed to \`compute_envelope\` as \`roof_fill\`, so one number decides both
how close the facade gets to its legal ceiling AND how full the comble is. A modest building gets
both a lower cornice and a shallower garret — backwards for where servants actually lived.
Split into two separately-named, separately-documented constants, each marked INFERRED (follow the
A1.3 precedent). Facade ambition and comble fill are different decisions.`,
    { label: 'fix:structure-roles', phase: 'Correct', model: 'opus' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/terminate.py\`, \`chronology.py\`,
\`catalogue.py\`, and their tests.

Implement **A2.4, A2.5, A2.6**.

### A2.4 — \`Silhouette.within\` must test what its name says
It measures setback from the **built eaves** rather than the **legal cornice**, so it answers a
strictly harder question than legality. Worse, \`env.ridge_height\` is computed by
\`compute_envelope\` as a height above the CORNICE and then re-anchored at the eaves — so in the
harness case 1.23 m of unused facade headroom is discarded rather than being available to the
comble. A building's roof can never reach into legal space its own facade declined to use.

Anchor containment at the **legal cornice**, which is what the gabarit actually constrains. Keep the
stricter built-eaves test available under a clearly different name if a caller wants it. Make sure
the S7 sweep (widths 6-40 m x years 1830/1860/1875/1890/1905) still shows every silhouette point
inside the envelope under the corrected anchoring.

### A2.5 — the roof "shape" axis duplicates a decision the decree already made
At 1885/comfortable the envelope is \`circular_arc\` while the chosen variant is named
\`diagonal_45_pedimented_dormers\`, because class lag means the arc variant is not yet available to
that class although the arc envelope is already law. Nothing checks the contradiction.

\`ROOF_SHAPE_VARIANTS\` is really a **dormer-and-ornament repertoire**. Rename the axis to what it
is, and **assert** that a chosen variant never contradicts \`env.roof_envelope\`.

This is the brief's legality-vs-fashion split and it must not blur here:
- comble GEOMETRY comes from the decree — 45° plane pre-1884, arc after, Bonnier's eighth-circle
  after 1902. Not negotiable, not subject to class lag.
- dormer form, cresting and ornament come from FASHION — ramped, class-lagged, retained by modest
  buildings long after the boulevards moved on.

### A2.6 — tie the two depth limits together
\`_comble_profile\` takes \`half_depth\` only to decide whether to append a flat terrasse; nothing
truncates a comble whose ridge inset exceeds half the parcel. It is safe today ONLY because
\`compute_envelope\` already depth-limits the ridge from the same \`site.parcel_depth\` — two modules
independently relying on the same unstated invariant.

This is a live hazard for the block stage: if a \`BlockDatums\` path supplies an envelope whose
\`parcel_depth\` disagrees with the site's, the roof silently runs past the middle of the parcel and
nothing errors. That is the same shape as the previous attempt's street-width failure, which is the
single named disaster this project exists to avoid.

Assert the invariant explicitly where the two meet, so it fails LOUDLY. Add a test that constructs
the disagreeing case and asserts it raises.

### Coordinate
The other agent is making \`Role.ATTIC\` reachable by emitting a habitable storey inside the comble.
Dormer count and placement should follow that attic storey's bay grid rather than being decided
independently. Read what they expose rather than recomputing it.`,
    { label: 'fix:terminate-chronology', phase: 'Correct', model: 'opus' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these corrections.
Read "Amendment 2" at the end of \`${ROOT}/dev/CONTRACTS.md\` — that is the spec.

Implementer claims (check them, do not trust them):
--- structure/roles ---
${(structReport || '(none)').slice(0, 2200)}
--- terminate/chronology ---
${(termReport || '(none)').slice(0, 2200)}
---

Verify every item by RUNNING code and reporting concrete numbers:

- **A2.1** Sweep >=1000 random situations (widths 5-42 m, years 1800-1914, all classes and ground
  programmes). Report the full role tally. \`ATTIC\` must now be non-zero, and must appear
  **only** where the comble genuinely has habitable clear height — check both directions, since a
  role that now fires everywhere is as wrong as one that fires nowhere. Confirm the attic falls out
  of the "inside the roof envelope" predicate and was not special-cased: read \`roles.py\` and grep
  for any hardcoded index or explicit attic branch. Confirm dormers follow the attic bay grid.
- **A2.2** Measure the mezzanine rate by class for ground=SHOP, >=200 situations per class. It must
  rise monotonically with class. Report all four percentages. Then measure for ground=RESIDENTIAL
  and confirm it is materially lower. Confirm the decision is made BEFORE the budget is filled —
  read the code path, do not infer it.
- **A2.3** Confirm two distinct named constants exist, both marked INFERRED, and that changing the
  facade-ambition one does NOT move the roofline. Demonstrate by patching each and reporting what
  moved.
- **A2.4** Confirm containment is anchored at the legal cornice. Re-run the S7 sweep (6-40 m x
  1830/1860/1875/1890/1905) and report violations and worst overshoot. Confirm the harness case's
  previously-discarded 1.23 m of headroom is now available to the comble — report the actual ridge
  heights before and after.
- **A2.5** Confirm the axis is renamed and that an assertion fires when a variant contradicts
  \`env.roof_envelope\`. **Construct the contradiction deliberately** (1885/comfortable was the
  reported case) and confirm it now raises or is prevented. Confirm comble geometry is NOT
  class-lagged while dormer ornament IS.
- **A2.6** Construct a \`BlockDatums\`/envelope whose \`parcel_depth\` disagrees with the site's and
  confirm it now raises LOUDLY rather than silently running the roof past mid-parcel.

Then: full suite, both guards in \`dev/harness/\`, and \`python3 dev/harness/first_building.py\` —
paste the storey stack and judge its architectural plausibility honestly for a c.1865 boulevard
immeuble. Also confirm no test was weakened or deleted to force a pass: inspect the test diffs.

\`passed: true\` only if every item is genuinely satisfied. Use \`design_problems\` for anything that
still looks wrong at the design level.`,
  { label: 'verify:amendment2', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
)

if (verdict && !verdict.passed) {
  log(`Amendment 2 gate FAILED: ${verdict.failures?.length || 0} defects — repairing`)
  const repair = await agent(
    `${PRE}

## The Amendment 2 corrections FAILED independent verification. Fix the root causes.

### Defects
${(verdict.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Check results
${(verdict.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

Fix the underlying error. Do not weaken tests or edit \`dev/harness/\` guards.
Re-run the failing checks and the full suite before finishing.`,
    { label: 'repair:amendment2', phase: 'Gate', model: 'opus' }
  )
  return { wave: 'amendment-2', verdict, repaired: true, repair }
}

return { wave: 'amendment-2', verdict, repaired: false }
