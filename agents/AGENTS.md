# Global agent instructions

## Tooling
- Python: use uv, never pip. `uv add <pkg>`, `uv sync`, `uv run -m pytest tests/`;
  `uv run --with="httpx,bs4" script.py` for ad-hoc deps. Run `uv lock` after version bumps.
- Lint/format Python with ruff.
- Use built-in generics (`list`, `dict`), not `typing.List`/`Dict`; importing `Any` etc. is fine.
- Search with `fd` and `rg`; keep their defaults of skipping gitignored and hidden files.
- Parse .docx with `doxx`, .xlsx with `xleak`.
- R: use `=` for assignment, not `<-`.
- Remote file transfer: rsync, not scp.
- GitHub: use the `gh` CLI, not browser apps; if an API call fails, retry once or twice.

## Git
- Stage only the files you modified; never `git add -A`.
- Conventional commits: `<type>[scope]: <description>` (`feat:`, `fix:`, `docs:`, ...);
  `!` before `:` for breaking changes.
- Commit bodies: concise; bullets when there are multiple meaningful changes. No padding
  with obvious detail.
- Multiline Git/GitHub text: never pass `\n` escapes—they may render literally. For
  commits, use repeated `-m` flags or `git commit -F`; for GitHub bodies, use
  `--body-file` or actual multiline input.
- No AI attribution trailers (`Co-Authored-By: Claude/Codex...`); an existing
  "Generated with ..." PR-body footer is fine to leave.
- Branch names: `feature/...`, `refactor/...`, etc.—no `agent/` prefix.
- Never push without my consent.

## Prose
- American English: -ize/-ization, neighbor, artifact, modeling; "20%" not "20 %".
- No spaces around em dashes. Punctuation outside quotation marks: `"b",` not `"b,"`.
- Precise claims over grand ones—describe outputs as what they are.

## Autonomy
Preferences for a single-user workflow. Flip any line.
- Code comments: keep ones that explain WHY, non-obvious mechanisms, or load-bearing
  ordering. Strip only trivial WHAT-restates-code. When in doubt, keep.
- Don't confirm: file edits/moves/renames, scaffolding in-scope files, running scripts
  and tests, local git ops (`add`, `commit`, `mv`, `rm`, `reset --soft`), amending
  unpushed commits on a feature branch.
- Do confirm: any `git push`, `git reset --hard`, `rm -rf` outside the working tree,
  creating/closing/commenting on PRs or issues, modifying CI.
- "go", "ok to all", "proceed" = execute the discussed scope without further questions.

## Repository scope
- Writable repo = the one containing the cwd; any other (sibling, parent, dependency,
  package) is read-only unless my prompt explicitly names it. Discovering a repo on
  disk, inherited plans/earlier-agent work, and autonomy keywords don't expand scope.
- If the task seems to require changes elsewhere, stop and ask first, stating the
  repo path and proposed changes.

## End-of-task notes
- Optionally close with a brief "wisdom gems" note: programming idioms, engineering
  folklore, or jargon that came up naturally in the work (e.g. shim, footgun,
  yak shaving, leaky abstraction). Only when genuinely useful—no trivia as filler.
