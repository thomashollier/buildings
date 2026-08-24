export const meta = {
  name: 'buildings-amendment-10',
  description: 'Close the four A9 residuals and get the repo green',
  whenToUse: 'Final pass on the Second Empire lock. The suite is currently red on a zero-width node.',
  phases: [
    { title: 'Correct', detail: 'geometry residuals (sonnet) and the class/count residuals (opus)' },
    { title: 'Gate', detail: 'independent verification; the repo must end green' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. Goal: **canonical Second Empire (1853-1870) solid before branching out.**

**Read \`Amendment 10\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Evidence: \`${ROOT}/dev/reference/daly_measurements.json\`, \`${ROOT}/dev/logs/DALY_MEASUREMENTS.md\`,
\`${ROOT}/dev/reference/SOURCES.md\`.

## State
Amendment 9 calibrated the canonical case against César Daly's 1864 measured plates. The carriage
door is SOURCED at 2.60 m from a printed callout; the hip arris has one source of truth; the golden
master bites. Two sourcing-honesty defects were already fixed by the orchestrator (a factually wrong
citation, and a twelfth quantity promoted on WEAK data).

**The suite is currently RED: 1402 passed, 1 failed.** Getting it green honestly is part of this wave.

Python 3.11, frozen dataclasses, stdlib only. Do not weaken tests. **Do not edit any guard in
\`dev/harness/\`** — report a false positive instead. Rasterise and LOOK at visual changes.

## A standing note on sourcing
Quantities are SOURCED only if \`daly_measurements.json\` → \`recommendation_summary\` lists them
there. WEAK means ordering only. INSUFFICIENT means leave it INFERRED. Do not promote anything.`

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

const [geoReport, clsReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/block/block.py\`, \`terminate.py\`, \`src/buildings/render/**\`, tests.

Implement **A10.4 and A10.5**.

### A10.5 first — the suite is red because of it
\`b/roof/no_dormer0\` (kind=\`special\`) is emitted with \`w=0.0\`, 4,412 occurrences, by rule
\`paris.terminate.dormer.clipped_by_the_hip\`. The invariant fuzzer catches it.

A dormer clipped out of existence should not be emitted at all. **An element with no extent is a lie
in the IR** — the same defect class as A6.6's zero-height ironwork, which we already fixed once.
Emit nothing, or emit something with extent. Then confirm the fuzzer passes.

### A10.4 — the chamfer roof draws a self-crossing hip
\`block.py:_chamfer_roof()\` rebuilds the pan coupé's roof node from the parent building's roof props
with \`w\` overridden to the chamfer width. It carefully re-counts \`seam_count\` for the narrower
face but not every width-derived value, so the hip geometry crosses itself — **a bowtie in the sky
at both ends of every block.**

This is the FIFTH time one module has held a width-derived opinion another module contradicts
(A4.1, A6.8, A7.3, A9.3, now this). Fix it the way A9.3 did: **derive once, put it in the IR,
consume it.** Copying a props dict and patching a few keys is the pattern that keeps producing this
bug — a chamfer roof should be *composed for the chamfer*, not inherited and patched.

While you are there, consider whether \`check_ir_is_consumed.py\` could be extended to catch
"props copied from another node and partially overridden". **Propose it in your report; do not
implement it** — guards are not yours to edit.

Verify by rasterising a 10-parcel block with corners at >=900 px and LOOKING at both ends.`,
    { label: 'fix:geometry-residuals', phase: 'Correct', model: 'sonnet' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/{structure,catalogue,terminate}.py\`, \`qualify/*\`, tests.

Implement **A10.1, A10.2, A10.3**.

### A10.1 — a stated ABSOLUTE bound is enforced on one side only
A9 added a tripwire for a slot WIDER than \`_BAY_PITCH_MAX\`, and it works (reverting the door to
3.00 m makes \`solve_structure\` raise). There is no guard below. The porte piétonne slot is 2.35 m
against \`_BAY_PITCH_MIN\` 2.70 m, giving a measured centre-to-centre pitch of **2.575 m** on modest
and ordinary buildings; narrow specials give **2.30 m**.

Decide which is true and make the code say it:
  - if the pitch floor genuinely does not apply to an entrance or a narrow special, **state that
    explicitly** in the constant's docstring and guard what the floor *does* apply to; or
  - if it does apply, the slot is too narrow — fix it.

What is not acceptable is a stated ABSOLUTE bound silently violated on one side while enforced on
the other.

### A10.2 — D6 improved, not closed
GRAND has fewer openings than MODEST on **2 of 8** frontages (18 m, 20 m), down from 6 of 8; the
named 16 m case is fixed. Residual cause: the carriage slot (3.40 m) takes 1.05 m more frontage
than the pedestrian slot (2.35 m).

**This may be correct.** A building with a carriage arch genuinely spends frontage on it, and Daly
shows entitlement to a carriage entrance is exactly what distinguishes the classes (Première 4/4,
Deuxième 3/10, Troisième 0/2). If so, the defect is in the COMPARISON, not the model: like should be
compared with like (same entrance type), and the test should say so.

Decide on the architecture, implement accordingly, and **record the reasoning** — if you conclude
the model is right and the metric was wrong, say that plainly rather than contorting the model to
satisfy a bad comparison.

### A10.3 — dormer count still falls as class rises
9 of 21 class/frontage combinations show it falling (12 m: 4/4/3/3; 18 m: 6/6/5/5; 20 m: 7/7/6/6).
A comble is floor, not show: dormer count should follow the comble's own frontage and geometry, not
class, and must never fall as class rises. Note the comble being class-invariant is CORRECT and
Daly-supported — do not change that.`,
    { label: 'fix:class-residuals', phase: 'Correct', model: 'opus' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 10\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claims (check, do not trust):
--- geometry --- ${(geoReport || '(none)').slice(0, 1800)}
--- class --- ${(clsReport || '(none)').slice(0, 1800)}

## Verify
1. **THE REPO MUST BE GREEN.** Full suite plus all three guards; report exact counts and exit codes.
   It was 1402 passed / 1 failed.
2. **A10.5** — zero-extent nodes. Sweep >=1000 buildings; assert NO node has w==0 or h==0 except
   kinds documented as line markers (keystones were a legitimate case). Report the census.
3. **A10.4** — rasterise a 10-parcel block with corners at >=900 px and LOOK at both ends. Is the
   bowtie gone? Then grep for any remaining "copy another node's props and patch a few keys"
   pattern and report what you find, whether or not it currently misbehaves.
4. **A10.1** — confirm the pitch floor is either documented as not applying to entrances/specials
   AND guarded for what it does apply to, or the slot was widened. Re-measure the minimum
   centre-to-centre pitch across a sweep and report it by slot type.
5. **A10.2** — re-measure openings per storey by class across 8 frontages. If the implementer
   concluded the metric was wrong rather than the model, **judge that argument on its merits** and
   say whether you accept it. Report the like-for-like comparison (same entrance type).
6. **A10.3** — dormer count by class across 7 frontages x 3 street widths. Must not fall as class
   rises. Report the full table.
7. **Sourcing audit, again.** Re-check that nothing new was promoted to SOURCED beyond the eleven,
   and that all SOURCED citations are factually accurate against \`daly_measurements.json\` — one
   was previously wrong on building AND plate. Verify each names a real plate that exists in
   \`dev/reference/images/daly-1864/\`.
8. **Guards untouched** — read all three, confirm logic intact.
9. **Regressions** — golden master still bites; door still 2.60 m SOURCED and byte-identical across
   classes; chimney count still matches the IR; window width class-flat while noble height rises.
10. **Look.** \`dev/logs/facade_a10.png\`, \`dev/logs/block_a10.png\`. Compare against the Daly
    elevations. Answer criterion 1 directly: would someone who knows Paris flinch, and at what?

\`passed: true\` only if the repo is GREEN and every item holds.`,
  { label: 'verify:amendment10', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-10', verdict }
