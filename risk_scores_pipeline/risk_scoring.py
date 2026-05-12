### Compute risk



###############
### IMPORTS ###
###############

import numpy as np
import pandas as pd



#################
### FUNCTIONS ###
#################

def _get_energy_term(
    energy: np.ndarray,
    energy_scale_factor: float = 10**14.5,
) -> np.ndarray:
    # Scale energy
    energy_scaled = energy * energy_scale_factor

    # Log transform energy
    energy_transformed = np.log10(1 + energy_scaled)

    # Get L_max normalization constant
    L_max = np.percentile(energy_transformed, 99) # 99th percentile represents "typical extreme"

    # Compute full energy term
    energy_term = np.minimum(1, energy_transformed / L_max)
    return energy_term

def _get_fire_distance_decay(
    fire_distances: np.ndarray,
    half_distance: int = 2 # Represents distance where fire decay halfes risk score
) -> np.ndarray:
    return half_distance / (fire_distances + half_distance)

def add_risk(grid: pd.DataFrame, energy_col: str) -> pd.DataFrame:
    # Extract vectors
    energy = grid[energy_col].to_numpy()
    fuel_scores = grid['fuel_score'].to_numpy()
    fire_distances = grid['dist_fire'].to_numpy()

    energy_term = _get_energy_term(energy)
    fire_distance_decay = _get_fire_distance_decay(fire_distances)

    # Compute risk
    risk = energy_term * fuel_scores * fire_distance_decay
    grid['energy_term'] = energy_term
    grid['risk'] = risk

    return grid
