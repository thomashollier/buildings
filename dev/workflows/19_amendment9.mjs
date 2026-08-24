export const meta = {
  name: 'buildings-amendment-9',
  description: 'Calibrate against Daly 1864 and close the A8 residuals; then lock the Second Empire case',
  whenToUse: 'The operator wants Second Empire solid before branching out. This is the wave that makes its constants sourced.',
  phases: [
    { title: 'Correct', detail: 'Daly calibration (opus) and the roof/hip single source of truth (sonnet)' },
    { title: 'Lock', detail: 'golden master + proportion assertions pinning the canonical case' },
    { title: 'Gate', detail: 'independent verification against the plates themselves' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. The operator's goal: **get canonical Second Empire (1853-1870) solidly right before
branching out.**

**Read \`Amendment 9\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

## Evidence you are working from
- \`${ROOT}/dev/reference/daly_measurements.json\` and \`${ROOT}/dev/logs/DALY_MEASUREMENTS.md\`
  — measurements from **César Daly, *L'Architecture privée au XIXme siècle sous Napoléon III*,
  Sér. 1 Vol. 1 t. 2 (1864)**, 77 plates of Paris *maisons à loyer*, each captioned with its class,
  address and architect.
- \`${ROOT}/dev/reference/SOURCES.md\` — the source register.
- \`${ROOT}/dev/logs/VALIDATION.md\` — the defect list.

Real sample: **n = 4 Première / 10 Deuxième / 2 Troisième BUILDINGS** (the unit is the building,
not the plate — several buildings contribute an elevation+section pair).

**The corpus's own error bar**, derived by measuring 26 rue Bergère twice independently:
printed dimensions are reliable; scale-bar widths carry ±10 %; storey heights ±0.2-0.4 m; derived
ratios worse. One scale-bar reading of 2.99 m sits against a printed 2.600 m — a 15 % error. So
**prefer printed dimensions, and treat a scale-bar figure as a range rather than a value.**

Python 3.11, frozen dataclasses, stdlib only. Do not weaken tests. Do not edit any guard in
\`dev/harness/\` — report a false positive instead. Rasterise and LOOK at visual changes.
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

const [calibReport, roofReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/{catalogue,structure,roles}.py\`, \`qualify/*\`,
\`compose.py\`, \`src/buildings/quantity.py\`, and their tests.

Implement **A9.1 (dormers), A9.2 (the door), A9.4 (calibration)**.

### A9.2 first — it is the highest-value single change
\`catalogue.py:309\` states \`Abs(3.00, "INFERRED — typical porte cochère clear width")\`.
Daly measures seven carriage doors: Première n=4 median **2.567 m** (2.410 / 2.534 / **2.600
printed** / 2.619); Deuxième n=3 median **2.575 m** (2.570 / 2.575 / 2.672).

The two top classes agree to **0.4 %**, which is itself the finding: a carriage door does not scale
with money because a carriage does not. The class signal is **entitlement** — Première 4/4 buildings
have one, Deuxième 3/10, Troisième 0/2 — not size.

Make the clear width **SOURCED at 2.60 m**, citing the printed dimension. Keep it ABSOLUTE.

This also closes the **D6 residual**: A8 correctly bounded bay pitch to an ABSOLUTE 2.70-3.40 m, but
the porte-cochère slot is 3.80 m — above that maximum — and is carried up EVERY storey, so a grand
building loses a bay (4 openings vs modest's 5 on a 16 m frontage). At 2.60 m clear the slot fits.
**Also: above the ground floor, the bay over a porte cochère is an ordinary bay.** Fix that too.

If entitlement is not already modelled, model it: whether a building gets a carriage entrance at all
should follow class and street width, with Daly's proportions as the evidence.

### A9.4 — calibrate, conservatively
Replace INFERRED with SOURCED for **exactly the eleven quantities marked SOURCED** in
\`daly_measurements.json\` → \`recommendation_summary\`. No others. Each gets a citation naming
Daly 1864, the plate, and whether the figure was **printed** or **scale-bar measured** (±10 %).

- **WEAK** quantities → use for **ordering only**. Assert the ordering, never the value.
- **INSUFFICIENT** quantities → leave INFERRED and untouched. Do not be tempted; recommending a thin
  number as sourced is the one failure mode that would make this whole exercise counterproductive.

### Two findings to encode as STRUCTURE, not scalars
**The window splits.** Width 1.04-1.30 m across all 16 buildings (×1.25, non-monotonic) while
noble-floor height runs 2.92 / 2.24 / 2.09 m (×1.40). Same aperture: **width ABSOLUTE, height
PROPORTIONAL.** This is the project's central distinction demonstrated from a period source — encode
it that way rather than as two numbers.

**The compressed level.** 14 of 16 buildings carry a compressed storey between shop and nobile:
Première dresses it as a low *1er* (4/4), Deuxième as an entresol (9/10). Troisième has neither and
**no piano nobile at all** — its étages are equal within 0.07 m. So "has a principal floor" is
itself class-dependent. The role predicates should express that WITHOUT a special case; if they
cannot, say so in your report rather than bolting one on.

**The regulation is visible in the data:** cornice height is flat between Première and Deuxième,
six buildings between 19.0 and 20.0 m, all pinned to the 1859 règlement's 20 m limit. Assert the
model reproduces this.

### A9.1 — dormers
Dormer count is 5/5/4/4, still favouring the modest building. A comble is floor rather than show:
count should follow the comble's own frontage and geometry, not class, and must not fall as class
rises. (The comble being class-invariant is CORRECT and Daly-supported — do not change that.)`,
    { label: 'fix:daly-calibration', phase: 'Correct', model: 'opus', effort: 'high' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/terminate.py\`, \`src/buildings/render/**\`,
and their tests.

Implement **A9.3** — the D2 residual.

### Two modules still hold independent opinions about the roof
A8 fixed \`elements._hip_arris\` to key the hip run to the FRONTAGE (4.311 m, was a constant 9.0),
and a ridge now exists at every frontage above ~8.7 m. Good.

But \`terminate._hip_arris_end\` (terminate.py:1084) **still uses \`profile[-1]\`** — the full 9.0
section run. So the IR-stated souche base is now up to **1.559 m BELOW** the drawn roof surface.
Measured: PW=16 → -1.225, -1.260; PW=20 → -1.127, -1.559.

That is the mirror image of the bug A7.3 fixed, and **the same two-independent-opinions divergence
A7.3 exists to eliminate**. We have now hit this class of bug four times (A4.1, A6.8, A7.3, and
here), so fix it structurally rather than by adjusting a number.

Consequence: chimneys are drawn BEFORE the roof mass and get swallowed by it — **one visible
chimney where the IR states five.**

**Required:**
- **One source of truth.** The hip run is a structural fact. Compute it ONCE in \`terminate\`, put
  it in the IR, have the renderer consume it. Neither module may derive it independently. Consider
  whether \`check_ir_is_consumed.py\` would have caught this — if not, say so in your report and
  propose (do not implement) an extension.
- Draw chimneys AFTER the roof mass.
- The repro \`PW=8\` still has no ridge (half-frontage 4.00 < rise-run 4.311). Decide what is correct
  for a very narrow corner parcel and make it so.
- End lucarnes overhang the hip into the sky on hipped corners — dormer top 2.65 m over eaves against
  a roof surface of 1.12-2.45 m at its edges. Fix.

Verify by rasterising a 20 m corner parcel and a 10-parcel block with corners, and COUNTING the
visible chimneys against what the IR states.`,
    { label: 'fix:roof-single-truth', phase: 'Correct', model: 'sonnet' }
  ),
])

phase('Lock')

const lock = await agent(
  `${PRE}

## Lock the canonical Second Empire case

Calibration report:
---
${(calibReport || '(none)').slice(0, 2500)}
---

The operator wants this style **solid before branching out** — it must not drift silently when later
work targets other periods.

### 1. The golden master
\`${ROOT}/tests/golden/test_second_empire_canonical.py\` (create the package).

Pin canonical Second Empire situations — a mid-block ordinary immeuble on a ~20 m boulevard c.1865;
a grand one on a 30 m street; a modest one on a 12 m street; a corner. Serialise each IR under
\`${ROOT}/tests/golden/data/\`.

The test asserts the IR still matches, and **a failure must be readable**: report which node and
which prop changed, not "bytes differ". Provide a documented way to regenerate goldens deliberately
(env var or script) so an intentional change is a visible, reviewed act rather than a silent overwrite.

### 2. Proportion assertions against the source
\`${ROOT}/tests/golden/test_second_empire_proportions.py\`, asserting across a SWEEP of Second Empire
situations — not only the pinned ones.

- Quantities calibrated **SOURCED**: assert the value, with the Daly citation in the test's docstring,
  exactly as the regulatory tests assert decree figures. Respect the error bar — a scale-bar figure
  gets a ±10 % tolerance, a printed one can be tight.
- Quantities that are **WEAK or INFERRED**: assert only the **ordering** (e.g. total height rises
  with class), never a value. Do not pin a guess as though it were sourced.
- Assert the two structural findings: the window's width is class-flat while its noble height rises;
  and cornice height is flat between the two upper classes because both are pinned to the 1859 limit.

### 3. \`${ROOT}/dev/SECOND_EMPIRE_STATUS.md\`
What is now sourced vs still inferred; what the golden master covers; what a future period port must
not break; and the honest limits — n = 4/10/2 buildings, all 1864, all exemplary buildings a journal
chose to publish (biased grand and better-designed), scale-bar error ±10 %, Troisième thin at n=2
with no printed dimension anywhere.

Run the full suite and all three guards. Report the final state.`,
  { label: 'lock:golden-master', phase: 'Lock', model: 'sonnet' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these changes.
Read \`Amendment 9\` at the end of \`${ROOT}/dev/CONTRACTS.md\`, plus
\`${ROOT}/dev/logs/DALY_MEASUREMENTS.md\` and \`${ROOT}/dev/reference/daly_measurements.json\`.

Claims (check, do not trust):
--- calibration --- ${(calibReport || '(none)').slice(0, 1600)}
--- roof --- ${(roofReport || '(none)').slice(0, 1600)}
--- lock --- ${(lock || '(none)').slice(0, 1600)}

## Verify

1. **A9.2 the door.** Confirm clear width is now 2.60 m, SOURCED, with a citation naming Daly and
   the printed dimension. Confirm it is still ABSOLUTE and byte-identical across classes. Then
   re-measure **openings per storey by class on a 16 m frontage**: GRAND must no longer have fewer
   than MODEST (was 4 vs 5, and fewer on 6 of 8 frontages). Sweep 8 frontages and report the table.
   Confirm centre-to-centre pitch now sits inside 2.70-3.40 m for every class INCLUDING across the
   porte-cochère slot, and that the slot is not carried up every storey at full width.
2. **A9.4 conservatism — the important audit.** Cross-check every constant changed against
   \`recommendation_summary\`. **Anything marked WEAK or INSUFFICIENT that was nonetheless
   calibrated as SOURCED is a hard FAIL** — list them. Confirm the six INSUFFICIENT quantities
   (comble share, cornice band depth, upper-storey aspect, entresol aspect, balcony height outside
   Deuxième, bay pitch by class) are untouched and still INFERRED.
3. **Citations are real.** Every new SOURCED citation must name Daly 1864 and say printed vs
   scale-bar. Grep them and list any vague or placeholder string.
4. **A9.3 one source of truth.** Grep for any second derivation of the hip run. Assert IR-stated
   souche base == drawn base because the IR is right, not because the renderer recomputed. Then
   **rasterise a 20 m corner and a 10-parcel block and COUNT visible chimneys against the IR count**
   — it was 1 visible where the IR stated 5. Report both numbers.
5. **A9.1 dormers** — count by class; must not fall as class rises.
6. **The structural findings.** Assert window width is class-flat while noble height rises ×~1.4.
   Assert cornice height is flat between the two upper classes and pinned near the 1859 20 m limit.
7. **The golden master bites.** Deliberately perturb one constant and confirm the golden test FAILS
   with a readable, node-level diff. Restore. A golden test that cannot fail is worthless.
8. **All three guards** exit 0 and none was edited — read each and confirm its logic is intact.
9. **Full suite**; report the count and any regressions.
10. **Look.** Harness facade, a modest building, a 10-parcel block; rasterise ≥900 px to
    \`dev/logs/facade_a9.png\`, \`dev/logs/modest_a9.png\`, \`dev/logs/block_a9.png\`.
    Compare against the Daly elevations in \`dev/reference/images/daly-1864/\` — same KIND of
    building? Answer the criterion-1 question directly: would someone who knows Paris still flinch,
    and at what? Rank what remains.

\`passed: true\` only if every item holds.`,
  { label: 'verify:amendment9', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-9', verdict }
