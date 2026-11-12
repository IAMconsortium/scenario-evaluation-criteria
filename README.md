<p align="center">
  <picture>
    <source
        media="(prefers-color-scheme: dark)"
        srcset="docs/assets/logos/logo-dark.svg"
    >
    <source
        media="(prefers-color-scheme: light)"
        srcset="docs/assets/logos/logo-light.svg"
    >
    <img
        src="docs/assets/logos/logo-light.svg"
        alt="SCI Logo"
        height="100"
    >
  </picture>
</p>


# Scenario Evaluation Criteria

Evaluation criteria for scenarios produced by Integrated Assessment
Models (IAMs), energy system models and similar tools.

[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Documentation Status](https://img.shields.io/badge/docs-online-blue)](https://scenario-evaluation-criteria.iamconsortium.org/)
[![CI](https://github.com/IAMconsortium/scenario-evaluation-criteria/actions/workflows/ci.yml/badge.svg)](https://github.com/IAMconsortium/scenario-evaluation-criteria/actions/workflows/ci.yml)

---

## A set of community criteria for evaluating integrated assessment emissions scenarios

Integrated Assessment Models (IAMs) are computational models that produce scenarios of economy, energy system, land use, and greenhouse-gas emissions developments over time, across regions, and under different policy assumptions. Those scenarios are often evaluated in the process of producing new scenarios or when collecting and assessing existing scenarios. Specifically, IAM scenarios are often checked against empirical observations, near-term projections, and sustainability targets to identify scenarios that are outdated, internally inconsistent, technically infeasible, or ecologically or socially undesirable.

This website documents the criteria used to evaluate scenarios in the [Scenario Compass Initiative (SCI)](https://scenariocompass.org/). The criteria are developed to curate a high-quality scenario ensemble suitable for a wide range of scenario users. Following a transparent, community-driven process, the scenario evaluation criteria are reviewed every year and published in a versioned, machine-readable format. In addition, this website details the chosen thresholds, reference data, and justification for each criterion.

---

## How the criteria are developed

The criteria are developed by the SCI in collaboration with the IAMC Scientific Working Groups on Scenarios and on Data, following the subsequent steps:

1. __Proposal.__ SCI working groups derive criteria and thresholds from peer-reviewed literature and official data sources.
2. __Open review.__ Draft criteria are published on this site for public review. The call is advertised online, through community mailing lists, and through professional networks.
3. __Response and revision.__ Responses to reviewer comments are made public. In the first public review, reviewers received direct responses to their comments and the resulting changes to the criteria via email.
4. __Release.__ The revised criteria are released as a new version and applied in the annual update of the Scenario Compass ensemble.

In general, criteria are required to refer to variables that are critical for the global energy transition, reported consistently across scenarios in the database, and that can be linked to quantifiable thresholds derived from scientific literature or official data sources.

---

## Two types of criteria

There are two types of evaluation criteria: historical vetting as well as feasibility and sustainability concerns.

- __Historical vetting.__ Scenarios are evaluated for correctly representing the current energy system. They are marked as inconsistent if they do not match reported historical real-world estimates for time periods in the past.
- __Feasibility and sustainability concerns.__ The feasibility evaluation concentrates on whether the near-term pace of technology deployment assumed in scenarios stays within empirically grounded bounds. An upper bound checks whether deployment is faster than existing capacity, project pipelines, lead times, and market dynamics can support. A lower bound, near-term plausibility, checks whether deployment falls implausibly low given capacity already operating or committed. The sustainability evaluation focuses on whether scenarios stay within resource and environmental limits, such as levels of bioenergy use, food availability, and cumulative geological CO₂ storage.

![SCI scenario evaluation criteria and their implications for the community benchmarks](landing/docs/figures/benchmarks.svg)

*SCI's scenario evaluation criteria and their implications for the community benchmarks reported in "Mitigation benchmarks from the 2025 community update of global emissions pathways" (Riahi et al., submitted).*

The criteria are applied on the SCI scenario database to derive a high-quality scenario ensemble recommended to use, amongst others for community benchmarks (see Riahi et al., submitted for the first edition of the community benchmarks). Please note that no scenario is removed from the database: all scenarios are recorded and remain available to users. Evaluation criteria are only used to identify a recommended scenario ensemble for benchmarking and other uses of scenario information.

Failing or insufficiently reporting variables required for historical vetting leads to a scenario not being represented in the benchmarking scenario ensemble. When a feasibility or sustainability threshold is crossed, the scenario is flagged with a medium or high concern. A medium concern marks the point where problems may begin to emerge. Medium concerns do not affect whether a scenario is included in the scenario ensemble. A high concern means a value is either inconsistent even with the most optimistic reading of current evidence, or that a scenario raises serious sustainability concerns, leading to the scenario not being considered for the benchmark-relevant ensemble.

---

## Repository structure

The core data lives in `inst/extdata/`:

```
inst/extdata/
├── criteria-types.yaml          # Definitions of criterion types
├── sources.bib                  # Bibliographic references
├── criteria/
│   ├── [criteria type]/         # Label of a criteria type
│   │   ├── thresholds.csv       # Threshold values (variable, region, year, bounds)
│   │   └── descriptions.yaml    # Justifications for criteria and thresholds
│   └── […]                      # More criteria types
└── reference-data/
    └── *.csv                    # External datasets used as threshold references
```

---

## Citation

If you use this package in your research, please cite it using the metadata in
[`CITATION.cff`](CITATION.cff).

---

## License

All data and code are published under the [MIT licence](LICENSE.md).

---

## Acknowledgments
This collection of scenario evaluation criteria was curated as part of the 
[Scenario Compass Initiative (SCI)](https://scenariocompass.org). Some of 
the reference data was previously derived in the 
[PRISMA](https://www.net0prisma.eu/) project.

SCI is supported financially by the Bezos Earth Fund. PRISMA has received 
funding from the European Union’s Horizon Europe research and innovation 
programme under grant agreement No. 101081604 (PRISMA).

<p align="center">
  <picture>
    <source
        media="(prefers-color-scheme: dark)"
        srcset="docs/assets/logos/sci-dark.svg"
    >
    <source
        media="(prefers-color-scheme: light)"
        srcset="docs/assets/logos/sci-light.svg"
    >
    <img
        src="docs/assets/logos/sci-light.svg"
        alt="SCI Logo"
        height="50"
    >
  </picture>
  <picture>
    <source
        media="(prefers-color-scheme: dark)"
        srcset="docs/assets/logos/prisma-dark.png"
    >
    <source
        media="(prefers-color-scheme: light)"
        srcset="docs/assets/logos/prisma-light.png"
    >
    <img
        src="docs/assets/logos/prisma-light.png"
        alt="PRISMA Logo"
        height="50"
    >
  </picture>
</p>
