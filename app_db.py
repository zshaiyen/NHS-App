#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#

#
# Methods related to sqlite3 database 
#
import os
import sqlite3
from flask import g
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

#
# Database
#
APP_DATABASE = os.getenv('APP_DATABASE')

#
# Get database connection
#
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(APP_DATABASE)
    db = sqlite3.connect(APP_DATABASE)
    db.row_factory = sqlite3.Row

    return db

#
# Run SELECT statements on the database
#
def query_db(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()

    # rv[row #]{'column_name'}
    return rv

#
# Run INSERT statements on the database and return last inserted row ID
#
def insert_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastrowid = cur.lastrowid
    cur.close()

    return lastrowid

#
# Run INSERT or UPDATE statements on database and return number of rows affected
#
def update_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    rowcount = cur.rowcount
    cur.close()

    return rowcount
