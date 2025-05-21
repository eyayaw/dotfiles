#!/usr/bin/env zsh
pkgs=(yt-dlp streamlit "mcp[cli]" "marimo[recommended]" markitdown marker)
for pkg in ${pkgs[@]}; do
  uv tool install $pkg
done
