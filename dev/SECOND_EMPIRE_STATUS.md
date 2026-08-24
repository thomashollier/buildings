# Second Empire status

**Scope of this document.** The operator's instruction was to get canonical
Second Empire (1853–1870) solidly right before branching out to any other
period or typology. This is the record of what "solidly right" means today:
what is sourced against César Daly's 1864 plates, what is still the
generator's own inference, what the golden master now pins so none of it can
drift silently, and the honest limits of the evidence behind all of it.

Companion documents: `dev/reference/daly_measurements.json` (machine-readable
measurements), `dev/logs/DALY_MEASUREMENTS.md` (the full reconciled write-up),
`dev/reference/SOURCES.md` (the source register), `dev/CONTRACTS.md`
Amendments 8–9 (the defects this closed and the calibration that produced
these numbers).

---

## 1. What is SOURCED

Eleven quantities were promoted from INFERRED to SOURCED by the Daly
measurement pass (Amendment 9.4), each carrying a citation naming the plate
and whether the figure was read from a **printed** dimension (reliable) or a
**scale bar** (±10 %, established by measuring 26 rue Bergère twice
independently). All are now asserted — value or ordering, as appropriate — in
`tests/golden/test_second_empire_proportions.py`, in addition to wherever
they were already asserted in `tests/unit/`.

| # | Quantity | Value | Basis | Where |
|---|---|---|---|---|
| 1 | Carriage door clear width | **2.60 m** | printed '2.600', 119 avenue des Champs-Élysées; medians 2.567 m (n=4 Première) / 2.575 m (n=3 Deuxième) agree to 0.4 % | `catalogue.door_carriage_entrance` |
| 2 | Pedestrian door clear width | **1.75 m** | median of 8 Deuxième doors, 2 printed | `catalogue.door_pedestrian` |
| 3 | Window opening width | **1.04–1.30 m, ABSOLUTE** | 16 buildings, all 3 classes, non-monotonic by class; 1.300 printed at 2-4 blvd de Sébastopol | `catalogue.opening_window` |
| 4 | Rez-de-chaussée height, class-independent | **3.95 m** | 16 buildings, median 3.95, range 3.42–4.85, class medians fall only 9 % end to end | `structure._TRADE_GROUND_HEIGHT` |
| 5 | Presence of a compressed level | **14 of 16** (4/4 Première, 10/10 Deuxième, 0/2 Troisième) | presence is the class marker, not the height | `structure._ENTRESOL_STOREYS_REQUIRED` (ordering), `roles._find_mezzanine` |
| 6 | Piano nobile height, **ordering** | strictly increasing MODEST→GRAND | Daly 2.923/2.236/2.085 m, ×1.39 Première→Troisième (value INFERRED) | `structure._typical_storey_band` |
| 7 | Nobile window height, **ordering** | strictly increasing MODEST→GRAND | Daly 2.92/2.24/2.09 m at the nobile, ×1.40 (value INFERRED) | `catalogue.opening_height_at_the_nobile` |
| 8 | Deuxième storey-height distribution | 2.32–3.83 m, not a constant | 10 buildings / 25 upper storeys, cross-checked against the 20 m ceiling | corroborates `_typical_storey_band`'s spread; not itself pinned to one figure |
| 9 | Deuxième entresol/ground ratio | **0.775** (range 0.585–0.871) | 9 Deuxième entresols | `structure._ENTRESOL_OVER_GROUND` |
| 10 | Floor structure over an opening | **0.30 m** | printed twice, two classes (125 av. Champs-Élysées; 9 rue du Conservatoire) | `catalogue.lintel_bearing_depth` |
| 11a | Balcony projection | **0.60 m** | printed twice: 0.600 (88 rue de Rivoli), 0.590 (120 blvd de Sébastopol), 2 % apart | `qualify.klass._BALCONY_PROJECTION` |
| 11b | Cornice height ceiling at 20 m | Première/Deuxième **flat** (19.11 / 18.90 m), both pinned near the 1859 decree's 20 m limit | 6 of 16 buildings sit 19.0–20.0 m | `structure._FACADE_AMBITION` (COMFORTABLE 0.96, GRAND 0.99) |

Two additional constants, used internally rather than exposed as top-level
catalogue figures, are also SOURCED and tested:

- `structure._COMPRESSED_UNDER_THE_FLOOR_IT_SERVES = 1.275` — the ratio of
  the noble floor to the compressed level beneath it (1.25× Première, 1.30×
  Deuxième).

**The two findings worth calling out as structure, not scalars** (both
directly asserted in `TestTheTwoStructuralFindings`):

1. **The window splits.** Width is ABSOLUTE and flat across class (1.04–1.30 m,
   non-monotonic); height at the nobile is PROPORTIONAL and rises with class
   (×1.40, Première→Troisième). Same aperture, opposite kind of number — the
   cleanest demonstration this project has of its own central rule, taken
   from a period source rather than asserted a priori.
2. **The compressed level is a class-dependent *presence*, not a
   class-dependent *height*.** Whether the building has one is the class
   signal (4/4, 10/10, 0/2); its height, where present, is a fraction of the
   ground storey (0.775) and does not itself carry a class ladder.

---

## 2. What is WEAK (ordering asserted, value never pinned)

Thin samples (Première storey taper n=3, Troisième n=1; every Troisième
figure; door height; garde-corps height; façade-width ladder). Asserted in
`TestWeakOrderingOnly` and scattered unit tests as directional facts only:

- Storey taper rate is `< 1.0` (a typical storey is shorter than the one
  below it) — never a specific ratio.
- The storey-height margin above a plain storey rises with class (the
  mechanism behind "piano nobile height rises with class") — asserted on the
  band itself (`structure._typical_storey_band`), not on the emergent
  per-building "principal" storey's realized height, which is also affected
  by each site's own storey count and taper and is not itself a clean,
  site-independent class signal (see the note in
  `test_the_storey_margin_above_a_plain_storey_rises_with_class`'s
  docstring).
- Window height's population-wide extremes (GRAND's mean clears MODEST's,
  matching Daly's own top-to-bottom spread) — the middle two classes are
  **not** asserted to sit strictly between them in every aggregate, because
  the realized value is confounded by rank and by each class's own storey
  count, neither of which the source constrains.

---

## 3. What is INSUFFICIENT (left INFERRED, deliberately untouched)

The measurement pass named these explicitly as unfit to calibrate on, and
A9.4 left them alone rather than promote a thin reading to SOURCED:

- Comble share of total height (bimodal by roof type, 2.4× within-class
  spread — a discrete type choice, not a proportion)
- Cornice band depth (zero Première observations; Troisième inverts the
  ladder)
- Opening aspect at upper storeys (non-monotonic; within-building variation
  exceeds between-class variation)
- Entresol opening aspect
- Balcony height above pavement outside Deuxième Classe (Première n=2 at two
  different storeys; Troisième n=1)
- Bay pitch as a function of class (flat in the corpus; corpus-wide median
  2.80 m is corroborated but not sourced — see `structure._BAY_PITCH_PREFERRED`)

A number promoted to SOURCED from one of these would be worse than leaving it
inferred, because the INFERRED marker is what tells the next stage which
figures are still open. None of this document's tests touch them.

---

## 4. What the golden master covers

`tests/golden/test_second_empire_canonical.py` pins four named situations
(`tests/golden/situations.py`) end to end through `generate()`, each
serialised to `tests/golden/data/*.json`:

| Situation | Street | Class | Ground | Corner |
|---|---:|---|---|---|
| `midblock_ordinary_20m_boulevard` | 20 m | ORDINARY | residential | no |
| `grand_30m_avenue` | 30 m | GRAND | residential | no — wide enough to clear the 20 m decree step |
| `modest_12m_street_shop` | 12 m | MODEST | shop | no — at the carriage-entrance threshold, doubly a pedestrian-door case |
| `corner_comfortable_18m_shop` | 18 m | COMFORTABLE | shop | yes |

A failure reports the first node id, kind, prop and trace field that changed
— never "bytes differ" — via a parallel tree walk
(`test_second_empire_canonical._diff`). Regenerating a fixture is a
deliberate, visible act, not a silent overwrite: either

```
UPDATE_SECOND_EMPIRE_GOLDENS=1 python -m pytest tests/golden/test_second_empire_canonical.py
```

or

```
python dev/harness/regenerate_second_empire_goldens.py [situation_name ...]
```

Both rewrite the affected `tests/golden/data/*.json` file(s) from the current
generator output, print exactly what was written, and (the pytest route)
fail on purpose so the write cannot be mistaken for a passing test. Diff the
rewritten file before treating the new output as correct.

`tests/golden/test_second_empire_proportions.py` is the complementary sweep:
~560 Second Empire situations (1853/1859/1865/1870 × 7 street widths × every
class × every ground programme × both corner states), asserting the eleven
SOURCED quantities (value, with the correct printed/scale-bar tolerance), the
WEAK quantities (ordering only), and the two structural findings above —
against both the catalogue/structure functions directly and the real
generated IR.

---

## 5. What a future period port must not break

These are the properties this typology now depends on being true, stated so
that porting the generator to a different period (or a different city) has a
checklist rather than a vague sense that "it used to work":

1. **ABSOLUTE/PROPORTIONAL/REGULATORY stays a three-way split with one
   scaling site.** `scale_for_class` is the only place proportional scaling
   happens (`quantity.py`); a door or a window's width may never pass through
   it in a way that changes the number.
2. **A door's width is entitlement, not size.** Whether a building gets a
   carriage entrance varies by class and street width
   (`catalogue._CARRIAGE_CLASSES`, `_CARRIAGE_STREET_MINIMUM`); its width,
   once granted, does not.
3. **Bay pitch is structural, not ambition.** `_BAY_PITCH_MIN` / `_BAY_PITCH_MAX`
   are ABSOLUTE and class-independent; a grand building must not get FEWER
   window axes than a modest one on the same frontage (A8.6/D6).
4. **The entrance slot fits inside the bay band.** 2.60 + 2×0.40 m jamb =
   3.40 m = `_BAY_PITCH_MAX` exactly, asserted in `solve_structure` — this
   must keep holding arithmetically, not just numerically, if either figure
   ever moves.
5. **Window width is ABSOLUTE and class-flat; window height is PROPORTIONAL
   and rises with class.** The single clearest period-sourced demonstration
   of the whole absolute/proportional split. A future typology that gives a
   window a class-scaled width would be repeating the defect this amendment
   fixed.
6. **The comble is a section (brisis + terrasson), sized by the room behind
   it, not a fraction of whatever facade height the class declined to
   spend.** `total_height` must keep rising with class while every class
   still sits short of its legal ceiling (A8.5's substantive finding,
   retracted only on the ordering of comble *share*, A9.1).
7. **"Has a principal floor" is itself allowed to be false.** A class/section
   combination whose étages are all one height (Troisième-shaped) has no
   PRINCIPAL role and ranks from the first letting floor instead — a future
   port must not reintroduce a forced tie-break that manufactures a noble
   floor where the building built none.
8. **The regulatory ceiling is visible in the data, and the model must keep
   reproducing that.** COMFORTABLE and GRAND land within a metre of each
   other and within Daly's own 19.0–20.0 m band on a >20 m street, because
   both are pinned near the 1859 decree's limit — not because of a
   coincidence in `_FACADE_AMBITION`'s numbers.
9. **Every building has exactly one entrance**, ABSOLUTE in width and
   height, placed by a positional rule (A6.1) — this must survive any
   period's ground-programme vocabulary changing.

---

## 6. Honest limits

Carried over verbatim in substance from `dev/logs/DALY_MEASUREMENTS.md §5`,
because a status document that hides its own evidence's limits is worse than
one with no evidence at all:

- **Sample size: n = 4 Première / 10 Deuxième / 2 Troisième buildings.** Not
  6/11/2 plates — several plates are elevation+section pairs of the same
  building. Seventeen buildings total, sixteen with measured storeys.
- **Première is thinner than n=4 suggests.** Only one of the four (125
  avenue des Champs-Élysées) carries a printed storey ladder; the other
  three are flagged uncertain, self-contradictory, or deliberately withheld
  by the measurer. Première storey-height medians rest on one solid building
  plus three inferences.
- **Troisième has no printed dimension anywhere.** Both plates are scale-bar
  only, with no independent check. Every Troisième figure should be read as
  "two buildings did this," never as a distribution.
- **Publication bias.** These are plates a luxury architectural journal chose
  to publish as exemplars, with named architects credited — biased toward
  the grander, better-designed, better-built end of each class. Nothing here
  describes the median Paris building of 1864.
- **One date.** Every plate is 1864. No evidence about drift across
  1850–1914 (this typology's own claimed range extends further via
  `chronology`'s variant windows, which this document does not touch). The
  20 m cornice ceiling that flattens Première/Deuxième is the 1859 decree
  specifically; it moves under 1884 and 1902.
- **Geographic concentration.** Seven of seventeen buildings are on the
  boulevard de Sébastopol or the rue de Rivoli — one Haussmann corridor,
  largely one group of architects. Treat that group as a cluster, not as
  seven independent samples.
- **Scale-bar reading carries real error; printed callouts do not.** 26 rue
  Bergère measured twice independently: façade width and bay pitch reproduce
  to under 0.5 %, but individual storey heights differ by up to 9 %, comble
  height by 19 %, and one scale-bar door-width reading (2.99 m) sat 15 %
  above its own plate's printed 2.600 m. Every SOURCED figure above that is
  marked scale-bar carries this ±10 % the same way a regulatory citation
  carries a decree number — treat it as a range, not a point.

---

## 7. Out of scope: one pre-existing, unrelated test failure

The full suite (1367 passed / 1 failed, guards clean) has exactly one
failure, `test_no_nan_negative_or_zero_dimension`, on a repro at
`year=1820` — before the Second Empire even begins, and before the 1859
règlement this document's work depends on. It is a zero-width placeholder
dormer (`no_dormer0`) on an extremely narrow (6 m street, 5 m parcel), corner,
Royal-era situation. Not touched by, and not a regression from, this work;
tracked as a pre-existing defect for whichever future stage takes on the
Royal era rather than fixed here, per the instruction to lock Second Empire
solidly before branching out to anything else.
