### Solara app layers



###############
### IMPORTS ###
###############

import solara
import pandas as pd
from ipyleaflet import Map, basemaps, basemap_to_tiles, ZoomControl, LayerGroup, CircleMarker



##############
### LAYERS ###
##############

def get_basemap(theme: solara.Reactive):
    theme_basemaps = {
        'Light': basemaps.CartoDB.Positron,
        'Dark': basemaps.CartoDB.DarkMatter,
        'Satellite': basemaps.Esri.WorldImagery
    }
    return basemap_to_tiles(theme_basemaps[theme.value])

def get_map(theme: solara.Reactive):
    initial_bm = get_basemap(theme)
    m = Map(
        center = [37, -120],
        zoom = 6,
        min_zoom = 6,
        max_zoom = 12,
        layers = (initial_bm,),
        zoom_control = False,
        attribution_control = False
    )
    m.add_control(ZoomControl(position = 'bottomright')) # Add custom zoom control
    m.layout.height = '100vh' # Set map to fill full page
    return m

def get_lightning_layers(lightning: pd.DataFrame) -> dict:
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
