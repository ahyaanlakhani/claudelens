"""Project-level configuration loader for .claudelens.toml."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]


@dataclass
class Thresholds:
    description_similarity: float = 0.82
    name_similarity: float = 0.85
    trigger_overlap: float = 0.5


@dataclass
class Config:
    thresholds: Thresholds = field(default_factory=Thresholds)
    ignore_pairs: list[tuple[str, str]] = field(default_factory=list)

    def is_ignored(self, a: str, b: str) -> bool:
        pair = frozenset({a, b})
        return any(frozenset(p) == pair for p in self.ignore_pairs)


def load_config(start: Path) -> Config:
    """Walk upward from `start` looking for .claudelens.toml. Return defaults if absent."""
    cfg_path = _find_config_file(start)
    if cfg_path is None:
        return Config()

    with cfg_path.open("rb") as f:
        data = tomllib.load(f)

    thresholds_data = data.get("thresholds", {}) or {}
    ignore_data = data.get("ignore", {}) or {}

    return Config(
        thresholds=Thresholds(
            description_similarity=float(
                thresholds_data.get("description_similarity", 0.82)
            ),
            name_similarity=float(thresholds_data.get("name_similarity", 0.85)),
            trigger_overlap=float(thresholds_data.get("trigger_overlap", 0.5)),
        ),
        ignore_pairs=[
            (str(a), str(b)) for a, b in (ignore_data.get("pairs") or []) if a and b
        ],
    )


def _find_config_file(start: Path) -> Path | None:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for parent in [cur, *cur.parents]:
        candidate = parent / ".claudelens.toml"
        if candidate.is_file():
            return candidate
    return None
