# -*- coding: utf-8 -*-
"""
Produces proportion plot from given Pandas dataframe, showing the evolution from value 1 to value 2.

Dataframe format:
Data name, value 1, value 2 

@author: Virginie Mathivet
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math

TEXT_MARGIN = 0.05
BAR_WIDTH = 0.02
GRAPH_WIDTH = 4
TEXT_WIDTH = 1.5

def proportion_plot(df, color_palette='hls', color_dict=None, vertical_space=1, fontsize=9, alpha=0.65, with_text=True, text_inside=False, with_axis_title=False, mode='smooth', image_filename=None):
    '''
    Make proportion plot for dataframe df
    
    Inputs:
        df = Dataframe with 3 columns: names, first value (left), last value (right)
        color_palette = Color palette from Seaborn (default: 'hls') or 'Teamwork'. Ignored if color_dict is not None
        color_dict = Dictionnary of colors. Warning: must be of same length than data 
        vertical_space = Space between data on vertical axis
        fontsize = Font size for texts (left and right bar)
        alpha = Alpha for strips inside
        with_text = Boolean indicating if categories are shown
        text_inside = Boolean indicating if categories are shown in a color block
        with_axis_title = Boolean indicating if bar names are shown. Ignored if with_text is False
        mode = 'linear', 'sigmoid' or 'smooth' connection between left and right nods
        image_filename = save image with this filename if not None (filetype: png)
        
    Outputs:
        None
    '''
    labels = df.iloc[:,0]
    colorDict = get_color_palette(color_palette, color_dict, labels)
    fig = init_figure()
    left_tops = create_bar('left', labels, df.columns[1], df.iloc[:,1], with_text, text_inside, with_axis_title, colorDict, fontsize, vertical_space, fig)
    right_tops = create_bar('right', labels, df.columns[2], df.iloc[:,2], with_text, text_inside, with_axis_title, colorDict, fontsize, vertical_space, fig)
    create_strips(labels, left_tops, right_tops, mode, vertical_space, alpha, colorDict)
    if image_filename is not None:
        save_image(image_filename)
    
def init_figure():
    fig = plt.figure(figsize=[10,6])
    plt.xlim([-1*TEXT_WIDTH, TEXT_WIDTH+GRAPH_WIDTH])
    plt.gca().axis('off')
    return fig
    
def get_color_palette(color_palette, color_dict, labels):
    ''' Create color palette, event from color_palette or color_dict 
        Return color dictionnary
    '''
    colorDict = {}
    if color_dict is not None:
        return get_color_palette_from_dict(labels, color_dict)
    if color_palette == 'Teamwork':
        return get_color_palette_teamwork(labels)
    return get_color_palette_from_sns(labels, color_palette)

def get_color_palette_from_dict(labels, color_dict):
    colorDict = {}
    for i, label in enumerate(labels):
        colorDict[label] = color_dict[i]
    return colorDict

def get_color_palette_teamwork(labels):
    colorDict = {}
    start = [5/255, 29/255, 73/255] # Teamwork dark blue
    stop = [0/255, 164/255, 227/255] # Teamwork light blue
    nb = len(labels)
    for i, label in enumerate(labels):
        colorDict[label] = get_intermediate_color(start, stop, i, nb)
    return colorDict

def get_intermediate_color(start, stop, step, nb):
    color = [0, 0, 0]
    for i in range(0, 3):
        color[i] = start[i] + (stop[i]-start[i]) * step / (nb-1) 
    return color

def get_color_palette_from_sns(labels, color_palette):
    colorDict = {}
    colorPalette = sns.color_palette(color_palette, len(labels))
    for i, label in enumerate(labels):
        colorDict[label] = colorPalette[i]
    return colorDict
    
def create_bar(side, labels, name, values, with_text, text_inside, with_axis_title, colorDict, fontsize, vertical_space, fig):
    ''' Create bar on side (left or right) and draw it
        Return tops values
    '''
    x_bar, x_text, ha = get_config_for_bars(side)

    # Compute vertical positions
    tops = [0]
    for i, element in enumerate(values):
        tops.append(tops[i] + element + vertical_space)
    
    # Draw texts
    if with_text:
        for i, element in enumerate(values):
            res = plt.text(x_text, tops[i]+element/2.0, labels[i], {'ha': ha, 'va': 'center'}, fontsize=fontsize)
    
    # Draw node bars
    if text_inside:
        width = TEXT_WIDTH
        x_bar = integrate_text_width(x_bar, width, side)
    for i, element in enumerate(values):
        plt.fill_between(x_bar, tops[i], tops[i]+element, color=colorDict[labels[i]])
        
    # Draw axis title
    if with_text and with_axis_title:
        plt.text(x_text, -1, name, {'ha': ha, 'va': 'top'}, fontsize=fontsize)

    return tops

def get_config_for_bars(side):
    if side == 'left':
        x_bar_width = [-1*BAR_WIDTH, 0]
        x_text = -1 * TEXT_MARGIN
        horizontal_align = 'right'
    else:
        x_bar_width = [GRAPH_WIDTH, GRAPH_WIDTH+BAR_WIDTH]
        x_text = GRAPH_WIDTH + TEXT_MARGIN
        horizontal_align = 'left'
    return x_bar_width, x_text, horizontal_align

def get_maximum_width(boxes, side):
    if len(boxes) == 0:
        return 0
    else:
        if side == 'left':
            width = min(box.x0 for box in boxes) * -1
        else:
            width = max(box.x1 for box in boxes) - 1
        return width  # box is always too small

def integrate_text_width(x_bar, width, side):
    if side == 'left':
        x_bar[0] = -1 * (width + 2 * TEXT_MARGIN)
    else:
        x_bar[1] = GRAPH_WIDTH + width + 2 * TEXT_MARGIN
    return x_bar
    
def create_strips(labels, left_tops, right_tops, mode, vertical_space, alpha, colorDict):
    for i, element in enumerate(labels):
        y_min, ticks = get_points(left_tops[i], right_tops[i], mode)
        y_max, ticks = get_points(left_tops[i+1]-vertical_space, right_tops[i+1]-vertical_space, mode)
        plt.fill_between(ticks, y_min, y_max, alpha=alpha, color=colorDict[labels[i]])

def get_points(y1, y2, mode):
    if mode == 'linear':
        return [y1, y2], [0, GRAPH_WIDTH]
    elif mode == 'sigmoid':
        return get_sigmoid_points(y1, y2)
    else: # mode == 'smooth'
        return get_smooth_points(y1, y2)

def get_sigmoid_points(y1, y2):
    res = []
    ticks = np.linspace(0, 1, 150) * GRAPH_WIDTH
    for x in range(-75, 75):
        gauss = 1 / (1 + math.exp(-x/10))
        res.append(y1 + gauss * (y2-y1))
    return res, ticks
    
def get_smooth_points(y1, y2):
    res = []
    ticks = np.linspace(0, 1, 100) * GRAPH_WIDTH
    for x in range(0, 100):
        smooth = -2 * (y2-y1) * pow(x/100, 3) + 3 * (y2-y1) * pow(x/100, 2)
        res.append(y1 + smooth)
    return res, ticks
    
def save_image(filename):
    plt.savefig(filename, bbox_inches='tight', dpi=150)