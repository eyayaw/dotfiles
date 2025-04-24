options(
  prompt = "R> ",
  max.print = 100L,
  max = 10L,
  example.ask = TRUE,
  warnPartialMatchArgs = TRUE,
  warnPartialMatchAttr = TRUE
)


# repos ----
# options(install.packages.check.source = "no")
# Enable multiple universes
options(
  # error = recover,
  repos = c(
    rspm = "https://packagemanager.rstudio.com/all/latest",
    CRAN = "https://cran.r-project.org"
  )
)

# data.table options ----
options(
  datatable.print.colnames = "auto",
  datatable.print.class = TRUE,
  datatable.print.keys = TRUE,
  datatable.print.nrows = TRUE,
  datatable.print.trunc.cols = TRUE,
  datatable.print.rownames = TRUE,
  datatable.warnredundantby = TRUE,
  datatable.dfdispatchwarn = TRUE,
  datatable.optimize = TRUE,
  datatable.print.topn = TRUE
)

# customize the tidyverse style
my_style <- function(...) {
  transformers = styler::tidyverse_style(...)
  transformers$token$force_assignment_op = NULL
  transformers$space$before_assignment_operator = NULL
  transformers$token$add_brackets_in_pipe = NULL
  transformers
}

options(
  styler.addins_style_transformer = "my_style()",
  styler.quiet = TRUE,
  styler.cache_root = "styler"
)


local({
  # taken from https://github.com/tidyverse/modelr/blob/main/R/na-warn.R
  na.warn <- function(object) {
    missing = sum(!stats::complete.cases(object))
    if (missing > 0) {
      warning("Dropping ", missing, " rows with missing values", call. = FALSE)
    }
    stats::na.exclude(object)
  }

  options(na.action = na.warn)


  # vs-code r options ----
  options(languageserver.formatting_style = function(options) {
    trans = styler::tidyverse_style(strict = FALSE, indent_by = options$tabSize)
    trans$token$force_assignment_op = NULL
    trans
  })
  # Disable completion from the language server
  options(languageserver.server_capabilities =
    list(completionProvider = FALSE, completionItemResolve = FALSE))
})
