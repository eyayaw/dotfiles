import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).with_name("commitgate.py")


def run(event: dict, tmp: Path) -> int:
    env = os.environ | {"TMPDIR": str(tmp)}
    return subprocess.run(
        [HOOK], input=json.dumps(event), env=env, capture_output=True, text=True
    ).returncode


def bash(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "session_id": "s",
        "tool_input": {"command": command},
    }


def prompt(text: str, **extra) -> dict:
    return {"hook_event_name": "UserPromptSubmit", "session_id": "s", "prompt": text} | extra


@pytest.mark.parametrize(
    "command",
    [
        "git add -A",
        "cd x && git commit -m y",
        "git stash push -- src",
        "git -C ~/r add file.py",
        "echo done\ngit add -A",
        "  git add -A",
        "env GIT_PAGER=cat /usr/bin/git add x",
        "{ git add -A; }",
        "bash -c 'git add -A'",
        "git stash list; git add -A",
        "git cherry-pick abc",
    ],
)
def test_staging_is_denied_until_the_human_asks(tmp_path, command):
    assert run(bash(command), tmp_path) == 2
    run(prompt("prep the commits"), tmp_path)
    assert run(bash(command), tmp_path) == 0


@pytest.mark.parametrize(
    "text",
    [
        "commit this",
        "send a pr",
        "push and update the pr",
        "commit this, no need to push",
        "amend it",
    ],
)
def test_asking_words_authorize(tmp_path, text):
    run(prompt(text), tmp_path)
    assert run(bash("git add -A"), tmp_path) == 0


@pytest.mark.parametrize(
    "text",
    [
        "do not commit yet",
        "fix the bug, no commit",
        "what does git add -p do?",
        "should I commit this later?",
        "merge these two functions and add a tag field",
        "review the ship mode hooks and release the lock",
    ],
)
def test_other_prompts_do_not_authorize(tmp_path, text):
    run(prompt(text), tmp_path)
    assert run(bash("git add -A"), tmp_path) == 2


def test_the_mark_lasts_one_turn_and_ignores_subagent_briefs(tmp_path):
    run(prompt("commit this"), tmp_path)
    run(prompt("now fix the docstring"), tmp_path)
    assert run(bash("git add -A"), tmp_path) == 2
    run(prompt("ready to commit", agent_id="sub"), tmp_path)
    assert run(bash("git add -A"), tmp_path) == 2


@pytest.mark.parametrize(
    "command",
    [
        "git stash list",
        "git status",
        "git diff --cached",
        "git log --grep commit -n 5",
        "git branch feature/add-mode",
        "git remote add origin x",
        "git worktree add ../w",
        "git diff -- src/add.py",
        "git commit --dry-run",
    ],
)
def test_reads_stay_allowed(tmp_path, command):
    assert run(bash(command), tmp_path) == 0
