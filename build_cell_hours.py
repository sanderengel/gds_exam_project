### Build cell hours data table



###############
### IMPORTS ###
###############

import pystac_client
import planetary_computer
import stackstac
import rasterio
import h3
import xarray as xr
import numpy as np
import pandas as pd
from utils import get_timeline, load_lightning_df, load_fire_df
from itertools import product



#################
### LOAD DATA ###
#################

lightning = load_lightning_df()
fire = load_fire_df()



########################
### BUILD CELL HOURS ###
########################

base_cols = ['h3_id', 'hour_bin']

# Get all unique h3 IDs from the fire data
fire_cells = set(fire['h3_id'].unique())

# Add the k=4 impact zone for every lightning strike
lightning_impact_zone = set()
lightning_cells = lightning['h3_id'].unique()
for c in lightning_cells:
    lightning_impact_zone.update(h3.grid_disk(c, 4)) # Cell c plus neighbors within distance 4

# Combine to get all active cells and impact zone
impact_cells = list(fire_cells.union(lightning_impact_zone))

print(f"Active cells: {len(set(fire['h3_id']).union(set(lightning['h3_id'])))}")
print(f'Active cells plus impact zone (k=4): {len(impact_cells)}')

# Create the full hourly timeline 
lightning_timeline = get_timeline(lightning)
fire_timeline = get_timeline(fire)

if lightning_timeline.equals(fire_timeline):
    timeline = lightning_timeline
else:
    raise Exception('Lightning timeline does not match fire timeline')

print(f'Total hours: {len(timeline)}')

# Build df
grid_df = pd.DataFrame(
    list(product(impact_cells, timeline)), # All combinations of area and time
    columns = base_cols
)
grid_df = grid_df.sort_values(base_cols).reset_index(drop = True)

# Create lookup dataframe
lats, lons = zip(h3.cell_to_latlng(c) for c in impact_cells)
spatial_lookup = pd.DataFrame({
    'h3_id': impact_cells,
    'lat': lats,
    'lon': lons
})

# Prep coordinate arrays for xr sampling
x_da = xr.DataArray(spatial_lookup['lon'].values, dims = 'h3_index')
y_da = xr.DataArray(spatial_lookup['lat'].values, dims = 'h3_index')




#######################
### MAP FIRE LABELS ###
#######################

# Create simplified fire df
fire_targets = fire[base_cols].copy()
fire_targets['has_fire'] = 1

# Merge onto the grid
grid_df = grid_df.merge(fire_targets, on = base_cols, how = 'left')
grid_df['has_fire'] = grid_df['has_fire'].fillna(0).astype(int)

# Computed "ignited" label (y)
grid_df['ignited'] = (
    grid_df.iloc[::-1]                     # Flip the df
    .groupby('h3_id')['has_fire']          # Group by spatial unit
    .rolling(window = 12, min_periods = 1) # Roll 12 steps forward (due to flip)
    .max()                                 # Any fire within next 12 hours equals ignition
    .reset_index(level = 0, drop = True)   # Clean index
    .iloc[::-1]                            # Flip back
    .shift(-1)                             # Exclude current hour t
    .fillna(0)
    .astype(int)
)



############################
### MAP LIGHTNING ENERGY ###
############################

# Aggregate raw strikes to hourly cell totals (k=0)
lightning_k0 = (
    lightning.groupby(base_cols)['energy']
    .sum()
    .reset_index()
).rename({'energy': 'energy_k0'})
grid_df = grid_df.merge(
    lightning_k0, 
    on = base_cols, 
    how = 'left'
).fillna({'energy_k0': 0})

# Pre-compute aggregated energy for k-distance neighbors
K_VALUES = range(1, 5)
neighbor_data = []
for c in impact_cells:
    for k in K_VALUES:
        # Get neighbors at distance k
        for nb in h3.grid_ring(c, k):
            neighbor_data.append({'target_id': c, 'neighbor_id': nb, 'k': k})

# Convert to df to create maps of which cells contribute to which targets
nb_lookup = pd.DataFrame(neighbor_data).drop_duplicates()

# Iterate through k to build energy columns
for k in K_VALUES:
    print(f'Aggregating energy for k={k}...')

    # Filter lookup for k
    ring_lookup = nb_lookup[nb_lookup['k'] <= k]

    # TODO: Continue with the ring_k sums



##################################
### GET ELEVATION SLOPE RASTER ###
##################################

# Define bbox from the h3 cells

bbox = [min(lons), min(lats), max(lons), max(lats)]

# Initialize PC catalog
catalog = pystac_client.Client.open(
    'https://planetarycomputer.microsoft.com/api/stac/v1',
    modifier = planetary_computer.sign_inplace,
)

# Fetch elevation from NASADEM
search_dem = catalog.search(collections = ['nasadem'], bbox = bbox, limit = 100)
items_dem = search_dem.item_collection()
print(f'Found {len(items_dem)} elevation tiles.')

if items_dem:
    dem_stack = stackstac.stack(
        items_dem,
        assets = ['elevation'],
        epsg = 4326,
        bounds_latlon = bbox,
        resolution = .001
    )
    dem_raster = dem_stack.sel(band = 'elevation').max(dim = 'time').squeeze().compute()

    # Compute gradients
    avg_lat = np.mean(lats)
    meters_per_degree_lat = 111000
    meters_per_degree_lon = meters_per_degree_lat * np.cos(np.radians(avg_lat))
    dy, dx = np.gradient(dem_raster.values, .001 * meters_per_degree_lat, .001 * meters_per_degree_lon)
    slope = np.sqrt(dx**2 + dy**2)
    slope_deg = np.rad2deg(np.arctan(slope))
    slope_da = dem_raster.copy(data = slope_deg).fillna(0)

    # Add to lookup
    spatial_lookup['slope'] = slope_da.sel(x = x_da, y = y_da, method = 'nearest').values
else:
    spatial_lookup['slope'] = None




#############################
### GET LAND COVER RASTER ###
#############################

search_lc = catalog.search(
    collections = ['io-lulc-9-class'], 
    bbox = bbox, 
    datetime = '2020', 
    limit = 100
)

items_lc = search_lc.item_collection()
print(f'Found {len(items_lc)} land cover tiles.')
if items_lc:
    lc_stack = stackstac.stack(
        items_lc,
        epsg = 4326,
        bounds_latlon = bbox,
        resolution = .001,
        resampling = rasterio.enums.Resampling.mode,
        gdal_env = stackstac.DEFAULT_GDAL_ENV.updated({
            'GDAL_HTTP_MAX_RETRY': '5',
            'GDAL_HTTP_RETRY_DELAY': '3'
        })
    )
    lc_raster = lc_stack.max(dim = 'time').squeeze().compute()

    # Add to lookup
    spatial_lookup['landcover'] = lc_raster.sel(x = x_da, y = y_da, method = 'nearest').values
else:
    spatial_lookup['landcover'] = None



###################################
### MAP LOOKUP TO GRID AND SAVE ###
###################################

# Map onto grid
grid_df = grid_df.merge(
    spatial_lookup[['h3_id', 'slope', 'landcover']],
    on = 'h3_id',
    how = 'left'
)

SAVE_PATH = 'data/grid_data_base.feather'
grid_df.to_feather(SAVE_PATH)
print(f'Saved grid data to {SAVE_PATH}.')
