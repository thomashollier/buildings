"""Mutation test: does the implementer's own suite actually catch breakage in roles.py?"""
from __future__ import annotations
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path("/Users/thomas/Documents/claude/buildings")
TGT = ROOT / "src/buildings/typologies/paris/roles.py"
BAK = Path("/private/tmp/claude-501/roles_bak.py")
BAK.parent.mkdir(parents=True, exist_ok=True)
orig = TGT.read_text()
BAK.write_text(orig)

MUTANTS = {
    "M1 ties break to HIGHEST not lowest":
        ("return min(i for i in candidates", "return max(i for i in candidates"),
    "M2 principal = FIRST tall, not tallest":
        ("tallest = max(storeys[i].width for i in candidates)",
         "tallest = max(storeys[i].width for i in candidates) * 0.0 + storeys[candidates[0]].width"),
    "M3 base exclusion removed":
        ("if i != base_idx and i != mezzanine_idx and not attic_flags[i]",
         "if i != mezzanine_idx and not attic_flags[i]"),
    "M4 mezzanine exclusion removed from principal pool":
        ("if i != base_idx and i != mezzanine_idx and not attic_flags[i]",
         "if i != base_idx and not attic_flags[i]"),
    "M5 mezzanine ratio 0.75 -> 0.0 (never a mezzanine)":
        ("_MEZZANINE_RATIO = 0.75", "_MEZZANINE_RATIO = 0.0"),
    "M6 mezzanine ratio 0.75 -> 1.5 (almost always a mezzanine)":
        ("_MEZZANINE_RATIO = 0.75", "_MEZZANINE_RATIO = 1.5"),
    "M7 attic predicate >= becomes > cornice+100 (never an attic)":
        ("return slot.start >= cornice_height - _EPS", "return slot.start >= cornice_height + 100.0"),
    "M8 attic predicate always true above base":
        ("return slot.start >= cornice_height - _EPS", "return slot.start > 0.0"),
    "M9 rank_from_principal sign flipped":
        ("rank = i - principal_idx if principal_idx is not None else 0",
         "rank = principal_idx - i if principal_idx is not None else 0"),
    "M10 index_from_top off by one":
        ("index_from_top=n - 1 - i,", "index_from_top=n - i,"),
    "M11 base is the TOP slot":
        ("base_idx = 0 if n > 0 else None", "base_idx = (n - 1) if n > 0 else None"),
    "M12 mezzanine eligible at index 2 instead of 1":
        ("return 1 if storeys[1].width < _MEZZANINE_RATIO * median_habitable else None",
         "return 2 if n > 2 and storeys[2].width < _MEZZANINE_RATIO * median_habitable else None"),
}

def run(target):
    r = subprocess.run([sys.executable, "-m", "pytest", target, "-q", "--no-header", "-x"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or [""])[-1]

print("baseline full suite:", run("tests/"))
print()
survivors = []
for name, (a, b) in MUTANTS.items():
    if a not in orig:
        print(f"SKIP  {name}  (anchor not found)")
        continue
    TGT.write_text(orig.replace(a, b, 1))
    rc_roles, out_roles = run("tests/unit/test_roles.py")
    rc_all, out_all = run("tests/")
    killed = rc_all != 0
    print(f"{'KILLED' if killed else 'SURVIVED':9s} {name}")
    print(f"          test_roles.py: rc={rc_roles} {out_roles}")
    print(f"          full suite   : rc={rc_all} {out_all}")
    if not killed:
        survivors.append(name)
    TGT.write_text(orig)

TGT.write_text(orig)
print()
print("SURVIVORS (undetected mutations):", survivors or "none")
assert TGT.read_text() == orig, "restore failed!"
print("roles.py restored OK")
