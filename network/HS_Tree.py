#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  1 23:40:03 2022

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

# TO DO: Abstract to class
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
            print(temp_dict[key])
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


data = pd.read_csv("world_imports_2017.csv")

trade_dict = data.to_dict(orient="records")

duties = pd.read_csv('all_duty_rates_countries_revised.csv')

duties_2017 = duties[duties["Year"] == 2017]
duties_2017 = duties_2017.rename(columns = {"Reporting Economy" : "Reporter",
                                            "Product/Sector Code" : "ProductCode"})

country_codes = duties_2017[["Reporter", "Reporting Economy Code"]]

partner_codes = country_codes.rename({"Reporter" : "Partner", 
                                      "Reporting Economy Code": "Partner Economy Code"})


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

clean_df = data[key_labels]

gdf = clean_df.groupby('Reporter')
df = pd.merge(data, country_codes, on = ['Reporter'])
df = df.merge(df, partner_codes, on = ['Partner'])

country_codes_dd = dd.from_pandas(country_codes.set_index("Reporter"))

partner_codes_dd = dd.from_pandas(partner_codes.set_index("Partner"))

data_dd = dd.from_pandas(data.set_index("Reporter"))


t1 = data_dd.merge(country_codes_dd, how ="left", on = ["Reporter"])
t2 = t1.merge(partner_codes_dd, how = "left", on = ["Partner"])


df.to_csv("data_w_codes_test.csv")

G = nx.Graph()


for i in df:
    imp_coords = (i['imp_lat'], i['imp_long'])
    exp_coords = (i['exp_lat'], i['exp_long'])
    G.add_node(imp_coords)
    G.add_node(exp_coords)


