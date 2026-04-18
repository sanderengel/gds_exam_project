### General utility functions



###############
### IMPORTS ###
###############

import sys
import solara
import pandas as pd



#################
### FUNCTIONS ###
#################

def get_colors(theme: solara.Reactive) -> tuple[str, str]:
    light = theme.value == 'Light'
    text_color = 'black' if light else 'white'
    glow_color = 'white' if light else 'black'
    return text_color, glow_color

def load_lightning_df(N: int = None) -> pd.DataFrame:
    sys.path.append('../')
    lightning_path = 'data/lightning/california_lightning_siege_2020.feather'
    lightning = pd.read_feather(lightning_path)
    lightning = lightning.sort_values(by = 'timestamp', ascending = True)

    if N is not None:
        lightning = lightning.head(N)

    return lightning

# def load_fire_df(N: int = None):
#     fire_path = 'data/fire/DL_FIRE_SV-C2_730956/fire_archive_SV-C2_730956.csv'
#     fire = pd.read_csv(fire_path)
#     fire = fire.sort_values(by = '')