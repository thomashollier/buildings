export const meta = {
  name: 'daly-measure',
  description: 'Read real dimensions off the Daly 1864 plates, by class, to calibrate the Second Empire case',
  whenToUse: 'Pure extraction — writes measurements to disk, touches no source. Safe to run alongside a code wave.',
  phases: [
    { title: 'Measure', detail: 'one agent per Daly class, plus the dimensioned details' },
    { title: 'Synthesise', detail: 'reconcile into one measurement set with per-class ratios' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const REF = `${ROOT}/dev/reference`

const CONTEXT = `You are extracting measurements from primary-source architectural plates for a
procedural building generator targeting 19th-century Paris.

# The source
**César Daly, *L'Architecture privée au XIXme siècle sous Napoléon III*, Série 1, Vol. 1 t. 2
(1864)** — 77 harvested plates of Paris **maisons à loyer**, the exact typology and period
(1853-1870) the generator targets. Public domain, from the Polona digital library.

**Every plate carries a scale bar** ("Échelle de 0.02 c.m pour mètre", graduated in mètres), and 30
also carry explicit metric callouts or a dimension ladder. Each is captioned with its **class**
(Première / Deuxième / Troisième), **address**, and **architect**.

Plates live under \`${REF}/images/daly-1864/\`. Grouped index: \`/tmp/daly_groups.json\`.

# Why this matters
The brief says: *"Photographs support qualitative comparison reliably and measurement not at all.
Where a number matters, use measured surveys and drawings, and record the source."*

The generator currently carries ~10 constants marked INFERRED — invented values for facade ambition,
comble fill, storey taper, bay pitch, opening aspect and class scaling. Validation found three are
actively wrong. Daly's plates, with a class printed on each, are what can make them **sourced**.

# The discipline that decides whether this is worth anything
**Never invent a number and present it as measured.** If you cannot read a dimension confidently,
say so and omit it. A fabricated measurement launders a guess into evidence and is far worse than an
honest gap.

Tag everything:
  - **MEASURED** — read off a scale bar or an explicit printed callout
  - **DERIVED** — a ratio computed from two measured values
  - **UNCERTAIN** — you think this is right but could not confirm it

**Prefer RATIOS.** A storey-to-storey ratio, an opening h/w, comble-over-total — these survive any
scale-bar error entirely, and they are what the generator's proportional constants actually need.
Absolute metres are valuable too (the door especially, since it is an ABSOLUTE quantity and the
ruler the eye measures the facade against), but ratios are the robust core.

# Method
1. Open each plate and **look at it**. These are dense 19th-century engravings; take care over
   decimal points and over m vs cm.
2. Establish scale from the bar: measure its pixel length, divide by the metres it spans.
   You may use python3 with PIL to read pixel coordinates precisely — that is more reliable than
   eyeballing, and you should.
3. Where a printed callout states a dimension, **prefer it over your own measurement**.
4. Record per plate, and keep the plates separate — do not average across buildings in this phase.`

const SCHEMA = {
  type: 'object',
  required: ['group', 'plates'],
  properties: {
    group: { type: 'string' },
    plates: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'readable', 'daly_class'],
        properties: {
          file: { type: 'string' }, daly_class: { type: 'string' }, address: { type: 'string' },
          readable: { type: 'boolean', description: 'false if scale/drawing could not be read' },
          scale_note: { type: 'string', description: 'how metres-per-pixel was established' },
          storey_count: { type: 'integer' },
          has_entresol: { type: 'boolean' },
          absolute_m: {
            type: 'array',
            items: { type: 'object', required: ['what', 'value_m', 'kind'],
              properties: { what: { type: 'string' }, value_m: { type: 'number' },
                            kind: { type: 'string' }, how: { type: 'string' } } },
            description: 'ground/entresol/principal/upper storey heights, bay pitch, facade width, door w+h, cornice height, comble height, balcony heights above pavement',
          },
          ratios: {
            type: 'array',
            items: { type: 'object', required: ['what', 'value'],
              properties: { what: { type: 'string' }, value: { type: 'number' }, how: { type: 'string' } } },
            description: 'storey/ground, storey/storey-below (the taper), comble/total, cornice/total, opening h/w per storey, bay pitch/facade width, door w/bay pitch',
          },
          notes: { type: 'string' },
        },
      },
    },
  },
}

phase('Measure')

const jobs = [
  { key: 'premiere', label: 'Première Classe',
    what: `The **Première Classe** plates — the grandest tier, 6 elevations/sections including
3 rue de la Paix, Champs-Élysées 119 and 125, and Avenue de l'Impératrice.
These calibrate the TOP of the class ladder. Read every plate in \`by_class["Première Classe"]\`.` },
  { key: 'deuxieme-a', label: 'Deuxième Classe (first half)',
    what: `The first five **Deuxième Classe** elevations — the middle tier and the largest sample,
mostly the Sébastopol percée plus rue de Rivoli 88. Take the FIRST FIVE entries of
\`by_class["Deuxième Classe"]\`. This tier is the canonical boulevard immeuble and matters most.` },
  { key: 'deuxieme-b', label: 'Deuxième Classe (second half)',
    what: `The remaining five **Deuxième Classe** elevations — take entries 5 onward of
\`by_class["Deuxième Classe"]\` (rue Bergère 26, rue du Conservatoire 9, Sébastopol 120,
rue Neuve des Mathurins 39, boulevard St-Germain 6 and any others).` },
  { key: 'troisieme', label: 'Troisième Classe',
    what: `The **Troisième Classe** plates — the modest tier, Beaumarchais 36-38-40 and rue de
Longchamps. Only 2 elevations, so this end of the ladder is thin: say so plainly in your notes,
and be careful not to over-claim from a small sample. Note that Beaumarchais is a TRIPLE elevation
(three adjacent buildings on one plate) — that is a bonus, since it shows how neighbours align.` },
  { key: 'details', label: 'Dimensioned details',
    what: `The **28 detail plates**, of which 30 across the corpus carry explicit metric callouts.
These are the most reliable numbers available because the dimensions are PRINTED rather than
measured off a bar.
Prioritise: entrance doors (w and h — ABSOLUTE, the scale ruler for the whole facade), window bays
(w, h, aspect, reveal depth, sill height above floor), balcony rail heights and console projections,
bossage course dimensions, cornice and string-course profiles.
Read \`details\` in the index. You will not get through all 28 carefully — prioritise the ones whose
\`dim\` flag is true and whose \`shows\` mentions doors, windows or balconies, and say which you
skipped.` },
]

const measured = await parallel(jobs.map((j) => () =>
  agent(
    `${CONTEXT}

# Your group: **${j.label}**

${j.what}

Index: \`/tmp/daly_groups.json\` (read with python3). Plate files are relative to \`${REF}/\`.

Write your result to \`${ROOT}/dev/logs/daly_measure_${j.key}.json\` as well as returning it.

Report \`readable: false\` for any plate you could not measure, with the reason. That is a
legitimate result — several of these are dense engravings and some scale bars are faint.`,
    { label: `measure:${j.key}`, phase: 'Measure', schema: SCHEMA, model: 'opus', effort: 'high' }
  )
))

const ok = measured.filter(Boolean)
const nPlates = ok.reduce((n, g) => n + (g.plates || []).length, 0)
const nRead = ok.reduce((n, g) => n + (g.plates || []).filter((p) => p.readable).length, 0)
log(`Measured ${nRead}/${nPlates} plates readably across ${ok.length} groups`)

phase('Synthesise')

const synth = await agent(
  `Reconcile the Daly 1864 measurements into one calibration set for the project at \`${ROOT}\`.

## Inputs
\`${ROOT}/dev/logs/daly_measure_{premiere,deuxieme-a,deuxieme-b,troisieme,details}.json\`
(read them all with python3 — do not work from the summaries below alone).

Group summaries:
${ok.map((g) => `  - ${g.group}: ${(g.plates || []).length} plates, ${(g.plates || []).filter((p) => p.readable).length} readable`).join('\n')}

## Task — write \`${ROOT}/dev/logs/DALY_MEASUREMENTS.md\` and \`${ROOT}/dev/reference/daly_measurements.json\`

1. **Per class** (Première / Deuxième / Troisième), report each quantity with **n, median, min, max**:
   storey heights (ground, entresol, principal, uppers), the storey taper ratio, bay pitch, opening
   aspect by storey role, comble share of total height, cornice height, door width and height,
   balcony height above pavement.

2. **Report the spread, not just a central value.** If Deuxième Classe storey heights vary from
   3.1 to 4.0 m across ten buildings, that range IS the finding — the generator should produce a
   distribution, not a constant. A median with no spread invites over-fitting.

3. **The class ladder is the point.** For each quantity, state whether it rises, falls, or is flat
   across Première → Deuxième → Troisième, and by how much. Flag explicitly any quantity where the
   ladder is NOT monotonic, or where n is too small to say. Troisième has only 2 elevations, so most
   claims about it should be marked weak.

4. **Absolute vs proportional.** Which quantities barely move across classes (candidates for
   ABSOLUTE — the door especially) and which scale strongly (PROPORTIONAL)? This is the project's
   central distinction and Daly can supply real evidence for it. Report the door dimensions across
   all three classes side by side — if they barely move, that is the strongest single result here.

5. **Honest limits section.** State plainly: n per class; that these are exemplary buildings a
   journal chose to publish (biased toward the grander and better-designed end); that all are 1864;
   that scale-bar reading carries error while printed callouts do not; and which numbers you would
   NOT calibrate on.

6. For each quantity give a **recommendation**: SOURCED (calibrate on this), WEAK (use only for
   ordering), or INSUFFICIENT (leave inferred). Be conservative — recommending SOURCED for something
   thin is the failure mode that would make this whole exercise counterproductive.

Do not modify any source code. This phase produces evidence only.`,
  { label: 'synthesise:measurements', phase: 'Synthesise', model: 'opus', effort: 'high' }
)

return { plates: nPlates, readable: nRead, groups: ok.map((g) => ({ group: g.group, n: (g.plates || []).length })), synth }
