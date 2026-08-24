# Invariant fuzzer report

Cases run: **3000**
- generated successfully: 3000
- refused as infeasible (`FitInfeasible`): 0
- raised an unexpected exception: 0
- wall time: 111.9 s

## Harness self-check (is the fuzzer actually fuzzing?)

- distinct street widths: 72 (range 6.00-40.00)
- distinct parcel widths: 71 (range 5.00-30.00)
- distinct years: 50 (range 1820-1910)
- classes present: ['comfortable', 'grand', 'modest', 'ordinary']
- ground programmes present: ['cafe', 'carriage', 'office', 'residential', 'shop']
- corner values present: [False, True]
- distinct seeds: 3000 of 3000 cases

- Checker negative controls (synthetic broken input, not from `generate()`):
- `check_bays_fill_parcel_exactly (bays sum wrong)`: PASS (caught the injected violation)
- `check_storey_minimum (storey under the 1859 minimum)`: PASS (caught the injected violation)
- `check_no_nan_negative_zero (NaN width + negative height)`: PASS (caught the injected violation)
- `check_silhouette_within_envelope (point pushed 5 m above the envelope)`: PASS (caught the injected violation)
- `Node.__post_init__` (I4): PASS (raises on empty trace, as documented)
- seed-variation groups sampled: 75, of which 30 showed >1 distinct rendered output across 5 alternate seeds

## Result: NO FAILURES FOUND

Every case in the sweep generated without raising, every I1-I5 check held, and every structural sanity check held. Per the task brief: a fuzzer that finds nothing on the first run of an unproven design is more likely broken than the design is perfect, so this result should be treated with suspicion rather than as a clean bill of health. The harness self-check above is the evidence that the sample really is varying every input axis and that assertions really are running (rather than, say, silently catching everything and asserting nothing) — read it before trusting this line.
