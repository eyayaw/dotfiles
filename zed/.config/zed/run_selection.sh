#!/bin/zsh

# Abs path of the current file
current_file="$ZED_FILE"
filename=$(basename "$current_file")

ext=$(echo "${filename##*.}" | tr '[:upper:]' '[:lower:]')

echo -e "[Running selected lines from $filename] ...\n"

if [[ "$ext" == "py" ]]; then
    source ~/.config/zed/robust_python.sh -c "$ZED_SELECTED_TEXT"
elif [[ "$ext" == "r" ]]; then
    Rscript --vanilla -e "$ZED_SELECTED_TEXT"
else
    echo "Failed to run selected lines from $current_file."
fi
