# Brooklyn and Manhattan brownstone: adversarial fidelity review (round 1)

Model under test: `src/buildings/typologies/brownstone/brownstone.toml` (rules), `grammar.py` (stoop, hood, grille and rock-face writers), and the render `docs/strips/brownstone.png`. I also rendered six more seeds (Italianate 1858 and 1862, Neo-Grec 1878 and 1884, Romanesque 1892 and 1895) and tallied 1,200 derivations (300 seeds at each of 1855, 1870, 1880 and 1890, on a 20 ft lot). I changed no file except this one.

## Method

- **Photographs.** I pulled 40 Wikimedia Commons images and used 38 of them. They cover about 30 distinct rows or houses in Prospect Heights, Park Slope, Fort Greene, Clinton Hill, Cobble Hill, Brooklyn Heights, Bedford-Stuyvesant/Stuyvesant Heights, Harlem and the Upper West Side. They are cited below as `pNN` and `qNN`, with URLs at the end. Two images (a Clinton Hill side view and an apartment house on Mount Morris Park) were not usable.
- **Measurement.** I gridded one near-frontal row, 17 E. 126th St, Harlem (`p13`). The scale comes from the parlour door pair, taken as 1.25-1.35 m wide and 2.8 m high, and is cross-checked against the stoop's riser count at about 18 cm a riser. Figures marked "measured" carry about **±15%**. Everything else is a range read by eye across several photos.
- **HABS and LPC.** I found no HABS measured-drawing set for a Brooklyn or Manhattan brownstone row. For the date ramp I relied on LPC records: the Park Slope Historic District (LP-0709, 1973) photo records tag typical houses as "Italianate with neo-Grec secondary style", c. 1875-1880 ([LPC Luna record](https://nyclandmarks.lunaimaging.com/luna/servlet/detail/NYClandmarks~2~2~94273~101323:Park-Slope-Historic-District)). The 2016 Park Slope Extension II staff report describes 19th-century houses as "typically three and four-story" ([LPC press release](https://home4.nyc.gov/site/lpc/about/pr2016/04-12b.page)). A round 2 should get a HABS or Hatfield-style measured elevation to anchor the storey heights.

## Bottom line

The skeleton is right: an English basement, a high stoop to a tall parlour floor, three bays stacked over the door and two windows, a cornice, and dress chosen by date. The storey heights are close. What gives the drawings away is mostly **dress, colour and the absence of the door**:

1. **The trim is cream on a brown wall.** Real brownstone trim is cut from the same stone as the wall, so the front reads as one chocolate-brown monochrome. Contrasting cream trim only appears where a later owner painted it (`p09`). As drawn, the fronts read as brick with limestone trim, not brownstone.
2. **The cornice is pale tan and spare.** Real cornices are wood or pressed metal painted near-black or dark brown. They carry 4-10 brackets with panels, dentils or a deep frieze between them (`p07`, `p09`, `p14`, `p21`, `q03`, `q09`).
3. **The door has no enframement.** On every real front the door surround is the loudest element. Italianate doors sit under a pediment or segmental hood on two big foliated consoles, often with pilasters or columns (`p06`, `p07`, `p09`, `p10`, `p13`). Neo-Grec doors have angular incised consoles running the full door height (`p12`, `p25`). The model gives the door the same thin hood as a window, or none.
4. **Vertical "pier" lines run from basement to cornice.** They divide the bays like pilasters on every flat front. Real flat fronts are smooth ashlar with no vertical divisions. The only verticals are the bay arrises on a bay front.
5. **Continuous horizontal bands cross the whole front at every floor.** The hoods line up and read as string courses. Real fronts have individual hoods and sills per window, and one water table at parlour-floor level.

---

## 1. Rules: holds / partly / wrong

| # | Rule (model) | Source | Verdict | Evidence and correct value |
|---|---|---|---|---|
| R1 | Dress by date: Italianate to ~1870, Neo-Grec ~1870-1885, Romanesque from ~1886, Romanesque 85% for every year after 1889 | `kind_ramp` | **PARTLY** | Italianate to Neo-Grec matches LPC dating (Park Slope "Italianate with neo-Grec secondary", 1875-80; `p06`, `p07`, `p09` are 1860s Italianate; `p12`, `p25`, `q03` are Neo-Grec). Romanesque from about 1886 holds (`q01`, `q02`, `p23`). **Wrong after about 1891:** Renaissance Revival bow fronts in limestone or brownstone dominate 1892-1905 (`p04`, `p27`, `p28`, `q06`, `q07`), and Queen Anne runs 1880-95 alongside Romanesque (`p02`, `q10`, `q12`, `p19`). Neither style exists in the model. Before 1855 the brick Greek Revival/early Italianate house with brownstone trim and a low stoop (`p15`, `q05`, `p01`) is also missing. |
| R2 | Lot 16-25 ft; default 20 ft | `LOT = 6.1` | **HOLDS** | `p13` measures about 5.0-5.5 m per house; Prospect Place and Park Slope rows read 18-25 ft. |
| R3 | Basement 2.3-2.7 m (parlour floor about 8 ft up) | `basement_h` | **HOLDS** | `p13` measured 2.6-2.9 m from sidewalk to parlour sill; 12-14 risers in most stoops (`p13`, `p21`, `q03`), so 2.2-2.6 m. **Range: 2.3-2.9.** |
| R4 | Parlour floor 3.9-4.4 m | `parlour_h` | **HOLDS** (slightly high) | `p13` measured 3.8-4.0 m floor to floor. **Range: 3.7-4.3.** |
| R5 | Bedroom floor 3.3-3.7 m, ×0.94 per floor | `upper_h`, `upper_taper` | **PARTLY** | `p13` measured 3.0-3.3 m; the taper is visible (`p07`, `p09`). **Range: 3.0-3.4.** |
| R6 | Ordinary house = basement + parlour + 2 bedroom floors ("three-story-and-basement"); grand = + 3 | `uppers` | **HOLDS** | 3-story-and-basement is the commonest Brooklyn type (`p06`, `p07`, `p09`, `p21`, `q09`). 4-story-and-basement is common in Manhattan and on later or wider lots (`p14`, `q04`, `q06`), matching `grand`. The tally shows every `ordinary` derivation at 4 levels, 12.7-14.1 m to the cornice; real rows read about 12-14 m. |
| R7 | Three bays: door bay is 36% of the width, with two windows | `entry_share`, `window_zone` | **HOLDS** | Universal on 18-25 ft fronts (`p07`, `p09`, `p13`, `q03`, `q04`). The door's bay with its enframement measured 0.38-0.42 of the house in `p13`. **Range: 0.36-0.42.** Two-bay houses exist on 12-16 ft lots (`q11`) but are rare. |
| R8 | Side of the door chosen 50/50 by seed | `entry_left` | **HOLDS** | Rows alternate or repeat by builder; both occur (`p13`, `q03`). |
| R9 | Window sash 1.05 m wide | `window_w` | **PARTLY** | `p13` measured 1.15-1.3 m. **Range: 1.1-1.3 m.** Upper-floor lights are too slender in the model (height/width ≈ 2.0 against a measured 1.45-1.6). |
| R10 | Parlour windows reach nearly to the floor (sill 0.35 m) | `a_window` | **PARTLY** | Full-length parlour windows with iron balconettes occur (`p20`, `p06`). The commoner sill is 0.5-0.7 m (`p13` measured about 0.6; `p09`, `q03`). **Range: 0.3-0.7.** |
| R11 | Top-floor window 0.45 m shorter under the cornice frieze | rule note | **HOLDS** | `p07`, `p09`, `p21`, `q04`. |
| R12 | Italianate parlour heads round 3 : segmental 2 | `parlour_heads` | **PARTLY** | Round-arched parlour windows occur (`p06`, `p20`), but flat-headed parlour windows under a cornice hood are at least as common (`p07`, `p09`, `p13`, `p21`). **Better: flat 2 : round 2 : segmental 1.** |
| R13 | Italianate bedroom windows always segmental | `a_window` | **WRONG** | Most Brooklyn Italianate upper windows are **flat-headed with a moulded cornice cap** (`p07`, `p09` second floor, `p13`, `p21` middle floor, `q04`). Segmental heads appear on some whole rows (`p06`, `q04` parlour) and often on the top floor only (`p21`). **Better: flat 0.6, segmental 0.4, with segmental likelier on the top floor.** |
| R14 | Italianate hood on every opening, consoles 3 : flat slab 1 | `italianate_hoods` | **PARTLY** | Every opening is capped (holds). Big foliated consoles belong to the **door** and sometimes the parlour windows (`p06`, `p09`, `p10`). Upper windows have a moulded cornice cap or eared hood on small corbels, plus a sill on corbels (`p07`, `p09`, `p13`). Model hoods are thin cream slabs with no ears and no sill blocks. |
| R15 | Neo-Grec: square heads, incised projecting lintel, no surround | `a_window` | **HOLDS** (form) | `p12`, `p25`, `q03`, `p08`. The lintels carry incised lines and stubby angular ears, and sills sit on angular corbels. The model shows a bare slab. |
| R16 | Romanesque: rock-face on basement and parlour | `Socle` when romanesque | **HOLDS** | `q01`, `q02`, `p23`. Some fronts are rock-faced throughout or in bands (`p23` banded quarry-faced courses). |
| R17 | Romanesque: round arches with keystones on parlour and top floors, square between | `a_window` | **PARTLY** | Round arches on parlour and top floor: `p23`, `q01`, `q02`. The arches carry **heavy rock-faced or contrasting voussoirs**, not a keystone (`q01`, `q02`, `p23`). The top floor is often an arcade of small arches (`p23`). |
| R18 | Romanesque: modillioned bracket cornice | `cornice_ornament` | **PARTLY** | About half the Romanesque fronts seen end in a **gable, stepped gable, parapet or corbelled brick frieze** (`q01`, `q02`, `p19`, `q10`) rather than a projecting cornice. |
| R19 | Brick bedroom floors over a brownstone base: Italianate 0.15, Neo-Grec 0.2, Romanesque 0.5 | `brick_uppers` | **PARTLY** | Romanesque 0.5 holds (`q01`, `q02`, `q10`). The early brick house (`p01`, `p22`, `q05`) is **brick from the parlour floor up**, often over a brownstone basement, with brownstone trim. The model keeps the parlour floor brownstone (`index >= 2`), so the brick starts one floor too high for Italianate and Neo-Grec. |
| R20 | Bay front only from Neo-Grec on, and only on lots ≥ 6.5 m (21 ft) | `bay_front_min` | **WRONG** (threshold) | Neo-Grec bay rows on Carroll Street stand on 20 ft lots (`q03`), as do Park Slope bays (`p03`, `p05`). **Threshold: about 5.8 m (19 ft).** Not every wide front gets a bay; give it odds of about 0.5 rather than a sure yes. |
| R21 | Neo-Grec bay rises 2 storeys; Romanesque bay rises through the house | `bay_top` | **PARTLY** | Two-storey bays (basement and parlour) occur (`p08`). **Full-height angled bays are at least as common in Neo-Grec Park Slope** (`q03`, `p03`). Romanesque/Renaissance bays are often **rounded (bowed)** (`p04`, `q06`, `q12`), which the model cannot make. |
| R22 | A bay drawn as three faces with a pilaster at each arris | `window_zone` bayed | **PARTLY** | The faces are right. A real bay has its own **head**: a cornice, iron balcony or balustrade where it stops below the house's top (`p08`, `q03`, `q07`). It also has **sill and lintel bands running round it**. The model draws neither, so a two-storey bay reads as two loose pilasters. |
| R23 | Basement windows sit low behind iron grilles; no opening under the stoop | `basement_window`, `under_the_stoop` | **HOLDS** | `p13`, `p14`, `q03`. Under the stoop there is usually an iron gate or door to the basement entrance, partly visible between the stoop's foot and the areaway (`p13`, `p10`). That is minor. |
| R24 | Water table capping the basement | `water_table` | **HOLDS** | `p13`, `p25`, `q03`. |
| R25 | Stoop 1.7-2.1 m wide, rising to the parlour floor | `stoop_ws` | **HOLDS** | `p13` measured about 1.8-2.0 m between rails, 2.4-2.8 m across the newels. |
| R26 | Stoop balustrade iron: Italianate 0.35, Neo-Grec 0.75, Romanesque 0.5 | `p_iron_stoop` | **WRONG** (Italianate) | Every Italianate stoop I saw carries **cast-iron railings with big cast-iron newels**: `p06`, `p07`, `p09`, `p10`, `p13`, `p21`, all six Italianate rows. Solid brownstone balustrades with turned balusters and a heavy stone newel are a **later** habit (`p16`, `q01`, `p04`, `q03`). **Better: Italianate 0.85, Neo-Grec 0.7, Romanesque/Renaissance 0.3.** |
| R27 | Areaway fence on 85% of fronts | `areaway_fence` | **HOLDS** | Nearly universal (`p05`, `p08`, `p10`, `p13`, `q09`). It often stands on a low stone curb or coping (`p05`, `p27`). |
| R28 | Front door a pair 1.35 m wide, height = parlour − 0.65 | `door_w`, `the_door` | **HOLDS** | `p13`: a door pair of about 1.25-1.35 m, about 2.8 m to the transom bar, with a round or segmental transom over it. |
| R29 | Door head round except Neo-Grec flat; keystone on Romanesque | `the_door` | **HOLDS** | Italianate round-arched doors (`p06`, `p09`, `p10`); Neo-Grec flat (`p12`, `p25`); Romanesque arched (`q01`, `q02`). |
| R30 | Cornice 0.75-1.0 m deep, ×0.75 on Romanesque | `cornice_hs` | **PARTLY** | The depth holds. Colour and ornament are wrong (see giveaways). |

**Count: 15 HOLDS, 12 PARTLY, 3 WRONG.**

---

## 2. What real fronts have that the rules lack

1. **A door enframement**: Italianate pediment or segmental hood on large consoles with pilasters (`p06`, `p09`, `p10`); Neo-Grec full-height angular consoles under a flat hood (`p12`, `p25`); a columned porch on Harlem and Clinton Hill fronts (`p14`, `p18`).
2. **A monochrome stone front**: trim, hoods, sills, water table, stoop and newels all in the wall's brownstone, with fine ashlar joints every 0.3-0.5 m.
3. **A dark, richly bracketed cornice**: wood or pressed metal, near-black or dark brown, with 4-10 brackets and panels, dentils or arched friezes. Some Italianate examples carry frieze windows.
4. **Sills on corbels and eared hoods** for each window, individually; no continuous storey bands.
5. **Renaissance Revival (1890-1905)**: limestone or pale brownstone, rounded bow fronts, carved swags, a swelling stoop with solid balustrade (`p04`, `p27`, `p28`, `q06`, `q07`).
6. **Queen Anne and picturesque Romanesque roofs**: gables, stepped gables, turrets, oriels and tile roofs (`q02`, `q10`, `q12`, `p19`).
7. **Rounded bays** as well as angled ones.
8. **A bay head** (cornice, balcony or balustrade) where a bay stops below the house's top.
9. **The row**: identical neighbours, aligned cornices and party walls. A brownstone almost never shows a side wall. The strip draws each house freestanding against the sky, and nothing in the rules lets a row repeat or vary a builder's design.
10. **Cast-iron newels and railings**: heavy newels about 0.3 m square and 1.2 m tall, with railings that scroll at the foot (`p08`, `p12`, `p13`).
11. **Romanesque window detail**: transom bars, small-paned or stained-glass transoms, and grouped arcades.
12. **Early brick houses**: brick fronts with brownstone trim, before about 1860 and on modest streets.

## 3. What the drawings show that no real front has

1. Cream or tan hoods, surrounds and cornice on a brownstone wall (every Italianate and Neo-Grec render).
2. Full-height vertical lines between the bays, from basement to cornice.
3. Window hoods reading as continuous horizontal bands across the front.
4. A door with no surround of its own, or with a hood identical to the windows'.
5. A pale beige stoop block, with no visible treads, on a brown front.
6. Neo-Grec bay pilasters standing free with no bay head (`docs/strips` Neo-Grec 1880).
7. A Romanesque front with a uniform bracketed cornice and brick uppers in bright orange. Real Romanesque brick is darker red, with rock-faced trim and contrasting voussoirs.
8. Slender upper-floor lights (h/w ≈ 2.0).

## 4. Giveaways, ranked

1. **Cream trim and pale cornice on brown stone.** It changes the whole read from brownstone to brick-and-limestone. Fix: trim in the wall's stone colour, a shade darker or lighter at most; cornice near-black or dark brown.
2. **No door enframement.** The eye looks for the doorway first and finds nothing. Fix: a door surround with consoles and a hood or pediment for each dress, wider than the door by about 0.3-0.5 m each side.
3. **Vertical full-height bay lines.** Fix: draw no edges on non-bay cells of a flat front.
4. **Continuous storey bands.** Fix: hoods only over each opening, plus a sill on corbels under each window.
5. **Thin, sparse cornice.** Fix: 4-10 brackets on a 20 ft front, with panelled frieze; dark paint.
6. **No Renaissance Revival bow fronts after 1891** (R1, R21). It is only a giveaway when late dates are drawn, but there it is the dominant real type.
7. **Italianate stoops in stone, upper windows always segmental** (R26, R13).
8. **Bay fronts missing on 20 ft lots, and bays with no head** (R20, R22).
9. **Upper-floor windows too slender** (R9).
10. **Freestanding presentation** with no row context. This is a presentation choice, but it is what a viewer notices next once the dress is fixed.

---

## 5. Photographs consulted

| Ref | Building / row | Use | URL |
|---|---|---|---|
| p01 | Brick rowhouses, Brooklyn ("Park Slope Brownstone") | early brick type, iron stoops | https://commons.wikimedia.org/wiki/File:Park_Slope_Brownstone.jpg |
| p02 | Park Slope house behind a vacant lot | Queen Anne/Romanesque with bay | https://commons.wikimedia.org/wiki/File:Park_Slope_Brownstone_%2848291928226%29.jpg |
| p03 | Park Slope block, NARA 1970s | full-height bays, 4 levels | https://commons.wikimedia.org/wiki/File:BLOCK_OF_BROWNSTONE_RESIDENCES_IN_PARK_SLOPE_OF_BROOKLYN_NEW_YORK_CITY._BROOKLYN_REMAINS_ONE_OF_AMERICA%27S_BEST..._-_NARA_-_555920.jpg |
| p04 | Park Slope limestone bow fronts | Renaissance Revival, stone stoops | https://commons.wikimedia.org/wiki/File:Park_Slope_Brownstones_%282625843478%29.jpg |
| p05 | Union Street, Park Slope | bays, areaway curb | https://commons.wikimedia.org/wiki/File:Union_Street%2C_Park_Slope%2C_Brooklyn.jpg |
| p06 | 147-157 Prospect Place | Italianate, round parlour heads, iron stoops | https://commons.wikimedia.org/wiki/File:147-157_Prospect_Place_Prospect_Heights.jpg |
| p07 | 181-189 Prospect Place | Italianate, flat heads, door pediment, cornice | https://commons.wikimedia.org/wiki/File:181-189_Prospect_Place_Prospect_Heights.jpg |
| p08 | 203-209 Prospect Place | Neo-Grec, 2-storey bays, cast-iron newels | https://commons.wikimedia.org/wiki/File:203-209_Prospect_Place_Prospect_Heights.jpg |
| p09 | 147-159 Prospect Place | Italianate row, cornices, top floor | https://commons.wikimedia.org/wiki/File:147-159_Prospect_Place_Prospect_Heights.jpg |
| p10 | 161-169 Prospect Place | door consoles, iron stoop | https://commons.wikimedia.org/wiki/File:161-_169_Prospect_Place.jpg |
| p11 | Park Place, Brooklyn | late rows, stoops | https://commons.wikimedia.org/wiki/File:Park_Place_Brooklyn_Jan_2010.jpg |
| p12 | Harlem brownstones | Neo-Grec door consoles, iron stoops | https://commons.wikimedia.org/wiki/File:Harlem%2C_New_York_brownstones.jpg |
| p13 | 17 E. 126th St, Harlem | **measured** frontal row | https://commons.wikimedia.org/wiki/File:17_E._126th_St%2C_Harlem.jpg |
| p14 | Lenox Ave at 123rd St | 4-story-and-basement, columned door porches | https://commons.wikimedia.org/wiki/File:Lenox_123_rowhouses_jeh.jpg |
| p15 | Brooklyn Heights townhouses | early brick, low stoops | https://commons.wikimedia.org/wiki/File:Brooklyn_Heights_Townhouses.jpg |
| p16 | Grace Court, Brooklyn Heights | stone stoop balustrade and newel | https://commons.wikimedia.org/wiki/File:Townhouses_on_Grace_Court_in_Brooklyn_Heights.jpg |
| p18 | 469-475 Clinton Avenue | Italianate with columned veranda | https://commons.wikimedia.org/wiki/File:469-475_Clinton_Avenue.jpg |
| p19 | 282-290 DeKalb Avenue | Romanesque/Queen Anne, turret, gables | https://commons.wikimedia.org/wiki/File:282-290_Dekalb_Avenue.jpg |
| p20 | 206-224 Kane Street | full-length round-arched parlour windows | https://commons.wikimedia.org/wiki/File:206_-_224_Kane_Street_Brooklyn.jpg |
| p21 | 101-127 St. Felix Street | Italianate, segmental top floor, bracketed cornices | https://commons.wikimedia.org/wiki/File:101-127_St._Felix_Street.jpg |
| p22 | 83-89 Hanson Place | brick front with brownstone trim | https://commons.wikimedia.org/wiki/File:83-89_Hanson_Place.jpg |
| p23 | Marcy Ave between Madison and Monroe | Romanesque arches, rock-face | https://commons.wikimedia.org/wiki/File:Bed-Stuy_20191130_-_21_-_Marcy_btwn_Madison_%26_Monroe.jpg |
| p25 | 105-107 South Elliot Place | Neo-Grec door surrounds, incised lintels | https://commons.wikimedia.org/wiki/File:105-107_South_Elliot_Place.jpg |
| p26 | MacDonough Street, Stuyvesant Heights | late rows, arched parlour windows | https://commons.wikimedia.org/wiki/File:MacDonoughStreetSH.jpg |
| p27 | Stuyvesant Heights, 1870-1899 | bow fronts, stone curb | https://commons.wikimedia.org/wiki/File:Brooklyn_brownstones_in_Stuyvesant_Heights_built_between_1870-1899.jpg |
| p28 | Bedford-Stuyvesant row | limestone bow fronts | https://commons.wikimedia.org/wiki/File:Bedford_Stuyvesant_Brooklyn_August_2026_12.jpg |
| q01 | 637-655 Carroll Street | Romanesque, brick over rock-face | https://commons.wikimedia.org/wiki/File:637-655_Carroll_Street_Park_Slope.jpg |
| q02 | 639 Carroll Street | stepped gable, voussoirs | https://commons.wikimedia.org/wiki/File:639_Carroll_Street_Park_Slope.jpg |
| q03 | 749-789 Carroll Street | Neo-Grec full-height bays on 20 ft lots | https://commons.wikimedia.org/wiki/File:749-789_Carroll_Street_Park_Slope.jpg |
| q04 | 263 Hicks Street | 4-story-and-basement Italianate | https://commons.wikimedia.org/wiki/File:263_Hicks_Street.jpg |
| q05 | 22-40 Orange Street | early brick row | https://commons.wikimedia.org/wiki/File:22_-_40_Orange_Street_Brooklyn_Heights.jpg |
| q06 | 22-32 West 96th Street | Renaissance bow fronts, arched top floor | https://commons.wikimedia.org/wiki/File:22-32_West_96th_Street.jpg |
| q07 | 34-42 West 96th Street | limestone bow fronts with bay heads | https://commons.wikimedia.org/wiki/File:34-42_West_96th_Street.jpg |
| q08 | Striver's Row, 265-249 W 139th | late brick Renaissance (out of scope, for contrast) | https://commons.wikimedia.org/wiki/File:2014_Striver%27s_Row_265-249_W_139_by_Stanford_White.jpg |
| q09 | 427A-499 8th Street | long Italianate/Neo-Grec row, dark cornices | https://commons.wikimedia.org/wiki/File:427A-499_8th_Street_Park_Slope.jpg |
| q10 | 146 Sterling Place | Queen Anne, gable, oriel | https://commons.wikimedia.org/wiki/File:146_Sterling_Place_Park_Slope.jpg |
| q11 | 64 Sterling Place | narrow 2-bay house | https://commons.wikimedia.org/wiki/File:64_Sterling_Place_Park_Slope.jpg |
| q12 | 276 Berkeley Place | Romanesque/Queen Anne, rounded bay, tile roof | https://commons.wikimedia.org/wiki/File:276_Berkeley_Place_Park_Slope.jpg |

LPC records: [Park Slope Historic District photo record](https://nyclandmarks.lunaimaging.com/luna/servlet/detail/NYClandmarks~2~2~94273~101323:Park-Slope-Historic-District); [Park Slope Extension II, 2016](https://home4.nyc.gov/site/lpc/about/pr2016/04-12b.page).
