### Coordinator script to build cell hours data table



###############
### IMPORTS ###
###############

import sys
from pathlib import Path
from spatial_utils import build_impact_grid, get_neighbor_lookup
from temporal_variables import add_fire_onset, add_neighbor_fire, add_lightning_energy
from raster_features import add_environmental_data

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_lightning_df, load_fire_df



#################
### LOAD DATA ###
#################

fire = load_fire_df()
lightning = load_lightning_df()



######################
### BUILD FEATURES ###
######################

# Define base columns
base_cols = ['h3_id', 'hour_bin']

# Build grid and impact cells
grid, impact_cells = build_impact_grid(fire, lightning, base_cols)

# Get neighbor lookup 
neighbors = get_neighbor_lookup(impact_cells)

# Add fire onset label (y) based on whether fire observed within next 12 hours
grid = add_fire_onset(grid, fire, base_cols)

# Set index to the base cols
grid = grid.set_index(base_cols).sort_index()

# Add neighbor fire based on if any distance 1 neighbors have fire at current time
grid = add_neighbor_fire(grid, neighbors)

# Add lightning energy matrix
grid = add_lightning_energy(grid, lightning, neighbors, base_cols)

# Reset index to get base cols back as columns
grid = grid.reset_index()

# Add slope and fuel features
grid = add_environmental_data(grid, impact_cells)



############
### SAVE ###
############

root = Path(__file__).resolve().parent.parent
save_dir = root / 'data'
save_path = save_dir / 'feature_grid.feather'

save_dir.mkdir(parents = True, exist_ok = True)

grid.to_feather(save_path)
print(f'Saved grid data to {save_path}.')
