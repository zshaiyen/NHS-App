#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
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

        total_hours_required, total_hours_worked, user_categories_rv = app_lib.get_user_category_hours(current_period_date, class_year_name, session['organization_id'], session['user_email'])
    else:
        user_categories_rv = []

    # Display last 3 verification logs for user
    verification_log_rv = app_lib.get_verification_logs(session['user_email'], 3)

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

        if app_lib.add_update_verification_log(category_name, event_date, hours_worked, event_name, supervisor, pathdata, coords,
                                                session['organization_id'], session['user_email'], session['user_id']):
            return redirect(url_for('home'))
        else:
            ## Handle issue?
            return "Could not save verification log"

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    # Use class_year_name to construct column name: Sophomore_visible_flag, Junior_visible_flag, etc.
    category_rv = app_lib.get_available_categories(session['organization_id'], class_year_name)

    if category_rv is None:
        return "Unable to determine available categories"

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

    verification_log_rv = app_lib.get_verification_logs(session['organization_id'], session['user_email'])

    return render_template("viewlogs.html", logs=verification_log_rv)


#
# User Profile
#
@app.route("/profile", defaults={'email': None, 'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>", defaults={'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>/<action>", methods=['GET', 'POST'])
def profile(email, action):
    if not app_auth.is_logged_in():
        return redirect(url_for('login'))

    is_admin = app_auth.is_user_admin()

    if email:
        if email == session['user_email'] and not action:
            return redirect(url_for('profile'))

        profile_email = email if is_admin else session['user_email']
    else:
        profile_email = session['user_email']

    if request.method == 'POST':
        class_of = request.form.get('class_of')
        school_id = request.form.get('school_id')
        team_name = request.form.get('team_name')
        admin_flag = request.form.get('admin_flag')
        disabled_flag = request.form.get('disabled_flag')

        updated_count = app_lib.update_user_profile(session['organization_id'], profile_email, session['user_id'], class_of, school_id, team_name, admin_flag, disabled_flag)

        if updated_count <= 0:
            return redirect(url_for('profile', email=profile_email))
        
        return redirect(url_for('profile', email=profile_email))

    user_profile_rv = app_lib.get_user_profile(session['organization_id'], profile_email)

    if not user_profile_rv:
        return "Invalid user " + str(profile_email)

    class_years_rv = app_lib.get_available_class_years(session['organization_id'])

    return render_template(
        "profile.html",
        user_profile=user_profile_rv,
        class_years=class_years_rv,
        is_admin=is_admin
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


# @app.route("/log", defaults={'log_id': None}, methods=['GET', 'POST'])
# @app.route("/log/<int:log_id>", methods=['GET', 'POST'])
# @app.route("/log/<int:log_id>/<action>", methods=['GET', 'POST'])
# def log(log_id):
    
#     if request.method == 'GET':
#         category = request.args.get('category', '')

#         if log_id is None:
#             message = "You have arrived at the log page."
#         else:
#             message = f"You are trying to edit the log ID number {log_id}."

#         return render_template("log.html", message=message, category=category, log_id=log_id)

#     if request.method == 'POST':
#         postcategory = request.form.get('category')
#         return postcategory
### go to /log print message that says you have arrived at log
### go to /log/3 you are trying to edit the log id number
### create a form template that has one input text field in it; call that field 'category'
### same function go to route /log/3?category=nhs load the form with the form already filled out in category