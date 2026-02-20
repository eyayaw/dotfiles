#!/usr/bin/env zsh
# Install custom Ghostty themes not bundled with Ghostty

THEMES_DIR="$HOME/.config/ghostty/themes"
mkdir -p "$THEMES_DIR"

KANSO_BASE="https://raw.githubusercontent.com/webhooked/kanso.nvim/main/extras/ghostty"
for variant in kanso-zen kanso-ink kanso-mist kanso-pearl; do
  curl -sL "$KANSO_BASE/$variant" -o "$THEMES_DIR/$variant"
done

echo "Ghostty custom themes installed to $THEMES_DIR"
