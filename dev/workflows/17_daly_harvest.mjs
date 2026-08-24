export const meta = {
  name: 'daly-1864-harvest',
  description: 'Harvest the measured plates from Daly Serie 1 (1864), the maisons a loyer volumes',
  whenToUse: 'The operator wants Second Empire locked. Daly Ser.1 is 154 dated, captioned, measured plates of exactly this typology.',
  phases: [
    { title: 'Harvest', detail: 'four agents triage and download from the 154 Serie 1 plates' },
    { title: 'Assemble', detail: 'fold into the review page as its own family' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const REF = `${ROOT}/dev/reference`

const CONTEXT = `You are harvesting from a single, exceptionally valuable primary source for a
procedural architecture project on 19th-century Paris.

# The source
**César Daly, *L'Architecture privée au XIXme siècle sous Napoléon III — Nouvelles maisons de Paris
et des environs*, Série 1 (1864).** Two tomes, 154 plates on Wikimedia Commons, all public domain.

Série 1 is **maisons à loyer** — Paris rental apartment buildings — which is *exactly* the typology
this project generates, in *exactly* the target period (1853-1870).

## Why this source is worth this much effort
The project's brief says: *"Photographs support qualitative comparison reliably and measurement not
at all. Where a number matters, use measured surveys and drawings, and record the source."*

Daly's plates ARE that source. Better still, they are **captioned** — a typical caption reads:

    MAISON À LOYER
    Première Classe — No 3 Rue de la Paix — Élévation
    par Mr PAUL MESNARD, ARCHte

That gives, per plate: the building type, its **CLASS** (Première / Deuxième / Troisième), the
**address**, the **architect**, and what the drawing shows. The generator has a class axis
(modest/ordinary/comfortable/grand) whose calibration constants are currently invented — so Daly's
own class ladder, attached to measured drawings, is the thing that can make them sourced.

Many plates also carry a **scale bar** ("Échelle de 0.02 c.m pour mètre") or explicit metric
callouts and dimension ladders.

# What is valuable, in order
1. **ÉLÉVATIONS** — full facade elevations, ideally with a scale bar. The most valuable thing here.
2. **DÉTAILS with dimensions** — window bays, entrance bays, mouldings, cornices, ironwork, with
   metric callouts. Directly usable for proportions.
3. **COUPES / sections** — give storey heights and floor construction.
4. **PLANS** — useful for parcel depth and light-well arrangement, lower priority.

# What to skip
Title pages, text-only pages, tables of contents, decorative frontispieces, blank/dark scans, plates
of *hôtels privés* or *villas* (those are Série 2/3, a different typology), and anything so
low-contrast the drawing cannot be read.

# The caption is the metadata — read it
Open each candidate and READ ITS CAPTION. Record the class, address and architect **exactly as
printed**. If a plate is uncaptioned or you cannot read it, say so — do not infer a class from how
grand the drawing looks. That would defeat the whole purpose, which is getting a *sourced* class label.`

const SCHEMA = {
  type: 'object',
  required: ['chunk', 'saved', 'reviewed', 'images'],
  properties: {
    chunk: { type: 'string' },
    reviewed: { type: 'integer' },
    saved: { type: 'integer' },
    skipped_reasons: { type: 'string' },
    images: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'title', 'source_url', 'license', 'plate_kind', 'shows', 'quality'],
        properties: {
          file: { type: 'string' }, title: { type: 'string' },
          source_url: { type: 'string' }, license: { type: 'string' }, author: { type: 'string' },
          plate_kind: { type: 'string', description: 'elevation | detail | section | plan | other' },
          daly_class: { type: 'string', description: "as printed: 'Premiere Classe' etc, or '' if not stated" },
          address: { type: 'string', description: 'as printed, else ""' },
          architect: { type: 'string', description: 'as printed, else ""' },
          has_scale_bar: { type: 'boolean' },
          has_dimensions: { type: 'boolean', description: 'explicit metric callouts or a dimension ladder' },
          year: { type: 'string', description: '1864 for Serie 1 (publication); "" if the building date is unknown' },
          shows: { type: 'string' }, quality: { type: 'string', description: 'good | partial | poor' },
        },
      },
    },
  },
}

phase('Harvest')

const chunks = await parallel([0, 1, 2, 3].map((i) => () =>
  agent(
    `${CONTEXT}

# Your task — chunk ${i} of 4

Your list of Commons file titles is at \`/tmp/daly_chunk${i}.json\` (about 38 titles). Read it with
python3.

## Method
1. For each title, get its imageinfo from the Commons API — request a ~1400px thumb, since these are
   dense engravings and detail matters:

\`\`\`bash
curl -s --get 'https://commons.wikimedia.org/w/api.php' \\
  --data-urlencode 'action=query' --data-urlencode 'titles=<TITLE>' \\
  --data-urlencode 'prop=imageinfo' --data-urlencode 'iiprop=url|extmetadata' \\
  --data-urlencode 'iiurlwidth=1400' --data-urlencode 'format=json'
\`\`\`

You can batch up to 50 titles per request with \`titles=A|B|C\`. Parse with python3, never by eye.

2. Download the thumbs to a scratch directory first.
3. **Look at each one.** Triage by the priority order above. Read the caption.
4. Keep the valuable ones; move them to \`${REF}/images/daly-1864/\` with clean names:
   \`daly_<plate_kind>_<nn>_<short-slug>.jpg\` — e.g. \`daly_elevation_03_rue-de-la-paix-3.jpg\`.
   Use a chunk-distinct number range so the four of you do not collide:
   chunk 0 → 01-24, chunk 1 → 25-48, chunk 2 → 49-72, chunk 3 → 73-96.
5. Record per image: \`plate_kind\`, \`daly_class\`, \`address\`, \`architect\`, \`has_scale_bar\`,
   \`has_dimensions\` — read from the caption and the drawing, not guessed.
6. Verify with \`ls\` that every file you list exists and is >20KB (these are large scans; a small
   file means a failed download). Drop failures. \`saved\` must equal the real count.
7. Write \`${REF}/meta/daly-1864-chunk${i}.json\` with the object you return.

## Judgement
Be selective on quality but **generous on elevations and dimensioned details** — those are the point
of this harvest, and we would rather have a marginal elevation than miss one. Be strict on plans,
sections and ornament plates: keep them only if genuinely legible and informative.

Set \`shows\` to what a rule could be held answerable to — e.g. "storey heights and bay pitch with
scale bar, Première Classe, 3 rue de la Paix" — not a generic description.

Report \`reviewed\` (how many titles you looked at) and \`skipped_reasons\` (what the rejects were).`,
    { label: `harvest:chunk${i}`, phase: 'Harvest', schema: SCHEMA, model: 'sonnet' }
  )
))

const ok = chunks.filter(Boolean)
const total = ok.reduce((n, c) => n + (c.saved || 0), 0)
const reviewed = ok.reduce((n, c) => n + (c.reviewed || 0), 0)
log(`Daly harvest: kept ${total} of ${reviewed} plates reviewed`)

phase('Assemble')

const assembled = await agent(
  `Fold the Daly 1864 harvest into the reference corpus at \`${ROOT}\`.

Four chunk files were written to \`${REF}/meta/daly-1864-chunk{0,1,2,3}.json\`; images are in
\`${REF}/images/daly-1864/\`.

Chunk results:
${ok.map((c) => `  - chunk ${c.chunk}: kept ${c.saved} of ${c.reviewed}. ${(c.skipped_reasons || '').slice(0, 160)}`).join('\n')}

## Task
1. Merge the four chunk files into a single \`${REF}/meta/daly-1864.json\` with
   \`family: "daly-1864"\`, preserving every field the chunks recorded (\`plate_kind\`,
   \`daly_class\`, \`address\`, \`architect\`, \`has_scale_bar\`, \`has_dimensions\`). Delete the
   chunk files afterwards so the family is not counted four times. Verify no duplicate \`file\`
   entries survived the merge.
2. Sort the merged list so **elevations come first**, then dimensioned details, then sections, then
   plans — the operator should meet the most valuable plates first.
3. Add \`daly-1864\` to \`FAMILY_INFO\` in \`${ROOT}/dev/harness/build_review_page.py\`, titled
   e.g. "César Daly 1864 — measured plates, maisons à loyer", positioned immediately after
   \`se-elevation\`. Note in its evidence line that these are the corpus's only source that supports
   **measurement** rather than qualitative comparison.
4. If it is cheap to do so, surface \`daly_class\`, \`address\` and a "SCALE BAR" / "DIMENSIONED"
   badge on the card for this family — that metadata is the reason these plates matter. Do not
   redesign the page; a small addition only.
5. Re-run the builder.
6. **Do not disturb \`${REF}/selection.json\`.** It is the operator's own 18-image Second Empire
   selection. Verify by hashing it before and after, and confirm all 18 still resolve on disk.

Report: total corpus size, the daly-1864 count broken down by \`plate_kind\`, how many carry a scale
bar or dimensions, the distribution of \`daly_class\`, and confirmation the selection is untouched.`,
  { label: 'assemble:daly', phase: 'Assemble', model: 'sonnet' }
)

return { reviewed, kept: total, chunks: ok.map((c) => ({ chunk: c.chunk, saved: c.saved, reviewed: c.reviewed })), assembled }
