#
# Zane Shaiyen, zaneshaiyen@gmail.com
#
# Main application with all routes
#
import os
from datetime import timedelta
from flask import Flask, redirect, url_for, session, render_template, g, request
from dotenv import load_dotenv

import app_auth     # Authentication helpers
import app_db       # Database connection helpers
import app_lib      # Other helpers


# Load environment variables from .env
load_dotenv()


#
# Flask
#
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')
#app.config["APPLICATION_ROOT"] = "/nhsapp"

# Stay logged in for 365 days, unless user explicitly logs out
app.permanent_session_lifetime = timedelta(days=365)

@app.before_request
def make_session_permanent():
    session.permanent = True

# Clean up at end of request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


###################################################################################################
#                                  Routes for this application
###################################################################################################

#
# Google OAuth2 authentication routes. See app_auth.py
#
app.add_url_rule('/login', view_func=app_auth.login)
app.add_url_rule('/oauth2callback', view_func=app_auth.callback)
app.add_url_rule('/logout', view_func=app_auth.logout)
app.add_url_rule('/userinfo', view_func=app_auth.userinfo)


#
# Sign-on screen
#
@app.route("/")
def signon():
    if app_auth.is_logged_in():
        return redirect(url_for('home'))

    return render_template(
        "signon.html"
    )
    

# 
# Home (Dashboard)
#
@app.route("/home")
def home():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))
    
    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

    # Category summary (hard-code for now but replace with actual data)
    user_categories = [{ 'category_name': 'NHS', 'hours_worked': 3.5, 'hours_required': 15.0 },
                       { 'category_name': 'Tutoring', 'hours_worked': 7.5, 'hours_required': 5.0 },
                       { 'category_name': 'Other', 'hours_worked': 4.5, 'hours_required': 5.0 }]

    # Display last 3 verification logs for user
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
        logs = verification_log,
        user_categories=user_categories
    )


#
# Add Verification Log
#
@app.route("/loghours", methods = ['GET', 'POST'])
def loghours():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

    # User clicked [Save] button
    if request.method == 'POST':
        eventname = request.form.get('eventname')
        eventdate = request.form.get('eventdate')
        supervisor = request.form.get('supervisor')
        hoursworked = request.form.get('hours')
        pathdata = request.form.get('pathdata')
        coords = request.form.get('coords')
        category = request.form.get('eventcategory')

        query = """INSERT INTO verification_log
                    (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, category_id, app_user_id, period_id)
                    SELECT ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id FROM app_user u
                    LEFT JOIN period p on p.organization_id = u.organization_id
                    LEFT JOIN category c on c.organization_id = u.organization_id
                    WHERE u.email = ? AND u.organization_id = ? AND p.start_date <= ? AND c.name = ?
                    ORDER BY p.start_date DESC
                    LIMIT 1
                """
        insert_count = app_db.update_db(query, [eventname, eventdate, supervisor, hoursworked, pathdata, coords,
                                                 session['user_email'], session['organization_id'], eventdate, category])

        if insert_count == 1:
            return redirect(url_for('viewlogs'))
        else:
            # Handle issue?
            pass
    else:
        category = None

    ##### Include visibility in WHERE clause
    query = """SELECT name, category_id FROM category
                WHERE
                organization_id = ?
                ORDER BY display_order
            """
    category_rv = app_db.query_db(query, [session['organization_id']])

    return render_template(
        "loghours.html",
        eventcategory=category,
        category_list=category_rv
    )


#
# View Verification Log
#
@app.route("/viewlogs")
def viewlogs():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

    # Verification logs for the user
    query = """SELECT event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, verification_log_id
                FROM verification_log vl
                INNER JOIN app_user u on u.app_user_id = vl.app_user_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
            """

    verification_log = app_db.query_db(query, [session['user_email']])

    return render_template("viewlogs.html", logs=verification_log)


#
# User Profile
#
@app.route("/profile", methods = ['GET', 'POST'])
def profile():
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    # User clicked [Save] button
    if request.method == 'POST':
        class_of = request.form.get('class_of')
        school_id = request.form.get('school_id')

        query = """UPDATE app_user SET class_of = ?, school_id = ?
                    WHERE email = ?
                """

        updated_count = app_db.update_db(query, [class_of, school_id, session['user_email']])

        if updated_count <= 0:
            # Handle issue?
            pass

    # Display User Profile data. Email and Name come from Session cookie (as reported by Google).
    query = "SELECT photo_url, class_of, school_id FROM app_user WHERE email = ?"
    user_profile = app_db.query_db(query, [session['user_email']])

    class_of_year_name = user_profile[0]['class_of']

    return render_template(
        "profile.html",
        user_email=session['user_email'],
        full_name=session['full_name'],
        photo_url=user_profile[0]['photo_url'],
        class_of=user_profile[0]['class_of'],
        school_id=user_profile[0]['school_id'],
        class_year_name=app_lib.get_class_year_name(user_profile[0]['class_of'])
    )


#
# Change this to footer with support information instead of menu entry?
#
@app.route("/contact")
def contact():
    return render_template(
        "contact.html"
    )


#
# Privacy Statement
#
@app.route("/privacy")
def privacy():
    return "Privacy"


#
# Terms of Service
#
@app.route("/tos")
def tos():
    return "Terms of Service"


#
# Scratch space - Use this route for testing code
#
@app.route("/test", defaults = { 'arg1': None, 'arg2': None })
@app.route("/test/<arg1>", defaults = { 'arg2': None })
@app.route("/test/<arg1>/<arg2>")
def dev_test(arg1, arg2):
    DEV_MODE = os.getenv('DEV_MODE')

    if DEV_MODE == '1':
        #
        # START TEST CODE BELOW
        #

        class_year_name = app_lib.get_class_year_name(arg1)

        return class_year_name

        #
        # END TEST CODE
        #

    return "This route is not available in Production"