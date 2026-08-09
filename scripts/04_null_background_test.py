"""
04_null_background_test.py

First-pass null/background test for terrain-derived drainage agreement.

Purpose
-------
Compare observed terrain-derived drainage agreement with independent
reference hydrography against randomized drainage masks containing the
same number of cells.

IMPORTANT
---------
This is a density-matched random-cell null model only.

It DOES preserve:
    - raster extent
    - valid analysis area
    - number of derived drainage cells

It DOES NOT preserve:
    - drainage-network connectivity
    - slope distribution
    - elevation distribution
    - terrain class
    - valley/ridge position
    - flow topology

Therefore, this is a preliminary inferential diagnostic, not the final
terrain-matched control framework described in the preregistration.

Inputs
------
Three terrain-derived drainage scenarios:
    250 cells
    500 cells
    1000 cells

Independent reference hydrography:
    clipped OSM waterways

Outputs
-------
For each threshold and tolerance:
    observed agreement
    null mean
    null standard deviation
    null percentile interval
    empirical p-value
    standardized effect size

Dependencies:
    numpy
    pandas
    rasterio
    geopandas
    scipy
"""

from pathlib import Path
import argparse

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt


SCENARIOS = {
    250: Path(r"..\outputs\terrain_250\drainage_threshold.tif"),
    500: Path(r"..\outputs\terrain\drainage_threshold.tif"),
    1000: Path(r"..\outputs\terrain_1000\drainage_threshold.tif"),
}

REFERENCE = Path(
    r"..\reference_hydrograph\yabboq_osm_waterways_clip.gpkg"
)

DEFAULT_OUTPUT = Path(
    r"..\outputs\null_background_test"
)

DEFAULT_TOLERANCES = [
    30,
    60,
    90,
    150,
    300,
]


def read_drainage(path):
    """
    Read a binary drainage raster.

    Returns:
        drainage mask
        valid-data mask
        raster profile
        raster transform
        raster CRS
    """

    with rasterio.open(path) as src:
        data = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    if nodata is None:
        valid = np.ones(
            data.shape,
            dtype=bool,
        )
    else:
        valid = data != nodata

    drainage = (
        (data == 1)
        & valid
    )

    return (
        drainage,
        valid,
        profile,
        transform,
        crs,
    )


def read_reference(
    path,
    target_crs,
):
    """
    Load independent reference hydrography
    and project it to the drainage raster CRS.
    """

    reference = gpd.read_file(path)

    if reference.empty:
        raise RuntimeError(
            "Reference hydrography contains no features."
        )

    if reference.crs is None:
        raise RuntimeError(
            "Reference hydrography has no CRS."
        )

    if reference.crs != target_crs:
        reference = reference.to_crs(
            target_crs
        )

    reference = reference[
        reference.geometry.notna()
        & ~reference.geometry.is_empty
    ].copy()

    if reference.empty:
        raise RuntimeError(
            "No valid reference geometries remain."
        )

    return reference


def rasterize_reference(
    reference,
    shape,
    transform,
):
    """
    Rasterize reference waterways onto
    the exact analysis grid.
    """

    shapes = (
        (geom, 1)
        for geom in reference.geometry
    )

    raster = rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
        all_touched=True,
    )

    return raster.astype(bool)


def distance_to_mask(
    mask,
    transform,
):
    """
    Euclidean distance in raster map units.

    EPSG:32636 uses meters.
    """

    xres = abs(transform.a)
    yres = abs(transform.e)

    return distance_transform_edt(
        ~mask,
        sampling=(
            yres,
            xres,
        ),
    ).astype(
        np.float32
    )


def agreement_percentage(
    drainage,
    valid,
    distance_to_reference,
    tolerance,
):
    """
    Percentage of derived drainage cells
    lying within tolerance of reference hydrography.
    """

    total = np.count_nonzero(
        drainage & valid
    )

    if total == 0:
        raise RuntimeError(
            "Drainage mask contains zero cells."
        )

    matched = np.count_nonzero(
        drainage
        & valid
        & (
            distance_to_reference
            <= tolerance
        )
    )

    return (
        100.0
        * matched
        / total
    )


def generate_random_mask(
    valid_indices,
    shape,
    cell_count,
    rng,
):
    """
    Generate a random drainage mask with
    exactly the same number of cells as
    the observed drainage mask.
    """

    chosen = rng.choice(
        valid_indices,
        size=cell_count,
        replace=False,
    )

    mask = np.zeros(
        shape,
        dtype=bool,
    )

    mask.flat[
        chosen
    ] = True

    return mask


def empirical_p_value(
    null_values,
    observed,
):
    """
    One-sided empirical p-value:
    probability that null agreement
    is at least as large as observed.
    """

    exceedances = np.count_nonzero(
        null_values >= observed
    )

    return (
        exceedances + 1
    ) / (
        len(null_values) + 1
    )


def summarize_null(
    threshold,
    tolerance,
    observed,
    null_values,
):
    """
    Summarize one threshold/tolerance pair.
    """

    null_mean = float(
        np.mean(null_values)
    )

    null_std = float(
        np.std(
            null_values,
            ddof=1,
        )
    )

    lower = float(
        np.percentile(
            null_values,
            2.5,
        )
    )

    upper = float(
        np.percentile(
            null_values,
            97.5,
        )
    )

    p_value = empirical_p_value(
        null_values,
        observed,
    )

    if null_std > 0:
        z_score = (
            observed - null_mean
        ) / null_std
    else:
        z_score = np.nan

    return {
        "flow_threshold_cells": threshold,
        "tolerance_m": tolerance,
        "observed_agreement_pct": observed,
        "null_mean_pct": null_mean,
        "null_std_pct": null_std,
        "null_2_5_pct": lower,
        "null_97_5_pct": upper,
        "observed_minus_null_pct": (
            observed - null_mean
        ),
        "z_score": z_score,
        "empirical_p_value": p_value,
    }


def write_text_summary(
    results,
    iterations,
    seed,
    out_path,
):
    """
    Write an auditable plain-text summary.
    """

    lines = []

    lines.append(
        "Density-Matched Random-Cell Null Test"
    )
    lines.append(
        "====================================="
    )
    lines.append("")

    lines.append(
        f"Random iterations per scenario: {iterations}"
    )
    lines.append(
        f"Random seed: {seed}"
    )
    lines.append("")

    lines.append(
        "IMPORTANT METHODOLOGICAL LIMITATION"
    )
    lines.append(
        "------------------------------------"
    )
    lines.append(
        "This first-pass null preserves only drainage-cell density "
        "within the valid raster area."
    )
    lines.append(
        "It does not preserve network connectivity, flow topology, "
        "slope, elevation, terrain class, or valley position."
    )
    lines.append(
        "Therefore it is a preliminary diagnostic and must not be "
        "treated as the final matched-control test."
    )
    lines.append("")

    for threshold in sorted(
        results[
            "flow_threshold_cells"
        ].unique()
    ):

        lines.append(
            f"{threshold}-cell threshold"
        )
        lines.append(
            "-" * 30
        )

        subset = results[
            results[
                "flow_threshold_cells"
            ] == threshold
        ]

        for _, row in subset.iterrows():

            lines.append(
                f"{row['tolerance_m']:.0f} m tolerance"
            )

            lines.append(
                "  Observed agreement: "
                f"{row['observed_agreement_pct']:.2f}%"
            )

            lines.append(
                "  Null mean: "
                f"{row['null_mean_pct']:.2f}%"
            )

            lines.append(
                "  Null 95% interval: "
                f"{row['null_2_5_pct']:.2f}%"
                " to "
                f"{row['null_97_5_pct']:.2f}%"
            )

            lines.append(
                "  Observed - null: "
                f"{row['observed_minus_null_pct']:.2f} percentage points"
            )

            lines.append(
                "  z-score: "
                f"{row['z_score']:.2f}"
            )

            lines.append(
                "  empirical p-value: "
                f"{row['empirical_p_value']:.4f}"
            )

            lines.append("")

    lines.append(
        "Interpretation rule"
    )
    lines.append(
        "-------------------"
    )
    lines.append(
        "Observed agreement exceeding this simple random-cell null "
        "only shows that the derived network performs better than "
        "randomly scattered cells of equal density."
    )
    lines.append(
        "It does not yet show that the agreement exceeds what would "
        "be expected from generic terrain structure."
    )
    lines.append(
        "A terrain-matched or topology-preserving null remains required "
        "for the stronger methodological claim."
    )

    out_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=500,
        help=(
            "Random simulations per threshold. "
            "Default: 500"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20260808,
        help=(
            "Random seed for reproducibility."
        ),
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Output directory."
        ),
    )

    parser.add_argument(
        "--tolerances",
        nargs="+",
        type=float,
        default=DEFAULT_TOLERANCES,
        help=(
            "Distance tolerances in meters."
        ),
    )

    args = parser.parse_args()

    if args.iterations < 10:
        raise ValueError(
            "Use at least 10 null iterations."
        )

    rng = np.random.default_rng(
        args.seed
    )

    args.out.mkdir(
        parents=True,
        exist_ok=True,
    )

    all_rows = []

    reference_gdf = None

    for scenario_number, (
        threshold,
        drainage_path,
    ) in enumerate(
        SCENARIOS.items(),
        start=1,
    ):

        print()
        print(
            f"Scenario {scenario_number}/3: "
            f"{threshold}-cell threshold"
        )

        print(
            "  Step 1/4: Reading drainage raster..."
        )

        (
            drainage,
            valid,
            profile,
            transform,
            crs,
        ) = read_drainage(
            drainage_path
        )

        if reference_gdf is None:

            print(
                "  Step 2/4: Reading reference hydrography..."
            )

            reference_gdf = read_reference(
                REFERENCE,
                crs,
            )

        else:

            print(
                "  Step 2/4: Reusing reference hydrography..."
            )

        reference_mask = rasterize_reference(
            reference_gdf,
            drainage.shape,
            transform,
        )

        reference_mask &= valid

        if not np.any(
            reference_mask
        ):
            raise RuntimeError(
                "Reference hydrography does not intersect analysis raster."
            )

        print(
            "  Step 3/4: Calculating observed agreement..."
        )

        distance_to_reference = (
            distance_to_mask(
                reference_mask,
                transform,
            )
        )

        observed_by_tolerance = {}

        for tolerance in args.tolerances:

            observed_by_tolerance[
                tolerance
            ] = agreement_percentage(
                drainage,
                valid,
                distance_to_reference,
                tolerance,
            )

        print(
            f"  Step 4/4: Running {args.iterations} "
            "density-matched null simulations..."
        )

        valid_indices = np.flatnonzero(
            valid
        )

        observed_cell_count = int(
            np.count_nonzero(
                drainage
            )
        )

        if (
            observed_cell_count
            > len(valid_indices)
        ):
            raise RuntimeError(
                "Observed drainage has more cells than valid raster area."
            )

        null_results = {
            tolerance: np.empty(
                args.iterations,
                dtype=np.float32,
            )
            for tolerance
            in args.tolerances
        }

        for iteration in range(
            args.iterations
        ):

            random_mask = generate_random_mask(
                valid_indices,
                drainage.shape,
                observed_cell_count,
                rng,
            )

            for tolerance in args.tolerances:

                null_results[
                    tolerance
                ][
                    iteration
                ] = agreement_percentage(
                    random_mask,
                    valid,
                    distance_to_reference,
                    tolerance,
                )

            if (
                (iteration + 1) % 100 == 0
                or iteration == 0
                or iteration + 1 == args.iterations
            ):
                print(
                    f"    completed "
                    f"{iteration + 1}/{args.iterations}"
                )

        for tolerance in args.tolerances:

            row = summarize_null(
                threshold,
                tolerance,
                observed_by_tolerance[
                    tolerance
                ],
                null_results[
                    tolerance
                ],
            )

            row[
                "derived_cells_total"
            ] = observed_cell_count

            row[
                "valid_cells_total"
            ] = int(
                np.count_nonzero(
                    valid
                )
            )

            row[
                "iterations"
            ] = args.iterations

            row[
                "seed"
            ] = args.seed

            all_rows.append(
                row
            )

    results = pd.DataFrame(
        all_rows
    )

    results = results.sort_values(
        [
            "flow_threshold_cells",
            "tolerance_m",
        ]
    ).reset_index(
        drop=True
    )

    csv_path = (
        args.out
        / "null_background_results.csv"
    )

    txt_path = (
        args.out
        / "null_background_summary.txt"
    )

    results.to_csv(
        csv_path,
        index=False,
    )

    write_text_summary(
        results,
        args.iterations,
        args.seed,
        txt_path,
    )

    print()
    print("SUCCESS")
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
        "Observed agreement minus null mean "
        "(percentage points):"
    )

    pivot = results.pivot(
        index="tolerance_m",
        columns="flow_threshold_cells",
        values="observed_minus_null_pct",
    )

    print(
        pivot.round(2).to_string()
    )

    print()
    print(
        "IMPORTANT: This is a density-matched "
        "random-cell null only."
    )
    print(
        "It is not yet the final terrain-matched "
        "control model."
    )


if __name__ == "__main__":
    main()