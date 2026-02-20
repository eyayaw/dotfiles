-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua

-- Theme sync: watch ~/.config/theme/current and apply colorscheme
local theme_map = {
  mocha = { "catppuccin-mocha", "dark" },
  frappe = { "catppuccin-frappe", "dark" },
  latte = { "catppuccin-latte", "light" },
  macchiato = { "catppuccin-macchiato", "dark" },
  moon = { "rose-pine-moon", "dark" },
  dawn = { "rose-pine-dawn", "light" },
  ["solarized-dark"] = { "solarized", "dark" },
  ["solarized-light"] = { "solarized", "light" },
  ["gruvbox-dark"] = { "gruvbox", "dark" },
  ["gruvbox-light"] = { "gruvbox", "light" },
}

local theme_file = vim.fn.expand("~/.config/theme/current")

local function apply_theme()
  local f = io.open(theme_file, "r")
  if not f then
    return
  end
  local name = f:read("*l")
  f:close()
  if not name then
    return
  end
  name = vim.trim(name)
  local entry = theme_map[name]
  if entry then
    vim.o.background = entry[2]
    local ok, err = pcall(vim.cmd.colorscheme, entry[1])
    if not ok then
      vim.notify("theme: " .. err, vim.log.levels.WARN)
    end
  end
end

-- Apply on startup
apply_theme()

-- Watch for file changes
local w = vim.uv.new_fs_event()
if w then
  local watched = vim.fn.expand("~/.config/theme")
  w:start(watched, {}, function(err)
    if not err then
      vim.schedule(apply_theme)
    end
  end)
end

-- Fallback: re-apply on FocusGained in case fs_event is unreliable
vim.api.nvim_create_autocmd("FocusGained", {
  callback = apply_theme,
})

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
