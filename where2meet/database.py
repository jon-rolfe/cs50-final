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
    # Check DB integrity
    FLIGHT_CURSOR.execute('PRAGMA quick_check')
    AIRPORTS_CURSOR.execute('PRAGMA quick_check')
    if FLIGHT_CURSOR.fetchone()[0] != 'ok':
        print 'Due to a problem, the database must be rebuilt.'
        destroydatabase()
    elif AIRPORTS_CURSOR.fetchone()[0] != 'ok':
        print 'There is an issue with the airports database.\n' \
              'Please remove and re-download this program.'
        closeandquit()

    # Create the master flights table (if it doesn't already exist)
    FLIGHT_CURSOR.execute('''
        CREATE TABLE if not exists `flights` (
            `id` INTEGER PRIMARY KEY,
            `origin` TEXT,
            `destination` TEXT,
            `timefetched` TEXT,
            `fare` REAL,
            `airlinecode` TEXT,
            `departuredate` TEXT,
            `returndate` TEXT
        )
    ''')

    # Now create the pricing/logic table
    FLIGHT_CURSOR.execute('''
        CREATE TABLE if not exists `pricing` (
            `id` INTEGER PRIMARY KEY,
            `origin_a` TEXT,
            `origin_b` TEXT,
            `a_price` REAL,
            `b_price` REAL,
            `a_code` TEXT,
            `b_code` TEXT,
            `destination` TEXT,
            `totalprice` REAL,
            `inequality` REAL,
            UNIQUE (`origin_a`,`origin_b`,`destination`) ON CONFLICT IGNORE
        )
    ''')

    FLIGHT_DB.commit()


def destroydatabase():
    """Drops the DB tables and makes new ones."""

    # Drop tables, commit, make a new one.
    FLIGHT_CURSOR.execute('''
        DROP TABLE IF EXISTS flights
    ''')
    FLIGHT_CURSOR.execute('''
        DROP TABLE IF EXISTS pricing
    ''')
    FLIGHT_DB.commit()

    initdatabase()


def addindividualfare(data):
    """Function that adds the individually-fetched fare data to the DB."""
    # for fare in data:
    origin = data['AirItinerary']['OriginDestinationOptions']['OriginDestinationOption'][
        0]['FlightSegment'][0]['DepartureAirport']['LocationCode'].encode('ascii', 'ignore')
    destination = data['AirItinerary']['OriginDestinationOptions'][
        'OriginDestinationOption'][0]['FlightSegment'][-1]['ArrivalAirport']['LocationCode'].encode('ascii', 'ignore')
    aircode = data['TPA_Extensions']['ValidatingCarrier'][
        'Code'].encode('ascii', 'ignore')
    fare = data['AirItineraryPricingInfo']['PTC_FareBreakdowns'][
        'PTC_FareBreakdown']['PassengerFare']['TotalFare']['Amount']
    departdate = data['AirItinerary']['OriginDestinationOptions']['OriginDestinationOption'][
        0]['FlightSegment'][0]['DepartureDateTime']
    returndate = data['AirItinerary']['OriginDestinationOptions'][
        'OriginDestinationOption'][-1]['FlightSegment'][-1]['ArrivalDateTime']

    FLIGHT_CURSOR.execute('''
        INSERT INTO flights (origin, destination, timefetched, fare,
        airlinecode, departuredate, returndate)
        VALUES(?, ?, ?, ?, ?, ?, ?)
    ''', (origin, destination, datetime.datetime.now(), fare, aircode,
          departdate, returndate))

    FLIGHT_DB.commit()


def adddestination(data, origin):
    """Function that puts data retrieved from the Destinations API into the DB."""
    # The only real data variation we should have is whether there's a lowest
    # nonstop fare that's different from the lowest fare
    for fare in data:
        # For some reason, the Destinations API sometimes returns
        # useless/skippable results
        try:
            aircode = ''.join(fare['LowestFare']['AirlineCodes'][0])
        except:
            continue

        FLIGHT_CURSOR.execute('''
            INSERT INTO flights (origin, destination, timefetched, fare,
            airlinecode, departuredate, returndate)
            VALUES(?, ?, ?, ?, ?, ?, ?)
        ''', (origin.encode('iso-8859-1', 'replace'), fare['DestinationLocation'],
              datetime.datetime.now(), fare['LowestFare']['Fare'],
              aircode.encode('ascii', 'ignore'), fare['DepartureDateTime'], fare['ReturnDateTime']))

    # Finally, commit all that to the DB
    FLIGHT_DB.commit()


def addpricing(origin_a, origin_b, departdate, returndate):
    """Function that combines flights data and puts it in the 'pricing' DB."""
    # Grab all data and put it into a python object
    FLIGHT_CURSOR.execute("""
            SELECT destination FROM flights
        """)
    data = FLIGHT_CURSOR.fetchall()

    # Add all pair rows into pricing DB.
    for row in data:
        # First, check to make sure that there are "pairs" of results
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_a, row[0]))
        check_A = FLIGHT_CURSOR.fetchone()[0]
        FLIGHT_CURSOR.execute("""
            SELECT SUM(fare)
            FROM flights
            WHERE origin = ? AND destination = ?
        """, (origin_b, row[0]))
        check_B = FLIGHT_CURSOR.fetchone()[0]

        # if there's no matching pair, just go on to the next one - it's
        # effectively useless
        if check_A is None or check_B is None:
            continue
        # otherwise, get more info about the paired flights from the DB
        else:
            FLIGHT_CURSOR.execute("""
                SELECT *
                FROM flights
                WHERE origin = ? AND destination = ?
            """, (origin_a, row[0]))
            detailedrow = FLIGHT_CURSOR.fetchone()
            a_fare = detailedrow[4]
            a_aircode = detailedrow[5]

            FLIGHT_CURSOR.execute("""
                SELECT *
                FROM flights
                WHERE origin = ? AND destination = ?
            """, (origin_b, row[0]))
            detailedrow = FLIGHT_CURSOR.fetchone()
            b_fare = detailedrow[4]
            b_aircode = detailedrow[5]

        inequality = round((a_fare - b_fare), 2)
        inequality = abs(inequality)

        FLIGHT_CURSOR.execute("""
            INSERT INTO pricing(origin_a, origin_b, a_price, b_price, a_code,
            b_code, destination, totalprice, inequality)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (origin_a, origin_b, a_fare, b_fare, a_aircode, b_aircode,
              row[0], round((a_fare + b_fare), 2), inequality))

    # Now, actually commit it to the DB
    FLIGHT_DB.commit()


def movecursor(flag):
    if flag == 'pricing':
        FLIGHT_CURSOR.execute("""
                SELECT * FROM pricing ORDER BY(inequality * 2 + totalprice)
            """)
    if flag == 'airports':
        AIRPORTS_CURSOR.execute("""
            SELECT iata_code FROM airports
            WHERE type = 'large_airport' AND continent = 'NA'
            ORDER BY iata_code
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
        WHERE type='large_airport' AND continent='NA')
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
        """, (data[7],))

        name = AIRPORTS_CURSOR.fetchone()
        print 'Destination #%d:' % i
        print '\tName:', name[3].encode('iso-8859-1', 'replace')
        if 'US' not in name[8]:
            print '\tCountry:', name[8]
        print '\tAirport ID:', data[2]
        print '\t\t$%d from %s (Airline: %s)' % (data[3], data[1], data[5])
        print '\t\t$%d from %s (Airline: %s)' % (data[4], data[2], data[6])
        print '\tTotal Itinerary Price: $%d' % data[8]
        print '\tInequality of Fares: $%d' % data[9]
        print ''
        i = i + 1

    return True


def closeandquit(*_):
    """Quick and simple: Closes the DBs and quits. Discards all arguments."""
    FLIGHT_DB.close()
    AIRPORTS_DB.close()
    print ''
    sys.exit(0)
