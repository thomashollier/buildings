export const meta = {
  name: 'reference-corpus',
  description: 'Scrape a Paris building-type reference corpus and build a selection review page',
  whenToUse: 'Standing requirement from the brief: every typology ships with reference photographs BEFORE it ships with rules.',
  phases: [
    { title: 'Collect', detail: 'one agent per building-type family: search Wikimedia Commons, download, record provenance', model: 'sonnet' },
    { title: 'Assemble', detail: 'build the selection review page from all metadata', model: 'sonnet' },
    { title: 'Verify', detail: 'check every referenced image exists on disk and the page is well-formed', model: 'haiku' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const REF = `${ROOT}/dev/reference`

// Eight families. Each is a distinct thing the rules have to get right, and each
// is separately selectable by the operator for the VLM ground-truth set.
const FAMILIES = [
  {
    key: 'restauration',
    title: 'Restauration & Louis-Philippe (1820–1848)',
    stresses: 'pre-Haussmann envelope; flat incised refends; thin lozenge/palmette ironwork; plaster over rubble',
    queries: [
      'Paris immeuble Restauration facade',
      'Paris architecture Louis-Philippe immeuble',
      'Paris rue de Rivoli facade 19th century',
    ],
  },
  {
    key: 'second-empire',
    title: 'Second Empire haussmannien, canonical (1853–1870)',
    stresses: 'THE reference case: 45° comble, bossage socle, balcon filant at 2nd and 5th, strict block unity',
    queries: [
      'immeuble haussmannien facade Paris',
      'Paris boulevard Haussmann building facade',
      'Paris Second Empire apartment building facade',
    ],
  },
  {
    key: 'third-republic',
    title: 'Early Third Republic (1870–1884)',
    stresses: 'mascarons becoming common; richening window pediments; still the 45° comble',
    queries: [
      'Paris immeuble 1875 facade',
      'Paris facade mascaron 19th century building',
      'Paris apartment building 1880 facade',
    ],
  },
  {
    key: 'belle-epoque',
    title: 'Belle Époque, post-1884 decree (1884–1902)',
    stresses: 'THE discontinuity test: arc comble replaces the 45° plane, taller and more elaborate, iron cresting, varied dormers',
    queries: [
      'Paris immeuble Belle Epoque facade',
      'Paris building 1890s facade architecture',
      'Paris toiture comble mansarde immeuble',
    ],
  },
  {
    key: 'post-1902',
    title: 'Post-1902 (Bonnier) & Art Nouveau',
    stresses: 'projections may now carry above the cornice; Guimard whiplash ironwork; Sauvage rue Vavin',
    queries: [
      'Hector Guimard Paris building facade',
      'Henri Sauvage rue Vavin Paris',
      'Paris Art Nouveau facade immeuble 1900',
    ],
  },
  {
    key: 'corner',
    title: 'Corner buildings — angle, chamfer, rotonde',
    stresses: 'the corner is a THIRD SHORT FACADE with its own rhythm, not a module type',
    queries: [
      'Paris immeuble angle rue facade corner building',
      'Paris rotonde corner building architecture',
      'Paris chamfered corner building haussmannien',
    ],
  },
  {
    key: 'class-range',
    title: 'Class range — modest faubourg vs grand boulevard',
    stresses: 'the absolute/proportional split: the door barely changes while bays, windows and cornice grow',
    queries: [
      'Paris modest 19th century apartment building narrow facade',
      'Paris grand boulevard building ornate facade',
      'Paris faubourg street buildings 19th century',
    ],
  },
  {
    key: 'ground-floor',
    title: 'Ground floor — shopfronts, cafés, portes cochères',
    stresses: 'fastest-turning feature family; carries the observation-date idea; the carriage door is the ruler for absolute scale',
    queries: [
      'Paris devanture ancienne boutique shopfront',
      'Paris porte cochere entrance 19th century building',
      'Paris cafe terrace facade old shopfront',
    ],
  },
]

const IMAGE_SCHEMA = {
  type: 'object',
  required: ['family', 'saved', 'images'],
  properties: {
    family: { type: 'string' },
    saved: { type: 'integer', description: 'how many image files were actually written to disk' },
    notes: { type: 'string', description: 'anything the operator should know: gaps, poor coverage, ambiguous dating' },
    images: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'title', 'source_url', 'license'],
        properties: {
          file: { type: 'string', description: 'path relative to dev/reference/, e.g. images/second-empire/foo.jpg' },
          title: { type: 'string' },
          source_url: { type: 'string' },
          license: { type: 'string' },
          author: { type: 'string' },
          year: { type: 'string', description: 'construction year or range if known, else ""' },
          klass: { type: 'string', description: 'modest|ordinary|comfortable|grand|unknown' },
          corner: { type: 'boolean' },
          street: { type: 'string', description: 'street/address if known' },
          shows: { type: 'string', description: 'what this image is EVIDENCE FOR — the feature a rule is answerable to' },
          quality: { type: 'string', description: 'good|partial|poor — is the facade actually legible and frontal?' },
        },
      },
    },
  },
}

phase('Collect')

const collected = await parallel(FAMILIES.map((fam) => () =>
  agent(
    `You are building a REFERENCE PHOTO CORPUS for a procedural architecture project on 19th-century Paris.

Your family: **${fam.title}** (key: \`${fam.key}\`)
What this family has to prove: ${fam.stresses}

## Task

Collect 8–14 good reference photographs of this family, download them, and record full provenance.

### Source policy — IMPORTANT
Use **Wikimedia Commons** as the primary source. It has excellent coverage of Paris architecture and clean licensing.
Do NOT scrape random websites or hotlink copyrighted press images. If Commons coverage is thin, you may also use
other clearly openly-licensed sources (Paris Musées open content, Gallica/BnF public domain, Flickr Commons),
but you must record the licence for every single file.

### Recipe

Search Commons via its API with curl, e.g.:

\`\`\`bash
curl -s --get 'https://commons.wikimedia.org/w/api.php' \\
  --data-urlencode 'action=query' \\
  --data-urlencode 'generator=search' \\
  --data-urlencode 'gsrsearch=immeuble haussmannien facade Paris' \\
  --data-urlencode 'gsrnamespace=6' \\
  --data-urlencode 'gsrlimit=40' \\
  --data-urlencode 'prop=imageinfo' \\
  --data-urlencode 'iiprop=url|extmetadata' \\
  --data-urlencode 'iiurlwidth=1000' \\
  --data-urlencode 'format=json'
\`\`\`

That returns, per result: \`imageinfo[0].thumburl\` (a ~1000px JPEG — download THIS, not the full-size original),
\`imageinfo[0].descriptionurl\` (the source page URL), and \`extmetadata.LicenseShortName\`, \`extmetadata.Artist\`,
\`extmetadata.ObjectName\`.

Suggested starting queries (vary and add your own — French terms work much better than English on Commons):
${fam.queries.map((q) => `  - ${q}`).join('\n')}

Parse the JSON with \`python3\`, not by eye. Download with curl into:

    ${REF}/images/${fam.key}/

Use clean lowercase filenames: \`${fam.key}_01_short-slug.jpg\` etc. Create the directory first.

### Selection criteria — be genuinely picky, this is ground truth

KEEP an image only if the facade is legible:
  - roughly frontal or a mild oblique — not a 60° raking shot
  - the whole facade, or a clean detail that shows the feature this family is about
  - daylight, not heavily obstructed by trees/scaffolding/vehicles
  - actually Paris, and actually the right period

REJECT: interiors, floor plans, maps, portraits, aerial views, modern buildings,
heavy night shots, images under ~500px, and anything where you cannot tell what you are looking at.

A corpus of 8 legible images beats 20 unusable ones. Set \`quality\` honestly — mark
\`partial\` or \`poor\` rather than silently including a bad frame, so the operator can filter.

### Dating discipline
Where the Commons description gives a construction date or address, record it. Where it does not,
leave \`year\` as "" — **do not guess a year and present it as fact.** An unknown date is fine;
a fabricated one poisons the ground truth. Same for \`klass\`: "unknown" is an acceptable answer.

### Output
1. Write \`${REF}/meta/${fam.key}.json\` containing exactly the JSON object you return
   (use python3 to write the file so quoting is safe).
2. Verify with \`ls\` that every \`file\` you list actually exists on disk and is >5KB.
   Drop entries whose download failed. \`saved\` must equal the number of real files.
3. Return the structured object.

Do not report success for files that are not on disk.`,
    { label: `collect:${fam.key}`, phase: 'Collect', schema: IMAGE_SCHEMA, model: 'sonnet' }
  )
))

const good = collected.filter(Boolean)
const totalImages = good.reduce((n, r) => n + (r.saved || 0), 0)
log(`Collected ${totalImages} images across ${good.length}/${FAMILIES.length} families`)

phase('Assemble')

const assembled = await agent(
  `Build the **reference selection review page** for a procedural Paris architecture project.

The operator will use this page to CHOOSE which reference photographs become the ground-truth set
for VLM checking of generated output. Selection is the entire point of the page.

## Inputs
Metadata files: \`${REF}/meta/*.json\` (one per family). Read them all with python3.
Images live under \`${REF}/images/<family>/\`.

Families and what each one is evidence for:
${FAMILIES.map((f) => `  - ${f.key}: ${f.title} — ${f.stresses}`).join('\n')}

Collector notes:
${good.map((r) => `  - ${r.family}: ${r.saved} saved. ${r.notes || ''}`).join('\n')}

## Write \`${ROOT}/dev/reference/review.html\`

A single self-contained HTML file (inline CSS + JS, no CDN, no external fonts) that the operator
opens directly from disk. Images referenced by **relative path** (\`images/<family>/<file>\`) so
it works offline via file://.

Requirements:

1. **Grouped by family**, each family a section with its title and a one-line note on what it is
   evidence for. Show a per-family kept-count in the heading.

2. **Every image is a card** with: the thumbnail (lazy-loaded, \`loading="lazy"\`, object-fit: cover,
   consistent tile height ~240px), its title, year/class/street when known, the \`shows\` note, the
   \`quality\` badge, and the licence + author line with a link to \`source_url\` (opens in a new tab).

3. **Selection.** Each card has a checkbox. Clicking anywhere on the card toggles it. Selected cards
   get a clear visual state (accent border + tint, not just the checkbox). Default: everything of
   quality \`good\` is pre-selected; \`partial\` and \`poor\` start unselected.

4. **Controls, in a sticky header:**
   - live count "N of M selected"
   - Select all / Select none / Invert
   - per-family select-all / none
   - a filter toggle to show only \`good\`, or show all
   - a filter to show only selected
   - **Download selection.json** — the important one. Writes a JSON file via a Blob download
     containing \`{ "generated_by": "review.html", "selected": [ <the full metadata record of each
     selected image, including file, title, source_url, license, year, klass, corner, shows> ] }\`.
     Tell the operator, in the page itself, to save it to \`dev/reference/selection.json\`.
   - **Copy JSON to clipboard** as a fallback.

5. **Persistence.** Selection survives reload via \`localStorage\` keyed by image file path,
   so the operator can work through it in more than one sitting.

6. **Click an image to open a lightbox** at larger size with its full metadata and source link,
   with left/right arrow-key navigation and Escape to close. Judging a facade from a 240px tile
   is not possible, so this is load-bearing rather than decoration.

7. **Design.** Clean, dense, dark-mode-friendly (respect \`prefers-color-scheme\`, define a full
   light palette on bare \`:root\` and override tokens under a dark media query). System font stack.
   This is a working tool, not a brochure — prioritise scanning many images quickly. Responsive
   grid via \`repeat(auto-fill, minmax(240px, 1fr))\`. No horizontal page scroll.

8. At the top, a short paragraph stating the two limits from the project brief, verbatim in substance:
   photographs support **qualitative** comparison reliably and **measurement** not at all; and a
   visual check is a **tripwire, not a passing grade** — "that looks wrong" is strong evidence,
   "that looks right" is weak.

## Also write \`${ROOT}/dev/reference/README.md\`
Briefly: what the corpus is, how it was collected, the source/licence policy, how to open the review
page, where to save selection.json, and how selection.json feeds the VLM check.

Build the page by generating it with a python3 script that reads the JSON and emits the HTML —
write that script to \`${ROOT}/dev/harness/build_review_page.py\` so the page can be regenerated
when the corpus changes. Then run it.

Return a short report: total images, per-family counts, and the absolute path of the page.`,
  { label: 'assemble:review-page', phase: 'Assemble', model: 'sonnet' }
)

phase('Verify')

const verdict = await agent(
  `Verify the reference corpus and its review page. Be skeptical and check the filesystem — do not
trust the previous agents' claims.

Check and report PASS/FAIL for each:

1. \`${REF}/images/\` — count files per family subdirectory. Any file <5KB or zero-byte is a failed
   download; list them.
2. \`${REF}/meta/*.json\` — valid JSON; every \`file\` entry resolves to a real file on disk.
   List any dangling references.
3. \`${ROOT}/dev/reference/review.html\` exists, is >5KB, and every \`src="images/..."\` in it
   resolves to a real file relative to \`${ROOT}/dev/reference/\`. Report the count of broken srcs.
4. The page contains the selection machinery: a checkbox per card, a download-selection control,
   and localStorage persistence. Grep for the evidence.
5. \`${ROOT}/dev/harness/build_review_page.py\` exists and re-running it does not crash.
6. Licences: every image record has a non-empty \`license\`. List any that don't.

FIX what you can fix cheaply and safely: prune dangling metadata entries, delete zero-byte files,
and re-run the page builder. Do NOT re-download or re-scrape.

Return a concise PASS/FAIL report per check, with the final image count and any remaining problems.`,
  { label: 'verify:corpus', phase: 'Verify', model: 'haiku' }
)

return {
  families: good.map((r) => ({ family: r.family, saved: r.saved, notes: r.notes })),
  totalImages,
  page: `${ROOT}/dev/reference/review.html`,
  assembled,
  verdict,
}
