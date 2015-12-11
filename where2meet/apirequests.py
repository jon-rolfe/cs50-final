"""
API request logic for where2meet.
"""

import requests
import base64
# import json

ENVIRONMENT = 'https://api.test.sabre.com'
ACCESS_TOKEN = 0


def gettoken():
    """Gets an OAUTH2 client token for all further API requests."""
    # open file, get client id/secret, strip newline chars
    global ACCESS_TOKEN
    apifile = open('./where2meet/key')
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
    ACCESS_TOKEN = data['access_token']


def suggest(query):
    """Given a string, resolve it to possible (valid) airports."""
    # get token, make request to API to suggest correct result
    if ACCESS_TOKEN == 0:
        gettoken()
    # make spaces web safe
    query = query.replace(' ', '+')

    url = ENVIRONMENT + '/v1/lists/utilities/geoservices/autocomplete'
    params = {
        'query': query,
        'category': 'AIR',
        'limit': '1'
    }
    header = {
        'Authorization': ('Bearer %s' % ACCESS_TOKEN),
    }
    request = requests.get(url, headers=header, params=params)
    # now actually act upon said data!
    data = request.json()['Response']['grouped']['category:AIR']['doclist']

    if data['numFound'] == 0:
        return False

    return data['docs'][0]


def destinations(query, departdate, returndate):
    """Function that actually calls the SABRE API to get all destinations."""
    # delayed load to reduce occasional python import wonkiness
    from database import adddestination

    # if there isn't already an access token generated, do so
    if ACCESS_TOKEN == 0:
        gettoken()

    # set up parameters and make query
    url = ENVIRONMENT + '/v2/shop/flights/fares'
    params = {
        'origin': query,
        'departuredate': departdate.date(),
        'returndate': returndate.date(),
        'topdestinations': 50,
    }
    header = {
        'Authorization': ('Bearer %s' % ACCESS_TOKEN),
    }
    request = requests.get(url, headers=header, params=params)
    data = (request.json()).get('FareInfo')
    if data is None:
        return False

    adddestination(data, query)
    return True


def fullsearch(query, departdate, returndate):
    """Function that calls the InstaSearch SABRE API to manually get destinations"""
    # delayed loading plays better with python for whatever reason
    from database import numberofairports, nextairport, movecursor, addindividualfare
    if ACCESS_TOKEN == 0:
        gettoken()

    # get # of big airports in NA, move cursor to right pos in DB
    airportcount = numberofairports()
    movecursor('airports')
    querynum = 0

    # grab next airport to look up
    while querynum < airportcount:
        destination = nextairport()
        if destination == False:
            break
        url = ENVIRONMENT + '/v1/shop/flights'
        params = {
            'origin': query,
            'destination': destination,
            'departuredate': departdate.date(),
            'returndate': returndate.date(),
            'passengercount': '1',
            'limit': '1',
        }
        header = {
            'Authorization': ('Bearer %s' % ACCESS_TOKEN),
        }
        request = requests.get(url, headers=header, params=params)
        data = (request.json()).get('PricedItineraries')

        # if there are results, add them to the DB
        if request.status_code == 200:
            addindividualfare(data[0])

        querynum = querynum + 1
