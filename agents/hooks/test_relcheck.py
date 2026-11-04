import os
import subprocess
from pathlib import Path

import pytest

RELCHECK = Path(__file__).resolve().parents[2] / "bin/.local/bin/relcheck"
ENV = os.environ | {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(repo: Path, *args: str) -> None:
    cmd = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args]
    subprocess.run(cmd, env=ENV, check=True, capture_output=True)


def commit(repo: Path, subject: str, body: str = "") -> None:
    (repo / "src/pkg/a.py").write_text((repo / "src/pkg/a.py").read_text() + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject, *(["-m", body] if body else []))


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src/pkg").mkdir(parents=True)
    (tmp_path / "src/pkg/a.py").write_text("def old(): pass\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "pkg"\nversion = "1.0.1"\n')
    (tmp_path / "README.md").write_text("# pkg\n\n```python\nfrom pkg import old\n```\n")
    git(tmp_path, "init", "-q", "-b", "main")
    commit(tmp_path, "feat: first")
    git(tmp_path, "tag", "v1.0.0")
    return tmp_path


def relcheck(repo: Path) -> str:
    return subprocess.run(
        [RELCHECK], cwd=repo, env=ENV, capture_output=True, text=True, check=True
    ).stdout


def test_breaking_footer_case_and_version_target(repo):
    commit(repo, "Fix: typo")
    commit(repo, "refactor: split", "BREAKING CHANGE: the old name is gone")
    out = relcheck(repo)
    assert "release: major bump" in out
    assert "version: 1.0.1 in pyproject.toml is below 2.0.0; bump to it" in out


def test_patch_version_does_not_satisfy_a_feat(repo):
    commit(repo, "feat: add shiny")
    assert "below 1.1.0" in relcheck(repo)


def test_readme_detects_unindented_names_and_fenced_mentions(repo):
    (repo / "src/pkg/a.py").write_text(
        "class Engine:\n    def start(self): pass\n\nasync def shiny(): pass\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "feat: engine")
    out = relcheck(repo)
    assert "readme: new public names not mentioned: Engine, shiny" in out
    assert "readme: still mentions removed names: old" in out


def test_no_tag_reads_the_start(tmp_path):
    (tmp_path / "src/pkg").mkdir(parents=True)
    (tmp_path / "src/pkg/a.py").write_text("")
    git(tmp_path, "init", "-q", "-b", "main")
    commit(tmp_path, "feat: first")
    assert "release: minor bump; 1 commits since the start: 1 feat" in relcheck(tmp_path)
