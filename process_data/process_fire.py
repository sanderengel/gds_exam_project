### Process raw data



###############
### IMPORTS ###
###############

import sys
import json
import h3
import pandas as pd
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import add_json_geometry



#############
### SETUP ###
#############

# Define paths
ROOT = Path(__file__).resolve().parent.parent
FIRE_DIR = ROOT / 'data' / 'fire'
INPUT_PATH = FIRE_DIR / 'DL_FIRE_SV-C2_745271' / 'fire_archive_SV-C2_745271.csv'
OUTPUT_PATH = FIRE_DIR / 'california_fire_polygons.feather'



#################
### LOAD DATA ###
#################

fire = pd.read_csv(INPUT_PATH)



#########################
### CLEAN AND PROCESS ###
#########################

# Keep only vegetation fire
fire = fire[fire['type'] == 0]

# Create timestamp and hour bin from date and time
fire['timestamp'] = pd.to_datetime(
    fire['acq_date'] + ' ' + fire['acq_time'].astype(str).str.zfill(4),
    format = '%Y-%m-%d %H%M'
)
fire['hour_bin'] = fire['timestamp'].dt.floor('h')
fire['timestamp'] = pd.to_datetime(fire['timestamp']).dt.tz_localize(None)

# Keep only relevant columns and rename
fire = fire[['latitude', 'longitude', 'brightness', 'timestamp', 'hour_bin']]
fire = fire.rename(columns = {'latitude': 'lat', 'longitude': 'lon'})

# Add tessellation IDs
fire['h3_id'] = [h3.latlng_to_cell(lat, lon, 7) for lat, lon in zip(fire['lat'], fire['lon'])]

# Group by hours and tessellation IDs
fire_agg = fire.groupby(['hour_bin', 'h3_id']).agg({'brightness': 'max'}).reset_index()

# Pre-calculate the geometry for every unique cell in the data
fire_agg = add_json_geometry(fire_agg)



############
### SAVE ###
############

fire_agg.to_feather(OUTPUT_PATH)
print(f'Saved {len(fire_agg)} fire polygons to {OUTPUT_PATH}.')
