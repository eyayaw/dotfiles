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

```sh
1. Clone my dotfiles repository: `git clone --depth=1 https://github.com/eyayaw/dotfiles.git ~/Developer/dotfiles`
  > macOS comes with a pre-installed version of Git.
  > Review the repo and add/remove stuff.
2. Run the bootstrap script: `cd ~/Developer/dotfiles && ./bootstrap.sh`.
  > You may need to give a permission with `chmod +x bootstrap.sh`
3. Reboot, your mac should be ready for use.
```

## Stowing

Most of the subdirs (pkgs in gnu Stow lingo) are symlinked into the home dir (-t target).

```sh
cd ~/Developer/dotfiles
stow -t ~ git ghostty karabiner nvim R rstudio tmux zed zsh
```

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


## Credits

I've taken inspiration from the dotfiles of [Mathias Bynens](https://github.com/mathiasbynens/dotfiles), [Dreams of Autonomy](https://github.com/dreamsofautonomy/zensh/blob/main/.zshrc), and [holman](https://github.com/holman/dotfiles/tree/21342e9f4e7d55ebfdc6e4e9071f94cbbc9eb0ef).
