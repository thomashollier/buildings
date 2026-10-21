# Paris rule file (`haussmann.toml`): grading

An independent assessment. I did not write the model and I did not gather the
evidence. I weighed the two fidelity reports against each other and against
`dev/reference/`, ran the model on a few sites the strip does not show, and
looked at three corpus photographs myself to settle the points where the
reports disagree.

- **Model:** `src/buildings/typologies/paris/haussmann.toml` (loaded by
  `paris/rules.py`; format in `dev/RULES.md`), drawn in
  `docs/strips/haussmann.png`.
- **Evidence:** `dev/fidelity/haussmann/observer.md` (blind to the model, 31
  buildings and 7 dated plates), `dev/fidelity/haussmann/adversary.md`
  (17 buildings, 47 claims), `dev/reference/daly_measurements.json` (Daly 1864:
  4 Première, 10–11 Deuxième and 2 Troisième classe buildings),
  `paris/reglement.py`, and for comparison `docs/strips/paris_measured.png`.

Grades: **A** matches · **B** right idea, needs tuning · **C** wrong, or misses a
key variant · **D** contradicted by the evidence (or by the file's own decree).

Date: 2026-10-21.

---

## 0. Method and the tie-breaks

**Commons.** I tried the Commons API. It answered `429 Too many requests`, and
`upload.wikimedia.org` and `fr.wikipedia.org` are refused at this session's
proxy (`403`). So I fetched nothing new. Instead I looked myself at three
photographs from the repository's own Commons corpus, all frontal enough to
count on:

| Photo | What I read off it |
|---|---|
| `images/se-facade/se-facade_06_boulevard-voltaire.jpg` (2 bd Voltaire) | 10 axes. Shop, then an entresol of square windows. Filant at the noble floor (full width, on consoles with mascarons). **Grouped balconies over 2–3 bays on the next floor**, with alternating segmental and triangular pediments one floor *above* the noble. Garde-corps on every window of the 4e. Heavy modillioned cornice **under** the top storey, carrying the second filant, and a light cornice above it. Door in bay 3 of 10, flat-headed, ground storey only. 5 dormers + 5 roof lights over 10 axes. |
| `images/se-facade/se-facade_07_rue-blanche-53.jpg` (53 rue Blanche) | 7 axes. **Porte cochère on the middle axis**, round-arched, rising through the entresol to the noble balcony's consoles. Noble filant over the central 5 bays only. Garde-corps on every upper window. No pediments: carved shells instead. Dentilled main cornice under the top storey, carrying the second filant. 3 dormers over 7 axes, zinc. |
| `images/se-facade/se-facade_11_rue-chateaudun-55.jpg` (55 rue de Châteaudun) | Glazed entresol as part of the shopfront. Round-arched porte cochère through the entresol. Filant at the noble and top floors. Grouped balconies on the middle floors, and a per-window balcony where not grouped. Dormers one per axis. |

**Where the two reports disagree, and how I settled it.**

1. **Entrance on the middle axis.** The adversary says it is mostly off-centre
   (7 of 8). The observer says it is central when the axis count is odd. Both
   are right: the adversary's off-centre cases are even counts, corners or
   modest houses, and the observer's central cases are odd-count designed
   plates. Bd Voltaire (10 axes, bay 3) and rue Blanche (7 axes, centre) fit
   that split exactly. **Ruling: parity decides, with the weights in R13.**
2. **Entresol on grand houses.** Daly has 0 of 4 Première with an entresol,
   but the adversary's grand commercial photos (Châteaudun, avenue de l'Opéra
   38) both have one. Daly's Première set is residential (rue de la Paix,
   Champs-Élysées, avenue de l'Impératrice). **Ruling: grand + shop usually
   has an entresol; grand + house has a low dressed 1er instead.**
3. **Pre-1884 roof pitch.** The adversary calls the 72° face a breach of the
   45° gabarit. The observer says the visible brisis reads at 45–70° in
   photos, and that pitch cannot be measured from the street. The Voltaire
   brisis does look steep, but it is foreshortened. The decree, which
   `reglement.py` encodes and the file cites, and the measured generator all
   say 45°. **Ruling: the decree wins. A 3.2 m comble at 72° has a run of 1.04
   m, where 45° needs 3.2 m.**
4. **Where the heavy cornice goes.** The two reports agree, and so do all
   three photographs: the heavy modillioned cornice sits under the top
   storey and carries its filant. The model has it on top.

**Things neither report caught, which I checked by running the model.**

- **The stone overshoots the legal cornice on narrow streets.** `lettings` is
  `max(1, …)`, and the base plus noble floor plus one letting floor is 13.44–13.6
  m. On a street under 7.80 m (legal 11.70 or 12.00 m) that is **1.9 m over
  the decree**. Ran: 7 m street, 1865, modest shop: eaves 13.60 against a
  legal 11.70. 7 m street, 1890, grand house: 13.44 against 12.00. The unit
  test (`tests/unit/test_haussmann_rules.py`) starts at 8 m streets, so it
  never sees this. The file's one stated guarantee is broken.
- **Balconies below 6 m.** The 1823 ordonnance, cited in `reglement.py`
  (`min_balcony_height = 6.00`), forbids a projecting balcony under 6 m. Every
  house without a shop puts its noble filant on a 3.6 m ground storey, so the
  deck sits at **3.6 m**. That happens in three of the six strip cases (1835,
  1868, 1875).

---

## 1. RULE problems: grades by rule and parameter

Line references are to `haussmann.toml`.

### 1.1 The envelope

| # | Rule / parameter | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| E1 | `steps_royal` 11.70 / 14.62 / 17.55 (1783–84) | **A** | Both reports; the printed 17.55 m at Sébastopol 72; the 17.5 m cluster on Sébastopol (observer R1.3). | Keep. |
| E2 | `steps_1859` values | **A** | Both reports; Daly's Première and Deuxième cornices crowd 19.0–20.0 m. | Keep. |
| E3 | `step()` boundaries (`value <= limit`) | **C** | Recalled from the decree text, which I could not open here: 1783 and 1859 read "de 7m80 à 9m74" and "9m75 et au-dessus"; 1859 reads "dans les voies de 20 mètres et au-dessus". So 7.80, 9.75 and 20.00 m belong to the **upper** band. The adversary flagged the 20 m case. The strip's showcase "1865, 20 m boulevard" gets 17.55 m, so it loses the storey that bd Voltaire and Daly's Sébastopol houses have (R+E+4 étages). Confidence M. | Limits `7.79, 9.74, 19.99` in all three tables, or a `<` step. Fix `reglement.py` to match. |
| E4 | `steps_1884` 12 / 15 / 18 / 20 | **B** | One secondary source (the adversary). The observer marks the middle bands L and recalls "18–20 m for 12–20 m". My own recollection is that 1884 gives 20 m from **12 m** streets up, which would add a storey to the 1890 12 m case. Not checked against the decree. | Keep for now. Read the 23 July 1884 decree; if it confirms, add `[11.99, 18.0]` and make ≥ 12 m give 20.0. |
| E5 | No regime after 1902 | **B** | Adversary C5. A site from 1902 on silently gets the 1884 rules. | Refuse `year >= 1902`, or add a Bonnier rule set. |
| E6 | 1859 storey cap missing | **C** | Recalled decree text (M): on ≥ 20 m streets, "plus de cinq étages carrés au-dessus du rez-de-chaussée, entresol compris" is forbidden. The model happens not to exceed it in the strip, but once the boundary fix (E3) and lower storeys (R5) are in, it could. | Guard: square storeys above the RDC ≤ 5, from 1859 to 1884. |
| E7 | `ambition` 0.86 / 0.90 / 0.95 / 0.98 | **B** | Daly: Première 0.93–1.05, Deuxième median 0.945, Troisième ≈ 0.79. Observer R1.4: 13 of 16 cornices are within 1 m of the limit. The constant is fine as a median. But `round()` on the letting count overshoots the target by up to half a storey (1890 modest: 16.64 m against a target of 15.48 m), so it is not really an ambition. | Per house: draw from {1.00: 0.45, 0.95: 0.35, 0.85: 0.20} for comfortable and grand; modest {0.95: 0.3, 0.85: 0.5, 0.75: 0.2}. Use `floor` with a check against legal, not `round`. |
| E8 | `lettings = max(1, …)` | **D** | My run (§0): 1.9 m over the legal cornice on any street under 7.80 m. That breaks the decree the file encodes. | Let lettings reach 0. If base + noble still exceeds legal, drop the entresol, then lower the noble floor to the 2.60 m minimum. Extend the test to 7 m streets. |
| E9 | Year switch at 1859 (old table before) | **A** | Observer R1.3: Sébastopol houses designed before mid-1859 have 17.55 m on a 30 m boulevard. | Keep. |

### 1.2 The storey stack

| # | Rule / parameter | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| S1 | `shop_ground` 4.0 m | **A** | Daly RDC median 3.95 m, 3.42–4.85, class-independent. | Keep (draw 3.6–4.4 if you like). |
| S2 | `house_ground` 3.6 m | **C** | Daly says the RDC is class-independent at 3.95 m; 3.6 m sits below every class's median. The grand 1868 case gets the lowest base in the strip. The observer adds a raised RDC (0.5–1.0 m over soupiraux) on residential avenues (R3.8). | 4.0 m. |
| S3 | `entresol` 2.8 m | **B** | Daly 2.40–3.12, median 2.98 (n = 9). | 3.0 m. |
| S4 | Entresol ⇔ shop | **C** | Daly: 9 of 10 Deuxième, 0 of 4 Première (residential), 0 of 2 Troisième. Photos: 9 of 11 shop bases have one. Class plays no part in the model. | Weighted by class (R4). |
| S5 | No low 1er under a grand noble floor | **C** | Daly: "a compressed level sits between the ground storey and the noble floor in every Première and Deuxième building". In Première it is a dressed 1er of 3.20–3.60 m (median 3.40). Adversary B10 also has one. | Grand without a shop: low 1er of 3.4 m, in the base's bossage. |
| S6 | `principal` 3.6 m at every class | **D** | Daly calls it "the clearest ladder in the corpus": 4.23 / 3.83 / 3.04 m (Première / Deuxième / Troisième). Both reports; bd Voltaire's noble floor measures ≈ 3.8 m. | grand 4.2, comfortable 3.8, ordinary 3.4, modest 3.0. |
| S7 | `upper` 3.2 m | **B** | Daly upper-storey medians: Première 3.48, Deuxième 3.07, Troisième 2.92. Right for comfortable only. | grand 3.45, comfortable 3.1, ordinary 3.0, modest 2.9. |
| S8 | `taper` 0.95, constant, starting at the first letting floor | **B** | Daly (from the noble floor up): Deuxième median 0.906, range 0.795–0.993 (n = 10); Première 0.861 (n = 3); Troisième 0.962 (n = 1). Two of ten don't taper at all and one tapers hard. "Sample a distribution, not a constant" (both reports and Daly). | Per house, drawn: {0.99: 0.2, 0.93: 0.35, 0.89: 0.35, 0.80: 0.1}. |
| S9 | Storey count as "what fits" | **A** | Adversary C15; bd Voltaire, Châteaudun and Daly's Sébastopol plates all show R+E+4 at 20 m. | Keep, but see E3, E6, E8. |
| S10 | Base entablature 0.45 m on the base | **A** | Daly cornice band median 0.45 m; the consoled entablature carrying the noble filant appears in all three of my photos. | Keep. |
| S11 | Main cornice crowns the top storey | **C** | Both reports, and all three of my photos: the heavy modillioned or dentilled cornice sits *under* the top square storey and is the deck of its filant. A lighter cornice or gutter crowns the top storey. | Move the 0.6 m modillioned cornice to the foot of the top storey; put a 0.3 m plain cornice at the top. |

### 1.3 Balconies

| # | Rule | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| B1 | Filant on the noble floor and on the top storey | **A** for 1853–84 comfortable/grand on wide streets; **D** for pre-1850 and modest | Observer R4.1 ("nearly every Second Empire photo"); adversary C28 (8 buildings); all three of my photos. But Daly's rue de Longchamps (Troisième) has no projecting balcony at all, and the pre-1850 and modest photos (B6–B8, B11–B13) have none or one thin one. The 1835 modest case gets two full-width filants. | Weighted by class and date (R6). |
| B2 | The filant is always full width | **B** | Central bays only on Sédille 1866, Sébastopol 72 and rue Blanche (5 of 7 bays, which I saw). Full width on most of the rest. | Per house: full 0.65, central bays 0.35. |
| B3 | A balcony at the noble floor on a house without a shop | **D** | The 1823 ordonnance (`reglement.py`: 6 m minimum). The model puts the deck at 3.6 m in three of six strip cases. | No projecting balcony under 6 m. Combined with S2 and S5, the grand house's noble deck rises to ≈ 7.4 m (4.0 + 3.4), which is legal and matches Daly (6.55–7.93 m). |
| B4 | Nothing on the letting floors (the `garde_corps` production never fires) | **D** | The single most common element in both reports: every one of the 17 adversary buildings and the observer's R5.1 ("every window on the étages is a French window … so every one has a garde-corps or a balcony"). My three photos agree. `garde_corps` is set by no rule (adversary C34). | Every étage window to the floor (sill 0.1) with a 1.0 m garde-corps, and letting-floor balconies weighted by date (R2). |

### 1.4 Windows

| # | Rule | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| W1 | `window_share` 0.45 of the bay | **B** | The value is right on average (Daly 0.43; bd Voltaire 0.45–0.50). The mechanism is wrong: Daly's strongest absolute is the opening width, 1.04–1.30 m regardless of bay or class. A 3.2 m bay gives 1.44 m and a 2.0 m bay gives 0.90 m, both outside the measured range. | `light_width = 1.2` (per house, draw 1.1–1.3). Let the pier absorb the bay. |
| W2 | Noble windows to the floor (sill 0.1) | **A** | Every photo, both reports. | Keep. |
| W3 | Letting windows on a 0.85 m allège | **D** | See B4. Only entresol and some attic windows have a true allège. | Sill 0.1 on every étage. |
| W4 | `light_height = h − sill − 0.65` | **D** | It gives a 2.85 m noble light at every class. Daly: 2.92 / 2.24 / 2.09 m (Première / Deuxième / Troisième). All of the class signal in a window is in its height (Daly). Letting lights come out 1.70 × 1.17 m (aspect 1.45) against a Daly aspect of 1.8–2.0, so the class ladder is inverted. | Noble light height by class: 2.9 / 2.25 / 2.15 / 2.1 m. Letting lights at aspect 1.9 (≈ 2.3 m), the top storey at 0.65–0.75 of the noble light (observer R3.4). |
| W5 | Moulded architrave and keystone on every window, every class | **C** | Observer R5.2: surrounds decrease upward; modest and pre-1850 have plain reveals or a band. | By floor and class (R10). |
| W6 | Pediments on the noble floor for comfortable and grand | **B** | Present on Opéra 38 and Sommerard. On bd Voltaire they are one floor up. Rue Blanche, Châteaudun and Halévy have none (shells or consoles instead). Alternating triangular and segmental is the grand mark (observer R5.3). | Weighted placement (R11). |
| W7 | Every head flat | **B** | True of the upper étages. Exceptions: segmental heads on a low 1er (Sommerard), round-headed RDC openings on residential avenues and arcades (R3.8, R8.5). | Flat by default; round or segmental on a residential RDC 0.5. |
| W8 | Entresol windows: squat, in the base stone | **A** | Daly entresol aspect 1.57; model ≈ 1.5. My photos agree. | Keep. |
| W9 | House ground windows on a 1.0 m allège | **B** | Few examples. A raised RDC over soupiraux is the residential-avenue type (R3.8). | Keep, and add soupiraux and a 0.6 m plinth. |

### 1.5 The ground floor and the entrance

| # | Rule | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| G1 | Shop: glass 0.86 of each bay between piers, 0.9 m fascia | **B** | One of two real types. The other is the wooden devanture over several bays (pre-1850 and modest), and a glazed entresol that belongs to the shop (Châteaudun, Opéra 38, Étienne-Marcel). | Weighted (R16). |
| G2 | Entrance on the middle axis | **C** | Settled in §0: centred on odd counts (rue Blanche, Sédille 1866, Sébastopol 72, Rennes 1881), off-centre on even counts (bd Voltaire bay 3 of 10, Étienne-Marcel end bay), and often off-centre on modest houses (St-Merri bay 4 of 5). On an even count the model's "middle bay" is not an axis at all. | Weighted by parity (R13). |
| G3 | Porte cochère iff comfortable or grand | **C** | Daly: Première 4 of 4 carriage doors; Deuxième 3 of 11; Troisième 0. Photos give comfortable arches on rue Blanche and Étienne-Marcel, and flat pedestrian doors on bd Voltaire and Sommerard. | Weighted by class (R12). |
| G4 | Porte cochère 2.6 m | **A** | Daly 2.41–2.67, median 2.58 (n = 7), the same in both top classes. | Keep. |
| G5 | Porte piétonne 1.4 m | **B** | Daly: Deuxième 1.61–1.91 (median 1.75); Troisième 1.36. | 1.75 m; 1.36 m for modest. |
| G6 | The entrance stops at the ground storey | **C** | Rue Blanche and Châteaudun (which I saw), Opéra 38; Daly has door heights of 5.00–5.07 m where the opening swallows the entresol. Bd Voltaire's door stops at its lintel. | A porte cochère with an entresol above: rises through it with weight 0.6 (R12). |

### 1.6 The comble

| # | Rule | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| C1 | `mansard.before_1884` 3.2 m | **A** | Daly single-level combles median ≈ 3.2 m (2.7–3.5); `reglement.py` caps the pre-1884 comble at 3.20 m. | Keep for the one-level type. |
| C2 | `mansard.after_1884` 4.6 m | **B** | It is a plausible median, but the evidence says comble height is a type (one level ≈ 3 m, two levels ≈ 7 m), not a scaled value (observer R1.7, Daly). | Type, drawn (R8). |
| C3 | Pitch 72° at every date | **D** before 1884; **B** after | See §0 tie-break 3. The 45° gabarit is the decree the file cites. After 1884 the arc starts near-vertical, so a steep brisis is right. | Before 1884: a 45° face, or brisis 60° up to 1.2 m and then a terrasson of ~20°, staying inside the 45° line from the cornice's edge. |
| C4 | Second dormer row only from 1884 | **D** | Daly records two-storey combles at 1 and 2–4 bd de Sébastopol (6.8 and 7.0 m), both 17.55 m cornices; the observer counts them as the type that goes with a 17.5 m cornice on a wide street (R1.3, R7.4); Halévy has a second row before 1884. | Weighted by period (R8). |
| C5 | One dormer per axis | **B** | Per axis: 6 adversary buildings plus Châteaudun; mostly grand. Fewer: bd Voltaire (5 on 10), rue Blanche (3 on 7), Duquesne (4 on 6), and the modest houses. Always symmetric. | Weighted by class (R9). |
| C6 | Dormer form: pedimented, then segmental above | **B** | One of four forms. Tally across both reports: pedimented 4, segmental or round zinc 3, oeil-de-boeuf or arched 4, plain box 3, hipped capucine 1. | Weighted (R9). |
| C7 | Roof material zinc | **B** | Zinc on the terrasson and often on the brisis; slate on the brisis of better houses (Sédille 1866, Rennes 1881, bd Voltaire). | Brisis: zinc 0.6, slate 0.4; terrasson zinc. |
| C8 | Two chimneys, one per party wall | **B** | Party-wall souches are right and dominant. They are wide masonry slabs of 1.5–3 m with rows of pots, not 0.9 m posts. Wide fronts also carry ridge stacks (bd Voltaire has 4 between its party walls). | Souches 1.5–2.5 m wide, rising 1.5–3 m; plus one ridge stack per ~4 axes on fronts of 8 axes or more. |

### 1.7 Bays, wall and class

| # | Rule | Grade | Evidence | Corrected value |
|---|---|---|---|---|
| X1 | `bay` 2.0 / 2.6 / 3.2 | **B** | Daly pitch 2.09–3.49 m, median 2.8 m, no class ladder. Pre-1850 reads tighter, 2.2–2.6 m (observer R2.2). | [2.1, 2.8, 3.5]; [2.1, 2.4, 2.8] before 1850. |
| X2 | `end` 0.2 / 0.35 / 0.75 | **untestable** | Neither report could see party walls. | Keep. |
| X3 | Even trumeaux, every bay alike | **B** | Even spacing is typical; grouped 2-1-2 or 1-3-1 rhythms are "more common after 1870" (observer R2.4). | Per house: even 0.75, grouped 0.25 after 1870 (0.1 before). |
| X4 | Every wall is stone | **C** | Plaster over rubble before c.1850 and on many modest fronts (observer R9.2; adversary C30; St-Merri, Bretagne, Victoire). | Weighted (R7). |
| X5 | `klass` drives only ambition, the door and pediments | **C** | The evidence puts class in: entresol vs low 1er, noble height, window height, balcony presence, door type, surround richness. Not in: window width, RDC height, bay pitch, balcony projection (observer R11.1; Daly). | Spread class over those (R3–R12). |
| X6 | `corner` is a site field that no rule reads | **C** | Adversary O1; observer §10. Corners are some of the most characteristic Paris forms. | See O1. |

---

## 2. DRAWING problems (`docs/strips/haussmann.png`)

These are about how the drawing turns what the rules say into marks. Some
fall away once the rule fixes go in; the ones marked *renderer* won't.

| # | Problem | Grade | Cause | Fix |
|---|---|---|---|---|
| D1 | Letting-floor windows float on blank stone with no rail | **D** | Rules B4 and W3. | Fixed by R1. |
| D2 | The roof is a flat grey slab: no brisis/terrasson break, no chéneau, no standing-seam ribs | **C** | *Renderer*, plus rule C3. | Draw the roof as two planes with a gutter line; zinc ribs at about 0.5 m. |
| D3 | Chimneys are pencil-thin posts at the edges | **C** | Rule C8 dimensions. | Fixed by R15. |
| D4 | The base doesn't read as a base: flat ashlar, a thin entablature line | **C** | Omission O2 (no bossage) and a thin course. | Draw refends (horizontal channel joints) on RDC + entresol. |
| D5 | The porte cochère arch is pinched inside the ground storey with entresol windows over it | **C** | Rule G6. | Fixed by R12. |
| D6 | The 1868 grand house has the lowest base, a noble floor no taller than the comfortable one, and a balcony at 3.6 m | **D** | Rules S2, S5, S6, B3. | Fixed by R3–R5. |
| D7 | Noble windows read grander on the modest 1890 house than on the comfortable 1865 one | **D** | Rule W4. | Fixed by R5. |
| D8 | The 1835 modest house is a small 1865 boulevard building | **D** | Rules B1 and X4; omission O4. | Fixed by R7. |
| D9 | The 1890 and 1900 houses look like 1865 plus a dormer row | **C** | Omission O5. | R17. |
| D10 | Dormers are small and float in the slab | **B** | *Renderer.* | Sit the dormer's sill 0.5–1.0 m above the gutter, behind the top filant (observer R7.2). Size 0.9–1.1 × 1.4–1.8 m. |

What the strip gets right, and should keep: the overall proportion of shop,
entresol, noble floor, tapering étages and comble; storey counts against the
height limit; the 2e/5e filants on the Second Empire commercial cases; the
window-to-pier rhythm; dormers on axes on the grand cases; and the 1900
house standing taller than the 1865 one.

The measured strip (`paris_measured.png`) already does D2 (a 45° comble
before 1884), D4 (bossage), D6 (a grand house on a rusticated RDC + low 1er)
and puts its arches through the base. Port those choices across, not the
code.

---

## 3. OMISSIONS

| # | Missing | Weight of evidence | Notes |
|---|---|---|---|
| O1 | **Corners**: pan coupé (one or two bays), rotonde, acute prow; lines wrap unbroken; the corner is the accent, with more balconies and a raised or domed cap; a tourelle after 1884 | H (observer §10; adversary O1; 12-image corpus family) | `corner` is already a site input. |
| O2 | **Bossage on the socle**: RDC + entresol (or low 1er), horizontal refends, 1853–1902 | H (both reports; measured strip) | Chaînes on the end-bay piers 0.25. |
| O3 | **Grouped and individual balconies on the letting floors** after c.1860 | H (both; bd Voltaire, Châteaudun) | R2. |
| O4 | **Pre-1850 vocabulary**: plaster, persiennes, a bandeau at every floor, many near-equal storeys, light wrought balconnets, a small comble | M (observer R3.5, R4.5, R5.5, R6.3; adversary O11) | R7. |
| O5 | **Post-1882 / 1884 vocabulary**: oriels (from 1882, ≤ 0.40 m, starting at the noble floor), stone balustrades at the noble and top floors, lucarnes passantes, a sculpted central lucarne, iron cresting | M (observer R4.6, R5.6, R7.6; B28–B30 all 1896–99) | R17. |
| O6 | **Persiennes** | M (both) | Pre-1850 0.9; ordinary/modest 0.5; comfortable 0.35; grand 0.15. |
| O7 | **The raised residential RDC** with soupiraux and a porte cochère swallowing RDC + 1er (residential avenues from 1860) | M (observer R3.8) | Goes with S5 and G6. |
| O8 | **Sculpture by date**: restrained before 1865; mascarons on keystones and consoles 1865–85; caryatids on grand houses | M (observer R5.4) | Low cost if the kit has a mascaron mark; otherwise later. |
| O9 | **Signage on the entresol and the noble filant** on commercial streets | M (observer R8.1, Marville photos) | Nice to have; low priority for an expert's acceptance. |
| O10 | **Neighbours share lines, not axes** | H (observer R1.8) | A street-level concern, not a single-house one. |

---

## 4. Ranked recommendations

Ordered by how much each moves an expert toward accepting the drawings,
then by cost. Weights are for the coming per-house (**house**) and per-floor
(**floor**) draws. Where the evidence gives counts, the weight follows them
and I say so; otherwise the weight is my reading of the reports and marked
*judged*.

**R1. Every étage window is a porte-fenêtre with a garde-corps.** Fixes B4,
W3, D1. Cost: one rule (set `sill = 0.1` and `garde_corps = true` on every
principal and upper cell); the dead production at line 107 then fires. Evidence: all
17 adversary buildings, observer R5.1, my three photos. *No weight: 1.0.*

**R2. Letting-floor balconies by date (floor draw).** Fixes O3. Cost: one
rule plus a grouped-balcony insert.

| period | garde-corps only | grouped balcony over 2–3 bays | balcony per window |
|---|---|---|---|
| before 1860 | 1.0 | 0 | 0 |
| 1860–1884 | 0.6 | 0.25 | 0.15 |
| 1884 on | 0.45 | 0.35 | 0.2 |

*Judged* from observer R4.4 and the photos (bd Voltaire, Châteaudun,
Étienne-Marcel grouped; rue Blanche, Opéra 38 rails only). Grouped
balconies should be symmetric about the centre.

**R3. Class ladder for the noble floor.** Fixes S6, D6. Cost: one table.
`principal = { grand = 4.2, comfortable = 3.8, ordinary = 3.4, modest = 3.0 }`
(Daly medians; ordinary interpolated). Per house, draw within
grand [3.9, 4.3], comfortable [3.2, 4.35], modest [3.0, 3.1] (Daly ranges).
Also `upper = { grand = 3.45, comfortable = 3.1, ordinary = 3.0, modest = 2.9 }`.

**R4. What sits between the ground storey and the noble floor (house draw).**
Fixes S4, S5, B3, D6. Cost: one draw and one storey kind.

| class, ground | entresol (3.0 m) | low dressed 1er (3.4 m) | nothing |
|---|---|---|---|
| grand, shop | 0.6 | 0.4 | 0 |
| grand, house | 0 | 0.8 | 0.2 |
| comfortable, shop | 0.9 | 0.05 | 0.05 |
| comfortable, house | 0.3 | 0.5 | 0.2 |
| ordinary, shop | 0.8 | 0 | 0.2 |
| ordinary, house | 0.2 | 0.2 | 0.6 |
| modest, any | 0.3 if shop | 0 | 0.7 (1.0 for a house) |

From counts where there are some: Daly Deuxième 9 of 10 entresols, Première
0 of 4 (residential), Troisième 0 of 2; grand commercial photos 2 of 2 with
an entresol; the rest *judged*. Also set `house_ground = 4.0` (S2). The rule
for balconies follows: **no projecting balcony with its deck under 6.0 m**
(1823; `reglement.py`). Where the noble deck would be under 6 m, it gets
garde-corps only.

**R5. Window size: absolute width, class in the height.** Fixes W1, W4, D7.
Cost: two expressions. `light_width = 1.2` (house draw 1.1–1.3; Daly n = 16).
Noble `light_height = { grand = 2.9, comfortable = 2.25, ordinary = 2.15, modest = 2.1 }`
(Daly medians). Letting floors at aspect 1.9 (Daly 1.8–2.0), capped at
`h − 0.1 − 0.6`. Top storey at 0.7 of the noble light (observer R3.4).

**R6. Filants by class and date (house draw).** Fixes B1, B2, D8.

| | noble + top filant | top filant only | none (garde-corps only) |
|---|---|---|---|
| grand / comfortable, 1853 on | 0.85 | 0.1 | 0.05 |
| ordinary, 1853 on | 0.5 | 0.35 | 0.15 |
| modest, 1853 on | 0.1 | 0.4 | 0.5 |
| any, before 1850 | 0.1 (a thin one) | 0.2 | 0.7 |

Then the noble filant's extent: full width 0.65, central bays 0.35 (3 of ~10
dated cases central, plus rue Blanche; *judged* for the rest). Counts behind
the top rows: the adversary's 8 of 8 wide-street Second Empire buildings;
Daly's Troisième 1 of 1 with no balcony; the observer's "a filant at the attic
level is the most likely single balcony on an ordinary house" (R4.7).

**R7. Before 1850, and on modest houses: plaster, persiennes, bandeaux (house draw).**
Fixes X4, O4, O6, D8. Cost: one date-gated rule layer.
- `wall_material`: before 1850, plaster 0.85, stone 0.15; modest from 1850 on, plaster 0.4.
- A bandeau at every floor before 1850 (1.0); from 1853, only the three strong horizontals (S11).
- Persiennes: O6 weights.
- Comble before 1850: a single slate pitch with a row of small dormers (0.6), or a mansard (0.4).

**R8. The comble is a type (house draw), and the pre-1884 one obeys 45°.**
Fixes C2, C3, C4, D2.

| period | one level, 3.2 m | two levels, 6.8 m |
|---|---|---|
| 1783–1884, cornice 17.55 m on a street ≥ 20 m | 0.6 | 0.4 |
| 1783–1884, otherwise | 0.9 | 0.1 |
| 1884 on | 0.4 (at ≈ 4.0 m) | 0.6 (at ≈ 6.0–7.0 m, within the 8.5 m arc) |

Daly: 2 of 15 measured combles hold two storeys, both on 17.55 m Sébastopol
houses. The post-1884 weights are *judged* (observer R7.6; the arc exists to
allow this). Before 1884, pitch 45° (or brisis 60° to 1.2 m and then a ~20°
terrasson inside the 45° line). A two-level comble gets the upper row of
tabatières.

**R9. Dormers (house draw).** Fixes C5, C6.
- **Count.** Grand/comfortable: every axis 0.75, every other axis 0.25. Ordinary/modest: every axis 0.4, every other 0.45, fewer and symmetric 0.15. (Adversary counts: 6 per-axis against 5 fewer, split by class as here; observer R7.2.)
- **Form.** Grand/comfortable 1855–84: pedimented 0.35, segmental zinc 0.3, oeil-de-boeuf 0.2, plain box 0.15. Ordinary/modest: plain box 0.5, segmental zinc 0.3, capucine 0.2. After 1884, grand: stone lucarne passante 0.3, pedimented 0.3, segmental 0.25, oeil-de-boeuf 0.15. (The tally under C6, plus observer R7.3 and R7.6.)
- **Roof lights** between dormers on "every other" fronts (bd Voltaire, rue Blanche).

**R10. The surround hierarchy (floor rule).** Fixes W5. A decreasing
ladder from a single peak (observer R5.2, H in the photos):

| floor | comfortable / grand | ordinary | modest / before 1850 |
|---|---|---|---|
| noble | chambranle + frieze + cornice on consoles (+ pediment, R11) | chambranle + flat hood | thin band |
| next | chambranle + flat hood | chambranle | thin band |
| next | chambranle (keystone 0.5) | chambranle | none |
| top | plain chambranle | none | none |

**R11. Pediments (house draw, comfortable/grand).** Fixes W6.
Placement: noble floor 0.5, the floor above the noble 0.2, none (shells,
cartouches or consoles) 0.3. Grand: alternating triangular/segmental 0.5,
all triangular 0.3, all segmental 0.2. Evidence: 2 on the noble, 1 a floor up,
3 with none among the photos both reports and I looked at; *judged* beyond
that.

**R12. Door type and height (house draw).** Fixes G3, G5, G6, D5.

| class | porte cochère | porte piétonne |
|---|---|---|
| grand | 1.0 | 0 |
| comfortable | 0.35 | 0.65 |
| ordinary | 0.15 | 0.85 |
| modest | 0 | 1.0 |

Daly: Première 4 of 4, Deuxième 3 of 11, Troisième 0 of 2. Comfortable is
nudged up to 0.35 because the photos show more arches (rue Blanche,
Étienne-Marcel, Châteaudun).
The piétonne is 1.75 m wide, or 1.36 m for modest. When there is an entresol
or low 1er above, a porte cochère rises through it with weight 0.6 (≈ 5.0 m to
the crown, round arch, keystone), or stops at a lintel under its own cornice
with weight 0.4. Daly has 2 of 7 cochères over 5 m; the photos have 4 of 5.

**R13. Entrance position (house draw).** Fixes G2. Cost: one draw.
- **Odd axis count:** middle 0.55, end bay 0.3, second bay 0.15.
- **Even axis count:** end bay 0.4, second or third bay 0.6. Never "the middle bay", which does not exist.
- **Modest:** end bay 0.6, otherwise as above.

From the §0 tie-break: 5 central cases, all odd, against 7 off-centre, mostly
even, corner or modest.

**R14. Fix the envelope.** Fixes E3, E6, E8. Cost: small, and it restores the
file's one stated guarantee.
1. Let `lettings` reach 0 and shed the entresol, then shrink the noble floor, when the base still overflows. Extend the test to 7 m streets.
2. Step limits at `7.79 / 9.74 / 19.99`, in this file and in `reglement.py` (decree wording, recalled, M).
3. 1859–1884: at most five square storeys above the RDC, entresol included (recalled, M).
4. Check the 1884 middle bands against the decree; refuse `year >= 1902` until Bonnier is modelled.

**R15. Party-wall souches and ridge stacks.** Fixes C8, D3. Cheap and very
visible on the skyline: party-wall stacks 1.5–2.5 m wide (house draw), rising
1.5–3 m above the roof; one ridge stack per ~4 axes on fronts of 8 axes or
more (bd Voltaire).

**R16. Rusticated socle, and the shop variants (house draw).** Fixes O2, G1,
D4. Bossage on RDC + entresol or low 1er: 0.8 from 1853 (both reports; most
photos), 0.2 plain. End-bay chaînes: 0.25. Shop type: stone piers per bay
0.6, a glazed shop entresol over a double-height front 0.25 (rising to 0.4
after 1870, observer R3.6), a wooden devanture 0.15 (0.8 before 1850).

**R17. After 1882 and 1884.** Fixes O5, D9. On grand houses: oriel from the
noble floor (≤ 0.40 m) at 0.1 for 1884–95 and 0.3 from 1895; stone
balustrades at the noble and top floors, replacing the iron filant, 0.4 from
1885; the +1 storey on wide streets comes from E3 and the arc comble. Low
confidence: the dated evidence is B28 and B29 (1896, 1899) and the 1885 and
1891 plates.

**R18. Corners.** Fixes O1, X6. The largest omission, but also the
largest piece of work. Pan coupé of one bay 0.5, of two bays 0.2, rotonde
0.25, prow 0.05 (*judged* from observer R10.2's order). Lines wrap unbroken,
balconies on more floors at the corner, a raised cap; after 1884, a tourelle
or dome 0.5 on grand corners.

**R19. Bay pitch and rhythm.** Fixes X1, X3. `bay = [2.1, 2.8, 3.5]` (Daly),
`[2.1, 2.4, 2.8]` before 1850. Grouped rhythm: 0.25 from 1870, 0.1 before.

### If only five changes go in

R1 (rails), R3 + R4 (the class ladder and the base), R5 (window height),
R8 (comble at 45°, and two-level combles) and R14 (the envelope bug). They are
all small, and together they fix every **D** in §1 except B1, which R6
fixes next.

---

## 5. Confidence and what would change these grades

- The decree wording in E3 and E6 is from memory; I couldn't reach Légifrance,
  Gallica or Wikipedia from here. Reading the 27 July 1859 and 23 July 1884
  texts would settle E3, E4 and E6. If the 1884 decree gives 20 m from 12 m
  streets, the strip's 1890 case gains a storey.
- Class weights rest on Daly's 16 buildings (Deuxième n = 10 is solid;
  Première and Troisième are thin) and about 35 distinct photographed
  buildings across both reports, with known biases toward the 9e, 8e, 1er and
  the boulevards. Modest 1853–1902 houses are under-sampled, so R4, R6 and R9's
  modest rows are the softest numbers here.
- Live Commons sampling was blocked by rate-limiting, so I couldn't test the
  corpus's own selection bias.
