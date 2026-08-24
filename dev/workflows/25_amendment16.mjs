export const meta = {
  name: 'buildings-amendment-16',
  description: 'The garret trade pays for bands the parcel refuses, and overprices the ones it gets',
  whenToUse: 'The canonical Daly stack — RdC + entresol + 4 etages + comble — is currently unreachable.',
  phases: [
    { title: 'Correct', detail: 'one source of truth for the garret band, priced at its own height' },
    { title: 'Gate', detail: 'independent verification that the canonical stack is reachable' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 16\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Read \`Amendment 15\` first — A16 fixes two faults A15 introduced, and you need to understand the
trade before changing how it is priced.

Sources: \`${ROOT}/dev/reference/SOURCES.md\`, \`${ROOT}/dev/reference/daly_measurements.json\`.

Repo: 1480 tests, three guards clean. Keep it that way. Python 3.11, stdlib only.
Do not weaken tests. Do not edit any guard. Rasterise and LOOK.`

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

## You own: \`src/buildings/typologies/paris/structure.py\`, \`terminate.py\`, \`dev/harness/layouts.py\`,
and their tests.

Implement **A16.1, A16.2, A16.3**.

### A16.1 — the facade pays for a band the parcel refuses
\`_a_second_storey_of_chambres_de_bonne\` decides to buy on street width, programme and ceiling.
\`_garret_storeys_the_parcel_holds\` then refuses to build it on a shallow parcel. Nothing
reconciles them, so on a 10 or 12 m parcel a shop building **gives up 4.01 m of facade and receives
exactly one garret storey — the same one a residential building gets for free**:

    depth 10 shop        buys 1  holds 1  built 1  cornice 15.99 (80%)
    depth 10 residential buys 0  holds 1  built 1  cornice 19.20 (96%)

This is the SIXTH time in this project that two functions have held independent opinions about one
fact with nothing tying them together (A4.1, A6.8, A7.3, A9.3, A10.4). **Fix it structurally** —
one function decides, or the buyer asks the holder before paying. Do not adjust a number to hide it.

### A16.2 — the band costs more than it is
The purchase deducts 4.01 m of facade, enough for a whole étage plus half of another, which is why
the stack loses TWO étages instead of one.

Daly's two deep-comble buildings sit at cornice 17.52 and 17.55 m — they gave up about **2.5 m** of
a 20 m ceiling. A second garret band is one storey of rooms and should cost about one storey of
facade. Derive the deduction from the band's own height (\`BRISIS_RISE\` = 2.90 m already exists),
composed of the quantities it is made of rather than restated as a figure — the style
\`_stone_under_a_bought_garret\` already uses.

**The rate stays INFERRED.** A15.2 stands; Daly's 3-of-9 cannot calibrate it.

### A16.3 — make the canonical stack reachable, and test it
The operator's statement of the standard, which is exactly Daly's five canonical buildings:

    RdC · entresol · 1er (balcon filant) · 2e · 3e · 4e (balcon filant) · comble
    cornice 19.05-19.98 m, i.e. 95-100% of a 20 m ceiling

A shop on a 22 m street at comfortable class must be able to produce it. Add it as a **test**, not
just a preset — it is the commonest real configuration (4 of 9 commercial, 11 of 16 overall) and the
generator cannot currently reach it at all.

Then update \`dev/harness/layouts.py\`: layout **A** is titled "the maximal stack" and expects
"RdC + entresol + 4 étages"; make it deliver that. **C1** is the deliberate comble-heavy case and
should keep its deep comble — check it still does, and that its cornice lands nearer Daly's
17.5 m than 15.99.

### Do NOT change these — they are correct
- the balcony rule ("the noble floor and the top of the wall"); the 3e placement is a symptom
- the 6 m ordonnance; a noble floor at 3.70 m correctly gets no balcony
- residential behaviour: 96% of the ceiling, five étages`,
  { label: 'fix:garret-trade', phase: 'Correct', model: 'opus', effort: 'high' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this fix.
Read \`Amendment 16\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claim (check, do not trust):
---
${(fix || '(none)').slice(0, 2500)}
---

## Verify
1. **A16.3 — THE CANONICAL STACK.** Generate a shop, 22 m street, comfortable, 1865. Report the full
   stack with roles and the storey each balcon filant lands on. It must be
   \`RdC · entresol · 1er(filant) · 2e · 3e · 4e(filant) · comble\` with the cornice at **95-100%**
   of the 20 m ceiling. Report the exact percentage. Anything below 95% fails this item.
   Then sweep parcel widths and depths and report how often that stack is produced.
2. **A16.1 — nobody pays for a band they do not get.** Sweep parcel depths 8-26 m x both programmes.
   For every case report (buys, parcel holds, attics BUILT, cornice, % of ceiling). Assert that
   whenever the facade is reduced, the extra garret storey is actually built. The failing rows were
   depth 10 and 12 with a shop: 4.01 m paid, one attic built. Confirm they are gone.
3. **A16.2 — the price is the band's height.** Report the facade deduction for a bought band and
   confirm it is derived from BRISIS_RISE / composed quantities, not a literal. It was 4.01 m;
   roughly one storey (~2.9-3.2 m) is the target. Check the resulting cornice for a deep-comble
   building against Daly's 17.52 / 17.55 m.
4. **C1 still deep.** Confirm the deliberate comble-heavy preset keeps two garret storeys and that
   its cornice now sits nearer 17.5 m than 15.99.
5. **Nothing correct was broken.** Assert: the balcony rule still reads "noble floor and top of the
   wall" and places filants on the 1er and the LAST habitable storey; a noble floor below 6 m still
   gets no balcony (build one with no entresol and check); residential on a 22 m street still
   reaches ~96% with five étages.
6. **The reconciliation is structural.** Grep for any second, independent opinion about how many
   garret bands exist. There must be one source. Report what you find.
7. Full suite (was 1480) and all three guards; confirm none was edited.
8. **LOOK.** Re-run \`python3 ${ROOT}/dev/harness/tile_sheet.py\` and inspect
   \`dev/logs/tiles/presets.png\`. A, AC and C4 should no longer read 80%. Report the cornice
   percentage on every tile, and say whether the two dormer rows on A and AC are gone.

\`passed: true\` only if the canonical stack is reachable and the repo is green.`,
  { label: 'verify:amendment16', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-16', verdict }
