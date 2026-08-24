# Source register

Every primary source the rules are answerable to. The brief makes this a standing
requirement rather than a courtesy:

> "Keep the rules inspectable and sourced. Encode where each number comes from,
> and mark clearly the ones you inferred because the source was silent. Then a
> test can assert the documented figures and fail when the model drifts from the
> law it claims to implement."

Two kinds of evidence, and the distinction is load-bearing:

- **Measured drawings** support *measurement*. A number may be calibrated on them.
- **Photographs** support *qualitative comparison* and measurement **not at all** —
  perspective, lens and unknown camera position mean dimensions cannot be read off
  them. They are a tripwire, never a source for a figure.

---

## 1. César Daly — the measured drawings

**César Daly, *L'Architecture privée au XIXme siècle sous Napoléon III —
Nouvelles maisons de Paris et des environs*.** Paris, 1864 (Série 1) and 1872
(Série 2).

The single most valuable source in this project. Plates are **captioned with the
building's class, address and architect**, and carry a **scale bar**
("Échelle de 0.02 c.m pour mètre", graduated in mètres); many also carry printed
metric callouts and dimension ladders.

Daly's own *Première / Deuxième / Troisième Classe* ladder is a **period class
taxonomy attached to measured drawings** — which is what lets this project's
`BuildingClass` constants be sourced rather than invented.

Scans are public domain, digitised by the **Polona digital library** (National
Library of Warsaw) and mirrored on Wikimedia Commons.

### Start here

**<https://commons.wikimedia.org/wiki/Category:L%27architecture_priv%C3%A9e_au_XIXe_si%C3%A8cle_sous_Napoleon_III>**

The parent category. Every volume hangs off it, and each volume page renders all
of its plates as a browsable thumbnail grid — click any plate for the full-size
scan, its licence and its provenance.

| Volume | Files | Typology | Period | Used |
|---|---:|---|---|---|
| **Sér. 1, Vol. 1, t. 2 (1864)** | **83** | ***Maisons à loyer*** — Paris rental apartment buildings | **1853–70, canonical Second Empire** | **Yes — 77 plates harvested** |
| Sér. 1, Vol. 1, t. 1 (1864) | 69 | *Hôtels privés* — private mansions | 1853–70 | No — different typology |
| Sér. 2, Vol. 2 (1872) | 64 | Maisons and hôtels | early Third Republic | Not yet |
| Sér. 2, Vol. 3 (1872) | 46 | Villas suburbaines | early Third Republic | No — different typology |

Commons category pages (each renders every plate as a browsable thumbnail grid):

- Sér. 1, Vol. 1 t. 2 (1864) — <https://commons.wikimedia.org/wiki/Category:L%27architecture_priv%C3%A9e_au_XIXe_si%C3%A8cle_sous_Napoleon_III._S%C3%A9r._1%2C_Vol._1_t_2_%281864%29>
- Sér. 1, Vol. 1 t. 1 (1864) — <https://commons.wikimedia.org/wiki/Category:L%27architecture_priv%C3%A9e_au_XIXe_si%C3%A8cle_sous_Napoleon_III._S%C3%A9r._1%2C_Vol._1_t._1_%281864%29>
- Sér. 2, Vol. 2 (1872) — <https://commons.wikimedia.org/wiki/Category:L%27architecture_priv%C3%A9e_au_XIXe_si%C3%A8cle_sous_Napoleon_III._S%C3%A9r._2%2C_Vol._2_%281872%29>
- Sér. 2, Vol. 3 (1872) — <https://commons.wikimedia.org/wiki/Category:L%27architecture_priv%C3%A9e_au_XIXe_si%C3%A8cle_sous_Napoleon_III._S%C3%A9r._2%2C_Vol._3_%281872%29>
Full-resolution originals: <https://polona.pl/>

### What was harvested

`dev/reference/images/daly-1864/` — **77 plates**, metadata in
`dev/reference/meta/daly-1864.json`.

| By drawing | | By Daly class | |
|---|---:|---|---:|
| Elevation | 16 | Deuxième Classe | 49 |
| Detail | 28 | Première Classe | 19 |
| Plan | 31 | Troisième Classe | 8 |
| Section | 2 | (multi-class sheet) | 1 |

All 77 carry a scale bar; 30 also carry printed dimensions. All 16 elevations
have a scale bar and a named class and address:

- **Première** — 3 rue de la Paix (Paul Mesnard); Champs-Élysées 119 and 125;
  Avenue de l'Impératrice
- **Deuxième** — boulevard de Sébastopol 1, 2–4, 63, 77, 120; rue de Rivoli 88;
  rue Bergère 26; rue du Conservatoire 9; rue Neuve des Mathurins 39;
  boulevard Saint-Germain 6
- **Troisième** — boulevard Beaumarchais 36–38–40 (a *triple* elevation, so it
  also evidences how neighbours align); rue de Longchamps

### A correction worth keeping on the record

Série 1 was initially assumed to be two *maisons à loyer* tomes. It is not:
**t. 1 is *hôtels privés***, a different typology. The tome title page reads
"TOME PREMIER DU VOL. PREM. — HOTELS PRIVES", confirmed against plate captions
("HOTEL PRIVE… par Mr Botrel"). All 69 were correctly excluded during the
harvest. The real pool for this project was 83 plates, not 154.

---

## 2. The regulations

The primary legal sources, cited in
`src/buildings/typologies/paris/reglement.py` and asserted by
`tests/unit/test_reglement.py` against their stated figures.

| Source | What it fixes |
|---|---|
| Déclaration royale, 10 avril 1783 / lettres patentes, 28 août 1784 | First ties facade height to street width; combles inscribed below a 45° diagonal springing from the eaves |
| Ordonnance de 1823 | Balconies project at most 0.80 m, and only at 6 m or more above the pavement |
| Circulaire du 21 septembre 1855 | Within a block, balcony, cornice and entablature lines must align building to building |
| Règlement du 27 juillet 1859 | Streets over 20 m may build 20 m of facade; minimum storey height 2.60 m |
| Décret du 22 juillet 1882 | Oriels permitted, ≤0.40 m projection, demountable; masonry oriels from 1893 |
| Décret du 23 juillet 1884 (Alphand) | Raises the height table; replaces the 45° diagonal with a circular arc — 20 m facade + 8.50 m comble = **28.50 m** |
| Décret du 13 août 1902 (Bonnier) | Comble inscribed in an eighth-circle arc continued by a 45° oblique; projections may carry above the cornice |

The 28.50 m ceiling is reproduced by the envelope arithmetic exactly, and was not
fitted to.

---

## 3. Photographic corpus

`dev/reference/images/` — **248 images across 17 families**, every one with a
recorded licence, author and source URL in `dev/reference/meta/*.json`.

Primary source **Wikimedia Commons**, with some Paris Musées and BnF/Gallica open
content. Licences: CC BY-SA (4.0/3.0/2.0), CC BY (4.0/3.0/2.0), CC0, and public
domain.

Notable photographers in the set: **Charles Marville**, whose 1860s
documentary views of the new boulevards (boulevard Malesherbes, boulevard
Saint-Michel) are contemporaneous with the buildings themselves.

**These are for qualitative comparison only.** No figure in the model is
calibrated on a photograph.

### Dating discipline

`year` is recorded **only where a source states it**. Commons descriptions
usually give the *photograph* date, which is irrelevant to a building's
construction date and was never used as a proxy. Of the original 94-image corpus,
63 have no recorded year — an honest unknown, not a gap to be filled by guessing.

---

## 4. Secondary literature

- **François Loyer, *Paris XIXe siècle: l'immeuble et la rue*** (1987) — the
  argument that the building only makes sense as a piece of the street. The
  source of this project's block-as-unit premise.
- **Stiny & Gips (1971)**; **Wonka et al., *Instant Architecture* (2003)**;
  **Müller et al., *Procedural Modeling of Buildings* (2006)** — the split/shape
  grammar lineage behind the fitting solver.
- **Esri CityEngine** and its CGA grammar — the reference for split-with-flexible-slots.

---

## 5. How sourcing is enforced

- `Reg(value, source)` raises on a blank citation, so a regulatory number cannot
  exist without one.
- Constants that are **not** sourced are marked `INFERRED` in the code, with a
  note saying so and a test that fails if the marker is removed.
- `tests/oracle/` asserts the documented regulatory figures against the ported
  règlement, and hard-fails rather than skipping if the source repo is absent.
- Measurements taken from Daly are tagged `MEASURED` / `DERIVED` / `UNCERTAIN`,
  and recorded in `dev/reference/daly_measurements.json` with the plate each came
  from.

---

## 6. Published plates other than Daly

`dev/reference/images/published-plates/`, `meta/published-plates.json`.

Engraved elevation sheets from 19th-century French architectural publications
that are **not** Daly. What unites them is that they are *measurable*: each
carries a scale bar, printed dimensions, or a sectional storey ladder. Daly is
one publication in one year; these are independent draughtsmen, publishers and
dates, which is the only way to tell a Daly **convention** apart from a Paris
**fact**.

**The three that matter most:**

| sheet | why |
|---|---|
| **bd de Sébastopol n° 72** — Moniteur des Architectes, 60ᵉ vol., pl. 715; Th. Vacquer *del.*, arch. Rolland | **Printed dimensions**: cornice **17.55**, comble **4.87**, width **16.40 m**, plus a 10 m scale bar. Same boulevard as six Daly anchors, different publication — and 17.55 m is exactly the 1859 règlement's cornice for the 12–20 m band *and* exactly Daly's figure at 1 bd de Sébastopol. Independent corroboration of the single most load-bearing number in the model. |
| **rue de Rennes** — "ANNÉE 1881, PL. 58", Maurage sc., arch. BOUSSARD (partial reading) | Dated **1881** and carries a scale bar: the only sheet in the register that is both dated and measurable outside 1864, and it lands in the long gap between the 1859 règlement and Alphand. |
| **avenue Duquesne** — A. Lévy éditeur, V.2 pl. 36; E. Japhet *del.*, arch. P. Vigouroux | A *maison de rapport de petits appartements* with a **printed total cost** (80 897 f 75, terrain excluded) and a **vertical section strip** showing every floor slab. The only direct evidence of what a programme cost, against a corpus drawn from a luxury journal. |

### On the archimaps crawl

`archimaps.tumblr.com/search/paris` was walked 15 pages deep, 223 posts, rate
limited. **The yield for the Second Empire was thin, and that is the finding
worth recording:** 203 of the 223 are not immeuble elevations at all — monuments,
churches, palaces, exposition pavilions, fountains, tombs, interiors. Of the 20
that matched the typology, most were interiors, plans, photographs or *hôtels
particuliers*. Seven elevations were kept, and **all seven read 1890s–1900s**
(Plumet, Labro, Chauchat), so they serve the post-1902 end of the chronology and
are **not** evidence for the 1859–1884 core.

The one Second Empire commercial sheet that blog holds is bd de Sébastopol 72 —
which the operator had already supplied by hand.

**Provenance is the weak part of this whole family.** These came from image
reposts, not from institutional scans. The *engravings* are long out of
copyright; the scans' hosts and rights are not recorded, and two sheets carry no
year at all. Treat the drawing as evidence and the attribution as a lead until an
original is located.

## 7. Dated anchors outside the Daly window

Daly is a single year, 1864. These are buildings with a **documented construction
date** used to give the chronology model something dated to answer to on the far
side of a decree. `dev/reference/meta/dated-anchors.json`.

### Rue de Rennes, Paris 6e — **1881** (plate)

`images/dated-anchors/1881_rue-de-rennes.jpg`

*Maison à Paris, rue de Rennes — façade principale.* **ANNÉE 1881, PL. 58**,
printed top left and top right of the sheet. Engraved by **Maurage**, printed by
**Imp. Lemercier et Cie**. Architect **BOUSSARD** — a partial reading: the credit
line is clipped by the bottom edge of the scan and the descenders are cut, so the
letterforms are consistent with it but this is not a citation.

The 1881 is the **publication's** date, not a construction date. That is the
right kind of date for the chronology model, which asks what a designer would
draw in a given year.

**Why it earns a place.** Two reasons, and the second is the stronger:

1. It sits **twenty-two years after the 1859 règlement and three years before
   Alphand**. The register had Daly's single year (1864) and one anchor at 1887,
   and nothing in the long middle the model runs straight through.
2. It **carries a scale bar** — 0 to 9 m, printed along the bottom. The 1887
   anchor is a 340 px thumbnail: datable but not measurable. This is the only
   dated, measurable plate outside 1864 in the register.

**It bears on an open question.** The upper-floor sill is unresolved (A21, and
the note below): `sill_lean_height` is INFERRED at 0.90 m, while Daly's measured
aspects imply 0.21–0.33 m on plate 77 and a noisy 0.21–1.76 m across the corpus,
because `opening_width_typical` is one figure per building reconstructed against
per-storey aspects. A scale bar separates the allège, the light and the lintel
bearing directly instead of by subtraction, which is exactly what that
reconstruction cannot do.

**Provenance is the weak part.** Supplied by the operator from a Tumblr repost;
the original scan's host is not recorded and the publication is unidentified —
"ANNÉE 1881 / PL. 58" with Lemercier printing is a French architectural annual,
but not Daly's *L'Architecture privée*, whose plates are captioned differently.
The engraving itself is long out of copyright; the scan's status is unknown.
Treat the drawing as evidence and the attribution as a lead.

### 31 rue de la Chaussée d'Antin / 71 rue de Provence, Paris 9e — **1887**

Corner *immeuble*, architect **Alfred Leroux**. R+5, ≈20 m, 421 m² parcel,
commerce below and housing above. Current ground-floor tenant: Onyx.

Three independent date sources, in increasing order of authority:

| source | date |
|---|---|
| *Bulletin municipal officiel*, 14 Feb 1886 | permit filed **13 February 1886** |
| PSS-archi | completion **≈1888** (estimated) |
| **the building itself** | **1887**, carved on the escutcheon |

The carved date falls between permit and estimate and resolves it. A date cut
into the fabric outranks a database estimate, and this is the only building in
the corpus that dates itself.

**Why it matters.** 1887 is **three years after the Alphand decree of 23 July
1884**, so it was designed under the arc-comble regime, not the 45° one that
governs every Daly plate. PSS classifies it *"Post-haussmannien"*. Yet it reads
as a classic haussmannien corner to almost any eye — which is the strongest
concrete argument for **date windows over a period enum**: an enum would file
1887 under "Third Republic" and lose the fact that the building still obeys
everything the 1859 règlement asked, under a different roof rule.

It is also the *pan coupé* case, the same condition as 3 rue La Fayette.

**Limits:** the only image located is a 340 × 255 thumbnail — enough for massing
and corner form, too small to judge whether the comble is the post-1884 arc, or
to read the escutcheon independently. The carved date is the operator's reading
from the street, not verified from a photograph. No Commons image exists; the
files indexed under "52 rue de la Chaussée d'Antin" are Carnavalet merchant's
tokens from a shop that traded nearby, not the building.
