### Process raw data



###############
### IMPORTS ###
###############

import json
import h3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors



#############
### SETUP ###
#############

# Define paths
INPUT_PATH = 'data/fire/DL_FIRE_SV-C2_730956/fire_archive_SV-C2_730956.csv'
OUTFILE_PATH = 'data/fire/california_fire_polygons.feather'



#################
### READ DATA ###
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
unique_cells = fire_agg['h3_id'].unique()
boundary_map = {cell: h3.cell_to_boundary(cell) for cell in unique_cells}
# Serialize geometries as JSON strings to avoid feather storing as arrays
fire_agg['geometry'] = fire_agg['h3_id'].map(
    lambda x: json.dumps([list(c) for c in h3.cell_to_boundary(x)])
)

# # Add color map
# norm = mcolors.Normalize(vmin = fire['brightness'].min(), vmax = fire['brightness'].max())
# cmap = mcolors.LinearSegmentedColormap.from_list('fire', ['#4d0000', '#ff0000'])
# fire['color_hex'] = [mcolors.to_hex(cmap(norm(v))) for v in fire['brightness']]



############
### SAVE ###
############

fire_agg.to_feather(OUTFILE_PATH)
print(f'Saved {len(fire_agg)} fire polygons to {OUTFILE_PATH}.')
