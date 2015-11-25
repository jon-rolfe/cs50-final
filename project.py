# 
#   Given two cities, calculate the optimal destination.
#   By: Jonathan Rolfe
#   For CS50 final project
#

import sys, requests, base64, json
environment = 'https://api.test.sabre.com'
access_token = 0

def main(args):
    
    # parse args
    if not args or len(args) != 2:
        print 'Usage: ./%s from to' % sys.argv[0]
        quit()
    
    # translate names -> airports
    origin = suggest(args[0])
    destination = suggest(args[1])
    
    print 'Origin: %s\nDestination: %s' % (origin, destination)
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
    
    print 'broken out!'

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
    r = requests.get(url, headers = header, params = params)
    
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
    
    r = requests.post(url, headers = auth, data = payload)
    data = r.json()
    # print json.dumps(data, indent = 4)
    access_token = data['access_token']
    
if __name__ == "__main__":
   main(sys.argv[1:])