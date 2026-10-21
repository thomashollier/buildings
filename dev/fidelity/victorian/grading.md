# San Francisco Victorian model: independent grading

Assessor brief: grade `typologies/victorian/victorian.toml` (+ `grammar.py`, and `kit.write_stoop` which it names) and the strip `docs/strips/victorian.png` against two independent evidence sources. I wrote neither the model nor the evidence. No files were changed except this one.

**Inputs**
- Model: `src/buildings/typologies/victorian/victorian.toml`, `grammar.py`, `src/buildings/typologies/common/kit.py` (`write_stoop`). Format: `dev/RULES.md`. Render: `docs/strips/victorian.png` (Italianate 1872 25 ft; Italianate 1878 20 ft mirrored; Stick 1883 double bay 30 ft; Stick 1886 side yard; Queen Anne 1892 extra floor; Queen Anne 1895 turret).
- Evidence:
  - `observer.md`: blind to the model. About 30 houses scaled from Commons photos, plus the Liberty Street NRHP nomination and SF Planning Bulletin 18. Strong on dimensions (±10-15%), medium on counts.
  - `adversary.md`: written sources only (14 NRHP nominations, the 51-entry Liberty inventory, Bulletin 18, the Alamo Square tour). Strong on kinds and counts, weak on dimensions; it borrows the observer's numbers where it has none, marked [obs].

**Own photo check: not done.** I tried to break ties against Commons photos (Walter St, Stick-Eastlake 2023, 1239-1245 Scott). The Commons API answered HTTP 429 (rate limited), and the file path was then refused by this session's proxy (403). So every tie below is broken by weighing the two reports, not by my own reading of a photo. The ties that most need a photo are listed in §5.

**Model figures I derived** (25 ft lot, single layout, from the toml):
- Bay zone 0.55 × 7.62 = 4.19 m; entry zone 3.43 m.
- Italianate/Queen Anne side faces 0.20 × 4.19 = 0.84 m apparent; front face 2.51 m, which passes the `w > 2.2` pair test, so **every Italianate bay gets a mullioned pair**.
- Stick side faces 0.07 × 4.19 = 0.29 m apparent; the sash rule gives them `max(0.3, min(w - 0.3, 1.1))` = **0.30 m of glass in a 0.29 m cell**, i.e. a light wider than its cell.
- Height to the top of the cornice ≈ 2.1 + 3.6 + 3.3 + 1.6 (+ cornice) ≈ 10.6-11 m: a ratio of about **1.4** to the width (strip panel 1 scales to 1.42).
- Stoop: 8 risers over 2.1 m = **26 cm risers**, 2.93 m wide, stone, drawn as a side profile.
- **Correlated seeds.** Layout uses `seed % 2`, extra floor `seed % 3`, side yard `seed % 4 == 3`, paint `paints[seed % 4]`. So every house with a side yard is rose (`paints[3]`) and single_right, and the extra floor recurs every third seed. Neither report noticed this; it is a rule defect that the coming `pick`/`draw` (independent streams) fixes for free.

---

## 1. Where the evidence disagrees, and how I weigh it

| Question | Observer | Adversary | Weighed conclusion |
|---|---|---|---|
| **Storey heights** | Parlour 4.1 (3.8-4.6), upper 3.7 (3.4-4.0), photo-scaled, M | 4.0 / 3.6, from one 12 ft ceiling (Spencer) plus [obs]; medium-low | **Agree in direction; take 4.0 / 3.6.** Two methods, one a direct ceiling figure, both say the model is ~10% low. |
| **Overall proportion** | Sidewalk to cornice 1.6-1.9 × width (3 straight-on photos), H | Model 5-20% squat; medium-low | **Observer, with a lower target.** Even the corrected floors give ~1.5; the observer's photos may include taller (downhill) basements. Aim for 1.5-1.65 on the standard house. |
| **Turrets** | Corner and high-end houses only; mid-block builder rows have gables (Steiner, Waller, Haight) | Builder mid-block bay-turrets are real (Wilford pair ~23 ft; 584 Page on 25 ft), but a minority (1 of 7 Liberty Queen Annes; Steiner none) | **Adversary wins on the gate, both win on the rate.** It names builder houses, so class is the wrong gate; but turrets are rare mid-block. Turret becomes a weighted pick, not a class switch. |
| **Queen Anne bay plan** | Any of slanted, square, round, part-hex; often square-over-slanted, upper corbelled on brackets | Round tower, polygonal upper-only, square-over-slant (Spencer); "curved bays" (tour) | **Agree**: slanted-only is wrong. Weights below are my reading of both lists combined (low-medium). |
| **Bay height** | 2 storeys standard; 1-storey parlour bays on early/cheaper Italianates | Same, with named examples (L7, L42, 584 Page upper-only) | **Agree.** Model runs the bay through every storey, so a third storey gets a 3-storey bay. |
| **Third storey** | "Larger houses and Edwardian flats" | 1 of ~30 Liberty houses; rich ones as mansards | **Agree**: rare except grand; the `seed % 3` clause is contradicted. |
| **Double-bay threshold** | Fronts of 37-50 ft, wealthy, M | Only 3 of 51 Liberty lots are double width; every 27.5-30 ft house is single-bay | **Agree**: ≥ ~12 m or `grand`. |
| **Slanted bay faces** | Centre 1.3-1.7 m, one window per face; sides 0.8-1.1 m true; but bay share of front measured 40-56% | One window per face is unanimous in the texts | **Agree on one window per face (H).** The observer's face widths and bay shares are not mutually consistent (1.5 + 2 × 0.67 apparent = 2.85 m, not 4 m), so the bay share probably includes flanking wall/pilasters. Resolve by narrowing the bay's glazed faces, not by dropping the pair rule alone (see V-BAY-1). |
| **Gable pitch** | 50-60°, from oblique photos, M-L; rise 0.6-0.9 × gable width | No text gives an angle | **Observer, flagged M-L.** Model is ~42°. Needs one straight-on photo (§5). |
| **Paint** | Period light stone colours for Italianate; earth palettes later; painted-lady is a 1960s+ revival (M) | Confirms the revival date (Wikipedia); period colour unsourced | **Agree the model is neither period nor modern.** Low confidence on period colours; make it an explicit mode. |
| **Stoop** | 10-14 risers (range 5-18), straight, perpendicular, 1.1-1.5 m wide, turned balusters, newels | 26 cm risers impossible; stone wrong (period stoops wood); width 2.9 m wrong | **Agree.** Counts are the observer's (exact from photos); material is the adversary's (texts). |
| **Basement under the bay** | Flush basement wall, small windows (arched or porthole), garage today on ~50% | Same; "garages usually added under the bay" | **Agree.** Model is right for the original state. |

---

## 2. Grades

A = matches; B = needs tuning; C = wrong, or missing a key variant; D = contradicted by the evidence.

### 2a. RULE problems (victorian.toml)

| ID | Rule / parameter (toml) | Model | Grade | Evidence | Corrected value |
|---|---|---|---|---|---|
| V-LOT-1 | `LOT` (grammar.py) | 7.62 m | **A** | Liberty "about 25 feet wide"; 584 Page, 70 Buena Vista, McMullen deeds 25 ft; observer scaled fronts | Keep. Width draw: 20-30 ft, weights below (R-15). |
| V-TYPE-1 | `victorian.lot` `kind` | Hard cuts: Italianate < 1880, Stick < 1888, QA after | **B** | Bulletin 18 overlapping ranges (1865-85 / 1880-1900 / 1885-1910); adversary scores 35/41 right, every miss within 4 years of a cut | Keep the order; replace cuts with a per-house `pick` whose weights ramp with year (table in §4, R-6). |
| V-TYPE-2 | (missing) flat-front Italianate | none | **C** | Bulletin 18 "popular during the 1860s and 1870s"; Liberty L16, L35; 2119 Bush, Beideman 45-47, 1321 | Add a bayless variant: 3 equal openings per floor (door + 2 windows on the parlour floor, 3 above), door at one side. Weights in R-7. |
| V-LAY-1 | `bay_w` / `BayZone` share | 0.55 of front | **B** | Observer measured 40-56% (Washington 56, TREA ~40, Stick 2023 ~50, Walter ~45) | Default 0.50; `draw` uniform 0.45-0.56 per house. |
| V-LAY-2 | layout mirroring `seed % 2` | 50/50 left/right | **A** | Mirrored pairs (1239/1245 Scott) | Keep as a 50/50 `pick`, on an independent stream. |
| V-LAY-3 | `double` at `w >= 8.4` | 27.6 ft | **D** | Liberty: double form only on the 3 lots "more than double width"; B2, B3, B6 at 27.5-30 ft all single-bay; Burr 91 ft | `double` when `w >= 12.0 or klass == 'grand' and w >= 10.5`; and always with a central portico (V-ENT-2). Italianate only (no Stick double in the evidence). |
| V-LAY-4 | side yard `seed % 4 == 3`, `w >= 6.8`, 1.3 m | 25% of single lots | **B** | Rows mostly continuous (L7, L24 party walls); side yards on large lots (Geilfuss 60 ft, Burr); no frequency for 25 ft lots | Weight 0.10 on 25 ft lots, 0.5 when `w >= 10` or grand; independent of paint. |
| V-STO-1 | `heights[0]` basement | 2.1 m | **B** | Observer 1.8-2.7 m from riser counts (10-14 × 0.18); adversary OK | Default 2.3 m; `draw` 1.8-2.7 (triangular, mode 2.3). |
| V-STO-2 | `heights[1]` parlour | 3.6 m | **B** | Observer 4.1 (3.8-4.6); Spencer 12 ft ceiling ≈ 4.0 | 4.0 m (draw 3.8-4.3). |
| V-STO-3 | `heights[2]` chamber | 3.3 m | **B** | Observer 3.7 (3.4-4.0) | 3.6 m (draw 3.4-3.8). |
| V-STO-4 | `extra_floor` on `seed % 3 == 2 or grand` | 1/3 of ordinary houses | **D** | Liberty 1 of ~30 with a 3rd storey; rich ones are mansards (B7, B8); a 3-storey bay under a flat cornice is Edwardian | Per-house `pick`: modest/ordinary 0.03, comfortable 0.10, grand 0.50. On an Italianate grand, the third storey is a mansard (O-7), not a third bay floor. |
| V-STO-5 | overall proportion (derived) | ~1.4 : 1 | **C** | Observer 1.6-1.9 (H); Liberty "tall and narrow" | Follows from V-STO-1..3 and V-TOP-1: target 1.5-1.65. |
| V-BAY-1 | `side_share.italianate` and the pair rule | 0.20; front face 2.51 m → mullioned pair | **D** | One window per face is unanimous (1356 Scott, 1624 Post, Dallam-Merritt, Geilfuss); observer centre face 1.3-1.7 m | `side_share.italianate = 0.25` (front face ≈ 2.1 m at bay 4.19 m, under the 2.2 m pair test). And gate `a_pair_in_the_front_face` on `kind != 'italianate'` so a wider bay cannot re-trigger it. Single front light 1.0-1.1 m wide. |
| V-BAY-2 | `side_share.stick` | 0.07 (0.29 m sliver holding a 0.30 m sash) | **C** | Observer: square-bay returns 0.4-0.7 m deep, 1 narrow window *or blank*; in true elevation a return is edge-on | Keep 0.07 as the visible return strip but set `opening_type = 'none'` when a side face is under 0.5 m. Also fix the sash rule: `light_width` must never exceed `w - 0.1`. |
| V-BAY-3 | `side_share.queen_anne` | 0.20 (the Italianate half-octagon) | **D** | Liberty "round, part-hexagonal or rectangular"; 584 Page round tower; Spencer square-over-slant; tour "curved bays" | Per-house bay-plan `pick` for QA (R-5); per-floor plan so the upper floor can be square over a slanted parlour bay. |
| V-BAY-4 | bay height = every non-basement storey | always | **C** | Bulletin 18 "two-story"; 1-storey bays L7, L42; upper-only 584 Page | Bay on parlour + chamber only; never on a 3rd storey. Per-house `pick` for Italianate: 2-storey 0.85, parlour-only (pair of windows above) 0.15. |
| V-BAY-5 | flush basement under the bay, one small window | always | **A** (form) / **B** (window) | Liberty "garage ... usually under the bay"; 2119 Bush arched windows; L22 portholes | Keep. Window `pick`: flat 0.6, arched 0.3, round 0.1 (low). Garage in a "now" mode (O-5). |
| V-BAY-6 | `bay_cornice` 0.32 m entablature at every floor | every storey | **B** | 1356 Scott: small bracketed cornice at the first-floor ceiling; Geilfuss/observer: panelled apron 0.5-0.8 m between floors; top floor runs into the main cornice | Intermediate: 0.5-0.6 m panelled apron with a small cornice. Top: no separate band; the main cornice breaks forward over the bay. |
| V-BAY-7 | `corner_board` 0.14 at every bay arris | corner boards | **B** | Italianate arrises carry engaged colonnettes (1356 Scott, 70 Buena Vista, Burr, Geilfuss) | Italianate: `order = 'colonnette'`, ~0.12 m; Stick: corner board/stick, keep 0.14. Facade corners: see O-10. |
| V-WIN-1 | sash fills the storey (sill 0.55, head 0.55) | parlour light 2.5 m, chamber 2.2 m | **A** (shape) / **B** (size) | Observer sills 0.4-0.6, head 0.4-0.7 below the next floor; parlour ~1.0 × 2.9 m | Keep sill/head offsets; with V-STO-2/3 the lights become ~2.9 / ~2.5 m, which matches. |
| V-WIN-2 | Italianate head `segmental`, keystone, moulded architrave | always segmental | **B** | Segmental: 70 Buena Vista, Geilfuss, 1356 Scott, Burr; round-headed: 1624 Post, 2119 Bush parlour, 881 Fulton | Per-floor `pick`: segmental 0.65, round 0.35. |
| V-WIN-3 | Stick head flat with architrave | flat | **A** | Bulletin 18; observer (Walter, Stick 2023) | Keep. Add sunburst/fan panel over (O-3). |
| V-WIN-4 | QA head flat, `surround_kind = 'none'` | plainest builder case | **B** | Transoms (McMullen), stepped arches (Spencer), Palladian (L19, L20) | Flat with a transom light as default; surround kept (a plain casing, not 'none'). |
| V-WIN-5 | one window over the door | always single | **A** | 1356 Scott, 70 Buena Vista, 1624 Post; observer R20 | Keep; give it the strongest hood on the front (O-3). Pair weight 0.15 on flat fronts. |
| V-ENT-1 | door: single 1.1 m flush opening, transom, segmental in Italianate | single, flush, no hood | **D** | Bulletin 18 "doors are paired and capped by a hood"; paired: Geilfuss, 70 Buena Vista, Dallam-Merritt, Burr, 1356 Scott | Italianate: paired leaves, 1.3 m, door + transom 3.0-3.4 m (`light_height = h - 0.7` at 4.0 m). Hood/porch per R-3. |
| V-ENT-2 | (no hood, portico or recessed porch) | none | **C** | Stick recessed porch with posts and pediment (Stick 2023, L28); QA round-arched recess (584 Page, L18, McMullen) | See R-3 for the per-kind `pick`. |
| V-STP-1 | stoop riser count (`kit.write_stoop` `n = 8`) | 26 cm risers | **D** | Observer counts 10-14 (range 5-18) | `n = round(h / 0.18)` (12 at 2.1 m, 13 at 2.3 m). |
| V-STP-2 | stoop width `entry_w - 0.5` | 2.93 m | **D** | Observer 1.1-1.5 m; adversary: "wide front stairs" noted as unusual | 1.3 m (draw 1.1-1.5), aligned under the door. |
| V-STP-3 | stoop material | stone | **D** | Geilfuss "wooden staircase"; Burr "wood steps"; granite/concrete only on rich or later houses (McMullen, Wilford) | Wood (painted the trim colour); stone weight 0.1 for grand. |
| V-TOP-1 | false front: 0.5 frieze + bracketed cornice, 1.6 m | Italianate and Stick identical | **A** (existence, height) / **B** (detail) | Liberty "corniced false fronts masking gable roofs"; observer 1.1-1.8 m band, 8-12 brackets at 0.6-0.9 m, paired at ends and bay angles | Keep 1.6 m (draw 1.3-1.8). Frieze panels between brackets; bracket pitch 0.7 m, pairs at the ends and over each bay arris. |
| V-TOP-2 | Stick top | same as Italianate | **C** | L28 "pediments over entry and bay", L29 "arch overhanging bay"; Walter, Stick 2023 gablet with sunburst | Stick: a gablet over the bay, weight 0.7; thinner, longer brackets. |
| V-TOP-3 | QA gable rise | 3.4 m (≈ 42° on a 7.62 m front) | **B** | Observer rise 0.6-0.9 × gable width, 50-60° (M-L) | Rise = 0.62 × gable width (≈ 51°); flagged for a photo check (§5). |
| V-TOP-4 | QA gable form: 0.25 m verge, no base, flat wall | flat-faced | **C** | Overhanging gable on brackets (L41; 584 Page); moulded frieze and cornice at its base (584 Page, L9) | Gable projects 0.4-0.6 m over the bay on brackets, over a full entablature continuing across the front. |
| V-TOP-5 | QA attic window | one, ≤ 1.8 m | **B** | 584 Page "paired attic windows"; L19 Palladian | Per-house `pick`: pair 0.5, single 0.3, Palladian group 0.2. |
| V-TUR-1 | turret gate `queen_anne and klass in (comfortable, grand)` | class-gated | **C** | Builder turrets: Wilford ~23 ft, 584 Page 25 ft; rare: 1/7 Liberty QAs, 0/6 Steiner | QA `pick` independent of class: mid-block 0.15 (comfortable 0.25, grand 0.4); corner 0.8 once a corner site exists (O-9). |
| V-TUR-2 | turret: square, as wide as the bay, rising a full storey above the eave | square box | **C** | Round (584 Page), polygonal (Wilford, Spencer octagonal), domical; 584 Page starts low | Round or octagonal drum (`pick` round 0.6 / octagonal 0.4), ~0.85 × bay width, a short turret storey (~2.0 m), roof cone rise ≈ 1.5 × drum width, finial. |
| V-PNT-1 | `paints`, one per house, cream trim | sage/blue/cream/rose | **C** | Revival practice is 3+ colours (1960s on); period Italianate light stone tones (obs, M) | Two modes. `period`: Italianate cream/buff/stone grey/white with near-tone trim; Stick/QA olive/ochre/Indian red/umber with 2-3 contrasting trims. `revival`: 3-5 colours. Default `period`. |
| V-MAT-1 | `wall_material` clapboard | lap clapboard | **B** | "Rustic siding covers most buildings" (Liberty); channel rustic (70 Buena Vista), V-groove (Dallam-Merritt) | Channel rustic siding, ~0.13 m exposure; rusticated boards on the basement (Geilfuss). |
| V-KLS-1 | what `klass` changes | turret and 3rd storey only | **D** | Wealth drives width, Corinthian portico, quoins, towers, mansards (L22, L30, L31, Stadtmuller, Geilfuss, Westerfeld, B7, B8); builders vary ornament, not massing | Route `klass` into portico weight, quoins, width draw, mansard and tower weights (§4); not into the turret gate. |
| V-SEED-1 | seed arithmetic (`seed % 2/3/4`) | correlated choices | **C** | Derived (not in either report): side yard ⇒ rose paint and single_right | Every choice its own `pick`/`draw` stream. |

### 2b. DRAWING problems (renderer / writers, seen in the strip)

| ID | Problem | Grade | Evidence | Fix |
|---|---|---|---|---|
| D-1 | Stoop drawn as a stepped side profile (reads as a stair running along the facade), no railing or newel | **D** | Observer R16: straight, perpendicular; adversary S1 | In elevation draw a perpendicular stair front-on: a stack of tread nosings between two railings with turned balusters and a panelled newel with a ball finial at the bottom. Keep the profile writer for a turned (parallel) run, weight 0.15. |
| D-2 | Bays do not read as projecting: no shade on the side faces, cornice does not break forward | **C** | Adversary S12; observer R15 | Tone the side faces one step darker; break the cornice and frieze forward over the bay, with a bracket at each arris. This makes the model's central parameter (side share) visible. |
| D-3 | Stick side faces hold a 0.30 m light in a 0.29 m cell | **C** | Derived; adversary S4 | Fixed by V-BAY-2; the renderer should also refuse a light wider than its cell. |
| D-4 | Turret: grey square box, `wall_material = 'shadow'` on the cone | **C** | Adversary S7 | Draw a drum with vertical curved-sash divisions and a shingled cone (tone, not flat grey), finial. |
| D-5 | QA gable: flat triangle, empty field | **C** | Observer R22; adversary S6 | Fish-scale shingle field, bargeboard, finial, sunburst at the apex (weight 0.5). |
| D-6 | Siding texture is lap clapboard everywhere | **B** | Both | Channel rustic hatch; shingle band between floors on QA (O-6). |
| D-7 | Side-yard fence drawn by `kit.balconette` as a short black railing | **C** | Adversary S11 | A board fence or gate ~1.8 m tall in the wall colour. |
| D-8 | Cornice brackets small and evenly spaced; no frieze panels | **B** | Observer R21 (8-12 brackets, paired at ends and bay angles) | Larger scrolled brackets, frieze panels between, pairs at the ends. |

### 2c. OMISSIONS (ranked by how often the evidence shows them)

| ID | Missing | Grade | Evidence | Frequency for weights |
|---|---|---|---|---|
| O-1 | Door hoods, porticoes, recessed porches | **C** | Most houses with an entry description (both reports) | See R-3. |
| O-2 | Flat-front Italianate | **C** | Bulletin 18; L16, L35; 2119 Bush, Beideman, 1321 | See R-7. |
| O-3 | Window hoods and pediments (arched hood moulds, entablature + triangular/segmental pediment); Stick sunburst panels | **C** | B1, B3, B8, L12, L16, L38; 1249 Scott, Beideman 45; 2119 Bush (different per floor) | Italianate per-floor `pick`: arched hood mould + keystone 0.45, segmental pediment 0.25, triangular pediment 0.2, flat cornice hood 0.1. Upper floor differs from parlour floor with weight 0.4. |
| O-4 | Flats: one door per unit at the top of one stoop | **C** | L6, L8, Beideman 33-35 | 2-flat weight 0.25 (M; many Liberty "flats" are conversions). |
| O-5 | Garage cut in under the bay | **B** (a "now" mode, not period) | Liberty; observer ~50% of photos | `now` mode only: 0.5. |
| O-6 | QA shingle bands and patterned gable fields | **C** | 584 Page, Belden, Wilford, 1550 Page | QA: shingle band at a floor line 0.6; gable field shingled 0.8. |
| O-7 | Mansard third storey on large Italianates | **C** | Burr, Dallam-Merritt | Grand Italianate with a third storey: mansard 0.7. |
| O-8 | Frieze attic lights between brackets | **B** | TREA, Beideman 45 | Italianate 0.3. |
| O-9 | Corner lots (bays round the corner, turret, store below) | **C** | 1249 Scott, Sacramento HABS, Pierce & Waller | Needs a `corner` site field. |
| O-10 | Quoins and corner pilasters at the facade edges | **C** | 1356 Scott "split pilasters"; Geilfuss, L22 quoins | Italianate corner pilaster 0.7; quoins grand 0.5, comfortable 0.15. |
| O-11 | QA balcony or loggia over the entry | **B** | L18, McMullen, 1550 Page | QA 0.3. |
| O-12 | Twins / mirrored pairs; shared builder design along a row | **B** | L2/L3, L24, B2, B9/B10, Steiner | Row generator: neighbour repeats or mirrors the design with weight 0.4. |
| O-13 | Setback / front garden; hill stepping | **B** | Liberty ~12 ft; Western Addition ~0; Noe, Waller | District parameter, not a per-house pick. |

---

## 3. What the strip gets right

An expert would recognise all six panels as San Francisco: the asymmetric bay + entry column, the raised basement with the door up a stair, false fronts on the Italianate and Stick, a gable on the Queen Anne, segmental heads and keystones on the Italianate against flat heads later, one window over the door, mirroring, and the date order. Both reports list these. What would make an expert reject the drawings is concentrated in five places: the stoop, the mullioned Italianate bay, the bare door, the Queen Anne (extra floor, square turret, low flat gable), and the squat proportion.

---

## 4. Recommendations (ranked: impact on expert acceptance first, then cost)

Cost: **S** = a parameter or one rule; **M** = a few rules or a writer change; **L** = a new variant or writer.

| # | Change | New value | Evidence | Cost |
|---|---|---|---|---|
| R-1 | Stoop: risers, width, material, front-on drawing | `n = round(h / 0.18)`; width 1.3 m (draw 1.1-1.5); wood; front-on with railings and a newel (D-1). Turned parallel run: weight 0.15 (0.4 on setback/hill lots) | V-STP-1..3; observer R16; adversary C21 | S (numbers) + M (writer) |
| R-2 | Italianate bay: one window per face | `side_share.italianate = 0.25`; pair rule `when` adds `kind != 'italianate'` | V-BAY-1 | S |
| R-3 | Entry by kind (per-house `pick`) | **Italianate:** paired leaves 1.3 m + transom (0.9) or single (0.1); hood on scrolled consoles 0.6, columned portico with balustrade 0.4 (grand: 0.2 / 0.8). **Stick:** recessed porch 1.2 m deep, two posts, gabled pediment 0.8; console hood 0.2. **QA:** round-arched recessed porch 0.5, columned portico with pediment 0.4, plain recess 0.1 | V-ENT-1/2; Bulletin 18; both reports | M-L |
| R-4 | Third storey and bay height | Third storey pick 0.03 / 0.10 / 0.50 (modest-ordinary / comfortable / grand), independent stream; bay on parlour + chamber only; Italianate bay height pick 2-storey 0.85 / parlour-only 0.15 | V-STO-4, V-BAY-4 | S |
| R-5 | Queen Anne as its own massing | Bay plan pick (per house, upper floor may differ): slanted 0.35, square-over-slanted 0.30, round/tower 0.20, square 0.15. Gable rise 0.62 × width, overhang 0.5 m on brackets over a full entablature; attic pick pair 0.5 / single 0.3 / Palladian 0.2; shingle band 0.6. Turret pick (not class-gated): 0.15 mid-block, 0.25 comfortable, 0.4 grand; drum round 0.6 / octagonal 0.4 | V-BAY-3, V-TOP-3..5, V-TUR-1/2, D-4, D-5 | L |
| R-6 | Type by date as a ramp | Weights (Italianate / Stick / QA): ≤1877 1/0/0; 1878-79 .9/.1/0; 1880-81 .7/.3/0; 1882-83 .5/.5/0; 1884-85 .3/.65/.05; 1886-87 .1/.6/.3; 1888-89 0/.45/.55; 1890-91 0/.25/.75; ≥1892 0/.1/.9. Late Italianate (1882-86) takes a square bay with weight 0.3 | V-TYPE-1; Bulletin 18 ranges; adversary's 6 misses (1880, 1882, 1884 ×2 Italianate; 1889 Stick). Shape H, exact weights M-L | S |
| R-7 | Flat-front Italianate | Weight among Italianates: 0.5 before 1870, 0.25 for 1870-77, 0.1 after; modest 1.5×, grand 0. 3 openings per floor; on a front < 6.5 m, 2 (door + paired window) | V-TYPE-2; Bulletin 18; Liberty | L |
| R-8 | Storey heights and proportion | basement 2.3 (draw 1.8-2.7), parlour 4.0 (3.8-4.3), chamber 3.6 (3.4-3.8); false-front band 1.6 (1.3-1.8). Target 1.5-1.65 : 1 | V-STO-1..3, V-STO-5 | S |
| R-9 | Show the bay's projection | Shade side faces; cornice and frieze break forward over the bay with a bracket at each arris; Italianate arrises as colonnettes | D-2, V-BAY-7 | M |
| R-10 | Double-bay layout | `w >= 12.0 or (klass == 'grand' and w >= 10.5)`; Italianate only; always a central portico | V-LAY-3 | S (+ R-3's portico) |
| R-11 | Window hoods and Stick ornament | O-3 weights; Italianate head pick segmental 0.65 / round 0.35 per floor; Stick gablet over the bay 0.7 (V-TOP-2) and sunburst panels over windows 0.5; QA transom lights | O-3, V-WIN-2, V-TOP-2, V-WIN-4 | M |
| R-12 | Independent random streams | Replace every `seed % k` with its own `pick`/`draw`; remove the duplicate `_PAINTS` in grammar.py (read the param) | V-SEED-1 | S |
| R-13 | Wealth routing | `klass` feeds R-3 portico weight, O-10 quoins, R-4 third storey, O-7 mansard, R-5 turret, width draw (R-15); nothing else gated on class | V-KLS-1 | S once R-3..5 exist |
| R-14 | Paint and siding | `period` mode default (light stone tones for Italianate; earth palettes with 2-3 trims for Stick/QA), `revival` mode 3-5 colours; channel rustic siding, rusticated basement | V-PNT-1, V-MAT-1, D-6 | M |
| R-15 | Width and side yard | Width draw: 25 ft 0.7, 20-24 ft 0.15, 26-30 ft 0.12, 37-50 ft 0.03 (grand: 0.4 for 37-50 ft). Side yard 0.10 on 25 ft lots, 0.5 on wide/grand; fence drawn as boards (D-7) | V-LAY-4, R1 of observer; Liberty | S |
| R-16 | Flats | 2-flat pick 0.25: two doors side by side under one hood or in one recess | O-4 | M |
| R-17 | Bay share | Default 0.50, draw 0.45-0.56 | V-LAY-1 | S |
| R-18 | Cornice detail | Bracket pitch ~0.7 m (8-12 on 25 ft), pairs at ends and bay arrises, frieze panels; attic lights 0.3 on Italianates | V-TOP-1, D-8, O-8 | M |

The first five fix what an expert sees first. R-1, R-2, R-4, R-6, R-8 and R-12 are each a parameter or a guard and could land together in one change.

---

## 5. Open ties a photo check should settle

1. **Gable pitch** (V-TOP-3): one straight-on photo of the Steiner row or Waller St.
2. **Slanted-bay face widths vs bay share** (V-BAY-1): measure centre face, side face (apparent) and the flanking wall on 2432 Washington and 1239 Scott.
3. **Proportion** (V-STO-5): sidewalk-to-cornice on three level-street houses, to separate floor height from downhill basements.
4. **Basement window form** (V-BAY-5) before garages: any HABS photo of an unaltered raised basement.

---

## 6. Verdict

**Rules: 7 A, 13 B, 11 C, 9 D** across 40 rows (counting a split grade by its first letter; drawings and omissions separate). The skeleton is right: an expert would name the style and the three types from these drawings. It would not accept them as they stand, chiefly for the stoop, the paired Italianate bay sash, the bare doors and the Queen Anne. R-1 to R-5 are what it takes to pass, and most of R-1, R-2 and R-4 are parameter changes.
