#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 15:28:02 2022

@author: stephentoner
"""

import plotly.express as px
import plotly.graph_objects as go

#from sqlalchemy import create_engine


import networkx as nx
import os

import time

import pandas as pd
import dask.dataframe as dd
import world_trade_data as wits

products = wits.get_products()


data = pd.read_csv("total_data_pull.csv")

trade_dict = data.to_dict(orient="records")


#engine = create_engine('sqlite://', echo=False)
duties = pd.read_csv('all_duty_rates_countries_revised.csv')

duties_2017 = duties[duties["Year"] == 2017]
duties_2017 = duties_2017.rename(columns = {"Reporting Economy" : "Reporter",
                                            "Product/Sector Code" : "ProductCode"})

country_codes = dd.from_pandas(duties_2017[["Reporter", "Reporting Economy Code"]],npartitions=10)

partner_codes = dd.from_pandas(country_codes.rename(columns = {"Reporter" : "Partner", 
                                      "Reporting Economy Code": "Partner Economy Code"}), npartitions=10)

df = pd.merge(data, country_codes, on = ['Reporter'])
df = pd.merge(df, partner_codes, how = "left", on = ['Partner'])

lat_long = pd.read_csv('lat_long.csv')

out = df.merge(lat_long, how = "left", left_on = 'Reporter', right_on = 'name')

out = out.rename(columns = {"latitude" : 'imp_lat', "longitude" : "imp_long"})



df = out.merge(lat_long, 
                    left_on = "Partner", 
                    right_on = "name",
                    how = "left").rename(
                        columns = {"latitude" : 'exp_lat',
                                  "longitude" : "exp_long"})
                        
#df.to_sql("trades", engine)

#df.to_csv("merged_data.csv", index = False)     
df.to_pickle("merged_data.pkl")                   
                        
G = nx.Graph()


for i in df.itertuples():    
    # Syntax: Import, Export, edge = list of all data
    G.add_node(i[9], pos = (i[14], i[13]))
    G.add_node(i[10], pos = (i[18], i[17]))
    G.add_edge(i[9], i[10], 
               product = i[4], value = i[7])

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = G.nodes[edge[0]]['pos']
    x1, y1 = G.nodes[edge[1]]['pos']
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
for node in G.nodes():
    x, y = G.nodes[node]['pos']
    node_x.append(x)
    node_y.append(y)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        # colorscale options
        #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        colorscale='YlGnBu',
        reversescale=True,
        color=[],
        size=10,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))

node_adjacencies = []
node_text = []
for node, adjacencies in enumerate(G.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    node_text.append('# of connections: '+str(len(adjacencies[1])))

node_trace.marker.color = node_adjacencies
node_trace.text = node_text

fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>Network graph made with Python',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
fig.show()



