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
import argparse
import signal
from database import *
from apirequests import *
from dateutil.parser import parse


def main():
    """Handles user input and passes it to relevant functions."""
    cli_parse = argparse.ArgumentParser(
        description='Calculates optimal city to meet in.')

    cli_parse.add_argument('first_origin', action='store',
                           help='one of the two origin cities')
    cli_parse.add_argument('second_origin', action='store',
                           help='the other origin city')
    cli_parse.add_argument('--no-autocorrect', action='store_true', dest='skip', default=False,
                           help='skips autocorrection of origins; validates input against local DB')
    cli_parse.add_argument('-d', '--departure', action='store',
                           required=False, dest='departdate', help='specify the departure date')
    cli_parse.add_argument('-r', '--return', action='store',
                           required=False, dest='returndate', help='specify the return date')

    args = cli_parse.parse_args()

    # somewhat confusingly, this parse() is the datetime parse (not
    # argparse)
    if args.departdate is not None or args.returndate is not None:
        departdate = parse(args.departdate, fuzzy=True)
        returndate = parse(args.returndate, fuzzy=True)
        print departdate, returndate

    # clear terminal
    # os.system('cls' if os.name == 'nt' else 'clear')

    if args.skip is True:
        if validate(args.first_origin.upper()) == False or validate(args.second_origin.upper()) == False:
            error('Invalid origin or destination code specified.')
        else:
            origin_a = args.first_origin.upper()
            origin_b = args.second_origin.upper()
    else:
        # translate names -> airports
        origin_a = suggest(args.first_origin)
        origin_b = suggest(args.second_origin)

        if origin_a == False or origin_b == False:
            error('Invalid origin or destination specified.')

        print 'Assuming %s meant %s (id: %s).' % (args.first_origin, origin_a[0]['name'], origin_a[0]['id'])
        print 'Assuming %s meant %s (id: %s).' % (args.second_origin, origin_b[0]['name'], origin_b[0]['id'])

        # here on out, all we need is the ID portion
        origin_a = origin_a[0]['id']
        origin_b = origin_b[0]['id']

    # double check origins with user
    print 'Origin A: %s\nOrigin B: %s' % (origin_a, origin_b)
    while True:
        correct = raw_input('Is this correct? (Y/N)\n')
        if correct.lower() == 'n':
            error('Please tweak your input and re-run the program.')
        elif correct.lower() == 'y' or '\n':
            break
        else:
            print 'Invalid response.'

    # clear terminal
    # os.system('cls' if os.name == 'nt' else 'clear')

    # figure out arrival/return dates of trip if not specified in CL args
    print 'Please enter the date you would like to meet on.'
    while True:
        try:
            departdate = parse(raw_input(
                'Form: Month Day Year (e.g. "December 8 2015")\n'), fuzzy=True)
        except:
            print 'You must enter a valid date.'
            continue
        if (departdate < datetime.datetime.now() or
                departdate > (datetime.datetime.now() + datetime.timedelta(192))):
            print 'You must enter a date in the future', \
                  'that is no more than 192 days from now.'
        else:
            correct = raw_input('OK, so you want to meet on %s? (Y/N)\n' %
                                departdate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break
    # os.system('cls' if os.name == 'nt' else 'clear')
    print 'Please enter the date you would like to return on.'

    while True:
        try:
            returndate = parse(raw_input(
                'Form: Month Day Year (e.g. "December 10 2015")\n'), fuzzy=True)
        except:
            print 'You must enter a valid date.'
            continue
        if (returndate < datetime.datetime.now() or
                returndate > (datetime.datetime.now() + datetime.timedelta(192)) or
                returndate < departdate or (returndate - departdate) > datetime.timedelta(16)):
            print 'You must enter a date after your departure', \
                  'that is no more than\n192 days from now nor', \
                  'more than 16 days past your departure date.'
        else:
            correct = raw_input('OK, so you want to return on %s? (Y/N)\n' %
                                returndate.strftime('%A, %B %d, %Y'))
            if correct.lower() == 'y':
                break

    # Debug defaults
    departdate = parse('december 8 2015')
    returndate = parse('december 10 2015')
    # clear terminal
    # os.system('cls' if os.name == 'nt' else 'clear')
    print ('Working on your trip between %s and %s, departing on %s and returning on %s.' % (
        origin_a, origin_b, departdate.strftime('%b %d, %Y'), returndate.strftime('%b %d, %Y')))
    calculatemidpoint(origin_a, origin_b, departdate, returndate)

    print 'Top suggested destinations:'
    movecursor()
    threefares = nextthree()
    if threefares == False:
        error('We were unable to find any midpoints for your specified airports.')

    while True:
        more = raw_input(
            'Type "m" for more results. Type anything else to exit.\n')
        if more == 'm':
            # os.system('cls' if os.name == 'nt' else 'clear')
            if nextthree() == False:
                print 'No more results.'
                break
        else:
            break

    # Should be the end of access to DB, so close it
    closeandquit()


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

    if results_a or results_b == False:
        error('One or both of the origins do not have scheduled air service.')

    print 'Calculating most balanced midpoint...'
    fareslist = addpricing(origin_a, origin_b, departdate, returndate)


def error(errortext):
    print errortext
    closeandquit()

if __name__ == "__main__":
    # make a SIGINT handler for ctrl-c, etc
    signal.signal(signal.SIGINT, closeandquit)
    # call main
    main()
