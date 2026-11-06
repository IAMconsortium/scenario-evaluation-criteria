"""Preprocess criteria definitions for use with IAMC nomenclature package."""

import pandas as pd

from nomenclature import countries

from . import load_criteria


def _convert_year(value):
    """Convert a single ``year`` cell to an int, or keep a cumulative range.

    Plain integer years are returned as Python ints so they still match the
    (integer) ``year`` column of the reference data during merging.
    Cumulative ranges of the form ``cumulative[YYYY-YYYY]`` are passed
    through unchanged: they denote a threshold on the cumulative sum over the
    year range rather than a single-year value, and never carry reference
    data. Missing values are returned as ``pd.NA``.

    Note that a single row may hold several comma-separated cumulative
    ranges; these are split and exploded into one row each upstream (Step 2),
    so this function only ever sees an individual entry.
    """
    if pd.isna(value):
        return pd.NA
    value = value.strip()
    if value.startswith("cumulative["):
        return value
    return int(value)


def _aggregate_reference_data_to_regions(reference_data, region_mapping):
    """Sum country-resolved reference-data rows up to regions.

    For each region in ``region_mapping``, sums the ``value`` of its member
    countries' rows, grouping by every other existing column so that
    per-source/variable/year (and cumulative-range) granularity is preserved.
    The aggregated rows are appended to ``reference_data``; existing rows
    (``World`` and individual countries) are left untouched, since they are
    simply no longer referenced once ``region_mapping`` is in use.
    """
    membership = pd.DataFrame(
        [
            (region, country)
            for region, members in region_mapping.items()
            for country in members
        ],
        columns=["region_agg", "region"],
    )
    group_cols = [
        c for c in reference_data.columns if c not in ("region", "value")
    ]
    aggregated = (
        reference_data.merge(membership, on="region")
        .groupby(group_cols + ["region_agg"], dropna=False)["value"]
        .sum()
        .reset_index()
        .rename(columns={"region_agg": "region"})
    )
    return pd.concat([reference_data, aggregated], ignore_index=True)


def region_mapping_from_definition(
    definitions_path, hierarchy=None
) -> dict[str, list[str]]:
    """Build a region_mapping dict from a local nomenclature region definition.

    Parameters
    ----------
    definitions_path
        Path to a local clone of a nomenclature-compatible ``definitions``
        folder containing a ``region`` subfolder (e.g. a checkout of
        github.com/IAMconsortium/common-definitions).
    hierarchy
        If given, only regions whose ``hierarchy`` attribute matches this
        value are included (e.g. ``"R5"``, ``"R10"``).

    Returns
    -------
    dict[str, list[str]]
        Mapping of region name to the ISO3-alpha-3 codes of its member
        countries, suitable for the ``region_mapping`` argument of
        :func:`load_criteria_combined`.

    """
    from nomenclature import DataStructureDefinition

    dsd = DataStructureDefinition(definitions_path, dimensions=["region"])
    return {
        code.name: [countries.lookup(name).alpha_3 for name in code.countries]
        for code in dsd.region.mapping.values()
        if code.countries
        and (hierarchy is None or code.hierarchy == hierarchy)
    }


def load_criteria_combined(
    region_mapping: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    """Load and combine criteria thresholds with reference data.

    Processes raw criteria definitions through six steps:
    melting bound types, exploding comma-separated fields, expanding
    ``All Countries``, resolving reference-data multipliers, and applying
    range/min/max operators across multiple sources.

    Parameters
    ----------
    region_mapping
        Optional mapping of region name to the ISO3-alpha-3 codes of its
        member countries (see :func:`region_mapping_from_definition`). If
        given, ``All Countries`` expands into the given region names instead
        of individual countries, and country-resolved reference data is
        aggregated (summed) up to each region before thresholds are applied.
        If omitted, ``All Countries`` expands into individual countries as
        before.

    Returns
    -------
    pd.DataFrame
        One row per (criterion, variable, region, year, evaluation_outcome,
        threshold_type) combination with columns ``value`` and ``unit``.

    """
    # Step 0: Load the raw criteria definitions.
    criteria_thrsh = load_criteria("criteria-thresholds")
    reference_data = load_criteria("reference-data")
    if region_mapping is not None:
        reference_data = _aggregate_reference_data_to_regions(
            reference_data, region_mapping
        )

    # Step 1: Melt threshold types (upper, lower) into column.
    criteria_step1 = criteria_thrsh.melt(
        id_vars=[c for c in criteria_thrsh if c not in ["upper", "lower"]],
        value_vars=["upper", "lower"],
        var_name="threshold_type",
    ).dropna(subset="value")

    # Step 2: Explode comma-separated values in variable, region, and year
    # columns. Comma-separated cumulative ranges (e.g.
    # ``cumulative[2020-2100], cumulative[2010-2050]``) are thereby expanded
    # into one row per range, just like plain years.
    criteria_tmp = criteria_step1.copy()
    for col_name in ["variable", "region", "year"]:
        criteria_tmp[col_name] = criteria_tmp[col_name].str.split(",")
        criteria_tmp = criteria_tmp.explode(col_name)
        criteria_tmp[col_name] = criteria_tmp[col_name].str.strip()

    # Cast plain years to int while keeping cumulative ranges as strings.
    criteria_step2 = criteria_tmp.reset_index(drop=True)
    criteria_step2["year"] = criteria_step2["year"].map(_convert_year)

    # Step 3: Replace `All Countries` with country/region codes and explode.
    if region_mapping is not None:
        all_countries = list(region_mapping.keys())
    else:
        all_countries = [country.alpha_3 for country in countries]
    criteria_step3 = (
        criteria_step2.assign(
            region=lambda df: df["region"].map(
                lambda r: all_countries if r == "All Countries" else r
            )
        )
        .explode("region")
        .reset_index(drop=True)
    )

    # Step 4: Explode sources; preserve the original full expression for
    # display.
    criteria_step4 = (
        pd.concat(
            [
                # Extract operator and individual source names from
                # reference_data.
                criteria_step3["reference_data"].str.extract(
                    r"(?P<reference_multi_operator>[a-z]+)?"
                    r"\(?(?P<reference_data>[^\)]+)\)?"
                ),
                # Carry the original expression alongside the rest of the data.
                criteria_step3.drop(columns="reference_data").assign(
                    reference_data_expr=criteria_step3["reference_data"].values
                ),
            ],
            axis=1,
        )
        # Insert value `range` if operator is empty.
        .fillna({"reference_multi_operator": "range"})
        # Split list of sources by comma and expand.
        .assign(reference_data=lambda df: df["reference_data"].str.split(","))
        .explode("reference_data")
        .assign(reference_data=lambda df: df["reference_data"].str.strip())
        # Reset index.
        .reset_index(drop=True)
    )

    # Step 5: Merge with references list and compute absolute values.
    # Keep value_rel (the threshold multiplier) and reference_value (the
    # dataset value) so they can be surfaced by load_criteria_combined.
    criteria_step5 = (
        criteria_step4
        # Merge with reference data.
        .merge(
            reference_data,
            on=["reference_data", "variable", "region", "year"],
        )
        # Assign new value and unit; retain relative and reference columns.
        .assign(
            value=lambda df: (
                df.value_y + (df.value_x - 1.0) * df.value_y.abs()
            ),
            unit=lambda df: df.unit_y.fillna(df.unit_x),
            value_rel=lambda df: df.value_x,
            reference_value=lambda df: df.value_y,
        )
        # Combine with data that does not use a reference.
        .pipe(
            lambda df: pd.concat(
                [
                    df,
                    criteria_step4.loc[
                        criteria_step4["reference_data"].isnull()
                    ],
                ]
            )
        )
        # Drop intermediate merge columns.
        .drop(columns=["value_x", "value_y", "unit_x", "unit_y"])
        .reset_index(drop=True)
    )

    # Step 6: Apply operator for multiple sources.
    # Track which source won (idxmin/idxmax) so value_rel and reference_value
    # reflect the actual source used for the aggregated absolute value.
    def combine(group):
        assert group["unit"].nunique() == 1, (
            "Unit must be the same across combined references."
        )
        assert group["reference_multi_operator"].nunique() == 1, (
            "Operation must be the same across combined references."
        )
        threshold_type = group.name[-1]
        # Determine operator
        operator = group["reference_multi_operator"].iloc[0]
        if operator == "range":
            operator = "min-max"
        if "-" in operator:
            operator = operator.split("-")[
                ["lower", "upper"].index(threshold_type)
            ]
        # Find the winning row (min or max of the absolute value).
        agg_value = getattr(group["value"], operator)()
        winning_row = group.loc[getattr(group["value"], f"idx{operator}")()]
        return pd.Series(
            {
                "value": agg_value,
                "unit": group["unit"].iloc[0],
                "value_rel": winning_row["value_rel"],
                "reference_value": winning_row["reference_value"],
                "reference_data": winning_row["reference_data"],
                "reference_data_expr": winning_row["reference_data_expr"],
            }
        )

    return (
        criteria_step5.groupby(
            [
                "criterion",
                "region",
                "year",
                "variable",
                "evaluation_outcome",
                "threshold_type",
            ],
            dropna=False,
        )[
            [
                "reference_multi_operator",
                "unit",
                "value",
                "value_rel",
                "reference_value",
                "reference_data",
                "reference_data_expr",
            ]
        ]
        .apply(combine)
        .reset_index()
    )


def load_criteria_for_validator() -> list[dict]:
    """Load criteria definitions for use with IAMC nomenclature validator.

    Returns
    -------
    list[dict]
        Criteria definitions for use with IAMC nomenclature validator.

    """
    criteria_combined = load_criteria_combined()

    def _build_entry(row):
        # Pass the evaluation outcome to the validator as `warning_level`
        # for the concern outcomes (`medium`/`high`), but drop it for the
        # vetting outcome (`failed`).
        entry = {
            "upper_bound": row["upper_bound"],
            "lower_bound": row["lower_bound"],
        }
        if row["evaluation_outcome"] != "failed":
            entry = {"warning_level": row["evaluation_outcome"], **entry}
        return entry

    # Convert dataframe to list of nested dictionaries and return.
    return (
        criteria_combined.query("region=='World'")
        .rename(columns={"criterion": "name"})
        .assign(
            name=lambda df: df["name"]
            + ("|" + df["region"].astype(str)).where(
                df["region"].notna(), other=""
            )
            + ("|" + df["year"].astype(str)).where(
                df["year"].notna(), other=""
            ),
            threshold_type=lambda df: df["threshold_type"] + "_bound",
        )
        .drop(columns="unit")
        # Keep the evaluation outcome in the pivot index so that medium and
        # high thresholds remain separate entries.
        .pivot(
            index=["name", "region", "year", "variable", "evaluation_outcome"],
            columns="threshold_type",
            values="value",
        )
        .reset_index()
        .groupby(["name", "region", "year", "variable"], dropna=False)[
            ["evaluation_outcome", "upper_bound", "lower_bound"]
        ]
        .apply(lambda df: list(df.apply(_build_entry, axis=1)))
        .to_frame("evaluation")
        .reset_index()
        .apply(lambda row: row.dropna().to_dict(), axis=1)
        .tolist()
    )
