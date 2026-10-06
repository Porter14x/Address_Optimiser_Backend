"""Functions related to interacting with the Nominatim engine should be placed here"""

import requests
import re

GEO_URL = "http://localhost:7070/search" #Nominatim
POSTCODE_RE = "([Gg][1-9]\d?|[Pp][Aa]\d{1,2}|[Mm][Ll]\d{1,2})\s*\d[A-Za-z]{2}" # G, PA and ML postcodes

def geocode_adds(addresses):
    """
    Takes a list of dict in the format [ {"q": "<ADDRESS>", "format": "json"} ]
    and returns a list of dict in the format [ {lat: float, lon: float} ]
    if there is an issue with geocoding return the index of the address causing issue
    tuple 0 spot is True/False depending on if geocoding is successful
    """

    geos = []
    for add in addresses:
        r = requests.get(GEO_URL, add).json()
        if not r:
            x = re.search(POSTCODE_RE, add["q"])
            #print(x.span)
            r = requests.get(GEO_URL, {"q": x.group(), "format": "json"}).json()
            if not r:
                return (False, add["q"])
        #print(r)
        geos.append({"lat": r[0]["lat"], "lon": r[0]["lon"]})
    return (True, geos)
