### Process raw data



###############
### IMPORTS ###
###############

import osmnx as ox
import h3
import pandas as pd
import geopandas as gpd
from pathlib import Path



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

# Filter to only keep California observations
epsg = 'EPSG:4326'
ca_boundary = ox.geocode_to_gdf('California, USA').to_crs(epsg)
fire_gdf = gpd.GeoDataFrame(
    fire,
    geometry = gpd.points_from_xy(fire['lon'], fire['lat']),
    crs = epsg
)
fire = gpd.sjoin(
    fire_gdf, 
    ca_boundary[['geometry']], 
    how = 'inner',
    predicate = 'intersects',
).drop(columns = ['geometry', 'index_right'])

# Group by hours and tessellation IDs
fire_agg = fire.groupby(['hour_bin', 'h3_id']).agg({'brightness': 'max'}).reset_index()



############
### SAVE ###
############

fire_agg.to_feather(OUTPUT_PATH)
print(f'Saved {len(fire_agg)} fire polygons to {OUTPUT_PATH}.')
