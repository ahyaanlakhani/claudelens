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
