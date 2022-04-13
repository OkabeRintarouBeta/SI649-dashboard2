
import pandas as pd
import os
import sys
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly as plt
import numpy as np

import networkx as nx


from PIL import Image
import requests
from io import BytesIO

def equirectangular(coords, height, width):
    x = (coords[1] + 180) * (width / 360)
    y = ((coords[0] * -1) + 90) * height / 180
    return y, x


def mod_sigmoid(t):
    if t == 0:
        return 0
    else:
        return(1./(1.+np.exp(-t)))


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

code_box = st.selectbox(
    label = "Choose an HS Code:",
    options = hs_codes,
    format_func = ffunc
)

conn_box = st.selectbox(
    label = "How many connections?",
    options = n_conn
)




def fetch(hs_code, nresults = 5):
    base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
    suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'
    
    query = base_url + hs_code + suffix
    fetch = pd.DataFrame(pd.read_json(query, orient='records')['Dataset'].to_dict()).T
    data = fetch.sort_values("Value", ascending = False).groupby('ReportingEconomyCode').head(nresults)

    totals = fetch.groupby('ReportingEconomyCode').agg('sum').sort_values('Value', ascending = False).reset_index()
    totals['Rank'] = totals['Value'].rank(ascending = False)
    totals['ReportingEconomyCode'] = totals['ReportingEconomyCode'].apply(pd.to_numeric)

    return data, totals


code_lookup = str(code_box)
code = str(code_box)
if(len(code_box) < 2):
    code = '0' + code_lookup    

num_results = conn_box


filtered_hs = hs_raw[hs_raw['Product/Sector Code'] == int(code_lookup)]
filtered_hs['Rate'] = filtered_hs['Value'].astype(float) / 100


# filtered_hs['label'] = filtered_hs['Rate'].apply(str)
filtered_hs['label'] = filtered_hs['Rate'].map("{:.2%}".format)
lat_long = pd.read_csv('https://srtoner.github.io/pictures/lat_long.csv').rename(columns={'Lookup' : 'ReportingEconomyCode'}).set_index("ReportingEconomyCode")
reporters = lat_long.rename(columns = {"name" : "Reporter", 'latitude' : 'r_lat', 'longitude' : 'r_long'})
partners = lat_long.rename(columns = {"name" : "Partner", 'latitude' : 'p_lat', 'longitude' : 'p_long'})

data, totals = fetch(code, num_results)

total_red = totals[['ReportingEconomyCode', 'Value', 'Rank']].rename(columns = {'Value' : 'Trade Vol'}).set_index('ReportingEconomyCode')

data['ReportingEconomyCode'] = data['ReportingEconomyCode'].apply(pd.to_numeric)
data['PartnerEconomyCode'] = data['PartnerEconomyCode'].apply(pd.to_numeric)

data = data.set_index('ReportingEconomyCode')

df = pd.merge(data, reporters, left_index = True, right_index = True)
total_df = pd.merge(total_red, partners, left_index = True, right_index = True)
df = pd.merge(df, partners, left_on = "PartnerEconomyCode", right_index = True)



df = df.reset_index()
df = df.rename(columns = {"ReportingEconomyCode" : "ReporterEconomyCode"})

df = df[['ReporterEconomyCode', 
       'PartnerEconomyCode', 
       'Year', 'Value', 'r_lat', 'r_long',
       'Reporter', 'p_lat', 'p_long', 'Partner', 'ProductOrSectorCode']]

fig2 = go.Figure(data=go.Choropleth(
    locations=filtered_hs['Reporting Economy'],
    z=filtered_hs['Rate'],
    locationmode='country names',
    colorscale='Blues',
    hoverinfo = "text",
    hovertext = filtered_hs['Reporting Economy'] + ": " + filtered_hs['label'],
    autocolorscale=False,
    text=filtered_hs['Reporting Economy'], # hover text
    marker_line_color='black', # line markers between countries
    colorbar_title= "Duty/Tariff Rate",
    colorbar_tickformat= "0.2p"
))

ids = []

for i in range(len(df)):
    trade_volume = totals[totals['ReportingEconomyCode'] == df.iloc[i,0]].iloc[0, 11] / 1000000
    trading_rank = totals[totals['ReportingEconomyCode'] == df.iloc[i,0]].iloc[0, 12]
    fig2.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [df['r_long'][i], df['p_long'][i]],
            lat = [df['r_lat'][i], df['p_lat'][i]],
            mode = 'lines+markers',
            hoverinfo = "text",
            # hovertext = (str(df.iloc[i,6]) + ", \n" + 
            #              "Trade USD(M) : " + "${:.1f}".format(trade_volume) + "\n" +
            #              "Trading rank : " + str(trading_rank)
            #              ),
            line = dict(width = 1.2,color = 'red'),
            opacity = mod_sigmoid(df.iloc[i,3] / df['Value'].mean()),
            legendgroup = str(df.iloc[i,6]),
        )        
    )
    ids.append(df.iloc[i,0])


for i in range(len(total_df)):
    fig2.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [total_df.iloc[i, 4]],
            lat = [total_df.iloc[i, 3]],
            mode = 'markers',
            hoverinfo = "text",
            hovertext = (str(total_df.iloc[i,5]) + ", \n" + 
                         "Trade USD(M) : " + "${:,.0f}".format(total_df.iloc[i, 0] / 1000) + "\n" +
                         "Trading rank : " + "{:.0f}".format(total_df.iloc[i, 1])
                         ),
            marker_size = 2 *total_df.iloc[i, 1] / total_df['Rank'].max(),
            marker_colorscale = plt.colors.sequential.Darkmint
            
        )        
    )


# fig2.add_trace(
#     go.Scattergeo(
#         locationmode = 'country names',
#         lon = total_df['p_long'],
#         lat = total_df['p_lat'],
#         mode = 'markers',
#         hoverinfo = "text",
#         mode = 'markers',
#         hoverinfo = "text",
#         hovertext = (total_df['ReportingEconomy']
#                          "Trade USD(M) : " + "${:,.0f}".format(total_df.iloc[i, 0] / 1000) + "\n" +
#                          "Trading rank : " + "{:.0f}".format(total_df.iloc[i, 1])
#                          ),
#             marker_color = total_df.iloc[i, 1] / total_df['Rank'].max(),
#     )        
# )   


fig2.update_layout(
    title_text="Global Trade Network for " + access(hs_dict, code_lookup)["label"],
    geo=dict(
        showframe=False,
        showcoastlines=True,
        showcountries = True,
        showlakes = True,
        projection_type='equirectangular'
    ),
    showlegend = False,
    # legend_orientation = "h",
    # annotations = [dict(
    #     x=0.55,
    #     y=0.1,
    #     xref='paper',
    #     yref='paper',
    #     showarrow = False
    # )]
).update_traces(ids=ids, selector=dict(type='scattergeo'))

# st.plotly_chart(fig, use_container_width = False)

st.plotly_chart(fig2, use_container_width = False)