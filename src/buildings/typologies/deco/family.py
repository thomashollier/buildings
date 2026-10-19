"""A family of rule files: one shared vocabulary, several programmes.

The rule-file loader (``common/rulefile.py``) reads one file. The Art Deco
family is many buildings -- a setback tower, a department store, a
courthouse, a church, a power house, a Miami Beach hotel, a movie palace --
that share one vocabulary: the same window kinds, the same piers and
spandrels, the same crests, the same eyebrows and racing stripes, the same
choice of zigzag or streamline by date. Writing that vocabulary once per
file would be copying it; so this module composes several rule files into
one style before loading it.

Composition is deliberately plain:

* ``[params]``, ``[emit]`` and ``[lot_props]`` are merged; a name defined
  twice with different values is an error (no silent override).
* ``[[production]]``, ``[[rule]]`` and ``[[layer]]`` entries are
  concatenated, so a programme file adds productions and rules (and may add a
  layer that overrides the vocabulary's per key, by its order).
* ``[style]`` comes from the last file that has one: the programme's.

Everything else -- the checks, the compilation, the derivation -- is the
standard loader's, called on the merged data.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from buildings.cga import AttributeStage, Layer
from buildings.typologies.common import kit
from buildings.typologies.common import rulefile as rf

__all__ = ["load_family", "VOCABULARY"]

VOCABULARY = Path(__file__).with_name("vocabulary.toml")


def _merge(paths: list[Path]) -> dict[str, Any]:
    out: dict[str, Any] = {"params": {}, "emit": {}, "lot_props": {}, "production": [], "rule": [], "layer": []}
    for path in paths:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        for section in ("params", "emit", "lot_props"):
            for key, value in (data.get(section) or {}).items():
                if key in out[section] and out[section][key] != value:
                    raise rf.RuleFileError(f"{path.name}: [{section}] {key} is already defined differently by an earlier file of the family")
                out[section][key] = value
        for section in ("production", "rule"):
            out[section].extend(data.get(section, ()))
        for layer in data.get("layer", ()):
            same = [l for l in out["layer"] if l["name"] == layer["name"]]
            if same and same[0].get("order", 0) != layer.get("order", 0):
                raise rf.RuleFileError(f"{path.name}: layer {layer['name']} is already declared with another order")
            if not same:
                out["layer"].append(layer)
        if "style" in data:
            out["style"] = data["style"]
        unknown = set(data) - rf._TOP
        if unknown:
            raise rf.RuleFileError(f"{path.name}: unknown section(s) {sorted(unknown)}")
    return out


def load_family(*paths: str | Path) -> rf.Style:
    """One style from several rule files, the main (programme) file last."""
    paths = [Path(p) for p in paths]
    main = paths[-1]
    data = _merge(paths)
    rf._check(data, main)
    meta = data.get("style") or {}
    name = meta.get("name") or main.stem
    params = dict(data["params"])
    productions = tuple(
        rf._production(p, params, f"{main.name}: production {p.get('id', i)}") for i, p in enumerate(data["production"])
    )
    layers_spec = {l["name"]: l.get("order", 0) for l in data["layer"]}
    by_label: dict[str, dict[str, list]] = {}
    for i, r in enumerate(data["rule"]):
        layer = r.get("layer", "base")
        layers_spec.setdefault(layer, 0)
        by_label.setdefault(r["label"], {}).setdefault(layer, []).append(rf._rule(r, params, f"{main.name}: rule {r.get('id', i)}"))
    stages = tuple(
        AttributeStage(label, tuple(Layer(lname, layers_spec[lname], tuple(rules)) for lname, rules in layers.items()))
        for label, layers in by_label.items()
    )
    writers = dict(kit.INTERPRETERS)
    for label, writer in data["emit"].items():
        if writer not in rf.WRITERS:
            raise rf.RuleFileError(f"{main.name}: no writer named {writer!r} for {label}")
        writers[label] = rf.WRITERS[writer]
    describe = dict(meta.get("describe") or {"rule": f"{name}.style", "detail": name})
    describe["detail"] = rf._expr(describe["detail"], f"{main.name}: style.describe.detail")
    axiom = {k: rf._expr(v, f"{main.name}: style.axiom.{k}") for k, v in (meta.get("axiom") or {"w": "width", "h": 40}).items()}
    return rf.Style(
        name=name,
        path=main,
        params=params,
        productions=productions,
        stages=stages,
        writers=writers,
        overhangs=frozenset(meta.get("overhangs", ())),
        axiom_spec=axiom,
        site_fields=tuple(meta.get("site", ())),
        describe=describe,
        lot_props=rf._map(data["lot_props"], f"{main.name}: lot_props"),
    )
