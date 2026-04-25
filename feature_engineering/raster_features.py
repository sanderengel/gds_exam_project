### Sample raster features



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
    1: 0,  # Water, not ignitable
    2: 10, # Trees, highly ignitable
    4: 2,  # Flooded vegetation, slightly ignitable
    5: 4,  # Crops, somewhat ignitable
    7: 1,  # Built area, barely ignitable
    8: 1,  # Bare ground, barely ignitable
    9: 0,  # Snow/ice, not ignitable
    11: 8  # Rangeland, highly ignitable
}


#################
### FUNCTIONS ###
#################

def _fetch_slope_data(
    bbox: list,
    lats: tuple,
    x_da: xr.DataArray,
    y_da: xr.DataArray,
    catalog: Client
) -> np.ndarray:
    print('Fetching elevation data and computing slopes...')
    # Fetch elevation from NASADEM
    search_dem = catalog.search(collections = ['nasadem'], bbox = bbox, limit = 100)
    items_dem = search_dem.item_collection()
    print(f'  Found {len(items_dem)} elevation tiles.')

    dem_stack = stackstac.stack(
        items_dem,
        assets = ['elevation'],
        epsg = 4326,
        bounds_latlon = bbox,
        resolution = .001,
        chunksize = 2048,
        gdal_env = stackstac.DEFAULT_GDAL_ENV.updated(HTTPS_ENV_ADDITIONS)
    )
    print('  Computing elevation mosaic...')
    dem_raster = stackstac.mosaic(dem_stack.sel(band = 'elevation')).compute()

    # Compute gradients
    avg_lat = np.mean(lats)
    meters_per_degree_lat = 111000
    meters_per_degree_lon = meters_per_degree_lat * np.cos(np.radians(avg_lat))
    dy, dx = np.gradient(dem_raster.values, .001 * meters_per_degree_lat, .001 * meters_per_degree_lon)
    slope = np.sqrt(dx**2 + dy**2)
    slope_deg = np.rad2deg(np.arctan(slope))
    slope_da = dem_raster.copy(data = slope_deg).fillna(0)

    return slope_da.sel(x = x_da, y = y_da, method = 'nearest').values

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
    return pd.Series(landcover).map(FUEL_MAP).fillna(0).astype(np.int8)

def add_environmental_data(grid: pd.DataFrame, cells: list, coordinate_lookup: pd.DataFrame) -> pd.DataFrame: 
    # Initialize PC catalog
    catalog = pystac_client.Client.open(
        'https://planetarycomputer.microsoft.com/api/stac/v1',
        modifier = planetary_computer.sign_inplace,
    )

    # Get spatial lookup and coordinate arrays
    x_da, y_da = get_coordinate_arrays(coordinate_lookup)

    lats, lons = zip(*[h3.cell_to_latlng(c) for c in cells])
    bbox = [min(lons), min(lats), max(lons), max(lats)]
    
    # Get slope data
    coordinate_lookup['slope'] = _fetch_slope_data(bbox, lats, x_da, y_da, catalog)

    # Get fuel data
    landcover = _fetch_landcover_data(bbox, x_da, y_da, catalog)
    coordinate_lookup['fuel_score'] = _get_fuel_scores(landcover)

    # Map onto grid
    grid = grid.merge(
        coordinate_lookup[['h3_id', 'slope', 'fuel_score']],
        on = 'h3_id',
        how = 'left'
    )

    return grid
