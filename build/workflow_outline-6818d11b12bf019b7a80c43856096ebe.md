# Ungauged Space Evaluation — Workflow Outline

## Problem Statement

The goal is to characterize how well the **existing streamflow monitoring network** represents the full population of ungauged catchments in a region. The measure of representation is KL divergence (KLD) between pairs of sites' unit area runoff (UAR) distributions. A high KLD between an ungauged site and its nearest gauged neighbors implies the site is poorly represented by the existing network.

The procedure has two main components:

1. **Baseline KLD** — compute the KLD distribution *within* the existing gauged network using 4-nearest-neighbor (4NN) matching on catchment descriptors.
2. **Predicted KLD for ungauged sites** — use trained XGBoost models to predict the KLD between each ungauged site and its k nearest gauged neighbors, then compare against the baseline.

The trained XGBoost models in `data/xgb_models/` predict pairwise KLD from catchment descriptor features. Three model groups exist: `proximity`, `physical_attributes`, and `proximity_plus_attributes`, each with 10 trials × 5 folds = 50 model files.

---

## Test Subset

Before running on the full PostgreSQL database, all steps will be validated on:

```
/home/danbot2/code_5820/large_sample_hydrology/bcub/processed_data/derived_basins/VCI/VCI_basins_R0.parquet
```

This file contains **20,205 VCI-region basins** with columns: `ID`, `drainage_area_km2`, `ppt_lon_m_3005`, `ppt_lat_m_3005`, `Elevation_m`, `Aspect_deg`, `Slope_deg`, `region_code`, and geometry columns. The full attribute set required by the models is in PostgreSQL (`basins_schema.basin_attributes`, `region_code = 'VCI'`, ~20,205 rows).

---

## Data Sources

| Source | Location | Contents |
|---|---|---|
| VCI parquet (test) | `.../VCI/VCI_basins_R0.parquet` | Basin geometry, basic terrain, centroid coords |
| PostgreSQL `basins` DB | `basins_schema.basin_attributes` | Full catchment descriptor set (1.26M rows across 18 regions) |
| XGBoost models | `data/xgb_models/` | Trained KLD prediction models (150 files) |
| Baseline PMFs | `KLD_predictability/data/baseline_distributions/` | Pre-computed UAR PMFs for gauged stations |
| Gauged station metadata | `KLD_predictability/data/cache/station_meta_{region}.parquet` | Lat/lon, descriptor columns for gauged network |

The XGBoost models require these feature columns (from the training notebook):

- **Terrain**: `drainage_area_km2`, `elevation_m`, `slope_deg`, `aspect_deg`
- **Land cover (2010)**: `land_use_forest_frac_2010`, `land_use_grass_frac_2010`, `land_use_wetland_frac_2010`, `land_use_water_frac_2010`, `land_use_urban_frac_2010`, `land_use_shrubs_frac_2010`, `land_use_crops_frac_2010`, `land_use_snow_ice_frac_2010`
- **Climate**: `prcp`, `srad`, `swe`, `tmax`, `tmin`, `vp`, `high_prcp_freq`, `high_prcp_duration`, `low_prcp_freq`, `low_prcp_duration`
- **Soil**: `logk_ice_x100`, `porosity_x100`
- **Proximity**: `centroid_distance_km` (computed from `centroid_x`, `centroid_y`)

All of these are present in `basins_schema.basin_attributes`.

---

## Procedure

### Step 1 — Compute Baseline KLD from the Existing Gauged Network

**Purpose**: Establish what level of KLD is expected *within* the gauged network when matching by 4NN descriptor similarity. This is the reference distribution against which ungauged site predictions are compared.

**Method** (follows `KLD_predictability/compute_baseline_divergence.py`):

1. Load gauged station metadata and pre-computed UAR PMFs from the KLD_predictability project.
2. Build a combined distance matrix: `d = α·d_spatial + (1-α)·d_descriptor`, where both distances are normalised to [0,1] by their 95th percentile. Default `α = 0.25`.
3. For each gauged station, identify its 4 nearest neighbors (excluding self) in combined distance.
4. Compute the 4NN mixture PMF: uniform average of the 4 neighbor PMFs.
5. Compute `KLD(P_i || Q_4NN_i)` for each station `i`.
6. Store as `data/cache/baseline_kld_gauged.parquet` (columns: `gauge_id`, `kld`, `w1`).

> **⚠ Ambiguity 1 — Which gauged stations are the "existing network"?**
> The KLD_predictability project covers Caravan stations (HYSETS, CAMELS, etc.). It is not clear whether any gauged VCI-region stations exist in that dataset, or whether the VCI parquet represents only ungauged basins. This determines whether the baseline is computed from an external set and then applied to VCI, or computed directly from VCI gauged subset. **Needs clarification.**

---

### Step 2 — Query Catchment Descriptors from PostgreSQL

1. Connect to `basins` database (port 5432, schema `basins_schema`).
2. Query `basin_attributes` for the VCI test region:

   ```sql
   SELECT id, region_code, centroid_x, centroid_y,
          drainage_area_km2, elevation_m, slope_deg, aspect_deg,
          land_use_forest_frac_2010, land_use_grass_frac_2010,
          land_use_wetland_frac_2010, land_use_water_frac_2010,
          land_use_urban_frac_2010, land_use_shrubs_frac_2010,
          land_use_crops_frac_2010, land_use_snow_ice_frac_2010,
          prcp, srad, swe, tmax, tmin, vp,
          high_prcp_freq, high_prcp_duration, low_prcp_freq, low_prcp_duration,
          logk_ice_x100, porosity_x100
   FROM basins_schema.basin_attributes
   WHERE region_code = 'VCI';
   ```

3. Cache result as `data/cache/vci_descriptors.parquet`.

> **⚠ Ambiguity 2 — Data quality / completeness flags**
> The `basin_attributes` table includes `geometry_flag`, `soil_flag`, `permafrost_flag`, `inside_pct_area_flag`, `outside_pct_area_flag`. The training data applied filters on these flags (see `KLD_predictability/config.py`). It is unclear whether the same filters should be applied here, and if so, what the thresholds are. **Needs clarification.**

---

### Step 3 — Identify Candidate Pairs

For 20K VCI basins, all-pairs comparison is ~200M pairs. Filtering is required.

**Proposed approach**:

1. Compute a spatial distance matrix (haversine) between all VCI basins.
2. For each basin, retain the k spatially closest candidates (e.g., k = 32, consistent with `K_MAX_NEIGHBOURS` in the KLD_predictability config).
3. Optionally apply a maximum distance cutoff (500 km was used during training).
4. Result: a sparse list of candidate pairs `(donor_id, target_id, centroid_distance_km)`.

> **⚠ Ambiguity 3 — Pairing strategy for ungauged evaluation**
> The training pairs were gauged-to-gauged comparisons within a 500 km radius. For the ungauged evaluation, the question is: are we predicting KLD between pairs of *ungauged* basins, or between each ungauged basin and the *gauged* network? The former characterises how diverse the ungauged space is; the latter characterises how well each ungauged basin is represented by existing gauges. **The intended comparison direction must be specified.**

---

### Step 4 — Assemble Pair Feature Vectors

For each candidate pair `(donor, target)`:

1. Attach descriptors for donor and target from Step 2.
2. Compute `donor_{attr}`, `target_{attr}`, and `{attr}_diff = target_{attr} - donor_{attr}` for all physical attributes.
3. Include `centroid_distance_km`.
4. Final feature vector per pair: `1 + 2×22 + 22 = 67` features (proximity variant: 1 feature).

> **⚠ Ambiguity 4 — Feature scaling and preprocessing**
> The training notebook did not apply explicit z-scoring to input features before XGBoost (tree methods are scale-invariant). However, if any preprocessing was applied during training (e.g., log-transforms on `drainage_area_km2`), the same must be applied here. **Confirm no transformations were applied to features before the XGBoost `DMatrix`.**

---

### Step 5 — Run XGBoost Inference

1. Load the ensemble of saved models from `data/xgb_models/`.
2. Group models by type: `proximity`, `physical_attributes`, `proximity_plus_attributes`.
3. For each pair feature matrix, run inference across all 50 models (10 trials × 5 folds) per model group.
4. Aggregate: compute per-pair **median predicted KLD** across the ensemble.

> **⚠ Ambiguity 5 — Ensemble aggregation strategy**
> During training, the "best trial" was selected by minimum mean test MAE, and each fold contributed one prediction for held-out pairs. For inference on new data (no held-out structure), all 50 models are applied and aggregated. The appropriate aggregation (mean vs. median vs. best-trial-only) is not specified. Median is more robust to outlier trials but the choice should match what was done in the training evaluation. **Confirm aggregation method.**

---

### Step 6 — Compute Per-Basin Predicted KLD Summary

For each ungauged basin, summarize its predicted KLD to neighbors:

1. From the full pair predictions, filter to pairs where the basin appears as either `donor` or `target`.
2. Sort by `centroid_distance_km` and select the 4 nearest neighbors.
3. Compute: `mean_predicted_kld`, `median_predicted_kld`, `min_predicted_kld` across the 4NN.
4. Store as `data/results/vci_predicted_kld_summary.parquet`.

---

### Step 7 — Compare Against Baseline and Evaluate

1. Merge the per-basin predicted KLD summary (Step 6) with the gauged network baseline KLD distribution (Step 1).
2. For each ungauged basin, compute a **relative representation score**: position of its predicted KLD within the baseline CDF.
3. Sites above the 90th percentile of the baseline KLD distribution are flagged as **underrepresented** by the existing network.
4. Produce a spatial map of representation scores across the VCI region.

> **⚠ Ambiguity 6 — Interpretation of "well-represented"**
> A low predicted KLD means the ungauged site is very similar to its neighbors. But whether similarity to *gauged* or *ungauged* neighbors is what matters depends on the framing (Step 3 ambiguity). Additionally, the predicted KLD comes from a model trained on log-transformed targets — the back-transformation and its effect on uncertainty estimates should be accounted for.

---

## Summary of Open Ambiguities

| # | Step | Question |
|---|---|---|
| 1 | Step 1 | Which stations constitute the "existing gauged network"? Do gauged VCI stations exist in the Caravan dataset? |
| 2 | Step 2 | Which quality/flag filters from `basin_attributes` should be applied to match training data conditions? |
| 3 | Step 3 | Are pairs ungauged↔ungauged, or ungauged↔gauged? This determines what "representation" means. |
| 4 | Step 4 | Were any feature transforms (e.g., log area) applied before `xgb.DMatrix` during training? |
| 5 | Step 5 | How should the 50-model ensemble be aggregated for inference (mean, median, best-trial)? |
| 6 | Step 7 | How does log-transform back-transformation affect the predicted KLD values and comparison to baseline? |
