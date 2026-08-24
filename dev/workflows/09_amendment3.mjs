export const meta = {
  name: 'buildings-amendment-3',
  description: 'Retract A2.4 and restore the legally-correct comble springing, then run the renderer and block waves',
  whenToUse: 'A2.4 was a bad specification. This corrects it before S8/S9 build on the roof geometry.',
  phases: [
    { title: 'Correct', detail: 'restore eaves springing, recover headroom the lawful way' },
    { title: 'Gate', detail: 'independent verification against the regulation text itself' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

phase('Correct')

const fix = await agent(
  `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century Paris.

**Read \`Amendment 3\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** It retracts an earlier
amendment (A2.4) that was specified incorrectly, and it is binding.

## Context you need

A2.4 told a previous agent to anchor comble containment at the **legal cornice**. That was wrong.
The regulation anchors it at the **built eaves** (*égout du toit*). Read these two places in
\`src/buildings/typologies/paris/reglement.py\` before touching anything:
- line ~14, the module docstring: "combles must be inscribed below a 45° diagonal springing from
  the eaves (égout du toit)"
- \`GabaritEnvelope.slope_profile\`'s docstring (~line 317), which anticipates this exact case:
  "A building whose stone face stopped below its legal cornice springs its comble from its own
  eaves and may run it further above *them* than the ridge stands above the cornice, so
  \`terminate\` traces the same curve to a taller top."

So the previous eaves-anchored behaviour was legally right, and the A2.4 change made \`within\`
**too permissive** — it now accepts combles the 45° diagonal from the real eaves forbids.

## You own
\`src/buildings/typologies/paris/terminate.py\`, \`structure.py\` (only the comble-height path),
and their tests.

## Implement A3.1

1. **Revert \`Silhouette.within\` to spring from the built eaves.** That is the legal question.
   Keep a legal-cornice query if it is useful, but under a different name — \`within\` means
   "inscribed below the diagonal springing from this building's own eaves".

2. **Recover the headroom the lawful way.** A comble springing from eaves below the legal cornice
   may run *further above those eaves* than \`ridge_height\` stands above the cornice — by tracing
   the **same curve** to a taller top. That is what \`slope_profile(top=...)\` is for. Derive the
   taller top from the envelope curve and the parcel depth. Do NOT re-anchor the springing.

3. **Never mix anchors in one arithmetic.** Anything computed above the cornice must not be applied
   at the eaves without an explicit conversion. Put an assertion or a clearly-named conversion at
   that boundary so this cannot recur silently — it is what caused the original confusion.

4. Every silhouette point must still come from \`setback_at\`.

Remove any test that asserts the A2.4 behaviour, and say so explicitly in your report with the
reason. Do not leave a test asserting a rule we have retracted. The suite must be green.

Report: what you reverted, how the taller-top derivation works, and the actual ridge heights for
the harness case (20 m street / 1865 / comfortable / shop) before and after.`,
  { label: 'fix:comble-springing', phase: 'Correct', model: 'opus' }
)

phase('Gate')

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

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this fix.

Read \`Amendment 3\` at the end of \`${ROOT}/dev/CONTRACTS.md\`, and — importantly — verify it
against the PRIMARY SOURCE: the docstrings and code of
\`src/buildings/typologies/paris/reglement.py\` (module docstring line ~14, and
\`GabaritEnvelope.slope_profile\` ~line 317). The regulation text is the authority here, not the
amendment and not the implementer.

Implementer claims (check, do not trust):
---
${(fix || '(none)').slice(0, 2500)}
---

Verify:
1. **The springing is the built eaves.** Read \`Silhouette.within\`. Confirm containment is tested
   from the eaves. Then construct a comble that is legal from the cornice but ILLEGAL from the real
   eaves, and confirm \`within\` now REJECTS it. That is the regression A2.4 introduced; prove it is
   gone.
2. **No mixed anchors.** Grep/read for any place a cornice-relative height is applied at the eaves
   without conversion. Confirm the assertion or named conversion at that boundary exists and fires
   — construct the mixed case and show it raising.
3. **Headroom recovered lawfully.** For the harness case (20 m / 1865 / comfortable / shop) report
   the built eaves, legal cornice, and actual built ridge. The comble should now run taller above
   its own eaves than \`ridge_height\` stands above the cornice, while every point still satisfies
   \`setback_at\`. Confirm it did NOT recover headroom by moving the springing.
4. **Sweep.** Widths 6-40 m x years 1830/1860/1875/1890/1905 x 4 classes x 3 ground programmes.
   Every silhouette point inside the eaves-sprung envelope. Report violations and worst overshoot.
5. **No retracted rule left asserted.** Confirm no test still asserts the A2.4 legal-cornice
   behaviour, and that any removed test was removed deliberately with a stated reason rather than
   quietly weakened.
6. Full suite, both guards in \`dev/harness/\`, and \`python3 dev/harness/first_building.py\`.

\`passed: true\` only if every item holds. If Amendment 3 is ITSELF wrong about the regulation,
say so plainly in \`design_problems\` — the source outranks the amendment.`,
  { label: 'verify:amendment3', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-3', fix, verdict }
