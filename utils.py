### General utility functions



###############
### IMPORTS ###
###############

import pandas as pd



#################
### FUNCTIONS ###
#################

def load_lightning_df(N: int = None):
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