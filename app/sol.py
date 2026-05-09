### Solara app renderer



###############
### IMPORTS ###
###############

import sys
import time
import solara
from pathlib import Path
from layers import get_data_layers
from colors import get_lightning_color_tuple, get_truncated_cmap, get_risk_color_tuple
from components import *

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import load_lightning_df, load_fire_df, load_risk_df



#################
### CONSTANTS ###
#################

FIRE_LOOKBACK_HOURS = 24
RISK_THRESHOLD = 0.1
N_RISK_BINS = 20
START_TIME = pd.Timestamp('2020-08-16 00:00')
END_TIME = pd.Timestamp('2020-08-31 23:00')
TIMELINE = pd.date_range(start = START_TIME, end = END_TIME, freq = 'h')
HOURS_LIST = TIMELINE.to_list()
RISK_CMAP = get_truncated_cmap('cool', end = 0.7)



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
    load_start = time.time()

    # Load data
    lightning = solara.use_memo(lambda: load_lightning_df(), [])
    fire = solara.use_memo(lambda: load_fire_df(), [])
    risk = solara.use_memo(lambda: load_risk_df(), [])
    
    # Build layers
    lightning_layers, fire_layers, risk_exposed_layers, risk_covered_layers = solara.use_memo(
        lambda: get_data_layers(
            lightning, fire, risk,
            TIMELINE, FIRE_LOOKBACK_HOURS, RISK_CMAP, N_RISK_BINS, RISK_THRESHOLD
        ),
        dependencies = [lightning, fire, risk]
    )

    # Compute lightning energy bounds and colors
    lightning_sorted = solara.use_memo(lambda: lightning.sort_values(by = 'energy'), [lightning])
    energy_list = lightning_sorted['energy'].tolist()
    energy_bounds = energy_list[0], energy_list[-1]
    energy_colors = solara.use_memo(lambda: get_lightning_color_tuple(lightning_sorted), [lightning_sorted])

    # Compute risk bounds and colors
    risk_valid = solara.use_memo(lambda: risk[risk['risk'] >= RISK_THRESHOLD].sort_values(by = 'risk'), [risk])
    risk_list = risk_valid['risk'].tolist()
    risk_bounds = risk_list[0], risk_list[-1]
    risk_colors = solara.use_memo(lambda: get_risk_color_tuple(RISK_CMAP, N_RISK_BINS, risk_bounds), [risk_bounds])

    load_end = time.time()
    print(f'Loaded data in {load_end - load_start:.2f} seconds.')

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
        MapComponent(
            lightning_layers, 
            fire_layers, 
            risk_exposed_layers, 
            risk_covered_layers, 
            fire,
            risk_valid, # Pass valid risk to avoid invalid cells being clickable
            HOURS_LIST,
            FIRE_LOOKBACK_HOURS
        )
        TopPanel(RISK_THRESHOLD, FIRE_LOOKBACK_HOURS)
        BottomPanel(HOURS_LIST)
        Legend(energy_bounds, energy_colors, risk_bounds, risk_colors, FIRE_LOOKBACK_HOURS)
