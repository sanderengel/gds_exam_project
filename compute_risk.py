### Compute the risk layer



###############
### IMPORTS ###
###############

import h3
import numpy as np
import pandas as pd
from utils import load_cell_hours
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression



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

# Create geo lookup
geo_lookup = cell_hours[['h3_id']].drop_duplicates()
geo_lookup['lat'] = geo_lookup['h3_id'].apply(lambda x: h3.cell_to_latlng(x)[0])

# Get back latitude and split into regions
geo_lookup['region'] = pd.qcut(geo_lookup['lat'], 4, labels = [1, 2, 3, 4])
cell_hours = cell_hours.merge(geo_lookup[['h3_id', 'lat', 'region']], on = 'h3_id', how = 'left')

# Define quartile boundaries
q1, q2, q3 = cell_hours['lat'].quantile([.25, .5, .75])
boundaries = [q1, q2, q3]

# Define buffer width
BUFFER_DEGREES = .09 # Approximately 10km
half_buffer = BUFFER_DEGREES / 2

# Create buffer mask, keeping rows outside the half_buffer of any boundary
is_in_buffer = pd.Series(False, index = cell_hours.index)
for b in boundaries:
    is_in_buffer |= (
        (cell_hours['lat'] > (b - half_buffer)) &
        (cell_hours['lat'] < (b + half_buffer))
    )

# Remove data inside buffer zones
cell_hours_buffered = cell_hours[~is_in_buffer].copy()

# Assign region 3 as the test set
train = cell_hours_buffered[cell_hours_buffered['region'] != 3].copy()
test = cell_hours_buffered[cell_hours_buffered['region'] == 3].copy()
X_train, y_train = train[[col for col in train.columns if col != 'fire_onset']], train['fire_onset']
X_test, y_test = test[[col for col in test.columns if col != 'fire_onset']], test['fire_onset']

print(f'Original rows: {len(cell_hours)}')
print(f'Rows after {BUFFER_DEGREES} degree buffers: {len(cell_hours_buffered)}')
print(f'Data loss from buffers: {((len(cell_hours) - len(cell_hours_buffered)) / len(cell_hours)) * 100:.2f}%')



#################################
### CROSS-VALIDATION TRAINING ###
#################################

# Define hyperparameter space
K_VALUES = [0, 1, 2, 3, 4]
W_VALUES = [24, 48, 72] # Window size in hours
CV_REGIONS = [1, 2, 4]  # Exclude region 3 for testing

results = []

for k in K_VALUES:
    # TODO: Spatial aggregation

    for w in W_VALUES:
        # TODO: Temporal aggregation

        fold_scores = []

        for val_region in CV_REGIONS:
            # TODO: Implement model
            pass