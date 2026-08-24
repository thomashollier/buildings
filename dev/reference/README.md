# Reference photo corpus

This is a hand-curated set of 171 real-world photographs (and, for one
family, measured 19th-century drawings) of Paris apartment buildings,
organised into 16 families that correspond to the stylistic / structural
periods and feature classes the procedural building generator is meant to
reproduce. The core period/feature sequence (`restauration` through
`ground-floor`) is deepened by eight additional Second Empire families
(`se-*`) that go feature-by-feature through the single most important
period in much greater depth than one `second-empire` family alone could:

| family          | period / topic                                          | count |
|-----------------|-----------------------------------------------------------|------:|
| restauration    | Restauration & Louis-Philippe (1820–1848)                 |     9 |
| second-empire   | Second Empire haussmannien, canonical (1853–1870)          |    12 |
| se-elevation    | Second Empire — measured elevations & drawings                |     9 |
| se-facade       | Second Empire — full frontal facades                           |    11 |
| se-ironwork     | Second Empire — ironwork & balcon filant                       |    10 |
| se-socle        | Second Empire — socle, bossage & refends                       |     8 |
| se-surround     | Second Empire — window surrounds, keystones & consoles         |    11 |
| se-comble       | Second Empire — the 45° comble, dormers & zinc                 |    11 |
| se-cornice      | Second Empire — cornices, modillions & string courses          |     8 |
| se-entrance     | Second Empire — portes cochères & entrances                    |     9 |
| third-republic  | Early Third Republic (1870–1884)                            |    13 |
| belle-epoque    | Belle Époque, post-1884 decree (1884–1902)                   |    11 |
| post-1902       | Post-1902 (Bonnier) & Art Nouveau                            |    13 |
| corner          | Corner buildings (angle / chamfer / rotonde)                  |    12 |
| class-range     | Modest faubourg vs grand boulevard (absolute vs proportional) |    13 |
| ground-floor    | Shopfronts, cafés, portes cochères                             |    11 |

The eight `se-*` families sit immediately after `second-empire` in both this
table and the review page, so anyone working on Second Empire specifically
finds all of it in one place rather than scattered among the later periods.

Each family's images live under `images/<family>/`, and its metadata lives in
`meta/<family>.json` — one JSON object per family with `family`, `saved`,
`notes` (a free-text collection log), and `images` (a list of per-photo
records: `file`, `title`, `source_url`, `license`, `author`, `year`, `street`,
`klass`, `quality`, `shows`, and — for the `belle-epoque` family only —
`corner`).

## How it was collected

All images are sourced from Wikimedia Commons (mostly via
`Category:Haussmannian architecture in Paris`, `Category:Mascarons in Paris`
and its by-arrondissement subcategories, plus targeted searches for named
buildings/streets). Files were downloaded via the Commons API's generated
`thumburl` (`iiurlwidth=1000`, actually delivered around 1280px wide) rather
than full-resolution originals or hand-built thumb paths.

`se-elevation` is the one exception to "photograph": its 9 images are
individually-scanned page images of measured facade elevations from César
Daly's *L'Architecture privée au XIXe siècle sous Napoléon III* (Paris: A.
Morel, 1864), Série 1, Volume 1 — a period-published, dimensioned source
rather than a photograph, kept separate precisely because it can answer
questions about exact proportion that no photograph can. The other seven
`se-*` families are ordinary Commons photographs, each a close, deep pass
on one specific Second Empire feature (ironwork, socle/bossage, window
surrounds, comble/dormers, cornice, or entrances) rather than a whole
facade.

Each family's `notes` field in its metadata JSON documents, per family:
what was searched for, what was accepted and why, and — importantly — what
was found and **rejected** (wrong period, not a photograph, obstructed,
mislabelled, etc.), so the corpus's gaps are visible rather than silent.

**Dating discipline.** Commons `extmetadata` almost never carries a
construction year for these buildings — only a photo-capture date, which is
irrelevant to the building's age and was never used as a stand-in. `year` is
left `""` throughout unless a construction date is independently confirmed
(an inscribed plaque, an architect's dated album entry, a museum record).
Nothing here was dated by "this looks like it's from the 1880s."

**Class discipline.** `klass` (modest / ordinary / comfortable / grand /
unknown) is an honest visual judgement of a building's scale and richness,
not a documented or sourced rating — sources never state a building's social
class. It is left `unknown` where no reasonable visual call could be made.

## Source & licence policy

Every image record carries `license`, `author`, and `source_url` copied
verbatim from the Commons file's API `extmetadata` (or, for a few archival
Paris Musées / BHVP prints, the museum's own CC0 attribution). Nothing here
is used past what its stated licence allows; all are either public domain,
CC0, or Commons-compatible open licences with attribution preserved. Follow
`source_url` from the review page or `selection.json` to verify any image's
licence before using it outside this project.

## Reviewing and selecting the ground-truth set

Open `review.html` directly from disk (double-click, or `open review.html`
on macOS) — it's a single self-contained file, no server or network needed.

The page groups all 171 candidates by family, shows every photo as a card
with its known metadata and a `good` / `partial` / `poor` collection-quality
badge, and lets you toggle selection per card (or per family, or globally).
`good`-quality photos are pre-selected by default; `partial` and `poor` start
unselected — review and override as needed. Click any thumbnail to open a
full-size lightbox with the complete metadata and a link to the Commons
source; use the left/right arrow keys to page through and Escape to close.
Your in-progress selection is saved to the browser's `localStorage`
automatically, so you can work through the set across more than one sitting.

Two limits govern how this review should be done, and the page repeats them
at the top: photographs support **qualitative** comparison reliably (rough
proportion, ornament family, silhouette, rhythm) and **measurement** not at
all (no photo here is a substitute for a drawn dimension). And treat a
visual pass/fail as a **tripwire, not a passing grade** — "that looks wrong"
is strong evidence something is broken in the generator; "that looks right"
is only weak evidence anything is actually correct.

When you're satisfied with a selection, click **Download selection.json** in
the sticky header. Save the downloaded file as:

```
dev/reference/selection.json
```

(overwriting any previous version). If the browser download is inconvenient,
**Copy JSON to clipboard** produces the identical payload to paste into a
file by hand.

## How `selection.json` feeds the VLM check

`selection.json` is `{ "generated_by": "review.html", "selected": [...] }`,
where each entry in `selected` is the full metadata record for one chosen
reference photo (`file`, `title`, `source_url`, `license`, `author`, `year`,
`klass`, `corner`, `shows`, `street`, `quality`, `family`). This is the
ground-truth set the VLM-check harness reads: for each family it has
selected reference photos for, the harness shows the VLM the generated
building output for that family alongside the selected reference image(s)
and their `shows` notes (which name the specific feature each photo is
meant to evidence — e.g. "45° comble" or "arc comble replacing the 45°
plane"), and asks it to flag qualitative mismatches. Consistent with the
limits above, the VLM check is a tripwire: a flagged mismatch means "go
look at this," not "this measurement is provably wrong," and a clean pass
means "nothing visually obvious is broken," not "this is dimensionally
correct."

## Regenerating the review page

`review.html` is generated, not hand-edited. If the corpus changes (new
images, new metadata files, edited `notes`), regenerate it with:

```
python3 dev/harness/build_review_page.py
```

This reads every `dev/reference/meta/*.json` and rewrites
`dev/reference/review.html` in place. Existing selections in the reviewer's
browser `localStorage` are keyed by image file path and are unaffected by
regeneration as long as file paths don't change.
