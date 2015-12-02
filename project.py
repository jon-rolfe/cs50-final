#!/usr/bin/env python

"""
Usage: project.py from to
Given two cities, calculate the optimal city to meet in.
"""

import sys
import os
import requests
import base64
import json
import datetime
import sqlite3
from dateutil.parser import parse

ENVIRONMENT = 'https://api.test.sabre.com'
ACCESS_TOKEN = 0
DATABASE_NAME = 'data/flights.sqlite'
DB = sqlite3.connect(DATABASE_NAME)
CURSOR = DB.cursor()


def main(args):
    """Handles user input and passes it to relevant functions."""

    # parse args
    if not args or len(args) != 2:
        print 'Usage: %s from to' % sys.argv[0]
        quit()

    # translate names -> airports
    origin_a = suggest(args[0])
    origin_b = suggest(args[1])

    # double check origins
    print 'Origin A: %s\nOrigin B: %s' % (origin_a, origin_b)
    while True:
        correct = raw_input('Is this correct? (Y/N)\n')
        if correct.lower() == 'y' or '\n':
            print 'Great!'
            break
        elif correct.lower() == 'n':
            print 'OK, please tweak your input.'
            quit()
        else:
            print 'Invalid response.'

    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    '''
    # figure out arrival/return dates of trip
    print 'Please enter the date you would like to meet on.'
    while True:
        departdate = parse(
            raw_input('Form: Month Day Year (e.g. "December 8 2015")\n'), fuzzy=True)
        if (departdate < datetime.datetime.now() or
                departdate > (datetime.datetime.now() + datetime.timedelta(192))):
            print 'You must enter a date in the future', \
                  'that is no more than 192 days from now.'
        else:
            correct = raw_input('OK, so you want to meet on %s? (Y/N)\n' %
                                departdate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break
    os.system('cls' if os.name == 'nt' else 'clear')
    print 'Please enter the date you would like to return on.'
    while True:
        returndate = parse(
            raw_input('Form: Month Day Year (e.g. "December 10 2015")\n'), fuzzy=True)
        if (returndate < datetime.datetime.now() or
                returndate > (datetime.datetime.now() + datetime.timedelta(192)) or
                returndate < departdate):
            print 'You must enter a date after your departure', \
                  'that is no more than 192 days from now.'
        else:
            correct = raw_input('OK, so you want to return on %s? (Y/N)\n' %
                                returndate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break
    '''
    # Debug defaults
    departdate = parse('december 8 2015')
    returndate = parse('december 10 2015')
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    print ('Working on your trip between %s and %s, departing on %s and returning on %s.' % (
        origin_a, origin_b, departdate.strftime('%b %d, %Y'), returndate.strftime('%b %d, %Y')))
    calculatemidpoint(origin_a, origin_b, departdate, returndate)


def suggest(query):
    """Given a string, resolve it to possible (valid) airports."""
    # get token, make request to API to suggest correct result
    gettoken()
    url = ENVIRONMENT + '/v1/lists/utilities/geoservices/autocomplete'
    params = {
        'query': query,
        'category': 'AIR',
        'limit': '3'
    }
    header = {
        'Authorization': ('Bearer %s' % ACCESS_TOKEN),
    }
    request = requests.get(url, headers=header, params=params)

    # now actually act upon said data!
    data = request.json()['Response']['grouped']['category:AIR']['doclist']

    if data['numFound'] == 0:
        print 'No results found.'
        return False
    else:
        print '%d results found.' % data['numFound']

    for entry in data['docs']:
        print 'Did you mean %s (id: %s)?' % (entry['name'], entry['id'])

    print 'Assuming %s meant %s (id: %s).' % (query, data['docs'][0]['name'], data['docs'][0]['id'])
    result = data['docs'][0]['id']
    return result


def gettoken():
    """Gets an OAUTH2 client token for all further API requests."""
    # open file, get client id/secret, strip newline chars
    global ACCESS_TOKEN
    apifile = open('./key')
    client_id = apifile.readline().strip()
    client_secret = apifile.readline().strip()
    apifile.close()

    # encode id and secret as per API spec:
    # https://developer.sabre.com/docs/read/rest_basics/authentication
    client_id = base64.b64encode(client_id)
    client_secret = base64.b64encode(client_secret)
    client_credentials = base64.b64encode(client_id + ':' + client_secret)

    url = ENVIRONMENT + '/v2/auth/token'
    auth = {
        'Authorization': ('Basic %s' % client_credentials),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    payload = 'grant_type=client_credentials'

    request = requests.post(url, headers=auth, data=payload)
    data = request.json()
    # print json.dumps(data, indent = 4)
    ACCESS_TOKEN = data['access_token']


def calculatemidpoint(origin_a, origin_b, departdate, returndate):
    """Attempts to calculate the best midpoint through which both parties could pass."""
    # DEBUG: Destroy DB every run. (This fn makes a new one, but this
    # statement won't be here for long and it doesn't hurt to run makedb
    # again.)
    makedatabase()
    destroydatabase()

    # make a DB, if it doesn't already exist

    # now: throw the query through the destinations engine
    print 'Querying the server about %s.' % origin_a
    results_a = destinations(origin_a, departdate, returndate)

    # repeat query for 2nd origin
    print 'Querying the server about %s.' % origin_b
    results_b = destinations(origin_b, departdate, returndate)

    # Should be the end of access to DB, so close it
    closedatabase()


def destinations(query, departdate, returndate):
    """Function that actually calls the SABRE API to get all destinations."""
    # if there isn't already an access token generated, do so
    if ACCESS_TOKEN == 0:
        gettoken()

    # set up parameters and make query
    url = ENVIRONMENT + '/v2/shop/flights/fares'
    params = {
        'origin': query,
        'departuredate': departdate.date(),
        'returndate': returndate.date(),
    }
    header = {
        'Authorization': ('Bearer %s' % ACCESS_TOKEN),
    }
    request = requests.get(url, headers=header, params=params)
    data = request.json()
    print type(data)
    addtodb(data, query)
    # TODO: return condition should be bool for success and false for failure
    return True


def addtodb(data, origin):
    """Function that adds JSON data retrieved from SABRE to SQLite DB."""
    print type(data)
    # for debugging purposes, erase + write data to file
    data_out = open('./results.json', 'w')
    data_out.truncate()
    data_out.close()
    with open('./results.json', 'w') as outfile:
        json.dump(data, outfile)

    # The only real data variation we should have is whether there's a lowest
    # nonstop fare that's different from the lowest fare
    for fare in data:
        try:
            # This next line is just to check existance w/o touching the DB
            fare['LowestNonStopFare']['Fare']
            CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, lowestnonstopfare, lowestnonstopairlines,
                currencycode, departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', origin, fare['DestinationLocation'], datetime.datetime.now(),
                           fare['LowestFare']['Fare'], fare[
                               'LowestFare']['AirlineCodes'],
                           fare['Distance'], fare['LowestNonStopFare']['Fare'],
                           fare['LowestNonstopFare'][
                               'AirlineCodes'], fare['CurrencyCode'],
                           fare['DepartureDateTime'], fare['ReturnDateTime'],
                           fare['PricePerMile'], fare['Links']['href'])
        except IndexError:
            CURSOR.execute('''
                INSERT INTO flights (origin, destination, timefetched, fare,
                airlinecode, distance, lowestnonstopfare, currencycode,
                departuredate, returndate, pricepermile, link)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', origin, fare['DestinationLocation'], datetime.datetime.now(),
                           fare['LowestFare']['Fare'], fare[
                               'LowestFare']['AirlineCodes'],
                           fare['Distance'], fare[
                               'LowestNonStopFare'], fare['CurrencyCode'],
                           fare['DepartureDateTime'], fare['ReturnDateTime'],
                           fare['PricePerMile'], fare['Links']['href'])

    # Finally, commit all that to the DB
    DB.commit()

'''


SAMPLE DB FORMAT:
{
  "LowestFare": {
    "Fare": 1955,
    "AirlineCodes": ["TN", "VT", "DL"]
  },
  "Distance": 5612,
  "LowestNonStopFare": "N/A",
  "Links": [{
    "href": "https://api.test.sabre.com/v1/shop/flights?origin=ATL&destination=BOB&departuredate=2015-12-08&returndate=2015-12-10&pointofsalecountry=US",
    "rel": "shop"
  }],
  "CurrencyCode": "USD",
  "DestinationLocation": "BOB",
  "DepartureDateTime": "2015-12-08T00:00:00",
  "ReturnDateTime": "2015-12-10T00:00:00",
  "PricePerMile": 0.35
}
'''


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

if __name__ == "__main__":
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    # call main
    main(sys.argv[1:])
