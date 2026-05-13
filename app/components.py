### Solara app components



###############
### IMPORTS ###
###############

import h3
import solara
import pandas as pd
import time
import threading
from ipyleaflet import LayerGroup
from elements import *
from layers import get_basemaps, get_map
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
    fire: pd.DataFrame,
    risk: pd.DataFrame,
    hours: list,
    fire_lookback_hours: int
):
    # Instantiate map only once and cache basemaps
    map_obj = solara.use_memo(lambda: get_map(theme), [])
    basemaps = solara.use_memo(lambda: get_basemaps(), [])
    basemap_layer = basemaps[theme.value]

    # Group layers to avoid flicker
    data_group = solara.use_memo(lambda: LayerGroup(layers = []), [])

    def _setup_map():
        map_obj.add_layer(data_group)
    solara.use_effect(_setup_map, [])

    # Create fire and risk lookups once
    risk_lookup = solara.use_memo(
        lambda: risk.set_index(['hour_bin', 'h3_id'])[[
            'energy_term', 'landcover', 'fuel_score', 'dist_fire', 'risk'
        ]].to_dict('index'), 
        []
    )
    fire_indexed = fire.set_index('hour_bin').sort_index()

    def _build_fire_cells():
        result = {}
        for hour in hours:
            start = hour - pd.Timedelta(hours = fire_lookback_hours)
            result[hour] = set(fire_indexed.loc[
                (fire_indexed.index > start) & (fire_indexed.index <= hour), 'h3_id'
            ].unique())
        return result
    fire_cells_by_hour = solara.use_memo(_build_fire_cells, [])

    # Helper function to check return cell data if active
    def _evaluate_cell(cell, hour, layers):
        is_fire_cell = 'Fire' in layers and cell in fire_cells_by_hour.get(hour, set())
        risk_row = risk_lookup.get((hour, cell)) if 'Risk' in layers else None
        if not is_fire_cell and not risk_row:
            return None
        cell_data = {'h3_id': cell}
        if risk_row:
            cell_data |= risk_row
        print(cell_data)
        return cell_data

    # Update cell information on click
    def _on_map_interaction(**kwargs):
        if kwargs.get('type') != 'click':
            return
        layers = selected_layers.value
        if 'Risk' not in layers and 'Fire' not in layers:
            return
        coords = kwargs.get('coordinates', [])
        if not coords:
            return

        lat, lon = coords
        cell = h3.latlng_to_cell(lat, lon, 7)
        result = _evaluate_cell(cell, hours[time_index.value], selected_layers.value)

        if result:
            cell_lat, cell_lon = h3.cell_to_latlng(cell)
            inspector_data.set({**result, 'lat': cell_lat, 'lon': cell_lon})
        else:
            inspector_data.set(None)

    def _setup_interaction():
        map_obj.on_interaction(_on_map_interaction)
    solara.use_effect(_setup_interaction, [])

    def _sync_basemap():
        if len(map_obj.layers) > 0:
            map_obj.substitute_layer(map_obj.layers[0], basemap_layer)
    solara.use_effect(_sync_basemap, [theme.value])

    # Sync the data layers
    def _setup_layer_sync():
        def _sync(*_):
            new_layers = []
            if hours:
                # Add selected layers
                for layers, name in zip(
                    [risk_exposed_layers, fire_layers, lightning_layers],
                    ['Risk', 'Fire', 'Lightning']
                ):
                    if name in selected_layers.value:
                        current_layer = layers.get(hours[time_index.value])
                        new_layers.append(current_layer)

                # Only add covered risk cells if fire not selected
                if 'Risk' in selected_layers.value and 'Fire' not in selected_layers.value:
                    new_layers.append(risk_covered_layers.get(hours[time_index.value]))
            data_group.layers = tuple(l for l in new_layers if l is not None)

        _sync()
        unsub1 = time_index.subscribe(_sync)
        unsub2 = selected_layers.subscribe(_sync)
        return lambda: (unsub1(), unsub2())
    solara.use_effect(_setup_layer_sync, [])

    # Update cell information on slider change
    def _setup_inspector_sync():
        def _sync(*_):
            data = inspector_data.value
            if data is None:
                return
            result = _evaluate_cell(data['h3_id'], hours[time_index.value], selected_layers.value)
            inspector_data.set({**result, 'lat': data['lat'], 'lon': data['lon']} if result else None)

        unsub1 = time_index.subscribe(_sync)
        unsub2 = selected_layers.subscribe(_sync)
        return lambda: (unsub1(), unsub2())
    solara.use_effect(_setup_inspector_sync, [])

    solara.display(map_obj)

@solara.component
def TopPanel(min_risk: float, fire_lookback_hours: int):
    # Button colors
    lightning_orange = '#ffb700'
    fire_red = '#ff0000'
    risk_blue = '#005eff'
    sun_yellow = '#ffdd00'
    moon_blue = '#5D88BB'
    satellite_green = "#2bff008a"

    # Place everything in ghost column on left side
    with left_ghost_column(width = 310, top_margin = 10):
        header('California Lightning Siege', top_margin = 10, bottom_margin = 8)
        solara.Text("""
            Explore lightning strikes, wildfire observations, and wildfire risk during the
            August 2020 lightning siege in California.
        """)

        # Variables dependent on theme and info button
        show_info, set_show_info = solara.use_state(False)
        text_color = 'white' if theme.value == 'Dark' else 'black'
        bg_color = '#121212' if theme.value == 'Dark' else 'white'

        # Place info button next to Layers title
        with solara.Row(style = {
            'align-items': 'center',
            'background-color': 'transparent',
            'margin': '0', 'padding': '0', 'min-height': '0', 'gap': '2px'
        }):
            solara.Markdown('**Layers**')
            solara.IconButton(
                icon_name = 'mdi-information-outline',
                on_click = lambda: set_show_info(True),
                style = {'margin-top': '3px', 'margin-left': '-4px'}
            )

        # Layer description pop-up
        with solara.v.Dialog(v_model = show_info, on_v_model = set_show_info, max_width = '600px'):
            with solara.v.Card(style_ = f'background-color: {bg_color}; color: {text_color};'):
                with solara.v.CardTitle(style = f'color: {text_color};'):
                    solara.Text('Layer Descriptions')
                with solara.v.CardText():
                    solara.HTML(tag = 'div', unsafe_innerHTML = f"""
                        <div style="color: {text_color};">
                            <p><span style="font-weight:600;">Lightning Layer:</span> Shows each lightning flash observed by NASA's GOES-17 satellite, colored by the at-sensor radiant energy (J) captured by the GOES-17 satellite.</p>
                            <p><span style="font-weight:600;">Fire Layer:</span> Shows areas where NASA's Suomi NPP satellite has observed fire. Each hexagonal cell is highlighted in red if the satellite observed fire inside the cell's boundaries at least once in the preceding {fire_lookback_hours} hours of the selected time.</p>
                            <p><span style="font-weight:600;">Risk Layer:</span> Shows cells with risk score ≥ {min_risk}. The score is a product of three terms, each in range [0,1]:</p>
                            <ul style="margin-top:0; margin-bottom:0.5em;">
                                <li><i>Lightning Score:</i> a log-scaled lightning energy term (summed over the preceding 72 hours and all neighbors within distance 4).</li>
                                <li><i>Fuel Score:</i> a land-cover fuel score based on the ground terrain type.</li>
                                <li><i>Fire Proximity Score:</i> a fire-distance decay which increases risk near recently (24 hours) active fires.</li>
                            </ul>
                            <p>Higher risk scores indicate a higher chance of wildfire in the immediate future. You can see the exact formula used in the project's <a href="https://github.com/sanderengel/gds_exam_project/tree/master" target="_blank">README</a>.</p>
                        </div>
                    """)
                with solara.v.CardActions():
                    solara.Button('Close', on_click = lambda: set_show_info(False), style = {'color': text_color})

        # Layer selection buttons
        with solara.ToggleButtonsMultiple(value = selected_layers):
            button_element('mdi-flash', lightning_orange, tooltip_text = 'Lightning')
            button_element('mdi-fire', fire_red, tooltip_text = 'Fire')
            button_element('mdi-alert', risk_blue, tooltip_text = 'Risk')

        # Theme selection buttons
        solara.Markdown('**Theme**')
        with solara.ToggleButtonsSingle(value = theme):
            button_element('mdi-weather-sunny', sun_yellow, tooltip_text = 'Light')
            button_element('mdi-weather-night', moon_blue, tooltip_text = 'Dark')
            button_element('mdi-satellite-variant', satellite_green, tooltip_text = 'Satellite')

        # Cell information if risk or fire layer active
        layers = selected_layers.value
        if 'Risk' in layers or 'Fire' in layers:
            data = inspector_data.value

            with solara.Div(style = {'margin-top': '16px'}):
                solara.Markdown('**Cell Information**')

            if data is None:
                solara.Markdown('_Click an active cell for info._')
            else:
                spaced_text(f"**H3 cell ID:** {data['h3_id']}")
                spaced_text(f"**Latitude:** {data['lat']:.2f}°")
                spaced_text(f"**Longitude:** {data['lon']:.2f}°")

                dist_fire = data.get('dist_fire', 0)
                if dist_fire > 1:
                    dist_fire_str = f'{dist_fire} cells'
                elif dist_fire == 1:
                    dist_fire_str = f'{dist_fire} cell'
                else:
                    dist_fire_str = 'active fire'
                spaced_text(f'**Distance to fire:** {dist_fire_str}')

                # Only show risk section if risk layer on
                if 'Risk' in layers:
                    with solara.Div(style = {'margin-top': '16px'}):
                        solara.Markdown('**Risk Information**')

                    # Only show actual risk term if above threshold
                    if 'risk' in data:
                        spaced_text(f'**Fire Proximity Score:** {2/(dist_fire + 2):.2f}')
                        spaced_text(f"**Lightning Score:** {data['energy_term']:.2f}")
                        spaced_text(f"**Fuel Score:** {data['fuel_score']:.2f} ({data['landcover']})")
 
                        risk_score = f"{data['risk']:.2f}"
                    else:
                        risk_score = f'<{min_risk}'
                    
                    spaced_text(f'**Risk score:** {risk_score}')
                    
@solara.component
def BottomPanel(sorted_hours: pd.DataFrame):
    # Define ties and dates to display
    max_idx = max(0, len(sorted_hours) - 1)
    display_time = sorted_hours[time_index.value].strftime('%b %d, %H:00 - %H:59') + ' UTC' if sorted_hours else 'Loading...' # Display on top of slider
    display_dates = [h.strftime('%b %d') if h.day % 2 == 1 and h.hour == 0 else '' for h in sorted_hours] # Display as tick labels on slider

    # Define function to control auto play/pause
    def _setup_playback():
        if not is_playing.value:
            return
        stop = threading.Event()
        def _advance():
            while not stop.is_set():
                time.sleep(0.3)
                if stop.is_set():
                    break
                idx = time_index.value
                if idx < max_idx:
                    time_index.set(idx + 1)
                else:
                    is_playing.set(False)
                    break
        threading.Thread(target = _advance, daemon = True).start()
        return lambda: stop.set()
    solara.use_effect(_setup_playback, [is_playing.value])

    # Slider and play/pause button next to each other
    with left_ghost_column(width = 700, bottom_margin = 30):
        solara.Markdown(f'**Data and Time:** {display_time}')
        with solara.Row(style = {'align-items': 'center', 'background-color': 'transparent', 'margin': '0', 'padding': '0', 'gap': '0'}):
            solara.SliderInt(
                label = '',
                value = time_index,
                min = 0,
                max = max_idx,
                step = 1,
                thumb_label = False,
                tick_labels = display_dates
            )
            
            # Add auto play/pause button
            solara.IconButton(
                icon_name = 'mdi-pause' if is_playing.value else 'mdi-play',
                on_click = lambda: is_playing.set(not is_playing.value)
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
                color_bar_element('Radiant Lightning Energy (Log)', energy_bounds, energy_colors, lambda x: f'{x:.2e} J')

            # Risk legend
            if has_risk:
                risk_margin = '12px' if has_lightning else '0px' # Margin dependent on if lightning legend shown 
                with solara.Div(style = {'margin-top': risk_margin}):
                    color_bar_element('Risk Scores', risk_bounds, risk_colors, lambda x: f'{x:.2f}')

            # Fire legend
            if has_fire:
                fire_margin = '12px' if (has_lightning or has_risk) else '0px' # Margin dependent on any legend above
                solara.HTML(tag = 'div', unsafe_innerHTML = f'''
                    <div style="display:flex; justify-content:flex-end; align-items:center; gap:12px; margin-top:{fire_margin}">
                        <div class="legend-hex"></div>
                        <p style="margin:0; font-weight:bold">Wildfire (Last {fire_lookback}h)</p>
                    </div>
                ''')
