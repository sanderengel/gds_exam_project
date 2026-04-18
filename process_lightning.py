### Process raw data



###############
### IMPORTS ###
###############

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from glob import glob



#############
### SETUP ###
#############

# Define paths
INPUT_BASE_PATH = 'data/lightning/glmcierra_1-20260402_162540'
OUTFILE_PATH = 'data/lightning/california_lightning_siege_2020.feather'

# Load California geometry
ca_boundary = ox.geocode_to_gdf('California, USA')
ca_boundary = ca_boundary.to_crs('EPSG:4326')

# Define rough bbox, used for inital filtering pass
bbox = {'min_lon': -124.5, 'max_lon': -114.1, 'min_lat': 32.5, 'max_lat': 42.0}



#################
### FUNCTIONS ###
#################

def extract_values(ds: xr.Dataset) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray
]:
    lats = ds['FLASH_LAT'].values
    lons = ds['FLASH_LON'].values
    energy = ds['FLASH_ENERGY'].values
    offsets = ds['FLASH_TIME_OFFSET_OF_FIRST_EVENT'].values
    return lats, lons, energy, offsets
    
def get_bbox_mask(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    return (
        (lons >= bbox['min_lon']) &
        (lons <= bbox['max_lon']) &
        (lats >= bbox['min_lat']) &
        (lats <= bbox['max_lat'])
    )

def get_temp_gdf(
    lats: np.ndarray,
    lons: np.ndarray,
    energy: np.ndarray,
    offsets: np.ndarray,
    mask: np.ndarray
) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            'lat': lats[mask],
            'lon': lons[mask],
            'energy': energy[mask],
            'offset': offsets[mask],
        },
        geometry = gpd.points_from_xy(lons[mask], lats[mask]), # Create geometry from coordinates
        crs = 'EPSG:4326'
    )

def _add_lightning_colors(df: pd.DataFrame, cmap: str = 'Wistia') -> pd.DataFrame:
    energy_vals = df['energy'].values
    norm = mcolors.LogNorm(vmin = energy_vals.min(), vmax = energy_vals.max())
    cmap = plt.get_cmap(cmap)
    rgba_colors = cmap(norm(energy_vals))
    df['color_hex'] = [mcolors.to_hex(rgba) for rgba in rgba_colors]
    return df



###########################################
### FILTER CALIFORNIA LIGHTNING STRIKES ###
###########################################

flashes = []
filepaths = glob(os.path.join(INPUT_BASE_PATH, '*.nc')) # Extract all .nc files

n_files = len(filepaths)
print(f'Filtering lightning flashes in {n_files} files for exact California geometry...')

# Iterate over each file
for i, fp in enumerate(filepaths):
    try:
        # Attempt to load the file in xarray
        with xr.open_dataset(fp) as ds:
            # Extract latitudes, longitudes, energy, time offsets
            lats, lons, energy, offsets = extract_values(ds)

            # Get rought cut mask
            mask = get_bbox_mask(lats, lons)

            if any(mask):
                # Define temporary gdf to store flashes within bbox
                gdf_temp = get_temp_gdf(lats, lons, energy, offsets, mask)

                # Spatial join keeps only points within CA polygon
                gdf_ca = gpd.sjoin(gdf_temp, ca_boundary[['geometry']], how = 'inner', predicate = 'intersects')

                if not gdf_ca.empty:
                    # Calculate actual timestamps from time offsets
                    base_time = pd.to_datetime(ds.attrs['TIME_COVERAGE_START'])
                    gdf_ca['timestamp'] = base_time + pd.to_timedelta(gdf_ca['offset'], unit = 's')
                    flashes.append(gdf_ca[['lat', 'lon', 'energy', 'timestamp']])

        if (i + 1) % 10 == 0 or i + 1 == n_files:
            print(f'Filtered {i + 1}/{n_files} files.')

    except Exception as e:
        print(f'Error in {os.path.basename(fp)}: {e}')



################################
### CLEAN, ENHANCE, AND SAVE ###
################################

if flashes:
    flashes_df = pd.concat(flashes, ignore_index = True)
    flashes_df = _add_lightning_colors(flashes_df)
    flashes_df['hour_bin'] = flashes_df['timestamp'].dt.floor('h')
    flashes_df.to_feather(OUTFILE_PATH)
    print(f'Saved {len(flashes_df)} flashes to {OUTFILE_PATH}.')
else:
    print('No flashes found within the California boundary.')
