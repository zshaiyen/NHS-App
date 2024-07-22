import os
from datetime import timedelta
from flask import Flask, redirect, url_for, session, render_template, g, request, flash
from dotenv import load_dotenv

import app_auth
import app_db

load_dotenv()


#
# Flask
#
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

#app.config["APPLICATION_ROOT"] = "/nhsapp"

# Translate None to '' in templates
#app.jinja_env.finalize = lambda x: x if x is not None else ''

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
        return redirect(url_for('home'))

    return render_template(
        "signon.html"
    )
    

@app.route("/home")
def home():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))
    
    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

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

@app.route("/loghours", defaults={'log_id': None}, methods = ['GET', 'POST'])
@app.route("/loghours/<log_id>", methods = ['GET', 'POST'])
def loghours(log_id):
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

    if request.method == 'POST':
        eventname = request.form.get('eventname')
        supervisor = request.form.get('supervisor')
        hoursworked = request.form.get('hours')
        pathdata = request.form.get('pathdata')
        coords = request.form.get('coords')

        if log_id is None:
            query = """INSERT INTO verification_log
                        (event_name, event_supervisor, hours_worked, supervisor_signature, location_coords, app_user_id)
                        SELECT ?, ?, ?, ?, ?, u.app_user_id FROM app_user u WHERE u.email = ?
                    """
            updated_count = app_db.update_db(query, [eventname, supervisor, hoursworked, pathdata, coords, session['user_email']])

        else:
            query = """UPDATE verification_log SET
                        event_name = ?,
                        event_supervisor = ?,
                        hours_worked = ?
                        WHERE
                        verification_log_id = ?
                    """
            updated_count = app_db.update_db(query, [eventname, supervisor, hoursworked, log_id])

        if updated_count == 1:
            return redirect(url_for('viewlogs'))

    return render_template(
        "loghours.html",
        log_id=log_id
    )


@app.route("/viewlogs")
def viewlogs():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))
    
    query = """SELECT event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, verification_log_id
                FROM verification_log vl
                INNER JOIN app_user u on u.app_user_id = vl.app_user_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
            """

    verification_log = app_db.query_db(query, [session['user_email']])

    return render_template("viewlogs.html", logs=verification_log)


@app.route("/profile", defaults={'action': None}, methods = ['GET', 'POST'])
@app.route("/profile/<action>", methods = ['GET', 'POST'])
def profile(action):
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    # Form submitted
    if request.method == 'POST' and action == 'update':
        class_of = request.form.get('class_of')
        school_id = request.form.get('school_id')

        query = """UPDATE app_user SET class_of = ?, school_id = ?
                    WHERE email = ?
                """
        updated_count = app_db.update_db(query, [class_of, school_id, session['user_email']])

        if updated_count == 1:
            flash("Saved successfully", "success")

        return redirect(url_for('profile'))

    # Display form data
    query = """SELECT class_of, school_id FROM app_user WHERE email = ?"""
    user_profile = app_db.query_db(query, [session['user_email']])

    return render_template(
        "profile.html",
        name=session['full_name'],
        email=session['user_email'],
        photo_url=session['picture'],
        class_of=user_profile[0]['class_of'],
        school_id=user_profile[0]['school_id']
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
