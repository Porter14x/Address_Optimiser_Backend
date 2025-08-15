import requests

GEO_URL = "http://localhost:7070/search" #Nominatim

def geocode_adds(addresses):
    """
    Takes a list of dict in the format [ {"q": "<ADDRESS>", "format": "json"} ]
    and returns a list of dict in the format [ {lat: <GEOCODE_1>, lon: <GEOCODE_2>} ]
    """

    geos = []
    for add in addresses:
        r = requests.get(GEO_URL, add).json()[0]
        geos.append({"lat": r["lat"], "lon": r["lon"]})
        #Assume starting address is also ending address
        geos.append(geos[0])
    return geos