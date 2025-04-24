#!/usr/bin/env zsh

# Install fonts ----
if [[ ${USER:l} = "eyayaw" ]]; then
    echo "Installing purchased fonts ..."
    purchases='/Users/eyayaw/Library/Mobile Documents/com~apple~CloudDocs/Documents/Backups/purchases'
    monolisa="$purchases/MonoLisa/ttf"
    comic_code="$purchases/Comic-Code/Tabular Type Foundry/Comic Code/OTF"
    berekeley_mono="$purchases/Berkeley-Mono/otf"

    for font in "$berekeley_mono" "$monolisa" "$comic_code"; do
        if [[ -d "$font" ]]; then
            echo "Installing fonts from $font"
            cp "$font"/(*.otf|*.ttf) ~/Library/Fonts/
        else
            echo "The dir of $font does not exist. Skipping."
        fi
    done
    echo "Successfully installed purchased fonts"
else
    echo "No purchased fonts to install for ${USER:l}"
fi

brew install --cask font-{jetbrains,ibm-plex}-mono font-monaspace
brew install --cask font-{fontawesome,inter,open-sans,roboto}
