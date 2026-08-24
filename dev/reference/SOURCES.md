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

## 6. Dated anchors outside the Daly window

Daly is a single year, 1864. These are buildings with a **documented construction
date** used to give the chronology model something dated to answer to on the far
side of a decree. `dev/reference/meta/dated-anchors.json`.

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
