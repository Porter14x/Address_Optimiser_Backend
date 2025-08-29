"""Main.py is responsible for handling requests via Flask 
and calling functions from other modules to satisfy the requests"""

import sqlite3
import atexit
from flask import Flask, request
import nominatim as n
import valhalla as v
import database as d
app = Flask(__name__)

DB_PATH = "rounds.db"

con = None

def get_con():
    """lazy instantiation of db connection"""
    global con
    if con is not None:
        return
    con = sqlite3.connect(DB_PATH)
    return con

def close_con():
    """Connection closer for atexit to call"""
    con.close()

atexit.register(close_con)

@app.route('/optimise', methods=["POST"])
def optimise_addresses(addresses=None):
    """Process the the requests addresses and return JSON of the addresses in optimised order"""
    if not addresses:
        request_data = request.get_json()
        addresses = request_data['addresses']
    geos = n.geocode_adds(addresses)
    opt_adds = v.optimise_adds(geos)
    return opt_adds

@app.route('/create_table', methods=["POST"])
def create_table():
    """Receive {"table": string} and see if a table in the db can be created
    return a success/fail msg"""
    get_con()
    cur = con.cursor()

    request_data = request.get_json()
    table = request_data['table']
    msg = d.create_table(table, cur, con)
    cur.close()
    return msg

@app.route('/delete_table', methods=["POST"])
def delete_table():
    """Receive {"table": string} and see if a table in the db can be deleted
    return a success/fail msg"""
    get_con()
    cur = con.cursor()

    request_data = request.get_json()
    table = request_data['table']
    msg = d.delete_table(table, cur, con)
    cur.close()
    return msg

@app.route('/insert_value', methods=["POST"])
def insert_value():
    """Receive {"table": string, "address": (street, postcode)} 
    and see if it can be inserted to db, return a success/fail msg"""
    get_con()
    cur = con.cursor()

    request_data = request.get_json()
    table = request_data['table']
    address = request_data['address'] #(street, postcode)
    d.rb_helper(table, cur)
    msg = d.insert_value(table, address[0], address[1], cur, con)

    if "Inserted values" not in msg:
        #something wrong with input return the error message so no work wasted
        cur.close()
        return msg

    select_table = d.select_all(table, cur)
    addresses = []
    for result in select_table:
        addresses.append({"q": f"{result[0]} {result[1]}", "format": "json"})

    opt_adds = optimise_addresses(addresses)
    new_add_order = []
    for add in opt_adds:
        #using select_table since already in (street, postcode) format
        new_add_order.append(select_table[add["original_index"]])

    d.table_optimisation_update(table, new_add_order, cur)
    con.commit()

    cur.close()
    return msg

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
