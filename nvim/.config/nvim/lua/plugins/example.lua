return {
  -- colorscheme
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    opts = {
      flavour = "auto",
      background = { light = "latte", dark = "mocha" },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = { colorscheme = "catppuccin" },
  },

  -- python: use ruff (linter/formatter) and ty (type checker/lsp)
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ruff = {},
        ty = {},
        pyright = { enabled = false },
      },
    },
  },

  -- disable noice entirely, use vanilla vim cmdline
  { "folke/noice.nvim", enabled = false },

  -- disable cmdline completion popup
  {
    "saghen/blink.cmp",
    opts = {
      cmdline = { enabled = false },
    },
  },

  -- tmux pane navigation with ctrl+h/j/k/l
  { "christoomey/vim-tmux-navigator", lazy = false },

  -- mason: ensure tools are installed
  {
    "mason-org/mason.nvim",
    opts = {
      ensure_installed = {
        "stylua",
        "shellcheck",
        "shfmt",
      },
    },
  },
}
