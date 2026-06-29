from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure


_COLORS = ['#0d0014', '#4d0050', '#8b005d', '#cc0084', '#ff00a8']
_LABELS = ['Q1 (lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (highest)']
_ROOT_DIR = Path(__file__).resolve().parent
_RESULTS_DIR = _ROOT_DIR / 'data' / 'results'
_STATIONS_PATH = _ROOT_DIR / 'data' / 'filtered_station_set.geojson'


def _load_results(results_dir=_RESULTS_DIR):
    frames = [pd.read_parquet(path) for path in sorted(results_dir.glob('kld_donor_*.parquet'))]
    return pd.concat(frames, ignore_index=True)


def _compute_soft_counts(df):
    soft_counts = Counter()
    for _, row in df.iterrows():
        donors_str = row['donors_within_5pct']
        donors = (
            donors_str.split(',')
            if isinstance(donors_str, str) and donors_str
            else [row['best_donor_official_id']]
        )
        weight = 1.0 / len(donors)
        for donor_id in donors:
            soft_counts[donor_id] += weight
    return soft_counts


def build_station_importance_map(results_dir=_RESULTS_DIR, stations_path=_STATIONS_PATH):
    df = _load_results(results_dir)
    soft_counts = _compute_soft_counts(df)

    stations_gdf = gpd.read_file(stations_path).to_crs('EPSG:3857')
    stations_gdf['soft_count'] = (
        stations_gdf['official_id'].map(soft_counts).fillna(0).round(1)
    )

    donors = stations_gdf[stations_gdf['soft_count'] > 0].copy()
    donors['quintile'] = pd.qcut(
        donors['soft_count'],
        q=5,
        labels=False,
        duplicates='drop',
    )
    non_donors = stations_gdf[stations_gdf['soft_count'] == 0].copy()

    hover = HoverTool(
        tooltips=[
            ('Station ID', '@official_id'),
            ('Soft count', '@soft_count{0.0}'),
        ]
    )

    p_map = figure(
        width=900,
        height=520,
        x_axis_type='mercator',
        y_axis_type='mercator',
        tools='pan,wheel_zoom,reset,save',
        toolbar_location='right',
    )
    p_map.add_tools(hover)
    p_map.add_tile('CartoDB Positron')
    p_map.axis.visible = False

    nd_src = ColumnDataSource(
        {
            'x': non_donors.geometry.x.values,
            'y': non_donors.geometry.y.values,
            'official_id': non_donors['official_id'].values,
            'soft_count': non_donors['soft_count'].values,
        }
    )
    p_map.scatter(
        x='x',
        y='y',
        source=nd_src,
        color='#000000',
        size=7,
        fill_alpha=0.0,
        line_width=2,
        line_color='#000000',
        legend_label='No representation',
    )

    for quintile, color, label in zip(range(5), _COLORS, _LABELS):
        sub = donors[donors['quintile'] == quintile]
        if sub.empty:
            continue
        src = ColumnDataSource(
            {
                'x': sub.geometry.x.values,
                'y': sub.geometry.y.values,
                'official_id': sub['official_id'].values,
                'soft_count': sub['soft_count'].values,
            }
        )
        p_map.scatter(
            x='x',
            y='y',
            source=src,
            color=color,
            size=9,
            alpha=0.9,
            legend_label=label,
        )

    p_map.legend.location = 'top_right'
    p_map.legend.title = 'Soft count quintile'
    p_map.legend.background_fill_alpha = 0.7
    p_map.legend.click_policy = 'hide'
    return p_map


def show_station_importance_map(results_dir=_RESULTS_DIR, stations_path=_STATIONS_PATH):
    p_map = build_station_importance_map(results_dir=results_dir, stations_path=stations_path)
    show(p_map)
    return p_map


def save_station_importance_map_html(
    out_path=_RESULTS_DIR / 'station_rankings.html',
    results_dir=_RESULTS_DIR,
    stations_path=_STATIONS_PATH,
):
    p_map = build_station_importance_map(results_dir=results_dir, stations_path=stations_path)
    output_file(out_path)
    show(p_map)
    return p_map