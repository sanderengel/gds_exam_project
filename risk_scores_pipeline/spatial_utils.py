### Spatial feature engineering utility functions



###############
### IMPORTS ###
###############

import h3
import numpy as np
import xarray as xr
import pandas as pd



#################
### FUNCTIONS ###
#################

def get_unique_cells(df: pd.DataFrame) -> set:
    return df['h3_id'].unique().tolist()

def build_sparse_impact_grid(
    fire: pd.DataFrame,
    lightning: pd.DataFrame,
    neighbor_lookup: pd.DataFrame,
    base_cols: list,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    max_k: int = 4,
    w: int = 72,
) -> tuple[pd.DataFrame, str]:
    print(f'Creating sparse impact grid by pushing lightning energy (k<={max_k}, w={w})...')

    # Expand spatially by mapping strikes to neighbors
    print('  Performing spatial expansion...')
    spatial_impact = lightning.merge(
        neighbor_lookup[neighbor_lookup['k'] <= max_k],
        left_on = 'h3_id',
        right_on = 'neighbor_id'
    ).groupby(['target_id', 'hour_bin'])['energy'].sum().reset_index()
    spatial_impact = spatial_impact.rename(columns = {'target_id': 'h3_id'})
    print(f'    Created spatial impact table with {len(spatial_impact)} rows.')

    # Expand temporaly by pushing energy forward w hours
    print('  Performing temporal expansion...')
    offsets = pd.DataFrame({'offset': pd.to_timedelta(range(w), unit = 'h')})
    energy_grid = (
        spatial_impact.assign(key = 1)
        .merge(offsets.assign(key = 1), on = 'key')
        .drop('key', axis = 1)
    )
    energy_grid['hour_bin'] += energy_grid['offset']
    print(f'    Created full lightning energy grid with {len(energy_grid)} rows.')

    # Sum overlapping energy windows
    energy_col = f'energy_k{max_k}_w{w}'
    energy_grid = energy_grid.groupby(['h3_id', 'hour_bin'])['energy'].sum().reset_index()
    energy_grid = energy_grid.rename(columns = {'energy': energy_col})

    # Union with fire to ensure fire cell-hours exist regardsless of lightning
    print('  Merging fire observations...')
    fire_seeds = fire[base_cols].copy()
    fire_seeds['has_fire'] = 1
    impact_grid = energy_grid.merge(fire_seeds, on = base_cols, how = 'outer')
    impact_grid['has_fire'] = impact_grid['has_fire'].fillna(0).astype(np.int8)
    impact_grid[energy_col] = impact_grid[energy_col].fillna(0)
    print(f'    Created full lightning and fire impact grid with {len(impact_grid)} rows.')

    # Cut off anything outside start and end time
    impact_grid = impact_grid[
        (impact_grid['hour_bin'] >= start_time) &
        (impact_grid['hour_bin'] <= end_time)
    ]

    impact_grid = impact_grid.sort_values(base_cols).reset_index(drop = True)
    return impact_grid, energy_col

def get_coordinate_lookup(cells: list) -> pd.DataFrame:
    print('Building spatial lookup table...')
    lats, lons = zip(*[h3.cell_to_latlng(c) for c in cells])
    coordinate_lookup = pd.DataFrame({
        'h3_id': cells,
        'lat': lats,
        'lon': lons
    })
    return coordinate_lookup

def get_neighbor_lookup(cells: list, max_k: int = 20) -> pd.DataFrame:
    print(f'Building neighbor lookup table (k<={max_k})...')
    neighbors = []
    for c in cells:
        for k in range(1, max_k + 1):
            for nb in h3.grid_ring(c, k):
                neighbors.append({'target_id': c, 'neighbor_id': nb, 'k': k})
    neighbors_lookup = pd.DataFrame(neighbors)
    print(f'  Finished creating neighbor lookup with {len(neighbors_lookup)} rows.')
    return neighbors_lookup

def get_min_h3_dist(target: str, cells: set, max_dist: int) -> int:
    # Minimum distance is zero if target is in the cells
    if target in cells:
        return 0
    
    min_dist = max_dist
    for c in cells:
        dist = h3.grid_distance(target, c)
        if dist < min_dist:
            min_dist = dist
    return min_dist

def get_coordinate_arrays(coordinate_lookup: pd.DataFrame) -> tuple[xr.DataArray, xr.DataArray]:
    x_da = xr.DataArray(coordinate_lookup['lon'].values, dims = 'h3_index')
    y_da = xr.DataArray(coordinate_lookup['lat'].values, dims = 'h3_index')
    return x_da, y_da
