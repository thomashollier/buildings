export const meta = {
  name: 'buildings-amendment-12',
  description: 'Make the mansard break and the garde-corps/balcony distinction read at facade scale',
  whenToUse: 'Both are drawing defects over a correct IR. Operator-reported.',
  phases: [
    { title: 'Correct', detail: 'comble section geometry (opus) and ironwork weight (sonnet)' },
    { title: 'Gate', detail: 'independent verification, by looking at rasterised elevations' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 12\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

Repo state: **1409 tests passing, three guards clean.** Keep it that way.

## The framing that matters
Both items are cases where **the IR is correct and the drawing misrepresents it.** Do not "fix"
either upstream in the rules — the rules are right, and changing them would break calibrated,
sourced behaviour. Reference: \`dev/reference/daly_measurements.json\`, \`dev/reference/SOURCES.md\`.

Python 3.11, frozen dataclasses, stdlib only. Do not weaken tests. Do not edit any guard in
\`dev/harness/\`. **Rasterise and LOOK** — \`rsvg-convert -h 700 in.svg -o out.png\`. These are
legibility defects, so a claim that is not backed by looking at the image is not a claim.`

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

const [roofReport, ironReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/terminate.py\` and its tests.

Implement **A12.1** — the mansard break must be legible.

A pre-1884 comble currently states \`lower=45.0, upper=12.0, break_pct=0.906\`. For the canonical
case (comble 3.20 m, parcel 16 m ⇒ half-depth 8.0 m) the silhouette is:

    (0.00, eaves) → (2.90, +2.90) → (4.311, +3.20) → (8.00, +3.20)
         brisis 45° for 2.90 m │ terrasson 0.30 m │ FLAT for 3.69 m

The brisis is 90.6 % of the comble; the terrasson is a 0.30 m hairline; and above it the roof runs
flat for 3.69 m. At facade scale that reads as a plain slab with a nick near the top.

**The comble HEIGHT is correct and calibrated** — Daly's sixteen buildings give a median comble of
3.19 m against the generator's 3.20 m. **Do not change the height.** The fold position is the defect.

The geometry is over-determined once the terrasson angle is fixed. With a 45° brisis folding at
height *b* and a terrasson at 12° running to the ridge at mid-depth:

    b + (half_depth − b)·tan(12°) = comble_height
    1.906 + (8.0 − 1.906)·0.2126 = 3.20   →   fold at 59.6 %, not 90.6 %

**Derive the fold from the terrasson reaching the ridge**, instead of placing the fold near the
ridge and flattening after it. A long flat *terrasse* belongs only on a parcel deep enough to earn
one — on an ordinary parcel the terrasson runs to the ridge.

Constraints that still bind and that the gate will re-check:
- every silhouette point comes from \`setback_at\`;
- the silhouette stays inside the envelope — sweep 6-40 m × 1830/1860/1875/1890/1905, currently
  **0 violations, worst overshoot 0.000000 m**; that must survive;
- the 1884 arc and 1902 eighth-arc profiles keep their own shapes — this is the pre-1884 case;
- **the lucarne fills the brisis.** If the brisis shortens, the lucarne must follow it, not
  overhang. \`_dormer_face_height\` already ties them; keep that true.

Verify by rasterising a c.1865 elevation at ≥700 px and LOOKING: are both slopes legible as a
*comble brisé*?`,
    { label: 'fix:mansard-break', phase: 'Correct', model: 'opus', effort: 'high' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/render/**\` and its tests. **Renderer only.**

Implement **A12.2** — a garde-corps must not be drawn with the weight of a balcony.

On the canonical building four storeys carry ironwork:

    y= 3.95   4x guards='opening'        w=0.92        <- window rail
    y= 6.71   2x + 3x + 1x balcon_filant w=0.6/2.8/3.4 <- RUNNING BALCONY
    y=10.23   4x guards='opening'        w=1.20        <- window rail
    y=13.50   2x + 3x + 1x balcon_filant w=0.6/2.8/3.4 <- RUNNING BALCONY

**The IR is correct** — it already distinguishes them via the \`guards\` prop, and the two
\`balcon_filant\` storeys are exactly the classic 2nd-and-5th pattern. The renderer draws both at
nearly the same visual weight, so a viewer counts four balconies and the facade loses the
2nd-and-5th rhythm that is the most recognisable thing about a haussmannian elevation.

Draw the difference:
- **balcon filant** — it PROJECTS. A slab or console-borne floor, a balustrade standing on it,
  running unbroken across the bays. Full visual weight.
- **garde-corps** — it does NOT project. A light rail set *within the opening reveal*, visually
  subordinate: thinner bars, lighter stroke, no slab, no projecting shadow line.

**The reading test:** at facade scale a viewer should count **two** balconies on the canonical
building and see the other rails as part of their windows. Rasterise at ≥700 px and check that
yourself before claiming it.

Do NOT change which storeys carry ironwork — that comes from the 1823 ordonnance via
\`reglement.balcony_rule\` and is correct. This is a drawing-weight change only.

Note the renderer may not decide anything arguable (\`check_renderer_dumb.py\`). If you find you
need a fact the IR does not state — e.g. whether a balcony projects, or its projection depth —
**report it as an IR gap** rather than inferring it from the \`guards\` string.`,
    { label: 'fix:ironwork-weight', phase: 'Correct', model: 'sonnet' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 12\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claims (check, do not trust):
--- roof --- ${(roofReport || '(none)').slice(0, 1800)}
--- ironwork --- ${(ironReport || '(none)').slice(0, 1800)}

## These are LEGIBILITY defects. Asserting is not enough — you must look.

1. **A12.1 numbers.** For the canonical case (street 20, parcel 13, depth 16, 1865, comfortable,
   shop, seed 11) report the roof node's \`lower_angle_deg\`, \`upper_angle_deg\`, \`break_pct\`
   and the full silhouette polyline. The fold should be near 60 %, not 90.6 %, and the flat run
   should be short or absent on an ordinary parcel.
2. **A12.1 comble height unchanged.** Confirm the comble is still ~3.20 m — Daly's median is 3.19 m
   and it is calibrated. If the fold was "fixed" by making the roof taller, that is a FAIL.
3. **A12.1 legality survives.** Re-run the envelope sweep: 6-40 m × 1830/1860/1875/1890/1905 ×
   4 classes. Report violations and worst overshoot; it was 0 and 0.000000 m. Confirm every point
   still comes from \`setback_at\`, and that 1884/1902 profiles are unchanged.
4. **A12.1 lucarnes follow the brisis.** Report dormer face height against brisis height. No dormer
   may overhang the fold.
5. **A12.2 — LOOK.** Render the canonical building at ≥700 px and **count the balconies a viewer
   sees.** It must read as TWO running balconies plus subordinate window rails, not four balconies.
   Say what you actually see. Then render modest/ordinary/comfortable/grand and confirm the
   2nd-and-5th rhythm is legible across the class ladder.
6. **A12.2 — the storeys did not change.** Assert the set of storeys carrying ironwork, and their
   \`guards\` values, are identical to before the change. If the renderer fix altered which storeys
   have balconies, the fix went upstream and that is a FAIL.
7. **IR gaps.** If the renderer agent reported needing a fact the IR does not state, evaluate it and
   say whether it is a real gap worth filling.
8. **Guards + suite.** All three guards exit 0 and are unedited; full suite green (was 1409).
9. **Look at the whole thing.** Save \`dev/logs/facade_a12.png\` and \`dev/logs/ladder_a12.png\`.
   Compare against the Daly plates in \`dev/reference/images/daly-1864/\` — particularly
   \`daly_elevation_50_rue-de-la-paix-3.jpg\`. Does the roof now read as a comble brisé? Rank what
   still looks wrong.

\`passed: true\` only if the repo is green AND both defects genuinely read correctly at facade scale.`,
  { label: 'verify:amendment12', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-12', verdict }
