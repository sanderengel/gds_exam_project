### Global state variables



###############
### IMPORTS ###
###############

import solara



################################
### DYNAMIC SOLARA VARIABLES ###
################################

theme = solara.reactive('Dark')
time_index = solara.reactive(0)
show_lightning = solara.reactive(True)
show_fire = solara.reactive(True)
show_risk = solara.reactive(True)
selected_layers = solara.reactive(['Lightning', 'Fire', 'Risk'])