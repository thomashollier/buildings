# A24 — the pier is too wide (PARKED, not landed)

## The complaint
The wall between two windows (the **pier**) renders wider than it is on the plates.
Ours: window 1.20 m, pier 1.83 m — the pier is 1.53x the window.
Daly's: pier runs 1.09x to 1.92x the window, but the *narrow-pitch* buildings sit near 1.1x.

## What the operator specified
Pier must land between **0.8x and 1.5x** the window. Surplus frontage is resolved by,
in preference order:
1. widen or narrow the spacing within that range
2. add a module (one more bay)
3. symmetrical: piers narrower in the middle, wider at the ends
4. inverse: wider in the middle, more crowded at the edges
5. if a pier still exceeds 1.5x, put something on it (a pilaster / column / panel)

Only (1) and (2) have been attempted. (3), (4), (5) are unimplemented.

Rule 5 makes a **testable prediction**: the plates whose piers exceed 1.5x
(39 rue Neuve des Mathurins at 1.75x, 120 bd de Sebastopol at 1.92x) should carry
something on those piers; the ones under (77 bd de Sebastopol 1.09x, 1 bd de
Sebastopol 1.16x) should not. Nobody has checked this. It is the cheapest next test.

## Root cause
The window is an ABSOLUTE quantity and the bay is elastic, so every metre of
frontage slack the solver cannot place elsewhere ends up inside the pier via the
WIDEN_FILLER rung. The pier has no upper bound of its own.

## The measurements this rests on
Taken off four plates, calibrated against each plate's own stated facade width.

| plate | window (glass) | pier | pitch | window / pitch | pier / window |
|---|---:|---:|---:|---:|---:|
| 77 bd de Sebastopol  | 1.11 | 1.23 | 2.35 | 0.474 | 1.11 |
| 1 bd de Sebastopol   | 1.04 | 1.21 | 2.24 | 0.463 | 1.16 |
| 39 rue Neuve des Mathurins | 1.10 | 1.93 | 3.02 | 0.364 | 1.75 |
| 120 bd de Sebastopol | 0.91 | 1.75 | 2.68 | 0.340 | 1.92 |
| **ours (House A)**   | 1.20 | **1.83** | **3.03** | 0.396 | **1.53** |

Note the window measurement is to the **glass**, not to the outside of the stone
surround. `opening_width_typical` in `daly_measurements.json` includes the surround
and so reads about 0.15 m wider; do not mix the two.

## The patches here
- `pier-ratio-band.patch` — clamps pier/window into the 0.8..1.5 band directly.
  Treats the symptom. Does not change the bay count, so House A still gets a
  3.03 m pitch, which no plate of that width shows.
- `natural-count-nearest.patch` — changes `_natural_count` in
  `src/buildings/solver/fitting.py` from `floor` to **nearest**, with a guard that
  steps back down if nearest would push the run below `bay.minimum`.
  This is the one that addresses the cause. See the note below.

Neither is applied. HEAD is green without them.

## Why `nearest` is probably the real fix
House A is a 14.0 m frontage. The solver computes 10.60 / 2.80 = 3.79 bays and
floors it to 3, so the facade carries 4 axes (1 door + 3 windows) at a 3.50 m
theoretical pitch, resolved down to 3.03 m with the surplus dumped in the piers.

Rounding to nearest gives 4 bays -> **5 axes** -> a 2.40 m pitch -> a 1.20 m window
against a 1.20 m pier -> **ratio 1.0**, inside the operator's band and matching the
two Sebastopol frontages measured above.

The operator supplied four counts read straight off the plates:

| plate | width (m) | axes | implied pitch |
|---|---:|---:|---:|
| 119 Champs-Elysees | 12.4 | 4 | 3.10 |
| 3 rue de la Paix | 16.7 | 7 | 2.39 |
| 39 rue Neuve des Mathurins | 15.0 | 5 | 3.00 |
| 1 bd de Sebastopol | 16.8 | 7 | 2.40 |

Those bracket House A: 12.4 m -> 4 axes and 15.0 m -> 5 axes, so 14.0 m should
carry **5**. It currently carries 4. That is the bug, stated without reference to
any ratio.

## Cost of landing it
About 29 tests fail — they pin which ladder rung fires for a given frontage, and
changing the starting count changes the rung. They are pinning the old behaviour,
not an invariant. They need rewriting, not deleting. The three guards
(`check_ir_is_consumed`, `check_no_period_branching`, `check_renderer_dumb`) are
untouched by this and must stay clean.

## Open discrepancy — do not lose this
The operator reads **119 Champs-Elysees as 12.4 m wide**. Our
`daly_measurements.json` records **14.93 m** for the same building. That is a 2.5 m
disagreement and it changes that plate's pitch from 3.10 to 3.49 — which is the
single widest pitch in the whole corpus and is currently doing real work as the
upper anchor for `_BAY_PITCH_MAX`. Resolve the width before trusting anything
derived from it. The other three widths agree to within 0.13 m, so this one looks
like a genuine error rather than a definitional difference.
