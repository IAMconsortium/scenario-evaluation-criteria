"""Shared helpers for dynamically generating the mkdocs "Summary" section.

Used by both ``gen_summary_pages.py`` (an mkdocs-gen-files script that
writes the page content) and ``mkdocs_nav.py`` (an mkdocs hook that builds
the matching sidebar nav), so that criteria only ever need to be
added/removed in the data — never as ``docs/summary/*.md`` files or
``mkdocs.yml`` nav entries.

Lives here rather than in the ``scenario_evaluation_criteria`` package
because none of this (HTML tables, mkdocs nav/page conventions, tab
widgets, ...) is needed outside of building the docs.
"""

import re
from functools import cache

import pandas as pd
from itables import to_html_datatable
from sigfig import round as sf_round

from scenario_evaluation_criteria import _deformat_prefix, load_criteria
from scenario_evaluation_criteria.formatting import format_sources, insert_citations
from scenario_evaluation_criteria.preprocessed import (
    load_criteria_combined,
    region_mapping_from_definition,
)

# Region groupings for the regionalised tables, sourced from
# IAMConsortium/common-definitions via region-definitions/nomenclature.yaml
# (see that file for why this isn't a regular package dependency).
REGION_DEFINITIONS = "region-definitions/definitions"

# One native-region version per model, chosen explicitly (rather than
# picked automatically) as the latest version of each model, excluding
# regionalised model variants (e.g. GCAM-Europe, GCAM-KSA, WITCH...EU28,
# POLES ENGAGE) and, for combined models, the combination only (e.g.
# REMIND-MAgPIE rather than its standalone REMIND predecessor). Judged
# from the file/hierarchy names under common-definitions'
# definitions/region/native_regions/ at the pinned commit (see
# region-definitions/nomenclature.yaml); bump when that pin is updated.
MODEL_HIERARCHIES = [
    "AIM 3.0",
    "C3IAM 3.0",
    "CGEM-ESM 1.0",
    "COFFEE 1.6",
    "GCAM 9.1",
    "GEM-E3 V2026",
    "IMACLIM 2.0",
    "IMAGE 3.4",
    "MEESA v1.4",
    "MESSAGEix-GLOBIOM 2.1-R12",
    "MINES 0.1.0",
    "OPEN-PROM 2.2",
    "POLES 2.4",
    "PROMETHEUS V1",
    "REMIND-MAgPIE 3.7-4.14",
    "WITCH 6.0",
]


def slugify(text: str) -> str:
    """Convert free text into a URL-safe, lower-case, hyphen-separated slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def criterion_type_dir(crit_type: str) -> str:
    """Directory slug for a criterion type (matches the on-disk criteria dir)."""
    return _deformat_prefix(crit_type)


def criterion_page_slug(criterion: str) -> str:
    """Filename slug for a full criterion key, e.g. ``"Type|A|B"`` -> ``"a-b"``."""
    _, _, rest = criterion.partition("|")
    return slugify(rest)


def criterion_page_href(criterion: str) -> str:
    """Relative link (from the summary landing page) to a criterion's page."""
    crit_type, _, _ = criterion.partition("|")
    return f"{criterion_type_dir(crit_type)}/{criterion_page_slug(criterion)}/"


@cache
def load_criteria_hierarchy() -> tuple[dict, dict[str, list[str]]]:
    """Return criteria types and, per type, its criteria in descriptions.yaml order.

    Cheap (only parses small YAML files, no thresholds/region-mapping I/O),
    so it's safe to call from the mkdocs nav-generation hook
    (``mkdocs_nav.py``), which runs on every build/reload before any page
    content is generated. Cached for the same reason as
    :func:`load_summary_context`; also used by that function so both draw
    the criteria order from a single source of truth.
    """
    criteria_types, criteria_meta = load_criteria(
        ["criteria-types", "criteria-descriptions"],
    ).values()
    ordered_criteria = list(criteria_meta)
    criteria_by_type = {
        crit_type: [c for c in ordered_criteria if c.startswith(f"{crit_type}|")]
        for crit_type in criteria_types
    }
    return criteria_types, criteria_by_type


@cache
def load_summary_context() -> dict:
    """Load and combine all data needed to render the summary pages.

    Cached: mkdocs-gen-files re-runs its scripts on every rebuild during
    `mkdocs serve` (in the same long-lived process), and the
    region-mapping lookups
    (:func:`~scenario_evaluation_criteria.preprocessed.region_mapping_from_definition`)
    are expensive (each hits the local nomenclature checkout for every
    model hierarchy) — caching avoids repeating that on every live-reload.
    """
    region_mapping_r5 = region_mapping_from_definition(
        REGION_DEFINITIONS, hierarchy="R5"
    )
    region_mapping_r9 = region_mapping_from_definition(
        REGION_DEFINITIONS, hierarchy="R9"
    )
    region_mapping_r10 = region_mapping_from_definition(
        REGION_DEFINITIONS, hierarchy="R10"
    )
    region_mapping_by_model = {
        model: region_mapping_from_definition(REGION_DEFINITIONS, hierarchy=model)
        for model in MODEL_HIERARCHIES
    }
    region_mapping = {
        **region_mapping_r5,
        **region_mapping_r9,
        **region_mapping_r10,
        **{
            region: codes
            for model_regions in region_mapping_by_model.values()
            for region, codes in model_regions.items()
        },
    }
    # Two groups of region tabs, nested under their own outer tab (see
    # render_criterion): "generic" cross-model region aggregations (R5/R9/
    # R10) vs. "model-native" regions (each model's own, non-aggregated
    # regions) — distinct enough in meaning that flattening them into one
    # tab row would obscure which kind of region a given tab represents.
    region_tab_groups = [
        ("Generic regions", [
            ("R5", set(region_mapping_r5)),
            ("R9", set(region_mapping_r9)),
            ("R10", set(region_mapping_r10)),
        ]),
        ("Model-native regions", sorted(
            (model_name, set(model_regions))
            for model_name, model_regions in region_mapping_by_model.items()
        )),
    ]

    criteria_types, criteria_by_type = load_criteria_hierarchy()
    criteria_meta, sources, reference_metadata = load_criteria(
        ["criteria-descriptions", "sources", "reference-metadata"],
    ).values()
    sources_formatted = format_sources(sources)
    # format_sources mutates the bib entries it's given (e.g. it deletes
    # their doi/url/pdf fields), so the html-rendered variant needs its own
    # freshly-parsed bib data rather than reusing `sources` above.
    sources_formatted_html = format_sources(load_criteria("sources"), target="html")
    criteria_combined_all = load_criteria_combined(region_mapping=region_mapping)

    return {
        "criteria_types": criteria_types,
        "criteria_by_type": criteria_by_type,
        "criteria_meta": criteria_meta,
        "sources_formatted": sources_formatted,
        "sources_formatted_html": sources_formatted_html,
        "reference_metadata": reference_metadata,
        "criteria_combined_all": criteria_combined_all,
        "region_tab_groups": region_tab_groups,
    }


def _fmt_num(v):
    if pd.isna(v):
        return v
    if v == 0:
        return 0.0
    if abs(v) >= 100:
        return round(v, 0)
    return float(sf_round(str(v), sigfigs=3))


def pivot_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot lower/upper bounds into columns, including relative and reference values."""
    d = df.drop(columns="criterion").copy()
    d["year"] = d["year"].astype("object").where(d["year"].notna(), other="")
    has_ref = d["value_rel"].notna().any()

    # Pivot absolute values, relative multipliers, and reference values together.
    pivoted = d.pivot_table(
        index=["variable", "region", "year", "evaluation_outcome", "unit"],
        columns="threshold_type",
        values=["value", "value_rel", "reference_value"],
        aggfunc="first",
    )
    name_map = {
        ("value", "lower"): "Lower (abs)", ("value", "upper"): "Upper (abs)",
        ("value_rel", "lower"): "Lower (rel)", ("value_rel", "upper"): "Upper (rel)",
        ("reference_value", "lower"): "Lower (ref)", ("reference_value", "upper"): "Upper (ref)",
    }
    pivoted.columns = [name_map.get(c, "_".join(c)) for c in pivoted.columns]
    pivoted = pivoted.reset_index()

    if has_ref:
        # reference_data_expr is the same for both threshold types; attach once.
        ref_expr = (
            d.groupby(["variable", "year", "evaluation_outcome"], dropna=False)
            ["reference_data_expr"].first().reset_index()
        )
        pivoted = pivoted.merge(ref_expr, on=["variable", "year", "evaluation_outcome"], how="left")

        for col in ["Lower (rel)", "Upper (rel)"]:
            pivoted[col] = pivoted[col].apply(
                lambda v: f"{(v - 1) * 100:+.0f}%" if pd.notna(v) else v
            )
        for col in ["Lower (ref)", "Upper (ref)"]:
            pivoted[col] = pivoted[col].apply(
                _fmt_num
            )
        pivoted["reference_data_expr"] = pivoted["reference_data_expr"].apply(
            lambda v: re.sub(r"^range\((.+)\)$", r"Most permissive value of: \1", v)
            if pd.notna(v) else v
        )

    for col in ["Lower (abs)", "Upper (abs)"]:
        if col in pivoted.columns:
            pivoted[col] = pivoted[col].apply(
                _fmt_num
            )

    col_order = [
        "variable", "region", "year", "unit", "evaluation_outcome",
        "Lower (abs)",
        *(["Lower (rel)", "Lower (ref)"] if has_ref else []),
        "Upper (abs)",
        *(["Upper (rel)", "Upper (ref)"] if has_ref else []),
        *(["reference_data_expr"] if has_ref else []),
    ]
    result = pivoted[[c for c in col_order if c in pivoted.columns]]
    result = result.rename(columns={"reference_data_expr": "reference_data"})
    return result.rename(columns=lambda c: c.replace("_", " ").capitalize())


def render_tabbed_set(tabs: list[tuple[str, str]], group_id) -> str:
    """Hand-render a pymdownx.tabbed "alternate style" tab set as raw HTML.

    ``=== "Tab"`` markdown content is reparsed by a nested block-processor
    call that never runs Python-Markdown's raw-HTML preprocessor (that
    preprocessor only ever sees the whole page once, before any nested
    block reparsing) — so multi-line raw HTML placed inside a tab (like an
    itables datatable) gets escaped/wrapped in a stray ``<p>`` instead of
    preserved verbatim. Emitting the same DOM structure directly, as one
    top-level raw HTML block, sidesteps that: top-level raw HTML *is*
    preserved untouched. The structure/classes below match pymdownx.tabbed's
    "alternate_style" output exactly, so mkdocs-material's tab CSS and
    "content.tabs.link" behaviour keep working unchanged.
    """
    inputs = "".join(
        f'<input{" checked=\"checked\"" if i == 0 else ""} '
        f'id="__tabbed_{group_id}_{i + 1}" name="__tabbed_{group_id}" type="radio" />'
        for i in range(len(tabs))
    )
    labels = "".join(
        f'<label for="__tabbed_{group_id}_{i + 1}">{label}</label>'
        for i, (label, _) in enumerate(tabs)
    )
    blocks = "".join(
        f'<div class="tabbed-block">\n{content}\n</div>\n' for _, content in tabs
    )
    return (
        f'<div class="tabbed-set tabbed-alternate" data-tabs="{group_id}:{len(tabs)}">'
        f'{inputs}<div class="tabbed-labels">{labels}</div>\n'
        f"<div class=\"tabbed-content\">\n{blocks}</div>\n"
        f"</div>\n"
    )


def render_summary_tree(ctx: dict) -> str:
    """Return a nested bullet list of all criteria types and criteria.

    Used on the summary landing page, mirroring the same hierarchy as the
    dynamically-generated sidebar nav (see ``mkdocs_nav.py``).
    """
    lines = []
    for crit_type, criteria in ctx["criteria_by_type"].items():
        if not criteria:
            continue
        lines.append(f"* [{crit_type}]({criterion_type_dir(crit_type)}/)")
        for criterion in criteria:
            display_name = criterion.split("|", 1)[1]
            lines.append(f"    * [{display_name}]({criterion_page_href(criterion)})")
    return "\n".join(lines)


def render_criteria_type(crit_type: str, ctx: dict) -> str:
    """Return the markdown body of a criterion type's own detail page."""
    type_spec = ctx["criteria_types"][crit_type]
    sources_formatted = ctx["sources_formatted"]

    def _fmt(text):
        return insert_citations(text, sources_formatted, "../../components/sources/").replace("\n", "<br>")

    blocks = [_fmt(type_spec["description"])]

    outcomes = ["**Possible evaluation outcomes:**\n"]
    outcomes += [
        f"* `{outcome}` — {outcome_desc}"
        for outcome, outcome_desc in type_spec["evaluation_outcomes"].items()
    ]
    blocks.append("\n".join(outcomes))

    links = ["**Criteria:**\n"]
    links += [
        f"* [{criterion.split('|', 1)[1]}]({criterion_page_slug(criterion)}/)"
        for criterion in ctx["criteria_by_type"].get(crit_type, [])
    ]
    blocks.append("\n".join(links))

    return "\n\n".join(blocks)


def render_reference_data_table(
    criterion: str,
    ctx: dict,
    reference_data_link_prefix: str,
    sources_link_prefix: str,
) -> str:
    """Return a "## Reference data" section listing the datasets used by ``criterion``.

    Mirrors the overview table on the "Reference data" component page
    (``docs/components/reference_data.md``), filtered to the datasets
    actually referenced by this criterion's thresholds.
    """
    criteria_combined_all = ctx["criteria_combined_all"]
    used = sorted(
        criteria_combined_all.loc[
            criteria_combined_all["criterion"] == criterion, "reference_data"
        ]
        .dropna()
        .unique()
    )
    if not used:
        return ""

    reference_metadata = ctx["reference_metadata"]
    sources_formatted = ctx["sources_formatted"]

    def source_link(source_key):
        if not source_key:
            return "—"
        cite = (
            sources_formatted[source_key]["cite"]
            if source_key in sources_formatted
            else source_key
        )
        return f"[{cite}]({sources_link_prefix}#{source_key})"

    lines = ["## Reference data\n", "| Dataset | Source | Description |", "|---|---|---|"]
    for ref in used:
        meta = reference_metadata.get(ref, {})
        src = source_link(meta.get("source"))
        # Unlike docs/components/reference_data.md, this runs as plain
        # Python (not inside a markdown page), so the placeholder never
        # goes through mkdocs-macros' Jinja pass and needs no {% raw %}
        # escaping — it's matched here exactly as it appears in the data.
        desc = meta.get("description", "").replace("{{source}}", src)
        page = f"{reference_data_link_prefix}#{ref.lower()}"
        lines.append(f"| [`{ref}`]({page}) | {src} | {desc} |")

    return "\n".join(lines)


_CITATION_RE = re.compile(r"{{(?:cite|citep):([^}]+)}}")


def _cited_source_ids(text: str | None) -> set[str]:
    return set(_CITATION_RE.findall(text)) if text else set()


def render_criterion_sources_table(criterion: str, ctx: dict) -> str:
    """Return a "## Sources" section for the sources cited on ``criterion``'s page.

    Mirrors the table on the "Sources" component page
    (``docs/components/sources.md``), filtered to the sources cited in this
    criterion's justification texts/note or used by its reference data.
    Citation links on the criterion page point here (same-page anchors)
    instead of to that shared, much larger table.
    """
    meta = ctx["criteria_meta"].get(criterion, {})
    cited = set()
    for field in ("justification_criterion", "justification_threshold", "note"):
        cited |= _cited_source_ids(meta.get(field))

    criteria_combined_all = ctx["criteria_combined_all"]
    used_datasets = (
        criteria_combined_all.loc[
            criteria_combined_all["criterion"] == criterion, "reference_data"
        ]
        .dropna()
        .unique()
    )
    reference_metadata = ctx["reference_metadata"]
    for ref in used_datasets:
        if source_key := reference_metadata.get(ref, {}).get("source"):
            cited.add(source_key)

    if not cited:
        return ""

    sources_formatted_html = ctx["sources_formatted_html"]
    ordered_ids = [sid for sid in sources_formatted_html if sid in cited]

    def combine_urls(entry):
        ret = []
        if entry["url_doi"]:
            ret.append(f"[ :simple-doi: DOI ]({entry['url_doi']}){{ .sm-button }} ")
        if entry["url"] and (not entry["doi"] or entry["doi"] == entry["url_doi"]):
            ret.append(f"[ :material-link-box: URL ]({entry['url']}){{ .sm-button }} ")
        if entry["pdf"]:
            ret.append(f"[ :fontawesome-solid-file-pdf: PDF ]({entry['pdf']}){{ .sm-button }} ")
        return "<br>".join(ret)

    lines = ["## Sources\n", "| Identifier | Bibliographic information | Links |", "|---|---|---|"]
    for sid in ordered_ids:
        entry = sources_formatted_html[sid]
        identifier = f'<p id="{sid}">`{sid}`</p>'
        bib = entry["bib"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {identifier} | {bib} | {combine_urls(entry)} |")

    return "\n".join(lines)


def render_criterion(criterion: str, ctx: dict, components_link_prefix: str) -> str:
    """Return the markdown/HTML body of a single criterion's detail page."""
    # Citations point to the "## Sources" section appended at the end of
    # this same page (see render_criterion_sources_table), not to the
    # component page's much larger table — an empty link prefix keeps the
    # generated href a same-page "#<id>" anchor.
    sources_link_prefix = ""
    sources_formatted = ctx["sources_formatted"]
    blocks = []

    def _fmt(text):
        return insert_citations(text, sources_formatted, sources_link_prefix).replace("\n", "<br>")

    meta = ctx["criteria_meta"].get(criterion, {})
    if jc := meta.get("justification_criterion"):
        blocks.append(f"**Why this criterion?** {_fmt(jc)}\n")
    if jt := meta.get("justification_threshold"):
        blocks.append(f"**Why this threshold?** {_fmt(jt)}\n")

    criteria_combined_all = ctx["criteria_combined_all"]
    world_df = pivot_thresholds(
        criteria_combined_all[
            (criteria_combined_all["criterion"] == criterion)
            & (criteria_combined_all["region"] == "World")
        ].copy()
    ).drop(columns="Region")
    world_html = to_html_datatable(world_df, connected=True, style="width:100%")
    world_body = f"<div>\n{world_html}\n</div>"

    regional_rows = criteria_combined_all[
        (criteria_combined_all["criterion"] == criterion)
        & (criteria_combined_all["region"] != "World")
    ]
    # World stays a top-level tab; the generic (R5/R9/R10) and model-native
    # region tabs are each nested one level down under their own group tab,
    # so the tab bar names what kind of regions it holds instead of mixing
    # ~20 flat, unlabelled tabs together (see render_tabbed_set — a tab's
    # content can itself be another tab set, so this needs no new markup).
    top_tabs = [("World", world_body)]
    for group_id, (group_label, group_tabs) in enumerate(
        ctx["region_tab_groups"], start=2
    ):
        inner_tabs = []
        for tab_label, tab_regions in group_tabs:
            tab_df = regional_rows[regional_rows["region"].isin(tab_regions)].copy()
            if tab_df.empty:
                continue
            # Native model regions are named "<model>|<region>"; the
            # model prefix is redundant once the region is shown in
            # that model's own tab.
            tab_df["region"] = tab_df["region"].str.rsplit("|", n=1).str[-1]
            tab_pivoted = pivot_thresholds(tab_df)
            tab_html = to_html_datatable(
                tab_pivoted, connected=True, style="width:100%"
            )
            inner_tabs.append((tab_label, f"<div>\n{tab_html}\n</div>"))
        if inner_tabs:
            top_tabs.append((group_label, render_tabbed_set(inner_tabs, group_id)))
    blocks.append(render_tabbed_set(top_tabs, 1))

    if note := meta.get("note"):
        blocks.append(f"!!! note\n\n    {_fmt(note).replace("\n", "\n    ")}\n")

    ref_table = render_reference_data_table(
        criterion,
        ctx,
        f"{components_link_prefix}reference_data/",
        sources_link_prefix,
    )
    if ref_table:
        blocks.append(ref_table)

    sources_table = render_criterion_sources_table(criterion, ctx)
    if sources_table:
        blocks.append(sources_table)

    # A single blank line is required between two blocks that are each
    # (or start with) a plain markdown table/heading — otherwise
    # python-markdown's table parser glues adjacent table-like lines
    # together, e.g. swallowing the "## Sources" heading as a stray row
    # of the preceding reference-data table.
    return "\n\n".join(blocks)
