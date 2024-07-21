import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

#
# Database
#
APP_DATABASE = os.getenv('APP_DATABASE')
APP_DATABASE_SCHEMA = os.getenv('APP_DATABASE_SCHEMA')

def get_db_connection():
    conn = sqlite3.connect(APP_DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = 1')
    return conn

def initialize_db_schema(conn):
    with open(APP_DATABASE_SCHEMA) as f:
        conn.executescript(f.read())
