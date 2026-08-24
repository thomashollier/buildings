# Validation report

Assembled from four independent checks (fuzz, reference oracle, contact sheets,
VLM reference comparison) plus a fifth pass run while writing this: every claim
below that carries a number was re-derived here against the live code, not
copied from an agent's summary. Where an agent's finding did not survive that
re-derivation it is corrected by name.

**Inputs**

| Check | Report |
|---|---|
| Invariant fuzz | `dev/logs/fuzz_report.md` |
| Reference oracle | `dev/logs/oracle_report.md` |
| Contact sheets | `dev/logs/sheets/index.html` |
| VLM reference | `dev/logs/vlm_report.md` |

---

## 0. Gates, actually run

```
$ python3 -m pytest tests/ -q
1331 passed in 150.74s (0:02:30)

$ python3 dev/harness/check_no_period_branching.py
check_no_period_branching: clean          (exit 0)

$ python3 dev/harness/check_renderer_dumb.py
check_renderer_dumb: clean                (exit 0)
```

Plus, from the four reports: fuzz **3000/3000 cases clean**, oracle **495/495
regulatory rows exact** and **29/320 proportion rows outside tolerance**,
contact sheets **0 failed cells** across all five sheets, VLM **14 ranked
findings** over 64 selected + 67 augmented reference images.

Every gate in the project is green. **The project is not in good shape.** Read
§2 before believing §0 — the gates are green because nothing they assert is
what is wrong.

---

## 1. The success criteria, graded

### 1. Someone who knows Paris doesn't flinch at a generated street — **FAIL**

Not a marginal fail. Four things a Parisian would notice inside five seconds:

- **Half of all buildings have no visible front door.** `draw_opening` branches
  on `opening_type == "carriage_entrance"` and has no branch for
  `"pedestrian_entrance"`, so the porte piétonne falls through to the generic
  window path — same glass fill, same mullion, same frame. Across an 80-situation
  sweep the split is exactly 40 carriage / 40 pedestrian: the commoner Paris
  entrance is invisible on every one of them.
- **No pre-1884 roof is a mansard.** Every comble from 1820 to 1883 draws as one
  unbroken plane, no brisis/terrasson break, with the dormers in its bottom
  fifth and bare zinc above. That is the entire Second Empire.
- **Every corner building is a triangular gable or a pyramid**, with no ridge,
  and a chimney floating detached above it.
- **A modest building wears a hat 37 % of its own height** while a grand one gets
  16 % — with five dormers against the grand building's two.

The VLM check's own summary of the 39 whole-elevation pairs: "one composition
repeated 39 times with the roof cap as almost the only variable." That is the
grade.

The one qualification: this is a **rendering and calibration** failure, not a
structural one. The IR under it is mostly right (see criteria 2 and 4). Nine of
the twelve confirmed defects in §2 are fixable without touching the phase model.

### 2. One input changes the output the way a specialist would predict, including the discontinuities — **PASS**

This is the strongest result in the project and it is worth stating plainly,
because it is the thing the brief said was most likely to be wrong.

**The step table, swept live** (comfortable, 16 m parcel, 1865):

| street width | total height | storeys |
|---:|---:|---:|
| 6–7 m | 14.868 | 4 |
| 8–9 m | 17.788 | 5 |
| 10–20 m | 20.718 | 6 |
| 22–40 m | 23.168 | 7 |

Steps, not a ramp, and the plateaus land on the 1859 décret's own hinges
(7.8 / 9.75 / 20 m). Height does not move at all between 10 m and 20 m of street,
which is correct and is exactly the behaviour a slider-based generator gets
wrong.

**The date hinges, swept live** (same site, comfortable):

| year | total height | roof envelope |
|---:|---:|---|
| 1858 | 20.520 | diagonal_45 |
| **1859** | **20.718** | diagonal_45 |
| 1883 | 20.718 | diagonal_45 |
| **1884** | **24.390** | **circular_arc** |
| 1901 | 24.390 | circular_arc |
| **1902** | **28.909** | **eighth_arc** |

Three legal discontinuities, on the right years, and at 1884 the roof changes
*kind*, not just size.

**And the other chronology moves differently**, which is the actual design claim.
Ironwork pattern by year, all four classes, fixed seed:

```
1820-1840  lozenge_palmette only
1850       lozenge_palmette 54 / haussmannian_scrollwork 14   <- turning over
1860       lozenge_palmette 38 / haussmannian_scrollwork 30
1870-1880  haussmannian_scrollwork only
1890       haussmannian_scrollwork 39 / renaissance_revival 30 <- turning over
1900-1910  renaissance_revival / whiplash_art_nouveau mixed
```

Gradual, class-lagged (the mix within one year is different classes adopting at
different times), and on entirely different years from the roof. Legality is a
step; fashion is a distribution; they have not collapsed into each other. The
oracle independently confirms the legal half: **495/495 regulatory rows —
era, facade height limit, arc radius, envelope shape, legal total height — agree
exactly (1e-6) with the reference implementation across 11 years × 11 widths.**

**The caveat that keeps this from being a clean win:** the gradual half is
demonstrated *in the IR only*. A viewer cannot see it, because every dated
difference the renderer draws has an amplitude of a few centimetres (a keystone
that grows from 0.12 m to 0.28 m wide) while the one dated difference with real
amplitude — the roof envelope — is the only thing legible at facade scale. The
model works; the drawing does not carry it. See D8.

### 3. A whole block generates fast enough to iterate on, and reads as one wall — **PASS on speed, PARTIAL on the wall**

**Speed is not a concern**, measured here:

| | time |
|---|---:|
| one building (mean of 50) | 7.6 ms |
| 72 m block, 6 parcels, plan + solve | 68 ms |
| 110 m block, 9 parcels, plan + solve + SVG | **110 ms end to end** |
| 220 m block, 18 parcels, plan + solve | 202 ms |

Linear in parcels, and a whole block round-trips faster than a keystroke.

**"One wall" holds exactly in the IR and breaks in the drawing.** In a 72 m
six-parcel block with both corners chamfered, every parcel states eaves
`14.9175`, comble `5.8005` and total `20.718` — bit-identical, no tolerance
needed — and the block emits its own full-length `cornice`, `string_course` and
continuous `balcony` nodes at `w = 72.0`. The datum machinery does what it was
built to do.

What the viewer sees instead is a stepped roofline, and it is **not** a datum
failure: it is D2 below. The two chamfered end parcels are `ends="hipped"`, and
the hip truncates their drawn apex to `full_h × half / 9.0`, so they render lower
than their identical neighbours. One renderer bug, three symptoms. Fix D2 and the
wall reads.

### 4. Any element can be traced back to the rule that produced it — **PASS in the IR, FAIL at the drawing**

**IR: 6329 of 6329 nodes** across 48 situations (4 classes × 4 eras × 3 street
widths) carry a non-empty trace, and `trace.explain(node.id)` returns a non-empty
explanation for **every one**. Zero exceptions, zero empties. The refusal path is
traced too — a 4 m parcel returns not "infeasible" but:

> a parcel 4.00 m wide cannot carry a 3.80 m porte_cochere (INFERRED — typical
> porte cochère clear width + INFERRED — the jamb carrying the arch over a
> carriage opening…): every building has an entrance, the entrance is absolute,
> and the two piers beside it are already at their minimum 0.27 m, so the
> frontage needs at least 4.34 m

That is the invariant paying for itself.

**The drawing is a different story, and `check_renderer_dumb` does not catch
it.** The guard passes while the renderer invents three quantities no node
states:

- `_hip_arris` invents how far a hip runs along the frontage (D2).
- `draw_cornice` hard-codes `overhang = 0.10` while the node states a
  `projection` of 0.71–1.18 m (D8).
- The drawn roof apex is `full_h × half / full_run`, which **contradicts** the
  chimney's stated `base_height` — the IR says the stack stands at 20.718 and the
  drawing puts the roof under it at 14.38. Two numbers for one thing, and the
  building's own `props["h"]` is the wrong one.

So the invariant is "every element names its rule", and it holds for every
element that is a node. The renderer draws things that are not nodes, and those
are untraceable by construction. **The guard's scope is the finding here**: it
checks that the renderer does not *branch* on generic keys, and does not check
that the renderer does not *invent geometry*. Those are different offences and
only the first is guarded.

### 5. Swapping the rule set gives a different city without touching the machinery — **OUT OF SCOPE; the seams are in the right place for two of three layers**

Not attempted, correctly. Reporting on seam placement only.

**Clean — zero typology references:** `solver/fitting.py`, `ir/nodes.py`,
`ir/serial.py`, `quantity.py`, `trace.py`, `rng.py`, `site.py`. The fitting
solver, the node vocabulary, the quantity kinds and the RNG would carry a second
typology untouched. That is the hard half and it is done.

**Not clean — `src/buildings/block/block.py`** imports Paris directly, five
times:

```python
from buildings.typologies.paris import catalogue
from buildings.typologies.paris.compose import Layer
from buildings.typologies.paris.generate import generate, walk
from buildings.typologies.paris.reglement_adapter import (...)
```

The README presents the block as general machinery ("the block is the unit, not
the building"). It is not: frontage subdivision, chamfer sizing, datum
resolution and programme choice all call into Paris by name. A second typology
requires editing `block.py`, which is precisely what criterion 5 says must not
happen. The seam wants an interface — "give me a typology that can answer
`datums_for(street_width, year, klass, regime)` and `generate(site)`" — and the
two call sites are already shaped like one.

**Not clean — `render/svg/`.** `elements.py:516` branches on the literal
`"haussmannian_scrollwork"`, and `draw_roof_mass`, `draw_cornice`,
`draw_shopfront` and `draw_opening` encode a Paris vocabulary (brisis, terrasson,
devanture, souche, porte cochère) in their structure, not just their names. This
is defensible — a renderer for one drawing convention is allowed to know that
convention — but it should be stated as a decision rather than discovered later.

---

## 2. Confirmed defects, by severity

Every one reproduced here. Unless stated otherwise the site is
`SiteContext(street_width=W, parcel_width=PW, parcel_depth=18.0, year=Y,
klass=K, ground=G, seed=S)`.

### D1 — Half of all buildings have no visible door · **renderer** · CRITICAL

`render/svg/elements.py:193` — `if opening_kind == "carriage_entrance":` is the
only entrance branch. `pedestrian_entrance` falls through to the generic window
path.

The IR is not at fault. `catalogue.entrance_for` places exactly one door on
every building and states it correctly:

```
{'opening_type': 'pedestrian_entrance', 'w': 1.4, 'h': 2.9, 'head': 'flat',
 'sill_height': 0.0, 'geometry_stated': True}
```

The renderer discards it. Across a sweep of 4 classes × 4 street widths × 5
programmes: **40 carriage entrances, 40 pedestrian entrances** — so this is
exactly half the population, and it is the half comprising every modest and
ordinary building and every building on a street under 12 m.

**Repro:** `W=8, PW=13, Y=1875, K=MODEST, G=RESIDENTIAL, S=1` → render the
ground storey; the 1.40 × 2.90 m door is pixel-identical to the window beside it.
**Also visible on:** the block sheet (`dev/logs/sheets/block_wall.svg`) — nine
ordinary parcels, one continuous run of glass, not one door along 110 m of wall.

### D2 — The hip run is keyed to the parcel depth, not the frontage · **renderer** · CRITICAL

`elements._hip_arris` runs the hip in by `min(facade_w/2, section_run)`, where
`section_run` is the last x of the silhouette profile — which is a section on a
plane *perpendicular to the street*, calibrated against `parcel_depth`. Measured
live: that value is **9.0 for every frontage from 8 m to 26 m**.

So any frontage under 18 m has `facade_w/2 < 9.0`, both hips meet at
mid-frontage, and the roof has **no ridge at all** — a triangular gable, or a
pyramid on a wide parcel. That is essentially every parcel in Paris.

This single bug produces three of the VLM's fourteen findings:

- **F2** the barn/pyramid roof;
- **F3** the floating chimney — `terminate` places the souche at the *stated*
  ridge (`base_height = 20.718`) while the drawing truncates the apex to
  `eaves + 5.80 × 4/9 = 17.5`, so the stack hangs 3.5 m in clear air;
- **F12** the block's stepped roofline — the IR ridge across a 72 m block is
  *dead level* (all six parcels state 20.718); only the two hipped corner
  parcels draw lower.

**Repro:** `W=20, PW=8, Y=1865, K=COMFORTABLE, G=RESIDENTIAL, S=7, corner=True`
→ `facade_w=8`, silhouette last point `(9.0, 20.718)`, `half=4.0`, apex drawn at
44 % of stated height.

### D3 — No Second Empire building has a mansard break · **rule + renderer** · HIGH

`draw_roof_mass` draws the brisis/terrasson break only when
`abs(lower_angle_deg - upper_angle_deg) > 1.0 and break_pct < 0.995`. What the
roof node actually states, measured:

| year | lower° | upper° | break_pct | break drawn |
|---:|---:|---:|---:|---|
| 1860 | 45.0 | 45.0 | 1.00 | **no** |
| 1870 | 45.0 | 45.0 | 1.00 | **no** |
| 1880 | 45.0 | 45.0 | 1.00 | **no** |
| 1884 | 66.97 | 21.97 | 0.72 | yes |
| 1902 | 67.50 | 45.00 | 0.445 | yes |

The renderer is obeying the IR faithfully — the defect is upstream, in what a
pre-1884 comble *states about itself*. A 45° diagonal envelope is a legal
maximum, not a roof section; the building inside it still had a brisis and a
terrasson. Fixing this in `draw_roof_mass` would be the wrong place.

Compounding it: the dormers sit in the lowest fifth of that unbroken plane with
bare zinc above, where a real lucarne occupies the whole brisis.

**Repro:** any `Y < 1884`.

### D4 — Upper-storey windows violate the catalogue's own declared aspect band · **rule** · HIGH

`catalogue.opening_aspect_band()` states the Paris band as **(1.70, 2.00)**.
Sweep of 4 classes × 5 street widths × 3 parcel widths × 3 years, mezzanines and
oculi excluded, aspect = h/w:

| class | role | n | median | min | % below 1.70 |
|---|---|---:|---:|---:|---:|
| grand | principal | 156 | 1.65 | 1.60 | 73 % |
| grand | **upper** | 472 | **1.33** | **1.00** | **94 %** |
| comfortable | upper | 551 | 1.39 | 1.06 | **94 %** |
| ordinary | upper | 612 | 1.52 | 1.18 | 74 % |
| modest | upper | 544 | 1.78 | 1.13 | 41 % |

A minimum of **1.00 is a square window**. This is worse than the VLM reported,
and it is worse for the *grander* classes. It is a stated-contract violation with
no assertion behind it — the reason "the wall has holes in it instead of
windows."

**Repro:** `W=30, PW=22, Y=1870, K=GRAND, G=RESIDENTIAL, S=7` → read the aspect
of any `upper` storey opening.

### D5 — The comble's share of the building is inversely proportional to class · **rule** · HIGH

Same site (`W=20, PW=16, Y=1865`), varying only class:

| class | total | comble | comble share | dormers |
|---|---:|---:|---:|---:|
| modest | 20.72 | **7.73** | **37 %** | **5** |
| ordinary | 20.72 | 5.80 | 28 % | 4 |
| comfortable | 20.72 | 4.40 | 21 % | 3 |
| grand | 20.72 | **3.34** | **16 %** | **2** |

`total_height == legal_total_height` in all four cases. So the facade allowance a
modest builder declines to use is silently converted into roof: the poorer the
building, the bigger its hat, and the more dormers on it. Backwards twice.

Traced to `structure._COMBLE_FILL = 0.99`, deliberately class-invariant, against
`structure._FACADE_AMBITION` which is not. **The oracle found the same constant
independently** — 22 of its 29 proportion outliers are `total_height_m`, all
`new > old`, across every class, growing with street width and era. Two harnesses
built for different purposes converging on one constant is the strongest signal
in this report.

### D6 — Grand buildings get fewer windows than modest ones on the same frontage · **rule** · HIGH

Class scaling is applied to the **bay pitch**. Same 16 m frontage, 1870:

| class | bay pitch (max) | bays per storey |
|---|---:|---:|
| modest | 2.55 m | **8** |
| ordinary | 3.12 m | 7 |
| comfortable | 3.80 m | 6 |
| grand | **4.05 m** | **6** |

Real Paris moves the other way: money buys taller and richer openings, not a
sparser wall, and bay pitch is bounded by what the structure will span (roughly
2.7–3.4 m) at every class. This is why the grand facades read too blank for their
pretension.

**Repro:** `W=20, PW=16, Y=1870, G=RESIDENTIAL, S=7`, sweep `K`.

### D7 — The attic storey is an empty box · **rule** · MEDIUM

Every generated building carries an `attic` storey of 3.34–3.69 m, inside the
comble, with **zero children** in every case sampled — no bays, no openings,
nothing. The comble floor is never lit from its own storey; the only openings in
the roof are the free-standing `dormer` siblings, which are too few and not
aligned to the bays below. The dormers' own trace says
`dormer.one_per_bay_of_the_storey_it_lights`, which the output contradicts.

The roles phase names the storey and nothing then qualifies it.

**Repro:** any site; walk for `storey` with `role == "attic"` and count children.

### D8 — The cornice states a projection and does not project it · **renderer** · MEDIUM

The IR does the right thing — projection ladders by class:

| class | stated `projection` |
|---|---:|
| modest | 0.71 m |
| ordinary | 0.73 m |
| comfortable | 0.91 m |
| grand | 1.15 m |

`draw_cornice` reads that number and uses it for the band's **height**
(`depth = projection * 0.5`), then draws the overhang — the part that throws the
shadow, the part that makes a Paris cornice legible at 50 m — as a hard-coded
`overhang = 0.10`, identical for every class and every year. The class ladder
that exists in the IR does not reach the drawing as projection.

Second half: `cornice_ornament` is `"plain"` on **855 of 912** sampled buildings
(94 %); modillions appear on 6 %. In the reference corpus the modillioned corona
is the most identity-carrying element of the whole facade.

**Repro:** `elements.py:345`, and sweep `cornice_ornament` over any range of
years and classes.

### D9 — Every chimney is a 0.80 m stub and two of them are clipped to the facade edge · **rule** · MEDIUM

Every `special` node of `element == "chimney_stack"`, at every class, year and
frontage, states `h = 0.80`. The end pair sits at `x = 0.0` and
`x = facade_w − 0.2975` at half width, so they render as small blocks riding the
cornice corners rather than as stacks on a party wall. A Paris roofscape's
souches are tall brick stacks with terracotta pots standing well above the ridge.

**Repro:** `W=20, PW=16, Y=1870, K=MODEST, G=RESIDENTIAL, S=0` → six chimney
nodes, all `h=0.8000000000000007`, first at `x=0.0`, last at `x=15.7025`.

### D10 — One bay is a different opening on every storey, always at one end · **rule** · MEDIUM

The `is_special` bay changes its opening type storey by storey, and is inserted
at one end only, never balanced.

**Repro:** `W=10, PW=9, Y=1870, K=MODEST, G=RESIDENTIAL, S=0` → column 1 of 6
(column 0 is a `pier_end`), bottom to top:

```
base       blind_panel
principal  blind_panel     <- a blind panel on the noble floor
upper      narrow_window
upper      narrow_window
```

A blind panel on the principal storey is a solecism, not a variation. Reproduces
identically at 1840, 1870 and 1895, and at `W=18` — it is not a rare seed.

### D11 — `SHOP` draws two of a devanture's five parts · **renderer** · MEDIUM

Better than the VLM reported, and still short. `draw_shopfront` **does** draw the
soubassement/stallriser and the enseigne fascia, and the IR states
`treatment='devanture'`, `threshold_height=0.4`, `fascia_depth=0.45`. Missing:
the **projecting shop cornice**, the **framing pilasters**, and the **recessed
door**; and the two parts that exist are flush with the masonry, so the whole
thing reads as a stone arcade with glass in it rather than as joinery applied in
front of the wall. The related porte cochère is a flat rectangle with no
archivolt, keystone or imposte.

### D12 — A chamfer's stated height excludes its own comble · **rule** · LOW

In a 72 m block, both `chamfer` nodes state `h = 14.9175` — the eaves — while
carrying a `roof` and a `silhouette` child, and while their neighbouring parcels
state `h = 20.718` for the same building line. Any consumer using
`chamfer.props["h"]` as the extent under-measures the pan coupé by its whole
roof. Same class of disagreement as D2's `props["h"]`.

---

## 3. Open questions — where the design, not the code, looks wrong

The brief predicted the rule model was "the part most likely to be wrong."

**It survived.** The regulatory layer matched an independent prior implementation
on 495/495 rows exactly. The derived-role model produced zero anomalies over
3000 fuzz cases. The two-chronologies split is visible in the data (§1.2), which
is the design's central and least obvious claim. The absolute/proportional/
regulatory quantity split is doing real work — D6 is *visible as a defect* only
because the system is explicit about which kind a bay pitch is. And the balcony
rule is a genuine success worth naming: over 384 sampled buildings the lowest
balcony ranges 6.06–7.70 m with **zero violations** of the 1823 ordinance's 6 m,
and the distribution is idiomatic (balcon filant at the principal storey and
again under the cornice, individual balconies between, nothing on the ground or
entresol). Nobody wrote "floor 2 gets a balcony"; it fell out of a height
predicate. That is the thesis of the project working.

What did **not** survive is the layer of calibration constants sitting on top of
the model, and the renderer. Those are the open questions.

**Q1. Is `_COMBLE_FILL = 0.99`, class-invariant, defensible?** Two harnesses hit
it independently. `total_height == legal_total_height` for every class, so the
brief's own warning — "conflating the legal ceiling with what got built makes
every building a maximal building, which is wrong and looks it" — was answered
for the facade line (`_FACADE_AMBITION` varies by class) and *not* for the roof
line. The roof is what the eye reads first. Either the comble needs its own
ambition dial, or the roof should be bounded by servant-room storeys rather than
by the decree.

**Q2. Is bay pitch the right place to spend class?** The system currently buys a
wider bay with money. If the real constraint is span (2.7–3.4 m at every class,
because that is what a floor joist will do) and the real luxury is opening height
and richness, then D6 is not a bug but a wrong model, and fixing it is a change
to what `class` *means*, not a constant.

**Q3. What is the attic for?** Amendment A2.1 made the attic a reachable storey.
Nothing then qualifies it (D7). Either the roles phase should not emit a storey
nothing will fill, or qualification owes it lucarnes aligned to the bays below —
and if the latter, the free-standing `dormer` siblings are the wrong mechanism
and should be children of that storey.

**Q4. Is class even the right axis for the comble?** D5's inversion may be a
symptom of asking class a question that belongs to programme and parcel depth.

**Q5. How good is the ground truth, really?** `dev/reference/selection.json`
exists (64 images) but its own `generated_by` says it is the review page's
*default* pre-selection on `quality=='good'` — a judgement about **photographs**
(framing, resolution, obstruction), not an operator's judgement about which
**buildings** are specimens. 25 of the 64 are close-up details that cannot be
compared to a whole-facade render at all. And 67 further targeted images
(`se-comble`, `se-cornice`, `se-elevation`, …) postdate the file and are absent
from it — two of the sharpest findings (D3, D8) came from that augmented set.
The ground-truth set is weaker than its file format implies, and the VLM check
should not be re-run against it without an operator pass first.

**Q6. Where does the block/typology seam go?** See §1.5. `block.py`'s five direct
Paris imports are a decision that has not been made yet, only deferred.

---

## 4. What is demonstrated vs asserted

### Demonstrated

- **I1–I5** over 3000 fuzz cases spanning 40 categorical combinations × 75
  situations, with the harness's own negative controls confirming each checker
  catches an injected violation.
- **Regulatory agreement with the reference implementation**: 495/495 rows
  exact at 1e-6.
- **Step behaviour** of height against street width and year, and the *shape*
  change of the roof envelope at 1884 and 1902 (re-derived here, §1.2).
- **Two chronologies moving at different rates** — legal step vs gradual,
  class-lagged fashion turnover (re-derived here, §1.2).
- **Block datum unity in the IR**: exact equality of eaves, comble and total
  height across six parcels; block-scope cornice/string-course/balcony nodes at
  full frontage.
- **Traceability**: 6329/6329 nodes carry a trace and explain.
- **Performance**: 110 ms for a 110 m block, end to end including SVG.
- **The refusal path**: reachable, and its message names the rule and the
  inferred constants that made the fit impossible.
- **The balcony rule** (§3): 384 buildings, 0 violations of the 6 m ordinance.
- **Contact sheets**: 0 failed cells of 69 across five sheets; the red-error-tile
  path verified by injection.

### Asserted, not demonstrated

- **That any dimension is correct.** The oracle checks agreement with an *earlier
  implementation of the same idea*, not with Paris. Both can be wrong the same
  way, and on the two constants that matter (`_COMBLE_FILL`, `_FACADE_AMBITION`)
  the oracle report says in terms that both sides are uncalibrated placeholders
  pointing in opposite directions. Neither is evidence.
- **That the fuzzer's 3000/3000 means anything about quality.** It does not, and
  the fuzz report says so itself. Two specifics that sharpen the point:
  - The sample's parcel-width floor is **5.0 m** and the infeasibility threshold
    is **4.34 m**, so the 3000 cases were drawn inside the feasible region by
    construction — 0 refusals is a property of the sample, not the code.
  - The checker set is I1–I5 + envelope containment + storey minimum + exact bay
    fill + NaN/negative/zero. **Every one of D1–D12 is invisible to all of
    them.** A building with no door, no ridge, a square window and a floating
    chimney passes the entire fuzz suite.
- **That `check_renderer_dumb` bounds the renderer.** It passes while the
  renderer invents a hip run, an overhang, and an apex that contradicts a stated
  node height. It guards against *branching on generic keys*, not against
  *inventing geometry* — a distinction worth writing into the guard.
- **That the two-chronologies model reaches a viewer.** Demonstrated in the IR
  only; contradicted at facade scale (§1.2 caveat, D8).
- **That the 29 proportion outliers are benign.** The oracle asserts they are
  placeholder constants behaving as documented. That they are the *right*
  constants is demonstrated nowhere, and D5 is the same constant seen from the
  other side.
- **Everything the VLM check lists under "what looked right."** By its own
  statement: "looks wrong" is strong evidence, "looks right" is weak, and a
  systematic three percent is invisible at that resolution by construction.
- **Corner buildings as such.** `generate()` alone cannot produce one — `corner=
  True` changes nothing in the tree except that the comble is hipped; the pan
  coupé lives in `block.solve_block`. All eight corner reference pairs were
  therefore compared against a mid-block elevation and can be judged on nothing
  but the roof.
- **Ornament quality.** 25 of the 64 selected references are close-ups of
  mascarons, ironwork and sculpture; the generated output has no resolution at
  which they can be compared.

---

## 5. The short version

The rule model — the part the brief called most likely to be wrong — is the part
that works. Steps are steps, decrees land on the right years, fashion and law
move independently, roles are derived rather than declared, the balcony falls out
of a height predicate, and every node names the rule that made it. That is the
hard, unobvious half and it is demonstrably sound.

What is broken is everything between the model and the eye: a renderer that
draws no door on half the buildings, no ridge on any corner, no break in any
Second Empire mansard, and no projection on any cornice; and four calibration
constants that give the poorest building the biggest roof and the richest
building the emptiest wall.

Twelve confirmed defects. Nine are fixable without touching the phase model.
None of the twelve is caught by any gate in the repo, and all four gates are
green.
