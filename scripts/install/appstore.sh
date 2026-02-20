#!/usr/bin/env sh

set -e

if ! command -v mas &> /dev/null; then
    echo "mas is not installed. Please install it first. brew install mas"
    exit 1
fi

mas install 441258766 # Magnet
mas install 424389933 # Final Cut Pro
mas install 424390742 # Compressor
mas install 497799835 # Xcode
mas install 1554235898 # Peek - A quick look extension
mas install 1569813296 # 1Password for Safari
mas install 572281534 # Transloader
mas install 1136220934 # Infuse
