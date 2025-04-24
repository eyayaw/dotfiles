#!/bin/bash

# Install tmux plugin manager
# https://github.com/tmux-plugins/tpm

# Adapted from: https://github.com/typecraft-dev/crucible/blob/main/install-tpm.sh

set -e

if ! command -v tmux &> /dev/null; then
  echo "tmux is not installed."
  exit 1
fi

TPM_DIR="$HOME/.tmux/plugins/tpm"

# Check if TPM is already installed
if [ -d "$TPM_DIR" ]; then
  echo "TPM is already installed in $TPM_DIR"
else
  echo "Installing Tmux Plugin Manager (TPM)..."
  git clone --depth=1 https://github.com/tmux-plugins/tpm $TPM_DIR
fi

echo "TPM installed successfully!"
echo "Now opening tmux session and installing plugins ..."

tmux new-session -d -s tpm_install_session

# I use C-a as my prefix for tmux. if you don't have that. change this line
hyper_prefix="C-a"
tmux send-keys -t tpm_install_session ${hyper_prefix} "I" C-m

tmux attach -t tpm_install_session

exit 0
