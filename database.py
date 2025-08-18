"""Functions related to interacting with the databse should be placed here"""

import sqlite3
import re
import atexit

DB_PATH = "rounds.db"
FORBIDDEN_CHAR = [";", '"',] # list of chars that should never appear in inputs

con = sqlite3.connect(DB_PATH)

def close_con():
    con.close()

atexit.register(close_con)

def create_table(table, cur):
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
    con.commit()
    return f"Table {table} created"

def insert_table(table, street, postcode, cur):
    """Insert street and postcode values into desired table"""

    all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]

    for char in FORBIDDEN_CHAR:
        if char in street or char in postcode:
            return f"Forbidden character {char} in input"

    rb = f"{table}_rb"
    sql_rb = f"CREATE TABLE {rb} AS SELECT * FROM {table}"

    if rb in all_table:
        sql_drop = f"DROP TABLE {rb}"
        cur.execute(sql_drop)
        cur.execute(sql_rb)
    else:
        cur.execute(sql_rb)
    
    sql_in = f"INSERT INTO {table} VALUES (?, ?)"
    cur.execute(sql_in, (street, postcode))
    con.commit()
    return f"Inserted values ({street}, {postcode}) into {table}"
