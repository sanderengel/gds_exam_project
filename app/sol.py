### Solara app renderer



###############
### IMPORTS ###
###############

import solara
from pathlib import Path
from utils import load_lightning_df
from layers import get_lightning_layers
from components import *



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
    # Load data
    lightning = solara.use_memo(lambda: load_lightning_df(), [])
    lightning_layers = solara.use_memo(lambda: get_lightning_layers(lightning), [lightning])
    sorted_hours = sorted(lightning_layers.keys())

    # Compute energy bounds and colors
    lightning_by_energy = lightning.sort_values(by = 'energy')
    energy_sorted = lightning_by_energy['energy'].tolist()
    lightning_colors = lightning_by_energy['color_hex'].tolist()
    energy_min, energy_max = energy_sorted[0], energy_sorted[-1]
    color_min, color_max = lightning_colors[0], lightning_colors[-1]
    color_mid = lightning_colors[len(lightning_colors)//2]

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
        MapComponent(lightning_layers, sorted_hours)
        TopPanel()
        BottomPanel(sorted_hours)
        Legend(energy_min, energy_max, color_min, color_mid, color_max)
