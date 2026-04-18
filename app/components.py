### Solara app components



###############
### IMPORTS ###
###############

import solara
import pandas as pd
from elements import *
from layers import get_basemap, get_map
from state import *



##################
### COMPONENTS ###
##################

@solara.component
def MapComponent(lightning_layers: dict, sorted_hours: pd.DataFrame):
    # Instantiate map only once
    map_obj = solara.use_memo(lambda: get_map(theme), [])
    basemap_layer = solara.use_memo(lambda: get_basemap(theme), [theme.value])

    def sync_map():
        active_layers = [basemap_layer]

        lightning_layer = None
        if 'Lightning' in selected_layers.value and sorted_hours:
            lightning_layer = lightning_layers.get(sorted_hours[time_index.value])
            if lightning_layer:
                active_layers.append(lightning_layer)

        # Update layers
        map_obj.layers = tuple(active_layers)

    solara.use_effect(
        sync_map, [theme.value, time_index.value, selected_layers.value]
    )

    solara.display(map_obj)

@solara.component
def TopPanel():
    with left_ghost_column(width = 320, top_margin = 10):
        header('California Lightning Siege', top_margin = 10, bottom_margin = 8)
        solara.Text("""
            Explore lightning strikes, wildfire observations, and fire risk during the
            August 2020 lightning siege in California.
        """)

        solara.Markdown('**Layers**')
        with solara.ToggleButtonsMultiple(value = selected_layers):
            with solara.Tooltip('Lightning'):
                solara.Button(icon_name = 'mdi-flash', text = True)
            with solara.Tooltip('Fire'):
                solara.Button(icon_name = 'mdi-fire', text = True)
            with solara.Tooltip('Risk'):
                solara.Button(icon_name = 'mdi-alert', text = True)

        solara.Markdown('**Theme**')
        with solara.ToggleButtonsSingle(value = theme):
            with solara.Tooltip('Light'):
                solara.Button(icon_name = 'mdi-weather-sunny', text = True)
            with solara.Tooltip('Dark'):
                solara.Button(icon_name = 'mdi-weather-night', text = True)
            with solara.Tooltip('Satellite'):
                solara.Button(icon_name = 'mdi-satellite-variant', text = True)

@solara.component
def BottomPanel(sorted_hours: pd.DataFrame):
    max_idx = max(0, len(sorted_hours) - 1)
    display_time = sorted_hours[time_index.value].strftime('%b %d, %H:00 - %H:59') if sorted_hours else 'Loading...'
    display_dates = [h.strftime('%b %d') if h.day % 2 == 1 and h.hour == 0 else '' for h in sorted_hours]

    with left_ghost_column(width = 700, bottom_margin = 30):

        solara.Markdown(f'**Data and Time:** {display_time}')
        solara.SliderInt(
            label = '',
            value = time_index,
            min = 0,
            max = max_idx,
            step = 1,
            thumb_label = False,
            tick_labels = display_dates
        )

@solara.component
def Legend(
    energy_min: float,
    energy_max: float,
    color_min: str,
    color_mid: str,
    color_max: str
):
    with right_ghost_column(width = 320, top_margin = 20):
        if 'Lightning' in selected_layers.value:
            label = 'Lightning Energy (Log)'
            left_text = f'<small>{energy_min:.2e} J</small>'
            right_text = f'<small>{energy_max:.2e} J</small>'
            color_bar(label, color_min, color_mid, color_max, left_text, right_text)

