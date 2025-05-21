#!/usr/bin/env zsh

source scripts/util.sh

# List of installation scripts
files=(
"scripts/install/brew.sh"
"scripts/install/packages.sh"
"scripts/install/fonts.sh"
"scripts/install/tpm.sh"
"scripts/install/better_bibtex.sh"
"scripts/install/appstore.sh"
"scripts/install/uv_tools.sh"
)

echo "${GREEN}Starting installations ...${NC}"
for fname in "${files[@]}"; do
  if [[ -f $fname ]]; then
    echo "${YELLOW}Running $fname ...${NC}"
    source $fname
  else
    echo "${RED}File $fname does not exist. Skipping ...${NC}"
  fi
done

# Install favorite R packages
Rscript scripts/install/packages.R

unset files

echo "${GREEN}All installations completed!${NC}"
