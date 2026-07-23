"""
03_build_figures.py
Composes layout panels, draws analytical overlays, and exports publication figures.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show

# Fixed Analytical Coordinates & Layer Constraints (Longitude, Latitude)
SITE_COORDINATES = {
    "Shekhem": (35.289, 32.213),
    "Petra_Basin": (35.444, 30.328)
}

INPUT_HILLSHADE = "data_processed/derived_hillshade.tif"
INPUT_DRAINAGE = "data_processed/derived_drainage_networks.tif"
OUTPUT_DIR = "figures"
OUTPUT_FIG_1 = f"{OUTPUT_DIR}/figure_1_thresholds.png"
OUTPUT_FIG_2 = f"{OUTPUT_DIR}/figure_2_shekhem_detail.png"

def main():
    print("Assembling raster bases and plotting analytical annotations...")
    
    if not os.path.exists(INPUT_HILLSHADE) or not os.path.exists(INPUT_DRAINAGE):
        print("[ERROR] Derived terrain files missing. Run scripts 01 and 02 first.")
        sys.exit(1)

    # Figure 1: Regional Thresholds
    fig1, ax1 = plt.subplots(figsize=(10, 10))
    
    with rasterio.open(INPUT_HILLSHADE) as hs_src:
        show(hs_src, ax=ax1, cmap='gray', alpha=0.7, title="Topographic and Hydrological Setting")
        
    with rasterio.open(INPUT_DRAINAGE) as dr_src:
        drainage_data = dr_src.read(1)
        # Mask zeros to display only the extracted drainage lines
        drainage_data = np.ma.masked_where(drainage_data == 0, drainage_data)
        show(drainage_data, transform=dr_src.transform, ax=ax1, cmap='Blues', alpha=0.8)

    # Plot Site Markers
    for site, (lon, lat) in SITE_COORDINATES.items():
        ax1.plot(lon, lat, 'ro', markersize=6)
        ax1.text(lon + 0.02, lat, site.replace("_", " "), fontsize=9, color='red', weight='bold')
        
    plt.savefig(OUTPUT_FIG_1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print(f"Exported {OUTPUT_FIG_1}")

    # Figure 2: Shekhem Detail (Zoomed Extent)
    fig2, ax2 = plt.subplots(figsize=(8, 8))
    
    with rasterio.open(INPUT_HILLSHADE) as hs_src:
        show(hs_src, ax=ax2, cmap='gray', alpha=0.8, title="Shekhem Environs Detail")
        # Constrain axes to Shekhem region
        ax2.set_xlim(35.15, 35.45)
        ax2.set_ylim(32.10, 32.35)
        
    with rasterio.open(INPUT_DRAINAGE) as dr_src:
        show(drainage_data, transform=dr_src.transform, ax=ax2, cmap='Blues', alpha=0.9)

    # Plot localized Shekhem marker
    lon, lat = SITE_COORDINATES["Shekhem"]
    ax2.plot(lon, lat, 'ro', markersize=8)
    ax2.text(lon + 0.01, lat + 0.01, "Shekhem", fontsize=12, color='red', weight='bold')

    plt.savefig(OUTPUT_FIG_2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"Exported {OUTPUT_FIG_2}")
    print("Figure generation complete.")

if __name__ == "__main__":
    main()
