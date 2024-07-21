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

    db.row_factory = sqlite3.Row

    return db


def query_db(query, args=()):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()

    return rv


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
