import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).with_name("prose_review.py")
ENV = os.environ | {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
CODE = '''\
# /// script
# requires-python = ">=3.14"
# ///
"""
Fetch pages over HTTP.

Note (proxies): the client honors HTTPS_PROXY, and the timeout defaults to 5.0 seconds.
"""

import json

# ----------


def fetch(url: str) -> str:
    """Fetch this URL."""
    # Return the url
    return url  # noqa: RET504


def connect(host: str, sep: str = "", port: int | None = None) -> None:
    """
    Open a socket to host.

    Args:
        port: Defaults to the PORT variable.
    """


def body(url: str, timeout: float = 5.0) -> str:
    """
    Return the response body, retrying on HTTP 503.

    Args:
        timeout (float): Seconds per attempt. Defaults to 5.0.

    Returns:
        The body.
    """
    # 2: send the request
    # 1.5x faster than requests on HTTP/2, measured on 2024-05-01.
    #
    # httpx, because the API serves HTTP/2 only.
    return url
'''
SUMMARY = "Return the response body, retrying on HTTP 503."


def git(repo: Path, *args: str, check: bool = True) -> None:
    subprocess.run(["git", "-C", repo, *args], env=ENV, check=check, capture_output=True)


def commit(repo: Path) -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")


def run(repo: Path, session: str = "s1", event: str = "Stop") -> dict:
    payload = json.dumps({"cwd": str(repo), "session_id": session, "hook_event_name": event})
    result = subprocess.run(
        [str(HOOK)], input=payload, env=ENV, capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout) if result.stdout else {}


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "mod.py").write_text("import json\n")
    commit(tmp_path)
    run(tmp_path, event="SessionStart")
    return tmp_path


def findings(out: dict, name: str = "mod.py") -> list[tuple[str, str]]:
    return [
        tuple(line.split(": ", 2)[1:])
        for line in out.get("reason", "").splitlines()
        if line.startswith(f"{name}:")
    ]


def test_lists_the_added_lines_that_fail_a_rule_and_no_others(repo):
    (repo / "mod.py").write_text(CODE)
    assert findings(run(repo)) == [
        ("the summary restates the signature", "Fetch this URL."),
        ("an Args entry repeats the type", SUMMARY),
        ("an Args entry repeats the default", SUMMARY),
        ("Returns repeats the summary", SUMMARY),
        ("a banner", "# ----------"),
        ("narrates the statement below", "# Return the url"),
        ("a step number", "# 2: send the request"),
    ]


def test_a_line_is_listed_once_per_session_and_again_in_another(repo):
    run(repo, session="s2", event="SessionStart")
    (repo / "mod.py").write_text(CODE)
    assert run(repo)["decision"] == "block"
    assert run(repo) == {}
    assert run(repo, session="s2")["decision"] == "block"


def test_lines_written_before_a_sessions_first_record_are_not_listed(repo):
    (repo / "mod.py").write_text(CODE)
    assert run(repo, session="entered-later") == {}
    assert run(repo, event="SessionStart") == {}
    assert run(repo) == {}


def test_a_repository_without_commits_or_python_files_is_handled(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "README").write_text("hi\n")
    assert run(tmp_path, event="SessionStart") == {}
    assert run(tmp_path) == {}
    (tmp_path / "mod.py").write_text("x = 1  # the x\n")
    assert findings(run(tmp_path)) == [("narrates the statement below", "# the x")]


def test_a_merge_conflict_and_the_lines_it_merges_are_not_listed(repo):
    (repo / "f.txt").write_text("a\n")
    commit(repo)
    git(repo, "checkout", "-q", "-b", "other")
    (repo / "f.txt").write_text("b\n")
    (repo / "lib.py").write_text("y = 1  # the y\n")
    commit(repo)
    git(repo, "checkout", "-q", "main")
    (repo / "f.txt").write_text("c\n")
    commit(repo)
    git(repo, "merge", "other", check=False)
    assert run(repo) == {}
    (repo / "f.txt").write_text("b\n")
    commit(repo)
    assert run(repo) == {}


def test_a_renamed_file_lists_only_its_new_lines(repo):
    (repo / "mod.py").write_text("x = 1  # the x\ny = 2\n")
    commit(repo)
    run(repo)
    git(repo, "mv", "mod.py", "moved.py")
    (repo / "moved.py").write_text("x = 1  # the x\ny = 3\n")
    assert findings(run(repo), name="moved.py") == []


def test_comments_in_a_file_that_does_not_parse_are_listed(repo):
    (repo / "mod.py").write_text("def g(:\n    # return the x\n    return x\n")
    assert findings(run(repo)) == [("narrates the statement below", "# return the x")]


def test_a_latin1_source_with_a_space_in_its_name_is_reviewed(repo):
    (repo / "my latin.py").write_bytes(b"# -*- coding: latin-1 -*-\ns = 'caf\xe9'  # the s\n")
    assert findings(run(repo), name="my latin.py") == [("narrates the statement below", "# the s")]
