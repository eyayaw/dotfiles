#!/usr/bin/env zsh

### -----------------------------------------------------------------###
# Homebrew packages and some other packages installation script
#
# aliases
alias bic="brew install --cask"
alias bi="brew install"
alias bic_trusted="brew install --cask --no-quarantine"
# NB: This installs the package without applying the macOS quarantine attribute,
# bypassing the initial security warning. Use cautiously and ensure the
# software source is trusted.
### -----------------------------------------------------------------###


# Critical ----
## Apps
# I trust these packages
bic_trusted 1password
bic_trusted raycast alfred
bic_trusted arc # zen-browser
bic_trusted karabiner-elements
bic_trusted ghostty

## Cli tools
bi git # Not to interfere with the pre-installed version
bi git-lfs # Git Large File Storage
bi gh # GitHub CLI
bi tldr # see simple help pages for packages
bi starship # Prompt for shell
bi tmux # terminal multiplexer
bi stow # GNU Stow for symlink management
bi bat # better cat
bi ripgrep # better grep
bi fzf # fuzzy finder
bi fd # better find
bi tree # tree-like directory listing
bi 1password-cli
bi act # run github actions locally
bi mas # Mac App Store CLI


# Productivity/Utilities ----
bic istat-menus # System monitoring
bic bartender # Hide menu bar items
bic cleanmymac # System cleaning and optimization
bic pastebot # Clipboard manager (raycast and alfred have this feature)
bic cleanshot # Screenshot/recording tool
bic shottr # Alternative for cleanshot
bic alt-tab # cmd + tab alternative
bic keycastr # Keystroke visualizer
bi leader-key # Faster launcher

# Development ----
bic_trusted visual-studio-code{,@insiders}
bic_trusted zed{,@preview}
bic_trusted rstudio positron # R & Python IDE by Posit
bi neovim
bic docker # Container management


# Programming ----
bi python # pip is part of it
bic r # the cask version is recommended
bi lua

## Pkg managers, kernels
bi uv
bi ark # r kernel
brew tap r-lib/rig
bic rig # install multiple R versions

### Linters and formatters
bi ruff # python linter
#bi air # r formatter
curl -LsSf https://github.com/posit-dev/air/releases/latest/download/air-installer.sh | sh

# Literate programming ----
bi pandoc # Document converter
bi typst # better latex
bi quarto
bi latex
bi glow # Markdown viewer


## Databases ----
bi postgresql
bi duckdb

## GIS ----
# GIS libraries
bi proj
bi gdal
bi geos
bi udunits
bic qgis

## Web and API ----
# API tools
bic bruno insomnia

# API Hacking
bic burp-suite
bic mitmproxy

# For android virtual devices
bic android-studio # installs emulator adb fastboot
# decompile android apps
bi apktool jadx


# Security ----
bic adguard{,-vpn} # Adblocker + VPN
bic {little,micro}-snitch # Network & device monitor
bic mullvadvpn # VPN


# Cloud storage ----
bic google-drive
bic macfuse # for pcloud-drive for mounting the cloud storage as a virtual drive
bic cryptomator # Encrypt files and folders


# Misc ----
bic bearnotes # Note taking
bic pdfexpert # PDF reader
bic zotero # Reference manager
bic raindropio # Bookmark manager
bic the-unarchiver # faster than archive utility for unzipping
bic zen-browser # arc alternative (firefox-based)


# Social & Communication ----
bic whatsapp signal telegram
bic zoom microsoft-teams


# AI tools ----
bic windsurf # vibe coding
bic ollama # Local LLMs
bic lm-studio # Local LLMs
bic claude # Anthropic
bic chatgpt # OpenAI
bi aider codex claude-code # AI pair programming in your terminal
bic superwhisper # voice2text


# cleanup
unalias bi
unalias bic
unalias bic_trusted
