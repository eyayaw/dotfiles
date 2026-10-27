#!/usr/bin/env bash
# Blocks an agent's `git commit` or `gh pr|issue create|edit|comment` until the
# usuals skill has checked exactly what would ship.
#
#   usuals-gate.sh record [FILE...]   run by usuals after its checks pass: records
#                                     the tree and the message or body FILEs
#   usuals-gate.sh                    PreToolUse hook: reads the tool call on stdin
#
# A commit needs the tree and its message file to match; a gh post needs only its
# body file. The tree covers every file git sees (tracked and untracked, minus
# ignored), so each commit of a stack cut from one checked working tree passes.
# Inline -m or --body text is not fingerprinted; message and body files (-F,
# --body-file) are.
# The hook runs before the command, so it cannot see a file that the same command
# writes before committing. A commit behind `env`, `command`, `time`, or `bash -c`,
# and a gh post behind any prefix, is not matched.
set -u

tree() {  # build the tree in a copy of the index, so the real index stays untouched
    local tmp
    tmp=$(mktemp)
    cp "$(git rev-parse --git-path index)" "$tmp" 2>/dev/null || rm -f "$tmp"  # no index yet: start empty
    GIT_INDEX_FILE=$tmp git add -A . >/dev/null 2>&1 && GIT_INDEX_FILE=$tmp git write-tree
    rm -f "$tmp"
}
marker() { git rev-parse --git-path usuals-ok; }

if [ "${1:-}" = record ]; then
    shift
    git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "usuals-gate: not in a git repository" >&2; exit 1; }
    {
        echo "tree $(cd "$(git rev-parse --show-toplevel)" && tree)"
        for f in "$@"; do echo "file $(git hash-object "$f")"; done
    } >"$(marker)"
    echo "usuals-gate: recorded $(head -1 "$(marker)")"
    exit 0
fi

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
dir=$(jq -r '.cwd // empty' <<<"$input")
start=$'(^|[;&|(\n][[:space:]]*)'
envs='([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*'
q="'"
path="(\"[^\"]*\"|${q}[^${q}]*${q}|[^;&|[:space:]]+)"  # quoted, or up to a space
opts="([[:space:]]+-[cC][[:space:]]+${path}|[[:space:]]+--[a-z-]+(=[^[:space:]]+)?)*"
commit_re="${start}${envs}git${opts}[[:space:]]+commit([[:space:]]|$)"
if [[ $cmd =~ $commit_re ]]; then
    hit=${BASH_REMATCH[0]}; files_re='(-F|--file)[=[:space:]]+([^[:space:]]+)'
elif [[ $cmd =~ ${start}gh[[:space:]]+(pr|issue)[[:space:]]+(create|edit|comment)([[:space:]]|$) ]]; then
    hit=${BASH_REMATCH[0]}; files_re='(-F|--body-file)[=[:space:]]+([^[:space:]]+)'
    post=1  # a gh post ships only its body, so only the body file is checked
else
    exit 0
fi
# Each commit's own arguments: line continuations joined, quoted strings removed whole, cut
# at the next command or line. A short cluster counts only when every flag before the n
# takes no argument (so -minit and -uno pass), and git accepts --no-veri and --no-verif as
# --no-verify. Before `commit`, a hook.* or core.hooksPath setting, a SKIP or PREK_SKIP
# variable, and a GIT_CONFIG_PARAMETERS or GIT_CONFIG_COUNT variable each turn hooks off.
off_re="(-c[[:space:]]+[\"']?|--config-env=)(hook\.|core\.hookspath)|(^|[[:space:];&|(])((prek_)?skip|git_config_parameters|git_config_count)="
rest=${cmd//$'\\\n'/ }
while [ -z "${post:-}" ] && [[ $rest =~ $commit_re ]]; do
    h=${BASH_REMATCH[0]}; rest=${rest#*"$h"}; args=$rest
    while [[ $args =~ \"[^\"]*\"|\'[^\']*\' ]]; do args=${args/"${BASH_REMATCH[0]}"/}; done
    args=${args%%[;\&|$'\n']*}
    h=$(tr '[:upper:]' '[:lower:]' <<<"$h")
    if [[ " $args " =~ [[:space:]](--no-veri(fy?)?|-[aeiopqsvz]*n[aeiopqsvz]*([CcFmStu][^[:space:]]*)?)[[:space:]] ]] ||
        [[ $h =~ $off_re ]]; then
        echo "usuals-gate: the pre-commit hooks are the gate. Commit with them on and fix what they report." >&2; exit 2
    fi
done
# The command runs where its last `cd` before the match, then `git -C`, point.
sub='' c=''
rest=${cmd%%"$hit"*}
while [[ $rest =~ ${start}cd[[:space:]]+${path} ]]; do sub=${BASH_REMATCH[2]}; rest=${rest#*"${BASH_REMATCH[0]}"}; done
[[ $hit =~ -C[[:space:]]+${path} ]] && c=${BASH_REMATCH[1]}
dir=${dir:-$PWD}
for d in "$sub" "$c"; do
    d=${d//[\"\']/}
    [ -z "$d" ] && continue
    [[ $d = *[\$\`]* ]] && exit 0  # a path only the shell can expand: cannot tell the repo
    d=${d/#\~/$HOME}; [[ $d = /* ]] && dir=$d || dir=$dir/$d
done
cd "$dir" 2>/dev/null && git rev-parse --show-toplevel >/dev/null 2>&1 || exit 0

block() { echo "usuals-gate: $1 Run the usuals skill on the change, including any message or body file, then retry." >&2; exit 2; }
if [ -z "${post:-}" ]; then
    [ -f "$(marker)" ] || block "usuals has not run in this checkout."
    grep -qx "tree $(cd "$(git rev-parse --show-toplevel)" && tree)" "$(marker)" || block "the files changed after usuals last passed."
fi
rest=$cmd
while [[ $rest =~ $files_re ]]; do
    f=${BASH_REMATCH[2]}; rest=${rest#*"${BASH_REMATCH[0]}"}
    [ -f "$f" ] || continue
    grep -qx "file $(git hash-object "$f")" "$(marker)" || block "usuals has not checked $f."
done
exit 0
