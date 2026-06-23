"""
Compute the 4-nearest-neighbour (4NN) baseline for ungauged basin evaluation.

For each ungauged basin (test region queried from PostgreSQL), find its
K nearest gauged stations in z-scored catchment descriptor space using a
cKDTree.  The mean descriptor-space distance to the K nearest gauged
neighbours is a measure of how well-represented the ungauged basin is by
the existing monitoring network.

Output is saved to RESULTS_DIR / 'baseline_4nn_{region}.parquet' with
columns:
    basin_id          - DB id of the ungauged basin
    nn{k}_official_id - official_id of the k-th nearest gauged station
    nn{k}_dist        - z-scored descriptor-space distance to that station
    mean_knn_dist     - mean distance over all K neighbours

Usage:
    python baseline_4nn.py
    python baseline_4nn.py --region VCI
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from scipy.spatial import cKDTree
from sklearn.preprocessing import StandardScaler

from config import (
    ALL_DESCRIPTOR_FEATURES,
    CACHE_DIR,
    CSV_COLUMN_RENAME,
    DB_ATTRIBUTES_TABLE,
    DB_DSN,
    DB_SCHEMA,
    DB_UNIT_CONVERSIONS,
    K_NEIGHBOURS,
    RESULTS_DIR,
    STATION_CSV,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

# Columns to pull from the DB for ungauged basins
_DB_EXTRA_COLS = ['id', 'region_code', 'centroid_x', 'centroid_y']


def load_gauged_stations() -> pd.DataFrame:
    df = pd.read_csv(STATION_CSV)
    df = df.rename(columns=CSV_COLUMN_RENAME)
    keep = ['official_id', 'region', 'centroid_lon_deg_e', 'centroid_lat_deg_n']
    missing = [c for c in ALL_DESCRIPTOR_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f'Missing descriptor columns in CSV: {missing}')
    return df[keep + ALL_DESCRIPTOR_FEATURES].copy()


def load_ungauged_from_db(region_codes: list[str]) -> pd.DataFrame:
    select_cols = _DB_EXTRA_COLS + ALL_DESCRIPTOR_FEATURES
    placeholders = ', '.join(f"'{r}'" for r in region_codes)
    query = (
        f"SELECT {', '.join(select_cols)} "
        f"FROM {DB_SCHEMA}.{DB_ATTRIBUTES_TABLE} "
        f"WHERE region_code IN ({placeholders})"
    )
    with psycopg2.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=col_names)
    for col, factor in DB_UNIT_CONVERSIONS.items():
        if col in df.columns:
            df[col] = df[col] * factor
    return df


def _fill_nans(df: pd.DataFrame, cols: list[str], fill_values: pd.Series) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(fill_values[col])
    return df


def compute_4nn_baseline(
    gauged: pd.DataFrame,
    ungauged: pd.DataFrame,
) -> pd.DataFrame:
    feature_cols = ALL_DESCRIPTOR_FEATURES

    # Fill NaN using column means from the gauged reference set
    gauged_means = gauged[feature_cols].mean()
    gauged = _fill_nans(gauged, feature_cols, gauged_means)
    ungauged = _fill_nans(ungauged, feature_cols, gauged_means)

    scaler = StandardScaler()
    X_gauged = scaler.fit_transform(gauged[feature_cols].values)
    X_ungauged = scaler.transform(ungauged[feature_cols].values)

    tree = cKDTree(X_gauged)
    distances, indices = tree.query(X_ungauged, k=K_NEIGHBOURS, workers=-1)

    gauged_ids = gauged['official_id'].values
    result = pd.DataFrame({'basin_id': ungauged['id'].values})
    for k in range(K_NEIGHBOURS):
        result[f'nn{k + 1}_official_id'] = gauged_ids[indices[:, k]]
        result[f'nn{k + 1}_dist'] = distances[:, k]
    result['mean_knn_dist'] = distances.mean(axis=1)

    # Carry through spatial reference columns for later visualisation
    result['centroid_x'] = ungauged['centroid_x'].values
    result['centroid_y'] = ungauged['centroid_y'].values
    result['region_code'] = ungauged['region_code'].values

    return result


def main(region_codes: list[str]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    log.info('Loading gauged stations from %s', STATION_CSV)
    gauged = load_gauged_stations()
    log.info('  %d gauged stations loaded', len(gauged))

    log.info('Querying ungauged basins for regions: %s', region_codes)
    ungauged = load_ungauged_from_db(region_codes)
    log.info('  %d ungauged basins loaded', len(ungauged))

    log.info('Computing %d-NN in descriptor space', K_NEIGHBOURS)
    results = compute_4nn_baseline(gauged, ungauged)
    log.info('  Done.  Mean of mean_knn_dist = %.3f', results['mean_knn_dist'].mean())

    tag = '_'.join(region_codes)
    out_path = RESULTS_DIR / f'baseline_4nn_{tag}.parquet'
    results.to_parquet(out_path, index=False)
    log.info('Saved → %s', out_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='4NN descriptor-space baseline.')
    parser.add_argument(
        '--region',
        nargs='+',
        default=['VCI'],
        metavar='CODE',
        help='Region code(s) to query from the DB (default: VCI)',
    )
    args = parser.parse_args()
    main(args.region)
