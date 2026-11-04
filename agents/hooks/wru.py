#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Record where each agent session left off, and list every session's last state.

``wru hook`` is a Stop and SessionStart hook for Claude Code and Codex. On Stop it saves the
opening of the agent's last message, the repo, and the Rex pane when there is one, under
``~/.local/state/agentic-modes/wru/<session_id>.json``. On a resume or compact it prints that
state back as context, so the agent knows where it was.

``wru`` lists the states of the last seven days, newest first, one line each. ``wru --here``
keeps the current repo only; ``wru --all`` drops the age limit.
"""

import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

STATE = Path.home() / ".local/state/agentic-modes/wru"
KEEP = timedelta(days=30)
RECENT = timedelta(days=7)
WIDTH = 240


def opening(text: str) -> str:
    """Return the start of text without markdown furniture, at most WIDTH characters."""
    lines = (re.sub(r"^[#>*\-\s]+|\*\*|`", "", ln).strip() for ln in text.splitlines())
    return " ".join(ln for ln in lines if ln)[:WIDTH]


def last_assistant_text(transcript: Path) -> str:
    """Return the last assistant text in a Claude or Codex transcript, reading only its tail."""
    with transcript.open("rb") as f:
        f.seek(max(0, transcript.stat().st_size - 400_000))
        tail = f.read().decode("utf-8", "ignore")
    last = ""
    for line in tail.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "assistant" and not d.get("isSidechain"):
            content = d.get("message", {}).get("content")
        elif d.get("type") == "response_item" and d.get("payload", {}).get("role") == "assistant":
            content = d["payload"].get("content")
        else:
            continue
        if isinstance(content, list):
            text = "\n".join(
                b.get("text", "") for b in content if b.get("type") in ("text", "output_text")
            )
            last = text if text.strip() else last
    return last


def hook(event: dict) -> None:
    sid = event.get("session_id") or "unknown"
    path = STATE / f"{sid}.json"
    match event.get("hook_event_name"):
        case "Stop":
            transcript = event.get("transcript_path") or ""
            text = event.get("last_assistant_message") or ""
            if not text.strip() and Path(transcript).is_file():
                text = last_assistant_text(Path(transcript))
            if not text.strip():
                return
            state = {
                "ts": datetime.now(UTC).isoformat(timespec="seconds"),
                "harness": "codex"
                if event.get("turn_id")
                else "claude",  # only Codex sends turn_id
                "session_id": sid,
                "cwd": event.get("cwd") or os.getcwd(),
                "pane": os.environ.get("REX_BLOCK", ""),
                "last": opening(text),
            }
            STATE.mkdir(parents=True, exist_ok=True)
            path.with_suffix(".tmp").write_text(json.dumps(state))
            os.replace(path.with_suffix(".tmp"), path)  # so a reader never sees a torn file
        case "SessionStart" if event.get("source") in ("resume", "compact") and path.is_file():
            s = json.loads(path.read_text())
            print(f"Where this session left off ({age(s['ts'])} ago): {s['last']}")


def age(ts: str) -> str:
    minutes = int((datetime.now(UTC) - datetime.fromisoformat(ts)).total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m"
    if minutes < 48 * 60:
        return f"{minutes // 60}h"
    return f"{minutes // 1440}d"


def listing(here: bool, everything: bool) -> None:
    now = datetime.now(UTC)
    states = []
    for f in STATE.glob("*.json") if STATE.is_dir() else ():
        try:
            s = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        old = now - datetime.fromisoformat(s["ts"])
        if old > KEEP:
            f.unlink()
        elif (everything or old <= RECENT) and (
            not here or Path(s["cwd"]).resolve() == Path.cwd().resolve()
        ):
            states.append(s)
    for s in sorted(states, key=lambda s: s["ts"], reverse=True):
        pane = s["pane"].removeprefix("block:")[-6:] or "-"
        project = "/".join(Path(s["cwd"]).parts[-2:])
        print(f"{age(s['ts']):>4}  {s['harness']:<6}  {pane:<6}  {project:<32}  {s['last'][:120]}")


def main() -> None:
    match sys.argv[1:]:
        case ["hook"]:
            hook(json.load(sys.stdin))
        case flags if set(flags) <= {"--here", "--all"}:
            listing("--here" in flags, "--all" in flags)
        case _:
            sys.exit("usage: wru [--here] [--all] | wru hook")


if __name__ == "__main__":
    main()
