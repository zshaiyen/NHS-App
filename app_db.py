#
# Methods related to sqlite3 database
#
import os
import sqlite3
from flask import g
from dotenv import load_dotenv

load_dotenv()

#
# Database
#
APP_DATABASE = os.getenv('APP_DATABASE')
APP_DATABASE_SCHEMA = os.getenv('APP_DATABASE_SCHEMA')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(APP_DATABASE)
    db = sqlite3.connect(APP_DATABASE)
    db.row_factory = sqlite3.Row

    return db


def query_db(query, args=()):
    cur = get_db().cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()

    # rv[row #]{'column_name'}
    return rv


def insert_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastrowid = cur.lastrowid
    cur.close()

    return lastrowid


def update_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    rowcount = cur.rowcount
    cur.close()

    return rowcount


#
# To initialize database the first time, run the following from python prompt:
#   from app_db import initialize_db
#   initialize_db()
#
def initialize_db():
    db = sqlite3.connect(APP_DATABASE)
    with open(APP_DATABASE_SCHEMA) as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()
