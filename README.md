# Ungauged Space Evaluation

Code supporting the analysis of how well the existing streamflow monitoring network represents the population of ungauged catchments in British Columbia. Representation is measured using KL divergence (KLD) between unit-area runoff distributions (flow duration curves) of gauged and ungauged sites.

## Background

A high minimum KLD between an ungauged basin and its most similar gauged neighbours indicates that the catchment is poorly represented by the current network. The analysis produces a ranked list of gauged stations by their representation of the ungauged space, which can be used to support monitoring network design.

## Method

1. **Baseline: Predicted KLD**: use trained XGBoost models (`proximity_plus_attributes` set) to predict pairwise KLD between each ungauged basin and all gauged stations (`predict_kld_donors.py`). Inference uses trial 6, selected as the trial whose mean out-of-sample MAE is closest to the median across all 10 trials in the tracked summary table.
2. **Station rankings**: aggregate per-basin predictions to rank gauged stations by how many ungauged basins they best represent (`generate_station_rankings.py`).

## Repository Structure

Run in this order.

1. Terminal, outside QGIS; generate or refresh the overview GeoPackage:

```bash
  Watershed_descriptors_*.csv           # catchment descriptor table
  BCUB_regions_merged_R0.geojson        # region boundaries
  xgb_models/                           # tracked: proximity_plus_attributes_trial6_fold*.json
```

Large precursor artifacts are not tracked here, including full model sets and the `.npy` result bundle. The model results come from [dankovacek/divergence_prediction](https://github.com/dankovacek/divergence_prediction).

## Requirements

```sh
uv sync
source .venv/bin/activate
```

## QGIS Script Workflow

Use one QGIS helper script:

- `qgis_scripts/style_and_layout_dkl.py`: optional class filter using `kld_class`, optional export of filtered points, DKL styling, station styling, region boundary styling, and print layout creation

Recommended order:

1. Build plot inputs and QGIS layers from Python.

```sh
source .venv/bin/activate
python plot_pred_dkl.py --overview-plot --update-overview
```

2. In QGIS, load `data/results/qgis/kld_donor_overview.gpkg` (layer `ungauged_kld_overview`).
3. Open `Plugins` -> `Python Console`, then click `Show Editor` in the console panel.
4. In the editor panel, click `Open Script` (folder icon), select `qgis_scripts/style_and_layout_dkl.py`, and review the settings block at the top.
5. Set `DKL_LAYER_NAME` to your layer name (or leave `None` to use the active layer), then adjust `APPLY_DKL_LT1_FILTER`, `THRESHOLD`, and `EXPORT_FILTERED` as needed.
6. Click `Run Script` (green play icon). Confirm the console prints `Styled:` and `Layout:` messages.
7. If output is not what you want, update settings and run the same script again.

Each point keeps the original `min_predicted_kld` value, donor metadata, region code,
and a `kld_class` field matching the plot bins (`1–2`, `2–5`, `5+`).

- `data/results/qgis/kld_donor_<region>.gpkg`: per-region ungauged points
- `data/results/qgis/kld_donor_overview.gpkg`: combined overview layer across all available region parquet files, written when `--update-overview` is used

Both GeoPackages store points in `EPSG:4326`, which QGIS can import directly.

## Jupyter Book

The book uses Jupyter Book v1 with `_config.yml` and `_toc.yml`.

### Local build and preview

```sh
uv sync
source .venv/bin/activate
jupyter-book clean .
jupyter-book build .
python -m http.server -d _build/html 8000 # to run a local server for preview
```

Then open `http://localhost:8000` in a browser to view the book.

### GitHub Pages deploy with ghp-import

One-time setup:

1. Ensure GitHub Pages source is set to `gh-pages` branch in GitHub Settings -> Pages.
2. Install `ghp-import` in the project environment.

```sh
source .venv/bin/activate
pip install ghp-import
```

Build and publish:

```sh
source .venv/bin/activate
jupyter-book clean .
jupyter-book build .
ghp-import -n -p -f _build/html
```

Flag notes:

- `-n` writes `.nojekyll` so folders that begin with `_` are served correctly
- `-p` pushes to `origin/gh-pages`
- `-f` force-updates the branch from the current build output

### Deploy updates

```sh
source .venv/bin/activate
jupyter-book clean .
jupyter-book build .
ghp-import -n -p -f _build/html
```

If a source edit does not show up in the site, run the clean build again first.
Jupyter Book can leave stale incremental output behind in `_build/html`.

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
git add README.md pyproject.toml _config.yml _toc.yml intro.md

# Then confirm exactly what is staged
git diff --cached --name-status
```
