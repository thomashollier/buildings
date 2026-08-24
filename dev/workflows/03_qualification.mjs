export const meta = {
  name: 'buildings-s6-s7',
  description: 'Stages S6-S7: qualification rules, layered composition, termination silhouette',
  whenToUse: 'Third build wave. This is the UNPROVEN part of the design — the rule model is on trial here.',
  phases: [
    { title: 'Qualify', detail: 'S6 context->properties rules and layered composition (opus)' },
    { title: 'Terminate', detail: 'S7 comble inscribed in envelope, silhouette in the IR' },
    { title: 'Gate', detail: 'independent verification incl. the first-week end-to-end acceptance' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PREAMBLE = `You are implementing one stage of a ground-up rewrite of a procedural building
generator for 19th-century Paris. Thesis: **model the constraints and the style comes out for free.**

## Binding documents
- \`${ROOT}/dev/PLAN.md\`, \`${ROOT}/dev/CONTRACTS.md\` (frozen), \`${OLD}/BRIEF.md\`\n**Read \`Amendment 1\` at the END of CONTRACTS.md — binding, and it overrides anything earlier that conflicts.**

## Available (S0-S5, gates passed) — READ THE SOURCE, do not guess
\`buildings.quantity\`, \`buildings.trace\`, \`buildings.rng\`, \`buildings.site\`,
\`buildings.ir.nodes\`/\`serial\`, \`buildings.solver.fitting\`,
\`buildings.typologies.paris.{reglement, reglement_adapter, structure, roles, chronology, catalogue}\`

## Honesty about where you are
BRIEF.md's "Confidence" section says of the rule model — phases, derived roles, layered composition —
**"This is the most elegant part of the document and the part most likely to be wrong. Nothing here
has been implemented. Treat the first typology as its test."** You are that test. If the design does
not survive contact, say so plainly in your report rather than forcing it through.

## Working rules
Python 3.11, \`from __future__ import annotations\`, frozen dataclasses, stdlib only.
\`cd ${ROOT} && python3 -m pytest tests/ -q\` must pass. Only touch files your stage owns.

## Invariants
I1 phases read strictly backwards  I2 buildings receive block facts  I3 quantities carry their kind
I4 every element records its rule  I5 seed + situation is deterministic
`

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['stage', 'passed', 'checks'],
  properties: {
    stage: { type: 'string' },
    passed: { type: 'boolean' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'passed', 'evidence'],
        properties: {
          name: { type: 'string' },
          passed: { type: 'boolean' },
          evidence: { type: 'string' },
        },
      },
    },
    failures: { type: 'array', items: { type: 'string' } },
    design_problems: {
      type: 'array', items: { type: 'string' },
      description: 'places the rule-model DESIGN itself (not the code) looks wrong — the brief expects some',
    },
  },
}

phase('Qualify')

const qualReport = await agent(
  `${PREAMBLE}

## Files you own
\`src/buildings/typologies/paris/qualify/{__init__,context,base,period,klass}.py\`,
\`src/buildings/typologies/paris/compose.py\`, \`tests/unit/test_qualify.py\`,
\`tests/unit/test_compose.py\`

## Stage S6 — Qualification and layered composition

Read BRIEF.md "The rule model" phases 3 and 4, "Consequences", "Costs to go in with your eyes open
about", and "Paris: the specifics → Qualification context".

### The context (\`qualify/context.py\`)
\`QualContext\` exactly as CONTRACTS.md lists it — and that list is the brief's list, deliberately.
It is **read-only, complete before qualification begins, and never mutated by it.** Frozen dataclass;
mutation must raise.

"If a rule needs a fact not on this list, that is a signal to extend the context deliberately rather
than to reach around it." So: if you need something more, ADD IT TO THE CONTEXT and say so in your
report. Do not have a rule import SiteContext or reach into the Grid.

### The rules
A rule is \`(QualContext, DecisionStream) -> Properties | None\`. \`None\` means "no opinion".
\`Properties\` is SPARSE — unset keys mean no opinion, which is exactly how layering works.

**Applicability is explicit, identity is derived.** The whole point:
> "A list saying that balconies go on the second and fifth floors does not say *why*, so it cannot
> be composed with anything, argued with, or carried to another city."

So write **"a balcony where the floor is at least 6 m above the pavement"** — which is the actual
1823 ordonnance — not "floors 2 and 5". Take the 6 m and the 0.80 m projection from
\`reglement.balcony_rule\`; do not hardcode them. The correctness test is that removing the mezzanine
moves the balcony up a floor by itself, because the rule is about height above the pavement.

Cover at minimum: opening type, window surround, balcony, ironwork, keystone/mascaron, socle
treatment, cornice, string course, shopfront/ground-floor treatment, ornament density.
Pull variant choices from \`chronology.available(feature, year, klass)\` weighted by prevalence,
and sample them through \`DecisionStream.at(path)\` with STABLE paths so decisions stay addressable.

**Treatment diminishes with rank from the principal floor** — that is what \`rank_from_principal\`
is for, and it is why you do not need a per-floor table.

### Layering (\`compose.py\`)
\`Layer\` and \`resolve()\` per CONTRACTS.md. Base vocabulary → period → class → site → override.
Later layers win; **specificity breaks ties within a layer**. Equal order AND equal specificity is a
CONFLICT — **raise, never silently pick one.** Silent tie-breaking is how this design becomes
nondeterministic-looking and unbeatable to debug.

User overrides are simply the top layer. There is NO parallel override mechanism.

### Traceability is not optional
Every property that survives resolution records the \`RuleId\` that produced it, and every emitted
node gets a non-empty trace (I4). Per the brief: "Build the 'why' tooling first, not last... Defer
that and you will spend weeks bisecting rule sets by hand and conclude the approach was a mistake."

Provide a working \`explain(node_id)\` path that a human can actually read, and demonstrate it in a test.

### A storey never lays out
It FILLS the shared grid solved in S3. The rule is "for this slot, on a floor of this role, what
occupies it?" — which cannot drift out of vertical alignment because there is only one grid.
If you find yourself computing an x-position, you are doing S3's job.

### Do NOT build a DSL
"Rules can be ordinary functions in the host language for a long time. The discipline is in the
shape — context in, properties out, layered, traceable — not in having a text format." Plain Python
functions. No parser, no config format.`,
  { label: 'impl:S6-qualification', phase: 'Qualify', model: 'opus' }
)

phase('Terminate')

const termReport = await agent(
  `${PREAMBLE}

## Files you own
\`src/buildings/typologies/paris/terminate.py\`, \`src/buildings/typologies/paris/generate.py\`,
\`tests/unit/test_terminate.py\`, \`tests/invariant/test_silhouette_envelope.py\`

## Stage S7 — Termination, plus the end-to-end assembly

Read BRIEF.md "Build order → 6 — Termination" and the roof paragraph in "The feature families
worth dating".

### \`terminate.py\`
\`Silhouette\` and \`terminate(...)\` per CONTRACTS.md.

The comble is **inscribed in the regulatory envelope** computed in S3 — get the envelope from
\`GabaritEnvelope\` (\`slope_profile\`, \`setback_at\`, \`mansard_angles\`) rather than inventing roof
geometry. The roof shape was not chosen by anyone; it is the residue of the rule:
- pre-1884: combles bounded by the **45° diagonal** springing from the eaves
- 1884+ (Alphand): the diagonal is replaced by an **arc of a circle whose radius depends on street
  width**, which is what lets a further storey be built set back from the facade
- 1902+ (Bonnier): eighth-of-a-circle arc continued by a 45° oblique

**The silhouette is emitted as a polyline IN THE IR** (\`SilhouetteNode\`), not derived by the
renderer. Dormers, chimneys and any cresting are IR nodes too, positioned against the bay grid.
Dormer form and cresting come from \`chronology\` (pedimented dormers canonical 1853-84; varied
shapes and iron cresting 1884+), never from a period test.

\`Silhouette.within(envelope)\` must genuinely check containment.

### \`generate.py\` — the end-to-end assembly
Wire the whole pipeline into one entry point:

\`\`\`python
def generate(site: SiteContext, datums: BlockDatums | None = None) -> tuple[BuildingNode, TraceLog]
\`\`\`

STRUCTURE → ROLES → QUALIFICATION (composed layers) → TERMINATION → a single \`BuildingNode\` tree
plus its \`TraceLog\`. Each phase receives the frozen output of the last and never reaches back (I1).

This is the brief's **first-week acceptance**: "Reproduce one real building's elevation end to end
through all four phases, with a trace explaining every element, before generalising anything."
So also write \`${ROOT}/dev/harness/first_building.py\` — a script that generates one plausible
canonical building (a Second Empire mid-block immeuble on a ~20 m boulevard, ordinary-to-comfortable
class, c. 1865), prints the storey stack with roles and heights, and prints the FULL TRACE: for every
element, the rule that produced it and why. Run it and confirm the output is readable and complete.

The qualification stage reported:
---
${(qualReport || '(none)').slice(0, 2000)}
---`,
  { label: 'impl:S7-termination', phase: 'Terminate', model: 'opus' }
)

phase('Gate')

const verdicts = await parallel([
  () => agent(
    `You are an INDEPENDENT VERIFIER for stage S6 (qualification + composition) at \`${ROOT}\`.
You did not write this code. Read \`${ROOT}/dev/CONTRACTS.md\` and BRIEF.md's "The rule model".

Implementer's claim (check it, don't trust it):
---
${(qualReport || '(none)').slice(0, 2500)}
---

## Gate G6 — run real code, report real numbers
1. **Context is immutable.** Attempt to mutate a \`QualContext\`; assert it raises. Grep the rule
   modules for any import of \`SiteContext\`, \`Grid\`, or \`reglement\` — rules must read the context
   only. List violations.
2. **The balcony rule is the ordinance, not a floor list.** Read the balcony rule source. It must
   test height above the pavement and take 6 m / 0.80 m from \`reglement.balcony_rule\`, not from a
   literal in the rule file and not from a list of floor indices. Grep for hardcoded \`6\`/\`0.8\`
   and for any floor-index list. Quote the actual rule body in your evidence.
3. **The mezzanine test — the one the brief names.** Generate two otherwise-identical buildings, one
   with a mezzanine and one without. Assert the balcony lands on a DIFFERENT storey index but at
   effectively the SAME height above the pavement, with no rule mentioning mezzanines. Report both
   storey indices and both heights. This is the single most important check in this gate.
4. **Layering truth table.** Construct layers that conflict and assert: later order wins; within a
   layer higher specificity wins; equal order AND equal specificity RAISES rather than silently
   picking. Show all three outcomes actually occurring.
5. **Trace completeness (I4).** Generate a building; assert EVERY node has a non-empty trace.
   Report the node count and any untraced nodes. Then call \`explain()\` on a leaf and paste the
   output — judge whether a human could actually answer "why is this here?" from it. A trace that is
   technically non-empty but says nothing useful is a FAIL; say so.
6. **No layout in qualification.** Grep the qualify package for x-position arithmetic. Storeys fill
   the grid; they do not lay out.
7. **No DSL.** Confirm rules are plain Python functions — no parser, no config format.
8. **Addressability (I5).** Pin one decision via the override layer; assert every OTHER decision in
   the building is unchanged. This is the brief's addressability requirement and it is easy to get
   wrong. Report how many other decisions shifted — the answer must be zero.

\`passed: true\` only if every check passes. Use \`design_problems\` for places the DESIGN, not the
code, looks wrong — the brief expects some and it is useful signal, not a failure.`,
    { label: 'verify:S6', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  ),

  () => agent(
    `You are an INDEPENDENT VERIFIER for stage S7 (termination + end-to-end) at \`${ROOT}\`.
You did not write this code. Read \`${ROOT}/dev/CONTRACTS.md\` and BRIEF.md's build order.

Implementer's claim (check it, don't trust it):
---
${(termReport || '(none)').slice(0, 2500)}
---

## Gate G7 — run real code, report real numbers
1. **Silhouette stays inside the envelope.** Sweep street width 6-40 m x year 1830/1860/1875/1890/1905.
   For each, assert every silhouette point lies within the \`GabaritEnvelope\` (tolerance 1e-6).
   Report the count of violations and the worst overshoot in metres.
2. **The 1884 discontinuity is visible in the IR.** Generate the same site at 1883 and 1885. Assert
   the roof profile changes SHAPE — a 45° plane before, an arc after — and that this is readable
   from the IR without running the renderer. Report the actual profiles. This is the brief's
   "move the date past a decree and the roofline should change shape" test.
3. **Silhouette is IR-owned.** Assert a \`SilhouetteNode\` with a real polyline exists in the tree.
4. **End-to-end determinism (I5).** Run \`generate()\` 50 times on the same site+seed; assert the
   serialised IR is byte-identical every time. Then change ONLY the seed and assert it differs.
5. **Phase order (I1).** Confirm no phase mutates an earlier phase's output — all the intermediate
   objects are frozen and \`generate()\` passes them forward only. Try mutating each; assert raises.
6. **The first-week acceptance.** Run \`python3 ${ROOT}/dev/harness/first_building.py\`. Paste a
   representative chunk of its output. Judge honestly: does the trace actually explain every
   element? Is the storey stack plausible for a c.1865 boulevard immeuble — ground floor tall,
   a principal floor above, storeys tapering upward, cornice near the legal limit, comble above?
   Report the actual heights. If the numbers are architecturally implausible, FAIL it and say why.
7. **Steps not ramps, end to end.** Sweep street width and confirm total built height moves in steps.

\`passed: true\` only if every check passes.`,
    { label: 'verify:S7', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  ),
])

const final = verdicts.filter(Boolean)
const failed = final.filter((v) => !v.passed)
log(`Wave 3 gates: ${final.length - failed.length}/2 passed`)

if (failed.length) {
  const repaired = await parallel(failed.map((v) => () =>
    agent(
      `${PREAMBLE}

## Stage ${v.stage} FAILED its verification gate at \`${ROOT}\`. Fix the root cause.

### Defects
${(v.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Check results
${(v.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

${v.design_problems?.length ? `### Design problems flagged\n${v.design_problems.join('\n')}\n` : ''}

Fix the underlying error, not the symptom. **Do not weaken or delete a test to make it pass.**
If the RULE MODEL DESIGN itself is what is wrong — which the brief explicitly expects is possible —
say so clearly rather than forcing it through. Re-run the failing checks and the full suite.`,
      { label: `repair:${v.stage}`, phase: 'Gate', model: 'opus' }
    )
  ))
  log(`Repaired ${repaired.filter(Boolean).length} stage(s)`)
}

return {
  wave: 'S6-S7',
  verdicts: final,
  failedStages: failed.map((v) => v.stage),
  designProblems: final.flatMap((v) => v.design_problems || []),
}
