# SoHo model: adversarial fidelity review (round 1)

Reviewer brief: try to falsify every rule in `typologies/soho/soho.toml` against photographs of real SoHo and Tribeca cast-iron and brick lofts. I changed no file except this one.

**Method.**
- I read `soho.toml`, `recipes.py`, `grammar.py` and `docs/strips/soho.png`.
- I rendered 12 more seeds: 7 cast-iron lofts (1852-1879, 1-3 lots, comfortable and grand) and 5 brick store-and-lofts (1855-1895, 1-3 lots, all four classes).
- I tallied 600 derivations (2 lots, grand, 1855/1865/1875) for storey count, head shape and top-to-first storey ratio.
- I fetched 34 Wikimedia Commons photos of 33 distinct buildings: 27 in SoHo, 4 in Tribeca, 2 on lower Broadway. The list with URLs is at the end, cited as `pNNN` / `qNNN`.
- Measurements are by eye from pixel ratios on near-frontal views, scaled from the 25 ft (7.62 m) lot width. They are **±15-20%**, and upper floors are foreshortened in every street-level photo.
- **Not done in this pass:** I opened no HABS sheet and no LPC report. Building dates below come from the Commons file names and my own recall of the LPC SoHo-Cast Iron district report (1973). They are marked *recall* where a verdict depends on them, and should be checked before anyone changes a date threshold.

**Bottom line.** The skeleton holds: three types by date and programme, the 25 ft lot, 3 bays a lot, 5-6 storeys, an iron entablature at every floor, a deep bracketed cornice, and heads moving from round to segmental to flat. What gives the drawings away is how a front is built:
- **A real iron front is a frame, not a wall.** Columns stand between bays and glass fills almost the whole bay from column to column (0.75-0.88 of the bay). The model draws a flat cream panel with dark holes cut in it (window share 0.70, plus a big head gap and a top-floor clearance). This reads as stucco, not iron.
- **Round-headed fronts have no arcade.** Every 1850s-60s round-arched front I found (Haughwout, Cary, 427 Broadway, 55 White, 85 Leonard) frames each arch with its own pair of colonnettes, a Venetian arcade. The model draws a bare arch.
- **Fire escapes have no stairs.** Every real fire escape is a stack of balconies joined by diagonal stairs, with a drop ladder at the bottom. The model draws floating railings on two central bays.
- **Cast iron is gated by money; it should be gated by date.** Plenty of modest 25 ft fronts are iron (102 Greene, 448 Broome, 444 and 452 Broadway). Iron was sold as the cheap substitute for stone.
- **The top floor is squashed.** The 7%-a-floor taper and the cornice clearance together make the top windows about half as tall as the first-floor ones. Real top floors are 80-95% of the first.

---

## 1. Claims table

| # | Claim (model) | Source | Verdict |
|---|---|---|---|
| S1 | Three types by date and programme: Federal to c.1835, cast iron 1848-1880, brick store-and-loft otherwise | `soho.lot` set type | **PARTLY**: the types are right; the 1880 cut-off and the class gate are wrong |
| S2 | Cast iron only for comfortable/grand; modest/ordinary lofts before 1880 are brick | `klass in ('comfortable','grand')` | **WRONG** |
| S3 | No loft before 1848; no dwelling after 1840 | `refuse` | **HOLDS** for this district (minor: Greek Revival houses to the mid-1840s) |
| S4 | Lot 7.62 m; bays 2.3-2.9 m (iron), 1.7-2.3 m (brick); 3 bays a lot | `lot_width`, `bay` | **HOLDS** |
| S5 | End piers 0.3-0.7 m (iron) | `end` | **PARTLY**: right on plain fronts; many fronts have wide rusticated or quoined end piers of 0.7-1.2 m |
| S6 | Storey count: ground + 3-6 uppers (iron and brick), mostly 5-6 storeys in all | `loft_uppers`, odds 2/4/1 | **HOLDS** |
| S7 | Ground storey 4.9 m (grand 5.4), first upper 4.4 (4.7) | `ground_storey`, `first_upper` | **HOLDS** (Broadway grounds are taller, about 5.5-6.5 m) |
| S8 | Taper 0.93/floor (iron), 0.94 (brick), so top/first is 0.7-0.8 | `taper` | **PARTLY**: too steep; real top/first is 0.8-0.95 |
| S9 | Top-floor windows lose a further `cornice_projection*0.65+0.15` (0.8 m) under the cornice | `a_bay_holds_a_window` `clear` | **WRONG** |
| S10 | Iron window share 0.70 of the bay, sill 0.75, head gap 0.70 | `window_share` etc. | **PARTLY**: share too low (0.75-0.88); the sill holds |
| S11 | Engaged column 0.36 m on every pier, every floor | `column_w`, `columns` | **HOLDS** for width (0.3-0.5 m); missing the arcade colonnettes and paired columns |
| S12 | Iron entablature 0.42 m crowning each floor | `entablature_every_floor` | **HOLDS** |
| S13 | Heads by date: round to about 1860, segmental about 1865-70, flat after; one head for the whole front | `head_ramp`, `iron_heads_of_their_date` | **PARTLY**: the ramp holds; the head often changes on the top floor, and round arches need colonnettes |
| S14 | Corinthian odds 0.15 / 0.25 / 0.45 / 0.8 by class, otherwise Doric | `corinthian_odds` | **WRONG**: Corinthian or Composite is the norm on nearly all fronts |
| S15 | Iron front painted one colour: cream 4, white 2, grey 2, buff 2, sage 1 | `iron_paints` | **PARTLY**: black and dark grey are missing, and so are two-tone fronts |
| S16 | Bracketed cornice projecting 0.8-1.2 m | `cornice_projection`, jitter | **HOLDS** |
| S17 | Crest (name-plate pediment over the middle of the cornice) on 35% of iron fronts, 20% of brick | `crest_odds`, `soho.crest` | **PARTLY**: incidence is plausible; the form and placement are wrong |
| S18 | Fire escape on non-grand iron and on all brick lofts: one railing per upper floor over the two central bays | `fire_escape`, `FireEscape` insert | **WRONG** in form; **PARTLY** in incidence |
| S19 | Store ground floor: glass from a 0.45 m bulkhead to a 0.85 m transom band, door to the stair at the right | `the_ground_floor_is_a_store`, `the_door` | **PARTLY**: there is no raised floor, and the door is always on the right |
| S20 | Vault-light platform 0.16 m high on 75% of lofts, lilac glass | `vault_lights`, `soho.vault` | **PARTLY**: lilac lenses are right; the real platform is a raised loading dock with steps |
| S21 | Brick store-and-loft: brick window share 0.52, thin moulded architrave, flat heads, cast-iron store | `brick_store_and_loft` | **PARTLY**: the iron store holds; windows are wrong for both decades |
| S22 | Brick colours: brick 3, dark 2, buff 1 | `brick_paints` | **HOLDS** (painted brick in grey or cream is missing) |
| S23 | Federal rowhouse: 2 storeys + garret, 40° roof, two dormers, party-wall chimneys, 6/6 sash, fanlit door on the left, 3 bays | `federal_rowhouse` | **PARTLY**: no stoop and no basement; the converted shop ground floor is missing |

---

## 2. Rule by rule, with evidence

**S1 types by date: PARTLY.** The three types are the right three, and all three appear in the photos:
- Federal houses at q000, q001, q002, q003.
- Iron fronts at most of the p-series.
- Brick lofts with an iron store at p034, p055 and q007.

The 1880 end of cast iron is too early. The 1870s-80s neo-Grec iron fronts on Greene, Mercer and Grand (p024 102 Greene, q017 26-28 Wooster, q018 47-49 Mercer) are flat-headed with incised neo-Grec detail. My *recall* of the LPC report is that iron fronts went on being built here into the late 1880s, with occasional ones in the 1890s.
- **Correct value:** a ramp, not a cliff. Iron-front odds of about 0.7 to 1875, 0.5 to 1885 and 0.2 to 1895, falling as brick, terracotta and stone take over.

**S2 cast iron only for money: WRONG.** Cheap 25 ft, 3-bay iron fronts are everywhere:
- p024 102 Greene, a plain flat-headed Tuscan front.
- p033 448 Broome.
- p058 444 Broadway.
- p059 452 Broadway.
- p025 125-127 Greene, two plain fronts side by side.

Iron was marketed as cheaper and faster than cut stone. The "grand" end of the market in the 1850s-60s is not only iron: marble and sandstone palazzo fronts on Broadway are missing from the model entirely, though none happened to come up in this photo set.
- **Correct rule:** from 1848 to the mid-1870s, the type is iron front for about 60-70% of lofts in every class, and brick-with-iron-store for the rest. Class changes the ornament (S14, S17, the arcade), not the material.

**S3 refusals: HOLDS.** SoHo's lofts replace houses from the early 1850s. A Greek Revival house of 1836-45 is possible, so moving the dwelling cut-off from 1840 to 1845 would be harmless. That is minor.

**S4 lot and bays: HOLDS.**
- 25 ft fronts carry 3 bays: p024, p033, p043, p058, p059.
- Measured on p059 452 Broadway, the bay pitch is about 2.3 m.
- 50 ft fronts carry 5-7 bays: p015 72 Greene has 5 plus a projecting centre.
- The model gives a 50 ft grand front 6 bays of 2.34 m, which is right.

**S5 end piers: PARTLY.** Plain fronts have narrow end piers, 0.4-0.5 m on p059 and p024. But a common grand variant is a wide, rusticated or quoined end pier, banded or vermiculated, that reads as a pilaster strip from top to bottom:
- p041 55 White.
- q016 134-140 Grand.
- p011 Gunther, at the ground floor.
- **Correct value:** end 0.4-0.5 m (plain); a wide pier of 0.8-1.2 m on about 30% of comfortable and grand fronts.

**S6 storey count: HOLDS.** Counting the ground floor:

| Storeys | Buildings |
|---|---|
| 5 | Haughwout (p003), 72 Greene (p015), 28-30 Greene (p021, plus mansard), 102 Greene (p024, about 5) |
| 6 | Gunther (p011), Cary (p040), 427 Broadway (p057), 452 Broadway (p059) |
| 7 | 47-49 Mercer (q018), 687 Broadway (p056) |

The model's 4-7 range (110/275/180/35 in 600 draws for 4/5/6/7) matches.

**S7 storey heights: HOLDS.** On p059 the first upper is about 5.2 m to the next entablature and the ground floor about 6 m. That is Broadway, near the top of the range. On p024 (Greene) both look about 4.5 m. The figures 4.9/4.4 are fine for the side streets; 5.4-6 m grounds belong to Broadway.

**S8 taper: PARTLY.** In the photos floors above the first are nearly equal: p003 Haughwout, p024, p040 Cary, p057. On p059 the drop is visible but still ends at about 0.8 of the first floor after correcting for foreshortening. The model's 600 draws give a top/first ratio of 0.7 in 36%, 0.8 in 46% and 0.9 in 18%.
- **Correct value:** taper 0.97-0.98 a floor, or a tall first upper with the rest equal. The top floor should be 0.8-0.95 of the first.

**S9 top-floor clearance: WRONG.** Real top-floor windows run to the top-floor entablature like every other floor (p003, p024, p040, p059). The cornice sits on top of that entablature, sometimes over a frieze of about 0.6-1.0 m, and does not eat into the window. The model subtracts 0.8 m on top of the taper, so in the 1879 and 1878 renders the top windows come out as squat squares, a shape no real front has.
- **Correct rule:** no clearance. Add a frieze of 0.5-0.9 m above the top entablature, under the cornice.

**S10 window share: PARTLY.**
- Measured on p059 452 Broadway: window about 2.0 m in a 2.3 m bay, 0.85.
- On p024 102 Greene: about 0.72-0.78.
- On the arcade fronts (p003, p040, p057) the glass between colonnettes is about 0.6 of the bay, but the colonnettes themselves are part of the window frame, so the solid share is still small.
- Sills sit at 0.6-0.8 m on a panelled iron apron, so the 0.75 sill holds.
- **Correct value:** window share 0.78-0.88 for flat and segmental fronts. Head gap is about the entablature alone (0.45-0.6 m), not 0.70.

**S11 columns: HOLDS for width, PARTLY for form.**
- Column widths: about 0.3 m on p059 and about 0.5 m on p024. The 0.36 m figure holds.
- **Missing: paired columns at the piers** on grand fronts (p015 72 Greene, q016 134 Grand, p021).
- **Missing: the arcade colonnette.** A smaller column under each arch springer, as well as the main pier column (p003, p040, p041, p043, p057). This is the Haughwout / Cary / Venetian motif and the single most recognisable SoHo element of the 1850s-60s.

**S12 entablature every floor: HOLDS.** It is there on every iron front in the set, and it is usually the strongest horizontal on the front.

**S13 heads by date: PARTLY.** In the 600 draws, 1855 gives round 87%, 1865 gives segmental 55%, and 1875 gives flat 54%.

| Head | Dated fronts |
|---|---|
| Round | Haughwout 1857 (p003), Cary 1857 (p040), 55 White 1861 (p041), 85 Leonard 1861 (p043) |
| Segmental | Woods Mercantile 1865 (p045), Gunther 1871-72 (p011), 419-421 Broome (p030) |
| Flat, neo-Grec | 102 Greene (p024), 26-28 Wooster (q017), 47-49 Mercer (q018) |

The ramp holds, with two exceptions:
- **Round survives late.** 427 Broadway (p057, an 1870s arcade) is fully round-arched.
- **One head per front is wrong in about a quarter of cases.** The top floor often switches shape: 448 Broome (p033) has a round-arched top floor over flat floors, and 85 Leonard (p043) has a flat top floor over arcaded floors.
- **Correct rule:** keep the ramp. Add a separate top-floor head draw (switch with odds of about 0.25). Give round heads colonnettes (S11).

**S14 Corinthian by class: WRONG.** Corinthian or Composite capitals are on almost every iron front, plain or rich:
- 72 Greene (p015), 28-30 Greene (p021), Gunther (p011), 47-49 Mercer (q018).
- Even modest fronts such as 159-161 Mercer's store (p055).

Plain Tuscan or Doric shows up on early or very plain fronts (p024) and on some ground floors. Neo-Grec fronts (q017) have stylised, incised capitals that are neither.
- **Correct value:** Corinthian/Composite 0.65-0.75 in every class. Doric/Tuscan 0.15. Neo-Grec stylised capitals 0.6 after about 1872.

**S15 paint: PARTLY.** White and cream dominate (p003 is grey; p008, p011, p021, p024, p040, p057 are white or cream), so the palette is right in spirit. Missing:
- **Black / very dark green fronts:** 127 Greene (p025), the ground floor of 419-421 Broome (p030), the ground floor of 45 White (p045).
- **Blue-grey:** 687 Broadway (p056).
- **Two-tone:** a darker ground floor under a light front (p030, p045, p060).
- **Correct value:** add black/near-black about 1 in 12 fronts, and a dark ground floor on about 20%.

**S16 cornice: HOLDS.** Cornices are deep, bracketed and dentilled on every iron front. Projection looks like 0.7-1.0 m.

**S17 crest: PARTLY.** Real central features take three forms:
- A triangular pediment the full width of the front: p040 Cary (with the building's name cast in it) and p057 427 Broadway.
- A segmental pediment over the middle bays: p030, p045, q018, q020.
- A projecting central pavilion with its own pediment: p015/p017 72 Greene.

In all three the cornice itself breaks upward, and the pediment carries the cornice's own mouldings and brackets. The model's crest is a panel-plus-lid floating above the cornice. In the 1852 and 1865 renders the segmental version reads as a dome or a lantern, and no real front has that.
- **Correct form:** a raised section of the cornice, 1-3 bays wide (or the full width on small fronts), rising 0.8-1.8 m, with the cornice mouldings carried round it. A name plate is optional.

**S18 fire escape: WRONG in form, PARTLY in incidence.** Every fire escape in the set is the same machine: a balcony at each upper floor, a diagonal stair between each pair, and a drop ladder or counterweighted stair from the first balcony. Examples: p003 (side), p015, p021, p025 (two), p033, p035, p055, p056, q007, q016.
- **Width:** 2-3 bays, often at one side rather than central (p025, p055, q016). On the model's 9-bay, 3-lot front the "central" pair of bays is actually off-centre (bays 4-5).
- **Incidence:** about 55% of the iron fronts in this set carry one on the street face. None on the front: p024, p040, p041, p043, p057 (Broadway face), p058, p059.
- **Correct rule:** fire-escape chance about 0.5 for iron fronts in every class, and 0.6-0.7 for brick lofts. Span 2-3 bays, at the centre or one side. Draw stairs between balconies and a ladder below the lowest one.

**S19 store: PARTLY.**
- The glass to a transom holds.
- **The ground floor is raised.** Many side-street lofts stand on a loading platform 0.4-1.0 m above the sidewalk, with granite steps and vault lights: p024 102 Greene, p058 444 Broadway, q003.
- **Columns run full height** to the entablature. The doors are double, panelled and glazed, and they share bays with the shop glass (p024, p055).
- **The stair door** is on the left at p024 and q018, and on the right at p059.
- **Correct rule:** door side about 50/50. Floor raised 0.4-1.0 m on about half of side-street lofts.

**S20 vault lights: PARTLY.** The lilac lenses (sun-purpled manganese glass) are right. The real thing is a sidewalk vault or the tread of a raised loading platform with steps up to the doors, not a 0.16 m strip across the foot of the front. See S19.

**S21 brick store-and-loft: PARTLY.** The cast-iron store under brick holds: p034 485 Broome and p055 159-161 Mercer have iron Corinthian ground floors. The windows above are wrong in both decades:
- **1850s-60s Italianate brick (p055):** windows about 0.45 of the bay is about right, but every window has a projecting stone or iron hood, triangular or segmental, or a heavy bracketed lintel. The model's thin architrave reads as nothing.
- **1880s-90s (q007 55 Crosby, q033 495 Broome, p060):** Romanesque and Queen Anne lofts group windows between brick piers, often in round-arched multi-storey arcades, with rough-faced stone bases and terracotta panels. Late-1880s and 1890s windows are wide and tripartite, with a share of 0.65-0.8 (q033). The model's 0.52 share with uniform, tiny, evenly spaced windows (the 3-lot, 1895 render has 11 identical bays) has no real counterpart.
- **Correct values:** pre-1875 share 0.45-0.5 with hoods on every window. Post-1880 share 0.6-0.8, piers grouping 2-3 windows, round-arched top storey or arcade on about 40%.

**S22 brick colour: HOLDS.** Red, dark red and buff/tan all appear (p055, q018 neighbour, q007). Painted brick in grey or cream is also common (p034, q001, q002), and the model has no way to draw it.

**S23 Federal rowhouse: PARTLY.** The 2½ storeys, two dormers and fanlit door hold (q001 146 Spring, q002 152 Spring, q000 105 Mercer). What is wrong or missing:
- **The stoop and raised parlour floor are missing.** The model's own comment says "raised parlour floor over its basement", but the drawing puts the door on the sidewalk. q000 has a 5-step stoop with iron railings and basement windows under the parlour floor.
- **Nearly every surviving SoHo Federal house has a shop cut into its ground floor** (q001, q002, q003). Many were raised to a full third storey (q003).
- **Correct rule:** stoop of 4-6 steps and a basement about 1.0-1.3 m above grade. On a converted house (most cases after 1850), a shop front replaces the parlour floor.

---

## 3. What real fronts have that the rules lack

Ranked by how much they would change the look:

1. **Frame, not wall.** Glass fills each bay from column to column, with a panelled iron apron below and an entablature above. There is almost no flat infill.
2. **The arcade:** paired colonnettes under every round arch, on 1850s-60s fronts. Some fronts double it, with small columns for the arch and a larger column for the pier.
3. **Fire escapes as stair stacks:** balconies, diagonal stairs, a drop ladder, 2-3 bays wide, often at one side.
4. **Sash windows:** 2-over-2 or 1-over-1 with a visible meeting rail, the upper sash following the arch. The model draws one dark pane with a faint cross.
5. **Raised loading platform** with steps and vault lights, and double panelled doors.
6. **Mansard roofs** on Second Empire fronts of about 1868-75: 28-30 Greene (p021), 134-140 Grand (q016). These have dormers, iron cresting, and sometimes a pavilion roof over the centre.
7. **Rusticated or quoined end piers** and paired columns at the piers on rich fronts.
8. **Projecting centre pavilion** (72 Greene) and **curved corners** (Gunther). Corners are out of scope for a mid-block lot, but worth noting.
9. **Hoods over brick-loft windows** (Italianate), and **grouped arched windows** (Romanesque).
10. **Two-tone paint** and black fronts.
11. **Federal stoop and basement**, and the shop cut into a Federal ground floor.
12. Small but distinctive: **neo-Grec incised detail** and eared window surrounds (q017), and the cast **name and date in the pediment** (p040).

## 4. What the drawings show that no real front has

1. **Squat top-floor windows** under a clearance band (S9 + S8). Real top floors look like the floor below.
2. **Fire-escape railings with no stairs**, floating on the two "central" bays, which are off-centre on odd-bay fronts.
3. **A dome or lid floating over the cornice** (the segmental crest), detached from the cornice line.
4. **A flat cream panel around arched holes:** the iron front read as stucco.
5. **Brick lofts of 11 identical tiny windows** with no hoods, piers or grouping (the 3-lot, 1895 render). Late lofts have the widest windows of all.
6. **The same brown door at the right-hand end** of every loft, at grade.
7. **A cream "stone" ground floor on brick lofts with no visible columns.** The real iron store shows its columns and capitals.

## 5. Giveaways, ranked

1. **Window/wall ratio and the missing column frame** (S10, S9). This is the first thing a viewer would notice, on every iron front.
2. **Fire escapes without stairs** (S18). Every real one has stairs, and they dominate a SoHo street view (p035).
3. **Round-arched fronts without colonnettes** (S11, S13). The Haughwout/Cary arcade is the period signature.
4. **The squat top floor** (S8, S9).
5. **The floating crest dome** (S17).
6. **Single-pane dark glass with no sash** (§3.4).
7. **Uniform punched brick-loft windows** (S21).
8. **No raised ground floor or steps, and a fixed door side** (S19, S20).
9. **Corinthian rationed by money** (S14), and cast iron rationed by money (S2). These do less visual harm but are factually wrong.
10. **Federal house at grade with no stoop** (S23). There are no mansards on 1868-75 fronts and no black fronts.

---

## 6. Sources (Wikimedia Commons)

| Ref | Building | URL |
|---|---|---|
| p003 | Haughwout Building, 488 Broadway (1857) | https://commons.wikimedia.org/wiki/File:E._V._Haughwout_Building,_1_(cropped).JPG |
| p008 | 469-475 Broome St (Gunther, Broome face) | https://commons.wikimedia.org/wiki/File:469-475_Broome_Street.JPG |
| p011 | Gunther Building, Broome and Greene (1871-72) | https://commons.wikimedia.org/wiki/File:Gunther_Building_Broome_and_Greene_St.jpg |
| p015 | 72-76 Greene St | https://commons.wikimedia.org/wiki/File:72_Greene_Street_02.JPG |
| p017 | 72-76 Greene St, from south | https://commons.wikimedia.org/wiki/File:72_Greene_Street_from_south.jpg |
| p021 | 28-30 Greene St (mansard) | https://commons.wikimedia.org/wiki/File:28-30_Greene_Street.JPG |
| p024 | 102 Greene St | https://commons.wikimedia.org/wiki/File:102_Greene_Street.jpg |
| p025 | 125-127 Greene St | https://commons.wikimedia.org/wiki/File:125-127_Greene_Street.jpg |
| p026 | 132-140 Greene St | https://commons.wikimedia.org/wiki/File:132-140_Greene_Street.jpg |
| p030 | 419-421 Broome St | https://commons.wikimedia.org/wiki/File:419-421_Broome_Street.jpg |
| p033 | 448 Broome St | https://commons.wikimedia.org/wiki/File:448_Broome_Street.jpg |
| p034 | 485 Broome St (painted brick, iron store) | https://commons.wikimedia.org/wiki/File:485_Broome_Street.jpg |
| p035 | Greene St view from Broome (fire escapes) | https://commons.wikimedia.org/wiki/File:Cast-Iron_451-Broome-Street_from_Greene_Street.jpg |
| p040 | Cary Building, 105-107 Chambers St (1857) | https://commons.wikimedia.org/wiki/File:Cary_Building.jpg |
| p041 | Condict Store, 55 White St (Tribeca) | https://commons.wikimedia.org/wiki/File:Condict_Store_55_White_Street.jpg |
| p043 | Kitchen, Montross & Wilcox Store, 85 Leonard St (Tribeca) | https://commons.wikimedia.org/wiki/File:Kitchen,_Montross_%26_Wilcox_Store_85_Leonard_Street.jpg |
| p045 | Woods Mercantile Building, 46-50 White St (Tribeca) | https://commons.wikimedia.org/wiki/File:Woods_Mercantile_Building_46-50_White_Street.jpg |
| p055 | 159-161 Mercer St (Italianate brick, iron store) | https://commons.wikimedia.org/wiki/File:159-161_Mercer_Street.jpg |
| p056 | 687-691 Broadway | https://commons.wikimedia.org/wiki/File:687-691_Broadway.jpg |
| p057 | 427 Broadway | https://commons.wikimedia.org/wiki/File:427_Broadway.jpg |
| p058 | 444 Broadway | https://commons.wikimedia.org/wiki/File:444_Broadway.jpg |
| p059 | 452 Broadway | https://commons.wikimedia.org/wiki/File:452_Broadway.jpg |
| p060 | 472-474 Broadway | https://commons.wikimedia.org/wiki/File:472-474_Broadway.jpg |
| p063 | 583 Broadway (later oriel front) | https://commons.wikimedia.org/wiki/File:583_Broadway_mid.jpg |
| q000 | 105 Mercer St (Federal, stoop) | https://commons.wikimedia.org/wiki/File:105_Mercer_Street.jpg |
| q001 | 146 Spring St (Federal, dormers, shop) | https://commons.wikimedia.org/wiki/File:146_Spring_Street.jpg |
| q002 | 152 Spring St (Federal, dormers, shop) | https://commons.wikimedia.org/wiki/File:152_Spring_Street.jpg |
| q003 | Dennison and Lydia Wood House, 310 Spring St | https://commons.wikimedia.org/wiki/File:Dennison_and_Lydia_Wood_House_310_Spring_Street.jpg |
| q007 | 53-55 Crosby St (Romanesque brick loft) | https://commons.wikimedia.org/wiki/File:55_%26_53_Crosby_Street.jpg |
| q016 | 134-140 Grand St (mansard) | https://commons.wikimedia.org/wiki/File:134-140_Grand_Street_from_west.jpg |
| q017 | 26-28 Wooster St / 71 Grand St (neo-Grec) | https://commons.wikimedia.org/wiki/File:26-28_Wooster_Street_71_Grand_Street.jpg |
| q018 | 47-49 Mercer St | https://commons.wikimedia.org/wiki/File:47-49_Mercer_Street.jpg |
| q020 | 75 Grand St | https://commons.wikimedia.org/wiki/File:75_Grand_Street.jpg |
| q033 | 495 Broome St (1890s brick/terracotta loft) | https://commons.wikimedia.org/wiki/File:495_Broome_Street.jpg |

Renders used: `docs/strips/soho.png`, plus 12 seeds drawn with `dev/harness/soho_sheet.py`'s `sheet()` (iron: 1L 1852 s1, 2L 1857 s3, 1L 1862 s4, 2L 1868 s5, 3L 1872 s6, 2L 1878 s7, 1L 1879 s8; brick: 1L 1855 s1, 2L 1865 s2, 1L 1882 s3, 2L 1890 s4, 3L 1895 s5). They were kept in scratch and not committed.
