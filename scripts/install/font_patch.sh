#!/bin/sh

# Path MonoLisa
if ! command -v fontforge > /dev/null 2>&1; then
    brew install fontforge
fi

git clone --depth 1 https://github.com/daylinmorgan/monolisa-nerdfont-patch.git && cd monolisa-nerdfont-patch
./patch-monolisa -f ~/Documents/Backups/purchases/MonoLisa/ttf/ -c
# Copy the patched fonts the fonts directory
cp ./patched/*.ttf ~/Library/Fonts/
fc-cache -f -v
cd --

# Path Berekely Mono
cd ~/Documents/Backups/purchases/Berkeley-Mono/
docker run --rm \
        -v "$(pwd)/ttf:/in" \
        -v "$(pwd)/ttf/patched:/out" \
        nerdfonts/patcher \
        --complete \
        --mono \
        --adjust-line-height
cp ./ttf/patched/*.ttf ~/Library/Fonts/
