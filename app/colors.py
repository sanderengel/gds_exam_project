### App color functions



###############
### IMPORTS ###
###############

import solara
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap



#################
### FUNCTIONS ###
#################

def get_colors(theme: solara.Reactive) -> tuple[str, str]:
    light = theme.value == 'Light'
    text_color = 'black' if light else 'white'
    glow_color = 'white' if light else 'black'
    return text_color, glow_color

def get_truncated_cmap(cmap_name: str, start: float = 0.0, end: float = 0.1) -> ListedColormap:
    cmap = plt.get_cmap(cmap_name)
    new_colors = cmap(np.linspace(start, end, 256))
    return ListedColormap(new_colors)

def get_lightning_color_tuple(df: pd.DataFrame) -> tuple:
    colors = df['color_hex'].tolist()
    color_min, color_max = colors[0], colors[-1]
    color_mid = colors[len(colors)//2]
    return color_min, color_mid, color_max

def get_risk_color_tuple(
    cmap: ListedColormap, 
    n_bins: int,
    risk_bounds
) -> tuple:
    # Define the three points on the 0.0 - 1.0 risk scale
    risk_min, risk_max = risk_bounds
    low_val = int(risk_min * n_bins) / n_bins
    mid_val = int(((risk_max + risk_min) / 2) * n_bins) / n_bins
    high_val = int(risk_max * n_bins) / n_bins
    
    return (
        mcolors.to_hex(cmap(low_val)),
        mcolors.to_hex(cmap(mid_val)),
        mcolors.to_hex(cmap(high_val))
    )