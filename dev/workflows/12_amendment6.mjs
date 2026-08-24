export const meta = {
  name: 'buildings-amendment-6',
  description: 'The entrance, the blind-panel stack, the chamfer roof, and the remaining drawing defects',
  whenToUse: 'Final build wave. A6.1 (no door anywhere) is the worst defect in the system.',
  phases: [
    { title: 'Correct', detail: 'entrance + specials (opus), chamfer roof + drawing defects (sonnet), guard extension (haiku)' },
    { title: 'Gate', detail: 'independent verification by looking at rasterised output' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const OLD = '/Users/thomas/Documents/claude/haussmann'

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris. S0-S9 built, 1238 tests passing, five amendments landed.

**Read \`Amendment 6\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.

Python 3.11, frozen dataclasses, stdlib only. Suite green when you finish.
Rasterise and LOOK (\`rsvg-convert -w 900 in.svg -o out.png\`) — do not claim a visual fix unseen.
Do not weaken tests. Do not edit \`dev/harness/check_renderer_dumb.py\` unless your task says to.
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

const [doorReport, drawReport, guardReport] = await parallel([
  () => agent(
    `${PRE}

## You own: \`src/buildings/typologies/paris/qualify/*\`, \`compose.py\`, \`catalogue.py\`,
\`structure.py\`, and their tests.

Implement **A6.1, A6.2, A6.5, A6.6, A6.7**.

### A6.1 — THERE IS NO DOOR. This is the worst defect in the system.
The harness ground storey is \`pier_end / shop / shop / shop / pier_end\` — three shops and **no way
into the building**. Across a 10-parcel block the opening census is
\`{window: 108, shop_bay: 27, blind_panel: 27, oeil_de_boeuf: 3}\` and not one entrance.

Every Paris immeuble has an entrance: a *porte cochère* on grander streets, a *porte piétonne* on
modest ones. It is the element the whole composition is organised around.

Read BRIEF.md's "Specials have position rules, not free slots" paragraph before writing anything.
The entrance is a **positional** problem:
> "The entrance is not 'one of the modules, anywhere.' It wants the centre, or a particular offset,
> and when it sits off-centre the composition should answer it — putting the narrow special on the
> opposite side, for instance. The grammar needs positional and symmetry constraints, not just a
> sequence of types."

Requirements:
- **Exactly one entrance per building**, always. Assert it.
- Placed by a positional rule — centre, or a stated offset — not by chance.
- \`ABSOLUTE\` in width and height. It is the ruler the eye measures the facade against, and A5.5
  already established that a porte cochère refuses rather than shrinks. Keep that.
- When it sits off-centre, the composition answers it.
- The choice between carriage and pedestrian entrance follows class and street width, via
  chronology/catalogue — not a literal.

### A6.2 — the leftover special becomes a stack of blind panels
Parcels carry a ~1.83 m \`special\` bay filled with a \`blind_panel\` on EVERY storey, pavement to
cornice — it reads as a walled-up building. The narrow special exists so the leftover is
architecturally *meaningful*. At ground level it is a strong candidate for the entrance; above, it
should vary — an œil-de-bœuf, a narrow window, a niche — not repeat one element five times.

### A6.5 — garde-corps are drawn across solid masonry
\`IronworkNode\`s span \`w = 3.450\` — the whole bay, piers included — in front of the solid allège
under a 1.322 m window. A garde-corps guards an **opening**: it is as wide as the opening.

### A6.6 — the mezzanine's ironwork has h = 0.000
Three \`IronworkNode\`s arrive with zero height and draw nothing. A rule emitting an element that
cannot be seen puts a lie in the IR. Either give it height or do not emit it.

### A6.7 — a pedimented surround over a shop light
Every ground-floor bay resolves \`surround_kind='pedimented'\`, emitting a bare triangle floating in
the enseigne band. Shop windows do not take pediments. Ground-floor surrounds come from the
shopfront vocabulary.

Coordinate prop names with the renderer agent.`,
    { label: 'fix:entrance-specials', phase: 'Correct', model: 'opus' }
  ),

  () => agent(
    `${PRE}

## You own: \`src/buildings/block/block.py\`, \`terminate.py\`, \`src/buildings/render/**\`,
and their tests.

Implement **A6.3, A6.4, A6.8, A6.9, A6.10**.

### A6.3 — the pan coupé has no roof
Both chamfer nodes carry storeys, string courses, balconies and a cornice, and **no roof child**;
\`render._draw_chamfer\` has no roof branch. Above each chamfer's cornice is bare sky, at both ends
of the block. The corner is the one place a Paris roof is most visible — often a *dôme* or a
distinct hipped section. Give the chamfer a roof, emitted in the IR like every other roof.

### A6.4 — chimneys float off the roof
Souches are placed at the silhouette apex for every parcel, but a hipped corner comble's drawn
surface falls away toward its ends, so stacks hang ~4 m clear of the tiles. A chimney emerges from
the roof surface **beneath it** — compute the surface height at the stack's own x.

### A6.8 — the devanture's head is stated and discarded
\`shop_bay\` openings carry \`head='segmental'\`, but \`draw_opening\` dispatches to
\`_draw_shop_light\` and returns before any head is drawn. The IR states a fact and the renderer
throws it away — the mirror of the A4.1 problem and just as wrong. Draw the stated head.

### A6.9 — the stall riser is 0.15 m
A real *soubassement* is 0.3–0.6 m of boarded or stone plinth. At 0.15 m the devanture reads as
glass meeting the ground. (Coordinate: the value should come from the IR, not a renderer literal.)

### A6.10 — the comble is one flat grey field
No zinc seam coursing and no visible break between *brisis* and *terrasson*, so the roof is a blank
rectangle occupying ~20% of the elevation. Zinc became the dominant Parisian roofing material
mid-century and its seam lines are a large part of how a Paris roof reads. Draw the seams and the
break. Keep it derived from the silhouette the IR gives you — do not re-derive roof geometry.`,
    { label: 'fix:roof-drawing', phase: 'Correct', model: 'sonnet' }
  ),

  () => agent(
    `${PRE}

## You own: \`dev/harness/check_renderer_dumb.py\` and \`dev/harness/\` hygiene ONLY.
Do not touch \`src/\`.

Implement **A6.11 (guard side) and A6.12**.

### A6.11 — extend the guard to catch renderer-side proportion arithmetic
Three separate waves have now found the same class of offence slipping past \`check_renderer_dumb\`,
because it inspects **names and enums**, not **arithmetic**:
- A4.3: \`ornament_weight = _num(props,'richness',0.5)\` then \`if ornament_weight >= 0.7\`
- A5.2: \`n = max(2, int(w / 1.4))\` — mullions at 1.5 m centres over 3.45 m structural bays
- A6.11: \`elements.py:300\` \`spacing = 0.5; n = max(1, int(w / spacing))\` for modillions

**This guard change is authorised** (normally agents may not edit guards; this task is the
exception, and it is scoped to you alone).

Add a check that flags renderer-side **proportion arithmetic**: a dimension read from the IR
(\`w\`, \`h\`, a span) divided or multiplied by a literal and used to decide **how many** of something
to draw — typically \`int(...)\`, \`round(...)\`, \`ceil(...)\`, or a \`range(...)\` bound.

Design it carefully to avoid false positives. Legitimate renderer arithmetic exists and must keep
passing: stroke widths, colour interpolation, converting metres to pixels, centring something, a
fixed inset. The offence is specifically **deciding a COUNT from a dimension and a magic number** —
that is a proportion decision and it belongs in qualification.

Report your false-positive analysis honestly. Run the guard against the current \`src/buildings/render/\`
and report what it flags. If the renderer agent has not yet moved the modillion count to the IR,
expect a genuine hit there — report it rather than tuning the guard until it passes.

Document the new rule in the module docstring, in the same voice as the existing one.

### A6.12 — hygiene
\`dev/harness/_render_a5_check.py\` is a scratch script left behind by an earlier wave. Read it; if
it does something worth keeping, promote it to a real harness entry point with a proper name and a
docstring. Otherwise delete it. Say which you did and why.`,
    { label: 'fix:guard-hygiene', phase: 'Correct', model: 'haiku' }
  ),
])

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write these fixes.
Read \`Amendment 6\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Claims (check, do not trust):
--- entrance/specials ---
${(doorReport || '(none)').slice(0, 1800)}
--- roof/drawing ---
${(drawReport || '(none)').slice(0, 1800)}
--- guard/hygiene ---
${(guardReport || '(none)').slice(0, 1200)}
---

## Verify by running code AND by looking

1. **A6.1 — THE DOOR.** Sweep >=500 buildings across all classes, street widths, ground programmes.
   Assert **exactly one entrance per building**, always — report the census and any building with
   zero or two. Then render a 10-parcel block and report its full opening census: every parcel must
   have an entrance. Confirm placement is positional (centre or a stated offset), not incidental,
   and that the entrance width/height do NOT change with class (ABSOLUTE). Rasterise and LOOK.
2. **A6.2** — assert no bay is filled with the same element on every storey. Report the worst
   remaining repeat.
3. **A6.3** — render a block with chamfered corners; assert chamfer nodes have a roof child.
   Rasterise and LOOK at both ends: is there a roof over the pan coupé?
4. **A6.4** — assert every chimney's base sits on the drawn roof surface at its own x. Report the
   worst gap in metres. LOOK at the block's corners.
5. **A6.5 / A6.6** — garde-corps width equals the opening width, not the bay; no IronworkNode has
   h == 0. Report distributions.
6. **A6.7 / A6.8** — no pediment over a shop light; the stated \`head\` is actually drawn for shops.
7. **A6.9 / A6.10** — stall riser in 0.3–0.6 m; the comble shows seam coursing and a brisis/terrasson
   break. LOOK — is the roof still a blank grey rectangle?
8. **A6.11 — the guard.** Read the extended \`check_renderer_dumb.py\`. Judge its false-positive
   design honestly: does it still pass legitimate renderer arithmetic (stroke widths, m→px, centring)
   while catching count-from-dimension? **Write your own small test cases both ways and run them.**
   Then run it against \`src/buildings/render/\` and report the result. A guard tuned until it passes
   is a FAIL — check whether the modillion count actually moved to the IR.
9. **Regression** — A4/A5 wins intact: door byte-identical across classes, window area ratio ~1.9x,
   no full-frontage glass rect, chamfers still pierced, porte cochère still 3.40 m or refused.
10. **Look at the whole thing.** Harness facade + 10-parcel block, rasterised >=900 px, saved to
    \`dev/logs/facade_final.png\` and \`dev/logs/block_final.png\`. Judge against a real Paris street
    and rank what remains. Be specific: "that looks wrong" is strong evidence, "that looks right"
    is weak.
11. Full suite and both guards.

\`passed: true\` only if every item holds.`,
  { label: 'verify:amendment6', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-6', verdict }
