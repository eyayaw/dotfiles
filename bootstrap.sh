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

stow --target=${HOME} ghostty git karabiner nvim R rstudio tmux zed zsh

git config --global core.excludesfile ~/.gitignore
