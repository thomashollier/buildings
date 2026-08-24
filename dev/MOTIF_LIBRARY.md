# A motif library — proposal

## The distinction that decides whether this helps or ruins the project

There are two things people mean by "clip art", and they sit on opposite sides of
this project's central rule.

**Composition clip art** — a library of nice balconies you browse and place.
This is the failure mode the brief exists to prevent: *"parameterised by taste…
they produce plausible buildings, and every one of them is plausible in the same
way, because the author's taste is the only thing holding them together."* It
would put an arguable decision back in the renderer, which
`check_renderer_dumb.py` forbids and which we have now removed four separate
times (A4.3, A5.2, A6.11, A7.2).

**Execution clip art** — the IR has already decided
`ironwork_pattern = "dense_cast_scrollwork", w = 2.80, h = 0.90, ornament_count = 7`,
and the library is *how that gets drawn*. No decision moves. The renderer stops
approximating dense cast scrollwork with a row of bars and circles, and draws
dense cast scrollwork.

**Only the second is worth building.** Everything below assumes it.

---

## The seam already exists

`elements.py` dispatches on IR-stated variant strings today:

| prop | values it already switches on |
|---|---|
| `form` | none · moulded_architrave · pedimented · round_arched · segmental · irregular · oeil_de_boeuf |
| `head` | round · segmental · irregular |
| `treatment` | raised_bossage · picturesque_rustication · timber_small_panes · cast_iron_larger_panes · devanture_elaborate |
| `course_kind` | plat_bande · entablature |
| `cornice_ornament` | modillioned · plain |
| `ironwork_pattern` | (from chronology) |

Each of those dispatch points is currently a procedural drawing routine. A motif
library replaces the *body* of each, not the dispatch. Nothing new decides
anything.

---

## Where the motifs should come from

**César Daly's detail plates.** We already hold **28 dimensioned detail plates**
in `dev/reference/images/daly-1864/`, plus more ornament plates that the harvest
deliberately skipped. They are public domain, **measured**, **dated 1864**, and
captioned with class and address.

That beats the alternatives decisively:

- *Drawing from imagination* — reintroduces the author's taste, which is the
  thing being eliminated
- *Scraping modern clip art* — licensing is murky and period accuracy is
  accidental at best; most "Parisian ironwork" clip art is Art Nouveau, which is
  **post-1895** and wrong for every building we currently generate
- *Tracing photographs* — perspective distorts, and the brief is explicit that
  photographs do not support measurement

Tracing a measured elevation gives clean provenance *and* correct proportion, and
the plate reference goes in the motif's metadata exactly as `Reg()` citations do.

For families Daly does not cover — 1820s–40s lozenge ironwork, 1890s
Renaissance-revival, Guimard whiplash — the honest move is to mark those motifs
**INFERRED** rather than pretend a source exists, or to harvest Daly **Série 2
(1872)**, which is already catalogued in `SOURCES.md` and sits on the far side of
the 1870 stylistic hinge.

---

## Four hard constraints

Each corresponds to a bug we have already fixed once. A motif library is the
easiest way to reintroduce all four at once.

1. **A motif may not carry its own extent.** The IR states `w` and `h`; the motif
   fills them. *(A4.1: openings were drawn at the bay's size because the IR
   didn't state their own.)*
2. **A motif may not decide a count.** The IR states `ornament_count`; the motif
   is the unit that gets repeated. *(A5.2 mullions, A6.11 modillions — the
   renderer dividing a width by a magic number.)*
3. **A motif is selected by the IR's variant string, never by year or class.**
   `check_renderer_dumb.py` enforces this; do not work around it.
   *(A4.3: renaming `richness` to `ornament_weight` to evade the scan.)*
4. **Date availability lives in `chronology.py`, not in the library.** The
   catalogue decides which variants a building of year Y and class K can see; the
   library only knows how to draw them. *(The period-enum trap.)*

---

## The tiling problem is the fitting problem again

Ironwork, modillions, dentils, cresting and bossage coursing are all **repeating
motifs that must exactly fill an IR-stated width at an IR-stated count**.

That is the brief's fitting problem at ornament scale, and the same answer
applies: a motif needs a *range* of acceptable widths, not one width, and the
remainder goes somewhere meaningful — a wider end panel, a half-motif at a
返 corner, a plain segment against the pier. Do not scale the motif to fit, which
is the ornament equivalent of stretching a doorway.

Worth reusing `solver.fitting` here rather than writing a second, worse solver.

---

## Priority, by visual payoff × dating value

1. **Ironwork** — the brief calls it *"the best of them"* for dating, and it is
   the most visible thing on the facade after the openings. Four dated variants:
   lozenge/palmette (1820s–40s) → dense cast scrollwork (1850s–80s) →
   Renaissance-revival (1880s–90s) → whiplash (1895+).
2. **Agrafes, consoles and mascarons** — the keystone family, which currently
   draws as a plain trapezoid. Daly's detail plates are rich in these.
3. **Modillions and dentils** — the cornice, which reads at street distance and
   is currently a row of rectangles.
4. **Window surrounds and pediments** — profiles rather than outlines.
5. **Dormers** — form is already stated by chronology; the drawing is crude.
6. **Shopfront parts** — fascia, consoles, stall riser, mosaic. The fastest-
   turning family, so the best carrier of observation-date variation.

**Not clip art, ever:** the roof silhouette, the bay grid, storey heights, the
gabarit. Those are derived, and a library would be a second opinion about
geometry the IR already owns — the bug class we hit five times.

---

## Format

SVG `<symbol>` definitions with a declared **unit width** and a **stretch
policy** (`tile` / `stretch-ends` / `centre-and-tile`), referenced by `<use>` at
the extent the IR states. Text-based, diffable, no binary assets, and it survives
the existing "renderer output is byte-identical" test.

A manifest maps `(element_kind, variant) → motif_id`, plus each motif's plate
citation and whether its proportions are MEASURED or INFERRED — the same
discipline as `daly_measurements.json`.

## A guard to add

`check_ir_is_consumed.py` currently catches a stated fact the renderer ignores.
It should be extended to catch a motif that **overrides** a stated fact — a
`<use>` whose width does not match the IR's `w`, or a repeat count that does not
match `ornament_count`. Otherwise constraints 1 and 2 above are honour-system.
