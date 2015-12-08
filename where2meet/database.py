#!/usr/bin/env python

"""
Database logic for where2meet.
"""

import json
import datetime
import sqlite3

FLIGHTS_DB_NAME = '../data/flights.sqlite'
FLIGHT_DB = sqlite3.connect(FLIGHTS_DB_NAME)
FLIGHT_CURSOR = FLIGHT_DB.cursor()
AIRPORTS_DB_NAME = '../data/airports.sqlite'
AIRPORTS_DB = sqlite3.connect(AIRPORTS_DB_NAME)
AIRPORTS_CURSOR = AIRPORTS_DB.cursor()


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
            FLIGHT_CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, lowestnonstopfare, lowestnonstopairlines,
                currencycode, departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin.encode('ascii', 'ignore'), fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes.encode(
                      'ascii', 'ignore'),
                  fare['Distance'], fare['LowestNonStopFare']['Fare'],
                  nonstopcodes.encode('ascii', 'ignore'), fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href'].encode('ascii', 'ignore')))
        except (TypeError, KeyError):
            FLIGHT_CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, currencycode,
                departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin.encode('ascii', 'ignore'), fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes.encode(
                      'ascii', 'ignore'),
                  fare['Distance'], fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href'].encode('ascii', 'ignore')))

    # Finally, commit all that to the DB
    FLIGHT_DB.commit()


def destroydatabase():
    """If something goes wrong, drop the DB and make a new one."""

    # Drop table, commit, make a new one.
    FLIGHT_CURSOR.execute('''
        DROP TABLE flights
    ''')
    FLIGHT_DB.commit()

    makedatabase()


def makedatabase():
    """Creates an SQLite DB if it doesn't already exist."""
    print 'Checking DB integrity...'
    FLIGHT_CURSOR.execute('PRAGMA quick_check')
    print 'Status: %s' % FLIGHT_CURSOR.fetchall()[0]

    # Create the master flights table (if it doesn't already exist)
    FLIGHT_CURSOR.execute('''
        CREATE TABLE if not exists `flights` (
            `id` INTEGER PRIMARY KEY,
            `origin` TEXT,
            `destination` TEXT,
            `timefetched` TEXT,
            `fare` REAL,
            `airlinecode` TEXT,
            `distance` INTEGER,
            `lowestnonstopfare` INTEGER,
            `lowestnonstopairlines` TEXT,
            `currencycode` TEXT, `departuredate` TEXT,
            `returndate` TEXT,
            `pricepermile` REAL,
            `link` TEXT
        )
    ''')

    # Now create the pricing/logic table
    FLIGHT_CURSOR.execute('''
        CREATE TABLE if not exists `pricing` (
            `id` INTEGER PRIMARY KEY,
            `origin_a` TEXT,
            `origin_b` TEXT,
            `destination` TEXT,
            `totalprice` REAL,
            `inequality` REAL
        )
    ''')

    FLIGHT_DB.commit()

# SELECT SUM(fare) FROM flights WHERE origin = 'ATL' AND destination =
# 'BOS'  OR origin = 'ATL' AND destination = 'EWR'


def balance(origin_a, origin_b, departdate, returndate):
    FLIGHT_CURSOR.execute("""
            SELECT destination FROM flights
        """)
    data = FLIGHT_CURSOR.fetchall()

    for row in data:
        # print 'Row: ' + row[0]
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_a, row[0].encode('ascii', 'ignore')))

        # Get the result that the cursor is at (i.e., the fare)
        fare_A = FLIGHT_CURSOR.fetchone()[0]

        #
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_b, row[0].encode('ascii', 'ignore')))
        fare_B = FLIGHT_CURSOR.fetchone()[0]

        # if there's no matching pair, just go on to the next one—it's useless
        if fare_A or fare_B = 'None'
            continue

        FLIGHT_CURSOR.execute("""
            INSERT INTO pricing (origin_a, origin_b, destination, totalprice,
            inequality)
            VALUES ()
        """)


def closedatabase():
    """Quick and simple: Closes the DB."""
    FLIGHT_DB.close()
    AIRPORTS_DB.close()
