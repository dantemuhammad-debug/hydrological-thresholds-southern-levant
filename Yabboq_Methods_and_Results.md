\# Yabboq Drainage Validation

\## Methods and Results



\### Project purpose



This project tests whether terrain-derived drainage structure in the Yabboq study area corresponds with independently mapped hydrography more strongly than would be expected from random placement or from generic terrain similarity alone.



The workflow is diagnostic and methodological. It is designed to test spatial correspondence, not to identify an ancient route, prove a historical itinerary, or establish the movement of any named historical or religious figure.



The broader research question grows out of the historical-geographic framework developed in \*We Were Not Looking: Reconstructing the Patriarchal World Through Ancient Near Eastern Context\*, where terrain, hydrology, roads, kinship, and political geography are treated as part of the material environment through which remembered patriarchal narratives may be examined.



\---



\## 1. Study area and coordinate system



The analysis uses a clipped Yabboq-region study area covering approximately:



\- Longitude: 35.5° E to 36.2° E

\- Latitude: 31.9° N to 32.3° N



All projected raster analysis was conducted in:



\*\*EPSG:32636 — WGS 84 / UTM Zone 36N\*\*



This projected coordinate system permits distance calculations in meters.



\---



\## 2. Elevation data



The terrain model was constructed from two SRTM elevation tiles:



\- `N32E035.hgt`

\- `N32E036.hgt`



The tiles were mosaicked, clipped to the study extent, projected to EPSG:32636, and written as:



`yabboq\_dem\_filled.tif`



The working DEM dimensions are approximately:



\- 2480 columns

\- 1299 rows



The prepared DEM serves as the common spatial grid for the terrain and drainage analyses.



\---



\## 3. Terrain derivation



Terrain variables were derived from the prepared DEM.



The workflow produced:



\- `slope\_degrees.tif`

\- `ruggedness\_tri.tif`

\- `flow\_direction\_d8.tif`

\- `flow\_accumulation\_cells.tif`

\- `drainage\_threshold.tif`



Flow direction was modeled using a D8 flow-routing approach.



The D8 method assigns each cell's downslope flow to one of its eight neighboring cells according to the steepest available descent.



Flow accumulation was then calculated as the number of upstream raster cells contributing flow to each cell.



\---



\## 4. Drainage-threshold scenarios



To avoid relying on a single arbitrary drainage-density choice, three flow-accumulation thresholds were tested:



\- 250 contributing cells

\- 500 contributing cells

\- 1000 contributing cells



The lower threshold produces a denser inferred drainage network.



The higher threshold produces a sparser network emphasizing stronger terrain-defined channels.



These scenarios were analyzed independently.



\---



\## 5. Independent reference hydrography



Reference hydrography was obtained from the Geofabrik Jordan OpenStreetMap dataset.



The relevant line layer was:



`gis\_osm\_waterways\_free`



The Jordan-wide layer was clipped to the DEM study extent and saved as:



`yabboq\_osm\_waterways\_clip.gpkg`



The reference hydrography was not used to generate:



\- the DEM,

\- flow direction,

\- flow accumulation,

\- drainage thresholds,

\- terrain bins,

\- or matched control cells.



It was introduced only after terrain-derived drainage networks had been generated.



This separation is important because it prevents the reference hydrography from determining the modeled drainage pattern being evaluated.



\---



\## 6. Diagnostic hydrography comparison



Terrain-derived drainage cells were compared with the independent reference hydrography at five spatial tolerances:



\- 30 m

\- 60 m

\- 90 m

\- 150 m

\- 300 m



Two directional measures were calculated:



1\. percentage of terrain-derived drainage cells lying within the specified distance of reference hydrography;

2\. percentage of reference hydrography lying within the specified distance of terrain-derived drainage.



Higher agreement at greater tolerances is expected because the allowable spatial search radius increases.



For that reason, raw agreement percentages were not treated as sufficient evidence by themselves.



\---



\## 7. Threshold comparison



The three drainage thresholds showed the expected density tradeoff.



As the flow-accumulation threshold increased:



\- the inferred network became sparser;

\- the percentage of derived drainage near reference hydrography increased;

\- the percentage of reference hydrography captured by the derived network decreased.



This means raw agreement percentages cannot independently select an optimal threshold because drainage density directly affects the measurement.



The threshold sweep was therefore treated as a sensitivity analysis rather than a ranking exercise.



\---



\## 8. Simple density-matched random-cell null



A first null model tested whether observed drainage/reference correspondence exceeded what would be expected from randomly located raster cells.



For each drainage threshold, the null model preserved:



\- raster extent;

\- valid analysis area;

\- number of drainage cells.



It did not preserve:



\- elevation;

\- slope;

\- ruggedness;

\- drainage connectivity;

\- flow topology;

\- branching structure;

\- spatial autocorrelation.



Five hundred random simulations were performed per threshold.



Random seed:



`20260808`



Across all thresholds and tolerances, the observed terrain-derived drainage agreement exceeded the simple random-cell null expectation.



The observed-minus-random-null differences were approximately:



\### 250-cell threshold



\- 30 m: +6.03 percentage points

\- 60 m: +5.89

\- 90 m: +5.38

\- 150 m: +4.60

\- 300 m: +3.48



\### 500-cell threshold



\- 30 m: +7.83 percentage points

\- 60 m: +7.85

\- 90 m: +7.43

\- 150 m: +6.76

\- 300 m: +5.50



\### 1000-cell threshold



\- 30 m: +12.02 percentage points

\- 60 m: +12.35

\- 90 m: +12.00

\- 150 m: +11.46

\- 300 m: +10.01



All one-sided empirical p-values were:



`0.0020`



With 500 simulations, this value represents the minimum attainable empirical p-value under the calculation used:



`(exceedances + 1) / (iterations + 1)`



The simple random-cell null therefore provided evidence that the observed correspondence is not explained by density-matched random placement alone.



However, this null is weak because drainage cells are not randomly distributed across terrain.



\---



\## 9. Terrain-matched null



A stronger null model was therefore constructed.



Random control cells were matched approximately to the observed drainage cells on:



\- elevation;

\- slope;

\- terrain ruggedness.



Five quantile bins were used for each terrain variable.



For each terrain stratum, the control model sampled the same number of cells represented by the observed drainage network.



Where possible, observed drainage cells were excluded from the control sampling pool.



The independent reference hydrography was not used to define terrain strata or to select matched control cells.



The terrain-matched null preserves approximately:



\- raster extent;

\- valid analysis area;

\- number of drainage cells;

\- elevation distribution;

\- slope distribution;

\- ruggedness distribution.



It does not preserve:



\- network connectivity;

\- flow topology;

\- branching structure;

\- exact spatial autocorrelation.



Five hundred terrain-matched simulations were performed per threshold.



Random seed:



`20260808`



\---



\## 10. Terrain-matched results



Observed terrain-derived drainage agreement exceeded terrain-matched expectation across all tested thresholds and spatial tolerances.



\### 250-cell threshold



| Tolerance | Observed | Terrain null mean | Observed minus null |

|---|---:|---:|---:|

| 30 m | 8.14% | 3.15% | +4.99 pp |

| 60 m | 9.20% | 4.26% | +4.93 pp |

| 90 m | 10.34% | 5.88% | +4.46 pp |

| 150 m | 12.27% | 8.69% | +3.58 pp |

| 300 m | 17.60% | 15.81% | +1.79 pp |



\### 500-cell threshold



| Tolerance | Observed | Terrain null mean | Observed minus null |

|---|---:|---:|---:|

| 30 m | 9.95% | 3.70% | +6.25 pp |

| 60 m | 11.17% | 4.86% | +6.31 pp |

| 90 m | 12.41% | 6.54% | +5.86 pp |

| 150 m | 14.43% | 9.50% | +4.93 pp |

| 300 m | 19.63% | 17.05% | +2.57 pp |



\### 1000-cell threshold



| Tolerance | Observed | Terrain null mean | Observed minus null |

|---|---:|---:|---:|

| 30 m | 14.12% | 4.39% | +9.74 pp |

| 60 m | 15.64% | 5.63% | +10.02 pp |

| 90 m | 16.95% | 7.45% | +9.50 pp |

| 150 m | 19.09% | 10.67% | +8.41 pp |

| 300 m | 24.11% | 18.93% | +5.18 pp |



All terrain-matched empirical p-values were:



`0.0020`



The observed values also lay above the corresponding terrain-null 95% intervals at every tested threshold and tolerance.



\---



\## 11. Interpretation



The first validation cycle supports the following limited methodological conclusion:



\*\*Terrain-derived drainage structure in the Yabboq study area shows reproducible spatial correspondence with independently mapped hydrography that exceeds both density-matched random expectation and terrain-matched expectation.\*\*



The terrain-matched result is especially important because it indicates that the observed correspondence is not explained merely by placing the same number of cells in broadly similar elevation, slope, and ruggedness conditions.



The strongest relative separation from terrain-matched expectation occurred in the 1000-cell drainage-threshold scenario.



This suggests that the strongest terrain-defined drainage corridors correspond more specifically with mapped hydrography than do generic cells occupying similar terrain conditions.



This is a spatial and methodological result.



It is not, by itself, a historical conclusion.



\---



\## 12. Limitations



Several limitations remain.



\### Modern reference hydrography



The OpenStreetMap reference layer represents modern mapped hydrography.



It may be:



\- incomplete;

\- spatially generalized;

\- differently classified across contributors;

\- affected by modern drainage alteration;

\- different from ancient channel locations or hydrological conditions.



Therefore correspondence with modern hydrography cannot be treated as direct evidence of ancient waterways.



\### DEM limitations



SRTM elevation data represent modern surface topography at finite spatial resolution.



They do not reconstruct:



\- ancient channel morphology;

\- historical sedimentation;

\- erosion;

\- tectonic change;

\- anthropogenic modification;

\- palaeohydrology.



\### Null-model limitations



The terrain-matched null does not preserve:



\- connected drainage structure;

\- stream-network topology;

\- branching;

\- upstream/downstream relationships;

\- exact spatial autocorrelation.



A future topology-preserving or network-structured null would provide a stronger second-stage robustness test.



\### Historical interpretation



No result in this workflow identifies:



\- Abraham/Ibrāhīm;

\- a patriarchal itinerary;

\- a prophetic route;

\- a sacred corridor;

\- or any historical event.



Historical interpretation requires separate textual, archaeological, chronological, environmental, and geographic argument.



\---



\## 13. Reproducibility



The workflow is organized as sequential Python scripts:



1\. `01\_prepare\_dem.py`

2\. `02\_derive\_terrain.py`

3\. `03b\_compare\_reference\_hydrography.py`

4\. `03c\_summarize\_threshold\_sweep.py`

5\. `04\_null\_background\_test.py`

6\. `05\_terrain\_matched\_null.py`

7\. `06\_build\_final\_comparison.py`

8\. `07\_plot\_final\_comparison.py`



The QGIS project is stored as:



`Yabboq\_GIS\_Project.qgz`



Consolidated outputs are stored under:



`outputs\\final\_comparison`



Final figures are stored under:



`outputs\\final\_comparison\\figures`



The working random seed used for both 500-iteration null analyses was:



`20260808`



\---



\## 14. Status of the first validation cycle



The first Yabboq validation cycle is complete through:



\- terrain preparation;

\- drainage derivation;

\- threshold sensitivity analysis;

\- independent reference comparison;

\- simple random-cell null testing;

\- terrain-matched null testing;

\- consolidated comparison;

\- graphical output.



A topology-preserving drainage-network null remains a possible second-stage robustness analysis.



The current results should therefore be understood as a reproducible first-stage validation of the terrain-derived drainage method, not as final historical validation of the broader sacred-geographic hypothesis.

