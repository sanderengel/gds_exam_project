### Temporal fire and lightning variables



###############
### IMPORTS ###
###############

import numpy as np
import pandas as pd
from spatial_utils import get_sparse_spatial_map



#################
### FUNCTIONS ###
#################

def add_fire_onset(
    grid: pd.DataFrame,
    fire: pd.DataFrame,
    base_cols: list,
    onset_hours: int = 12
) -> pd.DataFrame:
    print('Creating fire onset...')
    
    # Create simplied fire df
    fire_targets = fire[base_cols].copy()
    fire_targets['has_fire'] = 1

    # Merge onto the grid
    grid = grid.merge(fire_targets, on = base_cols, how = 'left')
    grid['has_fire'] = grid['has_fire'].fillna(0).astype(np.int8)

    # Compute "fire_onset" label (y) based on whether fire observed within next 12 hours
    grid = grid.sort_values(base_cols) # Sort to ensure rolling is contained geographically
    grid['fire_onset'] = (
        grid.groupby('h3_id')['has_fire']
        .shift(-onset_hours) # Roll ahead
        .rolling(window = onset_hours, min_periods = 1)
        .max()
    )
    grid['fire_onset'] = grid['fire_onset'].fillna(0).astype(np.int8)

    return grid

def add_neighbor_fire(grid: pd.DataFrame, neighbor_lookup: pd.DataFrame) -> pd.DataFrame:
    print('Creating neighbor has fire...')

    # Compute control variable for if any neighbor has fire
    k1_neighbors = neighbor_lookup[neighbor_lookup['k'] == 1]
    grid['neighbor_has_fire'] = (
        grid[['has_fire']]
        .reset_index()
        .merge(k1_neighbors, left_on = 'h3_id', right_on = 'neighbor_id')
        .groupby(['target_id', 'hour_bin'])['has_fire'].max()
        .rename_axis(index = {'target_id': 'h3_id'})
    )
    grid['neighbor_has_fire'] = grid['neighbor_has_fire'].fillna(0).astype(np.int8)

    return grid

def add_lightning_energy(
    grid: pd.DataFrame,
    lightning: pd.DataFrame,
    neighbor_lookup: pd.DataFrame,
    base_cols: list,
    max_k: int = 4
) -> pd.DataFrame:
    print('Creating lightning energy matrix...')

    # Compute k=0 energy
    grid['energy_k0'] = lightning.groupby(base_cols)['energy'].sum()
    grid['energy_k0'] = grid['energy_k0'].fillna(0)

    # Find spatial neighbors for active lightning cells
    sparse_spatial_map = get_sparse_spatial_map(grid, neighbor_lookup)

    # Iterate through k to build energy columns
    for k in range(max_k + 1):
        energy_col = f'energy_k{k}'

        # If k > 0, pull values from the sparse map
        if k > 0:
            grid[energy_col] = sparse_spatial_map.xs(k, level = 'k').rename_axis(
                index = {'target_id': 'h3_id'}
            ).fillna(0)
            grid[energy_col] = grid[energy_col].fillna(0)

        # Backwards rolling windows
        grouped_energy = grid[energy_col].groupby('h3_id')
        cum_energy = {
            w: grouped_energy.rolling(window = w, min_periods = 1).sum().droplevel(0)
            for w in [24, 48, 72]
        }

        # Add independent blocks as columns to the df
        grid[f'{energy_col}_w0_24'] = cum_energy[24]
        grid[f'{energy_col}_w24_48'] = cum_energy[48] - cum_energy[24]
        grid[f'{energy_col}_w48_72'] = cum_energy[72] - cum_energy[48]

        # Drop current energy_col to save memory unless it is k0
        if k > 0:
            grid = grid.drop(columns = [energy_col])

    grid = grid.drop(columns = ['energy_k0']) # Drop energy_k0 when all rings are done
    return grid

def add_temporal_validity(
    grid: pd.DataFrame,
    timeline: pd.DatetimeIndex,
    lookback_hours: int = 72,
    lookahead_hours: int = 12
) -> pd.DataFrame:
    print('Marking temporal validity edges...')

    start_buffer = timeline.min() + pd.Timedelta(hours = lookback_hours)
    end_buffer = timeline.max() - pd.Timedelta(hours = lookahead_hours)

    grid['is_temporal_valid'] = (
        (grid['hour_bin'] >= start_buffer) &
        (grid['hour_bin'] <= end_buffer)
    ).astype(np.int8)

    print(f"  Assigned {((len(grid[grid['is_temporal_valid'] == 0]) / len(grid)) * 100):.2f}% of rows to temporal buffers")

    return grid
