"""Main.py is responsible for handling requests via Flask 
and calling functions from other modules to satisfy the requests"""

from flask import Flask, request
import nominatim
import valhalla
app = Flask(__name__)

@app.route('/optimise', methods=["POST"])
def optimise_addreses():
    """Process the the requests addresses and return JSON of the addresses in optimised order"""
    request_data = request.get_json()
    addresses = request_data['addresses']
    geos = nominatim.geocode_adds(addresses)
    opt_adds = valhalla.optimise_adds(geos)
    return opt_adds

if __name__=='__main__': 
    app.run(debug=True, host='0.0.0.0', port=5000)