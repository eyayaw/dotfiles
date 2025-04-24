#!/usr/bin/env zsh
# Install HomeBrew and essential packages (gui apps and cli tools)

# Install HomeBrew ----
# (NONINTERACTIVE=1 for unattended installation (i.e. do not prompt for password)
# https://docs.brew.sh/Installation#unattended-installation

if test ! $(which brew)
then
  echo "Installing Homebrew ..."
NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi

# Latest Homebrew and upgrade already installed packages
brew update && brew upgrade
