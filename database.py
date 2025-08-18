"""Functions related to interacting with the databse should be placed here"""

import sqlite3
import re

DB_PATH = "rounds.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

def create_table(table):
    """Create a table with the passed name if it doesn't exist"""

    #ensure only letters, nums & underscores are in table name eg no space for 'DROP TABLE'
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
        return "Invalid table name. Please ensure only letters, numbers and underscores are used"

    if "_rb" in table:
        return "Cannot have _rb in table name"

    if table in [table[0] for table in cur.execute("SELECT name FROM sqlite_master").fetchall()]:
        return f"Table {table} already exists"
    
    creation = f"CREATE TABLE {table}(street VARCHAR(255), postcode VARCHAR(10))"
    cur.execute(creation)
    return f"Table {table} created"
