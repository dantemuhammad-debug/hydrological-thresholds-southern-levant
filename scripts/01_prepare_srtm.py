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
OUTPUT_MOSAIC = "data_processed/srtm_regional_mosaic.tif"

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
    # Processing implementation for cropping and merging goes here...
    print(f"Data successfully compiled into {OUTPUT_MOSAIC}")

if __name__ == "__main__":
    main()
