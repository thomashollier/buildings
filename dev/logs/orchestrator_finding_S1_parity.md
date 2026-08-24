# Orchestrator finding — S1 solver, central-feature parity

Found by an independent sweep run by the orchestrator, outside the workflow's own
verification pass.

## The claim

`CONTRACTS.md` states: *"`central_feature=True` ⇒ bay count changes by 2 on
`ADD_MODULE`, never 1."*

The solver honours this **on the `ADD_MODULE` rung only**. It does not hold as a
property of the solve as a whole.

## Evidence

Sweeping width 6.0→40.0 m at 0.05 m with `central_feature=True`:

```
13 transitions where bay count changed by 1
  at  6.5m: 1 -> 2 bays   rung=EXACT
  at  9.2m: 2 -> 3 bays   rung=EXACT
  at 11.9m: 3 -> 4 bays   rung=EXACT
  at 14.6m: 4 -> 5 bays   rung=EXACT
  ...
parities observed in the result set: {even, odd}
```

Every violation occurs at `rung=EXACT`, at widths that are exact multiples of the
preferred bay width (2.70 m). When an exact fit exists the solver takes it and
never consults the parity constraint.

## Why it matters architecturally

A central feature needs a **centre bay** to sit in. That requires an odd bay
count. Because the solver emits both parities, roughly half of all frontages
produce a building whose central entrance has no middle bay to occupy — it lands
on a pier.

The brief is explicit that this is not a detail:

> "Specials have position rules, not free slots. The entrance is not 'one of the
> modules, anywhere.' It wants the centre... The grammar needs positional and
> symmetry constraints, not just a sequence of types."

And on the ladder:

> "If the composition has a central feature, step 5 usually jumps by **two**
> modules, so it takes twice the slack to reach."

The two-step jump is the *mechanism*; preserving the centre is the *purpose*. The
current implementation has the mechanism without the purpose.

## The fix

Parity must be an invariant of the whole solve when `central_feature=True`, not a
rule attached to one rung: candidate bay counts of the wrong parity are excluded
before rung selection, including on `EXACT`. Rejecting an exact fit in favour of
a slightly-absorbed odd fit is the correct trade — that is precisely what the
absorption ladder exists to do.

## Not a defect

An earlier sweep suggested `INSERT_SPECIAL` never fires. That was an artefact of
the test parameterisation: ends with a 0.30–1.60 m range absorb every remainder
before the special is ever needed. With realistic ends (0.30–0.55 m) the rung
fires 25 times across the same sweep, placing a genuine narrow special:

```
 6.00m -> [end 0.55, bay 3.40, special 1.50, end 0.55]
 7.95m -> [end 0.525, bay 2.70, bay 2.70, special 1.50, end 0.525]
```

The solver is correct here.
