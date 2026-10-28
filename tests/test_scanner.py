from pathlib import Path

import pytest

from claudelens.scanner import scan


def test_scanner_finds_folder_and_flat_skills(fixtures_dir: Path):
    result = scan(fixtures_dir / "skills")
    names = sorted(s.name for s in result.skills)
    assert names == ["deploy", "pr-review", "review", "security-review"]
    assert result.errors == []


def test_scanner_raises_on_missing_dir(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        scan(tmp_path / "does-not-exist")


def test_scanner_finds_mixed_case_skill_filename(tmp_path: Path):
    skill_dir = tmp_path / "example"
    skill_dir.mkdir()
    (skill_dir / "sKiLl.Md").write_text(
        "---\nname: example\ndescription: An example skill\n---\n", encoding="utf-8"
    )
    result = scan(tmp_path)
    assert [skill.name for skill in result.skills] == ["example"]
    assert result.errors == []
