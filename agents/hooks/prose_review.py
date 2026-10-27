#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""
Claude Code hook: list the docstring and comment lines added in a turn that fail a prose rule.

Reads the hook event on stdin. SessionStart records the tree of the working copy's Python
files. Stop diffs that record against the current tree, checks each added docstring and
comment against the Python rules in ~/.claude/AGENTS.md, prints a block decision naming the
failing lines, and records the tree again. Records live per session under the repository's
git directory. Without a record, as in a repository the session entered after it started,
Stop only records. Outside a git repository or during a merge conflict the hook does nothing.
"""

import ast
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

PRAGMA = ("# type:", "# noqa", "# pragma", "# fmt:", "# ruff:", "# ty:", "# -*-")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)
WORD = re.compile(r"[A-Za-z]+")
IDENT = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])")  # the parts of snake_case and camelCase names
FUNCTION_WORDS = frozenset("a an the this that it its is are be of to for in on at by with from and or as into".split())  # noqa: SIM905 a word list reads best as one string  # fmt: skip
FILLER_VERBS = frozenset("return get set compute create build make handle process run call check perform do".split())  # noqa: SIM905 a word list reads best as one string  # fmt: skip
SECTION = re.compile(r"^[ \t]*([A-Z]\w*):[ \t]*$", re.MULTILINE)  # a header such as Args:
ARG_TYPE = re.compile(r"^\s*\w+\s*\([^)]*\)\s*:", re.MULTILINE)
DEFAULTS = re.compile(r"\bdefaults? to\b", re.IGNORECASE)
BANNER = re.compile(r"^#\s*(?:[-=*#~_]\s*){4,}")
STEP = re.compile(r"^#\s*(?:step\s*\d+\b|\d+[.):](?:\s|$))", re.IGNORECASE)
ADVICE = (
    "Prose review against the Python section of ~/.claude/AGENTS.md. "
    "Lines you added this turn that fail a rule:\n{lines}\n"
    "Fix each before you stop: delete the line, or rewrite it to state a fact the code does not."
)


def git(*args: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    """Return the stripped output of git, or "" when it fails."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def git_path(repo: Path, name: str) -> Path:
    return repo / git("rev-parse", "--git-path", name, cwd=repo)


def current_tree(repo: Path) -> str:
    """
    Return the tree of the working copy's Python files, written through a scratch index.

    Returns "" when the index holds a merge conflict, which write-tree refuses. Recorded, that
    "" makes the next Stop record only, so a merge's lines are never listed as the agent's.
    """
    index = git_path(repo, "index")
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "index"
        if index.is_file():
            shutil.copy(index, copy)
        env = os.environ | {"GIT_INDEX_FILE": str(copy)}
        git("add", "-A", "--", "*.py", cwd=repo, env=env)  # fails when no file matches
        return git("write-tree", cwd=repo, env=env)


def added_lines(repo: Path, base: str, tree: str) -> dict[str, set[int]]:
    """Map each changed Python file to the line numbers its diff adds."""
    diff = git(
        "-c", "core.quotePath=false", "diff-tree", "-r", "-p", "-U0", "--no-color", "-M",
        "--diff-filter=AMR", base, tree, "--", "*.py",
        cwd=repo,
    )  # fmt: skip
    added: dict[str, set[int]] = {}
    for section in f"\n{diff}".split("\ndiff --git ")[1:]:
        # git ends the header with a tab when the name holds a space
        name = next(
            (line[6:].rstrip("\t") for line in section.splitlines() if line.startswith("+++ b/")),
            "",
        )
        if not name or name.startswith('"'):  # a quoted name holds a control character
            continue
        for start, count in HUNK.findall(section):
            added.setdefault(name, set()).update(range(int(start), int(start) + int(count or 1)))
    return added


def stems(text: str, ignore: frozenset[str] = frozenset()) -> set[str]:
    """Return the words of text without a plural s, dropping each word in ignore."""
    words = (word.lower() for word in WORD.findall(text))
    return {word.rstrip("s") for word in words if not {word, word.rstrip("s")} & ignore}


def name_stems(*names: str) -> set[str]:
    return {part.lower().rstrip("s") for name in names for part in IDENT.findall(name)}


def docstring_faults(node: ast.AST, text: str) -> list[str]:
    summary = text.strip().partition("\n")[0].split(". ")[0]
    parts = SECTION.split(text)
    sections = dict(zip(parts[1::2], parts[2::2], strict=True))
    args = "".join(sections.get(h, "") for h in ("Args", "Arguments", "Parameters"))
    defaults: list[str] = []
    faults = []
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        names = [node.name]
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            params = [a for a in ast.walk(node.args) if isinstance(a, ast.arg)]
            names += [a.arg for a in params]
            names += [ast.unparse(a.annotation) for a in params if a.annotation]
            names += [ast.unparse(node.returns)] if node.returns else []
            values = [*node.args.defaults, *node.args.kw_defaults]
            defaults = [s for v in values if v and (s := ast.unparse(v).strip("'\""))]
        if not stems(summary, FUNCTION_WORDS | FILLER_VERBS) - name_stems(*names):
            faults.append("the summary restates the signature")
    if ARG_TYPE.search(args):
        faults.append("an Args entry repeats the type")
    if any(
        DEFAULTS.search(line) and re.search(rf"(?<![\w.]){re.escape(value)}(?!\w)", line)
        for line in args.splitlines()
        for value in defaults
    ):
        faults.append("an Args entry repeats the default")
    if {"Return", "Returns"} & sections.keys() and summary.lower().startswith("return"):
        faults.append("Returns repeats the summary")
    return faults


def comment_faults(text: str, code: str) -> list[str]:
    body = text.lstrip("#").strip()
    if BANNER.match(text):
        return ["a banner"]
    if STEP.match(text):
        return ["a step number"]
    words = stems(body, FUNCTION_WORDS)
    if words and words <= name_stems(code) | stems(code):
        return ["narrates the statement below"]
    return []


def next_code(lines: list[str], index: int) -> str:
    return next(
        (line for line in lines[index:] if line.strip() and not line.lstrip().startswith("#")), ""
    )


def file_findings(repo: Path, name: str, added: set[int]) -> list[str]:
    try:
        with tokenize.open(repo / name) as handle:
            source = handle.read()
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    return docstring_findings(name, source, added) + comment_findings(name, source, added)


def docstring_findings(name: str, source: str, added: set[int]) -> list[str]:
    found: list[str] = []
    with contextlib.suppress(SyntaxError):  # comments still count in a file that does not parse
        for node in ast.walk(ast.parse(source)):
            if not isinstance(
                node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
            ):
                continue
            first = node.body[0] if node.body else None
            if not (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                continue
            end = first.end_lineno or first.lineno
            if added.isdisjoint(range(first.lineno, end + 1)):
                continue
            text = first.value.value
            found += [
                f"{name}:{first.lineno}: {why}: {text.strip().partition('\n')[0]}"
                for why in docstring_faults(node, text)
            ]
    return found


def comment_findings(name: str, source: str, added: set[int]) -> list[str]:
    lines = source.splitlines()
    found: list[str] = []
    metadata = False  # inside a PEP 723 block, between "# /// script" and "# ///"
    # A line that does not tokenize ends the scan and keeps the comments before it.
    with contextlib.suppress(tokenize.TokenError, SyntaxError):
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            text, (row, col) = token.string, token.start
            if text.startswith("# ///"):
                metadata = text.strip() != "# ///"
                continue
            if metadata or text.startswith(PRAGMA):
                continue
            if row not in added:
                continue
            code = lines[row - 1][:col].strip() or next_code(lines, row)
            found += [f"{name}:{row}: {why}: {text}" for why in comment_faults(text, code)]
    return found


def review(repo: Path, session: str, *, record_only: bool) -> list[str]:
    """Return the failing prose lines added since this session's last record and record the tree again."""
    state = git_path(repo, "prose-review") / re.sub(r"[^\w.-]", "_", session)
    tree = current_tree(repo)
    base = "" if record_only or not state.is_file() else state.read_text().strip()
    found: list[str] = []
    if base:
        for name, lines in added_lines(repo, base, tree).items():
            found += file_findings(repo, name, lines)
    state.parent.mkdir(exist_ok=True)
    state.write_text(tree)
    return found


def main() -> int:
    """Read the hook event and, on Stop, print a block decision when added prose fails a rule."""
    event = json.load(sys.stdin)
    cwd = Path(event.get("cwd") or ".")
    try:
        top = git("rev-parse", "--show-toplevel", cwd=cwd)
    except OSError:
        return 0
    if not top:
        return 0
    found = review(
        Path(top),
        str(event.get("session_id") or "default"),
        record_only=event.get("hook_event_name") == "SessionStart",
    )
    if found:
        print(json.dumps({"decision": "block", "reason": ADVICE.format(lines="\n".join(found))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
