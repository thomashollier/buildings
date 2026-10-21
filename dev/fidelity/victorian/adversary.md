# San Francisco Victorian: adversarial fidelity review

Model under test: `src/buildings/typologies/victorian/victorian.toml` (rules), `grammar.py` (gable, turret and stoop outlines), `kit.write_stoop` in `src/buildings/typologies/common/kit.py`, and the render `docs/strips/victorian.png` (Italianate 1872 and 1878, Stick 1883 double bay and 1886 side yard, Queen Anne 1892 extra floor and 1895 turret).

## Method, and its main limit

**I could not look at photographs.** This session's network policy refuses `commons.wikimedia.org` and `upload.wikimedia.org`, along with loc.gov and flickr, from both the shell and the web fetcher. That rules out the Commons API method I was asked to use. So that this review is not mistaken for a photographic one:

- **Primary evidence (read by me):** National Register of Historic Places nominations for 14 individually listed San Francisco houses, and the Liberty Street Historic District nomination with its 51-entry inventory (about 30 contributing 1863-1896 houses). Also SF Planning Preservation Bulletin 18 and the SF Planning Alamo Square walking tour. These are written facade descriptions by architectural historians, usually made from site visits and the nominations' own photo sets. They are strong on **kinds and counts**: bay shape, number of storeys, door type, window heads, roof form, lot size. They are weak on **dimensions**, giving lot widths and the odd ceiling height but almost never storey heights.
- **Secondary evidence (not seen by me):** the blind observer report `dev/fidelity/victorian/observer.md`. It scaled 31 Commons photographs. I quote its measurements only where the texts give none, and mark them **[obs]**. They are someone else's photo readings, so they get lower confidence than the texts.
- Metric estimates use storey ≈ 3 m, door leaf ≈ 2.2-2.7 m, riser ≈ 18 cm, and 1 ft = 0.305 m. A 12 ft ceiling plus floor structure gives a floor-to-floor of about 4.0 m.

**Next step:** a round with Commons access should re-run C6-C9, C15 and C19-C22 against straight-on photos. Those are the dimension claims, where text evidence is thinnest.

Verdict counts (a split verdict is counted by its first rating): 10 SUPPORTED, 10 PARTLY, 7 CONTRADICTED, 2 UNTESTABLE.

---

## 1. Buildings consulted

| # | Building | Date / style (per source) | Source URL |
|---|---|---|---|
| B1 | Stadtmuller House, 819 Eddy St | 1880, Italianate | https://npgallery.nps.gov/GetAsset/503013b3-d9b7-4645-94e6-d048313eadf7 |
| B2 | 1356-62 Scott St (pair) | Italianate, 1870s | https://npgallery.nps.gov/GetAsset/43194398-7146-4761-bf4b-b2905d3d2513 |
| B3 | 1624 Post St | 1876, Italianate | https://npgallery.nps.gov/NRHP/GetAsset/NRHP/73000443_text |
| B4 | Henry Geilfuss House, 811 Treat Ave | 1882, bay Italianate | https://npgallery.nps.gov/GetAsset/4a7ae896-61a8-4610-8f16-f501d5c91b4a ; https://demo2.parks.ca.gov/pages/1067/files/CA_San%20Francisco%20County_Geilfuss%20House_Nom.pdf |
| B5 | House at 584 Page St | 1894, Queen Anne (builder Daniel Einstein) | https://npgallery.nps.gov/GetAsset/599a814c-f99f-47ff-a5d9-690415d468b4/ ; photo captions https://npgallery.nps.gov/GetAsset/1dad6212-3bab-4ede-ab72-32b02571d29b |
| B6 | 70 Buena Vista Terrace (De Lano House) | 1884, Italianate with Stick details | https://npgallery.nps.gov/GetAsset/7e2a3583-4aa8-4981-ac50-6cae2bbe396f |
| B7 | Burr House, 1772 Vallejo St | c.1878, Italianate with mansard | https://npgallery.nps.gov/GetAsset/f5bc3307-5627-4f00-aa5c-fc39f0ec4325 |
| B8 | Dallam-Merritt House, 2355 Washington St | c.1870, Italianate with mansard | https://npgallery.nps.gov/GetAsset/c65962ef-e086-4c79-885a-45e2101f4730 |
| B9-B10 | Albert Wilford Houses, 2121 and 2127 Vallejo St | 1890, Queen Anne (developer pair) | https://npgallery.nps.gov/GetAsset/251f9576-64d7-4643-8548-fed5f68e65fb |
| B11 | John Spencer House, 1080 Haight St (corner) | 1895, Queen Anne | https://npgallery.nps.gov/GetAsset/3bb565bb-c044-4408-a986-6c711bc7edb7 |
| B12 | C. A. Belden House, 2004 Gough St | 1889, Queen Anne | https://npgallery.nps.gov/GetAsset/fe695204-732a-4faf-8e04-2d408201fa6c |
| B13 | John McMullen House, 827 Guerrero St | 1881 Stick, remodelled 1890 Queen Anne | https://npgallery.nps.gov/GetAsset/0af86b94-e765-4d32-8121-ee65c6eb459b |
| B14 | House at 1254-1256 Montgomery St | 1865, Italianate | https://en.wikipedia.org/wiki/House_at_1254%E2%80%931256_Montgomery_Street |
| B15 | Liberty Street Historic District, 51 entries (37 contributing) | 1863-1913 | https://npgallery.nps.gov/GetAsset/a4288dad-64d1-4e04-880f-18f56396bb71/ |
| B16 | 710-720 Steiner St ("Painted Ladies") | 1892-96, Queen Anne (Matthew Kavanaugh) | https://default.sfplanning.org/Preservation/walking_tours/Walking_Tour_ALAMO_SQUARE.pdf ; https://en.wikipedia.org/wiki/Painted_ladies |
| B17 | Mohrdick House, 1021 Hayes St | 1891, Queen Anne | Alamo Square walking tour (above) |
| B18 | 719 Scott St | 1880 (per tour), Queen Anne | Alamo Square walking tour |
| B19 | Double house, 881-887 Fulton St | 1877, Italianate (John Hooker) | Alamo Square walking tour |
| B20 | Westerfeld House, 1198 Fulton St | 1889, "Stick Italian Villa" (Geilfuss) | Alamo Square walking tour |
| Style dates | SF Planning Preservation Bulletin 18 | — | https://sfplanning.org/sites/default/files/documents/preserv/bulletins/HistPres_Bulletin_18.PDF |

That is 19 individually described buildings, plus about 30 contributing Victorians in the Liberty inventory. The Liberty entries are cited as **L#** with the inventory number.

---

## 2. Claims table

| # | Claim | Source | Verdict |
|---|---|---|---|
| C1 | Type is a function of date alone: Italianate < 1880, Stick < 1888, Queen Anne after | toml:45, toml:7 | **PARTLY** (sequence right; hard cuts miss about 1 in 6 near the boundaries) |
| C2 | Lot is 25 ft (7.62 m) | grammar.py:25 | **SUPPORTED** |
| C3 | Layout: one bay zone (55%) + one entry zone (45%), mirrored by seed | toml:46, 50, 72-79 | **SUPPORTED** (form) / **PARTLY** (no flat front, no flats) |
| C4 | Two bays flanking a central entry once the front is ≥ 8.4 m (27.6 ft) | toml:46, 80-84 | **PARTLY** (the form is real; the threshold is far too low) |
| C5 | Side yard of 1.3 m with a fence on a quarter of the single-bay lots ≥ 6.8 m | toml:33, 47, 58 | **UNTESTABLE** (frequency) / plausible |
| C6 | Raised basement 2.1 m, parlour floor 3.6 m, chamber floor 3.3 m | toml:27 | **PARTLY** (basement OK; upper floors about 10% low) |
| C7 | Standard house = basement + 2 storeys | toml:27, 179 | **SUPPORTED** |
| C8 | A third storey on one seed in three, and always on `grand` | toml:32, 46 | **CONTRADICTED** (frequency) / SUPPORTED for `grand` |
| C9 | Overall height to the top of the false front ≈ 10.6 m on 7.62 m | derived from toml:27, 54 | **PARTLY** (likely 10-20% squat) |
| C10 | The bay starts at the parlour floor, over a flush basement with a small window | toml:101-106, 190-191 | **SUPPORTED** (original state) |
| C11 | The bay rises through *every* storey above the basement, including a third | toml:108-112 | **PARTLY** (2 storeys standard; 1-storey and parlour-only bays common) |
| C12 | Bay plan by type: Italianate slanted (side share 0.20), Stick square (0.07), Queen Anne slanted (0.20) | toml:29, 107 | **SUPPORTED** (Italianate, Stick) / **PARTLY** (Queen Anne) |
| C13 | A bay front face over 2.2 m holds a pair of sashes | toml:205-206 | **CONTRADICTED** for slanted Italianate bays / SUPPORTED for square Stick bays |
| C14 | One window in each side face | toml:108-112, 199 | **SUPPORTED** (slanted) / strip issue for square bays (S4) |
| C15 | Sash nearly fills the storey (sill 0.55, head 0.55 below the next floor) | toml:199 | **SUPPORTED** (shape) / UNTESTABLE (exact values) |
| C16 | Window heads: Italianate segmental with keystone and moulded architrave; Stick flat with architrave; Queen Anne flat, no surround | toml:196-199 | **SUPPORTED** (Italianate, Stick) / **PARTLY** (Queen Anne) |
| C17 | A storey-high entablature (0.32 m) caps the bay at every floor | toml:113 | **PARTLY** |
| C18 | Corner boards at every arris of the bay | toml:31, 114-116 | **PARTLY** (Italianate uses colonnettes; facade corners are left bare) |
| C19 | One flush door, 1.1 m wide, with transom; segmental head in the Italianate | toml:209-214 | **CONTRADICTED** (Italianate doors are paired, and Stick/Queen Anne entries are recessed porches) |
| C20 | One window over the door | toml:122, 199 | **SUPPORTED** |
| C21 | Stoop: 8 risers to 2.1 m, as wide as the entry zone less 0.5 m, of stone | toml:57; kit.py:461, 470 | **CONTRADICTED** (riser, width, material) |
| C22 | Italianate and Stick end in a false front: 0.5 m frieze + 0.6 m bracketed cornice, 1.6 m in all | toml:54, 85-88, 136 | **SUPPORTED** (existence) / PARTLY (Stick gablet missing) |
| C23 | Queen Anne ends in a front gable 3.4 m tall over the full front, 0.25 m eaves, one attic window ≤ 1.8 m wide | toml:54, 134-135; grammar.py:46 | **PARTLY** |
| C24 | Turret only on `comfortable`/`grand` Queen Annes; it rises out of the bay through the top floor and a storey of its own, under a cone | toml:52, 55-56, 140-143; grammar.py:59 | **PARTLY** (bay-turrets on mid-block builder houses are real) |
| C25 | One paint per house from sage / blue / cream / rose | toml:30, 179; grammar.py:35 | **CONTRADICTED** (neither period nor modern practice) |
| C26 | Wall is clapboard | toml:30 | **PARTLY** (channel rustic siding; Queen Annes add shingles) |
| C27 | Wealth (`klass`) changes only the turret and the third storey | toml:46, 52 | **CONTRADICTED** (wealth drives portico, width, quoins and towers) |
| C28 | Numbers are inferred from Alamo Square and the Mission | toml:8 | **UNTESTABLE** (provenance note) |
| C29 | Queen Anne uses the same 3-face slanted bay and flat sash as the Italianate, only without surrounds | toml:29, 199 | **CONTRADICTED** (the main Queen Anne bay is often round, a tower, or square-over-slant) |

---

## 3. Verdicts with evidence

### C1 Type by date (toml:45)
Bulletin 18 gives overlapping ranges: Italianate **1865-1885**, Stick/Eastlake **1880-1900**, Queen Anne **1885-1910**. The Alamo Square tour gives the same order of bay shapes: "angled bays" in the 1870s and early 1880s, "rectangular muscular bays" in the 1880s, "curved bays" in the 1890s.

I scored the model's cut against every dated house with a stated style: B1, B3, B4, B6-B13, B18, B19, and the 30 contributing Liberty Victorians. **Misses:**
- **B1 Stadtmuller, 1880, Italianate.** The model gives Stick, because the cut is `year < 1880`.
- **B4 Geilfuss, 1882, angled-bay Italianate.** The model gives Stick.
- **B6 70 Buena Vista, 1884, Italianate.** The model gives Stick, although this house does have a square bay.
- **L38, 1884, "Late Italianate".** The model gives Stick.
- **L1, 1889, Stick-Eastlake.** The model gives Queen Anne.
- **B18 719 Scott, 1880, Queen Anne (tour date; doubtful).** The model gives Stick.

About 6 of 41 are wrong (85% right), and every miss falls within 4 years of a cut. **PARTLY.** The ordering is right, but the cut should be a probability ramp over about 1878-1886 and 1886-1892, not a step. **Confidence: high.**

### C2 25 ft lot (grammar.py:25)
- Liberty: lots "typically about 25 feet wide and 115 feet deep".
- 584 Page: deed 25 × 100 ft.
- 70 Buena Vista: 25 × 115 ft.
- McMullen: original lot 25 × 100 ft.
- Wilford: facade "about 23 feet wide".

**SUPPORTED. High.**

### C3 Bay zone + entry zone (toml:50, 72-79)
Two-column asymmetric fronts:
- 1356-62 Scott: "two-story tiered projecting angled bay windows ... on the left side of each facade", with the entrance to the right.
- 1624 Post: "two-story angled bay on the east side" and "a single doorway".
- Geilfuss: "full-height angled bay at the north", porch to the south.
- 70 Buena Vista: entrance "on the right-hand side".
- 584 Page: tower bay at one corner, entry arch beside it.

[obs] gives a bay share of 40-56%, so the model's 55% sits at the top of that range. **SUPPORTED** for the form.

Two common alternatives are missing:
- **The flat-front Italianate.** Bulletin 18 says it was "popular during the 1860s and the 1870s". Liberty L16 has "two curve-pedimented windows per floor instead of bay", and L35 has "no bay". The model has no bayless type.
- **Flats with one door per unit.** L6: "two entries, one on each side of facade". About half the Liberty contributors are listed as flats or apartments, though many of those were converted later.

**PARTLY** for coverage. **High.**

### C4 Double bay at ≥ 8.4 m (toml:46)
The symmetric two-bay form is real:
- L30 "pedimented portico between pair of bays";
- L31 "large symmetrical house, portico between bays";
- Burr "two angled bay windows" on a **91 ft** lot.

But in Liberty only **3 of 51 lots are "more than double width"**, and those are the houses with this form. The model switches to it at 27.6 ft, which is the width of an ordinary Western Addition lot. Every 27.5-30 ft house in the sample (B2, B3, B6) is single-bay. The model also gives the symmetric form to a **Stick** house (strip panel 3). All the documented examples are Italianate, and they always have a **portico** at the centre, which the model never draws.

**PARTLY.** The threshold should be about 12-15 m (40-50 ft) or `klass == grand`. **Medium-high.**

### C5 Side yard (toml:47, 58)
Rows are mostly continuous:
- L24 "party wall";
- L7 "party wall with #8";
- 584 Page "nearly touches the neighboring building to the east", with "a deep notch" (a light well) on the other side.

Side yards appear on large lots (Geilfuss, 60 ft; Burr). A fenced 1.3 m gap at the street on a 25 ft lot is plausible, but I found no frequency evidence. **UNTESTABLE.**

### C6 Storey heights 2.1 / 3.6 / 3.3 m (toml:27)
- **Basement 2.1 m:** [obs] puts it 1.8-2.7 m above the sidewalk from stoop counts. The texts call it a "raised basement" (B6) and "almost fully exposed" (B8). OK.
- **Parlour floor 3.6 m:** Spencer has "twelve-foot, coved ceilings" on the first floor, which is about 4.0 m floor to floor. That is a rich 1895 house, but [obs] also scales ordinary parlour floors to 3.8-4.6 m. 3.6 m is about 10% low.
- **Chamber floor 3.3 m:** [obs] gives 3.4-4.0 m.

**PARTLY.** Raise the floors to about 4.0 and 3.6 m. **Medium-low**, as the only direct figure is one ceiling height.

### C7 Basement + 2 storeys (toml:27)
Liberty: of about 30 contributing 1863-1896 houses, all but three are "2 stories & basement". Queen Annes add "& attic" (L4, L9, L20). Also 1356 Scott, 1624 Post, the Wilford houses and 70 Buena Vista are "two-story". **SUPPORTED. High.**

### C8 Third storey on one in three (toml:46)
The texts:
- Liberty: **1 of about 30** (L31, a "large" double house) has 3 storeys over the basement.
- B7 and B8 have a third storey only as a **mansard** over a bracketed cornice, not as a third bay floor.
- B11 is a corner mansion with a hip-roof third storey.

So a third storey belongs to the large or rich house, which supports the `klass == 'grand'` half of the rule. `seed % 3 == 2` gives it to a third of ordinary houses. Strip panel 5 ("Queen Anne 1892, extra floor", `ORDINARY`) is exactly the case the evidence says is rare. A 3-storey bay under a flat cornice is the **Edwardian** flat type (1900-1915).

**CONTRADICTED** (the seed clause). **High.**

### C9 Overall proportion
Model: 2.1 + 3.6 + 3.3 + 1.6 = **10.6 m** to the top of the false front on 7.62 m, a ratio of 1.39.
- With the C6 correction: 2.1 + 4.0 + 3.6 + 1.4 ≈ 11.1 m, a ratio of 1.46.
- [obs] measures 1.6-1.9 from three straight-on photos, perhaps including a taller basement.
- Liberty: "tall and narrow" proportions.
- Geilfuss is "as wide as it is tall", but on a 60 ft lot.

**PARTLY.** The model is probably 5-20% squat; strip panels 1, 2 and 4 read as broad. **Medium-low.**

### C10 Bay starts at the parlour floor (toml:101-106, 190)
- Liberty: "garages ... usually added under the bay", which means there was once wall under the bay.
- 1624 Post: the bay "reaches almost to the ground".
- 1356 Scott: bays "from ground level to the roof cornice". Read with the "raised basement" type, I take this as the bay face continuing flush down to grade.

The model's flush basement under the bay is right. Its single small basement window is UNTESTABLE from these texts. Today a **garage** fills this position on about half the houses, according to Liberty and [obs]. **SUPPORTED** for the original state. **Medium-high.**

### C11 Bay height (toml:108-112)
- Bulletin 18: the bay window type "had a dominant **two-story** bay window".
- Two storeys: 1356 Scott, 1624 Post, 70 Buena Vista ("double-height").
- **One storey only:** L7 "first-story bay"; L42 "one-story bay"; 584 Page "polygonal bay window projects from the second storey only"; L11 and L33 (1908-10).
- Burr: bays on floors 1-2 only, and the third storey is a mansard.

The model runs the bay through all non-basement storeys, so a third storey gets a 3-storey bay (strip panel 5). **PARTLY. High.**

### C12 Bay plan by type (toml:29)
- **Italianate:** Liberty "half-octagonal bays rising into the cornice"; 1356 Scott, 1624 Post and Geilfuss all "angled"; B8 "semioctagonal". **SUPPORTED.**
  - Exceptions: L38 (1884, "Late Italianate, rectangular bay") and B6 (1884, "rectangular bay ... a form appropriated from the Stick Style").
- **Stick:** Liberty "rectangular bays"; Bulletin 18 "box-bay windows"; the tour "rectangular muscular bays". **SUPPORTED.**
- **Queen Anne:** Liberty "round, part-hexagonal, or rectangular"; L9 "semicircular and trapezoidal bays"; 584 Page round tower bay plus a polygonal bay; Spencer "square at the first story and change to partially octagonal forms at the second"; 719 Scott "rounded corner bay window"; the tour "curved bays". The model's 0.20 share draws every Queen Anne as an Italianate half-octagon. **PARTLY** (see C29).

A 0.20 share for a 45° half-octagon is plausible. If the bay zone is 4.2 m and the side faces show as 0.84 m each, their true width is 1.19 m. [obs] gives 0.8-1.1 m true width, so the sides are a touch wide. **Medium.**

### C13 Pair of sashes in the front face (toml:205)
The texts are unanimous that slanted Italianate bays have **one window per face**:
- 1356 Scott: "three windows per story";
- 1624 Post: "each face of the bay has one window per storey";
- Dallam-Merritt: "one window per face on each floor";
- Geilfuss: "three upper-level windows".

With the model's numbers, an Italianate front face is 4.19 × 0.6 = 2.51 m, which is over the 2.2 m threshold. So every Italianate bay gets a mullioned pair (strip panels 1-2 show two round-headed lights). For square Stick bays, 70 Buena Vista has "paired double-hung windows", so the rule is right there.

**CONTRADICTED** for the Italianate. The front face itself is too wide: [obs] gives 1.3-1.7 m. **High.**

### C14 One window per side face
Right for slanted bays (C13 sources). For Stick, see S4. **SUPPORTED.**

### C15 Sash fills the storey (toml:199)
The rule gives a parlour light 2.5 m tall and chamber 2.2 m. The texts describe "tall, narrow" windows (Liberty) but give no numbers. [obs] gives parlour windows of about 2.9 m and sills 0.4-0.6 m. **SUPPORTED** in shape. The exact numbers are UNTESTABLE here, but the C6 fix would make them about 0.4 m taller.

### C16 Window heads (toml:196-199)
- **Italianate**, segmental:
  - 70 Buena Vista "segmentally arched windows with moulded surrounds and keystones";
  - Geilfuss "flattened arch upper sash", keystones;
  - 1356 Scott "slightly round-headed ... floral ornament ... simulating a keystone";
  - Burr "paired segmental arched windows".
- **Italianate**, round-headed: 1624 Post; 881 Fulton "framed arched windows with hoods".
- **Hoods and pediments** are the norm and the model has none: Dallam-Merritt "bracketed segmental pediments"; Stadtmuller "dentillated pediments"; L16 "curve-pedimented windows"; 1624 Post "flat projecting cornice" over each opening.
- **Stick:** flat heads (Bulletin 18; [obs]).
- **Queen Anne:**
  - Spencer has radiused lower windows "with stepped arches" and carved casings with pilasters;
  - McMullen has transoms ("one large lower sash topped by four smaller transoms");
  - Palladian windows: L19, L20;
  - stained glass: Wilford, Spencer.
  
  "Flat, no surround" is the plainest builder case.

**SUPPORTED** (Italianate, Stick) / **PARTLY** (Queen Anne). The missing hoods are listed under O3. **High.**

### C17 Bay entablature at every floor (toml:113)
1356 Scott has "a small bracketed cornice at the first-story ceiling level, and a larger projecting bracketed cornice" at the roof. So an intermediate cornice exists. In real houses, the top one is the main cornice breaking forward over the bay ("bays rising into the cornice", Liberty), not a separate 0.32 m band under it. Geilfuss and [obs] also show a panelled apron or spandrel between floors, which the model lacks. **PARTLY. Medium.**

### C18 Corner boards (toml:114-116)
- On Italianate bays the arrises carry **colonnettes**: 1356 Scott "pipestem colonnettes"; 70 Buena Vista "engaged colonettes at the bay corners"; Burr; Geilfuss; L39.
- Geilfuss has carved corner boards.
- Facade corners carry **pilasters or quoins**, which the model omits: 1356 Scott "larger split pilasters at the building corners"; Geilfuss quoins; L22 quoins.

**PARTLY. High.**

### C19 Door (toml:209-214)
- Bulletin 18 on the Italianate: "doors are **paired** and capped by a hood".
- Paired doors in Italianate examples: Geilfuss "double front entry doors ... upper glazed transom"; 70 Buena Vista "a pair of windowed doors with a transom"; Dallam-Merritt and Burr "double ... front door"; 1356 Scott "tall, narrow double doors".
- **Hoods/porticoes:** 1356 Scott "pediments supported by fluted brackets"; Stadtmuller portico with Corinthian columns; L2, L5, L8, L9, L22, L30, L31, L49.
- **Recessed porches:** 70 Buena Vista "set in a recess behind a small porch"; Geilfuss; L18 "deeply recessed arched entry"; L51 "entry recessed"; 584 Page "round-headed arch"; McMullen "horseshoe-shaped ... arch framing a recessed paneled entryway".

The model draws one 1.1 m flush opening with no hood. A transom is right. A pair of 0.6-0.7 m leaves is 1.2-1.4 m, so 1.1 m is narrow. The segmental head matches B8's "segment-headed" opening.

**CONTRADICTED** (single, flush and unhooded is the exception, not the rule). **High.**

### C20 Window over the door
- 1356 Scott: "a single window with a curved pediment above it";
- 70 Buena Vista: "the window centered above the entrance ... segmentally arched";
- 1624 Post: "the upstairs window above the door has a wooden keystone".

**SUPPORTED** (the pediment is missing; see O3). **High.**

### C21 Stoop (toml:57; kit.py:461-470)
- **Risers:** `n = 8` over 2.1 m gives **26 cm risers**. That is about 1.5× a 17-18 cm stair riser and steeper than any domestic stair. [obs] counts 10-14 risers, which fits 2.1 m at 18 cm (12 risers).
- **Width:** `entry_w - 0.5` = 3.43 - 0.5 = **2.93 m** on a 25 ft lot. [obs] gives 1.1-1.5 m. 70 Buena Vista notes "wide front stairs" as remarkable.
- **Material:** `wall_material = "stone"`. Most period stoops were wood: Geilfuss "wooden staircase"; Burr "wood steps with heavy carved wood balusters". Stone or concrete is a later or rich case: McMullen granite; Wilford's lowest flight "likely original concrete".
- **Form:** the strip draws the stair's stepped side profile, so it reads as a stair running parallel to the facade. The common form is straight and perpendicular to the facade ([obs]), and in elevation it would show its front: a rectangle of treads between railings or newels. Turned and parallel runs do occur: 584 Page "two-legged stair"; Wilford "four flights of steps"; [obs] Liberty Hill. No railing or newel is drawn.

**CONTRADICTED** (riser, width, material). **High** for risers and material, **medium** for width.

### C22 False front (toml:85-88, 136)
- Liberty: "most have corniced false fronts masking gable roofs".
- 70 Buena Vista: "gabled roof is hidden behind a false front ... panels ... separated by large brackets".
- Bulletin 18: "False fronts are also a distinguishing feature".
- Geilfuss: "wide cornice with dentils and paneling between the ornately carved and evenly spaced brackets".
- 1624 Post: cornice brackets "separated by rectangular panels".

The 1.6 m height sits inside [obs]'s 1.1-1.8 m. **SUPPORTED.**

The Stick version should add a **gablet or pediment over the bay**: L28 "pediments over entry and bay"; L29 "arch overhanging bay"; [obs] Walter St and Stick 2023. The model's Stick top is identical to its Italianate one. **High.**

### C23 Queen Anne gable (toml:54, 134-135; grammar.py:46)
Front gables are right (Bulletin 18 "open facing gable roofs"). The details are partly wrong:
- **Pitch:** 3.4 m over a half-base of 4.06 m is about **40°**. [obs] estimates 50-60° on the Steiner row. Text sources give no angle. **Low-medium.**
- **Overhang:** L41 "bracketed overhanging gable"; noehill "often cantilevered out beyond the plane of the wall below"; 584 Page "overhanging eaves". The model's 0.25 m verge over a flat wall drops this.
- **Base:** 584 Page "the two bays support a molded frieze and cornice. Above them rises a gable end"; L9 "gable above cornice". The model has no entablature at the gable's base.
- **Field and windows:** 584 Page "paired attic windows"; L19 Palladian window; Bulletin 18 "decorated verge boards ... sunburst"; Belden "richly carved". The model has a single plain window and an empty field.

**PARTLY. Medium-high.**

### C24 Turret (toml:52-56, 140-143; grammar.py:59)
For the claim:
- The Wilford Houses (B9-B10) are mid-block developer houses about 23 ft wide. A "polygonal bay ... is capped by a square-based domical turret roof". So a turret rising straight out of the bay on an ordinary lot is real.
- 584 Page (25 ft lot, builder Einstein) has a "round tower bay with a conical roof" that "cantilevers out over the basement's southwest corner".
- L20 is a "cone-topped turret".

Against the claim:
- The model ties turrets to `comfortable`/`grand` class. Wilford and 584 Page are builder houses.
- The model's turret is a square box with a pointed roof and a whole extra storey. The documented ones are round (584 Page), polygonal (Wilford, Spencer octagonal), or domical, and the 584 Page tower starts low, at the basement corner.
- Turrets are a minority: 1 of 7 Liberty Queen Annes, and the Steiner row has none.

**PARTLY. Medium.**

### C25 Paint (toml:30, 179)
- One body colour per house from sage/blue/cream/rose, with the trim in one light tone.
- Wikipedia (Painted ladies): repainting "in three or more colors" began in the **1960s** (Butch Kardum, 1963). Many houses had been "battleship gray". The name dates from the 1978 book.
- [obs] (unverified) says period Italianates used light stone-imitating colours.

The model's palette is pastel modern, but only two-tone. It is neither the period look nor the modern painted-lady look it evokes. **CONTRADICTED**, though period colour is not well sourced here. **Medium-low.**

### C26 Siding
- Rustic siding: Liberty "rustic siding covers most buildings"; 70 Buena Vista "channel rustic siding"; 1624 Post "rusticated siding"; Dallam-Merritt "V-grooved rustic siding".
- Rusticated basement or lower floor imitating stone: Geilfuss "wood made to look like cut stone".
- Queen Anne shingle bands: 584 Page "band of geometric-patterned shingles ... wrapping around the tower"; Belden "fish scale shingles"; Wilford.

The model draws clapboard everywhere. **PARTLY. High.**

### C27 What wealth changes (toml:46, 52)
Evidence ties wealth to:
- lot width (double lots: L22, L30, L31; Geilfuss 60 ft; Burr 91 ft);
- the Corinthian portico (Stadtmuller, L22);
- quoins (L22, Geilfuss);
- towers and belvederes (Westerfeld, Spencer, Belden, McMullen);
- mansards (B7, B8).

Builder houses vary ornament, not massing (Wilford pair; Steiner row). The model gives `klass` only the turret and the third storey, so a `grand` Italianate differs from a `modest` one only in height. **CONTRADICTED. Medium-high.**

### C28 Provenance (toml:8)
**UNTESTABLE.** The note says the numbers are inferred, and no source is cited.

### C29 The Queen Anne is a gabled Italianate
Rules toml:29 and toml:199 make a Queen Anne an Italianate bay with flat sash and no surrounds, under a gable. The evidence shows a different massing:
- round or polygonal tower bays (584 Page, Wilford);
- square-over-slant bays (Spencer);
- a "polygonal bay window [on] the second storey only" (584 Page);
- an arched recessed entry (584 Page, McMullen, L18);
- a balcony or loggia over it (McMullen, L18);
- shingle bands;
- bays carrying a frieze under the gable.

None of these is generated. **CONTRADICTED. High.**

---

## 4. What real houses commonly have that the model leaves out

Ranked by how often they appear in the sample.

1. **Door hoods, porticoes and recessed porches** (C19): most of the houses that have an entry description. This is the largest single gap.
2. **Window hoods and pediments** over parlour and upper windows: segmental, triangular, flat on consoles (B1, B3, B8, L12, L16, L38).
3. **Bracket rhythm and frieze panels** in the cornice (B3, B4, B6). The cornice is the house's strongest horizontal, and the model's is plain.
4. **Flats: two (or three) doors** side by side at the top of one stoop (L6, L8; most "pair of flats" entries).
5. **Garage under the bay**: a later alteration, but present on about half of today's houses (Liberty; [obs]). It belongs in a "now" mode.
6. **Flat-front Italianate** with 2-3 openings per floor and no bay (Bulletin 18; L16, L35).
7. **Stoop railings and newels**, and stair landings or turns on setback and hill lots (B5, B9, B13).
8. **Setback / front garden** of about 12 ft in the Mission (Liberty). Zero setback in the Western Addition.
9. **Shingle bands and patterned gable fields** on Queen Annes (B5, B9, B12, B13).
10. **Quoins and corner pilasters** (B2, B4, L22).
11. **Panelled aprons** between bay storeys (B4; [obs]).
12. **Twins and mirrored pairs** built together (L2/L3 "twin", L24 "Siamese twin", B2, B9/B10). A row generator should share a seed between neighbours.
13. **Balconies** over Queen Anne entries (L18, B13, B8).
14. **Mansard third storey** on large Italianates (B7, B8).
15. **Hill stepping**: floors and cornices step with the slope, and the stoop count changes ([obs]; B11 basement taller on the slope side).

---

## 5. What looks wrong in the strip

- **S1. Stoops.**
  - All six are drawn as a stepped side profile.
  - Each is about 2.9 m wide, with eight steep steps.
  - None has a railing.
  - Each reads as a stone stair running along the facade, rather than a wooden stair coming straight at the viewer.
  - This is the most visibly wrong element (C21).
- **S2. Italianate bays carry a mullioned pair in the front face** (panels 1-2). Real slanted bays have one tall window per face (C13).
- **S3. No door hoods anywhere.** The Italianate door is a bare opening, and the Stick and Queen Anne doors sit flush rather than in a porch (C19).
- **S4. Square Stick bays (panels 3-4) show their returns as 0.29 m slivers, each with a ~0.3 m "window".** In true elevation a square bay's returns are edge-on and invisible. At 0.07 share there is no room for a sash. Either drop the side lights (`opening_type = 'none'` when the face is under about 0.5 m) or draw the return as a plain shadow strip.
- **S5. Panel 5 (Queen Anne, ordinary, "extra floor")** is a 3-storey bay under a low full-width gable. That reads as an Edwardian flat with a gable stuck on, not a Queen Anne. The usual builder Queen Anne has 2 storeys + basement + attic (C8, C11, C29).
- **S6. The Queen Anne gables are flat-faced and low (about 40°)**: no overhang over the bay, no frieze at the base, one small window, and an empty field (C23).
- **S7. Turret (panel 6)** is a square, grey-roofed box as wide as the bay (3.9 m) with a full storey above the eave. Documented turrets are round or polygonal, and a cone is drawn as a narrower curved-sash drum (C24). It is plausible in placement, not in form.
- **S8. Italianate and Stick tops are identical**, and the Stick has no gablet or pediment over the bay (C22).
- **S9. Proportions are broad**, especially panels 1, 2 and 4, at about 1.4:1 against a reported 1.6-1.9:1 (C9).
- **S10. Colour:** six pastel bodies with cream trim. They read as modern, but carry only two tones (C25). The siding texture is lap clapboard, not channel rustic (C26).
- **S11. The side-yard fence (panel 4)** is drawn as a short black railing standing alone beside the stoop. It reads as a stray balconette. A board fence or gate as tall as a person, set back with the facade, would read correctly.
- **S12. The bay does not read as projecting** in panels 1, 2 and 5: there is no shading on the side faces, and the cornice does not break forward. So the slanted/square distinction, which is the model's central parameter (toml:4-6), is almost invisible except through the S4 slivers.

What the strip gets right, to be fair:
- the asymmetric bay + entry column;
- the raised basement and the door up a stair;
- false fronts on the Italianate and Stick with a gable on the Queen Anne;
- segmental heads and keystones on the Italianate against flat heads later;
- one window over the door;
- mirroring by seed;
- the Italianate → Stick → Queen Anne order by date.

These are the features that make an SF Victorian recognisable, and they are all present.

---

## 6. Highest-value fixes (by evidence strength × visual impact)

1. Stoop: 12 risers of about 0.18 m, 1.2-1.5 m wide, wood, drawn front-on with newels (C21, S1).
2. Italianate slanted bay: one window per face, front face about 1.5 m (C13, S2).
3. Door: paired leaves about 1.3 m with a transom. Italianate gets a hood on consoles or a portico; Stick and Queen Anne get a recessed porch (C19, S3).
4. Third storey only for `grand` or wide lots; delete the `seed % 3` clause (C8, S5).
5. Double-bay layout only above about 12 m or for `grand`, always with a central portico (C4).
6. A Queen Anne that is its own type: an overhanging gable over a frieze, mixed bay plans, an arched porch, a shingle band, and a turret possible on builder houses (C23, C24, C29).
7. Date cuts as overlapping ramps (C1).
