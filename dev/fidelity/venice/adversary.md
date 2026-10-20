# Venice palazzo model: adversarial fidelity review

Reviewer brief: try to break `typologies/venice/venice.toml` (and `grammar.py`) with photographic and textual evidence. I changed no files except this one.

**Method.** I looked at 27 distinct buildings, mostly in straight-on Wikimedia Commons photographs (list at the end), and read textual sources: Ruskin's *Stones of Venice* vol. 10, with his own arch measurements; Italian and English Wikipedia; and the Notre Dame Marble catalogue. Measurements come from pixel ratios on near-frontal photos.
- Where I give metres, the anchor is named: a standing person is taken as 1.7 m, and Ruskin's printed arch spans are used for the Fondaco.
- Without an anchor I give only ratios.
- Metric figures are ±10-15% unless stated otherwise.

"Sample" below means the 20 Gothic fronts I could read clearly.

**Bottom line (fair version).** The skeleton is right for the canonical symmetric Grand Canal palazzo:
- a tripartite front;
- a polifora that takes about 35% of the width;
- two windows in each wing;
- a centred, pointed water gate about twice as tall as it is wide.

Several rules nonetheless fail on common cases:
- The polifora light count is capped at 5, and the second floor gets fewer lights than the first. The commonest grand form is the 6-light *esafora*, usually with equal counts on both floors.
- Wing balconettes on the first nobile floor are not universal.
- The model always adds a storey above the second nobile floor; many palazzi have none.
- The "Byzantine = no wings, continuous uniform arcade" claim fails.
- The torreselle and merlons rest on an 1869 reconstruction (the Fondaco) that the sources say invented the merlons.

The rendering also omits the elements that most identify a Venetian Gothic front: tracery, stone frames, quoins, roof and chimneys.

---

## 1. Claims table

| # | Claim (model) | Source line | Verdict |
|---|---|---|---|
| G1 | Every storey is cut wing \| centre \| wing, with the centre on the axis | toml 3-5, 83-93 | **PARTLY** |
| G2 | The centre (portego end) is 40% of the width | toml 44, 84 | **SUPPORTED** (symmetric type) |
| G3 | Storey heights rise with class (water 4.0-5.0, n1 4.6-6.0, n2 4.2-5.6) | toml 36-39 | **UNTESTABLE** by class; absolute values plausible |
| G4 | The first nobile floor is the tallest; the second is 0.4-0.6 m lower | toml 38-39, 76 | **CONTRADICTED** (usually equal; sometimes n2 is taller) |
| G5 | A mezzanine (2.3 m) appears if the house is rich and ≥16 m wide | toml 40, 68 | **PARTLY** (about half the sample has one; it does not follow class) |
| G6 | Always either a full third floor (4.4 m) or an attic (2.9 m) above n2 | toml 41-42, 69 | **CONTRADICTED** (8 of 20 have nothing above n2) |
| G7 | A third floor when width ≥21 m, or when rich and seed is odd | toml 68 | **CONTRADICTED** (Pisani Moretta and Ca' d'Oro are wide and have none) |
| G8 | The water gate is 2-3 m wide whatever the palazzo's width | toml 43, 117, 206-209 | **SUPPORTED** (1.8-3 m; lower bound slightly high) |
| G9 | Gate height is about 2 × width + 0.2 | toml 206, 209 | **SUPPORTED** |
| G10 | The gate head is ogee | toml 209, 217 | **PARTLY** (plain pointed arches are at least as common) |
| G11 | The gate is flanked by lights inside the centre when there is room | toml 114-125 | **SUPPORTED** |
| G12 | On a front ≥20 m with odd seed: two gates, one in each wing bay next to the centre, the centre lit by small windows ("two brothers") | toml 9, 64, 67, 211-217 | **PARTLY** |
| G13 | Wing windows: 1-3 bays per wing, bay 1.8-2.8 m, end 0.5-1.4 m | toml 45-46, 100 | **SUPPORTED** (two per wing is typical) |
| G14 | Wing window: a single ogee light 1.1 m wide, in a moulded frame | toml 187-189 | **SUPPORTED** (15th c.); frame detail wrong |
| G15 | Balconette on every wing window of nobile1; on nobile2 for 2/3 of families; never on the third floor | toml 187-189, 67 | **CONTRADICTED** |
| G16 | Polifora lights: grand 5 / other 4 on nobile1, one fewer on nobile2 and third, minimum 2 | toml 200-201 | **CONTRADICTED** |
| G17 | Smallest polifora light 0.95 m | toml 47, 200 | **SUPPORTED** |
| G18 | Colonnette 0.24 m wide, Corinthian order | toml 201 | **PARTLY** |
| G19 | The polifora has no surround | toml 201 | **CONTRADICTED** |
| G20 | A balcony across the polifora on every nobile floor; none on the third | toml 147-151, 201 | **PARTLY** |
| G21 | Water-storey lights: round-headed, 0.9 × 1.6 m, sill 1.6 m | toml 179-182 | **PARTLY** |
| G22 | Mezzanine and attic lights: small flat-headed windows, 3 in the centre | toml 131-135, 172-176 | **PARTLY** |
| G23 | Walls are rose stucco (`stucco_rose`) | toml 164 | **PARTLY** (about a third of the sample) |
| G24 | A plain bandeau string course on each storey; a modillioned cornice on top | toml 91-92 | **PARTLY** |
| B1 | Before 1300 the type is Veneto-Byzantine; after 1300 Gothic | toml 12, 50, 63, 224 | **PARTLY** (c.1250-1350 overlap) |
| B2 | Byzantine fronts have no wing \| centre \| wing | toml 15, 225-235 | **CONTRADICTED** |
| B3 | The water storey is one portico of round arches on columns across the whole front | toml 15-16, 291-295 | **PARTLY** |
| B4 | Uniform portico arch about 2.6 m with column; minimum 3 arches | toml 56, 295 | **PARTLY** (right magnitude; real arches are graded) |
| B5 | Floor above: a continuous arcade of stilted round arches, about twice as many and half as wide, behind a balustrade | toml 16-18, 298-302 | **PARTLY** (ratio 1.4-1.8; half-width and balustrade right) |
| B6 | Two corner torreselle on fronts ≥18 m; narrower fronts (Ca' da Mosto, Ca' Farsetti) have none | toml 17-19, 55, 226 | **CONTRADICTED** |
| B7 | Each torresella is 17% of the front | toml 54, 226 | **SUPPORTED** (Fondaco 13.5% and 22%, mean about 18%) |
| B8 | A torresella rises a storey (3.8 m) above the cornice and stands forward | toml 18-19, 53, 251-262 | **PARTLY / UNTESTABLE** (true only of the 1869 rebuild) |
| B9 | A torresella opens less: one round arch to the water, a bifora, then a trifora | toml 305-309 | **CONTRADICTED** |
| B10 | Grand Byzantine fronts are crenellated: merlons 0.7 m wide, 1.3 m high, pointed | toml 58, 228; grammar 34-54 | **CONTRADICTED** (historically and dimensionally) |
| B11 | Byzantine fronts are faced in white Istrian stone | toml 19, 281-288 | **PARTLY** |
| B12 | Portico 4.6-6.2 m and loggia 4.4-5.4 m by class | toml 51-52 | **UNTESTABLE** (magnitude plausible) |

---

## 2. Evidence per claim

### G1 Tripartite and symmetric (PARTLY)
**Supporting** (polifora on the axis, two wing windows each side):
- Pisani Moretta
- Bernardo a San Polo
- Morosini Brandolin
- Loredan dell'Ambasciatore
- Danieli (Dandolo)
- Ca' Foscari
- Giustinian (each half)
- Priuli Bon
- Mastelli

**Counterexamples**, where the polifora stands at one side (the "L" or asymmetric front):
- Ca' d'Oro: its asymmetry is documented by Wikipedia as deliberate, for light. The portico and polifore take the left two-thirds.
- Palazzo Ariani: polifora at the left corner.
- Palazzo Zorzi Bon: the polifore are in the left third.
- Ca' Sagredo: polifora at the left; the gate sits under it.
- Palazzo Barbaro: polifora left of centre.
- Palazzo Fortuny (campo front): a 7-light polifora in the left 55%, with one wing window bay to the right.
- Palazzo Soranzo: two polifore, each off-centre in its half.

Contarini Fasan (narrow, three-bay) has no wings at all. Wikipedia: ground floor of "three small rectangular windows", a trifora on nobile1, two single windows on nobile2.

Roughly 8 of the 20 sampled Gothic fronts are not symmetric. The model can only produce the symmetric type, and the strip's 11 m and 14 m houses force wings onto widths where real palazzetti have none.

### G2 Centre share 40% (SUPPORTED)
Polifora width over front width, measured on frontal photos:

| Palazzo | Share |
|---|---|
| Bernardo, n1 / n2 | 34% / 35% |
| Pisani Moretta | 37.5% |
| Morosini Brandolin | 35% |
| Loredan dell'Ambasciatore | 34% |
| Danieli, n1 / n2 | 34% / 37% |
| Ca' d'Oro | 33% |
| Ca' Foscari (oblique photo) | about 47% |

The model's centre is 0.40·w including two 0.45 m piers, so the polifora itself is (0.4w - 0.9). At w = 20 m that is 7.1 m, or 35.5%: a good match. Asymmetric outliers: Fortuny about 55%, Bembo about 53% (twin polifore).

### G3/G4 Storey heights (G4 CONTRADICTED)
String-course-to-string-course ratios on frontal photos:

| Palazzo | water : n1 : n2 (px) |
|---|---|
| Bernardo | 125 : 170 : 173 |
| Pisani Moretta (water + mezzanine together) | 180 : 175 : 180 |
| Ca' d'Oro | n1 280 : n2 280 |
| Morosini Brandolin | 200 : 255 : 275 (n2 taller) |

For Morosini Brandolin, scaling by a 1.7 m person standing on the jetty gives water ≈ 4.5 m, n1 ≈ 5.8 m, n2 ≈ 6.2 m. The person stands in front of the façade, so these figures are probably 5-10% high.

The absolute magnitudes match the model's "grand" values (5.0 / 6.0 / 5.6). The fixed rule "n2 is 0.4-0.6 m lower" does not hold: in 4 of 4 measurable cases n2 is equal or taller. The class dependence is not testable from photographs.

### G5 Mezzanine (PARTLY)
- **Has one:** Pisani Moretta (it.wiki: the ground floor "è sovrastato da mezzanino"), Loredan dell'Ambasciatore, Barbaro, Zorzi Bon (with its own balcony), Giustinian, Bembo.
- **Has none:** Ca' Foscari, Bernardo, Morosini Brandolin, Ca' d'Oro, Ariani, Sagredo.

Both groups include the grandest houses, so the mezzanine is not a wealth signal. Its frequency is about 50% in the sample.

### G6/G7 Always something above n2 (CONTRADICTED)
- **Cornice directly over n2:** Pisani Moretta, Ca' d'Oro, Ariani, Zorzi Bon, Loredan dell'Ambasciatore, Danieli, Mastelli, Contarini Fasan. That is 8 of 20.
- **Full third floor with its own polifora:** Ca' Foscari (6 lights), Bernardo (4 lights), Giustinian (4 lights), Fortuny (trifora). Morosini Brandolin also had a third piano nobile, demolished in the 19th century (it.wiki).
- **Low attic of rectangular windows:** Soranzo, Bembo, Sagredo, and on the Byzantine fronts Farsetti (added 1892) and da Mosto.

The model always emits `attic` or `third`; it needs a "none" outcome. The width ≥21 m trigger is contradicted by Pisani Moretta and Ca' d'Oro, both wide fronts with no third floor.

### G8/G9/G10/G11 Water gate
Width, anchored by a person: Morosini Brandolin gate ≈ 80 px at 44 px/m, so **≈ 1.8 m** wide and ≈ 3.6 m high, a ratio of 2.0. Other gates by front-width ratio, assuming fronts of 20-24 m:
- Bernardo ≈ 2.6 m
- Pisani Moretta ≈ 2.8 m
- Loredan dell'Ambasciatore ≈ 2.9 m (height ≈ 5 m, ratio 1.7)
- Ca' Foscari ≈ 3+ m

The model's 2-3 m range and roughly 2:1 proportion hold; its 2.0 m floor is a little high.

Head shape:
- **Pointed (sesto acuto):** Foscari, Pisani Moretta (it.wiki: "due portali a sesto acuto"), Morosini Brandolin, Zorzi Bon, Mastelli.
- **Ogee with a finial:** Bernardo, Loredan dell'Ambasciatore.
- **Round:** Sagredo, Giustinian, Priuli Bon.

Ogee is not the default; pointed is.

Gate flanked by lights inside the centre: Mastelli (one small pointed light each side) and Ca' Foscari both support G11.

### G12 Two gates (PARTLY)
**Supporting:**
- Bernardo: two gates, each straddling the centre/wing boundary, with barred windows between. The Notre Dame catalogue calls it "a well conserved example of a two-family palazzo". The "brothers" in the model are not attested; "two families" is.
- Morosini Brandolin: two gates in the inner wing bays, three pointed windows between them. This matches the model exactly.
- Palazzo Dandolo Paolucci: Wikipedia ties its two water portals to two-family use.

**Counterexamples to placement:**
- Pisani Moretta: two pointed gates side by side in the **centre**, under the polifora.
- Giustinian: a twin palazzo, where each half repeats the whole tripartite unit with its own gate and polifore. That is three gates across the double front.
- Zorzi Bon: three water arches at irregular spacing.

The commonest real two-family solution (Giustinian, Soranzo, Bembo) doubles the polifora as well, which the model cannot express.

### G13/G14 Wing windows (SUPPORTED)
Two windows per wing in Pisani Moretta, Bernardo, Morosini Brandolin, Loredan dell'Ambasciatore, Danieli and Foscari. Morosini Brandolin wing light ≈ 1.0 m by the person scale, against the model's 1.1 m.

Ogee (inflected) heads are right for 15th-century *gotico fiorito*. 14th-century fronts use plain pointed or trilobed heads: Ariani's nobile1, Fortuny's lower floor, Zorzi Bon in part. The model has no date sensitivity after 1300.

The real frame is a rectangular stone panel with dentil or rope edges and a finial ("dentello" frame), and the pair is often grouped tight to the corner. The model has only a generic moulded architrave.

### G15 Wing balconettes (CONTRADICTED)
- **None on nobile1 wing windows:** Ca' Foscari (only the third floor's wing windows have them), Bernardo, Morosini Brandolin, Loredan dell'Ambasciatore, Bembo.
- **Present:** Pisani Moretta (both floors), Danieli (both floors), Giustinian, Ariani, Ca' d'Oro, Sagredo, Barbaro.

Fortuny is a third pattern: balconettes only at the two ends of the polifora. The model's "always on nobile1" and "never on the third" both fail; Ca' Foscari is the counterexample to both at once.

### G16 Polifora light counts (CONTRADICTED)
Counted on photographs, as nobile1 / nobile2 / third:

| Palazzo | Lights |
|---|---|
| Ca' Foscari | 8 / 8 / 6 |
| Bernardo | 6 / 6 / 4 |
| Pisani Moretta | 6 / 6 (it.wiki: "due ordini di esafore") |
| Ca' d'Oro | 6 / 6 |
| Morosini Brandolin | 6 / 6 (it.wiki: "esafore centrali") |
| Danieli | 6 / 8 |
| Giustinian | 5-6 / 6 / 4 |
| Loredan dell'Ambasciatore | 4 / 4 |
| Fortuny | 7 / 7 / 3 |
| Soranzo | about 5 / 5 |
| Ariani | 4 / 6 |
| Zorzi Bon | 5 / 4 |
| Sagredo | 7-8 / 4 |
| Barbaro | 5 / 4 |
| Mastelli | 3 (round) / 4 |
| Bembo | 5 + 5 / 10 |
| Falier (13th c.) | 5 / 4 |

1. The model's maximum is 5. The modal grand count is **6**, and 7-8 occur.
2. "Nobile2 has one fewer" holds in only 5 of 17 cases. Counts are equal in 8 and n2 has more in 4.
3. The third floor's polifora having fewer lights is supported (Foscari 6 < 8, Bernardo 4 < 6, Giustinian 4 < 6).

With `fits` at 0.95 m minimum light and 0.24 m column, a 7.1 m polifora fits 6 lights. So it is the `want` cap of 5, not geometry, that blocks the esafora.

### G17/G18 Light and colonnette widths
Morosini Brandolin polifora: 8.3 m (person scale) over 6 lights gives a pitch of ≈ 1.38 m and a clear light of ≈ 1.0 m. That supports the 0.95 m minimum.

Colonnettes measured across the capital read 0.3-0.45 m:
- Morosini Brandolin ≈ 0.45 m including the capital.
- Fortuny's are visibly thick, about 0.7 × the light width.
- Ca' Foscari and Contarini Fasan shafts are slender, about 0.25-0.35 m.

So 0.24 m is the thin end of the range. "Corinthian" is a misnomer: the capitals are Gothic foliate or Byzantine basket capitals, and the shafts often have an annulet. This is minor.

### G19 No polifora surround (CONTRADICTED)
Every polifora in the sample sits in a stone frame: a rectangular panel with dentil or rope edges. Most grand ones carry a band of quatrefoil tracery (the "Ducal Palace" pattern) above the arches:
- Foscari n2 and third floor
- Bernardo n2
- Pisani Moretta n1 and n2
- Ca' d'Oro n1 and n2
- Morosini Brandolin n2
- Danieli n1
- Giustinian n2
- Loredan dell'Ambasciatore n1
- Ariani n2 (reticulated)
- Mastelli n2

That is 10 of 20. Its absence is the single largest identity loss in the model.

### G20 Polifora balcony on every nobile floor (PARTLY)
- **Continuous on both floors:** Foscari, Pisani Moretta, Ca' d'Oro, Danieli.
- **Nobile1 only:** Morosini Brandolin, Loredan dell'Ambasciatore.
- **Balconettes only at the two end lights:** Bernardo n2, Fortuny (both floors).

The model has no "ends only" or "n1 only" variant.

### G21 Water-storey lights (PARTLY)
- **Round-headed, barred:** Pisani Moretta, Loredan dell'Ambasciatore, Mastelli. These support the model.
- **Pointed:** Ca' Foscari, Morosini Brandolin, Zorzi Bon.
- **Rectangular, barred:** Bernardo, Contarini Fasan, Soranzo.

The water storey is often clad in Istrian ashlar ("bugnato", Morosini Brandolin per it.wiki) or has a stone base course. The model gives it the same stucco as the floors above.

### G23 stucco_rose (PARTLY)
- **Rose or red stucco:** Pisani Moretta, Danieli, Bembo, Soranzo, Sagredo, Morosini Brandolin (brownish), Priuli Bon (ochre-rose). That is 7 of 20.
- **Exposed brick with white stone trim:** Ca' Foscari, Ariani, Zorzi Bon, Fortuny, Giustinian, Falier, Contarini Fasan, Barzizza. That is 8.
- **Cream or white plaster:** Bernardo, Barbaro, Loredan dell'Ambasciatore, Farsetti, da Mosto. That is 5.
- **Marble cladding:** Ca' d'Oro.

Rose is a legitimate option but not "the" Venetian wall. Exposed brick is at least as common.

### G24 String courses and cornice (PARTLY)
The cornice is dentilled or modillioned under a tiled eave in every case, which supports the model. Real string courses usually run at the sill or balcony line of the floor above, not at the top of each storey. They are frequently rope-moulded ("cordonata": Morosini Brandolin, Loredan dell'Ambasciatore, Contarini Fasan, Ca' d'Oro). The cornice in the render is a thin line, while real cornices project 0.4-0.8 m with visible brackets.

### B1 1300 boundary (PARTLY)
Palazzo Falier (13th c.) and Mastelli's nobile1 keep round Byzantine arches inside fronts that are otherwise tripartite and later. Priuli Bon pairs a Byzantine water storey with a Gothic quadrifora above. A transitional "gotico primitivo" (stilted pointed arches, c.1270-1350) is missing. As a hard switch, 1300 is a defensible simplification.

### B2 No wing \| centre \| wing in Byzantine fronts (CONTRADICTED)
Ruskin (Works 10.146), on the Fondaco, Loredan, Farsetti, Rio-Foscari, Terraced and Madonnetta houses: their arcades are "divided, in each case, into a centre and wings", by bigger central arches and by alternating shafts and pilasters. His counts:
- Ca' Loredan: "five arches in the centre of the lower story, and two in each of its wings"; above, "seven central arches above the five below, and three at the flanks above the two below, the groups being separated by double shafts".
- Ca' Farsetti: "a centre of five arches, and wings of two".

Photographs show the same pattern:
- Ca' da Mosto: a central loggia with single side windows.
- Barzizza: a central 4-light loggia with side windows.
- Falier: a 5-light centre with flanking single arches.

The tripartite front is older than the Gothic, not a Gothic invention.

### B3/B4 Portico (PARTLY)
The Fondaco water storey is an open arcade across the whole front: 10 central arches plus 3 at each end (Ruskin counted 16 before the rebuild). At Loredan and Farsetti the full-width ground arcade survives, but the wing arches are closed or windowed. Ca' da Mosto has a 3-arch "curia" plus a separate water portal, not a full portico.

Ruskin's measured clear spans:
- Fondaco centre 7'6½"-8'1" (2.30-2.46 m), wings 4'5" (1.35 m).
- Loredan 6'1" / 5'2" / 4'9" in the centre (1.85 / 1.57 / 1.45 m), wings 4'6" / 4'4".
- Farsetti 8'0" / 5'10" / 5'4" / 5'3".

Adding a 0.4-0.5 m shaft gives pitches of 1.8-2.9 m, so the model's 2.6 m is the right magnitude. The arches are not uniform, though: they are graded, widest in the middle. Ruskin builds his whole argument on this, and the model ignores it.

### B5 Upper arcade (PARTLY)
Upper-to-lower arch ratios:
- Fondaco 26:16 = 1.6 (Ruskin, pre-rebuild); 18:10 = 1.8 in the rebuilt central body (it.wiki).
- Farsetti 15:9 = 1.67 (it.wiki: "quindici aperture").
- Loredan 13:9 = 1.44 (Ruskin).

So the real ratio is "about 1.5-1.8×", not 2×. "Half as wide" is supported: Fondaco upper central spans are 3'11" (1.19 m) against 2.3-2.46 m below. The continuous balustrade is supported (Farsetti, Loredan, Fondaco).

### B6 Torreselle threshold (CONTRADICTED)
- it.wiki on Ca' da Mosto: originally two storeys "affiancata da torri, dette torreselle", demolished when two more storeys were added. The model cites Ca' da Mosto as a front too narrow for towers.
- Ca' Foscari's predecessor was the "House with the Two Towers" (en.wiki), confirming the type existed beyond the Fondaco.
- Ca' Farsetti and Ca' Loredan are wide (about 22-26 m, estimated from Ruskin's spans) and show no towers today.
- The Fondaco's towers were demolished in 1627 and rebuilt in 1868-69 by Berchet. Zanotto's 1847 reconstruction drawing has no towers (Ruskin notes).

A width threshold is not supported. Towers depended on period and the specific house, not on width.

### B9 Tower openings (CONTRADICTED)
The Fondaco towers continue the arcade rhythm. Ruskin: the 26 upper arches are "four small ones above each lateral three of the lower arcade". The photo shows 3 arches per tower on the water storey and 4 above, plus a 5-light top storey on the rebuilt right tower. The model's single large arch, then bifora, then trifora does not occur.

### B10 Merlons (CONTRADICTED)
- it.wiki (Fondaco): the merlons were "assenti prima della ricostruzione". The Natural History Museum notes that Berchet's source, de' Barbari's 1500 view, does not show battlements.
- Dimensionally, at a scale of ≈ 26 px/m (from Ruskin's 1.19 m upper spans plus shafts), each Fondaco merlon is ≈ 2.4 m wide and ≈ 2.9 m tall, with 12 across the body. The model's 0.7 × 1.3 m merlons are about a third that size, so the render shows a fringe of tiny teeth.

Meanwhile the model gives the Gothic type no cresting, though Ca' d'Oro has a famous one and the Danieli has corner pinnacles.

### B11 Istrian stone (PARTLY)
The Fondaco and Ca' Loredan are stone or marble faced. Farsetti, Ca' da Mosto, Barzizza and Falier are plaster or brick with stone arcades, paterae and formelle.

---

## 3. What real palazzi commonly have that the model omits entirely

1. **Asymmetric (L-type) fronts**, with the polifora toward one end and only one wing (Ca' d'Oro, Ariani, Zorzi Bon, Sagredo, Barbaro, Fortuny). About 40% of the sample.
2. **Narrow palazzetti without wings**, 2-3 bays (Contarini Fasan).
3. **Twin or doubled fronts**, with two polifore side by side for two families (Giustinian, Soranzo, Bembo).
4. **Quatrefoil tracery** over the polifora: 10 of 20.
5. **Stone frames** around every window: rectangular panels with dentil or rope edges and a finial on the ogee.
6. **Istrian-stone quoins** (toothed corner blocks) and **rope-moulded corner and string mouldings** (Foscari, Bernardo, Contarini Fasan, Morosini Brandolin, Danieli, Loredan dell'Ambasciatore, Ca' d'Oro).
7. **Paterae, formelle and coats of arms** set in the wall between openings (Barbaro, Zorzi Bon, da Mosto, Barzizza, Falier, Contarini Fasan, Fondaco), and relief panels (the Ca' Foscari frieze, the Mastelli camel).
8. **Blank framed panels** in the wall between the wing windows and the polifora (Ariani, Morosini Brandolin, Ca' d'Oro).
9. **Istrian ashlar or bugnato water storey** (Morosini Brandolin), and stone base courses on brick fronts.
10. **Hipped tiled roofs** visible above the cornice, **funnel chimneys** (Sagredo, Foscari, Ariani), roof dormers and altane.
11. **Gothic cresting or pinnacles** (Ca' d'Oro, Danieli).
12. **Mezzanine windows with their own balcony**, and small square windows on nobile floors beside the polifora (Bernardo, Fortuny, Danieli).
13. **A water storey with an open portico** in Gothic houses (Ca' d'Oro).
14. **Graded Byzantine arches**, and **paired or double shafts** separating centre and wings (Ruskin).
15. **Stilted arches with extradosed dentil archivolts** and roundels between them in Byzantine arcades.
16. **Steps and a mooring platform**, and painted mooring poles (pali), at the water gate. The render's ground strip is grass-green; a canal front stands in water or on a narrow fondamenta.
17. **Later accretions**: added upper storeys over Byzantine fronts (Farsetti 1892, da Mosto, Loredan). Today these are the dominant look of every Byzantine palazzo the model cites.

## 4. Problems visible in the rendered strips

`docs/strips/venice.png`:
1. **The polifora reads as a row of separate bell or onion shapes** with gaps and small stubs between them. Real polifore are one continuous arcade of cusped ogee arches sharing capitals, inside a rectangular stone frame, usually with a tracery band above.
2. **The water gate is a rectangular panelled double door with a grey triangle over it.** It looks like a door under a gable, not an arched portal. Real gates are a single pointed or ogee-arched opening in a stone frame, often grilled, opening onto steps at water level.
3. **No polifora has more than 5 lights**, even on the 25 m grand front. Real 25 m Grand Canal fronts carry 6-8 lights.
4. **Every front has an attic or third floor.** The 19 m and 25 m grand fronts read as 5-storey blocks, where a typical grand Gothic palazzo has 3-4 storeys plus perhaps a mezzanine.
5. **The 11 m and 14 m fronts are miniature grand palazzi**, with wings of one window each, a 3-light polifora and a centred gate. Real fronts of that width (Contarini Fasan) have no wings or gate.
6. **Wing windows are spread evenly and all carry railings on nobile1.** In reality they pair toward the corners, are often without balconettes, and sit in stone panels.
7. **The wall is uniformly salmon**: no quoins, no stone dressings, no water-storey stone, a hairline cornice and no roof. That makes the fronts look flat and modern.
8. **The polifora gets a balcony on both nobile floors on every front**; see G20.

`docs/strips/venice_byzantine.png`:
1. **No centre/wing articulation and uniform arch sizes.** Ruskin's defining observation, graded arches with a distinct centre and wings, is absent.
2. **Tower openings** (single arch, bifora, trifora) do not match the Fondaco, whose towers carry 3 arches below and 4 above.
3. **Merlons are drawn about a third of their real size**, and they are a 19th-century addition.
4. **"1200, 12 m (Ca' da Mosto)"** shows 4 portico arches and a 7-arch full-width loggia. The real house has a 3-arch curia plus a separate portal, a central loggia with side windows (it.wiki: originally 8 arches), and originally torreselle.
5. **All Byzantine examples are two storeys of white stone.** That is defensible as a reconstruction of the original, but it should be labelled as such: no surviving example looks like this except the rebuilt Fondaco.

## 5. Weak spots in my own evidence (fairness)

- **Absolute metres** rest on one person-scaled photo (Morosini Brandolin) and on Ruskin's printed spans. Front widths elsewhere are assumed at 20-24 m, so the G8 widths are ±20%. The ratios (centre share, light counts, storey ratios) are solid.
- **The sample is biased** toward famous Grand Canal fronts on Wikipedia; minor palazzi on rii are probably even less symmetric, which would strengthen G1.
- **Rebuilt or restored fronts**: Fondaco (1869), Farsetti (1874 and 1892) and Ca' d'Oro (19th-century restoration) are partly restorations. So is Danieli, whose top-floor balconies are probably later. Light counts on these are original, per the sources.
- **The class-dependent storey heights (G3)** cannot be falsified with photographs. I did not mark them contradicted.
- **The "two brothers" story** is unattested, but the two-family reading of two gates is attested (Bernardo, Dandolo Paolucci). The rule is a fair simplification apart from gate placement.

## 6. Buildings and sources

Photographs. All are Wikimedia Commons 1280 px thumbnails under `upload.wikimedia.org/wikipedia/commons/thumb/...`; file names are given as on Commons.

**Gothic (20 fronts)**

| # | Building | Date | Commons file |
|---|---|---|---|
| 1 | Ca' Foscari | 1453 | `(Venice)_Ca'_Foscari.jpg` |
| 2 | Palazzo Bernardo a San Polo | 14th-15th c. | `Palazzo_Bernardo_Canal_Grande_Venezia.jpg` |
| 3 | Palazzo Contarini Fasan | 15th c. | `Palazzo_Contarini_Fasan_(Venice).jpg` |
| 4 | Palazzo Pisani Moretta | 2nd half 15th c. | `0_Venise,_palazzi_Tiepolo_Passi,_Pisani_Moretta_et_Grand_Canal.JPG` |
| 5 | Ca' d'Oro | 1421-1440 | `Ca'_d'Oro_facciata.jpg` |
| 6 | Palazzi Giustinian | 15th c. | `(Venice)_Palazzo_Giustinian.jpg` |
| 7 | Palazzo Soranzo, Campo San Polo | | `Palazzo_Soranzo_(Venice).jpg` |
| 8 | Palazzo Zorzi Bon | | `Palazzo_Zorzi_Bon_(Venice).jpg` |
| 9 | Palazzo Morosini Brandolin | 15th c. | `(Venice)_Palazzo_Morosini_Brandolin.jpg` |
| 10 | Ca' Sagredo | | `Ca'_Sagredo.jpg` |
| 11 | Palazzo Barbaro (Gothic wing) | 1425 | `Palazzo_Barbaro_a_San_Vidal.jpg` |
| 12 | Palazzo Fortuny (Pesaro degli Orfei) | | `Palazzo_Fortuny,_già_Pesaro_Orfei.jpg` |
| 13 | Palazzo Loredan dell'Ambasciatore | | `Palazzo_Loredan_dell'Ambasciatore_(Venice).jpg` |
| 14 | Palazzo Dandolo (Hotel Danieli) | | `Hotel_Danieli-dandolo_2012.jpg` |
| 15 | Palazzo Bembo | | `Palais_Bembo.jpg` |
| 16 | Palazzo Mastelli del Cammello | | `Palazzo_Mastelli_Rio_della_Madonna_dell'Orto_Cannaregio_Venezia.jpg` |
| 17 | Palazzo Priuli Bon | 13th c. base | `(Venice)_Palazzo_Priuli_Bon.jpg` |
| 18 | Palazzo Ariani | 14th c. | `Palazzo_Ariani_(Venice).jpg` |

**Veneto-Byzantine**

| # | Building | Date | Commons file |
|---|---|---|---|
| 19 | Fondaco dei Turchi | rebuilt 1869 | `Fondaco_dei_Turchi.jpg` |
| 20 | Ca' Farsetti | | `Ca'_Farsetti.jpg` |
| 21 | Ca' Loredan | | `Ca'_Loredan_Venice.jpg` |
| 22 | Ca' da Mosto | | `Palazzo_Ca'_da_Mosto_Canal_Grande_Venezia.jpg` |
| 23 | Palazzo Barzizza | | `(Venice)_Palazzo_Barzizza.jpg` |
| 24 | Palazzo Falier, Santi Apostoli | 13th c. | `Palazzo_Falier_(Venice).jpg` |

**Text only**
- 25: Palazzo Dandolo Paolucci (Wikipedia: two water portals, two-family use).
- 26: Ca' Foscari's predecessor, the "House with the Two Towers" (Wikipedia).
- 27: the Rio-Foscari, Terraced and Madonnetta houses (Ruskin).

Texts:
- Ruskin, *Stones of Venice* II, Works vol. 10 pp. 144-150 (arch counts and measured spans: Fondaco, Loredan, Farsetti): https://www.lancaster.ac.uk/fass/ruskin/eSoV/texts/vol10/vol10p146.html , ...p148.html , ...p149.html , ...p150.html
- Ruskin notes on the Fondaco (rebuilt 1868/9; Zanotto's reconstruction had no towers): https://www.lancaster.ac.uk/fass/ruskin/eSoV/notes/mfondacodeiturchi.html
- it.wikipedia, Fondaco dei Turchi (10 arches and an 18-arch loggia; towers added by Berchet; merlons "assenti prima della ricostruzione"): https://it.wikipedia.org/wiki/Fontego_dei_Turchi
- bonjourvenise (towers demolished 1627, rebuilt 1860s): https://bonjourvenise.fr/en/?p=708
- it.wikipedia, Ca' Farsetti (5-arch portico, 15 upper openings, top floor added 1892): https://it.wikipedia.org/wiki/Ca%27_Farsetti
- it.wikipedia, Ca' da Mosto (originally two storeys flanked by torreselle): https://it.wikipedia.org/wiki/Ca%27_da_Mosto
- it.wikipedia, Palazzo Pisani Moretta (two orders of esafore, two central pointed portals, mezzanine): https://it.wikipedia.org/wiki/Palazzo_Pisani_Moretta
- it.wikipedia, Palazzo Morosini Brandolin (two portals, esafore, third piano nobile demolished in the 19th c.): https://it.wikipedia.org/wiki/Palazzo_Morosini_Brandolin
- en.wikipedia: Ca' d'Oro (asymmetric façade), Ca' Foscari, Portego (the polifora's size follows the portego's width), Contarini Fasan (three ground windows, trifora, two monofore), Venetian Gothic architecture (brick vs Istrian stone facing): https://en.wikipedia.org/wiki/Ca%27_d%27Oro , https://en.wikipedia.org/wiki/Ca%27_Foscari , https://en.wikipedia.org/wiki/Portego , https://en.wikipedia.org/wiki/Palazzo_Contarini_Fasan , https://en.wikipedia.org/wiki/Venetian_Gothic_architecture
- Notre Dame Marble, Palazzo Bernardo ("two-family palazzo"): https://marble.nd.edu/item/1j92g734v5h
- en.wikipedia, Palazzo Dandolo Paolucci (two water portals for two-family use): https://en.wikipedia.org/wiki/Palazzo_Dandolo_Paolucci
