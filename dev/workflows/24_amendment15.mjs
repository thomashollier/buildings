export const meta = {
  name: 'buildings-amendment-15',
  description: 'Let the comble vary within an era — garret storey count as a programme decision',
  whenToUse: 'Two of the four commercial varieties are unreachable because the comble is constant within the 45 degree era.',
  phases: [
    { title: 'Correct', detail: 'garret storey count drives comble height, bounded by envelope and depth' },
    { title: 'Gate', detail: 'independent verification against the Daly spread' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 15\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Read \`Amendment 9\` too — A9.1 contains an over-reading that A15 corrects, and you should
understand why before changing anything.

Sources: \`${ROOT}/dev/reference/SOURCES.md\`, measurements in
\`${ROOT}/dev/reference/daly_measurements.json\`.

Repo: green, three guards clean. Keep it that way. Python 3.11, stdlib only.
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

## You own: \`src/buildings/typologies/paris/{structure,terminate,catalogue}.py\`, \`qualify/*\`,
and their tests.

Implement **A15.1 and A15.2**.

### The defect
Across eras the comble responds correctly to the envelope. **Within** the 45° era it is a constant:
at 1865 it is **3.20 m** for every street width, parcel width, parcel depth, class and ground
programme swept — 180 sites, one value.

Daly's nine 1864 commercial buildings span **2.69 / 2.77 / 2.85 / 3.18 / 3.34 / 3.45 / 4.72 / 6.80 /
7.00 m** — same era, a 2.6x range. So the generator cannot express two of the four commercial
varieties; asked for a 7.00 m comble it returns 3.20 m.

### The cause and the fix
The comble is **chambres de bonne**. Its height should follow the programme it carries, bounded
above by the envelope and by the parcel depth. The generator has a fixed **one-storey garret
allowance**, which is why parcel depth never binds and nothing else can move it.

Daly's two modes are one and two garret storeys:
- ~2.7-3.5 m — one storey, **one row of lucarnes** (6 of 9)
- ~4.7-7.0 m — two storeys, **two rows of lucarnes** (3 of 9)

Make the garret storey count a decision (1 or 2) and let the comble follow. A two-storey garret
needs the depth: on a shallow parcel the 45° diagonals meet before the second storey fits, and it
must not be built. That is a real constraint, not a guard — derive it.

### What must NOT change
- the silhouette stays inside the envelope. The current sweep reports **0 violations, worst
  overshoot 0.000000 m** — that must survive, and the gate will re-run it.
- every silhouette point still comes from \`setback_at\`.
- the per-era shapes (45°, arc, eighth-arc) are unchanged. **This is about how far the comble is
  carried, not what curve it follows.**
- A12.1's fold: the brisis/terrasson break must stay legible (it sits near 60%, derived from the
  terrasson reaching the ridge). With two garret storeys the lucarnes occupy the brisis in two rows.

### A15.2 — what may NOT be calibrated
The **rate** at which two garret storeys occur is **INFERRED**. Daly shows 3 of 9, but comble share
is marked INSUFFICIENT in the measurements and n=9 carries a known publication bias. Mark it
inferred. Assert only that both modes occur and that a two-storey garret carries two dormer rows.

**Do not key the choice to class.** A9.1's retraction stands: that comble share is not a class
function is the one solid piece of evidence here. Programme and parcel depth are the honest drivers.

### A15.3 — the balconette clips through the archivolt
From the A14 gate: in **90 of 210** tall arches the 0.90 m balconette is taller than the straight
part of the light below the springing (0.7615 m on layout AC), so its top rail and outer stiles cut
through the archivolt. Worst overflow **0.138 m**. Derive the garde-corps height from the straight
portion of the light rather than the flat-headed default; it must not intersect the moulding.

### A15.4 — the tall pedestrian arch overshoots its evidence
Ours 6.11-6.35 m against Daly's two examples at **5.01 m** (2 et 4 bd de Sébastopol) and **5.07 m**
(87 bd de Sébastopol) — 1.05-1.35 m too tall, aspect 3.49:1 against 2.88:1. The tall CARRIAGE arch
is fine (6.01-6.24 inside Daly's 5.00-7.30); only the pedestrian form overshoots, because both are
carried to the same crown line. A porte piétonne is narrower, so the same crown makes it lanky.

n=2 is thin: **assert the ordering** (pedestrian shorter than carriage, both clearly taller than
their one-storey forms) and mark the proportion INFERRED. **Do not touch the widths** — A14 proved
2.60 / 1.75 byte-identical across forms under a paired test and that result stands.

Verify by sweeping 1865 across depths and programmes and reporting the comble distribution — it
must span roughly Daly's range instead of collapsing to one value.`,
  { label: 'fix:comble-variation', phase: 'Correct', model: 'opus', effort: 'high' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this fix.
Read \`Amendment 15\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claim (check, do not trust):
---
${(fix || '(none)').slice(0, 2500)}
---

## Verify
1. **The comble now varies within the 45° era.** Sweep 1865 across street widths, parcel widths,
   parcel DEPTHS, classes and ground programmes (>=180 sites, as the defect report did). Report the
   full distribution of comble heights. It was a single value, 3.20 m. It must now span a range
   comparable to Daly's 2.69-7.00 m. A distribution with two clusters is the expected shape.
2. **Two dormer rows.** Confirm a two-storey garret carries TWO rows of lucarnes and a one-storey
   garret carries one. Rasterise one of each at >=700 px and LOOK.
3. **Depth actually binds.** Confirm a shallow parcel CANNOT get a two-storey garret — the 45°
   diagonals meet first. Report the depth threshold and show it derived rather than hardcoded.
4. **Legality survives.** Re-run the envelope sweep: widths 6-40 m x years 1830/1860/1875/1890/1905
   x 4 classes. Report violations and worst overshoot; both were 0. Confirm every point still comes
   from \`setback_at\`.
5. **Per-era shapes unchanged.** Confirm 1865 is still DIAGONAL_45, 1887 CIRCULAR_ARC, 1905
   eighth-arc, and that the A12.1 fold is still near 60% and legible.
6. **The rate is INFERRED, not calibrated.** Grep for the constant governing how often two storeys
   occur; it must be marked INFERRED with a reason. **If it was promoted to SOURCED that is a hard
   FAIL** — comble share is on the INSUFFICIENT list.
7. **Not keyed to class.** Confirm the choice is not a function of BuildingClass. Report the
   two-storey rate by class; it should not rise or fall monotonically.
8. **The four commercial varieties are now reachable.** Search for sites matching Daly's
   2 et 4 bd de Sébastopol (comble 7.00), 26 rue Bergère (4.72), 9 rue du Conservatoire (2.85) and
   39 rue Neuve des Mathurins (3.18). Report the best match and residual for each. All four should
   now be reachable; before, two were not.
9. Full suite and all three guards; confirm none was edited.
10. **LOOK.** Render the four and save to \`dev/logs/commercial/\`. Do they now read as genuinely
    different buildings rather than the same roof on different facades?

\`passed: true\` only if the repo is green and the comble genuinely varies.`,
  { label: 'verify:amendment15', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-15', verdict }
