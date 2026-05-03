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
def MapComponent(
    lightning_layers: dict, 
    fire_layers: dict, 
    risk_exposed_layers: dict, 
    risk_covered_layers: dict,
    hours: list
):
    # Instantiate map only once
    map_obj = solara.use_memo(lambda: get_map(theme), [])
    basemap_layer = solara.use_memo(lambda: get_basemap(theme), [theme.value])

    def sync_map():
        active_layers = [basemap_layer]

        # Add layers
        if hours:
            for layers, name in zip(
                    [risk_exposed_layers, fire_layers, lightning_layers], 
                    ['Risk', 'Fire', 'Lightning']
                ):
                if name in selected_layers.value:
                    current_layer = layers.get(hours[time_index.value])
                    active_layers.append(current_layer)

            # Add covered risk layer only if fire not active
            if 'Risk' in selected_layers.value and 'Fire' not in selected_layers.value:
                current_layer = risk_covered_layers.get(hours[time_index.value])
                active_layers.append(current_layer)

        # Update layers
        map_obj.layers = tuple(active_layers)

    solara.use_effect(
        sync_map, [theme.value, time_index.value, selected_layers.value]
    )

    solara.display(map_obj)

@solara.component
def TopPanel():
    # Button colors
    lightning_orange = '#ffb700'
    fire_red = '#ff0000'
    risk_blue = '#005eff'
    sun_yellow = '#ffdd00'
    moon_blue = '#5D88BB'
    satellite_green = "#2bff008a"

    with left_ghost_column(width = 310, top_margin = 10):
        header('California Lightning Siege', top_margin = 10, bottom_margin = 8)
        solara.Text("""
            Explore lightning strikes, wildfire observations, and ignition risk during the
            August 2020 lightning siege in California.
        """)

        solara.Markdown('**Layers**')
        with solara.ToggleButtonsMultiple(value = selected_layers):
            with solara.Tooltip('Lightning'):
                solara.Button(icon_name = 'mdi-flash', text = True, style = {'--button-color': lightning_orange})
            with solara.Tooltip('Fire'):
                solara.Button(icon_name = 'mdi-fire', text = True, style = {'--button-color': fire_red})
            with solara.Tooltip('Risk'):
                solara.Button(icon_name = 'mdi-alert', text = True, style = {'--button-color': risk_blue})

        solara.Markdown('**Theme**')
        with solara.ToggleButtonsSingle(value = theme):
            with solara.Tooltip('Light'):
                solara.Button(icon_name = 'mdi-weather-sunny', text = True, style = {'--button-color': sun_yellow})
            with solara.Tooltip('Dark'):
                solara.Button(icon_name = 'mdi-weather-night', text = True, style = {'--button-color': moon_blue})
            with solara.Tooltip('Satellite'):
                solara.Button(icon_name = 'mdi-satellite-variant', text = True, style = {'--button-color': satellite_green})

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
    energy_bounds: tuple,
    energy_colors: tuple,
    risk_bounds: tuple,
    risk_colors: tuple,
    fire_lookback: int
):
    with right_ghost_column(width = 320, top_margin = 20):
        # Extract current state for logical checks
        has_lightning = 'Lightning' in selected_layers.value
        has_risk = 'Risk' in selected_layers.value
        has_fire = 'Fire' in selected_layers.value

        with right_ghost_column(width = 320, top_margin = 20):
            if has_lightning:
                color_bar_element('Lightning Energy (Log)', energy_bounds, energy_colors, lambda x: f'{x:.2e} J')

            # Risk legend
            if has_risk:
                risk_margin = '12px' if has_lightning else '0px'
                with solara.Div(style = {'margin-top': risk_margin}):
                    color_bar_element('Risk Scores', risk_bounds, risk_colors, lambda x: f'{x:.1f}')

            # Fire legend
            if has_fire:
                fire_margin = '12px' if (has_lightning or has_risk) else '0px'
                solara.HTML(tag = 'div', unsafe_innerHTML = f'''
                    <div style="display:flex; justify-content:flex-end; align-items:center; gap:12px; margin-top:{fire_margin}">
                        <div class="legend-hex"></div>
                        <p style="margin:0; font-weight:bold">Wildfire (Last {fire_lookback}h)</p>
                    </div>
                ''')
