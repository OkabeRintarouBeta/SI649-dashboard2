#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 18:50:54 2022

@author: stephentoner
"""


import plotly.express as px
import plotly.graph_objects as go

import networkx as nx
import os

import time

import pandas as pd
import dask.dataframe as dd
import world_trade_data as wits


df = pd.read_pickle("merged_data.pkl")

df = df[df["ProductCode"] == 'Food Products']    


key_labels = ['Reporter', 
              'Partner', 
              'ProductCode',
              'Value', 
              'Reporting Economy Code',
              'Partner Economy Code', 
              'imp_lat', 
              'imp_long', 
              'exp_lat', 
              'exp_long']


clean_dd = dd.from_pandas(df[key_labels].dropna(
                            ),
                            npartitions = 10)

# clean_df = df[key_labels]
# alt_dict = clean_df.to_dict('records')

gdf = clean_dd.groupby('Reporter')

reporter_codes = df['Reporting Economy Code'].unique()



G = nx.Graph()
for group in clean_dd:
    print(group)
    G.add_node(name, data = group)

reporter_codes = []

for i in alt_dict:
    reporter_codes.append(i['Reporting Economy Code'])
    


                  
# G = nx.Graph()

# for i in df.itertuples():    
#     # Syntax: Import, Export, edge = list of all data
#     G.add_node(i[10], pos = (i[15], i[14]), name = i[3])
#     G.add_node(i[11], pos = (i[19], i[18]), name = i[4])
#     G.add_edge(i[10], i[11], 
#                product = i[5], value = i[8])




# for i in df.itertuples():    
#     # Syntax: Import, Export, edge = list of all data
#     G.add_node(i[10], pos = (i[15], i[14]), name = i[3])
#     G.add_node(i[11], pos = (i[19], i[18]), name = i[4])
#     G.add_edge(i[10], i[11], 
#                product = i[5], value = i[8])

# edge_x = []
# edge_y = []
# for edge in G.edges():
#     x0, y0 = G.nodes[edge[0]]['pos']
#     x1, y1 = G.nodes[edge[1]]['pos']
#     edge_x.append(x0)
#     edge_x.append(x1)
#     edge_x.append(None)
#     edge_y.append(y0)
#     edge_y.append(y1)
#     edge_y.append(None)

# edge_trace = go.Scatter(
#     x=edge_x, y=edge_y,
#     line=dict(width=0.5, color='#888'),
#     hoverinfo='none',
#     mode='lines')

# node_x = []
# node_y = []
# for node in G.nodes():
#     x, y = G.nodes[node]['pos']
#     node_x.append(x)
#     node_y.append(y)

# node_trace = go.Scatter(
#     x=node_x, y=node_y,
#     mode='markers',
#     hoverinfo='text',
#     marker=dict(
#         showscale=True,
#         # colorscale options
#         #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
#         #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
#         #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
#         colorscale='YlGnBu',
#         reversescale=True,
#         color=[],
#         size=10,
#         colorbar=dict(
#             thickness=15,
#             title='Node Connections',
#             xanchor='left',
#             titleside='right'
#         ),
#         line_width=2))

# node_adjacencies = []
# node_text = []
# for node, adjacencies in enumerate(G.adjacency()):
#     node_adjacencies.append(len(adjacencies[1]))
#     node_text.append('# of connections: '+str(len(adjacencies[1])))

# node_trace.marker.color = node_adjacencies
# node_trace.text = node_text

# fig = go.Figure(data=[edge_trace, node_trace],
#              layout=go.Layout(
#                 title='<br>Network graph made with Python',
#                 titlefont_size=16,
#                 showlegend=False,
#                 hovermode='closest',
#                 margin=dict(b=20,l=5,r=5,t=40),
#                 annotations=[ dict(
#                     text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
#                     showarrow=False,
#                     xref="paper", yref="paper",
#                     x=0.005, y=-0.002 ) ],
#                 xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#                 yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
#                 )
# fig.show()