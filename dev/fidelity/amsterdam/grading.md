# Amsterdam canal house: independent grading

Assessor: independent. I did not write the model or gather the evidence. I read:
- the model: `src/buildings/typologies/amsterdam/amsterdam.toml`, `grammar.py`, `kit.write_stoop` (`typologies/common/kit.py:458`) and `is_middle_bay` (`common/rulefile.py:147`);
- the strip `docs/strips/amsterdam.png` and blind images img06 and img10;
- the four evidence reports: `observer.md` (blind to the model), `adversary.md`, `judge_a.md` and `judge_b.md`;
- the blind key.

I did **no** photo checking of my own. Every tie below is broken by weighing the sources, not by new photographs.

Model numbers I computed from the TOML, used throughout:

| Part | Value |
|---|---|
| Storeys | souterrain 1.5 + bel-etage 3.6 + 3.40 + 3.16 + 2.94 = **14.6 m to the eave** |
| Step gable | 2.6 + 2.4 + 1.9 = 6.9 m, so **21.5 m overall** |
| Neck gable | 2.6 + 2.3 + crown 1.1 = 6.0 m, so **20.6 m** |
| Bell gable | 3.0 + crown 1.4 = 4.4 m, so **19.0 m** |
| Cornice house | **15.2 m** |
| Bel-etage : first storey | **1.06** |
| Window height ÷ width (3-bay, light 1.36 m wide) | 1.9 / 1.76 / 1.6 / 1.43, going up |

---

## 1. Where the sources disagree, and how I weighed them

**Weighting principles:**
- Measured orthographic sources rank above photo ratios, and photo ratios rank above impressions. Orthographic sources are the Grachtenboek plates and 3DBAG. Photo ratios are subject to perspective and to later alterations.
- Larger samples rank above single houses.
- A judge's unmeasured remark ranks lowest.
- The adversary had the model in hand, so its "outline is right" verdicts carry slight confirmation risk. The observer was blind, so it carries none.

| # | Question | Disagreement | Weighed conclusion |
|---|---|---|---|
| D1 | **Height / number of upper storeys** | **Observer:** 4 body storeys above the souterrain are typical (Grachtenboek row and 3DBAG, 31 of 51), eave 14-15.5 m. **Adversary:** 2-3 uppers, and the step houses are "too tall" at 8 rows. **Judges:** 7 levels is too tall. | Both are right about different things. The **body** (14.6 m, 4 storeys) matches the 3DBAG eave height. The excess is in the **gables**: 4.4-6.9 m against the observer's 3.2-4.0 m for neck and bell (about 0.5 × width). Overall height is 19-21.5 m against a typical hmax of 16-17.5 m. The step-era houses the adversary measured (Herengracht 203) also had 2 uppers, not 3. **Fix the gables first; give pre-1665 houses 2 uppers.** |
| D2 | **Neck height** | **Judge A:** "2 levels … typical" (impression). **Observer:** 1 storey, about 0.54 w (measured, Grachtenboek 133/247 px). **Adversary:** 1 storey plus a pediment (photos of Cromhout, Singel 326, Damrak 55). | **1 tier.** Two measured or photo sources outweigh one impression. Judge B even read the 2-tier neck as a *raised* neck gable, which is itself evidence that it looks unusual. |
| D3 | **Neck width** | **Observer:** 0.40 w (measured, a run of 7 identical houses). **Judge B:** 0.40, inside a real range of 0.33-0.5. **Adversary:** 0.25-0.3 (one engraving of wide Cromhout fronts). | **0.40 stands.** The Cromhout houses are wide fronts, which pushes the ratio down. |
| D4 | **Claw-piece curvature** | **Adversary:** a concave quadrant is the "correct outline". **Judge B:** real claw pieces are convex scrolls, and the concave curve makes a "funnel". **Observer:** a quarter-round or S-scroll *filling* the triangle, high at the neck and tapering out (that is, convex). | **Convex or S-scroll**, by 2 sources to 1, and the blind sources favour it. Not photo-checked. All four agree the claw pieces must be **sandstone-coloured and ornamented**, which matters more than the curvature. |
| D5 | **Window share of the bay** | **Observer:** 0.58-0.60 (Grachtenboek, measured) and 0.5 for early houses. **Adversary:** 0.63 in the 17th c. and 0.68-0.73 in the 18th c. (modern photos). **Judge B:** 0.65-0.75 (one photo), and the drawing's 0.68 is "OK". | The model's **0.62 is inside every range**. The photos show today's fabric, which includes 19th-c. enlargements (the observer notes 0.70-0.75 for 19th-c. alterations); the Grachtenboek is schematic. Let the share rise gently with date. This is low priority. |
| D6 | **Bel-etage height** | **Observer:** 4.3 m, 1.3-1.8 × the first upper storey (measured). **Adversary:** 1.3-1.8× (4 frontal measurements). **Judge A:** "only about 10% taller", which is wrong. **Judge B:** 3.4 m is "plausible", but that figure came from scaling to an assumed width. | **The model is too flat.** Three sources against one scaled estimate. |
| D7 | **Souterrain exposure** | **Observer:** 1.5 m (1.3-2.0). **Adversary:** 0.6-1.6 m; about 0.7 m in 1618. | **1.5 m is right for 18th-c. main-canal houses.** It should be lower (about 1.0 m) before about 1640. |
| D8 | **Step count and size** | **Observer:** Renaissance type has 2-3 large steps per side; the "plainer type" has 4-6 steps of 0.5-0.9 m each, many of them restorations. **Adversary:** 3-5 per side, each about 1.2-1.4 m. **Judge A:** 3-5. **Judge B:** 5-7. **Model:** 0.75 m rise, counted as 7-9 per side. | The **rise** of 0.75 m is defensible only for the restored small-step type. The **count** is too high under any reading, because the gable has 3 tall tiers. **Fewer tiers plus a rise of about 1.2 m gives about 4-5 steps per side,** which sits in the overlap of all four sources. |
| D9 | **Step-gable pitch** | Only **Judge B** measured it: 74-77°. **Observer D4:** shoulders follow a roof of 50-60°. **Observer D8:** steps about 0.15-0.2 w deep × 2-3 m, about 64°. | The target is an envelope of **about 60-65°**. The model is 72-77°. |
| D10 | **Door side** | **Judge A** lists "door in an end bay" as right. **Observer:** about 50/50 left and right, mirrored with the neighbour. **Adversary:** 5 right, 2 left, 4 centre. | An end bay is right for 2-3 bays. **The side must vary**, and the door is central for 5 bays. |
| D11 | **Gable-form dates** | No real disagreement. The observer (247 register entries plus nl.wiki) and the adversary (nl.wiki plus photos) give the same overlapping ranges. Both judges dated all six drawings within those ranges. | The **sequence is right; the exclusive bins are wrong** (see R1). |

---

## 2. Grades

A = matches the evidence; B = roughly right, needs tuning; C = wrong, or missing a key variant; D = contradicted.

### 2a. RULE problems (TOML)

| Rule / param | Model | Grade | Evidence | Corrected value or rule |
|---|---|---|---|---|
| **R1. Gable form by date** (`set form`, toml:49) | Exclusive bins: step < 1640 < neck < 1720 < bell < 1790 < straight | **D** | Observer D1, D3; adversary C1-C5. Herengracht 168 (1638) is a neck gable. Van Loon (1672) and Herengracht 475 (1730s) are cornice fronts. Necks run to about 1775, bells from about 1660, lijst from about 1660 on wide houses. | Use overlapping, seeded weights, conditioned on width. See Rec. 2. |
| R2. `bay` 1.8/2.2/2.6, `end` 0.3/0.5/0.9 | | **A** | Observer A3 (2.0-2.4 m); adversary C6 | Keep. Observer A3 says the outer pier is 0.6-1.0 × an inner pier; `end` 0.3 is at the low edge. |
| R3. `min_bays=2, max_bays=3` | | **C** (omission) | Observer A1: 4 bays about 8%, 5 bays 10-15% on the Heren- and Keizersgracht; adversary C7 | Allow up to 5 bays when `width ≥ 9 m` or `klass` is rich. Wide fronts get a central door, a double stoop and a lijst top. |
| R4. `window_share` 0.62 | | **A-** | Observer A4; adversary C8; Judge B | Optional: 0.52 before 1640, 0.60 for 1640-1750, 0.65 after 1750. |
| R5. `basement` 1.5 | | **A / B** | Observer B4; adversary C9 | Keep 1.5. Use 1.0 before 1640. |
| **R6. `ground` 3.6, `first` 3.4** | ratio 1.06 | **C** | Observer B3 (4.3 then 3.3); adversary C10 (1.3-1.8×); Judge A | `ground = 4.2`, `first = 3.3`. |
| R7. `taper` 0.93 | | **B** | Observer B3: 3.3 → 2.9 → 2.6, about 0.88; adversary 0.85-0.95 | `taper = 0.88`. The body is then 1.5 + 4.2 + 3.3 + 2.9 + 2.56 = **14.5 m**, which still matches the 3DBAG eave of 14-15.5 m. |
| R8. `uppers` 3 at every date | | **B** | Observer B1 (4 body storeys typical, 18th c.); adversary C12 (2 uppers on step-gable houses) | `uppers = 2 if form in ('step', 'raised_neck') else 3`. A lijst house gets one more storey or an attic (observer D10). |
| R9. **Window heights** (`a_bay_holds_a_tall_window`: sill 0.55, head 0.45 for every storey) | Height ÷ width 1.9 / 1.76 / 1.6 / 1.43 | **C** | Observer C1: 2.6-3.0 / 1.7-1.9 / 1.3-1.5 / 1.0-1.2; observer C2 (bel-etage sill 0.2-0.6); Judge A (b) "windows barely diminish" | Bel-etage `sill = 0.35`. Upper storeys `sill = 0.75`, head band 0.45. With R6/R7 this gives about 2.5 / 1.55 / 1.25 / 1.0. |
| R10. Step tiers (`tiers.step`) | 3 tiers, 0.78 / 0.52 / 0.32 w; 6.9 m | **B** (widths A, height and count C) | Adversary C13 (widths match Herengracht 203); observer D8 (2 storeys in a plain step gable); Judge B pitch 74-77° | `step = [[2.4, 0.74], [2.0, 0.46]]`, plus a top block (crown) of 0.9 m at about 0.22 w. That is about 5.3 m, roughly 64°. |
| **R11. Neck tiers** (`tiers.neck`) | 2 tiers × 0.40 w, 4.9 m, plus a 1.1 m crown | **C** | Observer D5 (1 storey, about 0.5 w tall overall); adversary C15; Judge B read it as "raised" | `neck = [[2.8, 0.40]]`, `crowns.neck = 0.9`, about 3.7 m. Add `raised_neck = [[2.6, 0.65], [2.6, 0.40]]` for 1640-1670 (observer D6, adversary O3). |
| **R12. Bell tier and crown** | `[[3.0, 0.62]]` holding 2 windows; crown 1.4 m | **C** (tier) / **D** (crown, see W3) | Observer D7 (base 0.6 w, 1 window or hatch, height 0.4-0.5 w); adversary C17; both judges | Keep the base at 0.62 w. Fit **one** opening. `crowns.bell = 0.6`, a segmental cap about 0.25 w wide. Total about 3.6 m. |
| **R13. Gable tier fit** (`gable_tier`, `max_bays = 3`) | Count is fit by width | **C** | Adversary C18; Judge A/B img06 | Neck and bell: `max_bays = 1`. Step: fit as now (3 → 2 → 1 matches Herengracht 203). |
| **R14. Attic hatch** (`is_middle_bay`) | With 2 openings, `bays()[len // 2]` returns the **right** bay, so the hatch is off-axis | **D** | Judges A and B (img06 fails on this); observer D11 (the beam is exactly on the axis, the hatch below it) | Only place the hatch when the top tier has an odd count. With R13 it then always has one opening. The hatch must be on the beam's axis. |
| R15. Door (`the_door_up_the_stoop`) | Always `is_first_bay`; 1.1 m; `light_height = h - 0.9` | **B** | Observer B5 (side about 50/50, mirrored; door plus fanlight reaches the window head); adversary C24 | Side by `seed` (or lot parity, to mirror neighbours). Central for 5 bays. `light_height = h - 0.45` (head aligned with the windows), with a fanlight of 0.8-1.2 m. |
| R16. Souterrain lights in every bay | | **B** | Observer B4; adversary C23; Judge B (glazed window behind the treads) | In the door bay, use a souterrain **door** under the landing. Other bays keep their windows, optionally barred. |
| R17. Cornice for `straight` | 0.6 m modillioned slab; nothing above it | **B** (cornice) / **C** (no dormer) | Observer D10, D11; Judge A (img07 "generic … no hoist beam"); Judge B (overhangs past the party walls) | 0.8-1.0 m console cornice that stops at the party walls. Add a central **dormer with a hoist beam** (kit `Dormer` exists). From 1700-1780 use a raised crest instead. |
| R18. `brick_dark` everywhere | | **B** | Observer E1; adversary C21 | Pre-1665: red brick (#9a4030) with sandstone bands. 18th c.: dark brick about 65%, black-painted about 20%. 19th-c. lijst: about 10% white plaster. Rich houses: sandstone. Choose by seed. |
| R19. Window dress (`moulded_architrave`, flat, no keystone) | | **C** | Observer C4 (brick arches, flush white frames, no stone surrounds after 1700); adversary C22 (relieving arches with keystones before 1665) | Before 1665: relieving arch, keystone and stone band. 1665 on: flush white frame under a flat brick arch (*strek*), no architrave. |
| R20. `klass` | Declared, never read | **C** (omission) | Adversary O1; observer E5 | Make it drive the bay count, the lijst top, sandstone and a central door (see R3). |

### 2b. DRAWING problems (grammar.py, kit, renderer)

| Drawing | Grade | Evidence | Fix |
|---|---|---|---|
| **W1. Stoop** (`kit.write_stoop`) | **D** | All four sources. One flight rises across the whole door bay. Judge B measured its top tread to the *right* of the door (x 229-243 against a door at 155-218), so it is physically impossible. There is no landing, no railing, and it sits over a glazed window. | Draw: a landing in front of the door at basement height, at least as wide as the door plus 0.3 m. A side flight of 7-9 treads of 0.19 m, parallel to the front, descending toward the party wall. A black iron railing about 0.9 m above the treads and landing. A souterrain door under the landing. Wide houses get a double flight. Source: observer B4. |
| W2. Step outline (`STEP_RISE` 0.75) | **C** | Adversary C14; Judges A and B; observer D8 | `STEP_RISE = 1.2` (about 2 steps per tier). Draw a light stone cap on every tread. Envelope about 60-65° (see R10). |
| **W3. Bell outline** | **D** | The crown is a semicircle of radius `first.w/2`, a "dome". The shoulders are an S-curve that ends horizontally and then turns vertical. Adversary C17; Judge A ("separate flares on a shaft"); Judge B (crown 61% of the width against 15-30% real) | One continuous outline: from the foot (a curl at about 0.68 w), concave, then convex, closing to a segmental cap about 0.25 w wide and 0.5-0.8 m high, edged with a sandstone band. |
| W4. Neck claw pieces | **C** | All four agree they lack sandstone and ornament. Curvature per D4. | Draw them in stone colour as convex or S-scrolls filling the triangle, 0.3 w × 1.2-1.6 m. Put a sandstone pediment with cornice returns over the neck. |
| W5. Hoist beam | **B** | Adversary C20 (undersized); Judge B (unsure it is a beam). In img10 the beam overlaps the hatch. | Project the beam 0.8-1.2 m, with a hood, under the cap and above the hatch, never over it. |
| W6. Glazing (kit default 4-light) | **C** | Observer C3; adversary C22; Judge B (b) | By date: cross windows before 1680; small-pane sashes 1680-1800 (3×4 / 3×3 per sash); 2-pane sashes after 1800. Frames white, not beige. |
| W7. Repetition | **C** | Both judges: img00 and img14 (1700 and 1670) are "one house drawn twice" | Comes free with Rec. 2, 6, 8 and 13: seed-driven form, door side, paint and dimension jitter of ±5-10%. |

### 2c. OMISSIONS (low or medium cost, in rough order of salience)

| Omission | Source |
|---|---|
| Stoop railing and landing | → W1 |
| Lijst dormer, hoist beam and raised crest | → R17 |
| Sandstone dressings (claw pieces, copings, plinth band) | Observer E2, E3: a light plinth band 1.3-2.0 m under a dark body |
| Raised neck gable | → R11 |
| 4-5-bay wide houses and the role of `klass` | → R3, R20 |
| Relieving arches and banding before 1665 | → R19 |
| Spout-gable warehouse | Observer D9; adversary O2. A separate subtype. |
| Wall anchors | Observer D12 |
| Forward lean, about 1:40 | Observer F7. Medium confidence, invisible in elevation. |
| Gable stones; shopfront ground floors after 1850 | Observer D12; adversary O7 |

---

## 3. Pass/fail: the blind judges

**Identification.**
- Both judges identified all six Amsterdam drawings as Amsterdam canal houses, correctly typed every gable (step, neck, bell, cornice), and dated each one within a range containing the key's year.
- Confidence was high, except Judge A on img07 (medium: "could pass as a US brick row house" without its stoop).
- Judge B called img00 a *raised* neck gable, because of the 2-tier neck.

| img | Key | Judge A (R / P) | Judge A pass? | Judge B | Decisive error |
|---|---|---|---|---|---|
| 00 | 1700 wide neck | 5 / 3 | at a glance | passes with flaws | bare brick claw pieces; stoop |
| 14 | 1670 neck | 5 / 3 | at a glance | passes with flaws | same as 00, a near-duplicate |
| 11 | 1620 step | 4 / 3 | at a glance | passes with flaws | too many tiny steps; too tall |
| 10 | 1635 narrow step | 4 / 2 | recognised, not convincing | borderline pass | 7 levels on 5 m; 74-77° pitch; 8 steps |
| 07 | 1800 cornice | 3 / 3 | Amsterdam "only through the stoop" | **most believable** | no dormer or hoist beam; slab cornice |
| 06 | 1750 bell | 4 / 2 | **would not pass** | **FAILS** | off-axis hatch under a centred beam; dome crown; 2-window bell |

Judge A's Amsterdam means are R 4.2 and P 2.7, against P 2.8 for Venetian Gothic and P 2.25 for Veneto-Byzantine.

**Tally.**
- Both judges pass 3 of 6 (00, 11, 14) with flaws.
- img10 is borderline for both.
- The judges split on img07.
- Both judges fail img06.
- No drawing passes cleanly.

**Errors that made drawings fail, ranked by the judges' own words:**
1. The bell gable (hatch off its beam, dome crown).
2. The stoop, called out on all six drawings by both judges, including "physically impossible".
3. Bare brick claw pieces and the absence of sandstone.
4. The step gable's height, steps and pitch.
5. A cornice house with nothing Amsterdam above the cornice.
6. Window heights that barely diminish.
7. Near-identical repeats.

---

## 4. Recommendations, ranked by impact on a blind expert, then by cost

| # | Change | New value / rule | Evidence | Cost |
|---|---|---|---|---|
| 1 | **Redraw the stoop** (kit or an Amsterdam writer) | Landing in front of the door at `basement` height, width ≥ door + 0.3. Side flight of 7-9 × 0.19 m treads descending toward the party wall. Black iron railing. Souterrain door under the landing (replacing that bay's window, R16). | All four sources; Judge B measured the impossibility | M |
| 2 | **Replace the date bins** (toml:49) with seeded, overlapping weights | **1600-37:** step. **1638-64:** step .45 / raised neck .25 / neck .30. **1665-99:** neck .60 / bell .25 / straight .15. **1700-49:** neck .50 / bell .30 / straight .20. **1750-89:** neck .25 / bell .45 / straight .30. **≥1790:** straight .9 / bell .1. Force `straight` from 1660 when bays ≥ 4 or `klass` is rich. | Observer D1-D3 (247 register tops; Grachtenboek 1768: 65-75% of 3-bay houses neck or bell); adversary C1-C5 | S |
| 3 | **Fix the bell gable** | Fit one opening (`max_bays = 1` for bell and neck). Hatch only on an odd, central bay. `crowns.bell = 0.6`. New outline: continuous S-curve closing to a segmental cap of 0.25 w. | Judges A/B (img06 fails); observer D7; adversary C17 | S-M |
| 4 | **Neck: one tier** | `tiers.neck = [[2.8, 0.40]]`, `crowns.neck = 0.9`. Add `raised_neck = [[2.6, 0.65], [2.6, 0.40]]` (1640-70). | Observer D5/D6 (measured); adversary C15 | S |
| 5 | **Step gable: lower, fewer and larger steps** | `tiers.step = [[2.4, 0.74], [2.0, 0.46]]` plus a 0.9 m top block at 0.22 w. `STEP_RISE = 1.2`. Stone caps on the treads. `uppers = 2` and `basement = 1.0` before 1665. | Adversary C12-C14; observer D8; Judge B pitch; Judge A height | S |
| 6 | **Stone colour on the gable trim**: claw pieces as convex or S-scrolls (0.3 w × 1.4 m), pediment, step caps, bell edge band, plus a light plinth band over the souterrain | sandstone #d8cfbd or white-painted | All four sources; observer E2/E3 | M |
| 7 | **Bel-etage and window taper** | `ground = 4.2`, `first = 3.3`, `taper = 0.88`. Bel-etage sill 0.35; upper sills 0.75. | Observer B3/C1/C2; adversary C10; Judge A (b) | S |
| 8 | **Cornice house top** | Cornice 0.8-1.0 m with consoles, stopping at the party walls. A central dormer (kit `Dormer`) with a hoist beam. From 1700-80, a raised crest instead (by seed). | Judge A (img07); Judge B; observer D10/D11 | S-M |
| 9 | Door side and head | Side by seed or lot parity; central for 5 bays. `light_height = h - 0.45`. | Observer B5/F3; adversary C24 | S |
| 10 | Glazing and frames by date | Cross window before 1680; 3×4 / 3×3 small-pane sash 1680-1800; 2-pane after 1800. White frames. Remove `moulded_architrave` after 1665. | Observer C3/C4; adversary C22; Judge B (b) | M (kit) |
| 11 | Hoist beam visible | 0.8-1.2 m projection with a hood, placed above the hatch, not over it | Observer D11; adversary C20 | S |
| 12 | Pre-1665 dress | Red brick, sandstone bands (*speklagen*), relieving arches with keystones | Observer D8/E4; adversary C21/C22/O4 | M |
| 13 | Wall colour variety | Dark brick .65 / black-painted .20 / white plaster .10 (19th-c. lijst only) / sandstone .05 (rich houses) | Observer E1 | S |
| 14 | Wide houses | 4-5 bays at width ≥ 9 m or rich `klass`; central door, double stoop, lijst top, optional middenrisaliet | Observer A1-A3/D3; adversary C7/O1 | M-L |
| 15 | Window share by date | 0.52 / 0.60 / 0.65 (before 1640 / 1640-1750 / after 1750) | Observer A4; adversary C8 | S |
| 16 | Later additions | Spout-gable warehouse subtype; wall anchors; forward lean of 1:40 | Observer D9/D12/F7 | M |

---

## 5. Verdict

**Body.** The rules capture the canal house's body well. Bay pitch, window share, souterrain height, eave height (14.6 m against a 3DBAG 14-15.5 m), step-tier widths, neck width and hoist beam are all supported. Both blind judges recognised every drawing as an Amsterdam canal house of the right type and period.

**Pass rate.** Only half the drawings pass an expert, and none passes cleanly. The failures come from a few specific, cheap-to-fix decisions:
- an impossible stoop on every house;
- a bell gable with an off-axis hatch and a dome crown;
- gables 2-3 m too tall, with too many steps;
- a bel-etage that is no taller than the floor above;
- no stone ornament;
- a cornice house with nothing above its cornice.

**Rules.** The one rule-level error that an expert would catch across a street, rather than in a single drawing, is the exclusive date-to-form bins. This is contradicted by every textual source and by the first neck gable (1638).

**Overall:** recognisable, but not yet acceptable to an independent observer. Recommendations 1-8 would plausibly move all six drawings to pass with minor flaws.
