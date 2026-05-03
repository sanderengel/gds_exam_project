### Solara app layers



###############
### IMPORTS ###
###############

import os
import sys
import h3
import solara
import time
import pandas as pd
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ipyleaflet import Map, basemaps, basemap_to_tiles, ZoomControl, LayerGroup, GeoJSON

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from utils import get_data_map



#################
### CONSTANTS ###
#################

DEFAULT_CENTER = [37, -120]
DEFAULT_ZOOM = 7



##############
### LAYERS ###
##############

def get_basemaps() -> dict:
    return {
        'Light': basemap_to_tiles(basemaps.CartoDB.Positron),
        'Dark': basemap_to_tiles(basemaps.CartoDB.DarkMatter),
        'Satellite': basemap_to_tiles(basemaps.Esri.WorldImagery)
    }

def get_basemap(theme: solara.Reactive):
    theme_basemaps = get_basemaps()
    return theme_basemaps[theme.value]

def get_map(theme: solara.Reactive):
    initial_bm = get_basemap(theme)
    m = Map(
        center = DEFAULT_CENTER,
        zoom = DEFAULT_ZOOM,
        min_zoom = 6,
        max_zoom = 12,
        layers = (initial_bm,),
        zoom_control = False,
        attribution_control = False
    )
    m.add_control(ZoomControl(position = 'bottomright')) # Add custom zoom control
    m.layout.height = '100vh' # Set map to fill full page
    return m

def _get_hour_layers_pooled(hour_builder, timeline: pd.DatetimeIndex) -> dict:
    # Pool hourly layers for speed
    max_workers = min(12, (os.cpu_count() or 4) + 4)
    with ThreadPoolExecutor(max_workers = max_workers) as executor:
        results = list(executor.map(hour_builder, timeline))
    return dict(zip(timeline, results))

def get_lightning_layers(lightning: pd.DataFrame, timeline: pd.DatetimeIndex) -> dict:
    start_time = time.time()
    print('Creating lightning layers...')
    # Pre-group data into dict for fast lookup
    data_map = get_data_map(lightning)
    
    # Hour bouilder function to pass to pool
    def _build_hour_layer(hour: pd.Timestamp):
        group = data_map.get(hour, pd.DataFrame())
        if group.empty:
            return LayerGroup(layers = [])
        
        # Group by color to minize widgets
        hour_layers = []
        for color, color_group in group.groupby('color_hex'):
            features = [
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [row.lon, row.lat]},
                    'properties': {}
                }
                for row in color_group.itertuples()
            ]
            hour_layers.append(GeoJSON(
                data = {'type': 'FeatureCollection', 'features': features},
                point_style = {
                    'radius': 1, 
                    'weight': 1, 
                    'fillOpacity': .8, 
                    'color': color,
                    'fillColor': color
                }
            ))

        return LayerGroup(layers = hour_layers)
    
    layers = _get_hour_layers_pooled(_build_hour_layer, timeline)

    end_time = time.time()
    print(f'Finished creating lightning layers in {end_time - start_time:.2f} seconds.')
    return layers

def _get_fire_layers(
    fire: pd.DataFrame, 
    timeline: pd.DatetimeIndex,
    lookback_hours: int,
) -> dict:
    start_time = time.time()
    print('Creating fire layers...')

    fire_indexed = fire.set_index('hour_bin').sort_index()

    # Hour bouilder function to pass to pool
    def _build_hour_layer(hour: pd.Timestamp):
        # Get fires from previous hours
        start_window = hour - pd.Timedelta(hours = lookback_hours)
        mask = (fire_indexed.index > start_window) & (fire_indexed.index <= hour)
        cells = fire_indexed.loc[mask, 'h3_id'].unique().tolist()

        if len(cells) == 0:
            return LayerGroup(layers = [])

        # Convert cells into a GeoJSON geometry
        geom = h3.cells_to_geo(cells)

        geojson_data = {
            'type': 'Feature',
            'geometry': geom,
            'properties': {}
        }

        # Create single widget for whole fire complex
        layer = GeoJSON(
            data = geojson_data,
            style = {
                'color': '#ff0000',
                'fillColor': '#ff0000',
                'fillOpacity': .6,
                'weight': 1
            }
        )

        return LayerGroup(layers = [layer])

    layers = _get_hour_layers_pooled(_build_hour_layer, timeline)

    end_time = time.time()
    print(f'Finished creating fire layers in {end_time - start_time:.2f} seconds.')
    return layers

def _get_risk_layers(
    risk: pd.DataFrame, 
    timeline: pd.DatetimeIndex,
    cmap: ListedColormap,
    n_bins: int,
    min_risk: float
) -> tuple[dict, dict]:
    start_time = time.time()
    print('Creating risk layers...')
    
    # Drop values below min_risk and create discrete buckets
    risk = risk[risk['risk'] > min_risk].copy()
    risk['style_bin'] = (risk['risk'] * n_bins).astype(int) 

    # Create covered flag (true if covered by fire)
    risk['covered'] = risk['dist_fire'] == 0

    # Compute colors and alphas
    unique_bins = risk['style_bin'].unique()
    style_lookup = {
        b: (mcolors.to_hex(cmap(b/n_bins)), ((b/n_bins)**(1/3)).round(1)) 
        for b in unique_bins
    }

    # Group by hours, covered status, and style bins
    groups = {
        (h, c, b): g['h3_id'].tolist()
        for (h, c, b), g in risk.groupby(['hour_bin', 'covered', 'style_bin'])
    }
    hours_with_data = set(risk['hour_bin'].unique())

    # Hour bouilder function to pass to pool
    def _build_hour_layer(hour: pd.Timestamp):
        if hour not in hours_with_data:
            return LayerGroup(layers = []), LayerGroup(layers = [])
            
        exposed_list = []
        covered_list = []
        
        for b, (color, alpha) in style_lookup.items():
            for layer_list, covered in zip([exposed_list, covered_list], [False, True]):
                cells = groups.get((hour, covered, b))
                if not cells:
                    continue

                geom = h3.cells_to_geo(cells)
                geojson_data = {
                    'type': 'Feature',
                    'geometry': geom,
                    'properties': {}
                }

                layer_list.append(GeoJSON(
                    data = geojson_data,
                    style = {
                        'color': color,
                        'fillColor': color,
                        'fillOpacity': alpha,
                        'weight': 0.5
                    }
                ))
        
        return LayerGroup(layers = exposed_list), LayerGroup(layers = covered_list)

    layers_combined = _get_hour_layers_pooled(_build_hour_layer, timeline)
    exposed_layers = {hour: layers[0] for hour, layers in layers_combined.items()}
    covered_layers = {hour: layers[1] for hour, layers in layers_combined.items()}

    end_time = time.time()
    print(f'Finished creating risk layers in {end_time - start_time:.2f} seconds.')
    return exposed_layers, covered_layers

def get_data_layers(
    lightning: pd.DataFrame,
    fire: pd.DataFrame,
    risk: pd.DataFrame,
    timeline: pd.DatetimeIndex,
    fire_lookback_hours: int,
    risk_cmap: ListedColormap,
    n_risk_bins: int,
    min_risk: float
) -> tuple[dict, dict, dict, dict]:
    with ThreadPoolExecutor(max_workers = 3) as executor:
        f_lightning = executor.submit(get_lightning_layers, lightning, timeline)
        f_fire = executor.submit(_get_fire_layers, fire, timeline, fire_lookback_hours)
        f_risk = executor.submit(_get_risk_layers, risk, timeline, risk_cmap, n_risk_bins, min_risk)
        lightning_layers = f_lightning.result()
        fire_layers = f_fire.result()
        exposed_layers, covered_layers = f_risk.result()
        return lightning_layers, fire_layers, exposed_layers, covered_layers
