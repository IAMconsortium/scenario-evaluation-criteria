"""Tests for ``scenario_evaluation_criteria.preprocessed``.

These load the installed package and exercise ``load_criteria_combined``
and its region-aggregation support against the data bundled into the
package, and against the real IAMConsortium/common-definitions region
definitions (fetched on demand via ``region-definitions/nomenclature.yaml``
using nomenclature-iamc's external-repository mechanism — see that file for
why common-definitions isn't a regular package dependency). These tests
therefore require network access to github.com.
"""

from pathlib import Path

import pandas
import pytest

from scenario_evaluation_criteria import load_criteria
from scenario_evaluation_criteria.preprocessed import (
    load_criteria_combined,
    region_mapping_from_definition,
)

REGION_DEFINITIONS = (
    Path(__file__).parent.parent.parent / "region-definitions" / "definitions"
)


@pytest.fixture(scope="module")
def region_mapping_r5():
    return region_mapping_from_definition(REGION_DEFINITIONS, hierarchy="R5")


# ---------------------------------------------------------------------------
# region_mapping_from_definition
# ---------------------------------------------------------------------------


def test_region_mapping_from_definition_returns_iso3_codes(region_mapping_r5):
    assert set(region_mapping_r5) == {
        "OECD & EU (R5)",
        "Reforming Economies (R5)",
        "Asia (R5)",
        "Middle East & Africa (R5)",
        "Latin America (R5)",
    }
    assert "DEU" in region_mapping_r5["OECD & EU (R5)"]
    assert "RUS" in region_mapping_r5["Reforming Economies (R5)"]
    assert all(
        isinstance(code, str) and len(code) == 3
        for members in region_mapping_r5.values()
        for code in members
    )


def test_region_mapping_from_definition_filters_by_hierarchy():
    unfiltered = region_mapping_from_definition(REGION_DEFINITIONS)
    r5 = region_mapping_from_definition(REGION_DEFINITIONS, hierarchy="R5")
    assert set(r5) <= set(unfiltered)
    r9 = region_mapping_from_definition(REGION_DEFINITIONS, hierarchy="R9")
    r10 = region_mapping_from_definition(REGION_DEFINITIONS, hierarchy="R10")
    assert set(r5).isdisjoint(r9)
    assert set(r5).isdisjoint(r10)


# ---------------------------------------------------------------------------
# load_criteria_combined: default behaviour (no region_mapping)
# ---------------------------------------------------------------------------


def test_load_criteria_combined_without_mapping_expands_countries():
    df = load_criteria_combined()
    assert isinstance(df, pandas.DataFrame)
    assert not df.empty
    assert "World" in df["region"].unique()
    # "All Countries" rows still expand into individual ISO3 codes.
    assert (df["region"].str.len() == 3).sum() > 100


# ---------------------------------------------------------------------------
# load_criteria_combined: with region_mapping
# ---------------------------------------------------------------------------


def test_load_criteria_combined_with_mapping_has_no_leftover_countries(
    region_mapping_r5,
):
    df = load_criteria_combined(region_mapping=region_mapping_r5)
    # Only "World" and the mapped region names should ever appear; no
    # individual (unaggregated) country code should leak through.
    assert set(df["region"].unique()) <= {"World"} | set(region_mapping_r5)


def test_load_criteria_combined_with_mapping_aggregates_countries(
    region_mapping_r5,
):
    # "Emissions|CH4|AFOLU|Agriculture" combines four country-resolved
    # sources (EDGAR-2025, FAOSTAT-2026, PRIMAP-2025-v2p7-HISTCR/HISTTP) via
    # a "range" operator (min for the lower bound, max for the upper bound),
    # with the same relative multiplier applied to every source. Since the
    # multiplier is a positive constant, the winning source is simply the
    # one with the smallest (lower bound) or largest (upper bound)
    # region-aggregated absolute value, so the outcome can be predicted by
    # hand-aggregating the reference data directly.
    variable = "Emissions|CH4|AFOLU|Agriculture"
    sources = [
        "EDGAR-2025",
        "FAOSTAT-2026",
        "PRIMAP-2025-v2p7-HISTCR",
        "PRIMAP-2025-v2p7-HISTTP",
    ]
    df = load_criteria_combined(region_mapping=region_mapping_r5)
    subset = df[
        (df["criterion"] == "Historical Vetting|" + variable)
        & (df["year"] == 2010)
    ]
    assert set(subset["region"]) == {"World"} | set(region_mapping_r5)

    reference_data = load_criteria("reference-data")

    def aggregated_source_values(region):
        members = region_mapping_r5.get(region)
        return {
            source: reference_data[
                (reference_data["reference_data"] == source)
                & (reference_data["variable"] == variable)
                & (reference_data["year"] == 2010)
                & (
                    reference_data["region"].isin(members)
                    if members is not None
                    else reference_data["region"] == "World"
                )
            ]["value"].sum()
            for source in sources
        }

    for region in set(region_mapping_r5) | {"World"}:
        values = aggregated_source_values(region)
        row = subset[
            (subset["region"] == region)
            & (subset["threshold_type"] == "lower")
        ].iloc[0]
        assert row["value"] == pytest.approx(0.8 * min(values.values()))
        row = subset[
            (subset["region"] == region)
            & (subset["threshold_type"] == "upper")
        ].iloc[0]
        assert row["value"] == pytest.approx(1.2 * max(values.values()))
