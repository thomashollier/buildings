export const meta = {
  name: 'buildings-amendment-13',
  description: 'Make the entresol read as the top of the commercial base, as Daly draws it',
  whenToUse: 'Operator-reported from a generated boulevard building; settled against two Daly plates.',
  phases: [
    { title: 'Correct', detail: 'qualification: base extent, string-course hierarchy, entresol opening treatment' },
    { title: 'Gate', detail: 'independent verification against the two plates' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 13\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

Repo: **1419 tests passing, three guards clean.** Keep it that way.
Sources: \`${ROOT}/dev/reference/SOURCES.md\`, measurements in
\`${ROOT}/dev/reference/daly_measurements.json\`.

## The evidence — look at these two plates yourself
- \`${ROOT}/dev/reference/images/daly-1864/daly_elevation_03_blvd-sebastopol-77.jpg\`
  RdC 4.00 + entresol 3.10. The entresol is **absorbed into the devanture** — the shopfront
  framework spans the whole 7.10 m and the entresol windows are its upper register. No separate
  entresol band exists on the facade.
- \`${ROOT}/dev/reference/images/daly-1864/daly_elevation_51_boulevard-sebastopol-120.jpg\`
  RdC 4.00 + entresol 3.10. The entresol IS its own band, but belongs to the base: **arched
  openings in the same ashlar/bossage coursing as the ground floor**, standing on the shopfront
  entablature, with small individual railings.

Both are Deuxième Classe, both 1864, both Paul Mesnard — so this is variation WITHIN a class and
period, not a date or class signal.

Python 3.11, frozen dataclasses, stdlib only. Do not weaken tests. Do not edit any guard.
Rasterise and LOOK (\`rsvg-convert -h 820 in.svg -o out.png\`).`

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

const fix = await agent(
  `${PRE}

## You own: \`src/buildings/typologies/paris/qualify/*\`, \`compose.py\`, \`catalogue.py\`,
\`src/buildings/render/svg/elements.py\` (consumption side only), and their tests.

Implement **A13.1 and A13.2**.

### A13.1 — the commercial base is RdC + entresol
Today \`raised_bossage\` stops at the top of the rez-de-chaussée and the entresol sits on plain wall
above it with a shrunken rectangular window. So it reads as a short residential storey.

Make the socle treatment run through the entresol where one exists, and move the strong string
course to sit **above the entresol** — the division that matters is commerce/residence, not
ground/first.

Note the hierarchy is currently inverted: 0.10 m above the entresol against 0.20 m above the
principal. The base's crowning course should be the emphatic one.

### A13.2 — the entresol gets its own opening treatment
Two forms, both legitimate, both from the plates above, and **both should be reachable**:
- **absorbed** — the devanture spans RdC + entresol as one framework; no separate opening band
- **arcaded** — arched openings in the base's own stone, on the shopfront entablature

Which one applies is a **qualification** decision. The renderer may not choose it. And it may not
be keyed to date or class alone — both plates are 1864 Deuxième Classe — so this is variation
within a class and period, which is what \`DecisionStream\` is for. Give it a stable path so the
choice stays addressable.

If the \`absorbed\` form means the entresol emits no opening of its own, make sure that does not
trip the zero-extent invariant (A10.5) — use the documented absence-marker convention rather than
emitting a zero-width node.

### Scope
Do NOT change which storeys exist, their heights, or the mezzanine's programme-driven presence
(A2.2) — those are calibrated. This is about how the entresol is TREATED.

**Do not touch \`_FACADE_AMBITION\`.** Our stack builds to 94% of the ceiling against Daly's
95-100%, but facade-ambition values are marked WEAK in the measurements and must not be calibrated
here. It is recorded as a known offset in A13.3.

Verify by generating the A layout (\`python3 ${ROOT}/dev/harness/layouts.py A --svg\`), rasterising,
and comparing side by side with both plates.`,
  { label: 'fix:entresol-base', phase: 'Correct', model: 'opus', effort: 'high' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this fix.
Read \`Amendment 13\` at the end of \`${ROOT}/dev/CONTRACTS.md\`, and **open the two Daly plates
named there and look at them** — they are the specification.

Implementer claim (check, do not trust):
---
${(fix || '(none)').slice(0, 2500)}
---

## Verify
1. **A13.1 — the base includes the entresol.** For the A layout (street 22, parcel 14, depth 18,
   1865, comfortable, shop, seed 3) report the socle node's y and h. It must span RdC + entresol,
   not RdC alone. Then confirm the emphatic string course sits ABOVE the entresol, and report both
   string-course depths — the hierarchy was inverted (0.10 above entresol vs 0.20 above principal).
2. **A13.2 — both forms reachable.** Sweep seeds and situations; confirm BOTH \`absorbed\` and
   \`arcaded\` occur, and report the proportions. If only one is ever produced, the other is dead
   code and that is a FAIL. Confirm the choice comes from qualification via \`DecisionStream\` with
   a stable path — not from the renderer, not from date or class alone.
3. **Addressability** — pin the entresol treatment via the override layer and confirm no other
   decision in the building changes.
4. **No zero-extent nodes** — if \`absorbed\` emits no entresol opening, confirm it uses the
   documented absence-marker convention and does not trip the A10.5 invariant. Run the fuzzer.
5. **Nothing calibrated moved.** Assert storey count, storey heights and mezzanine presence are
   unchanged for the A layout: base 3.95, mezzanine 2.66, principal 3.39, uppers 3.15/2.93/2.72,
   attic 2.60, built 18.79. Any drift means the fix went into structure and that is a FAIL.
   Confirm \`_FACADE_AMBITION\` is untouched.
6. **LOOK.** Render the A layout at >=820 px, save to \`dev/logs/layouts/A_after_a13.png\`, and put
   it beside both plates. Does the entresol now read as the top of a two-storey commercial base?
   Be concrete about what you see. Answer the operator's original observation directly: would
   someone still say "that doesn't have an entresol"?
7. Full suite (was 1419) and all three guards; confirm none was edited.

\`passed: true\` only if the repo is green and the entresol genuinely reads as part of the base.`,
  { label: 'verify:amendment13', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-13', verdict }
