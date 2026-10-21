# Blind observer: the Parisian immeuble de rapport, 1820–1902

Street-facade grammar derived from photographs and measured/dated plates, written
**blind to the model**: only `dev/reference/` was read (the Daly measurement set,
the operator axis counts, the corpus metadata and the images themselves). Nothing
under `src/`, no rule file and no other fidelity document was opened.

Date of observation: 2026-10-21.

---

## 0. Method, and one deviation

**Planned:** query the Wikimedia Commons search API, fetch `thumburl`s, look at 15+
buildings.

**What happened:** this session's network policy refuses `commons.wikimedia.org`,
`upload.wikimedia.org` and the other Wikimedia hosts (proxy `403` on CONNECT). So
I did not run new searches. Instead I looked at **the photographs already in
`dev/reference/images/`**, which were downloaded from the same Commons API
(`thumburl`, ~1280 px) and keep their Commons `source_url`. That reuses the
corpus's selection, so its biases (listed in §0.3) are inherited. I re-read every
image myself and did not take the `shows` captions on trust. In several places I
disagree with them (see R9.6 on curved combles).

**Scale references used for estimates:** storey ≈ 3 m (but see R3, which varies
2.3–4.9 m), person ≈ 1.7 m, door leaf ≈ 2.2–3.5 m, car roof ≈ 1.5 m, window
opening width ≈ 1.2 m (the most stable absolute in the Daly data, n = 16,
1.04–1.30 m). Photographs are perspective views from the pavement, so any figure I
read off one is **±15–25 %** and flagged as such. Where a printed dimension or a
scale bar exists (Daly 1864; *Moniteur* plates 1866/1879/1881/1885/1891), I used
that instead.

**Confidence tags.** **H** means several independent sources agree, or a printed
figure exists. **M** means it is consistent across the photographs but not
measured. **L** means few cases, or it is recalled from the literature and not
checked here. Frequency tags: **typical** (most buildings of the class/date),
**varies** (common but not default), **rare**.

### 0.1 Buildings examined (31 distinct)

Dates come only from a source (a plaque, a printed plate year, or a photo date
that bounds it). Dates in *italics* are street-opening dates, which give an
earliest possible construction date, not a construction date.

| # | Building | Date evidence | Class (visual) | Commons / source |
|---|---|---|---|---|
| B1 | 84 rue de la Victoire, 9e | photo c.1900s; *Restauration quarter* | comfortable | https://commons.wikimedia.org/wiki/File:Immeuble,_84_rue_de_la_Victoire,_9%C3%A8me_arrondissement,_Paris._PH12165.jpg |
| B2 | 87 rue de la Victoire, 9e | as above | comfortable | https://commons.wikimedia.org/wiki/File:Immeuble,_87_rue_de_la_Victoire,_9%C3%A8me_arrondissement,_Paris._PH12093.jpg |
| B3 | Square d'Orléans, 80 rue Taitbout, 9e | *c.1830 ensemble* | grand | https://commons.wikimedia.org/wiki/File:Fa%C3%A7ade_sur_rue_et_square_d%27Orl%C3%A9ans,_80_rue_Taitbout,_9%C3%A8me_arrondissement,_Paris._PH10758.jpg |
| B4 | 27 rue Saint-Lazare, 9e | none (reads 1830–50) | comfortable | https://commons.wikimedia.org/wiki/File:Paris_9_-_Immeuble_27_rue_Saint-Lazare_-871.JPG |
| B5 | rue de Rivoli arcades, 1er | photo 1916; *arcades 1800s–1850s* | grand | https://commons.wikimedia.org/wiki/File:Rue_de_Rivoli,_1er_arrondissement,_Paris._PH20814.jpg |
| B6 | 17–19 rue Saint-Merri, 4e | photo 1913 | modest | https://commons.wikimedia.org/wiki/File:Fa%C3%A7ade_des_immeubles_17_et_19_rue_St_Merri,_4%C3%A8me_arrondissement,_Paris._PH34672.jpg |
| B7 | 58–60 rue de Bretagne, 3e | photo c.1906; pre-1820 | modest | https://commons.wikimedia.org/wiki/File:Rue_de_Bretagne,_n%C2%B058-60,_3%C3%A8me_arrondissement,_Paris._PH12399.jpg |
| B8 | Boulevard Malesherbes corner (Marville) | photo 1853–70 | comfortable | https://commons.wikimedia.org/wiki/File:Charles_Marville,_Boulevard_Malesherbes,_du_Boulevard_de_Courcelles,_ca._1853%E2%80%9370.jpg |
| B9 | Boulevard de Sébastopol corner, "A Pygmalion" (Marville) | photo 1853–70 | comfortable | https://commons.wikimedia.org/wiki/File:Charles_Marville,_Boulevard_S%C3%A9bastopol,_ca._1853%E2%80%9370.jpg |
| B10 | Rue de Turbigo acute corner (Marville) | photo 1853–70 | comfortable | https://commons.wikimedia.org/wiki/File:Charles_Marville,_Rue_de_Turbigo,_ca._1853%E2%80%9370.jpg |
| B11 | 16 avenue Victoria, 1er | **plaque "A. Huguet architecte 1860"** | comfortable | https://commons.wikimedia.org/wiki/File:Paris_1er_16_Avenue_Victoria_370.JPG |
| B12 | 133 boulevard Haussmann, 8e | **plaque 1868** | grand | https://commons.wikimedia.org/wiki/File:133_Boulevard_Haussmann,_Paris_(01).jpg |
| B13 | 84 boulevard Malesherbes, 8e | none; *bd 1861–63* | comfortable | https://commons.wikimedia.org/wiki/File:Immeuble,_84_boulevard_Malesherbes,_Paris_2012.jpg |
| B14 | 12 rue Halévy / place de l'Opéra, 9e | none; *Opéra "élévation type" 1860s* | grand | https://commons.wikimedia.org/wiki/File:Rue_Halevy,_12.jpg |
| B15 | 1–3 place Saint-Michel, 5e/6e | none; *place c.1860* | grand | https://commons.wikimedia.org/wiki/File:2018_1-3_Place_Saint-Michel.jpg |
| B16 | 53 rue Blanche, 9e | none | comfortable | https://commons.wikimedia.org/wiki/File:53_rue_Blanche_P1050933.JPG |
| B17 | 2 boulevard Voltaire, 11e | none; *bd 1857–62* | ordinary | https://commons.wikimedia.org/wiki/File:2_boulevard_Voltaire_%C3%A0_Paris_le_7_ao%C3%BBt_2016.jpg |
| B18 | 19 rue Auber, 9e | none; *street 1860s* | grand | https://commons.wikimedia.org/wiki/File:19_rue_Auber,_Paris_29_April_2017.jpg |
| B19 | 164 rue du Faubourg-Saint-Honoré, 8e | none | comfortable | https://commons.wikimedia.org/wiki/File:164_rue_du_Faubourg-Saint-Honor%C3%A9.jpg |
| B20 | 55 rue de Châteaudun, 9e | none; *street 1860s* | grand | https://commons.wikimedia.org/wiki/File:55_Chateaudun.jpg |
| B21 | 38 avenue de l'Opéra, 1er/2e | none; *avenue built up 1870s* | grand | https://commons.wikimedia.org/wiki/File:Paris_Avenue_de_l%27Op%C3%A9ra_no_038.jpg |
| B22 | 31 rue du Sommerard, 5e (pan coupé) | none | comfortable | https://commons.wikimedia.org/wiki/File:31_rue_Du_Sommerard.JPG |
| B23 | 16 rue Berthollet, 5e | none | comfortable/ordinary | https://commons.wikimedia.org/wiki/File:Rue_Berthollet_16.jpg |
| B24 | 16 rue Étienne-Marcel, 2e | none; *street cut 1880s* | comfortable | https://commons.wikimedia.org/wiki/File:16_rue_Etienne-Marcel.jpg |
| B25 | 105–107 rue de Rennes, 6e | none; *southern rue de Rennes post-1870* | grand | https://commons.wikimedia.org/wiki/File:Immeuble_haussmannien,_105_%26_107,_rue_de_Rennes_(48098368467).jpg |
| B26 | 56 bd Saint-Michel / rue Monsieur-le-Prince, 6e | none | comfortable | https://commons.wikimedia.org/wiki/File:Paris_75006_rue_Monsieur-le-Prince_-_Bd_Saint-Michel_no_56_Banque_Populaire_20170416.jpg |
| B27 | rue d'Alger, 1er (attic, comble) | none | ordinary | https://commons.wikimedia.org/wiki/File:Windows,_rue_d%27Alger,_Paris_14_October_2010.jpg |
| B28 | 31 rue de Fleurus, 6e (Girault) | **c.1896** | grand | https://commons.wikimedia.org/wiki/File:Album_Immeuble_avenue_Henri_Martin,_Paris._Ch._Girault_architecte,_PPPH00667(11).jpg |
| B29 | 1 rue Le Peletier, 9e (Morin-Goustiaux) | **1899** | grand | https://commons.wikimedia.org/wiki/File:Immeuble_1,_rue_Le_Peletier,_%C3%A9lev%C3%A9_en_1899_par_Georges_Morin-Goustiaux,_architecte,_PH82998.jpg |
| B30 | 130 rue Réaumur, 2e | none; *street 1895–1900* | grand (commercial) | https://commons.wikimedia.org/wiki/File:Paris_-_Immeuble_130_rue_R%C3%A9aumur_-959.jpg |
| B31 | boulevard row at the Théâtre du Vaudeville | 1869–80s (photo) | mixed | operator-supplied, unrecorded host |

**Measured / dated drawings** (scale bar or printed dimensions, read for numbers):
Daly 1864 (17 buildings in `daly_measurements.json`, plus plates 01, 42 and 52
looked at directly); *Moniteur* bd Sébastopol 72 (printed 17.55 / 4.87 / 16.40 m);
bd Haussmann, Sédille, **1866** (printed width 18.55 m); avenue de l'Opéra,
Destailleur, **1879**; rue de Rennes, Boussard, **1881**; 21 bd Saint-Germain,
Boussard, **1885**; avenue de Friedland, Hubaine, **1891**; avenue Duquesne,
Vigouroux (petits appartements, undated). Plate years are publication years.

### 0.2 Counting convention

Floors are counted the French way: **RDC** (rez-de-chaussée), then **entresol** if
there is one (it gets no number), then **1er, 2e, …** étages, then **comble**.
"Étage noble" means the tallest, most dressed étage. That is usually the 1er
counted from above the entresol, which the photograph literature often calls the
"2nd floor". To avoid that ambiguity I say **"noble"** and **"attic étage"** (the
top square storey standing above the main cornice).

### 0.3 Known biases of what I looked at

- It is weighted toward the 9e/1er/8e and grand boulevards. The faubourgs and
  outer arrondissements are thin.
- Very few construction dates. Most period calls below rest on street-opening
  dates and on style. Where a rule depends on date, I name the dated anchor.
- Daly and the *Moniteur* published exemplars, which biases them upward in quality.
- Restauration and Louis-Philippe evidence is mostly from Nouvelle-Athènes
  enclaves (B1–B4), which were upmarket for their time.

---

## 1. Height envelope: street width and cornice

**R1.1 (H, typical).** A building's cornice height is set by the regulation band of
the street it fronts, not by its class. In Daly's 1864 set, Première and Deuxième
cornices both crowd 19.0–20.0 m (6 of 10 buildings), and only Troisième drops
(15.6–15.9 m). A generator must take street width as a primary input and class as
a secondary one.

**R1.2 (H for the wide band; M for the rest). The regulation tables** (heights to the
top of the cornice / eaves above the pavement):

| street width | 1783–84 | 1859 (27 July) | 1884 (23 July) |
|---|---|---|---|
| < 7.80 m | 36 pieds ≈ 11.70 m | 11.70 m | 12.00 m (L) |
| 7.80–9.74 m | 45 pieds ≈ 14.62 m | 14.62 m | 15.00 m (L) |
| 9.75–<20 m | 54 pieds ≈ 17.54 m | 17.55 m | 18.00 m (L) for 9.75–<12 m; 18–20 m for 12–<20 m (L) |
| ≥ 20 m | 17.54 m | **20.00 m** | **20.00 m** |

The 1783 and 1859 figures come from the reference register and from the printed
17.55 m at bd Sébastopol 72. The 1884 intermediate bands are recalled from the
literature and **not checked here**, so treat them as L.

**R1.3 (H). Two cornice clusters exist in the 1850s–60s, and they are datable.**
A ~17.5 m cluster (bd Sébastopol 1: 17.55; 2–4: 17.52; no. 72: printed 17.55)
and a 19.5–20 m cluster (Sébastopol 63: 19.72; 77: 19.48; 120: 19.98; Mathurins
39: 19.82; St-Germain 6: 19.05). Sébastopol is ~30 m wide, so the 17.55 m houses
used the old 54-pied limit, not the 1859 one. **A 30 m boulevard can legitimately
carry 17.5 m or 20 m cornices side by side, depending on whether the design
predates mid-1859.** The *visible* consequence is that 17.5 m houses put more
accommodation in the roof: Sébastopol 1 and 2–4 have tall bell combles of
6.8–7.0 m with two habitable levels, against 2.7–3.5 m elsewhere.

**R1.4 (H, typical). Cornice heights are pressed against the ceiling.** Builders
take the whole allowance: Daly's cornices sit within 0–1 m of the legal maximum
in 13 of 16 cases. The exception is rue de Rivoli 88 at 14.78 m: a deliberate
tall-storey type behind an attic balustrade with no mansard.

**R1.5 (M). Restauration / Louis-Philippe (1820–48) work to the same 1783 table**,
so a 9.75 m+ street gets ~17.5 m. Photos B1, B2 and B4 show 5–6 storeys of near-equal
height inside it (RDC + 4–5 étages), with **many thin storeys rather than a
pronounced noble floor**.

**R1.6 (M). Post-1884 the cornice ceiling stays at 20 m on wide streets, but the
storey count goes up by one.** On the dated 1885 plate (21 bd St-Germain) I count
RDC + entresol + **five** square étages, the top two behind balustrades, plus a low
comble. Daly's 1864 houses have RDC + entresol + **four**. The 1879 and 1881 plates
still have four. The same architect (Boussard) uses four in 1881 and five in 1885.
How that fits is not settled here: storeys are squeezed (the 1884 minimum storey
height was ~2.60–2.80 m, L), or an étage moves up inside the new comble arc.
Either way, **expect +1 visible storey after 1884 on wide streets.**

**R1.7 (H). Comble envelope.** Before 1884 (1783 and 1859 rules) the comble sits
under a 45° line rising from the cornice. From 1884 it sits under a circular arc,
and 20 m + 8.50 m comble gives a 28.50 m ceiling on ≥20 m streets (register
figure). Measured comble heights in 1864 run 2.7–7.0 m, median ~3.3 m (n = 15),
and the printed figure at Sébastopol 72 is 4.87 m. **Comble height is a type
choice (one or two habitable levels), not a proportion of the facade.** Do not
derive it from facade height.

**R1.8 (H, typical). Block alignment.** Within a block, the cornice, the two main
balcony lines and the floor lines match house to house within ~0.05–0.12 m (Daly's
Beaumarchais triple; photos of the avenue de l'Opéra and bd Sébastopol rows). **Bay
count and bay width do not match**: Beaumarchais has 3/4/3 bays on three near-equal
lots. The 1855 circulaire is the cause on the percées. **Varies:** on streets built
up piecemeal, or pre-1855 (B31 Vaudeville row, B6, B7), neighbour cornices differ
by a whole storey or more.

---

## 2. Frontage and bays

**R2.1 (H). Frontage** party wall to party wall: 8.5–20 m. Typical **12–18 m**
(Daly median 15.6 m Deuxième; 17.1 m Première; 8.6–12.3 m Troisième). Plates:
Rennes 1881 ≈ 10 m (scale bar), Sédille 1866 18.55 m (printed), Sébastopol 72
16.40 m (printed), St-Germain 21 (1885) ≈ 23 m (scale bar), Opéra (1879) ≈ 27 m
(scale bar). **Rare:** 25 m and over, on major avenues and in grand corner
ensembles (B14, B20, B17 run to 10–14 bays along one street).

**R2.2 (H). Bay pitch** (axis to axis): 2.1–3.7 m, median **~2.8 m**, with no class
ladder (Daly: Première 2.81, Deuxième 2.85, Troisième 2.54). The extremes are
Champs-Élysées 119 at 3.71 m (4 bays on 14.9 m) and rue du Conservatoire 9 at
2.09 m. Photos agree: ordinary facades read 2.4–3.0 m. Restauration facades
(B1, B2, B4) read tighter, ~2.2–2.6 m, with slender piers (M).

**R2.3 (H). Bay count is not a function of width.** Frontages of 14.2–15.1 m carry
4, 5, 6 or 7 axes in Daly. Use a distribution:

| frontage | typical axes | also seen |
|---|---|---|
| 8–10 m | 3 | 4 |
| 10–13 m | 4–5 | 3 (with a doubled centre bay, Rennes 1881) |
| 13–17 m | 5–6 | 4, 7 |
| 17–20 m | 6–7 | 5 (1866 Haussmann: 5 axes on 18.55 m!) |
| 20 m+ | 8–11 | — |

**R2.4 (M, typical). Symmetry.** Upper-floor axes are symmetric about the centre
line in nearly every facade looked at, including even-count ones. Three
symmetric spacings occur:
- (a) **even trumeaux.** Typical: Daly plates, B16, B17, Duquesne.
- (b) **grouped:** a 2-1-2 or 1-3-1 rhythm with a wider central or end pier
  (Longchamps 2-1-2; 1879 Opéra with a tight central three; Friedland 1891
  central triplet; B23 paired windows 2-2-2). Varies, and is more common after 1870.
- (c) **a doubled centre bay** (two windows under one surround) on narrow
  frontages (Rennes 1881). Rare.

**R2.5 (H). Window-to-pier ratio.** On the glazed opening (not the surround),
pier/window is 0.9–1.7 and typically **~1.2** (Daly scan: 0.93, 1.05, 1.21, 1.38,
1.69). So piers are about as wide as windows, never much narrower.

**R2.6 (M, typical). End bays.** The outermost bays are often a little narrower or
framed differently: rusticated chaînes d'angle, pilaster strips, medallion bays
(Rivoli 88; B18 and B21 have rusticated pier strips at the party walls). **Rare:**
colossal pilasters on the end bays only, spanning 2–3 étages (Duquesne,
St-Germain 21, Rennes 1881).

**R2.7 (H). The entrance sits on the central axis** when the axis count is odd
(1866 Sédille, Sébastopol 72, Rennes 1881, B16, B18). With an even count, the
**RDC ignores the upper axes**: shops and door are laid out on their own grid
(Duquesne: door on the centre line under a pier; 1879 Opéra: door off-centre in
the shop row). Shopfront divisions do not have to line up with the windows above
(typical on commercial boulevards).

---

## 3. The storey stack

Heights are floor-to-floor, from Daly 1864 unless noted (H for Deuxième, n = 10;
the other classes are thin, see the limits in `daly_measurements.json`).

**R3.1. The canonical Second Empire stack (1853–c.1880) on a commercial street.**
From the bottom up:

1. **RDC (shop storey):** 3.4–4.9 m, median **3.95 m**. Class-independent.
2. **Entresol:** 2.4–3.1 m, median **2.98 m**, and ~0.78 × RDC. Present in 9 of 10
   Deuxième buildings and in **0 of 4 Première and 0 of 2 Troisième**.
3. **Noble étage:** Deuxième 3.2–4.4 m, median **3.83 m**; Première ~4.2 m;
   Troisième ~3.0 m. This is the clearest class ladder.
4. **Two (sometimes three) letting étages:** ~3.0–3.2 m, falling.
5. **Attic étage above the main cornice** (the "5e"): ~2.7–3.0 m, wall height
   down to ~2.2 m.
6. **Comble:** 2.7–3.5 m with one level; 6.8–7.0 m with two.

Total to the cornice: 17.5–20 m (see R1).

**R3.2 (H). The entresol is a class marker, not a height.** Première hides the same
"compressed level" inside a low dressed 1er étage of 3.2–3.6 m. Troisième has
neither an entresol nor a true noble floor. Visually the Deuxième entresol reads
as a band of short, near-square windows (aspect ~1.3–1.8) inside the rusticated
base, often behind small iron garde-corps (B13, B19, Sédille 1866, Sébastopol 72,
Opéra 1879).

**R3.3 (H). Taper is measured from the noble floor upward, and it varies.** In
Deuxième the geometric-mean step ratio is 0.80–0.99, median **0.91**. Two
buildings barely taper at all (Sébastopol 120: 3.20 / 3.20 / 3.20 / 3.13); one
tapers hard (Mathurins 39: 4.15 → 3.70 → 3.15 → 2.32). Sample a distribution, not
a constant. **Do not** compute taper from RDC→1er: in Deuxième the 1er is often
the entresol, and the ratio inverts.

**R3.4 (M). The noble floor's window is the tallest.** Its opening is 2.0–3.2 m
tall (Deuxième median 2.24 m, aspect ~2.0; Première ~2.9 m, aspect ~2.5). From
there window *height* drops floor by floor while width stays at ~1.1–1.3 m. In
photos the top square étage's windows read about 60–75 % of the noble height (M,
±20 %).

**R3.5 (M). Restauration stack (1820–48).** RDC 3.5–4.5 m, often an arcade
(B4, B5) or a shop with an applied wooden devanture (B1, B2). Then **4–5 near-equal
étages of ~2.8–3.1 m** with weak hierarchy. A low entresol appears inside
arcades (B4, B5: entresol windows in the arch lunettes). The top floor is often
just a low storey under a shallow roof, with only a small comble or a row of small
dormers (B1, B2, B5).

**R3.6 (M). Early Third Republic stack (1870–84).** Same as R3.1, but it is more
common to stretch the shop zone into a **single double-height glazed opening
covering RDC + entresol**: iron-framed glazing or an arch (B24, B19, Rennes 1881
partly). The 1879 and 1881 plates are still R3.1 exactly.

**R3.7 (M). Post-1884 stack (1884–1902).** RDC + entresol + 4 square étages + attic
étage + comble, i.e. **one more square floor** (R1.6). Or, on residential avenues,
RDC + 1er in bossage + noble + 2 + attic + comble (Friedland 1891). Combles become
taller and busier (R7.6).

**R3.8 (H). The residential-avenue variant (no shops), any date from 1860.** The RDC
is raised 0.5–1.0 m over basement grilles (soupiraux), its windows are round-headed
or segmental, it is often paired with an entresol or low 1er in the same bossage,
and a **porte cochère arch swallows both** (B13, B12, Sédille 1866, Friedland 1891).
This is typical on bd Malesherbes, bd Haussmann west, avenue de Friedland, and
the 16e/17e.

---

## 4. Balconies

**R4.1 (H, typical 1853–c.1880). The two-filant rule.** A **continuous balcon filant
at the noble floor** and a **second at the attic étage**, resting on the main
cornice. Every other window gets an individual garde-corps (balconnet). This
holds in nearly every Second Empire photo (B8, B9, B13–B17, B21) and on all the
1866–1885 plates. The noble filant is carried on **stone consoles** set over the
entresol cornice. The attic filant uses the main cornice as its deck.

**R4.2 (M, varies). The noble filant may cover only the central bays** (the central
3 of 5 at Sédille 1866, Sébastopol 72, B16), with individual balconies on the
outer bays. On the widest and richest facades it is full width and wraps the
corners (B14, B20).

**R4.3 (H). Dimensions.** Projection **~0.60 m** (printed 0.600 m Rivoli 88 and
0.590 m Sébastopol 120). The 1823 maximum is 0.80 m, and no balcony may be
below 6 m. Rail height **~1.0 m** (0.87–1.07 m, n = 4). The lowest projecting deck
sits at **6.55–7.9 m** (Deuxième; it is RDC + entresol). In photos, filant rails
read about a person's height above the deck, and their decks about 2.3 m below the
windows' lintels (M).

**R4.4 (M). Balconies multiply after c.1870.** Between the two filants, the letting
étages gain **grouped balconies over 2–3 bays on paired consoles**, alternating
with single balconnets: B24, B25, B20, B19, B23, Opéra 1879 (central three). By
the 1880s some facades have a projecting balcony at every level (B24, B26 corner).
Before 1860 the letting floors carry only balconnets.

**R4.5 (M). Restauration balconies (1820–48)** are individual, shallow, light
wrought-iron balconnets at nearly every window, with lozenge, palmette or scroll
patterns. A thin filant may run at the 1er or at the top (B2, B3, B5 Rivoli). Rails
are thin bar-and-circle designs (B27), not the dense cast scrollwork of the 1860s.

**R4.6 (M). Ironwork by date.** 1820–48: wrought, sparse, geometric (lozenges,
crosses, circles). 1853–80: **cast iron (fonte), dense symmetric scroll and
rinceau panels**, repeated identically along the rail with posts at bay
divisions (B13–B21). 1885–1902: **stone balustrades** at the noble and attic
levels on grand houses (St-Germain 21, 1885; Friedland, 1891; B22 has stone
balustered balconnets at the noble floor), with iron kept at the middle floors.
Late 1890s: asymmetric, naturalistic iron (B28–B30).

**R4.7 (H). Troisième and modest houses:** few or no projecting balconies. Rue de
Longchamps (Daly) has **none**, only flush garde-corps. Modest photos (B6, B7)
show only small balconnets on a couple of floors. A filant at the attic level is
the most likely single balcony on an ordinary house (B17, B23, B27, Duquesne).

---

## 5. Windows and surrounds

**R5.1 (H). Every window on the étages is a French window (croisée)** reaching the
floor, so every one has a garde-corps or a balcony. Width ~1.1–1.3 m on all floors
and in all classes. Persiennes (folding louvred shutters) are standard on
ordinary and Restauration fronts (B1, B2, B23, B27) and absent from many grand
ashlar fronts (or folded into the reveal).

**R5.2 (M, typical). The surround hierarchy decreases upward.** This is the single
most legible rule in the photographs:

| floor | typical surround (Second Empire, comfortable/grand) |
|---|---|
| RDC | arched or in bossage; shopfronts |
| entresol | plain, or no surround inside the bossage; sometimes segmental |
| **noble** | moulded chambranle + frieze + **cornice on consoles**, often **pediment** (triangular, segmental, or alternating) |
| 2nd étage | chambranle + flat cornice (hood), sometimes small consoles |
| 3rd étage | chambranle only, possibly ears/keystone |
| attic étage | plain chambranle or none |
| dormer | its own frame (R7.3) |

Seen in B13–B22 and on the 1866, 1879 and 1881 plates. **Varies:** on some facades
the richest surround is one floor up (B22: segmental heads on the 1er and pediments
plus balustrades on the next). That is still a single peak with a decrease above it.

**R5.3 (M). Alternating triangular and segmental pediments** on the noble floor are
a grand-street marker (B21 avenue de l'Opéra, B18). Ordinary houses have flat
cornices on consoles, or nothing (B17, B23).

**R5.4 (M). Sculpture by date.** 1853–65: restrained, with small carved panels,
consoles and the odd keystone (B11, 1860; B13; Sébastopol 72). 1865–85: **mascarons
on keystones and console heads become standard**. Caryatids or atlantes appear on
grand houses (bd Magenta 56, dated 1866–67; B25; B18 mascaron over the arch; B24
mascarons at every console of the attic filant). 1885–1902: deeper relief,
cartouches, sculpted lucarnes, and naturalistic ornament by the late 1890s.

**R5.5 (M). Restauration windows** have thin, shallow or no surrounds: a plain
plaster band or a narrow moulding, little or no cornice on consoles, round-headed
openings at the RDC or 1er in grander houses (B4). A **plain bandeau string course
at every floor** is typical (B1, B2, B4). The 1850s+ facade drops most of those and
keeps only the strong horizontals (R6.2).

**R5.6 (L). Bow windows and oriels** only after the 1882 decree (≤ 0.40 m projection,
masonry from 1893). Absent from every dated pre-1882 source here. Present on B28
(1896) and B29 (1899). **Before 1882, the facade plane is flat** apart from
balconies, cornices and consoles.

---

## 6. Horizontals, the socle and the cornice

**R6.1 (H, typical 1853–1902). The socle is RDC + entresol** (or RDC + low 1er), in
**bossage continu**: deep horizontal channel joints (refends) with no vertical
joints showing, running up to the noble-floor balcony consoles (B13, B19, B18,
1866/1879/1881/1885/1891 plates). Above it the wall is smooth ashlar with fine
joints, or very light refends in ordinary houses (B17, B23). **Varies:** bossage
continues up the end-bay piers as chaînes (B18, B21). **Rare:** vermiculated or
diamond-point blocks (B12 door jambs, 1868).

**R6.2 (M). Three strong horizontals:**
1. the **entresol cornice / noble balcony shelf**, the deepest after the crown;
2. a **string course** under the noble's upper neighbour, or under the top square
   floor (varies; B23, B16);
3. the **main cornice** under the attic étage, with modillions or dentils and
   0.35–0.70 m deep (Daly, n = 8; M).

Then a light cornice or gutter at the top of the attic étage, under the comble.
Photos show modillion rows clearly on grand houses (B18, B21, B14) and plain
mouldings on ordinary ones.

**R6.3 (M). Restauration horizontals** are thin and numerous: one bandeau per floor
and a light crown cornice. The socle is usually plaster with incised refends (B3,
B4) or none at all (B1, B2).

---

## 7. The comble

**R7.1 (H, typical 1853–84). Straight-sided mansard inside the 45° envelope.** Zinc
(standing seam) on the slope, often slate on the steep brisis of better houses,
and a near-flat zinc terrasson (B13–B17, B27; all pre-1884 plates). The visible
slope from the street is **45–70°**. Ordinary houses have a single ~45–60° plane
(B17, B27). Better houses have a steeper brisis plus a terrasson (Sédille 1866,
Rennes 1881). Height 2.7–3.5 m with one level of chambres de bonne.

**R7.2 (H). Dormers stand on the window axes below.** Typical: one per axis (B17,
B21, B24, Sébastopol 72, Opéra 1879). **Varies:** fewer than the axes (every other
axis, e.g. Duquesne 4 on 6, B16 3 on 7), always symmetric about the centre. Dormers
sit just behind the attic filant and the gutter. Their sill is ~0.5–1 m above the
gutter.

**R7.3 (M). Dormer forms by register:**
- **pedimented lucarne** (triangular or segmental) in zinc or stone: grand and
  comfortable, 1855–84 (B14, B16, B21, B24, Sébastopol 72);
- **oeil-de-boeuf** (round or oval in a scrolled zinc frame): grand, 1860s–80s
  (Opéra 1879, B15, Sédille 1866 round-headed);
- **plain box (jacobine) with a flat or slightly hipped top**: ordinary and
  modest (B27, B23);
- **chien-assis / capucine (hipped)**: modest (rue Danielle-Casanova, https://commons.wikimedia.org/wiki/File:Paris_Rooftops_of_Rue_Danielle_Casanova.jpg).

Size ≈ 0.9–1.1 m wide × 1.4–1.8 m glazed (M, read against the 1.2 m windows below).

**R7.4 (M). Two rows of openings in the comble** when it holds two levels: a lower
row of dormers plus an upper row of small tabatières or skylights (Rennes 1881;
Sébastopol 1 and 2–4 at 6.8–7.0 m comble). Typical of the 17.5 m-cornice houses
on wide streets (R1.3).

**R7.5 (H, typical). Chimney stacks (souches)** stand on the party walls,
perpendicular to the street, in tall brick or rendered slabs with terracotta pots.
They rise 1.5–3 m above the ridge and mark every lot boundary on the skyline (all
photos; every plate draws them at the party walls). Their spacing *is* the lot
rhythm of the street.

**R7.6 (M). Post-1884 combles** are taller (arc envelope) and busier: stone dormers
passing through the cornice (lucarnes passantes), a central sculpted lucarne
(Friedland 1891), brick infill, domes and tourelles at corners, iron cresting,
weathervanes (B28, B29, B30). Some 1880s houses stay plain and low (St-Germain
21, 1885: a low comble with small square dormers above a balustraded attic étage).

**R7.7 (M). Curved (bombé) combles are NOT a reliable post-1884 tell.** The rue de
Rivoli arcades (Napoleon I to the 1850s; B5) and place Saint-Michel (c.1860; B15)
both carry convex combles on pavilions and corners, and corner caps are often
domed (B26). The corpus metadata uses curvature as a post-1884 reject criterion. I
think that rejects real Second Empire work. A safer reading: **curvature on a
corner or pavilion means a prestige ensemble at any date; curvature along an
ordinary run of a street suggests post-1884.**

---

## 8. Ground floor: shops and the porte cochère

**R8.1 (H, typical on commercial streets). Shops take the RDC across the whole
width except the entrance bay.** In 1850s–60s design the shopfront fills a
masonry opening, with wooden or iron framing and the entresol above shown as
a separate band (Sébastopol 72, Beaumarchais, Opéra 1879). Signage runs on the
fascia at the top of the RDC, and often **up onto the entresol and even the noble
filant** (B9 "Nouveautés à Pygmalion" lettering on two balcony levels; B10; B31).
A generator that keeps the upper facade clean of lettering misses a very visible
1860s–1900s feature.

**R8.2 (M). Restauration and modest shopfronts** are applied wooden devantures
projecting ~0.15–0.30 m, with a fascia, panelled pilasters and folding shutters
(B1, B2, B6, B7).

**R8.3 (H). Door sizes are set by door type, not class:**
- **carriage door (porte cochère):** clear width **2.4–2.7 m** (median 2.58,
  n = 7, Première = Deuxième);
- **pedestrian door:** 1.6–1.9 m in Deuxième, ~1.36 m in Troisième;
- leaf height ~2.95–3.55 m.

The class signal is **whether the house gets a carriage door**: Première always,
Deuxième sometimes, Troisième never in Daly. Photos agree: B13's door reads ~2.3–2.6
m wide against a person (M); B17's is ~2.4–2.6 m.

**R8.4 (H). The porte cochère opening often swallows RDC + entresol.** It is a
round-arched or segmental opening of 5.0–6 m to the crown, with a glazed or grilled
fanlight (imposte) over the leaves (Mathurins 39: 5.00; Sébastopol 2–4: 5.01;
B13, B16, B12, B18, Sédille 1866, Friedland 1891). A keystone, mascaron or
cartouche at the crown is typical from the mid-1860s. **Varies:** a square-headed
door under its own cornice, stopping at the RDC (Sébastopol 72, Duquesne,
Conservatoire 9 at 2.72 m).

**R8.5 (M). Arcades.** Round-arched RDC + entresol bays in bossage are used across
the whole width on prestige ensembles (B5 Rivoli; B14, B15, B29) and on
residential avenues (R3.8). They are rare on ordinary streets.

---

## 9. Materials and colour

**R9.1 (H, typical 1850s–1902).** Load-bearing **pierre de taille** (Paris
limestone, warm cream to grey) on the street front of every boulevard house in
the photo set. Ordinary side-street houses use ashlar at the RDC/socle and either
ashlar or plastered rubble above (B23 reads ashlar throughout; B27 plaster).

**R9.2 (M, typical 1820–48).** **Plastered (plâtre) facades** over rubble or timber,
painted pale. Ornament is in plaster, refends are incised, and stone appears only
at the plinth or in the grandest work (B1–B4).

**R9.3 (H).** Roofs are **zinc** (grey-blue) with slate on brisis. Ironwork is painted
black or dark green. Shutters are painted grey, cream or white.

**R9.4 (M, post-1880s).** Polychromy returns: brick in combles and dormers, ceramic
and enamelled lettering, and later brick-and-stone fronts (B28; Castel Béranger and
others in the corpus).

---

## 10. Corners

**R10.1 (H). Horizontal lines wrap the corner unbroken** at the same heights on both
streets: cornice, filants and string courses (B14, B9, B8, B26).

**R10.2 (M). Corner forms, from most to least common in this set:**
- **pan coupé** (chamfer) of one bay (B22) or two (B26);
- **rotonde** (a continuous curve, B14, B9, B8);
- **acute-angle prow** with sculpture or a single narrow bay (B10).

The chamfer width is roughly one or two bays (2.5–6 m, M).

**R10.3 (M). The corner is the accent.** It gets balconies on more floors than the
flanks (B26: projecting balconies on the chamfer at three levels where the flanks
have balconnets), a raised or domed roof cap or a corner dome (B15, B26, B29,
B30), and sometimes a corner shop or café entrance on the chamfer at the RDC.
After 1884 the corner becomes a tourelle or rotonde rising above the cornice (B29,
B30, B28).

**R10.4 (M). Axes on the two street fronts are independent.** Each front is
composed symmetric or regular on its own, and the corner bays close both.

---

## 11. What varies, and with what

**R11.1. Class** (Daly ladder; H for the ordering, L for absolute values).

| feature | Troisième / modest | Deuxième / comfortable | Première / grand |
|---|---|---|---|
| entresol | none | yes (typical) | absorbed into a dressed low 1er |
| carriage door | no | sometimes | yes |
| noble floor height | ~3.0 m | ~3.8 m | ~4.2 m |
| noble window aspect | ~1.95 | ~2.0 | ~2.5 |
| projecting balconies | few or none | 2 filants | 2 filants + more, stone balustrades |
| surrounds | plain | consoles and cornices | pediments, sculpture |
| frontage | 8–12 m | 12–20 m | 15–19 m |

**Constant across classes:** window width, door width within a type, balcony
projection, rail height, RDC height, bay pitch.

**R11.2. Date** (M). Signal features by period:
- **1820–48:** plaster, persiennes, many equal floors, a bandeau per floor, light
  balconnets, small comble.
- **1853–70:** ashlar, bossage socle, two filants, a peaked surround hierarchy, a
  straight mansard with dormers on axes, restrained carving.
- **1870–84:** mascarons and caryatids, grouped balconies on the middle floors, a
  double-height glazed RDC + entresol, colossal pilasters on accent bays.
- **1884–1902:** +1 storey, taller and busier combles, stone balustrades, oriels
  (after 1882), corner domes and tourelles, lucarnes passantes, polychromy, Art
  Nouveau after ~1895.

**R11.3. Street** (M).
- **Boulevard:** 20 m cornice (17.5 m if pre-1859), shops + entresol, two filants,
  long uniform blocks.
- **Residential avenue:** no shops, raised RDC and porte cochère, bossage over RDC +
  1er, richer upper floors.
- **Ordinary rue (9.75–20 m):** 17.5 m, 4–6 bays, one attic filant, plainer.
- **Narrow old street (< 9.75 m):** 11.7–14.6 m, often an older house refronted,
  irregular storeys, no cornice line shared with neighbours (B6, B7).

---

## 12. What a generator would most likely get wrong

1. **Height from class or from width.** Cornice height comes from the street band
   and design date (R1.1, R1.3). Two 30 m boulevard houses one block apart can sit
   at 17.5 m and 20 m.
2. **A uniform taper from the ground up.** RDC → entresol → noble is a
   *drop-then-jump*. Taper only starts above the noble (R3.3). Zero-taper facades
   exist.
3. **Scaling the window with the building.** Window and door widths are absolutes.
   Class lives in window *height*, surround richness and door *type* (R5.1, R8.3).
4. **Balconies at every floor, or nowhere.** Second Empire means two filants plus
   balconnets on all other croisées (R4.1). "Every floor" is a post-1870 or corner
   trait.
5. **A missing garde-corps.** French windows reach the floor, so every étage
   window needs a rail (R5.1).
6. **Dormers off-axis, or counted independently.** Dormers sit on axes, symmetric,
   one per axis or every other axis (R7.2).
7. **Comble height as a fraction of facade height.** It is one level (~3 m) or two
   (~7 m), by type (R1.7, R7.4).
8. **Even bay counts with a door on an axis.** The RDC has its own grid when the
   axis count is even (R2.7).
9. **Party-wall chimneys left out.** The souches carry the lot rhythm on the
   skyline (R7.5).
10. **Neighbour bay alignment enforced.** Block alignment is horizontal only.
    Neighbours share lines and **not** axes (R1.8).
11. **Bossage on every storey, or none.** It belongs to the socle (RDC + entresol)
    plus optional end-bay chaînes (R6.1).
12. **The noble floor at "the 2nd floor" by index.** Locate it as the first étage
    above the compressed level (R3.1, R3.2).
13. **Curved comble = post-1884.** False for corner pavilions and place ensembles
    (R7.7).
14. **Oriels or bow windows before 1882.** The facade stays flat (R5.6).
15. **Clean upper facades on commercial streets.** 1860s–1900s photos show
    lettering on the entresol and the noble filant (R8.1).
16. **Over-regular streets.** Real rows mix pre-Haussmann survivors of other
    heights (B31, B6, B7). Even on the percées, bay counts differ lot to lot.

---

## 13. Gaps

These are things this pass could not settle, with what would settle each.

- **Construction dates for the photos.** Almost none are known. The date rules
  lean on six dated plates (1864, 1866, 1879, 1881, 1885, 1891) and three
  plaques. A run of dated permit-file elevations for 1870–1900 would settle R1.6 and
  R11.2.
- **The 1884 intermediate height bands and storey caps** (R1.2) are recalled, not
  checked. Read the decree's text.
- **Comble pitch** cannot be measured from street photos (foreshortening). A dated
  section plate is needed.
- **Modest buildings** of 1853–1902 are thin (one Troisième pair in Daly, B6/B7
  are older). Faubourg photos from the 11e, 12e, 18e and 20e would test R4.7 and R11.3.
- **Live Commons sampling** was blocked in this environment. Allowing
  `commons.wikimedia.org` and `upload.wikimedia.org` would let a later pass draw
  fresh, non-curated samples and check the corpus's selection bias.
