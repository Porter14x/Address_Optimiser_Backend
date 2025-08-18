import unittest
import database as d
import sqlite3
import os

class TestDatabaseMethods(unittest.TestCase):

    con = sqlite3.connect("test.db")
    cur = con.cursor()

    def setUp(self):
        """ensure dummy table is wiped"""
        self.cur.execute("DROP TABLE IF EXISTS dummy;")
        return super().setUp()

    def test_create_table(self):
        regex_fail_list = ["!", '"', "£", "$", "%", "^", "&", "*", "(", ")", "-", "+","=",
                           "{", "}", "[", "]", "~", "#", ":", ";", "@", "'", "<", ",",
                           ">", ".", "?", "/", "|", "¬", "`",]

        rb_fail = "table_rb"
        self.assertEqual(d.create_table(rb_fail), "Cannot have _rb in table name")

        for char in regex_fail_list:
            self.assertEqual(d.create_table("table"+char), 
            "Invalid table name. Please ensure only letters, numbers and underscores are used")

        d.create_table("dummy")
        self.assertEqual(d.create_table("dummy"), "Table dummy already exists")

    def tearDown(self):
        """close connection"""
        self.cur.close()
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
    
