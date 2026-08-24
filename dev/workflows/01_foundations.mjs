export const meta = {
  name: 'buildings-s0-s2',
  description: 'Stages S0-S2: foundations, fitting solver, regulatory port — each independently verified',
  whenToUse: 'First build wave. Everything downstream depends on these three landing correctly.',
  phases: [
    { title: 'Implement', detail: 'foundations (sonnet), fitting solver (opus), reglement port (haiku)' },
    { title: 'Verify', detail: 'independent verifier runs each stage gate; did not write the code' },
    { title: 'Repair', detail: 'only spawned for stages whose gate failed' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PREAMBLE = `You are implementing one stage of a ground-up rewrite of a procedural building
generator. The project thesis: **model the constraints and the style comes out for free.**

## Read these first, they are binding
- \`${ROOT}/dev/PLAN.md\` — the stage sequence and verification gates
- \`${ROOT}/dev/CONTRACTS.md\` — **the frozen interface contract**
- \`${OLD}/BRIEF.md\` — the design rationale (read the sections relevant to your stage)

## The contract is frozen
Code against the signatures in CONTRACTS.md exactly. Do not rename, do not "improve" a signature,
do not add a required parameter. Other agents are implementing other modules against the same file
right now — a unilateral change breaks them. If a signature in CONTRACTS.md is genuinely wrong or
impossible, implement the rest, and report the problem clearly in your return value. Do not silently adapt.

## Working rules
- Python 3.11. \`from __future__ import annotations\`. Public dataclasses \`frozen=True\`.
- No external runtime dependencies. Standard library only.
- Type-hint everything. Docstrings say WHY, not what.
- Run \`cd ${ROOT} && python3 -m pytest tests/ -q\` before you finish. Your own tests must pass and
  you must not break anyone else's.
- Only create/modify the files your stage owns. Do not touch other stages' files.
- \`src/buildings/**/__init__.py\` already exist; leave them alone unless your stage needs exports.

## The five invariants — yours to uphold, not aspirations
I1 phases read strictly backwards, no phase mutates what an earlier one read
I2 a building never samples a block-level fact, it receives it
I3 every quantity carries its kind: absolute / proportional / regulatory
I4 every emitted element records the rule that produced it
I5 seed + situation yields identical output, always
`

const STAGES = [
  {
    key: 'S0',
    label: 'foundations',
    model: 'sonnet',
    owns: 'src/buildings/{quantity,trace,rng,site}.py, src/buildings/ir/{nodes,serial}.py, tests/unit/test_{quantity,trace,rng,site,ir}.py',
    task: `## Stage S0 — Foundations

Build, exactly per CONTRACTS.md:

- \`src/buildings/quantity.py\` — \`Kind\`, \`Quantity\`, \`Abs\`, \`Prop\`, \`Reg\`, \`scale_for_class\`.
  The absolute/proportional/regulatory split is the thing that stops procedural buildings looking
  like toys. \`Abs\` never scales — a door is as tall as a person whether the building is grand or
  modest, and the door is the ruler the eye measures everything else against. \`Reg\` with an empty
  source raises. Mixed-kind arithmetic yields the MOST RIGID kind (ABSOLUTE > REGULATORY > PROPORTIONAL).
  \`scale_for_class\` is the ONE place proportional scaling happens.

- \`src/buildings/trace.py\` — \`RuleId\`, \`TraceEntry\`, \`TraceLog\`.
  Build this BEFORE the second rule exists. The brief is explicit that deferring the trace facility
  is how this whole approach dies: "you will spend weeks bisecting rule sets by hand and conclude the
  approach was a mistake." \`explain(node_id)\` must give a human a real answer to "why is this here?".

- \`src/buildings/rng.py\` — \`DecisionStream\`.
  **Addressability is the hard requirement.** Derive each path's state by hashing \`(seed, path)\`
  (use \`hashlib.blake2b\` over the encoded path plus seed, seed a \`random.Random\` from the digest).
  Do NOT draw from one shared sequence. The test that matters: adding a brand-new path must not
  perturb the value returned for any existing path. This is painful to retrofit, so get it right now.

- \`src/buildings/site.py\` — \`BuildingClass\`, \`GroundProgramme\`, \`SiteContext\`.
  Frozen, hashable, NO rng, no sampling methods. \`street_width\` is received, never chosen (I2).

- \`src/buildings/ir/nodes.py\` — \`Node\` plus the concrete kinds listed in CONTRACTS.md.
  \`trace\` is a non-empty tuple on every node (I4). Geometry: metres, origin at pavement level at
  the left edge of the parcel, +x right, +y up. Nodes with extent carry x/y/w/h in \`props\`.

- \`src/buildings/ir/serial.py\` — \`to_json\` / \`from_json\`, lossless including traces and
  node subclass identity, from day one.

Write unit tests in \`tests/unit/\` for all of it, including the RNG independence property and the
IR round-trip over every node kind.`,
    gate: `## Gate G0

Verify by RUNNING code, not by reading it:
1. \`Quantity\` arithmetic preserves/rejects kind mixing per contract; \`Abs\`/\`Reg\` ignore \`scaled()\`;
   \`Reg("")\` raises.
2. IR JSON round-trips losslessly for EVERY concrete node type, traces included. Construct one of
   each and assert \`from_json(to_json(n)) == n\`.
3. **RNG independence — the load-bearing one.** Record values for 50 existing paths; then request a
   brand-new path; then re-record the original 50 and assert every one is unchanged. Also assert
   same (seed,path) is stable across process restarts (run python twice, compare).
4. \`SiteContext\` is frozen (assignment raises) and hashable (usable as a dict key).
5. \`grep\` \`site.py\` for any import of \`random\` or \`rng\` — there must be none (I2).`,
  },
  {
    key: 'S1',
    label: 'fitting-solver',
    model: 'opus',
    owns: 'src/buildings/solver/fitting.py, tests/unit/test_fitting.py, tests/invariant/test_fitting_sweep.py',
    task: `## Stage S1 — The fitting solver

**This is the most important algorithm in the project.** Read BRIEF.md sections "The fitting problem"
and "The module model" in full before writing anything, plus "Absolute and proportional →
Practical consequences".

Build \`src/buildings/solver/fitting.py\` exactly per CONTRACTS.md: \`SlotKind\`, \`SlotSpec\`,
\`Rung\`, \`PlacedSlot\`, \`FitResult\`, \`solve()\`.

A facade is a row of modules that must EXACTLY fill a width which is never a whole multiple of the
module. The generic-layout-engine-with-a-cosmetic-gutter answer is the one to avoid. What makes this
one different: **the leftover is architecturally meaningful.**

Requirements, each of which is a real design decision and not a detail:

1. **Centreline bay units.** The repeating unit is the bay measured centreline-to-centreline of the
   filler: half-pier, opening, half-pier. So \`N\` bays is exactly \`N × bay_width\`, and the ONLY
   special case is the two ends — which is where you wanted it. If you make the opening the module
   and the pier the gap between modules, the ends become a special case that infects the whole run.

2. **Elasticity is per type, and that ordering IS the solver.** Absorb into the most elastic thing
   available. \`rigid=True\` slots (ABSOLUTE quantities — a carriage entrance must admit a carriage)
   NEVER absorb slack and always emerge at exactly \`preferred\`. Stretching a doorway to make the
   arithmetic work is precisely the move that destroys scale.

3. **The absorption ladder, in order** — climb only as far as needed:
   \`WIDEN_ENDS\` (interior rhythm stays perfect) → \`WIDEN_FILLER\` (uniformly) →
   \`WIDEN_BAY\` (toward maximum) → \`INSERT_SPECIAL\` → \`ADD_MODULE\`.
   **Rung 4 is the one that gets skipped and the one that makes it convincing.** Five good bays plus
   one narrow odd one reads far better than six squeezed bays. The special is a legitimate element —
   a half-bay, a blind panel, a small round window — not an apology for bad arithmetic.

4. **Parity.** With \`central_feature=True\`, \`ADD_MODULE\` steps the bay count by **2**, never 1,
   so it takes twice the slack to reach.

5. **Return an account of what it did.** \`FitResult.account\` is a tuple of human-readable steps,
   and \`rung\` is the highest rung climbed. This feeds the trace — someone must be able to ask the
   solver why a facade came out the way it did.

6. Exact fill: \`sum(widths) == budget\` within 1e-9. No slot outside [minimum, maximum]. Deterministic.

One solver serves BOTH axes — storeys into a height budget, bays into a width. Do not specialise it
to the horizontal case.

Tests: unit tests for each rung firing when it should, plus \`tests/invariant/test_fitting_sweep.py\`
sweeping widths 4.0–40.0 m and asserting the hard requirements everywhere.`,
    gate: `## Gate G1

Write and RUN an independent sweep — do not reuse the implementer's test file:
1. For widths 4.0→40.0 at 0.05 m steps: solve() terminates, \`residual < 1e-9\`,
   \`sum(widths) == budget\` to 1e-9, and NO slot falls outside [minimum, maximum]. Report the count
   of violations, not just pass/fail.
2. Include a \`rigid=True\` fixed slot (a carriage door) in the sweep and assert its width is
   EXACTLY \`preferred\` at every width. Any drift at all is a failure.
3. **Ladder monotonicity**: as slack grows within a fixed bay count, the rung used must not go
   backwards. Report any width where it does.
4. **Parity**: with \`central_feature=True\`, sweep and assert bay count only ever changes by 2.
5. **Centreline property**: with ends held at minimum, assert interior span is exactly
   \`n_bays × bay_width\`.
6. Determinism: solve the same input 100 times, assert identical results.
Report concrete numbers and the specific failing widths.`,
  },
  {
    key: 'S2',
    label: 'reglement-port',
    model: 'haiku',
    owns: 'src/buildings/typologies/paris/reglement.py, reglement_adapter.py, tests/unit/test_reglement.py, tests/oracle/test_reglement_diff.py',
    task: `## Stage S2 — Port the regulatory module UNCHANGED

This is a **mechanical port**, deliberately. The regulatory model is the one part of the previous
system that is fully demonstrated: it reproduces the documented 28.50 m ceiling exactly, and that
figure was not fitted to. Do not improve it, do not refactor it, do not "clean it up".

1. Copy \`${OLD}/core/reglement.py\` to \`${ROOT}/src/buildings/typologies/paris/reglement.py\`.
   Change **only** import statements so it resolves in the new package. Every number, every
   docstring, every citation stays byte-identical. If it imports from \`core.types\`, copy across
   only the minimum it needs (or inline those definitions) — but do not alter values.

2. Add \`${ROOT}/src/buildings/typologies/paris/reglement_adapter.py\` — a THIN wrapper exposing the
   same calls but returning \`Reg(value, citation)\` from \`buildings.quantity\` instead of bare floats.
   Citations come from the docstring at the top of reglement.py: the 1783/84 declarations, the 1823
   ordonnance (0.80 m projection, 6 m minimum height), the 1855 circulaire (block alignment), the
   1859 règlement (20 m facade, 2.60 m minimum storey), the 1882 decree (oriels), the 1884 Alphand
   decree (arc comble, the 28.50 m ceiling), the 1902 Bonnier decree. Every \`Reg\` gets a real
   citation string naming its source. The numeric core stays in reglement.py, untouched and
   byte-comparable to the original.

3. Copy \`${OLD}/tests/test_reglement.py\` across to \`${ROOT}/tests/unit/test_reglement.py\`,
   adjusting imports only, and make it pass.

4. Write \`${ROOT}/tests/oracle/test_reglement_diff.py\` — a DIFFERENTIAL test that imports the old
   module directly from \`${OLD}\` (add that path to \`sys.path\` inside the test; skip the test with
   \`pytest.importorskip\`-style guarding if the old repo is absent) and asserts the ported module
   returns identical results across a sweep of street widths (3–40 m) × years (1820–1910) for
   \`facade_height_limit\`, \`arc_radius\`, \`compute_envelope().total_height\`, and \`era_for_year\`.

5. Assert explicitly that the 1884 decree yields 20 m facade + 8.50 m comble = **28.50 m**, and that
   this comes from the source rather than being fitted.

Report anything you had to change beyond imports. "Nothing" is the expected answer.`,
    gate: `## Gate G2

1. Run the differential test. It must compare against \`${OLD}/core/reglement.py\` for real — confirm
   the old module actually imported and the test did NOT silently skip. Report how many
   (width, year) pairs were compared. A skipped oracle test is a FAILING gate.
2. \`diff ${OLD}/core/reglement.py ${ROOT}/src/buildings/typologies/paris/reglement.py\` — every
   differing line must be an import or a trivially-forced adaptation. **Report the actual diff.**
   Any changed numeric literal is a hard failure.
3. Assert the 28.50 m ceiling from the 1884 path.
4. Every \`Reg(...)\` in reglement_adapter.py has a non-empty citation naming a real decree/date.
   Grep and list them; flag any placeholder or generic string.`,
  },
]

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['stage', 'passed', 'checks'],
  properties: {
    stage: { type: 'string' },
    passed: { type: 'boolean', description: 'true ONLY if every check passed' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'passed', 'evidence'],
        properties: {
          name: { type: 'string' },
          passed: { type: 'boolean' },
          evidence: { type: 'string', description: 'concrete output/numbers, not a claim' },
        },
      },
    },
    failures: { type: 'array', items: { type: 'string' }, description: 'precise, actionable defects' },
    contract_problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Implement')

const results = await pipeline(
  STAGES,

  // 1. implement
  (stage) => agent(
    `${PREAMBLE}\n\n## Files you own\n\`${stage.owns}\`\n\n${stage.task}\n\n` +
    `When done, return a concise report: files written, anything you could not do, and any place ` +
    `CONTRACTS.md was wrong. Do not pad the report.`,
    { label: `impl:${stage.key}-${stage.label}`, phase: 'Implement', model: stage.model }
  ),

  // 2. verify — independent, did not write the code
  (implReport, stage) => agent(
    `You are an INDEPENDENT VERIFIER for stage ${stage.key} (${stage.label}) of the project at \`${ROOT}\`.
You did NOT write this code. Your job is to find out whether it actually works, not to be agreeable.

Read \`${ROOT}/dev/CONTRACTS.md\` for the contract this code must satisfy.

The implementer reported:
---
${(implReport || '(no report — the implementer may have failed)').slice(0, 3000)}
---
Treat that as a claim to be checked, not as evidence.

${stage.gate}

## How to verify
Write your own throwaway check scripts under \`${ROOT}/dev/logs/\` (prefix \`verify_${stage.key}_\`)
and RUN them. Run \`cd ${ROOT} && python3 -m pytest tests/ -q\` too. Evidence means actual output and
actual numbers. "The code looks correct" is not evidence and will not be accepted.

Mark \`passed: true\` ONLY if every single check passed. A test that skipped did not pass.
Be specific in \`failures\` — the repair agent gets only what you write there.`,
    { label: `verify:${stage.key}`, phase: 'Verify', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
  ),

  // 3. repair — only if the gate failed
  async (verdict, stage) => {
    if (!verdict) return { stage: stage.key, passed: false, note: 'verifier produced no verdict' }
    if (verdict.passed) {
      log(`${stage.key} ${stage.label}: gate PASSED`)
      return verdict
    }
    log(`${stage.key} ${stage.label}: gate FAILED — repairing (${verdict.failures?.length || 0} defects)`)

    const repair = await agent(
      `${PREAMBLE}\n\n## Stage ${stage.key} (${stage.label}) FAILED its verification gate. Fix it.\n\n` +
      `Files you own: \`${stage.owns}\`\n\n` +
      `### Defects found by the independent verifier\n` +
      (verdict.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n') +
      `\n\n### Full check results\n` +
      (verdict.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n') +
      `\n\n### Original stage requirements\n${stage.task}\n\n` +
      `Fix the ROOT CAUSE of each defect. Do not weaken or delete a test to make it pass — if a test ` +
      `is genuinely wrong, say so explicitly in your report and explain why. Re-run the checks ` +
      `yourself before finishing. Report what you changed and what now passes.`,
      { label: `repair:${stage.key}`, phase: 'Repair', model: stage.model === 'haiku' ? 'sonnet' : stage.model }
    )

    const recheck = await agent(
      `Re-verify stage ${stage.key} (${stage.label}) at \`${ROOT}\` after a repair pass.

The repair agent reported:
---
${(repair || '(none)').slice(0, 2500)}
---

Re-run the gate:
${stage.gate}

Also confirm the repair did not weaken or delete tests to force a pass — \`git diff\` the test files
if the repo has history, otherwise inspect them for suspiciously trivial assertions. Report honestly.`,
      { label: `recheck:${stage.key}`, phase: 'Repair', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
    )
    return recheck || { stage: stage.key, passed: false, note: 'recheck produced no verdict' }
  }
)

const final = results.filter(Boolean)
const failed = final.filter((r) => !r.passed)

log(`Wave 1 complete: ${final.length - failed.length}/${STAGES.length} gates passed`)

return {
  wave: 'S0-S2',
  passed: final.filter((r) => r.passed).map((r) => r.stage),
  failed: failed.map((r) => ({ stage: r.stage, failures: r.failures, note: r.note })),
  contract_problems: final.flatMap((r) => r.contract_problems || []),
  detail: final,
}
