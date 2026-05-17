"""Scan a skills directory and yield Skill objects."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from claudelens.skill import Skill, SkillParseError, parse_skill_file


@dataclass
class ScanResult:
    skills: list[Skill]
    errors: list[tuple[Path, str]]


def scan(skills_dir: Path) -> ScanResult:
    """Discover skill files under skills_dir.

    Recognizes two layouts:
      - skills_dir/<slug>/SKILL.md
      - skills_dir/<slug>.md
    """
    if not skills_dir.exists():
        raise FileNotFoundError(f"Skills directory not found: {skills_dir}")
    if not skills_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {skills_dir}")

    skills: list[Skill] = []
    errors: list[tuple[Path, str]] = []

    for path in _candidate_files(skills_dir):
        try:
            skills.append(parse_skill_file(path))
        except SkillParseError as exc:
            errors.append((path, str(exc)))

    return ScanResult(skills=skills, errors=errors)


def _candidate_files(skills_dir: Path):
    # Folder-based: <skills_dir>/<slug>/SKILL.md (case-insensitive)
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir():
            for candidate in ("SKILL.md", "skill.md", "Skill.md"):
                f = entry / candidate
                if f.is_file():
                    yield f
                    break
        elif entry.is_file() and entry.suffix.lower() == ".md":
            # Flat: <skills_dir>/<slug>.md (skip README.md and similar)
            if entry.stem.lower() in {"readme", "index"}:
                continue
            yield entry
