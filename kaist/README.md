# IAMC benchmark for the historical validation (step 6)

The IAMC SWG National Scenarios Study 2 call (`IAMC SWG National Study 2_D4_10102026 (1).docx`, table "Historical" on page 6) lists ten historical metrics that a national submission should reproduce within a tolerance. This folder holds the reference values for South Korea; `kaist/kmip/step6_validation.R` compares a report with them.

| File | Content |
|------|---------|
| `IAMC_benchmark.csv` | One row per metric: `Metrics` (the IAMC variable in the report), `Region`, `Unit`, the values for 2005, 2010, 2015, 2020, the source of each value (`<year>_datasource`) and the tolerance (`Threshold_pct`, `Threshold_strict_pct`) |
| `{run_name}_validation.csv`, `.xlsx` | Copy of the step6 result of a run (same table as the sheet `validation` in the run's gcamreport workbook). Result files, ignored by git |
| `build_IAMC_benchmark.R` | Builds the csv from the sources below: `Rscript kaist/iamc/build_IAMC_benchmark.R` from the repo root (set `IAMC_CACHE` to a folder to keep the downloads; PRIMAP-hist is 77 MB) |

## Where the values come from

Each value is taken from the first source that has it: (1) the IAMC git, i.e. the reference data of [IAMconsortium/scenario-evaluation-criteria](https://github.com/IAMconsortium/scenario-evaluation-criteria) (commit `2ba4b80`, 2026-11-13), then (2) the source named in the document.

| Metric in the document | `Metrics` | Source by year | Tolerance |
|---|---|---|---|
| Population | `Population` | UN World Population Prospects 2024 (file) | none given |
| GDP\|MER | `GDP\|MER` | World Bank API, `NY.GDP.MKTP.KD` put on 2010 prices | none given |
| CO2 emissions (fossil CO2) | `Emissions\|CO2\|Energy and Industrial Processes` | PRIMAP-hist v2.8 (2026), HISTCR, categories 1 + 2 | ± 20/30 % |
| CO2 emissions, land | `Emissions\|CO2\|AFOLU` | 2010-2020: IAMC git (PRIMAP-hist v2.7, HISTTP). 2005: not available | ± 50 % |
| CH4 emissions, AFOLU | `Emissions\|CH4\|AFOLU` | 2010-2020: IAMC git (PRIMAP-hist v2.7, HISTCR, agriculture). 2005: PRIMAP-hist v2.8, HISTCR, category M.AG | ± 50 % |
| Primary Energy | `Primary Energy` | IEA API, total energy supply | ± 20/30 % |
| Primary Energy, coal / oil / gas | `Primary Energy\|Coal`, `\|Oil`, `\|Gas` | 2010-2020: IAMC git (Energy Institute 2023). 2005: IEA API | ± 20/30 % |
| Secondary Energy Electricity | `Secondary Energy\|Electricity` | IEA API, electricity generation | ± 20/30 % |

Things to know when reading a result:

- The IAMC git covers South Korea only for coal, oil, gas, land CO2 and agricultural CH4, and only from 2010. Everything else comes from the document sources, so a metric can mix two sources (coal, oil and gas: IEA for 2005, Energy Institute after). For oil the Energy Institute values are 15 to 19 % above the IEA ones.
- PRIMAP-hist has two variants: HISTCR (country-reported data first) and HISTTP (third-party data first). HISTCR is used where both exist. Land CO2 is in the IAMC git as HISTTP only, and PRIMAP-hist itself has no LULUCF category, so 2005 stays empty and is not checked. For agricultural CH4 the two variants differ by a factor of 1.8 for Korea (0.69 against 0.39 Mt CH4 in 2010).
- The CH4 benchmark is agriculture only; the report variable also holds land CH4, which is negligible for Korea.
- IEA total energy supply counts nuclear as heat and leaves out international bunkers; GCAM counts nuclear as electricity and keeps bunker fuel in oil. The total is therefore not exactly the same quantity.
- The document also names IMF (GDP) and Ember (energy). IMF is not used: its API refused the request. Ember is not used either: its electricity generation is within 2.5 % of the IEA values, and IEA comes first in the document.
- "± 20/30 %" is read as: pass within 30 %, with a note in the validation sheet when the value is outside 20 %. Population and GDP have no tolerance in the document; step6 uses 20 % (`validation_default_threshold_pct` in the settings file).

To change a value or a tolerance, edit the csv by hand and name the source in its `<year>_datasource` cell; a later rebuild overwrites the file.
