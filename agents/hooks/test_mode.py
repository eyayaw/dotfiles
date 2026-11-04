import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).with_name("mode.py")
CONFIG = """mode = "{kind}"
max_diff_lines = {cap}

[ship]
human = ["tests/acceptance/"]

[learn]
human = ["tests/acceptance/", "src/core/"]
"""


def env(home: Path, agent: bool = False) -> dict[str, str]:
    """A shell environment that keeps state under home and carries no agent marker unless asked."""
    e = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CODEX_AGENT")}
    e |= {
        "HOME": str(home),
        "TMPDIR": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    return e | {"CLAUDECODE": "1"} if agent else e


def mode(*args: str, home: Path, cwd: Path | None = None, stdin: str = "", agent: bool = False):
    return subprocess.run(
        [HOOK, *args],
        cwd=cwd or home,
        input=stdin,
        env=env(home, agent),
        capture_output=True,
        text=True,
    )


def git(repo: Path, *args: str) -> str:
    cmd = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args]
    return subprocess.run(cmd, env=env(repo), check=True, capture_output=True, text=True).stdout


def make_repo(root: Path, kind: str, cap: int = 200) -> Path:
    for p in ("src/core", "tests/acceptance"):
        (root / p).mkdir(parents=True)
    (root / "src/core/model.py").write_text("x = 1\n")
    (root / "src/other.py").write_text("y = 1\n")
    (root / "tests/acceptance/test_spec.py").write_text("def test_a(): pass\n")
    (root / ".gitignore").write_text("__pycache__/\n")
    (root / "mode.toml").write_text(CONFIG.format(kind=kind, cap=cap))
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


def event(root: Path, name: str, tool: str = "", **tool_input) -> str:
    return json.dumps(
        {
            "hook_event_name": name,
            "cwd": str(root),
            "session_id": "s1",
            "tool_use_id": "t1",
            "tool_name": tool,
            "tool_input": tool_input,
        }
    )


PATCH = "*** Begin Patch\n*** Update File: src/core/model.py\n@@\n-x = 1\n+x = 2\n*** End Patch"


@pytest.mark.parametrize(
    ("kind", "tool", "tool_input", "code"),
    [
        ("learn", "Edit", {"file_path": "src/core/model.py"}, 2),
        ("learn", "Edit", {"file_path": "src/CORE/model.py"}, 2),
        ("learn", "Write", {"file_path": "src/core/new.py"}, 2),
        ("learn", "Edit", {"file_path": "src/other.py"}, 0),
        ("learn", "apply_patch", {"command": PATCH}, 2),
        ("learn", "apply_patch", {"command": PATCH.replace("src/core", "src")}, 0),
        ("learn", "Bash", {"command": "cat src/core/model.py"}, 0),
        ("learn", "Bash", {"command": "uv run pytest tests/acceptance/ 2>&1 | tail -5"}, 0),
        ("learn", "Bash", {"command": "ls src/core 2>/dev/null"}, 0),
        ("learn", "Bash", {"command": "rg TODO src/core > /tmp/hits"}, 0),
        ("learn", "Bash", {"command": "cp src/core/model.py /tmp/copy.py"}, 0),
        (
            "learn",
            "Bash",
            {"command": "git commit -F - <<'EOF'\nfix tests/acceptance/test_spec.py\nEOF"},
            0,
        ),
        ("learn", "Bash", {"command": "echo 'x = 2' > src/core/model.py"}, 2),
        ("learn", "Bash", {"command": "echo x >src/core/model.py"}, 2),
        ("learn", "Bash", {"command": "cd src && echo x > core/model.py"}, 0),
        ("learn", "Bash", {"command": "sed -i '' 's/1/2/' src/core/model.py"}, 2),
        ("learn", "Bash", {"command": "cat > src/core/new.py <<'EOF'\nx=2\nEOF"}, 2),
        ("learn", "Bash", {"command": "cp /tmp/copy.py src/core/model.py"}, 2),
        ("learn", "Bash", {"command": "bash -c 'tee src/core/model.py < /tmp/x'"}, 2),
        ("learn", "Bash", {"command": "git checkout -- src/core/model.py"}, 2),
        ("learn", "Bash", {"command": "git checkout feature"}, 0),
        ("ship", "Edit", {"file_path": "src/core/model.py"}, 0),
        ("ship", "Edit", {"file_path": "tests/acceptance/test_spec.py"}, 2),
        ("ship", "Bash", {"command": "git commit -m x --no-verify"}, 2),
        ("ship", "Bash", {"command": "git commit --no-veri -m x"}, 2),
        ("ship", "Bash", {"command": "git commit -nm x"}, 2),
        ("ship", "Bash", {"command": "git -c core.hookspath=/dev/null commit -m x"}, 2),
        ("ship", "Bash", {"command": "PREK_SKIP=mode git commit -m x"}, 2),
        ("ship", "Bash", {"command": "export SKIP=mode; git commit -m x"}, 2),
        ("ship", "Bash", {"command": "GIT_CONFIG_COUNT=1 git commit -m x"}, 2),
        ("ship", "Bash", {"command": "rm .git/hooks/pre-commit"}, 2),
        ("ship", "Bash", {"command": "CLAUDECODE= git commit -m x"}, 2),
        ("ship", "Bash", {"command": "env -u CODEX_AGENT git commit -m x"}, 2),
        ("ship", "Bash", {"command": "git commit -m 'reject --no-verify and the -n flag'"}, 0),
        ("ship", "Bash", {"command": "git log --grep commit -n 5"}, 0),
        ("ship", "Bash", {"command": "git commit -m x"}, 0),
    ],
)
def test_pretooluse(tmp_path, kind, tool, tool_input, code):
    root = make_repo(tmp_path, kind)
    result = mode("hook", home=root, stdin=event(root, "PreToolUse", tool, **tool_input))
    assert result.returncode == code, result.stderr
    if code == 2:
        assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def post(root: Path, name: str = "PostToolUse"):
    return mode("hook", home=root, stdin=event(root, name, "Bash", command="python3 x.py"))


def test_bash_write_to_human_path_is_reported_after_the_fact(tmp_path):
    root = make_repo(tmp_path, "learn")
    assert (
        mode(
            "hook", home=root, stdin=event(root, "PreToolUse", "Bash", command="python3 x.py")
        ).returncode
        == 0
    )
    (root / "src/core/model.py").write_text("x = 2\n")
    os.utime(
        root / "src/core/model.py", ns=(1, 1)
    )  # a restored mtime hides nothing: content is compared
    after = post(root, "PostToolUseFailure")
    assert (
        after.returncode == 2
        and "src/core/model.py" in after.stderr
        and "revert nothing" in after.stderr
    )
    assert post(root).returncode == 0  # the snapshot is consumed


def test_bytecode_and_checkouts_are_not_writes(tmp_path):
    root = make_repo(tmp_path, "learn")
    git(root, "checkout", "-qb", "feature")
    (root / "src/core/model.py").write_text("x = 3\n")
    git(root, "commit", "-qam", "feature")
    git(root, "checkout", "-q", "main")
    assert (
        mode(
            "hook", home=root, stdin=event(root, "PreToolUse", "Bash", command="python3 x.py")
        ).returncode
        == 0
    )
    (root / "tests/acceptance/__pycache__").mkdir()
    (root / "tests/acceptance/__pycache__/t.pyc").write_bytes(b"\0")
    git(root, "checkout", "-q", "feature")  # moves src/core/model.py in step with HEAD
    assert post(root).returncode == 0


def test_session_start_prints_mode(tmp_path):
    root = make_repo(tmp_path, "learn")
    assert "LEARN" in mode("hook", home=root, stdin=event(root, "SessionStart")).stdout


@pytest.mark.parametrize(
    "text", ['mode = "learn', 'mode = "ship"\n', 'mode = "ship"\n[ship]\nhuman = "tests/"\n']
)
def test_unusable_config_is_a_deny_with_the_file_named(tmp_path, text):
    (tmp_path / "mode.toml").write_text(text)
    result = mode("hook", home=tmp_path, stdin=event(tmp_path, "PreToolUse", "Bash", command="ls"))
    assert result.returncode == 2 and "mode.toml" in result.stderr
    assert mode("status", home=tmp_path).returncode == 1


def stage(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text)
    git(root, "add", path)


def test_precommit_caps_diff_and_skips_excluded(tmp_path):
    root = make_repo(tmp_path, "ship", cap=5)
    stage(root, "uv.lock", "\n".join(str(i) for i in range(100)) + "\n")
    stage(root, "src/other.py", "y = 2\n")
    assert mode("precommit", home=root).returncode == 0
    stage(root, "src/other.py", "\n".join(f"y{i} = {i}" for i in range(10)) + "\n")
    assert "over the cap" in mode("precommit", home=root).stderr


def test_precommit_blocks_agent_commit_of_human_paths_including_renames(tmp_path):
    root = make_repo(tmp_path, "learn")
    stage(root, "src/core/model.py", "x = 2\n")
    assert mode("precommit", home=root).returncode == 0
    assert mode("precommit", home=root, agent=True).returncode == 1
    git(root, "reset", "-q", "--hard")
    git(root, "mv", "src/core/model.py", "src/model2.py")
    assert "src/core/model.py" in mode("precommit", home=root, agent=True).stderr


def test_set_learn_allows_one_repo(tmp_path):
    projects = tmp_path / "Developer"
    a = make_repo(projects / "a", "learn")
    b = make_repo(projects / "b", "ship")
    (projects / "c").mkdir()
    (projects / "c/mode.toml").write_text("mode = [\n")  # a broken repo must not stop the others
    refused = mode("set", "learn", home=tmp_path, cwd=b)
    assert "already in learn mode" in refused.stderr
    assert mode("set", "ship", home=tmp_path, cwd=a).returncode == 0
    assert mode("set", "learn", home=tmp_path, cwd=b).returncode == 0
    assert 'mode = "learn"' in (b / "mode.toml").read_text()
    assert len((tmp_path / ".local/state/agentic-modes/switches.tsv").read_text().splitlines()) == 2
