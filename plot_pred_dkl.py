import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import MultiPolygon
import numpy as np
from bokeh.io import output_file, show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, FixedTicker, Title
from bokeh.plotting import figure
from config import ACADEMIC_FONT

_CATEGORIES = [
    ('1\u20132', 1, 2,            '#1a0530'),
    ('2\u20135', 2, 5,            "#d3068f"),
    ('5+',   5, float('inf'), "#ff62cb"),
]

_POINT_SIZE  = 5
_POINT_ALPHA = 0.7
_REGION_SIMPLIFY_M = 2000  # simplification tolerance in metres (EPSG:3005)


def _make_inset(vals):
    q1, med, q3 = np.percentile(vals, [25, 50, 75])
    iqr = q3 - q1
    lo = max(float(vals.min()), q1 - 1.5 * iqr)
    hi = min(float(vals.max()), q3 + 1.5 * iqr)
    pad = iqr * 0.3
    p = figure(
        width=120, height=300,
        toolbar_location=None,
        x_range=(-0.55, 0.55),
        y_range=(lo - pad, hi + pad),
        min_border_left=15, min_border_right=8,
        min_border_top=10, min_border_bottom=8,
    )
    p.outline_line_color = '#aaaaaa00'
    p.xaxis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.background_fill_alpha = 0
    p.yaxis.ticker = FixedTicker(ticks=[round(v, 1) for v in [lo, q1, med, q3, hi]])
    p.yaxis.major_label_text_font = ACADEMIC_FONT
    p.yaxis.major_label_text_font_size = '14pt'
    p.border_fill_alpha = 0.8
    p.add_layout(Title(text='bits / sample', text_font=ACADEMIC_FONT,
                       text_font_size='12pt', align='center'), 'above')
    p.add_layout(Title(text='Predicted KLD', text_font=ACADEMIC_FONT,
                       text_font_size='14pt', align='center'), 'above')
    bx, bhw, chw = 0.0, 0.30, 0.15
    p.quad(
        left=[bx - bhw], right=[bx + bhw],
        bottom=[q1], top=[q3],
        fill_color='#8b005d', fill_alpha=0.25,
        line_color='#8b005d', line_width=1.5,
    )
    p.segment(x0=[bx - bhw], x1=[bx + bhw], y0=[med], y1=[med],
              line_color='#8b005d', line_width=2.5)
    p.segment(x0=[bx, bx], x1=[bx, bx], y0=[lo, q3], y1=[q1, hi],
              line_color='#4d0050', line_width=1.5)
    p.segment(x0=[bx - chw, bx - chw], x1=[bx + chw, bx + chw],
              y0=[lo, hi], y1=[lo, hi],
              line_color='#4d0050', line_width=1.5)
    p.styles = {
        'position': 'absolute',
        'bottom': '20px',
        'left': '50px',
        'z-index': '10',
        'box-shadow': '2px 2px 8px rgba(0,0,0,0.2)',
        'background-color': 'rgba(255, 255, 255, 0)',
    }
    return p


def _geom_to_patches(geom):
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    xs = [list(p.exterior.coords.xy[0]) for p in polys]
    ys = [list(p.exterior.coords.xy[1]) for p in polys]
    return xs, ys


def _make_figure(df, stations_active, stations_disc, region_code, region_xs, region_ys, toolbar_location):
    p = figure(
        width=1000, height=700,
        x_axis_type='mercator', y_axis_type='mercator',
        tools='pan,wheel_zoom,reset,save',
        toolbar_location=toolbar_location,
        # title=f"Predicted min KLD to gauged network  —  region {df['region_code'].iloc[0]}",
    )
    p.add_tile('CartoDB Positron')

    for label, lo, hi, color in _CATEGORIES:
        if hi == float('inf'):
            mask = df['min_predicted_kld'] > lo
        else:
            mask = (df['min_predicted_kld'] > lo) & (df['min_predicted_kld'] <= hi)
        sub = df.loc[mask, ['x', 'y']]
        source = ColumnDataSource(sub)
        p.scatter(
            x='x', y='y', source=source,
            color=color, size=_POINT_SIZE, alpha=_POINT_ALPHA,
            legend_label=label,
        )

    p.patches(
        xs=region_xs, ys=region_ys, line_dash='dashed',
        fill_alpha=0, line_color="#C05E5E", line_width=3.5,
        legend_label=f'{region_code} Region bound',
    )

    p.scatter(
        x='x', y='y', source=ColumnDataSource(stations_disc),
        marker='triangle', color='#ff8c42', size=9, alpha=0.45,
        legend_label='Discontinued stations',
    )
    p.scatter(
        x='x', y='y', source=ColumnDataSource(stations_active),
        marker='triangle', color='#00e676', size=9, alpha=0.9,
        legend_label='Active stations',
    )

    p.legend.location = 'top_right'
    if region_code in ['08A']:
        p.legend.location = 'bottom_left'
    p.legend.title = 'Min predicted \nKL Divergence \n(bits)'
    p.legend.label_text_font = ACADEMIC_FONT
    p.legend.label_text_font_size = '18pt'
    p.legend.title_text_font_size = '22pt'
    p.legend.title_text_font = ACADEMIC_FONT
    p.legend.background_fill_alpha = 0.6
    p.legend.click_policy = 'hide'
    return p


def main():
    parser = argparse.ArgumentParser(description='Plot predicted KLD donor results.')
    parser.add_argument('region', help='Region code, e.g. VCI or YKR')
    args = parser.parse_args()

    path = Path('data/results') / f'kld_donor_{args.region}.parquet'
    df = pd.read_parquet(path)
    df = df[df['min_predicted_kld'] > 1].copy()

    transformer = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
    df['x'], df['y'] = transformer.transform(df['centroid_lon'].values, df['centroid_lat'].values)

    # gauged stations (already EPSG:3857): show all stations within the plot bounding box
    stations_gdf = gpd.read_file('data/filtered_station_set.geojson')
    x_min, x_max = df['x'].min(), df['x'].max()
    y_min, y_max = df['y'].min(), df['y'].max()
    stn_x = stations_gdf.geometry.x.values
    stn_y = stations_gdf.geometry.y.values
    bbox_mask = (stn_x >= x_min) & (stn_x <= x_max) & (stn_y >= y_min) & (stn_y <= y_max)
    stations_gdf = stations_gdf[bbox_mask].copy()
    descriptors = pd.read_csv('data/Watershed_descriptors_20260203_with_stats.csv',
                              usecols=['official_id', 'active'])
    status = descriptors.set_index('official_id')['active']
    stations_gdf['active'] = stations_gdf['official_id'].map(status).fillna(True).astype(bool)

    def _stn_xy(mask):
        sub = stations_gdf[mask]
        return pd.DataFrame({'x': sub.geometry.x.values, 'y': sub.geometry.y.values})

    stations_active = _stn_xy(stations_gdf['active'])
    stations_disc   = _stn_xy(~stations_gdf['active'])

    # region boundary: dissolve, simplify, reproject
    regions_gdf = gpd.read_file('data/BCUB_regions_merged_R0.geojson')
    region_geom = regions_gdf[regions_gdf['region_code'] == args.region].geometry.union_all()
    region_geom = region_geom.simplify(_REGION_SIMPLIFY_M, preserve_topology=True)
    region_geom = (gpd.GeoSeries([region_geom], crs='EPSG:3005')
                      .to_crs('EPSG:3857').iloc[0])
    region_xs, region_ys = _geom_to_patches(region_geom)

    out_dir = Path('data/results')

    html_path = out_dir / f'kld_donor_{args.region}_plot.html'
    output_file(str(html_path))
    p_map = _make_figure(df, stations_active, stations_disc, args.region, region_xs, region_ys, toolbar_location='right')
    vals = df['min_predicted_kld'].replace([np.inf, -np.inf], np.nan).dropna().values
    p_inset = _make_inset(vals)
    map_with_inset = column(p_map, p_inset)
    map_with_inset.styles = {'position': 'relative', 'display': 'inline-block'}
    show(map_with_inset)
    print(f'Saved HTML: {html_path}')


if __name__ == '__main__':
    main()
