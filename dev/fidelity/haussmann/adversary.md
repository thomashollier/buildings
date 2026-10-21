# Paris immeuble rule file: adversarial fidelity review

Model under test: `src/buildings/typologies/paris/haussmann.toml` (loaded by `paris/rules.py`; format in `dev/RULES.md`), rendered in `docs/strips/haussmann.png` (1835 9 m street modest; 1865 20 m boulevard comfortable shop; 1868 30 m avenue grand; 1875 14 m street ordinary; 1890 12 m street modest shop; 1900 24 m street grand café). For comparison I also used `docs/strips/paris_measured.png` and `dev/reference/` (the photo corpus and `daly_measurements.json`). I changed no files except this one.

## Method, and its limits

- **Photographs.** The live Wikimedia Commons API was blocked by this session's network policy: every request to `commons.wikimedia.org` was refused at the proxy. So I worked from the repository's own Commons corpus in `dev/reference/images/`, which was downloaded through the same API (`iiurlwidth=1000`). I looked at each image myself, and each is listed below with its Commons page. I examined 17 distinct buildings. Ten of them are Second Empire or early Third Republic, four are pre-Haussmann or modest, and three are post-1884.
- **Measured drawings.** César Daly's 1864 plates (16 buildings with storey ladders) come from `dev/reference/daly_measurements.json`. I did not re-read the plates. I took the figures as the corpus records them, including its own caveats: a small n, publication bias toward good buildings, and a single date (1864).
- **Regulations.** Sources were the techno-science.net summary of the Paris règlements (1783/84, 1859, 1884, 1902) and the comments in `paris/reglement.py`.
- **Scale.** Photographs carry no scale bar, so I anchored on things whose size is known:
  - a window opening of about 1.2 m (Daly's most stable absolute, 1.04-1.30 m over 16 buildings);
  - a person at 1.7 m;
  - a carriage door at about 2.6 m.

  Street-level shots shorten the upper storeys, so storey ratios come only from the near-frontal views (2 bd Voltaire, 53 rue Blanche). Metric figures from photos are ±10-15%, and ±20% for anything above the 4th floor.

Verdict counts (47 claims, split verdicts counted by their first word): **18 SUPPORTED, 19 PARTLY, 7 CONTRADICTED, 3 UNTESTABLE.** C28 is also contradicted for pre-1850 and modest buildings, and C3's 20 m boundary is untestable.

**Bottom line (fair version).** The rule file gets the big skeleton of a Second Empire boulevard immeuble right:
- the legal envelope by street width and decree;
- a commercial base of shop plus entresol at about 6.8 m;
- a noble floor with a balcon filant;
- tapering letting floors and a second balcon filant at the top;
- a comble with dormers;
- window width about 0.45 of the bay;
- a carriage door of about 2.6 m.

Its absolute numbers for the commercial base, entresol, letting floors, bay and door sit inside Daly's measured ranges.

It fails in three places:
- **It ignores class and date wherever the evidence shows them mattering most.** Noble-floor height is class-blind, but it is the clearest class ladder in Daly. The same stone, balcons filants and moulded surrounds are given to an 1835 modest house as to an 1868 grand one. The `corner` input is never read.
- **It misreads two highly visible conventions.** Letting-floor windows stand on a blank allège, while nearly every photographed building has porte-fenêtres with garde-corps on every floor. The entrance is forced onto the middle axis, while most photographed entrances are off-centre.
- **Its pre-1884 roof breaks the 45° gabarit it cites.** A 72° face rising 3.2 m is only 1.04 m deep, where the gabarit needs 3.2 m.

---

## 1. Buildings examined

| # | Building | Date / class (corpus) | Commons page | What it shows |
|---|---|---|---|---|
| B1 | 2 boulevard Voltaire, 11e | Second Empire, ordinary/comfortable | [File:2_boulevard_Voltaire_à_Paris_le_7_août_2016.jpg](https://commons.wikimedia.org/wiki/File:2_boulevard_Voltaire_%C3%A0_Paris_le_7_ao%C3%BBt_2016.jpg) | Dead frontal, 10 bays. Shop + entresol; balcon filant at 2e and 5e. The heavy modillioned cornice is *under* the 5e balcony. Pediments over the 3e windows; garde-corps on the 4e. Pedestrian door at bay 3 of 10. 6 zinc dormers + 4 roof lights over 10 bays. 5+ chimney stacks. |
| B2 | 53 rue Blanche, 9e | comfortable | [File:53_rue_Blanche_P1050933.JPG](https://commons.wikimedia.org/wiki/File:53_rue_Blanche_P1050933.JPG) | Frontal. Round-arched porte cochère on the middle axis, rising through the entresol. Balcon filant at the 2e spans only the 4 central bays. Garde-corps on every upper window. The top balcony sits on the main cornice, with a storey above it. Steep zinc comble, 3 dormers over 7 bays, 2 large party-wall stacks. |
| B3 | Bd Malesherbes at bd de Courcelles (Marville, c.1853-70) | comfortable | [File:Charles_Marville,_Boulevard_Malesherbes,...jpg](https://commons.wikimedia.org/wiki/File:Charles_Marville,_Boulevard_Malesherbes,_du_Boulevard_de_Courcelles,_ca._1853%E2%80%9370.jpg) | Period photo. Shops + entresol, balcon filant at the 2e, oeil-de-boeuf dormers, rows of tall chimney stacks along the block. |
| B4 | Bd de Sébastopol, "Pygmalion" corner (Marville) | comfortable | [File:Charles_Marville,_Boulevard_Sébastopol,_ca._1853–70.jpg](https://commons.wikimedia.org/wiki/File:Charles_Marville,_Boulevard_S%C3%A9bastopol,_ca._1853%E2%80%9370.jpg) | Period photo. Cut corner; shop and entresol signage; balcon filant at the 2e and 5e; projecting shop devanture; stone-framed dormers; many ridge stacks. |
| B5 | 55 rue de Châteaudun, 9e | grand | [File:55_Chateaudun.jpg](https://commons.wikimedia.org/wiki/File:55_Chateaudun.jpg) | Glazed entresol. Round-arched porte cochère rising through the entresol, off-centre. Balcon filant at the 2e and 5e; individual balcons on the 3e and 4e; arched dormers one per axis. |
| B6 | 38 avenue de l'Opéra, 2e | grand (1870s-80s) | [File:Paris_Avenue_de_l'Opéra_no_038.jpg](https://commons.wikimedia.org/wiki/File:Paris_Avenue_de_l%27Op%C3%A9ra_no_038.jpg) | Entresol in the stone base. Triangular pediments over the 2e windows above the balcon filant; consoled cornice under the 5e balcony; dormers one per axis with a continuous gutter balcony; brick party-wall stacks. |
| B7 | 12 rue Halévy, 9e | grand (1860s) | [File:Rue_Halevy,_12.jpg](https://commons.wikimedia.org/wiki/File:Rue_Halevy,_12.jpg) | Corner. No entresol: round-arched openings swallow rdc + entresol height. Rusticated (refends) base. Balcon filant at the 2e and 5e. Porte cochères in the *end* bays. Dormers one per axis, plus a second row of small openings in the terrasson (pre-1884). Base about 6.8 m to the 2e deck (person = 1.7 m). |
| B8 | 17 rue Saint-Merri, 4e (Godefroy 1913) | modest | [File:Façade_des_immeubles_17_et_19_rue_St_Merri...jpg](https://commons.wikimedia.org/wiki/File:Fa%C3%A7ade_des_immeubles_17_et_19_rue_St_Merri,_4%C3%A8me_arrondissement,_Paris._PH34672.jpg) | 3 bays, plastered. Porte-fenêtres with garde-corps on *every* floor; no balcon filant; 2 dormers. |
| B9 | 19 rue Saint-Merri (same photo) | modest | same | 5 bays, rendered. Shops + entresol; round-arched passage at bay 4 of 5; thin balcony at the 1er only; 3 dormers over 5 bays. |
| B10 | 31 rue du Sommerard, 5e | comfortable | [File:31_rue_Du_Sommerard.JPG](https://commons.wikimedia.org/wiki/File:31_rue_Du_Sommerard.JPG) | Corner. Rusticated shop base, no entresol. **No balcon filant anywhere**: stone balustrades under the 2e windows. Segmental-headed windows on the 1er; alternating triangular and segmental pediments on the 2e above a low 1er. Flat-headed pedestrian door near the end. Dormers one per axis. |
| B11 | 84 rue de la Victoire, 9e (c.1820s-40s row) | comfortable | [File:Immeuble,_84_rue_de_la_Victoire...PH12165.jpg](https://commons.wikimedia.org/wiki/File:Immeuble,_84_rue_de_la_Victoire,_9%C3%A8me_arrondissement,_Paris._PH12165.jpg) | Plastered fronts. Persiennes on every window; thin garde-corps across porte-fenêtres on every floor; one balcony on consoles; wooden shop devantures. |
| B12 | 58 rue de Bretagne, 3e (c.1906) | modest | [File:Rue_de_Bretagne,_n°58-60...PH12399.jpg](https://commons.wikimedia.org/wiki/File:Rue_de_Bretagne,_n%C2%B058-60,_3%C3%A8me_arrondissement,_Paris._PH12399.jpg) | Rendered. 3 storeys + slate roof with 2 dormers; massive party-wall stack; shutters; wine-shop front. |
| B13 | 60 rue de Bretagne (same photo) | modest | same | Rendered. Irregular bays; garde-corps on porte-fenêtres; pedimented single dormer; pitched slate roof. |
| B14 | 130 rue Réaumur, 2e (c.1900) | grand commercial | [File:Paris_-_Immeuble_130_rue_Réaumur_-959.jpg](https://commons.wikimedia.org/wiki/File:Paris_-_Immeuble_130_rue_R%C3%A9aumur_-959.jpg) | Post-1884 corner tourelle with dome. Iron-framed glazed bays over 3 storeys; rusticated arcaded base; stone-pedimented dormers; dense sculpture. |
| B15 | 31 rue de Fleurus, 6e (Girault, 1896) | grand | [File:Album_Immeuble_avenue_Henri_Martin...PPPH00667(11).jpg](https://commons.wikimedia.org/wiki/File:Album_Immeuble_avenue_Henri_Martin,_Paris._Ch._Girault_architecte,_PPPH00667(11).jpg) | Bow window rising from the 1er to the comble; corner tourelle; balcon filant only at the 5e; partial balconies elsewhere. Residential ground floor with a columned porch at the end bay. Tall comble with two rows of openings. |
| B16 | 31 rue de la Chaussée-d'Antin / 71 rue de Provence (1887) | comfortable | [pss-archi FR-75056-81353](https://www.pss-archi.eu/immeubles/FR-75056-81353.html) (corpus anchor, small image) | Post-1884 rounded corner. Shops + entresol; balcon filant at the 2e, 5e and comble foot; dormers one per axis. |
| B17 | 16 rue Étienne-Marcel, 2e | comfortable (1880s) | [File:16_rue_Etienne-Marcel.jpg](https://commons.wikimedia.org/wiki/File:16_rue_Etienne-Marcel.jpg) | Shops + glazed entresol. Entrance door in the left end bay; heavy consoled entablature carrying the 2e balcon filant. **Balconies grouped over pairs of bays** on the 3e and 4e; giant Corinthian pilasters; consoled cornice under the 5e balcon filant. Stone pedimented dormers one per axis, plus a row of tabatières above. |

Daly (from `daly_measurements.json`): 4 Première, 11 Deuxième and 2 Troisième classe buildings (1864), of which 16 have measured storeys.

### Measurements I took

**B1, 2 bd Voltaire** (frontal, 1920 px wide). Scale: window opening ≈ 65 px = 1.2 m, so 0.0185 m/px.

| Quantity | Pixels | Metres |
|---|---|---|
| Bay pitch | 134 px | ≈ 2.5 m |
| Window share of bay | | 0.45-0.50 |
| Pavement to 2e balcony deck | 425 px | ≈ 7.9 m (Daly decks 6.55-7.93) |
| 2e floor-to-floor | 205 px | ≈ 3.8 m |
| 3e | 170 px | ≈ 3.1 m |
| 4e | 150 px | ≈ 2.8 m |
| Pavement to gutter | 1080 px | ≈ 20.0 m (the 1859 limit for a 30 m boulevard) |

Upper ratios are 0.83 and 0.88, but these are foreshortened and overstate the taper. Confidence: medium.

**B2, 53 rue Blanche** (shot from below; display scale 1.2 m ≈ 100 px).

| Quantity | Measurement |
|---|---|
| Noble floor | ≈ 3.4 m |
| Next two storeys | ≈ 3.0 m and 2.8 m (ratios 0.89, 0.92) |
| Bay pitch | irregular: 250 / 180 / 245 / 230 px (2.2-3.0 m). The bays either side of the door differ. |
| Window share | ≈ 0.43 |
| Porte cochère | ≈ 3.0 m to the outside of its moulding; leaves ≈ 2.5-2.6 m wide |

The porte cochère's arch crown is level with the entresol windows' heads. Confidence: low to medium.

**B7, 12 rue Halévy** (person ≈ 50 px = 1.7 m).

| Quantity | Measurement |
|---|---|
| Ground arches | ≈ 4.6 m tall × 1.9 m wide |
| Pavement to 2e balcony | ≈ 6.8 m |
| Bay pitch | ≈ 3.1 m |

Confidence: low, because the facade is oblique and the distance is unknown.

---

## 2. Claims table

"Real" below means the photographed buildings and Daly's plates, not the measured generator.

| # | Claim | Source | Verdict |
|---|---|---|---|
| C1 | The file "agrees with the measured generator on shape and differs in the second decimal" | toml:7-8; RULES.md:31-32 | **PARTLY** |
| C2 | 1783/84 cornice: 11.70 m below 7.80 m street, 14.62 m to 9.75 m, 17.55 m above | toml:23 | **SUPPORTED** |
| C3 | 1859: as 1783 to 20 m street, 20 m above | toml:24 | **SUPPORTED** (values) / **UNTESTABLE** (the exactly-20 m boundary) |
| C4 | 1884: 12 / 15 / 18 / 20 m at the same breaks | toml:25 | **SUPPORTED** (secondary source, medium confidence) |
| C5 | The regime switches at 1859 and 1884 and nothing later | toml:15, 45 | **PARTLY** (1902 missing) |
| C6 | Ambition by class 0.86 / 0.90 / 0.95 / 0.98 of the legal cornice (marked INFERRED) | toml:26-27, 47 | **PARTLY** |
| C7 | Shop ground storey 4.0 m | toml:28 | **SUPPORTED** |
| C8 | House ground storey 3.6 m | toml:29 | **PARTLY** (low) |
| C9 | Entresol 2.8 m | toml:30 | **SUPPORTED** |
| C10 | An entresol exists if and only if the ground floor is a shop or café | toml:45, 47, 63 | **PARTLY** |
| C11 | Noble floor 3.6 m at every class | toml:31, 64 | **CONTRADICTED** |
| C12 | The noble floor sits directly on the base (no low 1er étage) | toml:61-65, 134 | **PARTLY** (wrong for Première) |
| C13 | First letting floor 3.2 m | toml:32 | **SUPPORTED** (Deuxième) |
| C14 | Each letting floor is 0.95 of the one below | toml:33, 65 | **PARTLY** |
| C15 | Storey count = what fits under ambition × legal | toml:48-50 | **SUPPORTED** |
| C16 | Bay 2.0 / 2.6 / 3.2 m | toml:34, 51 | **SUPPORTED** (slightly narrow) |
| C17 | End piers 0.2 / 0.35 / 0.75 m | toml:35 | **UNTESTABLE** |
| C18 | At least 2 bays | toml:51 | **SUPPORTED** |
| C19 | Window width = 0.45 of its bay | toml:36, 150 | **SUPPORTED** (value) / **PARTLY** (mechanism) |
| C20 | Comble 3.2 m before 1884, 4.6 m after | toml:37, 53 | **SUPPORTED** (typical) / **PARTLY** |
| C21 | Roof face pitched 72° at every date | toml:53 | **CONTRADICTED** before 1884 |
| C22 | Roof is zinc | toml:53 | **PARTLY** |
| C23 | Dormers are pedimented (lower row) and segmental (upper row) | toml:53, 89 | **PARTLY** |
| C24 | One dormer over every window axis | toml:83, 85-86 | **PARTLY** |
| C25 | A second dormer row (two-storey comble) only after 1884 | toml:83, 88-89 | **CONTRADICTED** |
| C26 | Two chimney stacks, one on each party wall | toml:83, 91-92 | **PARTLY** |
| C27 | A 0.45 m entablature crowns the base | toml:72, 75 | **SUPPORTED** |
| C28 | A balcon filant fronts the noble floor and the top stone storey | toml:72, 76 | **SUPPORTED** (Second Empire boulevard) / **CONTRADICTED** (pre-1850, modest) |
| C29 | A 0.6 m modillioned cornice crowns the stone above the top storey | toml:72, 77 | **PARTLY** |
| C30 | Every wall is stone | toml:134 | **PARTLY** (contradicted pre-1850 / modest) |
| C31 | Every window, shop and ground opening is flat-headed | toml:150, 157, 164, 171 | **PARTLY** |
| C32 | Noble-floor windows are porte-fenêtres to the floor (sill 0.1 m) | toml:147, 149 | **SUPPORTED** |
| C33 | Letting-floor windows stand on a 0.85 m allège; only the top one goes to the floor | toml:147, 149 | **CONTRADICTED** |
| C34 | A garde-corps is put across a porte-fenêtre with no balcony | toml:104, 107 | **UNTESTABLE** (the rule never fires) |
| C35 | Light height = storey − sill − 0.65 m | toml:150 | **CONTRADICTED** for Deuxième/Troisième proportions |
| C36 | Every étage window has a moulded architrave and keystone, at every class | toml:150 | **PARTLY** |
| C37 | Shop = glass 0.86 of each bay between stone piers, under a 0.9 m fascia, sill 0.3 m | toml:155-157 | **PARTLY** |
| C38 | Entresol: squat square-headed windows in the base stone, 0.45 of the bay | toml:162-164 | **SUPPORTED** |
| C39 | House ground floor: square-headed windows on a 1.0 m allège | toml:169-171 | **SUPPORTED** (low confidence) |
| C40 | The entrance is on the middle axis | toml:176-177 | **CONTRADICTED** |
| C41 | Grand/comfortable get a round-arched porte cochère; ordinary/modest get a flat porte piétonne | toml:176, 179-180 | **PARTLY** |
| C42 | Porte cochère 2.6 m wide | toml:180 | **SUPPORTED** |
| C43 | Porte piétonne 1.4 m wide | toml:180 | **PARTLY** |
| C44 | The entrance is confined to the ground storey (height h − 0.35) | toml:180 | **CONTRADICTED** for portes cochères |
| C45 | Comfortable/grand crown the noble-floor windows with pediments | toml:183-188 | **PARTLY** |
| C46 | `corner` is a site input | toml:12 | **UNTESTABLE** (never read by any rule: see O1) |
| C47 | The stone never rises above the legal cornice (the test) | RULES.md:34; tests/unit/test_haussmann_rules.py | **SUPPORTED** as a rule of thumb / **UNTESTABLE** for exceptions |

---

## 3. Verdicts with evidence

### C1: "agrees with the measured generator on shape" (toml:7-8, RULES.md:31-32)
Comparing `haussmann.png` with `paris_measured.png` case by case, the two drawings differ in shape, not only in decimals:
- the measured strip rusticates the base (bossage) and the rule strip does not;
- the measured strip draws a straight 45° comble before 1884 and an arched or oeil-de-boeuf comble after, while the rule strip draws the same 72° slab at every date;
- on the 1868 grand building the measured strip puts the noble floor over a rusticated rdc + low 1er, while the rule strip puts it straight on a 3.6 m ground floor;
- the 1900 café is about one storey taller in the measured strip, with roof cresting and an oculus.

Agreement on storey count and bay count is good. "Second decimal" overstates it. PARTLY.

### C2-C5: the decrees (toml:23-25, 45)
- **1783/84.** 11.70 / 14.62 / 17.55 m at 7.80 / 9.75 m matches the table on techno-science.net, which comes from the déclaration royale of 10 April 1783 and the lettres patentes of 28 August 1784. SUPPORTED.
- **1859.** "In streets more than 20 m wide, façades may now reach 20 m" (techno-science). The values match. Because `step()` uses `value <= limit` (rulefile.py:164), a street of exactly 20.0 m gets 17.55 m. That is what the strip's "1865, 20 m boulevard" gets, and it loses a full storey relative to a 20 m facade. The secondary source says "plus de 20 m", which supports the model. I could not reach the decree text to check whether it reads "20 m et au-dessus". `reglement.py:171` makes the same choice. This is worth one look at the Bulletin des lois, because the strip's own showcase case sits exactly on the boundary. UNTESTABLE from photographs.
- **1884.** 12 / 15 / 18 / 20 m with breaks at 7.80, 9.75 and 20 m matches the same source. Medium confidence, because it is a single secondary source.
- **After 1902.** The 1902 Bonnier decree (projections above the cornice, eighth-arc comble) is not modelled. A site with `year >= 1902` silently gets 1884 rules. That does not touch the strip, whose last case is 1900. PARTLY.

### C6: ambition by class (toml:27)
Daly's cornice heights against the 20 m legal limit:

| Class | Cornice heights | Share of legal | Model |
|---|---|---|---|
| Première | 18.53-21.05 m | 0.93-1.05 | grand 0.98 ✓ |
| Deuxième | 14.78-19.98 m | 0.74-1.00 (median 0.945) | comfortable 0.95 ✓ |
| Troisième (Beaumarchais, a wide street) | 15.6-15.9 m | ≈ 0.79 | modest 0.86, a little high |

B1 reaches ≈ 20 m on a 30 m boulevard.

Two weaknesses:
- Daly's Deuxième spread (0.74 at 88 Rivoli, which spends its height on fewer, taller storeys) shows ambition is not a class constant.
- paix3 is recorded at 21.05 m, over the limit (low confidence).

The file honestly marks the numbers INFERRED. PARTLY.

### C7-C9, C13, C15: the storey heights that hold
- **Shop ground 4.0 m** (toml:28). Daly's rdc is class-independent: 3.42-4.85 m, median 3.95 m (n = 16). SUPPORTED.
- **Entresol 2.8 m** (toml:30). Daly 2.40-3.12 m, median 2.98 m. SUPPORTED, slightly low.
- **Base total of 6.8 m** for shop + entresol. Daly's Deuxième balcony decks are at 6.55-7.93 m (median 6.95). B1 measures ≈ 7.9 m and B7 ≈ 6.8 m. SUPPORTED.
- **First letting floor 3.2 m** (toml:32). Daly Deuxième uppers have a median of 3.07 m (2.32-3.83). SUPPORTED for Deuxième. Première uppers run 3.1-3.7 m (median 3.48), so the model is about 0.3 m low for grand.
- **Storey count** (toml:48). The 30 m-avenue cases come out as R + E + noble + 3, which is what B1, B5 and B6 show, and Daly's Sebastopol plates (seb63, seb77, seb120) have 4 étages over the entresol. SUPPORTED.

### C8: house ground 3.6 m (toml:29)
Daly's ground floor is class-independent at a median of 3.95 m. Première runs 3.7-4.32 m and Troisième 3.61-4.01 m. The 3.6 m figure sits at or below the minimum for every class. It matters most for the 1868 grand building, which gets the lowest ground floor in the strip. PARTLY.

### C10: entresol only with a shop (toml:47, 63)
Daly finds the entresol in 9 of 10 Deuxième buildings and in 0 of 4 Première and 0 of 2 Troisième. Photos:

| Base | Buildings |
|---|---|
| Shop with an entresol | B1, B2, B3, B4, B5, B6, B9, B16, B17 |
| Shop without an entresol | B7, a grand building whose arcades swallow the height; B10 |

So "shop ⇒ entresol" is a fair proxy for Deuxième. Two things are wrong:
- the 1900 grand café gets an entresol, where Daly's Première has none;
- class, which Daly calls "the class signal", plays no part.

PARTLY.

### C11: noble floor 3.6 m at every class (toml:31)
Daly calls this "THE CLEAREST LADDER IN THE CORPUS": Première 4.23 m, Deuxième 3.83 m, Troisième 3.04 m. The gap of 1.2 m is far larger than the reading error of 0.2 m. The model gives 3.6 m to all four classes. That is 0.6 m short for grand, 0.2 m short for comfortable, and 0.56 m too tall for modest, whose "noble floor" Daly says does not exist as such. B1's 2e measures ≈ 3.8 m on an ordinary/comfortable building, which agrees with Deuxième. CONTRADICTED. Of all the class signals, this one is missing.

### C12: no low 1er étage (toml:61-65)
Daly: "a compressed level sits between the commercial ground storey and the noble floor in every Première and Deuxième building measured". In Première it is dressed as a full 1er étage of 3.20-3.60 m. B10, a comfortable building, shows it: a low 1er with segmental heads and plain garde-corps, then a pedimented, balustraded 2e. The model's grand building without a shop goes straight from a 3.6 m rdc to the noble floor. PARTLY: right for shops with an entresol, wrong for grand houses.

### C14: taper 0.95 (toml:33)
Daly's taper ratios:

| Class | Median | Range | n |
|---|---|---|---|
| Deuxième | 0.906 | 0.795-0.993 | 10 |
| Première | 0.861 | | 3 |
| Troisième | 0.962 | | 1 |

The corpus itself warns: "sample a distribution, not apply a constant". B2's ratios of 0.89 and 0.92 (shot from below, so overstated) sit between the two. The sign is right, and 0.95 is at the gentle end of the Deuxième range. PARTLY.

### C16-C19: bays and windows (toml:34-36, 51, 150)
- **Bay.** Daly's bay pitch runs 2.09-3.49 m, median 2.8 m, with no class ladder. Measured: B1 ≈ 2.5 m, B2 2.2-3.0 m, B7 ≈ 3.1 m. A preferred 2.6 m sits a little under the median. A 3.2 m maximum excludes ce119 (3.49 m) and Impératrice (3.23 m). SUPPORTED, slightly narrow.
- **End piers.** Party walls are rarely visible in street photos, so I could not test them. UNTESTABLE.
- **At least 2 bays.** The narrowest front in the sample is B8 at 3 bays. SUPPORTED.
- **Window share 0.45.** Daly's opening of 1.2 m over a pitch of 2.8 m gives 0.43, with a per-building range of 0.37 (ce119) to 0.57 (cons9). B1 ≈ 0.45-0.50 and B2 ≈ 0.43. The value is SUPPORTED. The *mechanism* is not: Daly's strongest finding is that window width is an absolute of about 1.2 m, "set by the croisée … not by the building's grandeur", and that the pier absorbs the variation in bay. A 3.2 m bay in the model gets a 1.44 m window and a 2.0 m bay gets 0.9 m, both outside Daly's 1.04-1.30 m range. PARTLY.

### C20-C23: the comble (toml:37, 53)
- **Height.** Daly's comble heights run 2.69-4.72 m on single-storey combles, median about 3.2 m. 3.2 m before 1884 is SUPPORTED as typical. The comble is "a TYPE choice, not a class-scaled proportion" (see C25). PARTLY overall.
- **Pitch.** This is the strongest geometric finding. Before 1884 the comble had to stay under a 45° line from the eaves, as techno-science says for 1783/84 and 1859, and `reglement.py:13-14, 285` encodes it as `inset >= h`. A plane at 72° rising 3.2 m runs back only 3.2 / tan 72° = **1.04 m**. The 45° line allows 1.04 m of rise at that inset, and the model builds 3.2 m. So every pre-1884 roof in the strip breaks the decree the file cites at toml:15. The repository's own corpus notes the Marville Sebastopol corner (B4) and others as a "straight 45-degree comble". The measured strip draws them that way. CONTRADICTED before 1884. After 1884, the near-vertical start of the arc makes a steep face plausible.
- **Material.** B2 and B17 have zinc brisis; B1, B12, B13 and B15 have slate or ardoise brisis with zinc details. Slate on the steep part and zinc on the terrasson is a common split. PARTLY.
- **Dormer form.**

| Form | Buildings |
|---|---|
| Triangular pediment | B7, B17 |
| Segmental or round zinc | B1, B6 |
| Arched or oeil-de-boeuf | B3, B5 |
| Plain flat zinc | B2 |
| Masonry pediment over a single window | B13 |

  Pedimented is one form among four. PARTLY.

### C24: a dormer over every axis (toml:85-86)
- One per axis: B5, B6, B7, B10, B16, B17.
- Fewer than one per axis: B1 (6 dormers + 4 roof lights over 10 bays), B2 (3 over 7), B8 (2 over 3), B9 (3 over 5), B12/B13.

Grand and newer fronts follow the axes; ordinary and older ones skip. PARTLY.

### C25: a second row of dormers only after 1884 (toml:83, 88-89)
Daly (1864) records two buildings whose combles hold **two full storeys**: 1 bd de Sébastopol (6.8 m) and 2-4 bd de Sébastopol (7.0 m). The corpus notes that the comble share of 0.279 and 0.285 comes from those two. B7 (1860s) shows a second row of small openings in the terrasson. Two-storey combles therefore existed under the 45° regime 20 years before the date the model gives. The 1884 arc made them easier, not possible. CONTRADICTED as a date rule. A probability that rises after 1884 would fit.

### C26: two chimney stacks on the party walls (toml:91-92)
- Party-wall souches are real and dominant: B2, B6 and B12 each have huge stacks.
- They are wide masonry blocks of 1.5-3 m carrying rows of pots, not 0.9 m posts.
- B1, B3 and B4 also carry stacks on the ridge, between the party walls, often 4-6 per front.

PARTLY.

### C27: an entablature crowns the base (toml:75)
B1, B6 and B17 show a strong consoled or modillioned entablature carrying the 2e balcon filant. Daly's cornice band depth has a median of 0.45 m. SUPPORTED.

### C28: balcons filants on the noble and top storeys (toml:72, 76)
The canonical pair at the 2e and 5e appears on B1, B3, B4, B5, B6, B7, B16 and B17, all Second Empire or early Third Republic buildings on wide streets. That is the model's target case, and it is SUPPORTED.

Real fronts depart from it in several ways:
- B2: the 2e balcony covers only 4 of 7 bays.
- B15 (1896): a filant only at the 5e.
- B10 (comfortable): no filant at all, only stone balustrades per window.
- B8, B9, B11, B12, B13 (pre-1850 or modest): individual garde-corps, at most one thin balcony.

Daly's rue de Longchamps (Troisième) has "no projecting balcony anywhere on the facade, only flush garde-corps".

The model gives two full-width filants to the 1835 modest house on a 9 m street. For that case it is CONTRADICTED.

### C29: the cornice crowns the top storey (toml:77)
On B1, B2, B6 and B17 the **heaviest** modillioned or consoled cornice sits *below* the 5e (or top) storey and carries its balcon filant. A lighter cornice or gutter crowns the 5e. Daly's ce125 puts the last balcony deck at 15.27 m against a cornice at 18.53 m, so the balcony is one full storey below the cornice. The model has the balcony at the foot of the top storey, as the photos show, but no entablature under it, and puts its only heavy cornice at the top. PARTLY.

### C30: everything is stone (toml:134)
Cut stone (pierre de taille) is right for B1-B7, B10 and B14-B17. Before about 1850, and on modest fronts, walls are plaster or render over rubble (moellon) or timber: B8, B9, B11, B12 and B13 all are. The 1835 modest case should be plaster. PARTLY.

### C31: every opening is flat-headed (toml:150, 157, 164, 171)
Flat heads dominate on the upper étages: SUPPORTED there. Exceptions:
- segmental (cambré) heads: B10's 1er;
- round-arched ground openings: B7, B14, B17's shop arch;
- arched noble windows: B5 and others in the corpus.

The measured strip uses segmental heads on its noble floors. PARTLY.

### C32: noble windows to the floor (toml:149)
B1, B2, B5, B6, B7, B10 and B17 all show this. SUPPORTED.

### C33: letting floors on a 0.85 m allège (toml:147, 149)
In every one of the 17 buildings the upper-floor windows of the étages are **porte-fenêtres to the floor**, guarded by an iron garde-corps or an individual balcon:
- B1: 3e and 4e;
- B2: 3e and 4e;
- B5: 3e and 4e;
- B6: 3e and 4e;
- B8: every floor;
- B10: 1er, 3e and 4e;
- B11: every floor;
- B17: 3e and 4e grouped balconies.

Daly's balcony railing height is 0.87-1.07 m. Only the entresol and some attics have true allèges. The strip's letting floors, with plain windows floating on blank stone and no railing, are the single most visible departure from Paris. CONTRADICTED, high confidence.

### C34: a garde-corps across a porte-fenêtre (toml:104, 107)
The production fires only when `has('garde_corps') and garde_corps`, and no rule in the file sets `garde_corps` (grep: toml:107 is its only occurrence). So it never fires, and no real building can test it. UNTESTABLE as a claim, but it is a defect. It is also the mechanism that would fix C33.

### C35: light height = storey − sill − 0.65 m (toml:150)
On the noble floor the model gives 3.6 − 0.1 − 0.65 = **2.85 m** at every class.

| | Première | Deuxième | Troisième |
|---|---|---|---|
| Daly window height at the nobile | 2.92 m | 2.24 m | 2.09 m |
| Model window height at the nobile | 2.85 m | 2.85 m | 2.85 m |
| Daly upper-floor aspect (h/w) | 1.99 | 1.80 | 1.905 |

On a 3.2 m letting floor the model's light is 3.2 − 0.85 − 0.65 = 1.70 m over 1.17 m, an aspect of 1.45.

So the model's noble windows are 0.6-0.75 m too tall for comfortable and modest, and its letting-floor windows are too squat. That is the opposite of Daly's ladder. CONTRADICTED for Deuxième and Troisième; about right for Première.

### C36: a moulded architrave and keystone on every étage window (toml:150)
- Surrounds are usual on B1-B7, B10 and B17.
- Carved keystones or consoles appear on B1, B2, B10 and B17.
- B8, B9, B11, B12 and B13 (modest, pre-1850) have plain reveals or a thin band.

Klass does not affect it. PARTLY.

### C37: the shopfront (toml:155-157)
Two real types:
- **Glazing within stone piers, bay by bay** (B1 left, B7, B10, B14). This is the model's type.
- **Wooden devantures** that project and span several bays (B4, B8, B9, B11, B12), often with the entresol glazed as part of the shop (B5, B6, B17).

The 0.9 m fascia is plausible. PARTLY.

### C38-C39: entresol and house-ground windows (toml:162-171)
Entresol windows are squat and square-headed in the base stone (B1, B2, B6). Daly's entresol aspect has a median of 1.57; the model's 1.75 / 1.17 = 1.5. SUPPORTED. The model's residential ground floor, with windows on an allège, matches B15 and Daly's residential plates. SUPPORTED, low confidence (few examples).

### C40: the entrance on the middle axis (toml:176-177)
| Entrance | Buildings |
|---|---|
| Centred | B2 |
| Off-centre (bay 3 of 10, the end bay, bay 4 of 5, near-end) | B1, B5, B7, B9, B10, B15, B17 |
| Can't tell (party walls not visible) | B6 |

The plan logic (the passage to the courtyard and the stair) decides where the entrance goes. Façade symmetry does not. CONTRADICTED, medium confidence.

### C41-C44: the entrance itself (toml:176-180)
- **Width.** Daly's carriage door is 2.41-2.67 m (n = 7). B2's leaves are ≈ 2.5-2.6 m. 2.6 m is SUPPORTED.
- **Pedestrian door.** Daly: Deuxième 1.61-1.91 m (median 1.75), Troisième 1.36 m. A 1.4 m door fits modest but is ≈ 0.35 m narrow for ordinary. PARTLY.
- **Who gets an arch.** B2, B5, B7 and B17 have round-arched carriage doors. B1 (ordinary/comfortable) and B10 (comfortable) have flat-headed doors. In Daly, 8 of 11 Deuxième buildings have a porte piétonne, not a cochère. "Comfortable ⇒ porte cochère" is therefore too generous. PARTLY.
- **Height.** The porte cochère arch rises through the entresol on B2, B5 and B6. Daly's door heights reach 5.0-5.07 m at 39 Mathurins, 2-4 Sébastopol and 87 Sébastopol, because "the opening sometimes swallows the entresol". In the model the arch stops at the top of the ground storey and the entresol is pierced above it. CONTRADICTED for portes cochères on shop buildings with an entresol. Pedestrian doors do stop at a lintel.

### C45: pediments on the noble floor (toml:183-188)
- **On the noble floor:** B6, and B10 (its 2e, over a low 1er).
- **On the 3e, the floor above the noble:** B1, whose noble 2e carries consoles and mascarons instead.
- **No pediments at all**, carved shells or consoles instead: B2, B5, B7.

Pediments are common on comfortable and grand fronts but float between floors. PARTLY.

### C47: the stone stays under the legal cornice
Daly's Première and Deuxième buildings press up against 20 m: six of them sit at 19.0-20.0 m. B1 measures ≈ 20 m. As a generative rule this is SUPPORTED. Overshoots (paix3 at 21.05 m, low confidence) and surélévations cannot be checked from these photographs.

---

## 4. What real immeubles commonly have that the model leaves out

- **O1. Corner buildings.** `corner` is a site field (toml:12) that no rule reads. Corners are among the most characteristic Paris forms in the sample: B3, B4, B7 and B10 have cut or rounded corners; B14 and B15 have a tourelle or dome; B16 has a rounded corner. The repository has a whole corpus family for them (`corner`, 12 images).
- **O2. Rustication of the base.** Refends or bossage on rdc + entresol appear on B5, B6, B7, B10, B14 and B17, and in the measured strip. The rule strip's base is the same flat ashlar as the étages.
- **O3. Garde-corps and individual balcons on the 3e and 4e**, including balconies grouped over two bays (B17). See C33. This is the most frequent element in the sample and the model has none.
- **O4. Persiennes.** Folding iron or wood shutters appear on B1, B8, B9, B11 and B12, and are universal before 1850.
- **O5. The heavy entablature under the 5e balcony**, with a lighter crowning cornice (C29).
- **O6. The comble's profile.** The real comble has a brisis and terrasson break, a gutter (chéneau) and often a continuous balcony at the dormer foot (B6, B16). It also has zinc standing-seam ribs, oeil-de-boeuf openings and tabatières.
- **O7. Chimney souches.** Wide party-wall stacks with many pots, plus ridge stacks (C26).
- **O8. Off-centre entrances, multiple entrances, and doors that rise through the entresol** (C40, C44).
- **O9. Class-specific storey structure.** No entresol in Première; a low 1er under the noble floor; a taller noble floor and taller windows for richer buildings (C10-C12, C35). The model has the class parameter but spends it only on ambition, the door and pediments.
- **O10. Period change after 1882 / 1884 / 1902.** Bow windows and oriels (allowed from 1882 at 40 cm, much larger after 1902: B15, B14), denser sculpture, the attic storey above the cornice (B2, B15), and iron-and-glass commercial bays (B14). The 1890 and 1900 cases look the same as 1865 except for the extra dormer row.
- **O11. Pre-Haussmann vocabulary** for dates before 1850: plaster walls, thin cornices, shutters, simple pitched slate roofs with few dormers, irregular bays (B8, B9, B11, B12, B13).
- **O12. Sculpture and order.** Mascarons, carved consoles under balconies, caryatids (corpus B-magenta, rue de Rennes), giant pilasters (B6 left, B17). These are not required in a simple model, but they are what separates grand from comfortable in every photo.
- **O13. Shop devantures, awnings and signage**, and the glazed entresol as part of the shop (C37).
- **O14. Bay irregularity.** Bays next to the door or at the ends differ in width (B2), and central avant-corps or groupings break the uniform rhythm (B17).

---

## 5. What looks wrong in `docs/strips/haussmann.png`

1. **The letting floors are blank windows on blank stone.** No railing, no balconnet, no allège panel. Every real example has garde-corps on these floors (C33, O3).
2. **The 1835 modest house looks like a small 1865 boulevard building.** It has cut stone, two full-width balcons filants, moulded surrounds and a zinc mansard. It should be plastered, shuttered, with thin garde-corps and probably a plain slate roof (C28, C30, O11).
3. **The roof is a flat grey slab at the same steep pitch in every case.** Before 1884 it breaks the 45° gabarit (C21). There is no brisis/terrasson break, gutter or ribbing (O6). The dormers are small and float in the slab.
4. **Two pencil-thin chimneys at the outer edges.** Real party-wall souches are massive (C26, O7).
5. **The 1868 grand avenue building has the lowest base in the strip** (3.6 m), a noble floor at 3.6 m that is no taller than the comfortable one, and no low 1er. Grand should read as taller storeys, not more of the same (C8, C11, C12).
6. **The porte cochère arch is squeezed inside the ground storey**, with entresol windows above it in the 1865 and 1900 cases. Real arches rise through the entresol (C44).
7. **Every entrance is dead centre and every bay is identical** (C40, O14).
8. **The base is not rusticated.** The base entablature reads only as a thin band, so the base does not read as a base (O2). The heavy cornice under the 5e balcony is missing (C29).
9. **The 1890 and 1900 buildings show no Belle Époque change** apart from the second dormer row: no bow window, no attic storey and no richer sculpture (O10). The 1900 grand café is not a corner, though corner sites are common (O1).
10. **The noble-floor windows are very tall in every class.** On the modest 1890 and ordinary 1875 cases they read as grander than the comfortable 1865 (C35).

What is right in the strip, to be fair:
- the overall proportion of shop base, noble floor, tapering étages and comble;
- storey counts against the legal height;
- a balcon filant at the 2e and 5e on the Second Empire cases;
- window-to-pier rhythm;
- dormers on axes on the grand cases;
- the 1900 building visibly taller than the 1865 one, because of the 1884 comble.

---

## 6. Highest-value fixes (ranked by visual effect per line of TOML)

1. Set `garde_corps = true` on letting-floor porte-fenêtres (sill to about 0.1 m, garde-corps about 1.0 m). One rule, and the dead production at toml:107 starts working (C33, C34).
2. Make the pre-1884 comble a 45° face, or cap its height at the inset the 45° line allows (C21).
3. Give `principal` and the principal window height a class ladder: 4.2 / 3.8 / 3.4 / 3.0 m and about 2.9 / 2.25 / 2.15 / 2.1 m. Keep the window *width* absolute at about 1.2 m (C11, C19, C35).
4. Move the entrance off the middle axis by a seeded choice: end bay, bay 2-3, or middle. Let a porte cochère swallow the entresol when there is one (C40, C44).
5. Date gates: before 1850, plaster walls, shutters and no balcon filant; after 1882, an optional oriel. Read `corner` (C30, O1, O10, O11).
6. Allow a two-storey comble before 1884 with a low probability (C25).
