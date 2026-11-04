#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Let an agent stage or commit only in a turn the human asked for it.

A UserPromptSubmit hook marks the session when the prompt asks for a commit, a PR, a push, or a
release, in the words the human uses, and clears the mark on any other prompt, so the permission
lasts one turn. A question does not ask, a negated verb does not ask, and a subagent's brief is
not the human's prompt. A PreToolUse hook on Bash denies the git commands that stage or commit
while the mark is absent, and tells the agent to ask. Claude Code and Codex send the same event
JSON, so one script serves both.
"""

import json
import re
import sys
import tempfile
from pathlib import Path

import shell

ASK = re.compile(r"\b(commit|commits|stage|staged|push|pr|pull request|amend)\b", re.I)
NEGATED = re.compile(r"\b(don't|do not|never|no|not|without)\s+(\w+\s+){0,2}$", re.I)
GATED = {"add", "commit", "stash", "merge", "cherry-pick", "rebase", "am", "revert", "commit-tree"}


def asks(prompt: str) -> bool:
    """Return whether the prompt asks for a commit, with no negation within three words before."""
    if prompt.rstrip().endswith("?"):
        return False
    return any(
        not NEGATED.search(prompt[max(0, m.start() - 40) : m.start()]) for m in ASK.finditer(prompt)
    )


def stages(command: str) -> bool:
    """Return whether any simple command in the text stages or commits."""
    for seg in shell.segments(command):
        sub, args, _ = shell.git_subcommand(seg)
        read = (sub == "stash" and args[:1] in (["list"], ["show"])) or (
            sub == "commit" and "--dry-run" in args
        )
        if sub in GATED and not read:
            return True
    return False


def mark(event: dict) -> Path:
    d = Path(tempfile.gettempdir()) / "agentic-modes"
    d.mkdir(exist_ok=True)
    return d / f"commit-ok-{event.get('session_id', 'nosession')}"


def hook(event: dict) -> None:
    match event.get("hook_event_name"):
        case "UserPromptSubmit" if not event.get("agent_id"):
            if asks(event.get("prompt", "")):
                mark(event).touch()
            else:
                mark(event).unlink(missing_ok=True)
        case "PreToolUse" if event.get("tool_name") == "Bash":
            if stages(event.get("tool_input", {}).get("command", "")) and not mark(event).is_file():
                reason = (
                    "The human has not asked for a commit in this turn. Leave the tree unstaged, "
                    "report what is ready, and wait for the word."
                )
                print(reason, file=sys.stderr)
                out = {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
                print(json.dumps({"hookSpecificOutput": out}))
                sys.exit(2)


if __name__ == "__main__":
    hook(json.load(sys.stdin))
