### Solara app layers



###############
### IMPORTS ###
###############

import sys
import h3
import solara
import pandas as pd
from pathlib import Path
from ipyleaflet import Map, basemaps, basemap_to_tiles, ZoomControl, LayerGroup, CircleMarker, GeoJSON

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import get_timeline, get_data_map



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

def get_point_layers(df: pd.DataFrame) -> dict:
    # Pre-group data into dict for fast lookup
    data_map = get_data_map(df)
    
    # Get full timeline of hours without breaks
    timeline = get_timeline(df)

    # Group data by hours and return as dict of layers
    layers = {}
    for hour in timeline:
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

def get_tessellation_layers(df: pd.DataFrame, lookback_hours: int = 12) -> dict:  
    # Get full timeline of hours without breaks
    timeline = get_timeline(df)
    layers = {}

    for hour in timeline:
        # Get fires from previous hours
        start_window = hour - pd.Timedelta(hours = lookback_hours)
        mask = (df['hour_bin'] > start_window) & (df['hour_bin'] <= hour)

        # Get unique rows based on cell IDs
        active_ids = df.loc[mask, 'h3_id'].unique().tolist()
        if len(active_ids) == 0:
            layers[hour] = LayerGroup(layers = [])
            continue

        # Convert cells into a GeoJSON geometry
        geojson_geometry = h3.cells_to_geo(active_ids)

        geojson_data = {
            'type': 'Feature',
            'geometry': geojson_geometry,
            'properties': {}
        }

        # Create single widget for whole fire complex
        layer = GeoJSON(
            data = geojson_data,
            style = {
                'color': '#ff0000',
                'fillColor': '#ff0000',
                'fillOpacity': .5,
                'weight': 1
            }
        )

        layers[hour] = LayerGroup(layers = [layer])

    return layers
