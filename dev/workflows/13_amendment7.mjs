export const meta = {
  name: 'buildings-amendment-7',
  description: 'Move ornament counts to the IR, fix the chimney properly, and get the repo green',
  whenToUse: 'The repo is RED. This is the last build wave before validation.',
  phases: [
    { title: 'Correct', detail: 'ornament counts to qualification (opus), chimney + shop head (sonnet)' },
    { title: 'Gate', detail: 'independent verification; the repo must end GREEN' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century Paris.

**Read \`Amendment 7\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

## The repo is currently RED
\`python3 -m pytest tests/ -q\` -> 1 failed, 1271 passed, because
\`dev/harness/check_renderer_dumb.py\` exits 1 with **13 violations**. Getting it green — honestly,
by moving decisions upstream rather than by silencing the check — is the point of this wave.

**The guard has been rewritten by the orchestrator and agents may not edit it.** It was measured at
7/7 offences caught and 0/6 false positives against real test cases. If you believe it produces a
false positive, REPORT IT with the case; do not touch the file. Same for
\`check_no_period_branching.py\`.

Python 3.11, frozen dataclasses, stdlib only. Rasterise and LOOK at visual changes
(\`rsvg-convert -w 900 in.svg -o out.png\`). Do not weaken tests.
`

const VERDICT = {
  type: 'object',
  required: ['passed', 'checks'],
  properties: {
    passed: { type: 'boolean' },
    checks: { type: 'array', items: { type: 'object', required: ['name','passed','evidence'],
      properties: { name:{type:'string'}, passed:{type:'boolean'}, evidence:{type:'string'} } } },
    failures: { type: 'array', items: { type: 'string' } },
    design_problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Correct')

const [ornReport, chimReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/qualify/*\`, \`compose.py\`, \`catalogue.py\`,
\`src/buildings/render/svg/elements.py\` (consumption side), and their tests.

Implement **A7.2 and A7.5**.

### A7.2 — move the ornament counts into qualification
Run \`python3 ${ROOT}/dev/harness/check_renderer_dumb.py\` to see all 13. They are modillions,
dentils, rustication coursing, balcony brackets, rail bars, scrolls, waves, lozenges, cresting and
zinc seams — each deciding **how many** of something to draw from a dimension and a number the
renderer chose.

Ornament density is compositional. The brief lists *"the scale and density of ornament"* among the
**proportional** quantities that move with ambition and budget. So these counts belong in
qualification, driven by class and \`rank_from_principal\`, and must arrive in the IR.

Emit a count (or a spacing the IR owns) per ornamented element; have \`elements.py\` consume it.
Richer buildings get denser, finer ornament; modest ones get less — that is the point, and it
should be visible when you compare a modest and a grand facade side by side.

**The rail-bar case is the instructive one.** \`ceil(w / gap_max)\` where \`gap_max\` comes from the
IR is CORRECT and stays — a balustrade gap narrow enough for a child's head is an ABSOLUTE quantity
and the renderer is honouring it, not inventing it. Only the
\`_UNGUARDED_RAIL_BAYS_PER_METRE\` fallback is the offence. Keep the distinction; do not "fix" the
correct one.

### A7.5 — blind-panel runs
19% of special columns read as a near-full stack of one element (worst: 4 consecutive
\`blind_panel\` storeys out of 5). The letter of A6.2 holds, the spirit does not. Cap consecutive
identical fills so a special bay varies up the facade.

**Finish with \`check_renderer_dumb.py\` exiting 0 and the full suite green.**`,
    { label: 'fix:ornament-counts', phase: 'Correct', model: 'opus' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/terminate.py\`, \`qualify/base.py\` (shop head only),
\`src/buildings/render/svg/render.py\`, and their tests.

Implement **A7.3 and A7.4**.

### A7.3 — the chimney fix traded one defect for a worse one
A6.4 was implemented by having \`render.draw_building\` **overwrite** the IR's chimney \`y\` with a
surface height computed in the renderer. So "the base sits on the drawn surface" is true *by
construction* (0.000 m over 426 chimneys) while the IR now states a base up to **7.603 m** away
from what is drawn. That is the renderer discarding stated IR geometry — the same offence as A4.1
and A6.8, which we have now hit three times.

Worse, holding the head height absolute while dropping the base turned hip-end *souches* into
smokestacks: visible stacks up to **12.7 m**, 2,170 of 5,088 over 2.5 m. Three brown poles stand
outside the roof mass entirely.

**Fix it at the source.** The roof surface height at the stack's x is a STRUCTURAL fact: compute it
in \`terminate\`, put it in the IR, and have the renderer draw exactly what it is given. Remove the
renderer's override entirely.

A *souche* is roughly 0.5–1.5 m of brick above the tiles where it emerges — **its height above the
surface is what stays roughly constant**, not its apex. Fix the height model too, not just the base.

Verify by rendering a corner parcel and a 10-parcel block, rasterising, and LOOKING at the roofs.
No poles in the sky, no smokestacks.

### A7.4 — A6.8 closed the gap from the wrong end
\`draw_opening\`'s shop branch now draws \`head\` correctly, but
\`qualify/base.ground_floor_of_a_shop\` hard-codes \`opening_head='flat'\` and nothing can produce
anything else — so all 1,944 shop bays carry \`flat\` and the branch is dead code. The contract's
premise was made false rather than satisfied.

Segmental and round-headed *devantures* are common in Paris. Let \`chronology\` decide the head form
by date and class, the way every other fashion axis works, so the branch is actually reachable.`,
    { label: 'fix:chimney-shophead', phase: 'Correct', model: 'sonnet' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 7\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claims (check, do not trust):
--- ornament counts ---
${(ornReport || '(none)').slice(0, 2000)}
--- chimney/shop head ---
${(chimReport || '(none)').slice(0, 2000)}
---

## Verify

1. **THE REPO MUST BE GREEN.** Run \`python3 -m pytest tests/ -q\` and both guards in
   \`dev/harness/\`. All must pass. Report exact counts and exit codes.
2. **The guards were not touched.** \`git diff\` is unavailable (no history), so compare content:
   \`check_renderer_dumb.py\` must still contain the \`ProportionChecker\` taint analysis with its
   7/7-catching logic, and \`check_no_period_branching.py\` its AST visitor. If either was edited to
   make a check pass, that is an immediate hard FAIL — say so loudly.
3. **A7.2 — counts genuinely moved.** For each of the 13 former violations, confirm the count now
   comes from the IR and that \`elements.py\` consumes it. Then confirm ornament density actually
   VARIES with class: render modest vs grand at a fixed site and report modillion/dentil/bracket
   counts for each. If they are identical, the count moved but the decision did not.
4. **A7.2 — the correct case survived.** Confirm \`ceil(w / gap_max)\` with \`gap_max\` from the IR
   is still there and was not "fixed". Balustrade gap is ABSOLUTE; the renderer honouring it is right.
5. **A7.3 — no renderer override.** Grep \`render.py\` for any overwrite of a chimney's IR \`y\`.
   Then assert IR-stated base == drawn base **because the IR is right**, not because the renderer
   recomputed it. Report the worst |IR y - drawn y| and the visible stack-height distribution —
   nothing should approach 12.7 m. Rasterise a corner parcel and a 10-parcel block and LOOK: no
   poles in the sky, no smokestacks.
6. **A7.4** — confirm shop head form is now produced by chronology and that non-flat heads actually
   occur. Report the head census by date; if it is still 100% flat, the branch is still dead.
7. **A7.5** — report the consecutive-identical-fill run-length distribution for special columns.
8. **Regression** — A4/A5/A6 wins intact: exactly one entrance per building, entrance byte-identical
   across classes, window area ratio ~1.9x, no full-frontage glass rect, chamfers pierced and roofed.
9. **Look.** Harness facade + 10-parcel block rasterised >=900 px, saved to
   \`dev/logs/facade_final.png\` and \`dev/logs/block_final.png\`. Rank what a knowledgeable viewer
   would still flinch at.

\`passed: true\` only if the repo is GREEN and every item holds.`,
  { label: 'verify:amendment7', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-7', verdict }
