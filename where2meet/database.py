#!/usr/bin/env python

"""
Database logic for where2meet.
"""

import json
import datetime
import sqlite3
import sys

FLIGHTS_DB_NAME = '../data/flights.sqlite'
FLIGHT_DB = sqlite3.connect(FLIGHTS_DB_NAME)
FLIGHT_CURSOR = FLIGHT_DB.cursor()
AIRPORTS_DB_NAME = '../data/airports.sqlite'
AIRPORTS_DB = sqlite3.connect(AIRPORTS_DB_NAME)
AIRPORTS_CURSOR = AIRPORTS_DB.cursor()


def initdatabase():
    """Creates an SQLite DB if it doesn't already exist."""
    print 'Checking DB integrity...'
    FLIGHT_CURSOR.execute('PRAGMA quick_check')
    AIRPORTS_CURSOR.execute('PRAGMA quick_check')
    if FLIGHT_CURSOR.fetchone()[0] != 'ok':
        print 'Due to a problem, the database must be rebuilt.'
        destroydatabase()
    elif AIRPORTS_CURSOR.fetchone()[0] != 'ok':
        print 'There is an issue with the airports database.\n' \
              'Please remove and re-download this program.'

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
            `inequality` REAL,
            UNIQUE (`origin_a`,`origin_b`,`destination`) ON CONFLICT IGNORE
        )
    ''')

    FLIGHT_DB.commit()


def destroydatabase():
    """If something goes wrong, drop the flights DB and make a new one."""

    # Drop tables, commit, make a new one.
    FLIGHT_CURSOR.execute('''
        DROP TABLE IF EXISTS flights
    ''')
    FLIGHT_CURSOR.execute('''
        DROP TABLE IF EXISTS pricing
    ''')
    FLIGHT_DB.commit()

    initdatabase()


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
            ''', (origin.encode('iso-8859-1', 'replace'), fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes.encode(
                      'ascii', 'ignore'),
                  fare['Distance'], fare['LowestNonStopFare']['Fare'],
                  nonstopcodes.encode(
                      'iso-8859-1', 'replace'), fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href'].encode('iso-8859-1', 'replace')))
        except (TypeError, KeyError):
            FLIGHT_CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, currencycode,
                departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin.encode('iso-8859-1', 'replace'), fare['DestinationLocation'], datetime.datetime.now(),
                  fare['LowestFare']['Fare'], aircodes.encode(
                      'ascii', 'ignore'),
                  fare['Distance'], fare['CurrencyCode'],
                  fare['DepartureDateTime'], fare['ReturnDateTime'],
                  fare['PricePerMile'], fare['Links'][0]['href'].encode('iso-8859-1', 'replace')))

    # Finally, commit all that to the DB
    FLIGHT_DB.commit()


def addpricing(origin_a, origin_b, departdate, returndate):
    """Function that takes raw pricing data and gets useful pricing info."""
    # Grab all data and put it into a python object
    FLIGHT_CURSOR.execute("""
            SELECT destination FROM flights
        """)
    data = FLIGHT_CURSOR.fetchall()

    # Add all pair rows into pricing DB.
    for row in data:
        # Get the rows for origin A -> dest, put it into fare_A
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_a, row[0]))
        fare_A = FLIGHT_CURSOR.fetchone()[0]

        # Repeat for origin B -> dest
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_b, row[0]))
        fare_B = FLIGHT_CURSOR.fetchone()[0]

        # if there's no matching pair, just go on to the next one - it's
        # effectively useless
        if fare_A is None or fare_B is None:
            continue

        inequality = round((fare_A - fare_B), 2)
        inequality = abs(inequality)

        FLIGHT_CURSOR.execute("""
            INSERT INTO pricing (origin_a, origin_b, destination, totalprice,
            inequality)
            VALUES (?, ?, ?, ?, ?)
        """, (origin_a, origin_b, row[0], round((fare_A + fare_B), 2), inequality))

    # Now, actually commit it to the DB
    FLIGHT_DB.commit()


def movecursor(flag):
    if flag == 'pricing':
        FLIGHT_CURSOR.execute("""
                SELECT * FROM pricing ORDER BY (inequality*2 + totalprice)
            """)
    if flag == 'airports':
        AIRPORTS_CURSOR.execute("""
            SELECT iata_code FROM airports
            WHERE type = 'large_airport' AND continent = 'NA'
        """)


def validate(query):
    AIRPORTS_CURSOR.execute("""
        SELECT * FROM airports WHERE iata_code = ?
    """, [query])
    value = AIRPORTS_CURSOR.fetchone()

    # if there's no tables returned, invalid airport
    if value is None:
        return False
    else:
        return True


def numberofairports():
    AIRPORTS_CURSOR.execute("""
        SELECT COUNT(*) FROM
        (SELECT iata_code FROM airports
        WHERE type = 'large_airport' AND continent = 'NA')
    """)
    return AIRPORTS_CURSOR.fetchone()[0]


def nextairport():
    airport = ''
    # filter out blank results
    while airport is '':
        airport = AIRPORTS_CURSOR.fetchone()[0].encode('iso-8859-1', 'replace')
    if airport is None:
        return False
    return airport


def printthree():
    from apirequests import suggest
    """Function that fetches the next 3 best fares."""
    i = 1
    while i < 4:
        data = FLIGHT_CURSOR.fetchone()
        if data is None:
            return False
        # To reduce unneccesary API calls, grab the corresponding name from
        # airport DB. Also, data[3] = destination code
        AIRPORTS_CURSOR.execute("""
            SELECT * FROM airports WHERE iata_code = ?
        """, (data[3],))

        name = AIRPORTS_CURSOR.fetchone()

        print 'Destination #%d:' % i
        print '\tName:', name[3].encode('iso-8859-1', 'replace')
        if 'US' not in name[8]:
            print '\tCountry:', name[8]
        print '\tID:', data[3]
        print '\tTotal Itinerary Price: $%d' % data[4]
        print '\tInequality of Fares: $%d' % data[5]
        print ''
        i = i + 1

    return True


def closeandquit(*_):
    """Quick and simple: Closes the DBs and quits. Discards all arguments."""
    FLIGHT_DB.close()
    AIRPORTS_DB.close()
    print ''
    sys.exit(0)
