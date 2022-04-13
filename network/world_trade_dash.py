
import pandas as pd
import os
import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

import networkx as nx


from PIL import Image
import requests
from io import BytesIO

def equirectangular(coords, height, width):
    x = (coords[1] + 180) * (width / 360)
    y = ((coords[0] * 1) + 90) * height / 180
    return y, x


# url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/HD_15000_x_6500_Equirectangular_Blank_Political_Map_with_Oceans_Marked_in_Blue.png/1024px-HD_15000_x_6500_Equirectangular_Blank_Political_Map_with_Oceans_Marked_in_Blue.png"
# response = requests.get(url)
# img = Image.open(BytesIO(response.content))

hs_raw = pd.read_csv("all_2_4_6_digit_duty_rates.csv")

hs_raw = hs_raw[hs_raw['Year'] == 2019]
hs_raw['Value'] = hs_raw['Value'].apply(pd.to_numeric)

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

hs_codes = hs_dict.keys()

labels = []


def ffunc(key):
    if(len(key) == 2) and (key[0] == '0'):
        key = key[1]
    return key + ' - ' + hs_dict[key]['label']
    


for i, key in enumerate(hs_codes):
    labels.append(key + ' - ' + hs_dict[key]['label'])


n_conn = list(range(3, 6))

code_box = st.sidebar.selectbox(
    label = "Choose an HS Code:",
    options = hs_codes,
    format_func = ffunc
)

conn_box = st.sidebar.selectbox(
    label = "How many connections?",
    options = n_conn
)




def fetch(hs_code, nresults = 5):
    base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
    suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'
    
    query = base_url + hs_code + suffix
    fetch = pd.DataFrame(pd.read_json(query, orient='records')['Dataset'].to_dict()).T
    data = fetch.sort_values("Value", ascending = False).groupby('ReportingEconomyCode').head(nresults)
    return data


code_lookup = str(code_box)
code = str(code_box)
if(len(code_box) < 2):
    code = '0' + code_lookup    

num_results = conn_box


filtered_hs = hs_raw[hs_raw['Product/Sector Code'] == int(code_lookup)]

# st.write(hs_raw['Product/Sector Code'].describe())



lat_long = pd.read_csv('https://srtoner.github.io/pictures/lat_long.csv').rename(columns={'Lookup' : 'ReportingEconomyCode'}).set_index("ReportingEconomyCode")

reporters = lat_long.rename(columns = {"name" : "Reporter", 'latitude' : 'r_lat', 'longitude' : 'r_long'})
partners = lat_long.rename(columns = {"name" : "Partner", 'latitude' : 'p_lat', 'longitude' : 'p_long'})

data = fetch(code, num_results)

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

fig = px.line_geo(df, locations="Reporter",
                  color="Value",
                  text = df['Reporter'],#) # "continent" is one of the columns of gapminder)
                  projection="orthographic")


# trades.to_csv('total trade volume 2017.csv', index = False)

for i in range(len(df)):
    fig.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [df['r_long'][i], df['p_long'][i]],
            lat = [df['r_lat'][i], df['p_lat'][i]],
            mode = 'lines+markers',
            hovertext = str(df.iloc[i,6]) + ", " + str(df.iloc[i,9]) + ": " + str(df.iloc[i,3]),
            line = dict(width = 1.2,color = 'red'),
            opacity = float(df['Value'][i]) /  float(df['Value'].max()) ,
        )
        
    )

fig2 = go.Figure(data=go.Choropleth(
    locations=filtered_hs['Reporting Economy'],
    z=filtered_hs['Value'].astype(float) / 100,
    locationmode='country names',
    colorscale='Blues',
    autocolorscale=False,
    text=filtered_hs['Reporting Economy'], # hover text
    marker_line_color='white', # line markers between states
    colorbar_title="Doi"
))

for i in range(len(df)):
    fig2.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [df['r_long'][i], df['p_long'][i]],
            lat = [df['r_lat'][i], df['p_lat'][i]],
            mode = 'lines+markers',
            hovertext = str(df.iloc[i,6]) + ", " + str(df.iloc[i,9]) + ": " + str(df.iloc[i,3]),
            line = dict(width = 1.2,color = 'red'),
            opacity = float(np.log(float(df['Value'][i]))) /  float(np.log(float(df['Value'].max()))) ,
        )        
    )

fig2.update_layout(
    title_text='Global Trade',
    geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type='equirectangular'
    ),
    annotations = [dict(
        x=0.55,
        y=0.1,
        xref='paper',
        yref='paper',
        showarrow = False
    )]
)

st.write(access(hs_dict, code_lookup)["label"])

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


economy_codes = df.ReporterEconomyCode.unique()

G = nx.Graph()
height = 444
width = 1024


network = make_subplots

for code in economy_codes:    
    # Syntax: Import, Export, edge = list of all data
    trades = df[df['ReporterEconomyCode'] == code]
    print(trades.head())
    if(len(trades)):
        name = trades.iloc[0,6]
        lat = trades.iloc[0,4]
        long = trades.iloc[0,5]    
        
        G.add_node(code, pos = equirectangular((lat, long), height, width), name = name)
        for i in range(0,len(trades)):
            partner = trades.iloc[i, 1]
            print(partner)
            p_name = trades.iloc[i,9]
            p_lat = trades.iloc[i,7]
            p_long = trades.iloc[i,8]
            
            product_code = trades.iloc[i,10]
            
            trade_value = trades.iloc[i,3]
            
            G.add_node(partner, pos = equirectangular((p_lat, p_long), height, width), name = p_name)
            G.add_edge(code, partner, value = trade_value, product=product_code)





edge_x = []
edge_y = []
for edge in G.edges():
    y0, x0 = equirectangular(G.nodes[edge[0]]['pos'], height, width)
    y1, x1 = equirectangular(G.nodes[edge[1]]['pos'], height, width)
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)


# edge_trace = px.scatter_geo(
edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    lon=edge_x, lat=edge_y,
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
map_trace = go.Choropleth()



network = go.Figure(data=[node_trace],#, edge_trace],#,map_trace],
              layout=go.Layout(
                title='<br>Network graph made with Python',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                # margin=dict(b=20,l=5,r=5,t=40),
                # annotations=[ dict(
                #     text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                #     showarrow=False,
                #     xref="paper", yref="paper",
                #     x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

# network.add_trace(go.Image(z=img))




st.plotly_chart(fig, use_container_width = False)


st.plotly_chart(fig2, use_container_width = False)

st.plotly_chart(network, use_container_width = False)

# visualizations = ["Visualization 1", "Visualization 2", "Visualization 3", "Visualization 4"]

# select_box = st.sidebar.selectbox(
#     label = "Choose a visual:",
#     options = visualizations
# )