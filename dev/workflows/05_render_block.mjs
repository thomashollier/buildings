export const meta = {
  name: 'buildings-s8-s9',
  description: 'Stages S8-S9: renderer port with decisions stripped out, and the block level',
  whenToUse: 'Fourth build wave. Requires the IR to have stabilised (S7 green).',
  phases: [
    { title: 'Port+Block', detail: 'S8 renderer port (sonnet) and S9 block level (opus) in parallel' },
    { title: 'Gate', detail: 'independent verification incl. the previous attempt named failure' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PREAMBLE = `You are implementing one stage of a ground-up rewrite of a procedural building
generator for 19th-century Paris.

## Binding documents
\`${ROOT}/dev/PLAN.md\`, \`${ROOT}/dev/CONTRACTS.md\` (frozen), \`${OLD}/BRIEF.md\`\n**Read \`Amendment 1\` at the END of CONTRACTS.md — binding, and it overrides anything earlier that conflicts.**

## Available (S0-S7, gates passed) — read the source, do not guess
\`buildings.quantity\`, \`trace\`, \`rng\`, \`site\`, \`ir.nodes\`/\`serial\`, \`solver.fitting\`,
\`typologies.paris.{reglement, structure, roles, chronology, catalogue, qualify, compose, terminate, generate}\`

Python 3.11, frozen dataclasses, stdlib only. \`cd ${ROOT} && python3 -m pytest tests/ -q\` must pass.
Only touch files your stage owns.
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
        properties: { name: { type: 'string' }, passed: { type: 'boolean' }, evidence: { type: 'string' } },
      },
    },
    failures: { type: 'array', items: { type: 'string' } },
  },
}

phase('Port+Block')

const [renderReport, blockReport] = await parallel([
  () => agent(
    `${PREAMBLE}

## Files you own
\`src/buildings/render/svg/*.py\`, \`tests/unit/test_render.py\`

## Stage S8 — Port the renderer. PORT, do not rewrite.

Sources: \`${OLD}/backends/svg.py\` (1606 lines) and \`${OLD}/backends/svg_elements.py\` (1353 lines).
That is a lot of hard-won element drawing — cornices, mansards, dormers, ironwork, shopfronts,
rustication. **Reuse it.** Do not reinvent this geometry from scratch.

Entry point per CONTRACTS.md:
\`\`\`python
def render(node: Node, *, width_px: int = 1200, labels: bool = False) -> str
\`\`\`

### The one rule that matters
**The renderer decides nothing arguable.**
> "If a renderer is deciding anything a person could argue about, that decision is in the wrong place."

So on the way across, **move composition decisions OUT of the renderer**. The old renderer branches
on floor type, era, style preset and ornament level all over the place. Every one of those is a
qualification decision that now belongs upstream: the IR should already say *what* to draw, and the
renderer works out only *how to draw it*.

Concretely, when you hit such a branch in the old code, do one of:
- (a) the decision is already in the IR node's \`props\` — read it and draw
- (b) it is not — then it is MISSING from the IR. **Report it in your return value** as a gap for
  the qualification stage. Do not smuggle it into the renderer.

\`${ROOT}/dev/harness/check_renderer_dumb.py\` enforces this by AST scan: the renderer may not
branch on year, date, era, class, role, street width or prevalence. **Run it and make it pass.**
Do not edit that guard script to weaken it — it is not yours.

### Also build
- \`render/svg/contact_sheet.py\` — render N buildings into one grid SVG. Per the brief, contact
  sheets are "the cheapest way to catch the single broken outlier among many", so this is a real
  deliverable, not a nicety.
- Rendering the same IR twice must be byte-identical.
- Draw the silhouette from the \`SilhouetteNode\` polyline. **Do not re-derive roof geometry** —
  that is S7's job and the renderer must not have an opinion about it.`,
    { label: 'impl:S8-renderer', phase: 'Port+Block', model: 'sonnet' }
  ),

  () => agent(
    `${PREAMBLE}

## Files you own
\`src/buildings/block/block.py\`, \`tests/unit/test_block.py\`, \`tests/invariant/test_block_datums.py\`

## Stage S9 — The block level

Read BRIEF.md "The street is the unit, not the building", "Open question: what the block owns", and
"Build order → 8 — Block". Read the open-question section carefully: it is unresolved on purpose.

### The framing
> "A building on a nineteenth-century Paris street is not autonomous. Its cornice continues its
> neighbour's cornice. Its string courses and balcony lines run across the party wall. The block was
> conceived as one architectural object with several owners, and the regulation said so explicitly."

That last clause is the **circulaire du 21 septembre 1855** — within a block, balcony, cornice and
entablature lines must align from building to building. Take it from \`reglement\`, not from a literal.

> "Get this backwards and you spend forever bolting alignment onto a generator that was designed to
> produce isolated objects — the buildings will each be individually convincing and the street will
> read as a shelf of models."

### What to build
\`BlockDatums\`, \`Parcel\`, \`Block\`, \`subdivide()\`, \`solve_block()\` per CONTRACTS.md.

The block **always** owns frontage subdivision and adjacency — that part is irreducible under every
relation. For Paris it additionally owns the shared horizontal datums: cornice height, string course
levels, balcony levels.

**Strictly one-way.** The block resolves its facts and hands them DOWN to each building as
\`BlockDatums\`. A building never samples a block-level fact (I2).

### The named failure to prevent
> "In the previous attempt every building sampled its own street width independently — so buildings
> that were, by construction, on the same street disagreed about how wide it was, and their cornice
> lines did not line up. **Nothing errored.** The street simply looked subtly wrong, and the cause
> was a block-level fact being resolved per building."

Write a test that fails loudly if this ever recurs. It is the single most valuable test in this stage.

### Corners
A corner is **not a module type**. Where a corner is chamfered it becomes a **third short facade
with its own rhythm** — the join between two grammars. Give it its own concept. Do not try to fit it
into the row of bays; the brief says explicitly it will not fit.

### Scope discipline — deliberately NOT in this stage
- **No general binding system** for block relation. The brief defers that to the second typology
  port: "designing a general binding system now risks a mechanism that elegantly solves a problem
  nobody has." Paris aligns. Build alignment, concretely, and keep the channel one-way so contents
  can grow later.
- Frontage rhythm should vary plausibly along the run (parcels were not uniform), driven through
  \`DecisionStream\` so it stays deterministic and addressable.`,
    { label: 'impl:S9-block', phase: 'Port+Block', model: 'opus' }
  ),
])

phase('Gate')

const verdicts = await parallel([
  () => agent(
    `INDEPENDENT VERIFIER for stage S8 (renderer port) at \`${ROOT}\`. You did not write this code.

Implementer's claim (check it, don't trust it):
---
${(renderReport || '(none)').slice(0, 2500)}
---

## Gate G8
1. **The renderer is dumb.** Run \`python3 ${ROOT}/dev/harness/check_renderer_dumb.py\`; it must
   exit 0. Paste the output. Then **confirm the guard script itself was not weakened** —
   \`git diff\` it if there is history, and read it: it must still forbid year/date/era/class/role/
   street_width/prevalence. A passing check against a gutted guard is a FAIL.
2. **It actually draws.** Generate several buildings via \`generate()\` and render each. Assert valid
   SVG (parse it with \`xml.etree.ElementTree\`), non-trivial element count, and no exceptions.
   Report element counts.
3. **Byte-identical re-render.** Render the same IR twice; assert identical strings.
4. **The silhouette comes from the IR.** Grep the renderer for roof/mansard angle arithmetic. It
   should consume the \`SilhouetteNode\` polyline, not re-derive it. Quote what you find.
5. **Contact sheet.** Render 20 seeds into one grid; assert it succeeds and the file is well-formed.
   Save it to \`${ROOT}/dev/logs/contact_sheet_check.svg\` so a human can look at it.
6. **Reported IR gaps.** The implementer was asked to report decisions that were in the old renderer
   but missing from the IR. List them in your evidence — those are real follow-up work, not failures.`,
    { label: 'verify:S8', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  ),

  () => agent(
    `INDEPENDENT VERIFIER for stage S9 (block) at \`${ROOT}\`. You did not write this code.
Read BRIEF.md "The street is the unit" and "Open question: what the block owns".

Implementer's claim (check it, don't trust it):
---
${(blockReport || '(none)').slice(0, 2500)}
---

## Gate G9
1. **THE named failure.** Build a block of 8 buildings. Assert every building resolved EXACTLY ONE
   street-width value — the same one. Then assert their cornice heights are equal to within 1e-9.
   Report the actual values for all 8. This is the previous attempt's silent failure and the most
   important check here.
2. **One-way channel (I2).** Grep the building-side modules (structure, qualify, terminate) for any
   sampling of street width or cornice height when \`datums\` is supplied. There must be none.
   Also confirm nothing in \`block.py\` reads back from a generated building to decide a block fact.
3. **Shared datums are real.** Assert string-course and balcony levels align across neighbours to
   1e-9, and that the 6 m / 1855-alignment figures come from \`reglement\`, not literals.
4. **Frontage subdivision.** Assert parcels sum exactly to the block frontage, adjacency is
   consistent (each parcel's left/right neighbours agree with each other), and widths vary
   plausibly rather than being uniform. Report the width distribution.
5. **The corner is its own facade.** Assert a corner parcel produces a distinct short facade with
   its own bay rhythm — NOT a module inside the main row. Show the evidence.
6. **Determinism.** Same block + seed, 20 runs, identical output.
7. **Scope.** Confirm no general binding system was built (the brief defers it). A \`Binding\` class
   or relation-mode enum would be scope creep — report it if present.`,
    { label: 'verify:S9', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  ),
])

const final = verdicts.filter(Boolean)
const failed = final.filter((v) => !v.passed)
log(`Wave 4 gates: ${final.length - failed.length}/2 passed`)

if (failed.length) {
  const repaired = await parallel(failed.map((v) => () =>
    agent(
      `${PREAMBLE}

## Stage ${v.stage} FAILED its gate at \`${ROOT}\`. Fix the root cause.

### Defects
${(v.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Check results
${(v.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

Fix the underlying error, not the symptom. **Do not weaken or delete a test, and do not edit the
guard scripts in \`dev/harness/\`, to make a check pass.** Re-run the failing checks and the full suite.`,
      { label: `repair:${v.stage}`, phase: 'Gate', model: 'opus' }
    )
  ))
  log(`Repaired ${repaired.filter(Boolean).length} stage(s)`)
}

return { wave: 'S8-S9', verdicts: final, failedStages: failed.map((v) => v.stage) }
