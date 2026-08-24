export const meta = {
  name: 'buildings-amendment-17',
  description: 'Retract the invented "absorbed" entresol; shop and pedestrian door stop at the RdC, only the carriage arch spans both',
  whenToUse: 'Operator caught that half of all commercial buildings carry a ground-floor treatment no plate supports.',
  phases: [
    { title: 'Correct', detail: 'remove the absorbed form; entresol gets its own short windows' },
    { title: 'Gate', detail: 'verifier must read the plate FIRST, in its own words' },
  ],
}

const ROOT = '/Users/thomas/Documents/claude/buildings'
const P77 = `${ROOT}/dev/reference/images/daly-1864/daly_elevation_03_blvd-sebastopol-77.jpg`
const P120 = `${ROOT}/dev/reference/images/daly-1864/daly_elevation_51_boulevard-sebastopol-120.jpg`

const PRE = `Project at \`${ROOT}\` — constraint-derived procedural building generator for 19th-century
Paris, calibrated against César Daly's 1864 measured plates.

**Read \`Amendment 17\` at the END of \`${ROOT}/dev/CONTRACTS.md\`.** Binding.
Read \`Amendment 13\` too — A17 retracts half of it, and you need to see what is being withdrawn
and what survives.

Repo: 1480 tests, three guards clean. Python 3.11, stdlib only.
Do not weaken tests. Do not edit any guard. Rasterise and LOOK.

## Note on how this was found
A13 invented a ground-floor treatment ("absorbed": a devanture spanning RdC + entresol as one
framework) and sourced it to plate 77. **The plate does not show that.** Two checks passed it
because both compared the render to the amendment's prose rather than to the plate. The operator,
who knows the buildings, caught it. Treat the plates as the specification here, not my description
of them.`

const VERDICT = {
  type: 'object',
  required: ['passed', 'checks'],
  properties: {
    passed: { type: 'boolean' },
    plate_reading: { type: 'string', description: 'what you SEE in the plates, in your own words, written BEFORE you look at the render' },
    checks: { type: 'array', items: { type: 'object', required: ['name','passed','evidence'],
      properties: { name:{type:'string'}, passed:{type:'boolean'}, evidence:{type:'string'} } } },
    failures: { type: 'array', items: { type: 'string' } },
    design_problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Correct')

const fix = await agent(
  `${PRE}

## First: open these two plates and look at them
- \`${P77}\` — 77 bd de Sébastopol
- \`${P120}\` — 120 bd de Sébastopol

Both are Deuxième Classe, 1864, Paul Mesnard, both with a measured entresol (RdC 4.00 + entresol
3.10). Look at the bottom of each before you touch code.

## You own
\`src/buildings/typologies/paris/qualify/*\`, \`compose.py\`, \`catalogue.py\`,
\`src/buildings/render/svg/elements.py\` (consumption only), and their tests.

Implement **A17.1, A17.2, A17.3**.

### A17.1 — the generic ground floor
| element | height |
|---|---|
| shop window | the **rez-de-chaussée only**, stopping at the entablature |
| entresol window | its **own short window** above that line, with a garde-corps |
| porte piétonne | the **rez-de-chaussée only**, with a carved overpanel |
| porte cochère | **rises to the top of the entresol** — the two-storey arch of A14 |

The asymmetry is the whole point: the **carriage** entrance is the one opening that spans both
levels, because a carriage must pass under the entresol floor. A pedestrian door does not, and
neither does a shop window.

Note A14 currently offers the two-storey arch to BOTH door kinds as a ~25% draw. Under A17 the
carriage arch spanning the entresol is the NORM, not a coin-flip, and the pedestrian two-storey
arch should become rare or go entirely — Daly's two pedestrian examples (2 et 4 and 87 bd de
Sébastopol, 5.01 / 5.07 m) are real, so keep it reachable but as the exception. Say what you chose
and why.

### A17.2 — delete the absorbed form
Remove it, do not down-weight it. It is not a rare variant we over-produce; it is one we invented.
What survives as real variation is the entresol window's **head form** — rectangular (plate 77) or
segmental (plate 120) — drawn through \`DecisionStream\` exactly as A13.2 already does, rate INFERRED.

### A17.3 — keep what A13 got right
Do **not** undo these; plate 77 shows both:
- the socle runs through the entresol — RdC + entresol are one bossage-coursed block
- the emphatic string course crowns the base block, above the entresol, not above the RdC

Only the opening treatment was wrong.

Verify by rendering layout A and putting it beside plate 77 at matching scale. Rasterise and LOOK.`,
  { label: 'fix:entresol-openings', phase: 'Correct', model: 'opus', effort: 'high' }
)

phase('Gate')

const verdict = await agent(
  `INDEPENDENT VERIFIER at \`${ROOT}\`. You did not write this fix.

## Do this FIRST, before reading anything else
Open \`${P77}\` and \`${P120}\` and **look at the bottom two levels of each**. Write into
\`plate_reading\` what you actually see, in your own words:
- how tall is the shop window — does it stop at a line, or run up past it?
- does the entresol have its own windows? what shape are their heads? any garde-corps?
- how tall is the pedestrian door relative to the shop windows?
- is there a carriage arch, and if so how far up does it go?

**Write that before you look at the generated output.** The last two reviews of this feature both
passed a form no plate supports, because both compared the render to a written specification
instead of to the plate. Your reading of the plate is the specification.

Then read \`Amendment 17\` at the end of \`${ROOT}/dev/CONTRACTS.md\`.

Implementer claim (check, do not trust):
---
${(fix || '(none)').slice(0, 2200)}
---

## Verify
1. **Does the render match YOUR plate reading?** Render layout A (shop) and layout AC (carriage),
   rasterise at >=900 px, and put each beside plate 77. State concretely where they agree and differ.
2. **A17.1 heights.** From the IR, over >=200 buildings: assert every shop-bay opening's height
   equals the RdC storey height (less reveals), NOT RdC + entresol. Assert every entresol opening is
   its own short window. Assert porte piétonne height is within the RdC. Assert porte cochère spans
   RdC + entresol. Report the distributions.
3. **A17.2 absorbed is gone.** Grep the tree for the absorbed treatment and confirm it is deleted,
   not merely weighted to zero. Confirm entresol head form still varies (rectangular / segmental)
   through DecisionStream with the rate INFERRED.
4. **A17.3 survives.** Assert the socle still spans RdC + entresol as one block, and the emphatic
   string course still sits ABOVE the entresol. Report both string-course depths.
5. **A14 not broken.** Entrance widths still byte-identical across forms (2.60 carriage / 1.75
   pedestrian). Confirm the two-storey pedestrian arch is still reachable but now the exception.
6. **A16 not broken.** If A16 has landed, the canonical stack must still be reachable at 95-100%
   of the ceiling. Report the cornice percentage for a 22 m street shop building.
7. Full suite and all three guards; confirm none was edited.
8. **LOOK at the whole sheet.** Re-run \`python3 ${ROOT}/dev/harness/tile_sheet.py\` and inspect
   \`dev/logs/tiles/presets.png\`. Report what changed on every tile.

\`passed: true\` only if the render matches YOUR reading of the plates and the repo is green.`,
  { label: 'verify:amendment17', phase: 'Gate', schema: VERDICT, model: 'opus', effort: 'high' }
)

return { wave: 'amendment-17', verdict }
