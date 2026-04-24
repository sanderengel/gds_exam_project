### App color functions



###############
### IMPORTS ###
###############

import solara



#################
### FUNCTIONS ###
#################

def get_colors(theme: solara.Reactive) -> tuple[str, str]:
    light = theme.value == 'Light'
    text_color = 'black' if light else 'white'
    glow_color = 'white' if light else 'black'
    return text_color, glow_color
