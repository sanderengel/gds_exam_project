### Compute the risk layer



###############
### IMPORTS ###
###############

import numpy as np
import pandas as pd
from utils import load_cell_hours



#################
### LOAD DATA ###
#################

cell_hours = load_cell_hours()



######################
### TRANSFORM DATA ###
######################

# Log-transform lightning energy
# TODO: MOVE INTO LOOP AFTER AGGREGATION
cell_hours['energy_log'] = np.log1p(cell_hours['energy'])



##########################
### SPLIT INTO REGIONS ###
##########################

# Assign region 3 as the test set
train = cell_hours[cell_hours['region'] != 3].copy()
test = cell_hours[cell_hours['region'] == 3].copy()
X_train, y_train = train[[col for col in train.columns if col != 'fire_onset']], train['fire_onset']
X_test, y_test = test[[col for col in test.columns if col != 'fire_onset']], test['fire_onset']



#################################
### CROSS-VALIDATION TRAINING ###
#################################

# Define hyperparameter space
CV_REGIONS = [1, 2, 4]  # Exclude region 3 for testing

results = []

for val_region in CV_REGIONS:
    # TODO: Implement model
    pass