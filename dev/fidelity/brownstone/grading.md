# Brownstone model: round 1 grading

Graded: `src/buildings/typologies/brownstone/brownstone.toml` (with `grammar.py` and the shared colours in `render/svg/colors.py`, read only to explain what the strip shows) and `docs/strips/brownstone.png` (both at 6596127). Evidence: `observer.md` (blind to the model, 26 sites, HABS NY-449 as the one hard anchor) and `adversary.md` (38 photos, one row gridded at ±15%, LPC records). No other file was changed.

A = matches the evidence; B = right in kind, needs tuning; C = wrong in places or missing a key variant; D = contradicted, and it changes the read.

## 1. Grades

| Area | Grade | One-line reason |
|---|---|---|
| Proportions | **B** | Storeys within 5-10%; the parlour window is ~0.5 m too tall and the top-floor window ~0.3 m too short. |
| Openings | **C** | Every opening is capped (right), but Italianate bedroom heads are always segmental (wrong), hoods merge into bands, no sills on corbels. |
| Ground floor and entrance | **C** | Stoop, basement, water table and door pair are right in size; the door has no enframement, and the stoop is a pale block. |
| Ironwork | **B** | The grown areaway fence is good; Italianate stoops get stone 65% of the time (should be iron), newels are too slender, no curb. |
| Top and cornice | **C** | Depth right; colour pale, brackets sparse; Romanesque never ends in a gable or parapet; bays have no head. |
| Ornament (incl. grown parts) | **C** | Grown newel/urn and spear pickets read well; hoods are bare slabs, Neo-Grec has no incision or ears, Romanesque has keystones where voussoirs belong. |
| Colour | **D** | Cream trim, pale cornice, beige stoop and beige rock-face turn a brownstone into brick-and-limestone. The biggest single giveaway. |
| Variety | **C** | Three dresses, door side and brick uppers vary; no Renaissance after 1891, no early brick house, bays too rare, no mirrored pairs or row. |

## 2. Where the two reports differ, and the call

| Question | Observer | Adversary | Call |
|---|---|---|---|
| Parlour floor-to-floor | 3.6-4.3 (L-M) | 3.8-4.0 measured, range 3.7-4.3 | **3.8-4.2** (model 3.9-4.4). |
| Bedroom floor | 3.0-3.6, falling upward | 3.0-3.3 measured, range 3.0-3.4 | **3.1-3.5, taper 0.95** (model 3.3-3.7 × 0.94). |
| Basement / stoop | 10-13 risers, 2.0-2.8 m | 12-14 risers, 2.3-2.9 m | **2.3-2.8** (model 2.3-2.7, keep low end, raise top a little). |
| Window width | 1.0-1.1 m | 1.15-1.3 m measured | **1.15 m**, draw 1.05-1.25 per house. Observer's figure is a prior; adversary's is measured. |
| Parlour sill | 0.4-0.6 | ~0.6 measured, range 0.3-0.7 | **0.55 default**, full-length (0.35) on 25% of Italianate houses. |
| Parlour window height | 2.3-2.6 m | (not given; implied ~2.6-2.8 from sill + head) | **2.4-2.7 m.** The model's 2.8-3.3 m is too tall by both. |
| Upper window shape | second 2.0-2.1 m, top 1.6-1.8 m (h/w ≈ 1.9 then 1.6) | h/w 1.45-1.6 | **Second floor h/w ≈ 1.75, top ≈ 1.45.** Both agree the light shortens upward. |
| Italianate stoop rail | cast iron, heavy newel (H) | iron on all six Italianate rows | **Agree: iron.** Model is wrong. |
| Bays | about a third of Brooklyn rows; 3.0-3.6 m wide, 0.9-1.2 m deep | on 20 ft lots; full-height as common as 2-storey | **Agree**; threshold and odds below. |
| Post-1891 dress | Renaissance limestone bowfronts, low/no stoop appears | Renaissance bow fronts dominate 1892-1905 | **Agree.** Model gives 85% Romanesque forever. |

## 3. Ranked fixes

Ranked by how much each changes a viewer's first read. Values marked *inferred* are my reading of both reports where neither measured.

### 1. One-stone colour, dark cornice (Colour D → B)
The trim and cornice draw from shared keys: `surround_moulded_architrave` #C8B8A0, `cornice` #C0B49E, `stoop` #B9AE9C, `socle_picturesque_rustication` #BDAD8E. Changing those globally would break the other typologies, so give the brownstone its own paint keys (or a per-style palette override).
- Wall: draw per house from chocolate #6B4A3E, mid #7A5446 (current), red-brown #82574A, rosy #8C6455, weights 3 : 4 : 2 : 1.
- Hoods, surrounds, sills, water table, stoop, stone newels: the wall's own colour, lightness ±6% (*inferred*: "a shade darker or lighter at most").
- Cornice: near-black brown #3B2E28 0.5, dark brown #4A3328 0.3, dark green #2F3A30 0.2.
- Romanesque rock-face: a darker brownstone (#6A4637), not beige. Romanesque brick: darker red #7E3B2C instead of `wall_brick` #9E5440.
- Optional present-day mode: 10% of houses painted over (cream, pale grey or pink) in a row; off by default since it is modern.

### 2. A door enframement (Ground floor C → B)
Add a `DoorSurround` inserted around the door cell, wider than the door by 0.35-0.5 m each side and rising 0.5-0.8 m above its head.
- Italianate: two foliated consoles the full height of the door's architrave carrying a segmental pediment 0.5, triangular 0.2, flat hood 0.3; pilasters behind the consoles 0.5.
- Neo-Grec: angular incised consoles running the door's full height under a flat stepped hood.
- Romanesque: a heavy round arch of voussoirs springing from short columns 0.5, from plain jambs 0.5.
- Columned porch on the landing: 0.05 on `grand` only (observer RARE, adversary `p14`, `p18`).
- Door height: `light_height = h - 0.9` (now `h - 0.65`), so the head lands at 3.0-3.2 m, level with or just above the parlour windows.

### 3. No full-height vertical lines; separate hoods; sills (Openings C → B)
- On a flat front draw no outline on `slot = "end"` cells or on the EntryZone/WindowZone boundary; the lines from basement to cornice in every flat-front panel come from those edges (*inferred* from the strip; check `kit.write_cell`).
- Hood overhang: `x - 0.18 … w + 0.36` → `x - 0.10 … w + 0.20`. With a 1.15 m light the hood is 1.35 m, leaving ≥ 0.4 m of plain wall between hoods so they stop reading as string courses. Widen the middle pier from `w * 0.14` to `w * 0.17`.
- Add a sill per window: 0.12 m deep, projecting 0.08-0.12 m, light + 0.2 m wide, on two small corbels (Italianate scrolled, Neo-Grec angular). None on Romanesque rock-faced storeys.
- Keep the single water table at the basement head (holds in both reports).

### 4. Cornice brackets and frieze (Top C → B)
- Brackets: 4-8 on a 20 ft front (one pair at each end, then 2-4 single or paired between), so pitch ≈ 0.7-1.0 m; scale count by `w / 0.9`.
- Frieze 0.35-0.45 of the cornice depth, with recessed panels between brackets 0.6, small frieze windows 0.15 on Italianate, dentils 0.25.
- Projection 0.5-0.8 m (both reports); depth 0.75-1.0 holds.
- Romanesque ending: projecting modillioned cornice 0.5, corbelled brick frieze and parapet 0.25, gable or stepped gable 0.25 (adversary R18: about half are not cornices).

### 5. Italianate stoops in iron; the stoop drawn in stone with treads
- `p_iron_stoop = { italianate = 0.85, neo_grec = 0.7, romanesque = 0.3 }` (now 0.35 / 0.75 / 0.5).
- `write_stoop` sets `wall_material = "brick_dark"` but the render paints the pale `stoop` colour: paint it the wall's brownstone, with a riser line every tread (treads are already in the polygon; give them a stroke).

### 6. Window and storey sizes (Proportions B → A)
- `parlour_h = [3.8, 4.2]`; `upper_h = [3.1, 3.5]`; `upper_taper = 0.95`; `basement_h = [2.3, 2.8]`.
- `window_w = 1.15`, drawn 1.05-1.25 per house.
- Parlour: sill 0.55 (0.35 on 25% of Italianates, with an iron balconette); head gap 0.95, giving a light of 2.3-2.7 m.
- Bedroom: sill 0.75, head gap 0.55; top floor deduction 0.25 (now 0.45). That gives about 2.0 m on the second floor and 1.55-1.65 m on the top (now ~1.3 m on an Italianate top floor).

### 7. Italianate heads
- Bedroom heads: flat with a moulded cap 0.6, segmental 0.4; on the top floor alone segmental 0.6 (adversary R13; observer "segmental or flat cornice").
- `parlour_heads = { flat = 2, round = 2, segmental = 1 }` (now round 3 : segmental 2).
- `italianate_hoods` holds as a choice, but big consoles belong on the door and parlour; give bedroom windows a cap on small corbels or eared hood.

### 8. Bay fronts
- `bay_front_min = 5.8` (19 ft), and a bay only with odds 0.45 above it (*inferred* from "about a third of Brooklyn rows").
- Neo-Grec bay height: two storeys 0.5, full height 0.5 (now always two). Romanesque: full height.
- Bay width 3.0-3.6 m (observer); the window zone already fits.
- Bay head where it stops below the top: a small cornice 0.6, iron cresting/balcony 0.4. Run sill and lintel bands round the three faces.
- Rounded (bow) bays: needed for Renaissance (fix 9); 0.3 of Romanesque bays.

### 9. Date ramp and the missing dresses (Variety C → B)
- Add **Renaissance Revival** from 1890: limestone or pale brownstone, bow front 0.7, solid stone stoop balustrade, carved swags, low stoop or American basement 0.25. Ramp: `[1889: neo 0.3, rom 0.6, ren 0.1]`, `[1893: neo 0.05, rom 0.55, ren 0.4]`, `[9999: rom 0.35, ren 0.65]`.
- Add the **early brick house** before 1855: brick from the parlour floor up over a brownstone basement, brownstone slab lintels and sills, Greek Revival flat-pilaster door frame, 5-7 risers. Ramp `[1854: early 0.6, italianate 0.4]`, then the present ramp from 1855.
- Brick uppers start at the parlour floor (`index >= 1`) for Italianate and Neo-Grec; keep `index >= 2` for Romanesque.
- Until Renaissance exists, cap the strip at 1890.

### 10. Rows and mirrored pairs
- A row mode: 4-12 identical houses from one builder seed, pairs mirrored with odds 0.5 (doors and stoops coupled), shared cornice height; a new builder every 4-12 lots steps the cornice 0.3-1.0 m.
- 1890s architect rows: vary each house A-B-A-C under a shared cornice and stoop height.
- In the strip, at least stand houses against party walls rather than sky.

### 11. Romanesque detail
- Replace keystones with rock-faced voussoirs (0.3-0.4 m deep ring) on parlour and top-floor arches.
- Top floor as an arcade of 3-4 small arches: 0.4.
- Rock-face throughout or in bands: 0.2 (adversary `p23`, observer #25).

### 12. Ironwork detail (Ironwork B → A)
- Iron newel: 0.28-0.32 m square, 1.15 m to the cap, urn or ball to 1.4-1.5 m (now 0.2 wide, 1.05, urn to 1.42). Neo-Grec: a square incised newel with a flat or pyramid cap 0.6, urn 0.4.
- Areaway: stand the fence on a stone curb 0.15-0.25 m high; run it up to the newel (gap 0.35-0.4 → 0.05) so it reads as returning to the stoop.
- Finials: spear 0.7, fleur-de-lis 0.3.
- An iron gate under the stoop (0.9 × 1.9 m, dark, barred) where the stoop's foot leaves it visible: low priority.

## 4. What holds and should not change

Lot 16-25 ft at 20 ft default; three bays with the door bay at 0.36 (range 0.36-0.42); door side 50/50; door pair 1.35 m with round head except flat Neo-Grec; basement windows low behind grilles; water table; stoop width 1.7-2.1 m; areaway fence odds 0.85 and its grown pickets at 0.13 m; Italianate → Neo-Grec dating; 3-storey-and-basement as the ordinary house and 4 for `grand`; Romanesque rock-faced base; the 0.45-ish shortening of the top floor (kept, reduced to 0.25 in fix 6).

## 5. Open questions for round 2

- One measured elevation (HABS or LPC drawing) of an 1860s-70s Brooklyn row, to settle window width (1.05 vs 1.2 m) and upper h/w (1.5 vs 1.9).
- Cornice bracket count per 20 ft front, counted on frontal photos rather than estimated.
- Share of bay fronts by neighbourhood and date (current odds 0.45 are inferred).
