# Homebrew must be prepended here, not in .zshenv/.zshrc: /etc/zprofile runs
# path_helper AFTER .zshenv and rebuilds PATH with system dirs first, and
# login non-interactive shells (zsh -lc, used by codex/launchd/IDEs) never
# read .zshrc — so this is the only file where the prepend both survives
# path_helper and reaches non-interactive shells.
eval "$(/opt/homebrew/bin/brew shellenv)"
