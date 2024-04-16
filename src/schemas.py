import datetime as dt

from dataclasses import dataclass, fields
from typing import List, Optional

import os

import sqlite3

# REST SCHEMAS
@dataclass
class WeatherTimelineValues:
    # The way this dataclass is set up and inherited below means
    # any field I add from the http api request will automatically
    # start populating into the sqlite database when we execute.
    # For brevity's sake I am only adding two fields from the problem statement
    # (temp, windspeed) and two others documented at
    # https://docs.tomorrow.io/reference/weather-forecast
    windSpeed: float
    temperature: float

    humidity: int
    uvIndex: Optional[int]


@dataclass
class WeatherTimelineRecord:
    time: str
    values: WeatherTimelineValues


@dataclass
class WeatherTimeline:
    hourly: Optional[List[WeatherTimelineRecord]]
    minutely: Optional[List[WeatherTimelineRecord]]
    daily: Optional[List[WeatherTimelineRecord]]

    def __post_init__(self):
        if not (self.hourly or self.minutely or self.daily):
            raise ValueError(
                "At least one of hourly, minutely, and daily must not be None"
            )


@dataclass
class WeatherRecord:
    timelines: WeatherTimeline


# RDBMS SCHEMAS

# I'm kind of writing my own ORM here. In my experience I could end up spending as much time fighting with SQLAlchemy as it took
# to write this project. That upfront cost pays off for large projects.

# python type to sql type
def __p2s(t: type) -> str:
    if t in (int, bool, Optional[int]):
        return "INTEGER"
    elif t == float:
        return "REAL"
    elif t == dt.datetime: 
        return "DATETIME"
    elif t == str:
        return "TEXT"
    else:
        raise TypeError(f"Unhandled python to sqlite type: {t}")
    

@dataclass(kw_only=True)
class DBOutputRecord:
    # This is messy. SQLAlchemy can have these automatically populate with default
    # primary key and NOW() values.
    id: Optional[int] = None
    datetime_added: dt.datetime


# This is a little messy but it allows me to use multiple inheritance to set the column order
# in the Weather class below
@dataclass
class WeatherFields:
    datetime: str # this should be a datetime object but there's a bunch of timezone edge cases
                  # that need to be handled with that data type.
    is_measured: bool  # true if weather data is measured. false if it is forecasted
    longitude: float
    latitude: float


@dataclass
class Weather(WeatherTimelineValues, WeatherFields, DBOutputRecord):
    pass


DB_FILE = "Weather.db"
TABLE_NAME = "Weather"

# This is technically dynamic sql but the dynamic parts can only be modified if you have access to this code, 
# so the risk of sql injection is extremely low.
# An alternative way of saying this is reating a table is NEVER a consequence of end user input.
temperature_fields = ",".join([f"{f.name} {__p2s(f.type)}" for f in fields(Weather) if f.name != "id"])
all_temperature_fields = "id INTEGER PRIMARY KEY AUTOINCREMENT,"+temperature_fields
def create_table():
    conn = sqlite3.connect(os.path.join(os.getcwd(), "data", DB_FILE))
    cursor = conn.cursor()
    # This table has too many columns and probably needs to be normalized
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({all_temperature_fields});")
    print("Created table!")

    # For small projects I am fine migrating table schemas by hand instead of trying to dynamically
    # alter columns. For a big project I would use Alembic
    database_fields = {r[1] for  r in cursor.execute(f"Pragma table_info({TABLE_NAME});").fetchall()}
    if {f.name for f in fields(Weather)} != database_fields:
        raise RuntimeError("Database schema does not match schemas.py")
    conn.close()
create_table()