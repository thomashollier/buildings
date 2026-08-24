export const meta = {
  name: 'buildings-amendment-1',
  description: 'Close the contract holes the wave-1 verifiers found, before wave 2 builds on them',
  whenToUse: 'Between waves 1 and 2. Each item is a defect a later stage would certainly hit.',
  phases: [
    { title: 'Fix', detail: 'foundations fixes (sonnet) and the solver parity narrowing (opus)' },
    { title: 'Gate', detail: 'independent re-verification of every amendment item' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PRE = `Project at \`${ROOT}\` — a constraint-derived procedural building generator for
19th-century Paris. Stages S0-S2 are built and their gates passed, but the independent verifiers
found holes in the CONTRACT itself.

**Read \`${ROOT}/dev/CONTRACTS.md\` — specifically "Amendment 1", at the end of the file.** Those
amendments are binding and override anything earlier that conflicts. Also read \`${ROOT}/dev/PLAN.md\`.

Python 3.11, \`from __future__ import annotations\`, frozen dataclasses, stdlib only.
\`cd ${ROOT} && python3 -m pytest tests/ -q\` currently reports 627 passed. It must still be green
when you finish, with your new tests added. Do not weaken an existing test to accommodate a change —
if one genuinely encodes the old wrong behaviour, say so explicitly in your report.
`

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['passed', 'checks'],
  properties: {
    passed: { type: 'boolean' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'passed', 'evidence'],
        properties: { name: { type: 'string' }, passed: { type: 'boolean' }, evidence: { type: 'string' } },
      },
    },
    failures: { type: 'array', items: { type: 'string' } },
    notes: { type: 'array', items: { type: 'string' } },
  },
}

phase('Fix')

const [foundReport, solverReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/quantity.py\`, \`src/buildings/ir/{nodes,serial}.py\`,
\`tests/unit/test_{quantity,ir}.py\`, \`tests/oracle/test_reglement_diff.py\`

Implement amendments **A1.1, A1.2, A1.3, A1.4, A1.5, A1.7**.

### A1.1 is the important one — the I3 hole
Right now \`Abs(2.60, "a carriage must pass") * 1.35\` returns an ABSOLUTE 3.51. That is a scaled
doorway, and it is exactly what the brief warns about:
> "If a quantity doesn't know what kind it is, someone will eventually scale a doorway, and nobody
> will be able to say why the result looks wrong — only that it does."

Scalar \`*\` and \`/\` on ABSOLUTE or REGULATORY must **raise TypeError**, with a message that names
the kind and points the caller at \`scale_for_class\`. PROPORTIONAL scalar arithmetic stays legal.
Check nothing already in the tree relied on the old behaviour; if something did, fix the caller.

### A1.4 — serialisation must be lossless for what the IR actually carries
Two concrete failures, both of which later stages WILL hit:
- \`SilhouetteNode(props={"points": ((0.0,0.0),(1.0,5.0))})\` round-trips tuples to lists, so
  \`from_json(to_json(n)) == n\` is False. S7 writes exactly this payload.
- \`to_json\` raises \`TypeError\` when a \`Quantity\` sits in \`props\` or \`TraceEntry.inputs\`.
  A qualification rule recording \`inputs={"limit": Reg(6.0, "ordonnance de 1823")}\` is an obvious
  and intended use of the trace facility — it must not crash.

Use a tagged encoding for \`Quantity\` so kind and citation survive, and restore tuples for nested
sequences on the way back in. Add round-trip tests covering both, and a property test over nested
structures.

### A1.5 — hashability
\`hash(Node(...))\` and \`hash(TraceEntry(...))\` raise because \`props\` is a \`mappingproxy\`.
Make them genuinely hashable via a frozen hashable mapping, and test putting nodes in a set.

### A1.2 / A1.3 — small but real
\`Reg(6.0, "   ")\` must raise. And mark the \`scale_for_class\` factors as INFERRED in the docstring —
they appear in no source and a later stage should replace them rather than inherit a placeholder.

### A1.7 — the oracle must not skip silently
\`tests/oracle/test_reglement_diff.py\` uses \`pytest.importorskip\`. If \`${OLD}\` is ever moved,
all 417 oracle tests skip and the suite still reports green — the vacuous-gate condition G2 exists
to prevent. Make a missing oracle a **hard failure** unless \`HAUSSMANN_ORACLE_OPTIONAL=1\` is set.
Verify by temporarily pointing it at a bad path that it now FAILS rather than skipping.`,
    { label: 'fix:foundations', phase: 'Fix', model: 'sonnet' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/solver/fitting.py\`, \`tests/invariant/test_fitting_sweep.py\`

Implement amendments **A1.6 and A1.8**.

### A1.6 — the parity fix over-corrected
An earlier repair made \`central_feature=True\` hold parity by requiring \`(n_bays + n_fixed)\` to be
odd BEFORE rung 4 (INSERT_SPECIAL) is tried. That was right in spirit and too strong in effect: it
makes "even bay count plus one special sitting on the axis" unreachable, so the solver now refuses
widths that have a perfectly good symmetric answer.

Concrete case, from the verifier:
\`\`\`
solve(8.05, end=0.20/0.40/0.75, bay=2.70/3.00/3.30,
      special=1.10/1.35/1.60, central_feature=True)  ->  FitInfeasible
but   end 0.40 | bay 3.00 | special 1.25 | bay 3.00 | end 0.40  =  8.05 exactly
      every slot in bounds, perfectly symmetric, special exactly on the axis.
\`\`\`
9 of 18 refusals for the \`central\` vocabulary and 21 of 42 for \`central_with_porte\` are of this
kind, **all at widths below 8.7 m** — narrow Paris parcels, which S3 will certainly hand it.

**The invariant that actually matters is that SOMETHING sits on the centreline** — not that the bay
count is odd. An even bay count with a lone central special satisfies it: the special IS the centre.
Accept that arrangement. Keep the property that a central composition always has an element on the
axis, and keep ADD_MODULE stepping by 2.

Note the related dead code the verifier flagged: the \`(2, 1)\` branch of \`_special_counts\` is
currently unreachable, and \`_place_specials\` at fitting.py:282 inserts the lone centre special at
\`len(out) // 2\`, which is off-centre for any odd-length run — contradicting its own docstring two
lines above. Reproduction: \`solve(10.90, end=0.45/0.50/0.60, bay=2.95/3.00/3.10,
special=0.90/1.00/1.20, central_feature=True)\` gives \`[e,b,s,b,b,e]\` — 1 bay left, 2 right.
Fix the placement so a declared central feature is genuinely centred.

Also fix \`test_every_refusal_is_genuinely_infeasible\`: it enumerates \`counts = (0,2) if central
else (0,1)\` and skips even \`(n + n_fixed)\`, i.e. it applies the SAME policy the implementation
does, so it structurally cannot detect this class of narrowing. Make it enumerate arrangements
independently of the implementation's policy — a refusal must be provably "poverty of vocabulary,
never a solver that gave up."

### A1.8 — the \`rigid\` flag is untested
Mutation M5 — changing \`SlotSpec.pinned\` from \`self.rigid or self.kind is SlotKind.FIXED\` to just
the latter — passes all 627 tests. No test constructs a rigid slot with a genuinely wide
\`[minimum, maximum]\` that is not already \`FIXED\`, so the flag itself is unproven. Add a test with
e.g. \`SlotSpec("quoin", FLEXIBLE, 0.30, 0.50, 1.20, rigid=True)\` asserting zero drift across a
sweep, and confirm it FAILS under the M5 mutation before you finish.`,
    { label: 'fix:solver', phase: 'Fix', model: 'opus' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read "Amendment 1" at the end of \`${ROOT}/dev/CONTRACTS.md\` — that is the spec.

Implementer claims (check them, do not trust them):
--- foundations ---
${(foundReport || '(none)').slice(0, 2000)}
--- solver ---
${(solverReport || '(none)').slice(0, 2000)}
---

Verify EVERY amendment item by running code, and report concrete evidence:

- **A1.1** \`Abs(2.6,"x") * 1.35\` raises TypeError; \`Reg(...) * 2\` raises; \`Prop(...) * 2\` works
  and returns PROPORTIONAL. Also \`/\`. Grep the whole \`src/\` tree for any surviving scalar
  multiplication of a rigid quantity.
- **A1.2** \`Reg(6.0,"   ")\` raises ValueError.
- **A1.3** the class factors are marked INFERRED in the docstring.
- **A1.4** \`from_json(to_json(n)) == n\` is True for a SilhouetteNode carrying a nested tuple
  polyline; and a \`Quantity\` in both \`props\` and \`TraceEntry.inputs\` round-trips with kind and
  citation intact. Show the actual values.
- **A1.5** \`hash(Node(...))\` works and a set of nodes behaves.
- **A1.6** THE IMPORTANT ONE. Confirm \`solve(8.05, ...)\` with the vocabulary named in the
  amendment now SUCCEEDS and returns a symmetric layout with an element on the axis. Then sweep
  4.0-40.0 at 0.05 m over several central vocabularies and report: how many refusals remain, and for
  each remaining refusal PROVE by independent brute force that no valid arrangement exists.
  Independently verify that every central composition has an element on the centreline, and that
  ADD_MODULE still steps by 2. Also re-run \`solve(10.90, ...)\` and confirm the central special is
  genuinely centred, not \`[e,b,s,b,b,e]\`.
- **A1.7** temporarily break the oracle's import path and confirm the test now FAILS rather than
  skipping; then confirm \`HAUSSMANN_ORACLE_OPTIONAL=1\` still lets it skip. Restore afterwards.
- **A1.8** apply mutation M5 to \`SlotSpec.pinned\` yourself and confirm the suite now FAILS.
  Restore afterwards. A test that does not fail under its own mutation is not a test.

Then run the full suite and both guards in \`dev/harness/\`.
\`passed: true\` only if every item is genuinely satisfied.`,
  { label: 'verify:amendment1', phase: 'Gate', schema: VERDICT_SCHEMA, model: 'opus', effort: 'high' }
)

if (verdict && !verdict.passed) {
  log(`Amendment gate FAILED: ${verdict.failures?.length || 0} defects — repairing`)
  const repair = await agent(
    `${PRE}

## The Amendment 1 fixes FAILED independent verification at \`${ROOT}\`. Fix the root causes.

### Defects
${(verdict.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Check results
${(verdict.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

Fix the underlying error. Do not weaken a test or edit \`dev/harness/\` guards to force a pass.
Re-run the failing checks and the full suite before finishing.`,
    { label: 'repair:amendment1', phase: 'Gate', model: 'opus' }
  )
  return { wave: 'amendment-1', verdict, repaired: true, repair }
}

return { wave: 'amendment-1', verdict, repaired: false }
