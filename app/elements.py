### Solara app UI elements



###############
### IMPORTS ###
###############

import solara
import pandas as pd
from state import theme
from utils import get_colors



################
### ELEMENTS ###
################

def _html(tag: str, font_size: str, text: str, top_margin: int = 0, bottom_margin: int = 0):
    margins = f'{top_margin}px 0 {bottom_margin}px 0'
    solara.HTML(tag = tag, unsafe_innerHTML = text, style = {
        'margin': margins, 'fontSize': font_size
    })

def header(text: str, top_margin: int = 0, bottom_margin: int = 0):
    _html('h2', '1.6rem', text, top_margin, bottom_margin)

def subheader(text: str, top_margin: int = 0, bottom_margin: int = 0):
    _html('h3', '1.25rem', text, top_margin, bottom_margin)

def _ghost_column(
    width: int,
    top_margin: int = None,
    bottom_margin: int = None,
    left_margin: int = None,
    right_margin: int = None
):
    text_color, glow_color = get_colors(theme)
    style = {
        'position': 'absolute',
        'width': f'{width}px',
        'z-index': '1000',
        'background-color': 'transparent',
        '--text-color': text_color,
        '--glow-color': glow_color
    }
    if top_margin is not None:
        style['top'] = f'{top_margin}px'
    if bottom_margin is not None:
        style['bottom'] = f'{bottom_margin}px'
    if left_margin is not None:
        style['left'] = f'{left_margin}px'
    if right_margin is not None:
        style['right'] = f'{right_margin}px'

    return solara.Column(
        classes = ['ghost-panel'],
        gap = '0px',
        style = style
    )

def left_ghost_column(
    width: int,
    top_margin: int = None,
    bottom_margin: int = None
):
    return _ghost_column(
        width,
        top_margin = top_margin,
        bottom_margin = bottom_margin,
        left_margin = 20
    )

def right_ghost_column(
    width: int,
    top_margin: int = None,
    bottom_margin: int = None
):
    return _ghost_column(
        width,
        top_margin = top_margin,
        bottom_margin = bottom_margin,
        right_margin = 20
    )

def color_bar(
    label: str,
    color_min: str,
    color_mid: str,
    color_max: str,
    left_text: str,
    right_text: str
):
    solara.HTML(tag = 'p', unsafe_innerHTML = label, style = {'textAlign': 'right', 'margin': '0 0 0 0', 'fontWeight': 'bold'})
    solara.Div(classes = ['energy-colorbar'], style = {
        '--color_min': color_min,
        '--color_mid': color_mid,
        '--color_max': color_max
    })
    solara.HTML(
        tag = 'div',
        unsafe_innerHTML = f'<span style="float:left">{left_text}</span><span style="float:right">{right_text}</span>',
        style = {'overflow': 'hidden', 'margin': '2px 0 0 0'}
    )

