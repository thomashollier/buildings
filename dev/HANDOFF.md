# Where this stands — 2026-08-25

Read this first on a fresh session, then `README.md` for the invariants and the
construction ladder, `dev/GLOSSARY.md` for vocabulary and `dev/CONTRACTS.md` for
the binding spec.

## Repo state

**1520 tests passing, 0 failing. All three guards clean. IR verified
byte-identical over five runs of one site and seed.**

A24 — "the facade is under-divided" — is **CLOSED**. The two patches that were
parked in `dev/logs/a24-wip/` are gone; neither was applied, and the README
there now records why.

## What changed, and what it was worth

### The bay count is chosen by closeness, not by flooring (A24)

`_natural_count` in `src/buildings/solver/fitting.py` used to floor the
division, which discards up to a whole axis and then forces the ladder to hide
the remainder. It now walks candidate counts outward from the nearest-filling
one and takes the first the declared bounds permit.

House A — 14.0 m, 22 m street, 1865, comfortable, shop, seed 8 — was the case
this was raised on. It now solves symmetrically, with the entrance on the centre
axis and every bay on the preferred pitch:

    pier_end 0.280 | 2.600 | 2.600 | porte cochère 3.040 | 2.600 | 2.600 | pier_end 0.280
    = 14.000 m, 5 axes

Where no count is eligible the old floor is returned unchanged, so every width
that reaches rungs 4–5 solves bit-identically to before.

### The bands were redrawn — OPERATOR-SET, not measured

|  | min | preferred | max | was |
|---|---:|---:|---:|---|
| bay pitch | 2.00 | 2.60 | 3.20 | 2.70 / 2.80 / 3.40 |
| window | 1.20 | 1.30 | 1.35 | 1.04 / 1.20 / 1.30 |

Both are **OPERATOR-SET** and their `why` strings say so. They are *not* Daly
medians and must not be cited as such. The corpus is kept in the docstrings as
context, not as justification.

A soft `window / pitch = 0.45` target is handed to the solver as the bay's
`affinity` — a tie-break between counts that are equally far from preferred. It
never widens a bay on its own account and never makes an arrangement
infeasible. Note the three ideals cannot all hold: 1.30 / 2.60 = 0.500, so at
rest the ratio lands at 0.500 and the soft target yields.

### The aspect band floor moved on evidence

`opening_aspect_band` is now **(1.56, 2.00)**, was (1.70, 2.00). The floor moved
on `opening_aspect_principal` — Deuxième n=10, min 1.56, rated "SOURCED for
ordering". The ceiling was left alone: nothing was failing against it.

`opening_aspect_uppers` was considered and **rejected as INSUFFICIENT** — the
file's own note says within-building variation exceeds between-class variation,
and its 1.14 minimum is one storey of one building.

### The dormers clear the cornice (A25)

The main cornice crowns the eaves and stands *on* that line; lucarnes stood at
`eaves + skirt`, the plumber's 0.35 m apron and nothing else. The cornice
reached up through the apron and cut the feet off the dormers. Real on three of
the four canonical situations.

`_cornice_clearance` in `terminate.py` lifts the **bottom row only** — applying
it per row spends an already-full brisis and a two-storey garret came back with
its second storey blind — and is **clamped to available slack**, because
lifting past it deletes the row entirely.

### The lucarne clears the cornice because the FOLD knows about it (A30)

A25 lifted the bottom row of lucarnes clear of the main cornice and clamped the
lift to whatever slack the brisis had spare. Where a comble had no slack the
lift was zero and the cornice went on cutting the window. **Six of the ten
canonical presets overlapped**, H83 worst at 0.152 m — its brisis is 1.900 m,
which is `_shortest_brisis_that_carries_a_lucarne` to the millimetre.

The lift was the wrong object. What stands between the eaves and the foot of a
lucarne is the **apron**, and the apron is whichever is deeper of the two things
that must pass under there: the plumber's zinc (`_dormer_skirt`, 0.35) and the
masonry cornice crowning the same eaves (`_cornice_clearance`). `_lucarne_apron`
is that one line. It goes into `_shortest_brisis_that_carries_a_lucarne`, so the
**fold** stops above it and the room is there before any lucarne is placed.

    H83 brisis 1.900 -> 2.052    foot lands on the cornice line
    face 1.300 exactly           head keeps its 0.250
    cornice keeps its full height, nothing ABSOLUTE is spent

All ten presets clear. No dormers lost anywhere.

**Two things were tried first and failed, both instructive.** Raising the
minimum brisis *alone* makes it worse — the minimum and the slack move
together, so the clamp bites harder and AP went -0.013 -> -0.152. And letting
the face give would fix everything visually at a cost of 360 of 1728 swept
sites losing face, worst 1.037 m against a 1.300 m ABSOLUTE that means "a
window an adult can see out of standing". Neither is in the tree.

**It is roof-only.** Swept 480 sites: `roof`, `silhouette`, `dormer`,
`brisis_window` move and **zero facade nodes** do — no storey, bay, opening,
cornice, string course or balcony, and no site gains or loses a node. On the
four goldens the same holds; the `special` nodes that moved carry
`hidden_in_the_comble` and are chimneys sitting in the roof.

**Two accepted costs, both measured.**

1. **60 of 960 roofs gain a small flat terrasse** (none lose one) and the fold
   rises on 180 by at most 0.082 of `break_pct`. The canonical A12.1 case is
   one of them: it now folds on the lucarne floor at 2.052 rather than at the
   1.904 where the terrasson met the ridge, leaving **0.546 m** of deck. That
   is not the defect A12.1 removed — that one was **3.69 m** of an 8.0 m
   half-depth — and `test_the_fold_is_where_the_terrasson_reaches_the_ridge`
   now pins the difference rather than merely allowing a deck.

2. **`test_the_lucarne_count_is_the_comble_s_own_and_never_the_class_s` was
   narrowed to mid-block, on the operator's decision.** A cornice is a fraction
   of the storey it crowns and storey heights are class-scaled, so the apron is
   class-scaled; on a hipped corner the roof falls away toward the returns and
   a foot set higher genuinely runs out of roof. Clearing the cornice and
   keeping class out of the roofscape **cannot both hold** — pinning the apron
   to the deepest class does not flatten it either, because the storey varies
   too (measured: 0.529 / 0.491 / 0.589 / 0.613 at GRAND on one site).

   Mid-block keeps the strict claim: **175 of 175 buckets class-flat**. Corners
   split on **7 of 182**, always by exactly 2. The corner branch is not skipped
   — it asserts the thing A9.1 actually cared about, that the roofscape never
   *grows* as the building gets grander, which was the original defect (a 16 m
   frontage reading 5 / 5 / 4 / 4 down the ladder).

## Open, and none of it is blocking

**The carriage jamb is PROVISIONAL.** `carriage_jamb_width` is 0.22, marked
PROVISIONAL in both the docstring and the `why` string, with
`test_the_carriage_jamb_says_it_is_provisional` existing to be deleted when
someone settles it. It moved because the 3.40 m slot it produced collides with
the new 3.20 m pitch ceiling — every carriage building raised `RuntimeError`.

Two ways to settle it, neither taken:

1. **Measure the jambs.** HANDOFF used to call this "cheap to check". It is
   not. The corpus has door *clear* widths (2.41 / 2.534 / 2.57 / 2.575 / 2.60 /
   2.619 / 2.672) but **not the slots**, and inferring a slot from the bay pitch
   gives absurd results including negative jambs. It needs pier-face to
   pier-face measurement off the porte detail plates.
2. **Give the entrance its own ceiling.** A10.1 already gave it its own *floor*
   via `special_lo` — which is why a 2.35 m porte piétonne legitimately sits
   under the pitch floor. The entrance currently has its own floor and someone
   else's ceiling. Completing that symmetry needs no new number.

**~~The class-flat window width has never held.~~ CLOSED by A28.** The open
question was "may width give way to aspect at all?", and the operator's answer
is no. `window_in_slot` no longer narrows an opening that would be squat for
its storey; the aspect band governs the HEIGHT and nothing else. The realised
width now differs between classes on **0 of 60 sites**, where it differed on
60 of 60 before, and it no longer varies by storey either — 2 684 openings
across 196 class × street-width sites all measure 1.300 m. A short storey gets
a squatter window instead of a narrower one; the squattest realised aspect over
49 248 swept openings is 1.154 and none comes out wider than tall. The renderer's
0.06 m frame reveal went with it, so the drawn glass measures the stated
opening.

Two things it left behind, neither blocking:

- **The 2.00 aspect ceiling is not enforced on the output** and never was —
  a grand principal floor reaches 2.52. `window_in_slot` only ever asserted the
  floor. Unchanged by A28, recorded here because A28 is where anyone will next
  look.
- **A narrow special still emits a 0.455 m light**, under the 0.55 m
  `minimum_light_width` — its slot is only 1.10 m wide and `_fit_width` gives
  what is left after two piers. Ordinary windows are clear of the floor on all
  83 467 openings swept. It predates A28 — a width test in `window_in_slot`
  that would have caught it
  was tried and reverted, because it turned 640 fuzz openings blind and left an
  ironwork node hanging on a light that no longer existed. It wants its own
  decision, next to `block._refit_light`, which already answers the same
  question for a chamfer.

**The entresol is under a rule that does not govern it, and has no repertoire
of its own.** Operator, this session: *"the dormer and entresol windows don't
have the same window aspect ratio restrictions. Entresol treatments take all
sorts of shapes and sizes. Sometimes there is no window at all, sometimes it is
similar to the other windows but squatter, sometimes they are round."*

Two separate facts follow, and the first is a live trap:

1. **It asks for a facade window's proportion.**
   `entresol_arcade_is_sized_by_the_storey_it_lights` calls `window_in_slot`
   with `wanted_aspect=aspect_for_rank(ctx.rank_from_principal)`, which returns
   **2.000** at the mezzanine — the principal floor's own figure. It realises
   1.41-1.57 only because the entresol storey is too short to deliver what was
   asked. **It is squat because it is clipped, not because anything permits it
   to be squat.** Anyone who fixes the height shortfall (see below) will drag
   the entresol up with the facade windows unless it is cut loose first.

   **Dormers are already exempt and need no work.** They never reach
   `aspect_for_rank`: `terminate.py` sizes them from the comble via
   `_dormer_face_height(brisis, skirt)`. Realised aspects across the ten
   presets run 1.08-1.90 and follow the roof, which is the intended behaviour.
   Only three call sites reach `window_in_slot` and none is the dormer.

2. **The variety is not modelled.** `opening_type_for` returns exactly four
   strings — `window`, `shop_bay`, `none`, `narrow_window`. The entresol is
   always a `window`. None of "no window at all", "squatter", or "round" is
   expressible for it. Note `roundel_in_slot` already exists in the catalogue
   and is wired **only** to the narrow special, so the round entresol's
   machinery is built and merely unreachable from `Role.MEZZANINE`.

The small separable change is (1): give the entresol its own proportion instead
of `aspect_for_rank`. (2) is a repertoire, and wants the same treatment the
narrow special is waiting for — triggers of its own rather than a leftover.

**Piers cannot vary.** `_absorb` returns two scalars, so every end pier is one
width and every interior pier another. The operator's A24 rules 3 and 4 —
"symmetrical: piers narrower in the middle" and its inverse — are not
unimplemented features, they are inexpressible in the current object. The
primitive that survives non-uniform piers is *axis positions plus one window
width*, with pitch and pier both derived per interval. `_absorb` is the seam.

**`_BAY_PITCH_MAX` is crossed by the corpus.** 119 Champs-Élysées measures
3.71 m against the 3.20 ceiling. One plate, recorded rather than acted on.

## Where this is going — the layer above the baseline

Everything landed so far is the **default layout rule**: one uniform pitch,
absorption in a fixed tier order, no randomness, no class bias. That is
deliberate. It is the foundation the expressive layer sits on, and it wants to be
solid and predictable before anything is built over it. What follows is the
intended direction, recorded so the baseline is read as a foundation rather than
as the finished behaviour.

### 1. Rigidity in the ranges — absorption as a cloth solve

Today `_absorb` is a queue: each tier has effectively **zero** stiffness until
its capacity is spent and **infinite** stiffness thereafter. Ends take everything
until full, then bays begin.

The intent is a stiffness curve instead. Every elastic element yields at once, in
proportion to the room it has left, and **resists more the further it is from its
preferred value** — so a bay approaching its maximum stiffens and the residue
migrates to whatever still has room, the way a cloth solver redistributes
tension. The present queue becomes the degenerate case of that curve.

Both pieces already exist:

- `SlotSpec.elasticity` — a per-slot number the absorption sort already reads,
  currently 1.0 everywhere. Today a *priority*; it wants to become a *stiffness*.
- `FitResult.strain` — per slot, the fraction of that slot's own latitude spent.
  Already the right state variable; today it only *reports*, and it needs to
  *act*.

For linear springs the distribution is closed-form
(`d_i = residue x (1/k_i) / sum(1/k_j)`); stiffness that rises with deformation
makes it iterative, which is where it becomes genuinely cloth-like. This must not
break I5: the solve stays deterministic, and any iteration needs a fixed
termination rule.

### 2. Class as a bias within the generic ranges

The generic-first rule below still governs — no class-specific band. Class biases
*within* the shared ranges.

- **Per-class preferred pitch is one constant away.**
  `_BAY_PITCH_CLASS_SPREAD` is 0.0 and `_BAY_PITCH_CLASS_POSITION` already maps
  modest 0.0 -> grand 1.0. Set the spread non-zero and a modest building takes a
  narrower ideal bay than a grand one, with no code change.
- **Per-class absorption policy is different in kind** — a *policy*, not a
  parameter. A grand building would rather absorb surplus into a wider central
  symmetrical arrangement; a modest one would rather pack in another axis. That
  is a preference among *comparable* answers, so it attaches where the soft 0.45
  affinity tie-break already sits, and it is the natural consumer of seeded
  choice: sample among ties, weighted by class. Randomise among **ties only** —
  never let a seed pick a materially worse arrangement over a better one.

### 3. The narrow special — a design element awaiting its trigger

The special is a deliberate compositional element: a half-bay, an oeil-de-boeuf,
a blind panel. It comes into its own once the default rule is solid and the layer
above it exists. It is **not** a broken feature and should not be written up as
one.

What is true today is only that its *current* trigger is quiet. It is produced
from leftover width alone, and choosing the closest count on a 2.00-3.20 band
puts the pitch near preferred almost everywhere, so little is left over. Measured
across 210 widths from 3.0 to 24.0 m: one width yields a special with a
pedestrian door, eight with a carriage door, all below 5.4 m. That is the
expected consequence of a tidy baseline, not a fault in it.

Leftover width was never the real reason a building has one. The work is to give
the special **triggers of its own**:

- the class policy in (2) — a grand facade that *wants* a central accent is a
  building that wants a special, independent of any residue;
- conditions from the plates, none yet verified: an irregular parcel, a staircase
  or carriage passage forcing an odd division behind the facade, a party-wall or
  alignment inheritance, a corner or chamfer;
- operator **rule 5**, still unchecked and falsifiable — "if a pier exceeds 1.5x
  the window, put something on it." The plates whose piers exceed 1.5x should
  carry something; the ones under should not.

Revisit placement at the same time: a special is currently always central or a
flanking pair. If the plates show them elsewhere, the placement rule moves too,
not only the trigger.

## How the operator wants to work

- Explain in plain terms before changing anything.
- **Generic first.** Do not lock in numbers by building class until a generic,
  inclusive parameter set works on an average building. The generic ranges must
  be able to produce *all* classes; class then becomes a bias *within* them, not
  a separate band. Several bands are still drawn tighter than their evidence —
  auditing them against `daly_measurements.json`'s own SOURCED / WEAK /
  INSUFFICIENT ratings is the natural next pass.
- Measure against the plates, not against prose.
- Check a quantity's rating before quoting it. That file rates itself, and two
  numbers were leant on this session that it marks INSUFFICIENT.
