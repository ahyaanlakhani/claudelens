"""Detect naming clashes between skill slugs and aliases."""
from __future__ import annotations

from difflib import SequenceMatcher
from itertools import combinations

from claudelens.checks.base import Finding, Severity
from claudelens.config import Config
from claudelens.skill import Skill

_RESERVED = {
    "help",
    "clear",
    "init",
    "review",
    "compact",
    "config",
    "exit",
    "quit",
}


def _tokens(slug: str) -> frozenset[str]:
    return frozenset(t for t in slug.lower().replace("_", "-").split("-") if t)


def check_naming(skills: list[Skill], config: Config) -> list[Finding]:
    findings: list[Finding] = []

    # 1. Exact duplicate names (hard error).
    by_name: dict[str, list[Skill]] = {}
    for s in skills:
        by_name.setdefault(s.name.lower(), []).append(s)
    for name, group in by_name.items():
        if len(group) > 1:
            findings.append(
                Finding(
                    check="naming.duplicate",
                    severity=Severity.ERROR,
                    skills=tuple(sorted(s.name for s in group)),
                    message=f"Duplicate skill name '{name}' defined in {len(group)} files",
                )
            )

    # 2. Alias collisions with another skill's name or alias.
    name_index: dict[str, str] = {}  # lowercased identifier -> owning skill name
    for s in skills:
        name_index.setdefault(s.name.lower(), s.name)
    for s in skills:
        for alias in s.aliases:
            key = alias.lower()
            owner = name_index.get(key)
            if owner and owner != s.name:
                findings.append(
                    Finding(
                        check="naming.alias-collision",
                        severity=Severity.ERROR,
                        skills=tuple(sorted({s.name, owner})),
                        message=(
                            f"'{s.name}' declares alias '{alias}' which collides with "
                            f"skill '{owner}'"
                        ),
                    )
                )

    # 3a. Token-containment: one slug's tokens are a subset of another's.
    # Catches "review" vs "pr-review" — a common routing collision pattern.
    token_sets = {s.name: _tokens(s.name) for s in skills}
    for a, b in combinations(skills, 2):
        if config.is_ignored(a.name, b.name):
            continue
        ta, tb = token_sets[a.name], token_sets[b.name]
        if not ta or not tb or ta == tb:
            continue
        if ta <= tb or tb <= ta:
            findings.append(
                Finding(
                    check="naming.token-containment",
                    severity=Severity.WARNING,
                    skills=(a.name, b.name),
                    message=(
                        f"Skill names '{a.name}' and '{b.name}' share all tokens of "
                        f"the shorter slug; routing may be ambiguous"
                    ),
                )
            )

    # 3b. Near-duplicate slugs by edit ratio (catches typos like 'depoly' vs 'deploy').
    threshold = config.thresholds.name_similarity
    for a, b in combinations(skills, 2):
        if config.is_ignored(a.name, b.name):
            continue
        if a.name.lower() == b.name.lower():
            continue  # already covered above
        if token_sets[a.name] <= token_sets[b.name] or token_sets[b.name] <= token_sets[a.name]:
            continue  # already covered by token-containment
        ratio = SequenceMatcher(None, a.name.lower(), b.name.lower()).ratio()
        if ratio >= threshold:
            findings.append(
                Finding(
                    check="naming.near-duplicate",
                    severity=Severity.WARNING,
                    skills=(a.name, b.name),
                    message=(
                        f"Skill names '{a.name}' and '{b.name}' are very similar "
                        f"(ratio={ratio:.2f})"
                    ),
                    score=ratio,
                )
            )

    # 4. Reserved-word collisions.
    for s in skills:
        if s.name.lower() in _RESERVED:
            findings.append(
                Finding(
                    check="naming.reserved",
                    severity=Severity.WARNING,
                    skills=(s.name,),
                    message=(
                        f"Skill name '{s.name}' shadows a built-in Claude Code "
                        f"command — invocations may be ambiguous"
                    ),
                )
            )

    return findings
