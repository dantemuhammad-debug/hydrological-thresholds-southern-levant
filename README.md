# Hydrological Thresholds in the Southern Levant:
# An Exploratory Geospatial Workflow

This repository documents an exploratory geospatial workflow for examining hydrological
thresholds, including drainage patterns, watershed structure, and terrain constrictions
associated with selected locations in the southern Levant, including Shekhem, the Yabboq
corridor, and the Wadi Mūsā/Petra Basin.

The workflow was developed in connection with the article “Hydrological Thresholds and
Narrative Geography in the Southern Levant” and the research note “Hydrological Thresholds
and Narrative Geography: A Research Note on Terrain, Drainage, and Environmental Memory
in the Southern Levant.”

This is an open methodological framework, not a validated historical model. The workflow
identifies and visualizes environmental variables; it does not reconstruct itineraries or
claim proof for narrative events.

## Contents

- `scripts/` — SRTM preparation, hillshade generation, simplified D8-style flow routing,
  flow accumulation, drainage visualization, and figure production.
- `figures/` — Evidence maps derived from the workflow, without narrative arrows or
  reconstructed routes.
- `docs/` — Methods note, data description, and methodological limitations.

## Data

Elevation data: NASA Shuttle Radar Topography Mission 1 Arc-Second Global DEM,
distributed by USGS EROS.

Tiles used:

- `n30_e035_1arc_v3.tif` — Wadi Mūsā / Petra region
- `n31_e035_1arc_v3.tif` — Regional continuity around the Dead Sea
- `n32_e035_1arc_v3.tif` — Shekhem, central highlands, Yabboq, and Gilead

## Citation

Muhammad, Dante. *Hydrological Thresholds and Narrative Geography: A Research Note
on Terrain, Drainage, and Environmental Memory in the Southern Levant.* Covenant
Research LLC, 2026.
