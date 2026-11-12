---
hide:
  - navigation
  - toc
---

<div style="display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 20px; margin-bottom: 30px;">
  <div style="flex: 1 1 auto; min-width: 250px; max-width: 600px;">
    <img src="assets/logos/logo-light.svg" class="only-light" alt="Project Logo" style="width: 100%;">
    <img src="assets/logos/logo-dark.svg" class="only-dark" alt="Project Logo" style="width: 100%;">
  </div>
  <div style="flex: 0 1 auto; text-align: center;">
    <p>Developed as part of the <a href="https://scenariocompass.org/">Scenario Compass Initiative</a>.</p>
    <img src="assets/logos/sci-light.svg" class="only-light" alt="SCI Logo" style="height: 50px;">
    <img src="assets/logos/sci-dark.svg" class="only-dark" alt="SCI Logo" style="height: 50px;">
  </div>
</div>

<h1 style="position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;">Scenario Evaluation Criteria</h1>

<div style="text-align: center;" markdown>
[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/IAMconsortium/scenario-evaluation-criteria/blob/main/LICENSE.md)
[![Documentation Status](https://img.shields.io/badge/docs-online-blue)](https://scenario-evaluation-criteria.iamconsortium.org/)
[![CI](https://github.com/IAMconsortium/scenario-evaluation-criteria/actions/workflows/ci.yml/badge.svg)](https://github.com/IAMconsortium/scenario-evaluation-criteria/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21771914.svg)](https://doi.org/10.5281/zenodo.21771914)
</div>

{{ readme_section('## A set of community criteria for evaluating integrated assessment emissions scenarios') }}

---

## Versions

The documentation is published separately for each version of the criteria.

```python exec="true" session="versions" showcode="false"
from pathlib import Path

import yaml

versions = yaml.safe_load(Path("landing/versions.yaml").read_text())

links = [
    ("Summary", ":octicons-info-24:", ""),
    ("Components", ":octicons-three-bars-24:", "components/"),
    ("Tutorials", ":octicons-code-24:", "tutorials/"),
]

rows = [
    "| Version | Public review | Source | Zenodo | Note |",
    "|---------|---------------|--------|--------|------|",
]
for v in versions:
    nav = "<br>".join(
        f"[{icon} {label}]({v['path']}/{suffix})" for label, icon, suffix in links
    )
    source = f"[{v['source']['label']}]({v['source']['url']})"
    zenodo = v["zenodo"]
    zenodo = f"[{zenodo}](https://doi.org/{zenodo})" if zenodo else "—"
    rows.append(
        f"| {v['name']}<br>{nav} | {v['review']} | {source} | {zenodo} | {v['note']} |"
    )

print('<div markdown="1" style="text-align: center; font-size: 1.2em;">\n')
print("\n".join(rows))
print("\n</div>")
```

---

{{ readme_section('## How the criteria are developed') }}

---

{{ readme_section('## Two types of criteria').replace(
    "![SCI scenario evaluation criteria and their implications for the community benchmarks](landing/docs/figures/benchmarks.svg)\n\n*",
    "<figure markdown>\n  ![SCI scenario evaluation criteria and their implications for the community benchmarks](figures/benchmarks.svg){ style=\"width: 100%; max-width: 900px;\" }\n  <figcaption>",
).replace("(Riahi et al., submitted).*\n", "(Riahi et al., submitted).</figcaption>\n</figure>\n") }}

---

## Citation

Please cite as:

```python exec="true" session="index" showcode="false"
from pathlib import Path

import yaml

cff = yaml.safe_load(Path("CITATION.cff").read_text())


def _format_author(author):
    given = author.get("given-names", "").split()
    initials = " ".join(f"{part[0]}." for part in given if part)
    family = author.get("family-names", "")
    return f"{family}, {initials}".strip().rstrip(",")


authors = [_format_author(a) for a in cff["authors"]]
if len(authors) > 1:
    author_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
else:
    author_str = authors[0]

year = str(cff["date-released"]).split("-")[0]
title = cff["title"]
version = cff["version"]
# Overridden on this branch: no DOI is minted for unreleased work, so link
# to the branch itself instead (restore the CITATION.cff-derived DOI link
# once this lands on main and gets a release).
url = "https://github.com/IAMconsortium/scenario-evaluation-criteria/tree/2026-update"

print(
    f"> {author_str} ({year}). *{title}* "
    f"(Version {version}) [Computer software]. {url}"
)
```

---

## License

All data and code are published under the [MIT licence](https://github.com/IAMconsortium/scenario-evaluation-criteria/blob/main/LICENSE.md).

---

{{ readme_section('## Acknowledgments') }}

<p align="center">
  <img src="assets/logos/sci-light.svg" class="only-light" alt="SCI Logo" style="height: 50px; margin-bottom: 20px;">
  <img src="assets/logos/sci-dark.svg" class="only-dark" alt="SCI Logo" style="height: 50px; margin-bottom: 20px;">
  <img src="assets/logos/prisma-light.png" class="only-light" alt="PRISMA Logo" style="height: 50px; margin-bottom: 20px;">
  <img src="assets/logos/prisma-dark.png" class="only-dark" alt="PRISMA Logo" style="height: 50px; margin-bottom: 20px;">
</p>
