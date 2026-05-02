### General utility functions



###############
### IMPORTS ###
###############

import json
import h3
import pandas as pd
from pathlib import Path



#############
### SETUP ###
#############

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'



#################
### FUNCTIONS ###
#################

def get_timeline(df: pd.DataFrame, start_offset_hours: int = 0) -> pd.DatetimeIndex:
    # Define absolute start and end of timeline
    start_time = df['hour_bin'].min().floor('d') + pd.Timedelta(hours = start_offset_hours)
    end_time = df['hour_bin'].max().ceil('d') - pd.Timedelta(hours = 1)

    # Generate all hours between the bounds
    return pd.date_range(start = start_time, end = end_time, freq = 'h')

def get_data_map(df: pd.DataFrame) -> dict:
    # Pre-group data into dict for fast lookup
    return {hour: group for hour, group in df.groupby('hour_bin')}

def load_lightning_df() -> pd.DataFrame:
    path = DATA_DIR / 'lightning' / 'california_lightning_siege_2020.feather'
    lightning = pd.read_feather(path)
    lightning = lightning.sort_values(by = 'timestamp', ascending = True)
    return lightning

def load_fire_df():
    path = DATA_DIR / 'fire' / 'california_fire_polygons.feather'
    fire = pd.read_feather(path)
    fire['geometry'] = fire['geometry'].map(json.loads)
    fire = fire.sort_values(by = 'hour_bin', ascending = True)
    return fire

def load_risk_grid():
    path = DATA_DIR / 'risk' / 'risk_grid.feather'
    risk_grid = pd.read_feather(path)
    risk_grid = risk_grid.sort_values(by = 'hour_bin', ascending = True)
    return risk_grid

def load_risk_enhanced_grid():
    path = DATA_DIR / 'risk' / 'risk_grid_enhanced.feather'
    risk_grid_enhanced = pd.read_feather(path)
    risk_grid_enhanced['geometry'] = risk_grid_enhanced['geometry'].map(json.loads)
    risk_grid_enhanced = risk_grid_enhanced.sort_values(by = 'hour_bin', ascending = True)
    return risk_grid_enhanced

def add_json_geometry(df: pd.DataFrame) -> pd.DataFrame:
    # Serialize geometries as JSON strings to avoid feather storing as arrays
    print('Adding json geometry column...')
    df['geometry'] = df['h3_id'].map(
        lambda x: json.dumps([list(c) for c in h3.cell_to_boundary(x)])
    )
    return df