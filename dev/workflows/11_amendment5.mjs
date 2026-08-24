export const meta = {
  name: 'buildings-amendment-5',
  description: 'Fix the eye-level defects: shopfront curtain wall, invented mullion rhythm, blank pan coupe',
  whenToUse: 'Final correction wave before validation. These are the last things that would make a viewer flinch.',
  phases: [
    { title: 'Correct', detail: 'shopfront per bay + carriage clear height (opus), chamfer facade + renderer (sonnet)' },
    { title: 'Gate', detail: 'independent verification, by looking at rasterised output' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. S0-S9 built, suite reports 1232 passed.

**Read \`Amendment 5\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

## Where the project stands
Amendment 4 succeeded at the thing that mattered: openings have their own geometry, and the
absolute/proportional split is visible — across modest→grand the porte cochère stays 3.000×3.000 m
byte-identical while mean window area grows 1.836→3.551 m² (1.93x). Storeys 1-4 now read as masonry
with windows cut into it, and a block renders as one wall with a continuous cornice.

What remains is concentrated at **eye level**, which is where a viewer looks first.

Python 3.11, frozen dataclasses, stdlib only. Suite green when you finish.
Rasterise and LOOK at your output (\`rsvg-convert -w 900 in.svg -o out.png\`) — do not claim a
visual fix you have not seen.
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

const [shopReport, chamferReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/qualify/*\`, \`compose.py\`, \`catalogue.py\`,
\`structure.py\` (ground-storey height only), and their tests.

Implement **A5.1, A5.2 (IR side), A5.5**.

### A5.1 — the shopfront belongs to the BAY, not the frontage
\`compose.py\` (~645-668) emits a \`ShopfrontNode\` with \`x=0.0, w=facade_w\` — the whole frontage —
and \`render._draw_storey\` draws it BEFORE the bays. So the renderer glazes 0→12 m in one rect and
paints over masonry you had already carved correctly: each shop bay is 2.645 m inside a 3.45 m bay
with 0.4025 m piers, leaving 0.805 m of pier between shops.

**A4.1 was implemented correctly and then obliterated by a node drawn on top of it.** That is the
single most visible remaining defect, and it is at eye level.

Emit **one shopfront per shop bay**, respecting the piers. A Paris *devanture* has a stall riser
below, a fascia above, and real masonry between shops — the pier between two shops is structural,
and it is what stops the ground floor reading as a glass band.

Where several adjacent bays are one shop, they may share a fascia — but the piers stay.

### A5.2 (IR side) — state the pane rhythm
\`elements.draw_shopfront\` currently invents \`n = max(2, int(w / 1.4))\`, giving mullions at 1.5 m
centres over a facade whose structural bays are at 3.45 m centres — the decorative rhythm
contradicting the structural one. Emit the mullion/pane rhythm in the IR so the renderer does not
have to guess. Coordinate the prop names with the other agent.

### A5.5 — a carriage entrance a carriage cannot pass is a structural failure
44/44 sampled portes cochères come out 3.00 × 3.00 m — square — because height is capped by
\`slot_h - lintel_bearing_depth\`, well below the 3.40 m \`carriage_clear_height\` the catalogue
itself declares. The ABSOLUTE constraint is being silently overridden by storey height.

That inverts the project's central rule in the least forgivable place. If the clear height cannot
be met, the ground storey is too short for the programme it carries: **either raise the storey, or
refuse the combination loudly.** Do not silently emit a door a carriage could not pass through.

(The full-slot width with no pier either side is a stated design position — "the opening IS that
slot" — and is defensible. Keep it, but say so explicitly in a docstring.)`,
    { label: 'fix:shopfront-carriage', phase: 'Correct', model: 'opus' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/block/block.py\`, \`src/buildings/render/**\`, and their tests.

Implement **A5.4, A5.2 (renderer side), A5.3**.

### A5.4 — the pan coupé is a blank wall
\`block.py\` (~1341) builds chamfer bays with \`x/y/w/slot_name\` and **no children**, and
\`render._draw_chamfer\` (~366-376) handles bay/cornice/string_course/balcony but has no opening
branch. So every chamfered corner in a block renders as an unpierced blank wall — plainly visible
at both ends of \`dev/logs/block_a4_verify.png\`.

The brief is explicit: a chamfered corner *"becomes a third short facade with its own rhythm"* —
it is the join between two grammars and needs its own concept, not a slot in the row. Give it its
own bay solve and its own qualified openings, exactly as any other facade gets. Reuse the existing
solver and qualification path rather than writing a parallel one.

### A5.2 (renderer side) — stop inventing a rhythm
Remove \`n = max(2, int(w / 1.4))\` from \`draw_shopfront\`. Consume the pane rhythm the other agent
emits in the IR. \`check_renderer_dumb\` does not catch this today (no forbidden token in the
expression), but it is the same offence as A4.3: a renderer deciding proportion.

If you think the guard should be extended to catch renderer-side proportion arithmetic, **propose
it in your report** — do not edit \`dev/harness/check_renderer_dumb.py\` yourself.

### A5.3 — the ghost frame
The full-width glass band sits at \`y=1296.62 h=213.63\` while the shop-bay openings drawn over it
sit at \`y=1288.66 h=242.04\` — misregistered by 8 px vertically and 28 px in height, so every
shopfront shows a ghost frame offset from its glass. Fixing A5.1 should remove the double-draw;
**confirm by looking, rather than assuming.**

### Verify visually
Render the harness building (20 m / 1865 / comfortable / shop) and a 10-parcel block with corners,
rasterise both, and look. Save to \`${ROOT}/dev/logs/facade_after_a5.png\` and
\`${ROOT}/dev/logs/block_after_a5.png\`.`,
    { label: 'fix:chamfer-renderer', phase: 'Correct', model: 'sonnet' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 5\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Implementer claims (check, do not trust):
--- shopfront/carriage ---
${(shopReport || '(none)').slice(0, 2000)}
--- chamfer/renderer ---
${(chamferReport || '(none)').slice(0, 2000)}
---

## Verify by running code AND by looking

1. **A5.1** — assert no node spans the full frontage on a shop ground floor. Grep the emitted SVG
   for a single rect whose width equals the facade width. Confirm one shopfront per shop bay and
   that the 0.805 m masonry piers between shops SURVIVE into the rendered output. Rasterise and
   LOOK: is the ground storey masonry-with-shops-in-it, or still a glass band? Be concrete.
2. **A5.2** — confirm \`n = max(2, int(w / 1.4))\` is gone and the pane rhythm comes from the IR.
   Then scan \`render/\` for any OTHER invented proportion arithmetic of the same class (a divisor
   or multiplier deciding how many of something to draw) and report what you find, whether or not
   the guard catches it.
3. **A5.3** — confirm the ghost frame is gone by inspecting actual y/h values, then by looking.
4. **A5.4** — render a block with chamfered corners. Assert chamfer bays now have opening children.
   Rasterise and LOOK at both ends: is the pan coupé a real short facade with windows, or still
   blank? Report the chamfer's bay count and opening dimensions.
5. **A5.5** — sweep carriage-entrance buildings. Assert every emitted porte cochère either meets
   \`carriage_clear_height\` (3.40 m) or the combination was refused loudly. Report the height
   distribution and the count of refusals. A silently-square 3.00 m door is a FAIL.
6. **Regression** — re-confirm A4's win still holds: modest→grand, door byte-identical, window area
   ratio ~1.9x. If A5 broke it, that is a hard failure.
7. **Look at the whole thing.** Render the harness facade and a 10-parcel block, rasterise at
   >=900px, and judge honestly against a real Paris street. Save to \`dev/logs/facade_after_a5.png\`
   and \`dev/logs/block_after_a5.png\`. List what a knowledgeable viewer would still flinch at,
   ranked. "That looks wrong" is strong evidence; "that looks right" is weak — so be specific.
8. Full suite and both guards.

\`passed: true\` only if every item holds.`,
  { label: 'verify:amendment5', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-5', verdict }
