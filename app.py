#
# Zane Shaiyen, zaneshaiyen@gmail.com
#
# Main application with all routes
#
import os
from datetime import date, timedelta, datetime
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

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    if class_year_name is not None:
        # Category hours worked / hours required for user for the current period
        current_period_date = os.getenv('CURRENT_PERIOD_DATE')
        override_period_flag = 1
        if current_period_date is None:
            override_period_flag = 0
            current_period_date = date.today()

        user_categories_rv = app_lib.get_user_category_hours(current_period_date, class_year_name, session['organization_id'], session['user_email'])
        total_result = app_lib.get_user_total_hours(current_period_date, class_year_name, session['organization_id'], session['user_email'])
        if total_result is None:
            total_hours_required = total_hours_worked = 0
        else:
            total_hours_required, total_hours_worked = total_result
    else:
        user_categories_rv = []

    # Display last 3 verification logs for user
    query = """SELECT c.name AS category_name, p.name AS period_name, vl.event_name, vl.event_date, vl.event_supervisor, vl.hours_worked, vl.supervisor_signature, vl.location_coords, vl.verification_log_id
                FROM verification_log vl
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
                INNER JOIN category c ON c.category_id = vl.category_id
                INNER JOIN period p ON p.period_id = vl.period_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
                LIMIT 3
            """

    verification_log_rv = app_db.query_db(query, [session['user_email']])

    return render_template(
        "home.html",
        logs = verification_log_rv,
        user_categories=user_categories_rv,
        total_hours_required=total_hours_required,
        total_hours_worked=total_hours_worked,
        current_period_date=current_period_date,
        override_period_flag=override_period_flag
    )


#
# Add Verification Log
#
@app.route("/loghours", defaults = { 'category_name': None }, methods = ['GET', 'POST'])
@app.route("/loghours/<category_name>", methods = ['GET', 'POST'])
def loghours(category_name):
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    if not app_auth.is_profile_complete():
        return redirect(url_for('profile'))

    # User clicked [Save] button
    if request.method == 'POST':
        event_date = request.form.get('eventdate')
        hours_worked = request.form.get('hours')
        pathdata = request.form.get('pathdata')
        event_name = request.form.get('eventname')   
        supervisor = request.form.get('supervisor')       
        coords = request.form.get('coords')

        if category_name is None:
            category_name = request.form.get('eventcategory')

        ## Check for required fields here too (don't rely on <input required>). Flash message back if required fields not filled.

        ## Event date cannot be in the future
        if datetime.strptime(event_date, "%Y-%m-%d").date() > date.today():
            return "Event date cannot be in the future"

        period_rv = app_lib.get_period_by_date(session['organization_id'], event_date)
        if period_rv is None:
            ## Could not determine period. Handle this. Event date entered is probably out of range. Flash message
            return "Event date is out of range"
        elif period_rv[0]['locked_flag'] == 1:
            ## Not allowed to enter verification logs for locked periods. Flash message
            return "Period is locked. Not allowed to enter verification logs for locked periods."

        ## Insert verification log and update summary table should happen as one transaction. Create SQL procedure for this?
        query = """INSERT OR IGNORE INTO verification_log
                    (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, category_id, app_user_id, period_id)
                    SELECT ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id FROM app_user u
                    LEFT JOIN period p on p.organization_id = u.organization_id AND ? BETWEEN p.start_date AND p.end_date
                    LEFT JOIN category c on c.organization_id = u.organization_id and c.name = ?
                    WHERE u.email = ? AND u.organization_id = ?
                """
        insert_count = app_db.update_db(query, [event_name, event_date, supervisor, hours_worked, pathdata, coords,
                                                event_date, category_name, session['user_email'], session['organization_id']])

        if insert_count == 1:
            # Update summary table
            app_lib.update_user_category_hours(event_date, category_name, session['organization_id'], session['user_email'])
            return redirect(url_for('viewlogs'))
        else:
            ## Handle issue?
            return "Could not save verification log"

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    if class_year_name is None:
        category_rv = []
    else:
        # Use class_year_name to construct column name: Sophomore_visible_flag, Junior_visible_flag, etc.
        query = f"""SELECT name, category_id FROM category
                    WHERE
                    organization_id = ? AND {class_year_name}_visible_flag == 1
                    ORDER BY display_order
                """
        category_rv = app_db.query_db(query, [session['organization_id']])

    return render_template(
        "loghours.html",
        eventcategory=category_name,
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
    
    ## Should only show logs for current academic year by default

    # Verification logs for the user
    query = """SELECT c.name AS category_name, p.name AS period_name, vl.event_name, vl.event_date, vl.event_supervisor, vl.hours_worked, vl.supervisor_signature, vl.location_coords, vl.verification_log_id
                FROM verification_log vl
                INNER JOIN app_user u on u.app_user_id = vl.app_user_id
                INNER JOIN category c on c.category_id = vl.category_id
                INNER JOIN period p ON p.period_id = vl.period_id
                WHERE u.email = ?
                ORDER BY event_date DESC, verification_log_id DESC
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

        ## Check for required fields here too (don't rely on <input required>). Flash message back if required fields not filled.

        query = """UPDATE app_user SET class_of = ?, school_id = ?
                    WHERE email = ?
                """

        updated_count = app_db.update_db(query, [class_of, school_id, session['user_email']])

        if updated_count <= 0:
            ## Handle issue?
            return "Could not save user profile"

    # Display User Profile data. Email and Name come from Session cookie (as reported by Google).
    query = """SELECT u.photo_url, u.school_id, u.class_of, cy.name as class_year_name
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE
                u.email = ? AND u.organization_id = ?
            """
    user_profile_rv = app_db.query_db(query, [session['user_email'], session['organization_id']])

    query = "SELECT year_num FROM class_year WHERE organization_id = ? ORDER BY year_num"
    class_years_rv = app_db.query_db(query, [session['organization_id']])

    return render_template(
        "profile.html",
        user_email=session['user_email'],
        full_name=session['full_name'],
        photo_url=user_profile_rv[0]['photo_url'],
        class_of=user_profile_rv[0]['class_of'],
        school_id=user_profile_rv[0]['school_id'],
        class_year_name=user_profile_rv[0]['class_year_name'],
        class_years=class_years_rv
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
        ### START TEST CODE

        pass

        ### END TEST CODE

    return "This route is not available in Production"