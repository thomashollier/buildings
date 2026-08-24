# `dev/` — plan, harness, and execution record

Everything in here is *about* the build rather than part of the shipped system.
`src/` and `tests/` are the product; this directory is how it got made and how
it is held to account.

## Contents

| Path | What it is |
|---|---|
| `PLAN.md` | The execution contract: stages S0–S11, dependencies, and the verification gate each must pass |
| `CONTRACTS.md` | **The frozen interface contract.** Every agent codes against it; none may change it |
| `workflows/` | The orchestration scripts, one per build wave |
| `harness/` | Verification scripts — the guards, the fuzzer, the oracle diff, the VLM check |
| `reference/` | The scraped reference photo corpus and the selection review page |
| `logs/` | Verifier scratch scripts and generated reports |

## Why it is shaped this way

Three problems dominate multi-agent code generation, and each got a specific
countermeasure.

**Interface drift.** Agents working in parallel invent slightly different
versions of the same type and nothing composes. Countermeasure: `CONTRACTS.md`
is written before any code and frozen. An agent that thinks a signature is wrong
reports it and stops rather than adapting silently.

**Agreeable self-assessment.** An agent asked whether its own code works tends
to say yes. Countermeasure: every stage is gated by a **separate verifier agent**
that did not write the code, is told the implementer's report is a claim rather
than evidence, and must return concrete numbers from scripts it ran itself. A
skipped test counts as a failure, not a pass.

**Tests bent to fit the code.** The cheapest way to pass a gate is to weaken the
assertion. Countermeasure: the guard scripts (`check_no_period_branching.py`,
`check_renderer_dumb.py`) are written by the orchestrator, not by the agents they
police; repair prompts state explicitly that weakening a test is not an
acceptable fix; and the re-check pass is told to look for exactly that.

## Build waves

| Workflow | Stages | Gate highlights |
|---|---|---|
| `01_foundations.mjs` | S0 foundations, S1 fitting solver, S2 regulatory port | RNG independence; solver sweep over 720 widths; byte-diff of the ported règlement |
| `02_structure.mjs` | S3 structure, S4 roles, S5 chronology | height moves in *steps*; the base exclusion; zero period-enum branching |
| `03_qualification.mjs` | S6 qualification + composition, S7 termination | the mezzanine test; layering conflict raises; the 1884 roofline discontinuity |
| `05_render_block.mjs` | S8 renderer port, S9 block | renderer decides nothing arguable; one street width per block |
| `06_validation.mjs` | S10 validation harness, S11 VLM check | fuzz, oracle diff, contact sheets, reference comparison |
| `04_reference_corpus.mjs` | S11 corpus (runs in parallel from the start) | every image on disk, licensed, and provenance-recorded |

## Model tiering

Chosen per task rather than uniformly, to keep cost proportionate to difficulty:

- **haiku** — mechanical work: the règlement port, corpus verification
- **sonnet** — ordinary implementation, tests, scraping, the renderer port
- **opus** — the fitting solver, the rule model, the block, and **every verifier**

Verification is deliberately the most expensive tier. A cheap verifier that
misses a defect costs far more than it saves, because everything downstream is
built on top of the thing it waved through.

## The gates that matter most

Three checks are worth more than the rest combined, because each corresponds to
a failure the brief specifically warns about:

1. **The mezzanine test** (G4/G6) — remove the mezzanine and the balcony must
   move up a floor *by itself*, because the rule is about height above the
   pavement, not floor index. If this passes, derived roles and contextual
   qualification are genuinely working rather than being a table in disguise.

2. **One street width per block** (G9) — the previous attempt's silent failure.
   Buildings on the same street each sampled the width independently, their
   cornices did not line up, and *nothing errored*.

3. **Zero period-enum branching** (G5) — the moment a rule reads
   `period == SECOND_EMPIRE`, the straggler building that kept its ironwork for
   twenty years becomes unrepresentable, which is most buildings.

## Re-running

Workflows are re-invocable from their script path, and resumable:

```
Workflow({scriptPath: "dev/workflows/02_structure.mjs"})
Workflow({scriptPath: "...", resumeFromRunId: "wf_..."})   # cached prefix, only edits re-run
```

Guards and harness scripts run standalone:

```
python3 dev/harness/check_no_period_branching.py
python3 dev/harness/check_renderer_dumb.py
python3 -m pytest tests/ -q
```

- [Source register](reference/SOURCES.md) — Daly 1864 measured plates, the regulations, and the photographic corpus
