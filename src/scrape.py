import datetime as dt
import json
import os
import sys
import time

from typing import NamedTuple, Dict

import requests
import sqlite3

import db
from schemas import WeatherRecord, WeatherTimeline, WeatherTimelineRecord, WeatherTimelineValues, Weather, DB_FILE

class Coordinate(NamedTuple):
    latitude: float
    longitude: float

# As this list of infrequently changing values increases I would move them out to
# a "configs.py" file. Some poeple move it out to json but I don't like how that
# breaks intellisense. I'm only a fan of json/yaml config files when I expect an
# end user to have to modify them.

COORDS = (
    Coordinate(25.86, -97.42),
    Coordinate(25.90, -97.52),
    Coordinate(25.90, -97.48),
    Coordinate(25.90, -97.44),
    Coordinate(25.90, -97.40),
    Coordinate(25.92, -97.38),
    Coordinate(25.94, -97.54),
    Coordinate(25.94, -97.52),
    Coordinate(25.94, -97.48),
    Coordinate(25.94, -97.44)
)
API_URL = "https://api.tomorrow.io/v4/"

DATA_DIRECTORY = os.path.join(os.getcwd(), "data")

# We need the option to read json from files to reduce how many api calls we run while testing
if len(sys.argv) < 2:
    FROM_FILE = False
else: 
    FROM_FILE = sys.argv[1] == "from_file"

if __name__ == '__main__':
    # Do not hardcode access keys ever!! In a production env I would secure this with KMS, secrets manager, cyberark, etc
    with open(os.path.join(DATA_DIRECTORY, "api_key")) as fp:
        api_key = fp.read()
    coord_forecast_mapping: Dict[Coordinate, WeatherRecord] = {}
    coord_measured_mapping: Dict[Coordinate, WeatherRecord] = {}
    # I'm not bothering with a context manager because they don't close connections.
    # https://docs.python.org/3/library/sqlite3.html#sqlite3-connection-context-manager
    conn = sqlite3.connect(os.path.join(os.getcwd(), "data", DB_FILE))
    cursor = conn.cursor()
    for coord in COORDS:
        location_string = f"{coord.latitude}, {coord.longitude}"
        if FROM_FILE:

            forecast_fname = os.path.join(DATA_DIRECTORY, f"forecast_response_{location_string}.json")
            if not os.path.exists(forecast_fname):
                print(f"Missing forecast file for {coord}. Skipping.")
                continue
            with open(forecast_fname) as fp:
                forecast_response = json.load(fp)

            measured_fname = os.path.join(DATA_DIRECTORY, f"measured_response_{location_string}.json")
            if not os.path.exists(measured_fname):
                print(f"Missing forecast file for {coord}. Skipping.")
                continue
            with open(measured_fname) as fp:
                measured_response = json.load(fp)

        else:
            forecast_response = requests.get(API_URL+"weather/forecast",
                        params={  # ALWAYS use params for GET!! Never build the query string yourself!! I have battle scars!!!!
                            # if i wanted to be super obsessive I would make a dataclass for this dict
                            "apikey": api_key,
                            "location": location_string,
                            "units": "metric",
                            "timesteps": "1h"

                        })
            # Requests are pretty heavily throttled
            if forecast_response.status_code == 429:
                print(f"We got throttled. Skipping {coord}.")  # Ideally I would be using pythons logging library
                continue
            time.sleep(1)
            with open(os.path.join(DATA_DIRECTORY, f"forecast_response_{location_string}.json"), "w") as fp:
                fp.write(forecast_response.text)
            forecast_response = json.loads(forecast_response.text)

            measured_response = requests.get(API_URL+"weather/history/recent",
                        params={  
                            "apikey": api_key,
                            "location": location_string,
                            "units": "metric",
                            "timesteps": "1h"

                        })
            if measured_response.status_code == 429:
                print(f"We got throttled. Skipping {coord}.") 
                continue
            time.sleep(1)
            with open(os.path.join(DATA_DIRECTORY, f"measured_response_{location_string}.json"), "w") as fp:
                fp.write(measured_response.text)
            measured_response = json.loads(measured_response.text)

        # This is redundant and hard to change but
        # worth the benefits of working with dataclasses.
        # There's ways to just pass in dictionaries to dataclasses
        # with __post_init__ but it's a pain to set up.
        coord_forecasted_record = WeatherRecord(
            timelines=WeatherTimeline(
                daily=None,
                minutely=None,
                hourly=[WeatherTimelineRecord(
                    time=r["time"], 
                    values=WeatherTimelineValues(
                        windSpeed=r["values"]["windSpeed"],
                        temperature=r["values"]["temperature"],
                        humidity=r["values"]["humidity"],
                        uvIndex=r["values"]["uvIndex"] if "uvIndex" in r["values"] else None
                    )
                ) for r in forecast_response["timelines"]["hourly"]],
        ))

        coord_measured_record = WeatherRecord(
            timelines=WeatherTimeline(
                daily=None,
                minutely=None,
                hourly=[WeatherTimelineRecord(
                    time=r["time"], 
                    values=WeatherTimelineValues(
                        windSpeed=r["values"]["windSpeed"],
                        temperature=r["values"]["temperature"],
                        humidity=r["values"]["humidity"],
                        uvIndex=r["values"]["uvIndex"]
                    )
                ) for r in measured_response["timelines"]["hourly"]],
        ))
        
        database_records = [Weather(
            datetime_added=dt.datetime.now(), 
            datetime=r.time,
            is_measured=False,
            longitude=coord.longitude,
            latitude=coord.latitude,
            windSpeed=r.values.windSpeed,
            temperature=r.values.temperature,
            humidity=r.values.humidity,
            uvIndex=r.values.uvIndex)
        for r in coord_forecasted_record.timelines.hourly]

        database_records += [Weather(
            datetime_added=dt.datetime.now(), 
            datetime=r.time,
            is_measured=True,
            longitude=coord.longitude,
            latitude=coord.latitude,
            windSpeed=r.values.windSpeed,
            temperature=r.values.temperature,
            humidity=r.values.humidity,
            uvIndex=r.values.uvIndex)
        for r in coord_measured_record.timelines.hourly]

        db.insert(cursor, database_records)
    conn.commit()
    conn.close()
    print("DONE")