"""Addressable, decorrelated decision streams (I5).

The hard requirement: every decision in the system is reached by a stable
dotted path (`"bay/3/opening/surround"`), and the stream for that path is
derived independently by hashing `(seed, path)` — never by pulling the next
value off one shared `random.Random` instance. A single shared sequence would
mean every decision's value depends on the number and order of decisions made
before it; add one new decision anywhere and every later draw shifts. That is
exactly the failure this module exists to rule out: pinning one decision, or
adding a brand-new kind of decision later, must not perturb any other path's
result, ever.

`blake2b` is used (not the builtin `hash()`) because `hash()` is salted per
process by default (`PYTHONHASHSEED`) — it would break the "same (seed, path)
=> same sequence, forever" guarantee across process restarts. `blake2b` is a
pure, unsalted function of its input bytes.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class DecisionStream:
    """One `DecisionStream` per seed. Every `path` string addresses an
    independent, reproducible `random.Random` — the streams share nothing."""

    def __init__(self, seed: int) -> None:
        self._seed = seed

    @property
    def seed(self) -> int:
        return self._seed

    def at(self, path: str) -> random.Random:
        """Independent, decorrelated stream keyed by a stable path.

        Same (seed, path) => same sequence, forever. Adding a NEW path must
        not perturb any existing path — true here because each path's state
        is derived on its own from `(seed, path)`, with no shared cursor for
        a new draw to disturb.
        """
        payload = f"{self._seed}:{path}".encode("utf-8")
        digest = hashlib.blake2b(payload, digest_size=16).digest()
        return random.Random(digest)

    def choice(
        self,
        path: str,
        options: Sequence[T],
        weights: Sequence[float] | None = None,
    ) -> T:
        rng = self.at(path)
        if weights is None:
            return rng.choice(options)
        return rng.choices(options, weights=weights, k=1)[0]

    def uniform(self, path: str, lo: float, hi: float) -> float:
        return self.at(path).uniform(lo, hi)
