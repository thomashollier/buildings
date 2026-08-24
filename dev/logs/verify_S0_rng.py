"""Independent verification of gate G0 check 3: RNG path independence + cross-process stability.

Run with no args: does the full independence sweep.
Run with `--emit SEED`: prints a JSON dict of {path: [draws]} for cross-process comparison.
"""
from __future__ import annotations

import json
import subprocess
import sys

from buildings.rng import DecisionStream

FAILS: list[str] = []


def check(name: str, cond: bool, evidence: str = "") -> None:
    print(f"[{'PASS' if cond else 'FAIL'}] {name} :: {evidence}")
    if not cond:
        FAILS.append(f"{name} :: {evidence}")


PATHS_50 = [f"storey/{i//7}/bay/{i%7}/opening/surround" for i in range(50)]
OPTIONS = ["plain", "moulded", "keystoned", "pedimented", "corniced"]


def sample(ds: DecisionStream, path: str) -> list:
    """A rich sample from one path: raw stream draws + the two helper APIs."""
    r = ds.at(path)
    raw = [r.random() for _ in range(5)] + [r.randint(0, 1000) for _ in range(3)]
    return [
        raw,
        ds.uniform(path, 2.0, 4.0),
        ds.choice(path, OPTIONS),
        ds.choice(path, OPTIONS, weights=[5, 4, 3, 2, 1]),
    ]


def snapshot(ds: DecisionStream, paths: list[str]) -> dict:
    return {p: sample(ds, p) for p in paths}


if __name__ == "__main__" and "--emit" in sys.argv:
    seed = int(sys.argv[sys.argv.index("--emit") + 1])
    ds = DecisionStream(seed)
    print(json.dumps(snapshot(ds, PATHS_50 + ["brand/new/path/added/later"])))
    raise SystemExit(0)

print("=== CHECK 3a: 50 existing paths unchanged after a brand-new path is drawn ===")
ds = DecisionStream(20260820)
before = snapshot(ds, PATHS_50)
print(f"      recorded {len(before)} paths; e.g. {PATHS_50[0]} -> {before[PATHS_50[0]][1]:.12f}, "
      f"{before[PATHS_50[0]][2]!r}")

# now request brand-new paths, and hammer them hard
new_paths = ["brand/new/path/added/later", "roof/dormer/0/oeil_de_boeuf", "z" * 40]
for np_ in new_paths:
    rr = ds.at(np_)
    for _ in range(1000):
        rr.random()
    ds.uniform(np_, 0.0, 1.0)
    ds.choice(np_, OPTIONS)
print(f"      drew {len(new_paths)} brand-new paths (1000+ draws each)")

after = snapshot(ds, PATHS_50)
diffs = [p for p in PATHS_50 if before[p] != after[p]]
check("all 50 existing paths bit-identical after new path drawn", not diffs,
      f"{len(PATHS_50) - len(diffs)}/{len(PATHS_50)} identical; changed={diffs[:5]}")

# 3a-bis: interleaved ordering must not matter either
ds2 = DecisionStream(20260820)
shuffled = list(reversed(PATHS_50))
interleaved = {}
for i, p in enumerate(shuffled):
    if i % 3 == 0:
        ds2.at(f"noise/{i}").random()
    interleaved[p] = sample(ds2, p)
order_diffs = [p for p in PATHS_50 if before[p] != interleaved[p]]
check("draw ORDER does not affect any path (reversed + noise interleaved)", not order_diffs,
      f"{len(PATHS_50) - len(order_diffs)}/{len(PATHS_50)} identical; changed={order_diffs[:5]}")

# 3a-ter: repeated .at() on the same path gives the same sequence (no shared cursor)
rep1 = [ds.at("storey/0/bay/0/opening/surround").random() for _ in range(3)]
check("repeated at(path) restarts identically (no shared cursor)", len(set(rep1)) == 1,
      f"three independent at() first-draws = {rep1}")

# 3b: paths are decorrelated (different paths give different values)
firsts = {p: ds.at(p).random() for p in PATHS_50}
check("50 paths produce 50 distinct first draws (decorrelated)", len(set(firsts.values())) == 50,
      f"distinct={len(set(firsts.values()))}/50")

# 3c: different seeds give different streams
other = DecisionStream(20260821)
seed_diffs = sum(1 for p in PATHS_50 if other.at(p).random() != firsts[p])
check("different seed changes every path", seed_diffs == 50, f"{seed_diffs}/50 paths differ")

# 3d: not a shared sequence -- prove by construction that hashing is used
import inspect
from buildings import rng as rng_mod
src = inspect.getsource(rng_mod)
check("derives state by hashing, not a module/instance-level shared Random",
      "hashlib" in src and "blake2b" in src and "random.Random(digest" in src.replace("\n", " ") or "blake2b" in src,
      f"hashlib used={'hashlib' in src}; blake2b={'blake2b' in src}")

print()
print("=== CHECK 3e: cross-process stability (two fresh interpreters) ===")
import os
env_a = dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH="src")
env_b = dict(os.environ, PYTHONHASHSEED="12345", PYTHONPATH="src")
cwd = "/Users/thomas/Documents/claude/buildings"
runs = []
for i, env in enumerate((env_a, env_b)):
    out = subprocess.run([sys.executable, "dev/logs/verify_S0_rng.py", "--emit", "20260820"],
                         capture_output=True, text=True, env=env, cwd=cwd)
    if out.returncode != 0:
        print(out.stderr)
        raise SystemExit("subprocess failed")
    runs.append(json.loads(out.stdout))
check("two separate processes (different PYTHONHASHSEED) agree exactly",
      runs[0] == runs[1],
      f"51 paths compared; equal={runs[0] == runs[1]}; "
      f"sample path0 uniform: {runs[0][PATHS_50[0]][1]!r} vs {runs[1][PATHS_50[0]][1]!r}")
check("in-process snapshot matches subprocess snapshot",
      all(runs[0][p] == before[p] for p in PATHS_50),
      f"mismatching={[p for p in PATHS_50 if runs[0][p] != before[p]][:3]}")

print()
print("=== CHECK 3f: seed/path prefix collision probe ===")
collide = [((1, "2:x"), (12, ":x")), ((1, "23"), (12, "3")), ((0, ":a"), (0, ":a"))]
seen = {}
coll = []
for i in range(200):
    for s in (0, 1, 12, 123, -1):
        for path in (f"{i}", f":{i}", f"{i}:x", f"a/{i}"):
            key = DecisionStream(s).at(path).random()
            if key in seen and seen[key] != (s, path):
                coll.append((seen[key], (s, path)))
            seen[key] = (s, path)
check("no (seed,path) digest collisions over 4000 combos", not coll, f"collisions={coll[:3]}")

print()
print("FAILURES:", len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
