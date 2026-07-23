#!/bin/bash
# Statusline: cwd │ branch │ model (effort) │ context usage

# One jq pass: extract fields and pre-format the token counts.
# Unit-separator, not tab: read() would collapse empty fields on whitespace IFS.
IFS=$'\x1f' read -r cwd model effort pct tokens < <(
    jq -r '
        def fmt: if . >= 1000000 then "\(. / 100000 | floor / 10)M"
                 elif . >= 1000 then "\(. / 1000 | floor)k"
                 else "\(.)" end;
        (.context_window // {}) as $c |
        (($c.current_usage // {}) | (.input_tokens // 0)
            + (.cache_creation_input_tokens // 0)
            + (.cache_read_input_tokens // 0)) as $used |
        [
            .workspace.current_dir // "unknown",
            .model.display_name // "Unknown",
            .effort.level // "",
            (if   $c.remaining_percentage then 100 - ($c.remaining_percentage | floor)
             elif $c.used_percentage      then $c.used_percentage | floor
             else "" end),
            (if $used > 0 and ($c.context_window_size // 0) > 0
             then " (\($used | fmt)/\($c.context_window_size | fmt))"
             else "" end)
        ] | map(tostring) | join("")'
)

dir=$(printf '%s' "${cwd/#$HOME/\~}" | tr '[:upper:]' '[:lower:]')
model=${model% (*)} # drop suffixes like "(1M context)"
branch=$(cd "$cwd" 2>/dev/null && git --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)

R=$'\033[0m' DIM=$'\033[2m' BLUE=$'\033[94m' CYAN=$'\033[96m' GRAY=$'\033[37m'

seg=("$BLUE$dir$R")
[ -n "$branch" ] && seg+=("$CYAN$branch$R")
[ -n "$effort" ] && effort=" $DIM($effort)$R"
seg+=("$GRAY$model$R$effort")

if [ -n "$pct" ]; then
    if   [ "$pct" -lt 50 ]; then color=$'\033[32m'   # green
    elif [ "$pct" -lt 80 ]; then color=$'\033[33m'   # yellow
    else                         color=$'\033[31m'   # red
    fi
    seg+=("$color$pct%$tokens$R")
fi

printf '%s' "${seg[0]}"
SEP="|"
for s in "${seg[@]:1}"; do printf '%s%s' " ${DIM}${SEP}${R} " "$s"; done
