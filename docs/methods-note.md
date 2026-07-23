# Methods Note: DEM Processing, Drainage Extraction, and Terrain Analysis

## Data

- Source: NASA Shuttle Radar Topography Mission 1 Arc-Second Global DEM
- Distributor: USGS EROS
- Nominal resolution: approximately 30 m
- Tiles used:
  - `n30_e035_1arc_v3.tif`
  - `n31_e035_1arc_v3.tif`
  - `n32_e035_1arc_v3.tif`

## Workflow Overview

1. **DEM preparation**
   - Load and verify the SRTM tiles.
   - Crop the regional extents used in the figures.
   - Apply limited smoothing for visualization and exploratory drainage extraction.

2. **Terrain visualization**
   - Derive hillshade to emphasize ridges, valleys, escarpments, saddles, and basin form.

3. **Flow direction and accumulation**
   - Use a simplified D8-style surface-routing procedure.
   - Compute raster flow accumulation.
   - Apply selected thresholds to visualize major drainage tendencies.

4. **Watershed and basin structure**
   - Examine watershed structure through terrain relief and surface-flow outputs.
   - Display provisional watershed and basin annotations for methodological illustration.
   - Identify saddles and terrain constrictions through local topographic analysis
     and visual inspection.

5. **Analytical annotations**
   - Site markers for Shekhem and Petra.
   - Central highland divide.
   - Wadi Mūsā basin outline.
   - Saddle and terrain-constriction markers.

These annotations are provisional and require further geological-hydrological and
archaeological validation.

## Limitations

- SRTM represents surface elevation, not subsurface karst drainage.
- DEM artifacts and smoothing can affect extracted flow paths.
- Flat terrain creates ambiguity in flow routing.
- Narrow channels and small saddles may not be captured at this resolution.
- Accumulation thresholds affect the number and extent of displayed channels.
- DEM-derived drainage does not establish perennial flow.
- Modern surface terrain does not independently reconstruct ancient hydrology.
- Anthropogenic channels, dams, cisterns, and terraces require separate dating.
- Terrain constrictions require a formal reproducible metric in later analysis.
- Narrative association does not constitute archaeological or historical proof.

This workflow identifies environmental variables and generates methodological visualizations. It does not validate historical events or the Hydrological Spine Hypothesis.
