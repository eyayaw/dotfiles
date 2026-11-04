#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Enforce a repository's ship or learn mode for agents and for git.

A repository declares its mode in ``mode.toml`` at its root::

    mode = "learn"                  # or "ship"
    max_diff_lines = 200            # cap on added+deleted lines per commit
    exclude = ["*.lock"]            # globs left out of the line count

    [ship]
    human = ["tests/acceptance/"]   # paths only the human edits in this mode

    [learn]
    human = ["tests/acceptance/", "src/pkg/core/"]

``mode hook`` reads a Claude Code or Codex event from stdin. SessionStart prints the mode as
context. PreToolUse denies an Edit, Write, or Codex patch under a human-owned path, and a Bash
command that writes there, hides the agent marker, or turns git's hooks off. PostToolUse on Bash
reports a human-owned file the command changed anyway, by content, ignoring what a checkout moved
in step with HEAD. ``mode precommit`` rejects a staged diff over the cap and an agent's commit
touching a human-owned path; the agent is known by the ``CLAUDECODE`` or ``CODEX_AGENT`` variable
each harness sets in its shell. ``mode set learn|ship`` switches, allowing one learn repo at a time.
``mode status`` prints the mode here and the repo in learn mode. Exit 2 is the block signal for
both harnesses and for git.

The shell checks read the command text. A program that opens its own files, or a command run
from a cwd outside the repo, is caught only by the PostToolUse comparison and the pre-commit.
"""

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import shell

PROJECTS = Path.home() / "Developer"
SWITCH_LOG = Path.home() / ".local/state/agentic-modes/switches.tsv"
AGENT_MARKERS = {"CLAUDECODE", "CODEX_AGENT"}  # set in the shell by each harness
HOOK_SWITCHES = re.compile(r"^(PREK_)?SKIP$|^GIT_CONFIG_")  # env names that turn git hooks off
DEFAULT_EXCLUDE = ["*.lock", "*.snap", "*.ipynb", "*.csv", "*.parquet"]
CASEFOLD = sys.platform == "darwin"  # APFS matches paths without regard to case
PATCH_PATH = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.M)
ROLE = {
    "ship": "You write the code; the human reviews by behaviour. New tests fail before the "
    "implementation, and you show that run as evidence.",
    "learn": "The human writes the core code to learn. You answer conceptual questions, review "
    "what the human wrote, write tests against the spec, and run /quiz when asked. A worked "
    "example or skeleton goes under notes/, never into core.",
}
GATE = "The pre-commit hooks are the gate. Commit with them on and fix what they report."


def key(path: Path) -> str:
    return str(path).casefold() if CASEFOLD else str(path)


def relative(p: object) -> bool:
    return isinstance(p, str) and not Path(p).is_absolute() and ".." not in Path(p).parts


class Mode:
    def __init__(self, root: Path, data: dict) -> None:
        self.root = root
        self.mode = data.get("mode")
        if self.mode not in ROLE:
            raise ValueError(f"mode must be ship or learn, not {self.mode!r}")
        human = data.get(self.mode, {}).get("human")
        if not isinstance(human, list) or not all(relative(p) for p in human):
            raise ValueError(
                f"[{self.mode}] human must be a list of paths relative to the repo root"
            )
        self.human = [(root / p).resolve() for p in human]
        self.max_diff_lines = data.get("max_diff_lines", 200)
        self.exclude = data.get("exclude", DEFAULT_EXCLUDE)
        if not isinstance(self.max_diff_lines, int) or not all(
            isinstance(g, str) for g in self.exclude
        ):
            raise ValueError("max_diff_lines must be an integer and exclude a list of globs")

    @classmethod
    def find(cls, start: Path) -> Mode | None:
        """Return the mode of the nearest enclosing repo, or None without a mode.toml.

        Raises ValueError, naming the file, for a mode.toml that cannot be used.
        """
        for d in (start.resolve(), *start.resolve().parents):
            if (f := d / "mode.toml").is_file():
                try:
                    return cls(d, tomllib.loads(f.read_text()))
                except (tomllib.TOMLDecodeError, ValueError) as e:
                    raise ValueError(f"{f}: {e}") from None
        return None

    def owned(self) -> str:
        return ", ".join(str(c.relative_to(self.root)) for c in self.human) or "nothing"

    def is_human(self, path: str | Path, cwd: Path) -> bool:
        p = key((cwd / Path(os.path.expanduser(str(path)))).resolve())
        return any(p == key(c) or p.startswith(key(c) + "/") for c in self.human)

    def tree(self) -> dict[str, str]:
        """Return a content hash per tracked or unignored file under the human-owned paths."""
        rel = [str(c.relative_to(self.root)) for c in self.human]
        listed = git(
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *rel,
            cwd=self.root,
        )
        files = ((p, self.root / p) for p in listed.split("\0") if p)
        return {
            p: hashlib.blake2b(f.read_bytes(), digest_size=16).hexdigest()
            for p, f in files
            if f.is_file()
        }

    def dirty(self) -> set[str]:
        """Return the human-owned paths that differ from HEAD or are untracked."""
        rel = [str(c.relative_to(self.root)) for c in self.human]
        status = git(
            "status",
            "--porcelain",
            "-z",
            "--no-renames",
            "--untracked-files=all",
            "--",
            *rel,
            cwd=self.root,
        )
        return {entry[3:] for entry in status.split("\0") if entry}

    def context(self) -> str:
        return (
            f"Repo mode: {self.mode.upper()}. Human-owned paths, which you never create or edit, "
            f"including through shell commands: {self.owned()}. {ROLE[self.mode]} "
            f"Each commit stays under {self.max_diff_lines} changed lines."
        )


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    out = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    print(json.dumps({"hookSpecificOutput": out}))
    sys.exit(2)


def hooks_off(command: str) -> str:
    """Return why the command would hide the agent marker or commit with git's hooks off, or ''."""
    names = shell.env_changes(command)
    if hit := names & AGENT_MARKERS:
        return f"{hit.pop()} marks the agent's shell and stays set. " + GATE
    if any(HOOK_SWITCHES.match(n) for n in names):
        return GATE
    for seg in shell.segments(command):
        sub, args, _ = shell.git_subcommand(seg)
        flags = [a for a in args if a.startswith("-")]
        if sub == "commit" and any(
            a.startswith("--no-v") or re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", a) for a in flags
        ):
            return GATE
        if sub == "commit-tree" or any(
            s in " ".join(seg).casefold() for s in ("core.hookspath", ".git/hooks")
        ):
            return GATE
    return ""


def hook(event: dict) -> None:
    cwd = Path(event.get("cwd") or os.getcwd())
    name, tool = event.get("hook_event_name"), event.get("tool_name", "")
    inp = event.get("tool_input", {})
    command = inp.get("command", "")
    if name == "PreToolUse" and tool == "Bash" and (reason := hooks_off(command)):
        deny(reason)
    try:
        mode = Mode.find(cwd)
    except ValueError as e:
        deny(f"mode.toml cannot be used: {e}")
    if mode is None:
        return
    snapshot = Path(tempfile.gettempdir()) / "agentic-modes"
    snapshot /= f"{event.get('session_id', 'nosession')}-{event.get('tool_use_id', 'notool')}.json"
    match name, tool:
        case "SessionStart", _:
            print(mode.context())
        case "PreToolUse", "Edit" | "Write" | "NotebookEdit":
            path = inp.get("file_path") or inp.get("notebook_path") or ""
            if path and mode.is_human(path, cwd):
                deny(f"{path} is human-owned ({mode.owned()}). Explain, review, or propose it.")
        case "PreToolUse", "apply_patch":
            hits = [
                p
                for m in PATCH_PATH.finditer(command)
                for p in m.groups()
                if p and mode.is_human(p, cwd)
            ]
            if hits:
                deny(f"The patch touches {', '.join(hits)}, human-owned ({mode.owned()}).")
        case "PreToolUse", "Bash":
            hits = [
                t
                for seg in shell.segments(command)
                for t in shell.write_targets(seg)
                if mode.is_human(t, cwd)
            ]
            if hits:
                deny(f"This looks like a write to {', '.join(hits)}, human-owned ({mode.owned()}).")
            snapshot.parent.mkdir(exist_ok=True)
            snapshot.write_text(json.dumps(mode.tree()))
        case "PostToolUse" | "PostToolUseFailure", "Bash" if snapshot.is_file():
            before = json.loads(snapshot.read_text())
            snapshot.unlink()
            after, dirty = mode.tree(), mode.dirty()
            changed = sorted(
                p
                for p in before.keys() | after.keys()
                if before.get(p) != after.get(p) and p in dirty
            )
            if changed:  # exit 2 so the message reaches the agent; exit 1 would only warn the user
                print(
                    f"The last command changed human-owned files: {', '.join(changed)}. Stop, "
                    "revert nothing, and tell the human what you ran and what you meant to do.",
                    file=sys.stderr,
                )
                sys.exit(2)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def precommit() -> None:
    root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
    mode = Mode.find(root)
    if mode is None:
        return
    agent = next((m for m in AGENT_MARKERS if os.environ.get(m)), None)
    total = 0
    touched = []
    for entry in git("diff", "--cached", "--numstat", "-z", "--no-renames", cwd=root).split("\0"):
        if not entry:
            continue
        added, deleted, path = entry.split("\t", 2)
        if agent and mode.is_human(path, root):
            touched.append(path)
        excluded = any(
            fnmatch.fnmatch(path, g) or fnmatch.fnmatch(Path(path).name, g) for g in mode.exclude
        )
        if added != "-" and not excluded:
            total += int(added) + int(deleted)
    if touched:
        sys.exit(
            f"mode: this commit comes from an agent ({agent}) but touches human-owned files: "
            f"{', '.join(touched)}. Unstage them and let the human commit them."
        )
    if total > mode.max_diff_lines:
        sys.exit(
            f"mode: staged diff is {total} lines, over the cap of {mode.max_diff_lines}. "
            "Split the change into commits of one idea each."
        )


def learn_repos() -> list[Path]:
    found = []
    for f in [*PROJECTS.glob("*/mode.toml"), *PROJECTS.glob("*/*/mode.toml")]:
        try:
            if tomllib.loads(f.read_text()).get("mode") == "learn":
                found.append(f.parent)
        except tomllib.TOMLDecodeError as e:
            print(f"mode: skipping {f}: {e}", file=sys.stderr)
    return found


def set_mode(target: str) -> None:
    mode = Mode.find(Path.cwd())
    if mode is None:
        sys.exit("mode: no mode.toml found here or above. Create one at the repo root first.")
    if target == "learn":
        others = [r for r in learn_repos() if r != mode.root]
        if others:
            sys.exit(f"mode: {others[0]} is already in learn mode. Switch it to ship first.")
    f = mode.root / "mode.toml"
    text, n = re.subn(
        r'^(mode\s*=\s*)"(ship|learn)"', rf'\1"{target}"', f.read_text(), count=1, flags=re.M
    )
    if n != 1:
        sys.exit(f"mode: could not find the mode line in {f}.")
    f.write_text(text)
    SWITCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SWITCH_LOG.open("a") as log:
        log.write(
            f"{datetime.now(UTC).isoformat(timespec='seconds')}\t{mode.root}\t{mode.mode}\t{target}\n"
        )
    print(f"mode: {mode.root.name} {mode.mode} -> {target}")


def status() -> None:
    mode = Mode.find(Path.cwd())
    here = (
        f"{mode.root.name}: {mode.mode}, human-owned: {mode.owned()}"
        if mode
        else "no mode.toml (ship)"
    )
    print(f"{here}\nlearn mode: {', '.join(str(r) for r in learn_repos()) or 'none'}")


def main() -> None:
    try:
        match sys.argv[1:]:
            case ["hook"]:
                hook(json.load(sys.stdin))
            case ["precommit"]:
                precommit()
            case ["set", ("ship" | "learn") as target]:
                set_mode(target)
            case ["status"]:
                status()
            case _:
                sys.exit("usage: mode hook | mode precommit | mode set ship|learn | mode status")
    except ValueError as e:
        sys.exit(f"mode: {e}")


if __name__ == "__main__":
    main()
