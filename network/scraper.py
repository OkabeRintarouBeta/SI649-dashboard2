import time

import pandas as pd
import world_trade_data as wits
import requests

countries = pd.read_csv('countries.csv')

def get_world_trade(partners, indicator, year_str):
    df = wits.get_indicator(indicator, reporter=partners[0], 
                                          year=year_str,
                                          partner = 'all',
                                          product='all').reset_index()
    non_reporters = []
    partner = partners[1:]
    for p in partner:
        try:
            df_t = wits.get_indicator(indicator, 
                                   reporter=p, 
                                   year=year_str,
                                   partner = 'all').reset_index()
            
            df = pd.concat((df, df_t))
            # time.sleep(10)
        except:
            non_reporters.append(p)
    return df, non_reporters

country_list = list(countries['ISO3'])
#country_list = list(pd.read_csv('reporters.csv'))
print(country_list[0])
world_imports, non_reporters = get_world_trade(country_list,'MPRT-TRD-VL', '2017')
world_exports, non_reporters = get_world_trade(country_list,'XPRT-TRD-VL', '2017')

# Code Fetch
# http://wits.worldbank.org/API/V1/SDMX/V21/rest/codelist/all/

world_imports.to_csv("total_data_pull.csv", index = False)


top_partners = world_imports.sort_values("Value", ascending = False).groupby(['Reporter', 'ProductCode']).head(5)

top_partners.to_csv("top_partners.csv")
