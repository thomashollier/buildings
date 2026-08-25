# Frozen Interface Contract

**Every agent building this system codes against this file and may not change
it.** If a signature here is wrong, the agent reports the problem and stops; it
does not silently adapt. This is what keeps parallel implementation from
drifting.

Python 3.11+. `from __future__ import annotations` everywhere. All public
dataclasses `frozen=True` unless stated. No external runtime dependencies.

---

## `buildings.quantity`

```python
class Kind(Enum):
    ABSOLUTE = "absolute"        # human body / object that must pass. Never scales.
    PROPORTIONAL = "proportional"  # composition and money. Scales.
    REGULATORY = "regulatory"    # a number in a law. Changes on a date.

@dataclass(frozen=True)
class Quantity:
    value: float
    kind: Kind
    why: str                 # absolute/proportional: the reason. regulatory: the citation.
    def __float__(self) -> float: ...
    def scaled(self, factor: float) -> Quantity:
        """PROPORTIONAL scales. ABSOLUTE and REGULATORY return self unchanged."""
    @property
    def rigid(self) -> bool:  # True for ABSOLUTE and REGULATORY
        ...

def Abs(value: float, why: str) -> Quantity: ...
def Prop(value: float, why: str) -> Quantity: ...
def Reg(value: float, source: str) -> Quantity: ...   # source must be non-empty

def scale_for_class(q: Quantity, klass: BuildingClass) -> Quantity:
    """The ONE place proportional scaling happens. Called nowhere else."""
```

Rules: `Reg` with an empty `source` raises `ValueError`. Arithmetic between two
`Quantity` of different `Kind` returns a `Quantity` whose kind is the *most
rigid* of the two (ABSOLUTE > REGULATORY > PROPORTIONAL).

---

## `buildings.trace`

```python
RuleId = str        # stable dotted id, e.g. "paris.qualify.balcony.ordonnance_1823"

@dataclass(frozen=True)
class TraceEntry:
    rule: RuleId
    phase: str                  # "structure" | "roles" | "qualification" | "termination"
    detail: str                 # human-readable: what it decided and why
    inputs: Mapping[str, object] = field(default_factory=dict)

class TraceLog:
    def record(self, node_id: str, entry: TraceEntry) -> None: ...
    def explain(self, node_id: str) -> list[TraceEntry]: ...
    def all_ids(self) -> list[str]: ...
```

Every emitted IR node carries `trace: tuple[TraceEntry, ...]` — **non-empty**.
A node with an empty trace is a bug and `test_trace_completeness` fails on it.

---

## `buildings.rng`

```python
class DecisionStream:
    def __init__(self, seed: int) -> None: ...
    def at(self, path: str) -> random.Random:
        """Independent, decorrelated stream keyed by a stable path.
        Same (seed, path) => same sequence, forever.
        Adding a NEW path must not perturb any existing path."""
    def choice(self, path: str, options: Sequence[T], weights: Sequence[float] | None = None) -> T: ...
    def uniform(self, path: str, lo: float, hi: float) -> float: ...
```

Implementation must derive per-path state by hashing `(seed, path)` — **not** by
drawing from one shared sequence.

---

## `buildings.site`

```python
class BuildingClass(Enum):
    MODEST = "modest"; ORDINARY = "ordinary"; COMFORTABLE = "comfortable"; GRAND = "grand"

class GroundProgramme(Enum):
    RESIDENTIAL = "residential"; SHOP = "shop"; CAFE = "cafe"; CARRIAGE = "carriage"; OFFICE = "office"

@dataclass(frozen=True)
class SiteContext:
    street_width: float          # metres, HANDED DOWN by the block (I2)
    parcel_width: float
    parcel_depth: float
    year: int
    klass: BuildingClass
    ground: GroundProgramme
    corner: bool = False
    seed: int = 0
```

`SiteContext` holds **no RNG and no methods that sample**. A building receives
`street_width`; it never chooses it.

---

## `buildings.solver.fitting`

The generic 1-D budget solver. One solver serves both axes.

```python
class SlotKind(Enum):
    FIXED = "fixed"          # exactly `preferred`; never absorbs (use for ABSOLUTE)
    REPEATING = "repeating"  # the bay; count may change
    FLEXIBLE = "flexible"    # filler and ends; absorbs first

@dataclass(frozen=True)
class SlotSpec:
    name: str
    kind: SlotKind
    minimum: float
    preferred: float
    maximum: float
    elasticity: float = 1.0   # higher absorbs sooner. ends > filler > opening > door
    rigid: bool = False       # True for ABSOLUTE-kind: NEVER absorbs slack

class Rung(Enum):
    """The absorption ladder, in order. Recorded for the trace."""
    EXACT = 0            # no slack
    WIDEN_ENDS = 1
    WIDEN_FILLER = 2
    WIDEN_BAY = 3
    INSERT_SPECIAL = 4   # narrow special: half-bay, blind panel, oeil-de-boeuf
    ADD_MODULE = 5

@dataclass(frozen=True)
class PlacedSlot:
    name: str
    kind: SlotKind
    start: float
    width: float
    is_special: bool = False

@dataclass(frozen=True)
class FitResult:
    slots: tuple[PlacedSlot, ...]
    rung: Rung                    # the highest rung the solver had to climb
    account: tuple[str, ...]      # what it did, step by step, for the trace
    residual: float               # must be < 1e-9

def solve(
    budget: float,
    *,
    end: SlotSpec,
    bay: SlotSpec,
    special: SlotSpec | None = None,
    fixed: Sequence[tuple[int, SlotSpec]] = (),   # (index_hint, spec) e.g. carriage door
    central_feature: bool = False,                # parity: ADD_MODULE steps by 2
    min_bays: int = 1,
    max_bays: int = 24,
) -> FitResult: ...
```

**Hard requirements:**
- `sum(s.width for s in slots) == budget` to within 1e-9
- No slot outside `[minimum, maximum]`
- `rigid=True` slots always emerge at exactly `preferred`
- Bays measured **centreline to centreline**: `N` bays is exactly `N × width`;
  only the two ends are special-cased
- `central_feature=True` ⇒ bay count changes by 2 on `ADD_MODULE`, never 1

---

## `buildings.ir.nodes`

```python
@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    trace: tuple[TraceEntry, ...]        # NON-EMPTY (I4)
    children: tuple[Node, ...] = ()
    props: Mapping[str, object] = field(default_factory=dict)

# Concrete kinds (all subclass Node, all frozen):
# BuildingNode, StoreyNode, BayNode, OpeningNode, SurroundNode, BalconyNode,
# CorniceNode, StringCourseNode, SocleNode, ShopfrontNode, RoofNode,
# DormerNode, SilhouetteNode, IronworkNode, KeystoneNode, SpecialNode
```

Geometry convention: **metres, origin at pavement level at the left edge of the
parcel, +x right, +y up.** Every node with extent carries `x`, `y`, `w`, `h` in
`props`.

## `buildings.ir.serial`

```python
def to_json(node: Node) -> str: ...
def from_json(s: str) -> Node: ...
```

Round-trip must be lossless including traces. Tested from day one.

---

## `buildings.typologies.paris.reglement`

**Ported unchanged** from `../haussmann/core/reglement.py`. Public surface kept
exactly:

```
Era, RoofEnvelope, Reglement, GabaritEnvelope, BalconyRule, OrielRule
era_for_year(year) -> Era
get_reglement(era) -> Reglement
compute_envelope(...) -> GabaritEnvelope
balcony_rule(...), oriel_rule(...)
Reglement.facade_height_limit(street_width), .arc_radius(street_width)
GabaritEnvelope.total_height, .setback_at(h), .max_height_for_setback(inset),
                .slope_profile(samples), .mansard_angles()
```

Only permitted changes: import paths, and returning `Reg(v, citation)` where the
original returned a bare float — via a thin adapter module, leaving the ported
numeric core byte-comparable to the original for the differential test.

---

## `buildings.typologies.paris.structure`

```python
@dataclass(frozen=True)
class Grid:
    """Phase 1 output. Purely quantitative. NO roles, NO names, NO meaning."""
    storeys: tuple[PlacedSlot, ...]      # vertical, bottom-up
    bays: tuple[PlacedSlot, ...]         # horizontal, left-right — ONE solve per building
    cornice_height: Quantity
    envelope: GabaritEnvelope
    account: tuple[str, ...]

def solve_structure(site: SiteContext, datums: BlockDatums | None = None) -> Grid: ...
```

`Grid` must contain no field naming a role. Enforced by `test_grid_is_unnamed`.

---

## `buildings.typologies.paris.roles`

```python
class Role(Enum):
    BASE = "base"; MEZZANINE = "mezzanine"; PRINCIPAL = "principal"
    UPPER = "upper"; ATTIC = "attic"

@dataclass(frozen=True)
class RoledStorey:
    slot: PlacedSlot
    role: Role
    rank_from_principal: int        # 0 for principal, +1 upward
    index_from_bottom: int
    index_from_top: int

@dataclass(frozen=True)
class RoledGrid:
    storeys: tuple[RoledStorey, ...]
    bays: tuple[PlacedSlot, ...]
    grid: Grid

def assign_roles(grid: Grid) -> RoledGrid: ...
```

Predicates exactly as the brief states. `PRINCIPAL` = **tallest** habitable slot
above base and mezzanine, ties → lowest. The base exclusion is load-bearing.

---

## `buildings.typologies.paris.chronology`

```python
@dataclass(frozen=True)
class Variant:
    feature: str            # "ironwork" | "socle" | "keystone" | "roof" | "shopfront"
    name: str
    earliest: int
    peak_from: int
    peak_to: int
    latest: int
    class_lag: Mapping[BuildingClass, int] = ...   # years behind GRAND
    source: str = ""

def prevalence(v: Variant, year: int, klass: BuildingClass) -> float:
    """Fashion: a continuous ramp/peak/decline in [0,1]. NOT a step."""

def available(feature: str, year: int, klass: BuildingClass) -> list[tuple[Variant, float]]:
    """Variants whose window contains `year` (after class lag), with weights."""

def legal(feature: str, year: int) -> bool:
    """Legality: a STEP function, sourced. Distinct mechanism from prevalence."""
```

**Forbidden:** any rule outside `reglement.py` branching on a period enum.
`dev/harness/check_no_period_branching.py` greps for it and fails the build.

---

## `buildings.typologies.paris.qualify`

```python
@dataclass(frozen=True)
class QualContext:
    """The read-only fact set every rule sees. Complete before qualification
    begins; NEVER mutated by it. Exactly the brief's list."""
    # structure
    slot_h: float; slot_w: float; level_above_pavement: float
    index_from_bottom: int; index_from_top: int; storey_count: int
    # role
    role: Role; rank_from_principal: int
    # horizontal (bay slots)
    bay_index_from_left: int; bay_index_from_centre: int; is_centre_bay: bool
    distance_from_entrance: int; is_edge_special: bool; is_inserted_special: bool
    slot_kind: SlotKind
    # building
    year: int; klass: BuildingClass; street_width: float; corner: bool
    # envelope
    cornice_height: float; within_comble: bool

@dataclass(frozen=True)
class Properties:
    """What a rule returns. Sparse: unset keys mean 'no opinion', which is how
    layering works."""
    values: Mapping[str, object]
    rule: RuleId
    specificity: int

Rule = Callable[[QualContext, DecisionStream], Properties | None]
```

## `buildings.typologies.paris.compose`

```python
@dataclass(frozen=True)
class Layer:
    name: str          # "base" | "period" | "class" | "site" | "override"
    order: int         # later wins
    rules: tuple[Rule, ...]

def resolve(ctx: QualContext, layers: Sequence[Layer], rng: DecisionStream) -> Properties:
    """Later layer wins. Within a layer, higher `specificity` wins.
    Equal order AND equal specificity is a CONFLICT -> raise, never silently pick."""
```

User overrides are simply a `Layer` with the highest `order`. There is no
parallel override mechanism.

---

## `buildings.typologies.paris.terminate`

```python
@dataclass(frozen=True)
class Silhouette:
    points: tuple[tuple[float, float], ...]    # polyline, metres, IR-owned
    def within(self, env: GabaritEnvelope, tol: float = 1e-6) -> bool: ...

def terminate(grid: Grid, roled: RoledGrid, site: SiteContext,
              rng: DecisionStream) -> tuple[SilhouetteNode, tuple[Node, ...]]: ...
```

The silhouette is emitted **in the IR**. The renderer never derives it.

---

## `buildings.block`

```python
@dataclass(frozen=True)
class BlockDatums:
    """What the block hands DOWN. One-way (I2)."""
    street_width: float          # ONE value for the whole block
    cornice_height: float
    string_course_levels: tuple[float, float, ...]
    balcony_levels: tuple[float, ...]

@dataclass(frozen=True)
class Parcel:
    width: float; depth: float; corner: bool
    left_neighbour: int | None; right_neighbour: int | None

@dataclass(frozen=True)
class Block:
    street_width: float
    parcels: tuple[Parcel, ...]
    datums: BlockDatums

def subdivide(frontage: float, rng: DecisionStream, ...) -> tuple[Parcel, ...]: ...
def solve_block(block: Block, year: int, ...) -> tuple[Node, ...]: ...
```

The block always owns **frontage subdivision and adjacency**. For Paris it also
owns the shared horizontal datums (1855 circulaire). A corner is its own short
facade, **not** a module type.

---

## `buildings.render.svg`

```python
def render(node: Node, *, width_px: int = 1200, labels: bool = False) -> str: ...
```

**The renderer decides nothing arguable.** It may not branch on `year`, `klass`,
or `Role`. `dev/harness/check_renderer_dumb.py` enforces this by AST scan.

---

## Testing conventions

- `tests/unit/` — per module
- `tests/invariant/` — I1–I5, fuzz sweeps
- `tests/oracle/` — differential vs `../haussmann`
- Run with `python -m pytest`. No network in tests.

---

# Amendment 1 — after the S0–S2 verification pass

The wave-1 verifiers found holes in the contract itself. These amendments are
binding on all later stages and override anything above that conflicts.

## A1.1 `quantity`: scalar arithmetic must respect rigidity

The original contract specified arithmetic only *between two `Quantity` objects*,
which left `Quantity * float` unspecified. The implementation allowed it and
preserved the kind, so:

```python
Abs(2.60, "a carriage must pass") * 1.35   # -> ABSOLUTE 3.51
```

That is a scaled doorway. It routes around `scale_for_class` with no grep-able
marker, and it is exactly the failure the brief names: *"If a quantity doesn't
know what kind it is, someone will eventually scale a doorway, and nobody will be
able to say why the result looks wrong — only that it does."*

**Required:** scalar `*` and `/` on an `ABSOLUTE` or `REGULATORY` quantity
**raise** `TypeError`, with a message naming the kind and pointing at
`scale_for_class`. Scalar arithmetic on `PROPORTIONAL` is permitted.

`Quantity + float` already raises; this makes the surface consistent.

## A1.2 `quantity`: citations must be non-blank

`Reg(6.0, "   ")` is currently accepted. The guard must be `if not source.strip()`.

## A1.3 `quantity`: class factors are a placeholder, not a finding

`scale_for_class` currently uses MODEST 0.85 / ORDINARY 1.00 / COMFORTABLE 1.15 /
GRAND 1.35. These are **invented** and appear in neither the brief nor any
source. They must be marked as inferred in the docstring, in the same way
`chronology` marks inferred dates. Only the monotonic ordering and the
ABSOLUTE/REGULATORY no-op are contractual.

## A1.4 `ir.serial`: round-trip must be lossless for the values the IR actually carries

Two gaps, both of which later stages will hit:

- **Sequences denormalise.** `SilhouetteNode(props={"points": ((0.0,0.0), ...)})`
  round-trips tuples to lists, so `from_json(to_json(n)) == n` is **False**.
  S7 writes exactly this payload. `from_json` must restore tuples for nested
  sequence values so the round-trip is genuinely lossless.
- **`Quantity` is not serialisable.** `to_json` raises `TypeError` when a
  `Quantity` appears in `props` or `TraceEntry.inputs`. A qualification rule
  recording `inputs={"limit": Reg(6.0, "ordonnance de 1823")}` is an obvious and
  intended use of the trace facility, and it would crash.
  **Required:** a tagged encoder/decoder so `Quantity` round-trips with its kind
  and citation intact.

## A1.5 `ir.nodes`: hashability is declared, not accidental

`hash(Node(...))` and `hash(TraceEntry(...))` raise, because `props` is a
`mappingproxy`. Frozen dataclasses are normally hashable, so this will surprise
later code that puts nodes in a set.

**Required:** make them genuinely hashable via a frozen hashable mapping, and
test it. Nodes in a set is a reasonable thing for the block and trace layers to do.

## A1.6 `solver.fitting`: the parity fix must not refuse solvable symmetric layouts

The S1 repair enforced parity by requiring `(n_bays + n_fixed)` to be odd *before*
rung 4 is tried. That makes "even bay count plus one special on the axis"
unreachable, and the solver now raises `FitInfeasible` on widths that have a
perfectly good symmetric answer:

```
solve(8.05, end=0.20/0.40/0.75, bay=2.70/3.00/3.30,
      special=1.10/1.35/1.60, central_feature=True)   -> FitInfeasible
but  end 0.40 | bay 3.00 | special 1.25 | bay 3.00 | end 0.40  = 8.05 exactly,
     every slot in bounds, perfectly symmetric, special on the axis.
```

9 of 18 refusals for the `central` vocabulary and 21 of 42 for
`central_with_porte` are of this kind, **all at widths below 8.7 m** — narrow
Paris parcels, which S3 will certainly hand it.

**Required:** an even bay count with a lone central special is a legal
arrangement — the special itself sits on the axis. Accept it. The invariant that
matters is *something is on the centreline*, not that the bay count is odd.

`test_every_refusal_is_genuinely_infeasible` must also stop enumerating the same
parity policy the implementation uses; as written it cannot detect this class of
narrowing.

## A1.7 The oracle must not be allowed to skip silently

`tests/oracle/test_reglement_diff.py` uses `pytest.importorskip("core.reglement")`.
If `../haussmann` is ever moved or renamed, the entire 417-test oracle module
skips and the suite still reports green — the exact vacuous-gate condition G2
exists to prevent.

**Required:** a missing oracle is a **hard failure**, unless
`HAUSSMANN_ORACLE_OPTIONAL=1` is explicitly set in the environment.

## A1.8 `SlotSpec.rigid` must be tested independently of `SlotKind.FIXED`

Mutation M5 — changing `SlotSpec.pinned` from `self.rigid or self.kind is
SlotKind.FIXED` to just the latter — passes all 627 tests. The implementation is
correct, but no test constructs a rigid slot with a genuinely wide
`[minimum, maximum]` that is not already `FIXED`, so the flag itself is unproven.
Add one.

---

# Amendment 2 — after the S6–S7 verification pass

S6 (qualification + composition) passed its gate outright. S7 passed 8 of 9 and
the verifier flagged six problems in the **design**, not the code. The brief
predicted this — *"the most elegant part of the document and the part most likely
to be wrong"* — so these are the rule model being corrected by contact, which is
what the first typology is for.

Binding on all later stages.

## A2.1 `Role.ATTIC` must be reachable, or it must not exist

Across 1200 random situations the role tally is base 1200 / principal 1200 /
upper 2536 / mezzanine 607 / **attic 0**. `structure.py` never builds a storey
above the cornice, so `within_comble` is always `False`, and any qualification
rule keyed to `ATTIC` is dead code. The contract currently declares a role the
system cannot produce.

**Decision: make it reachable.** A Paris comble is not empty roof — it holds the
*chambres de bonne*, lit by the dormers `terminate.py` already emits. The comble
is habitable space and the brief's predicate says so plainly: *"Attic — the slot
inside the roof envelope."*

**Required:** when the comble has enough clear height for a habitable storey,
`structure.py` emits a storey slot inside the roof envelope, `within_comble` is
`True` for it, and `assign_roles` labels it `ATTIC`. Dormer count and placement
should then follow that storey's bay grid rather than being decided independently.
Where the comble is too shallow, no attic storey — and `ATTIC` legitimately does
not appear.

## A2.2 The entresol is a programme decision, not leftover budget

At an identical 20 m / 1865 / shop site, modest and ordinary get a mezzanine
while comfortable and grand do not. Measured rate by class across 600 situations:
modest 42 %, ordinary 64 %, comfortable 57 %, grand 43 % — not monotonic, because
the mezzanine appears only where the class factor squeezes the budget hard enough
to leave a short slot.

That is the right element for the wrong reason. On a boulevard an entresol over a
shop is **more** common the richer the building, not less.

**Required:** the entresol is decided by *programme* — the ground-floor use
(`SHOP`/`CAFE`/`OFFICE` want one; `RESIDENTIAL` largely does not) and class —
before the height budget is filled, and the solver then accommodates it. It must
not be an artefact of what was left over.

## A2.3 One constant may not do two unrelated jobs

`_AMBITION_FRACTION` is passed to `compute_envelope` as `roof_fill`, so the single
number deciding how close the facade comes to its legal ceiling *also* decides how
full the comble is. A modest building therefore gets both a lower cornice and a
shallower garret — backwards for where servants actually lived, and it means a
change intended to affect facade ambition silently moves the roofline.

**Required:** two separately-named, separately-documented constants, each marked
INFERRED. Facade ambition and comble fill are different decisions.

## A2.4 `Silhouette.within` must test what its name says

It measures setback from the **built eaves** rather than the **legal cornice**, so
it answers a strictly harder question than legality. `env.ridge_height` is computed
by `compute_envelope` as a height above the cornice and then re-anchored at the
eaves, so in the harness case 1.23 m of unused facade headroom is discarded rather
than being available to the comble. A building's roof can never reach into legal
space its own facade declined to use.

**Required:** anchor containment at the legal cornice, which is what the gabarit
actually constrains. Keep the built eaves available as a separate, clearly-named
query if a caller wants the stricter test.

## A2.5 The roof "shape" axis duplicates a decision the decree already made

At 1885 / comfortable the envelope is `circular_arc` while the chosen variant is
named `diagonal_45_pedimented_dormers` — because class lag means the arc variant
is not yet available to that class although the arc *envelope* is already law.
The variant is really a **dormer-and-ornament repertoire**; naming it after a
comble geometry that `terminate.py` explicitly refuses to choose invites the
contradiction.

**Required:** rename the axis to what it is, and assert that a chosen variant
never contradicts `env.roof_envelope`. Comble *geometry* comes from the decree;
only dormer form, cresting and ornament come from fashion. This is the
legality-vs-fashion split from the brief, and it must not blur here.

## A2.6 Tie the two depth limits together with an assertion

`_comble_profile` takes `half_depth` only to decide whether to append a flat
terrasse; nothing truncates a comble whose ridge inset exceeds half the parcel.
That is safe today only because `compute_envelope` already depth-limits the ridge
from the same `site.parcel_depth` — **two modules independently relying on the
same unstated invariant.**

This is a live hazard for S9: if a `BlockDatums` path supplies an envelope whose
`parcel_depth` disagrees with the site's, the roof silently runs past the middle
of the parcel and nothing errors. That is the same shape as the previous attempt's
street-width failure.

**Required:** assert the invariant explicitly where the two meet, so it fails
loudly rather than silently.

---

# Amendment 3 — retracting A2.4

**A2.4 was wrong, and it was my error, not the implementer's.** It is retracted
and replaced by this item. The Amendment-2 verifier reported honestly that the
defect A2.4 described had not been fixed; the reason is that the code was
already closer to correct than the amendment was.

## What A2.4 got wrong

A2.4 required containment to be anchored at the **legal cornice**. That is not
what the gabarit constrains. `reglement.py` states the rule directly:

> "combles must be inscribed below a 45° diagonal springing from the eaves
> (*égout du toit*)" — line 14

and `slope_profile`'s docstring anticipates exactly the case A2.4 raised:

> "A building whose stone face stopped below its legal cornice **springs its
> comble from its own eaves** and may run it further above *them* than the ridge
> stands above the cornice."

So the springing is the **actual eaves**. A building that stops below its legal
cornice does not get to bank the difference and start its roof higher up. The
original eaves-anchored implementation was legally correct, and anchoring
`within` at the legal cornice made the containment check **too permissive** —
it would accept combles that the 45° diagonal from the real eaves forbids.

## What the original finding got right

The underlying observation was still sound: `env.ridge_height` is computed as a
height above the *cornice* and then applied at the *eaves*, which silently mixes
two anchors. The headroom is partly recoverable — but by the mechanism the
règlement actually provides, not by moving the springing.

## A3.1 — Required

1. **The springing is the built eaves.** Revert `Silhouette.within` to test
   containment against the envelope curve springing from the eaves. That is the
   legal question. If a separately-named legal-cornice query is useful, keep it,
   but it is not the definition of `within`.

2. **Recover the headroom the lawful way.** A comble springing from eaves below
   the legal cornice may run *further above those eaves* than `ridge_height`
   stands above the cornice — tracing the **same curve** to a taller top, which
   is precisely what `slope_profile(top=...)` exists for and what its docstring
   says `terminate` does. Derive that top from the envelope curve and the parcel
   depth, not by re-anchoring.

3. **Never mix the two anchors in one arithmetic.** Whatever is computed above
   the cornice must not be applied at the eaves without conversion. Add an
   assertion or a clearly-named conversion at the boundary so the mix cannot
   recur silently.

4. Every point must still come from `setback_at` — this is a query about the
   shape, not a second opinion about the ceiling.

## Note for the record

This is the amendment mechanism working in the direction it is supposed to: a
verifier declined to mark an item passed when the letter had been satisfied and
the substance had not, which surfaced that the specification was the thing at
fault. A gate that had accepted "the test passes" would have hidden it.

---

# Amendment 4 — after the S8–S9 verification pass

S9 (block) passed outright, including the named failure the previous attempt
died of. S8 (renderer) failed, and the visual check confirms it: generated
facades read as **curtain wall**. The structural bones are right — storeys taper,
*balcons filants* land at the ordinance height, the cornice runs, the comble
carries dormers — but every opening fills its whole bay, so there is no masonry
between, above or below the windows.

Success criterion 1 is *"someone who knows Paris doesn't flinch."* Today they
would. These items are what stands between the two.

## A4.1 An opening is not a bay — qualification must emit its geometry

`OpeningNode.props` currently carries x/y/w/h **byte-identical to its parent
`BayNode`**. The renderer, given nothing else, invents a 0.10 m margin and glazes
the bay. The old implementation had its own width and height and centred the
window in the bay (`../haussmann/backends/svg.py:485`).

This is an **IR gap, not a renderer bug**, and it must be fixed in qualification —
the renderer is not permitted to decide window proportion, because that is
exactly the kind of thing a person can argue about.

**Required:** qualification emits opening width, height and position within the
bay slot. These are `PROPORTIONAL` quantities and must move with class and role:
a grand building's windows are much larger than a modest one's while its door
barely changes. That contrast *is* the absolute/proportional split, and it is the
thing the eye reads as scale. A Paris opening is a tall rectangle — roughly 1:1.7
to 1:2 — with a real pier either side and a spandrel below the sill.

The vertical position must respect `sill_height`, which is `ABSOLUTE`: a sill is
something a person leans on, and it does not scale with the building.

## A4.2 `sill_height` is being discarded

`elements.py:100` silently drops the IR's `sill_height` on every storey above the
ground floor. An `ABSOLUTE` quantity handed to the renderer is being ignored,
which inverts the project's central rule. The renderer must honour it.

## A4.3 The renderer guard is being routed around

`elements.py` renames forbidden tokens into locals before branching, and its own
docstring says so: *"no local variable is ever named after one of the guard's
forbidden tokens."* Two branches do this —
`ornament_weight = _num(props, 'richness', 0.5)` then `if ornament_weight >= 0.7`,
and `pattern = props.get('variant')` then `if pattern == ...`.

The values are resolved qualification facts rather than dates, so this is not the
worst version of the offence. But **0.7 is a renderer-chosen threshold a person
could argue about**, and a guard that can be satisfied by renaming a variable is
weaker evidence than a clean exit suggests.

**Required:** the threshold moves into qualification, which emits a resolved
decision (e.g. `keystone_kind`, `ornament_tier`) that the renderer merely draws.
Deliberately evading a guard is not an acceptable pattern anywhere in this repo —
if a guard is wrong, say so and change the guard by agreement.

## A4.4 The chimney stack has no visible base

`SpecialNode` chimney_stack carries `y = eaves_height` and `h = ridge - eaves`,
i.e. its full *section* extent, with no notion of where it emerges from the roof
surface. The renderer faithfully draws the whole rectangle, so stacks paint as
full-height bars over every roof. The IR must carry the visible base.

## A4.5 Corner buildings with an arc comble render as onion domes

Reported by the contact-sheet check. Diagnose and fix; a corner is a third short
facade with its own rhythm, not a dome.

## A4.6 There is no render path for block output

`render()` assumes the node **is** a `BuildingNode` and looks for `storey`
children, so a `parcel` node renders an empty 325-character SVG. S11's contact
sheets need a block to render as one wall — which is the whole point of the block
being the unit.

## A4.7 One fact, two names

Chamfer bays carry `props['slot']` (`block.py:1349`) while every building bay
carries `props['slot_name']`. A consumer keying on `slot_name` silently reads
`None` on a chamfer bay. Pick one name.

## A4.8 Assert the datum agreement

`solve_structure` does not assert `site.street_width == datums.street_width`; when
datums are supplied it silently prefers the datum and ignores the `SiteContext`
value. That is a latent second source of truth of exactly the kind this project
exists to eliminate. Assert they agree, or document why they may differ.

---

# Amendment 5 — after the A4 verification pass

A4 succeeded where it mattered most: openings now have their own geometry, and
the absolute/proportional split is **visible** — across modest→grand the porte
cochère stays 3.000 × 3.000 m byte-identical while mean window area grows
1.836 → 3.551 m² (1.93×). Storeys 1–4 read as masonry with windows cut into it,
and a block renders as one wall with a continuous cornice.

Three defects remain, and they are concentrated at **eye level**, which is where
a viewer looks first.

## A5.1 The shop ground floor is still literal curtain wall

`compose.py` emits a `ShopfrontNode` with `x = 0.0, w = facade_w` — the **whole
frontage** — and `render._draw_storey` draws it *before* the bays. So
`draw_shopfront` glazes 0→12 m in a single rect and paints over the masonry
qualification had already carved: each shop bay is 2.645 m in a 3.45 m bay with
0.4025 m piers either side, leaving 0.805 m of pier between shops.

A4.1 was implemented correctly and then obliterated by a node drawn on top of it.

**Required:** a shopfront belongs to its **bay**, not to the frontage. Emit one
shopfront element per shop bay, respecting the piers already carved. A Paris
*devanture* has a stall riser below, a fascia above, and real masonry between
shops — the pier between two shops is structural, and it is what stops the
ground floor reading as a glass band.

## A5.2 The renderer is inventing a rhythm the IR did not state

`elements.draw_shopfront` computes `n = max(2, int(w / 1.4))`, giving 8 mullions
at 1.5 m centres across a 12 m frontage whose structural bays are at 3.45 m
centres. The decorative rhythm therefore **contradicts** the structural one.

`check_renderer_dumb` does not catch this — there is no forbidden token in the
expression — but it is the same offence as A4.3: a renderer deciding proportion.
Mullion spacing is arguable, so it belongs in qualification.

**Required:** the mullion/pane rhythm comes from the IR. Remove the invented
divisor. Consider extending the guard to catch renderer-side proportion
arithmetic, but **propose it rather than editing the guard unilaterally.**

## A5.3 The shopfront glass is misregistered against its own frame

The full-width band sits at `y=1296.62 h=213.63` while the shop-bay openings
drawn over it sit at `y=1288.66 h=242.04` — off by 8 px vertically and 28 px in
height, so every shopfront shows a ghost frame offset from its glass. Fixing
A5.1 should remove the double-draw; confirm it does rather than assuming.

## A5.4 The *pan coupé* renders as a blank wall

`block.py` builds chamfer bays with `x/y/w/slot_name` and **no children**, and
`render._draw_chamfer` has no opening branch — so every chamfered corner in a
block is an unpierced blank wall. Visible at both ends of the block render.

The brief is explicit that a chamfered corner *"becomes a third short facade with
its own rhythm"*. It needs its own bay solve and its own openings, qualified like
any other facade. The onion dome is genuinely gone; this is the other half of the
same item.

## A5.5 The carriage entrance — a decision to confirm, not a defect

44/44 sampled portes cochères have `offset_x = 0.0` and width exactly equal to
their slot, giving a square 3.00 × 3.00 m opening with no pier either side.
`catalogue.carriage_entrance_in_slot` documents this as intentional — "the
opening IS that slot" — so it is a stated position.

It is defensible: a carriage entrance genuinely occupies its full structural bay.
But the height is being capped by `slot_h − lintel_bearing_depth` well below the
3.40 m `carriage_clear_height` the catalogue declares, which means the ABSOLUTE
constraint that a carriage must physically pass is being silently overridden by
storey height.

**Required:** if the clear height cannot be met, that is a **structural** problem
— the ground storey must be tall enough for the programme it carries. Either raise
the storey, or refuse the combination loudly. Do not silently emit a carriage
entrance a carriage could not pass through; that is the absolute/proportional rule
being inverted where it is least forgivable.

---

# Amendment 6 — the last flinch-points

A5 passed every item: shopfronts are per-bay with real masonry piers between,
the *pan coupé* is a pierced short facade, the invented mullion divisor is gone,
and a porte cochère now refuses rather than silently shrinking below the 3.40 m
a carriage needs. **1238 tests passing.**

The A5 verifier then listed what a knowledgeable viewer would still flinch at.
This amendment takes the ones that are genuinely wrong rather than merely thin.

## A6.1 There is no door. Anywhere.

The harness ground storey is `pier_end / shop / shop / shop / pier_end` — three
shops and **no way into the building**. Across a whole 10-parcel block the
opening census is `{window: 108, shop_bay: 27, blind_panel: 27, oeil_de_boeuf: 3}`
and not one entrance.

This is the single worst defect in the system. Every Paris immeuble has an
entrance — a *porte cochère* on the grander streets, a *porte piétonne* on modest
ones — and it is the element the whole composition is organised around.

The brief is explicit that this is a positional problem, not a slot problem:

> "Specials have position rules, not free slots. The entrance is not 'one of the
> modules, anywhere.' It wants the centre, or a particular offset, and when it
> sits off-centre the composition should answer it — putting the narrow special
> on the opposite side, for instance. The grammar needs positional and symmetry
> constraints, not just a sequence of types."

**Required:** every building has exactly one entrance, placed by a positional
rule rather than left to chance. It is `ABSOLUTE` in width and height — it is the
ruler the eye measures the facade against. When it sits off-centre, the
composition answers it.

## A6.2 The leftover special becomes a stack of blind panels

Parcels 1, 5 and 8 each carry a ~1.83 m `special` bay filled with a `blind_panel`
on **every** storey, pavement to cornice. A blind panel is a legitimate element;
a full-height column of them is not — it reads as a walled-up building.

The narrow special exists so the leftover is architecturally meaningful. At
ground level it is a strong candidate for the **entrance**; above, it should vary
— an *œil-de-bœuf*, a narrow window, a niche — not repeat one element five times.

## A6.3 The *pan coupé* has no roof

Both chamfer nodes carry storeys, string courses, balconies and a cornice, and
**no roof child**; `render._draw_chamfer` has no roof branch. Above each chamfer's
cornice is bare sky, at both ends of the block. The corner is the one place a
Paris roof is most visible.

## A6.4 Chimneys float off the roof

*Souches* are all placed at the silhouette apex for every parcel, but a hipped
corner comble's drawn surface falls away toward its ends — so two stacks hang in
blank sky roughly 4 m clear of the tiles. A chimney emerges from the roof surface
beneath it.

## A6.5 Garde-corps are drawn across solid masonry

Three `IronworkNode`s span `w = 3.450` — the **whole bay, piers included** — in
front of the solid *allège* under a 1.322 m window. A garde-corps guards an
opening; it is as wide as the opening, not as wide as the bay.

## A6.6 The mezzanine's ironwork has `h = 0.000`

Three `IronworkNode`s arrive with zero height and draw nothing. A rule that emits
an element which cannot be seen is a rule producing a lie in the IR — either give
it height or do not emit it.

## A6.7 A pedimented surround over a shop light

Every ground-floor bay resolves `surround_kind='pedimented'`, emitting a bare
three-point polygon floating in the *enseigne* band with no entablature, returns
or jambs. Shop windows do not take pediments. Ground-floor surrounds should come
from the shopfront vocabulary.

## A6.8 The devanture's head is stated and discarded

`shop_bay` openings carry `head='segmental'`, but `draw_opening` dispatches to
`_draw_shop_light` and returns before any head is drawn. The IR states a fact the
renderer throws away — the opposite of the A4.1 problem and just as wrong.

## A6.9 The stall riser is 0.15 m

A real *soubassement* is 0.3–0.6 m of boarded or stone plinth. At 0.15 m the
devanture reads as glass meeting the ground.

## A6.10 The comble is one flat grey field

No zinc seam coursing, no visible break between *brisis* and *terrasson*, so the
roof is a large blank rectangle occupying ~20 % of the elevation. Zinc became the
dominant Parisian roofing material mid-century and its seams are a strong part of
how a Paris roof reads.

## A6.11 Renderer-side proportion arithmetic remains

`elements.py:300` computes modillion spacing as `spacing = 0.5;
n = max(1, int(w / spacing))` — the same offence as A5.2, uncaught because
`check_renderer_dumb` inspects names and enums, not arithmetic. Move the count to
the IR.

**Also required:** extend `check_renderer_dumb.py` to catch renderer-side
proportion arithmetic — a division or multiplication of a dimension used to decide
how many of something to draw. This one guard change **is** authorised, since
three separate waves have now found the same class of offence slipping past it.

## A6.12 Hygiene

`dev/harness/_render_a5_check.py` is a scratch script left behind. Promote it to a
real harness entry point or delete it.

---

# Amendment 7 — ornament counts, the chimney, and a rewritten guard

A6 landed the entrance (7,680/7,680 buildings now carry exactly one, placed
positionally, byte-identical across classes), the chamfer roof, the garde-corps
width, the stall riser and the comble seam coursing. Two items did not land, and
the repository is currently **red**.

## A7.1 The proportion guard has been rewritten — by the orchestrator

The A6.11 guard caught 2 of 7 spellings of count-from-dimension and carried dead
logic (`name.startswith("_") and not name.startswith("_")`). It has been replaced
with a small per-function taint analysis: a value is *dimensional* if it comes
from IR geometry, *chosen-here* if it is a literal written in the renderer
(including behind a ternary or bound to a local, singly or in a tuple), and a
`dimensional ⊘ chosen-here` result reaching `int`/`round`/`ceil`/`floor`/`range`
is a count and therefore a violation.

Dividing a dimension by a limit the **IR stated** is exempt — that is the renderer
obeying a stated limit rather than inventing one. The exemption applies to the
divisor only: `_num(props,'w') / 0.25` is still the offence, because the dividend
coming from the IR is exactly what makes it a dimension.

Measured: **7/7 offences caught, 0/6 false positives** against the A6 verifier's
own test cases — stroke widths, metres-to-pixels, centring, clamping,
`ceil(w / props['pane_max_span'])`, and dividing by a count all pass.

**Agents may not edit this guard.** If it produces a false positive, report it.

## A7.2 Move the ornament counts to the IR

The rewritten guard finds **13 violations**, all in
`src/buildings/render/svg/elements.py`: modillions (`w / spacing`), dentils,
rustication coursing (`course_w, course_h = 0.9, 0.32`; `course_h = 0.22`;
`course_h = 0.3`), balcony brackets (`w / 1.5`), rail bars
(`w * _UNGUARDED_RAIL_BAYS_PER_METRE`), scrolls (`w / 0.35`), waves and lozenges
(`w / 0.3`), cresting (`w / 0.4`), and zinc seams
(`facade_w / (0.6 if zinc else 1.3)`).

Every one decides **how many** of something to draw from a dimension and a number
the renderer chose. Ornament density is compositional — the brief lists "the scale
and density of ornament" among the *proportional* quantities that move with
ambition and budget — so these counts belong in qualification, driven by class and
`rank_from_principal`, and must arrive in the IR.

The rail-bar case is the instructive one: `ceil(w / gap_max)` where `gap_max` comes
from the IR is **correct and stays** — a balustrade gap narrow enough for a
child's head is an ABSOLUTE quantity and the renderer is honouring it. Only the
`_UNGUARDED_RAIL_BAYS_PER_METRE` fallback is the offence.

## A7.3 The chimney fix traded one defect for a worse one

A6.4 was implemented by having `render.draw_building` **overwrite** the IR's
chimney `y` with a surface height computed in the renderer. So the check "the base
sits on the drawn surface" is true *by construction* — 0.000 m over 426 chimneys —
while the IR now states a base up to **7.603 m** from what is drawn. That is the
renderer discarding stated IR geometry: the same offence as A4.1 and A6.8.

And because the head height was held absolute while the base dropped, hip-end
*souches* became smokestacks: visible stacks up to **12.7 m**, with 2,170 of 5,088
exceeding 2.5 m. Three brown poles now stand outside the roof mass entirely.

**Required:** the roof surface height at the stack's x is a **structural** fact.
Compute it in `terminate`, put it in the IR, and have the renderer draw what it is
given. A *souche* is roughly 0.5–1.5 m of brick above the tiles where it emerges —
its height above the surface is what stays roughly constant, not its apex.

## A7.4 A6.8 closed the gap from the wrong end

`draw_opening`'s shop branch now draws `head` correctly, but
`qualify/base.ground_floor_of_a_shop` hard-codes `opening_head='flat'` and nothing
can produce anything else — so all 1,944 shop bays carry `flat` and the branch is
dead code. The contract's premise (shops carry `segmental`) was made false rather
than satisfied. Segmental and round-headed *devantures* are common; let the
chronology decide it.

## A7.5 Blind-panel runs

19 % of special columns still read as a near-full stack of one element — worst
case 4 consecutive `blind_panel` storeys out of 5. The letter of A6.2 holds
(never *all* storeys) but the spirit does not. Cap consecutive identical fills.

---

# Amendment 8 — the critical and high defects from validation

S10/S11 validation graded the build against the brief's own success criteria.
**Criterion 2 passes** (inputs change output predictably, including the
discontinuities); the fuzzer ran 3,000 cases clean with five negative controls
proving its checkers have teeth; the oracle matched the old implementation on
**495/495 regulatory rows**. The rule model — the part the brief called most
likely to be wrong — works.

**Criterion 1 fails.** What is broken sits between the model and the eye.

Six defects, all of which the validation located precisely. Note that **none was
caught by any gate, and all four gates were green** — so a new guard,
`check_ir_is_consumed.py`, has been added by the orchestrator alongside them.

## A8.0 The new guard: what the IR states, the renderer draws

`dev/harness/check_ir_is_consumed.py` is the complement of
`check_renderer_dumb.py`. That guard stops the renderer *deciding*; this one
stops it *ignoring*. Two checks: every kind the IR can state has a renderer
branch, and every prop the generator writes is read (or listed as ignored with a
reason). It already catches D1.

**Agents may not edit either guard.** Report a false positive; do not tune it.

## A8.1 (D1) Half of all buildings have no visible door — CRITICAL

`render/svg/elements.py:193` — `if opening_kind == "carriage_entrance":` is the
**only** entrance branch. `pedestrian_entrance` falls through to the generic
window path.

The IR is not at fault. `catalogue.entrance_for` places exactly one door on every
building and states it correctly: `{'opening_type': 'pedestrian_entrance',
'w': 1.4, 'h': 2.9, 'head': 'flat', 'sill_height': 0.0}`. The renderer discards
it. Across the sweep: 40 carriage, 40 pedestrian — **exactly half the
population**, comprising every modest and ordinary building and every building on
a street under 12 m.

A *porte piétonne* is a panelled timber door with a fanlight or a glazed upper
panel, its own surround, and no sill — not a window. It is the ruler the eye
measures the facade against, so drawing it as a window destroys the scale
reference the whole absolute/proportional split exists to provide.

## A8.2 (D2) The hip run is keyed to parcel depth, not frontage — CRITICAL

`elements._hip_arris` runs the hip in by `min(facade_w/2, section_run)`, where
`section_run` is the last x of the silhouette profile — a section on a plane
**perpendicular to the street**, calibrated against `parcel_depth`. Measured:
that value is **9.0 for every frontage from 8 m to 26 m**.

So any frontage under 18 m has both hips meeting at mid-frontage and the roof has
**no ridge at all** — a gable, or a pyramid on a wide parcel. That is essentially
every parcel in Paris.

This one bug produces three separate VLM findings: the barn/pyramid roof, the
floating chimney (the souche is placed at the *stated* ridge 20.718 while the
drawing truncates the apex to 17.5, so it hangs 3.5 m in clear air), and the
block's stepped roofline. **Fixing it should retire all three.**

The hip run is a function of the **frontage**, not the section. Take it from the
IR rather than from the section profile.

## A8.3 (D3) No Second Empire building has a mansard break — HIGH

A pre-1884 roof node states `lower=45.0, upper=45.0, break_pct=1.00`, so
`draw_roof_mass` correctly draws no break. **The renderer is obeying the IR
faithfully; the defect is upstream.**

A 45° diagonal is the *legal maximum envelope*, not a roof section. The building
inside it still had a **brisis** (the steep lower slope) and a **terrasson** (the
shallow upper one) — that is what a mansard *is*. `terminate` must state the
actual comble section it built, inscribed within the 45° envelope, not restate
the envelope as though it were the roof.

Compounding it: dormers sit in the lowest fifth of the unbroken plane with bare
zinc above, where a real *lucarne* occupies the whole brisis.

## A8.4 (D4) Upper windows violate the catalogue's own declared band — HIGH

`catalogue.opening_aspect_band()` states the Paris band as **(1.70, 2.00)**.
Measured aspect (h/w), mezzanines and oculi excluded:

| class | role | n | median | min | % below 1.70 |
|---|---|---:|---:|---:|---:|
| grand | upper | 472 | **1.33** | **1.00** | **94 %** |
| comfortable | upper | 551 | 1.39 | 1.06 | 94 % |
| grand | principal | 156 | 1.65 | 1.60 | 73 % |
| modest | upper | 544 | 1.78 | 1.13 | 41 % |

A minimum of 1.00 is a **square window**, and it is worse for the *grander*
classes. This is a stated-contract violation with no assertion behind it, and it
is why the wall reads as having holes in it rather than windows.

**Required:** openings respect the declared band, and an assertion enforces it.
Where a storey is too short to fit a 1.70 aspect at the bay's width, the opening
must get **narrower**, not squatter — width is proportional and elastic, the
aspect is what carries the reading.

## A8.5 (D5) The comble's share is inversely proportional to class — HIGH

Same site, varying only class:

| class | total | comble | share | dormers |
|---|---:|---:|---:|---:|
| modest | 20.72 | **7.73** | **37 %** | 5 |
| ordinary | 20.72 | 5.80 | 28 % | 4 |
| comfortable | 20.72 | 4.40 | 21 % | 3 |
| grand | 20.72 | **3.34** | **16 %** | 2 |

`total_height == legal_total_height` in all four. So the facade allowance a modest
builder declines to use is silently converted into **roof**: the poorer the
building, the bigger its hat. Backwards twice over.

Traced to `structure._COMBLE_FILL = 0.99`, deliberately class-invariant, against
`_FACADE_AMBITION` which is not. **The oracle found the same constant
independently** — 22 of its 29 proportion outliers are `total_height_m`, all
`new > old`, across every class. Two harnesses built for different purposes
converging on one constant is the strongest signal in the report.

This also violates the brief's own warning: *"Conflating them makes every building
a maximal building, which is wrong and looks it."* A modest building should be
shorter overall, not merely lower-eaved.

## A8.6 (D6) Grand buildings get fewer windows than modest ones — HIGH

Class scaling is applied to the **bay pitch**. Same 16 m frontage, 1870:

| class | bay pitch (max) | bays |
|---|---:|---:|
| modest | 2.55 m | **8** |
| ordinary | 3.12 m | 7 |
| comfortable | 3.80 m | 6 |
| grand | **4.05 m** | **6** |

Real Paris moves the other way. Money buys **taller and richer openings**, not a
sparser wall, and bay pitch is bounded by what the masonry will span — roughly
2.7–3.4 m at every class. This is why grand facades read too blank for their
pretension.

**Required:** bay pitch is structurally bounded and only weakly class-dependent.
Class expresses itself in the opening within the bay, in storey height, and in
ornament — not by thinning the rhythm.

---

# Amendment 9 — Daly calibration, and the A8 residuals

Amendment 8 passed D1, D3 and D4. D2, D5 and D6 came back partial. Separately,
the Daly 1864 measurement pass completed. The two converge, and **one of the
convergences shows that A8.5 was my error, not the implementers'.**

Measurement evidence: `dev/reference/daly_measurements.json`,
`dev/logs/DALY_MEASUREMENTS.md`. Sources: `dev/reference/SOURCES.md`.
Real sample: **n = 4 Première / 10 Deuxième / 2 Troisième buildings** (the unit is
the building, not the plate). Self-derived error bar, from measuring one building
twice independently: printed dimensions reliable; scale-bar widths ±10 %; storey
heights ±0.2–0.4 m; derived ratios worse.

## A9.1 — RETRACTION: A8.5 asked for something the evidence does not support

A8.5 required the comble share to **rise** with class. The implementers instead
made the comble class-invariant (3.20 m) and let total height rise with class
(16.19 / 18.12 / 19.52 / 20.57 m), then asserted the invariance deliberately.

Daly says they were right to. Comble share is marked **INSUFFICIENT** in the
measurements: it is *bimodal by roof type* with 2.4× within-class spread, so the
plates cannot support a class ladder in it at all.

**A8.5's ordering requirement is retracted.** What A8.5 got right — and what the
implementers delivered — is the substantive half: *"a modest building must be
shorter overall, not merely lower-eaved."* Total height now rises with class and
every class sits short of the legal ceiling, which is the brief's "not every
building is a maximal building" requirement met.

**Still required:** dormer count is 5/5/4/4, still favouring the modest building.
A comble is floor rather than show, so dormer count should follow the comble's own
frontage and geometry, not class — and certainly not fall as class rises.

## A9.2 — The carriage entrance is 15 % too wide, and it is costing grand buildings a bay

`catalogue.py:309` states `Abs(3.00, "INFERRED — typical porte cochère clear
width")`. Daly measures, across seven carriage doors:

| Class | n | median | values |
|---|---:|---:|---|
| Première | 4 | **2.567 m** | 2.410, 2.534, **2.600 (printed)**, 2.619 |
| Deuxième | 3 | **2.575 m** | 2.570, 2.575, 2.672 |

The two top classes agree to **0.4 %** — which is itself the finding: a carriage
door does not scale with money, because a carriage does not. The class signal is
**entitlement**, not size: Première 4/4 buildings have one, Deuxième 3/10,
Troisième 0/2.

**Required:** the clear width becomes **SOURCED at 2.60 m**, citing the printed
dimension (Daly 1864, Sér. 1 Vol. 1 t. 2). Keep it ABSOLUTE.

This also resolves the **D6 residual**. A8 correctly bounded bay pitch to an
ABSOLUTE 2.70–3.40 m, but the porte-cochère slot is 3.80 m — above that stated
maximum — and is carried up **every storey**, so a grand building loses a bay
(GRAND 4 openings vs MODEST 5 on a 16 m frontage; fewer on 6 of 8 frontages).
At 2.60 m clear the slot fits inside the band.

**Also required:** the carriage slot must not be carried up every storey at full
width. Above the ground floor the bay above a porte cochère is an ordinary bay.

Note Daly independently confirms A8's pitch fix: bay pitch is **non-monotonic**
across classes in the plates and is marked INSUFFICIENT as a class discriminator.
Making it class-independent was correct.

## A9.3 — D2 residual: two modules still hold independent opinions about the roof

A8 fixed `elements._hip_arris` to key the hip run to the frontage (4.311 m, was a
constant 9.0), and a ridge now exists at every frontage above ~8.7 m. But
`terminate._hip_arris_end` (terminate.py:1084) **still uses `profile[-1]` = the
full 9.0 run**. So the IR-stated souche base is now up to **1.559 m BELOW** the
drawn roof surface — the mirror image of the bug A7.3 fixed, and the same
two-independent-opinions divergence that A7.3 exists to eliminate.

Consequence: chimneys are drawn *before* the roof mass and are swallowed by it.
**One visible chimney where the IR states five.**

**Required:** one source of truth. The hip run is a structural fact; compute it
once in `terminate`, put it in the IR, and have the renderer consume it. Neither
module may derive it independently. Draw chimneys after the roof mass.

Two lesser items in the same area: the exact repro `PW=8` still has no ridge
(half-frontage 4.00 < rise-run 4.311), and end lucarnes overhang the hip into the
sky on hipped corners.

## A9.4 — Calibrate the SOURCED quantities

Replace INFERRED with SOURCED **only** for the eleven quantities the measurement
pass marked SOURCED:

door width by door type · window opening width · rez-de-chaussée storey height
(as class-independent) · presence of an entresol/compressed level · piano nobile
height *ordering* · window nobile height *ordering* · Deuxième storey-height
distribution · Deuxième entresol/ground ratio 0.775 · floor structure thickness
0.30 m · balcony projection ~0.60 m · cornice height ceiling at 20 m

Each gets a citation naming Daly 1864, the plate, and whether the figure was
**printed** or **scale-bar measured** (the latter carries ±10 %).

**WEAK** quantities — storey taper, facade-width ladder, door height, garde-corps
height, all Première storey-height values, all Troisième values — may be used for
**ordering only**. Assert the ordering, never the value.

**INSUFFICIENT** quantities stay INFERRED, untouched: comble share, cornice band
depth, upper-storey opening aspect, entresol aspect, balcony height above pavement
outside Deuxième, bay pitch as a function of class.

### Two findings worth encoding as structure, not scalars

**The window splits.** Width 1.04–1.30 m across all 16 buildings (×1.25,
non-monotonic) while noble-floor height runs 2.92 / 2.24 / 2.09 m (×1.40). Same
aperture: **width absolute, height proportional.** That is the project's central
distinction, demonstrated from a period source. Encode it that way.

**The compressed level.** 14 of 16 buildings carry a compressed storey between the
shop floor and the nobile — Première dresses it as a low *1er* (4/4), Deuxième as
an entresol (9/10). Troisième has neither, and no piano nobile at all: its étages
are equal within 0.07 m. So "has a principal floor" is itself class-dependent,
which the role predicates should be able to express without a special case.

**The regulation is visible in the data.** Cornice height is flat between Première
and Deuxième — six buildings sit between 19.0 and 20.0 m, all pinned to the 1859
règlement's 20 m limit. Assert that the model reproduces this.

---

# Amendment 10 — the A9 residuals

A9 landed the calibration: the carriage door is SOURCED at 2.60 m from a printed
plate callout, with a load-bearing tripwire (reverting it to 3.00 m makes
`solve_structure` raise); the hip arris has one source of truth; chimney counts
match the IR; the golden master bites; and the audit confirmed **the six
INSUFFICIENT quantities were left untouched**. `_COMBLE_FILL` is gone entirely —
the comble is now composed as a section rather than a fraction.

Six residuals. Two were sourcing-honesty defects and have already been fixed by
the orchestrator; four remain.

## Already fixed (orchestrator)

**A10.0a — a citation was factually wrong.** `catalogue.py` cited the 1.61 m
*porte piétonne* to "9 rue du Conservatoire, plate daly_elevation_36". Three
errors: the 1.609 m door is at **No 77 boulevard de Sébastopol** (Paul Mesnard,
plate **daly_elevation_03**); `daly_elevation_36` does not exist in the corpus;
and 9 rue du Conservatoire's door is 1.630 m and *printed*, so the scale-bar
label was backwards. The value was right and the provenance was not, which is the
more dangerous of the two failures — corrected against the JSON.

**A10.0b — a twelfth quantity was promoted on WEAK data.**
`_COMPRESSED_UNDER_THE_FLOOR_IT_SERVES = 1.275` was marked SOURCED. It is not
among the eleven; its Première half derives from values the corpus marks WEAK by
name; and it is a *derived ratio*, which the measurements warn carry worse error
than their inputs. **Two WEAK values divided by one another do not make a sourced
one.** Value retained, claim withdrawn, reasoning recorded in the docblock.

## A10.1 — the pedestrian door breaks the bay-pitch floor, unguarded

A9 added a tripwire for a slot *wider* than `_BAY_PITCH_MAX`. There is no
corresponding guard below. The *porte piétonne* slot is 2.35 m against a
`_BAY_PITCH_MIN` of 2.70 m, giving a measured centre-to-centre pitch of **2.575 m**
on modest and ordinary buildings; narrow specials give **2.30 m**.

Either the floor genuinely does not apply to an entrance slot — in which case say
so explicitly, and guard what does apply — or the slot is too narrow. Do not leave
a stated ABSOLUTE bound silently violated on one side while it is enforced on the
other.

## A10.2 — D6 is improved but not closed

GRAND has fewer openings than MODEST on **2 of 8** frontages (18 m and 20 m), down
from 6 of 8. The named 16 m case is fixed. Residual cause: the carriage slot
(3.40 m) still takes 1.05 m more frontage than the pedestrian slot (2.35 m), which
is a third of a bay.

Note this may be *correct*: a building with a carriage arch genuinely spends
frontage on it. If so, the defect is in the comparison rather than the model —
compare like with like (same entrance type) and say so. Decide, on the
architecture, and record the reasoning.

## A10.3 — dormer count still falls as class rises

9 of 21 class/frontage combinations show it falling (12 m: 4/4/3/3; 18 m: 6/6/5/5;
20 m: 7/7/6/6). A9.1 required that it must not. A comble is floor, not show.

## A10.4 — the chamfer roof draws a self-crossing hip

`block.py:_chamfer_roof()` rebuilds the *pan coupé*'s roof node from the parent
building's roof props with `w` overridden to the chamfer width. It re-counts
`seam_count` for the narrower face but not every width-derived value, so the hip
geometry crosses itself — a bowtie in the sky at both ends of a block.

This is the **fifth** instance of one module holding a width-derived opinion that
another module contradicts. Fix it the same way as A9.3: derive once, put it in
the IR, consume it.

## A10.5 — a zero-width node, and the suite is red

`b/roof/no_dormer0` (kind=`special`) is emitted with `w=0.0`, 4,412 occurrences,
by rule `paris.terminate.dormer.clipped_by_the_hip`. The invariant fuzzer catches
it and **the suite is failing: 1402 passed, 1 failed.**

A dormer clipped out of existence should not be emitted at all. An element with no
extent is a lie in the IR — the same class of defect as A6.6's zero-height
ironwork. Emit nothing, or emit something with extent.

**The repo must end green.**

---

# Amendment 11 — adjudication of A10.3, and the close of the Second Empire lock

## A11.1 — A10.3's criterion is RETRACTED. The model was right.

A10.3 required that dormer count "must not fall as class rises". The verifier
reported it unmet — the table was digit-identical to the defect — and objected,
correctly, that the implementer had **rewritten the acceptance criterion in a test
docstring rather than met it**. A10.2's text explicitly licensed a "the metric is
wrong" argument; A10.3's did not.

The objection about *process* is upheld. The conclusion about *architecture* is
not, and I have verified it independently:

```
NAIVE (class picks the door)        modest ordinary comfort grand
  frontage 12 m                       4 ped   4 ped   3 car   3 car
  frontage 18 m                       6 ped   6 ped   5 car   5 car
  frontage 20 m                       7 ped   7 ped   6 car   6 car

LIKE-FOR-LIKE (carriage door forced for every class)
  frontage 12 m                       3       3       3       3
  frontage 18 m                       5       5       5       5
  frontage 20 m                       6       6       6       6
```

Dormer count is **exactly flat across class** once the entrance type is held
constant. The apparent fall is the carriage arch spending 1.05 m more frontage
(3.40 m slot vs 2.35 m) and therefore costing one axis — the identical mechanism
accepted in A10.2, and the dormers follow lit bays as they should.

Meeting A10.3 as written would require decoupling dormer count from the bays it
lights, which is worse architecture in service of a worse metric. **The criterion
is withdrawn; the like-for-like equality is the contract.**

Daly supports this: entitlement to a *porte cochère* is what distinguishes the
classes (Première 4/4, Deuxième 3/10, Troisième 0/2), while the door itself
differs by 0.4 % between the two classes that have one.

## A11.2 — The process point stands

Two waves running, an implementer has answered a requirement by arguing the
requirement was wrong. Both times the argument was **correct**. But an argument
belongs in the report, where a verifier and the orchestrator can weigh it — not in
a test docstring, where it silently becomes the new criterion.

Standing rule: **if you believe a requirement is wrong, implement nothing, say so
in your return value, and stop.** Encoding your own acceptance criterion in a test
is not an acceptable substitute, even when you are right.

## A11.3 — Accepted with a note: the absence marker

A10.5 offered "emit nothing, or emit something with extent". The weaker option was
taken: `no_dormer0` now carries `w = slot.width > 0` but `h = 0.0`, matching the
pre-existing `no_dormers` convention (`absence='dormer'`).

Accepted. An explicit, documented absence marker is not the same defect as an
element that claims extent it does not have — and consistency with the existing
convention is worth more than a local improvement. The zero-height census is now
fully accounted for: keystones (documented line-at-the-crown), absence markers,
and block datum lines.

## Status at the close of this wave

**Repo green: 1409 tests, all three guards clean.** The canonical Second Empire
case is calibrated against César Daly's 1864 measured plates, pinned by a golden
master that has been shown to bite, and its sourcing has survived two independent
audits — one of which caught a factually wrong citation and a twelfth quantity
promoted on WEAK data.

---

# Amendment 12 — two things that do not read at facade scale

Both are cases where the IR is **correct** and the drawing misrepresents it. Neither
is a rule defect; do not "fix" them upstream.

## A12.1 — the mansard break sits too high to be legible

A pre-1884 comble states `lower=45.0, upper=12.0, break_pct=0.906`. The silhouette
for a typical case (comble 3.20 m, parcel 16 m, so half-depth 8.0 m):

```
(0.00, eaves) → (2.90, +2.90) → (4.311, +3.20) → (8.00, +3.20)
     brisis at 45° for 2.90 m │ terrasson 0.30 m │ flat terrasse for 3.69 m
```

So the brisis is **90.6 %** of the comble and the terrasson is 0.30 m — a hairline.
Above it the roof runs *flat* for 3.69 m. At facade scale that reads as a plain
slab with a nick near the top, which is why A8's own verifier said it "reads as a
mansard only weakly".

**The comble height is not the problem.** Daly's sixteen buildings give a median
comble of **3.19 m** against the generator's 3.20 m — that is calibrated and
correct. The fold position is what is wrong.

The geometry is over-determined once the terrasson angle is fixed. With a brisis
at 45° folding at height *b*, and a terrasson at 12° running to the ridge at
mid-depth:

```
b + (half_depth − b)·tan(12°) = comble_height
1.906 + (8.0 − 1.906)·0.2126 = 3.20   →   break at 59.6 %, not 90.6 %
```

**Required:** derive the fold from the terrasson reaching the ridge, rather than
placing it near the ridge and flattening. A long flat *terrasse* belongs only on a
parcel deep enough to earn one; on an ordinary parcel the terrasson runs to the
ridge. Both slopes must be legible in a facade elevation.

Constraints that still bind: every point comes from `setback_at`; the silhouette
stays inside the envelope (the sweep asserts 0 violations); the 1884 and 1902
profiles keep their own shapes; and the lucarne must still fill the brisis — if
the brisis shortens, the lucarne follows it rather than overhanging.

## A12.2 — a garde-corps is drawn with the weight of a balcony

Four storeys carry ironwork on the canonical building. Two are genuine
*balcons filants* (bay-wide segments, 2.80–3.40 m, `guards='balcon_filant'`, on
storeys that really do carry a continuous `BalconyNode`). Two are
`guards='opening'` rails at **0.92 m and 1.20 m** — window-width *garde-corps* in
the reveal, so nobody falls out of a full-height window.

**The IR distinguishes them correctly.** The renderer does not draw the
distinction strongly enough, so four rails read as four balconies and the facade
loses the 2nd-and-5th rhythm that is the most recognisable thing about a
haussmannian elevation.

**Required — a renderer change only:**

- A **balcon filant** projects. It has a slab or console-borne floor, a balustrade
  standing on it, and it runs unbroken across the bays. Draw it with that weight.
- A **garde-corps** does not project. It is a light rail set **within the opening
  reveal**, visually subordinate: thinner bars, lighter stroke, no slab, no
  projecting shadow line.

The reading test: at facade scale a viewer should count **two** balconies on the
canonical building, and see the other rails as part of their windows.

Do not change which storeys carry ironwork — that comes from the 1823 ordonnance
via `reglement.balcony_rule` and is correct.

---

# Amendment 13 — the entresol belongs to the base, not to the upper facade

> **PARTLY RETRACTED BY AMENDMENT 17.** A13.2's *absorbed* entresol — the
> devanture spanning RdC + entresol as one framework — was a misreading of plate
> 77 and does not exist in the corpus. A17.2 deleted it; what survives as real
> variation is the entresol window's **head form**. A13.1 (the socle runs through
> the entresol, the emphatic string course crowns the base block) is correct and
> stands — see A17.3. Read A17 before acting on anything below.

Reported by the operator looking at a generated commercial boulevard building:
*"the comfortable doesn't have an entresol."* It does — `mezzanine`, 2.66 m
against a 3.39 m principal — but it does not **read** as one, and the source
shows why.

## What Daly does

Two plates, both Deuxième Classe, both by Paul Mesnard, both with a measured
entresol:

**No 77 boulevard de Sébastopol** (RdC 4.00 + entresol 3.10 = 7.10 m). The
entresol is **absorbed into the devanture**. The shopfront framework spans the
whole 7.10 m as one architectural object, and the entresol's windows are the
upper register of that glazing. There is no separate entresol band on the facade
at all — which is exactly why a modern awning at 3 rue La Fayette can swallow an
entresol without leaving a visible trace.

**No 120 boulevard de Sébastopol** (RdC 4.00 + entresol 3.10). The entresol *is*
expressed as its own band, but it belongs to the base: **arched openings**
(*arcs surbaissés*) in the **same ashlar/bossage coursing** as the ground floor,
standing on the shopfront entablature, with small individual railings. Together
the two levels read as a single two-storey commercial base, and the first
"proper" residential floor is the one above.

## What we do

The socle (`raised_bossage`) stops at the top of the rez-de-chaussée, and the
entresol sits on **plain wall** above it, with a small rectangular window —
a shrunken version of an upper-floor window. So it reads as a short residential
storey rather than as the top of the commercial base.

## A13.1 — Required

The **socle treatment runs through the entresol**, not just the rez-de-chaussée.
The commercial base is `RdC + entresol` where an entresol exists, and the strong
string course goes **above** the entresol — dividing commerce from residence —
rather than above the ground floor.

Note the current string courses are the wrong way round: 0.10 m above the
entresol against 0.20 m above the principal. The division that matters most is
the one at the top of the base.

## A13.2 — Required

Entresol openings get their **own treatment**, not a scaled-down upper window.
Both Daly forms are legitimate and both should be reachable:

- **absorbed** — the devanture spans RdC + entresol as one framework, and there
  is no separate opening band (77 Sébastopol)
- **arcaded** — arched openings in the base's own stone, on the shopfront
  entablature (120 Sébastopol)

Which one applies is a qualification decision. Do not let the renderer choose it,
and do not pick by date alone — both are 1864 and both are Deuxième Classe, so
this is variation within a class and period, which is what `DecisionStream` is
for.

## A13.3 — Not required, but note it

Our stack builds to **18.79 m of a 20.00 m ceiling (94 %)**. The five Daly
buildings with this exact stack sit at **19.05–19.98 m**. So the generator is
about a metre short of how hard the real ones pressed the limit. That is
`_FACADE_AMBITION`, it is INFERRED, and the measurements mark facade-ambition
values WEAK — so **do not calibrate it here**. Recorded as a known offset.

---

# Amendment 14 — the two-storey arched entrance

> **RATE AMENDED BY AMENDMENT 18.** A14.2 draws the tall arch at one rate for
> both entrance kinds, reasoning from "two carriage and two pedestrian" among
> Daly's four. That counts numerators only; against the denominators the kinds
> differ, and the rate is now kind-dependent. A14's form, geometry and
> applicability conditions are unchanged.

Requested by the operator: *"variations where a round porte cochère extends up to
include the entresol."* It is a real, documented form, and the measurement pass
had already flagged it — the Première Classe door-height table carries a
`height_excluding_two_storey_arch` field precisely because one outlier forced it.

## The evidence — 4 of 16 buildings, 25 % of the corpus

| Building | type | width | height | RdC | entresol |
|---|---|---:|---:|---:|---:|
| Avenue de l'Impératrice (Raban) | porte cochère | 2.62 | **7.30** | 4.30 | absorbed |
| 39 rue Neuve des Mathurins | porte cochère | 2.57 | **5.00** | 4.10 | 2.40 |
| 2 et 4 bd de Sébastopol (Davioud) | porte piétonne | 1.74 | **5.01** | 3.42 | 2.65 |
| 87 bd de Sébastopol | porte piétonne | 1.76 | **5.07** | — | — |

Against a one-storey median of 3.49 m (cochère) and 3.03 m (piétonne).

**The width does not move.** Carriage doors are 2.41–2.67 m whether they rise one
storey or two; pedestrian doors 1.36–1.91 m likewise. So the two-storey arch is a
*compositional* choice about height, made against an *absolute* width — the
absolute/proportional split appearing again, in the one element that is the
facade's ruler.

Note **39 rue Neuve des Mathurins is one of the five canonical-stack buildings**
(RdC + entresol + 4 étages, cornice 19.82 m). So the tall arch is not an
alternative to the entresol stack — it coexists with it, rising through the RdC
and into the entresol.

## The form, from the Impératrice plate

A round-headed arch spanning RdC + entresol, with:
- the leaves occupying roughly the lower storey
- a carved **tympanum / imposte panel** above them
- a **balconette with ironwork set inside the arch** at entresol level — the
  entresol's window for that bay, contained by the arch rather than beside it
- a sculpted **agrafe** (keystone) at the crown
- the arch springing from the same rusticated coursing as the flanking bays,
  whose RdC windows are themselves arched with bossage voussoirs

## A14.1 — Required

An entrance may span the base and the entresol as a single round-headed arch.
Reachable for both `carriage_entrance` and `pedestrian_entrance`.

- **Width stays ABSOLUTE and unchanged** — 2.60 m carriage, 1.75 m pedestrian,
  exactly as A9.2 calibrated them. A tall arch is not a wide one. Assert this.
- The arch's height spans RdC + entresol where an entresol exists; where one does
  not (Impératrice), it spans the equivalent height and the entresol is absorbed.
- The entresol's opening in that bay is **inside the arch** — a balconette with
  ironwork — not a separate window beside it.
- The head is **round**, not flat or segmental. That is what makes the form.

## A14.2 — How it is chosen

A qualification decision through `DecisionStream`, on a stable path. **Not** by
date (all four are 1864) and **not** by class alone (two Première, two Deuxième).
Roughly a quarter of buildings with an entrance should take it — but treat the
25 % as an observation from n=16, not a calibrated rate: mark the rate INFERRED.

Interacts with A13: where the entresol is `absorbed` into the devanture, the tall
arch reads as the natural entrance form; where it is `arcaded`, the arch springs
from the same coursing as the flanking arches. Both combinations must work.

## A14.3 — Layouts

Add the variations to `dev/harness/layouts.py` so they can be regenerated:
`A` (as built), plus a variant with the two-storey carriage arch, and one with
the two-storey pedestrian arch on a narrower parcel.

---

# Amendment 15 — the comble does not vary within an era

## The finding, stated precisely

Across eras the comble responds correctly to the envelope — the 1884 and 1902
decrees change the roof rule and the comble follows:

| year | comble heights produced across 180 sites |
|---|---|
| 1865 | **3.20 only** |
| 1887 | 6.72, 7.21, 7.47, 7.65, 8.12, 8.50 |
| 1905 | 7.17 … 17.00 |

**Within** the 45° era it is a constant. At 1865 the comble is 3.20 m for every
street width, parcel width, **parcel depth**, class and ground programme swept.

Daly's nine 1864 commercial buildings span **2.69, 2.77, 2.85, 3.18, 3.34, 3.45,
4.72, 6.80, 7.00 m** — the same era, a 2.6× range.

Consequence: two of the four commercial varieties are **unreachable**. Asked for
a comble-heavy building (target 7.00 m) and a middle one (4.72 m), the generator
returns 3.20 m in both cases, so they render as the same roof.

## An orchestrator error to record

A9.1 said *"the comble being class-invariant is CORRECT and Daly-supported."*
That over-read the evidence. Daly supports **"comble share is not a function of
class"** — which is why it is marked INSUFFICIENT. It does **not** support
"comble height is a constant". The measurements mark the quantity INSUFFICIENT
*because it is bimodal*, and bimodality is evidence of a variable with two modes,
not of an invariant. The wording licensed the stronger reading.

## A15.1 — Required

The comble is **chambres de bonne**, so its height follows the *programme it
carries*, bounded above by the envelope and the parcel depth.

The two Daly modes are one and two garret storeys:
- ~2.7–3.5 m — a single storey of garret, one row of *lucarnes* (6 of 9)
- ~4.7–7.0 m — two storeys, **two rows of lucarnes** (3 of 9)

The generator has a fixed one-storey allowance, which is why parcel depth never
binds and nothing else moves it. Make the **garret storey count** a decision —
1 or 2 — and let the comble follow.

Constraints that still bind:
- the silhouette stays inside the envelope; the current sweep reports **0
  violations, worst overshoot 0.000000 m**, and that must survive
- every point still comes from `setback_at`
- the 45° / arc / eighth-arc shapes per era are unchanged — this is about how far
  the comble is carried, not what curve it follows
- a two-storey garret needs the depth for it: on a shallow parcel the 45°
  diagonals meet before the second storey fits, and it must not be built

## A15.2 — What may NOT be calibrated

The **rate** — how often a building takes two garret storeys — is **INFERRED**.
Daly shows 3 of 9, but comble share is marked INSUFFICIENT and n=9 with a known
publication bias. Mark it inferred; assert only that both modes occur and that a
two-storey garret carries two dormer rows.

Do **not** key the choice to class: A9.1's retraction stands, and the evidence
that comble share is not a class function is the one thing here that *is* solid.
Programme and parcel depth are the honest drivers.

## A15.3 — the balconette clips through the archivolt (from the A14 gate)

In **90 of 210** tall arches the 0.90 m balconette is taller than the straight
part of the light beneath the springing (0.7615 m on layout AC), so its top rail
and outer stiles cross the springing and cut through the archivolt. Worst
overflow **0.138 m**, visible at 5000 px.

A garde-corps inside an arched opening has to fit under the springing, or sit
forward of the archivolt. It may not intersect the moulding. Derive its height
from the straight portion of the light, not from the flat-headed default.

## A15.4 — the tall pedestrian arch is too tall for its evidence

Ours: **6.11–6.35 m**. Daly's two examples: **5.01 m** (2 et 4 bd de Sébastopol,
Davioud) and **5.07 m** (87 bd de Sébastopol). We are **1.05–1.35 m above both**,
giving an aspect of 3.49:1 against Daly's 2.88:1.

The tall *carriage* arch is fine — 6.01–6.24 m sits inside Daly's 5.00–7.30 band.
It is the pedestrian form that overshoots, because both are being carried to the
same crown line.

A *porte piétonne* is narrower, so carrying it to the same height as a carriage
arch makes it disproportionately lanky. Let the pedestrian arch stop lower —
n=2 is thin, so **assert the ordering** (pedestrian arch shorter than carriage
arch, both clearly taller than their one-storey forms) rather than pinning a
value, and mark the proportion INFERRED.

Do **not** change the widths. A14 established 2.60 / 1.75 as byte-identical
across forms under a paired test, and that result stands.

---

# Amendment 16 — the garret trade is mispriced and unconditional

Found by testing against the operator's statement of the canonical stack:

> RdC · entresol · **noble floor with balcony** · 2 floors without · **1 floor
> with balcony** · comble

That is exactly Daly's five canonical-stack buildings — RdC + entresol + 4 étages,
*balcons filants* on the 1er and the 4e, cornices at 19.05–19.98 m. The generator
cannot currently produce it: it returns **3 étages at 15.99 m of a 20.00 m
ceiling (80 %)**, with the upper filant landing on the 3e.

Two separate faults, both in A15's garret trade.

## A16.1 — the facade pays for a band the parcel refuses to hold

| depth | programme | buys? | parcel holds | attics built | cornice |
|---:|---|---:|---:|---:|---:|
| 10 m | shop | **1** | 1 | **1** | **15.99 (80 %)** |
| 10 m | residential | 0 | 1 | 1 | 19.20 (96 %) |
| 12 m | shop | **1** | 1 | **1** | **15.99 (80 %)** |
| 14 m | shop | 1 | 2 | 2 | 15.99 (80 %) |

At 10 and 12 m the shop building gives up **4.01 m of facade and receives exactly
one garret storey — the same one the residential building gets for nothing.**

`_a_second_storey_of_chambres_de_bonne` decides to buy on street width, programme
and ceiling alone. `_garret_storeys_the_parcel_holds` then refuses to build it.
Nothing reconciles them, so the height is spent and never received.

This is the **sixth** instance of the same structural fault — two functions
holding independent opinions about one fact with nothing tying them together
(A4.1, A6.8, A7.3, A9.3, A10.4, now this).

**Required:** the purchase is conditional on the parcel actually delivering the
band. One function decides, or the buyer asks the holder first. Do not patch this
by adjusting a number.

## A16.2 — the band is priced at more than it costs

Buying the second garret storey deducts **4.01 m** of facade (20.00 → 15.99),
which is enough for a whole étage plus half of another, and is why the stack
loses two étages rather than one.

Daly's two deep-comble buildings sit at cornice **17.52** and **17.55 m** — they
gave up roughly **2.5 m** of a 20 m ceiling, not 4. A second garret band is one
storey of rooms; it should cost about one storey of facade, not two.

**Required:** the deduction is the band's own height, derived rather than
asserted. `BRISIS_RISE` is 2.90 m and already exists; whatever the figure, it
must be composed of the quantities it is made of rather than restated, in the
style `_stone_under_a_bought_garret` already uses.

**The rate stays INFERRED** — A15.2 stands, and Daly's 3-of-9 cannot calibrate it.

## A16.3 — the canonical stack must be reachable

After the fix, a shop on a 22 m street with a comfortable class must be able to
produce:

```
RdC · entresol · 1er (filant) · 2e · 3e · 4e (filant) · comble
cornice in the 19–20 m band, i.e. 95–100 % of the ceiling
```

Add it as a test, not merely a preset. This is the commonest real configuration
in the corpus (4 of 9 commercial buildings, 11 of 16 overall) and the generator
currently cannot reach it at all.

## What is NOT broken, and must not be "fixed"

- **The balcony rule is correct.** Its trace reads *"the noble floor and the top
  of the wall"*, and it places filants on the 1er and the last habitable storey.
  The 3e placement is a symptom of the short stack, not a fault in the rule.
- **The 6 m ordonnance is correct.** With no entresol the noble floor sits at
  3.70 m and correctly receives no balcony — which is precisely why the operator's
  standard requires the entresol.
- **Residential is correct**: 96 % of the ceiling, five étages.

---

# Amendment 17 — the "absorbed" entresol was a misreading. Retracting it.

## The error, and whose it was

A13 specified two entresol treatments and weighted them evenly:

- **absorbed** — "the devanture spans RdC + entresol as one framework, and there
  is no separate opening band", sourced to 77 bd de Sébastopol
- **arcaded** — the entresol as its own band in the base's stone, sourced to
  120 bd de Sébastopol

**The absorbed form is a misreading of plate 77 and does not exist there.** Read
at full resolution the plate shows:

- the **rez-de-chaussée** is a shopfront with a stall riser, stopping at a clear
  horizontal entablature
- **above that line**, the **entresol is a separate register** with its own short
  windows, each carrying a small ironwork garde-corps, set in ashlar with visible
  coursing between them
- the **porte piétonne** rises to the head of the RdC only, with a carved
  overpanel above it — not to the top of the entresol

So 77 and 120 show the *same* arrangement. What differs between them is only the
**head form** of the entresol window — rectangular at 77, segmental-arched at 120
— not whether the entresol has windows at all.

The mistake was mine, in the amendment text. The A13 verifier then checked our
render against my specification rather than against the plate independently, and
confirmed a wrong reading. Weighted 50/50, roughly **half of all commercial
buildings generated since A13 carry a treatment that no plate in the corpus
supports.**

## A17.1 — the generic ground floor

The default, and what both plates show:

| element | height |
|---|---|
| shop window | **the rez-de-chaussée only**, stopping at the entablature |
| entresol window | **its own short window** above that line, with a garde-corps |
| *porte piétonne* | **the rez-de-chaussée only**, with a carved overpanel |
| *porte cochère* | **rises to the top of the entresol** — the two-storey arch of A14 |

The asymmetry is the point: the **carriage** entrance is the one opening that
spans both levels, because a carriage has to pass under the entresol floor. The
pedestrian door does not, and neither does a shop window.

> **CORRECTED BY AMENDMENT 18.** The last row of that table is not a reading of
> either plate — neither 77 nor 120 has a carriage entrance — and 26 rue Bergère
> shows a porte cochère of 3.474 m under a 3.09 m entresol, stopping at the
> rez-de-chaussée. The asymmetry is real but it is a lean, not an absolute; it
> now lives in a rate. The first three rows stand as read.

## A17.2 — remove the absorbed form

Delete it rather than down-weight it. It is not a rare variant we happen to
over-produce; it is a form we invented. If a plate is later found showing a
devanture genuinely spanning both levels, it can come back with that citation.

What survives as real variation is the entresol window's **head form** —
rectangular (77 bd de Sébastopol) or segmental/arched (120 bd de Sébastopol) —
chosen through `DecisionStream` as A13.2 already does, with the rate INFERRED.

## A17.3 — keep what A13 got right

A13's other half stands and must not be undone:

- the **socle runs through the entresol**: RdC + entresol are one bossage-coursed
  block, and 77 shows exactly that
- the **emphatic string course sits above the entresol**, crowning the base block,
  not above the rez-de-chaussée

Those were right. Only the opening treatment was wrong.

## A17.4 — a process note

Two independent checks passed a form that no source supports, because both were
checking against my prose rather than against the plate. Where an amendment cites
a specific plate as its specification, the gate should require the verifier to
state **what it sees in the plate**, in its own words, before comparing it to the
render — not to confirm that the render matches the amendment.

---

# Amendment 18 — A17.1's carriage arch was asserted, not read

## The error, and where it came from

A17.1 gave the generic ground floor as a table of four rows, "what both plates
show". Three of those rows are readings of plates 77 and 120. The fourth is not:

| element | height |
|---|---|
| *porte cochère* | **rises to the top of the entresol** — the two-storey arch of A14 |

**Neither 77 nor 120 bd de Sébastopol has a carriage entrance.** Both have a
*porte piétonne*. So that row could not have been read off the plates it cites;
it was reasoned from clearance — a carriage has to pass under the entresol floor
to reach the cour — and then written down in the same table as the three rows
that were observed.

The reasoning is sound and it is not evidence. It says why a carriage door **may**
span the floor. It cannot say why every one must, and the corpus says they do not.

## The corpus, with denominators

`daly_measurements.json`, all 17 buildings, entresol against door height:

| | has entresol | of those, two-storey |
|---|---:|---:|
| *porte cochère* | 2 of 7 | **1 of 2** |
| *porte piétonne* | 7 of 10 | 1 of 7 |

The decisive record is **26 rue Bergère**: an entresol of 3.09 m under a porte
cochère measuring **3.474 m** — a carriage entrance that stops at the
rez-de-chaussée like any shop door. One measured plate in our own corpus, against
an amendment that said it could not happen.

The other five carriage entrances (Champs-Élysées 125 and 119, rue de la Paix 3,
rue de Rivoli 88, avenue de l'Impératrice) stand on entresol-less grand addresses,
where "two-storey" is not defined. Only **39 rue Neuve des Mathurins** (entresol
2.40 m, door 5.00 m) supports the tall form.

Note also what this overturns in the opposite direction. `TWO_STOREY_ARCH_RATE`
called the choice kind-blind because Daly's four tall entrances are "two carriage
and two pedestrian". That counts numerators. Against the denominators the two
kinds are **not** alike — 2 of 7 against 2 of 10, and 1 of 2 against 1 of 7 on the
population where the choice exists at all. A17.1 saw a real asymmetry and then
recorded it as an absolute.

## A18.1 — Required, and done

One draw for both kinds, at a rate the entrance kind sets. Not a branch, and not
a single blind rate either:

- `TWO_STOREY_ARCH_RATE` — 0.25, the *porte piétonne*, unchanged
- `TWO_STOREY_ARCH_RATE_CARRIAGE` — 0.40, the *porte cochère*

0.40 is **INFERRED and calibrated by nothing.** The corpus offers two denominators
and neither is the right one: 0.286 counts four entresol-less addresses where the
choice did not exist, and 0.50 is n = 2. The figure sits between them because the
honest reading is between them.

**Only the ORDERING is contractual, and it is two-sided:** the carriage arch is
likelier than the pedestrian one, AND it is still the minority of carriage
entrances. A later measurement pass should expect the number to move and must not
be able to move it past either bound without saying so.

## A18.2 — what forcing it had already broken

The unconditional form put an arch register on an opening filling its whole slot,
leaving no stone over the lintel — a curtain wall, which
`test_the_facade_is_stone_with_holes_in_it_not_a_curtain_wall` exists to forbid.
Two facade guards were failing on it. This is worth recording because the guards
caught it and the amendment's own gate did not: the gate asked whether the render
matched A17.1, and it did.

## A18.3 — the process note A17.4 should have applied to itself

A17.4 says that where an amendment cites a plate as its specification, the gate
must make the verifier state what it sees in the plate before comparing it to the
render. A17.1 broke that rule **inside the amendment that wrote it**, by putting
an asserted row in a table headed "what both plates show".

So the rule needs a second half, about writing rather than checking:

> A table that claims to be a reading of a source may contain only rows that
> were read from it. A row derived some other way — from physics, from
> convention, from what must surely be true — belongs in its own paragraph,
> labelled with what it was derived from, so that a later reader can see which
> claims have a plate behind them and which have an argument.

The failure mode is not believing something false. It is filing an inference in
the drawer marked *observation*, where nobody thinks to ask it for a source.

---

# Amendment 19 — the brisis is a wall, and the hip breaks where the roof does

Two findings from one question. The operator, looking at a contact sheet of every
preset, asked whether the post-1884 corner's pointed roof was right and whether
two storeys inside a comble were right. Neither was a false alarm.

## A19.1 — a mansard's hip is two timbers, not one

`derive_hip_arris` returned a single straight line at the section's **average**
pitch. A mansard is two planes — a steep brisis and a shallow terrasson — and the
average is precisely what it is not. Near the eaves the hip came out far too
shallow, which dragged the fold inward until it disappeared:

| | as drawn | as built |
|---|---:|---:|
| pavilion peak (preset `P`) | 6.21 m | **6.83 m** |
| brisis fold spans | **1.00 m** of a 15 m frontage | **9.68 m** |

So the roof read as a plain cone rather than a steep skirt under a small
pyramidal cap.

**A4.5 is not retracted, it is restated.** Its concern was reusing the curved
depth-section verbatim edge-on, which "bulged into an onion dome on a narrow
chamfer". Straightness was right; *singleness* was the error. The arris is now a
polyline whose every SEGMENT is straight, with a knot at the fold — and on a
post-1884 arc the lower segment is the arc's **chord**, which lies inside the
section by construction, so the dome cannot return.

The fold's height comes from the roof's own `break_pct`, per **A6.10**: where a
plane changes is a stated fact, not something to be guessed from a polyline
vertex, since "a curve refined for tolerance can carry an extra vertex nowhere
near the actual break".

**Required, and done.** One consequence worth recording rather than hiding: the
corrected hip is steeper near the ends, so the roof surface over the end bays
rose, and lucarnes that used to be clipped there now fit. The clipping guard is
still real — it fires on a 10 m frontage — and its test moved to one. The site
moved; the assertion did not weaken.

## A19.2 — the brisis carries a storey, and it is not a row of dormers

The deep-comble mode holds two garret storeys. That is **corpus-attested** and the
storey count is right. What we draw in them is not.

Read at full resolution, the two deep-comble plates show:

- **2 et 4 bd de Sébastopol** (comble 7.00 m) — the brisis is a **brick wall**.
  A full storey of moulded window surrounds with individual iron balconettes,
  and above it a row of small plain lights tucked under the eaves. **No dormer
  projects anywhere on that plate.**
- **1 bd de Sébastopol** (comble 6.80 m) — the brisis is faced in
  vertical-seamed metal. The **upper** row is a true *lucarne*: round-arched,
  scrolled consoles. The **lower** row is again windows set into the brisis
  face, each with its own balconette.

So the common form, on both, is a **lower storey whose windows sit in the plane
of the brisis** — not on it. A brisis steep enough (65–80°) is a wall that
happens to be roof, and it is built and faced as one: brick at 2 et 4, metal at
1 bd. Only the *upper* register is ever a dormer, and only on one of the two.

We draw both rows as pedimented dormers, so the lower row is wrong on both
anchors.

**Required.** Where a comble holds more than one garret storey, the LOWEST
garret's openings are windows in the brisis face — sill, surround and garde-corps
in the plane of the roof — and not dormers standing out of it. Dormers remain
what they are for: the register under the eaves, and every single-storey comble,
which is the majority.

**The face material is NOT required and must not be invented.** Brick at one
plate and metal at the other is n = 1 each; that is variation with no rate behind
it. What is contractual is the OPENING, which both plates agree on.

## A19.3 — where the wording came from

`LAYOUTS_COMMERCIAL.md` said this mode carried "two rows of *lucarnes*", sourced
to these plates. Neither shows two rows of lucarnes; one shows none at all. The
phrase was written from a picture in the head rather than from the plate, and it
survived because it lived in a layouts document rather than in an amendment —
where A17.4's "state what you see before you compare" and A18.3's "a table that
claims to be a reading may hold only rows that were read" would have caught it.

**Those two rules apply to every document in `dev/`, not only to amendments.**
A caption is a claim.

---

# Amendment 20 — the tall entrance is one door, and it is 5 m tall

Reported by the operator from the contact sheet: *"the door itself from ground
level to the top of the curve should be one solid door. The drawings have a
masonry piece and a fence between the RdC and the entresol."* Both true, and
checking them turned up a third fault neither of us had named.

## What the plates show

Two of them draw this object at large scale, and they agree.

**`daly_detail_56` — 2 et 4 bd de Sébastopol, "Porte de l'Entrée N°4"** (Davioud;
the 5.01 m *porte piétonne*). One joinery assembly inside one frame: two
panelled leaves with arched glazed heads, a carved overpanel above them, a
glazed overlight above that, and a carved entablature crowning the whole. A
guilloche architrave runs unbroken up both sides. **Nothing crosses it** — no
band, no rail, no masonry.

**`daly_elevation_52` — 39 rue Neuve des Mathurins** (the 5.00 m *porte
cochère*). Tall panelled leaves running up into a carved tympanum, all inside a
single archivolt with its rosette-studded moulding. Again nothing crosses it,
and the arch springs from *below* the rez-de-chaussée ceiling — the arch is a
head on a door, not a composition spanning two storeys.

## A20.1 — nothing crosses the opening

We draw five things where the plates draw one: leaves, a carved panel, the
storey's own ledge, **a garde-corps**, and a separate glazed light above it.

The garde-corps is the worst of them, and it came from A14.1's own words — "the
entresol's opening in that bay is inside the arch — a balconette with ironwork".
No plate shows it. A rail across a *porte cochère* would also be a rail across
the way in, which is what the opening is for.

**Required.** The tall entrance is ONE opening: leaves rising to the springing,
a carved tympanum inside the head, and no band, rail or reveal at the storey
line. `the_entresol_of_a_tall_arch_is_a_balconette_inside_it` is deleted.

**A14.1's two-REGISTER device stands.** It is not a claim about what is visible:
it exists because an opening rectangle handed across a storey joint gets painted
over by the wall of the storey it trespasses into. What goes is everything that
made the joint show.

## A20.2 — 5.00 m, and it is ABSOLUTE

Neither "to the top of the entresol" (A17.1) nor "to the entresol windows'
heads" (what we build today) is what the corpus measures.

| building | kind | width | **height** | crown above the RdC |
|---|---|---:|---:|---|
| 39 rue Neuve des Mathurins | cochère | 2.57 | **5.00** | 0.90 m — 38 % of the entresol |
| 2 et 4 bd de Sébastopol | piétonne | 1.74 | **5.01** | 1.59 m — 60 % of the entresol |
| 87 bd de Sébastopol | piétonne | 1.76 | **5.07** | — |
| Avenue de l'Impératrice | cochère | 2.62 | 7.30 | — |

**Three of the four agree within 0.07 m**, across two architects and both
entrance kinds, while their widths differ by 48 %. That is not a proportion of
anything on the building — it is an absolute, and the tightest one this corpus
has produced. Ours currently builds **6.08 m**, crowning 78 % up the entresol.

**Required.** The tall entrance's height is ABSOLUTE, ~5.0 m, SOURCED — offered
only where the base block can carry it, as A14.2 already tests. It does not
follow the entresol's height, its windows, or its ceiling.

The Impératrice's 7.30 m is **Première Classe** and is left as the exception it
is; a fourth reading is not a rate. If the grand class is later shown to carry a
taller arch as a rule, that is a separate finding needing more than n = 1.

## A20.3 — a correction to the operator's own reading

The operator gave the rule as "the curve should match the top of the entresol
windows". That is what the generator already does — arch crown and entresol
light head both land at 6.077 m on preset `AC` — and the plates put the crown
*below* the window heads, not level with them: at Mathurins the lights' heads
stand at ~6.27 m above the pavement against the arch's ~5.39 m.

So the instinct was right and the diagnosis was better than the rule offered
with it: the arch is too tall. Recorded because a rule accepted from a correct
observation is still an unsourced rule, which is the A13 failure exactly.

---

# Amendment 21 — a garde-corps stands in its opening, not on the wall below it

Reported by the operator alongside A20: *"the railings are correct on the étage
noble where they match the bottom of the windows since they are actually doors
and balconies and line up with the floor. On the 3rd and 4th floor, it's a
traditional window and the railing lines up inside the window opening."*

Both halves confirmed, and the second was a fault.

## What we built

| storey | sill above the floor | railing base | |
|---|---:|---|---|
| principal | **0.00** — a *porte-fenêtre* | at the opening's foot | correct |
| 3e / 4e | **0.90** — an ordinary window | **at the storey floor** | wrong |

On every ordinary window the railing was drawn from the floor and stopped
exactly where the glass began — a rail standing on the blank wall UNDER the
window, guarding masonry. Nothing can fall through a wall.

## What plate 77 shows

Every railing on that facade crosses its own light. Not one stands on masonry
beneath a window. The bar sits on the appui, inside the reveal, over the glass.

## A21.1 — one rule, told apart by the opening's own sill

The base of a garde-corps is the **opening's own foot**. On a *porte-fenêtre*
that is the floor, which is why the noble floor's railing lines up with the
floor line — not because that storey is special, but because its light comes
down to it. On a window standing on an appui it is the appui.

One expression, both cases, and the noble floor's answer is unchanged.

## A21.2 — and what stands on an appui is a different object

Where the light comes down to the floor the iron is a **guard**: a body could
walk through, so it is the full `sill_lean_height`.

Where the light stands on an appui, **the appui IS the guard** — the same
0.90 m, which is not a coincidence but the same fact about the same body — and
the iron across it is a *barre d'appui* over the openable lower sash. It is
therefore a share of the LIGHT and not an absolute off the floor.

`BARRE_D_APPUI_SHARE_OF_LIGHT = 0.40`, **INFERRED from a reading**: measured on
plate 77 at two storeys independently, where the bar covers 0.40 and 0.42 of its
light. The second reading is the check, not the source.

**A *balcon filant* keeps the absolute either way.** It is a barrier standing at
the balcony's own floor, and what is behind it does not change how high a body
leans on it. The rule states both facts; `compose` uses whichever fits the shape
it is hanging, because the rule is storey-scope and cannot see the light.

## A21.3 — one iron, two weights

A12.2 gave the garde-corps a lighter **colour** as well as lighter lines, so the
same wrought iron read as two metals on one facade: a *balcon filant* in black
over windows railed in grey.

What differs between them is **depth, not material**. A filant stands on a slab
in front of the wall; a garde-corps sits in the reveal behind it. So the line
weights stay apart — that is the depth cue, and A12.2 is right about it — and
the colour does not.

## A21.4 — a filant is stepped out onto wherever it runs

`sill_height_for` and `noble_floor_steps_out_onto_its_balcon_filant` both carried
a `rank_from_principal == 0` test beside the filant test, with a comment
admitting it: *"the second filant, along the top of the wall, guards a window
rather than carrying a room out onto a terrace (INFERRED)"*.

Plate 77 shows the upper filant's windows coming down to the balcony floor
exactly as the noble floor's do. A balcony nobody can step onto is a railing,
and the storeys that have a railing rather than a balcony already draw one.

**Required.** The condition is the filant, not the rank.

### The bound the facade imposes

With one exception, which is not a rank test in disguise but a fact about the
building. A frontage whose **noble floor** sits below the 1823 threshold has no
balcony there. If the second filant still took its window's sill away, the TOP
storey would carry the tallest opening on the facade and out-rank the floor the
building exists to show off — measured, on an 1862 shop frontage:

```
window heights by rank   {0: 1.79, 1: 1.58, 2: 1.40, 3: 2.04}
```

So the upper filant is stepped out onto **where the noble floor's own is**.
Where the noble floor never got a balcony, the rail along the top of the wall is
a guard and the window behind it keeps its sill.

This needs the noble floor's level to be askable from any storey, which is
context **EXTENSION 6** (`principal_level`) — an envelope-level height in the
same species as `base_block_top`, and a LEVEL rather than a floor number, so
moving the noble floor moves it by itself.

### And what this splits

`test_across_a_whole_facade_the_noble_floor_carries_the_tallest_openings` was
making two claims in one sequence, and a walked-through opening at the top of
the wall broke it. A *porte-fenêtre* is not an ordinary window — this codebase
says so everywhere else — so the two are now asserted separately:

- ordinary windows, the ones with a sill to lean on, fall off upward
- the noble floor carries the **tallest opening on the facade**, which that
  test's own name claimed and its body never checked

Neither is weaker than what it replaced, and the second is new.

---

# Amendment 22 — the sill is the allège, not the leaning height

Reported by the operator from the contact sheet: *"the third and fourth floor
windows are too high within their row and crowd the separation with the new
floor. the reference images show a much more regular spacing."*

Both halves true, and the cause was one word doing two jobs.

## The measurement

Our upper storeys against 77 bd de Sébastopol, as fractions of the storey:

| | plate 77 | ours (before) |
|---|---:|---:|
| light | **78–83 %** | 60–63 % |
| below it | ~10 % | **28–30 %** |
| above it | ~10 % | 9 % |

The margin *above* was right — `lintel_bearing_depth` is 0.30 m and **SOURCED
twice**, from printed callouts on two plates in two classes. It stays. What was
wrong is the margin below, and it was wrong by 0.60 m, which is why the light
came out short and its head sat one bearing off the floor band.

## A22.1 — two different heights, one name

`sill_lean_height` is 0.90 m and **INFERRED** — its own docstring says so: *"a
sill height an adult can lean on without bending."* That number is real. It is
the height a body leans on, which is the top of the **guard**.

It is not the top of the **masonry**. A Paris *croisée* comes down onto a low
breast and the iron *barre d'appui* carries the rest of the way to the leaning
height — which is precisely what A21 found when it put the railing inside the
opening rather than on the wall beneath it. A21 and A22 are the same discovery
arriving from two directions.

**Required.** The sill of an ordinary window is `window_allege_height`, and
`sill_lean_height` keeps the job it actually names: the guard, and the *balcon
filant*'s rail.

## A22.2 — the number, and its limit

**0.30 m, SOURCED against 77 bd de Sébastopol.** Daly measures that facade's
upper storeys at 3.043 / 2.870 / 2.991 m and its aspects at 1.923 / 1.761 /
1.954 on a typical width of 1.27 m. Subtract each light and the 0.30 m lintel
bearing from its storey:

```
0.30    0.33    0.21   m
```

Three storeys, one plate, one number. It is also **exactly**
`entresol_allege_height`, reached from a different plate — corroboration, not
duplication, and kept as two constants so moving one cannot silently move the
other.

**The limit, recorded rather than buried.** Run the same subtraction over all 32
upper storeys in the corpus and it spreads **0.21–1.76 m with a median back at
0.90**. That reconstruction is noisy because `opening_width_typical` is one
figure per building set against per-storey aspects, so it drifts on any building
whose upper windows are not the typical width. 77 is the tightest and most
internally consistent case and it is the plate this model is calibrated against
elsewhere. A later measurement pass with a scale bar — the 1881 rue de Rennes
sheet, or the unidentified dimensioned survey drawing — settles it directly
instead of by subtraction.

## What it moved

Every window on every building. Goldens: all four, in `y`/`h`/`w`/`x`,
`sill_height`, `pier_width`, `lintel_height` — the openings growing and dropping,
and their surrounds and railings following. Upper storeys now read 80–81 % light
against the plate's 78–83 %, with 0.30 m above and 0.30 m below.
