# Hydrological Thresholds in the Southern Levant

## A Terrain-First Geospatial Research Workflow

This repository documents a reproducible GIS workflow for testing whether hydrological and topographic structure can be derived independently from terrain and then evaluated against external spatial data.

This repository supports part of a larger investigation into whether routes and locations remembered in the Torah and Qur’an correspond to recoverable features of the physical landscape. Current work here focuses on a controlled terrain analysis at the Yabboq/Wadi Zarqa basin.

The hypothesis and its supporting reasoning are developed in *We Were Not Looking* (Appendix A, “The Hydrological Spine Hypothesis”). This repository is not the argument for that hypothesis. It is the reproducible testing ground for one part of it.

The central methodological rule is simple:

> **The terrain model must be allowed to exist before the historical interpretation is allowed to explain it.**

This repository therefore separates terrain derivation, hydrological modeling, reference-data comparison, null-model testing, and historical interpretation as far as practicable.

The project is exploratory and falsifiable.

It does **not** treat GIS correspondence as proof of an ancient itinerary, historical event, prophetic route, or textual claim.

---

# Current Validation Stage: Yabboq / Wadi Zarqa

The repository now includes a first reproducible validation cycle focused on the Yabboq / Wadi Zarqa basin.

The question tested at this stage is deliberately narrower than the larger historical hypothesis:

> **If drainage structure is derived from elevation data alone, before mapped waterways are introduced, does the resulting network correspond to independently mapped hydrography more strongly than would be expected from random placement or from broadly similar terrain conditions?**

The current workflow:

- prepares and projects SRTM elevation data;
- derives slope and terrain ruggedness;
- calculates D8 flow direction;
- calculates flow accumulation;
- extracts drainage using multiple accumulation thresholds;
- introduces independent mapped hydrography only after drainage derivation;
- measures agreement across multiple spatial tolerances;
- compares observed agreement with density-matched random controls;
- compares observed agreement with terrain-matched controls;
- consolidates results into reproducible tables and figures.

The first validation cycle tests drainage thresholds of:

- **250 contributing cells**
- **500 contributing cells**
- **1000 contributing cells**

Spatial agreement is evaluated at:

- **30 m**
- **60 m**
- **90 m**
- **150 m**
- **300 m**

---

# Current Result

Across the tested thresholds and spatial tolerances, terrain-derived drainage shows greater agreement with independently mapped hydrography than both:

1. a density-matched random-cell expectation; and
2. a terrain-matched expectation using control cells matched approximately on elevation, slope, and terrain ruggedness.

The strongest separation from the terrain-matched expectation occurs in the 1000-cell threshold scenario.

For that scenario, observed agreement exceeds the terrain-matched mean by approximately:

- **+9.74 percentage points at 30 m**
- **+10.02 percentage points at 60 m**
- **+9.50 percentage points at 90 m**
- **+8.41 percentage points at 150 m**
- **+5.18 percentage points at 300 m**

These results support a limited methodological conclusion:

> **Terrain-derived drainage in the Yabboq study area exhibits reproducible spatial correspondence with independent mapped hydrography that exceeds both density-matched random expectation and terrain-matched expectation.**

This is a result about spatial correspondence.

It is **not** historical route identification.

---

# Why the Control Tests Matter

A simple visual resemblance between derived drainage and mapped waterways is not sufficient.

Drainage naturally occupies particular terrain positions, so some apparent agreement can occur merely because both modeled and mapped networks are associated with similar slope, elevation, and relief conditions.

Two null models are therefore used.

## Density-Matched Random-Cell Null

The first control preserves:

- raster extent;
- valid analysis area;
- number of drainage cells.

It does not preserve terrain characteristics or network structure.

This asks whether observed correspondence exceeds arbitrary spatial placement.

## Terrain-Matched Null

The stronger control approximately preserves:

- elevation distribution;
- slope distribution;
- terrain-ruggedness distribution;
- number of cells;
- valid analysis extent.

The independent hydrography is not used to define the terrain strata or select the matched control cells.

This asks whether observed correspondence exceeds what would be expected simply because drainage cells occupy similar terrain conditions.

The current terrain-matched null does **not** preserve:

- network connectivity;
- drainage topology;
- branching structure;
- exact spatial autocorrelation.

A topology-preserving or network-structured null is therefore an important possible second-stage robustness test.

---

# Data Sources

## Elevation

The workflow uses **NASA / USGS Shuttle Radar Topography Mission (SRTM) 1 Arc-Second Global** elevation data.

Official source:

[USGS SRTM 1 Arc-Second Global](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1)

The current Yabboq analysis uses:

- `N32E035.hgt`
- `N32E036.hgt`

SRTM 1 Arc-Second Global provides approximately 30 m spatial resolution.

## Reference Hydrography

Independent reference hydrography is derived from OpenStreetMap data distributed by **Geofabrik** for Jordan.

Official regional extract:

[Geofabrik Jordan OpenStreetMap Extract](https://download.geofabrik.de/asia/jordan.html)

The waterways layer is introduced only after terrain-derived drainage has been generated.

Because OpenStreetMap data change over time, the exact extract or acquisition date should be recorded for reproducibility.

---

# Coordinate System

Projected analysis is performed in:

**WGS 84 / UTM Zone 36N**

**EPSG:32636**

This allows distance-based comparisons to be calculated in meters.

---

# Hydrological Workflow

The current Yabboq workflow includes:

1. DEM preparation
2. reprojection and clipping
3. terrain-variable derivation
4. D8 flow-direction calculation
5. flow-accumulation calculation
6. threshold-based drainage extraction
7. independent hydrography comparison
8. threshold sensitivity analysis
9. density-matched random-null testing
10. terrain-matched null testing
11. consolidated comparison
12. figure generation

Flow-accumulation thresholds are treated as sensitivity parameters rather than as automatically meaningful hydrological boundaries.

QGIS documentation likewise treats flow accumulation / catchment area as a basis from which channel-initiation thresholds can be applied:

[QGIS Training Manual — Hydrological Analysis](https://docs.qgis.org/latest/en/docs/training_manual/processing/hydro.html)

---

# Yabboq Workflow Scripts

The current validation cycle is implemented sequentially through Python scripts:

```text
01_prepare_dem.py
02_derive_terrain.py
03b_compare_reference_hydrography.py
03c_summarize_threshold_sweep.py
04_null_background_test.py
05_terrain_matched_null.py
06_build_final_comparison.py
07_plot_final_comparison.py
