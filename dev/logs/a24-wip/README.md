# A24 — CLOSED, 2026-08-25

**The facade was under-divided. It no longer is.** Kept as the record of what
the problem was and why the two patches parked here were both wrong; the
patches themselves have been deleted, neither having been applied.

## What the complaint was

A 14.0 m frontage (House A) carried 4 axes where the plates say 5. The pier
rendered 1.53x the window against a corpus that runs nearer 1.0-1.2. Everything
downstream — piers too fat, rhythm too slack, windows too far apart — fell out
of that single miscount.

## The cause

`_natural_count` floored `run / bay.preferred`. Flooring discards up to a whole
axis and then obliges the ladder to hide the remainder. On a 15.0 m frontage
with a carriage entrance it took 3 axes and inflated every pitch to 3.367 m to
absorb 2.5 m of slack, where 4 axes sit near the preferred pitch.

## The fix

The count is now chosen by *closeness* — walk candidates outward from the
nearest-filling one, take the first the declared bounds permit. Plus a redrawn
pitch band (2.00 / 2.60 / 3.20, OPERATOR-SET). Neither alone was enough: the
count change could not give House A its fifth axis while the floor stood at
2.70, because that arrangement needs 2.550 m.

House A now solves symmetrically, entrance on the centre axis, every bay on the
preferred pitch:

    pier_end 0.280 | 2.600 | 2.600 | porte cochère 3.040 | 2.600 | 2.600 | pier_end 0.280
    = 14.000 m, 5 axes

See `README.md` for the ladder and `dev/HANDOFF.md` for what remains open.

## The two patches, and why both were wrong

**`natural-count-nearest.patch`** — a naive floor→nearest swap. Its own guard
stepped back down whenever `run / n < bay.minimum`, which reverted it to
flooring on exactly the cases that mattered. Applied to House A it was a
**no-op**, and it cost 33 failures and 21 errors for nothing. The README that
recommended it also had its arithmetic wrong: it computed `10.60 / 2.80 = 3.79`
having forgotten to subtract the two end piers. The real division is
`9.90 / 2.80 = 3.54`.

**`pier-ratio-band.patch`** — clamped pier/window into the 0.8–1.5 band
directly. Treated the symptom. It did not change the count, so House A kept a
3.03 m pitch that no plate of that width shows.

## The bracket argument was also wrong

The case for 5 axes rested on interpolating operator-read plate counts:
12.4 m -> 4 axes and 15.0 m -> 5, so 14.0 m -> 5. The 12.4 m was a misreading of
119 Champs-Élysées; two independent measurements give 14.86 and 14.93 m.
Corrected, that anchor becomes 14.86 m -> 4 axes and points the other way.

A wider scan of all 16 elevations shows width does **not** determine axis count:
frontages of 14.2–15.1 m carry 4, 5, 6 and 7 axes. Five for a 14.0 m frontage is
well inside what Daly built and is the median for that band, but the plates do
not force it. See `dev/reference/daly_elevation_scan_2026-08-24.json`.

## Rules 3, 4 and 5 remain unimplemented

The operator's resolution order was: (1) adjust spacing, (2) add a module,
(3) symmetrical — piers narrower in the middle, wider at the ends, (4) inverse,
(5) if a pier still exceeds 1.5x, put something on it.

Only (1) and (2) exist. **(3) and (4) are not missing features — they are
inexpressible**: `_absorb` returns one end width and one bay width, so a facade
whose piers vary cannot be represented at all. That needs the object to become
*axis positions plus one window width*, with pitch and pier derived per
interval. `_absorb` is the seam.

Rule (5) makes a testable prediction nobody has checked: the plates whose piers
exceed 1.5x should carry something on them, and the ones under should not.
