export const meta = {
  name: 'buildings-amendment-8',
  description: 'The two critical and four high defects from S10/S11 validation, plus the new IR-consumption gate',
  whenToUse: 'Validation graded criterion 1 as FAIL. These six are what stand between here and a street that does not make a Parisian flinch.',
  phases: [
    { title: 'Correct', detail: 'renderer criticals (sonnet), roof section + proportions (opus)' },
    { title: 'Gate', detail: 'independent verification, by looking, plus all three guards' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. S0-S11 complete, **1331 tests passing**, three guards green.

**Read \`Amendment 8\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
The full validation is at \`${ROOT}/dev/logs/VALIDATION.md\` (defect list with repros) and
\`${ROOT}/dev/logs/vlm_report.md\` (the visual findings). Read the entries for your items.

## Where this stands
Validation graded the build against the brief's success criteria. **Criterion 2 PASSES** — inputs
change the output the way a specialist would predict, including the discontinuities. The fuzzer ran
3,000 cases clean with negative controls proving its checkers bite; the oracle matched the old
implementation on 495/495 regulatory rows. **The rule model works.**

**Criterion 1 FAILS.** Everything broken sits between the model and the eye. Your six items are that
gap. Note that none of these was caught by any gate while all four gates were green — so verify by
LOOKING, not only by asserting.

## Guards
Three now: \`check_no_period_branching.py\`, \`check_renderer_dumb.py\`, and the new
\`check_ir_is_consumed.py\` (what the IR states, the renderer must draw — it already catches D1).
**Agents may not edit any of them.** Report a false positive; do not tune it.

Python 3.11, frozen dataclasses, stdlib only. Rasterise and LOOK
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

const [rendReport, ruleReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/render/**\`, and its tests.

Implement **A8.1 (D1) and A8.2 (D2)** — both CRITICAL, both renderer-side.

### A8.1 — half of all buildings have no visible door
\`elements.py:193\` — \`if opening_kind == "carriage_entrance":\` is the ONLY entrance branch, so
\`pedestrian_entrance\` falls through to the generic window path and draws as a window.

The IR is correct: \`catalogue.entrance_for\` states
\`{'opening_type':'pedestrian_entrance','w':1.4,'h':2.9,'head':'flat','sill_height':0.0}\`.
The renderer discards it. That is **exactly half the population** — every modest and ordinary
building, and every building on a street under 12 m. On the block sheet it is 110 m of wall with
not one door.

Draw a *porte piétonne*: a panelled timber door, a fanlight or glazed upper panel, its own surround,
no sill. It must read as a DOOR beside the windows of the same storey — it is the ruler the eye
measures the facade against, and drawing it as a window destroys the scale reference the whole
absolute/proportional split exists to provide.

Run \`python3 ${ROOT}/dev/harness/check_ir_is_consumed.py\` — it currently FAILS on exactly this.
Make it pass by drawing the door, not by removing the kind.

### A8.2 — the hip run is keyed to parcel depth, not frontage
\`elements._hip_arris\` runs the hip in by \`min(facade_w/2, section_run)\`, where \`section_run\` is
the last x of the silhouette profile — a section on a plane **perpendicular to the street**,
calibrated against \`parcel_depth\`. Measured: that value is **9.0 for every frontage from 8 m to
26 m**. So any frontage under 18 m has both hips meeting at mid-frontage and the roof has **no ridge
at all** — a gable, or a pyramid on a wide parcel. That is essentially every parcel in Paris.

The hip run is a function of the **frontage**, not the section. Take it from the IR.

**This one bug produces three separate VLM findings** — the barn/pyramid roof (F2), the floating
chimney (F3: the souche is placed at the stated ridge 20.718 while the drawing truncates the apex to
17.5, so it hangs 3.5 m in clear air), and the block's stepped roofline (F12). Fixing it properly
should retire all three; verify that it does, by looking.

**Repro:** \`W=20, PW=8, Y=1865, K=COMFORTABLE, G=RESIDENTIAL, S=7, corner=True\`.`,
    { label: 'fix:renderer-criticals', phase: 'Correct', model: 'sonnet' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/{terminate,structure,catalogue}.py\`,
\`qualify/*\`, \`compose.py\`, and their tests.

Implement **A8.3, A8.4, A8.5, A8.6** — all HIGH, all rule-side.

### A8.3 (D3) — no Second Empire building has a mansard break
A pre-1884 roof node states \`lower=45.0, upper=45.0, break_pct=1.00\`, so the renderer correctly
draws no break. **The renderer is obeying the IR faithfully; the defect is upstream, in what a
pre-1884 comble states about itself.**

A 45° diagonal is the *legal maximum envelope*, not a roof section. The building inside it still had
a **brisis** (steep lower slope) and a **terrasson** (shallow upper). That is what a mansard IS, and
it is the single most recognisable thing about a Paris roof.

\`terminate\` must state the actual comble section it built, inscribed within the 45° envelope —
not restate the envelope as though it were the roof. Keep every point coming from \`setback_at\`
and keep the silhouette inside the envelope (that gate still holds).

Compounding it: dormers sit in the lowest fifth of the unbroken plane with bare zinc above, where a
real *lucarne* occupies the whole brisis. Fix that too.

### A8.4 (D4) — upper windows violate the catalogue's own declared band
\`catalogue.opening_aspect_band()\` states (1.70, 2.00). Measured: grand/upper median **1.33**,
minimum **1.00** — a square window — with 94% below the band, and it is WORSE for the grander
classes. This is why the wall reads as having holes in it rather than windows.

Make openings respect the declared band and **assert it**. Where a storey is too short to fit a 1.70
aspect at the bay's width, the opening must get **narrower, not squatter** — width is proportional
and elastic; the aspect is what carries the reading.

### A8.5 (D5) — the comble's share is inversely proportional to class
modest 37% of total height and 5 dormers; grand 16% and 2. \`total_height == legal_total_height\` in
all four classes, so the facade allowance a modest builder declines to use is silently converted
into ROOF: the poorer the building, the bigger its hat.

Traced to \`_COMBLE_FILL = 0.99\`, class-invariant, against \`_FACADE_AMBITION\` which is not.
**The oracle found the same constant independently** — 22 of its 29 proportion outliers are
\`total_height_m\`, all new > old, across every class. Two harnesses converging on one constant is
the strongest signal in the report.

This violates the brief directly: *"Conflating them makes every building a maximal building, which
is wrong and looks it."* A modest building should be **shorter overall**, not merely lower-eaved.

### A8.6 (D6) — grand buildings get fewer windows than modest ones
Class scaling is applied to the BAY PITCH: modest 2.55 m → 8 bays; grand 4.05 m → 6 bays on the same
16 m frontage. Real Paris moves the other way — money buys taller and richer openings, not a sparser
wall, and bay pitch is bounded by what the masonry will span (roughly 2.7–3.4 m) at every class.

Make bay pitch structurally bounded and only weakly class-dependent. Class expresses itself in the
**opening within the bay**, in storey height, and in ornament — never by thinning the rhythm.

Coordinate with the renderer agent; tell them any prop names you change.`,
    { label: 'fix:rule-proportions', phase: 'Correct', model: 'opus' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 8\` at the end of \`${ROOT}/dev/CONTRACTS.md\` and the D1-D6 entries in
\`${ROOT}/dev/logs/VALIDATION.md\` — those carry exact repros and measured numbers to compare against.

Claims (check, do not trust):
--- renderer ---
${(rendReport || '(none)').slice(0, 2000)}
--- rules ---
${(ruleReport || '(none)').slice(0, 2000)}
---

## Verify. These defects all passed four green gates, so ASSERTING IS NOT ENOUGH — look.

1. **D1** — sweep 4 classes x 4 street widths x 5 programmes. Confirm every building's entrance is
   drawn as a DOOR. Render a modest/ordinary residential building
   (\`W=8, PW=13, Y=1875, K=MODEST, G=RESIDENTIAL, S=1\`), rasterise, and LOOK: is the 1.40x2.90 m
   opening still pixel-identical to the window beside it? Then render the 9-parcel block sheet and
   count visible doors along the run — it was 0 along 110 m.
2. **D2** — measure the hip run against frontage for frontages 8→26 m. It was **9.0 for every one**.
   Report the new values. Then confirm the roof HAS A RIDGE at frontages under 18 m. Rasterise a
   corner parcel and LOOK: gable, pyramid, or proper comble?
   Then check the two downstream findings retired: is the souche still hanging 3.5 m in clear air
   (stated ridge 20.718 vs drawn apex 17.5)? Is the block's roofline still stepped? Report both.
3. **D3** — for years 1860/1870/1880 report the roof node's \`lower\`, \`upper\`, \`break_pct\`.
   A pre-1884 comble must now state a real brisis/terrasson section, not 45/45/1.00. Confirm the
   silhouette is STILL inside the envelope (sweep 6-40 m x 5 years; report violations and worst
   overshoot) — the fix must not buy the break by breaking legality. Rasterise a c.1865 building and
   LOOK: does it read as a mansard? Do the lucarnes occupy the brisis?
4. **D4** — re-measure the aspect table by class and role, same method as VALIDATION.md
   (mezzanines and oculi excluded). Report median, min and % below 1.70 for each row. Grand/upper
   was median 1.33, min 1.00, 94% below. Confirm an assertion now enforces the band.
5. **D5** — re-measure the comble-share table by class at \`W=20, PW=16, Y=1865\`. It was
   37/28/21/16%. It must now rise with class, and a modest building must be **shorter overall**, not
   just lower-eaved — report total height per class too.
6. **D6** — re-measure bay pitch and bay count by class on a 16 m frontage. Pitch must sit within
   roughly 2.7-3.4 m at every class, and grand must NOT have fewer bays than modest.
7. **All three guards** — \`check_no_period_branching.py\`, \`check_renderer_dumb.py\`,
   \`check_ir_is_consumed.py\` must all exit 0. **Confirm none was edited**: read each and check its
   logic is intact (the IR-consumption guard must still have both the coverage and consumption
   checks; the renderer guard its ProportionChecker taint analysis). A guard tuned to pass is a hard FAIL.
8. **Full suite** — 1331 tests were passing. Report the new count; no regressions.
9. **Regression on earlier wins** — exactly one entrance per building; entrance dimensions
   byte-identical across classes; block cornice continuous; no full-frontage glass rect.
10. **Look at the whole thing.** Harness facade, a modest residential building, and a 10-parcel
    block. Rasterise >=900 px, save to \`dev/logs/facade_a8.png\`, \`dev/logs/modest_a8.png\`,
    \`dev/logs/block_a8.png\`. Then answer the criterion-1 question directly and honestly:
    **would someone who knows Paris still flinch, and at what?** Rank what remains.

\`passed: true\` only if every item holds.`,
  { label: 'verify:amendment8', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-8', verdict }
