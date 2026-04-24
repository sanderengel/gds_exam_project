### General utility functions



###############
### IMPORTS ###
###############

import json
import pandas as pd



#################
### FUNCTIONS ###
#################

def get_timeline(df: pd.DataFrame) -> pd.DatetimeIndex:
    # Define absolute start and end of timeline
    start_time = df['hour_bin'].min().floor('d')
    end_time = df['hour_bin'].max().ceil('d') - pd.Timedelta(hours = 1)

    # Generate all hours between the bounds
    return pd.date_range(start = start_time, end = end_time, freq = 'h')

def get_data_map(df: pd.DataFrame) -> dict:
    # Pre-group data into dict for fast lookup
    return {hour: group for hour, group in df.groupby('hour_bin')}

def load_lightning_df() -> pd.DataFrame:
    lightning_path = 'data/lightning/california_lightning_siege_2020.feather'
    lightning = pd.read_feather(lightning_path)
    lightning = lightning.sort_values(by = 'timestamp', ascending = True)
    return lightning

def load_fire_df():
    fire_path = 'data/fire/california_fire_polygons.feather'
    fire = pd.read_feather(fire_path)
    fire['geometry'] = fire['geometry'].map(json.loads)
    fire = fire.sort_values(by = 'hour_bin', ascending = True)
    return fire

def load_cell_hours():
    cell_hours_path = 'data/grid_data_base.feather'
    cell_hours = pd.read_feather(cell_hours_path)
    return cell_hours
