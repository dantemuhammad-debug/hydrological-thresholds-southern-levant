"""
03c_summarize_threshold_sweep.py

Combines hydrography agreement results from multiple structural
drainage-threshold scenarios into one comparison table.

This script does not modify any terrain or hydrography data.
It only reads the CSV outputs produced by
03b_compare_reference_hydrography.py and summarizes them.

Expected scenarios:
    250 cells
    500 cells
    1000 cells

Outputs:
    threshold_sweep_summary.csv
    threshold_sweep_summary.txt
"""

from pathlib import Path
import pandas as pd


SCENARIOS = {
    250: Path(r"..\outputs\hydrography_comparison_250\hydrography_agreement.csv"),
    500: Path(r"..\outputs\hydrography_comparison\hydrography_agreement.csv"),
    1000: Path(r"..\outputs\hydrography_comparison_1000\hydrography_agreement.csv"),
}

OUTPUT_DIR = Path(r"..\outputs\threshold_sweep_summary")


def load_scenario(threshold, path):
    """
    Load one hydrography agreement CSV and label every row
    with its structural drainage threshold.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Missing scenario file for threshold {threshold}: {path}"
        )

    df = pd.read_csv(path)

    required_columns = {
        "tolerance_m",
        "derived_cells_total",
        "derived_cells_near_reference",
        "derived_agreement_pct",
        "reference_cells_total",
        "reference_cells_near_derived",
        "reference_agreement_pct",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Scenario {threshold} is missing columns: {sorted(missing)}"
        )

    df.insert(0, "flow_threshold_cells", threshold)

    return df


def build_summary():
    """
    Combine all structural scenarios into one long-form table.
    """

    frames = []

    for threshold, path in SCENARIOS.items():
        print(f"Reading {threshold}-cell scenario...")
        frames.append(load_scenario(threshold, path))

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined = combined.sort_values(
        ["tolerance_m", "flow_threshold_cells"]
    ).reset_index(drop=True)

    return combined


def build_pivot_table(combined):
    """
    Create a human-readable side-by-side table showing agreement
    percentages by tolerance and threshold.
    """

    derived = combined.pivot(
        index="tolerance_m",
        columns="flow_threshold_cells",
        values="derived_agreement_pct",
    )

    reference = combined.pivot(
        index="tolerance_m",
        columns="flow_threshold_cells",
        values="reference_agreement_pct",
    )

    return derived, reference


def write_text_summary(
    combined,
    derived_pivot,
    reference_pivot,
    out_path,
):
    """
    Write a plain-language summary suitable for audit/review.
    """

    lines = []

    lines.append("Structural Drainage-Threshold Sweep")
    lines.append("===================================")
    lines.append("")

    lines.append(
        "This file summarizes diagnostic hydrography agreement "
        "for the 250-, 500-, and 1000-cell structural scenarios."
    )
    lines.append("")

    lines.append(
        "IMPORTANT: These values are not evidence of historical "
        "support by themselves. They diagnose how reference "
        "agreement changes as drainage-network density changes."
    )
    lines.append("")

    lines.append("Derived drainage -> reference hydrography (%)")
    lines.append("---------------------------------------------")
    lines.append(
        derived_pivot.round(2).to_string()
    )
    lines.append("")

    lines.append("Reference hydrography -> derived drainage (%)")
    lines.append("---------------------------------------------")
    lines.append(
        reference_pivot.round(2).to_string()
    )
    lines.append("")

    lines.append("Interpretation")
    lines.append("--------------")
    lines.append(
        "Lower flow-accumulation thresholds create denser derived "
        "drainage networks. Denser networks generally increase the "
        "chance that mapped reference waterways fall near some "
        "derived drainage cell."
    )
    lines.append("")
    lines.append(
        "Higher thresholds create sparser networks. These may show "
        "higher derived-to-reference agreement simply because only "
        "the strongest terrain-defined channels remain."
    )
    lines.append("")
    lines.append(
        "Therefore, raw agreement percentages alone cannot identify "
        "an optimal threshold. The next methodological step is to "
        "compare observed agreement against a null/background "
        "expectation that accounts for network density."
    )

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    out_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():

    print("Step 1/3: Loading threshold scenarios...")

    combined = build_summary()

    print("Step 2/3: Building comparison tables...")

    derived_pivot, reference_pivot = build_pivot_table(
        combined
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        OUTPUT_DIR
        / "threshold_sweep_summary.csv"
    )

    txt_path = (
        OUTPUT_DIR
        / "threshold_sweep_summary.txt"
    )

    combined.to_csv(
        csv_path,
        index=False,
    )

    print("Step 3/3: Writing summary...")

    write_text_summary(
        combined,
        derived_pivot,
        reference_pivot,
        txt_path,
    )

    print()
    print("SUCCESS")
    print()
    print("Created:")
    print(f"  {csv_path}")
    print(f"  {txt_path}")
    print()

    print("Derived drainage -> reference hydrography (%)")
    print(
        derived_pivot.round(2).to_string()
    )
    print()

    print("Reference hydrography -> derived drainage (%)")
    print(
        reference_pivot.round(2).to_string()
    )
    print()

    print(
        "IMPORTANT: This sweep diagnoses threshold sensitivity. "
        "It does not select a preferred threshold."
    )


if __name__ == "__main__":
    main()