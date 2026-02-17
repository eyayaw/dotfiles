#!/usr/bin/env zsh

# Installation of homebrew, brew packages, fonts, and other tools
source scripts/install.sh

# MacOS Settings
source scripts/macos/update.sh
source scripts/macos/set_defaults.sh

# stow .gitignore
# an empty .stow-local-ignore file is needed to allow stow to symlink .gitignore
# https://github.com/aspiers/stow/issues/75#issuecomment-1719558252
if [[ ! -f git/.stow-local-ignore ]]; then
    touch git/.stow-local-ignore
fi

stow --restow --target=${HOME} ghostty git karabiner nvim R rstudio tmux zed zsh

# Generate starship config if missing
if command -v starship &>/dev/null && [[ ! -f ~/.config/starship.toml ]]; then
    starship preset pure-preset -o ~/.config/starship.toml
fi

# Install tmux plugin manager if missing
if [[ ! -d ~/.tmux/plugins/tpm ]]; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi
