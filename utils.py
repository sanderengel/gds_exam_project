### General utility functions



###############
### IMPORTS ###
###############

import json
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

def load_feature_grid():
    path = DATA_DIR / 'features' / 'feature_grid.feather'
    feature_grid = pd.read_feather(path)
    return feature_grid
