from pathlib import Path

from claudelens.checks import check_descriptions, check_naming, check_triggers
from claudelens.checks.base import Severity
from claudelens.config import Config
from claudelens.scanner import scan


def _load(fixtures_dir: Path):
    return scan(fixtures_dir / "skills").skills


def test_naming_flags_token_containment(fixtures_dir: Path):
    skills = _load(fixtures_dir)
    findings = check_naming(skills, Config())
    pairs = {
        tuple(sorted(f.skills))
        for f in findings
        if f.check == "naming.token-containment"
    }
    # "review" is a token-subset of both "pr-review" and "security-review".
    assert ("pr-review", "review") in pairs
    assert ("review", "security-review") in pairs


def test_descriptions_flag_overlap(fixtures_dir: Path):
    skills = _load(fixtures_dir)
    findings = check_descriptions(skills, Config())
    overlap = [f for f in findings if f.check == "descriptions.overlap"]
    pairs = {tuple(sorted(f.skills)) for f in overlap}
    assert ("pr-review", "review") in pairs


def test_triggers_shared_trigger(fixtures_dir: Path):
    skills = _load(fixtures_dir)
    findings = check_triggers(skills, Config())
    shared = [f for f in findings if f.check == "triggers.shared"]
    assert any(set(f.skills) == {"review", "pr-review"} for f in shared)
    assert all(f.severity == Severity.ERROR for f in shared)


def test_ignore_pair_suppresses_finding(fixtures_dir: Path):
    skills = _load(fixtures_dir)
    config = Config(ignore_pairs=[("pr-review", "review")])
    desc = check_descriptions(skills, config)
    nam = check_naming(skills, config)
    assert all(set(f.skills) != {"pr-review", "review"} for f in desc)
    assert all(set(f.skills) != {"pr-review", "review"} for f in nam if f.check != "naming.duplicate")
