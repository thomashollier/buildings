export const meta = {
  name: 'buildings-amendment-4',
  description: 'Fix the curtain-wall defect and the renderer/IR gaps standing between here and criterion 1',
  whenToUse: 'After S8/S9. Generated facades currently read as curtain wall; this is what fixes that.',
  phases: [
    { title: 'Correct', detail: 'opening geometry in qualification (opus), renderer + block render path (sonnet)' },
    { title: 'Gate', detail: 'independent verification, including LOOKING at the rendered output' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. S0-S9 are built; suite reports 1199 passed.

**Read \`Amendment 4\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Also read \`${ROOT}/dev/PLAN.md\` and the relevant parts of \`${OLD}/BRIEF.md\`.

## The problem, stated plainly
Generated facades currently render as **curtain wall**: every opening fills its entire bay, so
there is no masonry between, above or below the windows. The structure underneath is correct —
storeys taper, balcons filants land at the ordinance height, the cornice runs, the comble carries
dormers — but the result would make anyone who knows Paris flinch, which fails success criterion 1.

Python 3.11, frozen dataclasses, stdlib only. Suite green when you finish, with new tests.
Do not weaken a test to force a pass; delete deliberately and say why.
`

const VERDICT = {
  type: 'object',
  required: ['passed', 'checks'],
  properties: {
    passed: { type: 'boolean' },
    checks: { type: 'array', items: { type: 'object', required: ['name','passed','evidence'],
      properties: { name:{type:'string'}, passed:{type:'boolean'}, evidence:{type:'string'} } } },
    failures: { type: 'array', items: { type: 'string' } },
    design_problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Correct')

const [qualReport, renderReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/qualify/*\`, \`catalogue.py\`, \`compose.py\`,
\`terminate.py\` (the chimney base only), and their tests.

Implement **A4.1, A4.4, A4.7, A4.8**.

### A4.1 is the one that matters — an opening is not a bay
\`OpeningNode.props\` currently carries x/y/w/h **byte-identical to its parent BayNode**. Given
nothing else, the renderer invents a 0.10 m margin and glazes the whole bay. That is why every
facade reads as curtain wall.

This is an **IR gap and it must be fixed here**, in qualification — NOT in the renderer. Window
proportion is precisely the kind of thing a person can argue about, so per the brief it cannot live
in a renderer.

Emit opening **width, height and position within the bay slot**. Requirements:
- These are \`PROPORTIONAL\` quantities: they must move with class and role. A grand building's
  windows are much larger than a modest one's **while its door barely changes** — that contrast IS
  the absolute/proportional split, and it is what the eye reads as scale. Route the scaling through
  \`scale_for_class\`, the one sanctioned place.
- A Paris opening is a tall rectangle, roughly **1:1.7 to 1:2**, with a real pier either side and a
  spandrel below the sill. Take the pier from the bay's own filler width rather than inventing a margin.
- Vertical position must respect \`sill_height\`, which is \`ABSOLUTE\` — a sill is something a person
  leans on and does not scale with the building.
- Treatment diminishes with \`rank_from_principal\`: the noble floor's openings are the tallest, and
  they shorten upward. You already have that context; use it.
- Consult \`${OLD}/backends/svg.py\` around line 485 to see how the previous implementation centred
  a window in its bay. Reuse the idea, not the code.

### A4.4 — the chimney needs a visible base
\`SpecialNode\` chimney_stack carries \`y = eaves_height\` and \`h = ridge - eaves\` — its full section
extent — so the renderer draws a full-height bar over every roof. Emit where the stack actually
emerges from the roof surface.

### A4.7 — one fact, one name
Chamfer bays carry \`props['slot']\`; building bays carry \`props['slot_name']\`. A consumer keying on
\`slot_name\` reads None on a chamfer bay. Pick one and use it everywhere.

### A4.8 — assert the datum agreement
\`solve_structure\` silently prefers \`datums.street_width\` and ignores \`site.street_width\` when
they disagree — a latent second source of truth, the exact class of bug this project exists to
eliminate. Assert they agree, or document precisely why they may legitimately differ.

Coordinate: the other agent is making the renderer honour opening geometry, fixing the guard
evasion, and adding a block render path. Tell them the prop names you emit.`,
    { label: 'fix:opening-geometry', phase: 'Correct', model: 'opus' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/render/**\`, and its tests.

Implement **A4.2, A4.3, A4.5, A4.6**.

### A4.3 — stop routing around the guard. Do this one first, honestly.
\`elements.py\`'s own docstring admits it: *"no local variable is ever named after one of the guard's
forbidden tokens."* Two branches rename a forbidden token into a local and then branch on it:
- \`ornament_weight = _num(props,'richness',0.5)\` then \`if ornament_weight >= 0.7\` (~line 224,229)
- \`pattern = props.get('variant')\` then \`if pattern == ...\` (~line 335)

\`0.7\` is a **renderer-chosen threshold a person could argue about** — it does not belong here.
Move the threshold into qualification (coordinate with the other agent) so the IR carries a
resolved decision the renderer merely draws.

**Deliberately evading a guard is not acceptable anywhere in this repo.** If you think a guard is
wrong, say so in your report and propose changing it — do not rename around it. Remove that
docstring sentence and the pattern it describes. Do NOT edit \`dev/harness/check_renderer_dumb.py\`.

### A4.2 — honour \`sill_height\`
\`elements.py:100\` silently discards the IR's \`sill_height\` on every storey above the ground floor.
That is an ABSOLUTE quantity being ignored by the renderer, which inverts the project's central
rule. Honour it.

### A4.1 consumption — draw the opening the IR gives you
The other agent is emitting real opening width/height/position within the bay. Consume those
instead of inventing a 0.10 m margin and glazing the bay. **Do not fall back to bay geometry** if
the props are present. If they are absent, that is a bug worth failing loudly on rather than
papering over with a guess.

### A4.5 — corner buildings with an arc comble render as onion domes
Reported by the contact-sheet check. Diagnose and fix. A corner is a third short facade with its own
rhythm, not a dome.

### A4.6 — there is no render path for block output
\`render()\` assumes the node IS a \`BuildingNode\` and looks for \`storey\` children, so a \`parcel\`
node renders an empty 325-character SVG. Add a block path: a run of buildings drawn side by side on
one ground line with their shared cornice continuous across party walls. The block must read as
**one wall**, not a shelf of models — that is the entire point of the block being the unit.

### Verify visually, do not just assert
Render buildings, rasterise them (\`rsvg-convert -w 900 in.svg -o out.png\` is available), and
**look at the PNGs**. Iterate until a facade reads as masonry with windows in it rather than as
curtain wall. Save your best examples under \`${ROOT}/dev/logs/\`.`,
    { label: 'fix:renderer', phase: 'Correct', model: 'sonnet' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 4\` at the end of \`${ROOT}/dev/CONTRACTS.md\` — that is the spec.

Implementer claims (check, do not trust):
--- qualification ---
${(qualReport || '(none)').slice(0, 2200)}
--- renderer ---
${(renderReport || '(none)').slice(0, 2200)}
---

## Verify by running code AND by looking at images

1. **A4.1 — openings have their own geometry.** Assert \`OpeningNode\` x/y/w/h differ from the parent
   \`BayNode\`'s, over >=200 buildings. Report the opening:bay width ratio and the opening aspect
   ratio distribution — aspect should sit near 1:1.7–1:2. Assert a real pier either side and a
   spandrel below the sill.
2. **A4.1 — the absolute/proportional split is VISIBLE.** Generate modest→grand at a fixed year,
   street and parcel. Report door width and window area for each. **The door must barely change
   while the windows grow substantially.** If the door scales with the class, that is a hard
   failure — it is the doll's-house effect the brief exists to prevent. Give the actual numbers and
   the ratio between them.
3. **A4.2** — \`sill_height\` is honoured on upper storeys. Patch it and confirm the drawing moves.
4. **A4.3 — the guard evasion is gone.** Grep \`render/\` for the rename-then-branch pattern:
   any local assigned from a forbidden prop and then compared. Confirm the \`0.7\` threshold no
   longer lives in the renderer and that the docstring sentence describing the evasion is removed.
   **Confirm \`dev/harness/check_renderer_dumb.py\` is byte-unchanged** (sha256 it and compare
   against the mtime/content the earlier verifier recorded: it must still forbid year/date/era/
   period/klass/role/street_width/prevalence/variant). A guard edited to pass is a hard failure.
5. **A4.5** — render corner buildings with an arc comble; rasterise and LOOK. No onion domes.
6. **A4.6** — render a block of 8-12. Rasterise and LOOK. Report whether the cornice is continuous
   across party walls and whether it reads as ONE WALL. Save the PNG under \`dev/logs/\`.
7. **A4.7 / A4.8** — one prop name everywhere; the datum disagreement now asserts.
8. **LOOK AT A FACADE.** Render the harness building (20 m / 1865 / comfortable / shop), rasterise
   at >=900px, and view it. Judge honestly against a real Paris immeuble: is this masonry with
   windows in it, or is it still curtain wall? Be specific about what remains wrong. Save it to
   \`${ROOT}/dev/logs/facade_after_a4.png\`.
9. Full suite and both guards.

\`passed: true\` only if every item holds AND the facade genuinely no longer reads as curtain wall.
Remember the brief's rule: "that looks wrong" is strong evidence, "that looks right" is weak — so
be concrete about what you see rather than offering reassurance.`,
  { label: 'verify:amendment4', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

if (verdict && !verdict.passed) {
  log(`Amendment 4 gate FAILED: ${verdict.failures?.length || 0} defects — repairing`)
  const repair = await agent(
    `${PRE}

## The Amendment 4 fixes FAILED independent verification. Fix the root causes.

### Defects
${(verdict.failures || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

### Checks
${(verdict.checks || []).map((c) => `- [${c.passed ? 'PASS' : 'FAIL'}] ${c.name}: ${c.evidence}`).join('\n')}

Fix the underlying error. Do not weaken tests, and do not edit \`dev/harness/\` guards.
Rasterise and LOOK at the result before claiming it is fixed. Re-run the full suite.`,
    { label: 'repair:amendment4', phase: 'Gate', model: 'opus' }
  )
  return { wave: 'amendment-4', verdict, repaired: true, repair }
}

return { wave: 'amendment-4', verdict, repaired: false }
