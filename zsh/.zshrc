# zinit plugin manager setup
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
[ ! -d $ZINIT_HOME ] && mkdir -p "$(dirname $ZINIT_HOME)"
[ ! -d $ZINIT_HOME/.git ] && git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
source "${ZINIT_HOME}/zinit.zsh"
# Plugins
zinit light zsh-users/zsh-syntax-highlighting
zinit light zsh-users/zsh-completions
zinit light zsh-users/zsh-autosuggestions
zinit light Aloxaf/fzf-tab


# Completion configuration
autoload -Uz compinit && compinit
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' menu no
_comp_options+=(globdots) # Include hidden files.
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls --color $realpath'
zstyle ':fzf-tab:complete:__zoxide_z:*' fzf-preview 'ls --color $realpath'
zstyle ':completion:*' insert-tab pending

# History configuration
HISTSIZE=1000000
SAVEHIST=$HISTSIZE
HISTFILE=~/.zsh_history
HISTDUP=erase
setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

# Keybindings
bindkey '^p' history-search-backward
bindkey '^n' history-search-forward
bindkey '^[w' kill-region

# Stolen from Luke Smith's dotfiles
# Edit line in vim with ctrl-e:
autoload edit-command-line; zle -N edit-command-line
bindkey '^e' edit-command-line
bindkey -M vicmd '^[[P' vi-delete-char
bindkey -M vicmd '^e' edit-command-line
bindkey -M visual '^[[P' vi-delete

# Shell integrations
# Homebrew -- pkg manager
eval "$(/opt/homebrew/bin/brew shellenv)"

# Starship -- Prompt
eval "$(starship init zsh)"

# fuzzy completion
source <(fzf --zsh)
# source <(sk --shell zsh)

# Zoxide -- better cd
eval "$(zoxide init zsh)"


## Load other zsh files
# Load aliases
[[ -f ~/.zsh_aliases ]] && source ~/.zsh_aliases
[[ -f ~/.zsh_theme ]] && source ~/.zsh_theme

# Fastfetch
FASTFETCH_ALLOWED=(ghostty apple_terminal wezterm kitty alacritty)
term_id=${TERM_PROGRAM:-${TERM}}

if (( ${FASTFETCH_ALLOWED[(Ie)${(L)term_id}]} )); then
    command -v fastfetch >/dev/null 2>&1 && fastfetch
fi


