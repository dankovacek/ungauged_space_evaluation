"""
For each ungauged basin, predict KLD to every gauged station using the
proximity_plus_attributes XGBoost models (physical attrs + centroid distance).

Feature convention (empirically verified against training results):
  - donor  = gauged station (the one whose FDC would be used)
  - target = ungauged basin (the one being represented)
  - Features: [donor_a, target_a for a in MODEL_PHYSICAL_ATTRS] + [centroid_distance_km]

Training used log(kld) as target, so predictions are back-transformed with exp().
Trial 6 (median-MAE across 10 trials) is used; see data/KLD_prediction_results/trial_results_summary.csv.
All 5 fold models for that trial are averaged for each prediction.

Output: data/results/kld_donor_{region}.parquet
  basin_id, best_donor_official_id, min_predicted_kld,
  donors_within_5pct, centroid_lat, centroid_lon, region_code
"""

import argparse
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import psycopg2
import shapely
import xgboost as xgb

import config

_N_FOLDS = 5
_BATCH_SIZE = 500


def _load_gauged():
    df = pd.read_csv(config.STATION_CSV, dtype={'official_id': str})
    df = df.rename(columns=config.CSV_COLUMN_RENAME)
    needed = ['official_id', 'centroid_lat_deg_n', 'centroid_lon_deg_e'] + config.MODEL_PHYSICAL_ATTRS
    df = df[needed].copy()
    means = df[config.MODEL_PHYSICAL_ATTRS].mean()
    df[config.MODEL_PHYSICAL_ATTRS] = df[config.MODEL_PHYSICAL_ATTRS].fillna(means)
    return df


def _load_ungauged(region):
    db_cols = ['id', 'region_code', 'centroid_x', 'centroid_y'] + config.MODEL_PHYSICAL_ATTRS
    col_str = ', '.join(db_cols)
    conn = psycopg2.connect(config.DB_DSN)
    cur = conn.cursor()
    cur.execute(
        f"SELECT {col_str} FROM {config.DB_SCHEMA}.{config.DB_ATTRIBUTES_TABLE}"
        " WHERE region_code = %s",
        (region,),
    )
    rows = cur.fetchall()
    col_names = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    df = pd.DataFrame(rows, columns=col_names)
    for col, factor in config.DB_UNIT_CONVERSIONS.items():
        if col in df.columns:
            df[col] = df[col].astype(float) * factor
    gauged_means = _load_gauged()[config.MODEL_PHYSICAL_ATTRS].mean()
    for col in config.MODEL_PHYSICAL_ATTRS:
        if col in df.columns:
            df[col] = df[col].fillna(gauged_means[col])
    return df


def predict_kld_donors(region='VCI'):

    out_path = config.RESULTS_DIR / f'kld_donor_{region}.parquet'
    if out_path.exists():
        print(f'Output file {out_path} already exists, skipping prediction for {region}', flush=True)
        return None

    t_start = time.time()

    trial = config.XGB_SELECTED_TRIAL
    print(f'Using trial {trial} ({config.XGB_MODEL_SET})', flush=True)

    models = []
    for fold in range(_N_FOLDS):
        m = xgb.Booster()
        m.load_model(config.XGB_MODELS_DIR / f'{config.XGB_MODEL_SET}_trial{trial}_fold{fold}_model.json')
        models.append(m)
    print(f'Loaded {_N_FOLDS} fold models  [{time.time() - t_start:.1f}s]', flush=True)

    gauged = _load_gauged()
    print(f'Loaded {len(gauged)} gauged stations  [{time.time() - t_start:.1f}s]', flush=True)

    ungauged = _load_ungauged(region)
    print(f'Loaded {len(ungauged)} ungauged {region} basins  [{time.time() - t_start:.1f}s]', flush=True)

    # Reproject gauged stations (WGS84) to EPSG:3005.
    gauged_3005 = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(gauged['centroid_lon_deg_e'], gauged['centroid_lat_deg_n']),
        crs='EPSG:4326',
    ).to_crs('EPSG:3005')
    g_geom = np.asarray(gauged_3005.geometry)

    # Ungauged centroids are already in EPSG:3005.
    ung_3005 = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(ungauged['centroid_x'], ungauged['centroid_y']),
        crs='EPSG:3005',
    )
    ung_geom = np.asarray(ung_3005.geometry)

    # Reproject ungauged centroids to WGS84 for the output columns.
    ung_wgs84 = ung_3005.to_crs('EPSG:4326')
    ung_lats = ung_wgs84.geometry.y.values
    ung_lons = ung_wgs84.geometry.x.values
    print(f'Reprojected coordinates  [{time.time() - t_start:.1f}s]', flush=True)

    g_attrs = gauged[config.MODEL_PHYSICAL_ATTRS].values.astype(float)
    ung_attrs = ungauged[config.MODEL_PHYSICAL_ATTRS].values.astype(float)
    n_g = len(gauged)
    n_ung = len(ungauged)
    n_batches = (n_ung + _BATCH_SIZE - 1) // _BATCH_SIZE
    g_ids = gauged['official_id'].values
    print(
        f'Predicting {n_ung} x {n_g} pairs in {n_batches} batches',
        flush=True,
    )

    _DONOR_RADIUS_KM = 250.0
    total_within_radius = 0
    rows = []
    t_loop = time.time()
    for i in range(0, n_ung, _BATCH_SIZE):
        b_ung_attrs = ung_attrs[i:i + _BATCH_SIZE]
        b_lats = ung_lats[i:i + _BATCH_SIZE]
        b_lons = ung_lons[i:i + _BATCH_SIZE]
        b_geom = ung_geom[i:i + _BATCH_SIZE]
        n_b = len(b_ung_attrs)

        ung_idx = np.repeat(np.arange(n_b), n_g)
        g_idx = np.tile(np.arange(n_g), n_b)

        donor_attrs = g_attrs[g_idx]
        target_attrs = b_ung_attrs[ung_idx]

        phys = np.empty((n_b * n_g, 2 * len(config.MODEL_PHYSICAL_ATTRS)), dtype=float)
        phys[:, 0::2] = donor_attrs
        phys[:, 1::2] = target_attrs

        # shapely.distance broadcasts (n_b, 1) x (1, n_g) -> (n_b, n_g) in metres.
        dists = shapely.distance(b_geom[:, None], g_geom[None, :]) / 1000.0
        X = np.column_stack([phys, dists.ravel()])

        dmat = xgb.DMatrix(X)
        log_kld = np.mean([m.predict(dmat) for m in models], axis=0)
        kld = np.exp(log_kld).reshape(n_b, n_g)
        kld[dists > _DONOR_RADIUS_KM] = np.inf  # ignore donors beyond 250 km
        total_within_radius += int((dists <= _DONOR_RADIUS_KM).sum())

        best_idx = kld.argmin(axis=1)
        min_kld = kld.min(axis=1)

        for j in range(n_b):
            threshold = min_kld[j] * 1.05
            near = ','.join(g_ids[kld[j] <= threshold])
            rows.append({
                'basin_id': ungauged.iloc[i + j]['id'],
                'best_donor_official_id': g_ids[best_idx[j]],
                'min_predicted_kld': float(min_kld[j]),
                'donors_within_5pct': near,
                'centroid_lat': float(b_lats[j]),
                'centroid_lon': float(b_lons[j]),
                'region_code': ungauged.iloc[i + j]['region_code'],
            })

        done = i + n_b
        elapsed = time.time() - t_loop
        rate = done / elapsed
        eta = (n_ung - done) / rate if rate > 0 else 0
        print(
            f'  {done}/{n_ung} basins  '
            f'({100 * done / n_ung:.1f}%)  '
            f'[{elapsed:.0f}s elapsed, ETA {eta:.0f}s]',
            flush=True,
        )

    avg_donors = total_within_radius / n_ung
    print(f'Donors within {_DONOR_RADIUS_KM:.0f} km: avg {avg_donors:.1f} per basin (vs {n_g} total)  [{time.time() - t_start:.1f}s]', flush=True)

    out = pd.DataFrame(rows)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    print(f'Saved {len(out)} rows to {out_path}  [{time.time() - t_start:.1f}s total]', flush=True)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', default='VCI')
    args = parser.parse_args()

    if args.region == 'all':
        conn = psycopg2.connect(config.DB_DSN)
        cur = conn.cursor()
        cur.execute(
            f"SELECT DISTINCT region_code FROM {config.DB_SCHEMA}.{config.DB_ATTRIBUTES_TABLE}"
            " ORDER BY region_code"
        )
        regions = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        print(f'Processing all {len(regions)} regions: {regions}', flush=True)
        for region in regions:
            predict_kld_donors(region)
    else:
        predict_kld_donors(args.region)
