"""Unit tests for whole project are placed here"""

import unittest
import sqlite3
from unittest.mock import patch
import database as d
from main import app

class MainTestCase(unittest.TestCase):
    """Class for testing functions of main.py - may see some redundancy in how it has similar tests
    to DatabaseTestCase but will do so anyway to test request/response handling"""

    con = sqlite3.connect("test.db")
    FORBIDDEN_CHAR = [";", '"', "'"]
    regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`", " "]

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
        """test handling an insert address request, ensure it
        optimises the addresses correctly and ensure the _rb is before insert+optimise"""
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

    #no patch for optimise_address since a fail case shouldn't get that far
    @patch("main.DB_PATH", "test.db")
    def test_insert_value_fail(self):
        """handle a request fail case and ensure the error msgs are returned as expected"""

        for char in self.FORBIDDEN_CHAR:
            response0 = self.app.post("/insert_value",
            json={"table": "dummy","address": ("1 House St", f"{char}A01")})
            response1 = self.app.post("/insert_value",
            json={"table": "dummy", "address": (f"{char}1 House St", "A01")})
            response2 = self.app.post("/insert_value",
            json={"table": "dummy", "address": (f"{char}1 House St", f"{char}A01")})

            self.assertEqual(response0.text, f"Forbidden character {char} in input")
            self.assertEqual(response1.text, f"Forbidden character {char} in input")
            self.assertEqual(response2.text, f"Forbidden character {char} in input")

        duplicate = self.app.post("/insert_value",
            json={"table": "dummy","address": ("2 House St", "A01")})
        self.assertEqual(duplicate.text, "Street and postcode already in database")

    @patch("main.DB_PATH", "test.db")
    def test_create_table_success(self):
        """test /create_table handles a correct request and returns a msg"""
        response = self.app.post("/create_table", json={"table": "tester"})
        self.assertEqual(response.text, "Table tester created")

    @patch("main.DB_PATH", "test.db")
    def test_create_table_fail(self):
        """test /create_table handles incorrect requests and returns error msgs"""
        duplicate = self.app.post("/create_table", json={"table": "dummy"}) #dummy from setUp
        self.assertEqual(duplicate.text, "Table dummy already exists")

        rb_fail = self.app.post("/create_table", json={"table": "tester_rb"})
        self.assertEqual(rb_fail.text, "Cannot have _rb in table name")

        for char in self.regex_fail_list:
            regex_fail = self.app.post("/create_table", json={"table": f"fail{char}"})
            self.assertEqual(regex_fail.text,
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

    @patch("main.DB_PATH", "test.db")
    def test_delete_table_success(self):
        """test /delete_table handles a correct request and returns a msg"""
        drop = self.app.post("/delete_table", json={"table": "dummy"})
        self.assertEqual(drop.text, "Table dummy and its rollback deleted")

    @patch("main.DB_PATH", "test.db")
    def test_delete_table_fail(self):
        """test /delete_table handles incorrect requests and returns error msgs"""
        missing = self.app.post("/delete_table", json={"table": "blank"})
        self.assertEqual(missing.text, "Table blank does not exist")

        for char in self.regex_fail_list:
            regex_fail = self.app.post("/create_table", json={"table": f"fail{char}"})
            self.assertEqual(regex_fail.text,
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

    @patch("main.optimise_addresses")
    @patch("main.DB_PATH", "test.db")
    def test_delete_value_success(self, mock_opt):
        """test handling an delete address request, ensure it
        optimises the addresses correctly and ensure the _rb is before delete+optimise"""

        cur = self.con.cursor()

        d.insert_value("dummy", "4 House St", "A01", cur, self.con)
        d.insert_value("dummy", "1 House Dr", "A01", cur, self.con)
        #Assume that (somehow) 1 House Dr becomes the most optimal address to go to first when
        #4 House St is deleted

        #lat and lon arent used so val doesnt matter
        mock_opt_json = [
            {"lat": 0, "lon": 0, "original_index": 2}, #1 House Dr
            {"lat": 0, "lon": 0, "original_index": 0}, #2 House St
            {"lat": 0, "lon": 0, "original_index": 1}, #3 House St
        ]
        mock_opt.return_value = mock_opt_json

        response = self.app.post("/delete_value", json={"table": "dummy", "address": ("4 House St", "A01")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Deleted values (4 House St, A01) from dummy")

        cur = self.con.cursor()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertTrue("dummy" in all_tables)
        self.assertTrue("dummy_rb" in all_tables)
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        self.assertListEqual(result_dummy_rb, [("2 House St", "A01"), ("3 House St", "A01"),
                                               ("4 House St", "A01"), ("1 House Dr", "A01")])
        self.assertListEqual(result_dummy, [("1 House Dr", "A01"), ("2 House St", "A01"),
                                            ("3 House St", "A01")])

    #no patch for optimise_address since a fail case shouldn't get that far
    @patch("main.DB_PATH", "test.db")
    def test_delete_value_fail(self):
        """handle a request fail case and ensure the error msgs are returned as expected"""

        for char in self.FORBIDDEN_CHAR:
            response0 = self.app.post("/delete_value",
            json={"table": "dummy","address": ("1 House St", f"{char}A01")})
            response1 = self.app.post("/delete_value",
            json={"table": "dummy", "address": (f"{char}1 House St", "A01")})
            response2 = self.app.post("/delete_value",
            json={"table": "dummy", "address": (f"{char}1 House St", f"{char}A01")})

            self.assertEqual(response0.text, f"Forbidden character {char} in input")
            self.assertEqual(response1.text, f"Forbidden character {char} in input")
            self.assertEqual(response2.text, f"Forbidden character {char} in input")

        missing = self.app.post("/delete_value",
            json={"table": "dummy","address": ("1 None St", "A01")})
        self.assertEqual(missing.text, "Street and postcode not found in database")

    @patch("main.DB_PATH", "test.db")
    def test_rollback_success(self):
        """test a rollback request and ensure table is rolled back as expected"""
        cur = self.con.cursor()

        response = self.app.post("/rollback", json={"table": "dummy"})
        self.assertEqual(response.text, "Table dummy has been rolled back")

        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertTrue("dummy" in all_tables)
        self.assertTrue("dummy_rb" not in all_tables)

        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        self.assertListEqual(result_dummy, [("2 House St", "A01")])

        cur.close()

    @patch("main.DB_PATH", "test.db")
    def test_rollback_fail(self):
        """test a failcase rollback request and ensure error msg is returned as expected"""
        cur = self.con.cursor()

        missing = self.app.post("/rollback", json={"table": "blank"})
        self.assertEqual(missing.text, "Table blank does not exist")

        d.create_table("no_rollback", cur, self.con)
        no_rb = self.app.post("/rollback", json={"table": "no_rollback"})
        self.assertEqual(no_rb.text, "No rollback for no_rollback")

        cur.execute("DROP TABLE no_rollback;")
        cur.close()

    def tearDown(self):
        """double check test tables wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.execute("DROP TABLE IF EXISTS dummy_rb;")
        cur.execute("DROP TABLE IF EXISTS tester;")
        cur.execute("DROP TABLE IF EXISTS tester_rb;")
        cur.close()
        return super().tearDown()

class DatabaseTestCase(unittest.TestCase):
    """Class for testing the functions of database.py"""

    con = sqlite3.connect("test.db")
    FORBIDDEN_CHAR = [";", '"', "'"]
    regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`", " "]

    def setUp(self):
        """ensure dummy table is wiped"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")
        cur.close()
        return super().setUp()

    def test_table_verification(self):
        """test tables are verified correctly"""
        rb_fail = "table_rb"
        self.assertEqual(d.table_verification(rb_fail)[1], "Cannot have _rb in table name")

        for char in self.regex_fail_list:
            self.assertEqual(d.table_verification("table"+char)[1],
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

    def test_forbidden_char_check(self):
        """test forbidden chars are found"""
        for char in self.FORBIDDEN_CHAR:
            self.assertEqual(d.forbidden_char_check("street", f"{char}postcode")[1],
                             f"Forbidden character {char} in input")
            self.assertEqual(d.forbidden_char_check(f"{char}street", "postcode")[1],
                             f"Forbidden character {char} in input")
            self.assertEqual(d.forbidden_char_check(f"{char}street", f"{char}postcode")[1],
                             f"Forbidden character {char} in input")

    def test_create_table_success(self):
        """test create_table table creation and sanitation"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.create_table("dummy", cur, self.con)[1], "Table dummy already exists")

        self.assertTrue("dummy" in 
                        [r[0] for r in cur.execute("SELECT name FROM sqlite_master").fetchall()])

        cur.close()

    def test_create_table_fail(self):
        """test fail cases for create_table - see test_table_verification for regex check"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.create_table("dummy", cur, self.con)[1], "Table dummy already exists")

        cur.close()

    def test_insert_value_success(self):
        """test insert_table value insertion and sanitation"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)

        output = d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Inserted values (1 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Inserted values (2 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Inserted values (3 House St, A01) into dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01"),
                                            ("3 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        cur.close()

    def test_insert_value_fail(self):
        """test insert_value fail case handling"""
        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)

        for char in self.FORBIDDEN_CHAR:
            self.assertEqual(d.insert_value("dummy", "street", f"{char}postcode",
                                            cur, self.con)[1], f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", "postcode",
                                            cur, self.con)[1], f"Forbidden character {char} in input")
            self.assertEqual(d.insert_value("dummy", f"{char}street", f"{char}postcode",
                                            cur, self.con)[1], f"Forbidden character {char} in input")

        d.insert_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(d.insert_value("dummy", "3 House St", "A01", cur, self.con)[1],
                         "Street and postcode already in database")

        cur.close()

    def test_delete_value_success(self):
        """test delete_value value deletion and sanitation"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)

        output = d.delete_value("dummy", "3 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Deleted values (3 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01"),
                                               ("3 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.delete_value("dummy", "2 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Deleted values (2 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [("1 House St", "A01")])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01"), ("2 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        output = d.delete_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(output[1], "Deleted values (1 House St, A01) from dummy")
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        result_dummy_rb = cur.execute("SELECT street, postcode FROM dummy_rb").fetchall()
        all_tables = [r[0] for r in
                      cur.execute("SELECT name FROM sqlite_master").fetchall()]

        self.assertListEqual(result_dummy, [])
        self.assertListEqual(result_dummy_rb, [("1 House St", "A01")])
        self.assertListEqual(all_tables, ["dummy", "dummy_rb"])

        cur.close()

    def test_delete_value_fail(self):
        """test delete_value failcases"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)

        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        d.insert_value("dummy", "2 House St", "A01", cur, self.con)
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)

        self.assertEqual(d.delete_value("dummy", "4 House St", "A01", cur, self.con)[1],
                         "Street and postcode not found in database")

        cur.close()

    def test_delete_table_success(self):
        """Test delete_table table deletion and sanitation"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        d.create_table("dummy", cur, self.con)
        #making sure we have a _rb
        d.insert_value("dummy", "3 House St", "A01", cur, self.con)

        self.assertEqual(d.delete_table("dummy", cur, self.con)[1], "Table dummy and its rollback deleted")

        all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertEqual(len(all_table), 0)

        cur.close()

    def test_delete_table_fail(self):
        """test delete_table failcases"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        self.assertEqual(d.delete_table("blank", cur, self.con)[1], "Table blank does not exist")

        cur.close()

    def test_rollback_table_success(self):
        """test rollback_table reverts to the table_rb"""

        cur = self.con.cursor()
        d.create_table("dummy", cur, self.con)

        d.rb_helper("dummy", cur)
        d.insert_value("dummy", "1 House St", "A01", cur, self.con)
        self.assertEqual(d.rollback_table("dummy", cur, self.con)[1], "Table dummy has been rolled back")
        all_table = [t[0] for t in cur.execute("SELECT name FROM sqlite_master").fetchall()]
        self.assertTrue("dummy_rb" not in all_table)
        self.assertTrue("dummy" in all_table)
        result_dummy = cur.execute("SELECT street, postcode FROM dummy").fetchall()
        self.assertEqual(len(result_dummy), 0)

        cur.close()

    def test_rollback_table_fail(self):
        """test rollback_table failcases"""

        cur = self.con.cursor()
        cur.executescript("DROP TABLE IF EXISTS dummy; DROP TABLE IF EXISTS dummy_rb")

        self.assertEqual(d.rollback_table("blank", cur, self.con)[1], "Table blank does not exist")
        d.create_table("dummy", cur, self.con)
        self.assertEqual(d.rollback_table("dummy", cur, self.con)[1], "No rollback for dummy")

        cur.close()

    def tearDown(self):
        """double check test tables wiped"""
        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS dummy;")
        cur.execute("DROP TABLE IF EXISTS dummy_rb;")
        cur.execute("DROP TABLE IF EXISTS tester;")
        cur.execute("DROP TABLE IF EXISTS tester_rb;")
        cur.close()
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
