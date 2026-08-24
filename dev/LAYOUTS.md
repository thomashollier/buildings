# Preset layouts — a proposal

A *layout* is a **situation**, not a building: the handful of facts the generator
needs, from which everything else follows. No preset chooses a storey count, a
roof angle or an ornament level.

Two rules for what earns a place here:

1. **Each preset stresses something different.** The brief's own validation-set
   logic — a set where every entry tests an assumption the others leave intact.
2. **Anchored to a real building wherever possible.** Where a Daly plate shows
   the case, it is named, so the preset is answerable to something.

What the 16 Daly buildings actually span, for calibration:

| axis | range |
|---|---|
| étages | 4 (×11), 3 (×4), 2 (×1) |
| entresol | 9 with, 7 without |
| entrance | 7 cochère, 9 piétonne; 3 two-storey |
| cornice | 14.78 – 21.05 m |
| frontage | 8.57 – 19.98 m |
| bay pitch | 2.09 – 3.49 m |

---

## Tier 1 — the class ladder

The spine. Three points on Daly's own *Première / Deuxième / Troisième* ladder,
which is a period taxonomy rather than an invented one.

**A · Commercial boulevard** — *built*
`street 22 m · parcel 14 m · 1865 · comfortable · shop`
RdC + entresol + 4 étages + comble. The densest lawful stack: a street over 20 m
grants the full 20 m of facade, a shop buys an entresol, and four étages is what
then fits. Cornice presses the ceiling.
*Daly: 63 / 77 / 120 bd de Sébastopol, 39 rue Neuve des Mathurins, 6 bd Saint-Germain.*

**B · Grand avenue** — *proposed*
`street 30 m · parcel 18 m · 1865 · grand · residential · carriage`
No entresol, carriage entrance, richest ornament.

What separates this group from A is **programme, not proportion**: the entresol
buildings are the commercial percées (Sébastopol, Bergère, Conservatoire,
Saint-Germain, Neuve des Mathurins) and the entresol-less ones are the
residential avenues. That is the same finding A2.2 already encodes — an entresol
follows a shop, not a class.

> **Retracted claim.** An earlier draft said the height freed by omitting an
> entresol goes into taller étages — "an entresol *or* tall rooms, never both".
> **The measurements do not support it.** Mean étage height: 3.34 m with an
> entresol against 3.40 m without — a 0.06 m difference, well inside the
> ±0.2–0.4 m error bar on storey heights. The principal floor runs 3.82 m *with*
> an entresol against 3.79 m without, i.e. marginally the other way. The ranges
> overlap almost entirely (3.05–3.82 vs 2.98–3.83). The claim came from
> cherry-picking Champs-Élysées 119 and 125 while ignoring that Bergère 26 (4.29)
> and Sébastopol 2–4 (4.36) are taller still *and* have entresols.
>
> Nor was there ever footprint evidence: **0 of 16 buildings carry any depth or
> area measurement.** These are elevations. Any claim about room *size* rather
> than *height* is unsupported by this corpus in principle, not just in practice.

*Daly: 119 and 125 avenue des Champs-Élysées, 3 rue de la Paix.*

**C · Modest faubourg** — *proposed*
`street 11 m · parcel 9 m · 1865 · modest · residential`
Narrow street, so the ceiling never binds — cornice ~15 m against a 20 m limit
elsewhere. Pedestrian door, no entresol, minimal ornament, étages nearly equal.
Troisième has **no piano nobile at all**: its floors sit within 0.07 m.
*Daly: rue de Longchamps; 36–40 bd Beaumarchais.*

---

## Tier 2 — entrance variations

The entrance is the facade's ruler, so it deserves its own axis.

**D · Two-storey carriage arch** — *A14, built as `AC`*
`as A, with a round arch through RdC + entresol`
2.60 m wide. The width does not move; only the height. `A` and `AC` are the
matched pair — same street, parcel, date, class and programme, differing only in
the seed, and rasterised against each other every difference falls in the
entrance bay.
*Daly: Avenue de l'Impératrice (2.62 × 7.30), 39 rue Neuve des Mathurins (2.57 × 5.00).*

**E · Two-storey pedestrian arch** — *A14, built as `AP`*
`street 11 m · parcel 9 m · 1865 · comfortable · shop`
The same idea at the narrower end, where a carriage entrance was never available:
an 11 m street is under the 12 m a carriage needs to turn in, so the frontage
takes a porte piétonne however comfortable the household. The arch is 1.75 m wide
here against 2.60 at `AC`, and neither figure moved when the arch grew to two
storeys.

The tall form is **rarer on a pedestrian door than on a carriage one** — 1 of 7
against 1 of 2 among frontages that have an entresol — which is a rate and not a
rule (A18). Both kinds draw for it.
*Daly: 2 et 4 bd de Sébastopol (Davioud, 1.74 × 5.01), 87 bd de Sébastopol.*

---

## Tier 3 — entresol head forms

~~**F · Entresol absorbed**~~ — **WITHDRAWN by A17.2.** This asked for a preset
showing the devanture spanning RdC + entresol as one framework, with no separate
entresol band. There is no such building. It was a misreading of plate 77, which
at full resolution shows the shopfront closing at a full-width entablature and
the entresol above it standing as its own register in the stone. A preset cannot
be built for it because the generator no longer produces it, and should not.

**F · Entresol head form** — *A17.2, done*
One pair, identical but for the seed, showing the one thing that does vary between
Daly's two entresols: the head their lights are turned with. Square-headed at 77,
*arc surbaissé* at 120 — both on their own low *allège*, both with a garde-corps,
both in the base's own bossage. Drawn per frontage on `facade/entresol/head`.
*Daly: 77 bd de Sébastopol (square), 120 bd de Sébastopol (segmental).*

---

## Tier 4 — the date hinges

These are the **discontinuity tests** — the brief's "move the date past a decree
and the roofline should change shape."

**H · The 1884 pair** — *half built; the post-1884 side is `P`*
Two presets, identical but for the year. Straight 45° comble against Alphand's
circular arc, and a storey gained. Nothing else changes.

`P` is the post-1884 side, at 1887. The matched pre-1884 twin is **not** a
preset, but the hinge it was written to test does work — run `P`'s own site at
1883 against 1887 and only the year differs:

| | 1883 | 1887 |
|---|---:|---:|
| comble profile | 4 points (straight 45° brisé) | 28 points (circular arc) |
| ridge over eaves | 3.20 m | 7.04 m |
| storeys | 6 | 7 |
| cornice built | 19.45 m | 22.48 m |

So the storey **is** gained and the roof **does** change shape, exactly as this
entry predicted. What is still missing is the pair as a shipped, rendered preset
so the discontinuity is visible on a contact sheet rather than only in a table.

**I · Post-Bonnier** — *proposed*
`street 22 m · 1905` — eighth-circle arc continued by a 45° oblique; projections
may now carry above the cornice. Outside Daly's window, so unanchored.

**J · Pre-Haussmann** — *proposed*
`street 12 m · 1835` — before the 1859 règlement. Lower ceiling, flat incised
*refends* rather than bossage, thin lozenge ironwork. Tests that the chronology
runs backwards as well as forwards.

---

## Tier 5 — geometry the solver has to survive

**K · Corner with *pan coupé*** — *built as `P`*
`corner=True` — the chamfer as a third short facade with its own rhythm. The
3 rue La Fayette condition.

**L · Narrow parcel** — *proposed*
`parcel 7 m` — where the fitting solver's narrow special fires and the entrance
consumes a third of the frontage. Daly's narrowest is 8.57 m.

**M · Wide frontage** — *proposed*
`parcel 24 m` — where `ADD_MODULE` and the parity rule matter, and a central
feature has to hold the axis.

---

## Tier 6 — the block

**N · A run** — *proposed*
`frontage 110 m · 9–10 parcels · corners both ends`
The 1855 circulaire: shared cornice, string courses and balcony lines across
party walls. The unit the brief says is primary. Varied parcel widths.

---

## Notes on what is deliberately absent

- **No "typical Haussmann" preset.** There isn't one, and asserting one would be
  the taste-driven parameterisation this project exists to avoid.
- **No second typology.** Brownstone, canal house and cast-iron are the port
  exercise, and the brief is explicit that designing for them before the first
  typology is finished fits neither.
- **Nothing between Tier 4's hinges.** The point of a date preset is to sit
  either side of a decree; sampling the middle adds cost without testing anything.
