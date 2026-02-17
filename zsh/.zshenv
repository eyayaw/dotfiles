# Settings
export EDITOR=nvim
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export BASH_SILENCE_DEPRECATION_WARNING=1
export HOMEBREW_NO_AUTO_UPDATE=
export TLDR_AUTO_UPDATE_DISABLED=
export HOMEBREW_USE_INTERNAL_API=

# Path definitions
export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

# Android Studio
export PATH="$PATH:$HOME/Library/Android/sdk/tools"
export PATH="$PATH:$HOME/Library/Android/sdk/platform-tools"
export PATH="$PATH:$HOME/Library/Android/sdk/emulator"
export ANDROID_EMULATOR_WAIT_TIME_BEFORE_KILL=5

export BAT_THEME="Solarized (dark)"
# bat can be used as a colorizing pager for man
export MANPAGER="sh -c 'col -bx | bat -l man -p'"

# Load secure environment variables from .localrc
[[ -f ~/.localrc ]] && source ~/.localrc

# LM Studio CLI (lms)
export PATH="$PATH:$HOME/.lmstudio/bin"
