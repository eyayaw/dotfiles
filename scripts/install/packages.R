#!/usr/bin/env Rscript

# Avoid reinstalling in the case of install.packages
install_pkg = function(pkg, installer = NULL, ...) {
  if (is.null(installer)) {
    installer = if (requireNamespace("pak", quietly = TRUE)) {
      pak::pkg_install
    } else {
      utils::install.packages
    }
  }

  if (requireNamespace(pkg, quietly = TRUE)) {
    print(sprintf("%s is already installed. Skipping ...", pkg))
  } else {
    installer(pkg, ...)
  }
}

# Favorite packages
packages = c(
  "bit64",
  "data.table",
  "ggplot2",
  "ragg",
  "marquee",
  "sf",
  "terra",
  "glue",
  "rmarkdown",
  "quarto",
  "litedown",
  "tinytable",
  "tinyplot",
  "haven",
  "rvest",
  "yyjsonr",
  "duckdb",
  "arrow",
  "nanoparquet",
  "languageserver",
  "lintr",
  "renv"
)

install_pkg("pak")
installer = pak::pkg_install

for (pkg in packages) {
  install_pkg(pkg, installer)
}

print("All packages have been installed.")
