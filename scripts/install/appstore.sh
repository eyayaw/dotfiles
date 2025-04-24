#!/usr/bin/env sh

set -e

if ! command -v mas &> /dev/null; then
    echo "mas is not installed. Please install it first."
    exit 1
fi

mas install 441258766 # Magnet
mas install 424389933 # Final Cut Pro
mas install 424390742 # Compressor
mas install 1554235898 # Peek - A quick look extension
mas install 1091189122 # Bear Notes
mas install 1569813296 # 1Password for Safari
mas install 771076721 # Hotspot Shield
