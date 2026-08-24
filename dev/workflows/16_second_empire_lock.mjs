export const meta = {
  name: 'second-empire-lock',
  description: 'Calibrate the canonical Second Empire case against the Daly measured plates, then pin it with a golden master',
  whenToUse: 'The operator wants Second Empire solid before branching out. Run after Amendment 8.',
  phases: [
    { title: 'Measure', detail: 'read real dimensions off the four dated 1864 Daly plates' },
    { title: 'Calibrate', detail: 'replace INFERRED constants with sourced ones, for this case only' },
    { title: 'Lock', detail: 'golden-master regression test pinning the canonical profile' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const REF = `${ROOT}/dev/reference`

const CONTEXT = `Project at \`${ROOT}\` — constraint-derived procedural building generator for
19th-century Paris. The operator's goal: **get canonical Second Empire (1853-1870) solidly right
before branching out to other periods.**

\`${REF}/selection.json\` is the operator's own ground-truth set: 18 images, all Second Empire.
Four are **measured architectural plates from César Daly, *L'Architecture privée au XIXme siècle
sous Napoléon III — Nouvelles Maisons de Paris* (1864)**:

  se-elevation_06  Maison à loyer, 3 rue de la Paix — FULL ELEVATION, "Première Classe",
                   architect Paul Mesnard. Carries a SCALE BAR: "Échelle de 0.02 c.m pour mètre",
                   graduated to 10 mètres.
  se-elevation_07  120 boulevard de Sébastopol — entrance-bay detail, dimensioned mouldings
                   with metric callouts
  se-elevation_08  9 rue du Conservatoire — two stacked window bays, dimensioned reveals in
                   metres and centimetres
  se-elevation_09  63 boulevard de Sébastopol — door/window pediment with a full dimension
                   ladder in the margin

They live under \`${REF}/images/se-elevation/\`. **You can read image files directly — do so.**

## Why this matters
The brief is explicit: *"Photographs support qualitative comparison reliably and measurement not at
all... Where a number matters, use measured surveys and drawings, and record the source."*

These plates are that source. The system currently carries roughly ten constants marked INFERRED —
facade ambition per class, comble fill, storey taper, bay pitch, opening aspect band, the
\`scale_for_class\` factors — all invented. Daly lets several become **sourced**.

## The discipline that matters most
**Do not invent a number and present it as measured.** If you cannot read a dimension off a plate
with confidence, say so and leave the constant INFERRED with its existing value. A fabricated
"source" is far worse than an honest inference, because it launders a guess into evidence.

Distinguish clearly in everything you write:
  - MEASURED — read off a scale bar or an explicit metric callout
  - DERIVED — a ratio computed from two measured values
  - INFERRED — still a guess

Also: **n = 1 to 4 buildings.** Daly's plates are exemplary buildings a journal chose to publish,
which biases toward the grander end. Calibrate with them; do not claim they prove a population.
`

const MEASURE_SCHEMA = {
  type: 'object',
  required: ['plate', 'confident', 'measurements'],
  properties: {
    plate: { type: 'string' },
    confident: { type: 'boolean', description: 'false if the scale/callouts could not be read reliably' },
    scale_note: { type: 'string', description: 'how the scale was established, or why it could not be' },
    building_class: { type: 'string', description: "Daly's stated class if the plate names one, else unknown" },
    measurements: {
      type: 'array',
      items: {
        type: 'object',
        required: ['what', 'value_m', 'kind', 'how'],
        properties: {
          what: { type: 'string', description: 'e.g. "ground storey height", "bay pitch", "principal window w"' },
          value_m: { type: 'number' },
          kind: { type: 'string', description: 'MEASURED | DERIVED | INFERRED' },
          how: { type: 'string', description: 'exactly how you obtained it — scale bar, callout text, ratio of two measures' },
          confidence: { type: 'string', description: 'high | medium | low' },
        },
      },
    },
    ratios: {
      type: 'array',
      items: {
        type: 'object',
        required: ['what', 'value'],
        properties: { what: { type: 'string' }, value: { type: 'number' }, how: { type: 'string' } },
      },
      description: 'dimensionless ratios, which survive scale error: storey/storey, opening h/w, comble/total',
    },
    notes: { type: 'string' },
  },
}

phase('Measure')

const plates = [
  { id: 'se-elevation_06_maison-a-loyer-rue-de-la-paix.jpg',
    aim: `The FULL ELEVATION, and the most valuable plate in the corpus. It has a scale bar
("Échelle de 0.02 c.m pour mètre", graduated to 10 Mètres) so absolute metres are recoverable:
measure the bar in pixels, get metres-per-pixel, then measure everything else.

Extract, in metres: total height to cornice; comble height; each storey's floor-to-floor height
(ground, entresol if present, and each upper in order); bay pitch (centreline to centreline);
facade width; the entrance door width and height; window width and height on the principal floor
and on the top habitable floor; the height above pavement of each running balcony.

Also record the ratios, which survive any scale error: each storey height over the ground storey;
comble over total; window h/w per floor; bay pitch over facade width.

The plate names its class — "Première Classe" — record that.` },

  { id: 'se-elevation_07_maison-a-loyer-boulevard-sebastopol-120-detail.jpg',
    aim: `Entrance-bay detail with dimensioned mouldings and metric callouts. Read the CALLOUTS —
they are more reliable than a scale bar. Extract entrance door width and height, entresol window
dimensions, surround/moulding depths, balcony console projection. The door is an ABSOLUTE quantity
in the system and the ruler the eye measures the facade against, so its true dimensions matter more
than anything else on this plate.` },

  { id: 'se-elevation_08_maison-a-loyer-rue-conservatoire-detail.jpg',
    aim: `Two stacked measured window bays with dimensioned reveals in metres and centimetres.
Extract window width and height for both storeys (giving a real storey-to-storey diminution),
reveal/jamb depths, sill height above the floor, balcony rail height, and the bandeau/string-course
depth. The window ASPECT RATIO (h/w) per storey is the single most useful number here — the system
currently declares a band of 1.70-2.00 and produces as low as 1.00.` },

  { id: 'se-elevation_09_maison-a-loyer-boulevard-sebastopol-63-detail.jpg',
    aim: `Door/window pediment with a full dimension ladder in the margin. Extract the dimension
ladder values, the bossage course height and width either side of the opening, the arched
porte-cochère lintel dimensions, and the pediment proportions. Bossage coursing is drawn by the
renderer from an IR count, so real course dimensions are directly usable.` },
]

const measured = await parallel(plates.map((p) => () =>
  agent(
    `${CONTEXT}

# Your plate: \`${REF}/images/se-elevation/${p.id}\`

${p.aim}

## Method
1. **Open the image and look at it.** Read it carefully; these are 19th-century engravings with
   handwritten-style annotation, so take care over decimal points and units (m vs cm).
2. Establish scale first, and state exactly how. If the plate has a scale bar, measure it. If it has
   explicit callouts, prefer those — a stated dimension beats a measured one.
   You may use python3 with PIL to inspect pixel coordinates if that helps you measure accurately.
3. Record each value with its \`kind\` (MEASURED / DERIVED / INFERRED), \`how\`, and \`confidence\`.
4. **Record the dimensionless ratios too.** They survive scale error entirely and are what the
   generator's proportional constants actually need.
5. If you cannot read the plate reliably, set \`confident: false\` and say why. That is a perfectly
   good outcome — an honest "cannot read this" is worth more than a confident guess.

Do not invent. Do not round a guess into a plausible-looking metric value.`,
    { label: `measure:${p.id.slice(0, 22)}`, phase: 'Measure', schema: MEASURE_SCHEMA, model: 'opus', effort: 'high' }
  )
))

const ok = measured.filter(Boolean)
const confident = ok.filter((m) => m.confident)
log(`Measured ${confident.length}/${plates.length} plates confidently`)

phase('Calibrate')

const calib = await agent(
  `${CONTEXT}

# Calibrate the canonical Second Empire case against the measurements

## What the plates gave us
${ok.map((m) => `### ${m.plate}  (confident: ${m.confident}; class: ${m.building_class || 'unknown'})
scale: ${m.scale_note || '—'}
${(m.measurements || []).map((x) => `  - ${x.what}: ${x.value_m} m  [${x.kind}, ${x.confidence}] — ${x.how}`).join('\n')}
ratios:
${(m.ratios || []).map((r) => `  - ${r.what}: ${r.value}  (${r.how || ''})`).join('\n')}
notes: ${m.notes || ''}`).join('\n\n')}

## Your task
Replace INFERRED constants with SOURCED ones **wherever the measurements genuinely support it, and
only there.** Run \`grep -rn INFERRED src/buildings/\` to find them all. The main ones:

  - \`structure._FACADE_AMBITION\` — how much of the legal ceiling a class builds to
  - \`structure._COMBLE_FILL\` — flagged by validation (D5) as class-invariant and backwards
  - the storey taper fraction
  - \`catalogue.opening_aspect_band()\` — declares (1.70, 2.00); D4 says reality is 1.00-1.33
  - bay pitch per class — D6 says grand currently gets FEWER bays than modest
  - \`quantity.scale_for_class\` factors (0.85 / 1.00 / 1.15 / 1.35)

## Rules
1. **Only change a constant the measurements actually support.** Leave the rest INFERRED, untouched.
   Changing a constant on the strength of a number you did not measure is the failure mode here.
2. Every changed constant gets a **citation** naming the plate, the building, and Daly 1864 —
   in the same form the regulatory citations use. Mark it MEASURED or DERIVED, not INFERRED.
3. **Prefer ratios to absolute values.** A storey-to-storey ratio is robust; a metre value read off a
   scale bar carries the bar's error.
4. **Daly's "Première Classe" is a data point for ONE class**, and an exemplary building at that.
   Do not extrapolate it across the whole class ladder and call the result sourced. Where you must
   interpolate, say so and keep those INFERRED.
5. This is calibrated for **canonical Second Empire, 1853-1870**. It must not silently change other
   eras' behaviour. Check that it does not: compare a 1830 and a 1895 building before and after.
6. Do not weaken tests. The full suite must stay green.

Write \`${ROOT}/dev/logs/SECOND_EMPIRE_CALIBRATION.md\`: a table of every constant — old value, new
value, kind (MEASURED/DERIVED/INFERRED), and the citation or the reason it stayed inferred.`,
  { label: 'calibrate:constants', phase: 'Calibrate', model: 'opus', effort: 'high' }
)

phase('Lock')

const lock = await agent(
  `${CONTEXT}

# Lock the canonical Second Empire case

Calibration report:
---
${(calib || '(none)').slice(0, 3000)}
---

The operator wants this style **solid before branching out**. Locking means: it cannot drift
silently when later work targets other periods.

## 1. The golden master
Write \`${ROOT}/tests/golden/test_second_empire_canonical.py\` (create the package).

Pin a small set of canonical Second Empire situations — a mid-block ordinary immeuble on a ~20 m
boulevard c.1865; a grand one on a 30 m street; a modest one on a 12 m street; a corner. For each,
serialise the IR and store it under \`${ROOT}/tests/golden/data/\`.

The test asserts the generated IR still matches. Structure it so a diff is **readable** — report
which node and which prop changed, not "bytes differ". Include a documented way to regenerate the
goldens deliberately (an env var or a script), so an intentional change is a visible, reviewed act
rather than a silent overwrite.

## 2. The proportion assertions
Write \`${ROOT}/tests/golden/test_second_empire_proportions.py\` asserting the calibrated
proportions hold across a SWEEP of Second Empire situations, not just the pinned ones — storey
taper, comble share by class, bay pitch band, opening aspect band. These are the numbers Daly
sourced; assert them against the source, exactly as the regulatory tests assert decree figures.

**Where a proportion is still INFERRED, assert only its ordering** (e.g. comble share rises with
class) rather than its value — do not pin a guess as though it were sourced.

## 3. The scope marker
Write \`${ROOT}/dev/SECOND_EMPIRE_STATUS.md\`: what is now sourced vs still inferred, what the
golden master covers, what a future period port must NOT break, and the honest limits — n=4 plates,
all 1864, all exemplary buildings a journal chose to publish, which biases grand.

Run the full suite and all three guards. Report the final state.`,
  { label: 'lock:golden-master', phase: 'Lock', model: 'sonnet' }
)

return { measured: ok.map((m) => ({ plate: m.plate, confident: m.confident, n: (m.measurements || []).length })), calib, lock }
