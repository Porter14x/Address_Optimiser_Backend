"""Unit tests for whole project are placed here"""

import unittest
import sqlite3
import database as d

class TestDatabaseMethods(unittest.TestCase):
    """Class for testing the functions of database.py"""

    con = sqlite3.connect("test.db")

    def setUp(self):
        """ensure dummy table is wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.close()
        return super().setUp()

    def test_create_table(self):
        """test create_table table creation and sanitation"""
        cur = self.con.cursor()
        regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`",]

        rb_fail = "table_rb"
        self.assertEqual(d.create_table(rb_fail, cur, self.con), "Cannot have _rb in table name")

        for char in regex_fail_list:
            self.assertEqual(d.create_table("table"+char, cur, self.con),
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.create_table("dummy", cur, self.con), "Table dummy already exists")

        cur.close()

    def test_insert_value(self):
        """test insert_table value insertion and sanitation"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")

        d.create_table("dummy", cur, self.con)

        FORBIDDEN_CHAR = [";", '"',]
        for char in FORBIDDEN_CHAR:
            self.assertEqual(d.insert_value("dummy", "street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", "postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")

        output = d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (1 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (2 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (3 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01"),
                                            ("3 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        cur.close()
    
    def test_delete_value(self):
        """test delete_value value deletion and sanitation"""

        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")

        d.create_table("dummy", cur, self.con)
        FORBIDDEN_CHAR = [";", '"',]

        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)

        for char in FORBIDDEN_CHAR:
            self.assertEqual(d.delete_value("dummy", "street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.delete_value("dummy", f"{char}street", "postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.delete_value("dummy", f"{char}street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
        
        self.assertEqual(d.delete_value("dummy", "4 House St", "A01", cur, self.con),
                         "Street and postcode not found in database")
        
        output = d.delete_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (3 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01"),
                                               ("3 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.delete_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (2 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.delete_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (1 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        cur.close()

    def tearDown(self):
        """double check dummy table wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.close()
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
