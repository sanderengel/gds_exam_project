### Temporal fire variables



###############
### IMPORTS ###
###############

import numpy as np
import pandas as pd
from spatial_utils import get_min_h3_dist



#################
### FUNCTIONS ###
#################

def add_fire(grid: pd.DataFrame, fire: pd.DataFrame, base_cols: list) -> pd.DataFrame:
    print('Creating fire column...')
    
    # Create simplied fire df
    fire_targets = fire[base_cols].copy()
    fire_targets['has_fire'] = 1

    # Merge onto the grid
    grid = grid.merge(fire_targets, on = base_cols, how = 'left')
    grid['has_fire'] = grid['has_fire'].fillna(0).astype(np.int8)

    return grid

def _get_fire_map(grid: pd.DataFrame, fire: pd.DataFrame, w: int) -> pd.DataFrame:
    delta = pd.Timedelta(hours = w)
    fire_map = {
        hour: set(
            fire[
                (fire['hour_bin'] <= hour) &
                (fire['hour_bin'] > hour - delta)
            ]['h3_id']
        )
        for hour in grid['hour_bin'].unique()
    }
    return fire_map

def add_fire_distance_persistent(
    grid: pd.DataFrame, 
    fire: pd.DataFrame, 
    w: int = 24,
    max_dist: int = 100
) -> pd.DataFrame:
    print(f'Calculating distance to nearest fire within last w={w} hours...')

    # Pre-compute dict mapping hours to active fires, accounting for w
    fire_map = _get_fire_map(grid, fire, w)

    # Initialize fire distance column
    grid['dist_fire'] = 0

    # Process each hour's search space once
    results = []
    mask = grid['has_fire'] == 0 # No reason to look at rows with current fire
    for hour, group in grid[mask].groupby('hour_bin'):
        lookback_fires = fire_map.get(hour, set())

        # If no fires for this lookback window, assign max_dist to all cells
        if not lookback_fires:
            group_dists = [max_dist] * len(group)
        else:
            group_dists = [
                get_min_h3_dist(target, lookback_fires, max_dist) 
                for target in group['h3_id']
            ]

        # Keep track of index to ensure values align
        results.append(pd.Series(group_dists, index = group.index))

    if results:
        grid.loc[mask, 'dist_fire'] = pd.concat(results)

    return grid
