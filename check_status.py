"""
One-time script to add an 'active' boolean column to the watershed descriptors
CSV.

Priority:
  1. HYDAT HYD_STATUS: A → True, D → False
  2. HYSETS discharge time series: active if the last non-NaN year equals the
     last year in the file's time coordinate, discontinued otherwise
  3. Stations found in neither source → True (unknown, assumed active)
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

_HYDAT = Path('/home/danbot2/code_5820/large_sample_hydrology/common_data'
              '/HYDAT_db/Hydat_sqlite3_20260417/Hydat.sqlite3')
_HYSETS_NC    = Path('/home/danbot2/code_5820/large_sample_hydrology/common_data'
                     '/HYSETS_data/HYSETS_2023_update_QC_stations.nc')
_HYSETS_PROPS = Path('/home/danbot2/code_5820/large_sample_hydrology/common_data'
                     '/HYSETS_data/HYSETS_watershed_properties.txt')
_DESCRIPTORS  = Path('data/Watershed_descriptors_20260203_with_stats.csv')


def _hysets_active(unknown_ids):
    """Return a Series (index = official_id str) → bool for stations in HYSETS."""
    props = pd.read_csv(_HYSETS_PROPS, sep=';', usecols=['Watershed_ID', 'Official_ID'])
    props['Official_ID'] = props['Official_ID'].astype(str)
    relevant = props[props['Official_ID'].isin(set(unknown_ids))].copy()
    if relevant.empty:
        return pd.Series(dtype=bool)

    ds = xr.open_dataset(_HYSETS_NC)
    time_vals = pd.DatetimeIndex(ds['time'].values)
    last_year  = time_vals.max().year
    years      = time_vals.year.values

    ws_ids     = ds['watershedID'].values.astype(int)
    id_to_idx  = {wid: i for i, wid in enumerate(ws_ids)}

    relevant['ws_idx'] = relevant['Watershed_ID'].map(id_to_idx)
    relevant = relevant.dropna(subset=['ws_idx'])
    relevant['ws_idx'] = relevant['ws_idx'].astype(int)

    idxs      = relevant['ws_idx'].tolist()
    discharge = ds['discharge'].isel(watershed=idxs).values  # (n, time)
    ds.close()

    result = {}
    for i, (_, row) in enumerate(relevant.iterrows()):
        valid = ~np.isnan(discharge[i])
        if not valid.any():
            result[row['Official_ID']] = False
        else:
            result[row['Official_ID']] = int(years[valid].max()) >= last_year

    return pd.Series(result, dtype=bool)


def main():
    df = pd.read_csv(_DESCRIPTORS)

    con = sqlite3.connect(_HYDAT)
    hydat_status = pd.read_sql(
        'SELECT STATION_NUMBER, HYD_STATUS FROM STATIONS', con
    ).set_index('STATION_NUMBER')['HYD_STATUS']
    con.close()

    hydat_active = (df['official_id'].astype(str)
                      .map(hydat_status)
                      .map({'A': True, 'D': False}))   # True/False/NaN

    unknown_ids  = df.loc[hydat_active.isna(), 'official_id'].astype(str).tolist()
    hysets_map   = _hysets_active(unknown_ids)
    hysets_col   = df['official_id'].astype(str).map(hysets_map)   # aligned to df

    df['active'] = (hydat_active.combine_first(hysets_col)
                                .fillna(True)
                                .astype(bool))

    df.to_csv(_DESCRIPTORS, index=False)

    n_active  = int(df['active'].sum())
    n_disc    = int((~df['active']).sum())
    n_hydat   = int(hydat_active.notna().sum())
    n_hysets  = int(hysets_map.notna().sum())
    n_assumed = len(unknown_ids) - n_hysets
    print(
        f'{len(df)} stations total: {n_active} active, {n_disc} discontinued\n'
        f'  {n_hydat} resolved via HYDAT, '
        f'{n_hysets} via HYSETS discharge, '
        f'{n_assumed} assumed active (not found in either)'
    )


if __name__ == '__main__':
    main()

