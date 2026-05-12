### Coordinator script to build risk grid



###############
### IMPORTS ###
###############

import sys
from pathlib import Path
from spatial_utils import *
from fire_features import add_fire_distance_persistent
from fuel_scores import add_fuel_scores
from risk_scoring import add_risk

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_lightning_df, load_fire_df



#############
### SETUP ###
#############

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / 'data' / 'risk'
OUTPUT_PATH = OUTPUT_DIR / 'risk_grid.feather'
OUTPUT_DIR.mkdir(parents = True, exist_ok = True)



#################
### LOAD DATA ###
#################

fire = load_fire_df()
lightning = load_lightning_df()



#######################
### BUILD RISK GRID ###
#######################

ANALYSIS_START_TIME = pd.Timestamp('2020-08-16 00:00')
ANALYSIS_END_TIME = pd.Timestamp('2020-08-31 23:00')
MAX_K = 4
LIGHTNING_LOOKBACK_HOURS = 72
FIRE_LOOKBACK_HOURS = 24
base_cols = ['h3_id', 'hour_bin']

# Get lightning cells
lightning_cells = get_unique_cells(lightning)

# Generate neighbor lookup for lightning cells
lightning_neighbor_lookup = get_neighbor_lookup(lightning_cells, MAX_K)

# Build impact grid directly from aggregated energy
grid, energy_col = build_sparse_impact_grid(
    fire,
    lightning, 
    lightning_neighbor_lookup, 
    base_cols, 
    ANALYSIS_START_TIME,
    ANALYSIS_END_TIME,
    MAX_K, 
    LIGHTNING_LOOKBACK_HOURS
)

# Get unique cell IDs for environmental features
impact_cells = get_unique_cells(grid)
coordinate_lookup = get_coordinate_lookup(impact_cells)

# Add fire distance
grid = add_fire_distance_persistent(grid, fire, FIRE_LOOKBACK_HOURS)

# Add fuel scores
grid = add_fuel_scores(grid, impact_cells, coordinate_lookup)

# Add risk
grid = add_risk(grid, energy_col)



###############
### CLEANUP ###
###############

# Drop columns which are no longer used
keep_cols = base_cols + ['dist_fire', 'risk']
risk_grid = grid[keep_cols].copy()

# Drop any rows with 0 risk
risk_grid = risk_grid[risk_grid['risk'] > 0]



############
### SAVE ###
############

risk_grid.to_feather(OUTPUT_PATH)
print(f'Saved risk grid to {OUTPUT_PATH}.')
