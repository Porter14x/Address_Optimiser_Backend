from flask import Flask
app = Flask(__name__)

GEO_URL = "http://localhost:7070/search" #Nominatim
ROUTE_URL = "http://localhost:8002/optimized_route" #Valhalla



@app.route('/', methods=["POST"])
def hello():
    return "hello"

if __name__=='__main__': 
    app.run(debug=True, )