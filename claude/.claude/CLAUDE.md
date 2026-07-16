@AGENTS.md

# Claude Code specific
- System-reminder nags (TodoWrite, date-changed, linter-modified, auto-mode
  signals): absorb silently; don't restate or re-ask.
- End-of-turn summary: only when there's something non-obvious or a real next
  step. If the commit or diff tells the story, end without one.
