import requests

GEO_URL = "http://192.168.0.209:7070/search"

params = {
    "q": "Gibberish G81 4NP",
    "format": "json"
}

r = requests.get(GEO_URL, params).json()
print(f"lat: {r[0]['lat']}")
print(f"lon: {r[0]['lon']}")