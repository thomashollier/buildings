from __future__ import annotations

import subprocess
import sys
import textwrap

from buildings.rng import DecisionStream


def test_same_seed_and_path_gives_same_value() -> None:
    s1 = DecisionStream(42)
    s2 = DecisionStream(42)
    assert s1.uniform("bay/3/opening/width", 0.0, 1.0) == s2.uniform("bay/3/opening/width", 0.0, 1.0)


def test_different_paths_diverge() -> None:
    s = DecisionStream(42)
    a = s.uniform("bay/0/opening/width", 0.0, 1.0)
    b = s.uniform("bay/1/opening/width", 0.0, 1.0)
    assert a != b


def test_different_seeds_diverge() -> None:
    a = DecisionStream(1).uniform("bay/0/opening/width", 0.0, 1.0)
    b = DecisionStream(2).uniform("bay/0/opening/width", 0.0, 1.0)
    assert a != b


def test_choice_and_uniform_deterministic() -> None:
    s = DecisionStream(7)
    options = ["a", "b", "c", "d"]
    assert s.choice("bay/0/kind", options) == s.choice("bay/0/kind", options)


def test_weighted_choice_is_deterministic() -> None:
    s = DecisionStream(7)
    options = ["a", "b", "c"]
    weights = [0.1, 0.1, 0.8]
    picks = {s.choice(f"path/{i}", options, weights=weights) for i in range(1)}
    # deterministic re-run of the same path gives the same result
    again = s.choice("path/0", options, weights=weights)
    assert next(iter(picks)) == again


def test_new_path_does_not_perturb_existing_paths() -> None:
    """The load-bearing property: adding a brand-new path must not shift the
    value returned for any existing path."""
    stream = DecisionStream(1234)
    paths = [f"bay/{i}/opening/surround" for i in range(50)]
    before = {p: stream.uniform(p, 0.0, 100.0) for p in paths}

    # request a brand-new path that never existed before
    _ = stream.uniform("bay/999/opening/surround/new_kind_of_decision", 0.0, 1.0)

    after = {p: stream.uniform(p, 0.0, 100.0) for p in paths}
    assert before == after


def test_at_returns_independent_random_instances() -> None:
    stream = DecisionStream(5)
    r1 = stream.at("a")
    r2 = stream.at("b")
    assert r1 is not r2

    # drawing repeatedly from path "a" must not affect what a freshly
    # re-derived stream for path "b" produces.
    expected_b = stream.at("b").random()
    r1.random()
    r1.random()
    assert stream.at("b").random() == expected_b


def test_stable_across_process_restarts() -> None:
    """Same (seed, path) => same sequence, forever — verified by running a
    fresh Python process, not just re-instantiating within this one."""
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, "src")
        from buildings.rng import DecisionStream
        s = DecisionStream(999)
        print(s.uniform("bay/3/opening/surround", 0.0, 1.0))
        """
    )
    results = []
    for _ in range(2):
        out = subprocess.run(
            [sys.executable, "-c", script],
            cwd=__file__.rsplit("/tests/", 1)[0],
            capture_output=True,
            text=True,
            check=True,
        )
        results.append(out.stdout.strip())
    assert results[0] == results[1]
    # and matches an in-process computation too
    in_process = str(DecisionStream(999).uniform("bay/3/opening/surround", 0.0, 1.0))
    assert results[0] == in_process
