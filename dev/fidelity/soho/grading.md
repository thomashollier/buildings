# SoHo cast-iron model: round 1 grading

Graded: `src/buildings/typologies/soho/soho.toml` and `docs/strips/soho.png` (both at 145f629), plus three close renders I drew in scratch from the same grammar (iron 1858 comfortable 1 lot; 1866 grand 2 lots; 1875 comfortable 2 lots, seed 3). Evidence: `observer.md` (blind, 27 buildings, HABS frontal shots of Haughwout as the ratio anchor) and `adversary.md` (34 photos of 33 buildings, 600 derivations tallied). No other file was changed.

The cast-iron loft is graded in full. The brick store-and-loft and Federal house are graded only under Variety, since they share the recipe.

A = matches the evidence; B = right in kind, needs tuning; C = wrong in places or missing a key variant; D = contradicted, and it changes the read.

## 1. Grades

| Area | Grade | One-line reason |
|---|---|---|
| Proportions | **C** | Storey count, lot, bay pitch and ground height hold; the 0.93 taper plus the 0.8 m top-floor clearance make the top windows 0.4 of the first-floor ones (1866 grand render). Real is 0.85-0.95. |
| Openings | **C** | The round to segmental to flat ramp is right. But the glass sits as dark holes in a flat painted panel (stucco, not iron frame), round heads have no colonnettes, and the sash is one dark pane. |
| Ground floor and entrance | **C** | Column-and-glass store holds. Floor at grade, door always at the right, door unglazed with a token transom, no freight bay. |
| Ironwork | **D** | Fire escapes are floating railings with no stairs or ladder, off-centre on odd-bay fronts, missing on grand fronts. The vault platform is a 0.16 m black line. |
| Top and cornice | **C** | Bracketed cornice depth holds. No frieze under it, the squat top floor, and the crest floats over the cornice as a dome or lantern. No mansard, no water tank. |
| Ornament (incl. grown parts) | **C** | Entablature every floor and fluted columns are good. Capitals are Doric on most fronts (should be Corinthian), no arcade colonnettes, bare aprons, no Neo-Grec detail. The grown crest is the wrong form; the grown lenses are right but almost invisible. |
| Colour | **B** | White-to-buff family is right. Missing the darker shop storey (a quarter of fronts), dark window frames, and blue-grey/black outliers. Sage as a whole-front colour is not in either sample. |
| Variety | **C** | Head ramp and storey odds vary well. Iron is gated by money, one head per front, door side fixed, no pavilion, mansard, giant order or Neo-Grec family. |

## 2. Where the two reports differ, and the call

| Question | Observer | Adversary | Call |
|---|---|---|---|
| Upper storey taper | "almost equal" (Haughwout HABS, two storeys 340 px each); ≤10% drop on some 1850s fronts (L) | 0.97-0.98 a floor; top/first 0.8-0.95 | **taper 0.98**. Both say near-equal. |
| First upper height | 3.6-4.2 side streets, 4.3-5.0 Broadway; shop ≈ 1.2-1.4 × upper | 4.4/4.7 holds; p059 Broadway 5.2 | **first_upper 4.1, grand 4.6** (shop/first then 1.2, inside the observer's ratio). Small change. |
| Shop storey | 4.5-5.0 side, 5.5-6.5 Broadway | 4.9 fine, Broadway 5.5-6.5 | **4.9 keep; grand 5.4 → 5.8.** |
| Window share | glass fraction rises with date: 0.5 (1857), 0.6-0.65 (1871), 0.8-0.85 (1874) | 0.78-0.88 flat/segmental; ~0.6 between colonnettes on arcades | **Share by head**: round 0.62 (+ colonnettes), segmental 0.76, flat 0.84. Both agree on the rise with date. |
| Head gap | entablature ≈ 18% of storey on Haughwout | entablature alone, 0.45-0.6 m | **entablature 0.42 → 0.55; head_gap = entablature + 0.05.** |
| Corinthian | ≈ 16/25 (0.65), any class | 0.65-0.75 every class | **0.7 every class**; class does not gate it. |
| Iron by class | about half of Mercer is brick-over-iron-store | cheap 3-bay iron fronts common; class gate WRONG | **Iron 0.65 for modest/ordinary, 0.85 comfortable/grand**, to 1875. The observer's Mercer brick lofts are the remaining 0.35. |
| Iron after 1880 | Neo-Grec 1870s-80s | ramp 0.7/0.5/0.2 to 1875/1885/1895 (*recall*) | **Ramp, adversary's values**, flagged as recall until checked against the LPC report. |
| Fire escape incidence | ≈ 15/25 (0.6) | ≈ 0.55 of iron fronts, none on Broadway faces | **0.55 iron in every class** (grand now 0); 0.65 brick. |
| Crest / pediment | ≈ 6/25, only on 5+ bay fronts; 3-bay fronts have no centre feature | incidence plausible; form wrong | **0.05 on 1 lot, 0.4 on 2+ lots.** Form per §3.6. |
| Round-arch colonnettes | Haughwout Palladian bay RARE; Hopkins ½ columns; archivolt + keystone usual | every 1850s-60s round front has an arcade (5 named) | **Colonnettes on 0.65 of round fronts** (0.8 comfortable/grand, 0.45 modest/ordinary); archivolt + keystone on all round heads. |
| Head switch on one front | 254 Canal lintelled 2nd storey: 1/25 | top floor switches ~0.25 | **Top-floor switch 0.15; lintelled 2nd storey under arches 0.04.** The adversary's 0.25 is from a smaller set. |
| Two-tone / dark | darker shop storey ≈ 8/25; no black front | black ≈ 1/12; dark ground 20% | **Dark shop storey 0.25; whole black front 0.04.** |
| Mansard | 1/27 | 2 (1868-75) | **0.08** on comfortable/grand 2+ lots, 1867-1877. |

## 3. Ranked fixes

Ranked by how much each changes a viewer's first read.

### 1. Frame, not wall (Openings C → B, Proportions C → B)
Today a 2.55 m bay holds a 1.78 m light with 0.75 m sill, 0.70 m head gap and the flat paint all round; it reads as stucco.
- `window_share` by head (set in `iron_heads_of_their_date`, not the type table): round 0.62, segmental 0.76, flat 0.84. Brick keeps 0.52 (see §3.10).
- `entablature` 0.42 → 0.55; `head_gap` 0.70 → `entablature + 0.05` (0.60). The window head (or arch crown) lands just under the entablature.
- Split each bay's solid into named iron parts rather than one wall fill: an **apron panel** from 0.05 m to the sill (0.6-0.75 m), drawn as a recessed panel with a raised lozenge (comfortable/grand: a sill balustrade instead on 0.35 of grand fronts, every floor; 0.15 on the second floor only), and a **spandrel** above the head, a shade darker than the face (lightness −5%).
- Keep `sill` 0.75 (both hold).

### 2. The top floor (Proportions → A with fix 1)
- `taper` 0.93 → 0.98 (iron); 0.94 → 0.97 (brick).
- Delete `clear` in `a_bay_holds_a_window` for iron and brick lofts (the rule's `let`). The top floor's window runs to its entablature like every other floor; keep the entablature on the top storey too (`role != 'top'` → always, for `entablature_every_floor`).
- Add a crowning **frieze** 0.6-0.9 m (grand 0.9-1.3) between the top entablature and the cornice; it carries the brackets' feet.
- Check on the 1866 grand render: top light goes from 1.27 m (0.39 of first) to ≈ 3.0 m (0.89).

### 3. Fire escapes as stair stacks (Ironwork D → B)
- Shape: a balcony at each upper floor (deck 0.75-0.9 m deep shown as a slatted band, rail 0.95 m), a **diagonal stair** between each pair of balconies running the balcony's width (alternating direction floor to floor), and a **drop ladder** hung under the first balcony, its foot ≈ 2.4-3.0 m above the sidewalk.
- Span 2 bays 0.6, 3 bays 0.4. Position: centred on the middle bay(s) 0.5, at the left or right end 0.5. On odd bay counts "centred" means the middle 1 or 3 bays, not bays `n//2-1, n//2`.
- Incidence 0.55 on iron in every class (`fire_escape_grand` true at the same odds), 0.65 on brick. None before c. 1860 is *not* needed: both reports treat them as part of today's look.
- Colour: black 0.7, the front's own paint 0.3.

### 4. The arcade on round-headed fronts (Ornament C → B)
- On round heads: a **colonnette** under each arch springer, 0.16-0.2 m wide, standing on the apron and rising to the springing line, inside the main pier column. Odds 0.8 comfortable/grand, 0.45 modest/ordinary.
- Every round head gets an **archivolt** (moulded band 0.12-0.15 m around the arch) and a keystone/console (the keystone is there today; the band is not).
- Segmental heads get a plain raised hood 0.1 m, no keystone. Flat heads: plain, or Neo-Grec (§3.9).
- Variant, grand only, 0.15: paired columns at each pier (Cary, 72 Greene).

### 5. Sash and frames (Openings)
- Each window drawn as 2-over-2 double-hung (0.7) or 1-over-1 (0.3): a dark frame 0.06-0.08 m, a meeting rail at 0.5 of the light, one muntin per sash. The upper sash follows the arch or segment.
- Frame colour: dark brown 0.4, bottle green 0.3, black 0.3, contrasting with the light front (observer 18/25). The glass is a separate, slightly lighter fill than the frame.

### 6. The crest becomes part of the cornice (Top C → B)
Remove the panel-plus-lid that floats at `front + cornice_depth * 0.37`. In its place:
- A **pediment** formed by the cornice breaking upward over the centre: triangular 0.55, segmental 0.45, rising 0.8-1.8 m (grand at the top end), carrying the cornice mouldings and brackets round its rake. The `soho.crest` l-system keeps its job but draws the tympanum and raked cornice, not a free plate.
- Width: the middle 3 bays on odd counts, the middle 2 on even counts; the full width when the front has ≤ 3 bays.
- A name or date panel in the tympanum 0.5 (segmental: a date roundel 0.4).
- Odds per §2: 0.05 on 1 lot, 0.4 on 2+ lots (iron); brick 0.15.
- With a pediment, on 0.4 of 5+ bay fronts, also break the storey entablatures forward over the same bays (a shallow centre pavilion, 72 and 28-30 Greene), drawn as a step in each entablature line and doubled columns at the pavilion edges.

### 7. The store front (Ground floor C → B)
- **Door side** 50/50 left/right (`door_side` drawn, not fixed).
- **Entrance**: paired leaves, tall glass over a panelled bottom, ≈ 1.35 m wide × 2.6 m, under a 0.9 m transom (opening ≈ 3.5 m). Today's leaves are solid brown with a 0.3 m transom.
- **Freight bay** on 0.55 of non-Broadway fronts (no Broadway flag exists, so tie it to modest/ordinary/comfortable): wide double doors 1.8-2.4 m × 3.0-3.4 m, wood or sheet iron, in an end bay opposite the stair door.
- Shop glass: keep the 0.45 bulkhead (observer 0.4-0.6) and move the transom band to 2.6-3.0 m above the floor, divided into 3-4 lights per bay.

### 8. The raised loading platform (Ground floor, Ironwork)
- Replace the 0.16 m strip: on 0.5 of iron and brick lofts the store floor stands on a **platform 0.5-0.9 m** high across the frontage, its face iron or granite with cast-iron grilles 0.4 × 0.3 m at 1.5-2 m centres, and **2-4 steps** (0.18 m risers) at the door and freight bay. The whole front rises by the platform height.
- The other 0.5 stand at grade, with a 0.1 m granite curb and no visible platform. The lilac lenses stay (both reports accept them) but go into the platform face's grilles and step treads where they can be seen.

### 9. Orders and the Neo-Grec family (Ornament)
- Capitals: Corinthian/Composite 0.7 in every class; Tuscan/Doric 0.3, rising to 0.5 on flat-headed fronts before 1870. Drop `corinthian_odds` by class.
- Shop columns: fluted or reeded lower third above a ring, smooth above, on a 0.45 m plinth.
- **Neo-Grec** after 1870 on 0.6 of flat-headed fronts: square piers with incised lines instead of round columns, stylised capitals, and a pierced segmental spandrel bracket in each bay under the flat head (478 Broadway, 40 Crosby, 102 Greene); glass share 0.85.
- **Giant order**, 1856-1874, 0.12 of comfortable/grand fronts: storeys paired 2+3 and 4+5 under one arch or between one column, no entablature between the pair, a recessed spandrel panel at the floor line.

### 10. Iron by date, not money (Variety C → B)
- Type rule in `soho.lot`: iron front odds 0.65 (modest/ordinary) or 0.85 (comfortable/grand) to 1875; 0.5 to 1885; 0.2 to 1895; brick store-and-loft otherwise. Dates are *recall*; confirm the 1880s tail against the LPC 1973 report before tuning.
- Class then changes ornament: colonnettes, paired columns, balustrades, pediment height, cornice frieze.
- Head draw: keep `head_ramp`; add a top-floor switch (0.15, to the neighbouring shape in the ramp) and a lintelled second storey under arched floors (0.04).
- Brick store-and-loft windows (both reports): before 1875 share 0.45-0.5 with a hood on every window (pedimented 0.4, segmental 0.4, bracketed lintel 0.2); after 1880 share 0.65-0.8, grouped 2-3 between piers, round-arched top storey or arcade on 0.4. Show the iron store's columns and capitals on brick lofts.
- Federal house: stoop of 4-6 steps over a 1.0-1.3 m basement; after 1850, a shop cut into the ground floor on 0.7.

### 11. Paint (Colour B → A)
- Front: white 4, cream 4, buff 2, pale grey 1.5, blue-grey 0.5, ochre 0.3, black 0.4. Drop sage as a whole-front colour.
- Shop storey a darker colour on 0.25: charcoal, black, dark green, grey-green (sage moves here).
- Cornice: the front's colour (both reports show no contrast).
- Painted brick (grey or cream) on 0.2 of brick lofts (adversary S22).

### 12. Roof silhouette (Top)
- Mansard 0.08 (§2): slate or dark red, one storey of dormers (alternate pedimented and arched), iron cresting.
- Timber water tank behind the cornice on 0.3 of lofts, set back so its top shows 1.5-2.5 m above the cornice.
- Corner urns or finials at the ends of the cornice 0.05 (grand).

## 4. What holds and should not change

- The three types by date and programme, the 1848 and 1840 refusals, the 7.62 m lot.
- Bay pitch 2.3-2.9 m, 3 bays a lot, continuous column lines from shop to cornice.
- Storey count odds (4-7 storeys, adversary's 600-draw tally matches both samples).
- Shop storey 4.9 m, sill 0.75, engaged column 0.36 m.
- An iron entablature at every floor; bracketed cornice projecting 0.8-1.2 m.
- The head ramp by date (round 87% at 1855, segmental 55% at 1865, flat 54% at 1875).
- The white-to-buff palette family and the lilac vault lenses.

## 5. Open questions for round 2

- The iron-front end date and 1880s odds (§3.10) rest on the adversary's recall; one LPC report check settles them.
- Neither report measured a cornice's height (as opposed to projection) on a frontal photo; the frieze figures in §3.2 are the observer's Haughwout ratio and the adversary's estimate.
- Vault lights were inferred by the observer and accepted by the adversary without a photo of the lenses on a SoHo platform; worth one targeted photo before the platform is drawn in detail.
- Corners (Gunther's curved glass, Laing) are out of scope for a mid-block lot, but corner lots carry the longest and richest fronts in both samples.
