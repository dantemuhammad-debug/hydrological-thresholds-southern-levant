"""
07_plot_final_comparison.py

Create final comparison figures for the Yabboq drainage-validation workflow.

For each flow-accumulation threshold, plot:

    - observed drainage/reference agreement
    - simple random-cell expectation
    - terrain-matched expectation
    - terrain-matched 95% interval

Outputs
-------
One PNG and one SVG figure for each threshold:

    final_comparison_threshold_250.png
    final_comparison_threshold_250.svg

    final_comparison_threshold_500.png
    final_comparison_threshold_500.svg

    final_comparison_threshold_1000.png
    final_comparison_threshold_1000.svg

IMPORTANT
---------
These figures summarize spatial agreement only.

They do not identify an ancient route or establish a historical itinerary.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------
# INPUT / OUTPUT
# ---------------------------------------------------------------------

INPUT_CSV = Path(
    r"..\outputs\final_comparison\final_comparison.csv"
)

OUTPUT_DIR = Path(
    r"..\outputs\final_comparison\figures"
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def require_file(path):
    """
    Confirm that the consolidated comparison table exists.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Input file was not found:\n{path}"
        )


def verify_columns(df):
    """
    Confirm required columns exist before plotting.
    """

    required = [
        "flow_threshold_cells",
        "tolerance_m",
        "observed_agreement_pct",
        "random_null_mean_pct",
        "terrain_null_mean_pct",
        "terrain_null_2_5_pct",
        "terrain_null_97_5_pct",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise KeyError(
            "Required columns are missing:\n"
            f"{missing}\n\n"
            "Available columns are:\n"
            f"{list(df.columns)}"
        )


def make_figure(df, threshold):
    """
    Create one standalone figure for one flow threshold.
    """

    subset = df[
        df[
            "flow_threshold_cells"
        ] == threshold
    ].copy()

    subset = subset.sort_values(
        "tolerance_m"
    )

    if subset.empty:
        raise RuntimeError(
            f"No rows found for threshold {threshold}."
        )

    x = subset[
        "tolerance_m"
    ]

    observed = subset[
        "observed_agreement_pct"
    ]

    random_null = subset[
        "random_null_mean_pct"
    ]

    terrain_null = subset[
        "terrain_null_mean_pct"
    ]

    terrain_lower = subset[
        "terrain_null_2_5_pct"
    ]

    terrain_upper = subset[
        "terrain_null_97_5_pct"
    ]

    lower_error = (
        terrain_null
        - terrain_lower
    )

    upper_error = (
        terrain_upper
        - terrain_null
    )

    terrain_error = [
        lower_error,
        upper_error,
    ]

    # -------------------------------------------------------------
    # Create standalone plot.
    # -------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(8.5, 5.5)
    )

    ax.plot(
        x,
        observed,
        marker="o",
        linewidth=2,
        label="Observed drainage",
    )

    ax.plot(
        x,
        random_null,
        marker="o",
        linewidth=2,
        label="Random-cell expectation",
    )

    ax.errorbar(
        x,
        terrain_null,
        yerr=terrain_error,
        marker="o",
        linewidth=2,
        capsize=4,
        label="Terrain-matched expectation (95% interval)",
    )

    ax.set_title(
        f"Yabboq Drainage Validation — "
        f"{int(threshold)}-Cell Threshold"
    )

    ax.set_xlabel(
        "Spatial tolerance (meters)"
    )

    ax.set_ylabel(
        "Agreement with reference hydrography (%)"
    )

    ax.set_xticks(
        x
    )

    ax.set_ylim(
        bottom=0
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend()

    fig.tight_layout()

    png_path = (
        OUTPUT_DIR
        / f"final_comparison_threshold_{int(threshold)}.png"
    )

    svg_path = (
        OUTPUT_DIR
        / f"final_comparison_threshold_{int(threshold)}.svg"
    )

    fig.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        svg_path,
        bbox_inches="tight",
    )

    plt.close(
        fig
    )

    return (
        png_path,
        svg_path,
    )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print(
        "Step 1/4: Checking consolidated comparison table..."
    )

    require_file(
        INPUT_CSV
    )

    print(
        "Step 2/4: Reading comparison data..."
    )

    df = pd.read_csv(
        INPUT_CSV
    )

    verify_columns(
        df
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    thresholds = sorted(
        df[
            "flow_threshold_cells"
        ].unique()
    )

    print(
        "Step 3/4: Creating figures..."
    )

    created_files = []

    for threshold in thresholds:

        print(
            f"  Plotting {int(threshold)}-cell threshold..."
        )

        png_path, svg_path = make_figure(
            df,
            threshold,
        )

        created_files.extend(
            [
                png_path,
                svg_path,
            ]
        )

    print(
        "Step 4/4: Final audit..."
    )

    print()
    print(
        "SUCCESS"
    )
    print()

    print(
        "Created:"
    )

    for path in created_files:
        print(
            f"  {path}"
        )

    print()
    print(
        "Interpretation reminder:"
    )

    print(
        "Observed agreement is compared with both random-cell "
        "and terrain-matched expectations."
    )

    print(
        "The terrain-matched 95% interval is shown as error bars."
    )

    print(
        "These figures summarize spatial correspondence, not "
        "historical route identification."
    )


if __name__ == "__main__":
    main()