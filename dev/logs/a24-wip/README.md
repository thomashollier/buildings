# A24 work in progress — the pier/window band

`pier-ratio-band.patch` applies cleanly to `856b62a`. It is **not** committed to
`src` because it breaks a real invariant; the measurements behind it are sound
and are the reason to finish it.

## The operator's rule

Where nothing stands on the pier, it is never wider than **1.5×** the window and
never narrower than **0.8×**. A bay is centreline to centreline — one window plus
one pier — so those ratios are the bay's band: **1.8× to 2.5×** the window.

Surplus frontage is then resolved by: (1) widening/narrowing within the range,
(2) adding a module, (3) symmetrical arrangement with narrower piers at the
centre, (4) the inverse, or (5) putting a column on any pier over 1.5×.

## What the patch does

- composes `_BAY_PITCH_MIN/MAX` from `opening_window().preferred` and the two
  pier ratios, instead of two free numbers — 2.16 to 3.00 m
- separates `_FIXED_SLOT_SPAN_MAX` (3.40 m, what a lintel spans) from the
  repeating bay's ceiling, so a *porte cochère* is bounded by its own lintel
  rather than by the rhythm

## Why it is parked

It pushes the solver up the ladder into `INSERT_SPECIAL`, and something on that
path is **seed-sensitive**: `test_a_different_seed_is_a_different_building_but_
the_same_shape` fails with different bay counts AND a different storey count
between seeds. Shape must not depend on the seed. That is core solver behaviour
and wants a design pass, not a patch.

## The measurements, which stand either way

Measured off four Daly plates, each calibrated on its own stated facade width:

| plate | window (glass) | pier | pitch | win ÷ bay |
|---|---:|---:|---:|---:|
| 77 bd de Sébastopol | 1.11 | 1.23 | 2.35 | 0.474 |
| 1 bd de Sébastopol | 1.04 | 1.21 | 2.24 | 0.463 |
| 39 rue Neuve des Mathurins | 1.10 | 1.93 | 3.02 | 0.364 |
| 120 bd de Sébastopol | 0.91 | 1.75 | 2.68 | 0.340 |
| **ours at 856b62a** | 1.20 | **1.83** | **3.03** | 0.396 |

Ours is at the wide edge on both. With the patch: pier/window 0.71–1.33 against
the rule's 0.8–1.5, and win/bay median 0.429 against the corpus's 0.432.

## Two claims in the codebase the corpus refutes

1. **`_BAY_PITCH_MIN` = 2.70 m**, whose note argued "a facade built of 2.35 m
   bays is not the same claim at all". 77 bd de Sébastopol *is* a facade built of
   2.35 m bays — six openings across 14.75 m, measured at 57.6 px/m and agreeing
   with Daly's stated 2.353 to a centimetre. **Six of the sixteen sit under
   2.70.**
2. **The tripwire binding a fixed slot to the repeating bay's ceiling.** On four
   of Daly's seven carriage buildings the door is at or wider than that
   building's own pitch (125 Champs-Élysées 2.53 against 2.39; 3 rue de la Paix
   2.60 against 2.32); on the other three it fits. Neither direction holds as an
   absolute.

## Not attempted

Rules 3, 4 and 5 — symmetrical pier arrangements and the pilaster on an
over-wide pier. Rule 5 makes a testable prediction worth checking first: the two
plates whose piers exceed 1.5× (Mathurins 1.75, 120 bd de Sébastopol 1.92)
should carry something standing on those piers, and the two under it (77 at 1.09,
1 bd at 1.16) should not.
