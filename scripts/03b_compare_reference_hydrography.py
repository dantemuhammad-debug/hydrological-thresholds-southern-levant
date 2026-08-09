"""
03b_compare_reference_hydrography.py

Diagnostic comparison between a terrain-derived drainage raster
and an independent reference hydrography vector layer.

This script does NOT modify the terrain-derived model.

It answers questions such as:

- What proportion of derived drainage cells lie within a given
  distance of mapped reference waterways?
- What proportion of mapped reference waterways lie near the
  derived drainage network?
- How does agreement change as the tolerance distance changes?

The comparison is deliberately post-hoc and diagnostic.
Reference hydrography must never be burned into the DEM or used
to create the terrain-derived drainage raster.

Dependencies:
    rasterio
    numpy
    geopandas
    shapely
    scipy

Example:

py 03b_compare_reference_hydrography.py ^
    --derived ..\\outputs\\terrain\\drainage_threshold.tif ^
    --reference ..\\reference_hydrography\\yabboq_osm_waterways_clip.gpkg ^
    --out ..\\outputs\\hydrography_comparison ^
    --tolerances 30 60 90 150 300
"""

import argparse
import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt


def load_derived_drainage(path: Path):
    """
    Load the binary terrain-derived drainage raster.

    Expected values:
        1 = candidate drainage
        0 = background
        nodata = excluded
    """

    with rasterio.open(path) as src:
        data = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    if nodata is None:
        valid = np.ones(data.shape, dtype=bool)
    else:
        valid = data != nodata

    drainage = (data == 1) & valid

    return drainage, valid, profile, transform, crs


def load_reference_waterways(path: Path, target_crs):
    """
    Load the independent reference hydrography layer and reproject
    it to the drainage raster CRS if necessary.
    """

    reference = gpd.read_file(path)

    if reference.empty:
        raise RuntimeError(
            "Reference hydrography contains no features."
        )

    if reference.crs is None:
        raise RuntimeError(
            "Reference hydrography has no CRS defined."
        )

    if reference.crs != target_crs:
        reference = reference.to_crs(target_crs)

    reference = reference[
        reference.geometry.notnull()
        & ~reference.geometry.is_empty
    ].copy()

    if reference.empty:
        raise RuntimeError(
            "No valid reference geometries remain after cleaning."
        )

    return reference


def rasterize_reference(
    reference,
    out_shape,
    transform,
):
    """
    Rasterize reference waterways onto the exact same grid as the
    terrain-derived drainage raster.

    The reference data remain diagnostic only.
    """

    shapes = (
        (geom, 1)
        for geom in reference.geometry
    )

    reference_raster = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
        all_touched=True,
    )

    return reference_raster.astype(bool)


def calculate_distance_to_network(
    network_mask,
    transform,
):
    """
    Calculate Euclidean distance in map units to the nearest
    network cell.

    Since the raster is in EPSG:32636, units are meters.
    """

    xres = abs(transform.a)
    yres = abs(transform.e)

    distance = distance_transform_edt(
        ~network_mask,
        sampling=(yres, xres),
    )

    return distance.astype(np.float32)


def summarize_agreement(
    derived,
    reference,
    valid,
    distance_to_reference,
    distance_to_derived,
    tolerances,
):
    """
    Summarize bidirectional agreement.

    Direction A:
        fraction of derived drainage cells within tolerance
        of reference waterways.

    Direction B:
        fraction of reference waterway cells within tolerance
        of derived drainage.
    """

    derived_count = int(
        np.count_nonzero(derived & valid)
    )

    reference_count = int(
        np.count_nonzero(reference & valid)
    )

    if derived_count == 0:
        raise RuntimeError(
            "Derived drainage raster contains no candidate cells."
        )

    if reference_count == 0:
        raise RuntimeError(
            "Reference waterways do not intersect the raster extent."
        )

    rows = []

    for tolerance in tolerances:

        derived_near_reference = (
            derived
            & valid
            & (distance_to_reference <= tolerance)
        )

        reference_near_derived = (
            reference
            & valid
            & (distance_to_derived <= tolerance)
        )

        derived_matches = int(
            np.count_nonzero(
                derived_near_reference
            )
        )

        reference_matches = int(
            np.count_nonzero(
                reference_near_derived
            )
        )

        rows.append(
            {
                "tolerance_m": float(tolerance),
                "derived_cells_total": derived_count,
                "derived_cells_near_reference": derived_matches,
                "derived_agreement_pct": (
                    100.0
                    * derived_matches
                    / derived_count
                ),
                "reference_cells_total": reference_count,
                "reference_cells_near_derived": reference_matches,
                "reference_agreement_pct": (
                    100.0
                    * reference_matches
                    / reference_count
                ),
            }
        )

    return rows


def write_csv(
    rows,
    path: Path,
):
    """
    Write the comparison table.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "tolerance_m",
        "derived_cells_total",
        "derived_cells_near_reference",
        "derived_agreement_pct",
        "reference_cells_total",
        "reference_cells_near_derived",
        "reference_agreement_pct",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_distance_raster(
    path: Path,
    data,
    profile,
):
    """
    Write a float32 diagnostic distance raster.
    """

    output_profile = profile.copy()

    output_profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=-9999.0,
        compress="lzw",
    )

    output = data.astype(
        np.float32
    ).copy()

    output[
        ~np.isfinite(output)
    ] = -9999.0

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with rasterio.open(
        path,
        "w",
        **output_profile,
    ) as dst:

        dst.write(
            output,
            1,
        )


def write_text_summary(
    rows,
    derived_path,
    reference_path,
    path: Path,
):
    """
    Write a plain-language diagnostic summary.
    """

    lines = []

    lines.append(
        "Reference Hydrography Diagnostic Comparison"
    )
    lines.append(
        "=========================================="
    )
    lines.append("")

    lines.append(
        f"Derived drainage: {derived_path}"
    )
    lines.append(
        f"Reference hydrography: {reference_path}"
    )
    lines.append("")

    lines.append(
        "IMPORTANT:"
    )
    lines.append(
        "This comparison is diagnostic only."
    )
    lines.append(
        "Reference hydrography was not used to create "
        "the terrain-derived drainage network."
    )
    lines.append("")

    lines.append(
        "Agreement by tolerance:"
    )
    lines.append("")

    for row in rows:

        lines.append(
            f"{row['tolerance_m']:.0f} m tolerance"
        )

        lines.append(
            "  Derived drainage near reference: "
            f"{row['derived_agreement_pct']:.2f}%"
        )

        lines.append(
            "  Reference hydrography near derived: "
            f"{row['reference_agreement_pct']:.2f}%"
        )

        lines.append("")

    lines.append(
        "Interpretation note:"
    )
    lines.append(
        "Higher agreement at larger tolerances is expected. "
        "The meaningful question is how agreement behaves "
        "across multiple drainage-threshold scenarios and "
        "whether observed correspondence exceeds what would "
        "be expected by chance or by generic terrain structure."
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
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
        "--derived",
        required=True,
        type=Path,
        help=(
            "Binary terrain-derived drainage raster."
        ),
    )

    parser.add_argument(
        "--reference",
        required=True,
        type=Path,
        help=(
            "Independent reference hydrography "
            "GeoPackage."
        ),
    )

    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help=(
            "Output directory for diagnostic "
            "comparison results."
        ),
    )

    parser.add_argument(
        "--tolerances",
        nargs="+",
        type=float,
        default=[
            30,
            60,
            90,
            150,
            300,
        ],
        help=(
            "Distance tolerances in meters."
        ),
    )

    args = parser.parse_args()

    print(
        "Step 1/5: Loading terrain-derived drainage..."
    )

    (
        derived,
        valid,
        profile,
        transform,
        crs,
    ) = load_derived_drainage(
        args.derived
    )

    print(
        "Step 2/5: Loading independent reference hydrography..."
    )

    reference_gdf = load_reference_waterways(
        args.reference,
        crs,
    )

    print(
        "Step 3/5: Rasterizing reference hydrography..."
    )

    reference = rasterize_reference(
        reference_gdf,
        derived.shape,
        transform,
    )

    reference &= valid

    print(
        "Step 4/5: Calculating network distances..."
    )

    distance_to_reference = (
        calculate_distance_to_network(
            reference,
            transform,
        )
    )

    distance_to_derived = (
        calculate_distance_to_network(
            derived,
            transform,
        )
    )

    print(
        "Step 5/5: Summarizing agreement..."
    )

    rows = summarize_agreement(
        derived,
        reference,
        valid,
        distance_to_reference,
        distance_to_derived,
        args.tolerances,
    )

    args.out.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        args.out
        / "hydrography_agreement.csv"
    )

    summary_path = (
        args.out
        / "hydrography_agreement_summary.txt"
    )

    distance_reference_path = (
        args.out
        / "distance_to_reference_waterways.tif"
    )

    distance_derived_path = (
        args.out
        / "distance_to_derived_drainage.tif"
    )

    write_csv(
        rows,
        csv_path,
    )

    write_text_summary(
        rows,
        args.derived,
        args.reference,
        summary_path,
    )

    write_distance_raster(
        distance_reference_path,
        distance_to_reference,
        profile,
    )

    write_distance_raster(
        distance_derived_path,
        distance_to_derived,
        profile,
    )

    print()
    print("SUCCESS")
    print()

    print(
        "Diagnostic comparison written to:"
    )
    print(args.out)
    print()

    print("Created:")
    print(
        "  hydrography_agreement.csv"
    )
    print(
        "  hydrography_agreement_summary.txt"
    )
    print(
        "  distance_to_reference_waterways.tif"
    )
    print(
        "  distance_to_derived_drainage.tif"
    )
    print()

    print(
        "Agreement:"
    )

    for row in rows:

        print(
            f"  {row['tolerance_m']:.0f} m: "
            f"derived->reference "
            f"{row['derived_agreement_pct']:.2f}% | "
            f"reference->derived "
            f"{row['reference_agreement_pct']:.2f}%"
        )

    print()
    print(
        "IMPORTANT: These values are diagnostics, "
        "not evidence of historical support by themselves."
    )


if __name__ == "__main__":
    main()