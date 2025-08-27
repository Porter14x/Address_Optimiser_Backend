"""Unit tests for whole project are placed here"""

import unittest
import sqlite3
from unittest.mock import patch
import database as d
from main import app, DB_PATH

class MainTestCase(unittest.TestCase):
    """Class for testing functions of main.py"""

    con = sqlite3.connect("test.db")

    def setUp(self):
        # Create a test client
        self.app = app.test_client()
        self.app.testing = True

        #want database with vals to test the insertion/deletion + optimisation operations
        cur = self.con.cursor()
        d.create_table("dummy", cur, self.con)
        d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        cur.close()

    @patch("main.optimise_addresses")
    @patch("main.DB_PATH", "test.db")
    def test_insert_value_success(self, mock_opt):
        #lat and lon arent used so val doesnt matter
        mock_opt_json = [
            {"lat": 0, "lon": 0, "original_index": 2}, #1 House St
            {"lat": 0, "lon": 0, "original_index": 0}, #2 House St
            {"lat": 0, "lon": 0, "original_index": 1}, #3 House St
        ]
        mock_opt.return_value = mock_opt_json

        response = self.app.post("/insert_value", json={"table": "dummy", "address": ("1 House St", "A01")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Inserted values (1 House St, A01) into dummy")

        cur = self.con.cursor()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertTrue("dummy" in all_tables)
        self.assertTrue("dummy_rb" in all_tables)
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        self.assertListEqual(result_dummy_rb, [("2 House St", "A01"), ("3 House St", "A01")])
        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01"),
                                            ("3 House St", "A01")])

class DatabaseTestCase(unittest.TestCase):
    """Class for testing the functions of database.py"""

    con = sqlite3.connect("test.db")
    FORBIDDEN_CHAR = [";", '"', "'"]
    regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`",]

    def setUp(self):
        """ensure dummy table is wiped"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")
        cur.close()
        return super().setUp()
    
    def test_table_verification(self):
        rb_fail = "table_rb"
        self.assertEqual(d.table_verification(rb_fail)[1], "Cannot have _rb in table name")

        for char in self.regex_fail_list:
            self.assertEqual(d.table_verification("table"+char)[1],
            "Invalid table name. Please ensure only letters, numbers and underscores are used")
    
    def test_forbidden_char_check(self):
        for char in self.FORBIDDEN_CHAR:
            self.assertEqual(d.forbidden_char_check("street", f"{char}postcode")[1],
                             f"Forbidden character {char} in input")
            self.assertEqual(d.forbidden_char_check(f"{char}street", f"postcode")[1],
                             f"Forbidden character {char} in input")
            self.assertEqual(d.forbidden_char_check(f"{char}street", f"{char}postcode")[1],
                             f"Forbidden character {char} in input")

    def test_create_table(self):
        """test create_table table creation and sanitation"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.create_table("dummy", cur, self.con), "Table dummy already exists")

        self.assertTrue("dummy" in 
                        [r[0] for r in cur.execute("SELECT name FROM sqlite_master").fetchall()])

        cur.close()

    def test_insert_value(self):
        """test insert_table value insertion and sanitation"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        d.rb_helper("dummy", cur)

        for char in self.FORBIDDEN_CHAR:
            self.assertEqual(d.insert_value("dummy", "street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", "postcode",
                                            cur, self.con), f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", f"{char}postcode",
                                            cur, self.con), f"Forbidden character {char} in input")

        output = d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (1 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        d.rb_helper("dummy", cur)
        output = d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (2 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        d.rb_helper("dummy", cur)
        output = d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output, "Inserted values (3 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01"),
                                            ("3 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        self.assertEqual(d.insert_value("dummy", "3 House St", "A01", cur, self.con),
                         "Street and postcode already in database")

        cur.close()

    def test_delete_value(self):
        """test delete_value value deletion and sanitation"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)

        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)

        self.assertEqual(d.delete_value("dummy", "4 House St", "A01", cur, self.con),
                         "Street and postcode not found in database")

        d.rb_helper("dummy", cur)
        output = d.delete_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (3 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01"),
                                               ("3 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        d.rb_helper("dummy", cur)
        output = d.delete_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (2 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        d.rb_helper("dummy", cur)
        output = d.delete_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output, "Deleted values (1 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        cur.close()

    def test_delete_table(self):
        """Test delete_table table deletion and sanitation"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        self.assertEqual(d.delete_table("blank", cur, self.con), "Table blank does not exist")

        d.create_table("dummy", cur, self.con)
        #making sure we have a _rb
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        d.rb_helper("dummy", cur)

        self.assertEqual(d.delete_table("dummy", cur, self.con), "Table dummy and its rollback deleted")

        all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertEqual(len(all_table), 0)

        cur.close()
    
    def test_rollback_table(self):
        """test rollback_table reverts to the table_rb"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        self.assertEqual(d.rollback_table("blank", cur, self.con), "Table blank does not exist")
        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.rollback_table("dummy", cur, self.con), "No rollback for dummy")

        d.rb_helper("dummy", cur)
        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(d.rollback_table("dummy", cur, self.con), "Table dummy has been rolled back")
        all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertTrue("dummy_rb" not in all_table)
        self.assertTrue("dummy" in all_table)
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        self.assertEqual(len(result_dummy), 0)

        cur.close()

    def tearDown(self):
        """double check dummy table wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.close()
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
