# -*- coding: utf-8 -*-

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import plotly.io as py
import matplotlib.colors as mcolors

commute_flows = pd.read_csv('C:/Users/agaaz/.spyder-py3/Commute Flows1.csv')
commute_flows['County Name Residence'] = commute_flows['County Name Residence'].apply(lambda x: 'From ' + x)

# Define the mapping from county name to borough name
county_to_borough = {
    'From New York County': 'From Manhattan',
    'From Kings County': 'From Brooklyn',
    'From Bronx County': 'From Bronx',
    'From Queens County': 'From Queens',
    'New York County': 'Manhattan',
    'Kings County': 'Brooklyn',
    'Bronx County': 'Bronx',
    'Queens County': 'Queens'
}


commute_flows = commute_flows[~commute_flows['County Name Residence'].isin(['From Richmond County'])]
commute_flows = commute_flows[~commute_flows['County Name Workplace'].isin(['Richmond County'])]

commute_flows.replace({'County Name Residence': county_to_borough}, inplace=True)
commute_flows.replace({'County Name Workplace': county_to_borough}, inplace=True)

all_nodes = pd.concat([commute_flows['County Name Residence'], commute_flows['County Name Workplace']]).unique()

# Define pastel color list
colors = ['LightSkyBlue', 'PaleGreen', 'LightCoral', 'LemonChiffon', 'Thistle']

colors_rgba = [mcolors.to_rgba(color, alpha=0.8) for color in colors]

node_colors = [f'rgba({int(color[0]*255)},{int(color[1]*255)},{int(color[2]*255)},0.8)' 
               for color in colors_rgba for _ in range(2)]

node_dict = {node: index for index, node in enumerate(all_nodes)}

# Create a dictionary to map nodes to their corresponding colors
color_dict = {node: color for node, color in zip(all_nodes, node_colors)}

# Use the dictionaries to populate the color values for each link
link_colors = [color_dict[commute_flows['County Name Residence'].iloc[i]] for i in range(len(commute_flows))]

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=all_nodes,
        color=node_colors
    ),
    link=dict(
        source=commute_flows['County Name Residence'].map(node_dict).values,
        target=commute_flows['County Name Workplace'].map(node_dict).values,
        value=commute_flows['Workers in Commuting Flow'].values,
        color=link_colors
    ))])

fig.update_layout(font=dict(
    family="Arial Black",
    size=20,
    color="black"
))

fig.show()

# Save the figure
py.write_html(fig, 'nyc_commute_flows.html')



