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
        cur = self.con.cursor()
        """test create_table table creation and sanitation"""
        regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`",]

        rb_fail = "table_rb"
        self.assertEqual(d.create_table(rb_fail, cur), "Cannot have _rb in table name")

        for char in regex_fail_list:
            self.assertEqual(d.create_table("table"+char, cur),
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

        d.create_table("dummy", cur)
        self.assertEqual(d.create_table("dummy", cur), "Table dummy already exists")

        cur.close()

    def test_insert_table(self):
        """test insert_table value insertion and sanitation"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")

        d.create_table("dummy", cur)

        FORBIDDEN_CHAR = [";", '"',]
        for char in FORBIDDEN_CHAR:
            self.assertEqual(d.insert_table("dummy", "street", f"{char}postcode", cur),
                             f"Forbidden character {char} in input")
            self.assertEqual(d.insert_table("dummy", f"{char}street", "postcode", cur),
                             f"Forbidden character {char} in input")
            self.assertEqual(d.insert_table("dummy", f"{char}street", f"{char}postcode", cur),
                             f"Forbidden character {char} in input")
        
        output = d.insert_table("dummy", "1 House St", "A01", cur)
        self.assertEqual(output, "Inserted values (1 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]
        
        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_table("dummy", "2 House St", "A01", cur)
        self.assertEqual(output, "Inserted values (2 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT * FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT * FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_table("dummy", "3 House St", "A01", cur)
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

    def tearDown(self):
        """double check dummy table wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.close()
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
