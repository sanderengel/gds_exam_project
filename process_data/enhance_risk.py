### Enhance risk scores



###############
### IMPORTS ###
###############

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_risk_grid, add_json_geometry



#############
### SETUP ###
#############

# Define paths
ROOT = Path(__file__).resolve().parent.parent
RISK_DIR = ROOT / 'data' / 'risk'
OUTPUT_PATH = RISK_DIR / 'risk_grid_enhanced.feather'



#################
### LOAD DATA ###
#################

risk_grid = load_risk_grid()



###############
### ENHANCE ###
###############

# Pre-calculate the geometry for every unique cell in the data
risk_enhanced = add_json_geometry(risk_grid)

# Add linear color scale based on risk scores
CMAP = 'Blues'
norm = mcolors.Normalize(vmin = 0, vmax = 1)
cmap = plt.get_cmap(CMAP)
rgba_colors = cmap(norm(risk_enhanced['risk'].values))
risk_enhanced['color_hex'] = [mcolors.to_hex(rgba) for rgba in rgba_colors]

# Add square root alpha channel
risk_enhanced['alpha'] = np.sqrt(risk_enhanced['risk'])



############
### SAVE ###
############

risk_enhanced.to_feather(OUTPUT_PATH)
print(f'Saved enhanced risk grid to {OUTPUT_PATH}.')
