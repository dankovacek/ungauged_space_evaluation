# Ungauged Space Evaluation

Code supporting the analysis of how well the existing streamflow monitoring network represents the population of ungauged catchments in British Columbia. Representation is measured using KL divergence (KLD) between unit-area runoff distributions (flow duration curves) of gauged and ungauged sites.

## Background

A high (minimum) KLD between an ungauged basin and its most similar gauged neighbours indicates the basin is poorly represented by the current network. The analysis produces a ranked list of gauged stations by their coverage of ungauged space, which can be used to support monitoring network design.

## Method

1. **Baseline KLD**: compute the within-network KLD distribution using 4-nearest-neighbour (4NN) matching on catchment descriptors (`baseline_4nn.py`).
2. **Predicted KLD**: use trained XGBoost models (`proximity_plus_attributes` set) to predict pairwise KLD between each ungauged basin and all gauged stations (`predict_kld_donors.py`). Inference uses trial 6, selected as the trial whose mean out-of-sample MAE is closest to the median across all 10 trials in the tracked summary table.
3. **Station rankings**: aggregate per-basin predictions to rank gauged stations by how many ungauged basins they best represent (`generate_station_rankings.py`).

## Repository Structure

```
config.py                    # paths and shared settings
baseline_4nn.py              # 4NN baseline computation
predict_kld_donors.py        # KLD prediction for ungauged basins
generate_station_rankings.py # station ranking and visualisation
plot_pred_dkl.py             # diagnostic plots
check_status.py              # progress monitoring utility
data/
  filtered_station_set.geojson          # gauged station locations
  Watershed_descriptors_*.csv           # catchment descriptor table
  BCUB_regions_merged_R0.geojson        # region boundaries
  xgb_models/                           # tracked: proximity_plus_attributes_trial6_fold*.json
  KLD_prediction_results/               # tracked: trial_results_summary.csv
  results/                              # per-region output parquet files and plots
```

## Data

This repository tracks a compact model selection record at `data/KLD_prediction_results/trial_results_summary.csv` and only the selected inference models (`data/xgb_models/proximity_plus_attributes_trial6_fold*.json`).

Large precursor artifacts are not tracked here, including full model sets and the `.npy` result bundle. The model results come from [dankovacek/divergence_prediction](https://github.com/dankovacek/divergence_prediction).

## Requirements

Python 3.14. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```sh
uv sync
source .venv/bin/activate
```

A running PostgreSQL instance (database `basins`) is required for querying ungauged basin attributes. Connection settings are in `config.py`.

## Usage

```sh
# Compute 4NN baseline for a region
python baseline_4nn.py --region VCI

# Predict KLD donors for a region
python predict_kld_donors.py --region VCI

# Generate station rankings across all processed regions
python generate_station_rankings.py
```

## Safe Git Staging

Use this sequence before committing to avoid accidentally tracking large files.

```sh
# 1) See what would be staged, without staging anything
git add --dry-run .

# 2) Show all current untracked and modified paths
git status --porcelain=v1

# 3) List the largest untracked files (top 20)
git ls-files -o --exclude-standard -z \
  | xargs -0 -r stat -c '%s %n' \
  | sort -nr \
  | head -n 20

# 4) Optional gate: fail if any untracked file is over 50 MB
git ls-files -o --exclude-standard -z \
  | xargs -0 -r stat -c '%s %n' \
  | awk '$1 > 50*1024*1024 {print; found=1} END {exit found}'
```

If the size check prints files, add ignore rules first, then stage only selected paths.

```sh
# Stage specific files or folders you intend to commit
git add README.md pyproject.toml

# Then confirm exactly what is staged
git diff --cached --name-status
```
