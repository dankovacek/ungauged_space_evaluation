from pathlib import Path

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

DATA_DIR = Path('data')
RESULTS_DIR = DATA_DIR / 'results'
CACHE_DIR = DATA_DIR / 'cache'

# ---------------------------------------------------------------------------
# Gauged network (reference) files
# ---------------------------------------------------------------------------

STATION_CSV = DATA_DIR / 'Watershed_descriptors_20260203_with_stats.csv'
STATION_GEOJSON = DATA_DIR / 'filtered_station_set.geojson'

# ---------------------------------------------------------------------------
# Ungauged test subset (VCI region parquet)
# ---------------------------------------------------------------------------

VCI_PARQUET = Path(
    '/home/danbot2/code_5820/large_sample_hydrology/bcub'
    '/processed_data/derived_basins/VCI/VCI_basins_R0.parquet'
)

# ---------------------------------------------------------------------------
# PostgreSQL database
# ---------------------------------------------------------------------------

DB_HOST = '/var/run/postgresql'  # Unix socket directory (avoids TCP auth)
DB_PORT = 5432
DB_NAME = 'basins'
DB_USER = 'danbot2'
DB_SCHEMA = 'basins_schema'
DB_ATTRIBUTES_TABLE = 'basin_attributes'

# psycopg2 DSN string — host is the socket directory for peer authentication
DB_DSN = f'host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER}'

# ---------------------------------------------------------------------------
# KLD prediction results and XGBoost models  (used in later phase)
# ---------------------------------------------------------------------------

KLD_TRIAL_SUMMARY = (
    DATA_DIR / 'KLD_prediction_results' / 'trial_results_summary.csv'
)
XGB_MODELS_DIR = DATA_DIR / 'xgb_models'

# Model set used for inference.
XGB_MODEL_SET = 'proximity_plus_attributes'

# Trial selected for inference: the trial whose mean out-of-sample MAE is
# closest to the median across all 10 trials, to avoid ex-post cherry-picking.
# Derived once from data/KLD_prediction_results/trial_results_summary.csv;
# models from dankovacek/divergence_prediction.
XGB_SELECTED_TRIAL = 6

# ---------------------------------------------------------------------------
# Catchment descriptor feature groups  (canonical / CSV-aligned names)
# ---------------------------------------------------------------------------

TERRAIN_FEATURES = [
    'drainage_area_km2',
    'elevation_m',
    'slope_deg',
    'aspect_deg',
]

LAND_COVER_FEATURES = [
    'land_use_forest_frac_2010',
    'land_use_grass_frac_2010',
    'land_use_wetland_frac_2010',
    'land_use_water_frac_2010',
    'land_use_urban_frac_2010',
    'land_use_shrubs_frac_2010',
    'land_use_crops_frac_2010',
    'land_use_snow_ice_frac_2010',
]

CLIMATE_FEATURES = [
    'prcp',
    'srad',
    'swe',
    'tmax',
    'tmin',
    'vp',
    'high_prcp_freq',
    'high_prcp_duration',
    'low_prcp_freq',
    'low_prcp_duration',
]

SOIL_FEATURES = [
    'logk_ice_x100',
    'porosity_x100',
]

ALL_DESCRIPTOR_FEATURES = (
    TERRAIN_FEATURES + LAND_COVER_FEATURES + CLIMATE_FEATURES + SOIL_FEATURES
)

# Physical attributes in the order the saved XGBoost models expect.
# Empirically verified: features are interleaved [donor_a, target_a] pairs
# in the order terrain → land_cover → soil → climate.
# proximity_plus_attributes model appends centroid_distance_km as the last feature.
MODEL_PHYSICAL_ATTRS = (
    TERRAIN_FEATURES + LAND_COVER_FEATURES + SOIL_FEATURES + CLIMATE_FEATURES
)

# KLD thresholds (bits) for ungauged space representation analysis.
REPRESENTATION_THRESHOLDS = [1, 2, 5]

# ---------------------------------------------------------------------------
# CSV column rename  (unit-annotated CSV headers → canonical names)
# ---------------------------------------------------------------------------

CSV_COLUMN_RENAME = {
    'prcp (mm/day)':               'prcp',
    'high_prcp_freq (fraction)':   'high_prcp_freq',
    'low_prcp_freq (fraction)':    'low_prcp_freq',
    'high_prcp_duration (days)':   'high_prcp_duration',
    'low_prcp_duration (days)':    'low_prcp_duration',
    'tmax (degrees c)':            'tmax',
    'tmin (degrees c)':            'tmin',
    'vp (pa)':                     'vp',
    'swe (kg/m2)':                 'swe',
    'srad (w/m2)':                 'srad',
}

# ---------------------------------------------------------------------------
# DB → CSV unit conversions
#
# The BCUB PostgreSQL database stores several columns in different units from
# the CSV training data:
#   prcp          : DB = mm/year (integer)  → CSV = mm/day  → factor = 1/365
#   high/low_prcp_freq  : DB = integer %    → CSV = fraction → factor = 1/100
#   land_use_*_frac_*   : DB = integer %    → CSV = fraction → factor = 1/100
#
# All other feature columns share the same units between DB and CSV.
# ---------------------------------------------------------------------------

_LAND_COVER_COLS_ALL_YEARS = [
    f'land_use_{cls}_frac_{yr}'
    for cls in ['forest', 'shrubs', 'grass', 'wetland', 'crops', 'urban', 'water', 'snow_ice']
    for yr in [2010, 2015, 2020]
]

DB_UNIT_CONVERSIONS: dict[str, float] = {
    'prcp':          1 / 365,
    'high_prcp_freq': 1 / 100,
    'low_prcp_freq':  1 / 100,
    **{col: 1 / 100 for col in _LAND_COVER_COLS_ALL_YEARS},
}

# ---------------------------------------------------------------------------
# 4-NN baseline parameters
# ---------------------------------------------------------------------------

K_NEIGHBOURS = 4

# ---------------------------------------------------------------------------
# Plotting parameters
# ---------------------------------------------------------------------------

ACADEMIC_FONT = "EB Garamond, Palatino Linotype, Palatino, Georgia, serif"
