### Sample fuel scores from raster



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
from pystac_client.client import Client
from spatial_utils import get_coordinate_arrays



#################
### CONSTANTS ###
#################

HTTPS_ENV_ADDITIONS = {
    'GDAL_HTTP_MAX_RETRY': '5',
    'GDAL_HTTP_RETRY_DELAY': '3',
    'GDAL_HTTP_TIMEOUT': '30',
}

FUEL_MAP = {
    1: 0.0,  # Water, not ignitable
    2: 1.0, # Trees, highly ignitable
    4: 0.2,  # Flooded vegetation, slightly ignitable
    5: 0.4,  # Crops, somewhat ignitable
    7: 0.1,  # Built area, barely ignitable
    8: 0.1,  # Bare ground, barely ignitable
    9: 0.0,  # Snow/ice, not ignitable
    11: 0.8  # Rangeland, highly ignitable
}


#################
### FUNCTIONS ###
#################

def _fetch_landcover_data(bbox: list, x_da: xr.DataArray, y_da: xr.DataArray, catalog: Client) -> np.ndarray:
    print('Fetching landcover data...')
    search_lc = catalog.search(
        collections = ['io-lulc-9-class'], 
        bbox = bbox, 
        datetime = '2020', 
        limit = 100
    )

    items_lc = search_lc.item_collection()
    print(f'  Found {len(items_lc)} land cover tiles.')
    lc_stack = stackstac.stack(
        items_lc,
        epsg = 4326,
        bounds_latlon = bbox,
        resolution = .001,
        resampling = rasterio.enums.Resampling.mode,
        chunksize = 2048,
        gdal_env = stackstac.DEFAULT_GDAL_ENV.updated(HTTPS_ENV_ADDITIONS)
    )
    print('  Computing land cover mosaic...')
    lc_raster = stackstac.mosaic(lc_stack).squeeze().compute()

    # Add to lookup
    return lc_raster.sel(x = x_da, y = y_da, method = 'nearest').values

def _get_fuel_scores(landcover: np.ndarray) -> pd.Series:
    # Map land cover to fuel scores
    return pd.Series(landcover).map(FUEL_MAP).fillna(0)

def add_fuel_scores(grid: pd.DataFrame, cells: list, coordinate_lookup: pd.DataFrame) -> pd.DataFrame: 
    # Initialize PC catalog
    catalog = pystac_client.Client.open(
        'https://planetarycomputer.microsoft.com/api/stac/v1',
        modifier = planetary_computer.sign_inplace,
    )

    # Get spatial lookup and coordinate arrays
    x_da, y_da = get_coordinate_arrays(coordinate_lookup)

    lats, lons = zip(*[h3.cell_to_latlng(c) for c in cells])
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    
    # # Get slope data
    # coordinate_lookup['slope'] = _fetch_slope_data(bbox, lats, x_da, y_da, catalog)

    # Get fuel data
    landcover = _fetch_landcover_data(bbox, x_da, y_da, catalog)
    coordinate_lookup['fuel_score'] = _get_fuel_scores(landcover)

    # Map onto grid
    grid = grid.merge(
        coordinate_lookup[['h3_id', 'fuel_score']],
        on = 'h3_id',
        how = 'left'
    )

    return grid
