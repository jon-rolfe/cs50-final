# cs50-final
My final project for cs50. A nice little tool to calculate what city two people
should meet in using air travel.


Welcome to the wonderful world of where2meet's documentation!
(For program design info, check out design.txt)

=== INSTALLATION ===

where2meet is written in Python 2.7; as such, you need to have Python 2.7
downloaded and installed.  Python can be downloaded at:
https://www.python.org/downloads/
(Click "Download Python 2.7.11")

If you do not have the latest version of Python installed, where2meet will
probably break in fun and interesting ways.

Once you have Python installed, where2meet relies on an excellently designed
HTTP-magic module called "Requests."  Installation instructions can be found
here:
http://docs.python-requests.org/en/latest/user/install/#install
(Python 2.7.11 comes with "pip", a python package manager.)

Once you've done this, you'll need a free SABRE developer account. SABRE is
the flight fare data provider used in where2meet, and without it... well,
the program won't be able to do much!

To get a key, go to:
https://developer.sabre.com/member/register

The username and application name can be whatever you want; I recommend making
it "where2meet," but I'm something of a biased source.

Once you've registered and confirmed your email, log in and mosey on over to
"my account," where you should see something like:
Flights API Key: V1:abcd1234abcd1234:DEVCENTER:EXT

Make a new text file under the /where2meet/ subdirectory called "key". Then,
put the key on the first line and the shared secret on the second. It should
end up looking like this:
V1:abcd1234abcd1234:DEVCENTER:EXT
aBcD234f

Then you should be good!

=== USAGE ===

Open up terminal (or command prompt) and navigate to the directory this
file (documentation.txt) is in.

Type:
> python where2meet.py --help
to be presented with valid command line arguments.

In general, the program will try to hold your hand if you don't specify
all the information required to calculate the best place to meet.
That said, there are two required arguments: "origin A", and "origin B."

For example, if I was trying to calculate a good meeting point for a person
in New York City and one in Atlanta, I would put:
> python where2meet.py "New York City" Atlanta
(The order of the arguments is not important.)

Given no other arguments, the program will then attempt to resolve your
specified origins into valid airport codes and check with you before
continuing.
Finally, it will ask you for a valid departure and return date.

And then the ~magic~ will happen!  Unless you specified the '-f' switch,
it will take about a minute to fetch results from the server.

=== RESULTS ===

Assuming midpoints could be found, you'll be presented with something
like this:
--
Destination #2:
        Name: Chicago O'Hare International Airport
        Airport ID: ORD
                $106 from LGA (Airline: NK)
                $78 from ATL (Airline: F9)
        Total Itinerary Price: $184
        Inequality of Fares: $28
--

There will be up to 3 destinations listed at a time.  Each destination
has the name and ID of the midpoint airport (here, Chicago O'Hare and ORD
respectively), followed by details on fares for both parties and the
codes of their airlines.  When not obvious (e.g., "F9"), airline codes can
be decoded into airline names here:
http://www.iata.org/publications/Pages/code-search.aspx
("F9" maps to "Frontier Airlines" and "NK" maps to "Spirit Airlines")

Finally, the total itinerary price and the difference in the two fares
is listed.  Hopefully this will allow you to make an informed and fair
decision as to where you and your friend/colleague/associate/random person
you met on the internet should meet!

=== THE BIG KNOWN ISSUE ===

where2meet was designed around the wonderfully complex, detailed, and well-
documented SABRE API.  Developer keys can be obtained for free.  After
extensive research, I found the SABRE development API to be pretty much
the only free, open, well-designed flight fare API. Emphasis on free.
I contacted some closed fare API providers, but none of them ever got
back to me.  I have also contacted SABRE to try to get a production key,
but I have not received a response yet.

What this means for you, dear user, is that the data received by where2meet is
incomplete.  It's not bad data, and it's not a misrepresentation of real data--
it's just that the development API has a limited dataset (because if you
could get the entire dataset without paying, why would anyone pay?).  As a
result, there are combinations of cities that *clearly* have midpoints that
where2meet will return as having no midpoints.  Generally speaking, all data
for major airports about trips that are relatively soon is good.  But if you're
looking for a midpoint between, say, Washington D.C. and Fargo, North Dakota,
SABRE's development API (and thus where2meet) will not return any results.

Hopefully SABRE will give me a free production key, making this entire section
moot.  But until then... this is the biggest caveat of using where2meet in
the real world.

=== THANKS WHERE DUE ===

Complete credit for the airports DB should be given to OurAirports.com, who do a
great job compiling airport information (and release it into the public
domain!).
And complete credit for the flight data itself goes to SABRE, who graciously
allow developers free (if somewhat limited) access
