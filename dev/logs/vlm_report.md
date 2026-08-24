# VLM reference check — S11

**Run:** `python3 dev/harness/vlm_check.py` (and `--augment`, see below)
**Outputs:** `dev/logs/vlm/` (64 pairs, `sheet.html`, `situations.json`),
`dev/logs/vlm_aug/` (131 pairs, augmented run)

---

## 1. Ground-truth set

`dev/reference/selection.json` **exists**, so the fallback was **not** used. 64
images. But two things about it have to be on the record, because they change
how much the pass is worth:

1. Its own `generated_by` field reads
   `"orchestrator (all quality=='good', the review page's default selection)"`.
   That is the review page's *default* pre-selection, not a human's considered
   judgement of which buildings are ground truth. `quality` grades the
   **photograph** (framing, obstruction, resolution); it does not say the
   operator vouched for the **building** as a specimen. So this is a
   "selection" in file format only.
2. Eight scraped families **postdate** the selection file and are absent from
   it — `se-comble`, `se-cornice`, `se-elevation`, `se-entrance`, `se-facade`,
   `se-ironwork`, `se-socle`, `se-surround` — 67 further `quality=="good"`
   images, and they are the most *targeted* material in the corpus (they were
   scraped to evidence single features). The harness detects this, says so in
   its provenance line, and offers `--augment` to fold them in tagged
   `UNSELECTED`. **Two of the findings below (F1, F7) are carried by images
   from that augmented set** and are flagged accordingly.

Of the 64 selected, **39 are whole elevations** and **25 are close-up details**
(a mascaron, a stretch of railing, one shopfront, a metro entrance). A detail
cannot be compared against a whole-facade render on the axes this check cares
about — storey count, proportion, roofline — so the harness marks them and they
are judged only on the one feature they show.

## 2. The two limits, and how they were respected

**Photographs support qualitative comparison and no measurement at all.** Every
image was taken from an unknown position with an unknown lens; verticals
converge, roofs are seen from below, facades are foreshortened. **No number
anywhere in this report was read off a photograph.** Every metre, ratio and
count quoted comes from the IR (`node.props`) or from the source, and is there
to *locate* a defect the eye found — never to prove one. Where I say something
is "too short" or "too few", the evidence is a difference in **kind or
proportion within one image**, which survives perspective; not a dimension.

**A visual check is a tripwire, not a passing grade.** Everything below is
ranked by how confidently the eye says *wrong*, not by how much would be fixed.
Nothing here should be read as "the rest is correct" — a systematic three
percent is invisible at this resolution by construction and belongs to the
assertions. Three of the findings (F4, F5, F8) were **found by eye and then
confirmed against the IR**, which is the intended direction; none was found by
measuring a JPEG.

## 3. This harness's own weaknesses

- The corpus records an **address, not a street width**, and the gabarit needs
  the width. `vlm_check.SITUATIONS` supplies one per street and tags each
  `measured` / `estimated` / `unknown`. On an `estimated` row, a *height*
  disagreement is a question about that table before it is a question about the
  generator. It is printed beside every render for exactly that reason.
- **A corner situation cannot be rendered by `generate()` alone.** `corner=True`
  changes nothing structural in the building tree except that the comble is
  hipped (verified: identical node census, identical child counts). The pan
  coupé lives in `block.solve_block`. So all 8 `corner`-family pairs, and the
  `corner: true` belle-époque ones, are being compared against a plain
  mid-block elevation. That is a real property of the architecture, not a bug —
  but it means those pairs cannot be judged on their corner at all, and one
  block render (`dev/logs/vlm/era/block.png`) was made separately to cover it.
- Class comes from the corpus's own honest-but-unsourced visual judgement, and
  year is empty on most records (the corpus's dating discipline), so most
  buildings are generated at a **family-default year**. A period mismatch on an
  undated record is therefore uninformative.

---

## 4. Per-pair findings

Pairs inspected closely are named. The remaining elevations were surveyed as a
contact strip (`dev/logs/vlm/contact_a.png`, `contact_b.png`); nothing in them
contradicted the pattern below, and the population reads as **one composition
repeated 39 times** with the roof cap as almost the only variable.

### second-empire — the generator's core competence

- **45 · 1–3 Place Saint-Michel** (grand, 30 m, corner). The reference is a
  five-storey stone facade under a *tall bell-cast mansard* carrying two tiers
  of openings, capped by a corniche so deep it reads as a black line at 50 m.
  The generated building is a five-storey stone facade under **a triangular
  hipped gable with a sharp apex** and a cornice that is a flat lip flush with
  the wall. Same storey count, right ballpark height — but not the same *kind*
  of object. Also: the left-hand dormer stands entirely **outside** the drawn
  roof, floating over the cornice, because the hip has already collapsed to the
  eaves at that x. Two chimneys are 0.8 m stubs riding the cornice corners.
- **47 · Avenue de l'Opéra 38** (grand, 30 m, mid-block — the best-framed pair
  in the set). The nearest thing to a match. Storey count, entresol, balcon
  filant at the noble floor and again under the cornice: all present and all
  right. What is wrong is **density and crown**: four windows where the
  reference's rhythm gives roughly twice that over the same frontage, so the
  wall reads under-fenestrated; a cornice with no projection; three tiny
  dormers where the reference has one large lucarne per bay, each nearly as
  wide as the bay below.
- **54 · 12 rue Halévy** (grand, 18 m). Same as 45. The reference's mansard
  carries a large dormer row *plus* a row of oeils above; the generated roof is
  a shallow gable with two dormers and a chimney at the apex. The reference's
  ground order is a tall rusticated arcade with a monumental arched porte
  cochère; the generated ground order is short, smooth, and has a **flat brown
  rectangle for a carriage door**.

### class-range — where the class ladder shows

- **17 · 2 boulevard Voltaire** (ordinary, 35 m). Nearly frontal photograph, so
  the cleanest comparison available. The generated upper windows are **small
  squarish punched holes** in a lot of blank stone; the reference's are tall
  casements running nearly floor-to-ceiling behind their railings. This is the
  observation that led to F5 below.
- **16 · rue Saint-Merri 17–19** (modest, archival). **The roof is 37 % of the
  building.** A five-storey modest faubourg house wearing a blank grey slab
  taller than two of its storeys, with three tiny dormers pushed to the bottom
  edge and metres of empty zinc above them. This is the single most
  face-obvious wrongness in the selected set, and the reference — a modest
  house with a modest comble — makes the point without any measuring.
  Also: the right-hand bay carries an **oculus on the top floor and a stunted
  narrow window on the two below it**, i.e. one vertical strip that is a
  different thing on every storey.
- **13 · 53 rue Blanche** (comfortable, 12 m). One of the better pairs; at a
  glance it reads as a Paris building. Wrong: three windows where the reference
  shows more over the same frontage; two dormers, shoved to the extreme ends of
  a roof they do not fill; a porte cochère with no archivolt, keystone or
  imposte where the reference has a monumental arched one; a balcon filant
  drawn as a **uniform picket fence** with no consoles and no panel rhythm.

### belle-epoque and post-1902 — where it breaks down completely

- **9 · 130 rue Réaumur** (grand, 1893, corner). The comble is **a smooth grey
  pyramid with a single chimney on the apex**, about a third of the total
  height. The left-hand bay is a blind panel on two storeys, a narrow window on
  a third and an oculus on the fourth. Nothing about this reads as Paris.
- **37 · 26 rue Vavin, Sauvage** (grand, clamped to 1902). The comble is
  **12.2 m — taller than the whole stone facade below it** — drawn as a plain
  grey rectangle with a **saw-tooth zig-zag along its top edge**, carrying one
  dormer at the very bottom. This is the worst single render in the set.
- **1, 3 · Castel Béranger**, **5, 6 · Lavirotte**: named Art Nouveau one-offs.
  Comparing them to a rule-driven typology is not informative in either
  direction and I have not scored them.

### corner

- **24 · angle rue du Renard / Saint-Merri** (modest, 8 m, 1895). **A chimney
  hangs in the sky, detached, roughly 3.5 m above the roof apex**, over a
  triangular gable. Unambiguous render/termination failure — see F3.
- 18–23, 25: all compared against a mid-block elevation for the reason in §3;
  the only corner-specific thing they exercise is the hipped comble, and that
  is F2.

### restauration

- **41, 42 · 84 and 87 rue de la Victoire** (comfortable, 1835). Marville. The
  generated 1835 building is **compositionally indistinguishable from the
  generated 1865 and 1893 ones** — same surrounds, same railings, same cornice,
  same dormers. Separately: the reference's every window carries *persiennes*,
  and shutters are not modelled at all. See F9.

### ground-floor (details)

- **28 · devanture, boulangerie rue Ordener** and **26, 29, 30, 32**. Each shows
  the same thing: a Paris shopfront is a **timber/lacquered devanture applied in
  front of the masonry** — projecting shop cornice, lettered enseigne fascia,
  framing pilasters, stallriser panel under the glass, recessed door.
  `GroundProgramme.SHOP` produces **a stone arcade with plate glass in it** and
  none of those five parts. See F8.
- **27 · porte cochère, rue de la Tombe-Issoire**: same story as 13 and 54 — the
  reference's arched, moulded, keystoned carriage door versus a flat rectangle.

### augmented (unselected) references that decided two findings

- **`se-comble_03` brisis / terrasson with pedimented dormers.** The reference
  is the definition of a Paris comble: steep slate *brisis* whose **full height
  is occupied by one pedimented dormer per bay**, a hard horizontal break, then
  a shallow zinc *terrasson* with standing seams. The generated comble is one
  unbroken plane with two dormers in its bottom fifth. → F1.
- **`se-cornice_02` rue Halévy modillions.** Deep projecting corona on a dense
  modillion row over a dentil course, throwing a hard shadow. The generated
  cornice is a 0.68 m flat band flush with the wall, identical for modest and
  grand. → F7.

---

## 5. Ranked "that looks wrong" signals

Ranked by confidence that something is broken, then by how much of the corpus
it touches.

### F1 — The comble is not a mansard: no brisis/terrasson break, ever, before 1884
**Every pre-1884 building.** `elements.draw_roof_mass` draws the break line only
when `abs(lower_angle_deg - upper_angle_deg) > 1.0 and break_pct < 0.995`. A
45° comble states equal angles and `break_pct == 1.0`, so **no break is ever
drawn** and the whole Second Empire period renders its roof as a single
unbroken plane. Reference `se-comble_03` shows what is missing. The dormers
compound it: they sit in the lowest fifth of the roof with bare zinc above,
where a real lucarne occupies the *whole* brisis.
*Where:* `terminate.py` (what the roof states) and
`render/svg/elements.py:draw_roof_mass` (what is drawn from it).

### F2 — A hipped comble becomes a barn roof: the hips meet in the middle
**Every `corner=True` building, i.e. all 8 corner-family pairs plus the corner
belle-époque ones.** `elements._hip_arris` runs the hip inward by
`min(facade_w/2, section_run)`, where `section_run` is the silhouette's run —
which is measured along the **parcel depth** (9.0 m for the default 18 m
depth), a quantity that has nothing to do with how far a hip runs along a
frontage. With `parcel_depth = 18`, any frontage under 18 m gets both hips
meeting at mid-frontage: **no ridge at all, a pure triangular gable or
pyramid.** That is essentially every parcel in the corpus. The renderer's own
docstring admits `"Hipped" does not say how far the hip runs along the
frontage` — this is the cost of that silence, and it is not a small graphical
one.
*Evidence:* pairs 45, 9, 24, 54.

### F3 — A chimney floats detached in the sky
**Narrow hipped buildings.** `terminate` places the souche at the *stated* ridge
(`_roof_surface_height_at`), while `_hip_arris` truncates the *drawn* apex to
`full_h × half / full_run`. The two disagree whenever `facade_w/2 < section_run`
— the same condition as F2 — and the stack is drawn hanging in mid-air above
the roof it is supposed to stand on. For pair 24 the IR states the stack base at
`y = 17.92 m` while the drawn apex is at `eaves + 6.38 × 4.0/9.0 = 14.38 m`.
The building's own `props["h"]` (total height) also disagrees with the drawing
by the same amount, so `building_extent_m` is wrong for these.
*Evidence:* pairs 24 and 28.

### F4 — The comble's share of the building is inversely proportional to class
Found by eye on pair 16, confirmed in the IR. Same street (20 m), same parcel
(16 m), 1865:

| class | eaves | comble | comble as % of total | dormers |
|---|---:|---:|---:|---:|
| modest | 12.99 | **7.73** | **37 %** | 5 |
| ordinary | 14.92 | 5.80 | 28 % | 4 |
| comfortable | 16.32 | 4.40 | 21 % | 3 |
| grand | 17.37 | **3.34** | **16 %** | 2 |

`total_height == legal_total_height` in **all** cases: the comble always fills
the legal envelope to the millimetre regardless of who built it. So the part of
the facade allowance a modest builder *declines to use* is silently converted
into roof, and the poorer the building the bigger its hat. The dormer count
follows the same inversion — a modest 16 m frontage gets 5 lucarnes and a grand
one gets 2, which is backwards twice over: the grand building should have both
the richer *and* the more numerous dormers.

### F5 — Upper-storey windows are squat, outside the catalogue's own declared band
Found by eye on pair 17, confirmed against `catalogue.opening_aspect_band()`,
which states the Paris band as **(1.70, 2.00)**. Over a sweep of 4 classes ×
5 street widths × 3 parcel widths × 3 years, excluding mezzanines and oculi:

| class | role | median aspect | min | % below 1.70 |
|---|---|---:|---:|---:|
| grand | principal | 2.00 | 2.00 | 0 % |
| grand | upper | **1.42** | 1.00 | **92 %** |
| comfortable | upper | 1.49 | 1.00 | 82 % |
| ordinary | principal | 1.68 | 1.56 | 68 % |
| ordinary | upper | **1.25** | 1.00 | **98 %** |
| modest | upper | 1.70 | 1.00 | 58 % |

The principal is pinned at exactly the top of the band in every single case and
everything above it collapses, some of it to **1.00 — a square window**. This is
the visual cause of "the wall has holes in it instead of windows", and it is a
declared-contract violation, so it should become an assertion rather than
living here.

### F6 — Grand buildings get *fewer* windows than modest ones on the same frontage
Class scaling is applied to the **bay pitch**: the grand bay solves to
4.05–4.09 m against modest's 2.55–2.68 m. On the same 16 m frontage that is
**4 openings per floor for grand and 6 for modest**. Real Paris moves the other
way — money buys taller, richer openings, not a sparser wall; bay pitch is
bounded by what the structure will span (roughly 2.7–3.4 m) at every class.
Visible on pairs 47, 9, 54 as facades that read too blank for their pretension.

### F7 — There is effectively no cornice
The cornice is a flat band (0.68 m in the sampled cases) flush with the wall,
carrying at most a dotted dentil row, **identical for modest and grand and for
1830 and 1901**. In the references it is the most identity-carrying element of
the whole facade: a projecting corona on modillions throwing a hard shadow,
richer as the class rises. Reference `se-cornice_02`. On grand buildings its
absence is the difference between "a Paris building" and "a block of flats".

### F8 — `SHOP` produces a stone arcade, never a devanture
The generated ground floor is masonry openings with plate glass in them. A Paris
shopfront is a *thing applied in front of the masonry*: projecting shop cornice,
lettered enseigne fascia, framing pilasters, stallriser under the glass,
recessed door. None of the five is drawn. Note `render/svg/render.py` claims the
shopfront node carries a threshold band and an enseigne board — those are in the
IR but do not read at facade scale. Related: the porte cochère is a flat
rectangle with no archivolt, keystone or imposte, which is the other half of
what makes a Paris ground floor legible.
*Evidence:* pairs 28, 26, 29, 30, 32, 27; and 13, 54 for the door.

### F9 — Chronology has almost no visible signature
Same site, same seed, same class, five years (`dev/logs/vlm/era/era.png`,
1830 / 1855 / 1870 / 1890 / 1901): the compositions are **indistinguishable**.
Identical bay layout, identical window surrounds, identical railing rhythm,
identical cornice, identical dormer count and placement. What changes is the
roof's *height* (correct in principle) and a small shift in railing pattern.
S5's whole apparatus — variant date windows, prevalence curves, class adoption
lag — is not reaching the drawing. A viewer cannot date any of these five to
within seventy years, which is precisely the thing the brief says the model is
for.

### F10 — One bay of the facade is a different thing on every storey
The inserted `special` slot changes its opening type floor by floor. Real
output, one comfortable building, bottom to top:

```
base       … blind_panel …
mezzanine  … narrow_window …
principal  … blind_panel …      ← a blind panel on the noble floor
upper      … narrow_window …
upper      … oeil_de_boeuf …
```

It is also always inserted at **one end only**, never balanced. Visible in most
of the 39 elevations as an incoherent strip down one side, and a blind panel on
the principal storey of a comfortable building is a solecism, not a variation.

### F11 — The attic storey is an empty box
Every generated building carries an `attic` storey node — 3.3–3.7 m of it,
inside the comble — with **zero children** in every case sampled. The comble
floor is never lit from its own storey; the only openings in the roof are the
free-standing `dormer` siblings, which are too few and not aligned to the bays
below. The roles phase names the storey and nothing then qualifies it.
The dormers' own trace says `dormer.one_per_bay_of_the_storey_it_lights`, which
the output contradicts (2 dormers, 4 bays).

### F12 — Across a block the cornice line holds but the ridge line does not
`dev/logs/vlm/era/block.png` (72 m, six parcels, both corners chamfered). The
cornice, string courses and balcon filant lines run true across every parcel
boundary — S9's stated gate, and it holds visibly. But **the roofline is a
zig-zag**: the chamfered end parcels take their own hipped pyramids (F2) and the
middle run takes a taller slab, so the ridge steps down, up and down again. A
Paris block reads as one continuous mansard; this reads as three buildings that
were delivered separately.

### F13 — Ironwork reads as a picket fence and never varies
Uniform vertical bars with a row of dots, dead straight edge to edge, at every
level, every class and every year. No consoles under the balcony, no panel
rhythm per bay, no moulded main courante; the balcony slab itself is a hairline
with no thickness. A balcon filant is one of the two or three things a viewer
uses to place a Paris building, and it is currently a fence.

### F14 — Souches are 0.8 m stubs, two of them clipped at the facade edges
Every chimney is `h = 0.80 m`, and the end pair are placed at `x = 0.0` and
`x = facade_w − 0.47` at half width, so they render as small blocks riding the
cornice corners rather than stacks on a party wall. Reference `se-comble_02`
and `se-comble_10` show what a Paris roofscape's souches are: tall brick
stacks with terracotta pots, well above the ridge.

---

## 6. What looked right (weak evidence, recorded as such)

- **Storey counts and overall height** land in the right band for every class
  and street width in the set; the facade→cornice proportion is convincing.
- **The balcony rule is correct where it matters.** I went looking for the
  classic failure — a balcony a storey too low on modest buildings — and did not
  find it. Lowest balcony across classes: 6.35–7.05 m, all above the ordinance's
  6 m. Distribution is idiomatic too: *balcon filant* at the principal storey
  and again at the storey under the cornice, individual balconies between,
  nothing on the ground or the entresol. This one is genuinely good.
- **The entresol** appears and reads correctly on comfortable and grand.
- **Storey diminution upward** is monotonic among habitable storeys.
- **Block datum unity** (F12's other half) holds visibly.
- Height **steps** with street width rather than sliding.

None of this is evidence that any of it is dimensionally right.

## 7. What this check cannot say

- Nothing about **dimensional accuracy**. F4, F5 and F6 quote numbers, but
  those came from the IR after the eye had already flagged the pair; they are
  citations, not measurements of a photograph.
- Nothing about **corner buildings** as such — see §3. The corner pairs test the
  comble and nothing else until they are routed through `block.solve_block`.
- Nothing about the **67 unselected images** unless `--augment` is passed; the
  selection on disk is the review page's default and predates them.
- Nothing about **ornament quality** (mascarons, caryatids, keystone
  sculpture): 25 of the 64 selected are close-up details of exactly that, and
  the generated output has no resolution at which they can be compared.
