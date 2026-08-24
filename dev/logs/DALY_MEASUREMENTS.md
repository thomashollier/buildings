# Daly 1864 — reconciled calibration set

**Source.** César Daly, *L'Architecture privée au XIXme siècle sous Napoléon III*, Série 1, Vol. 1 t.2 (1864). Polona scans, 1920 px wide.
**Inputs.** `dev/logs/daly_measure_{premiere,deuxieme-a,deuxieme-b,troisieme,details}.json`
**Machine-readable output.** `dev/reference/daly_measurements.json`
**Status.** Evidence only. No generator code was read or modified.

---

## 0. What the sample actually is

The unit of observation is a **building**, not a plate. Plate counts overstate the sample:

| Class | Plates | **Distinct buildings** | Printed dimension callouts? |
|---|---|---|---|
| Première | 6 elevation/section + 3 readable detail | **4** (two are elevation+section pairs of the same house) | 1 full storey ladder (125 Champs-Élysées), 1 printed door width (119 CE) |
| Deuxième | 11 elevation + 11 readable detail | **10** (+1 door-only from details) | 7 buildings carry at least one printed callout |
| Troisième | 2 elevation | **2** | **none — both plates are scale-bar only** |

Total: **17 buildings** (16 with measured storeys). Three of the four Première buildings have storey heights the source itself flagged as uncertain, contradictory, or withheld. Read §5 before using any number below.

---

## 1. Per-class summary — median [min – max], n

Storey heights are floor-to-floor. n counts buildings unless marked "st" (storeys).

| Quantity | Première | Deuxième | Troisième |
|---|---|---|---|
| **Ground storey (RdC)** | 4.20 [3.70 – 4.32] n=4 | 3.95 [3.42 – 4.85] n=10 | 3.81 [3.61 – 4.01] n=2 |
| **Entresol** | *none present* n=0 | 2.98 [2.40 – 3.12] n=9 | *none present* n=0 |
| **Compressed level below the nobile** (entresol, or a low 1er where there is none) | 3.40 [3.20 – 3.60] n=4 | 2.98 [2.40 – 3.12] n=10 | *absent* n=0 |
| **Principal / piano nobile** | 4.23 [3.87 – 4.30] n=4 | 3.83 [3.20 – 4.36] n=10 | 3.04 [3.00 – 3.07] n=2 |
| **Upper storeys** (above the nobile) | 3.48 [3.10 – 3.70] n=6 st | 3.07 [2.32 – 3.83] n=25 st | 2.92 [2.84 – 3.00] n=2 st |
| **Storey taper** (geometric step ratio counted *upward from the nobile*) | 0.861 [0.849 – 0.937] n=3 | 0.906 [0.795 – 0.993] n=10 | 0.962 n=**1** |
| **Bay pitch** | 2.81 [2.32 – 3.49] n=4 | 2.85 [2.09 – 3.22] n=10 | 2.54 [2.39 – 2.69] n=2 |
| **Façade width** | 17.05 [14.93 – 18.76] n=4 | 15.61 [11.86 – 19.98] n=10 | 10.42 [8.57 – 12.27] n=2 |
| **Opening width, typical croisée** | 1.14 [1.11 – 1.28] n=4 | 1.24 [1.14 – 1.30] n=10 | 1.07 [1.04 – 1.10] n=2 |
| **Opening height at the nobile** | 2.92 [2.60 – 3.20] n=4 | 2.24 [1.97 – 2.82] n=10 | 2.09 [2.01 – 2.16] n=2 |
| **Opening aspect h/w — nobile** | 2.49 [2.35 – 2.83] n=4 | 2.04 [1.56 – 2.45] n=10 | 1.95 [1.93 – 1.96] n=2 |
| **Opening aspect h/w — uppers** | 1.99 [1.63 – 2.27] n=7 st | 1.80 [1.14 – 2.08] n=22 st | 1.91 [1.79 – 2.00] n=4 st |
| **Opening aspect h/w — entresol** | — | 1.57 [1.28 – 1.83] n=6 | — |
| **Comble share of total height** | 0.139 [0.117 – 0.183] n=4 | 0.149 [0.120 – 0.285] n=10 | 0.120 [0.061 – 0.179] n=2 |
| **Cornice height above pavement** | 19.11 [18.53 – 21.05] n=4 | 18.90 [14.78 – 19.98] n=10 | 15.79 [15.64 – 15.93] n=2 |
| **Cornice band depth** (the moulding itself) | **no data** n=0 | 0.45 [0.33 – 0.68] n=8 | 0.69 [0.45 – 0.92] n=2 |
| **Total height to roof crest** | 22.55 [21.97 – 23.85] n=4 | 22.78 [18.26 – 24.52] n=10 | 18.03 [16.66 – 19.40] n=2 |
| **Door width — all doors** | 2.57 [2.41 – 2.62] n=4 | 1.78 [1.61 – 2.67] n=11 | 1.36 [1.36 – 1.36] n=2 |
| **Door height — all doors** | 3.53 [3.05 – 7.30] n=4 | 3.38 [2.72 – 5.07] n=11 | 2.90 [2.59 – 3.21] n=2 |
| **Lowest balcony deck above pavement** | 6.28 [4.10 – 8.45] n=2 | 6.95 [6.55 – 7.93] n=7 | 7.01 n=1 |
| **Garde-corps height above deck** | 1.07 n=1 | 0.97 [0.87 – 1.03] n=3 | *no balcony data* n=0 |

---

## 2. The spread is the finding

Three quantities where a median alone would be actively misleading:

**Deuxième storey heights are a distribution, not a constant.** The upper-storey population runs **2.32 to 3.83 m** across 25 storeys — a 1.65× span. The corpus contains, at the two extremes:

- **120 blvd de Sébastopol** — 1er, 2e and 3e étages at *exactly* 3.20 m each, verified three independent ways. Zero taper. Differentiation is done entirely by ornament.
- **39 rue Neuve des Mathurins** — 4.15 / 3.70 / 3.15 / 2.32 m, a clean 0.89 / 0.85 / 0.74 taper.

Both are Deuxième Classe, both are by named architects, both are 1864. A generator emitting a single taper constant reproduces neither.

**Comble share is bimodal, not noisy.** Deuxième runs 0.120 to 0.285. The two high values (1 blvd de Sébastopol 0.279, 2–4 blvd de Sébastopol 0.285) are combles containing *two full storeys of accommodation*; the low ones are plain mansards. This is a discrete type choice masquerading as a continuous proportion. Sampling uniformly from [0.12, 0.29] would generate roofs that exist nowhere in the corpus.

**Bay pitch varies more within a class than between classes.** Première alone spans 2.32 → 3.49 m (1.50×); Deuxième spans 2.09 → 3.22 m (1.54×). The between-class difference in medians is 0.04 m. "Première Classe" does not mean one bay rhythm.

---

## 3. The class ladder, quantity by quantity

**Monotonic and large enough to trust the ordering:**

| Quantity | Prem → Deux | Deux → Trois | Total | Note |
|---|---|---|---|---|
| Piano nobile height | −0.39 m (−9%) | −0.79 m (−21%) | **×1.39** | clearest ladder in the corpus |
| Opening height at nobile | −0.68 m (−23%) | −0.15 m (−7%) | **×1.40** | Deux→Trois step is weak |
| Opening aspect at nobile | −0.45 (−18%) | −0.09 (−4%) | ×1.28 | Deux→Trois step is inside the noise |
| Upper-storey height | −0.41 m (−12%) | −0.15 m (−5%) | ×1.19 | Troisième n=2 storeys, one building |
| Façade width | −1.44 m (−8%) | −5.19 m (−33%) | ×1.64 | ranges overlap heavily Prem/Deux |
| Cornice height | −0.21 m (−1%) | −3.11 m (−16%) | ×1.21 | **flat** Prem/Deux, see below |

**Monotonic but too small to be a ladder — treat as FLAT:**

- **Ground storey height** falls only 9% end to end (4.20 → 3.95 → 3.81 m) while Deuxième's range alone (3.42–4.85 m) contains every value in the other two classes. Class-independent.
- **Cornice height above pavement** is flat between Première and Deuxième (19.11 vs 18.90 m) because **both are pinned against the 20 m legal façade maximum of the 1859 decree**. Six of the sixteen buildings sit between 19.0 and 20.0 m. That ceiling, not class, sets the number. The one building far below it (88 rue de Rivoli, 14.78 m) spends its allowance on fewer, taller storeys instead.

**NOT monotonic — flagged explicitly:**

- **Bay pitch.** 2.81 / 2.85 / 2.54 m. Deuxième sits *above* Première.
- **Opening width.** 1.14 / 1.24 / 1.07 m. Deuxième is the *widest*.
- **Comble share.** 0.139 / 0.149 / 0.120. Deuxième is the *highest*.
- **Total height to roof crest.** 22.55 / 22.78 / 18.03 m. Deuxième exceeds Première, because Deuxième combles are taller.
- **Opening aspect at upper storeys.** 1.99 / 1.80 / 1.91. Troisième sits *above* Deuxième.
- **1er étage / ground storey ratio.** 0.834 / 0.993 / 0.789 — inverts. This is the naive ratio a generator would reach for, and it is wrong; see §3b.
- **Cornice band depth.** No Première observation at all, and the Troisième value (0.69) is *higher* than the Deuxième (0.45), inverting the expected ladder.

**Too thin to say anything:**

- **Storey taper ratio.** Première n=3, Troisième n=**1**. The apparent trend (taper weakens down the ladder: 0.861 / 0.906 / 0.962) is plausible and physically sensible, but one Troisième observation cannot support it.
- **Balcony height above pavement.** Première n=2, and the two values (4.10 and 8.45 m) are not even the same storey. Troisième n=1.
- **Everything about Troisième Classe.** Two elevations, two architects, no printed callouts anywhere. Every Troisième figure in §1 should be read as "two buildings did this", not as a distribution.

### 3b. The structural finding that is *not* a scalar

Fourteen of the sixteen buildings with measured storeys have a **compressed level between the commercial ground storey and the piano nobile**, and the two exceptions are both Troisième:

- **Première** dresses it as a full 1er étage: 3.20–3.60 m, 0.83× the ground storey. The noble floor is the **2e**. This holds in 4 of 4.
- **Deuxième** dresses it as an entresol: 2.40–3.12 m, 0.775× the ground storey (median, n=9). The noble floor is the **1er above it**. This holds in 9 of 10; the tenth (88 rue de Rivoli) has no entresol and instead has a low 2.97 m 1er under a 3.88 m 2e — the same shape under a different label.
- **Troisième** has neither. Its étages are equal within 0.07 m. **There is no piano nobile.**

The ratio nobile ÷ compressed level is 1.25 (Première, median) and 1.30 (Deuxième, median) — effectively the same gesture at two social levels.

Caveat that must travel with this: reading A and reading B of 26 rue Bergère disagreed on whether the same physical 3.09 m band was "a low 1er étage" or "an entresol". Storey *roles* in this file are interpretations, not measurements.

---

## 4. Absolute vs proportional — the central question

**The one-line answer: what a body touches is absolute; what a body looks at is proportional.**

### The door — the strongest single result

Reported side by side across all three classes, and then split by door type, because the split is the result:

| | Première | Deuxième | Troisième |
|---|---|---|---|
| **All doors, width** | 2.57 [2.41 – 2.62] n=4 | 1.78 [1.61 – 2.67] n=11 | 1.36 n=2 |
| **Porte cochère (carriage), width** | **2.57 [2.41 – 2.62] n=4** | **2.58 [2.57 – 2.67] n=3** | *none exists* |
| **Porte piétonne (pedestrian), width** | *none exists* | **1.75 [1.61 – 1.91] n=8** | **1.36 [1.36 – 1.36] n=2** |
| Porte cochère, height | 3.49 [3.05 – 3.56] n=3 † | 3.64 [3.47 – 5.00] n=3 | — |
| Porte piétonne, height | — | 3.08 [2.72 – 5.07] n=8 | 2.90 [2.59 – 3.21] n=2 |

† excluding the 7.30 m two-storey carriage arch at Avenue de l'Impératrice, which is an architectural event, not a door height.

Individual carriage-door widths, all seven, both classes pooled and sorted:
**2.410 · 2.534 · 2.570 · 2.575 · 2.600\* · 2.619 · 2.672**  (\* = printed callout, 119 Champs-Élysées)

The carriage door does not know what class of building it is in. Median 2.57 m in Première and 2.58 m in Deuxième — a **0.4% difference across the two top classes**. The whole apparent door-width ladder (2.57 → 1.78 → 1.36) is a ladder of **entitlement**, not of scaling: does this house get a carriage entrance at all? Première: always. Deuxième: 3 of 10. Troisième: never.

Pedestrian doors tell the same story one size down: eight Deuxième doors span 1.609–1.910 m, of which two are printed (1.760 at 87 Sébastopol, 1.630 at 9 rue du Conservatoire). Both Troisième doors are 1.36 m — narrower than any Deuxième door, but n=2, so WEAK.

**Door height is *not* an absolute** and should not be treated as one. It ranges 2.72–5.07 m in Deuxième alone, because the opening sometimes swallows the entresol (5.00, 5.01, 5.07 m) and sometimes stops at a lintel (2.72 m). The *leaf* height is far more stable: 2.95 / 3.25 / 3.55 m on the three buildings where it is separately dimensioned, two of them printed.

### The window — the second-strongest result

Window opening **width** across all sixteen buildings, three classes, façades varying 2.4× in width: **1.04 – 1.30 m**, a 1.25× span, with the *middle* class holding the widest median. One value is a printed callout (1.300 m at 2–4 Sébastopol); a second (1.25 m at 9 rue du Conservatoire) is pixel-read on a plate whose scale is fixed by printed callouts, so its scale error is nil even though its edge-finding error is not. Both agree with the ordinary scale-bar readings. Width is set by the *croisée* — the two-leaf French casement — not by grandeur.

Window **height** at the noble floor over the same sixteen buildings: **1.97 – 3.20 m**, and the class medians run 2.92 / 2.24 / 2.09 — a 1.40× ladder between Première and Troisième alone.

Same aperture. Width absolute, height proportional. That is the cleanest demonstration of the project's central distinction anywhere in this dataset, and it means the class signal in a window lives entirely in its aspect ratio, which is exactly what 39 rue Neuve des Mathurins does deliberately: window widths constant at 1.25 m on every storey, only the height varies.

### Candidates for ABSOLUTE (calibrate as constants)

| Quantity | Value | Range | n | Recommendation |
|---|---|---|---|---|
| Carriage door clear width | 2.58 m | 2.41 – 2.67 | 7 | **SOURCED** |
| Pedestrian door clear width | 1.75 m | 1.61 – 1.91 | 8 | **SOURCED** (Deuxième); Troisième 1.36 m is WEAK |
| Window opening width | 1.20 m | 1.04 – 1.30 | 16 | **SOURCED** |
| Ground storey floor-to-floor | 3.95 m | 3.42 – 4.85 | 16 | **SOURCED** as class-independent |
| Floor structure (plancher) | 0.30 m | 0.30 – 0.30 | 2 | **SOURCED** — both printed |
| Balcony projection from wall face | 0.595 m | 0.59 – 0.60 | 2 | **SOURCED** as a value — both printed, two different buildings, 2% apart |
| Balcony garde-corps height | 1.00 m | 0.87 – 1.07 | 4 | WEAK (n=4) but a clean absolute in shape |
| Bay pitch | 2.80 m | 2.09 – 3.49 | 16 | **SOURCED** as a corpus-wide distribution; INSUFFICIENT as a class discriminator |

### Candidates for PROPORTIONAL (scale with class)

Piano nobile height (×1.39 across the ladder) · window height at the nobile (×1.40) · opening aspect at the nobile · upper-storey height · façade width · cornice height *only* for the drop to Troisième.

Plus three **categorical** class markers that are stronger than any of the scalars: presence of an entresol (0/4 · 9/10 · 0/2), presence of a carriage entrance (4/4 · 3/10 · 0/2), presence of projecting balconies (2/2 measured · 9/10 · 1/2).

---

## 5. Honest limits

**Sample size.** 4 / 10 / 2 buildings. Not 6 / 11 / 2 plates — the pairs are the same buildings.

**Première is thinner than its n=4 suggests.** Only 125 Champs-Élysées carries a printed storey ladder. Of the other three: 3 rue de la Paix has no drawn floor lines at all and every level is source-flagged UNCERTAIN; 119 Champs-Élysées contradicts itself (elevation 1er 3.35 / 2e 4.30 versus its own detail plate 78 at sill-to-sill 1er 3.99 / 2e 3.80, which reverses which storey is taller); Avenue de l'Impératrice had its street-elevation storey heights *deliberately withheld* by the measurer because elevation and section could not be reconciled. **Première storey-height medians rest on one solid building plus three inferences.**

**Troisième has no printed dimensions anywhere.** Both plates are scale-bar only. There is no independent check on either.

**Publication bias.** These are plates a luxury architectural journal chose to publish as exemplars, with named architects credited. They are biased toward the grander, better-designed, better-built end of each class. Nothing here describes the median Paris building of 1864, and the Troisième examples in particular are model tenements — one is a three-house composition by a single architect with perfectly aligned floor levels — not ordinary speculative work.

**One date.** Every plate is 1864. No evidence about drift across 1850–1914. The 20 m cornice ceiling that flattens the Première/Deuxième difference is the **1859** decree; it moves under the 1884 and 1902 rules, so that flatness is a fact about one regulatory moment, not about class.

**Geographic concentration.** Seven of the seventeen buildings are on the boulevard de Sébastopol or the rue de Rivoli — one Haussmann corridor, one set of frontage conditions, largely one group of architects. Treat that group as a cluster, not as seven independent samples.

**Scale-bar reading carries error; printed callouts do not.** The metre bars themselves resolve to ~0.3%. The error is not in the bar, it is in the *datum*. Three hard measurements of that error:

1. **26 rue Bergère was measured twice, independently.** Façade width 17.349 vs 17.380 m (0.2%). Bay pitch 2.802 vs 2.810 m (0.3%). Total height 23.528 vs 23.400 m (0.5%). But: individual storey heights differ by up to **0.36 m (9%)**, comble height 4.32 vs 5.12 m (**19%**), eaves height 19.208 vs 18.280 m (5%), carriage door width 2.754 vs 2.590 m (**6%**), window width up to **15%**.
2. **119 Champs-Élysées porte cochère**: 2.99 m read off the elevation against a **printed 2.600 m** on the plan — a **15% error** in a scale-bar width reading, caught only because a printed value existed.
3. **120 blvd de Sébastopol door**: 1.80 × 3.40 m from the elevation, 1.61 × 3.35 m from its own detail plate — 11% on width.

Rule of thumb from this: horizontal extents and total heights reproduce to under 1%; **any un-printed width in this file could be 10% wrong and any storey height 0.2–0.4 m wrong.** Derived quantities (comble share, taper, cornice band depth) are differences of two uncertain datums and carry the sum of both errors — which is exactly why they are the ones marked INSUFFICIENT below.

**Storey labels are interpretations.** The same physical band was called a low 1er étage by one reader and an entresol by another, on the same plate.

### Numbers I would NOT calibrate on

- **Comble share** — non-monotonic, 2.4× within-class spread, bimodal by roof type.
- **Cornice band depth** — zero Première observations; half the Deuxième values source-flagged uncertain; Troisième inverts the ladder.
- **Opening aspect at upper storeys** — non-monotonic; within-building variation exceeds between-class variation.
- **1er étage ÷ ground storey ratio** — inverts across the ladder.
- **Balcony height above pavement** in Première (n=2, different storeys) or Troisième (n=1).
- **The 7.30 m porte cochère at Avenue de l'Impératrice** — a two-storey arch, not a door.
- **Any Troisième value as a distribution** — use the two buildings for *ordering* only.
- **Bay pitch as a class discriminator** — it is flat; and 9 rue du Conservatoire (2.09 m) is flagged unrepresentative by its own source.
- **Storey heights at 3 rue de la Paix, 119 Champs-Élysées, Avenue de l'Impératrice** — these are inferences, not measurements, and should not be averaged with printed values as if they were peers.

---

## 6. Recommendations

### SOURCED — calibrate on this

| Quantity | Basis |
|---|---|
| Door width **by door type** (2.58 m carriage / 1.75 m pedestrian) | n=7 and n=8, two printed values, invariant across two classes |
| Window opening width (1.20 m, 1.04–1.30) | n=16, all three classes, one printed callout plus one reading on a printed-scale plate |
| Ground storey height as **class-independent** (3.95 m, 3.42–4.85) | n=16, ladder is only 9% with total range overlap |
| Presence of a compressed level below the nobile | 14 of 16, absent in both Troisième |
| Deuxième Classe entresol ÷ ground ratio (0.775, 0.585–0.871) | n=9 |
| Deuxième Classe storey-height **distribution** | n=10 buildings / 25 upper storeys, several cross-checked against the 20 m limit |
| **Ordering** of piano nobile height and nobile window height across classes | ×1.39 and ×1.40, far larger than the 0.2–0.4 m error bar |
| Floor structure thickness 0.30 m | two printed sources |
| Balcony projection ≈ 0.60 m | two printed sources, two buildings, 2% apart |
| Cornice height ceiling at 20 m for Première/Deuxième | 6 of 16 buildings within 1 m of it; legal corroboration |

### WEAK — use for ordering only, never as a value

Storey taper ratio (Première n=3, Troisième n=1) · façade width ladder · door **height** · garde-corps height (n=4) · all Première storey-height *values* · all Troisième values · the Deuxième→Troisième step in nobile opening aspect · Troisième pedestrian door width 1.36 m (n=2, but the 0.25 m gap below Deuxième is consistent) · presence of projecting balconies as a class marker.

### INSUFFICIENT — leave inferred

Comble share · cornice band depth · opening aspect at upper storeys · entresol opening aspect · balcony height above pavement outside Deuxième · bay pitch as a function of class · Première Classe storey taper.

---

*The failure mode this document is written against is over-fitting to sixteen exemplary buildings from one year on one boulevard. Where a quantity is marked SOURCED it is because it survives that objection; where it is marked WEAK or INSUFFICIENT the objection stands.*
