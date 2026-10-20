# Amsterdam canal house: adversarial fidelity review

Model under test: `src/buildings/typologies/amsterdam/amsterdam.toml` (rules), `grammar.py` (gable outline), render `docs/strips/amsterdam.png` (1620 step, 1635 narrow step, 1670 neck, 1700 wide neck, 1750 bell, 1800 cornice).

Method: I looked at 19 photographs and one engraved elevation from Wikimedia Commons, covering 22 or more distinct buildings once neighbours are counted. They include RCE (Rijksdienst voor het Cultureel Erfgoed) survey photographs and Vingboons' engraved elevation of the Cromhout houses. I also read the nl.wikipedia articles on halsgevel, klokgevel, trapgevel and lijstgevel (two of these credit Bureau Monumentenzorg Amsterdam) and a Stadsherstel source on plot widths. Measurements come from photographs, so they are pixel ratios inside one elevation (bay pitch, window width, storey pitch). Proportions within a row are fairly reliable. Absolute metres are not, because Commons photos have no scale; where I give metres, I say which reference I used. Photographs taken from street level shorten the upper storeys, so I only use storey-pitch ratios from the near-frontal shots (Herengracht 203, Leliegracht 7, RCE 20319513, and the Vingboons engraving).

Verdict counts: 6 SUPPORTED, 13 PARTLY, 6 CONTRADICTED, 2 UNTESTABLE.

---

## 1. Claims table

| # | Claim (what the model asserts) | Source | Verdict |
|---|---|---|---|
| C1 | Gable form is a function of date alone: step < 1640, neck < 1720, bell < 1790, straight cornice after | toml:5-6, toml:49; grammar.py:4 | **CONTRADICTED** (boundaries) / order roughly right |
| C2 | Step gables end in 1640 | toml:49 | **CONTRADICTED** |
| C3 | Neck gables run 1640-1720 | toml:49 | **CONTRADICTED** (start ok, end 55 years too early) |
| C4 | Bell gables run 1720-1790 | toml:49 | **PARTLY** (end ok, start 60 years late) |
| C5 | Straight cornice only after 1790 | toml:49, toml:73 | **CONTRADICTED** |
| C6 | Bay (window + pier) 1.8 / 2.2 / 2.6 m; end piers 0.3-0.9 m | toml:25-26 | **SUPPORTED** for 6-9 m lots |
| C7 | 2 to 3 bays only | toml:50 | **PARTLY** (true for the modal house; excludes 1-bay and 4-7-bay fronts) |
| C8 | Window width = 62% of bay | toml:29, toml:138 | **SUPPORTED** for the 17th c. / **PARTLY** for the 18th c. (measured 0.63-0.73) |
| C9 | Souterrain shows 1.5 m above the street | toml:30 | **PARTLY** (0.6-1.6 m seen) |
| C10 | Raised ground floor 3.6 m, first floor 3.4 m (ratio 1.06) | toml:31-32 | **PARTLY / CONTRADICTED for 17th c.** (ground floor 1.3-1.8x the next storey) |
| C11 | Upper storeys shrink geometrically by 0.93 | toml:33 | **SUPPORTED** (direction and rough size) |
| C12 | Always 3 upper storeys below the gable, at every date and width | toml:34 | **PARTLY** (2-3 typical under gables, so the step houses come out too tall) |
| C13 | Step gable = 3 tiers [2.6 m, 0.78w], [2.4 m, 0.52w], [1.9 m, 0.32w] | toml:40 | **SUPPORTED** (widths) / **PARTLY** (tier count) |
| C14 | Step rise 0.75 m, so many small steps (about 9 per side) | grammar.py:31, 49-56 | **CONTRADICTED** |
| C15 | Neck gable = 2 tiers, each 0.4w wide, one window wide, + 1.1 m pediment | toml:37-41 | **PARTLY** |
| C16 | Neck shoulders = short ledge, then concave claw piece | grammar.py:63-67 | **PARTLY** (outline right, ornament absent) |
| C17 | Bell gable = 1 tier 3.0 m, 0.62w wide, + 1.4 m round crown | toml:39-41; grammar.py:74-80 | **PARTLY** (tier) / **CONTRADICTED** (crown shape) |
| C18 | Gable tiers hold as many windows as fit (up to 3) | toml:88-91 | **PARTLY** |
| C19 | Top-tier middle opening is a hoisting hatch/door | toml:156-162 | **PARTLY** |
| C20 | Hoisting beam at the apex | grammar.py:60, 73, 81 | **SUPPORTED** |
| C21 | The whole front, gable and all, is the same dark brick | toml:119-124; grammar.py:99 | **PARTLY** (true for the modal 18th-c. house; wrong for 1600-1665 and for rich fronts) |
| C22 | Every bay holds a tall flat-headed window under a stone lintel, a moulded architrave and no keystone, at every date | toml:132-138 | **CONTRADICTED** for 17th c. (relieving arches) / **PARTLY** otherwise |
| C23 | Souterrain lit by low windows in every bay | toml:140-146 | **PARTLY** |
| C24 | Door always in the first (left) bay, 1.1 m wide, with a transom | toml:150-154 | **PARTLY** |
| C25 | A stoop climbs from the street to the door, over the souterrain, in the door bay | toml:53-55 | **SUPPORTED** (existence) / **PARTLY** (form) |
| C26 | Cornice (straight) house: 0.6 m modillioned cornice | toml:73 | **SUPPORTED** (UNTESTABLE for the depth) |
| C27 | The front is lit only from its two ends (rationale for window share) | toml:29 | **UNTESTABLE** from elevations (plausible) |
| C28 | Class (`klass`) is an input | toml:12 | Never used by any rule, so wealth has no effect: see O1 |

---

## 2. Verdicts with evidence

### C1-C5 Gable form by date (toml:49)
Textual sources (nl.wikipedia, articles partly credited to Bureau Monumentenzorg Amsterdam):
- **Trapgevel:** the Dutch high point is given as about 1600 to about 1665. The model stops at 1640.
- **Halsgevel:** first example Herengracht 168, **1638** (Philips Vingboons). The period is about 1640-1775, and *most were built in the first half of the 18th century*. The model ends necks at 1720, cutting off their most prolific decades. The *raised* neck gable (verhoogde halsgevel, steps and neck together) was built about 1640-1670 as a transitional form, and the model has no such hybrid.
- **Klokgevel:** from about **1660** until 1790; in the 18th century more bells than necks were built. The model starts bells in 1720.
- **Lijstgevel:** *already from 1660*, chosen above all for large double houses. 18th-century cornices often carry an attiek, and the form becomes most common in the 19th century.

Photographic counterexamples:
- Herengracht 168 (1638): a neck gable two years inside the model's "step" period, and **sandstone**, not brick.
- Museum Van Loon, Keizersgracht 672 (1672): a straight cornice with balustrade and statues, 118 years before the model permits one. The Trippenhuis (1660s) is the same case.
- Herengracht 475 (1730s, RM1651): a sandstone cornice front with attic. Its neighbours 473 and 477 are 4-5-bay brick cornice houses with dormers, all in the model's "bell" period.
- RCE 20319513: an 18th-century sandstone 3-bay front with a balustraded cornice and a double stoop.
- Damrak 55: described by nl.wiki as transitional neck/bell, so the two forms overlapped in time.
- Singel 318-330 row: neck, bell and cornice fronts stand side by side. Visually they are coeval, so date alone does not pick the form.

Judgement: the *sequence of fashions* (step, then neck, then bell, then cornice) is right as a statement about which form was *newest*. The model turns it into exclusive bins, and that is wrong in two ways:
1. The forms overlap by decades: step and neck 1638-1665, neck and bell 1660-1775, cornice from 1660 on.
2. In any given year the choice is driven by **wealth and width**: wide or rich houses got cornices from the 1660s on, while narrow houses kept gables through the 18th century. This is not a weak counterexample; the most-cited first neck gable falls in the model's step period. **CONTRADICTED.**

### C6 Bay 1.8-2.6 m (toml:25)
Stadsherstel gives Herengracht plots as 30 ft (8.5 m) and Prinsengracht plots as 22 ft (6.2 m). Three bays on 8.5 m with 0.5-0.9 m end piers give 2.2-2.5 m bays; three bays on 6.2 m give about 1.7-1.9 m. Herengracht 168, 203, Lindengracht 12, Singel 326, Keizersgracht 133 and Leliegracht 7 are all 3-bay fronts on plots of this order. **SUPPORTED** (confidence moderate, since the metres come from plot widths rather than direct measurement).

### C7 2-3 bays (toml:50)
The modal canal house is 3 bays, and 2 bays is common on narrow side-street lots (RCE 20402562, a 2-bay bell). Not rare, and outside the model:
- 4 bays: Keizersgracht 133 has 4 openings at ground level.
- 5 bays: Herengracht 475, Van Loon, and the RCE 20014396 step-gable front.
- 6 or more bays: Huis met de Hoofden, Keizersgracht 123 (1622); Huis Bartolotti, Herengracht 170-172 (1617, bent front).
- Double houses: the Cromhout houses were built as pairs; RCE 20409963 is a "dubbele halsgevel", two neck gables on one 4-bay front.

At the other end, 1-bay houses exist (the narrowest Amsterdam houses are about 2 m wide). **PARTLY:** the range covers most houses, but by excluding wide fronts it erases most of the rich houses that make up the Golden Bend.

### C8 Window 62% of bay (toml:29)
Measured as window width / bay pitch on near-frontal photos:

| House | Ratio | Notes |
|---|---|---|
| Herengracht 203 (c.1618) | 40/63 px = **0.63** | |
| Lindengracht 12 (bell) | 55/75 = **0.73** | |
| Singel 326 | 67/95 = **0.70** | |
| Leliegracht 7 | 35/50 = **0.70** | |
| Vingboons Cromhout elevation (1660s) | **0.60-0.65** | |

17th-century fronts sit right at 0.62. 18th-century sash fronts run 0.68-0.73: brick piers shrank as sashes grew. **SUPPORTED** for the 17th c., **PARTLY** for the 18th c. The share should rise with date.

### C9 Souterrain 1.5 m (toml:30)
Basement windows and doors visible above street level:
- Herengracht 168: about 1.3-1.5 m, with a basement door under the stoop. Reference: the basement door is about 1.6 m, against a front door of about 2.4 m.
- Singel 326 and Leliegracht 7: about 1.2-1.5 m.
- Herengracht 203 (1618): about 0.7 m, with only about 3 steps up.
- Damrak 55 and RCE 20298714 (shopfronts): 0 m, with no stoop at all.

Listings give a 2.66 m souterrain ceiling (Keizersgracht 631), consistent with about half of it above ground. **PARTLY:** 1.5 m is the upper end of the range for 18th-century houses on the main canals, and too high for early 17th-century and commercial fronts.

### C10 Ground 3.6 / first 3.4 (toml:31-32)
Ground-floor storey pitch against the storey above:
- Herengracht 203 (frontal, sill-to-sill): 105 : 75 px, so **1.4x**.
- Leliegracht 7: ground window 120 px tall against 65 px for upper windows; storey pitch about **1.6x**.
- Singel 326: about **1.8x**, though the low camera exaggerates this.
- Vingboons Cromhout elevation (no perspective): ground storey including the door about **1.3x** the first floor.

The tall front room (voorhuis, later the bel-etage) is the defining proportion of the canal house. The model's 1.06 ratio flattens it. **CONTRADICTED** for 17th-c. houses, **PARTLY** for 18th-c. ones (about 1.2-1.3x).

### C11 Taper 0.93 (toml:33)
From the first floor upward, storeys diminish in every photo. Frontal measurements give about 0.85-0.95 per storey: Herengracht 203 75 then 65 px (0.87); Cromhout engraving about 0.9. **SUPPORTED.**

### C12 Three uppers at every date (toml:34)
Full-width storeys above the ground floor, below the gable or cornice:

| House | Uppers | Gable or crown |
|---|---|---|
| Herengracht 203 | 2 | + 2-tier step gable |
| Keizersgracht 133 | 2 | + 3-tier raised neck |
| Cromhout houses | 2 | + neck |
| Leliegracht 7 | 2 | + 2-tier bell |
| Lindengracht 12 | 3 | + 1-tier bell |
| Singel 326 | 3 | + neck |
| Damrak 55 | 3 | + neck/bell |
| RCE 20402562 | 3 | |
| Herengracht 475 | 2 | + attic |

So 2-3 uppers is the range. The model's fixed 3 uppers, plus a 3-tier step gable, gives the 1620 house 8 window rows over 21.5 m (14.6 m front + 6.9 m gable). No photographed step-gable house has more than 6 rows. **PARTLY:** right for 18th-c. narrow houses, too tall for step-gable ones.

### C13 Step tiers 0.78 / 0.52 / 0.32 (toml:40)
Herengracht 203: the gable tiers hold 3, 2 and 1 (small) windows, at about 0.75, 0.5 and 0.25 of the front width. Bartolotti and the RCE 20014396 drawings agree. The widths are **SUPPORTED**. The tier count is **PARTLY** right: 2 tiers plus a small top is as common as 3.

### C14 Step rise 0.75 m, many small steps (grammar.py:31)
`round(h/0.75)` steps per tier over tiers of 2.6, 2.4 and 1.9 m gives 3+3+3 = **9 steps per side**; the render shows fine staircases.
- Herengracht 203: about 4-5 steps per side, roughly 2 per window tier, each about 1.2-1.4 m. Reference: a gable window of about 1.4 m.
- RCE 20014396 front: 3 per side.
- Bartolotti: about 5 per side, each topped by a volute or obelisk.

nl.wiki's description of the Amsterdam type: steps "often unequal in size and few in number". **CONTRADICTED**, and the effect on the silhouette is plain to see. Real Amsterdam step gables have a few large steps, usually capped with stone and often with scrolls in the angles. The model draws many small brick steps, which reads as Flemish or Hanseatic.

### C15-C16 Neck gable (toml:37-41; grammar.py:62-73)
Neck one window wide:
- Supported by Singel 326, Cromhout 364-370, Damrak 55 and RCE 20298714.
- Contradicted by RCE 20409963 (a double neck gable with a 2-window neck) and Herengracht 168 (a wide sandstone neck).

Neck height: the necks photographed are typically **one** storey plus a pediment (Cromhout: an arched window, then a small window in the pediment zone; Singel 326; Damrak 55). Raised necks (Keizersgracht 133) have 3 tiers. The model's fixed 2 tiers × 2.3-2.6 m, plus a 1.1 m pediment, gives a 6 m neck, taller than in most examples.

Width 0.4w: in the Cromhout engraving the neck is about 0.25-0.3 of each house front. **PARTLY.**

Claw pieces: the outline (a concave quadrant into the 90° corner) is correct. Real claw pieces are carved sandstone scrolls and volutes that fill the corner and often reach the outer bays (Cromhout). The render shows a plain brick curve. **PARTLY.**

### C17 Bell gable (toml:39-41; grammar.py:74-80)
Tier count:
- One tier with one window: Lindengracht 12, Damrak 55, RCE 20409963 (a hatch with shutters).
- Two tiers (3 windows, then 1): Leliegracht 7 and RCE 20402562.

The model's single tier with **2 windows** at 0.62w is wider than any bell I found; at its base the bell body holds about 1 window and about 0.32-0.45w, and with its scroll feet it spans about 0.7w.

Crown: the model draws a semicircle of radius `first.w/2` over the full tier width, which reads as a dome or mushroom (strip, 1750 house). In every photo the bell's own sides converge into a narrow top capped by a small segmental cornice, about 1 window wide and 0.5-1 m high (Lindengracht 12, Leliegracht 7, RCE 20402562). **CONTRADICTED** for the crown shape.

### C18 Windows per tier (toml:88-91)
Fitting by width puts 2-3 windows in lower step tiers, which matches Herengracht 203. In necks and bells the real count is set by form, not fit: 1 for most, 2 for wide or double houses. **PARTLY.**

### C19 Top-tier hatch (toml:156-162)
The top opening is a hatch or door with shutters in RCE 20409963 and Damrak 55 (under the hoist beam), and in warehouse-like spout gables (RCE 20298714, left neighbour). Houses such as Lindengracht 12 and Singel 326 have a glazed window there. The rule only fires when the last tier has a middle bay; for 1-window necks that seems to happen (the render shows doors with shutters at the top of every gable). **PARTLY:** common, not universal.

### C20 Hoist beam (grammar.py)
Present in Damrak 55, Leliegracht 7, Lindengracht 12, RCE 20402562 (the photo title says "hijsbalk") and Cromhout. Often it has a small hood (kap). **SUPPORTED**, though the render's tick is undersized.

### C21 Dark brick everywhere (toml:119-124)
Counterexamples by category, not one-offs:
- (a) **1600-1665 fronts are red brick banded with white sandstone** (speklagen, keystones, relieving-arch tympana): Herengracht 203, Bartolotti, Huis met de Hoofden, Keizersgracht 133, RCE 20014396. That is the whole period the model calls "step".
- (b) **Sandstone fronts** on rich houses: Herengracht 168, 475, Van Loon, RCE 20319513.
- (c) **Timber fronts**: Begijnhof 34, c.1528.
- (d) **Plastered or painted 19th-c. fronts** throughout the Singel row.

For the plain 18th-c. narrow gable house (Lindengracht 12, Singel 326, Leliegracht 7, RCE 20402562), dark brown-red brick with white trim is accurate. **PARTLY.**

### C22 Window dress (toml:132-138)
- 17th-c. windows sit under brick **relieving arches** with sandstone keystones and blocks (Herengracht 203, Keizersgracht 133, RCE 20014396, RCE 20409963), and the rule sets `keystone_present = false`.
- Glazing is date-blind: the render uses the same 4-light cross window in 1620 and 1800. Photos show cross windows with leaded upper lights and shutters below for the 17th c. (Huis met de Hoofden), small-pane sashes for the 18th c. (Lindengracht 12: 3×4 panes per sash; Singel 326), and 2-pane sashes for the 19th c. (Leliegracht 7).
- Flat, white-painted wooden frames set flush in brick are right for the 18th c.

**CONTRADICTED** for the 17th c., **PARTLY** after.

### C23 Souterrain windows in every bay (toml:140-146)
The basement under the stoop usually has a **door** (Herengracht 168, 203, Leliegracht 7, RCE 20402562), and the other bays have barred or shuttered windows. **PARTLY.**

### C24 Door in the first bay (toml:150-154)
Door position observed:
- Right: Herengracht 203, Lindengracht 12, Singel 326, Leliegracht 7, RCE 20402562.
- Left: Herengracht 168, Cromhout (outer bays, mirrored in pairs).
- Centre: Huis met de Hoofden, RCE 20319513, Herengracht 475, Van Loon.

The rule always picks x-min, so the strip has every door on the left. A side door is right for 2-3-bay houses, but the side should vary, and rich 3-5-bay houses have central doors. The 1.1 m width and fanlight are fine; real doors have a fanlight (bovenlicht) and a sandstone or carved-wood doorcase. **PARTLY.**

### C25 Stoop (toml:53-55)
A stoop exists on almost every residential canal house; the exceptions are shopfront houses. Its real form:
- a landing (bordes) in front of the door, with steps running *parallel to the front* from one side (Herengracht 168, Leliegracht 7, Lindengracht 12) or from both sides (Cromhout, RCE 20319513, Herengracht 475);
- iron railings, which are universal;
- the basement door under the landing.

The render shows a bare diagonal stair filling the door bay, with no landing, no railing and no basement door. **SUPPORTED** that a stoop exists, **PARTLY** on its form.

### C26 Cornice
A wooden cornice with consoles is right for late-18th and 19th-c. lijstgevels (Singel row). Rich fronts add an attic or balustrade (Herengracht 475, Van Loon, RCE 20319513), and the raised cornice (verhoogde lijst) is omitted. 0.6 m depth is plausible but untestable from elevations.

---

## 3. Omissions (common on real houses, absent from the model)

| # | Omission | Evidence |
|---|---|---|
| O1 | **Wealth/width as a driver of form.** `klass` is declared (toml:12) and never read. Wide/rich houses: cornice, sandstone, central door, double stoop, 4-7 bays. Narrow houses: gables. | Van Loon, Herengracht 475, RCE 20319513, Huis met de Hoofden vs. Lindengracht 12, Singel 326 |
| O2 | **Spout gable (tuitgevel)**: the warehouse and back-front form, very common in the Jordaan, on Brouwersgracht and on the Prinsen islands. **Point gable (puntgevel)** and **timber fronts** before 1600. | RCE 20298714 (left neighbour), Begijnhof 34 |
| O3 | **Raised neck gable** (steps under a neck, 1640-1670) and the **double neck gable** | Keizersgracht 133, RCE 20409963 |
| O4 | **Sandstone banding, relieving arches, keystones and pilasters** on 1600-1665 fronts (Amsterdam Renaissance, Hendrick de Keyser) | Herengracht 203, Bartolotti, Huis met de Hoofden |
| O5 | **Gable ornament:** sandstone claw pieces, scrolls, festoons, pediments with cartouches, vases, gable stones (gevelstenen) | Cromhout, Herengracht 168, Lindengracht 12, Damrak 55 |
| O6 | **Window types by date:** leaded cross windows with shutters, then small-pane sashes, then big-pane sashes. Also shutters (luiken) on ground and basement windows. | §C22 |
| O7 | **Timber shopfronts (puien)** on the ground floor, with no stoop | Damrak 55, RCE 20298714, Singel row |
| O8 | **Stoop landing, iron railings, basement door under the landing, double stoops** | §C25 |
| O9 | **Forward lean (vooroverhelling)** of gabled fronts; not testable precisely from these photos but conspicuous in RCE 20402562 | — |
| O10 | **Wall anchors (muurankers)**, hoist-beam hoods, the staircase window offset in the middle bay | Herengracht 168: the middle-column windows sit at half-storey heights |
| O11 | **Attic or balustrade over cornices**, the raised cornice, **dormers** (dakkapel) behind cornices | Herengracht 475 neighbours, RCE 20319513, Leliegracht 7 neighbour |
| O12 | **Paint and colour variation:** black-painted brick, grey, ochre plaster; white-painted gable trims and frames | Singel row, Damrak 55 (right neighbour black) |

## 4. Rendering problems (strip vs photographs)

1. **The bell crown is a dome** (1750 house). Real bells close to a narrow segmental cap about 1 window wide; the render's cap is a semicircle about 2 bays wide.
2. **Step gables have about 9 small steps per side.** Amsterdam ones have 3-5 large steps capped with stone, so the render looks Flemish.
3. **The step-gable houses are too tall:** 8 window rows (21.5 m). Real step-gable houses show 5-6 rows.
4. **Neck gables are too tall and bottle-like:** 2 neck tiers plus a pediment. Typical is 1 tier plus a pediment.
5. **Every door is in the left bay** on all six houses; real streets mix sides.
6. **The stoop is a bare diagonal stair** filling the door bay, with no landing, no railing and no basement door under it.
7. **The ground floor hardly reads taller than the first floor.** In photos the bel-etage windows are visibly the tallest, at 1.3-1.8x.
8. **Identical 4-light cross windows from 1620 to 1800.**
9. **Uniform dark brick for 1620/1635.** Those houses should be red brick with white sandstone bands and arches.
10. **No ornament on any gable:** no claw-piece scrolls, festoons or cartouches. The neck and bell outlines are bare brick curves with a cream edge.
11. **A hatch-door with shutters appears at the top of every gable**, including where photos show a plain window.

## 5. What survives

To be fair, these claims withstood the attack:
- the general scheme of a tall, narrow brick front with a gable whose tiers narrow as they rise, holding fewer windows;
- 2-3 bays of about 2.2 m on 6-9 m lots;
- window share of about 0.62 (17th c.);
- upper storeys diminishing upward;
- step-tier widths of about 0.78 / 0.52 / 0.32;
- a raised ground floor over a half-sunk basement reached by a stoop;
- a hoist beam at the apex;
- dark brick for the plain 18th-c. gable house.

None of my counterexamples to these is stronger than "this varies more than the model allows".

The strong hits are:
- C1-C5: the date bins are wrong at every boundary, and the first neck gable (1638) and cornice houses of the 1660s-1730s sit inside the wrong bins;
- C14: step size and count;
- C17: the bell crown;
- C10: ground-floor height;
- C21-C22: materials and windows of the 1600-1665 period.

## 6. Buildings and sources

Photographs and elevations (Wikimedia Commons file pages):
1. Herengracht 168 (1638, Vingboons, first neck gable, sandstone): https://commons.wikimedia.org/wiki/File:WLM2011_-_Amsterdam_-_Herengracht_168.JPG
2. Herengracht 166, right neighbour in the same photo: a dark-painted cornice house.
3. Herengracht 203 (c.1618, step gable, red brick and sandstone): https://commons.wikimedia.org/wiki/File:Amsterdam_Koopmanshuis_Herengracht_203.jpg
4. Huis met de Hoofden, Keizersgracht 123 (1622, wide, central door): https://commons.wikimedia.org/wiki/File:Huis_met_de_Hoofden-Keizersgracht_123.jpg
5. Huis Bartolotti, Herengracht 170-172 (1617): https://commons.wikimedia.org/wiki/File:Huis_Bartolotti,_Herengracht_170,_Hendrick_de_Keyser,_1617.jpg
6. Cromhout houses, Herengracht 364-366, Vingboons engraved elevation (c.1660-62): https://commons.wikimedia.org/wiki/File:Voorgevels_van_de_twee_linker_Cromhouthuizen_te_Amsterdam,_RP-P-1911-3117.jpg
7. Museum Van Loon, Keizersgracht 672 (1672, cornice): https://commons.wikimedia.org/wiki/File:Keizersgracht_672-674.JPG
8. Lindengracht 12 (bell gable): https://commons.wikimedia.org/wiki/File:Amsterdam_Lindengracht_12.JPG
9. Keizersgracht 133 (raised neck gable): https://commons.wikimedia.org/wiki/File:Amsterdam_-_Keizersgracht_133.JPG
10. Singel 326 (neck gable): https://commons.wikimedia.org/wiki/File:Amsterdam_-_Singel_326.JPG
11. Herengracht 475, plus neighbours 473 and 477 (1730s, sandstone cornice): https://commons.wikimedia.org/wiki/File:RM1651_Herengracht_475.jpg
12. Begijnhof 34 (timber front, c.1528): https://commons.wikimedia.org/wiki/File:RM371_Amsterdam_-_Begijnhof_34.jpg
13. Damrak 55 (neck/bell transition, shopfront): https://commons.wikimedia.org/wiki/File:Amsterdam_-_Damrak_55.JPG
14. Leliegracht 7 (2-tier bell gable, stoop with landing): https://commons.wikimedia.org/wiki/File:RM3451_Amsterdam_-_Leliegracht_7.jpg
15. 5-bay front with central step gable (RCE 20014396; house number 246 visible): https://commons.wikimedia.org/wiki/File:Voorgevel_in_vijf_travee%C3%ABn_met_trapgevel_-_Amsterdam_-_20014396_-_RCE.jpg
16. 2-bay bell gable with hoist beam and basement shopfront (RCE 20402562): https://commons.wikimedia.org/wiki/File:Overzicht_van_de_voorgevel_met_klokgevel,_hijsbalk_en_kelderpui_-_Amsterdam_-_20402562_-_RCE.jpg
17. Sandstone 3-bay house with double stoop, balcony and balustrade (RCE 20319513): https://commons.wikimedia.org/wiki/File:Overzicht_voorgevel_grachtenhuis_met_stoep_en_balkon_-_Amsterdam_-_20319513_-_RCE.jpg
18. Neck gable with spout-gable and bell neighbours (RCE 20298714): https://commons.wikimedia.org/wiki/File:Exterieur_VOORGEVEL_(HALSGEVEL),_OVERZICHT_-_Amsterdam_-_20298714_-_RCE.jpg
19. Singel 318-330 street row (neck, bell, cornice mixed): https://commons.wikimedia.org/wiki/File:Amsterdam-singel_330-318.jpg
20. Bell gable and double neck gable (RCE 20409963): https://commons.wikimedia.org/wiki/File:Voorgevels,_klokgevel_en_dubbele_halsgevel_-_Amsterdam_-_20409963_-_RCE.jpg

Texts:
- nl.wikipedia, *Halsgevel*: Herengracht 168 (1638); c.1640-1775; raised neck 1640-1670.
- nl.wikipedia, *Klokgevel*: c.1660-1790; more bells than necks in the 18th c.
- nl.wikipedia, *Trapgevel*: high point c.1600-1665; Amsterdam steps "unequal and few"; S-shaped relieving arches.
- nl.wikipedia, *Lijstgevel*: from 1660; large double houses; 18th-c. attiek; mostly 19th c.
- Stadsherstel, *Vriendenwandeling 2025*: Herengracht plots 30 ft (8.5 m), Prinsengracht 22 ft (6.2 m). https://stadsherstel.nl/wp-content/uploads/2025/09/Vriendenwandeling-2025.pdf
- MVA listing, Keizersgracht 631: bel-etage front room 3.36 m clear, souterrain 2.66 m clear. https://mva.nl/en/koop/woningen/keizersgracht-631
