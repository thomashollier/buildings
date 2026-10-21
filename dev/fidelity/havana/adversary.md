# Old Havana model: adversarial fidelity review (round 1)

Reviewer brief: try to falsify every rule in `typologies/havana/havana.toml` (and `grammar.py`) against photographs of real Old Havana fronts. I changed no file except this one.

**Method.**
- I read the rule file, the grammar and `docs/strips/havana.png`, and rendered 12 more seeds (1700-1925, 8-22 m, plaza and street).
- I tallied 300 colonial derivations for the kinds of node they emit.
- I fetched 81 Wikimedia Commons images. 43 of them are usable street or plaza views of about 30 distinct buildings inside Habana Vieja; the list with URLs is at the end, cited as `pNNN`.
- Measurements are by eye from pixel ratios on near-frontal views and are **±15-20%**. The one anchored figure (Plaza Vieja, p008) uses a person in the frame at 1.7 m, and I cross-checked it against the storey count.
- Where I give a figure without "measured", it is a range read off several photos, not a measurement.

**Bottom line.** The three-manner skeleton by date is sound, and so are the storey heights, the entresuelo and the pastel palette. Several rules are wrong where they matter most to the eye, though:
- **Openings are glazed sash windows.** Havana has none. Every opening is a pair of full-height wooden leaves (louvred and/or panelled) behind an iron or wooden railing.
- **Exterior stained-glass mediopuntos are given to 85% of colonial (pre-1800) houses.** Real 17th and 18th century street fronts have flat-headed, lintelled openings. The street mediopunto is a 19th-century feature.
- **The colonial wooden gallery has no posts and no roof over it.** The `Tejaroz` rule can never fire (0 of 300 colonial fronts).
- **The colonial house is always exactly two floors** (plus a 35% entresuelo). The one-storey house, which is very common, is missing.
- **The portal is drawn as solid black arches on thin piers.** Real portales are columns, either arched or trabeated, with a lit gallery behind.
- **One flat colour for the whole wall, and never bare stone.** Real fronts have contrasting trim and a painted *zócalo* (base band), and the palaces are exposed limestone.

---

## 1. Claims table

| # | Claim (model) | Source | Verdict |
|---|---|---|---|
| H1 | Manner by date: colonial to ~1800, neoclassical ~1800-1880, eclectic ~1880-1930 (overlapping ramp) | `manner_ramp` | **HOLDS** (broadly) |
| H2 | Colonial = ground + exactly 1 upper (+ entresuelo 35%) | `uppers.colonial=[1,1]`, `entresuelo 0.35` | **PARTLY**: one-storey houses are missing |
| H3 | Neoclassical = ground + 1-2 uppers | `uppers.neoclassical` | **HOLDS** |
| H4 | Eclectic = ground + 2-3 uppers | `uppers.eclectic` | **PARTLY**: 4-6 uppers are common |
| H5 | Storey heights: colonial 5.0-6.0 / 4.6-5.4; neo 5.0-5.6 / 4.4-5.0; eclectic 4.6-5.2 / 3.9-4.4; ×0.95 per floor | `ground_h`, `upper_h` | **HOLDS** within error |
| H6 | Entresuelo 2.4-2.9 m with low square windows | `entresuelo_h`, `entresuelo_lights` | **HOLDS** (where present) |
| H7 | Bays 2.4 / 3.0 / 3.6 m, end piers 0.4-1.2 m | `bay`, `end` | **PARTLY**: bays too narrow, so there are too many openings |
| H8 | Openings 1.2-1.5 m wide, nearly floor to ceiling | `open_w`, `an_opening_to_the_floor` | **PARTLY**: height right; width too narrow on plazas |
| H9 | Glazing `sash` 2×3 (louvres only on 60% of colonial uppers) | `an_opening_to_the_floor` | **WRONG** |
| H10 | Mediopunto on 85% colonial / 75% neo / 30% eclectic houses | `mediopunto` | **WRONG** for colonial; **PARTLY** for neo; holds for eclectic |
| H11 | Mediopunto width = opening width; half-round; patterns fan 3 / ring 2 / grid 2 (colonial ring 60%) | `havana.mediopunto` | **PARTLY**: shape right, glass and tracery wrong |
| H12 | Colonial ground windows: wooden reja to the floor (sill 0.45) on every non-door bay | `Reja` each | **PARTLY**: the reja is right, its form is wrong |
| H13 | Colonial: 70% long wooden gallery along the upper floor, else wooden balcony at each opening | `wood_gallery`, Balcon | **PARTLY**: every colonial front gets a balcony; the gallery's form is wrong |
| H14 | Tile tejaroz over the colonial gallery | `Tejaroz` | **WRONG**: dead rule (never emitted), and the real feature is different |
| H15 | Colonial roof: tiled alero 0.55 m | `alero` | **PARTLY**: the pitched tile roof is not shown; azoteas are missing |
| H16 | Neo/eclectic iron balconies: per opening (60/50%) or one long one, the same on every floor | `p_iron_each`, Balcon | **PARTLY**: real fronts mix the two by floor |
| H17 | Iron railing = straight bars + rosette between each pair | `havana.balusters` (not timber) | **PARTLY**: scrollwork panels and stone balusters are missing |
| H18 | Portal on 85% of plaza fronts (not eclectic): round arches, piers 0.5 m, arch nearly full storey | `portal_on_plaza`, `the_portal` | **PARTLY**: the incidence holds, the form is wrong |
| H19 | Zaguán door 2.2-2.8 m, stone frame, keystone, central (odd bays, 50%) or at an end | `door_w`, `the_zaguan_door` | **HOLDS** (minor detail missing) |
| H20 | Flat roof (neo/eclectic): cornice 0.5/0.7 m + balustered pretil 1.0 m | `Pretil`, `havana.balustrade` | **PARTLY**: the balustrade is one of four common pretils |
| H21 | Crest over the pretil: 20% neo / 70% eclectic, plain segmental panel | `p_crest`, `havana.crest` | **PARTLY**: incidence plausible, form too plain |
| H22 | Paint: one pastel per front (blue 2, mint 1, yellow 3, rose 2, peach 2, white 2, aqua 1) | `paints`, `roles.floor` | **PARTLY**: the palette holds; one colour and no bare stone are wrong |
| H23 | Persianas on 60 / 50 / 35% of houses, over the lower part of upper openings | `persianas` | **PARTLY**: they are far commoner and full height |
| H24 | Louvre colours green 4 / blue 3 / teal 2 / brown 1 | `louvre_paints` | **PARTLY**: brown is underweighted |
| H25 | Pilasters between bays: colonial 10 / neo 55 / eclectic 45% | `pilasters` | **HOLDS** |
| H26 | Bodega on the ground floor 15 / 25 / 45%, all bays become shop openings | `bodega`, `a_bodega` | **PARTLY**: incidence fine, form wrong |
| H27 | Surrounds: colonial bare band; neo/eclectic moulded architrave + keystone | `surround_kind`, `keystone_present` | **PARTLY**: keystones are rare; hoods and pediments are missing |

---

## 2. Rule by rule, with evidence

**H1 manner by date: HOLDS.** The surviving intramuros fabric is mostly 18th-19th century, with eclectic rebuilding from the 1890s to the 1920s. Dated fronts agree:
- A 1922 date plaque on an eclectic front (p076).
- Ambos Mundos (p025), 1920s eclectic.
- The 18th-century houses on Plaza de la Catedral (p123, p129).
- The 19th-century remodelled houses on Plaza Vieja (p003, p008).

A ramp is the right device for this. The model has no art-nouveau or deco tail after about 1920, which is minor.

**H2 colonial floors: PARTLY.**
- The two-floor house (ground + *planta alta*) is right: p023, p106, p111, p024.
- The three-row palace (ground + entresuelo + principal) also exists, around the plazas.
- But the **one-storey house** (*casa de una planta*, tile roof, a door and one or two tall windows) is everywhere in the side streets: p020 (corner of Calle Brasil), p024 (left side of the old Mercaderes postcard), p079 (Empedrado), p147 (corner), p106 (right).
- **Correct:** colonial uppers 0-1, with about 30-40% one-storey on streets (fewer on plazas). Keep the entresuelo at about 30%, but only with 1 upper.

**H3 neoclassical 2-3 floors: HOLDS.** Examples: p177 and p118 (Calle Brasil, 3 floors), the blue house on Plaza Vieja (p008, 3 floors), p119 (3+), p055/p057 (Segundo Cabo, 2 tall floors).

**H4 eclectic 3-4 floors: PARTLY.**
- Ambos Mundos (p025) has 5 floors, Edificio Barraqué (p087) 7, p155 5, and the stone block in p002 4.
- 3-4 is the low end.
- **Correct:** uppers 2-5, weighted 2:3, 3:3, 4:2, 5:1.

**H5 storey heights: HOLDS.**
- Measured on Plaza Vieja (p008, green house, person-anchored): the three rows are about 4.3 / 4.2 / 4.6 m. That is a little under the model's colonial ground 5.0-6.0, but these are 19th-century remodels, so neoclassical, where the model says 5.0-5.6 / 4.4-5.0. It is within error.
- Eclectic floors visibly shrink: p025 and p155 have about 3.6-4.0 m uppers. That agrees with 3.9-4.4 and the 0.95 taper.
- One flag: the *portal* ground floor is the tallest row on plazas (p003, p123). The model gives it no extra height. Allow +0.5 m when `portal`.

**H6 entresuelo: HOLDS** as a 2.4-2.9 m row of small square windows under the principal floor, on the larger houses. I could not measure it on an unambiguous example; the value is plausible.

**H7 bays: PARTLY.**
- On the Calle Brasil arcade (p177) the bay is about 4.5 m (pier to pier, scaled from a storey of about 4.5 m).
- On Plaza Vieja (p008) it is about 5 m.
- On ordinary street houses (p119, p073, p069) it is about 3.2-4 m.
- The model's 2.4-3.6 m puts 4 bays on 11-14 m colonial fronts (strip panels 1-2). Real houses that wide show 3 openings plus the door, with much more wall between them. That higher wall-to-void ratio is part of the colonial character (p023, p106).
- **Correct:** bay 3.2 / 3.8 / 4.5 m on streets, and 4.5-5.5 m behind a portal.

**H8 openings 1.2-1.5 m: PARTLY.**
- Street houses have openings of about 1.3-1.8 m (p119, p177, p073, p077).
- The famous Plaza Vieja fronts (p003, p008) have arched openings of about **3-4 m**, roughly 0.75 of the bay. Each one is filled with a 4-6-leaf door set under a mediopunto that spans the whole arch.
- The model's narrow lancet-like openings with a small fan read as a different building type.
- **Correct:** street 1.3-1.8 m; on plaza or arcaded fronts a "wide arch" variant at 0.7-0.8 of the bay.

**H9 sash glazing: WRONG.**
- There are no sash windows in any of the 43 photos.
- Every opening is a pair (sometimes 4-6) of **full-height wooden leaves**: louvred (*persianas*), panelled (p077, green panels), or louvred above and panelled below (p068-p074).
- Upper-floor openings are balcony doors. Ground openings are doors, or tall windows behind a reja.
- Glass appears only in the mediopunto or luceta above, and in small *postigos* within the leaves.
- The renders' dark-blue glass grid is the single most "not Havana" thing on the page.
- **Correct:** glazing = `leaves` (louvred 0.5 / panelled 0.25 / louvred-over-panelled 0.25), with glass only in the transom.

**H10 mediopunto incidence: WRONG for colonial, PARTLY for neoclassical.**
- The 18th-century street fronts I could see have **lintelled, flat-headed openings and no exterior mediopunto**: the Mercaderes/Amargura house (p023), the houses on Empedrado (p104, p107, p109), the Catedral surroundings (p106), and the one-storey Calle Brasil corner (p020).
- Stained-glass mediopuntos on the street are concentrated on 19th-century remodels: Plaza Vieja (p003, p008), the Catedral houses' upper floors (p123), and Lombillo, which has an **iron** fan over the gate (p189, p191).
- Many 19th-century street houses use a **rectangular luceta** (a transom of coloured glass or an iron grille) instead: p073, p068, p070, p142 (iron grille transoms).
- **Correct:** colonial 0.15-0.25; neoclassical 0.5, plus a rectangular luceta in 0.35 of houses; eclectic 0.3 (holds).

**H11 mediopunto form: PARTLY.**
- The half-round with radial bars round a hub is right (p008).
- Real ones show three things the model does not:
  - A **concentric outer band** of scallops or arches round the rays (every Plaza Vieja fan; it is closer to the "ring" pattern than to "fan").
  - **Coloured glass**: red, blue, amber, green (p123's blue-and-white fans); the render fills them dark.
  - Tracery painted white against the colour.
- The "grid" vitral is plausible but I saw none in this sample.
- **Correct:** ring 0.6 / fan 0.25 / grid 0.15 in every manner, and coloured panes.

**H12 rejas: PARTLY.**
- The wooden turned-bar reja on colonial ground windows is right (p023, right of the corner, green-painted balusters; p109).
- But the reja is **voladiza**: it projects about 0.2-0.3 m from the wall on a moulded stone sill, with a small cap or *guardapolvo* on top, and sits about 0.6-0.9 m above the pavement (p023, p079), not floor to near-ceiling.
- In the 19th century, iron rejas (p079, p142, p062) replace wood and appear on neoclassical ground floors too. The model gives rejas only to colonial fronts.
- **Correct:** reja sill 0.6-0.9 m with a projecting sill and cap; wood in colonial, iron in neo and eclectic (0.6 of non-shop ground windows).

**H13 colonial balconies: PARTLY.**
- 300 of 300 colonial derivations carry a balcony, but real colonial fronts often have none (p020, p106 left, p024).
- The **balcón corrido de madera** is real: p023 is the type specimen, with p030, p104/p107 (blue, Empedrado) and p111.
- Its form, though, is:
  - painted turned posts (*pies derechos*) at about 1.5-2 m centres, rising to carry the roof eave;
  - a balustrade of turned wood or iron;
  - a deck on exposed joist ends with a fascia;
  - all painted green or blue, not dark brown.
- **Correct:** colonial balcony 0.6 when there is an upper floor (gallery 0.6 of those); posts and a roof over every gallery; timber painted with the louvre colour.

**H14 tejaroz: WRONG.**
- The rule fires only when `index < count - 1`, but the colonial upper floor is always the top storey. In 300 colonial derivations the tejaroz appeared **0 times**.
- In reality the gallery's cover is usually the main roof's alero **extended and carried on the gallery posts** (p023), or a separate tile lean-to on posts for a lower gallery.
- **Correct:** whenever there is a gallery, draw its posts and a tile cover over it, joined to the alero on the top floor.

**H15 colonial roof: PARTLY.**
- Two-storey colonial houses with tile roofs show a **visible pitched tile slope** above the eave, red, a metre or more in elevation: p023, p106, p111, p020 (hipped, one storey).
- The model draws a 0.55 m dark strip.
- Many colonial and plaza houses have **flat azoteas** behind a pretil instead: the Plaza Vieja green house (p008) has pretil dies with iron railing between them.
- **Correct:** pitched tile roof 0.6 / azotea with pretil 0.4 for colonial; draw the slope at about 25° and red.

**H16 iron balcony arrangement: PARTLY.**
- The commonest street pattern **mixes by floor**: separate balconettes on one floor and a long balcony on the other (p177, p118, p201: balconettes on the first floor, a corrido on the top; p155 is the reverse).
- The model's choice is per house and applies to every floor.
- Balcony slabs rest on visible **moulded corbels or a moulded slab edge** (p069, p072, p076, p077). The writer sets `bracket_count`, but no brackets show in the render.
- **Correct:** choose per floor (corrido 0.4 / each 0.6), with a 0.3 chance that the top floor flips; draw the slab edge and corbels.

**H17 railings: PARTLY.**
- Straight bars occur (p073, p177).
- Equally common are **cast-iron scroll panels** (p068-p072, p077, p142) and, on eclectic fronts, **stone or cement balusters** on corbels (p076, p025, p146 bellied balconies).
- The "rosette between each pair" is not something I saw.
- **Correct:** neo: bars 0.5 / scroll 0.5; eclectic: scroll 0.4 / stone balusters 0.4 / bars 0.2.

**H18 portal: PARTLY.**
- The incidence on plazas holds: Plaza Vieja (p003, p008), Catedral (p123, p129), Armas/Segundo Cabo (p055, p056).
- Portales also line some streets: Calle Brasil (p118, p177, p201), close to the wall line.
- Their form is wrong in the model:
  - Real supports are **round Tuscan columns** (p003, p123, p008 blue), **massive piers with engaged columns** (p056), or columns carrying a **flat beam** (p008 green house, trabeated, with no arches at all).
  - The arch springs at about 60-70% of the storey.
  - The opening is not a void: you see a lit gallery with doors, windows and the house's own colour behind.
- The render's 0.5 m piers and black-filled arches read like a viaduct.
- The model also excludes eclectic portales. The blue Plaza Vieja front (p008) is late and has one, so allow it at 0.3.
- **Correct:** support = column 0.6 / pier 0.4; head = arch 0.75 / lintel 0.25; draw the back wall.

**H19 zaguán: HOLDS.**
- A wide door of about 2.2-3 m in a moulded stone frame is right (p023, p189 with Lombillo's iron fan above, p033/p034 in the 20th century).
- What is missing: the leaves are heavy panelled timber with a *postigo* (wicket door), and the frame is often a full *portada* with pilasters and a cornice on the grander houses.

**H20 pretil: PARTLY.** Four types recur:
- plain solid parapet with a moulded coping: p177, p119, p201 (the commonest);
- dies with iron railing between: p008 green;
- dies with **urns or pinnacles**: p008 blue, p055, p057, p084;
- stone balustrade: p084, p144.

**Correct:** solid 0.4 / balustrade 0.25 / urns on dies 0.2 / iron between dies 0.15.

**H21 crest: PARTLY.**
- A central crest over the pretil exists (p008 blue, p084, p144).
- It is a **cartouche with scrolls**, often carrying initials or a date, and flanked by urns.
- The model's plain beige segmental slab reads as a pediment fragment.

**H22 paint: PARTLY.**
- The pastel set is right for today's restored streets (p008, p119, p177, p022), and yellow, blue and mint are the right leaders.
- Two things are wrong:
  - **Trim is contrasted**: pilasters, floor bands, cornices and surrounds take a second colour, such as white columns on green (p008), blue bands on white (p177, p118), grey-green bands on turquoise (p119), red trim (p020).
  - **Bare coralline limestone** is the finish of the palaces and of many 18th-century houses: p002, p021, p023, p031, p055-p057, p123, p129.
- A painted ***zócalo*** (base band, about 0.8-1.2 m, darker) runs along most ordinary fronts: p020, p062, p104, p108, p177 (blue pier bases).
- **Correct:** stone (unpainted) 0.25 colonial / 0.15 neo / 0.1 eclectic; otherwise a pastel plus a contrasting trim colour (white 0.5 or a darker tone 0.5), with a zócalo on 0.5 of fronts.

**H23 persianas incidence and form: PARTLY.**
- Louvred leaves are on most openings of every period (p118, p119, p177, p201, p068-p074, p073), not 35-60% of houses.
- They are **the whole opening**, full height. They are not "over the lower part" of a glazed opening.
- **Correct:** 0.8 / 0.7 / 0.5, full height, with the H9 leaf mix.

**H24 louvre colours: PARTLY.** Natural or brown-stained wood dominates the ordinary streets (p118, p119, p177, p201, p068, p069); green (p023, p073, p077) and blue (p020, p104) follow. **Correct:** brown 4 / green 3 / blue 2 / teal 1.

**H25 pilasters: HOLDS.** Rare in colonial (p023 has none), common on neo and eclectic (p008 both, p062, p119). Corner pilasters or quoins at the end piers are near-universal on neo and eclectic fronts; add an end-pier pilaster at 0.6.

**H26 bodega: PARTLY.**
- The incidence is plausible, and bodegas cluster on **corners** (*bodega de esquina*): p186, p203.
- The form is wrong: wooden posts between openings, with folding wooden doors or roll shutters (p203) and no plate glass.
- The render's large blue glass shopfronts (strip panels 5-6) are 1950s Miami, not Havana.

**H27 surrounds: PARTLY.**
- Keystones are uncommon.
- Neoclassical surrounds are flat architraves with a cornice hood, or segmental "eyebrow" hoods (p069, p072, p074).
- Eclectic fronts carry pediments and moulded surrounds (p008 blue, p142).
- Colonial openings have a plain stone frame or no surround (p023).

---

## 3. What real fronts have that the rules lack (by visual weight)

1. **Wooden leaves in place of glass** in every opening (H9).
2. **Gallery posts and a roof over the colonial gallery**, and the visible red tile roof (H13-H15).
3. **Contrasting trim, a painted zócalo, and exposed limestone** on palaces (H22).
4. **One-storey colonial houses** (H2).
5. **Corbels and moulded slab edges under balconies**; balconettes and long balconies mixed by floor (H16).
6. **Wide arched openings on plaza fronts**, 3-4 m with 4-6 leaves (H8).
7. **Rectangular lucetas and iron fan grilles** over doors (H10, p189, p142).
8. **Projecting rejas on sills** (H12).
9. **Corner buildings** with a chamfer or wrapped balcony (p023, p062, p072). The model has only mid-block fronts.
10. **Urns and pinnacles on the pretil dies** (H20).
11. Weathering (p068-p075). This is a reading cue, and probably out of scope.

## 4. What the drawings show that no real front has

- Blue glazed grids (sash) in every opening, including upper balcony doors.
- Plate-glass shopfronts filling the whole ground floor of eclectic houses (strip panels 5-6; render h05, h09).
- A portal of black voids on thin piers (strip panel 3; render h06).
- Mediopuntos over narrow 1.2-1.5 m openings on an 18th-century house (strip panel 2; renders h02, h03, h11).
- A colonial "wooden gallery" drawn as a thin dark railing with no posts or roof (strip panels 1-2; render h00).
- A colonial roof drawn as a thin dark slab (all colonial panels).
- Every colonial front having a balcony.
- A tall 10 m-wide eclectic tower of identical floors with a fanlight on every opening (render h07). Real narrow eclectic fronts usually vary the top floor or the attic.

## 5. Giveaways, ranked

1. **Sash glazing** in place of louvred or panelled wooden leaves (H9, H23). This is the whole texture of the street.
2. **Colonial roof and gallery**: no red tile slope, no posts, no cover; the tejaroz rule is dead (H13-H15).
3. **Mediopuntos on 18th-century houses**, and too small on plaza houses (H8, H10, H11).
4. **The black-void portal** (H18).
5. **Single-colour walls**: no trim, no zócalo, no stone (H22).
6. **Glass shopfronts** on bodegas (H26).
7. **No one-storey colonial houses**, and eclectic capped at 4 storeys (H2, H4).
8. **Bays too narrow**: colonial fronts have too many openings and too little wall (H7).
9. **Balconies** with no corbels, uniform per house, and a bar-and-rosette railing (H16, H17).
10. **Pretil and crest** too uniform and plain (H20, H21).

---

## Photographs used (Wikimedia Commons)

| id | subject | URL |
|---|---|---|
| p002 | Stone 4-storey block with portal, Plaza Vieja | https://commons.wikimedia.org/wiki/File:Plaza_Vieja,_Havana.jpg |
| p003 | Plaza Vieja, row of portal houses with mediopuntos | https://commons.wikimedia.org/wiki/File:Plaza_Vieja,_Havana_(13967173639).jpg |
| p008 | Plaza Vieja, green mediopunto house + blue house with crest (anchored measurement) | https://commons.wikimedia.org/wiki/File:Plaza_Vieja_in_Havana.jpg |
| p020 | One-storey tile-roofed corner + 3-storey with red trim, Calle Brasil | https://commons.wikimedia.org/wiki/File:Calle_Brasil._Habana_Vieja,_La_Habana,_Cuba._Agosto_de_2016_02.jpg |
| p021 | Stone palaces, Mercaderes | https://commons.wikimedia.org/wiki/File:Calle_Mercaderes,_Habana_Vieja,_La_Habana,_Cuba._agosto_de_2016.jpg |
| p022 | Mercaderes street fronts, yellow with balconies | https://commons.wikimedia.org/wiki/File:Calle_de_los_Mercaderes,_Havana_._._._(50224392793).jpg |
| p023 | Corner house with wooden gallery on posts, Mercaderes y Amargura | https://commons.wikimedia.org/wiki/File:Calles_Mercaderes_y_Amargura_in_Havana,_Cuba.jpg |
| p024 | Old postcard, Mercaderes, low colonial houses | https://commons.wikimedia.org/wiki/File:Habana_-_Calle_Mercaderes.jpg |
| p025 | Hotel Ambos Mundos, 5-storey eclectic | https://commons.wikimedia.org/wiki/File:Hotel_Ambos_Mundos_(Havana).jpg |
| p030 | Empedrado by the cathedral, blue wooden balconies | https://commons.wikimedia.org/wiki/File:AJM_(2)_(Aufnahmedatum_2015-03-15_11-55-08).JPG |
| p031 | Amargura y Oficios, stone front with iron balconies | https://commons.wikimedia.org/wiki/File:Amargura_y_Oficios_-_panoramio.jpg |
| p055 | Segundo Cabo / Capitanes Generales, archive photo, pinnacles | https://commons.wikimedia.org/wiki/File:Palacio_del_Segundo_Cabo,_Havana,_Cuba.jpg |
| p056 | Portal of piers with engaged columns, stone | https://commons.wikimedia.org/wiki/File:Palacio_del_Segundo_Cabo.JPG |
| p057 | Segundo Cabo, two floors, pinnacled pretil | https://commons.wikimedia.org/wiki/File:Palacio_del_Segundo_Cabo_de_La_Habana.jpg |
| p062 | Eclectic corner, zócalo, balconettes, Compostela | https://commons.wikimedia.org/wiki/File:Havana,_Cuba_(37255754410).jpg |
| p068 | Scroll-iron balcony, louvred door, grille transom | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(27789446527).jpg |
| p069 | Two balcony doors with eyebrow hoods | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(34455102741).jpg |
| p072 | Corner balcony on moulded slab | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(35825411434).jpg |
| p073 | Street front, slab balconies, louvred leaves, rectangular lucetas | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(36386574041).jpg |
| p076 | Stone-balustered balcony on consoles, 1922 plaque | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(38231078966).jpg |
| p077 | Panelled green leaves, scroll balconette on corbel | https://commons.wikimedia.org/wiki/File:Habana_Vieja_(38812237721).jpg |
| p079 | Empedrado, low houses, projecting iron rejas | https://commons.wikimedia.org/wiki/File:Calle_Empedrado,_La_Habana,_Cuba_(46366818485).jpg |
| p084 | Plaza Vieja, crest front with balustrade and urns | https://commons.wikimedia.org/wiki/File:Plaza_Vieja_de_La_Habana,_Cuba.jpg |
| p087 | Edificio Barraqué, 7-storey eclectic (postcard) | https://commons.wikimedia.org/wiki/File:Havana_-_Edificio_Barraque.jpg |
| p104 | Empedrado, Bodeguita, zócalo bands | https://commons.wikimedia.org/wiki/File:Bodeguita_del_Medio,_Havana,_Cuba_9.jpg |
| p106 | Near the cathedral, two-storey tile-roofed house, lintelled openings | https://commons.wikimedia.org/wiki/File:Habana_-_Alrededores_de_la_catedral.jpg |
| p107 | Empedrado, blue wooden balconies | https://commons.wikimedia.org/wiki/File:Havana_(33119931622).jpg |
| p109 | Empedrado 1904, long rejas, wooden balconies | https://commons.wikimedia.org/wiki/File:Havana_-_Empedrado_Street.jpg |
| p111 | Postcard, tile-roofed colonial with long balcony | https://commons.wikimedia.org/wiki/File:Havana_Vieja.jpg |
| p118 | Calle Brasil, arcaded 3-storey, mixed balconies | https://commons.wikimedia.org/wiki/File:Houses_in_Calle_Brasil_(Havana,_Jan_2014)-2.jpg |
| p119 | Calle Brasil, turquoise with contrasting bands | https://commons.wikimedia.org/wiki/File:Houses_in_Calle_Brasil_(Havana,_Jan_2014).jpg |
| p123 | Plaza de la Catedral, column portal, coloured mediopuntos | https://commons.wikimedia.org/wiki/File:Havanna_-_Plaza_de_la_Catedral_1.jpg |
| p129 | Plaza de la Catedral, stone portal houses | https://commons.wikimedia.org/wiki/File:Plaza_de_la_Catedral_of_Havana_(Jan_2014).jpg |
| p142 | Blue eclectic ground floor, iron-grilled arched windows | https://commons.wikimedia.org/wiki/File:Colorful_building_fa%C3%A7ade_in_Old_Havana,_Cuba_LCCN2010638644.tif |
| p144 | Eclectic front with azulejo panels and crest | https://commons.wikimedia.org/wiki/File:Fa%C3%A7ades_and_details_in_residential_neighborhoods_in_Old_Havana,_Cuba_LCCN2010638960.tif |
| p146 | Bellied stone balconies over a column portal | https://commons.wikimedia.org/wiki/File:Fa%C3%A7ades_and_details_in_residential_neighborhoods_in_Old_Havana,_Cuba_LCCN2010638962.tif |
| p147 | One-storey corner with heavy cornice | https://commons.wikimedia.org/wiki/File:Fa%C3%A7ades_and_details_in_residential_neighborhoods_in_Old_Havana,_Cuba_LCCN2010638963.tif |
| p155 | 5-storey street front, long top balcony | https://commons.wikimedia.org/wiki/File:Fachada_de_un_edificio_de_La_Habana_Vieja_-_panoramio.jpg |
| p177 | Calle Brasil, arcade + balconettes + corrido (bay measurement) | https://commons.wikimedia.org/wiki/File:Houses_in_Calle_Brasil_(Havana,_Jan_2014)-3.jpg |
| p189 | Casa del Lombillo, iron fan over the gate | https://commons.wikimedia.org/wiki/File:Casa_del_Lombillo-8.jpg |
| p191 | Casa del Lombillo, gate and stone jamb | https://commons.wikimedia.org/wiki/File:Plaza_de_la_Catedral-Casa_del_Lombillo.jpg |
| p201 | Calle Brasil, arcaded block, mixed balconies | https://commons.wikimedia.org/wiki/File:Balcony_in_Havanna_Cuba_-_Calle_Brasil.jpg |
| p203 | Corner bodega with posts and roll shutters, Calle Brasil | https://commons.wikimedia.org/wiki/File:Calle_Brasil_-_La_Habana_(23676253494).jpg |

Caveats:
- The Calle Brasil arcades (p118, p177, p201) stand at the west end of Teniente Rey, near the old wall line. They are in the Habana Vieja district but may be just outside the intramuros.
- Commons search mostly returns postcards and close-up details, so plaza fronts are over-represented against ordinary side-street houses.
- No dimension here was measured on site.
