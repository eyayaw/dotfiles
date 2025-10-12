local wezterm = require 'wezterm'
function scheme_for_appearance(appearance)
  if appearance:find 'Dark' then
    return 'Batman' -- 'Default'
  else
    return 'MaterialDark'
  end
end

return {
  -- font = wezterm.font 'JetBrains Mono',
  font = wezterm.font_with_fallback{
	"MonoLisa",
	"Berkeley Mono",
	"Maple Mono",
    "JetBrains Mono",
  },
  --  color_scheme = 'Solarized Dark',
  color_scheme = scheme_for_appearance(wezterm.gui.get_appearance()),
  font_size = 18.0,
  -- Enable the scrollbar.
  enable_scroll_bar = true,
  adjust_window_size_when_changing_font_size = true,
  enable_tab_bar = true,
  hide_tab_bar_if_only_one_tab = true,
  -- window_decorations = "NONE",
  -- padding
  window_padding = {
    left = 0,
    right = 0,
    top = 0,
    bottom = 0,
  },
  -- window size
 initial_cols = 80,
 initial_rows = 30,

 -- Reset both the font size and the terminal dimensions for the current window
 -- to the values specified by your font, initial_rows, and initial_cols configuration.
  keys = {
    {
      key = '0',
      mods = 'CTRL',
      action = wezterm.action.ResetFontAndWindowSize,
      -- action = wezterm.action.ResetFontSize,
    },
  },
}
