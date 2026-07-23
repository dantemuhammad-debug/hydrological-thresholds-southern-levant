"""
01_prepare_srtm.py
Loads, verifies, crops, and mosaics source NASA SRTM 1 Arc-Second tiles.
"""

import os
import sys
import rasterio
from rasterio.merge import merge

# Explicit Geographic Constraints & Processing Inputs
TILES = ["n30_e035_1arc_v3.tif", "n31_e035_1arc_v3.tif", "n32_e035_1arc_v3.tif"]
EXPECTED_CRS = "EPSG:4326"
CROP_BOUNDS = {"left": 34.5, "bottom": 29.5, "right": 36.5, "top": 32.8}
OUTPUT_DIR = "data_processed"
OUTPUT_MOSAIC = f"{OUTPUT_DIR}/srtm_regional_mosaic.tif"

def verify_inputs(tile_list):
    """Verifies existence, coordinate reference system, and dimensional health of tiles."""
    missing_tiles = [t for t in tile_list if not os.path.exists(t)]
    if missing_tiles:
        print(f"[ERROR] Missing required USGS source tiles: {missing_tiles}")
        print("Please download these files via EarthExplorer and place them in the project root.")
        sys.exit(1)

    for tile in tile_list:
        with rasterio.open(tile) as src:
            if src.crs.to_string() != EXPECTED_CRS:
                print(f"[ERROR] Tile {tile} uses CRS {src.crs}, expected {EXPECTED_CRS}.")
                sys.exit(1)

def main():
    print("Beginning SRTM tile ingestion and validation routine...")
    verify_inputs(TILES)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Cropping and merging tiles...")
    src_files_to_mosaic = []
    
    # Open tiles and append to list
    for tile in TILES:
        src = rasterio.open(tile)
        src_files_to_mosaic.append(src)
        
    # Merge and crop using the specified bounding box
    mosaic, out_trans = merge(
        src_files_to_mosaic, 
        bounds=(CROP_BOUNDS["left"], CROP_BOUNDS["bottom"], CROP_BOUNDS["right"], CROP_BOUNDS["top"])
    )
    
    # Update metadata for the new mosaic
    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": EXPECTED_CRS
    })
    
    # Write the output file
    with rasterio.open(OUTPUT_MOSAIC, "w", **out_meta) as dest:
        dest.write(mosaic)
        
    # Close open files
    for src in src_files_to_mosaic:
        src.close()

    print(f"Data successfully compiled into {OUTPUT_MOSAIC}")

if __name__ == "__main__":
    main()
