from dataclasses import fields, astuple

from typing import List

import sqlite3

from schemas import Weather, TABLE_NAME

# update, and delete are to be added as needed
def insert(cursor: sqlite3.Cursor, records: List[Weather]) -> None:
    # There's a lot to be said about tweaking performance here.
    # Specifically for sqlite there's experimenting with BEGIN/END transactions,
    # making records a generator instead of a list, and a million other things
    # a google search away :)
    
    # Each of these changes should have some sort of test and documentation
    # confirming they actually increase the performance of the system unless the gains
    # are exceptionally obvious.
    
    # though most likely performance would come up after migrating to a 
    # proper db server :)
    weather_fields = [f for f in fields(Weather) if f.name != 'id']

    field_count = len(weather_fields)
    field_names = [f.name for f in weather_fields]
    # slice off the id primary key field
    field_values = [astuple(record)[1:] for record in records]
    cursor.executemany(
        f"INSERT INTO {TABLE_NAME} ({','.join(field_names)}) VALUES ({','.join(['?']*field_count)});",
        field_values
    )
