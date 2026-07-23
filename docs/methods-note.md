# Methods Note

## Data
NASA Shuttle Radar Topography Mission (SRTM) 1 Arc-Second Global elevation data distributed by USGS EROS.

Tiles used:
* `n30_e035_1arc_v3.tif`
* `n31_e035_1arc_v3.tif`
* `n32_e035_1arc_v3.tif`

## Spatial resolution
The elevation products have a nominal resolution of 1 arc-second, approximately 30 meters at the equator. Actual ground dimensions vary with latitude.

The data are appropriate for regional terrain visualization and exploratory surface-drainage analysis. They are not sufficient by themselves for identifying springs, subsurface karst flow, ancient channels, or small archaeological water features.

## Figure-production procedure
* **Terrain visualization:** DEM-derived hillshade.
* **Surface preparation:** Limited smoothing for display and drainage extraction.
* **Flow direction:** Simplified D8-style routing.
* **Flow accumulation:** Raster accumulation from the routed surface.
* **Drainage visualization:** Selected flow-accumulation threshold.
* **Site locations:** Supplied geographic reference coordinates.
* **Figure composition:** Cropped regional panels with analytical annotations.

## Analytical annotations
The current figures include some features that were not automatically derived from the DEM:
* The displayed central watershed divide.
* The Wadi Mūsā/Petra basin outline.
* Saddle and terrain-constriction markers.
* Textual labels.

These should be understood as provisional analytical annotations requiring further geological-hydrological verification.

## Limitations
* SRTM represents surface elevation, not subsurface karst drainage.
* DEM artifacts and smoothing can affect extracted flow paths.
* Flat terrain creates ambiguity in flow routing.
* Narrow channels and small saddles may not be captured at this resolution.
* Accumulation thresholds affect the number and extent of displayed channels.
* DEM-derived drainage does not establish perennial flow.
* Modern surface terrain does not independently reconstruct ancient hydrology.
* Anthropogenic channels, dams, cisterns, and terraces require separate dating.
* Terrain constrictions require a formal reproducible metric in later analysis.
* Narrative association does not constitute archaeological or historical proof.

This workflow identifies environmental variables and generates methodological visualizations. It does not validate historical events or the Hydrological Spine Hypothesis.
