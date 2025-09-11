"""Functions related to interacting with the Valhalla Engine should be put inside this module"""

import requests

ROUTE_URL = "http://localhost:8002/optimized_route"

def optimise_adds(geocodes):
    """
    take a list of dict in the format [ {lat: <GEOCODE_1>, lon: <GEOCODE_2>} ]
    and returns a list of dict with the organised geocodes 
    [ {"lat": float , "lon": float , "original_index": int}, ...]
    """

    payload = {
    "locations": geocodes,
    "costing": "auto",
    "directions_options": {"units": "kilometers"}
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(ROUTE_URL, headers=headers, json=payload).json()

    return response['trip']['locations']
