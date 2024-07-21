import os
import sqlite3
from datetime import timedelta
from flask import Flask, redirect, url_for, session, render_template, g
from dotenv import load_dotenv

import app_auth
import app_db

load_dotenv()


#
# Flask
#
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

# Google authentication routes
app.add_url_rule('/login', view_func=app_auth.login)
app.add_url_rule('/oauth2callback', view_func=app_auth.callback)
app.add_url_rule('/logout', view_func=app_auth.logout)
app.add_url_rule('/userinfo', view_func=app_auth.userinfo)

# Remember login for 365 days
app.permanent_session_lifetime = timedelta(days=365)


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


#
# Routes
#

@app.route("/")
def signon():
    if app_auth.is_logged_in():
        return redirect('/home')

    return render_template(
        "signon.html"
    )
    

@app.route("/home")
def home():
    if not app_auth.is_logged_in():
        return redirect('/login')

    # Last 3 verification logs for this end-user
    query = """SELECT event_name, event_date, event_supervisor, hours_worked, supervisor_signature
                FROM verification_log vl
                INNER JOIN app_user u on u.app_user_id = vl.app_user_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
                LIMIT 3
            """

    verification_log = app_db.query_db(query, [session['user_email']])

    return render_template(
        "home.html",
        logs = verification_log
    )


@app.route("/loghours")
def loghours():
    if not app_auth.is_logged_in():
        return redirect('/login')

    return render_template(
        "loghours.html"
    )


@app.route("/viewlogs")
def viewlogs():
    if not app_auth.is_logged_in():
        return redirect('/login')
    
    query = """SELECT event_name, event_date, event_supervisor, hours_worked, supervisor_signature
                FROM verification_log vl
                INNER JOIN app_user u on u.app_user_id = vl.app_user_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
            """

    verification_log = app_db.query_db(query, [session['user_email']])
    
    return render_template("viewlogs.html", logs=verification_log)


@app.route("/profile")
def profile():
    if not app_auth.is_logged_in():
        return redirect('/login')

    return render_template(
        "profile.html",
        name=session['full_name'],
        email=session['user_email'],
        photo_url=session['picture']
    )  


@app.route("/contact")
def contact():
    return render_template(
        "contact.html"
    )


@app.route("/privacy")
def privacy():
    return "Privacy"


@app.route("/tos")
def tos():
    return "Terms of Service"


    # if Profile Class of is not populated, then redirect to Profile

#Screens (Users):
#Login, Dashboard, Log hours page, See hours completed page, Upcoming and Past Events, Announcements, Info and Contact Me, view users
#Screens (Managers):
#Everything that Users have, See all students verification logs, Enter hours for other people, Enter event data, change permissions
