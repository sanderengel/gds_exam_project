### General utility functions



###############
### IMPORTS ###
###############

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
    fire = fire.sort_values(by = 'hour_bin', ascending = True)
    return fire

def load_risk_df():
    path = DATA_DIR / 'risk' / 'risk_grid.feather'
    risk_grid = pd.read_feather(path)
    risk_grid = risk_grid.sort_values(by = 'hour_bin', ascending = True)
    return risk_grid
