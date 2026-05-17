"""Detect ambiguous trigger overlap between skills."""
from __future__ import annotations

import re
from itertools import combinations

from claudelens.checks.base import Finding, Severity
from claudelens.config import Config
from claudelens.skill import Skill


def check_triggers(skills: list[Skill], config: Config) -> list[Finding]:
    """Flag skills that share trigger strings or whose regex triggers overlap."""
    findings: list[Finding] = []
    threshold = config.thresholds.trigger_overlap

    # Index normalized literal triggers.
    literal_index: dict[str, list[str]] = {}
    for s in skills:
        for trig in s.triggers:
            if _looks_like_regex(trig):
                continue
            literal_index.setdefault(trig.lower().strip(), []).append(s.name)

    for trig, owners in literal_index.items():
        unique_owners = sorted(set(owners))
        if len(unique_owners) > 1:
            findings.append(
                Finding(
                    check="triggers.shared",
                    severity=Severity.ERROR,
                    skills=tuple(unique_owners),
                    message=(
                        f"Trigger '{trig}' is declared by {len(unique_owners)} "
                        f"skills: {', '.join(unique_owners)}"
                    ),
                )
            )

    # Jaccard overlap on literal trigger sets (warns on heavy overlap below 100%).
    literal_sets: dict[str, set[str]] = {
        s.name: {t.lower().strip() for t in s.triggers if not _looks_like_regex(t)}
        for s in skills
    }
    for a, b in combinations(skills, 2):
        if config.is_ignored(a.name, b.name):
            continue
        sa, sb = literal_sets[a.name], literal_sets[b.name]
        if not sa or not sb:
            continue
        if sa == sb:
            continue  # already flagged by triggers.shared on each element
        inter = sa & sb
        union = sa | sb
        if not union:
            continue
        jaccard = len(inter) / len(union)
        if jaccard >= threshold and inter:
            findings.append(
                Finding(
                    check="triggers.overlap",
                    severity=Severity.WARNING,
                    skills=(a.name, b.name),
                    message=(
                        f"'{a.name}' and '{b.name}' share triggers "
                        f"{sorted(inter)} (Jaccard={jaccard:.2f})"
                    ),
                    score=jaccard,
                )
            )

    # Regex-vs-literal: warn when one skill's regex matches another's literal.
    for s in skills:
        regex_triggers = [t for t in s.triggers if _looks_like_regex(t)]
        compiled = []
        for r in regex_triggers:
            try:
                compiled.append((r, re.compile(_strip_slashes(r), re.IGNORECASE)))
            except re.error:
                findings.append(
                    Finding(
                        check="triggers.invalid-regex",
                        severity=Severity.ERROR,
                        skills=(s.name,),
                        message=f"'{s.name}' has invalid regex trigger: {r!r}",
                    )
                )
        for other in skills:
            if other.name == s.name:
                continue
            if config.is_ignored(s.name, other.name):
                continue
            for raw, pat in compiled:
                for lit in other.triggers:
                    if _looks_like_regex(lit):
                        continue
                    if pat.search(lit):
                        findings.append(
                            Finding(
                                check="triggers.regex-matches-literal",
                                severity=Severity.WARNING,
                                skills=(s.name, other.name),
                                message=(
                                    f"Regex trigger {raw!r} on '{s.name}' matches "
                                    f"literal trigger '{lit}' on '{other.name}'"
                                ),
                            )
                        )

    return findings


def _looks_like_regex(trig: str) -> bool:
    """Heuristic: surrounded by /.../ or contains regex metacharacters."""
    if trig.startswith("/") and trig.endswith("/") and len(trig) > 2:
        return True
    return bool(re.search(r"[\\^$*+?(){}\[\]|]", trig))


def _strip_slashes(trig: str) -> str:
    if trig.startswith("/") and trig.endswith("/"):
        return trig[1:-1]
    return trig
