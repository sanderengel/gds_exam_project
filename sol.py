### Solara app renderer



###############
### IMPORTS ###
###############

import solara
import pandas as pd
from pathlib import Path
from ipyleaflet import Map, basemaps, basemap_to_tiles, ZoomControl, LayerGroup, CircleMarker
from utils import load_lightning_df



###############
### STYLING ###
###############

css_path = Path(__file__).parent / 'style.css'
css_content = css_path.read_text()



#########################
### DYNAMIC VARIABLES ###
#########################

theme = solara.reactive('Dark Theme')
time_index = solara.reactive(0)
show_lightning = solara.reactive(True)
show_fire = solara.reactive(True)
show_risk = solara.reactive(True)



########################
### HELPER FUNCTIONS ###
########################

def _get_basemap():
    theme_basemaps = {
        'Light Theme': basemaps.CartoDB.Positron,
        'Dark Theme': basemaps.CartoDB.DarkMatter,
        'Satellite Theme': basemaps.Esri.WorldImagery
    }
    return basemap_to_tiles(theme_basemaps[theme.value])

def _map():
    initial_bm = _get_basemap()
    m = Map(
        center = [37, -120],
        zoom = 6,
        min_zoom = 6,
        max_zoom = 12,
        layers = (initial_bm,),
        zoom_control = False
    )
    m.add_control(ZoomControl(position = 'bottomleft')) # Add custom zoom control
    m.layout.height = '100vh' # Set map to fill full page
    return m

def _get_lightning_layers(lightning: pd.DataFrame) -> dict:
    df = lightning.copy()

    # Pre-group data into dict for fast lookup
    data_map = {hour: group for hour, group in df.groupby('hour_bin')}
    
    # Define absolute start and end of timeline
    start_time = df['hour_bin'].min()
    end_time = df['hour_bin'].max()

    # Generate all hours between the bounds
    full_timeline = pd.date_range(start = start_time, end = end_time, freq = 'h')

    # Group lightning by hours and return as dict of layers
    layers = {}
    for hour in full_timeline:
        group = data_map.get(hour, pd.DataFrame())
        markers = [
            CircleMarker(
                location = (row['lat'], row['lon']),
                radius = 1,
                weight = 1,
                color = row['color_hex'],
                fill_color = row['color_hex'],
                fill_opacity = .8
            ) for _, row in group.iterrows()
        ]
        layers[hour] = LayerGroup(layers = markers, name = f'Strikes {hour}')

    return layers



###################
### SOLARA PAGE ###
###################

@solara.component
def MapComponent(lightning_layers: dict, sorted_hours: pd.DataFrame):
    # Instantiate map only once
    map_obj = solara.use_memo(_map, dependencies = [])
    basemap_layer = solara.use_memo(_get_basemap, [theme.value])

    def sync_map():
        # Get lightning layer
        lightning_layer = None
        if show_lightning.value and sorted_hours:
            current_hour = sorted_hours[time_index.value]
            lightning_layer = lightning_layers.get(current_hour)

        # Update layers
        map_obj.layers = (basemap_layer, lightning_layer) if lightning_layer else map_obj.layers

    solara.use_effect(
        sync_map, [theme.value, time_index.value, show_lightning.value]
    )

    solara.display(map_obj)

@solara.component
def ControlPanel(text_color: str, glow_color: str, sorted_hours: pd.DataFrame):
    max_idx = max(0, len(sorted_hours) - 1)
    display_time = sorted_hours[time_index.value].strftime('%b %d, %H:00 - %H:59') if sorted_hours else 'Loading...'

    with solara.Column(
        classes = ['ghost-panel'],
        gap = '0px',
        style = {
            'position': 'absolute',
            'top': '20px',
            'left': '20px',
            'width': '230px',
            'z-index': '1000',
            'background-color': 'transparent',
            '--text-color': text_color,
            '--glow-color': glow_color
        }
    ):

        # Global Style targeting the container and the buttons
        solara.Style(css_content)

        solara.Markdown('### Layers')
        solara.Checkbox(label = 'Lightning')
        solara.Checkbox(label = 'Fire')
        solara.Checkbox(label = 'Risk')

        solara.Markdown('### Controls')

        solara.Markdown(f'**Time:** {display_time}')
        solara.SliderInt(
            label = '',
            value = time_index,
            min = 0,
            max = max_idx,
            step = 1,
            thumb_label = False
        )

        solara.Markdown('**Theme**')
        with solara.ToggleButtonsSingle(value = theme):
            with solara.Tooltip('Light Theme'):
                solara.Button(icon_name = 'mdi-weather-sunny', text = True)
            with solara.Tooltip('Dark Theme'):
                solara.Button(icon_name = 'mdi-weather-night', text = True)
            with solara.Tooltip('Satellite Theme'):
                solara.Button(icon_name = 'mdi-satellite-variant', text = True)

@solara.component
def Legend(text_color: str, glow_color: str, energy_min: float, energy_max: float):
    solara.Markdown('### Legend')
    with solara.Column(
        classes = ['ghost-panel'],
        style = {
            'position': 'absolute',
            'bottom': '80px',
            'left': '20px',
            'width': '230px',
            'z-index': '1000',
            'background-color': 'transparent',
            '--text-color': text_color,
            '--glow-color': glow_color
        }
    ):
        solara.Markdown('**Lightning Energy (Log)**')
        solara.Div(classes = ['energy-colorbar'])
        with solara.Row(justify = 'space-between', style = {'padding': '0 2px'}):
            solara.Markdown(f'<small>{energy_min} kA</small>')
            solara.Markdown(f'<small>{energy_max} kA</small>')

@solara.component
def Page():
    dark = theme.value in {'Dark Theme', 'Satellite Theme'}
    text_color = 'white' if dark else 'black'
    glow_color = 'black' if dark else 'white'

    # Load data
    lightning = solara.use_memo(lambda: load_lightning_df(), [])
    lightning_layers = solara.use_memo(lambda: _get_lightning_layers(lightning), [lightning])
    sorted_hours = sorted(lightning_layers.keys())

    # Compute energy bounds
    energy_min = lightning['energy'].min() if not lightning.empty else 0
    energy_max = lightning['energy'].max() if not lightning.empty else 100

    with solara.Div(style = {
        'position': 'relative',
        'height': '100vh',
        'width': '100%',
        'overflow': 'hidden',
        'background-color': '#121212' if theme.value == 'Dark Theme' else 'white'
    }):
        MapComponent(lightning_layers, sorted_hours)
        ControlPanel(text_color, glow_color, sorted_hours)
        Legend(text_color, glow_color, energy_min, energy_max)
