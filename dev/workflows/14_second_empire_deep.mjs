export const meta = {
  name: 'second-empire-deep-scrape',
  description: 'Deep reference scrape of canonical Second Empire haussmannien (1853-1870): details, full views, elevations',
  whenToUse: 'The canonical family is the reference case for the whole typology and needs denser evidence than one pass gave it.',
  phases: [
    { title: 'Collect', detail: 'one agent per feature family — details, full views, measured drawings' },
    { title: 'Assemble', detail: 'fold the new families into the review page' },
    { title: 'Verify', detail: 'every image on disk, licensed, and in period' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const REF = `${ROOT}/dev/reference`

const PERIOD = `**The period is strict: 1853-1870, the canonical haussmannien immeuble.**

This is the reference case the whole generator is measured against, so period discipline matters more
here than breadth. The regulation in force is the *Règlement du 27 juillet 1859* (and the 1855
circulaire requiring block alignment), NOT the 1884 Alphand decree.

REJECT anything that is actually later work, even when Commons calls it "haussmannien" — that label
is used loosely for anything cream-coloured with a mansard. The tells for post-1884, all of which
should make you drop the image:
- a **curved/arc comble** instead of a straight 45-degree one (that is the 1884 decree)
- bow windows / oriels (illegal in Paris until the 1882 decree)
- elaborate near-universal mascarons, caryatids, atlantes (these ramp through the 1870s-90s)
- Art Nouveau anything — whiplash ironwork, Guimard, Lavirotte, grès flammé
- corner domes, rotondes and individualised facades (block unity weakens after the 1880s)
- an architect's plaque with a date outside 1853-1870

What you WANT is the canonical article:
- **straight 45-degree comble** with pedimented dormers
- **balcon filant** — a continuous running balcony, classically at the 2nd and 5th floors
- **bossage** — raised, regular rustication on the socle/ground floor
- flat wall plane, minimal relief (projections capped at 0.80 m since the 1823 ordonnance)
- dense symmetrical **cast scrollwork** ironwork — the standard haussmannian railing
- *pierre de taille* ashlar on the percées; strict horizontal continuity across party walls`

const SOURCES = `## Source policy
**Wikimedia Commons is the primary source** — use its API, do not scrape arbitrary sites.

\`\`\`bash
curl -s --get 'https://commons.wikimedia.org/w/api.php' \\
  --data-urlencode 'action=query' \\
  --data-urlencode 'generator=search' \\
  --data-urlencode 'gsrsearch=YOUR QUERY' \\
  --data-urlencode 'gsrnamespace=6' \\
  --data-urlencode 'gsrlimit=50' \\
  --data-urlencode 'prop=imageinfo' \\
  --data-urlencode 'iiprop=url|extmetadata' \\
  --data-urlencode 'iiurlwidth=1200' \\
  --data-urlencode 'format=json'
\`\`\`

Per result: \`imageinfo[0].thumburl\` (download THIS, not the original), \`descriptionurl\`,
\`extmetadata.LicenseShortName\`, \`.Artist\`, \`.ObjectName\`.

Also worth using \`generator=categorymembers\` with \`gcmtitle=Category:...\` — Commons categories are
far richer than its search. Useful roots to walk:
\`Category:Haussmannian architecture in Paris\`, \`Category:Balconies in Paris\`,
\`Category:Wrought iron balconies in France\`, \`Category:Mansard roofs in Paris\`,
\`Category:Rustication (architecture)\`, \`Category:Doors in Paris\`,
\`Category:Architectural drawings of buildings in Paris\`, \`Category:Cornices\`.

**Parse JSON with python3, never by eye.** Other openly-licensed sources are acceptable if Commons
is thin — Paris Musées open content, Gallica/BnF public domain — but record a licence for EVERY file.

## Dating discipline
Record \`year\` ONLY where a source states it. Commons usually gives the *photograph* date, which is
irrelevant — do NOT use it as a proxy. An unknown date is fine; a fabricated one poisons the ground
truth. Same for \`klass\`: "unknown" is a real answer.

Use the \`shows\` field to say what a rule could be held answerable to in this image — that is the
whole point of the corpus.`

const SCHEMA = {
  type: 'object',
  required: ['family', 'saved', 'images'],
  properties: {
    family: { type: 'string' },
    saved: { type: 'integer', description: 'image files actually written to disk and >5KB' },
    notes: { type: 'string', description: 'coverage gaps, rejects worth recording, ambiguous dating' },
    rejected: { type: 'integer', description: 'candidates dropped on period or legibility grounds' },
    images: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'title', 'source_url', 'license', 'shows', 'quality'],
        properties: {
          file: { type: 'string', description: 'path relative to dev/reference/, e.g. images/se-ironwork/x.jpg' },
          title: { type: 'string' }, source_url: { type: 'string' }, license: { type: 'string' },
          author: { type: 'string' },
          year: { type: 'string', description: 'construction year ONLY if the source states it, else ""' },
          klass: { type: 'string', description: 'modest|ordinary|comfortable|grand|unknown' },
          corner: { type: 'boolean' },
          street: { type: 'string' },
          shows: { type: 'string', description: 'the feature a rule is answerable to' },
          quality: { type: 'string', description: 'good|partial|poor' },
        },
      },
    },
  },
}

const FAMILIES = [
  { key: 'se-elevation', title: 'Second Empire — measured elevations & drawings',
    n: '8-12',
    aim: `Architectural ELEVATIONS and measured drawings — the one source that supports actual
measurement, which photographs explicitly do not. These are the most valuable images in the whole
corpus, because where a number matters the brief says to use measured surveys and drawings.
Look for: elevation drawings, coupes/sections, plates from 19th-c architectural publications
(César Daly's *Revue générale de l'architecture*, Rouyer, Calliat, Normand), competition drawings,
and permit drawings. Gallica/BnF has a great deal of this in the public domain.`,
    q: ['immeuble parisien elevation dessin architecture 19e',
        'Cesar Daly revue generale architecture immeuble',
        'Paris facade elevation drawing 19th century apartment',
        'architecture privee XIXe siecle Calliat Daly planche'] },

  { key: 'se-facade', title: 'Second Empire — full frontal facades',
    n: '12-16',
    aim: `Whole-facade frontal views of canonical mid-block immeubles. Frontal or mild oblique only;
the entire facade from pavement to ridge in one frame. These carry the storey stack, the balcon
filant positions, and the cornice-to-comble relationship, so they are what the generated elevation
gets compared against directly.`,
    q: ['immeuble haussmannien facade Paris',
        'Paris boulevard Sebastopol immeuble facade',
        'rue de Rivoli immeuble facade Paris',
        'Paris avenue de l Opera immeuble facade'] },

  { key: 'se-ironwork', title: 'Second Empire — ironwork & balcon filant',
    n: '10-14',
    aim: `The single best dating instrument on a real facade. You want the STANDARD haussmannian
railing: dense, symmetrical CAST scrollwork (1850s-80s). Reject the thin repeating lozenges and
palmettes of the 1820s-40s, the looser Renaissance-revival variants of the 1880s-90s, and anything
with asymmetric organic whiplash (that is 1895+, Guimard).
Want both: close details of the railing pattern, AND views showing the balcon filant running
CONTINUOUSLY across several buildings, which is the 1855 circulaire made visible.`,
    q: ['balcon fer forge Paris immeuble XIXe',
        'garde-corps fonte balcon parisien',
        'Paris balcony wrought iron detail haussmannian',
        'balcon filant Paris facade'] },

  { key: 'se-socle', title: 'Second Empire — socle, bossage & refends',
    n: '8-12',
    aim: `Ground-floor stone treatment. You want **bossage** — raised rustication, heavy and REGULAR
(1850s-70s). Reject flat incised *refends* (that is 1820s-50s, the earlier family) and exaggerated
picturesque/vermiculated/rock-faced rustication (1880s-90s).
Show the coursing clearly: this is what the renderer draws as socle coursing, and the course
dimensions are a real number a rule is answerable to.`,
    q: ['bossage pierre taille facade Paris rez-de-chaussee',
        'Paris rusticated stone ground floor building',
        'refends facade parisienne pierre',
        'soubassement immeuble parisien pierre de taille'] },

  { key: 'se-surround', title: 'Second Empire — window surrounds, keystones & consoles',
    n: '10-14',
    aim: `Window treatment and what sits over the opening. For 1853-70 you want the SIMPLE console
or volute keystone, and moulded architraves — mascarons appear only sparingly before the 1870s.
Reject elaborate figurative mascarons, caryatids and atlantes, which are the 1870s-90s curve.
Capture the whole opening where you can: architrave, sill, appui, and the pediment/cornice over it,
plus how treatment DIMINISHES on the upper floors — that diminution is a rule in the system.`,
    q: ['agrafe fenetre console immeuble parisien',
        'Paris window surround architrave 19th century facade',
        'chambranle fenetre pierre Paris immeuble',
        'fronton fenetre facade parisienne XIXe'] },

  { key: 'se-comble', title: 'Second Empire — the 45° comble, dormers & zinc',
    n: '10-14',
    aim: `THE canonical roof, 1853-84: a straight 45-degree comble with pedimented dormers.
**Reject any curved or arc comble — that is the 1884 decree and the wrong period.**
Want: the slope read against the cornice, dormer (lucarne) form and spacing, zinc standing seams,
souches/chimney stacks sitting on the roof, and the ridge terrasson. Roofscape views across a
quarter are useful for how the combles line up.`,
    q: ['toit mansarde zinc Paris immeuble lucarne',
        'Paris rooftops zinc mansard roof',
        'lucarne toiture parisienne fronton',
        'souche cheminee toit parisien zinc'] },

  { key: 'se-cornice', title: 'Second Empire — cornices, modillions & string courses',
    n: '8-12',
    aim: `The crowning entablature and the horizontal lines. For this period: modillions and dentils,
deep but not yet the very heavy bracketed cornices of the 1880s+.
Most valuable are views showing the cornice running UNBROKEN across a party wall between two
different buildings — that is the 1855 circulaire and the single most important block-level fact in
the system. Also string courses and the bandeaux marking storey divisions.`,
    q: ['corniche immeuble parisien modillons',
        'Paris cornice building detail stone',
        'bandeau corniche facade parisienne XIXe',
        'entablement immeuble Paris pierre'] },

  { key: 'se-entrance', title: 'Second Empire — portes cochères & entrances',
    n: '10-14',
    aim: `The entrance is the ruler the eye measures the whole facade against — an ABSOLUTE quantity
in the system — so this family is disproportionately useful.
Want: *portes cochères* (carriage entrances, double-leaf, tall enough for a carriage), pedestrian
entrances, their surrounds, the ironwork over/in them, and — critically — views showing the entrance
IN CONTEXT beside the shopfronts and windows of the same ground floor, so its relative size can be
read. Include shopfronts of the period (cast-iron framing, larger panes than the 1820s-50s timber).`,
    q: ['porte cochere Paris immeuble XIXe',
        'Paris carriage entrance door building 19th century',
        'porte immeuble haussmannien entree',
        'devanture boutique Paris XIXe siecle fonte'] },
]

phase('Collect')

const collected = await parallel(FAMILIES.map((fam) => () =>
  agent(
    `You are deepening a REFERENCE PHOTO CORPUS for a procedural architecture project on
19th-century Paris. An earlier pass collected 12 general images of Second Empire buildings; this
pass goes deep on one feature family so the rules have real evidence to answer to.

# Your family: **${fam.title}**  (key: \`${fam.key}\`)

${fam.aim}

Target: **${fam.n} images.** Quality over count — 8 legible images beat 20 unusable ones.

${PERIOD}

${SOURCES}

## Suggested starting queries — vary them, and add your own.
French terms work far better than English on Commons.
${fam.q.map((q) => `  - ${q}`).join('\n')}

## Selection criteria
KEEP only if you can actually see the thing this family is about: in focus, well lit, not
obstructed by scaffolding/trees/vehicles, at least ~600px. For DETAIL families a tight crop is
ideal; for facade families the whole elevation must be in frame.

REJECT: interiors, plans, maps, portraits, aerial cityscapes where no facade is legible, night
shots, modern buildings, and anything out of period per the tells above.

Set \`quality\` honestly (good/partial/poor) — the operator filters on it, and a \`partial\` marked
honestly is more useful than a \`good\` that is wrong.
Set \`rejected\` to how many candidates you dropped, and say in \`notes\` what the notable rejects
were and WHY — that record is genuinely useful.

## Output
1. \`mkdir -p ${REF}/images/${fam.key}\` and download there, filenames \`${fam.key}_01_slug.jpg\`.
2. Write \`${REF}/meta/${fam.key}.json\` containing exactly the object you return (write it with
   python3 so quoting is safe).
3. Verify with \`ls\` that every \`file\` exists and is >5KB. Drop failed downloads.
   \`saved\` must equal the number of real files on disk.
4. Return the structured object.

Do not report success for files that are not on disk.`,
    { label: `collect:${fam.key}`, phase: 'Collect', schema: SCHEMA, model: 'sonnet' }
  )
))

const good = collected.filter(Boolean)
const total = good.reduce((n, r) => n + (r.saved || 0), 0)
log(`Second Empire deep scrape: ${total} new images across ${good.length}/${FAMILIES.length} families`)

phase('Assemble')

const assembled = await agent(
  `Fold the new Second Empire reference families into the existing review page at \`${ROOT}\`.

## What changed
Eight new families were collected into \`${REF}/images/<key>/\` with metadata in
\`${REF}/meta/<key>.json\`:
${FAMILIES.map((f) => `  - \`${f.key}\` — ${f.title}`).join('\n')}

Collector results:
${good.map((r) => `  - ${r.family}: ${r.saved} saved, ${r.rejected || 0} rejected. ${(r.notes || '').slice(0, 200)}`).join('\n')}

## Task
1. Edit \`${ROOT}/dev/harness/build_review_page.py\`. Add each new key to \`FAMILY_INFO\` with its
   title and a one-line note on what it is evidence for (use the titles above). Order them so the
   eight new Second Empire families sit TOGETHER, immediately after the existing \`second-empire\`
   family, with the other original families following — the operator is working on Second Empire
   specifically and should not have to hunt.
2. Re-run the builder so \`${REF}/review.html\` includes them all.
3. **Preserve the existing selection.** The page persists selections in \`localStorage\` keyed by
   image file path, and \`${REF}/selection.json\` already exists with 64 chosen images. Adding
   families must not disturb either — verify the existing keys are untouched and say how you checked.
4. New images should follow the existing default: \`good\` pre-selected, \`partial\`/\`poor\` not.

Then update \`${REF}/README.md\` to describe the deepened corpus.

Report: total images now, per-family counts, and confirmation that the prior selection survived.`,
  { label: 'assemble:review-page', phase: 'Assemble', model: 'sonnet' }
)

phase('Verify')

const verdict = await agent(
  `Verify the deepened Second Empire corpus at \`${ROOT}\`. Check the filesystem; do not trust the
collectors' reports.

1. Count files per new family directory under \`${REF}/images/\`. Flag any file <5KB or zero-byte.
2. Every \`meta/*.json\` is valid JSON and every \`file\` entry resolves on disk. List dangling refs.
3. Every image record has a non-empty \`license\` and a non-empty \`shows\`. List any that don't.
4. \`${REF}/review.html\` exists and every \`src="images/..."\` resolves relative to \`${REF}/\`.
   Report the count of broken srcs (must be 0) and the total image count on the page.
5. \`${REF}/selection.json\` still lists 64 images and every one still resolves on disk — the new
   scrape must not have disturbed the operator's existing selection.
6. **Period spot-check — the important one.** Open at least 12 of the new images across families and
   LOOK at them. The family is strictly 1853-1870 canonical haussmannien. Flag any that show the
   post-1884 tells: a curved/arc comble rather than a straight 45-degree one, bow windows or oriels,
   elaborate near-universal mascarons or caryatids, Art Nouveau ironwork, or corner domes/rotondes.
   Report what you actually saw per image, and list any that should be downgraded to \`partial\` or
   dropped. Be specific — this is the reference case the whole generator is measured against, so a
   wrongly-dated image here is worse than a missing one.
7. Fix cheaply and safely: prune dangling metadata entries, delete zero-byte files, correct the
   \`quality\` of anything you judged wrongly dated, and re-run the page builder. Do NOT re-scrape.

Return a concise PASS/FAIL per check with the final counts and any images you downgraded.`,
  { label: 'verify:se-corpus', phase: 'Verify', model: 'opus', effort: 'high' }
)

return { newImages: total, families: good.map((r) => ({ family: r.family, saved: r.saved, rejected: r.rejected })), assembled, verdict }
