# Photo check: tie-breaks for the Victorian and Paris gradings, and a corpus audit

Date: 2026-10-21. Follows `victorian/grading.md` §5 and `haussmann/grading.md` §0 and §5,
which could not fetch photos. Nothing in the model or the corpus was changed; this file is
the only addition.

## 0. Access, and how far it got

- **The Commons API works from this environment** once requests carry a descriptive
  User-Agent; without one it answers 429. Image files come from `upload.wikimedia.org`
  (`thumb.wikimedia.org`, which the API now hands back as `thumburl`, is refused by the proxy
  with 403; rewriting the host to `upload.wikimedia.org` works).
- **The image server then throttled this network.** 28 SF photos came through at about one a
  minute. After that, `upload.wikimedia.org` answered `429 ... robot policy` to every request
  for over 40 minutes, and the API itself began to answer 429. The fetch was done at 960 px, a
  standard thumbnail step, one request at a time, so this is a shared-egress limit rather
  than something the script can tune away.
- **What that means for coverage.**

  | Style | Buildings read off photos | Target (15) |
  |---|---|---|
  | SF Italianate (bay and flat-front) | 24 | met |
  | SF Stick / Stick-Eastlake | 8 | short |
  | SF Queen Anne | 4 | short |
  | Paris 1853–1902 (from the corpus, all on Commons) | 21 | met, but the corpus's own bias carries through (§3) |
  | Paris, new ordinary/modest streets (queued: 25 address-level street photos from the 9e, 10e, 11e, 17e, 18e) | 0 | blocked |

  The Stick and Queen Anne verdicts below are flagged **L** where they rest on fewer than 8
  buildings. The queued lists are in §5 so the run can be finished in one go.

**Method.** As in the observer reports: scale from a known width (25 ft = 7.62 m lot) or,
better, from a door leaf (single 1.07 m, 2.4–2.7 m tall), a person (1.7 m, corrected for
standing nearer the camera) or a floor band. Heights are ±10–15 %; counts are exact where
the photo allows. HABS large-format photos have corrected verticals and are the best for
ratios. In a slanted bay seen square-on, a 45° side face shows at 0.71 of its true width.

---

## 1. San Francisco Victorian

### 1.1 Buildings used

New to the fidelity work unless marked *re-measured* (the observer used the photo but did
not take this measurement).

| # | Building | Type, class | Commons file |
|---|---|---|---|
| 1–2 | 1239 and 1245 Scott St, mirrored pair (*re-measured*) | Italianate bay, ordinary | [1239-1245_Scott_St](https://commons.wikimedia.org/wiki/File:1239-1245_Scott_St_(San_Francisco,_California).jpg) |
| 3 | 1249 Scott St, corner | Italianate bay, comfortable | [1249_Scott_St](https://commons.wikimedia.org/wiki/File:1249_Scott_St_(San_Francisco,_California).jpg) |
| 4–5 | 1811 and 1815 Sutter St | Italianate bay, ordinary | [1815_Sutter_NRHP_SF_CA](https://commons.wikimedia.org/wiki/File:1815_Sutter_NRHP_SF_CA.JPG) |
| 6 | 33-35 Beideman St (*re-measured*) | Italianate flat front, double house | [33-35_Beideman_St](https://commons.wikimedia.org/wiki/File:33-35_Beideman_St_(San_Francisco,_California).jpg) |
| 7 | 45-47 Beideman St (*re-measured*) | Italianate flat front, double house | [45-47_Beideman_St](https://commons.wikimedia.org/wiki/File:45-47_Beideman_St_(San_Francisco,_California).jpg) |
| 8 | Brune-Reutlinger House, 824 Grove | Italianate bay, comfortable/grand | [Brune-Reutlinger_House](https://commons.wikimedia.org/wiki/File:Brune-Reutlinger_House,_San_Francisco.jpg) |
| 9 | 2119 Bush St (*re-measured*) | Italianate flat front | [Bush_St.-Cottage_Row_Historic_District_2](https://commons.wikimedia.org/wiki/File:Bush_St.-Cottage_Row_Historic_District_2.JPG) |
| 10–12 | Bush St Cottage Row, 3 bay houses | Italianate bay, ordinary | [Bush_St.-Cottage_Row_Historic_District_3](https://commons.wikimedia.org/wiki/File:Bush_St.-Cottage_Row_Historic_District_3.JPG) |
| 13 | Dallam-Merritt House, 2355 Washington | Italianate, grand, mansard | [Dallam-Merritt_House](https://commons.wikimedia.org/wiki/File:Dallam-Merritt_House.JPG) |
| 14 | Delano House, 70 Buena Vista Terrace | Italianate bay, 25 ft, hill | [Delano_House_(San_Francisco,_CA)](https://commons.wikimedia.org/wiki/File:Delano_House_(San_Francisco,_CA).JPG) |
| 15 | Russell Warren House (465-467) | Italianate flat front, flats | [Russell_Warren_House](https://commons.wikimedia.org/wiki/File:Russell_Warren_House_(San_Francisco).JPG) |
| 16 | TREA House, 2503 Clay (*re-measured*) | Italianate bay, plain | [The_Real_Estate_Associates_(TREA)_House](https://commons.wikimedia.org/wiki/File:The_Real_Estate_Associates_(TREA)_House.JPG) |
| 17 | 2432 Washington St (*re-measured*) | Italianate bay | [Victorian_house_on_Washington_St_..._dllu](https://commons.wikimedia.org/wiki/File:Victorian_house_on_Washington_St_San_Francisco_dllu.jpg) |
| 18 | Stadtmuller House, 819 Eddy | Italianate bay, grand | [Stadtmuller_House](https://commons.wikimedia.org/wiki/File:Stadtmuller_House_(San_Francisco).JPG) |
| 19 | Burr House, 1772 Vallejo | Italianate double bay, grand, mansard | [Burr_House_14000967](https://commons.wikimedia.org/wiki/File:Burr_House_14000967_San_Francisco.jpg) |
| 20 | Henry Geilfuss House (stoop only, under scaffolding) | Italianate/Stick, comfortable | [Henry_Geilfuss_House_(NRHP)](https://commons.wikimedia.org/wiki/File:Henry_Geilfuss_House_(NRHP).jpg) |
| 21 | "1321", flat front (*re-measured*) | Italianate flat front, 20 ft | [Stick-Eastlake_house_(San_Francisco,_California)](https://commons.wikimedia.org/wiki/File:Stick-Eastlake_house_(San_Francisco,_California).jpg) |
| 22–24 | Noe Valley hill row, Italianate/Stick part (*re-measured*) | bay houses | [Noe_Valley_San_Francisco_6](https://commons.wikimedia.org/wiki/File:Noe_Valley_San_Francisco_6.jpg) |
| 25–27 | 1331, 1333, 1335 Scott St | Stick row, square bays | [1331-1335_Scott_St_..._2](https://commons.wikimedia.org/wiki/File:1331-1335_Scott_St_(San_Francisco,_California)_2.jpg) |
| 28 | Unnamed Stick house, June 2023 (*re-measured*) | Stick, square bay | [Stick-Eastlake_architecture,_San_Francisco_June_2023](https://commons.wikimedia.org/wiki/File:Stick-Eastlake_architecture,_San_Francisco_June_2023.jpg) |
| 29 | 46 Walter St (*re-measured*) | Stick cottage over garage | [Walter_Street_Victorian](https://commons.wikimedia.org/wiki/File:Walter_Street_Victorian.jpg) |
| 30 | Westerfeld House, 1198 Fulton, HABS CA-2218-1 (*re-measured*) | Stick/Italianate, grand | [FRONT_ELEVATION_-_Westerfeld_House](https://commons.wikimedia.org/wiki/File:FRONT_ELEVATION_-_Westerfeld_House,_1198_Fulton_Street,_San_Francisco,_San_Francisco_County,_CA_HABS_CAL,38-SANFRA,166-1.tif) |
| 31 | Myrtle Street Flats | Stick-era workers' flats, modest | [Myrtle_Street_Flats](https://commons.wikimedia.org/wiki/File:Myrtle_Street_Flats_(San_Francisco).JPG) |
| 32 | 3397-3399 Sacramento, HABS (*re-measured*) | flats over a corner store | [HABS ... 3397-3399 Sacramento](https://commons.wikimedia.org/wiki/File:Historic_American_Buildings_Survey_Robert_Brandeis,_Photographer_December_20,_1978_NORTH_(FRONT)_ELEVATION_-_3397-3399_Sacramento_Street_(House),_San_Francisco,_San_Francisco_HABS_CAL,38-SANFRA,133-5.tif) |
| 33–34 | Steiner St between Haight and Page, two houses | Queen Anne, ordinary; QA cottage | [Steiner_Victorians](https://commons.wikimedia.org/wiki/File:Steiner_Victorians.jpg) |
| 35 | Divisadero St house | late Queen Anne, grand, turret | [Divisadero_Victorian](https://commons.wikimedia.org/wiki/File:Divisadero_Victorian.jpg) |
| 36 | Noe Valley row, hipped late house with a tower bay | late Queen Anne | (as 22–24) |

Rejected: `Wishy_Washy_Victorian.jpg` (Commons files it under Italianate, but it is a c.1900–10
four-storey corner flats block: a round corner bay running three storeys under a flat
modillioned cornice, a store below; it does confirm V-STO-4's "a three-storey bay under a
flat cornice is Edwardian"). `Old_Ohio_Street_Houses_(San_Francisco).JPG` (shows brick
commercial buildings on Osgood Place, not the houses).

### 1.2 The four ties in grading §5

**T1. Gable pitch (V-TOP-3).** Measured on the gable's base and apex:

| Building | rise / gable width | angle |
|---|---|---|
| Steiner St QA, full-front gable | 0.62 | 51° (camera low, so 51–55° true) |
| Divisadero St QA, wide gable | 0.76 | 57° |
| Steiner St QA cottage, small gablet | 0.75 | 56° |

**Verdict: the grading's 0.62 (≈ 51°) is the low end, not the median.** Use rise =
0.62–0.78 × width, default 0.70 (≈ 54°). Narrow and grand gables are steeper. Confidence
**M-L** (3 gables; the observer's 50–60° from oblique photos agrees).

**T2. Slanted-bay faces against bay share (V-BAY-1, R-17).** Four near-frontal bays:

| Building | bay / front | side face (apparent) / centre face |
|---|---|---|
| 1239 Scott | 0.43 | 0.73 |
| TREA, 2503 Clay | 0.44 | 0.71 |
| 2432 Washington | (left edge hidden) | 0.85 |
| Stadtmuller | 0.48 | 0.84 |
| 1811 / 1815 Sutter | 0.53 / 0.53 | (oblique) |

Mean side/centre 0.78. A bay drawn as centre + 2 × apparent side + colonnettes then has
**each apparent side ≈ 0.29 of the bay and the centre ≈ 0.38–0.42**. The observer's
inconsistency (centre 1.5 + 2 × 0.67 ≠ 4 m) came from taking the true side width as 0.67 m;
the sides are wider than that.

**Verdict:** `side_share.italianate = 0.29` (not 0.25). With a 0.50 bay (3.81 m) the centre
face is about 1.55 m, under the 2.2 m pair test, so the pair stops firing as the grading
wanted. Bay share 0.43–0.53, mean 0.48: **R-17's 0.50 (draw 0.45–0.56) stands.** But a pair
in the centre face is not wrong: Delano (a 25 ft lot) and Burr both have one. **Add a
centre-face pair pick of 0.15 for Italianates (0.4 on grand or double-bay houses)** instead of
banning it. Glass fills about 0.7 of each face. Confidence **M**.

**T3. Proportion: floor height against downhill basements (V-STO-5, R-8).**

| Building | front | sidewalk to cornice top | ratio |
|---|---|---|---|
| Russell Warren (flat front, near-level, frontal) | 25 ft | 12.0 m (+0.75 m parapet) | 1.57 |
| "1321" (flat front, frontal) | 20 ft | 11.5 m | 1.89 |
| Stick house, June 2023 (person for scale) | ≈ 21 ft | 11.1 m (12.0 m to the gablet) | 1.74 |
| 1239 Scott | 25 ft | ≈ 11.4 m | 1.49 |
| Stadtmuller (main block) | — | — | 1.64 |
| Westerfeld (HABS, 3 storeys, wide lot) | — | — | 1.50 |

Storey heights where a floor line could be placed:

| | basement | parlour floor-to-floor | upper (to frieze) | cornice band |
|---|---|---|---|---|
| 1239 Scott | 2.3 | 3.8 | ≈ 4.0 | — |
| 2119 Bush | ≥ 2.5 | 4.5 | 3.5 | — |
| Russell Warren | 2.7 | 4.0 | 3.9 | 1.4 + parapet |
| 2432 Washington (scaled on a 4.0 m parlour) | 2.6 | (4.0) | 3.5 | 1.5 |
| "1321" | 2.25 | 4.6 | 3.3 | 1.3 |
| Stick, June 2023 | ≈ 2.5 | ≈ 3.7 | ≈ 4.0 | — |

**Verdict: the height is close to constant and the ratio follows the lot width.** On level
streets the sidewalk-to-cornice height is 11.1–12.0 m whatever the width, so the ratio runs
from about 1.5 on 25 ft to 1.9 on 20 ft. Target the height, not a ratio: basement **2.4 m**
(draw 2.2–2.7; grading had 2.3), parlour **4.1 m** (3.8–4.6; grading 4.0), upper **3.6 m**
(3.3–4.0; unchanged), cornice band 1.4 m (1.3–1.5) plus an optional panelled parapet
0.5–0.8 m (seen on Russell Warren). That sums to about 11.5 m. Downhill basements add to
this; they do not explain it. Confidence **M** (6 houses).

**T4. Basement window form before garages (V-BAY-5).** Unaltered basements seen: 2119 Bush,
two segmental-arched windows; Brune-Reutlinger, arched; Delano, flat; 1249 Scott, a flat
door and window; Dallam-Merritt, low with small windows. **Verdict: arched 0.5, flat 0.4,
round 0.1** (grading: flat 0.6, arched 0.3). Confidence **L** (5 houses).

### 1.3 Other low-confidence items, now with counts

| Item (grading id) | Grading value | What the photos show | Verdict |
|---|---|---|---|
| Italianate window head (V-WIN-2, R-11) | segmental 0.65, round 0.35 | By house: round-headed 13 (1239, 1245, 1249, 1815, 2119, Cottage Row ×3, Delano, Russell Warren, Stadtmuller, Burr, 45-47 parlour); segmental 4 (Brune-Reutlinger, Dallam-Merritt, 2432 Washington, 1811 upper); flat 4 (TREA, 1321, 33-35 Beideman, 45-47 upper) | **round 0.55, segmental 0.25, flat 0.20** (the raw split is 0.6 / 0.2 / 0.2; shaded toward segmental because landmark houses dominate the sample). Flat on plain and early houses. **Changes the value.** M |
| Head or hood differs by floor (O-3) | 0.4 | 2119 Bush (segmental pediment below, triangular above), 45-47 Beideman (round below, flat above), 1811 Sutter | 0.4 stands. L |
| Italianate entry type (R-3) | hood on consoles 0.6, portico 0.4 | Console hood 5 (1815 Sutter, 33-35 Beideman, TREA, 1321, Russell Warren); framed recess, an arched opening between pilasters or colonnettes under an entablature or pediment, 5 (1239/1245, 1249, 1811, 2119, 2432 Washington); columned portico 4 (Brune-Reutlinger, Dallam-Merritt, Delano, Stadtmuller) | **console hood 0.35, framed recess 0.35, portico 0.30** (grand: portico 0.8). The framed recess is a third type the grading lacks. **Changes the value.** M |
| Paired leaves (R-3) | 0.9 | Paired 7 (2119 Bush, Dallam-Merritt, Delano, Stadtmuller, Geilfuss, 2432 Washington, Westerfeld); single 5 (TREA, 1321, the two Beideman double houses, Russell Warren's flat doors) | **paired 0.7, single 0.3**, single favoured on flat fronts and modest houses. Note: 1239/1241 Scott and Russell Warren 465/467 show two doors side by side that are **two flats' doors**, not a pair of leaves. **Changes the value.** M |
| Flats, two doors under one hood (O-4, R-16) | 0.25 | 1239/1241 Scott, Russell Warren 465/467, 33-35 and 45-47 Beideman, Myrtle St | Supports 0.25; draw both doors under one hood, served by one wider stoop. M |
| Stoop width (V-STP-2, R-1) | 1.3 m (1.1–1.5) | Single door: 1249 Scott 1.3–1.5, 1811/1815 Sutter 1.4–1.6, Walter 1.5, Stick 2023 1.6, 1321 about 1.8 inside the rails; paired leaves or flats: 2119 Bush 1.9, Geilfuss 1.8–2.0, Russell Warren 2.5; grand portico: Stadtmuller ≈ 2.7 (as wide as the portico) | **1.6 m for a single door (draw 1.4–1.8); 1.9–2.5 m for paired leaves or flats; the portico's width on a grand house.** The grading's 1.3 is a little narrow. **Changes the value.** M |
| Stoop risers (V-STP-1) | `round(h / 0.18)` | 11–15 on bay houses (1249: 14; 1811/1815: 11–12; Walter: ~15; Stick 2023: ~12); 4–6 on low flat fronts (Beideman), 8–9 on some grand houses with low basements (Dallam-Merritt, Stadtmuller) | Stands. M |
| Stoop material (V-STP-3) | wood; stone 0.1 grand | Wood with turned balusters and panelled newels on every unaltered stoop seen (8). Granite, concrete or brick ones (Stick 2023, 2432 Washington, Steiner) are replacements; Delano's is rebuilt with pipe rails | Stands. H |
| Cornice brackets (V-TOP-1, R-18) | pitch 0.7 m | 2119 Bush 0.85, Russell Warren 0.9, 1321 0.65 m; frieze panels between in all three; frieze attic lights at Delano, TREA, 45-47 Beideman | Pitch **0.65–0.9, default 0.8**. Attic lights: 3 of ~12 Italianates where the frieze is visible, so **O-8 0.3 stands**. M |
| Quoins / corner strips (O-10) | grand 0.5, comfortable 0.15; corner pilaster 0.7 | Rusticated corner strips on Russell Warren (ordinary flats), Brune-Reutlinger, Stadtmuller, Burr | Not only grand: **quoin strips 0.25 on ordinary, 0.5 comfortable, 0.7 grand.** L |
| Mansard third storey (O-7) | grand Italianate with 3rd storey: 0.7 | Dallam-Merritt and Burr: both mansards with arched dormers | Stands. L |
| Garage cut under the bay (O-5, "now" mode) | 0.5 | Garages on 1239, 1245, 1811, 1815, 2432 Washington, Stadtmuller, Russell Warren, Stick 2023, Walter, 311 Steiner: 10 of 19 houses whose basement is visible | **0.5 stands.** H |
| Stick bay returns (V-BAY-2) | `opening_type = 'none'` under 0.5 m | Stick 2023 and Westerfeld: returns blank; 1331-1335 Scott: a narrow window in each return of the cantilevered upper bay | Stands for flush square bays; a cantilevered upper bay gets a narrow return light. L |
| Stick square bay front (new) | (centre face glazed) | Three lights in the front face (Westerfeld, Stick 2023, wide centre + 2 narrow); a pair on narrow cottages (Walter) | Stick square-bay front: triple 0.6, pair 0.4. L |
| Stick gablet over the bay (V-TOP-2) | 0.7 | Stick 2023 (sunburst), Walter (sunburst), Westerfeld (pediment) | Stands. L |
| Stick sunburst panels over windows (R-11) | 0.5 | Walter (both windows) | No change; too few. L |
| Upper-only bays (V-BAY-4, R-4) | parlour-only 0.15 for Italianate | Myrtle St flats: square oriels on the upper floor only; 1331-1335 Scott: upper square bay cantilevered on brackets over the porch | Add an **upper-only** option for modest Stick flats (0.3 on modest). L |
| Turret cone (V-TUR-2) | cone rise 1.5 × drum width | Divisadero: rise 0.95 × drum width (≈ 62°) | **Use about 1.0 × drum width.** Westerfeld's tower is square with a pyramidal roof (Stick), not a drum. **Changes the value**, but L (1 drum measured). |
| QA overhanging gable on entablature (V-TOP-4) | overhang 0.4–0.6 m on brackets over a full entablature | Steiner St QA: yes, on brackets over a dentilled entablature | Stands. L |
| QA balcony or loggia over the entry (O-11) | 0.3 | Steiner St QA (balustraded balcony), Divisadero (loggia in the gable) | Stands. L |
| One-storey raised cottage (new omission) | none | 46 Walter (Stick), 311 Steiner (QA): one living storey over a tall basement, gablet or front gable | Add as a modest variant; weight unknown from photos (the Liberty inventory would give one). L |

### 1.4 What would still settle the Stick and Queen Anne numbers

The queued Queen Anne and Stick photos (§5) would take both styles to 15: 710-720 Steiner,
Pierce & Waller, Waller St row, 1550 Page, Haas-Lilienthal, Spencer, McMullen, Belden,
Wilford, Einstein, Doolan, 4040 17th St, Grateful Dead House (710 Ashbury), Mrs Doubtfire
house (2640 Steiner), Hermann, Haight, Fillmore and Sanchez rows, Vollmer, Mish, Ohlandt.
The ones that matter most: gable pitch on 6+ more gables, turret cone on 4+ more drums, and
the QA bay-plan split (R-5).

---

## 2. Paris (`haussmann.toml`)

### 2.1 Buildings used

All are Commons photos already in `dev/reference/` (their `source_url` is in the metadata),
looked at directly, plus the three the grader used. The new ordinary-street sample did not
download (§0), so these counts inherit the corpus's lean toward grand and comfortable houses
in the 9e, 8e and 1er (§3).

| # | Building | Corpus file(s) |
|---|---|---|
| 1 | 2 bd Voltaire | se-facade_06 (grader) |
| 2 | 53 rue Blanche | se-facade_07 (grader) |
| 3 | 55 rue de Châteaudun | se-facade_11 (grader) |
| 4 | 16 rue Étienne-Marcel | class-range_06 |
| 5 | 31 rue du Sommerard | class-range_08 |
| 6 | 19 rue Auber | se-surround_10 |
| 7 | 164 rue du Faubourg-Saint-Honoré | se-surround_11 |
| 8 | 2 pl. d'Estienne-d'Orves / 60 Châteaudun | se-entrance_05 |
| 9 | 16 rue Berthollet | se-cornice_05 |
| 10 | 12 rue Halévy | second-empire_12 |
| 11 | rue Halévy (commercial block) | se-ironwork_08 |
| 12 | 105-107 rue de Rennes | second-empire_10 |
| 13 | 50 bd Magenta | se-facade_10 |
| 14 | corner rue Christiani / rue de Clignancourt | third-republic_03 |
| 15 | 27 rue Saint-Lazare | se-entrance_04 |
| 16–18 | Marville: bd de Sébastopol corner, bd Malesherbes, rue de Turbigo (c.1853–70) | se-facade_01–03 |
| 19 | rue du Renard / rue Saint-Merri (photo 1895) | corner_11 |
| 20–21 | 84 and 87 rue de la Victoire | restauration_03, _04 |

### 2.2 Tie-breaks and low-confidence items

| Item (grading id) | Grading value | Count from the photos | Verdict |
|---|---|---|---|
| Heavy cornice under the top storey (S11) | move the 0.6 m cornice to the foot of the top storey | Voltaire, Blanche, Châteaudun, Halévy commercial, Berthollet, Magenta 50, Étienne-Marcel: all 7 where it can be seen | **Confirmed.** H |
| Noble + top filants (R6) | grand/comfortable 0.85; ordinary: top only 0.35; none 0.15 | Noble + top: 15 of 17 post-1853 buildings (19 rue Auber's top floor is out of frame). Top only: Berthollet (ordinary, residential). None: Sommerard (comfortable, garde-corps and stone balustrade allèges only) | **Stands** for grand/comfortable. Sommerard shows "none" is real on comfortable houses too, so give it 0.05–0.1 as the grading does. M |
| Noble filant extent (B2) | full 0.65, central 0.35 | Full width 14, central bays only 1 (Blanche) | **full 0.8, central 0.2.** **Changes the value.** M (corpus is mostly boulevards and wide streets) |
| Letting-floor balconies, 1860–84 (R2) | rails 0.6, grouped 0.25, per window 0.15 | Grouped over 2–3 bays: Voltaire, Étienne-Marcel, Fbg St-Honoré 164, Berthollet, Magenta 50, Rennes 105-107 (6). Per-window balconies: Marville Sébastopol corner and Turbigo, Châteaudun, part of Étienne-Marcel (4). Rails only: Blanche, Halévy commercial, Sommerard, Malesherbes, Christiani (5) | **rails 0.4, grouped 0.35, per window 0.25** for 1860 on. Per-window balconies are visible in Marville's own 1860s photos, so they are not only a late form. Some grouped cases are probably 1880s (Étienne-Marcel, Rennes). **Changes the value.** M |
| Pediment placement (R11) | noble 0.5, floor above 0.2, none 0.3 | Noble: Auber 19, Sommerard (segmental hoods), Opéra 38 (grader) = 3. Floor above the noble: Voltaire, Fbg St-Honoré 164, Estienne-d'Orves = 3. None (consoles, shells, plain): Blanche, Châteaudun, both Halévy, Magenta 50, Étienne-Marcel = 6 | **noble 0.3, floor above 0.25, none 0.45.** **Changes the value.** M |
| Dormers per axis (R9) | grand/comfortable: every axis 0.75 | Every axis: Sommerard, Estienne-d'Orves, Halévy ×2, Magenta 50, Étienne-Marcel, Châteaudun = 7; fewer: Voltaire (5 on 10), Blanche (3 on 7) = 2 | **0.75 stands** (7 of 9). Both Halévy blocks add small roof lights between, a second row. M |
| Two-level comble before 1884 (C4, R8) | 0.4 on ≥ 20 m streets with 17.55 m cornices | 12 rue Halévy: dormers plus a second row of roof lights | Consistent; no change. L |
| Entrance position (R13) | odd: middle 0.55, end 0.3, second 0.15; even: end 0.4, 2nd/3rd 0.6 | Odd counts: middle (Blanche), end (Magenta 50), near-end (Fbg St-Honoré 164, bay 7 of 9). Even: bay 3 of 10 (Voltaire), bay 3 of 6 (Berthollet). Étienne-Marcel and Sommerard near an end (counts not fully visible) | Parity rule holds (no "middle" door on an even count). For odd counts the photos give 1 middle of 3, so **lower middle to 0.4, end 0.35, second 0.25.** Few cases: L-M |
| Porte cochère rising through the entresol (R12, G6) | 0.6 | Arched doors rising into the entresol zone: Blanche, Châteaudun, Estienne-d'Orves, Fbg St-Honoré 164, Auber 19; stopping at the ground storey: Voltaire (flat pedestrian door) | Stands or a little higher (**0.7**). M |
| Pre-1850 layer (R7) | plaster, persiennes, bandeau per floor | Victoire 84/87, Renard / St-Merri: persiennes on almost every window, a bandeau per floor, balconnets, small combles | Confirmed. M |
| Pre-1884 roof pitch (C3) | 45° by decree | Not measurable from street photos (the grader's point stands); no profile view in the corpus | No change. |

Not settled by photos: the decree wording (E3, E4, E6) and storey heights by class (S6,
Daly is better evidence than any photo).

---

## 3. Corpus audit (`dev/reference/`)

Counts are over the 164 photograph records (Daly plates and published elevations excluded).

### 3.1 Duplicates

The 164 records are **136 distinct Commons files**. The same file sits in several families:

| File | Copies | Families |
|---|---|---|
| `53_rue_Blanche_P1050933.JPG` | 6 | class-range, se-comble, se-entrance, se-facade, se-surround, third-republic |
| `2_boulevard_Voltaire_..._2016.jpg` | 3 | class-range, se-entrance, se-facade |
| `16_rue_Etienne-Marcel.jpg` | 3 | class-range, se-facade, third-republic |
| `2018_1-3_Place_Saint-Michel.jpg`, `2018_5-7_Place_Saint-Michel.jpg` | 2 each | class-range, second-empire |
| `Avenue_de_l'Opéra,_Paris,_France_2009.jpg` | 2 | class-range, second-empire |
| `31_rue_Du_Sommerard.JPG` | 2 | class-range, se-surround |
| `Immeuble_haussmannien_(34321494015).jpg` | 2 | class-range, third-republic |
| Castel Béranger façade and portal | 2 each | belle-epoque, post-1902 |
| 5 Daly plates | 2 each | daly-1864, se-elevation |

Building level is worse: rue Halévy appears in 11 records, Castel Béranger in 5 and 29 avenue
Rapp (Lavirotte) in 5. A VLM check that samples per family will show the same few buildings
again and again, and a selection by family over-weights them.

### 3.2 Wrong period or contradictory filing

| Record | Problem |
|---|---|
| 53 rue Blanche | Filed both as Second Empire (se-*) and as third-republic_02. It cannot be both; no date is recorded. |
| 16 rue Étienne-Marcel | In se-facade (Second Empire) and third-republic. The west section of rue Étienne-Marcel was cut in the 1880s, and the façade (grouped balconies, heavy consoles) reads 1880s. Probably Third Republic. |
| avenue de l'Opéra (second-empire_04, _05; se-ironwork_02, _03; se-entrance_01, _09; class-range_03) | The avenue was largely built in 1876–79, after the Second Empire. At least seven records file it as Second Empire evidence. |
| 105-107 rue de Rennes (second-empire_10; third-republic_05, _06) | Rue de Rennes north of bd Saint-Germain is 1870s–80s; filed in both periods. |
| Place Saint-Michel (second-empire_01–03, class-range_01–02, se-ironwork_01, _07) | se-facade's own notes reject Place Saint-Michel as a post-1870 rotonde, while seven other records use it as canonical Second Empire. One of the two has to go. |
| 27 rue Saint-Lazare (se-entrance_04) | Round-headed 1er windows in arched recesses, a plain dressed wall, light balconnets, no filant: reads as Restauration or Louis-Philippe. Check the date before using it as Second Empire. |
| post-1902 family | Castel Béranger (1895–98) and 29 av. Rapp (1901) predate the 1902 règlement and already sit in belle-epoque. The Porte Dauphine Métro entrance (post-1902_03) and a 1927 studio building (post-1902_12) are not apartment buildings of the period. |
| belle-epoque family | 8 of 11 records are three Art Nouveau showpieces (Castel Béranger ×3, Lavirotte ×3, Les Arums ×2), and the other three are architect-signed or prize façades (1 rue Le Peletier, 31 rue de Fleurus, 130 rue Réaumur). The ordinary 1884–1902 immeuble de rapport, which is what the generator draws for those dates, has no record. |
| 2 bd Voltaire | Classed `ordinary` in class-range and se-entrance and `comfortable` in se-facade: the same photo with two classes. |

### 3.3 Gaps

- **Class.** grand 77 (47 %), comfortable 57 (35 %), ordinary 13 (8 %), modest 8 (5 %),
  unknown 9. The generator's commonest output, ordinary and modest houses, has about 21
  photos, and most of the modest ones are pre-1850 archival prints.
- **Place.** The 9e alone has 36 records (22 %); 1er, 5e, 6e, 8e and 16e add 61. The 10e,
  11e, 12e, 14e, 17e and 18e have 15 between them; the 13e, 15e, 19e and 20e have none.
  Working-class and outer-ring streets, where most 1860–1900 houses stand, are nearly absent.
- **Date.** 37 of 164 photos have a construction year, and 23 of those are the Belle Époque
  and post-1902 showpieces. Second Empire and Third Republic are almost entirely undated.
- **Altered ground floors.** Most modern street photos show replaced shopfronts (Office
  Depot, Zara, Intermarché). That is unavoidable, but no family has a note saying which
  ground floors are original.
- **Frame quality.** class-range_10 and restauration_03/04 are full museum mounts with the
  building in 20–50 % of the frame; se-facade_09 is a thin sliver of a street view. Several
  se-socle and third-republic records are door or keystone crops (fine for ornament, not for
  façade counts).
- **No San Francisco corpus at all.** `dev/reference/` is Paris-only. The Victorian fidelity
  work rests on photos no one has curated into the corpus, so the VLM check has nothing to
  compare the Victorian strip against.

### 3.4 Recommended changes (not applied here)

1. **De-duplicate**: keep each Commons file in one family and refer to it from others in
   `notes`. Add a `building` key so selection can sample by building, not by record.
2. **Fix period filing**: move avenue de l'Opéra, 16 Étienne-Marcel and 105-107 rue de
   Rennes to third-republic; resolve Place Saint-Michel one way; date-check 27 rue
   Saint-Lazare; drop post-1902_03 and _12, and move Castel Béranger and avenue Rapp out of
   post-1902.
3. **Make `klass` one value per building** (2 bd Voltaire).
4. **Add ordinary and modest houses from the outer arrondissements**, 1853–1902. The 25
   address-level street photos queued in §5 (rue de Lancry, rue de Paradis, rue du
   Faubourg-Poissonnière, rue Marcadet, rue Rochechouart, rue Cadet, rue de Provence, rue
   Troyon, rue de Tocqueville, bd Beaumarchais, rue de Belleville and others, by the Commons
   photographer *rwk*) are frontal, unshowy and spread over the 9e, 10e, 11e, 14e, 17e, 18e
   and 19e: the right material for this gap.
5. **Add 2–3 ordinary 1884–1902 immeubles** to belle-epoque so it is not three Art Nouveau
   buildings.
6. **Start an `sf-victorian` family** from §1.1. The HABS large-format frontals
   (Westerfeld, 3397 Sacramento) and the frontal photos (Russell Warren, 1321, 2119 Bush,
   Stick 2023, Stadtmuller, TREA) are the measurable ones. The metadata fetch
   (`extmetadata` for licence and author) was refused by the same rate limit, so they are
   not added yet; nothing goes into the corpus without its licence copied from Commons.

---

## 4. Verdicts that change a recommended value

Victorian (`victorian/grading.md`):

| Id | Was | Now | Confidence |
|---|---|---|---|
| V-BAY-1 / R-2 | `side_share.italianate = 0.25`, no pair | **0.29**; centre-face pair pick 0.15 (0.4 grand/double) | M |
| V-WIN-2 / R-11 | segmental 0.65, round 0.35 | **round 0.55, segmental 0.25, flat 0.20** | M |
| R-3 Italianate | hood 0.6, portico 0.4; paired 0.9 | **hood 0.35, framed recess 0.35, portico 0.30; paired 0.7** | M |
| V-STP-2 / R-1 | 1.3 m (1.1–1.5) | **1.6 m single (1.4–1.8); 1.9–2.5 paired or flats; portico width grand** | M |
| V-STO-1..3, V-STO-5 / R-8 | 2.3 / 4.0 / 3.6, target ratio 1.5–1.65 | **2.4 / 4.1 / 3.6, target height ≈ 11.5 m, ratio follows width** | M |
| V-TOP-3 / R-5 | rise 0.62 × width | **0.70 (0.62–0.78)** | M-L |
| V-TUR-2 / R-5 | cone rise 1.5 × drum | **≈ 1.0 ×** | L |
| V-BAY-5 | flat 0.6, arched 0.3, round 0.1 | **arched 0.5, flat 0.4, round 0.1** | L |
| O-10 | quoins grand 0.5, comfortable 0.15 | **ordinary 0.25, comfortable 0.5, grand 0.7** | L |
| R-18 | bracket pitch 0.7 | **0.8 (0.65–0.9)** | M |

Paris (`haussmann/grading.md`):

| Id | Was | Now | Confidence |
|---|---|---|---|
| B2 / R6 | noble filant full 0.65, central 0.35 | **full 0.8, central 0.2** | M |
| R2 (1860 on) | rails 0.6, grouped 0.25, per window 0.15 | **rails 0.4, grouped 0.35, per window 0.25** | M |
| R11 | noble 0.5, above 0.2, none 0.3 | **noble 0.3, above 0.25, none 0.45** | M |
| R13 (odd) | middle 0.55, end 0.3, second 0.15 | **middle 0.4, end 0.35, second 0.25** | L-M |
| R12 | through the entresol 0.6 | **0.7** | M |

Confirmed unchanged: S11 (heavy cornice under the top storey), R9 dormers 0.75, R7 pre-1850
layer, V-STP-1, V-STP-3, O-5 garage 0.5, R-17 bay share 0.50, O-8 attic lights 0.3.

---

## 5. Queued fetches (for when Commons stops rate-limiting)

SF Queen Anne and Stick (Commons titles): `"Painted Ladies" row ... 710 to 720 Steiner
Street ... LCCN2013630348.tif`, `Pierce and Waller.jpg`, `Waller Street Painted Ladies, San
Francisco.jpg`, `1550 Page St., San Francisco, CA 3-4-2012 4-13-37 PM.JPG`, `Haas-Lilienthal
House, 1.jpg`, `John Spencer House (San Francisco).JPG`, `John McMullen House (San
Francisco).JPG`, `C. A. Belden House (San Francisco).JPG`, `Albert Wilford Houses (San
Francisco).jpg`, `Daniel Einstein House (San Francisco).JPG`, `Richard P. Doolan Residence
and Storefronts, 557 Ashbury St. & 1500 Haight St., San Francisco, CA 3-4-2012 4-03-43
PM.JPG`, `4040 17th St - McCormick House.jpg`, `Grateful Dead House.jpg`, `Mrs doubtfire
house san francisco.jpg`, `Hermann Victorians.jpg`, `Haight Victorians.jpg`, `Fillmore
Victorians.jpg`, `Sanchez Street Victorian.jpg`, `Vollmer House.JPG`, `Mish House (San
Francisco).JPG`, `Ohlandt Newlyweds House, 1260 Potrero Ave., ... 1-43-01 PM.JPG`,
`Victorian facades on 16th Street in San Francisco.jpg`, `Row of Victorian houses in San
Francisco.JPG`.

Paris, ordinary streets (photographer *rwk*): `P1170482 Paris VII rue Vaneau n°14 rwk.jpg`,
`CF7763 Paris 9e rue Blanche n73 rwk.jpg`, `P1220581 Paris XVII rue de Tocqueville n45
rwk.jpg`, `P1310421 Paris XVII rue Troyon n1 rwk.jpg`, `P1220770 Paris X rue Bouchardon n22
rwk.jpg`, `P1300850 Paris X rue de Paradis n6 rwk.jpg`, `P1300837 Paris X rue de Paradis n21
rwk.jpg`, `P1280510 Paris X rue de Lancry n12 rwk.jpg`, `P1280511 Paris X rue de Lancry N14
rwk.jpg`, `P1300795 Paris X rue Fbg-Poissonniere n30 rwk.jpg`, `P1300800 ... n54`, `P1300801
... n57`, `P1300804 ... n58`, `P1340519 Paris XVIII rue Marcadet n145 rwk.jpg`, `P1280228
Paris IX rue Cadet N26 rwk.jpg`, `P1280266 Paris IX rue Rochechouart n36 rwk.jpg`, `P1280278
... N58`, `P1280283 ... N67`, `P1220819 Paris IX rue de Provence n22 rwk.jpg`, `P1220834 ...
n57`, `P1030035 Paris IX rue Chauchat n°10 rwk.JPG`, `P1280289 Paris IX rue du Delta n26
rwk.jpg`, `CF7968 Paris 19e rue de Belleville n275 rwk.jpg`, `F1207 Paris XI bd Beaumarchais
n109 rwk.jpg`, `P1160897 Paris XVII rue de Lévis rwk.jpg`.

Fetch notes: send a descriptive User-Agent; ask the API for `iiurlwidth` at a standard step
(960 or 1280) and rewrite the `thumb.wikimedia.org` host to `upload.wikimedia.org`; keep to
one request at a time with a pause of several seconds; batch `extmetadata` lookups in small
groups, since large ones are the first to be refused.
