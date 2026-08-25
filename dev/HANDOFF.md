# Where this stands — 2026-08-24

Read this first on a fresh session, then `dev/GLOSSARY.md` for the vocabulary and
`dev/CONTRACTS.md` for the binding spec.

## Repo state
- HEAD `5c9b7ad`, working tree clean, **1507 tests passing**, all three guards clean.
- Nothing in flight. Two unapplied patches are parked in `dev/logs/a24-wip/` with a
  README explaining what each does and why neither landed.

## The one open problem: the facade is under-divided

A 14.0 m frontage (House A) currently gets **4 axes** — one carriage door plus three
windows. The plates say a frontage that wide gets **5**. Everything the operator has
complained about downstream (piers too fat, rhythm too slack, windows too far apart)
falls out of that single miscount.

Full diagnosis, measurements, the operator's five resolution rules, and the two
candidate patches: **`dev/logs/a24-wip/README.md`**. That is the live document.

The short version: `_natural_count` in `src/buildings/solver/fitting.py` floors
`10.60 / 2.80 = 3.79` to 3. Nearest gives 4, which yields a 2.40 m pitch and a
pier/window ratio of 1.0 — matching the two Sebastopol plates. Costs ~29 test
rewrites. Not landed because the operator has not approved it.

## Two questions left on the table

**1. Is the 3.40 m door universal? No.**
There are two doors: *porte cochere* 3.40 m (street >= 12 m AND comfortable/grand)
and *porte pietonne* 2.35 m (everything else, and much commoner). House A gets the
carriage door because its street is 22 m and its class is comfortable.

The 3.40 decomposes as `2.60 clear + 2 x 0.40 jamb`. Those halves are not equally
sound:
- **2.60 is SOURCED and near-universal.** Daly measures 7 carriage doors,
  2.41-2.67; Premiere median 2.567, Deuxieme median 2.575 — two classes agreeing to
  **0.4%**. There is also a printed dimension on the 119 Champs-Elysees plate.
  A quantity that steady while everything else scales with money is a genuine
  absolute: it is about a vehicle, not a purse.
- **0.40 jamb is INFERRED.** Never measured. At 39 rue Neuve des Mathurins the door
  is 2.57 in a 3.02 pitch, implying roughly **0.22 m** per jamb — about half what we
  use. If that holds across the other six, the slot should be nearer **3.05** than
  3.40, and House A recovers 0.35 m before anything else changes. Unchecked. Cheap
  to check. Independent of the bay-count problem.

**2. What "corpus pitch" means — asked, answered here.**
It is the `bay_pitch` field in `dev/reference/daly_measurements.json`, defined there
as *"mean window-axis to window-axis spacing"*. Provenance:
- It came from an **earlier automated measuring pass** (`generated: 2026-08-21`,
  inputs `dev/logs/daly_measure_*.json`), not from anything done by hand in the
  current sessions, and not from me eyeballing the plates.
- The four numbers I measured *this* session — window, pier, pitch on plates 77,
  1, 39, 120 — were done differently: a programmatic pixel scan calibrated against
  each plate's own stated facade width. Those are in the A24 README.
- **The axis counts behind `bay_pitch` were never re-verified.** That matters: the
  operator counted 119 Champs-Elysees independently and got a width 2.5 m off ours.
  Treat `bay_pitch` as corroborating evidence, not as ground truth, and prefer a
  count read directly off the plate when the two disagree.

The record itself is honest about its limits and worth quoting before using it as a
class signal:

> `"2.81 / 2.85 / 2.54 m. Deuxieme sits ABOVE Premiere. The class ladder does not
> exist in this quantity."` — verdict, `bay_pitch.ladder`

So pitch is SOURCED as a corpus-wide range and **INSUFFICIENT** as a per-class
discriminator. Do not build a class ladder on it.

## How the operator wants to work
Stated directly this session, after a stretch where I moved too fast:
- Explain in plain terms before changing anything. Jargon ("rungs", "invariants")
  without definition is not communication.
- Work on **one building at a time**. Current focus is **House A** — 14.0 m wide,
  11.0 m deep, 22 m street, 1865, comfortable, shop ground floor, seed 8.
- Measure against the plates rather than against my own prose. Two reviews have
  already passed a form no plate supports because both compared the render to a
  written specification instead of to the drawing.
