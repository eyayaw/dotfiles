#!/bin/bash
input=$(cat)

# Adapted from https://github.com/trailofbits/claude-code-config

# Single jq call for all values
IFS=$'\t' read -r cwd model_name cost duration_ms ctx_used ctx_tokens ctx_window cache_pct < <(
    echo "$input" | jq -r '[
        .workspace.current_dir // "unknown",
        .model.display_name // "Unknown",
        (try (.cost.total_cost_usd // 0 | . * 100 | floor / 100) catch 0),
        (.cost.total_duration_ms // 0),
        (try (
            if (.context_window.remaining_percentage // null) != null then
                100 - (.context_window.remaining_percentage | floor)
            elif (.context_window.used_percentage // null) != null then
                .context_window.used_percentage | floor
            else "null" end
        ) catch "null"),
        (try ((.context_window.current_usage.input_tokens // 0) +
              (.context_window.current_usage.cache_creation_input_tokens // 0) +
              (.context_window.current_usage.cache_read_input_tokens // 0)) catch 0),
        (.context_window.context_window_size // 0),
        (try (
            (.context_window.current_usage // {}) |
            if (.input_tokens // 0) + (.cache_read_input_tokens // 0) > 0 then
                ((.cache_read_input_tokens // 0) * 100 /
                 ((.input_tokens // 0) + (.cache_read_input_tokens // 0))) | floor
            else 0 end
        ) catch 0)
    ] | @tsv'
)

# Tilde-shorten path and lowercase
dir=$(echo "$cwd" | sed "s|^$HOME|~|" | tr '[:upper:]' '[:lower:]')

# Strip parenthetical suffixes like "(1M context)"
model=$(echo "$model_name" | sed 's/ *([^)]*)$//')

# Git info
branch=""
status=""
if cd "$cwd" 2>/dev/null; then
    branch=$(git -c core.useBuiltinFSMonitor=false rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        porcelain=$(git status --porcelain 2>/dev/null)
        staged=$(echo "$porcelain" | grep -c '^[MADRC]')
        modified=$(echo "$porcelain" | grep -c '^ [MD]\|^MM\|^.D')
        untracked=$(echo "$porcelain" | grep -c '^??')
        [ "$staged" -gt 0 ] 2>/dev/null && status="${status}+${staged}"
        [ "$modified" -gt 0 ] 2>/dev/null && status="${status}!${modified}"
        [ "$untracked" -gt 0 ] 2>/dev/null && status="${status}?${untracked}"
    fi
fi

# Dim separator
SEP='\033[2m│\033[0m'

# Line 1: path (blue), branch (cyan), model
printf '\033[94m%s\033[0m' "$dir"
if [ -n "$branch" ]; then
    printf '  \033[96m%s\033[0m' "$branch"
    [ -n "$status" ] && printf ' \033[33m%s\033[0m' "$status"
fi
printf ' %b \033[37m%s\033[0m' "$SEP" "$model"

# Color-coded progress bar (green <50%, yellow 50-79%, red 80%+)
if [ -n "$ctx_used" ] && [ "$ctx_used" != "null" ]; then
    bar_width=10
    filled=$((ctx_used * bar_width / 100))
    empty=$((bar_width - filled))

    if [ "$ctx_used" -lt 50 ]; then
        color='\033[32m'   # green
    elif [ "$ctx_used" -lt 80 ]; then
        color='\033[33m'   # yellow
    else
        color='\033[31m'   # red
    fi

    bar="${color}"
    for ((i=0; i<filled; i++)); do bar="${bar}█"; done
    bar="${bar}\033[2m"
    for ((i=0; i<empty; i++)); do bar="${bar}⣿"; done
    bar="${bar}\033[0m"

    # Format token counts as human-readable (e.g. 240k/1M)
    fmt_tokens() {
        local n=$1
        if [ "$n" -ge 1000000 ]; then
            awk -v n="$n" 'BEGIN{printf "%.1fM", n/1000000}'
        elif [ "$n" -ge 1000 ]; then
            printf '%sk' "$((n / 1000))"
        else
            printf '%s' "$n"
        fi
    }
    tok_str=""
    if [ "$ctx_tokens" -gt 0 ] 2>/dev/null && [ "$ctx_window" -gt 0 ] 2>/dev/null; then
        tok_str=" ($(fmt_tokens "$ctx_tokens")/$(fmt_tokens "$ctx_window"))"
    fi

    printf ' %b %d%%%s' "$bar" "$ctx_used" "$tok_str"
fi

# Cost
if [ "$cost" != "0" ]; then
    printf ' %b \033[33m$%s\033[0m' "$SEP" "$cost"
fi

# Session time
if [ "$duration_ms" -gt 0 ] 2>/dev/null; then
    total_sec=$((duration_ms / 1000))
    hours=$((total_sec / 3600))
    minutes=$(((total_sec % 3600) / 60))
    seconds=$((total_sec % 60))
    if [ "$hours" -gt 0 ]; then
        t="${hours}h${minutes}m"
    elif [ "$minutes" -gt 0 ]; then
        t="${minutes}m${seconds}s"
    else
        t="${seconds}s"
    fi
    printf ' %b \033[36m%s\033[0m' "$SEP" "$t"
fi

# Cache hit rate
if [ "$cache_pct" -gt 0 ] 2>/dev/null; then
    printf ' \033[2m↻%s%%\033[0m' "$cache_pct"
fi
