#!/usr/bin/env zsh
pkgs=(yt-dlp sqlit-tui streamlit "mcp[cli]" "marimo[recommended]" markitdown marker)
for pkg in ${pkgs[@]}; do
  uv tool install $pkg
done
