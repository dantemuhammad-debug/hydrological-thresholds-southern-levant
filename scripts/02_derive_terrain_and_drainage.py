"""
02_derive_terrain_and_drainage.py
Generates hillshades, runs D8 flow routing, and extracts drainage vectors.
"""

import os
import sys
import numpy as np
import rasterio
import richdem as rd

INPUT_MOSAIC = "data_processed/srtm_regional_mosaic.tif"
OUTPUT_HILLSHADE = "data_processed/derived_hillshade.tif"
OUTPUT_ACCUMULATION = "data_processed/derived_flow_accumulation.tif"
OUTPUT_DRAINAGE = "data_processed/derived_drainage_networks.tif"

FLOW_THRESHOLD = 500  # Cell accumulation threshold for channel initialization

def main():
    if not os.path.exists(INPUT_MOSAIC):
        print(f"[ERROR] Input mosaic '{INPUT_MOSAIC}' missing. Run 01_prepare_srtm.py first.")
        sys.exit(1)
        
    print("Loading DEM data...")
    dem = rd.LoadGDAL(INPUT_MOSAIC)
    
    # 1. Generate Hillshade
    print("Calculating surface hillshade...")
    hillshade = rd.TerrainAttribute(dem, attrib='hillshade')
    rd.SaveGDAL(OUTPUT_HILLSHADE, hillshade)
    
    # 2. Flow Routing and Accumulation
    print("Filling depressions and calculating simplified D8 flow direction...")
    rd.FillDepressions(dem, in_place=True)
    
    # D8 flow accumulation
    print("Calculating flow accumulation...")
    accum = rd.FlowAccumulation(dem, method='D8')
    rd.SaveGDAL(OUTPUT_ACCUMULATION, accum)
    
    # 3. Extract Drainage Network based on Threshold
    print(f"Extracting drainage networks (Threshold > {FLOW_THRESHOLD} cells)...")
    drainage = np.where(accum > FLOW_THRESHOLD, 1, 0)
    
    # Save drainage as raster using original metadata
    with rasterio.open(INPUT_MOSAIC) as src:
        meta = src.meta.copy()
        meta.update(dtype=rasterio.int16, count=1, nodata=0)
        
        with rasterio.open(OUTPUT_DRAINAGE, 'w', **meta) as dst:
            dst.write(drainage.astype(rasterio.int16), 1)

    print("Drainage matrix generation complete.")

if __name__ == "__main__":
    main()
