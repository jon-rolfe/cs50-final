#!/usr/bin/env python

"""
Usage: ./where2meet.py from to
Given two cities, calculate the optimal city to meet in.
This file handles the core calculation logic and user input.
"""

import sys
import os
import requests
import base64
import json
from database import *
from apirequests import *
from dateutil.parser import parse


def main(args):
    """Handles user input and passes it to relevant functions."""

    # parse args
    if not args or len(args) != 2:
        print 'Usage: %s from to' % sys.argv[0]
        quit()
    elif args[0] == args[1]:
        print 'Must specify two unique destinations.'
        quit()

    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')

    # translate names -> airports
    origin_a = suggest(args[0])[0]
    print 'Assuming %s meant %s (id: %s).' % (args[0], origin_a['name'], origin_a['id'])

    origin_b = suggest(args[1])[0]
    print 'Assuming %s meant %s (id: %s).' % (args[1], origin_b['name'], origin_a['id'])

    # here on out, all we need is the ID portion
    origin_a = origin_a['id']
    origin_b = origin_b['id']

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
    # TODO: Refuse return dates > 16 days from depart date.
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

    print 'Top suggested destinations:'
    movecursor()
    threefares = nextthree()
    if threefares == False:
        print 'We were unable to find any midpoints for your specified airports. So sorry!'
        quit()

    while True:
        more = raw_input(
            'Type "m" for more results. Type anything else to exit.\n')
        if more == 'm':
            os.system('cls' if os.name == 'nt' else 'clear')
            if nextthree() == False:
                print 'No more results.'
                break
        else:
            break

    # Should be the end of access to DB, so close it
    closedatabase()


def calculatemidpoint(origin_a, origin_b, departdate, returndate):
    """Attempts to calculate the best midpoint through which both parties could pass."""
    # DEBUG: Destroy and remake DB every run.
    destroydatabase()

    # now: throw the query through the destinations engine
    print 'Querying the server about %s.' % origin_a
    results_a = destinations(origin_a, departdate, returndate)

    # repeat query for 2nd origin
    print 'Querying the server about %s.' % origin_b
    results_b = destinations(origin_b, departdate, returndate)

    print 'Calculating most balanced midpoint...'
    fareslist = addpricing(origin_a, origin_b, departdate, returndate)


if __name__ == "__main__":
    # call main
    main(sys.argv[1:])
