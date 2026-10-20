# Venice palazzo model: independent grading

Assessor brief: grade `typologies/venice/venice.toml` (+ `grammar.py`) and its rendered strips against four independent evidence sources. I wrote neither the model nor the evidence. No files were changed except this one.

**Inputs**
- Model: `src/buildings/typologies/venice/venice.toml`, `grammar.py`. Renders: `docs/strips/venice.png`, `docs/strips/venice_byzantine.png`, and the blind images (`scratchpad/blind/img*.png`).
- Evidence:
  - `observer.md`: 36 fronts, blind to the model. Dimensions are estimated from photos.
  - `adversary.md`: 27 buildings, 20 legible Gothic fronts, plus Ruskin's measured spans.
  - `judge_a.md`, `judge_b.md`: two blind judges, 16 shuffled drawings.
- Key (Venice rows only):

| Image | Style | Caption |
|---|---|---|
| img01 | venice_byzantine | 1230, 22 m, comfortable |
| img04 | venice_byzantine | 1250, 16 m, comfortable |
| img08 | venice_byzantine | 1200, 12 m (Ca' da Mosto) |
| img12 | venice_byzantine | 1225, 30 m, grand (Fondaco) |
| img02 | venice | 14 m, ordinary |
| img03 | venice | 19 m, grand |
| img05 | venice | 25 m, grand |
| img09 | venice | 16 m, comfortable |
| img13 | venice | 11 m, ordinary |
| img15 | venice | 22 m, grand, two gates |

**My own photo check (tie-breaker).** I viewed four straight-on Wikimedia Commons photos in the browser pane:
- `Palazzo_Ca_Foscari_facciata_Canal_Grande.jpg`
- `Palazzo_Bernardo_(Venice).jpg`
- `Ca_Loredan_Ambasciatore_Canal_Grande_Venezia.jpg`
- `Palazzo_Pisani_Moretta_Canal_Grande_Venezia.jpg`

These are marked **[own check]** below. What I read from them:

| Palazzo | Storeys | Polifora lights (PN1 / PN2 / 3rd) | Wing balconettes | Gates | Mezzanine | Other |
|---|---|---|---|---|---|---|
| Ca' Foscari | 4, no mezzanine | 8 / 8 + tracery / 6 | none on any nobile wing window | one, **round**-headed | none | water-storey windows pointed |
| Bernardo | 4 | 6 / 6 + quatrefoils / 4 | none | two, at about the quarter points, pointed-ogee | none | PN2 balcony only at the two end lights |
| Loredan dell'Ambasciatore | 3, **nothing above PN2** | 4 + quatrefoils / 4 | none | one, pointed, rising through the mezzanine zone | small windows **in the wings only** | PN2 polifora is a recessed loggia, no balcony |
| Pisani Moretta | 3 + frieze, **nothing above PN2** | 6 / 6, both traceried | yes, both floors | **two, side by side under the polifora** | wing tier only | stone balustrades; storeys about equal; stone base course |

All four: Istrian quoins or dentil corner strips, stone-framed wing windows, white trim on brick or plaster.

---

## 1. Where the evidence disagrees, and how I weigh it

| Question | Observer | Adversary | Judges | My check | Weighed conclusion |
|---|---|---|---|---|---|
| **Is anything above PN2?** | "Normal" is 3 full storeys + attic/top floor (R6) | 8 of 20 have nothing above PN2 (named list) | A objects to 3 stacked polifore ("even Ca' Foscari has only two") | Pisani and Loredan Amb. have nothing above PN2. Foscari and Bernardo have a full third floor *with a polifora*. | **Adversary wins.** It names buildings; the observer probably counted the frieze band (which he notes at Pisani) as an "attic". Judge A is factually wrong about Foscari, so a third-floor polifora is legitimate. It is over-produced, though. |
| **PN1 vs PN2 light count** | Usually the same (H) | Equal in 8/17, PN2 fewer in 5, PN2 more in 4 | B: always equal (3 refs). A: unequal is odd. | Equal in 4/4 | **Equal is the default.** "PN2 = PN1 − 1" is the least common case. |
| **PN2 storey height** | PN1 usually tallest, PN2 equal or 5-10% less (estimated) | PN2 equal or taller in 4/4 (measured px ratios) | n/a | Pisani about equal; Foscari PN2 tallest (relief frieze) | The difference is **near zero**. The model's −0.4 to −0.6 m is at the edge of the observer's range. Use equal, or −0.2 m at most. |
| **Wing balconettes on PN1** | "Almost always" (H) | Absent in 5 (Foscari, Bernardo, Morosini Brandolin, Loredan Amb., Bembo), present in 7 | Both judges list poggioli as "right" | Absent in 3/4 (Foscari, Bernardo, Loredan Amb.), present at Pisani | **Adversary wins**: about half. The observer's H rating is not supported by its own listed evidence. |
| **Mezzanine** | Wings only, inside the water storey (H) | About 50%, not wealth-linked | A: "correct, typical" | Loredan Amb. and Pisani: wings only; Foscari, Bernardo: none | **Wings only, about 50%, independent of class.** Judge A accepted the mezzanine but did not test its extent. |
| **Gate head** | Pointed or ogee | Pointed 5, ogee 2, round 3 | A: ogee correct | Round (Foscari), round with tracery (Pisani), pointed-ogee (Bernardo), pointed (Loredan Amb.) | **Mixed.** Ogee-only is a narrowing, not an error. |
| **Two-gate placement** | Side by side under the polifora (Pisani), or at the quarter points (Bernardo) | The model's inner-wing placement matches Bernardo and Morosini Brandolin exactly | B: FAIL ("off the portego axis"); A: gates should flank the centre | Bernardo matches the model; Pisani is a central pair | **The model's layout is attested** but reads wrong to experts. The judges knew only Pisani/Giustinian. The central pair should be the default; keep the wing variant as the minority. |
| **Byzantine centre/wings** | Continuous arcade over most of the width, wing groups set off by a wider pier | Ruskin: "divided, in each case, into a centre and wings" | B: no wings means FAIL; A: needs solid flanking bays | — | **All agree** once read closely: the arcade is grouped centre + wings. The model's uniform end-to-end arcade is wrong. |
| **Upper/lower arcade ratio** | "About twice" | 1.44-1.8 (Ruskin, it.wiki) | B: 13/7 = 1.86 "good"; A: counts "unrelated" | — | The model's formula `2n−1` already gives 1.67-1.86, so the ratio is fine. The docstring's "twice" is the only thing wrong. |
| **Merlons** | L/M confidence; Byzantine merli existed in old views | Invented in the 1869 rebuild; drawn about ⅓ real size | A: the merlons are the "silhouette signature", too small; B: without them the towers read as Italianate | — | History says restoration; experts expect them. **Keep them, Fondaco-type only, at a larger size**, and label them "as restored". |
| **Byzantine storey count** | Originally 2 (H) | Same | A: real survivors carry later floors | — | 2 is correct as a reconstruction. The later-floor accretion is an optional variant, not an error. |
| **Polifora light width** | 0.85-1.1 m | ≈1.0 m (person scale) | A: drawn 1.3-1.6 m | — | Judge A scaled from an assumed 4 m gate. The model's real lights are about 1.0-1.2 m. They get wide only on grand fronts, where the 5-light cap stretches them. |

**Sample size and method.** Observer and adversary: about 30 and 20 Gothic fronts, mostly famous Grand Canal palazzi, metres estimated (±10-20%), ratios reliable. Adversary is the only source with a measured scale (one person-scaled photo, plus Ruskin's printed spans). Judges: few references each (A about 13 Venetian, B about 9). They are strong on what looks wrong and weak on frequencies. Where they assert "always" from 3 examples, the larger samples override them.

---

## 2. Grades

A = matches the evidence; B = roughly right, needs tuning; C = wrong, or missing a key variant; D = contradicted.

### 2a. RULE problems (venice.toml)

**Gothic**

| Rule / param | Model | Grade | Evidence | Corrected value / rule |
|---|---|---|---|---|
| Tripartite wing \| centre \| wing | always, symmetric | **B** | About 60% symmetric (Obs R4, Adv G1). L-type, corner and doubled types make up ~40%. | Keep as the default. Add an asymmetric layout (see Omissions). |
| `centre_share` | 0.40 incl. 0.45 m piers | **B** | Measured shares 33-39%, median 36% (Obs R2, Adv G2). Polifora absolute width is 6-9 m, tracking the portego. | `centre = clamp(0.36*w, 5.5, 9.5)`. Wider fronts get wider wings, not a wider polifora. |
| `wing_bay`, `wing_end`, `max_bays` 3 | 1.8-2.8 / 0.5-1.4 | **B** | 2 per wing at 14-21 m, 2-3 above 23 m, 0-1 below 12 m (Obs R3, Adv G13; own check: 2 at all four). The strips give 1 per wing at 14 m and 16 m. | Require 2 bays per wing for 14-22 m, e.g. `wing_bay=[1.6,2.0,2.6]` with fit preferring more bays. Observer: inner window 1-1.5 m off the polifora pier. |
| `water_h` | 4.0-5.0 (0.6-1.0 m below PN1) | **C** | The water storey is as tall as a piano nobile (Obs R8: 4.5-6; Pisani ≈ equal [own check]). | `water_h ≈ nobile1_h` (modest 4.6 … grand 5.8). It *contains* the mezzanine. |
| `mezzanine_h` and its placement | 2.3 m full-width storey, rich and ≥16 m | **C** | Wings only, inside the water storey; the centre is the double-height androne with the gate (Obs R9 H; Loredan Amb., Pisani [own check]). About 50%, not tied to wealth (Adv G5). | Make it a wing-only upper tier of small windows inside `water` (sill ≈ water_h − 1.9). The gate rises through it. Frequency ~50% by seed, any class ≥14 m. |
| `nobile2_h` | PN1 − 0.4…0.6 | **B** | Equal, or ±5% (Adv G4 measured, Obs R8). | `nobile2_h = nobile1_h` (or −0.2). |
| Top storey `third` / `attic` | always one; third if w ≥ 21 or (rich and odd seed) | **C** | 8/20 have nothing above PN2 (Adv G6; Pisani, Loredan Amb. [own check]). Wide Pisani and Ca' d'Oro have no third floor (Adv G7). | Three outcomes by seed: **none ~40%**, low attic ~35%, full third with polifora ~25% (grand/comfortable only). Drop the width trigger. |
| `attic_h` 2.9 | | **A** | 2.8-4 m, 55-70% of a PN (Obs R8). | Keep. |
| `third_h` 4.4 | | **B** | Foscari and Bernardo third floors are about 0.8-0.9 × PN [own check]. | `0.85 * nobile1_h`. |
| Polifora light count `want` | grand 5 / else 4; −1 on PN2 and third; min 2 | **D** | Modal grand count is 6, range 3-8 (Obs R11, Adv G16). PN2 equals PN1 by default (Obs, Adv 8/17, B, own check 4/4). | `n1 = clamp(round(polifora_w / 1.25), 3, 8)`, capped by class (ordinary 4, comfortable 5, grand 6; grand with polifora ≥ 8.5 m may take 7-8). **`n2 = n1`** (rare seed variant ±1). Third floor `= max(3, n1 − 2)`. |
| `polifora_min_light` 0.95 | | **A** | 0.85-1.1, typically 0.95 (Obs R12; Adv G17). | Keep. |
| `divider_width` 0.24 | | **B** | Shaft 0.2-0.3, capital 0.35-0.45 (Obs R12, Adv G18). | 0.28, with the capital drawn 0.4 wide. |
| Light heights (wing and polifora) `h − sill − 1.2` | about 4.6 m on grand PN1 (h:w ≈ 4) | **B** | 2.6-3.6 m, h:w 2.5-3.5 (Obs R12, R16). | `light_height = min(h − sill − 1.2, 3.2 * light_width)`. Put the remaining wall above in a stone panel or tracery band. |
| Wing light `light_width` 1.1 | | **A** | 1.0-1.3 (Obs R16), ≈1.0 (Adv). | Keep. |
| Wing balconettes `balcony` | always on PN1; PN2 when `seed%3 != 2`; never on the third | **C** | Present in about half (Adv G15; own check 1/4). Foscari: none on PN1, but some on the third (Adv). | `wing_balconies` by seed ~55% applies to PN1 and PN2 together. Allow it on a third floor that has a polifora. |
| Polifora balcony | on every nobile floor | **B** | Variants: both floors (Pisani, Foscari); PN1 only (Loredan Amb., Morosini Brandolin); ends only (Bernardo PN2, Fortuny) (Adv G20, own check). | Seed choice: both 60% / PN1 only 25% / ends-only on PN2 15%. |
| Polifora `surround_kind = "none"` | | **D** | Every polifora sits in a rectangular Istrian frame with a dentilled top band (Obs R14 H, Adv G19, both judges). | `surround_kind = "dentil_panel"` (rule) plus the drawing support for it. |
| Gate `gate_w` [2.0, 3.0] | | **A** | 2.2-3.5, typically 2.6 (Obs R21); 1.8-3 (Adv G8). | `[1.9, 3.2]`, if anything. |
| Gate height `2w + 0.2` | | **A** | Ratio 1.7-2.0 (Adv G9; Obs 3.8-5.5 m high). | Keep. |
| Gate head `ogee` | always | **B** | Pointed most common; ogee and round both occur (Adv G10, own check). | By seed: pointed 45%, ogee 30%, round 25%. |
| Gate flanked by lights when there is room | | **A** | Mastelli, Foscari (Obs R22, Adv G11). | Keep. |
| `two_gates` | ≥20 m and odd seed (50%); inner wing bays | **B** | The placement is attested (Bernardo, Morosini Brandolin). The central pair (Pisani) is equally attested and is the only form judges accept. The frequency is too high: ~4 cases in ~20. | ~25% of ≥20 m fronts. Of those, 60% a **central pair under the polifora** and 40% wing placement, with the gate straddling the centre/wing boundary as at Bernardo. |
| Water-storey lights: round, 0.9×1.6, sill 1.6 | | **B** | Round, pointed and rectangular-barred all occur (Adv G21). Lower tier 0.7-0.9 × 1.0-1.3 (Obs R9). Judge A: too tiny. | Seed the head (round / pointed / flat-barred); 0.9 × 1.4. |
| Mezzanine/attic lights 0.75 × 0.95 | | **B** | Upper tier 0.8-1.0 × 1.2-1.6 (Obs R9). | 0.85 × 1.25. Align them to the wing axes (Judge B: img03 mezzanine off the polifora axes). |
| Mezzanine and attic: 3 windows in the centre | | **C** (mezzanine) / **B** (attic) | The centre has no mezzanine (Obs R9). | Mezzanine: none in the centre. Attic: windows on the light axes below. |
| `wall_material = stucco_rose` | always | **C** | Brick ~40%, rose ~35%, cream ~25%, red/ochre occasional (Obs R33, Adv G23; own check: 2 brick, 1 rose, 1 cream). | Seed: brick 0.4, rose 0.3, cream 0.2, red/ochre 0.1. Istrian trim on all. |
| String course at the top of each storey; bandeau | | **B** | At floor/balcony line (right place). Real ones are dentilled or rope (Obs R24, Adv G24). | `course_kind = "dentil"` / `"rope"`. |
| Cornice 0.45, modillioned | | **A** (rule) | 0.4-0.8 projecting, dentil + corbels (Obs R26). | 0.6. Drawn too thin: see 2b. |

**Veneto-Byzantine**

| Rule / param | Model | Grade | Evidence | Corrected value / rule |
|---|---|---|---|---|
| `byzantine_until` 1300 | hard switch | **B** | A transitional 1250-1350 type with stilted pointed arches is missing (Adv B1, Obs R13). | Keep 1300, or add a 1270-1340 "gotico primitivo" head (pointed, stilted). |
| No wing \| centre \| wing; arcade end to end | | **D** | Ruskin: Loredan has 5 centre + 2 per wing, with 7 + 3 above; Farsetti 5 + 2 (Adv B2). Obs R30 has grouped wings; both judges fail img04/img08 for exactly this. | Body = wing \| centre \| wing. Centre portico of 3-7 arches, **odd**. Each wing has 1-2 closed or windowed arches, or solid wall with single arched windows, set off by a wider pier or double shaft. |
| Portico full width | | **C** | Only the Fondaco is fully open; Loredan and Farsetti have closed or windowed wings; da Mosto has a 3-arch curia (Adv B3). | Follows from the row above. |
| `portico_arch` 2.6 uniform; `max(3, …)` | | **B** | The magnitude is right (Ruskin spans 1.35-2.46 + shaft). Real arches are **graded**, widest at the centre (Adv B4). Counts are odd (Judge B, Obs counts 3/5/5). | Centre arch ×1.2, outer arches ×0.85. Force an odd count. |
| Loggia count `2n − 1` | | **A** | Gives 1.67-1.86× against a real 1.44-1.8 (Adv B5) and Fondaco 1.8 (Judge B). | Keep; fix the docstring ("about 1.5-1.8×"). In the wings: 3 lights over each 2 below. |
| Loggia balustrade `balcony = true` | | **A** (rule) | Continuous stone balustrade (Obs R30, Adv B5). | Drawn as iron: see 2b. |
| `torreselle_from` 18 m | width gate | **C** | Ca' da Mosto had torreselle (it.wiki, Adv B6). Wide Loredan and Farsetti have none. | Towers by type, not width: grand fondaco only, or a seed option ≥ 20 m. Drop the da Mosto citation in the comment. |
| `torresella_share` 0.17 | | **A** | Fondaco 13.5-22%, mean ≈ 18% (Adv B7; Obs 1/6-1/5). | Keep. |
| `tower_top_h` 3.8, one storey above the cornice | | **B** | True of the 1869 rebuild only (Adv B8, Obs R28 M). | Keep; label it "as restored". |
| Tower openings: one arch, then bifora, then trifora | | **D** | The Fondaco towers continue the arcade: 3 arches below, 4 above, 4-5 at the top (Adv B9, Obs R28, both judges). | `tower_water`: 2-3 arches at the portico pitch. `tower_loggia`: 4 at the loggia pitch. `tower_top`: 4-5 small lights. |
| `merlon_h` 1.3, `MERLON_W` 0.7 | | **C** | Fondaco merlons are ≈ 2.4 m wide × 2.9 m tall at Ruskin's scale (Adv B10). Judge A: "tiny tabs". Historically a restoration. | `merlon_h ≈ 2.4`, `MERLON_W ≈ 1.8`, gap ≈ 0.6 × width, stepped shoulders with a pointed tip. Only on the towered grand type. |
| `crenellated = grand` | | **B** | Restoration-only (Adv), but the expected silhouette (judges). | Tie it to the towered Fondaco type, not to class alone. |
| `istrian_stone` wall | | **B** | Fondaco and Loredan are stone-faced; Farsetti, da Mosto, Falier are plaster or brick with stone arcades (Adv B11). | Seed: stone 50% / cream plaster 50%. The arcades are always stone. |
| Two storeys | | **A** | Originally 2 (Obs R7 H, Adv). | Keep. Optional variant: later Renaissance upper floors (Judge A e; Adv omission 17). |
| `portico_h`, `loggia_h` | | **B** (untestable) | Plausible. Judge A saw a deep blank band between the floors (img04). | Keep the heights, but fill the band with a paterae/formelle frieze (Omissions). |

### 2b. DRAWING problems (the renderer, flagged by the judges)

| Drawing decision | Grade | Who flagged it | Correction |
|---|---|---|---|
| **Ogee drawn as a Gaussian "bell"**: horizontal tangent at the foot, rounded top, no point | **D** | Judge A (error a, "#1, cheapest fix"), Judge B (error e, "single most obvious fake signal"), Adversary (render 1). Confirmed in img13. | S-curve: vertical tangent at the springing, convex lower half, inflection at ~0.6 of the rise, concave to a **sharp point**, with a small finial. Rise ≈ 0.6-0.8 × span. Optional trefoil cusping. |
| **Arches do not spring from capitals.** Polifora colonnettes run up to the apex with capitals beside the tips; Byzantine capitals sit ~20 px above the springing. | **D** | Judge B (f, j, pattern 1), Adversary ("separate bell shapes with stubs"). Visible in img13 and img12. | Set `springing_y = capital_top_y` for every divider. The column ends at the springing, and the spandrel above is wall (or tracery). |
| **Iron bar railings** under polifore, wing windows and the Byzantine loggia | **D** (polifora, loggia) / **B** (wing poggioli) | Both judges (A-b, B-g, B-m). Obs R15: stone balustrade on 4-8 corbels, 0.9-1.0 m high. | Stone balustrade of small colonnettes on corbels, projecting 0.4-0.6 m. Iron only as a seed "later alteration" on poggioli or the third floor (Bernardo). |
| **Water gate drawn as a rectangular panelled double door under a bell lunette, in a frame that cuts the string course** | **C** | Adversary (render 2), Judge A (img13: too large, frame cuts the course). Judge B found the lunette-over-door plausible. | One arched opening (dark void or iron grille), springing at ~0.65 of the height, in a stone frame with a dentil edge, kept inside the water storey. Steps and pali are optional. |
| **Byzantine supports drawn fluted, as pilasters** (`order = "corinthian"`; tower edge `order = "pilaster"`) | **D** | Judge A (a: "wrong order by ~300 years"), Judge B (i). | `order = "byzantine"`: smooth round shaft, basket/impost capital, stilted arch with a dentilled archivolt. Remove the fluting. Draw the tower edge as a plain projecting arris. |
| **Portico drawn glazed with mullions to the ground** | **C** | Judge B (k: "reads as a shopfront") | Portico openings as open dark voids (no glazing bars). |
| Polifora columns too thin, so the polifora reads as one glass wall | **B** | Judge A (e) | `divider_width` 0.28 + a 0.4 capital (see 2a). |
| Cornice drawn as a hairline | **B** | Adversary (render 7, G24) | Draw 0.6 m deep with modillion brackets and a tile eave. |

### 2c. OMISSIONS

Ranked by how often the evidence names them.

| Missing | Grade | Evidence |
|---|---|---|
| **Quatrefoil tracery band** over the polifora, on one nobile floor (both on the richest fronts), 15th c. | **C** | Adv: 10/20; Obs R13 H; both judges; own check 4/4. |
| **Istrian quoins / dentil corner strip / rope arris**; stone-framed wing windows (rectangular dentil panel) | **C** | Obs R17, R25 H; Adv omissions 5-6; Judges A-d, B-h; own check 4/4. |
| **Paterae and formelle** in Byzantine spandrels and in the band between the floors | **C** | Both judges ("defining Veneto-Byzantine ornament"), Obs R31, Adv 15. |
| **Asymmetric L-type and corner-polifora layouts** (~40%) | **C** | Obs R4, Adv G1. |
| **Narrow palazzetto (<12 m), bipartite or mono, no wings, sometimes no gate** | **C** | Obs R5, Adv G1 (Contarini Fasan). The 11 m strip front is a miniature grand palazzo. |
| **Doubled (twin) palazzo**: two tripartite units, each with its own polifora and gate | **B** | Obs R4d, Adv G12 (Giustinian, Soranzo, Bembo). |
| **Stone base course / ashlar water storey** | **B** | Obs R32, Adv G21; Pisani [own check]. |
| **Roof, funnel chimneys (fumaioli), altana** | **B** | Obs R29 H, Judge B (h), Adv 10. |
| **Date sensitivity after 1300** (pointed or trilobed heads before ~1380, ogee after, tracery after ~1420) | **B** | Obs R13, Adv G14. |
| Ogee finial, trefoil cusping | **B** | Judge A (a). Belongs with the ogee redraw. |
| Graded Byzantine arches, double shafts between centre and wings | **B** | Adv B4, B14 (Ruskin). |

---

## 3. Pass/fail: how the blind judges scored the Venice drawings

**Identification.** Both judges correctly identified the city and the type of **all 10** Venice drawings:
- Gothic: img02, 03, 05, 09, 13, 15.
- Veneto-Byzantine: img01, 04, 08, 12.
- Both named img12 as the Fondaco dei Turchi type (Judge B "very high" confidence) and recognised img01 as the same type without merlons.
- Judge A's width estimates were within about 20% for most fronts. They overestimated the small Byzantine ones (img08 at 16-18 m against a real 12 m).
- Identification was weakest for img04 and img08 ("medium / medium-low"; "could pass as an Italianate arcade, orangery or Spanish portal").

**Scores**

| img | Truth | Judge A (R/P of 5) | A: passes? | Judge B | Decisive error |
|---|---|---|---|---|---|
| 13 | Gothic 11 m ordinary | 4/3 | **at a glance** | passes with flaws (best of family) | bell arches, iron rails |
| 02 | Gothic 14 m | 4/3 | recognised, not convincing | passes with flaws | bell arches; 4-over-3 count mismatch |
| 09 | Gothic 16 m | 4/3 | recognised, not convincing | passes with flaws | bell arches; 4-over-3; bare ground floor |
| 03 | Gothic 19 m grand | 4/3 | recognised, not convincing | passes with flaws | iron rails; 5-over-4 mismatch |
| 05 | Gothic 25 m grand | 4/2 | **would not pass** | passes with flaws | 5 storeys and 3 polifore with no tracery or stone balcony; mismatched counts |
| 15 | Gothic 22 m two gates | 4/3 | recognised, not convincing | **FAILS** | gates in the wing bays, centre without a gate |
| 12 | Byz 30 m Fondaco | 4/3 | recognised, not convincing | passes with flaws | fluted pilasters; arches not on capitals; tiny merlons |
| 01 | Byz 22 m towers | 3/2 | **would not pass** | passes with flaws (borderline) | pilasters, no merlons, no paterae ("Italianate villa") |
| 04 | Byz 16 m | 2/2 | **would not pass** | **FAILS** | arcade end to end with no wings; no Byzantine signature |
| 08 | Byz 12 m (da Mosto) | 2/2 | **would not pass** | **FAILS** | same as img04; even arch count |

**Tally**
- Recognition: 10/10.
- Clean pass: Judge B 0/10; Judge A only img13, and only "at a glance".
- Failed by at least one judge: img04, img08 (both judges), img15 (B), img01 and img05 (A). That is 5 of 10.
- Gothic means (Judge A): R 4.0, P 2.8. Byzantine means: R 2.75, P 2.25.

**What made drawings fail**
1. **Byzantine fronts with no wings.** This is a rule error, and it causes 2 unanimous fails.
2. **Wrong tectonics and ornament in the Byzantine drawings**: fluted pilasters, no paterae, a glazed portico. These are drawing errors.
3. **Two gates in the wing bays.** The rule is historically attested but reads wrong to an expert.
4. **The grand front over-built**: mezzanine + third floor + 3 polifore, no tracery. This is a rule error.

The bell-shaped ogee and the iron railings did not by themselves make a Gothic drawing fail. But they are named first or second in every Gothic verdict, and they are why none passes cleanly.

---

## 4. Recommendations

Ranked by impact on blind-expert acceptance, then by cost.

| # | Change | Kind | Cost | Evidence |
|---|---|---|---|---|
| 1 | **Redraw the ogee.** Vertical tangent at the springing, convex then concave, a sharp point plus a finial, rise 0.6-0.8 × span. Make every arch (ogee and round) spring from `capital_top_y`, and end the colonnettes at the springing. | drawing | low | Judges A-a, B-e/f/j; Adv render 1 (unanimous). Present in all 10 Venice images. |
| 2 | **Byzantine centre + wings.** Split `venice.byzantine_body` into wing \| centre \| wing. Centre: an **odd** portico of 3-7 arches, graded (centre ×1.2, outer ×0.85). Wings: 1-2 closed or windowed arches per side, set off by a wider pier or double shaft. Loggia above: `2n−1` arches in the centre, 3 per wing. | rule | medium | Ruskin via Adv B2/B4; Obs R30; both judges (img04 and img08 fail). |
| 3 | **Byzantine tectonics.** `order = "byzantine"`: smooth shafts, basket capitals, stilted arches, dentil archivolts, no fluting. Portico as open voids. A **paterae/formelle** band in the spandrels and in the blank band between the floors. Tower edge as a plain arris, not a pilaster. | drawing | medium | Judges A-a/c, B-i/k/l; Obs R31. |
| 4 | **Polifora light counts.** `n1 = clamp(round(polifora_w/1.25), 3, class cap)`, with caps ordinary 4 / comfortable 5 / grand 6 (7-8 when the polifora is ≥ 8.5 m). **`n2 = n1`**; third floor `max(3, n1−2)`. Replace `want` in `venice.base.the_polifora`. | rule | low | Obs R11; Adv G16 (modal 6, equal 8/17); Judge B; own check 4/4 equal. Removes the 4/3 and 5/4 mismatches cited in img02, 03, 05, 09, 15. |
| 5 | **Stone balustrades.** Balconette kind `stone_balustrade` (colonnettes on 4-8 corbels, 0.9-1.0 m high, 0.5 m projection) under the polifore and along the Byzantine loggia. Iron only as a seed "later" variant on wing poggioli or the third floor. | drawing + rule | low-medium | Judges A-b, B-g/m; Obs R15. |
| 6 | **Storey stack.** `water_h ≈ nobile1_h`. Make the mezzanine a **wing-only tier inside the water storey** (~50% by seed, any class), not a full-width storey; the gate rises through it. `nobile2_h = nobile1_h`. Top storey by seed: **none 40%** / attic 35% / third floor with polifora 25% (comfortable/grand only); drop `width >= 21`. | rule | medium | Adv G4-G7; Obs R8-R9; own check (Pisani, Loredan Amb. have nothing above PN2; mezzanines in the wings). Fixes the 5-storey img05/img03 look. |
| 7 | **Two gates.** Lower the frequency to ~25% of ≥20 m fronts. Default (60%) is a **central pair under the polifora** (Pisani Moretta); the remaining 40% are wing gates straddling the centre/wing boundary (Bernardo). | rule | low | Judge B (img15 fail), Judge A; Obs R20; Adv G12; own check. |
| 8 | **Polifora frame and tracery.** `surround_kind = "dentil_panel"` on the polifora and on wing windows. Add a quatrefoil tracery band (height ≈ light width, one quatrefoil per column) on one nobile floor for comfortable/grand fronts after ~1420, on both floors for a grand seed variant. | rule + drawing | medium | Adv G19 (10/20); Obs R13-R14; both judges; own check 4/4. |
| 9 | **Water gate drawing.** One arched void or grille in a dentil stone frame kept inside the water storey, with no panelled double door. Head by seed: pointed 45 / ogee 30 / round 25. | drawing + rule | low | Adv render 2, G10; Judge A (img13); own check. |
| 10 | **Corners and walls.** Istrian quoins or a dentil corner strip, and a stone base course. `wall_material` by seed: brick 0.4 / rose 0.3 / cream 0.2 / red-ochre 0.1. | rule + drawing | low-medium | Obs R25, R32-33; Adv G23; judges; own check. |
| 11 | **Fondaco towers and merlons.** Tower openings continue the arcade (2-3 below at the portico pitch, 4 at the loggia pitch, 4-5 at the top). `merlon_h` 2.4, `MERLON_W` 1.8. Towers and merlons tied to the grand fondaco type, not to `width >= 18`. | rule + drawing | low | Adv B6, B9, B10; both judges (img01, img12). |
| 12 | **Wing windows.** 2 per wing at 14-22 m (tune `wing_bay`/fit). `light_height ≤ 3.2 × light_width`. Wing balconettes by seed ~55%, PN1 and PN2 together. Polifora balcony variants: both / PN1 only / ends only. | rule | low | Obs R3, R12, R16; Adv G13, G15, G20; own check. |
| 13 | **Layouts.** Narrow fronts (<12 m) bipartite or mono with no wings. Asymmetric L-type (~30%). Twin palazzo at ≥30 m. `centre = clamp(0.36w, 5.5, 9.5)`. | rule | high | Obs R2, R4-R5; Adv G1. |
| 14 | **Roof and chimneys.** A hipped coppi roof and 1-3 funnel chimneys (fumaioli). Cornice drawn 0.6 m deep with modillions. | drawing | medium | Obs R26, R29; Judge B-h; Adv render 7. |

---

## 5. Verdict

The rules capture the Venetian palazzo's skeleton well enough that both blind experts identified the city and the type of all ten drawings, so the model passes the recognition test. It does not pass the fidelity test. No drawing passed cleanly with Judge B, only one (img13) passed "at a glance" with Judge A, and half were failed by at least one judge. The failures trace to a few causable defects:
- a bell-shaped "ogee" whose arches do not spring from their capitals;
- iron railings in place of stone balustrades;
- a Byzantine front with no centre/wing grouping and with classical fluted supports;
- rule slips in the storey stack, polifora counts and gate placement that the photographic evidence contradicts.

Recommendations 1-8 are mostly cheap rule and drawing changes. With them, the Gothic set should move from "recognised but not convincing" to passing, and the two failing Byzantine fronts to at least "passes with flaws".
