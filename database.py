#!/usr/bin/env python

"""
Usage: project.py from to
Given two cities, calculate the optimal city to meet in.
"""

import json
import datetime
import sqlite3

DATABASE_NAME = 'data/flights.sqlite'
DB = sqlite3.connect(DATABASE_NAME)
CURSOR = DB.cursor()


def addtodb(data, origin):
    """Function that adds JSON data retrieved from SABRE to SQLite DB."""

    # for debugging purposes, erase + write data to file
    data_out = open('./results.json', 'w')
    data_out.truncate()
    data_out.close()
    with open('./results.json', 'w') as outfile:
        json.dump(data, outfile, indent=1)

    # The only real data variation we should have is whether there's a lowest
    # nonstop fare that's different from the lowest fare
    for fare in data:
        # For some reason, the API sometimes returns useless/skippable results
        try:
            aircodes = ''.join(fare['LowestFare']['AirlineCodes'])
        except:
            continue
        try:
            # This next line will trigger an error if there are no nonstops
            nonstopcodes = ''.join(fare['LowestNonStopFare']['AirlineCodes'])
            CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, lowestnonstopfare, lowestnonstopairlines,
                currencycode, departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin, fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes,
                  fare['Distance'], fare['LowestNonStopFare']['Fare'],
                  nonstopcodes, fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href']))
        except (TypeError, KeyError):
            CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, currencycode,
                departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin, fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes,
                  fare['Distance'], fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href']))

    # Finally, commit all that to the DB
    DB.commit()


def destroydatabase():
    """If something goes wrong, drop the DB and make a new one."""

    # Drop table, commit, make a new one.
    CURSOR.execute('''
        DROP TABLE flights
    ''')
    DB.commit()

    makedatabase()


def makedatabase():
    """Creates an SQLite DB if it doesn't already exist."""
    print 'Checking DB integrity...'
    errors = CURSOR.execute('PRAGMA quick_check')
    print errors

    # Create the table (if it doesn't already exist)
    CURSOR.execute('''
        CREATE TABLE if not exists flights(id INTEGER PRIMARY KEY, origin TEXT,
        destination TEXT, timefetched TEXT, fare REAL, airlinecode TEXT,
        distance INTEGER, lowestnonstopfare INTEGER, lowestnonstopairlines TEXT,
        currencycode TEXT, departuredate TEXT, returndate TEXT,
        pricepermile REAL, link TEXT)
    ''')
    DB.commit()


def closedatabase():
    """Quick and simple: Closes the DB."""
    DB.close()
