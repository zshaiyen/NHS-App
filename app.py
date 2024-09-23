#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#
# Main application with all routes
#

import os
import math
from datetime import date, timedelta, datetime
from flask import Flask, redirect, url_for, session, render_template, g, request, flash, send_file, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import app_auth     # Authentication helpers
import app_lib      # Other helpers


# Load environment variables from .env
load_dotenv()


#
# Flask
#
template_dir = os.getenv('TEMPLATE_DIR')
if template_dir:
    app = Flask(__name__, static_url_path='', template_folder=template_dir)
else:
    app = Flask(__name__, static_url_path='')

app.secret_key = os.getenv('SECRET_KEY')

# File upload (used for signature files)
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH'))
DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER')
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

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
    organization_rv = app_lib.get_organization_detail(request.headers['HOST'])

    if len(organization_rv) <= 0:
        return "Could not determine organization details for " + request.headers['HOST']

    app_lib.update_organization_session_data(session)

    if app_lib.is_logged_in(session):
        return redirect(url_for('home'))

    return render_template(
        "signon.html",
        organization=organization_rv
    )


# 
# Home (Dashboard)
#
@app.route("/home", methods=['GET','POST'])
def home():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))
    
    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    if class_year_name is None:
        flash('Unable to determine user class year name', 'danger')

        return redirect(url_for('profile'))

    # Get current unlocked period
    #current_period_rv = app_lib.get_unlocked_period_details(session['organization_id'])

    # Get period for today's date
    current_period_rv = app_lib.get_period_by_date(session['organization_id'], date.today())

    if len(current_period_rv) <= 0:
        flash('Unable to find current unlocked period')
        current_period_date = date.today()
        current_period_name = None
    else:
        current_period_date = current_period_rv[0]['start_date']
        current_period_name = current_period_rv[0]['name']

    user_cat_count, total_hours_required, total_hours_worked, user_categories_rv = app_lib.get_user_category_hours(current_period_date, class_year_name, session['organization_id'], session['user_email'])

    # Display last 3 verification logs for user
    total_count, verification_log_rv = app_lib.get_verification_logs(session['organization_id'], user_email=session['user_email'], row_limit=3)

    # User medals
    user_medals_rv = app_lib.get_user_medals(session['organization_id'], session['user_email'])

    return render_template(
        "home.html",
        logs = verification_log_rv,
        user_categories=user_categories_rv,
        user_medals=user_medals_rv,
        total_hours_required=total_hours_required,
        total_hours_worked=total_hours_worked,
        current_period_name=current_period_name,
        hide_add_flag=True,
        is_admin=is_admin
    )


#
# Add Verification Log
#
@app.route("/loghours", defaults = {'log_id': None}, methods = ['GET', 'POST'])
@app.route("/loghours/<int:log_id>", methods = ['GET', 'POST'])
def loghours(log_id):
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

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
        event_user_email = app_lib.empty_to_none(request.form.get('event_user_email', default=None))
        event_category = app_lib.empty_to_none(request.form.get('event_category', default=None))
        event_name = app_lib.empty_to_none(request.form.get('event_name', default=None))
        event_date = app_lib.empty_to_none(request.form.get('event_date', default=None))
        event_supervisor = app_lib.empty_to_none(request.form.get('event_supervisor', default=None))
        hours_worked = app_lib.empty_to_none(request.form.get('hours_worked', default=None))
        pathdata = app_lib.empty_to_none(request.form.get('pathdata', default=None))
        location_coords = app_lib.empty_to_none(request.form.get('coords', default=None))
        location_accuracy = app_lib.empty_to_none(request.form.get('coords_accuracy', default=None))

        # Uploaded signature file, if any
        if 'sig_file' in request.files:
            signature_file = request.files['sig_file']
        else:
            signature_file = None

        failed_validation = False

        if event_user_email is None or not is_admin:
            event_user_email = session['user_email']
        else:
            # Add suffix if not already there
            if str(event_user_email).find('@') < 0:
                event_user_email = str(event_user_email) + '@student.hbuhsd.edu'    ## This should come from organization instead?

            # Ensure email address is valid
            if len(app_lib.get_user_profile(session['organization_id'], event_user_email)) <= 0:
                flash(str(event_user_email) + ' is not a valid application user', 'danger')
                event_user_email = None
                failed_validation = True

        # Event date cannot be in the future
        if event_date and datetime.strptime(event_date, "%Y-%m-%d").date() > date.today():
            flash('Event Date cannot be in the future', 'danger')
            failed_validation = True
    
        period_rv = app_lib.get_period_by_date(session['organization_id'], event_date)
        if len(period_rv) <= 0:
            flash('Could not determine period for date ' + str(event_date), 'danger')
            failed_validation = True

        elif period_rv[0]['locked_flag'] == 1:
            flash('This event date falls in a locked period (' + str(period_rv[0]['name']) + '). You cannot enter verification logs for locked periods.', 'danger')
            failed_validation = True

        if failed_validation:
            return render_template("loghours.html",
                                        log_id=log_id,
                                        event_user_email=event_user_email,
                                        event_category=event_category,
                                        event_name=event_name,
                                        event_date=event_date,
                                        event_supervisor=event_supervisor,
                                        supervisor_signature=None,
                                        location_coords=location_coords,
                                        location_accuracy=location_accuracy,
                                        hours_worked=hours_worked,
                                        category_list=category_rv,
                                        is_admin=is_admin)

        # Update
        if log_id:
            if app_lib.update_verification_log(log_id, session['organization_id'], session['user_id'],
                                                event_name=event_name,
                                                event_date=event_date,
                                                event_supervisor=event_supervisor,
                                                hours_worked=hours_worked,
                                                event_category=event_category):

                flash('Updates to verification log saved successfully', 'success')

                return redirect(url_for('viewlogs'))

            else:
                flash('Failed to update verification log', 'danger')

                return render_template("loghours.html",
                                            log_id=log_id,
                                            event_user_email=event_user_email,
                                            event_category=event_category,
                                            event_name=event_name,
                                            event_date=event_date,
                                            event_supervisor=event_supervisor,
                                            hours_worked=hours_worked,
                                            category_list=category_rv,
                                            is_admin=is_admin)

        # Add
        else:
            signature_file_name = None

            # Save signature file
            if signature_file and signature_file.filename != '':
                if pathdata is not None:
                    flash("You cannot use both signature pad and uploaded signature. Please choose one option.", 'danger')

                    return render_template("loghours.html",
                                                log_id=log_id,
                                                event_user_email=event_user_email,
                                                event_category=event_category,
                                                event_name=event_name,
                                                event_date=event_date,
                                                event_supervisor=event_supervisor,
                                                supervisor_signature=None,
                                                location_coords=location_coords,
                                                location_accuracy=location_accuracy,
                                                hours_worked=hours_worked,
                                                category_list=category_rv,
                                                is_admin=is_admin)

                if not allowed_file(signature_file.filename):
                    flash("Allowed file extensions " + str(ALLOWED_EXTENSIONS), 'danger')

                    return render_template("loghours.html",
                                                log_id=log_id,
                                                event_user_email=event_user_email,
                                                event_category=event_category,
                                                event_name=event_name,
                                                event_date=event_date,
                                                event_supervisor=event_supervisor,
                                                supervisor_signature=None,
                                                location_coords=location_coords,
                                                location_accuracy=location_accuracy,
                                                hours_worked=hours_worked,
                                                category_list=category_rv,
                                                is_admin=is_admin)


                file_prefix = str(datetime.now()).replace(':','').replace('-','').replace('.','').replace(' ', '')
                signature_file_name = secure_filename(file_prefix + '_' + signature_file.filename)
                signature_file.save(os.path.join(app.config['UPLOAD_FOLDER'], signature_file_name))

            if app_lib.add_verification_log(event_category, event_date, hours_worked, event_name, event_supervisor, pathdata, location_coords, location_accuracy, signature_file_name,
                                            session['organization_id'], event_user_email, session['user_id'],
                                            ip_address, str(user_agent), mobile_flag):

                flash('Successfully added verification log', 'success')

                return redirect(url_for('viewlogs'))
            else:
                flash('Failed to add verification log', 'danger')

                return render_template("loghours.html",
                                            log_id=log_id,
                                            event_user_email=event_user_email,
                                            event_category=event_category,
                                            event_name=event_name,
                                            event_date=event_date,
                                            event_supervisor=event_supervisor,
                                            supervisor_signature=None,
                                            location_coords=location_coords,
                                            location_accuracy=location_accuracy,
                                            hours_worked=hours_worked,
                                            category_list=category_rv,
                                            is_admin=is_admin)
    
    if log_id:
        verification_log_rv = app_lib.get_verification_log(log_id)
        event_category = verification_log_rv[0]['category_name']
        event_name = verification_log_rv[0]['event_name']
        event_date = verification_log_rv[0]['event_date']
        event_supervisor = verification_log_rv[0]['event_supervisor']
        hours_worked = verification_log_rv[0]['hours_worked']
        supervisor_signature = verification_log_rv[0]['supervisor_signature']
        location_coords = verification_log_rv[0]['location_coords']
        location_accuracy = verification_log_rv[0]['location_accuracy']
        ip_address = verification_log_rv[0]['ip_address']
        user_agent = verification_log_rv[0]['user_agent']
        mobile_flag = verification_log_rv[0]['mobile_flag']
        created_at = verification_log_rv[0]['created_at']
        created_by_name = verification_log_rv[0]['created_by_name']
        updated_at = verification_log_rv[0]['updated_at']
        updated_by_name = verification_log_rv[0]['updated_by_name']
        signature_file_name = verification_log_rv[0]['signature_file']
        event_user_email = verification_log_rv[0]['user_email']

    else:
        event_name = event_supervisor = hours_worked = event_category = supervisor_signature = location_coords = location_accuracy = None
        ip_address = user_agent = mobile_flag = created_at = created_by_name = updated_at = updated_by_name = signature_file_name = None

        event_category = app_lib.empty_to_none(request.args.get('default_category'))
        event_date = date.today()
        event_user_email = session['user_email']

        if event_category == '':
            event_category = None

    return render_template("loghours.html",
                            log_id=log_id,
                            event_user_email=event_user_email,
                            event_category=event_category,
                            event_name=event_name,
                            event_date=event_date,
                            event_supervisor=event_supervisor,
                            supervisor_signature=supervisor_signature,
                            signature_file_name=signature_file_name,
                            location_coords=location_coords,
                            location_accuracy=location_accuracy,
                            hours_worked=hours_worked,
                            category_list=category_rv,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            mobile_flag=mobile_flag,
                            created_at=created_at,
                            created_by_name=created_by_name,
                            updated_at=updated_at,
                            updated_by_name=updated_by_name,
                            is_admin=is_admin
                            )


#
# View Verification Log 
#
@app.route("/viewlogs", methods=['GET','POST'])
def viewlogs():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    filter_category = app_lib.empty_to_none(request.args.get('filter_category', default=None, type=str))
    filter_period = app_lib.empty_to_none(request.args.get('filter_period', default=None, type=str))
    filter_min_hours = app_lib.empty_to_none(request.args.get('filter_min_hours', default=None, type=int))
    filter_max_hours = app_lib.empty_to_none(request.args.get('filter_max_hours', default=None, type=int))
    filter_school_id = app_lib.empty_to_none(request.args.get('filter_school_id', default=None, type=str))
    filter_no_signature_flag = app_lib.empty_to_none(request.args.get('filter_no_signature_flag', default=None))
    filter_no_location_flag = app_lib.empty_to_none(request.args.get('filter_no_location_flag', default=None))

    if request.method == 'GET':
        # Default current open period if GET-ing not filtering
        if filter_period is None:            
            current_period_rv = app_lib.get_unlocked_period_details(session['organization_id'])

            if len(current_period_rv) <= 0:
                filter_period = None
            else:
                filter_period = current_period_rv[0]['name']

    # Pagination
    page_num = app_lib.empty_to_none(request.args.get('p', default=1, type=int))
    rows_per_page = 10

    # Only admin can filter by name
    if is_admin:
        filter_name = app_lib.empty_to_none(request.args.get('filter_name', default=None, type=str))
        user_email = None
    else:
        user_email = session['user_email']
        filter_name = None

    total_count, verification_log_rv = app_lib.get_verification_logs(session['organization_id'],
                                                                     user_email=user_email,
                                                                     filter_category=filter_category,
                                                                     filter_min_hours=filter_min_hours,
                                                                     filter_max_hours=filter_max_hours,
                                                                     filter_name=filter_name,
                                                                     filter_period=filter_period,
                                                                     filter_no_location_flag=filter_no_location_flag,
                                                                     filter_no_signature_flag=filter_no_signature_flag,
                                                                     page_num=page_num,
                                                                     row_limit=rows_per_page,
                                                                     filter_school_id=filter_school_id
                                                                    )

    # Get user class year name (Freshman, Sophomore, Junior, Senior)
    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    # Use class_year_name to construct column name: Sophomore_visible_flag, Junior_visible_flag, etc.
    category_rv = app_lib.get_available_categories(session['organization_id'], class_year_name)

    period_rv = app_lib.get_available_periods(session['organization_id'])

    if len(category_rv) <= 0:
        flash('Unable to determine available categories', 'danger')

        return redirect(url_for('home'))

    # Pagination
    total_pages = math.ceil(total_count / rows_per_page)

    return render_template("viewlogs.html", 
                           logs=verification_log_rv,
                           total_count=total_count,
                           filter_category=filter_category,
                           filter_name=filter_name,
                           filter_period=filter_period,
                           filter_min_hours=filter_min_hours,
                           filter_max_hours=filter_max_hours,
                           filter_no_signature_flag=filter_no_signature_flag,
                           filter_no_location_flag=filter_no_location_flag,
                           category_list=category_rv,
                           period_list=period_rv,
                           is_admin=is_admin,
                           page_num=page_num,
                           total_pages=total_pages,
                           filter_school_id=filter_school_id
                           )


#
# User Category Hours
#
@app.route("/userhours", methods=['GET', 'POST'])
def userhours():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    is_admin = app_lib.is_user_admin(session)

    if not is_admin:
        flash('This functionality requires admin permissions', 'danger')

        return redirect(url_for('home'))

    app_lib.update_organization_session_data(session)

    # Filters
    filter_class_year_name = app_lib.empty_to_none(request.args.get('filter_class_year_name', default=None, type=str))
    filter_period = app_lib.empty_to_none(request.args.get('filter_period', default=None, type=str))
    filter_name = app_lib.empty_to_none(request.args.get('filter_name', default=None, type=str))
    filter_school_id = app_lib.empty_to_none(request.args.get('filter_school_id', default=None, type=str))
    download = app_lib.empty_to_none(request.args.get('download', default=None, type=int))

    if filter_class_year_name is None:
        filter_class_year_name = 'Sophomore'

    if filter_period is None:
        current_period_rv = app_lib.get_unlocked_period_details(session['organization_id'])

        if len(current_period_rv) <= 0:
            filter_period = None
        else:
            filter_period = current_period_rv[0]['name']

    # Pagination
    page_num = app_lib.empty_to_none(request.args.get('p', default=1, type=int))

    # If downloading, get all the data
    if download is not None and download == 1:
        rows_per_page = -1
    else:
        rows_per_page = 10

    total_rows, user_hours_rv = app_lib.get_users_category_hours(session['organization_id'], filter_class_year_name, filter_period, filter_name=filter_name,
                                                                 filter_school_id=filter_school_id, page_num=page_num, user_limit=rows_per_page)

    total_pages = math.ceil(total_rows / rows_per_page)

    period_rv = app_lib.get_available_periods(session['organization_id'])
    class_years_rv = app_lib.get_available_class_years(session['organization_id'])
    category_rv = app_lib.get_available_categories(session['organization_id'], filter_class_year_name)

    # Download requested
    if download is not None and download == 1:
        filename = app_lib.download_user_category_hours(filter_period, filter_class_year_name, user_hours_rv, category_rv, DOWNLOAD_FOLDER)

        return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True, download_name=filename)


    return render_template("userhours.html",
                           user_hours_rv=user_hours_rv,
                           total_count=total_rows,
                           filter_name=filter_name,
                           filter_period=filter_period,
                           filter_class_year_name=filter_class_year_name,
                           filter_school_id=filter_school_id,
                           period_list=period_rv,
                           class_years_rv=class_years_rv,
                           category_rv=category_rv,
                           is_admin=is_admin,
                           page_num=page_num,
                           total_pages=total_pages
                           )


#
# Transfer hours between two categories
#
@app.route("/transfer", methods=['GET','POST'])
def transfer():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    is_admin = app_lib.is_user_admin(session)

    app_lib.update_organization_session_data(session)

    class_year_name = app_lib.get_user_class_year_name(session['organization_id'], session['user_email'])

    category_rv = app_lib.get_available_categories(session['organization_id'], class_year_name)

    from_category = to_category = transfer_hours = None

    if request.method == 'POST':
        from_category = app_lib.empty_to_none(request.form.get('from_category'))
        to_category = app_lib.empty_to_none(request.form.get('to_category'))
        transfer_hours = app_lib.empty_to_none(request.form.get('transfer_hours'))

        ip_address, user_agent, mobile_flag = app_lib.get_user_agent_details(request)

        app_lib.transfer_user_hours(session['organization_id'], session['user_email'], session['user_id'], transfer_hours, from_category, to_category, date.today(), ip_address, user_agent, mobile_flag)
        flash('Hours transferred successfully', 'success')

        return redirect(url_for('home'))

    return render_template('transfer.html',
                            from_category=from_category,
                            to_category=to_category,
                            category_list=category_rv,
                            transfer_hours=transfer_hours,
                            is_admin=is_admin
    )


#
# User Profile
#
@app.route("/profile", defaults={'email': None, 'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>", defaults={'action': None}, methods=['GET', 'POST'])
@app.route("/profile/<email>/<action>", methods=['GET', 'POST'])
def profile(email, action):
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    app_lib.update_organization_session_data(session)

    is_admin = app_lib.is_user_admin(session)

    if email:
        if email == session['user_email'] and not action:
            return redirect(url_for('profile'))

        profile_email = email if is_admin else session['user_email']
    else:
        profile_email = session['user_email']

    if request.method == 'POST':
        class_of = app_lib.empty_to_none(request.form.get('class_of'))
        school_id = app_lib.empty_to_none(request.form.get('school_id'))
        team_name = app_lib.empty_to_none(request.form.get('team_name'))
        admin_flag = app_lib.empty_to_none(request.form.get('admin_flag'))
        disabled_flag = app_lib.empty_to_none(request.form.get('disabled_flag'))

        # Capture unchecked checkboxes from admin
        if is_admin:
            if admin_flag is None and profile_email != session['user_email']:
                admin_flag = 0

            if disabled_flag is None and profile_email != session['user_email']:
                disabled_flag = 0
        else:
            admin_flag = disabled_flag = None

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

#
# User Profiles
#
@app.route("/profiles")
def profiles():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    is_admin = app_lib.is_user_admin(session)

    if not is_admin:
        flash('This functionality requires admin permissions', 'danger')

        return redirect(url_for('home'))

    app_lib.update_organization_session_data(session)    

    filter_name = app_lib.empty_to_none(request.args.get('filter_name', default=None, type=str))
    filter_school_id = app_lib.empty_to_none(request.args.get('filter_school_id', default=None, type=str))
    filter_class_year_name = app_lib.empty_to_none(request.args.get('filter_class_year_name', default=None, type=str))
    filter_admin_flag = app_lib.empty_to_none(request.args.get('filter_admin_flag', default=None))
    filter_disabled_flag = app_lib.empty_to_none(request.args.get('filter_disabled_flag', default=None))

    page_num = app_lib.empty_to_none(request.args.get('p', default=1, type=int))
    rows_per_page = 16

    total_count, user_profiles_rv= app_lib.get_user_profiles(session['organization_id'],
                                                                     filter_name=filter_name,
                                                                     filter_school_id=filter_school_id,
                                                                     filter_class_year_name=filter_class_year_name,
                                                                     filter_admin_flag=filter_admin_flag,
                                                                     filter_disabled_flag=filter_disabled_flag,
                                                                     page_num=page_num,
                                                                     row_limit=rows_per_page
                                                                    )
    
    total_pages = math.ceil(total_count / rows_per_page)
    class_years_rv = app_lib.get_available_class_years(session['organization_id'])

    return render_template('profiles.html',
                            user_profiles=user_profiles_rv,
                            class_years_rv=class_years_rv,
                            filter_name=filter_name,
                            filter_school_id=filter_school_id,
                            filter_class_year_name=filter_class_year_name,
                            filter_admin_flag=filter_admin_flag,
                            filter_disabled_flag=filter_disabled_flag,
                            is_admin=is_admin,
                            total_count=total_count,
                            page_num=page_num,
                            total_pages=total_pages
    )


#
# View Periods 
#
@app.route('/periods')
def periods():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    if not app_lib.is_profile_complete(session):
        return redirect(url_for('profile'))

    is_admin = app_lib.is_user_admin(session)

    app_lib.update_organization_session_data(session)

    periods_rv = app_lib.get_available_periods(session['organization_id'])

    return render_template("periods.html",
                           periods_rv=periods_rv,
                           is_admin=is_admin
                           )


#
# Contact Us
#
@app.route("/contact")
def contact():
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

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
# Organization profile
#
@app.route('/organization')
def organization_profile():
    is_admin = app_lib.is_user_admin(session)

    if not is_admin:
        flash('This functionality requires admin permissions', 'danger')

        return redirect(url_for('home'))

    organization_rv = app_lib.get_organization_detail(request.headers['HOST'])
    return render_template("organization.html",
                           organization_rv=organization_rv,
                           is_admin=is_admin
                           )


#
# Remote database backup
#
@app.route("/remotebackup", methods=['POST'])
def remote_backup():
    if app_lib.empty_to_none(request.form.get('secret', default=None)) == app.secret_key:
        backup_prefix = app_lib.empty_to_none(request.form.get('backup_prefix', default=None))

        if backup_prefix is None:
            backup_prefix = 'backup'

        backup_name = backup_prefix + '_' + datetime.now().strftime('%Y%m%d%H%M') + '.db'

        return send_file(os.getenv('APP_DATABASE'), as_attachment=True, download_name=backup_name)

    return redirect(url_for('home'))


#
# Serve uploaded signatures
#
@app.route("/sigs/<path:filename>")
def serve_sig(filename):
    if not app_lib.is_logged_in(session):
        return redirect(url_for('signon'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


#
# Health check
#
@app.route("/healthcheck")
def health_check():
    org_rv = app_lib.get_organization_detail(request.headers['HOST'])

    # 200 - OK
    if len(org_rv) > 1:
        return ""

    # 503 - Service Unavailable
    return str(request.headers['HOST']), 503


#
# Debug - Display/Update Session cookie contents
#
@app.route("/zane/cookie")
def display_cookie():
    session_str = ''
    if 'secret' in request.args.keys() and request.args.get('secret') == app.secret_key:
        for q in request.args.keys():
            if q != 'secret':
                val = str(request.args.get(q))
                if val == '':
                    session.pop(q, None)
                else:
                    session[q] = val
    else:
        session_str = 'NO SECRET<br>'

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
        
        ### END TEST CODE
        pass

    return "This route is not available in Production"


#
# Allowed extensions for file uploadds
#
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#
# HTTP 413 - Upload file size too large
#
@app.errorhandler(413)
def request_entity_too_large(error):
    flash('Uploaded file cannot be larger than ' + str(MAX_CONTENT_LENGTH) + 'MB', 'danger')

    return redirect('loghours')
