-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua

-- Quiet diagnostics: signs only, <leader>cd for details
vim.api.nvim_create_autocmd("LspAttach", {
  once = true,
  callback = function()
    vim.diagnostic.config({
      virtual_text = false,
      underlines = false,
      float = { border = "rounded", source = true },
    })
  end,
})
