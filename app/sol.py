### Solara app renderer



###############
### IMPORTS ###
###############

import sys
import solara
from pathlib import Path
from layers import get_point_layers, get_tessellation_layers
from components import *

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_lightning_df, load_fire_df



###############
### STYLING ###
###############

css_path = Path(__file__).parent / 'style.css'
css_content = css_path.read_text()



###################
### SOLARA PAGE ###
###################

@solara.component
def Page():
    # Load lightning data
    lightning = solara.use_memo(lambda: load_lightning_df(), [])
    lightning_layers = solara.use_memo(lambda: get_point_layers(lightning), [lightning])
    lightning_hours = sorted(lightning_layers.keys())

    # Compute energy bounds and colors
    lightning_by_energy = lightning.sort_values(by = 'energy')
    energy_sorted = lightning_by_energy['energy'].tolist()
    lightning_colors = lightning_by_energy['color_hex'].tolist()
    energy_min, energy_max = energy_sorted[0], energy_sorted[-1]
    color_min, color_max = lightning_colors[0], lightning_colors[-1]
    color_mid = lightning_colors[len(lightning_colors)//2]

    # Load fire data
    lookback_hours = 12
    fire = solara.use_memo(lambda: load_fire_df(), [])
    fire_layers = solara.use_memo(lambda: get_tessellation_layers(fire, lookback_hours), [fire])
    fire_hours = sorted(fire_layers.keys())

    # Check if hours match
    if lightning_hours != fire_hours:
        solara.Error('Error: Lightning hours do not match fire hours')
        return
    hours = lightning_hours

    with solara.Div(style = {
        'position': 'relative',
        'height': '100vh',
        'width': '100%',
        'overflow': 'hidden',
        'background-color': '#121212' if theme.value == 'Dark' else 'white'
    }):
        # Global Style
        solara.Style(css_content)

        # Components
        MapComponent(lightning_layers, fire_layers, hours)
        TopPanel()
        BottomPanel(hours)
        Legend(energy_min, energy_max, color_min, color_mid, color_max, lookback_hours)
