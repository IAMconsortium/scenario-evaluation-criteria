################################################################################
# Build kaist/iamc/IAMC_benchmark.csv: the historical reference values that
# kaist/kmip/step6_validation.R compares a report with.
#
# Metrics, years and tolerances come from the "Historical" table on page 6 of
# the IAMC SWG National Scenarios Study 2 call (the docx in this folder).
# Every value is taken from the first source that has it:
#   1. IAMC git: the reference data of IAMconsortium/scenario-evaluation-criteria
#   2. the source named in the document (UN WPP, World Bank, PRIMAP-hist, IEA)
# The <year>_datasource column names the source of each value. See README.md.
#
# Usage (repo root):  Rscript kaist/iamc/build_IAMC_benchmark.R
# Downloads are kept in the folder named by IAMC_CACHE (default: tempdir());
# PRIMAP-hist is 77 MB and Zenodo is slow, so set IAMC_CACHE to keep it.
################################################################################

suppressMessages({
  library(dplyr)
  library(tidyr)
})

########## Settings ##########
region_name <- "South Korea"   # Region name in the report
iso3        <- "KOR"
years       <- c(2005, 2010, 2015, 2020)
out_file    <- file.path(getwd(), "kaist/iamc/IAMC_benchmark.csv")

# List of IAMC template metrics, units and tolerances (from the document). The order is preserved.
metrics <- tribble(
  ~Metrics,                                        ~Unit,                 ~Threshold_pct, ~Threshold_strict_pct,
  "Population",                                    "million",             NA,             NA,   # Population
  "GDP|MER",                                       "billion USD_2010/yr", NA,             NA,   # GDP|MER
  "Emissions|CO2|Energy and Industrial Processes", "Mt CO2/yr",           30,             20,   # CO2 Emissions (fossil CO2)
  "Emissions|CO2|AFOLU",                           "Mt CO2/yr",           50,             NA,   # CO2 Emissions|Land
  "Emissions|CH4|AFOLU",                           "Mt CH4/yr",           50,             NA,   # CH4 Emissions|AFOLU
  "Primary Energy",                                "EJ/yr",               30,             20,
  "Primary Energy|Coal",                           "EJ/yr",               30,             20,
  "Primary Energy|Oil",                            "EJ/yr",               30,             20,
  "Primary Energy|Gas",                            "EJ/yr",               30,             20,
  "Secondary Energy|Electricity",                  "EJ/yr",               30,             20)

# Data sources (URLs) for the IAMC git and the sources named in the document. The IAMC git
iamc_git_ref <- "2ba4b8091d5d7eb3689cf148e93d89dcc6d8574a"
iamc_git_url <- paste0("https://raw.githubusercontent.com/IAMconsortium/scenario-evaluation-criteria/",
                       iamc_git_ref, "/inst/extdata/reference-data/")
wpp_url    <- paste0("https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/",
                     "CSV_FILES/WPP2024_TotalPopulationBySex.csv.gz")
primap_url <- paste0("https://zenodo.org/api/records/22876287/files/",
                     "Guetschow_et_al_2026-PRIMAP-hist_v2.8_final_22-Sep-2026.csv/content")
wb_url     <- "https://api.worldbank.org/v2/country/%s/indicator/%s?format=json&date=2005:2020&per_page=100"
iea_url    <- "https://api.iea.org/stats/indicator/%s?countries=%s"
##############################

########## Download helper ##########
cache_dir <- Sys.getenv("IAMC_CACHE", file.path(tempdir(), "iamc_benchmark"))
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
options(timeout = 3600)
# Download url once into the cache (three tries) and return the local path.
fetch <- function(url, name) {
  f <- file.path(cache_dir, name)
  for (i in 1:3) {
    if (file.exists(f) && file.size(f) > 0) return(f)
    cat("  download", name, "\n")
    try(download.file(url, f, mode = "wb", quiet = TRUE), silent = TRUE)
  }
  stop("download failed: ", url)
}
one <- function(metric, year, value, datasource)
  data.frame(Metrics = metric, Year = year, value = value, datasource = datasource, stringsAsFactors = FALSE)
#####################################

########## 1. IAMC git ##########
iamc_git <- function(dataset, variable, metric = variable) {
  d <- read.csv(fetch(paste0(iamc_git_url, dataset, ".csv"), paste0("iamc_", dataset, ".csv")),
                comment.char = "#", stringsAsFactors = FALSE)
  d <- d[d$region == iso3 & d$variable == variable & d$year %in% years, ]
  one(metric, d$year, d$value, paste0("IAMC git: ", dataset))
}
from_iamc_git <- bind_rows(
  iamc_git("EI-2023", "Primary Energy|Coal"),
  iamc_git("EI-2023", "Primary Energy|Oil"),
  iamc_git("EI-2023", "Primary Energy|Gas"),
  # PRIMAP-hist v2.7 in the IAMC git: land CO2 only as HISTTP (third-party priority);
  # agricultural CH4 as HISTCR (country-reported priority) and HISTTP, HISTCR is used.
  iamc_git("PRIMAP-2025-v2p7-HISTTP", "Emissions|CO2|AFOLU"),
  iamc_git("PRIMAP-2025-v2p7-HISTCR", "Emissions|CH4|AFOLU|Agriculture", "Emissions|CH4|AFOLU"))
#################################

########## 2. Sources named in the document ##########
# Population: UN World Population Prospects 2024, total population on 1 July (thousand).
wpp <- readr::read_csv(fetch(wpp_url, "WPP2024_TotalPopulationBySex.csv.gz"), show_col_types = FALSE,
                       col_select = c("ISO3_code", "Variant", "Time", "PopTotal")) %>%
  filter(ISO3_code == iso3, Variant == "Medium", Time %in% years)
from_un <- one("Population", wpp$Time, wpp$PopTotal / 1000, "File: UN WPP 2024")

# GDP|MER: World Bank constant-price GDP (2015 USD), put on the 2010 price level
# with the 2010 current-USD value: GDP_2010USD(t) = KD(t) * CD(2010) / KD(2010).
wb <- function(indicator) {
  d <- jsonlite::fromJSON(fetch(sprintf(wb_url, iso3, indicator), paste0("wb_", iso3, "_", indicator, ".json")))[[2]]
  setNames(d$value, d$date)
}
kd <- wb("NY.GDP.MKTP.KD")
cd <- wb("NY.GDP.MKTP.CD")
from_wb <- one("GDP|MER", years, kd[as.character(years)] * cd[["2010"]] / kd[["2010"]] / 1e9,
               "API: World Bank NY.GDP.MKTP.KD (2010 USD)")

# PRIMAP-hist v2.8 (2026), HISTCR, Gg -> Mt. Fossil CO2 = energy (1) + industrial
# processes (2). The dataset has no LULUCF category, so land CO2 has no 2005 value.
pm <- readr::read_csv(fetch(primap_url, "PRIMAP-hist_v2.8_final.csv"), show_col_types = FALSE,
                      col_select = c(scenario = "scenario (PRIMAP-hist)", area = "area (ISO3)", entity = "entity",
                                     category = "category (IPCC2006_PRIMAP)", all_of(as.character(years)))) %>%
  filter(area == iso3, scenario == "HISTCR") %>%
  pivot_longer(all_of(as.character(years)), names_to = "Year", values_to = "value") %>%
  mutate(Year = as.integer(Year), value = value / 1000)
primap <- function(metric, gas, categories) {
  d <- pm %>% filter(entity == gas, category %in% categories) %>%
    group_by(Year) %>% summarise(value = sum(value), n = n(), .groups = "drop")
  if (any(d$n != length(categories))) stop("PRIMAP: category missing for ", metric)
  one(metric, d$Year, d$value, "File: PRIMAP-hist v2.8 HISTCR")
}
from_primap <- bind_rows(
  primap("Emissions|CO2|Energy and Industrial Processes", "CO2", c("1", "2")),
  primap("Emissions|CH4|AFOLU", "CH4", "M.AG"))

# IEA energy statistics (free API of the IEA data browser): total energy supply
# by source (TJ) and electricity generation by source (GWh), in EJ.
iea <- function(indicator) {
  d <- jsonlite::fromJSON(fetch(sprintf(iea_url, indicator, iso3), paste0("iea_", iso3, "_", indicator, ".json")))
  d %>% mutate(Year = as.integer(year)) %>% filter(Year %in% years)
}
iea_sum <- function(d, metric, factor, label) {
  s <- d %>% group_by(Year) %>% summarise(value = sum(value) * factor, .groups = "drop")
  one(metric, s$Year, s$value, label)
}
tes  <- iea("TESbySource")       # products: COAL, MTOTOIL, NATGAS, NUCLEAR, HYDRO, GEOTHERM, COMRENEW
elec <- iea("ElecGenByFuel")
stopifnot(all(tes$units == "TJ"), all(elec$units == "GWh"))
from_iea <- bind_rows(
  iea_sum(tes, "Primary Energy", 1e-6, "API: IEA TESbySource"),
  iea_sum(tes %>% filter(product == "COAL"),    "Primary Energy|Coal", 1e-6, "API: IEA TESbySource"),
  iea_sum(tes %>% filter(product == "MTOTOIL"), "Primary Energy|Oil",  1e-6, "API: IEA TESbySource"),
  iea_sum(tes %>% filter(product == "NATGAS"),  "Primary Energy|Gas",  1e-6, "API: IEA TESbySource"),
  iea_sum(elec, "Secondary Energy|Electricity", 3.6e-6, "API: IEA ElecGenByFuel"))
######################################################

########## 3. First source per metric and year, wide table ##########
candidates <- bind_rows(from_iamc_git, from_un, from_wb, from_primap, from_iea) %>%   # priority order
  filter(!is.na(value))
picked <- candidates %>% group_by(Metrics, Year) %>% slice(1) %>% ungroup()

grid <- crossing(Metrics = metrics$Metrics, Year = years) %>%
  left_join(picked, by = c("Metrics", "Year")) %>%
  mutate(value = signif(value, 6),
         datasource = ifelse(is.na(value), "not available", datasource))
wide <- function(col, suffix) grid %>% select(Metrics, Year, all_of(col)) %>%
  pivot_wider(names_from = Year, values_from = all_of(col), names_glue = paste0("{Year}", suffix))

benchmark <- metrics %>% mutate(Region = region_name) %>%
  left_join(wide("value", ""), by = "Metrics") %>%
  left_join(wide("datasource", "_datasource"), by = "Metrics") %>%
  select(Metrics, Region, Unit, all_of(as.character(years)), all_of(paste0(years, "_datasource")),
         Threshold_pct, Threshold_strict_pct)

write.csv(benchmark, out_file, row.names = FALSE, na = "")
print(as.data.frame(benchmark %>% select(Metrics, all_of(as.character(years)))), row.names = FALSE)
cat("\nWritten:", out_file, "\n")
#####################################################################
