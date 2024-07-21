#Zane was here

import os
import sqlite3
from datetime import timedelta
from flask import Flask, redirect, url_for, session, render_template
from dotenv import load_dotenv

import app_auth
import app_db

load_dotenv()

conn = app_db.get_db_connection()
app_db.initialize_db_schema(conn)

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

#
# Routes
#

@app.route("/")
def signon():
    if 'oauth_token' in session:
        return redirect('/home')

    return render_template(
        "signon.html"
    )
    

@app.route("/home")
def home():
    if 'oauth_token' not in session:
        return redirect('login')

    return render_template(
        "home.html"
    )


@app.route("/loghours")
def loghours():
    if 'oauth_token' not in session:
        return redirect('login')

    return render_template(
        "loghours.html"
    )


@app.route("/viewlogs")
def viewlogs():
    if 'oauth_token' not in session:
        return redirect('login')
    
    connection = sqlite3.connect('data/nhsapp.db')
    cursor = connection.cursor()
    cursor.execute("SELECT event_name, event_supervisor, hours_worked, supervisor_signature FROM verification_log")
    verification_log = cursor.fetchall()
    connection.close()

    return render_template("viewlogs.html", logs=verification_log)


@app.route("/profile")
def profile():
    if 'oauth_token' not in session:
        return redirect('login')

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

@app.route("/signature-pad")
def signature_svg():
    return app.send_static_file("img/signature.svg")


    # if Profile Class of is not populated, then redirect to Profile

#Screens (Users):
#Login, Dashboard, Log hours page, See hours completed page, Upcoming and Past Events, Announcements, Info and Contact Me, view users
#Screens (Managers):
#Everything that Users have, See all students verification logs, Enter hours for other people, Enter event data, change permissions
