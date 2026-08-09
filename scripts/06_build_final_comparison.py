"""
06_build_final_comparison.py

Build a consolidated comparison table from the Yabboq drainage validation
workflow.

Inputs
------
1. Simple density-matched random-cell null results
2. Terrain-matched null results

Outputs
-------
1. final_comparison.csv
2. final_comparison_summary.txt

The final table reports, for each flow-accumulation threshold and spatial
tolerance:

    - observed drainage/reference agreement
    - simple random-cell null mean
    - terrain-matched null mean
    - observed minus simple random null
    - observed minus terrain-matched null
    - terrain-matched null 95% interval
    - empirical p-values

IMPORTANT
---------
This is a diagnostic summary of spatial agreement.

It does NOT establish:
    - an ancient route
    - historical identity
    - patriarchal movement
    - drainage-network topology

The terrain-matched null remains stronger than the simple random-cell null,
but it does not preserve network connectivity or flow topology.
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# INPUTS
# ---------------------------------------------------------------------

RANDOM_NULL_RESULTS = Path(
    r"..\outputs\null_background_test\null_background_results.csv"
)

TERRAIN_NULL_RESULTS = Path(
    r"..\outputs\terrain_matched_null\terrain_matched_null_results.csv"
)

OUTPUT_DIR = Path(
    r"..\outputs\final_comparison"
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def require_file(path, label):
    """
    Confirm that an expected input file exists.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"{label} was not found:\n{path}"
        )


def find_column(df, candidates, label):
    """
    Return the first matching column name from a list of possible names.

    This makes the script slightly tolerant of naming differences between
    earlier analysis scripts.
    """

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    raise KeyError(
        f"Could not identify {label}.\n"
        f"Tried these column names:\n"
        f"{candidates}\n\n"
        f"Available columns are:\n"
        f"{list(df.columns)}"
    )


def percent(value):
    """
    Format a percentage value.
    """

    if pd.isna(value):
        return "NA"

    return f"{value:.2f}%"


def points(value):
    """
    Format percentage-point differences.
    """

    if pd.isna(value):
        return "NA"

    sign = "+" if value >= 0 else ""

    return f"{sign}{value:.2f} pp"


def pvalue(value):
    """
    Format an empirical p-value.
    """

    if pd.isna(value):
        return "NA"

    return f"{value:.4f}"


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print(
        "Step 1/5: Checking input files..."
    )

    require_file(
        RANDOM_NULL_RESULTS,
        "Simple random-cell null results",
    )

    require_file(
        TERRAIN_NULL_RESULTS,
        "Terrain-matched null results",
    )

    print(
        "Step 2/5: Reading results..."
    )

    random_df = pd.read_csv(
        RANDOM_NULL_RESULTS
    )

    terrain_df = pd.read_csv(
        TERRAIN_NULL_RESULTS
    )

    # -------------------------------------------------------------
    # Identify key columns.
    # -------------------------------------------------------------

    threshold_random = find_column(
        random_df,
        [
            "flow_threshold_cells",
            "threshold_cells",
            "flow_threshold",
        ],
        "random-null threshold column",
    )

    tolerance_random = find_column(
        random_df,
        [
            "tolerance_m",
            "tolerance",
        ],
        "random-null tolerance column",
    )

    observed_random = find_column(
        random_df,
        [
            "observed_agreement_pct",
            "observed_pct",
            "observed_agreement",
        ],
        "random-null observed agreement column",
    )

    random_mean = find_column(
        random_df,
        [
            "null_mean_pct",
            "random_null_mean_pct",
            "background_null_mean_pct",
            "null_background_mean_pct",
        ],
        "simple random-null mean column",
    )

    random_difference = find_column(
        random_df,
        [
            "observed_minus_null_pct",
            "observed_minus_random_null_pct",
            "observed_minus_background_null_pct",
        ],
        "observed-minus-random-null column",
    )

    random_p = find_column(
        random_df,
        [
            "empirical_p_value",
            "p_value",
            "empirical_p",
        ],
        "random-null empirical p-value column",
    )

    threshold_terrain = find_column(
        terrain_df,
        [
            "flow_threshold_cells",
            "threshold_cells",
            "flow_threshold",
        ],
        "terrain-null threshold column",
    )

    tolerance_terrain = find_column(
        terrain_df,
        [
            "tolerance_m",
            "tolerance",
        ],
        "terrain-null tolerance column",
    )

    observed_terrain = find_column(
        terrain_df,
        [
            "observed_agreement_pct",
            "observed_pct",
            "observed_agreement",
        ],
        "terrain-null observed agreement column",
    )

    terrain_mean = find_column(
        terrain_df,
        [
            "terrain_null_mean_pct",
            "null_mean_pct",
        ],
        "terrain-null mean column",
    )

    terrain_lower = find_column(
        terrain_df,
        [
            "terrain_null_2_5_pct",
            "null_2_5_pct",
            "null_lower_95_pct",
        ],
        "terrain-null lower 95% interval column",
    )

    terrain_upper = find_column(
        terrain_df,
        [
            "terrain_null_97_5_pct",
            "null_97_5_pct",
            "null_upper_95_pct",
        ],
        "terrain-null upper 95% interval column",
    )

    terrain_difference = find_column(
        terrain_df,
        [
            "observed_minus_terrain_null_pct",
            "observed_minus_null_pct",
        ],
        "observed-minus-terrain-null column",
    )

    terrain_p = find_column(
        terrain_df,
        [
            "empirical_p_value",
            "p_value",
            "empirical_p",
        ],
        "terrain-null empirical p-value column",
    )

    print(
        "Step 3/5: Consolidating comparison table..."
    )

    random_subset = random_df[
        [
            threshold_random,
            tolerance_random,
            observed_random,
            random_mean,
            random_difference,
            random_p,
        ]
    ].copy()

    random_subset.columns = [
        "flow_threshold_cells",
        "tolerance_m",
        "observed_agreement_random_source_pct",
        "random_null_mean_pct",
        "observed_minus_random_null_pct",
        "random_null_empirical_p",
    ]

    terrain_subset = terrain_df[
        [
            threshold_terrain,
            tolerance_terrain,
            observed_terrain,
            terrain_mean,
            terrain_lower,
            terrain_upper,
            terrain_difference,
            terrain_p,
        ]
    ].copy()

    terrain_subset.columns = [
        "flow_threshold_cells",
        "tolerance_m",
        "observed_agreement_terrain_source_pct",
        "terrain_null_mean_pct",
        "terrain_null_2_5_pct",
        "terrain_null_97_5_pct",
        "observed_minus_terrain_null_pct",
        "terrain_null_empirical_p",
    ]

    final = pd.merge(
        random_subset,
        terrain_subset,
        on=[
            "flow_threshold_cells",
            "tolerance_m",
        ],
        how="inner",
        validate="one_to_one",
    )

    if final.empty:
        raise RuntimeError(
            "The random-null and terrain-null tables did not share "
            "matching threshold/tolerance combinations."
        )

    # -------------------------------------------------------------
    # Verify that both analyses used the same observed agreement.
    # Small floating-point differences are acceptable.
    # -------------------------------------------------------------

    final[
        "observed_source_difference_pct"
    ] = (
        final[
            "observed_agreement_random_source_pct"
        ]
        - final[
            "observed_agreement_terrain_source_pct"
        ]
    ).abs()

    max_observed_difference = final[
        "observed_source_difference_pct"
    ].max()

    if max_observed_difference > 0.05:
        raise RuntimeError(
            "Observed agreement differs unexpectedly between the "
            "random-null and terrain-null analyses.\n"
            f"Maximum difference: {max_observed_difference:.4f} "
            "percentage points."
        )

    final[
        "observed_agreement_pct"
    ] = final[
        "observed_agreement_terrain_source_pct"
    ]

    # -------------------------------------------------------------
    # Add useful comparison fields.
    # -------------------------------------------------------------

    final[
        "terrain_null_minus_random_null_pct"
    ] = (
        final[
            "terrain_null_mean_pct"
        ]
        - final[
            "random_null_mean_pct"
        ]
    )

    final[
        "terrain_null_interval_width_pct"
    ] = (
        final[
            "terrain_null_97_5_pct"
        ]
        - final[
            "terrain_null_2_5_pct"
        ]
    )

    # Keep only the final audit-friendly columns.
    final = final[
        [
            "flow_threshold_cells",
            "tolerance_m",
            "observed_agreement_pct",
            "random_null_mean_pct",
            "terrain_null_mean_pct",
            "terrain_null_2_5_pct",
            "terrain_null_97_5_pct",
            "observed_minus_random_null_pct",
            "observed_minus_terrain_null_pct",
            "terrain_null_minus_random_null_pct",
            "random_null_empirical_p",
            "terrain_null_empirical_p",
        ]
    ]

    final = final.sort_values(
        [
            "flow_threshold_cells",
            "tolerance_m",
        ]
    ).reset_index(
        drop=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        OUTPUT_DIR
        / "final_comparison.csv"
    )

    txt_path = (
        OUTPUT_DIR
        / "final_comparison_summary.txt"
    )

    print(
        "Step 4/5: Writing final comparison files..."
    )

    final.to_csv(
        csv_path,
        index=False,
    )

    # -------------------------------------------------------------
    # Plain-language text summary.
    # -------------------------------------------------------------

    lines = []

    lines.append(
        "Yabboq Drainage Validation — Final Comparison"
    )
    lines.append(
        "============================================"
    )
    lines.append("")

    lines.append(
        "This file consolidates the observed drainage/reference "
        "agreement, the simple density-matched random-cell null, "
        "and the terrain-matched null."
    )
    lines.append("")

    lines.append(
        "Terrain-matched controls approximately preserve elevation, "
        "slope, and ruggedness distributions."
    )
    lines.append("")

    lines.append(
        "Neither null preserves complete drainage-network topology."
    )
    lines.append("")

    lines.append(
        "Reference hydrography was used for evaluation rather than "
        "construction of the terrain-derived drainage model."
    )
    lines.append("")

    for threshold in sorted(
        final[
            "flow_threshold_cells"
        ].unique()
    ):

        lines.append(
            f"{int(threshold)}-cell flow threshold"
        )
        lines.append(
            "-" * 32
        )

        subset = final[
            final[
                "flow_threshold_cells"
            ] == threshold
        ]

        for _, row in subset.iterrows():

            lines.append(
                f"{row['tolerance_m']:.0f} m tolerance"
            )

            lines.append(
                "  Observed agreement: "
                + percent(
                    row[
                        "observed_agreement_pct"
                    ]
                )
            )

            lines.append(
                "  Simple random null mean: "
                + percent(
                    row[
                        "random_null_mean_pct"
                    ]
                )
            )

            lines.append(
                "  Terrain-matched null mean: "
                + percent(
                    row[
                        "terrain_null_mean_pct"
                    ]
                )
            )

            lines.append(
                "  Terrain null 95% interval: "
                + percent(
                    row[
                        "terrain_null_2_5_pct"
                    ]
                )
                + " to "
                + percent(
                    row[
                        "terrain_null_97_5_pct"
                    ]
                )
            )

            lines.append(
                "  Observed - random null: "
                + points(
                    row[
                        "observed_minus_random_null_pct"
                    ]
                )
            )

            lines.append(
                "  Observed - terrain null: "
                + points(
                    row[
                        "observed_minus_terrain_null_pct"
                    ]
                )
            )

            lines.append(
                "  Random-null empirical p: "
                + pvalue(
                    row[
                        "random_null_empirical_p"
                    ]
                )
            )

            lines.append(
                "  Terrain-null empirical p: "
                + pvalue(
                    row[
                        "terrain_null_empirical_p"
                    ]
                )
            )

            lines.append("")

    lines.append(
        "Interpretation"
    )
    lines.append(
        "--------------"
    )

    lines.append(
        "Observed terrain-derived drainage agreement exceeds both "
        "the simple density-matched random-cell null and the "
        "terrain-matched null across the tested thresholds and "
        "spatial tolerances."
    )
    lines.append("")

    lines.append(
        "The terrain-matched result indicates that the observed "
        "correspondence is not explained merely by placing the "
        "same number of cells in broadly similar elevation, slope, "
        "and ruggedness conditions."
    )
    lines.append("")

    lines.append(
        "These results are evidence about spatial correspondence "
        "between terrain-derived drainage structure and independent "
        "mapped hydrography."
    )
    lines.append("")

    lines.append(
        "They do not identify an ancient route, establish a "
        "historical itinerary, or demonstrate that the modern "
        "reference hydrography exactly represents ancient channels."
    )
    lines.append("")

    lines.append(
        "A future topology-preserving or network-structured null "
        "would provide a stronger second-stage robustness test."
    )

    txt_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        "Step 5/5: Final audit..."
    )

    print()
    print(
        "SUCCESS"
    )
    print()

    print(
        "Created:"
    )

    print(
        f"  {csv_path}"
    )

    print(
        f"  {txt_path}"
    )

    print()

    print(
        "Observed agreement minus terrain-matched null mean "
        "(percentage points):"
    )

    pivot = final.pivot(
        index="tolerance_m",
        columns="flow_threshold_cells",
        values="observed_minus_terrain_null_pct",
    )

    print(
        pivot.round(2).to_string()
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "This consolidates the first validation cycle."
    )

    print(
        "It does not constitute historical route identification."
    )


if __name__ == "__main__":
    main()