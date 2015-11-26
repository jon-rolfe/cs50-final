#
#   Given two cities, calculate the optimal place to meet in.
#   By: Jonathan Rolfe
#   For CS50 final project
#

import sys
import os
import requests
import base64
import json
import datetime
from dateutil.parser import parse

environment = 'https://api.test.sabre.com'
access_token = 0


def main(args):

    # parse args
    if not args or len(args) != 2:
        print 'Usage: ./%s from to' % sys.argv[0]
        quit()

    # translate names -> airports
    originA = suggest(args[0])
    originB = suggest(args[1])

    # double check origins
    print 'Origin A: %s\nOrigin B: %s' % (originA, originB)
    while(True):
        correct = raw_input('Is this correct? (Y/N)\n')
        if correct.lower() == 'y':
            print 'Great!'
            break
        elif correct.lower() == 'n':
            print 'OK, please tweak your input.'
            quit()
        else:
            print 'Invalid response.'

    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')

    # figure out arrival/return dates of trip
    '''
    print 'Please enter the date you would like to meet on.'
    while(True):
        departdate = parse(
            raw_input('Form: Month Day Year (e.g. "December 8 2015")\n'), fuzzy=True)
        if departdate < datetime.datetime.now() or departdate > (datetime.datetime.now() + datetime.timedelta(192)):
            print 'You must enter a date in the future that is no more than 192 days from now.'
        else:
            correct = raw_input('OK, so you want to meet on %s? (Y/N)\n' %
                                departdate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break
    os.system('cls' if os.name == 'nt' else 'clear')
    print 'Please enter the date you would like to return on.'
    while(True):
        returndate = parse(
            raw_input('Form: Month Day Year (e.g. "December 10 2015")\n'), fuzzy=True)
        if returndate < datetime.datetime.now() or returndate > (datetime.datetime.now() + datetime.timedelta(192)) or returndate < departdate:
            print 'You must enter a date after your departure that is no more than 192 days from now.'
        else:
            correct = raw_input('OK, so you want to return on %s? (Y/N)\n' %
                                returndate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break
    '''
    departdate = parse('december 8 2015')
    returndate = parse('december 10 2015')
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    print 'Working on your trip between %s and %s, departing on %s and returning on %s.' % (originA, originB, departdate.strftime('%b %d, %Y'), returndate.strftime('%b %d, %Y'))
    calculatemidpoint(originA, originB, departdate, returndate)


def suggest(query):
    # get token, make request to API to suggest correct result
    gettoken()
    url = environment + '/v1/lists/utilities/geoservices/autocomplete'
    params = {
        'query': query,
        'category': 'AIR',
        'limit': '3'
    }
    header = {
        'Authorization': ('Bearer %s' % access_token),
    }
    r = requests.get(url, headers=header, params=params)

    # now actually act upon said data!
    data = r.json()['Response']['grouped']['category:AIR']['doclist']

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
    # open file, get client id/secret, strip newline chars
    global access_token
    apifile = open('./key')
    client_id = apifile.readline().strip()
    client_secret = apifile.readline().strip()
    apifile.close()

    # encode id and secret as per API spec:
    # https://developer.sabre.com/docs/read/rest_basics/authentication
    client_id = base64.b64encode(client_id)
    client_secret = base64.b64encode(client_secret)
    client_credentials = base64.b64encode(client_id + ':' + client_secret)

    url = environment + '/v2/auth/token'
    auth = {
        'Authorization': ('Basic %s' % client_credentials),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    payload = 'grant_type=client_credentials'

    r = requests.post(url, headers=auth, data=payload)
    data = r.json()
    # print json.dumps(data, indent = 4)
    access_token = data['access_token']


def calculatemidpoint(originA, originB, departdate, returndate):

    # first throw the query through the destinations engine
    print 'Querying the server about %s.' % originA
    resultsA = destinations(originA, departdate, returndate)
    fileA = open('./results.json', 'w')
    fileA.truncate()
    fileA.close()
    with open('./results.json', 'w') as outfile:
        json.dump(resultsA, outfile)


def destinations(query, departdate, returndate):
    # if there isn't already an access token generated, do so
    if access_token == 0:
        gettoken()

    # set up parameters and make query
    url = environment + '/v2/shop/flights/fares'
    params = {
        'origin': query,
        'departuredate': departdate.date(),
        'returndate': returndate.date(),
    }
    header = {
        'Authorization': ('Bearer %s' % access_token),
    }
    r = requests.get(url, headers=header, params=params)
    data = r.json()
    return data

if __name__ == "__main__":
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')
    # call main
    main(sys.argv[1:])
