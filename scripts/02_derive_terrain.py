"""
02_derive_terrain.py

Derive terrain and baseline hydrological structure from the prepared
Yabboq / Wadi Zerka DEM.

Inputs
------
A sink-filled, projected DEM produced by 01_prepare_dem.py.

Outputs
-------
1. slope_degrees.tif
2. ruggedness_tri.tif
3. flow_direction_d8.tif
4. flow_accumulation_cells.tif
5. drainage_threshold.tif

Methodological note
-------------------
The drainage network is derived from terrain alone.

No modern mapped waterways are burned into the DEM or used to force
flow direction. External hydrography must be compared later as an
independent diagnostic layer.

The drainage threshold supplied here is provisional. It is intended
for scenario testing and must not be interpreted as a privileged or
final value.

Example:

py 02_derive_terrain.py ^
    --dem ..\\outputs\\yabboq_dem_filled.tif ^
    --out-dir ..\\outputs\\terrain ^
    --flow-threshold 500
"""

import argparse
from collections import deque
from pathlib import Path

import numpy as np
import rasterio


# -------------------------------------------------------------------
# D8 neighborhood
#
# Code:
#
#   4  3  2
#   5  X  1
#   6  7  8
#
# Code 0 means no downslope receiver was found.
# -------------------------------------------------------------------

D8_NEIGHBORS = [
    (0, 1, 1),     # East
    (-1, 1, 2),    # Northeast
    (-1, 0, 3),    # North
    (-1, -1, 4),   # Northwest
    (0, -1, 5),    # West
    (1, -1, 6),    # Southwest
    (1, 0, 7),     # South
    (1, 1, 8),     # Southeast
]


def read_dem(path):
    """
    Read the prepared DEM and return the elevation array
    plus its raster profile.
    """

    with rasterio.open(path) as src:
        dem = src.read(1).astype(np.float64)
        profile = src.profile.copy()
        nodata = src.nodata

    if nodata is not None:
        valid = ~np.isclose(dem, nodata)
    else:
        valid = np.isfinite(dem)

    return dem, profile, valid


def pixel_sizes(transform):
    """
    Return positive X and Y pixel dimensions in map units.
    """

    xres = abs(transform.a)
    yres = abs(transform.e)

    return xres, yres


def derive_slope(dem, valid, transform):
    """
    Calculate slope in degrees using elevation gradients.

    Because the DEM is already projected to UTM Zone 36N,
    horizontal and vertical units are both meters.
    """

    xres, yres = pixel_sizes(transform)

    working = dem.copy()
    working[~valid] = np.nan

    dz_dy, dz_dx = np.gradient(
        working,
        yres,
        xres,
    )

    slope_radians = np.arctan(
        np.sqrt(
            dz_dx ** 2 +
            dz_dy ** 2
        )
    )

    slope_degrees = np.degrees(
        slope_radians
    )

    slope_degrees[~valid] = np.nan

    return slope_degrees.astype(np.float32)


def derive_ruggedness(dem, valid):
    """
    Calculate a simple Terrain Ruggedness Index (TRI).

    For each valid cell, TRI is the mean absolute elevation
    difference between that cell and its valid neighboring cells.

    Units are meters.
    """

    rows, cols = dem.shape

    total_difference = np.zeros(
        dem.shape,
        dtype=np.float64,
    )

    neighbor_count = np.zeros(
        dem.shape,
        dtype=np.uint8,
    )

    offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]

    for dr, dc in offsets:

        src_row_start = max(0, -dr)
        src_row_end = min(rows, rows - dr)

        src_col_start = max(0, -dc)
        src_col_end = min(cols, cols - dc)

        nbr_row_start = src_row_start + dr
        nbr_row_end = src_row_end + dr

        nbr_col_start = src_col_start + dc
        nbr_col_end = src_col_end + dc

        center = dem[
            src_row_start:src_row_end,
            src_col_start:src_col_end,
        ]

        neighbor = dem[
            nbr_row_start:nbr_row_end,
            nbr_col_start:nbr_col_end,
        ]

        center_valid = valid[
            src_row_start:src_row_end,
            src_col_start:src_col_end,
        ]

        neighbor_valid = valid[
            nbr_row_start:nbr_row_end,
            nbr_col_start:nbr_col_end,
        ]

        pair_valid = (
            center_valid &
            neighbor_valid
        )

        differences = np.abs(
            center - neighbor
        )

        target_total = total_difference[
            src_row_start:src_row_end,
            src_col_start:src_col_end,
        ]

        target_count = neighbor_count[
            src_row_start:src_row_end,
            src_col_start:src_col_end,
        ]

        target_total[pair_valid] += (
            differences[pair_valid]
        )

        target_count[pair_valid] += 1

    ruggedness = np.full(
        dem.shape,
        np.nan,
        dtype=np.float64,
    )

    usable = (
        valid &
        (neighbor_count > 0)
    )

    ruggedness[usable] = (
        total_difference[usable] /
        neighbor_count[usable]
    )

    return ruggedness.astype(np.float32)


def derive_d8_flow_direction(
    dem,
    valid,
    transform,
):
    """
    Derive D8 flow direction by selecting the neighboring cell
    with the steepest positive downslope gradient.

    Returns
    -------
    direction:
        Raster of D8 direction codes.

    receiver:
        Flattened index of the downstream receiving cell.
        -1 indicates no receiver.
    """

    rows, cols = dem.shape
    xres, yres = pixel_sizes(transform)

    direction = np.zeros(
        dem.shape,
        dtype=np.uint8,
    )

    receiver = np.full(
        rows * cols,
        -1,
        dtype=np.int64,
    )

    diagonal_distance = np.sqrt(
        xres ** 2 +
        yres ** 2
    )

    distance_lookup = {
        (-1, -1): diagonal_distance,
        (-1, 0): yres,
        (-1, 1): diagonal_distance,
        (0, -1): xres,
        (0, 1): xres,
        (1, -1): diagonal_distance,
        (1, 0): yres,
        (1, 1): diagonal_distance,
    }

    best_gradient = np.full(
        dem.shape,
        -np.inf,
        dtype=np.float64,
    )

    for dr, dc, code in D8_NEIGHBORS:

        center_row_start = max(
            0,
            -dr,
        )

        center_row_end = min(
            rows,
            rows - dr,
        )

        center_col_start = max(
            0,
            -dc,
        )

        center_col_end = min(
            cols,
            cols - dc,
        )

        nbr_row_start = (
            center_row_start + dr
        )

        nbr_row_end = (
            center_row_end + dr
        )

        nbr_col_start = (
            center_col_start + dc
        )

        nbr_col_end = (
            center_col_end + dc
        )

        center = dem[
            center_row_start:center_row_end,
            center_col_start:center_col_end,
        ]

        neighbor = dem[
            nbr_row_start:nbr_row_end,
            nbr_col_start:nbr_col_end,
        ]

        center_valid = valid[
            center_row_start:center_row_end,
            center_col_start:center_col_end,
        ]

        neighbor_valid = valid[
            nbr_row_start:nbr_row_end,
            nbr_col_start:nbr_col_end,
        ]

        drop = center - neighbor

        gradient = (
            drop /
            distance_lookup[(dr, dc)]
        )

        candidate = (
            center_valid &
            neighbor_valid &
            (drop > 0)
        )

        current_best = best_gradient[
            center_row_start:center_row_end,
            center_col_start:center_col_end,
        ]

        current_direction = direction[
            center_row_start:center_row_end,
            center_col_start:center_col_end,
        ]

        better = (
            candidate &
            (gradient > current_best)
        )

        current_best[better] = (
            gradient[better]
        )

        current_direction[better] = code

    # Convert direction codes into downstream flattened indexes.
    for row in range(rows):
        for col in range(cols):

            if not valid[row, col]:
                continue

            code = direction[row, col]

            if code == 0:
                continue

            for dr, dc, test_code in D8_NEIGHBORS:

                if code != test_code:
                    continue

                nr = row + dr
                nc = col + dc

                if (
                    0 <= nr < rows
                    and 0 <= nc < cols
                    and valid[nr, nc]
                ):
                    source_index = (
                        row * cols +
                        col
                    )

                    receiver_index = (
                        nr * cols +
                        nc
                    )

                    receiver[source_index] = (
                        receiver_index
                    )

                break

    direction[~valid] = 0

    return direction, receiver


def derive_flow_accumulation(
    receiver,
    valid,
):
    """
    Calculate upstream contributing-cell accumulation.

    Each valid cell begins with an accumulation of 1,
    meaning its own area is included.

    A topological queue routes contributions downstream.
    """

    flat_valid = valid.ravel()
    n_cells = flat_valid.size

    accumulation = np.zeros(
        n_cells,
        dtype=np.float64,
    )

    accumulation[flat_valid] = 1.0

    indegree = np.zeros(
        n_cells,
        dtype=np.int32,
    )

    valid_indices = np.flatnonzero(
        flat_valid
    )

    for source in valid_indices:

        target = receiver[source]

        if target >= 0:
            indegree[target] += 1

    queue = deque(
        int(index)
        for index in valid_indices
        if indegree[index] == 0
    )

    processed = 0

    while queue:

        source = queue.popleft()
        processed += 1

        target = receiver[source]

        if target >= 0:

            accumulation[target] += (
                accumulation[source]
            )

            indegree[target] -= 1

            if indegree[target] == 0:
                queue.append(target)

    # With strict downhill receivers there should be no cycles.
    # Any unprocessed valid cell indicates a routing problem.
    if processed != len(valid_indices):

        unresolved = (
            len(valid_indices) -
            processed
        )

        raise RuntimeError(
            f"Flow routing contains "
            f"{unresolved} unresolved cells."
        )

    return accumulation.reshape(
        valid.shape
    ).astype(np.float32)


def threshold_drainage(
    accumulation,
    valid,
    threshold_cells,
):
    """
    Convert flow accumulation into a binary candidate
    drainage-network raster.

    1 = accumulation meets or exceeds threshold
    0 = below threshold
    255 = nodata
    """

    drainage = np.zeros(
        accumulation.shape,
        dtype=np.uint8,
    )

    drainage[
        valid &
        (
            accumulation >=
            threshold_cells
        )
    ] = 1

    drainage[~valid] = 255

    return drainage


def write_float_raster(
    path,
    data,
    profile,
):
    """
    Write a float32 GeoTIFF.
    """

    output_profile = (
        profile.copy()
    )

    nodata = -9999.0

    output = data.copy()

    output[
        ~np.isfinite(output)
    ] = nodata

    output_profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=nodata,
        compress="lzw",
    )

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
            output.astype(
                np.float32
            ),
            1,
        )


def write_uint8_raster(
    path,
    data,
    profile,
    nodata=255,
):
    """
    Write an unsigned 8-bit GeoTIFF.
    """

    output_profile = (
        profile.copy()
    )

    output_profile.update(
        driver="GTiff",
        dtype="uint8",
        count=1,
        nodata=nodata,
        compress="lzw",
    )

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
            data.astype(
                np.uint8
            ),
            1,
        )


def main():

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--dem",
        required=True,
        type=Path,
        help=(
            "Prepared DEM produced by "
            "01_prepare_dem.py"
        ),
    )

    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help=(
            "Directory for derived terrain "
            "products."
        ),
    )

    parser.add_argument(
        "--flow-threshold",
        required=True,
        type=int,
        help=(
            "Flow accumulation threshold "
            "in contributing cells. "
            "This value is provisional and "
            "must later be scenario-tested."
        ),
    )

    args = parser.parse_args()

    if args.flow_threshold <= 0:
        raise ValueError(
            "--flow-threshold must be "
            "greater than zero."
        )

    print(
        "Step 1/5: Reading prepared DEM..."
    )

    dem, profile, valid = read_dem(
        args.dem
    )

    print(
        "Step 2/5: Deriving slope..."
    )

    slope = derive_slope(
        dem,
        valid,
        profile["transform"],
    )

    print(
        "Step 3/5: Deriving terrain ruggedness..."
    )

    ruggedness = derive_ruggedness(
        dem,
        valid,
    )

    print(
        "Step 4/5: Deriving D8 flow direction..."
    )

    direction, receiver = (
        derive_d8_flow_direction(
            dem,
            valid,
            profile["transform"],
        )
    )

    print(
        "Step 5/5: Calculating flow accumulation..."
    )

    accumulation = (
        derive_flow_accumulation(
            receiver,
            valid,
        )
    )

    drainage = threshold_drainage(
        accumulation,
        valid,
        args.flow_threshold,
    )

    out_dir = args.out_dir

    write_float_raster(
        out_dir /
        "slope_degrees.tif",
        slope,
        profile,
    )

    write_float_raster(
        out_dir /
        "ruggedness_tri.tif",
        ruggedness,
        profile,
    )

    write_uint8_raster(
        out_dir /
        "flow_direction_d8.tif",
        direction,
        profile,
        nodata=255,
    )

    write_float_raster(
        out_dir /
        "flow_accumulation_cells.tif",
        accumulation,
        profile,
    )

    write_uint8_raster(
        out_dir /
        "drainage_threshold.tif",
        drainage,
        profile,
        nodata=255,
    )

    print()
    print("SUCCESS")
    print()
    print(
        "Derived terrain products written to:"
    )
    print(out_dir)
    print()
    print("Created:")
    print("  slope_degrees.tif")
    print("  ruggedness_tri.tif")
    print("  flow_direction_d8.tif")
    print(
        "  flow_accumulation_cells.tif"
    )
    print("  drainage_threshold.tif")
    print()
    print(
        "Provisional flow threshold:"
    )
    print(
        f"  {args.flow_threshold} cells"
    )
    print()
    print(
        "IMPORTANT: This threshold is a "
        "scenario parameter, not a result."
    )


if __name__ == "__main__":
    main()