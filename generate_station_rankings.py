import geopandas as gpd
import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path

from bokeh.io import output_file, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, FixedTicker, Label, Title
from bokeh.plotting import figure
from config import ACADEMIC_FONT

_COLORS = ['#0d0014', '#4d0050', '#8b005d', '#cc0084', '#ff00a8']
_LABELS = ['Q1 (lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (highest)']

# ── load all parquet files ────────────────────────────────────────────────────
processed_dir = Path('data/results')
files = sorted(processed_dir.glob('kld_donor_*.parquet'))
frames = [pd.read_parquet(f) for f in files]
df = pd.concat(frames, ignore_index=True)

# Simple count: how many basins name each station as the single best donor
hard_counts = Counter(df['best_donor_official_id'])

# Soft count: each basin distributes 1 vote equally among all tied donors
soft_counts = Counter()
for _, r in df.iterrows():
    donors_str = r['donors_within_5pct']
    donors = donors_str.split(',') if isinstance(donors_str, str) and donors_str else [r['best_donor_official_id']]
    weight = 1.0 / len(donors)
    for d in donors:
        soft_counts[d] += weight

top10 = pd.DataFrame({'station': [s for s, _ in Counter(hard_counts).most_common(10)]})
top10['hard_count'] = top10['station'].map(hard_counts)
top10['soft_count'] = top10['station'].map(soft_counts).round(1)
top10 = top10.sort_values('hard_count', ascending=False).reset_index(drop=True)
print(top10.to_string(index=False))

# ── empirical CDF scatter ─────────────────────────────────────────────────────
counts_arr = np.sort(list(hard_counts.values()))
n = len(counts_arr)
cdf_y = np.arange(1, n + 1) / n

p_cdf = figure(
    width=900, height=400,
    x_axis_label='Soft count (basins represented)',
    y_axis_label='Cumulative fraction of stations',
    tools='pan,wheel_zoom,reset,save',
    toolbar_location='right',
    x_axis_type='log',
)
p_cdf.scatter(counts_arr, cdf_y, size=5, color='#8b005d', alpha=0.7)
p_cdf.xaxis.axis_label_text_font = ACADEMIC_FONT
p_cdf.yaxis.axis_label_text_font = ACADEMIC_FONT
p_cdf.xaxis.axis_label_text_font_size = '16pt'
p_cdf.yaxis.axis_label_text_font_size = '16pt'

# ── map ───────────────────────────────────────────────────────────────────────
stations_gdf = gpd.read_file('data/filtered_station_set.geojson').to_crs('EPSG:3857')
stations_gdf['soft_count'] = stations_gdf['official_id'].map(soft_counts).fillna(0).astype(int)

donors = stations_gdf[stations_gdf['soft_count'] > 0].copy()
donors['quintile'] = pd.qcut(donors['soft_count'], q=5, labels=False, duplicates='drop')

non_donors = stations_gdf[stations_gdf['soft_count'] == 0].copy()
print(len(stations_gdf))
print(asdfsadf)
p_map = figure(
    width=800, height=460,
    x_axis_type='mercator', y_axis_type='mercator',
    tools='pan,wheel_zoom,reset,save',
    toolbar_location='right',
)
p_map.add_tile('CartoDB Positron')

p_map.scatter(
    x=non_donors.geometry.x.values, y=non_donors.geometry.y.values,
    color="#000000", size=7, fill_alpha=0.0, 
    line_width=2, line_color="#000000",    
    legend_label='No representation',
)
for q, color, label in zip(range(5), _COLORS, _LABELS):
    sub = donors[donors['quintile'] == q]
    if sub.empty:
        continue
    p_map.scatter(
        x=sub.geometry.x.values, y=sub.geometry.y.values,
        color=color, size=9, alpha=0.9,
        legend_label=label,
    )

p_map.legend.location = 'top_right'
p_map.legend.title = 'Soft count quintile'
p_map.legend.label_text_font = ACADEMIC_FONT
p_map.legend.label_text_font_size = '14pt'
p_map.legend.title_text_font = ACADEMIC_FONT
p_map.legend.title_text_font_size = '16pt'
p_map.legend.background_fill_alpha = 0.6
p_map.axis.visible = False
# p_map.grid.visible = False

# ── inset: distribution of optimal-donor KLD ─────────────────────────────────
_vals = df['min_predicted_kld'].replace([np.inf, -np.inf], np.nan).dropna().values
_q1, _med, _q3 = np.percentile(_vals, [25, 50, 75])
_iqr = _q3 - _q1
_lo = max(float(_vals.min()), _q1 - 1.5 * _iqr)
_hi = min(float(_vals.max()), _q3 + 1.5 * _iqr)
_pad = _iqr * 0.3

p_inset = figure(
    width=120, height=300,
    toolbar_location=None,
    x_range=(-0.55, 0.55),
    y_range=(_lo - _pad, _hi + _pad),
    min_border_left=15, min_border_right=8,
    min_border_top=10, min_border_bottom=8,
)
p_inset.outline_line_color = "#aaaaaa00"
p_inset.xaxis.visible = False
p_inset.xgrid.visible = False
p_inset.ygrid.visible = False
p_inset.background_fill_alpha = 0
p_inset.yaxis.ticker = FixedTicker(ticks=[round(v, 1) for v in [_lo, _q1, _med, _q3, _hi]])
p_inset.yaxis.major_label_text_font = ACADEMIC_FONT
p_inset.yaxis.major_label_text_font_size = '14pt'
p_inset.border_fill_alpha = 0.8
p_inset.add_layout(Title(text='bits / sample', text_font=ACADEMIC_FONT,
                         text_font_size='12pt', align='center'), 'above')
p_inset.add_layout(Title(text='Predicted KLD', text_font=ACADEMIC_FONT,
                         text_font_size='14pt', align='center'), 'above')

_bx, _bhw, _chw = 0.0, 0.30, 0.15
p_inset.quad(
    left=[_bx - _bhw], right=[_bx + _bhw],
    bottom=[_q1], top=[_q3],
    fill_color='#8b005d', fill_alpha=0.25,
    line_color='#8b005d', line_width=1.5,
)
p_inset.segment(
    x0=[_bx - _bhw], x1=[_bx + _bhw],
    y0=[_med], y1=[_med],
    line_color='#8b005d', line_width=2.5,
)
p_inset.segment(
    x0=[_bx, _bx], x1=[_bx, _bx],
    y0=[_lo, _q3], y1=[_q1, _hi],
    line_color='#4d0050', line_width=1.5,
)
p_inset.segment(
    x0=[_bx - _chw, _bx - _chw],
    x1=[_bx + _chw, _bx + _chw],
    y0=[_lo, _hi], y1=[_lo, _hi],
    line_color='#4d0050', line_width=1.5,
)
# Position p_inset as a CSS overlay over the bottom-left of p_map.
p_inset.styles = {
    'position': 'absolute',
    'bottom': '20px',
    'left': '50px',
    'z-index': '10',
    'box-shadow': '2px 2px 8px rgba(0,0,0,0.2)',
    # set fill background alpha to 0
    'background-color': 'rgba(255, 255, 255, 0)',
}
map_with_inset = column(p_map, p_inset)
map_with_inset.styles = {'position': 'relative', 'display': 'inline-block'}

out_path = 'data/results/station_rankings.html'
output_file(out_path)
show(column(p_cdf, map_with_inset))