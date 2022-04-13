#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  8 14:26:01 2022

@author: stephentoner
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#from sqlalchemy import create_engine


import networkx as nx
import os

import time

import pandas as pd
import json
from pandas.io.json import json_normalize
import dask.dataframe as dd
import world_trade_data as wits
import numpy as np

usa_imports_2017 = wits.get_indicator('MPRT-TRD-VL',
                                      reporter='usa',
                                      year='2017',
                                      partner='all').reset_index()

hs_raw = pd.read_csv("all_2_4_6_digit_duty_rates.csv")


code_desc = list(hs_raw.columns[3:5])

code_cats = hs_raw.loc[:, code_desc].groupby(
    code_desc).agg('count').reset_index()

code_cats['HS_Code'] = code_cats['Product/Sector Code'].apply(str)
code_cats['Length'] = code_cats['HS_Code'].apply(len)

hs_dict = {}
desc_list = list(code_cats['Product/Sector'])
code_list = list(code_cats.HS_Code)

schema = list(zip(code_list, desc_list))

# Parse the HS Code

for entry in schema:
    code_length = (len(entry[0]) + 1) // 2
    key = entry[0][0:min(len(entry[0]), 2)]
    temp_dict = hs_dict
    for x in range(0, code_length):
        if key in temp_dict:
            temp_dict = temp_dict[key]["children"]
            key = entry[(2*x):(2*x + min(len(entry[0]) - 2*x,2))]
        else:
            temp_dict[key] = {"label": entry[1], "children" : {}}

def access(schema, code):
    temp = code
    source = schema
    while(len(temp) > 2):
        source = source[temp[0:2]]
        temp = temp[2]
    
    return source[temp]

# Now we have the hs dict, we can pull the data for each of the hs codes

base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'

def recursive_fetch(dict_input):
    base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
    suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'
    for key, value in dict_input.items():
        temp_key = str(key)
        if(len(temp_key) == 1):
            temp_key = '0' + temp_key
        query = base_url + temp_key + suffix
        fetch = pd.DataFrame(pd.read_json(query, orient='records')['Dataset'].to_dict()).T
        value['data'] = fetch
        recursive_fetch(value['children'])
        

def fetch(hs_code, nresults = 100):
    base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
    suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'
    
    query = base_url + hs_code + suffix
    fetch = pd.DataFrame(pd.read_json(query, orient='records')['Dataset'].to_dict()).T
    data = fetch.sort_values("Value", ascending = False).groupby('ReportingEconomyCode').head(nresults)
    return data
        

duties = pd.read_csv('all_duty_rates_countries_revised.csv')

lat_long = pd.read_csv('lat_long.csv').rename(columns={'Lookup' : 'ReportingEconomyCode'}).set_index("ReportingEconomyCode")


# duties = duties.rename(columns = {"Reporting Economy" : "Reporter",
#                                             "Product/Sector Code" : "ProductCode"})


# country_lookup = pd.merge(duties.set_index("Reporter"), lat_long, left_index=True, right_index = True)

# location_set = country_lookup.reset_index().set_index("Reporting Economy Code")

# location_set = location_set[['index', 'latitude', 'longitude']]

# location_set = location_set.rename(columns = {"index" : "Reporter"}).drop_duplicates()

reporters = lat_long.rename(columns = {"name" : "Reporter", 'latitude' : 'r_lat', 'longitude' : 'r_long'})
partners = lat_long.rename(columns = {"name" : "Partner", 'latitude' : 'p_lat', 'longitude' : 'p_long'})

data = fetch('01', 5)

data['ReportingEconomyCode'] = data['ReportingEconomyCode'].apply(pd.to_numeric)
data['PartnerEconomyCode'] = data['PartnerEconomyCode'].apply(pd.to_numeric)



data = data.set_index('ReportingEconomyCode')

df = pd.merge(data, reporters, left_index = True, right_index = True)
df = pd.merge(df, partners, left_on = "PartnerEconomyCode", right_index = True)

df = df.reset_index()
df = df.rename(columns = {"ReportingEconomyCode" : "ReporterEconomyCode"})

df = df[['ReporterEconomyCode', 
       'PartnerEconomyCode', 
       'Year', 'Value', 'r_lat', 'r_long',
       'Reporter', 'p_lat', 'p_long', 'Partner', 'ProductOrSectorCode']]

df.to_csv('processed.csv', index = False)


# df = pd.read_csv('processed.csv')
economy_codes = df.ReporterEconomyCode.unique()

G = nx.Graph()

for code in economy_codes:    
    # Syntax: Import, Export, edge = list of all data
    trades = df[df['ReporterEconomyCode'] == code]
    print(trades.head())
    if(len(trades)):
        name = trades.iloc[0,6]
        lat = trades.iloc[0,4]
        long = trades.iloc[0,5]    
        
        G.add_node(code, pos = (lat, long), name = name)
        for i in range(0,len(trades)):
            partner = trades.iloc[i, 1]
            print(partner)
            p_name = trades.iloc[i,9]
            p_lat = trades.iloc[i,7]
            p_long = trades.iloc[i,8]
            
            product_code = trades.iloc[i,10]
            
            trade_value = trades.iloc[i,3]
            
            G.add_node(partner, pos = (p_lat, p_long), name = p_name)
            G.add_edge(code, partner, value = trade_value, product=product_code)




edge_x = []
edge_y = []
for edge in G.edges():
    y0, x0 = G.nodes[edge[0]]['pos']
    y1, x1 = G.nodes[edge[1]]['pos']
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)


# edge_trace = px.scatter_geo(
edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    #lon=edge_x, lat=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
node_text = []
for node in G.nodes():
    y, x = G.nodes[node]['pos']
    node_x.append(x)
    node_y.append(y)
    node_text.append(G.nodes[node]['name'])


# node_trace = px.scatter_geo(
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

for node, adjacencies in enumerate(G.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    

node_trace.marker.color = node_adjacencies
node_trace.text = node_text

map_trace = px.choropleth()
# map_trace = go.Choropleth()

                    # #locations="iso_alpha",
                    # # color="lifeExp", # lifeExp is a column of gapminder
                    # hover_name="Reporter", # column to add to hover information
                    # color_continuous_scale=px.colors.sequential.Plasma)



network = go.Figure(data=[edge_trace, node_trace],#,map_trace],
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

worldmap = px.choropleth(df, #locations="",
                    # color="lifeExp", # lifeExp is a column of gapminder
                    hover_name="Reporter", # column to add to hover information
                    color_continuous_scale=px.colors.sequential.Plasma)

# network.add_choropleth(autocolorscale = True)#, worldmap)


# df = px.data.gapminder().query("year==2007")



# network.add_trace(map)



# fig = make_subplots(specs=[[{"secondary_y": True}]])
# fig.add_trace(network)
# fig.add_trace(worldmap,secondary_y=True)
# fig['layout'].update(height = 600, width = 800, title = "Booh Yahh",xaxis=dict(
#       tickangle=-90
#     ))



# fig.show()

network.add_layout_image(
        dict(
            source="backgroundmap.png",
            xref="x",
            yref="y",
            x=0,
            y=3,
            sizex=2,
            sizey=2,
            sizing="stretch",
            opacity=0.5,
            layer="below")
)

network.show()


fig = px.line_geo(df, locations="Reporter",
                  color="Partner", # "continent" is one of the columns of gapminder
                  projection="orthographic")


# trades.to_csv('total trade volume 2017.csv', index = False)

for i in range(len(df)):
    fig.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [df['r_long'][i], df['p_long'][i]],
            lat = [df['r_lat'][i], df['p_lat'][i]],
            mode = 'lines',
            line = dict(width = 1,color = 'red'),
            opacity = float(np.log(float(df['Value'][i]))) /  float(np.log(float(df['Value'].max()))) ,
        )
    )

fig.show()