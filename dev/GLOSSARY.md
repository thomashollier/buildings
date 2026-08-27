# Glossary

The model is written in the vocabulary of its sources, which is French and
technical. This is what the words mean and where each one lives in the code.

## The stack, bottom to top

| term | what it is |
|---|---|
| **rez-de-chaussée** (RdC) | the ground storey |
| **socle** | the base of the wall, usually in heavier coursed stone |
| **bossage** | rustication — stone cut with a raised face and recessed joints |
| **devanture** | a shopfront: the joinery framework filling a commercial ground floor |
| **entresol** | the low storey over a shop, part of the *base block* rather than of the residential facade (A13) |
| **étage noble** / principal | the show floor, tallest and most ornamented — usually the 1er |
| **comble** | the roof volume as a whole. *Brisé* = broken-backed, i.e. a mansard |
| **garret** | a habitable storey inside the comble; the *chambres de bonne*. One per brisis band |

## The roof

| term | what it is |
|---|---|
| **brisis** | the steep lower slope of a mansard. `BRISIS_RISE` = 2.90 m |
| **terrasson** | the shallow upper slope above the fold |
| **brisure** | the fold where the two meet — what makes a comble *brisé* |
| **égout du toit** | the eaves; where the decree springs the roof envelope from (A3.1) |
| **lucarne** | a dormer — a window standing *out of* the slope, with its own cheeks and roof |
| **souche** | a chimney stack |
| **gabarit** | the legal envelope the roof must be inscribed in |

## Openings

| term | what it is |
|---|---|
| **croisée** | an ordinary window |
| **allège** | the low breast wall a light stands on. `window_allege_height` = 0.30 m (A22) |
| **appui** | the sill proper — the stone capping the allège |
| **barre d'appui** | the iron bar across the lower part of a light, standing on the appui (A21) |
| **garde-corps** | a guard rail. At floor level on a *porte-fenêtre*; inside the opening on a window |
| **porte-fenêtre** | a French window: a light down to the floor, walked through onto a balcony |
| **imposte** | the fixed panel over a door, inside the same frame — glazed, or an iron grille (A20.4) |
| **tympanum** | the carved panel filling an arch head above the leaves |
| **lintel** | the stone spanning an opening's head. `lintel_bearing_depth` = 0.30 m is that stone *plus* the joist ends bearing over it |
| **linteau / plate-bande** | the flat arch a lintel is cut as |
| **archivolt** | the moulding following the curve of an arch |
| **agrafe** | the ornamented keystone at an arch crown |
| **trumeau** | the pier of wall between two openings |

## Dividing the frontage

The horizontal vocabulary, which is the easiest part of this model to muddle
because three of the words are near-synonyms and one is overloaded. Diagram
drawn on a real solve: `dev/reference/diagrams/horizontal-nomenclature.svg`.

| term | what it is |
|---|---|
| **slot** | the generic unit. *Every* piece of the frontage is a slot — ends, bays, specials, the entrance. The solver's own word, deliberately architecture-free, because the same code fills a height budget with storeys. A `PlacedSlot` is just `name, kind, start, width` |
| **axis** | the centreline of an opening, running up the facade. **The thing you count.** Every slot carrying an opening has one; end slots and blind panels do not |
| **bay** | a slot of kind `REPEATING` — the module the rhythm is made of. Measured **centreline to centreline of the filler**: half-pier, opening, half-pier. That definition is why `N` bays is *exactly* `N × pitch` and the only special case is the two ends |
| **pitch** | the width of a bay, i.e. axis to axis. **The thing you measure.** Bay and pitch are the *same number*; prefer "pitch" in prose |
| **pier** | the masonry between two openings. `window + pier = pitch`, exactly |
| **jamb** | the structural minimum masonry beside an opening — the stone its head lands on. ABSOLUTE, set by what it carries. Anything wider than the jamb is ordinary elastic pier |
| **end** | the two `FLEXIBLE` slots at the extremities. No opening, no axis. The most elastic thing on the frontage: they absorb leftover width **first**, which is why they are often the fattest masonry on a facade |
| **narrow special** | a half-bay, œil-de-bœuf or blind panel — **off pitch by definition**. Its widest band (1.650 m) sits 0.350 m below the pitch minimum (2.000 m), so the two bands *cannot* overlap. It is the deliberate absorber for a frontage that will not divide evenly, and it is **not counted as an axis** even when it carries a light — so no lucarne stands over one |

**A word to avoid: "bay" in prose.** It names three different things — the
solver's repeating module, the vestigial `standard_bay` entry in the catalogue
(never called), and colloquially the opening itself. Say **axis** when counting
and **pitch** when measuring.

**Off pitch** is a real and useful description. Three things can be:

- a **narrow special**, off pitch *by design* — that is what it is for;
- a **porte cochère**, off pitch *by necessity* — at 2.60 clear plus two jambs
  its slot is 3.040 m, wider than most pitches, so it genuinely displaces the
  rhythm. This is the case the D6 guard is about: "a fixed slot wider than a bay
  is carried up every storey and costs the building a window on every floor";
- a **porte piétonne**, off pitch only *by accident* — its 2.350 m slot is
  narrower than a typical pitch and it has no need to break the rhythm. It did
  so only because the entrance was built as a rigid slot sitting in an elastic
  run. **Being corrected (A27):** a door narrower than the pitch is an opening
  in an ordinary bay, like a window — clear width ABSOLUTE, masonry around it
  elastic.

The general rule the three cases collapse into: *every axis is a bay; every bay
carries an opening; the opening's clear width is ABSOLUTE; a bay takes the
rhythm's pitch unless opening + 2 × jamb will not fit, and only then does that
one bay grow.*

## Entrances

| term | what it is |
|---|---|
| **porte cochère** | a carriage entrance — wide enough to drive through to the *cour*. 2.60 m clear; 3.040 m of frontage with its jambs |
| **porte piétonne** | a pedestrian door. 1.75 m clear; 2.350 m with its jambs. The commoner of the two — Daly has eight to three in Deuxième Classe, and Troisième has no carriage door at all |
| **battant** | a door leaf |
| **cour** | the courtyard behind the carriage passage |

## Horizontals

| term | what it is |
|---|---|
| **corniche** | the cornice — the crowning moulding at the top of the stone facade |
| **bandeau / string course** | a flat band running across the facade at a floor line |
| **balcon filant** | a *running* balcony: continuous across the whole frontage |
| **balconnet** | an individual balcony at one opening |
| **modillon** | a bracket under a cornice |

## Regulation

| term | what it is |
|---|---|
| **règlement du 27 juillet 1859** | the cornice-height step table, keyed to street width |
| **ordonnance de 1823** | the balcony rule — nothing may project below 6 m |
| **décret du 23 juillet 1884** | Alphand: the comble becomes a circular arc, not a 45° plane |
| **circulaire du 21 septembre 1855** | datum lines must align across a party wall — why a block reads as one wall |

## Sources

| term | what it is |
|---|---|
| **César Daly**, *L'Architecture privée au XIXme siècle sous Napoléon III* (1864) | the measured corpus, 16 buildings, one year |
| **Moniteur des Architectes** | a rival journal; the register holds several of its plates |
| **Première / Deuxième / Troisième Classe** | Daly's own social tiers, which the model maps to `grand` / `comfortable` / `ordinary` |
