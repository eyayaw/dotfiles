#!/usr/bin/env zsh
# Set Zed as the default app for common file types
# Requires: https://github.com/scriptingosx/utiluti

if ! command -v utiluti &>/dev/null; then
  echo "utiluti not found. Install from https://github.com/scriptingosx/utiluti"
  return 1
fi

zed_bundle_id=$(defaults read /Applications/Zed.app/Contents/Info CFBundleIdentifier 2>/dev/null)
zed_bundle_id=${zed_bundle_id:-dev.zed.Zed}

extensions=(r py js css md qmd rmd tex lua toml sh zsh txt log json)

for ext in "${extensions[@]}"; do
  uti=$(utiluti get-uti "$ext")
  if [[ -z "$uti" ]]; then
    temp_file=$(mktemp "/tmp/tempfile.XXXXXX.$ext")
    uti=$(utiluti file get-uti "$temp_file")
    unlink "$temp_file"
  fi
  [[ -n "$uti" ]] && utiluti type set "$uti" "$zed_bundle_id"
done
