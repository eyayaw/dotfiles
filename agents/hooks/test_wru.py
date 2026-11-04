import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

HOOK = Path(__file__).with_name("wru.py")
LAST = "## Done\n\n**Tests pass.** `main` is 2 commits ahead, ready to push.\n- next: docs"


def wru(*args: str, home: Path, stdin: str = "", cwd: Path | None = None) -> str:
    env = os.environ | {"HOME": str(home), "REX_BLOCK": "block:0123456789"}
    result = subprocess.run(
        [HOOK, *args], input=stdin, env=env, cwd=cwd, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def folder(home: Path) -> Path:
    return home / ".local/state/agentic-modes/wru"


def test_stop_records_the_opening_and_resume_prints_it(tmp_path):
    stop = {
        "hook_event_name": "Stop",
        "session_id": "s1",
        "cwd": str(tmp_path),
        "last_assistant_message": LAST,
    }
    wru("hook", home=tmp_path, stdin=json.dumps(stop))
    s = json.loads((folder(tmp_path) / "s1.json").read_text())
    assert s["last"] == "Done Tests pass. main is 2 commits ahead, ready to push. next: docs"
    assert (s["harness"], s["pane"]) == ("claude", "block:0123456789")
    assert not list(folder(tmp_path).glob("*.tmp"))
    wru("hook", home=tmp_path, stdin=json.dumps(stop | {"session_id": "s2", "turn_id": "t"}))
    assert json.loads((folder(tmp_path) / "s2.json").read_text())["harness"] == "codex"
    start = {"hook_event_name": "SessionStart", "source": "startup", "session_id": "s1"}
    assert wru("hook", home=tmp_path, stdin=json.dumps(start)) == ""
    out = wru("hook", home=tmp_path, stdin=json.dumps(start | {"source": "compact"}))
    assert out.startswith("Where this session left off (0m ago): Done Tests pass.")


def test_stop_falls_back_to_the_transcript_tail(tmp_path):
    rows = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "first"}]}},
        {
            "type": "assistant",
            "isSidechain": True,
            "message": {"content": [{"type": "text", "text": "subagent"}]},
        },
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "the real last message"}]},
        },
    ]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("".join(json.dumps(r) + "\n" for r in rows))
    stop = {
        "hook_event_name": "Stop",
        "session_id": "s2",
        "cwd": str(tmp_path),
        "transcript_path": str(transcript),
    }
    wru("hook", home=tmp_path, stdin=json.dumps(stop))
    assert json.loads((folder(tmp_path) / "s2.json").read_text())["last"] == "the real last message"


def test_listing_is_newest_first_filters_by_cwd_and_skips_a_torn_file(tmp_path):
    now = datetime.now(UTC)
    folder(tmp_path).mkdir(parents=True)
    for sid, ago, cwd, last in [("a", 2, str(tmp_path), "older"), ("b", 1, "/elsewhere", "newer")]:
        row = {
            "ts": (now - timedelta(hours=ago)).isoformat(timespec="seconds"),
            "harness": "claude",
            "session_id": sid,
            "cwd": cwd,
            "pane": "",
            "last": last,
        }
        (folder(tmp_path) / f"{sid}.json").write_text(json.dumps(row))
    (folder(tmp_path) / "torn.json").write_text('{"ts": "2026-')
    assert [ln.split()[-1] for ln in wru(home=tmp_path).splitlines()] == ["newer", "older"]
    assert wru("--here", home=tmp_path, cwd=tmp_path).splitlines()[0].endswith("older")
