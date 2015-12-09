"""
API request logic for where2meet.
"""

import requests
import base64

ENVIRONMENT = 'https://api.test.sabre.com'
ACCESS_TOKEN = 0


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
    # TODO: Add non-200 response logic
    data = request.json()
    # print json.dumps(data, indent = 4)
    ACCESS_TOKEN = data['access_token']


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
    # TODO: Add non-200 response logic

    # now actually act upon said data!
    data = request.json()['Response']['grouped']['category:AIR']['doclist']

    if data['numFound'] == 0:
        return False

    return data['docs']


def destinations(query, departdate, returndate):
    """Function that actually calls the SABRE API to get all destinations."""
    from database import addtodb

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
    # TODO: Add non-200 response logic
    data = (request.json()).get('FareInfo')
    if data is None:
        return False

    addtodb(data, query)
    # TODO: return condition should be bool for success and false for failure
    return True


def fullsearch(query, departdate, returndate):
    """Function that calls the InstaSearch SABRE API to manually get destinations"""
    # TODO
    if ACCESS_TOKEN == 0:
        gettoken()

    url = ENVIRONMENT + '/v1/shop/flights'
    # destination =
    params = {
        'origin': query,
        # 'destination':,
        'departuredate': departdate.date(),
        'returndate': returndate.date(),
        'outboundflightstops': '3',
        'inboundflightstops': '3',
    }
    header = {
        'Authorization': ('Bearer %s' % ACCESS_TOKEN),
    }

    request = requests.get(url, headers=header, params=params)
    data = request.json()
    print data
