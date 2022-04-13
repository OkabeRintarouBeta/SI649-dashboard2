
import pandas as pd
import os
import sys
import jupytab



def fetch(hs_code, nresults = 5):
    base_url = 'https://api.wto.org/timeseries/v1/data?i=HS_M_0010&r=all&p=all&pc='
    suffix = '&spc=false&ps=2017&max=1000000&fmt=json&mode=codes&lang=1&meta=false&subscription-key=bee004eb9f06452389fd8ed91da707cc'
    
    query = base_url + hs_code + suffix
    fetch = pd.DataFrame(pd.read_json(query, orient='records')['Dataset'].to_dict()).T
    data = fetch.sort_values("Value", ascending = False).groupby('ReportingEconomyCode').head(nresults)
    return data

code = str(sys.argv[1])
num_results = sys.argv[2]        

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


tables['dynamic'] = jupytab.DataFrameTable('Trade', refresh_method=fetch)

# GET /schema
tables.render_schema()

# GET /data
tables.render_data(REQUEST)
