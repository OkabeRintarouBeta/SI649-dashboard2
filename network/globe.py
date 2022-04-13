#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 26 11:52:12 2022

@author: stephentoner
"""
import plotly.express as px
import plotly.graph_objects as go
import os.path as os

import time

import pandas as pd
import world_trade_data as wits

from scraper import get_world_trade

# def get_world_trade(partners, indicator, year_str):
#     df = wits.get_indicator(indicator, reporter=partners[0], 
#                                           year=year_str,
#                                           partner = 'all').reset_index()
#     non_reporters = []
#     partner = partners[1:]
#     for p in partner:
#         try:
#             df_t = wits.get_indicator(indicator, 
#                                    reporter=p, 
#                                    year=year_str,
#                                    partner = 'all').reset_index()
            
#             df = pd.concat((df, df_t))
#         except:
#             non_reporters.append(p)
#     return df, non_reporters


regions = ['World', 
           'East Asia and Pacific', 
           'Europe and Central Asia', 
           'Latin America and Caribbean',
           'North America',
           'Middle East and North Africa']



files = ['allcountries.csv', 'reporters.csv', 'total trade volume 2017.csv', 'world_imports_2017.csv']

missing_files = [x for x in files if not os.exists(x)]

if(missing_files):
    usa_imports_2017 = wits.get_indicator('MPRT-TRD-VL', 
                                        reporter='usa', 
                                        year='2017',
                                        partner = 'all').reset_index()

    countries = list(usa_imports_2017[~usa_imports_2017['Partner'].isin(regions)]['Partner'].unique())
    country_list = list(countries['ISO3'])
    world_imports, non_reporters = get_world_trade(country_list,'MPRT-TRD-VL', '2017')
    world_exports, non_reporters = get_world_trade(country_list,'XPRT-TRD-VL', '2017')

    reporters = []

    for c in country_list:
        if c not in non_reporters:
            reporters.append(c)
            

    world_imports.to_csv('world_imports_2017.csv', index = False)
    # world_exports
    pd.DataFrame(reporters).to_csv('reporters.csv', index = False)


countries = pd.read_csv('countries.csv')
country_list = list(pd.read_csv('reporters.csv').iloc[:,0])

world_imports = pd.read_csv('world_imports_2017.csv')


total_imports = world_imports.groupby(['Reporter', 'Partner']).agg('sum').reset_index()

lat_long = pd.read_csv('lat_long.csv')

out = total_imports.reset_index().merge(lat_long, left_on = 'Reporter', right_on = 'name')

out = out.rename(columns = {"latitude" : 'imp_lat', "longitude" : "imp_long"})




trades = out.merge(lat_long, 
                    left_on = "Partner", 
                    right_on = "name").rename(
                        columns = {"latitude" : 'exp_lat',
                                  "longitude" : "exp_long"})

top_trades = trades.sort_values("Value").groupby('Partner').head(5)                            

print(top_trades.head())


fig = px.line_geo(trades, locations="Reporter",
                  color="Partner", # "continent" is one of the columns of gapminder
                  projection="orthographic")


trades.to_csv('total trade volume 2017.csv', index = False)

for i in range(len(trades) // 2):
    fig.add_trace(
        go.Scattergeo(
            locationmode = 'country names',
            lon = [trades['imp_long'][i], trades['exp_long'][i]],
            lat = [trades['imp_lat'][i], trades['exp_lat'][i]],
            mode = 'lines',
            line = dict(width = 1,color = 'red'),
            opacity = float(trades['Value'][i]) / float(trades['Value'].max()),
        )
    )

fig.show()