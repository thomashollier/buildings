export const meta = {
  name: 'buildings-amendment-14',
  description: 'The two-storey round-arched entrance spanning RdC and entresol, plus layout variations',
  whenToUse: 'Operator-requested; documented in 4 of 16 Daly buildings. Run after Amendment 13.',
  phases: [
    { title: 'Correct', detail: 'catalogue + qualification: the tall arch, and the layout presets' },
    { title: 'Gate', detail: 'independent verification against the Impératrice plate' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 14\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Read \`Amendment 13\` immediately before it too — it changed how the entresol is treated, and this
builds directly on it.

Sources: \`${ROOT}/dev/reference/SOURCES.md\`; measurements in
\`${ROOT}/dev/reference/daly_measurements.json\`.

## The plate to look at
\`${ROOT}/dev/reference/images/daly-1864/daly_elevation_25_avenue-imperatrice.jpg\`
— *Maison à loyer, Première Classe, Avenue de l'Impératrice*, by Raban. **Open it and look.**
It is the clearest instance: a round-headed porte cochère 2.62 m wide and **7.30 m tall**, spanning
the rez-de-chaussée and the entresol, with the leaves below, a carved tympanum above them, a
balconette with ironwork set INSIDE the arch at entresol level, and a sculpted agrafe at the crown.
The flanking bays have arched RdC windows with bossage voussoirs and separate entresol windows.

Also worth a look, for the pedestrian version:
\`daly_elevation_02\` (2 et 4 bd de Sébastopol, by Davioud — porte piétonne 1.74 x 5.01 m).

Python 3.11, frozen dataclasses, stdlib only. Do not weaken tests. Do not edit any guard in
\`dev/harness/\`. Rasterise and LOOK.`

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

## You own: \`src/buildings/typologies/paris/{catalogue,structure}.py\`, \`qualify/*\`,
\`compose.py\`, \`src/buildings/render/svg/elements.py\` (consumption only),
\`dev/harness/layouts.py\`, and their tests.

Implement **A14.1, A14.2, A14.3**.

### The evidence — 4 of 16 buildings
| building | type | w | h | RdC | entresol |
|---|---|---|---|---|---|
| Avenue de l'Impératrice | cochère | 2.62 | **7.30** | 4.30 | absorbed |
| 39 rue Neuve des Mathurins | cochère | 2.57 | **5.00** | 4.10 | 2.40 |
| 2 et 4 bd de Sébastopol | piétonne | 1.74 | **5.01** | 3.42 | 2.65 |
| 87 bd de Sébastopol | piétonne | 1.76 | **5.07** | — | — |

against one-storey medians of 3.49 (cochère) and 3.03 (piétonne).

### A14.1 — the form
An entrance may span base + entresol as one **round-headed** arch, for both carriage and pedestrian.

**The width does not move.** 2.60 m carriage / 1.75 m pedestrian, exactly as A9.2 calibrated them
from the printed callout. Daly's tall arches are 2.57-2.62 and 1.74-1.76 — squarely inside the
one-storey range. **A tall arch is not a wide one. Assert it**, because getting this wrong would
undo the single best-evidenced result in the project.

The entresol's opening in that bay sits **inside the arch** — a balconette with ironwork — not as a
separate window beside it. The head is **round**; that is what makes the form.

Note **39 rue Neuve des Mathurins is one of the five canonical-stack buildings** (RdC + entresol +
4 étages, cornice 19.82 m), so the tall arch coexists with the entresol stack rather than replacing
it. Layout A must be able to take it.

### A14.2 — how it is chosen
A qualification decision through \`DecisionStream\` on a stable path. **Not** by date — all four are
1864 — and **not** by class alone — two Première, two Deuxième. About a quarter of entrances should
take it, but that is an observation from n=16: **mark the rate INFERRED**, do not present it as
sourced.

It must compose with A13: where the entresol is \`absorbed\`, the tall arch is the natural entrance;
where \`arcaded\`, the arch springs from the same coursing as the flanking arches. Both must work.

### A14.3 — layouts
Extend \`dev/harness/layouts.py\`. Keep \`A\` as it is, and add variants with the two-storey carriage
arch and the two-storey pedestrian arch (the latter on a narrower parcel). Follow the existing
\`Layout\` dataclass, and give each a \`why\` and its \`daly\` reference. Make sure
\`python3 dev/harness/layouts.py --svg\` renders them all.

### Scope
Do not change storey counts, storey heights, or entrance WIDTHS. Do not touch \`_FACADE_AMBITION\`.`,
  { label: 'fix:two-storey-arch', phase: 'Correct', model: 'opus', effort: 'high' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this.
Read \`Amendment 14\` at the end of \`${ROOT}/dev/CONTRACTS.md\`, and **open
\`${ROOT}/dev/reference/images/daly-1864/daly_elevation_25_avenue-imperatrice.jpg\` and look at it.**
The plate is the specification.

Claim (check, do not trust):
---
${(fix || '(none)').slice(0, 2500)}
---

## Verify
1. **THE WIDTH DID NOT MOVE.** Sweep every building that gets a tall arch and assert the entrance
   width is byte-identical to the one-storey case — 2.60 m carriage, 1.75 m pedestrian. Report the
   distribution for both forms. **Any drift is an immediate hard FAIL**: it would undo A9.2, the
   best-evidenced result in the project.
2. **The height spans two levels.** Report tall-arch heights against RdC + entresol for a sweep.
   Daly: cochère 5.00-7.30, piétonne 5.01-5.07. Ours should be comparable, and clearly distinct
   from the one-storey medians (3.49 / 3.03).
3. **The head is round.** Assert it, and confirm the renderer draws a round head — rasterise and
   look. A flat-headed tall opening is not this form.
4. **The entresol opening is inside the arch.** Confirm the bay with the tall arch does NOT also get
   a separate entresol window beside it, and that a balconette/ironwork sits within the arch.
5. **Choice mechanism.** Confirm it comes from \`DecisionStream\` on a stable path, not from date or
   class alone. Report the incidence rate and confirm the rate is marked INFERRED, not SOURCED.
   Pin the decision via the override layer and confirm nothing else in the building changes.
6. **Composes with A13.** Generate buildings with the entresol \`absorbed\` and \`arcaded\`, each
   with and without the tall arch — all four combinations must render sensibly. Rasterise and look.
7. **Layout A still takes it.** 39 rue Neuve des Mathurins proves the tall arch coexists with the
   canonical stack. Confirm layout A with the arch still gives base 3.95 / mezzanine 2.66 /
   principal 3.39 / uppers 3.15, 2.93, 2.72 / attic 2.60 and built 18.79 — storey heights must not
   have moved.
8. **Layouts run.** \`python3 ${ROOT}/dev/harness/layouts.py --svg\` renders every preset without
   error. Rasterise them to \`dev/logs/layouts/\` and LOOK at each.
9. **Compare with the plate.** Put our tall-arch bay beside the Impératrice plate. Does it read as
   the same architectural idea? Be concrete about what differs.
10. Full suite (was 1419) and all three guards; confirm none was edited.

\`passed: true\` only if the repo is green, the width is provably unchanged, and the form reads.`,
  { label: 'verify:amendment14', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-14', verdict }
