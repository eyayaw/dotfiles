#!/bin/zsh

if [ -f "$ZED_WORKTREE_ROOT/.venv/bin/activate" ]; then
    source "$ZED_WORKTREE_ROOT/.venv/bin/activate" && python3 "$@"
elif [ -f "$ZED_WORKTREE_ROOT/venv/bin/activate" ]; then
    source "$ZED_WORKTREE_ROOT/venv/bin/activate" && python3 "$@"
else
    python3 "$@"
fi
