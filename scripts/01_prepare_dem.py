"""
01_prepare_dem.py

Prepare the Yabboq / Wadi Zerka DEM for terrain and hydrological analysis.

This script:

1. Opens and merges the SRTM tiles.
2. Clips them to a working study-area bounding box.
3. Reprojects the DEM to UTM Zone 36N (EPSG:32636).
4. Fills sinks/depressions using an auditable priority-flood algorithm.
5. Writes the resulting filled DEM as a GeoTIFF.

Required packages:
    rasterio
    numpy
    scipy
    pyyaml

Example command:

py 01_prepare_dem.py --tiles ..\\dem_raw\\N32E035.hgt ..\\dem_raw\\N32E036.hgt --bbox 35.5 31.9 36.2 32.3 --out ..\\outputs\\yabboq_dem_filled.tif
"""

import argparse
import heapq
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge as rio_merge
from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling,
)
from rasterio.windows import from_bounds


TARGET_CRS = "EPSG:32636"


def load_and_merge_tiles(tile_paths):
    """
    Open one or more SRTM .hgt tiles and merge them into one DEM.
    """

    datasets = [rasterio.open(path) for path in tile_paths]

    try:
        mosaic, out_transform = rio_merge(datasets)

        profile = datasets[0].profile.copy()

        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=out_transform,
            count=1,
        )

        return mosaic[0], profile

    finally:
        for dataset in datasets:
            dataset.close()


def clip_to_bbox(array, profile, bbox):
    """
    Clip the DEM to west, south, east, north.

    Bounding-box coordinates are in the source CRS.
    SRTM data are expected to use WGS84 geographic coordinates.
    """

    west, south, east, north = bbox
    transform = profile["transform"]

    window = from_bounds(
        west,
        south,
        east,
        north,
        transform=transform,
    )

    window = window.round_offsets().round_lengths()

    row_start = max(int(window.row_off), 0)
    col_start = max(int(window.col_off), 0)

    row_stop = min(
        row_start + int(window.height),
        array.shape[0],
    )

    col_stop = min(
        col_start + int(window.width),
        array.shape[1],
    )

    if row_stop <= row_start or col_stop <= col_start:
        raise ValueError(
            "The requested bounding box does not overlap the DEM tiles."
        )

    clipped = array[
        row_start:row_stop,
        col_start:col_stop,
    ]

    clipped_window = rasterio.windows.Window(
        col_start,
        row_start,
        col_stop - col_start,
        row_stop - row_start,
    )

    new_transform = rasterio.windows.transform(
        clipped_window,
        transform,
    )

    new_profile = profile.copy()

    new_profile.update(
        height=clipped.shape[0],
        width=clipped.shape[1],
        transform=new_transform,
    )

    return clipped, new_profile


def reproject_to_metric(
    array,
    profile,
    target_crs=TARGET_CRS,
):
    """
    Reproject the DEM into UTM Zone 36N.

    Metric coordinates are needed for downstream slope,
    distance, and corridor calculations.
    """

    src_crs = profile["crs"]

    if src_crs is None:
        src_crs = "EPSG:4326"

    src_nodata = profile.get("nodata")

    if src_nodata is None:
        src_nodata = -32768

    bounds = rasterio.transform.array_bounds(
        profile["height"],
        profile["width"],
        profile["transform"],
    )

    transform, width, height = calculate_default_transform(
        src_crs,
        target_crs,
        profile["width"],
        profile["height"],
        *bounds,
    )

    dst_nodata = -9999.0

    dst_array = np.full(
        (height, width),
        dst_nodata,
        dtype=np.float32,
    )

    reproject(
        source=array,
        destination=dst_array,
        src_transform=profile["transform"],
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=transform,
        dst_crs=target_crs,
        dst_nodata=dst_nodata,
        resampling=Resampling.bilinear,
    )

    new_profile = profile.copy()

    new_profile.update(
        driver="GTiff",
        crs=target_crs,
        transform=transform,
        width=width,
        height=height,
        dtype="float32",
        nodata=dst_nodata,
        count=1,
    )

    return dst_array, new_profile


def fill_sinks(dem, nodata_value=None):
    """
    Fill depressions using a priority-flood algorithm.

    The algorithm starts at valid raster-edge cells and moves inward,
    raising enclosed low cells only as much as necessary to create a
    drainage path toward the boundary.
    """

    filled = dem.astype(np.float64).copy()

    rows, cols = filled.shape

    visited = np.zeros(
        filled.shape,
        dtype=bool,
    )

    if nodata_value is not None:
        nodata_mask = np.isclose(
            dem,
            nodata_value,
        )
    else:
        nodata_mask = np.isnan(dem)

    heap = []

    # Top and bottom edges.
    for col in range(cols):
        for row in (0, rows - 1):

            if (
                not nodata_mask[row, col]
                and not visited[row, col]
            ):
                heapq.heappush(
                    heap,
                    (
                        float(filled[row, col]),
                        row,
                        col,
                    ),
                )

                visited[row, col] = True

    # Left and right edges.
    for row in range(rows):
        for col in (0, cols - 1):

            if (
                not nodata_mask[row, col]
                and not visited[row, col]
            ):
                heapq.heappush(
                    heap,
                    (
                        float(filled[row, col]),
                        row,
                        col,
                    ),
                )

                visited[row, col] = True

    neighbors = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]

    while heap:

        elevation, row, col = heapq.heappop(heap)

        for drow, dcol in neighbors:

            new_row = row + drow
            new_col = col + dcol

            if not (
                0 <= new_row < rows
                and 0 <= new_col < cols
            ):
                continue

            if visited[new_row, new_col]:
                continue

            if nodata_mask[new_row, new_col]:
                continue

            visited[new_row, new_col] = True

            if filled[new_row, new_col] < elevation:
                filled[new_row, new_col] = elevation

            heapq.heappush(
                heap,
                (
                    float(filled[new_row, new_col]),
                    new_row,
                    new_col,
                ),
            )

    if nodata_value is not None:
        filled[nodata_mask] = nodata_value

    return filled.astype(np.float32)


def main():

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--tiles",
        required=True,
        nargs="+",
        type=Path,
        help=(
            "SRTM .hgt files, for example "
            "..\\dem_raw\\N32E035.hgt "
            "..\\dem_raw\\N32E036.hgt"
        ),
    )

    parser.add_argument(
        "--bbox",
        required=True,
        nargs=4,
        type=float,
        metavar=(
            "WEST",
            "SOUTH",
            "EAST",
            "NORTH",
        ),
        help=(
            "Working bounding box in longitude/latitude. "
            "Example: 35.5 31.9 36.2 32.3"
        ),
    )

    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output GeoTIFF path.",
    )

    args = parser.parse_args()

    print("Step 1/4: Merging SRTM tiles...")

    array, profile = load_and_merge_tiles(
        args.tiles
    )

    print("Step 2/4: Clipping working area...")

    array, profile = clip_to_bbox(
        array,
        profile,
        tuple(args.bbox),
    )

    print("Step 3/4: Reprojecting to UTM Zone 36N...")

    array, profile = reproject_to_metric(
        array,
        profile,
    )

    print("Step 4/4: Filling depressions...")

    nodata = profile.get("nodata")

    filled = fill_sinks(
        array,
        nodata_value=nodata,
    )

    args.out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # IMPORTANT:
    # The source SRTM files use the SRTMHGT driver.
    # The processed raster has different dimensions, so it must
    # explicitly be written as a normal GeoTIFF.
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        compress="lzw",
    )

    with rasterio.open(
        args.out,
        "w",
        **profile,
    ) as destination:

        destination.write(
            filled,
            1,
        )

    print()
    print("SUCCESS")
    print("Wrote filled DEM to:")
    print(args.out)
    print()

    print(
        f"Raster size: "
        f"{filled.shape[1]} columns x "
        f"{filled.shape[0]} rows"
    )

    print(
        f"Coordinate system: "
        f"{profile['crs']}"
    )


if __name__ == "__main__":
    main()