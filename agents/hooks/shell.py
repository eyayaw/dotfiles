"""Split a shell command into simple commands and name what each one writes.

Shared by the hooks that judge an agent's Bash call. Tokens come from shlex with shell punctuation
as separate tokens, so quotes hold, operators end a command, and a ``bash -c`` string is parsed in
turn. This is a reading of the text, not a shell: a program that opens its own files is invisible
here, which is why ``mode.py`` also compares the tree after the call.
"""

import shlex
from pathlib import Path

SEPARATORS = {";", ";;", "&&", "||", "|", "|&", "&", "\n", "(", ")", "{", "}"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>", "<>"}  # the next token names a file that gets written
WRAPPERS = {"env", "command", "exec", "nohup", "time", "nice", "caffeinate", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash"}
# program -> the operands it writes: all of them, the last one, or the files after an in-place flag
WRITERS = {
    "tee": "all",
    "touch": "all",
    "rm": "all",
    "rmdir": "all",
    "truncate": "all",
    "mkdir": "all",
    "cp": "last",
    "mv": "last",
    "ln": "last",
    "install": "last",
    "sed": "inplace",
    "perl": "inplace",
    "dd": "of",
}
GIT_WRITERS = {
    "checkout",
    "restore",
    "stash",
    "apply",
    "am",
    "cherry-pick",
    "merge",
    "rebase",
    "reset",
    "revert",
    "mv",
    "rm",
    "clean",
}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # an unbalanced quote: read the words, which is still better than nothing
        return command.replace("\n", " \n ").split()


def is_assignment(token: str) -> bool:
    name, eq, _ = token.partition("=")
    return bool(eq) and name.isidentifier()


def segments(command: str) -> list[list[str]]:
    """Return each simple command as its tokens, with env assignments and wrappers stripped.

    The first token is the program's base name. A ``bash -c`` string contributes its own commands.
    """
    out: list[list[str]] = []
    current: list[str] = []
    for token in [*tokens(command), ";"]:
        if token in SEPARATORS:
            out.extend(_strip(current))
            current = []
        else:
            current.append(token)
    return out


def _strip(seg: list[str]) -> list[list[str]]:
    i = 0
    while i < len(seg):
        if is_assignment(seg[i]) or seg[i] in WRAPPERS and seg[i] != "env":
            i += 1
        elif seg[i] == "env":
            i += 1
            while i < len(seg) and (seg[i].startswith("-") or is_assignment(seg[i])):
                i += 2 if seg[i] in ("-u", "-C", "-S") else 1
        else:
            break
    seg = seg[i:]
    if not seg:
        return []
    seg[0] = Path(seg[0]).name
    if seg[0] in SHELLS and "-c" in seg[:-1]:
        return [seg, *segments(seg[seg.index("-c") + 1])]
    return [seg]


def env_changes(command: str) -> set[str]:
    """Return the names a command assigns or unsets, through NAME=, env -u, or unset."""
    names = set()
    toks = tokens(command)
    for i, token in enumerate(toks):
        if is_assignment(token):
            names.add(token.partition("=")[0])
        elif token in ("-u", "--unset") and i and toks[i - 1] == "env" or token == "unset":
            names.update(t for t in toks[i + 1 : i + 2] if t.isidentifier())
    return names


def git_subcommand(seg: list[str]) -> tuple[str, list[str], list[str]]:
    """Return a git segment's subcommand, its arguments, and the global options before it."""
    if seg[:1] != ["git"]:
        return "", [], []
    i = 1
    options = []
    while i < len(seg) and seg[i].startswith("-"):
        options.append(seg[i])
        if seg[i] in GIT_OPTIONS_WITH_VALUE and i + 1 < len(seg):
            options.append(seg[i + 1])
            i += 1
        i += 1
    return (seg[i], seg[i + 1 :], options) if i < len(seg) else ("", [], options)


def operands(args: list[str]) -> list[str]:
    """Return the arguments that are not options; everything after ``--`` counts."""
    if "--" in args:
        i = args.index("--")
        return [a for a in args[:i] if not a.startswith("-")] + args[i + 1 :]
    return [a for a in args if not a.startswith("-")]


def write_targets(seg: list[str]) -> list[str]:
    """Return the paths a simple command writes, as far as its text shows."""
    targets = []
    plain: list[str] = []  # the command without its redirections
    skip = False
    for i, token in enumerate(seg):
        if skip:
            skip = False
        elif token in REDIRECTS or token in ("<", "<<", "<<<", "<&", ">&"):
            skip = i + 1 < len(seg)
            if token in REDIRECTS and skip and not seg[i + 1].startswith("/dev/"):
                targets.append(seg[i + 1])
        else:
            plain.append(token)
    if not plain:
        return targets
    program, args = plain[0], plain[1:]
    ops = [o for o in operands(args) if o]
    if program == "git":
        sub, rest, _ = git_subcommand(plain)
        if sub in GIT_WRITERS:
            targets += operands(rest)
    elif (rule := WRITERS.get(program)) == "all":
        targets += ops
    elif rule == "last" and ops:
        targets.append(ops[-1])
    elif rule == "inplace" and any(a.startswith(("-i", "-pi", "-ni", "-I")) for a in args):
        targets += ops[1:]  # after the script
    elif rule == "of":
        targets += [a.removeprefix("of=") for a in args if a.startswith("of=")]
    return targets
