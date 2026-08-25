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

**The class-flat window width has never held.** A9.4 says the width does not
move with class. That is true of the catalogue's declared band — `scale_for_class`
really is a no-op on it — and false of what gets drawn. Across a sweep the
realised width differs between classes on **60 of 60 sites**, before the 2026-08
changes as well as after. `window_in_slot` narrows an opening that would be
squat for its storey, class drives storey height, so class drives width. The
test only ever checked one fixture. Needs its own decision: may width give way
to aspect at all?

**Piers cannot vary.** `_absorb` returns two scalars, so every end pier is one
width and every interior pier another. The operator's A24 rules 3 and 4 —
"symmetrical: piers narrower in the middle" and its inverse — are not
unimplemented features, they are inexpressible in the current object. The
primitive that survives non-uniform piers is *axis positions plus one window
width*, with pitch and pier both derived per interval. `_absorb` is the seam.

**`_BAY_PITCH_MAX` is crossed by the corpus.** 119 Champs-Élysées measures
3.71 m against the 3.20 ceiling. One plate, recorded rather than acted on.

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
