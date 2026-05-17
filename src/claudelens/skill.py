"""Skill model and frontmatter parser."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<yaml>.*?)\n---\s*(?:\n|\Z)",
    re.DOTALL,
)


@dataclass
class Skill:
    """A single skill discovered in a skills directory."""

    name: str
    description: str
    path: Path
    triggers: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    raw_frontmatter: dict = field(default_factory=dict)

    @property
    def display_path(self) -> str:
        return str(self.path)


class SkillParseError(ValueError):
    """Raised when a skill file has missing or invalid frontmatter."""


def parse_skill_file(path: Path) -> Skill:
    """Parse a SKILL.md (or <name>.md) file into a Skill.

    Raises SkillParseError if frontmatter is missing or required fields are absent.
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise SkillParseError(f"{path}: no YAML frontmatter found")

    try:
        data = yaml.safe_load(match.group("yaml")) or {}
    except yaml.YAMLError as exc:
        raise SkillParseError(f"{path}: invalid YAML frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise SkillParseError(f"{path}: frontmatter must be a mapping")

    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str) or not name.strip():
        raise SkillParseError(f"{path}: missing required 'name' field")
    if not isinstance(description, str) or not description.strip():
        raise SkillParseError(f"{path}: missing required 'description' field")

    triggers = _as_str_list(data.get("triggers"))
    aliases = _as_str_list(data.get("aliases"))

    return Skill(
        name=name.strip(),
        description=description.strip(),
        path=path,
        triggers=triggers,
        aliases=aliases,
        raw_frontmatter=data,
    )


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []
