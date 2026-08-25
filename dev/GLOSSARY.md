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

## Entrances

| term | what it is |
|---|---|
| **porte cochère** | a carriage entrance — wide enough to drive through to the *cour*. 2.60 m clear |
| **porte piétonne** | a pedestrian door. 1.75 m clear. The commoner of the two |
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
