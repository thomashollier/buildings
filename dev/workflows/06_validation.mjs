export const meta = {
  name: 'buildings-s10-s11',
  description: 'Stage S10-S11: validation harness, fuzz, oracle diff, contact sheets and the VLM reference check',
  whenToUse: 'Final wave. Requires a working end-to-end generate() and renderer.',
  phases: [
    { title: 'Harness', detail: 'fuzz + invariants, oracle diff, contact sheets — built in parallel' },
    { title: 'VLM', detail: 'compare generated output against the operator-selected reference set' },
    { title: 'Report', detail: 'assemble the findings into one review artifact' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PREAMBLE = `You are building validation for a ground-up rewrite of a procedural building
generator for 19th-century Paris. The system is complete end to end; your job is to find out where
it is WRONG.

## Binding documents
\`${ROOT}/dev/PLAN.md\`, \`${ROOT}/dev/CONTRACTS.md\`, \`${OLD}/BRIEF.md\`

Entry point: \`buildings.typologies.paris.generate.generate(site, datums=None) -> (BuildingNode, TraceLog)\`
Renderer: \`buildings.render.svg.render(node)\`. Block: \`buildings.block.block\`.

Python 3.11, stdlib only. Read the source before assuming behaviour.
`

phase('Harness')

const [fuzzReport, oracleReport, sheetReport] = await parallel([
  () => agent(
    `${PREAMBLE}

## Files you own
\`${ROOT}/dev/harness/fuzz.py\`, \`${ROOT}/tests/invariant/test_invariants.py\`

## Build the invariant fuzzer

> "Fuzz across seeds, widths and eras for invariant violations."

Sweep the cross product: street width 6-40 m, parcel width 5-30 m, year 1820-1910, all four
building classes, all ground programmes, corner and mid-block, many seeds. Sample it sensibly
(a few thousand cases, not a combinatorial explosion) and make the sample deterministic.

For every case assert the five invariants:
- **I1** phases read strictly backwards — intermediate objects frozen, mutation raises
- **I2** the building never samples a block-level fact — with datums supplied, the handed-down
  values survive unchanged
- **I3** every quantity carries its kind; ABSOLUTE quantities are identical across classes while
  PROPORTIONAL ones scale
- **I4** every emitted node has a non-empty trace
- **I5** same seed + situation is byte-identical; different seed differs

Plus structural sanity:
- the silhouette lies within the regulatory envelope
- storey heights respect the 1859 minimum of 2.60 m
- bays fill the parcel exactly (residual < 1e-9)
- no NaN, no negative dimension, no zero-width element
- generation does not raise for ANY case in the sweep

**Report the failures rather than hiding them.** A fuzzer that finds nothing on a first run of an
unproven design is more likely broken than the design is perfect — say so if that happens, and
double-check the fuzzer is actually varying its inputs and actually asserting.

Write a summary to \`${ROOT}/dev/logs/fuzz_report.md\`: cases run, failures by category, and the
minimal reproducing input for each distinct failure.`,
    { label: 'harness:fuzz', phase: 'Harness', model: 'sonnet' }
  ),

  () => agent(
    `${PREAMBLE}

## Files you own
\`${ROOT}/tests/oracle/test_oracle_diff.py\`, \`${ROOT}/dev/harness/oracle_diff.py\`

## Build the reference-oracle diff

> "Keep the previous implementation running as a reference oracle; diff the same situations against it."

The previous implementation lives at \`${OLD}\` and still runs (\`core/generator.py\`,
\`core/grammar.py\`, \`backends/svg.py\`). Drive BOTH systems over the same situations and diff.

Important framing: the two systems are **not expected to agree on everything** — this is a
deliberate rewrite with a different rule model, and disagreement is often the new system being
right. The oracle's job is to surface **unexplained** divergence, not to enforce equality.

So:
1. **Where they must agree — regulatory output.** Cornice height limits, envelope geometry,
   arc radii, era boundaries, the 28.50 m ceiling. These come from the same ported \`reglement\`
   and any difference is a real bug. Assert equality here.
2. **Where they should be close — gross proportions.** Storey counts, total height, bay counts for
   a given parcel width. Report distributions side by side and flag outliers beyond a tolerance
   you state explicitly.
3. **Where they may differ — everything qualitative.** Ornament, variant choice, per-storey
   treatment. Record the differences; do not assert on them.

Write \`${ROOT}/dev/logs/oracle_report.md\`: a table of situations x metric x old x new x verdict,
and a clear list of the divergences that look like genuine bugs in the NEW system, separated from
the ones that look like deliberate improvements.

Guard the import of the old repo so the test skips cleanly if it is absent — but if it IS present,
the test must actually run. Report how many situations were compared.`,
    { label: 'harness:oracle', phase: 'Harness', model: 'sonnet' }
  ),

  () => agent(
    `${PREAMBLE}

## Files you own
\`${ROOT}/dev/harness/contact_sheets.py\`, output under \`${ROOT}/dev/logs/sheets/\`

## Build the contact sheets

> "Render generated output alongside them routinely, not once at the end. Contact sheets — twenty
> seeds in one grid — are the cheapest way to catch the single broken outlier among many."

Generate a set of contact sheets as **PNG or SVG** files, each a labelled grid:

1. **Seed sweep** — 20 seeds, one situation held fixed. Catches the broken outlier.
2. **Street-width sweep** — one seed, width 8→38 m. The height should visibly move in STEPS.
3. **Date sweep** — one seed, one site, years 1830→1905 at ~5-year steps. The roofline must visibly
   change shape at 1884, and ironwork/socle/keystone treatment must turn over gradually. This sheet
   is the visual proof of the two-chronologies design.
4. **Class sweep** — modest → grand at a fixed year and width. The DOOR should barely change while
   bays, windows and cornice grow. That contrast is the absolute/proportional split made visible,
   and it is the sheet most worth looking at closely.
5. **A block** — 8-12 buildings in a run. It must read as ONE WALL with a continuous cornice, not a
   shelf of models.

Label every cell with its situation. Write an index at \`${ROOT}/dev/logs/sheets/index.html\` that
shows all the sheets on one scrollable page with headings explaining what each one is testing and
what a viewer should look for.

If rendering fails for a cell, draw a visible error tile rather than aborting the sheet — a missing
cell in a contact sheet is exactly the outlier you are trying to catch.`,
    { label: 'harness:sheets', phase: 'Harness', model: 'sonnet' }
  ),
])

phase('VLM')

const vlmReport = await agent(
  `${PREAMBLE}

## The VLM reference check

The operator has scraped a reference corpus to \`${ROOT}/dev/reference/\` and reviewed it in
\`review.html\`, selecting the images that are good enough to be ground truth.

1. Look for \`${ROOT}/dev/reference/selection.json\`. If it exists, use the images it names.
   **If it does NOT exist** (the operator has not made a selection yet), fall back to every image in
   \`${ROOT}/dev/reference/meta/*.json\` whose \`quality\` is \`good\`, and say clearly in your report
   that you used the fallback.

2. Build \`${ROOT}/dev/harness/vlm_check.py\`. For each selected reference image, it should:
   - read that image's recorded situation (year, class, corner, street if known)
   - generate the closest matching building with \`generate()\` and render it
   - write the pair side by side into a comparison sheet

3. **Actually look at the images.** You can read image files directly — do so. For each pair, judge:
   - storey count and proportion — does the generated stack read as the same KIND of building?
   - the cornice and roofline — right shape for the date?
   - bay rhythm and count for the frontage width
   - the vertical position of balconies relative to the pavement
   - ground-floor treatment
   - overall: would someone who knows Paris flinch?

4. **Respect the two limits, and state them in your report:**
   - photographs support **qualitative** comparison reliably and **measurement not at all** —
     perspective, lens and unknown camera position mean you cannot read dimensions off them.
     Do not report a measured discrepancy from a photograph.
   - a visual check is a **tripwire, not a passing grade**. "That looks wrong" is strong evidence;
     "that looks right" is weak. Systematic small error — every window three percent too tall — is
     invisible to the eye and belongs to the assertions, not here.

5. Write \`${ROOT}/dev/logs/vlm_report.md\`: per-pair findings, then a ranked list of the strongest
   "that looks wrong" signals. Be specific and concrete. Vague praise is worthless here; a single
   precise "the balcony sits a storey too low on modest buildings" is worth more than twenty
   "looks plausible" lines.

Return the ranked findings.`,
  { label: 'vlm:reference-check', phase: 'VLM', model: 'opus', effort: 'high' }
)

phase('Report')

const summary = await agent(
  `Assemble the final validation report for the project at \`${ROOT}\`.

## Inputs
- Fuzz: \`${ROOT}/dev/logs/fuzz_report.md\`
- Oracle: \`${ROOT}/dev/logs/oracle_report.md\`
- Contact sheets: \`${ROOT}/dev/logs/sheets/index.html\`
- VLM: \`${ROOT}/dev/logs/vlm_report.md\`

Agent summaries:
FUZZ: ${(fuzzReport || '(none)').slice(0, 1200)}
ORACLE: ${(oracleReport || '(none)').slice(0, 1200)}
SHEETS: ${(sheetReport || '(none)').slice(0, 1200)}
VLM: ${(vlmReport || '(none)').slice(0, 2000)}

## Write \`${ROOT}/dev/logs/VALIDATION.md\`

Structure it against the brief's own success criteria, and grade each honestly:
1. Someone who knows Paris doesn't flinch at a generated street.
2. Changing one input changes the output the way a specialist would predict, **including the
   discontinuities**.
3. A whole block generates fast enough to iterate on, and reads as one wall.
4. Any element can be traced back to the rule that produced it.
5. Swapping the rule set gives a different city without touching the machinery.
   (Out of scope in this stage — report on whether the SEAMS are in the right place, not on
   whether it was done.)

Then:
- **Confirmed defects**, ranked by severity, each with a reproducing input.
- **Open questions** — where the design, not the code, looks wrong. The brief predicts the rule
  model is "the part most likely to be wrong"; report on whether it survived contact.
- **What is demonstrated vs asserted**, mirroring the brief's own confidence section.

Also run \`cd ${ROOT} && python3 -m pytest tests/ -q\` and both guard scripts in \`dev/harness/\`,
and record the actual results.

Be blunt. An honest list of what is broken is worth far more than a clean-looking report.`,
  { label: 'report:validation', phase: 'Report', model: 'opus', effort: 'high' }
)

return { wave: 'S10-S11', fuzzReport, oracleReport, sheetReport, vlmReport, summary }
