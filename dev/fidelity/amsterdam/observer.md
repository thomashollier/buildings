# Amsterdam canal house (grachtenpand), c. 1600-1850: facade grammar from photographic reference

Independent observer report. I worked only from photographs, engravings and web sources. I did not look at any existing model.

Method, briefly:
- **Photographs:** about 45 Wikimedia Commons photos of named canal houses, plus RCE (Rijksdienst voor het Cultureel Erfgoed) survey photos of facade rows.
- **Orthographic elevations:** the *Grachtenboek* of Caspar Philips (1768-71), which draws every house on the Herengracht and Keizersgracht as a true elevation. I measured those plates in pixels. It is the best proportion source available, because there is no perspective.
- **Register text:** a text-mined sample of 380 canal-side rijksmonument register descriptions (RCE monument register PDFs), used for gable-type frequencies and dates.
- **Footprints and heights:** a 3DBAG / BAG footprint and height sample for canal addresses, geocoded through PDOK.
- **Dimensions:** in photographs I took dimensions from cars (about 4.7 m long), doors (leaf about 2.2-2.4 m) and stoop steps (about 0.18-0.20 m). Grachtenboek ratios were turned into metres with a 3-bay house width of about 7.0 m. I cross-checked that against 3DBAG eave heights (h70 is about 14-16 m), and the two agree.

Units: m = metres. "Bay" (travee / vensteras) = one vertical column of windows. "Bel-etage" = the raised main floor reached by the stoop. "Souterrain" = the half-sunk basement.

---

## 1. Buildings and sources used

### 1a. Individual buildings (photographs)

| # | Building | Date | What it showed | Source |
|---|---|---|---|---|
| 1 | Herengracht 203 | c. 1618 | Step gable in Amsterdam Renaissance style, 3 bays, relieving arches, storey heights measured with a car for scale | https://commons.wikimedia.org/wiki/File:Amsterdam_Koopmanshuis_Herengracht_203.jpg |
| 2 | Huis Bartolotti, Herengracht 170-172 | 1617 | Brick with sandstone banding, tall step gable, raised entrance | https://commons.wikimedia.org/wiki/File:Huis_Bartolotti,_Herengracht_170,_Hendrick_de_Keyser,_1617.jpg |
| 3 | Herengracht 168 | 1638 (Ph. Vingboons) | First neck gable, sandstone, 3 bays | https://commons.wikimedia.org/wiki/File:Herengracht_168.jpg and https://commons.wikimedia.org/wiki/File:WLM2011_-_Amsterdam_-_Herengracht_168.JPG |
| 4 | Keizersgracht 123, Huis met de Hoofden | 1622 | Wide Renaissance house, 6+ bays, cross windows | https://commons.wikimedia.org/wiki/File:Huis_met_de_Hoofden-Keizersgracht_123.jpg |
| 5 | Korte Prinsengracht 5 | 17th c. (BAG 1653) | Small-step gable with 4-5 steps per side and white step caps | https://commons.wikimedia.org/wiki/File:Korte_Prinsengracht_No_5_Trapgevel.JPG |
| 6 | Bloemgracht 87-91, De Drie Hendricken | 1642 | Row of 3 step gables (RCE photo) | https://commons.wikimedia.org/wiki/File:Exterieur_VOORGEVELS,_OVERZICHT_-_Amsterdam_-_20298470_-_RCE.jpg |
| 7 | Keizersgracht 133 | 17th c. | Raised neck gable: the transition from step to neck | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Keizersgracht_133.JPG |
| 8 | Singel 326 | 18th c. | Neck gable, 3 bays | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Singel_326.JPG |
| 9 | Lindengracht 12 | 18th c. | Bell gable, 3 bays, Louis XV side scrolls | https://commons.wikimedia.org/wiki/File:Amsterdam_Lindengracht_12.JPG |
| 10 | Singel 63 | BAG 1751 | Bell gable, 3 bays, door in an outer bay with a tall fanlight, hoist beam under a cap; main measurement photo | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Singel_63.JPG |
| 11 | Keizersgracht 319 | 1639 (Vingboons) | Neck gable on a wide house; Vingboons' published engraving | https://commons.wikimedia.org/wiki/File:Amsterdam_Keizersgracht_0319_001.JPG and https://commons.wikimedia.org/wiki/File:Ontwerp_voorgevel_van_Vingboons_-_Amsterdam_-_20408669_-_RCE.jpg |
| 12 | Herengracht 386 (Grachtenhuis) | 1663-65 | Wide classical lijstgevel | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Herengracht_386.JPG |
| 13 | Cromhouthuizen, Herengracht 364-370 | 1662 | Run of neck gables (archive photo) | https://commons.wikimedia.org/wiki/File:Stadsarchief_Amsterdam,_Afb_012000006547.jpg |
| 14 | Herengracht 475 | c. 1730 | Sandstone double house, 5 bays, central door, double stoop | https://commons.wikimedia.org/wiki/File:RM1651_Herengracht_475.jpg and https://commons.wikimedia.org/wiki/File:Amsterdam_-_Herengracht_475.JPG |
| 15 | Herengracht 478 and neighbours | 17th-19th c. | Brick lijstgevel, 5 bays, rusticated basement, tarred neighbour | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Herengracht_478.JPG |
| 16 | Keizersgracht 672-674, Museum Van Loon | 1672 | Paired houses, sandstone, balcony over the door | https://commons.wikimedia.org/wiki/File:Keizersgracht_672-674.JPG |
| 17 | Trippenhuis, Kloveniersburgwal 29 | 1660-62 | Giant pilaster palace front (outlier) | https://commons.wikimedia.org/wiki/File:Trippenhuis_2945.jpg |
| 18 | Kloveniersburgwal 26, "Kleine Trippenhuis" | 1696 | 1-bay sandstone front with a bell top | https://commons.wikimedia.org/wiki/File:Kloveniersburgwal_26_-_1696_-_Amsterdam_-_20018350_-_RCE.jpg |
| 19 | Oudezijds Voorburgwal 187 | 1663 | Neck gable with garlands, row of 4 | https://commons.wikimedia.org/wiki/File:RM6081_Oudezijds_Voorburgwal_187.jpg |
| 20 | Prinsengracht 175 | 1661 | Gable stones and 19th-c. shop front on a step-gable house | https://commons.wikimedia.org/wiki/File:Amsterdam_-_Prinsengracht_175.JPG |

Also used from Commons, each titled "Amsterdam - <address>.JPG" (one photographer, mostly near-frontal):
- Herengracht 54, 127, 134-136, 217, 412, 560, 562
- Keizersgracht 52, 86, 140, 424, 492, 678, 804
- Prinsengracht 237, 325, 397, 405, 407, 1077
- Singel 54, 91, 93, 159, 288, 424, 516
- Brouwersgracht 84, 91, 94, 111, 131, 141
- Leidsegracht 63, 68
- Kloveniersburgwal 86a

Warehouses:
- Brouwersgracht warehouse rows: "Voorgevels - Amsterdam - 20016307 - RCE.jpg" and "Brouwersgracht pakhuis, foto 2.JPG"
- Prinsengracht 715

### 1b. Orthographic sources

- **Caspar Philips (Jan Caspar Philips), *Grachtenboek*, 1768-71.** Plates No. 2 and No. 7 measured in detail; plates 3-8 scanned for variety. Commons files are "Philips, Jan Caspar (1700-1775), Afb 010097012557.jpg" to "...012564.jpg", for example https://commons.wikimedia.org/wiki/File:Philips,_Jan_Caspar_(1700-1775),_Afb_010097012557.jpg and https://commons.wikimedia.org/wiki/File:Philips,_Jan_Caspar_(1700-1775),_Afb_010097012562.jpg
  - Keizersgracht from the Binnen-Amstel to the Utrechtsestraat: about 22 houses.
  - Keizersgracht No. 7 row: about 16 houses, including a run of 7 identical neck gables.
  - Herengracht Golden Bend around the Nieuwe Spiegelstraat and Vijzelstraat: about 12 wide houses.
  - Herengracht Reguliersgracht-to-Leidsegracht rows: about 60 houses.
  - In total, more than 100 elevations were seen, and about 25 were measured.
- **Vingboons, *Afbeelsels*:** engraving of a 3-bay neck-gable house, reproduced in the RCE collection (see #11).

### 1c. Data sets and text sources

- **RCE rijksmonumentenregister.** 763 register PDFs were fetched (monument numbers 2-7000, every 10th, plus 1600-1900, every 3rd). Of these, 380 are on canals or burgwallen; 247 of those name the top type.
  - Base URL: https://monumentenregister.cultureelerfgoed.nl/monumenten/pdf/<nr>
  - Examples: 1651 (Herengracht 475), 1726 and 1807 (step gables XVIIa), 1666 (bell gable 1683), 1819 (neck gable).
- **3DBAG** (https://api.3dbag.nl) heights and footprints, with PDOK locatieserver geocoding:
  - 70 canal addresses with a pre-1860 build year.
  - A further 658 deep, narrow pre-1850 footprints in the western canal belt (bbox RD 120550-121150 / 487000-488100).
- **nl.wikipedia:** Halsgevel, Klokgevel, Lijstgevel, Trapgevel and Tuitgevel (dates, first examples). en.wikipedia Canal house: lot widths in feet, foot = 28.13 cm, 7-9 stoop steps.
- **Jaarboek Monumentenzorg 1993 and 1996 (dbnl):**
  - Sash windows in NL from the 1680s.
  - Casements from the mid-17th c.
  - Keur of 1532: timber facades may lean forward 4 duim per roede.
- **MIT OCW 4.175, chapter 2:** single house 3 bays, 25-30 ft; double house 5 bays, 50-60 ft.

---

## 2. Rules

Format: **Rule** - typical value; range; confidence (H/M/L); evidence.

### A. Frontage, bays, piers

**A1. Bay count follows width; three bays is the norm.**
- 3 bays: about 60% of houses.
- 2 bays: about 15%.
- 4 bays (*vierraamsgevel*): about 8%.
- 5 bays (*dubbel huis*): about 10-15% on the Herengracht and Keizersgracht, but under 5% elsewhere.
- 6-7 bays: rare palaces.
- 1 bay: curiosities only.
- In the register sample, "dubbel huis" is 21 of 380 canal entries (5.5%), and "vierraamsgevel" is named only explicitly, 2 times.
- Confidence H.
- Evidence: Grachtenboek rows (about 80% of the houses in the Keizersgracht rows are 3-bay); photo set 1a; register.

**A2. Frontage width by bay count.** Lots were laid out in Amsterdam feet (1 voet = 0.283 m) of 18, 20, 22, 24, 26 and 30 feet. Many lots were later split.

| Bays | Typical width | Range |
|---|---|---|
| 2 | 4.5 m | 3.4-5.2 m |
| 3 | 6.5-7.0 m | 5.2-8.5 m |
| 4 | 9 m | 8-10.5 m |
| 5 | 13-14 m | 11-16 m (two lots) |
| 6-7 | 20-24 m | rare |

- 3DBAG canal sample, pre-1860 houses, footprint short side:
  - Quartiles 4.5 / 5.6 / 10.4 m.
  - Histogram peak at 4.5-6.0 m.
  - Second cluster at 9.5-11 m and a tail at 13-16 m.
- Confidence M. BAG sometimes merges or splits houses, so treat these as indicative.
- Evidence:
  - Korte Prinsengracht 5: 3 bays, 5.7 m.
  - Keizersgracht 678: 3 bays, 5.9 m.
  - Herengracht 203: 3 bays, about 7.4 m from car scale.
  - Grachtenboek 3-bay houses are all equal width within ±5%.

**A3. Bay pitch is the width divided by the bay count, so all bays are equal.**
- Bay pitch is about 2.0-2.4 m in a 3-bay house and about 2.5-2.8 m in a 5-bay classical house.
- Do not make the end bays wider. The outer pier (from the party wall to the first window) is 0.6-1.0 × an inner pier.
- In wide classical houses the central bay is often a projecting frontispiece (*middenrisaliet*), 1-3 bays wide. It is 0.1-0.3 m proud and may have a slightly wider central window or doorway.
- Confidence H.
- Evidence: Grachtenboek plate 2/7 measurements; Herengracht 475, 386, 478.

**A4. Window width as a share of bay pitch.**

| Facade type | Share | Range |
|---|---|---|
| 3-bay brick gable houses of 1650-1800 | 0.60 | 0.55-0.65 |
| Early Renaissance houses, 1600-1640 | about 0.50 | — |
| 5-bay classical/sandstone houses | 0.45-0.50 | — |
| 19th-c. rebuilt ground floors and some Singel houses | 0.70-0.75 | piers shrink to 0.5 m |

- Inner piers are therefore about 0.8-1.0 m in a 3-bay house and 1.2-1.5 m in a 5-bay classical house.
- Window clear width is typically 1.2-1.45 m and nearly constant on all floors.
- Confidence M-H.
- Evidence:
  - Grachtenboek Keizersgracht No. 7 row: window 48 px in a pitch of 79-80 px.
  - Plate 2 row: windows 38-43 px in a pitch of 69 px.
  - Herengracht 203: 0.51. Singel 63: 0.74 at the bel-etage.
  - Golden Bend houses in Grachtenboek: windows about 40 px in a pitch of 85-95 px.

**A5. Windows stack in strict vertical columns from souterrain to attic.** The door takes the place of one column's bel-etage window. Columns never shift between floors in the original design.
- Confidence H.
- Evidence: all Grachtenboek elevations; all photos.

### B. Storeys and vertical zoning

**B1. A standard 3-bay house has this vertical sequence:**
1. a souterrain, half sunk;
2. a raised bel-etage, reached by the stoop;
3. 2-3 upper storeys;
4. one attic storey inside the gable or behind the cornice;
5. the top of the gable.

- Main-body storeys above the souterrain: 4 typical (bel-etage plus 3); 3-5.
- 3DBAG *bouwlagen* for canal houses: 4 most common (31 of 51 with data), then 5 (13), then 3 (6).
- Confidence H.
- Evidence: Grachtenboek; 3DBAG; photos.

**B2. Heights above street.**
- Eave or gable-foot (3DBAG h70 for Herengracht and Keizersgracht houses):
  - typical 14-15.5 m; quartiles 12.1-15.6 m;
  - Prinsengracht lower, median about 12 m.
- Highest point, including the gable top: typical 16-17.5 m, range 12-21 m.
- Wider houses are not much taller:
  - widths 4.5-6 m: median hmax 15.4 m;
  - widths 9-12 m: 17.6 m;
  - widths over 12 m: 17.7 m.
- So the facade aspect (height ÷ width) falls from about 3.5 for a narrow 2-bay house to about 2.3 for a 3-bay house, 1.3 for a 5-bay house, and about 0.8 for a 7-bay house.
- Confidence M-H.
- Evidence: 3DBAG (70 canal addresses and 658 belt footprints); Grachtenboek body height ÷ width of about 2.2 for 3-bay houses.

**B3. Storey heights (3-bay house about 7 m wide). Each storey is shorter than the one below.**

| Level | Typical | Range |
|---|---|---|
| Souterrain floor below street | 0.8-1.0 m | — |
| Bel-etage floor above street | 1.5 m | 1.3-2.0 m (7-9 steps of about 0.19 m) |
| Bel-etage storey height | 4.3 m | 3.9-4.8 m |
| 2nd storey (1st upper) | 3.3 m | 3.0-3.6 m |
| 3rd storey | 2.9 m | 2.5-3.2 m |
| 4th storey | 2.6 m | 2.4-3.0 m |
| Attic in the gable | 2.4-2.8 m to the collar | — |

- Ratio of bel-etage to upper storeys: 1.3-1.8.
- Confidence M.
- Evidence:
  - Grachtenboek No. 7 row: bel-etage pitch 165 px, then 113, 87 and 88 px, against a house width of 247 px.
  - Herengracht 203: 4.4 m, then 3.1 m and about 2.5 m.
  - 3DBAG eave heights constrain the total.

**B4. Stoop (*stoep*) and souterrain.** Every pre-1800 house on a main canal has a stoop to a bel-etage door. The arrangement:
- The landing sits in front of the door and is about 1.3-2.0 m up.
- Stairs run parallel to the facade: one flight, or two symmetrical flights for a central door.
- Iron or stone railings run along the flights.
- The stair occupies 1.5-3 m of pavement depth.
- Under the landing is the souterrain door. Beside it are souterrain windows, about 0.8-1.1 m visible above the pavement, often barred.
- Neighbouring 3-bay houses often place their doors in the adjacent outer bays, so that the two stoops form one shared, mirrored double-flight stair at the party wall.
- In 5-bay houses the door is central, with a double-flight stoop. These are often sculpted, with balusters.
- In the 19th c. many stoops were removed and the entrance moved down to the souterrain.
- Confidence H.
- Evidence: Grachtenboek (dozens of paired stoops on Keizersgracht plates 2/7); en.wiki (7-9 steps); register ("versierde stoep", "stoephek", 35 mentions); photos of Herengracht 475, 168, 127, 386 and Keizersgracht 140, 424, 804.

**B5. Door position and size.**
- In 3-bay houses the door is in an outer bay, left or right. It is about 50/50, and mirrored with the neighbour.
- In 5-bay houses it is in the centre bay.
- In 4-bay houses it is usually in an inner bay or an outer one; this is irregular.
- 2-bay houses: one bay.
- Door leaf: about 1.1-1.3 m wide (often a single leaf) and 2.3-2.6 m high.
- Above it is a fanlight (*bovenlicht*, 0.8-1.3 m tall) with carved or wrought glazing bars. Empire-style radial or oval bars date c. 1790-1830.
- Door plus fanlight equals the bel-etage window height, so their heads align.
- Surround: a framed casing, or in rich houses a sandstone frontispiece with a pediment or balcony.
- Doors are dark green, black or dark brown/oxblood, often with heavy panels.
- Confidence H for position; M for sizes.
- Evidence: Singel 63; Grachtenboek; Herengracht 168, 203, 475; Keizersgracht 140.

### C. Windows

**C1. Window height ÷ width falls going up. Width stays roughly constant, so height shrinks.**

| Floor | Height ÷ width | Typical size |
|---|---|---|
| Bel-etage | 2.6-3.0 | about 1.35 × 3.6-4.0 m (incl. transom); the tallest windows in the house |
| 2nd storey | 1.7-1.9 | about 1.35 × 2.4 m |
| 3rd storey | 1.3-1.5 | about 1.35 × 1.9 m |
| 4th / top storey | 1.0-1.2 | about 1.3 × 1.4 m, often nearly square |
| Gable/attic window or hatch | 0.8-1.5 | narrower, 0.8-1.1 m wide |
| Souterrain | 0.6-1.0 | full bay-column width |

- Confidence M-H.
- Evidence: Grachtenboek No. 7 row (142/48, 85/48, 67/48, 50/48 px); plate 2; Singel 63 photo; Keizersgracht 140, 492, Singel 54.

**C2. Sill and head positions.**
- The bel-etage sill is low: about 0.2-0.6 m above the floor. In the 18th c. the windows run nearly floor to ceiling.
- Upper-floor sills are 0.6-0.9 m above the floor.
- Heads are 0.3-0.6 m below the next floor. That band holds the lintel or relieving arch, and on Renaissance fronts a sandstone band.
- Glass occupies about 70-78% of each storey's height.
- Confidence M.
- Evidence: Grachtenboek measurements (spandrels of 20-38 px in an 85-113 px pitch).

**C3. Glazing by date.**
- **1600-c. 1680: cross windows (*kruiskozijn*).** A stone or timber cross divides the opening:
  - upper lights are leaded and fixed;
  - lower lights are wooden shutters, or later casements;
  - on Renaissance fronts there are relieving arches above, often with brick-and-stone tympana.
- **1680s-1800: sash windows (*schuiframen*).** The lower sash slides. Small panes about 0.25 × 0.30 m in a dense grid:
  - bel-etage: 3 panes wide × 5-7 high, often with a separate transom light;
  - upper floors: 3 × 4 down to 3 × 3.
- **1800-1850 (Empire and after):** fewer, larger panes. Typical patterns:
  - 2 panes wide;
  - 2 × 2 per sash;
  - T-windows with a single pane below and a transom above.
- Glazing bars stay white. Upper floors keep smaller panes longer than the bel-etage.
- Confidence M.
- Evidence: Grachtenboek (all windows drawn with fine grids, 1768); Jaarboek Monumentenzorg 1993 (sash from the 1680s); register ("empire roedenverdeling"); photos (Herengracht 203 cross windows; Keizersgracht 492 and Singel 63 sashes; Prinsengracht 405/407 19th-c. panes).

**C4. Window frames are flush or nearly flush with the brick face.**
- Reveal 0.05-0.12 m.
- Frames are wide (0.08-0.12 m) and painted white or off-white.
- Brick facades have flat or segmental brick arches (*strekken*) over the windows. After about 1700 there are no stone surrounds, except on rich houses (moulded sandstone surrounds, keystones).
- There are no external shutters on 18th-c. house fronts. Shutters (*luiken*) belong to warehouses and to early 17th-c. lower lights.
- Confidence M-H.

### D. The top: gable or cornice

**D1. Top types, dates and frequency.**
- Frequency: from 247 register entries that name the top. Today's mix includes many 19th-c. replacement cornices.
- Dates: from nl.wikipedia and the register.

| Type | Dutch | Built | Share today |
|---|---|---|---|
| Step gable | trapgevel | c. 1600-1665 | about 4% |
| Raised neck gable | verhoogde halsgevel | c. 1640-1670 | <3% |
| Neck gable | halsgevel | c. 1638 (Herengracht 168) to c. 1775; most 1700-1750 | about 21% |
| Bell gable | klokgevel | c. 1660-1790; most 1725-1790 | about 17% |
| Spout gable | tuitgevel | c. 1620-1720; warehouses, back facades, simplified workers' houses | — |
| Straight-cornice front | lijstgevel | wide houses from c. 1660; common from c. 1700; dominant from 1750 | about 58% |

- The lijstgevel was also the usual cheap 19th-c. replacement for a decayed gable.
- Raised-cornice variants (*verhoogde lijst*, a carved central crest) run c. 1700-1780.
- Register dating of lijst tops: XVIIIa 8, XVIIId 7, XIXa 16, XIX(b/c) 24 or more. That is 101 dated, and about half are 19th c.
- Confidence H.
- Evidence: register sample; wiki; Grachtenboek of 1768 already shows lijst tops on most wide houses and neck/bell tops on most 3-bay houses.

**D2. A street of a given date is mixed, not uniform.** In a 1768 Keizersgracht row:
- about 65-75% of 3-bay houses are neck or bell;
- 5-bay houses are lijst with an attic or a hipped roof;
- 2-bay houses can carry any top.

Today, about one canal house in two has a straight cornice, and gables cluster in runs of 2-8 houses, often identical speculative series. A generator should pick tops per house with these weights, conditioned on width and date, and allow runs of identical neighbours.
- Confidence M-H.

**D3. Gable versus width.**
- Gables (step, neck, bell, spout) belong to 2-4-bay houses up to about 9 m wide.
- 5-bay or wider houses almost always have a lijstgevel, often with an attic, balustrade or pediment and a hipped or saddle roof behind. Rare 5-bay exceptions carry a single wide neck, or two neck gables on a double house.
- Confidence H.
- Evidence: Grachtenboek Golden Bend; register ("Dubbel huis ... onder rechte lijst met attiek", 12 or more entries).

**D4. Roof behind.**
- Gabled houses have a saddle roof with its ridge perpendicular to the canal. The gable is a screen in front of the roof.
- Neck and bell shoulders, and step sides, roughly follow the roof slope of about 50-60°.
- Lijst houses have:
  - a saddle roof running back from the canal, hidden by a raised cornice or dormer; or
  - a hipped roof (wide houses), with 1-2 dormers and chimneys visible from the street.
- Confidence M-H.
- Evidence: Grachtenboek plate 2 (roof triangles drawn behind neck gables; hipped roofs on double houses).

**D5. Neck gable (*halsgevel*).** The facade wall rises full-width to the attic floor. The neck is a narrow upright block, flanked by two claw pieces that fill the triangles where the shoulders meet the roof slope.
- Neck width: about 0.40 × facade width (range 0.35-0.45), i.e. about 1 central bay plus its piers, about 2.6-3.0 m.
- Neck height above the eave line: about 0.5 × facade width (0.4-0.6), i.e. 3.2-4.0 m.
- The neck holds one storey: one attic window or hatch on the central axis. Above that is a cap.
- The cap is a segmental, triangular or broken pediment, or a scrolled crest, overhanging the neck by about 0.15 m each side, sometimes with a vase.
- The hoist beam projects from just under the cap.
- **Claw pieces:**
  - Sandstone scrolls, about 0.3 × facade width wide (≈2 m) and 1.2-1.6 m tall, sitting on the eave line.
  - Shape: a quarter-round or an S-scroll, filling a right-angled triangle that is high next to the neck and tapers to the facade edge.
  - Before about 1700 they are lions, dolphins or human figures, or acanthus; after 1700 they are Louis XIV / XV acanthus scrolls.
- Corners at the neck foot are 90°.
- Copings and caps are sandstone (light grey or white-painted).
- Confidence M-H.
- Evidence: Grachtenboek No. 7 row (neck 100 px wide, 133 px tall, claw pieces 75 × 50 px, on houses 247 px wide); Singel 326; Herengracht 168; Oudezijds Voorburgwal 187.

**D6. Raised neck gable (*verhoogde halsgevel*), 1640-1670.** This is a neck gable with one extra step:
- at the eave the facade first steps in once to a wide shoulder piece about 0.6-0.7 × width, one storey tall;
- the neck then rises from that shoulder.

The result holds 2 attic storeys. The lower level has 2-3 windows and the upper level 1. Claw pieces sit at both levels.
- Confidence M.
- Evidence: Keizersgracht 133; wiki; Grachtenboek (a few examples on the Herengracht rows).

**D7. Bell gable (*klokgevel*).** A single curved outline: concave at the foot, then convex (bell-shaped). It rises from the eave line and is topped by a small cap or crest.
- Base width: about 0.6 × facade width (0.55-0.70).
- Height above the eave: about 0.4-0.5 × width.
- It holds one attic storey: one window or hatch, sometimes with a small oculus above. The hoist beam sits under the crest.
- The outline is edged with a broad sandstone band.
- Feet: small scroll curls (*krullen*) or Louis XV rocaille.
- Body: plain brick, with no claw pieces. Simplified side-pieces filled with scale or waffle brick can occur.
- Dates and ornament:
  - 17th c.: lower and plainer, with garlands and a pediment cap;
  - 18th c.: more pronounced curve, rocaille crest and no pediment.
- Confidence M-H.
- Evidence: Singel 63; Lindengracht 12; Kloveniersburgwal 26; Grachtenboek; nl.wiki Klokgevel.

**D8. Step gable (*trapgevel*), 1600-1665.** The steps rise from the eave line on both sides, symmetrically, to a top block that carries a finial or hoist beam.

Two kinds:
- **Amsterdam Renaissance (Hendrick de Keyser style):** few, large, unequal steps, 2-3 per side. Each step is about one storey tall (2.0-3.0 m) and about 0.15-0.2 × width deep.
  - Decoration:
    - claw-piece or volute ornaments in each step's corner;
    - sandstone bands (*speklagen*) at the impost and sill levels of each storey, alternating with red brick;
    - relieving arches with stone tympana over the windows;
    - pinnacles or obelisks on the steps.
  - The gable holds 2-3 storeys: 3 windows, then 2 (or 1 window and a hatch), then a hatch in the top block.
- **Plainer type:** 4-6 small steps per side, each about 0.5-0.9 m, with white stone caps on every step. The gable holds 2 storeys.

- Confidence M.
- Evidence: Herengracht 203; Bartolotti; Korte Prinsengracht 5; Bloemgracht 87-91; register 1726 and 1807 ("trapgevel versierd met kleine blokjes, XVIIa").

**D9. Spout gable (*tuitgevel*), warehouses (*pakhuizen*).**
- The gable is a plain triangle at roof pitch, about 50-60°. Its edges are finished with a brick-on-edge course (*rollaag*).
- At the apex is a small rectangular neck (the *tuit*), about 1/5 of the width, under a little pediment or round cap. The hoist beam projects from it.
- Small flat shoulders or curls sit at the foot of each slope.
- Front layout:
  - A central column of loading doors, one per floor, with wooden shutter doors often painted red, green or black (sometimes white-bordered).
  - One window column each side. Windows are small, often round-arched or with shutters.
  - A wide door at the street, with no stoop.
- Typically 4-6 storeys of low height (2.4-2.8 m), 5-8 m wide. Often in rows with names on gable stones.
- Confidence M-H.
- Evidence: Brouwersgracht RCE rows; Brouwersgracht 91, 94; Prinsengracht 715; Grachtenboek warehouse elevations (plate 4).

**D10. Straight-cornice front (*lijstgevel*).** The brick facade ends at a projecting wooden (later stone) cornice.
- Cornice depth: 0.4-0.7 m.
- Moulding with consoles, or a triglyph frieze after about 1750.
- Behind or on the cornice, one of these:
  - **(a)** a central dormer (*dakkapel*) holding the hoist beam, typically 1, 2 on 4-bay houses (*"met consoles en twee hijsbalken"*);
  - **(b)** a raised central section (*verhoogde lijst*) with a carved crest, about 1.0-1.5 m tall, in 1700-1780;
  - **(c)** on wide houses, an attic storey and/or a stone balustrade with vases or statues (Golden Bend).
- Body storeys for a lijst house are one more than in a gabled house of the same height, because the attic floor is under the roof.
- Confidence M-H.
- Evidence: Grachtenboek Golden Bend; register; Keizersgracht 140, 804; Prinsengracht 405/407; Brouwersgracht 111.

**D11. Hoist beam (*hijsbalk*).**
- Present on almost every gabled house and on most lijst houses.
- A timber beam projects 0.8-1.2 m from the top of the gable (under the neck/bell cap), from the dormer, or from the raised cornice crest.
- It is exactly on the axis of the central bay (or of each half of a double house).
- On gables it is often sheltered by a small timber hood.
- Below it on that axis is the attic hatch or window.
- Confidence H.
- Evidence: Singel 63; Grachtenboek (drawn on most tops); Brouwersgracht 141; register.

**D12. Gable stones and anchors.**
- Gable stones (*gevelstenen*, carved name or sign plaques, about 0.5-0.8 m) are common on 17th-c. houses. They sit at bel-etage-head height, or between the 1st and 2nd storeys in the pier or central bay.
- Iron wall anchors (*muurankers*) show as short decorative bars or S-shapes at each floor level near the party walls and gable edges. There are typically 2 per floor per side, decorative on 17th-c. fronts.
- Confidence M.
- Evidence: Prinsengracht 175 ("D.Bonte Os anno 1661"); Herengracht 203; Singel 63 (anchors visible at each storey).

### E. Materials and colour

**E1. Brick and colour shares.**
- Wall material: small hand-made brick in stretcher/cross bond, with thin joints.
- The shares below are from the photo set of about 40 houses.

| Facade finish | Share | Notes |
|---|---|---|
| Unpainted brick | about 60-65% | red-brown to purple-brown, mid-dark (approx. #6b3a2a-#8a4a35); 17th c. brighter red (#9a4030) |
| Tarred, oiled or painted black or near-black | about 15-25% | very common; also dark grey-brown |
| Plastered or painted white, cream or light grey | about 10% | often 19th-c. lijstgevels |
| Natural sandstone or limestone ashlar | about 5% | rich houses only |

- Confidence M.
- Evidence: s1/s2 photo sets (Brouwersgracht 131 and 141, Leidsegracht 68, Prinsengracht 325 and Singel 91 black; Herengracht 127 and Singel 288 white; Herengracht 412 and 475 stone).

**E2. Trim and other colours.**
- Window frames and sashes: white or off-white (some cream). On black facades this is near-universal and strongly contrasting.
- Cornices: white or cream.
- Stone trim: sandstone left grey-buff or painted white. This covers copings, neck and bell edges, claw pieces, caps, frontispieces, the plinth, the stoop, and souterrain window surrounds.
- Doors: dark green, black or brown.
- Stoop railings: black iron.
- Warehouse shutters: red, green, black or white, sometimes with diagonal two-colour stripes.
- Confidence M-H.

**E3. Plinth.** The souterrain zone, up to bel-etage floor level, is usually stone-faced or plastered and painted grey or white. Rich houses use a rusticated (*geblokt*) sandstone plinth. This makes a light band about 1.3-2.0 m tall under a dark brick body.
- Confidence M-H.
- Evidence: Herengracht 478, 475; Singel 63; Keizersgracht 424, 804.

**E4. What changes with date.** Ornament concentrates on the top and the doorway as time goes on.
- **1600-1640:** step gable, brick with stone bands and relieving-arch tympana; cross windows; lower window share of the bay (about 0.5).
- **1640-1670:** raised neck and neck gables; sandstone festoons and pilasters on rich houses (Vingboons); classical lijst-and-pilaster fronts on double houses.
- **1670-1750:** neck and bell gables; plain brick bodies; sash windows; Louis XIV carved tops and doors.
- **1750-1800:** bell gables and lijst tops dominate; Louis XV / XVI ornament; window share up to about 0.65.
- **1800-1850:** straight cornices (often replacing gables); Empire doors and fanlights; larger panes; plastered or white-painted fronts; stoops start to disappear.
- Confidence M-H.

**E5. What changes with wealth.** The extremes are 2-bay brick houses with a plain bell or spout and few ornaments, and 5-7-bay houses with sandstone or ashlar, corner pilaster strips (*hoeklisenen*), sculpted attics and statues.
- Wealth means more width (A2).
- Sandstone instead of brick, or at least sandstone frontispieces.
- A central projecting frontispiece.
- A sculpted doorway and balcony.
- Balustraded attics with statues and vases.
- Double, sculpted stoops.
- Taller bel-etage windows.
- Confidence H.
- Evidence: Golden Bend plates; Herengracht 475, 386; Keizersgracht 672.

### F. Things a generator gets wrong without knowing them

**F1. Gables are not on top of the full facade as a separate triangle.** In neck and bell gables the full-width wall stops at the attic floor (eave line), and only the narrow neck or bell continues up. The neck or bell holds one storey, two for a raised neck. Do not put 3-window attic floors inside a neck gable. Do not make the gable a full-width pediment.

**F2. Neighbours differ.**
- Adjacent houses differ in eave height by 0-3 m, and in floor levels and window heads (bel-etage height varies).
- Party walls are not expressed.
- A narrow house beside a tall one exposes plain side brick above the neighbour.
- The only consistency within a street is the stoop line and souterrain zone, plus runs of identical speculative houses (2-8 in a row).

**F3. Mirrored door pairs.** 3-bay houses put the door in an outer bay, and pairs mirror so that stoops meet. Never centre the door of a 3-bay house. That is a 5-bay feature.

**F4. Diminishing windows.** All windows keep the same width but get shorter going up (C1). Uniform window heights on all floors look wrong immediately.

**F5. Tall and narrow but not skinny.** A 3-bay house is about 2.2-2.4 × as tall (to the eave) as it is wide. A narrow 2-bay house is about 3 ×.

**F6. Glass-heavy.** Piers between windows are narrow, under 1 m. Brick shows mostly as narrow piers and spandrel bands. Windows sit almost flush in white frames.

**F7. Forward lean (*op vlucht*).** Facades were deliberately built leaning towards the street. The Keur of 1532 allowed 4 duim per roede for timber fronts, about 1:36. In practice brick fronts lean about 1:25-1:50, so the top of a 16 m front stands 0.3-0.6 m forward. A small default lean, around 1:40, reads as authentic.
- Confidence M.

**F8. No pitched roof visible from the canal on gabled houses.** You see the gable, not the roof. On lijst houses with saddle roofs only the dormer shows. Hipped roofs with chimneys belong to wide houses.

**F9. Hoist beam on the central axis on nearly every house.** Missing it removes a signature element.

**F10. Warehouse front ≠ house front.** Warehouses have:
- a central column of shuttered doors;
- no stoop and no bel-etage;
- low equal storeys;
- a spout gable.
Mixing house windows onto a spout gable is a common error.

**F11. Wide houses are not taller.** 5-7-bay houses carry 3-4 tall storeys plus an attic, at the same overall height as their neighbours (about 16-20 m). Do not scale height with width.

**F12. Souterrain windows and a door under the stoop always exist** on main-canal houses before about 1850. Ground-floor shop fronts (*winkelpui*) are 19th-20th-c. insertions.

---

## 3. Open questions

1. **Absolute frontage distribution.** 3DBAG footprints sometimes merge or split houses, so the 3DBAG medians (about 5.6 m) may run low against the 26-30-foot lots often quoted (7.4-8.5 m). A clean per-house cadastral frontage sample would settle the 3-bay width; I estimate 6.0-7.5 m.
2. **Grachtenboek vertical accuracy.** Basement and stoop heights in the plates (bel-etage floor 2.0-2.4 m above street) look exaggerated next to the 7-9 steps (1.3-1.8 m) in the sources. The storey-height ratios may be partly schematic.
3. **Share of black-painted facades.** It varies strongly by street: high on Brouwersgracht, Singel and in the Jordaan, lower on the Herengracht. 15-25% is a rough figure from about 40 houses.
4. **Original 17th-18th-c. window-frame colour.** It may have been off-white, cream, grey or ochre/"Bentheimer" before the 19th-c. white convention. All modern photos show white.
5. **Step-gable step geometry.** Large versus small steps is not quantified on a measured sample. Many surviving step gables are 19th-20th-c. restorations or reconstructions (e.g. Korte Prinsengracht 5).
6. **4-bay houses (*vierraamsgevel*).** Door placement and top type (lijst with two hoist beams; neck gables are rarer) are under-sampled.
7. **Raised neck gables.** Fewer than 5 examples were seen. The shoulder width (about 0.65 × width) and the number of attic storeys (2) need confirming.
8. **Hoist-beam projection and timber hood size** are estimated, not measured.
9. **Forward-lean values** come from a 1532 timber-facade keur and general literature, not from measured brick fronts.
