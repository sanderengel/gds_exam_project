### Spatial feature engineering utility functions



###############
### IMPORTS ###
###############

import sys
import h3
import xarray as xr
import pandas as pd
from pathlib import Path
from itertools import product

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import get_timeline


#################
### FUNCTIONS ###
#################

def build_impact_grid(fire: pd.DataFrame, lightning: pd.DataFrame, base_cols: list) -> pd.DataFrame:
    print('Creating cell hours base grid...')

    # Get all unique h3 IDs from the fire data
    fire_cells = set(fire['h3_id'].unique())

    # Add the k=4 impact zone for every lightning strike
    lightning_impact_zone = set()
    lightning_cells = lightning['h3_id'].unique()
    for c in lightning_cells:
        lightning_impact_zone.update(h3.grid_disk(c, 4)) # Cell c plus neighbors within distance 4

    # Combine to get all active cells and impact zone
    impact_cells = list(fire_cells.union(lightning_impact_zone))

    print(f"  Active cells: {len(set(fire['h3_id']).union(set(lightning['h3_id'])))}")
    print(f'  Active cells plus impact zone (k=4): {len(impact_cells)}')

    # Create the full hourly timeline 
    lightning_timeline = get_timeline(lightning)
    fire_timeline = get_timeline(fire)

    if lightning_timeline.equals(fire_timeline):
        timeline = lightning_timeline
    else:
        raise Exception('Lightning timeline does not match fire timeline')

    print(f'  Total hours: {len(timeline)}')

    # Build df
    grid = pd.DataFrame(
        list(product(impact_cells, timeline)), # All combinations of area and time
        columns = base_cols
    )

    print(f'  Total cell hours: {len(grid)}')

    grid = grid.sort_values(base_cols).reset_index(drop = True)
    return grid, impact_cells

def get_coordinate_lookup(cells: list) -> pd.DataFrame:
    print('Building spatial lookup table...')
    lats, lons = zip(*[h3.cell_to_latlng(c) for c in cells])
    coordinate_lookup = pd.DataFrame({
        'h3_id': cells,
        'lat': lats,
        'lon': lons
    })
    return coordinate_lookup

def get_neighbor_lookup(cells: list) -> pd.DataFrame:
    print('Building neighbor lookup table...')
    neighbors = []
    for c in cells:
        for k in range(1, 5):
            for nb in h3.grid_ring(c, k):
                neighbors.append({'target_id': c, 'neighbor_id': nb, 'k': k})
    return pd.DataFrame(neighbors)

def get_coordinate_arrays(coordinate_lookup: pd.DataFrame) -> tuple[xr.DataArray, xr.DataArray]:
    x_da = xr.DataArray(coordinate_lookup['lon'].values, dims = 'h3_index')
    y_da = xr.DataArray(coordinate_lookup['lat'].values, dims = 'h3_index')
    return x_da, y_da

def get_sparse_spatial_map(grid: pd.DataFrame, neighbor_lookup: pd.DataFrame) -> pd.DataFrame:
    # Find spatial neighbors for active lightning cells
    active_lightning = grid[grid['energy_k0'] > 0][['energy_k0']].reset_index()

    # Merge active strikes with neighbors, group by target, time, k
    return (
        active_lightning
        .merge(neighbor_lookup, left_on = 'h3_id', right_on = 'neighbor_id')
        .groupby(['target_id', 'hour_bin', 'k'])['energy_k0'].sum()
    )
