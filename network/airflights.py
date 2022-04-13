import os
import requests
import json
import urllib3
import pandas as pd

import jupytab

http_proxy  = os.environ.get('HTTP_PROXY')
https_proxy = os.environ.get('HTTPS_PROXY')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
proxies = {}

if http_proxy:
    proxies["http"] = http_proxy
    print("HTTP proxy defined as {}".format(http_proxy))
else:
    print("No HTTP proxy defined")
    
if https_proxy:
    proxies["https"] = https_proxy
    print("HTTPS proxy defined as {}".format(http_proxy))
else:
    print("No HTTPS proxy defined")


def compute_flights():
    try:
        states = requests.get(url='https://opensky-network.org/api/states/all',
                              proxies=proxies,
                              verify=False,
                              timeout=5)
        states_json = states.json()['states']
    except Exception as e:
        states_json = [{'icao24': str(e)}]

    return pd.DataFrame(
            data=states_json,
            columns=['icao24', 'callsign', 'origin_country', 'time_position', 'last_contact',
                     'longitude', 'latitude', 'baro_altitude', 'on_ground', 'velocity',
                     'true_track', 'vertical_rate', 'sensors', 'geo_altitude', 'squawk',
                     'spi', 'position_source'])\
        .set_index('icao24')

flight_df = compute_flights()
flight_df.head(5)

tables = jupytab.Tables()
tables['flights'] = jupytab.DataFrameTable('All flights', dataframe=flight_df, refresh_method=compute_flights)

# GET /schema
tables.render_schema()

# GET /data
tables.render_data(REQUEST)