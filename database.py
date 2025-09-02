"""Functions related to interacting with the databse should be placed here"""

import sqlite3
import re

def forbidden_char_check(street, postcode):
    """checks street and postcode vals for any established forbidden characters
    return a (False, char) tuple if one is detected, (True, None) otherwise"""
    FORBIDDEN_CHAR = [";", '"', "'",] # list of chars that should never appear in inputs

    for char in FORBIDDEN_CHAR:
        if char in street or char in postcode:
            return (False, f"Forbidden character {char} in input")

    return (True, None)

def rb_helper(table, cur):
    """creates/overwrites the rollback for the table being modified"""
    all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]

    rb = f"{table}_rb"
    sql_rb = f"CREATE TABLE {rb} AS SELECT * FROM {table}"

    if rb in all_table:
        sql_drop = f"DROP TABLE {rb}"
        cur.execute(sql_drop)
        cur.execute(sql_rb)
    else:
        cur.execute(sql_rb)

def table_verification(table):
    """verify inputted table is correctly formatted"""

    #ensure only letters, nums & underscores are in table name eg no space for 'DROP TABLE'
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
        return (False, "Invalid table name. Please ensure only letters, numbers and underscores are used")

    if "_rb" in table:
        return (False, "Cannot have _rb in table name")

    return (True, None)

def verify_insert(table, street, postcode, cur):
    """verify street and postcode isn't forbidden or duplicate"""

    valid = forbidden_char_check(street, postcode)
    if valid[0] is False:
        return valid

    sql_search = f"SELECT street, postcode FROM {table} WHERE street=? AND postcode=?;"
    result = [r[0] for r in cur.execute(sql_search, (street, postcode)).fetchall()]
    if len(result) > 0:
        return (False, "Street and postcode already in database")

    return (True, None)

def verify_delete(table, street, postcode, cur):
    """verify street and postcode isn't forbidden or missing"""

    valid = forbidden_char_check(street, postcode)
    if valid[0] is False:
        return valid

    sql_search = f"SELECT street, postcode FROM {table} WHERE street=? AND postcode=?;"
    result = [r[0] for r in cur.execute(sql_search, (street, postcode)).fetchall()]
    if result == []:
        return (False, "Street and postcode not found in database")

    return (True, None)

def create_table(table, cur, con):
    """Create a table with the passed name if it doesn't exist"""

    valid = table_verification(table)
    if valid[0] is False:
        return valid

    if table in [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]:
        return (False, f"Table {table} already exists")

    creation = f"CREATE TABLE {table}(id INTEGER PRIMARY KEY, street VARCHAR(255), postcode VARCHAR(10));"
    cur.execute(creation)
    con.commit()
    return (True, f"Table {table} created")

def insert_value(table, street, postcode, cur, con):
    """Insert street and postcode values into desired table, return status msg"""

    valid = verify_insert(table, street, postcode, cur)
    if valid[0] is False:
        return valid
    rb_helper(table, cur)

    sql_in = f"INSERT INTO {table} (street, postcode) VALUES (?, ?)"
    cur.execute(sql_in, (street, postcode))
    con.commit()
    return (True, f"Inserted values ({street}, {postcode}) into {table}")

def delete_value(table, street, postcode, cur, con):
    """delete street and postcode value from desired table"""

    valid = verify_delete(table, street, postcode, cur)
    if valid[0] is False:
        return valid
    rb_helper(table, cur)

    sql_del = f"DELETE FROM {table} WHERE street=? AND postcode=?;"
    cur.execute(sql_del, (street, postcode))
    con.commit()
    return (True, f"Deleted values ({street}, {postcode}) from {table}")

def delete_table(table, cur, con):
    """Fully delete a table and its rollback - irreversible"""

    valid = table_verification(table)
    if valid[0] is False:
        return valid

    if table not in [table[0] for table in cur.execute("SELECT name FROM sqlite_master").fetchall()]:
        return (False, f"Table {table} does not exist")

    sql_drop = f"DROP TABLE {table};"
    sql_drop_rb = f"DROP TABLE {table}_rb;"

    cur.execute(sql_drop)
    cur.execute(sql_drop_rb)
    con.commit()
    return (True, f"Table {table} and its rollback deleted")

def rollback_table(table, cur, con):
    """revert a table to its table_rb - original table is dropped"""

    valid = table_verification(table)
    if valid[0] is False:
        return valid[1]

    all_table = [table[0] for table in cur.execute("SELECT name FROM sqlite_master").fetchall()]

    if table not in all_table:
        return (False, f"Table {table} does not exist")
    if f"{table}_rb" not in all_table:
        return (False, f"No rollback for {table}")

    rb = f"{table}_rb"
    sql_rollback = f"""
    DROP TABLE {table};
    CREATE TABLE {table} AS SELECT * FROM {rb};
    DROP TABLE {rb};
    """
    cur.executescript(sql_rollback)
    con.commit()
    return (True, f"Table {table} has been rolled back")

def select_all(table, cur):
    """get all (street, postcode) used when re-optimising table after deletion/insertion"""
    sql_select = f"SELECT street, postcode FROM {table}"
    output = cur.execute(sql_select).fetchall()

    #output will look like [("1 House St", "A01"), ("2 House St", "A01"), ...]
    return output

def table_optimisation_update(table, new_add_order, cur):
    """Update the table to reflect the new optimisation order in new_add_order"""

    #make sure we have fresh table to insert into
    sql_setup = f"""
    DROP TABLE {table};
    CREATE TABLE {table}(id INTEGER PRIMARY KEY, street VARCHAR(255), postcode VARCHAR(10));
    """
    cur.executescript(sql_setup)

    for add in new_add_order:
        cur.execute(f"INSERT INTO {table} (street, postcode) VALUES (?, ?);", (add[0], add[1]))
