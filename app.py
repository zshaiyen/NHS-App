#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#
# Main application with all routes
#
import os
from datetime import date, timedelta, datetime
from flask import Flask, redirect, url_for, session, render_template, g, request, flash
from dotenv import load_dotenv

import app_auth     # Authentication helpers
import app_db       # Database connection helpers
import app_lib      # Other helpers


# Load environment variables from .env
load_dotenv()


#
# Flask
#
template_dir = os.getenv('TEMPLATE_DIR')
if template_dir:
    app = Flask(__name__, template_folder=template_dir)
else:
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
    if app_lib.is_logged_in(session):
        return redirect(url_for('home'))

    app_lib.update_organization_session_data(session)

    organization_rv = app_lib.get_organization_detail(request.headers['HOST'])

    if len(organization_rv) <= 0:
        return "Could not determine organization details for " + request.headers['HOST']

    return render_template(
        "signon.html",
        organization=organization_rv
    )


# 
# Home (Dashboard)
#
@app.route("/home")
def home():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('login'))
    
    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    if class_year_name is None:
        flash('Unable to determine user class year name', 'danger')

        return redirect(url_for('profile'))

    total_hours_required, total_hours_worked, user_categories_rv = app_lib.get_user_category_hours(date.today(), class_year_name, session['organization_id'], session['user_email'])

    # Display last 3 verification logs for user
    total_hours, verification_log_rv = app_lib.get_verification_logs(session['organization_id'], session['user_email'], row_limit=3)

    return render_template(
        "home.html",
        logs = verification_log_rv,
        user_categories=user_categories_rv,
        total_hours_required=total_hours_required,
        total_hours_worked=total_hours_worked,
        is_admin=is_admin
    )


#
# Add Verification Log
#
@app.route("/loghours", defaults = {'log_id': None}, methods = ['GET', 'POST'])
@app.route("/loghours/<int:log_id>", methods = ['GET', 'POST'])
def loghours(log_id):
    if not app_lib.is_logged_in(session):
        return redirect(url_for('login'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    # Use class_year_name to construct column name: Sophomore_visible_flag, Junior_visible_flag, etc.
    category_rv = app_lib.get_available_categories(session['organization_id'], class_year_name)

    ip_address, user_agent, mobile_flag = app_lib.get_user_agent_details(request)

    # User clicked [Save] button
    if request.method == 'POST':
        event_category = request.form.get('event_category', default=None)
        event_name = request.form.get('event_name', default=None)
        event_date = request.form.get('event_date', default=None)
        event_supervisor = request.form.get('event_supervisor', default=None)
        hours_worked = request.form.get('hours_worked', default=None)
        pathdata = request.form.get('pathdata', default=None)
        location_coords = request.form.get('coords', default=None)
        location_accuracy = request.form.get('coords_accuracy', default=None)

        failed_validation = False

        # Event date cannot be in the future
        if event_date and datetime.strptime(event_date, "%Y-%m-%d").date() > date.today():
            flash('Event Date cannot be in the future', 'danger')
            failed_validation = True
    
        period_rv = app_lib.get_period_by_date(session['organization_id'], event_date)
        if len(period_rv) <= 0:
            flash('Could not determine period for date ' + str(date), 'danger')
            failed_validation = True

        elif period_rv[0]['locked_flag'] == 1:
            flash('Period for this event date is locked. Not allowed to enter verification logs for locked periods.', 'danger')
            failed_validation = True

        if failed_validation:
            return render_template("loghours.html",
                                        log_id=log_id,
                                        event_category=event_category,
                                        event_name=event_name,
                                        event_date=event_date,
                                        event_supervisor=event_supervisor,
                                        supervisor_signature=None,
                                        location_coords=location_coords,
                                        location_accuracy=location_accuracy,
                                        hours_worked=hours_worked,
                                        category_list=category_rv,
                                        is_admin=is_admin,
                                        ip_address=ip_address,
                                        user_agent=user_agent,
                                        mobile_flag=mobile_flag)

        if log_id:
            if app_lib.update_verification_log(log_id, event_name, hours_worked, session['user_id']):

                flash('Updates to verification log saved successfully', 'success')

                return render_template("loghours.html",
                                            log_id=log_id,
                                            event_category=event_category,
                                            event_name=event_name,
                                            event_date=event_date,
                                            event_supervisor=event_supervisor,
                                            supervisor_signature=None,
                                            location_coords=location_coords,
                                            location_accuracy=location_accuracy,
                                            hours_worked=hours_worked,
                                            category_list=category_rv,
                                            is_admin=is_admin,
                                            ip_address=ip_address,
                                            user_agent=user_agent,
                                            mobile_flag=mobile_flag)
            else:
                flash('Failed to update verification log', 'danger')

                return render_template("loghours.html",
                                            log_id=log_id,
                                            event_category=event_category,
                                            event_name=event_name,
                                            event_date=event_date,
                                            event_supervisor=event_supervisor,
                                            supervisor_signature=None,
                                            location_coords=location_coords,
                                            location_accuracy=location_accuracy,
                                            hours_worked=hours_worked,
                                            category_list=category_rv,
                                            is_admin=is_admin,
                                            ip_address=ip_address,
                                            user_agent=user_agent,
                                            mobile_flag=mobile_flag)

        else:
            if app_lib.add_verification_log(event_category, event_date, hours_worked, event_name, event_supervisor, pathdata, location_coords, location_accuracy,
                                            session['organization_id'], session['user_email'], session['user_id'],
                                            ip_address, str(user_agent), mobile_flag):

                flash('Successfully added verification log', 'success')

                return redirect(url_for('viewlogs'))
            else:
                flash('Failed to add verification log', 'danger')

                return render_template("loghours.html",
                                            log_id=log_id,
                                            event_category=event_category,
                                            event_name=event_name,
                                            event_date=event_date,
                                            event_supervisor=event_supervisor,
                                            supervisor_signature=None,
                                            location_coords=location_coords,
                                            location_accuracy=location_accuracy,
                                            hours_worked=hours_worked,
                                            category_list=category_rv,
                                            is_admin=is_admin,
                                            ip_address=ip_address,
                                            user_agent=user_agent,
                                            mobile_flag=mobile_flag)
    
    if log_id:
        verification_log_rv = app_lib.get_verification_log(log_id)
        event_category = verification_log_rv[0]['category_name']
        event_name = verification_log_rv[0]['event_name']
        event_date = verification_log_rv[0]['event_date']
        event_supervisor = verification_log_rv[0]['event_supervisor']
        hours_worked = verification_log_rv[0]['hours_worked']
        ip_address = verification_log_rv[0]['ip_address']
        user_agent = verification_log_rv[0]['user_agent']
        mobile_flag = verification_log_rv[0]['mobile_flag']
        supervisor_signature = verification_log_rv[0]['supervisor_signature']
        location_coords = verification_log_rv[0]['location_coords']
        location_accuracy = verification_log_rv[0]['location_accuracy']
    else:
        event_name = event_supervisor = hours_worked = event_category = ip_address = user_agent = mobile_flag = supervisor_signature = location_coords = location_accuracy = None
        event_category = request.args.get('defaultcategory')
        event_date = date.today()

        if event_category == '':
            event_category = None

    return render_template("loghours.html",
                            log_id=log_id,
                            event_category=event_category,
                            event_name=event_name,
                            event_date=event_date,
                            event_supervisor=event_supervisor,
                            supervisor_signature=supervisor_signature,
                            location_coords=location_coords,
                            location_accuracy=location_accuracy,
                            hours_worked=hours_worked,
                            category_list=category_rv,
                            is_admin=is_admin,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            mobile_flag=mobile_flag)


#
# View Verification Log 
#
@app.route("/viewlogs", methods=['GET', 'POST'])
def viewlogs():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('login'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    category = min_hours = max_hours = name_filter = period = None

    if request.method == 'POST':
        category = request.form.get('filter_category', default=None, type=str)
        min_hours = request.form.get('min_hours', default=None, type=int)
        max_hours = request.form.get('max_hours', default=None, type=int)
        name_filter = request.form.get('name_filter', default=None, type=str)
        period = request.form.get('period_filter', default=None, type=str)

        if category == '':
            category = None
        if period == '':
            period = None

    total_count, verification_log_rv = app_lib.get_verification_logs(session['organization_id'], 
                                                                     session['user_email'],
                                                                     category=category,
                                                                     min_hours=min_hours,
                                                                     max_hours=max_hours,
                                                                     name_filter=name_filter,
                                                                     period=period
                                                                    )

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    # Use class_year_name to construct column name: Sophomore_visible_flag, Junior_visible_flag, etc.
    category_rv = app_lib.get_available_categories(session['organization_id'], class_year_name)

    period_rv = app_lib.get_available_periods(session['organization_id'])

    if len(category_rv) <= 0:
        return "Unable to determine available categories"

    return render_template("viewlogs.html", 
                           logs=verification_log_rv,
                           total_count=total_count,
                           filter_category=category,
                           filter_minhours=min_hours,
                           filter_maxhours=max_hours,
                           category_list=category_rv,
                           period_list=period_rv,
                           period_filter=period,
                           is_admin=is_admin,
                           name_filter=name_filter
                           )

#
# User Profile
#
@app.route("/profile", defaults={'email': None, 'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>", defaults={'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>/<action>", methods=['GET', 'POST'])
def profile(email, action):
    if not app_lib.is_logged_in(session):
        return redirect(url_for('login'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

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

        # Capture unchecked checkboxes from admin
        if is_admin:
            if admin_flag is None:
                admin_flag = 0

            if disabled_flag is None:
                disabled_flag = 0

        updated_count = app_lib.update_user_profile(session['organization_id'], profile_email, session['user_id'], class_of, school_id, team_name, admin_flag, disabled_flag)

        if updated_count <= 0:
            flash('Failed to save changes', 'danger')
            return redirect(url_for('profile', email=profile_email))

        flash('Updates to Profile saved successfully', 'success')        
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

@app.route("/profiles", methods=['GET', 'POST'])
def profiles():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('login'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    is_admin = app_lib.is_user_admin(session)

    if not is_admin:
        flash('This route requires admin permissions', 'danger')

        return redirect(url_for('home'))

    app_lib.update_organization_session_data(session)    

    name_filter = school_id = class_filter = admin_flag = disabled_flag = None

    if request.method == 'POST':
        name_filter = request.form.get('name_filter', default=None, type=str)
        school_id = request.form.get('school_id', default=None, type=int)
        class_filter = request.form.get('class_filter', default=None, type=int) 
        admin_flag = request.form.get('admin_flag', default=None)
        disabled_flag = request.form.get('disabled_flag', default=None)        

    total_count, user_profiles_rv= app_lib.get_user_profiles(session['organization_id'], 
                                                                     name_filter=name_filter,
                                                                     school_id=school_id,
                                                                     class_filter=class_filter,
                                                                     admin_flag=admin_flag,
                                                                     disabled_flag=disabled_flag
                                                                    )
        
    return render_template(
        'profiles.html',
        user_profiles=user_profiles_rv,
        name_filter=name_filter,
        school_id=school_id,
        class_filter=class_filter,
        admin_flag=admin_flag,
        disabled_flag=disabled_flag,
        is_admin=is_admin,
        total_count=total_count
    )

#
# Change this to footer with support information instead of menu entry?
#
@app.route("/contact")
def contact():
    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)
    
    return render_template(
        "contact.html",
        is_admin=is_admin
    )


#
# Privacy Statement
#
@app.route("/privacy")
def privacy():
    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    return render_template("privacy.html", is_admin=is_admin)


#
# Terms of Service
#
@app.route("/tos")
def tos():
    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    return render_template("tos.html", is_admin=is_admin)


#
# Debug - Display Session cookie contents
#
@app.route("/zane/cookie")
def display_cookie():
    session_str = ''
    for k in session.keys():
        session_str += k + ' = ' + str(session[k]) + '<br>'

    return session_str            


#
# Scratch space - Use this route for testing code
#
@app.route("/zane/test", defaults = { 'arg1': None, 'arg2': None })
@app.route("/zane/test/<arg1>", defaults = { 'arg2': None })
@app.route("/zane/test/<arg1>/<arg2>")
def dev_test(arg1, arg2):
    DEV_MODE = os.getenv('DEV_MODE')

    if DEV_MODE == '1':
        ### START TEST CODE
        
        # return str(request.environ)

        ip_address = mobile_flag = None
        if 'HTTP_X_FORWARDED_FOR' in request.environ:
            ip_address = request.environ['HTTP_X_FORWARDED_FOR']
        elif 'REMOTE_ADDR' in request.environ:
            ip_address = request.environ['REMOTE_ADDR']

        if 'HTTP_SEC_CH_UA_MOBILE' in request.environ:
            mobile_flag = request.environ['HTTP_SEC_CH_UA_MOBILE'][1]

        # return ip_address + ' ' + str(request.user_agent) + ' ' + str(mobile_flag)

        s = ''
        for k in request.environ:
            s += k + '=' + str(request.environ[k]) + '<br>'

        return s

        ### END TEST CODE
        pass

    return "This route is not available in Production"
