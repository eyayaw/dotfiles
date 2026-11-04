# My dotfiles

Setting up macOS with Homebrew, GNU Stowed dotfiles, and good default macOS settings. Read my blogpost about it [here](https://eyayaw.github.io/posts/setting-up-a-new-mac.html).

## Stack

* [Zsh](https://www.zsh.org/) - a shell
* [zinit](https://github.com/zdharma-continuum/zinit.git) - a lightweight plugin manager for Zsh
* [HomeBrew](https://brew.sh) - a package manager for macOS
* [GNU Stow](https://www.gnu.org/software/stow/) - a dotfiles manager
* [Karabiner](https://karabiner-elements.pqrs.org/) - a keyboard customizer for macOS
* [Mas](https://github.com/mas-cli/mas) - a Mac App Store command line interface

> Installs apps and tools such as Ghostty, Zed, VS Code, Zotero, tmux, programming typefaces, R, Python, DuckDB, etc.

## Usage

1. Clone my dotfiles repository: `git clone --depth=1 https://github.com/eyayaw/dotfiles.git ~/Developer/dotfiles`
  > macOS comes with a pre-installed version of Git.
  > Review the repo and add/remove stuff.
2. Run the bootstrap script: `cd ~/Developer/dotfiles && ./bootstrap.sh`.
  > You may need to give a permission with `chmod +x bootstrap.sh`
3. Reboot, your mac should be ready for use.


## Stowing

Most of the subdirs (pkgs in gnu Stow lingo) are symlinked into the home dir (-t target).

```sh
cd ~/Developer/dotfiles
stow -t ~ git ghostty karabiner nvim R rstudio tmux zed zsh tuna claude codex
```

`codex-system/config.toml` holds the hand-written Codex settings. Codex reads it from `/etc/codex`, outside the home dir, so link it by hand:

```sh
sudo mkdir -p /etc/codex
sudo ln -s ~/Developer/dotfiles/codex-system/config.toml /etc/codex/config.toml
```

Codex writes its own state to `~/.codex/config.toml`, which stays out of this repo.

The empty `.stow-local-ignore` file in `git/` is a [trick](https://github.com/aspiers/stow/issues/75#issuecomment-1719558252) to stow git/.gitignore.

<details>
<summary>Using Stow</summary>
For my own reference.

```sh
stow --target=$HOME --dir=$STOW_DIR <list of pkgs>
stow --target-$HOME --dir=$STOW_DIR --simulate <list of pkgs> # to see what will change
stow -t $HOME -d $STOW_DIR --adopt <pkg> # import from home dir (overwrites existing files)
```

For more, check `man stow`.
</details>


## Agent hooks and tools

Claude Code and Codex run the scripts in `agents/hooks/` as hooks, so the rules I care about are
enforced by a program. The `bin` package puts three of them on `PATH`. Both harnesses send the same
event JSON, so one script serves both.

| Hook | When | What it does |
|---|---|---|
| `mode.py` | session start, before and after each tool call | Reads the repo's `mode.toml`, tells the agent its role, and denies edits and shell writes to the paths only I edit. Refuses a commit with hooks turned off. |
| `commitgate.py` | each prompt, before each shell command | Denies the git commands that stage or commit until the turn's prompt asks for a commit, PR, or push. A question or a negated verb does not ask. |
| `wru.py` | each stop, resume, and compaction | Saves the opening of the agent's last message, the repo, and the Rex pane when there is one, and feeds it back after a resume or compaction. |
| `prose_review.py` | session start and stop | Lists docstring and comment lines added in the turn that break the prose rules in `AGENTS.md`. |
| `usuals-gate.sh` | before each shell command | Blocks `git commit` and `gh` posts until the `usuals` skill has checked the exact tree and message. |

The commands:

```sh
mode status        # this repo's mode and human-owned paths, and the one repo in learn mode
mode set learn     # switch; refused while another repo is in learn mode
wru                # every session's last state, newest first, with its Rex pane when it had one
relcheck           # in a package: the bump its commits imply, and what the release still needs
```

A sample `wru` line and a sample `relcheck` run:

```
 2m  claude  26ea05  profile/career   Five of the six network segments are done. Development and spatial...
release: major bump; 6 commits since v0.3.0: 3 docs, 1 build, 1 refactor, 1 fix
version: 0.3.0 in pyproject.toml still equals v0.3.0; bump to 0.4.0
changelog: Unreleased has 1 entries for 1 feat/fix commits
readme: covers the 0 public names added since v0.3.0
```

To put a repo under the mode system, copy `mode.toml` from the Python template in
`~/Developer/workflows/templates/python`, add its `mode precommit` entry to `prek.toml`, and create
`tests/acceptance/`. The design, with the evidence behind it, is in
`~/Developer/agentic-modes/Ship Mode Learn Mode v2.md`. Each script's docstring is its reference,
and `agents/hooks/test_*.py` shows every rule as a case.

## Credits

I've taken inspiration from the dotfiles of [Mathias Bynens](https://github.com/mathiasbynens/dotfiles), [Dreams of Autonomy](https://github.com/dreamsofautonomy/zensh/blob/main/.zshrc), and [holman](https://github.com/holman/dotfiles/tree/21342e9f4e7d55ebfdc6e4e9071f94cbbc9eb0ef).
