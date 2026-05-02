### Coordinator script to build cell hours data table



###############
### IMPORTS ###
###############

import sys
from pathlib import Path
from spatial_utils import *
from fire_variables import *
from fuel_scores import add_fuel_scores

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_lightning_df, load_fire_df



#################
### LOAD DATA ###
#################

fire = load_fire_df()
lightning = load_lightning_df()



##################
### BUILD GRID ###
##################

MAX_K = 4
W = 72
base_cols = ['h3_id', 'hour_bin']

# Get lightning cells
lightning_cells = get_unique_cells(lightning)

# Generate neighbor lookup for lightning cells
lightning_neighbor_lookup = get_neighbor_lookup(lightning_cells, MAX_K)

# Build impact grid directly from aggregated energy
grid = build_sparse_impact_grid(fire, lightning, lightning_neighbor_lookup, base_cols, MAX_K, W)

# Get unique cell IDs for environmental features
impact_cells = get_unique_cells(grid)
coordinate_lookup = get_coordinate_lookup(impact_cells)

# Add fire distance
grid = add_fire_distance_persistent(grid, fire, w = W)

# Add fuel scores
grid = add_fuel_scores(grid, impact_cells, coordinate_lookup)



############
### SAVE ###
############

root = Path(__file__).resolve().parent.parent
save_dir = root / 'data' / 'features'
save_path = save_dir / 'feature_grid.feather'

save_dir.mkdir(parents = True, exist_ok = True)

grid.to_feather(save_path)
print(f'Saved grid data to {save_path}.')
