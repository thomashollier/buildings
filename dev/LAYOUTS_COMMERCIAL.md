## Commercial varieties — the four presets, and the corpus behind them

"Commercial" = a building with an entresol, which in this corpus means a shop
ground floor. Nine of the sixteen qualify.

Sorted by comble height, they split cleanly — and the split explains why the
measurement pass marked **comble share INSUFFICIENT to calibrate**: it is not
noisy, it is **bimodal**. Two strategies, not one number.

| building | ét | cornice | comble | share | total | door h |
|---|---:|---:|---:|---:|---:|---:|
| 2 et 4 bd de Sébastopol (Davioud) | 3 | 17.52 | **7.00** | .285 | **24.52** | 5.01 |
| 1 bd de Sébastopol | 3 | 17.55 | **6.80** | .279 | **24.35** | 3.13 |
| 26 rue Bergère | 3 | 18.74 | 4.72 | .202 | 23.46 | 3.47 |
| 6 bd Saint-Germain | 4 | 19.05 | 3.45 | .153 | 22.50 | 3.00 |
| 77 bd de Sébastopol | 4 | 19.48 | 3.34 | .146 | 22.82 | 2.99 |
| 39 rue Neuve des Mathurins | 4 | 19.82 | 3.18 | .138 | 23.00 | **5.00** |
| 9 rue du Conservatoire | 3 | 18.15 | 2.85 | .136 | 21.00 | 2.72 |
| 120 bd de Sébastopol | 4 | 19.98 | 2.77 | .122 | 22.75 | 3.38 |
| 63 bd de Sébastopol | 4 | 19.72 | 2.69 | .120 | 22.41 | 3.03 |

**Cornice and comble run opposite.** The buildings that stop the facade ~2 m short
of the ceiling carry combles more than twice as deep — and end up the **tallest in
the whole corpus**. Total height varies far less (21.0–24.5 m) than the split
between facade and roof (share .120–.285).

I am *not* asserting the mechanism. Deeper parcel, more *chambres de bonne*, or
both — the corpus carries **no parcel depths**, so the cause is not recoverable
from it. What is observable is that both strategies existed on the same boulevard
in the same year.

---

## The presets

These are the four `C*` entries in `dev/harness/layouts.py`, which is the
authoritative definition — run `python3 dev/harness/layouts.py C1 C2 C3 C4` to
print the stack each actually produces. **The keys were renumbered when A15/A16
reworked the garret trade; this document previously described a different C1–C3
and has been brought back into line with the code.**

### C1 · Comble-heavy — height in the roof
`street 22 m · parcel 11 m · depth 16 m · 1865 · grand · shop`
3 étages under a deep **two-storey** garret, two rows of openings in it. Cornice
built to 16.93 m of a 20.00 m ceiling (85 %) — the height goes into the roof.

Two conditions must hold together and both are structural: the street must clear
the 14.81 m of stone a bought garret stands on, which only the >20 m step does;
and the parcel must be deep enough to hold two garret bands before the 45° slopes
meet, which is 12.20 m.

*Daly: 2 et 4 bd de Sébastopol (Davioud), cornice 17.52 / comble 7.00 / total
24.52 — the tallest in the corpus, reached by building the facade lower. Also
1 bd de Sébastopol (17.55 / 6.80). Ours reaches comble 6.10 against 7.00, a
residual of −0.90 m; the cap is decree ridge 3.20 + one brisis rise 2.90.*

> **This entry used to say "two rows of *lucarnes*", and that was a description
> of something nobody read off a plate.** Two rows of *openings* is right and
> both plates show it. What neither shows is a lucarne in the lower row:
>
> - **2 et 4 bd de Sébastopol** — the brisis is a **brick wall**. A full storey
>   of moulded window surrounds with individual balconettes, and above it a row
>   of small plain lights under the eaves. Nothing projects.
> - **1 bd de Sébastopol** — the brisis is faced in vertical-seamed metal. The
>   **upper** row is a true lucarne (round-arched, scrolled consoles); the
>   **lower** row is again windows set in the brisis face with balconettes.
>
> We draw both rows as pedimented dormers, so the lower row is wrong on both
> anchors. See **Amendment 19**.

### C2 · The middle strategy — **deliberately unreachable**
`street 20 m · parcel 13 m · depth 13 m · 1865 · comfortable · shop`
Kept as a **failing** case rather than deleted. The comble is either one garret
band or two, so the reachable set is roughly [2.0, 3.2] and [5.9, 6.1] with
nothing between, and a 4.72 m comble sits in the gap.

Whether the gap is wrong is genuinely open: Daly's two independent readings of
this building disagree (4.32 vs 5.12), so the target is inside the corpus's own
error bar. Left here so the gap stays visible instead of being quietly rounded
to a neighbour.

*Daly: 26 rue Bergère, cornice 18.74 / comble 4.72 / total 23.46, and a
**one-storey** porte cochère of 3.474 m under a 3.09 m entresol — the record that
refutes A17.1's compulsory two-storey arch (see Amendment 18).*

### C3 · The small end
`street 14 m · parcel 11 m · depth 10 m · 1865 · comfortable · shop`
3 étages, low cornice, shallow comble — the shortest commercial building.

A 14 m street never reaches the >20 m step, so the ceiling binds at 17.55 m and
the 14.81 m stone bar is never cleared: no bought garret is possible here whatever
the programme wants, and the shallow parcel would refuse it anyway. This is the
case where the envelope, not ambition, decides how big the building is.

*Daly: 9 rue du Conservatoire, cornice 18.15 / comble 2.85 / total 21.00.*

### C4 · Facade to the ceiling
`street 22 m · parcel 15 m · depth 11 m · 1865 · comfortable · shop`
4 étages pressed to the cornice limit, **one-storey** garret. Cornice 19.20 m of
20.00 m (96 %).

The mirror of C1 and the commonest case, 4 of the 9. Same 22 m street, so the
same ceiling and the same stone bar cleared — but at 11 m the parcel is too
shallow to hold a second garret band, so the trade is not on offer and the height
stays in the facade. **Depth, not money, is what separates this from C1.**

*Daly: 39 rue Neuve des Mathurins (cornice 19.82 / comble 3.18, two-storey porte
cochère 2.57 × 5.00). Also 120 / 63 / 77 bd de Sébastopol and 6 bd Saint-Germain.*

---

### What the four span

| | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| facade/roof strategy | max roof | *(unreachable)* | envelope-bound | max facade |
| étages | 3 | — | 3 | 4 |
| built / ceiling | 85 % | 96 % | 96 % | 96 % |
| garret bands | 2 | — | 0 | 1 |
| what decides it | depth ≥ 12.20 m | — | street step | depth < 12.20 m |

C1 and C4 are the pair that matters: the same street and the same ceiling, split
only by parcel depth. C3 is the case where the street decides instead. C2 is a
known hole between the two comble modes, kept visible on purpose.

**Entrance height** is a separate axis and does not belong to any one preset — see
`A` / `AC` / `AP` in `layouts.py`, which hold street, parcel, date, class and
programme fixed and move only the entrance. Both entrance kinds draw for the
two-storey arch, at different rates (Amendment 18).

**The entresol has one treatment.** A13 claimed two — *absorbed* into the
devanture (77 bd de Sébastopol) against *arcaded* in the base's own stone (120) —
and the absorbed form was a misreading of plate 77 that A17.2 retracted. Both
plates show the same arrangement: the devanture closes at a full-width
entablature over the rez-de-chaussée and the entresol above it is its own register
in the stone, with its own short lights on a low *allège*, each carrying a
garde-corps. What genuinely varies between the two plates is the **head** those
lights are turned with — square at 77, *arc surbaissé* at 120 — drawn per frontage
on `facade/entresol/head`.

**Overlap, stated honestly:** 2 et 4 bd de Sébastopol anchors C1 and also carries
a two-storey pedestrian arch. The varieties are not orthogonal axes; they are
combinations that occur. Four presets sample the space, they do not partition it.
