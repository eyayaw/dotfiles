#!/usr/bin/env bash
# Bootstrap tmux sessions if they don't exist. Idempotent.
#
# Usage:
#   tmux-sessions.sh           # create all defined sessions
#   tmux-sessions.sh dev data  # only create the named sessions

set -u

REQUESTED=("$@")
EXISTING=$'\n'$(tmux list-sessions -F '#S' 2>/dev/null)$'\n'

# Spec format: window-name=absolute-path
# First positional after $cwd becomes the first window of the session.
create_session() {
    local name=$1 cwd=$2
    shift 2

    if ((${#REQUESTED[@]})); then
        local r matched=
        for r in "${REQUESTED[@]}"; do [[ $r == "$name" ]] && matched=1; done
        [[ $matched ]] || return 0
    fi

    if [[ $EXISTING == *$'\n'"$name"$'\n'* ]]; then
        echo "skip   $name"
        return 0
    fi

    local args spec
    if (($# == 0)); then
        args=(new-session -d -s "$name" -c "$cwd")
    else
        local first=$1; shift
        args=(new-session -d -s "$name" -c "${first#*=}" -n "${first%%=*}")
        for spec in "$@"; do
            args+=(';' new-window -t "$name:" -n "${spec%%=*}" -c "${spec#*=}")
        done
        args+=(';' select-window -t "$name:1")
    fi
    tmux "${args[@]}"
    echo "create $name"
}

create_session dev ~/Developer/datakomari/packages \
    databrew=$HOME/Developer/datakomari/packages/databrew \
    itemstore=$HOME/Developer/datakomari/packages/itemstore \
    fetchkit=$HOME/Developer/datakomari/packages/fetchkit \
    extractkit=$HOME/Developer/datakomari/packages/extractkit \
    eg2c=$HOME/Developer/datakomari/packages/eg2c

create_session data ~/Developer/datakomari/gan \
    jiji-africa=$HOME/Developer/datakomari/gan/jiji-africa \
    jumia=$HOME/Developer/datakomari/gan/jumia \
    afrotie=$HOME/Developer/datakomari/gan/afrotie \
    eth-crawlers=$HOME/Developer/datakomari/gan/eth-crawlers

create_session config ~/Developer/dotfiles \
    dotfiles=$HOME/Developer/dotfiles \
    skills=$HOME/Developer/workflows/skills \
    claude=$HOME/.claude \
    homeautomation=$HOME/Developer/HomeAutomation \
    site=$HOME/Documents/Projects/eyayaw.github.io

create_session learn ~/Documents/Learning \
    nederlands=$HOME/Documents/Learning/nederlandes-leren \
    driving=$HOME/Documents/Learning/driving

create_session research   ~/Documents/Projects/research
create_session career     ~/Documents/Projects/profile/career
create_session work       "$HOME/AMS Institute Dropbox/Eyayaw Beze/Work/Ideals"
create_session playground ~/Developer/playground
