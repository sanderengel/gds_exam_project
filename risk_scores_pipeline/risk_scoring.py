### Compute risk



###############
### IMPORTS ###
###############

import numpy as np
import pandas as pd



#################
### FUNCTIONS ###
#################

def _compute_risk(
    energy: np.ndarray,
    fuel_scores: np.ndarray,
    fire_distances: np.ndarray,
    energy_scale_factor: float = 10**14.5
) -> np.ndarray:
    # Scale energy
    energy_scaled = energy * energy_scale_factor

    # Log transform energy
    energy_transformed = np.log10(1 + energy_scaled)

    # Get L_max normalization constant
    L_max = np.percentile(energy_transformed, 99) # 99th percentile represents "typical extreme"

    # Compute full energy term
    energy_term = np.minimum(1, energy_transformed / L_max)

    # Compute fire distance decay
    fire_distance_decay = 1 / (fire_distances + 1)

    # Compute risk
    risk = energy_term * fuel_scores * fire_distance_decay
    return risk

def add_risk(grid: pd.DataFrame, energy_col: str) -> pd.DataFrame:
    # Extract vectors
    energy = grid[energy_col].to_numpy()
    fuel_scores = grid['fuel_score'].to_numpy()
    fire_distances = grid['dist_fire'].to_numpy()

    # Compute risk
    grid['risk'] = _compute_risk(energy, fuel_scores, fire_distances)
    return grid
