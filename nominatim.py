"""Functions related to interacting with the Nominatim engine should be placed here"""

import requests

GEO_URL = "http://localhost:7070/search" #Nominatim

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
            return (False, add)
        print(r)
        geos.append({"lat": r[0]["lat"], "lon": r[0]["lon"]})
    return (True, geos)
