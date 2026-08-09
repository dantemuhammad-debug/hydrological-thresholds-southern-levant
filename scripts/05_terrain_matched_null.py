"""
05_terrain_matched_null.py

Terrain-matched null test for terrain-derived drainage agreement.

Purpose
-------
Compare observed terrain-derived drainage agreement with independent
reference hydrography against randomized control masks that are matched
to the observed drainage cells on:

    - elevation
    - slope
    - terrain ruggedness

This is stronger than the simple density-matched random-cell null because
the control cells occupy similar terrain conditions.

IMPORTANT
---------
The independent reference hydrography is used only for evaluation.
It is NOT used to define terrain bins, select control cells, or generate
the terrain-derived drainage network.

This test preserves:
    - raster extent
    - valid analysis area
    - number of drainage cells
    - approximate elevation distribution
    - approximate slope distribution
    - approximate ruggedness distribution

It does NOT preserve:
    - network connectivity
    - flow topology
    - channel branching structure
    - exact spatial autocorrelation

Therefore this is a stronger matched-terrain null, but it is still not
a topology-preserving drainage-network null.
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

DEM = Path(
    r"..\yabboq_dem_filled.tif"
)

SLOPE = Path(
    r"..\outputs\terrain\slope_degrees.tif"
)

RUGGEDNESS = Path(
    r"..\outputs\terrain\ruggedness_tri.tif"
)

REFERENCE = Path(
    r"..\reference_hydrograph\yabboq_osm_waterways_clip.gpkg"
)

DEFAULT_OUTPUT = Path(
    r"..\outputs\terrain_matched_null"
)

DEFAULT_TOLERANCES = [
    30,
    60,
    90,
    150,
    300,
]


def read_raster(path):
    """
    Read one raster and return:
        data
        valid mask
        profile
        transform
        CRS
    """

    with rasterio.open(path) as src:
        data = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    if nodata is None:
        valid = np.isfinite(data)
    else:
        valid = (
            np.isfinite(data)
            & (data != nodata)
        )

    return (
        data,
        valid,
        profile,
        transform,
        crs,
    )


def verify_alignment(reference_profile, other_profile, label):
    """
    Ensure rasters occupy the same grid.
    """

    keys = [
        "width",
        "height",
        "transform",
        "crs",
    ]

    for key in keys:
        if reference_profile[key] != other_profile[key]:
            raise RuntimeError(
                f"{label} is not aligned with the DEM: {key} differs."
            )


def read_reference(path, target_crs):
    """
    Load independent reference hydrography.
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


def rasterize_reference(reference, shape, transform):
    """
    Rasterize reference waterways to the analysis grid.
    """

    shapes = (
        (geom, 1)
        for geom in reference.geometry
    )

    output = rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
        all_touched=True,
    )

    return output.astype(bool)


def distance_to_mask(mask, transform):
    """
    Euclidean distance in meters.
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
    mask,
    valid,
    distance_to_reference,
    tolerance,
):
    """
    Percentage of mask cells within tolerance
    of reference hydrography.
    """

    total = int(
        np.count_nonzero(
            mask & valid
        )
    )

    if total == 0:
        raise RuntimeError(
            "Mask contains zero valid cells."
        )

    matched = int(
        np.count_nonzero(
            mask
            & valid
            & (
                distance_to_reference
                <= tolerance
            )
        )
    )

    return (
        100.0
        * matched
        / total
    )


def quantile_edges(values, valid_mask, bins):
    """
    Create quantile-based bin edges.
    """

    valid_values = values[
        valid_mask
    ]

    quantiles = np.linspace(
        0,
        1,
        bins + 1,
    )

    edges = np.quantile(
        valid_values,
        quantiles,
    )

    edges = np.unique(
        edges
    )

    if len(edges) < 2:
        raise RuntimeError(
            "Unable to construct terrain bins."
        )

    edges[0] = -np.inf
    edges[-1] = np.inf

    return edges


def bin_array(values, edges):
    """
    Assign integer bin labels.
    """

    return np.digitize(
        values,
        edges[1:-1],
        right=False,
    )


def build_strata(
    elevation,
    slope,
    ruggedness,
    valid,
    bins_per_variable,
):
    """
    Combine elevation, slope, and ruggedness bins
    into one terrain-stratum code per raster cell.
    """

    elev_edges = quantile_edges(
        elevation,
        valid,
        bins_per_variable,
    )

    slope_edges = quantile_edges(
        slope,
        valid,
        bins_per_variable,
    )

    rugged_edges = quantile_edges(
        ruggedness,
        valid,
        bins_per_variable,
    )

    elev_bin = bin_array(
        elevation,
        elev_edges,
    )

    slope_bin = bin_array(
        slope,
        slope_edges,
    )

    rugged_bin = bin_array(
        ruggedness,
        rugged_edges,
    )

    strata = (
        elev_bin
        * bins_per_variable
        * bins_per_variable
        + slope_bin
        * bins_per_variable
        + rugged_bin
    )

    strata = strata.astype(
        np.int32
    )

    strata[
        ~valid
    ] = -1

    return strata


def terrain_matched_random_mask(
    observed,
    valid,
    strata,
    rng,
):
    """
    Generate one terrain-matched control mask.

    For each terrain stratum, sample the same number of
    control cells as observed drainage cells in that stratum.

    Observed drainage cells are excluded from the control pool
    where enough alternatives exist.
    """

    output = np.zeros(
        observed.shape,
        dtype=bool,
    )

    observed_strata = strata[
        observed & valid
    ]

    unique_strata, counts = np.unique(
        observed_strata,
        return_counts=True,
    )

    for stratum, count in zip(
        unique_strata,
        counts,
    ):

        stratum_mask = (
            valid
            & (strata == stratum)
        )

        alternative_pool = np.flatnonzero(
            stratum_mask
            & ~observed
        )

        full_pool = np.flatnonzero(
            stratum_mask
        )

        if len(alternative_pool) >= count:
            pool = alternative_pool
        elif len(full_pool) >= count:
            pool = full_pool
        else:
            raise RuntimeError(
                f"Terrain stratum {stratum} "
                f"contains fewer cells than required."
            )

        chosen = rng.choice(
            pool,
            size=int(count),
            replace=False,
        )

        output.flat[
            chosen
        ] = True

    return output


def empirical_p_value(null_values, observed):
    """
    One-sided empirical p-value.
    """

    exceedances = int(
        np.count_nonzero(
            null_values >= observed
        )
    )

    return (
        exceedances + 1
    ) / (
        len(null_values) + 1
    )


def summarize(
    threshold,
    tolerance,
    observed,
    null_values,
):
    """
    Summarize one scenario/tolerance pair.
    """

    null_mean = float(
        np.mean(
            null_values
        )
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
        "terrain_null_mean_pct": null_mean,
        "terrain_null_std_pct": null_std,
        "terrain_null_2_5_pct": lower,
        "terrain_null_97_5_pct": upper,
        "observed_minus_terrain_null_pct": (
            observed - null_mean
        ),
        "z_score": z_score,
        "empirical_p_value": empirical_p_value(
            null_values,
            observed,
        ),
    }


def write_text_summary(
    results,
    iterations,
    seed,
    bins_per_variable,
    path,
):
    """
    Write plain-language audit summary.
    """

    lines = []

    lines.append(
        "Terrain-Matched Null Test"
    )
    lines.append(
        "========================="
    )
    lines.append("")

    lines.append(
        f"Iterations per scenario: {iterations}"
    )

    lines.append(
        f"Random seed: {seed}"
    )

    lines.append(
        f"Quantile bins per terrain variable: "
        f"{bins_per_variable}"
    )

    lines.append("")

    lines.append(
        "Matching variables:"
    )
    lines.append(
        "  elevation"
    )
    lines.append(
        "  slope"
    )
    lines.append(
        "  terrain ruggedness"
    )
    lines.append("")

    lines.append(
        "IMPORTANT:"
    )
    lines.append(
        "Reference hydrography was not used to construct "
        "terrain strata or select matched control cells."
    )
    lines.append("")

    lines.append(
        "This null preserves approximate terrain distributions "
        "but does not preserve drainage-network topology or "
        "spatial connectivity."
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
                "  Terrain-matched null mean: "
                f"{row['terrain_null_mean_pct']:.2f}%"
            )

            lines.append(
                "  Null 95% interval: "
                f"{row['terrain_null_2_5_pct']:.2f}%"
                " to "
                f"{row['terrain_null_97_5_pct']:.2f}%"
            )

            lines.append(
                "  Observed - terrain null: "
                f"{row['observed_minus_terrain_null_pct']:.2f} "
                "percentage points"
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
        "Interpretation limitation"
    )
    lines.append(
        "-------------------------"
    )

    lines.append(
        "Agreement exceeding this terrain-matched null "
        "would show that observed correspondence is not "
        "explained merely by cells occupying similar "
        "elevation, slope, and ruggedness conditions."
    )

    lines.append(
        "It still would not establish historical claims "
        "or preserve complete drainage-network topology."
    )

    path.write_text(
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
            "Matched-null simulations per threshold."
        ),
    )

    parser.add_argument(
        "--bins",
        type=int,
        default=5,
        help=(
            "Quantile bins per terrain variable. "
            "Default: 5"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20260808,
        help=(
            "Random seed."
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
    )

    args = parser.parse_args()

    if args.iterations < 10:
        raise ValueError(
            "Use at least 10 iterations."
        )

    if args.bins < 2:
        raise ValueError(
            "Use at least 2 terrain bins."
        )

    rng = np.random.default_rng(
        args.seed
    )

    args.out.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "Step 1/5: Reading terrain variables..."
    )

    (
        elevation,
        elev_valid,
        dem_profile,
        transform,
        crs,
    ) = read_raster(
        DEM
    )

    (
        slope,
        slope_valid,
        slope_profile,
        _,
        _,
    ) = read_raster(
        SLOPE
    )

    (
        ruggedness,
        rugged_valid,
        rugged_profile,
        _,
        _,
    ) = read_raster(
        RUGGEDNESS
    )

    verify_alignment(
        dem_profile,
        slope_profile,
        "Slope raster",
    )

    verify_alignment(
        dem_profile,
        rugged_profile,
        "Ruggedness raster",
    )

    terrain_valid = (
        elev_valid
        & slope_valid
        & rugged_valid
    )

    print(
        "Step 2/5: Building terrain strata..."
    )

    strata = build_strata(
        elevation,
        slope,
        ruggedness,
        terrain_valid,
        args.bins,
    )

    print(
        "Step 3/5: Reading independent reference hydrography..."
    )

    reference_gdf = read_reference(
        REFERENCE,
        crs,
    )

    reference_mask = rasterize_reference(
        reference_gdf,
        elevation.shape,
        transform,
    )

    reference_mask &= terrain_valid

    if not np.any(
        reference_mask
    ):
        raise RuntimeError(
            "Reference hydrography does not intersect analysis area."
        )

    distance_to_reference = distance_to_mask(
        reference_mask,
        transform,
    )

    all_rows = []

    print(
        "Step 4/5: Running terrain-matched scenarios..."
    )

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

        (
            drainage_data,
            drainage_valid,
            drainage_profile,
            _,
            _,
        ) = read_raster(
            drainage_path
        )

        verify_alignment(
            dem_profile,
            drainage_profile,
            f"{threshold}-cell drainage raster",
        )

        drainage = (
            drainage_data == 1
        )

        valid = (
            terrain_valid
            & drainage_valid
        )

        drainage &= valid

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

        null_results = {
            tolerance: np.empty(
                args.iterations,
                dtype=np.float32,
            )
            for tolerance
            in args.tolerances
        }

        print(
            f"  Running {args.iterations} "
            "terrain-matched simulations..."
        )

        for iteration in range(
            args.iterations
        ):

            random_mask = terrain_matched_random_mask(
                drainage,
                valid,
                strata,
                rng,
            )

            for tolerance in args.tolerances:

                null_results[
                    tolerance
                ][iteration] = agreement_percentage(
                    random_mask,
                    valid,
                    distance_to_reference,
                    tolerance,
                )

            if (
                iteration == 0
                or (iteration + 1) % 100 == 0
                or iteration + 1 == args.iterations
            ):
                print(
                    f"    completed "
                    f"{iteration + 1}/{args.iterations}"
                )

        for tolerance in args.tolerances:

            row = summarize(
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
                "iterations"
            ] = args.iterations

            row[
                "terrain_bins_per_variable"
            ] = args.bins

            row[
                "seed"
            ] = args.seed

            row[
                "derived_cells_total"
            ] = int(
                np.count_nonzero(
                    drainage
                )
            )

            all_rows.append(
                row
            )

    print()
    print(
        "Step 5/5: Writing results..."
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
        / "terrain_matched_null_results.csv"
    )

    txt_path = (
        args.out
        / "terrain_matched_null_summary.txt"
    )

    results.to_csv(
        csv_path,
        index=False,
    )

    write_text_summary(
        results,
        args.iterations,
        args.seed,
        args.bins,
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
        "Observed agreement minus terrain-matched "
        "null mean (percentage points):"
    )

    pivot = results.pivot(
        index="tolerance_m",
        columns="flow_threshold_cells",
        values="observed_minus_terrain_null_pct",
    )

    print(
        pivot.round(2).to_string()
    )

    print()
    print(
        "IMPORTANT: This is terrain-matched, "
        "not topology-preserving."
    )


if __name__ == "__main__":
    main()