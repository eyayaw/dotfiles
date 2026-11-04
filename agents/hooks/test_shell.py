import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def shell(expr: str) -> str:
    """Evaluate expr against shell.py in a fresh interpreter, so the test reads as a caller."""
    code = f"from shell import *; print({expr})"
    return subprocess.run(
        [sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("echo done\ngit add -A", "[['echo', 'done'], ['git', 'add', '-A']]"),
        ("{ git add -A; }", "[['git', 'add', '-A']]"),
        ("env -u FOO GIT_PAGER=cat /usr/bin/git add x", "[['git', 'add', 'x']]"),
        (
            "bash -c 'git add -A && ls'",
            "[['bash', '-c', 'git add -A && ls'], ['git', 'add', '-A'], ['ls']]",
        ),
        ("git log --grep='git add' -n 5", "[['git', 'log', '--grep=git add', '-n', '5']]"),
    ],
)
def test_segments(command, expected):
    assert shell(f"segments({command!r})") == expected


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("uv run pytest tests/acceptance/ 2>&1 | tail", "[]"),
        ("ls src/core 2>/dev/null", "[]"),
        ("rg TODO src/core > /tmp/t", "['/tmp/t']"),
        ("echo x >> src/core/m.py", "['src/core/m.py']"),
        ("cat > src/core/new.py <<'EOF'\nx=2\nEOF", "['src/core/new.py']"),
        ("cp src/core/m.py /tmp/copy.py", "['/tmp/copy.py']"),
        ("cp /tmp/copy.py src/core/m.py", "['src/core/m.py']"),
        ("sed -i '' 's/1/2/' src/core/m.py", "['src/core/m.py']"),
        ("tee src/core/m.py < /tmp/x", "['src/core/m.py']"),
        ("git checkout -- src/core/m.py", "['src/core/m.py']"),
        ("git checkout feature", "['feature']"),
        ("git log -- src/core/m.py | tee /tmp/l", "['/tmp/l']"),
        ("dd if=/dev/zero of=src/core/m.py", "['src/core/m.py']"),
    ],
)
def test_write_targets(command, expected):
    assert shell(f"[t for s in segments({command!r}) for t in write_targets(s)]") == expected


def test_git_subcommand_skips_global_options():
    assert shell("git_subcommand(['git', '-C', 'r', '-c', 'k=v', 'commit', '-m', 'x'])") == (
        "('commit', ['-m', 'x'], ['-C', 'r', '-c', 'k=v'])"
    )


def test_env_changes():
    assert shell("sorted(env_changes('CLAUDECODE= env -u SKIP git commit; unset PREK_SKIP'))") == (
        "['CLAUDECODE', 'PREK_SKIP', 'SKIP']"
    )
