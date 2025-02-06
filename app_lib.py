#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#

#
# Library of helper functions
#
import os
from datetime import date, datetime, timedelta
from flask import flash
from openpyxl import Workbook

# Database helpers
import app_db

#
# Get end-user's IP address and browser information
#
def get_user_agent_details(request):
    ip_address = mobile_flag = None

    if 'HTTP_X_FORWARDED_FOR' in request.environ:
        ip_address = request.environ['HTTP_X_FORWARDED_FOR']
    elif 'REMOTE_ADDR' in request.environ:
        ip_address = request.environ['REMOTE_ADDR']

    if 'HTTP_SEC_CH_UA_MOBILE' in request.environ:
        mobile_flag = request.environ['HTTP_SEC_CH_UA_MOBILE'][1]

    return ip_address, str(request.user_agent), mobile_flag


#
# Use this function to validate that user is logged in before accessing a route.
#
def is_logged_in(session):
    if 'user_email' in session:
        # Check disabled
        query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE organization_id = ? AND email = ? AND disabled_flag = 1"
        if app_db.query_db(query, [session['organization_id'], session['user_email']])[0]['ROWCOUNT'] > 0:
            flash('Sorry, your account has been disabled.', 'danger')

            return False

        return True
    
    return False


#
# Use this function before giving access to admin routes
#
def is_user_admin(session):
    query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE organization_id = ? AND email = ? AND admin_flag = 1"
    if app_db.query_db(query, [session['organization_id'], session['user_email']])[0]['ROWCOUNT'] > 0:
        return True
    
    return False


#
# Use this function to validate that user's profile is complete before accessing a route
#
def is_profile_complete(session):
    # Profile is considered complete if Class of field is populated. What about Student ID?
    query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE organization_id = ? AND email = ? AND class_of IS NOT NULL"

    if app_db.query_db(query, [session['organization_id'], session['user_email']])[0]['ROWCOUNT'] > 0:
        return True
    
    return False


#
# Returns organization row factory
#
def get_organization_detail(organization_domain_root):
    query = """SELECT domain_root, name, short_name, logo, support_email, IFNULL(disabled_flag, 0) AS disabled_flag, organization_id
                FROM organization
                WHERE domain_root = ?
            """
    
    return app_db.query_db(query, [organization_domain_root])


#
# Update Session cookie with latest organization data from the database for use in templates
#
def update_organization_session_data(session):
    if 'organization_id' in session:
        query = "SELECT domain_root, name, short_name, logo, support_email, disabled_flag, organization_id FROM organization WHERE organization_id = ?"
        rv = app_db.query_db(query, [session['organization_id']])

        session['organization_name'] = rv[0]['name']
        session['organization_short_name'] = rv[0]['short_name']
        session['organization_logo'] = rv[0]['logo']
        session['organization_support_email'] = rv[0]['support_email']


#
# Return user class year name (Freshman, {class_year_name}, Junior, Senior)
#
def get_user_class_year_name(organization_id, user_email):
    query = """SELECT cy.name as class_year_name
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE
                u.organization_id = ? AND u.email = ?
            """
 
    class_year_name_rv = app_db.query_db(query, [organization_id, user_email])

    if len(class_year_name_rv) > 0:
        return class_year_name_rv[0]['class_year_name']
    
    return None


#
# Return available class years (for "Class of" drop-down)
#
def get_available_class_years(organization_id):
    query = "SELECT year_num, name FROM class_year WHERE organization_id = ? ORDER BY year_num"
    
    return app_db.query_db(query, [organization_id])


#
# Return available categories for a class year
#
def get_available_categories(organization_id, class_year_name):
    if class_year_name is None:
        return []

    query = f"""SELECT name, category_id, {class_year_name}_hours_required FROM category
                WHERE
                organization_id = ? AND {class_year_name}_visible_flag == 1
                ORDER BY display_order
            """

    return app_db.query_db(query, [organization_id])


#
# Given a date, returns period row factory
#
def get_period_by_date(organization_id, date):
    if date is None:
        return []

    query = """SELECT academic_year, name,
                CASE
                    WHEN start_date > datetime('now', 'localtime') THEN 2
                    ELSE locked_flag
                END AS locked_flag,
                no_required_hours_flag, period_id, start_date, end_date
                FROM period
                WHERE
                organization_id = ? AND ? BETWEEN start_date AND end_date
            """

    return app_db.query_db(query, [organization_id, date])

def get_period_by_id(organization_id, period_id):
    if period_id is None:
        return []

    query = """SELECT academic_year, name,
                CASE
                    WHEN start_date > datetime('now', 'localtime') THEN 2
                    ELSE locked_flag
                END AS locked_flag,
                no_required_hours_flag, period_id, start_date, end_date
                FROM period
                WHERE
                organization_id = ? AND period_id = ?
            """

    return app_db.query_db(query, [organization_id, period_id])

#
# Given a date, returns period row factory
#
def get_period_by_name(organization_id, period_name):
    if period_name is None:
        return []

    query = """SELECT academic_year, name, 
                CASE
                    WHEN start_date > datetime('now', 'localtime') THEN 2
                    ELSE locked_flag
                END AS locked_flag, 
                start_date, end_date, no_required_hours_flag, period_id
                FROM period
                WHERE
                organization_id = ? AND name = ?
            """

    return app_db.query_db(query, [organization_id, period_name])


#
# Get available periods row factory
#
def get_available_periods(organization_id):
    query = """SELECT name, academic_year, start_date, end_date, no_required_hours_flag, period_id,
                CASE
                    WHEN start_date > datetime('now', 'localtime') THEN 2
                    ELSE locked_flag
                END AS locked_flag
                FROM period
                WHERE
                organization_id = ?
                ORDER BY start_date DESC
            """

    return app_db.query_db(query, [organization_id])


#
# Returns earliest unlocked period row factory
#
def get_unlocked_period_details(organization_id):
    query = """SELECT name, academic_year, start_date, end_date, no_required_hours_flag, period_id
            FROM period
            WHERE
            organization_id = ? AND (locked_flag = 0 OR locked_flag IS NULL)
            ORDER BY start_date
            LIMIT 1
            """

    return app_db.query_db(query, [organization_id])


#
# Locks specified period
#
def lock_period(organization_id, period_id):
    query = "UPDATE period SET locked_flag = 1 WHERE organization_id = ? AND period_id = ?"

    return app_db.update_db(query, [organization_id, period_id])

def lock_period_update(organization_id, period_id):
    class_year_rv = get_available_class_years(organization_id)
    period_rv = get_period_by_id(organization_id, period_id)
    period_name = period_rv[0]['name']

    current_period_date = datetime.strptime(period_rv[0]['end_date'], "%Y-%m-%d").date()
    next_period_date = current_period_date + timedelta(days=1)

    next_period_rv = get_period_by_date(organization_id, next_period_date)
    next_period_year = next_period_rv[0]['academic_year']

    if period_rv[0]['academic_year'] < next_period_year:
        populate_class_year(organization_id, next_period_year)

    for cy in class_year_rv:
        ignore, users_cat_rv = get_users_category_hours(organization_id, cy['name'], period_name, user_limit=-1)

        for user_cat in users_cat_rv:
            carryover_hours = user_cat['hours_worked'] - user_cat['hours_required']
            if carryover_hours > 0:
                add_verification_log(user_cat['category_name'], next_period_date, carryover_hours, 'Surplus ' + str(user_cat['category_name']), None, None, None, None, None, organization_id, user_cat['user_email'], 2, None, None, None)
            if carryover_hours < 0:
                add_verification_log(user_cat['category_name'], next_period_date, carryover_hours, 'Deficit ' + str(user_cat['category_name']), None, None, None, None, None, organization_id, user_cat['user_email'], 2, None, None, None)
    
    lock_period(organization_id, period_id)


def populate_class_year(organization_id, academic_year):

    query = "DELETE FROM class_year WHERE year_num < ? AND organization_id = ?"
    app_db.update_db(query, [academic_year, organization_id])

    for i in range(4):
        insert_year_num = academic_year + i

        match i:
            case 0:
                class_year_name = 'Senior'
            case 1:
                class_year_name = 'Junior'
            case 2:
                class_year_name = 'Sophomore'
            case 3:
                class_year_name = 'Freshman'
            case _:
                class_year_name = None

        query = "UPDATE class_year SET name = ? WHERE organization_id = ? AND year_num = ?"
        if app_db.update_db(query, [class_year_name, organization_id, insert_year_num]) == 0:
            query = "INSERT OR IGNORE INTO class_year (organization_id, year_num, name) VALUES(?, ?, ?)"
            if app_db.update_db(query, [organization_id, insert_year_num, class_year_name]) == 1:
                print ("Insert class_year: organization_id=" + str(organization_id) + " year_num=" + str(insert_year_num) + " name=" + class_year_name)

#
# Given an email, returns user row factory
#
def get_user_profile(organization_id, user_email):
    if user_email is None:
        return []

    query = """SELECT u.app_user_id, u.email AS user_email, u.full_name, u.photo_url, u.school_id, u.team_name, u.class_of,
                IFNULL(u.admin_flag, 0) AS admin_flag, IFNULL(u.disabled_flag, 0) AS disabled_flag,
                IFNULL(u.super_user_flag, 0) AS super_user_flag, cy.name AS class_year_name,
                SUBSTR(u.email, 1, INSTR(u.email, '@') -1) AS user_email_prefix,
                CASE
                    WHEN INSTR(u.full_name, '(') THEN SUBSTR(u.full_name, 1, INSTR(u.full_name, '(') -2)
                    ELSE u.full_name
                END AS full_name_prefix
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE u.organization_id = ? AND u.email = ?"""

    return app_db.query_db(query, [organization_id, user_email])


#
# Add user profile
#
def add_user_profile(organization_id, user_email, full_name, photo_url):
    query = "INSERT INTO app_user (email, full_name, photo_url, organization_id, created_at) VALUES(?, ?, ?, ?, datetime('now', 'localtime'))"
    inserted_count = app_db.update_db(query, [user_email, full_name, photo_url, organization_id])

    return inserted_count


#
# Update user profile
#
def update_user_profile(organization_id, user_email, updated_by, class_of=None, school_id=None, team_name=None, admin_flag=None, disabled_flag=None, full_name=None, photo_url=None):

    ## Turn this function into taking **kwargs instead
    bindings = []
    query = "UPDATE app_user SET updated_at = datetime('now', 'localtime'), updated_by = ?"
    bindings.append(updated_by)

    if class_of is not None:
        query += ", class_of = ?"
        bindings.append(class_of)

    if school_id is not None:
        query += ", school_id = ?"        
        bindings.append(school_id)

    if team_name is not None:
        query += ", team_name = ?"
        bindings.append(team_name)

    if admin_flag is not None:
        query += ", admin_flag = ?"
        bindings.append(admin_flag)

    if disabled_flag is not None:
        query += ", disabled_flag = ?"
        bindings.append(disabled_flag)

    if full_name is not None:
        query += ", full_name = ?"
        bindings.append(full_name)

    if photo_url is not None:
        query += ", photo_url = ?"
        bindings.append(photo_url)

    query += " WHERE organization_id = ? AND email = ?"
    bindings.append(organization_id)
    bindings.append(user_email)

    updated_count = app_db.update_db(query, bindings)

    return updated_count


#
# Returns user profiles row factory matching the criteria
#
def get_user_profiles(organization_id, filter_name=None, filter_school_id=None, filter_class_year_name=None, filter_admin_flag=None, filter_disabled_flag=None, page_num=1, row_limit=5):
    query = """SELECT COUNT(*) AS ROWCOUNT
               FROM app_user u
               LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
               WHERE u.organization_id = ?"""

    query_where = ""
    bindings = [organization_id]

    if filter_name is not None and filter_name != '':
        query_where += " AND (u.full_name LIKE ? OR u.email LIKE ?)"
        bindings.append('%' + str(filter_name) + '%')
        bindings.append('%' + str(filter_name) + '%')

    if filter_school_id is not None:
        query_where += " AND u.school_id = ?"
        bindings.append(filter_school_id)

    if filter_class_year_name is not None:
        query_where += " AND cy.name = ?"
        bindings.append(filter_class_year_name)

    if filter_admin_flag is not None:
        query_where += " AND admin_flag = 1"

    if filter_disabled_flag is not None:
        query_where += " AND disabled_flag = 1"

    total_count = app_db.query_db(query + query_where, bindings)[0]['ROWCOUNT']

    query = """SELECT u.app_user_id, u.email AS user_email, u.full_name, u.photo_url, u.school_id, u.team_name, u.class_of,
                IFNULL(u.admin_flag, 0) AS admin_flag, IFNULL(u.disabled_flag, 0) AS disabled_flag,
                IFNULL(u.super_user_flag, 0) AS super_user_flag, cy.name AS class_year_name,
                SUBSTR(u.email, 1, INSTR(u.email, '@') -1) AS user_email_prefix,
                CASE
                    WHEN INSTR(u.full_name, '(') THEN SUBSTR(u.full_name, 1, INSTR(u.full_name, '(') -2)
                    ELSE u.full_name
                END AS full_name_prefix
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE u.organization_id = ?
            """

    query += query_where

    query += """ ORDER BY u.full_name ASC
                    LIMIT ? OFFSET ?
                """

    offset = (page_num - 1) * row_limit
    bindings.append(row_limit)
    bindings.append(offset)

    user_profiles_rv = app_db.query_db(query, bindings)

    return total_count, user_profiles_rv


#
# Returns verification_log row factory for user
#
def get_verification_logs(organization_id, user_email=None, filter_name=None, filter_category=None, filter_period=None, filter_min_hours=None, filter_max_hours=None, filter_school_id=None, filter_no_signature_flag=None, filter_no_location_flag=None, page_num=1, row_limit=5):
    query = """SELECT COUNT(*) AS ROWCOUNT
                FROM verification_log vl
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
                INNER JOIN category c ON c.category_id = vl.category_id
                INNER JOIN period p ON p.period_id = vl.period_id
                WHERE u.organization_id = ?
            """

    query_where = ""
    bindings = [organization_id]

    if user_email is not None:
        query_where += " AND u.email = ?"
        bindings.append(user_email)

    if filter_category is not None:
        query_where += " AND c.name = ?"
        bindings.append(filter_category)

    if filter_min_hours is not None:
        query_where += " AND vl.hours_worked >= ?"
        bindings.append(filter_min_hours)

    if filter_max_hours is not None:
        query_where += " AND vl.hours_worked <= ?"
        bindings.append(filter_max_hours)

    if filter_period is not None:
        query_where += " AND p.name = ?"
        bindings.append(filter_period)

    if filter_school_id is not None:
        query_where += " AND u.school_id = ?"
        bindings.append(filter_school_id)

    if filter_name != '':
        if filter_name is not None:
            query_where += " AND (u.full_name LIKE ? OR u.email LIKE ?)"
            bindings.append('%' + str(filter_name) + '%')
            bindings.append('%' + str(filter_name) + '%')

    if filter_no_signature_flag is not None:
        query_where += " AND vl.supervisor_signature IS NULL AND vl.signature_file IS NULL"

    if filter_no_location_flag is not None:
        query_where += " AND vl.location_coords IS NULL"

    total_count = app_db.query_db(query + query_where, bindings)[0]['ROWCOUNT']

    query = """SELECT c.name AS category_name, p.name AS period_name,
                u.email AS user_email, u.full_name,
                vl.event_name, vl.event_date, vl.event_supervisor, 
                vl.hours_worked, vl.supervisor_signature, vl.signature_file,
                vl.location_coords, vl.location_accuracy, vl.verification_log_id,
                vl.ip_address, vl.user_agent,
                CASE
                    WHEN INSTR(u.full_name, '(') THEN SUBSTR(u.full_name, 1, INSTR(u.full_name, '(') -2)
                    ELSE u.full_name
                END AS full_name_prefix,
                SUBSTR(u.email, 1, INSTR(u.email, '@') -1) AS user_email_prefix,
                IFNULL(vl.mobile_flag, 0) AS mobile_flag
                FROM verification_log vl
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
                INNER JOIN category c ON c.category_id = vl.category_id
                INNER JOIN period p ON p.period_id = vl.period_id
                WHERE u.organization_id = ?
            """

    query += query_where

    query += """ ORDER BY vl.verification_log_id DESC
                    LIMIT ? OFFSET ?
                """

    offset = (page_num - 1) * row_limit
    bindings.append(row_limit)
    bindings.append(offset)

    verification_log_rv = app_db.query_db(query, bindings)

    return total_count, verification_log_rv


#
# Returns specified verification_log row factory
#
def get_verification_log(verification_log_id, organization_id, user_email, is_admin):
    if verification_log_id is not None:
        query = """SELECT c.name AS category_name, p.name AS period_name, p.locked_flag,
                    vl.event_name, vl.event_date, vl.event_supervisor, 
                    vl.hours_worked, vl.supervisor_signature, vl.signature_file,
                    vl.location_coords, vl.location_accuracy, vl.verification_log_id,
                    vl.ip_address, vl.user_agent, IFNULL(vl.mobile_flag, 0) AS mobile_flag,
                    vl.created_at, vl.updated_at, cb.full_name AS created_by_name, cb.email AS created_by_email, ub.full_name AS updated_by_name,
                    vlu.email AS user_email, vlu.full_name
                    FROM verification_log vl
                    INNER JOIN category c ON c.category_id = vl.category_id
                    INNER JOIN period p ON p.period_id = vl.period_id
                    INNER JOIN app_user vlu ON vlu.app_user_id = vl.app_user_id
                    LEFT JOIN app_user cb ON cb.app_user_id = vl.created_by
                    LEFT JOIN app_user ub ON ub.app_user_id = vl.updated_by
                    WHERE vl.verification_log_id = ? AND vlu.organization_id = ?
                """

        bindings = [verification_log_id, organization_id]

    if is_admin == False:
        query += " AND vlu.email = ?"
        bindings.append(user_email)

    rv = app_db.query_db(query, bindings)

    if len(rv) <= 0:
        return []
    else:
        return rv

    return []


#
# Add verification_log
#
def add_verification_log(category_name, event_date, hours_worked, event_name, supervisor, pathdata, coords, coords_accuracy, signature_file,
                         orgnanization_id, user_email, created_by, ip_address, user_agent, mobile_flag):

    query = """SELECT COUNT(*) AS ROWCOUNT FROM verification_log vl
                INNER JOIN category c ON c.category_id = vl.category_id AND c.name = ?
                INNER JOIN app_user vlu ON vlu.app_user_id = vl.app_user_id AND vlu.organization_id = ? AND vlu.email = ?
                WHERE
                vl.event_date = ? AND hours_worked = ? AND event_name = ?
            """

    total_count = app_db.query_db(query, [category_name, orgnanization_id, user_email, event_date, hours_worked, event_name])[0]['ROWCOUNT']

    if total_count > 0:
        return False

    query = """INSERT OR IGNORE INTO verification_log
                (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, location_accuracy, signature_file,
                category_id, app_user_id, period_id, created_at, updated_at, created_by, updated_by, ip_address, user_agent, mobile_flag)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id, datetime('now', 'localtime'), datetime('now', 'localtime'),
                ?, ?, ?, ?, ?
                FROM app_user u
                LEFT JOIN period p on p.organization_id = u.organization_id AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN category c on c.organization_id = u.organization_id and c.name = ?
                WHERE u.organization_id = ? AND u.email = ?
            """

    insert_count = app_db.update_db(query, [event_name, event_date, supervisor, hours_worked, pathdata, coords, coords_accuracy, signature_file,
                                            created_by, created_by, ip_address, user_agent, mobile_flag,
                                            event_date, category_name, orgnanization_id, user_email])

    if insert_count == 1:
        return True

    return False

#
# Delete from verification_log
#
def delete_verification_log(verification_log_id, organization_id, user_email, is_admin):

    rv = get_verification_log(verification_log_id, organization_id, user_email, is_admin)

    if len(rv) <= 0:
        return (False, 'You are not authorized to delete Log ID ' + str(verification_log_id))
    
    print(str(rv[0]['created_by_email']))
    
    if rv[0]['created_by_email'] != user_email and is_admin == False:
        return (False, 'You are not authorized to delete system generated logs')

    if rv[0]['locked_flag'] == 1:
        return (False, 'You cannot delete logs from a locked period')

    query = "DELETE FROM verification_log WHERE verification_log_id = ?"

    delete_count = app_db.update_db(query, [verification_log_id])  

    if delete_count == 1:
        return (True, None)

    return (False, 'Deleted ' + str(delete_count) + ' verification logs')

#
# Update verification_log. Note Delete log is not allowed. Just set the Hours worked to 0 instead.
#
def update_verification_log(verification_log_id, organization_id, updated_by, event_name=None, event_date=None, event_supervisor=None, hours_worked=None,  event_category=None):

    query = """UPDATE verification_log
                SET updated_by = ?, updated_at=datetime('now', 'localtime')
            """

    bindings = [updated_by]

    if event_name is not None:
        query += ', event_name = ?'
        bindings.append(event_name)

    if event_date is not None:
        query += ', event_date = ?'
        bindings.append(event_date)

        query += ', period_id = (SELECT p.period_id FROM period p WHERE p.organization_id = ? AND ? BETWEEN p.start_date AND p.end_date)'
        bindings.append(organization_id)
        bindings.append(event_date)

    if event_supervisor is not None:
        query += ', event_supervisor = ?'
        bindings.append(event_supervisor)

    if hours_worked is not None:
        query += ', hours_worked = ?'
        bindings.append(hours_worked)

    if event_category is not None:
        query += ', category_id = (SELECT c.category_id FROM category c WHERE c.organization_id = ? AND c.name = ?)'
        bindings.append(organization_id)
        bindings.append(event_category)

    query += " WHERE verification_log_id = ?"
    bindings.append(verification_log_id)

    update_count = app_db.update_db(query, bindings)

    if update_count == 1:
        return True
    
    return False


#
# Transfer hours from one category to another
#
def transfer_user_hours(organization_id, user_email, created_by, transfer_hours, from_category, to_category, to_period_start_date, ip_address, user_agent, mobile_flag):
    
    transfer_removal = -1 * float(transfer_hours)

    add_verification_log(from_category, to_period_start_date, transfer_removal, f'Transfer to {to_category}', 'NHS App',
                            None, None, None, None, organization_id, user_email, created_by, ip_address, user_agent, mobile_flag)
    add_verification_log(to_category, to_period_start_date, transfer_hours, f'Transfer from {from_category}', 'NHS App',
                            None, None, None, None, organization_id, user_email, created_by, ip_address, user_agent, mobile_flag)


#
# Return user hours summary by category for given period, including Total Hours
#
def get_user_category_hours(date, class_year_name, organization_id, filter_name=None, filter_school_id=None, row_limit=25, offset=0):
    # Total count
    query = f"""SELECT COUNT(DISTINCT u.app_user_id) AS ROWCOUNT
                FROM app_user u
                INNER JOIN class_year cy ON cy.organization_id = u.organization_id AND cy.year_num = u.class_of
                WHERE
                (u.disabled_flag is null OR u.disabled_flag = 0) AND u.organization_id = ? AND cy.name = ?
            """

    total_count = app_db.query_db(query, [organization_id, class_year_name])[0]['ROWCOUNT']

    if total_count <= 0:
        return 0, 0, 0, []

    # Category hours_worked/hours_required for given user
    query = f"""SELECT c.name AS category_name, IFNULL(SUM(vl.hours_worked), 0) AS hours_worked, COUNT(vl.verification_log_id) AS log_count,
                SUBSTR(u.email, 1, INSTR(u.email, '@') -1) AS user_email_prefix, u.class_of, u.school_id, u.disabled_flag,
                CASE
                    WHEN p.no_required_hours_flag == 1 THEN 0
                    ELSE c.{class_year_name}_hours_required
                END AS hours_required,
                CASE
                    WHEN INSTR(u.full_name, '(') THEN SUBSTR(u.full_name, 1, INSTR(u.full_name, '(') -2)
                    ELSE u.full_name
                END AS full_name_prefix,
                u.email AS user_email, u.full_name, u.school_id, u.app_user_id, p.name AS period_name
                FROM category c
                LEFT JOIN app_user u ON u.organization_id = c.organization_id AND (u.disabled_flag is null OR u.disabled_flag = 0)
                LEFT JOIN class_year cy ON cy.organization_id = c.organization_id AND cy.year_num = u.class_of
                LEFT JOIN period p ON p.organization_id = c.organization_id AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN verification_log vl ON vl.category_id = c.category_id AND vl.app_user_id = u.app_user_id AND vl.period_id = p.period_id
                WHERE
                c.{class_year_name}_visible_flag = 1 AND c.organization_id = ? AND cy.name = ?
            """

    bindings = [date, organization_id, class_year_name]

    if filter_name is not None:
        query += " AND (u.email LIKE ? OR u.full_name LIKE ?)"
        bindings.append('%' + str(filter_name) + '%')
        bindings.append('%' + str(filter_name) + '%')

    if filter_school_id is not None:
        query += " AND u.school_id = ?"
        bindings.append(filter_school_id)

    query += f""" GROUP BY u.email, c.name, c.{class_year_name}_hours_required
                ORDER BY u.full_name, u.email, c.display_order
                LIMIT ? OFFSET ?
            """

    bindings.append(row_limit)
    bindings.append(offset)

    user_categories_rv = app_db.query_db(query, bindings)

    # Calculate total hours as sum of category hours
    total_hours_required = total_hours_worked = 0
    for row in user_categories_rv:
        total_hours_required += row['hours_required']
        total_hours_worked += row['hours_worked']

    return total_count, total_hours_required, total_hours_worked, user_categories_rv


#
# Downlaod users hours as XLSX file
#
def download_user_category_hours(filter_period_name, filter_class_year_name, user_hours_rv, category_rv, download_folder):
    filename = filter_class_year_name + '_' + filter_period_name

    wb = Workbook()
    ws = wb.active
    ws.title = filename

    # Populate headers
    row = ['Student Name', 'School ID']
    for cat in category_rv:
        row.append(cat['name'])

    ws.append(row)

    # Populate data
    row = []
    i = 0
    for uh in user_hours_rv:
        i = i + 1

        if i == 1:
            row.append(uh['full_name_prefix'])
            row.append(uh['school_id'])
        
        row.append(uh['hours_worked'])

        if i == len(category_rv):
            ws.append(row)
            i = 0
            row = []
    
    wb.save(os.path.join(download_folder, filename + '.xlsx'))

    return filename + '.xlsx'


#
# Return hours summary by category for given period for ALL users
#
def get_users_category_hours(organization_id, class_year_name, period_name, filter_name=None, filter_school_id=None, page_num=1, user_limit=5):
    categories_count = len(get_available_categories(organization_id, class_year_name))

    period_rv = get_period_by_name(organization_id, period_name)

    row_limit = user_limit * categories_count
    offset = (page_num - 1) * row_limit

    user_cat_count, total_hours_required, total_hours_worked, user_categories_rv = get_user_category_hours(period_rv[0]['start_date'], class_year_name, organization_id,
                                                                                                           filter_name=filter_name, filter_school_id=filter_school_id,
                                                                                                           row_limit=row_limit, offset=offset)

    return user_cat_count, user_categories_rv


#
# Calculate user medals
#
def calculate_user_medals(organization_id):
    # Delete existing medals of type P(eriod) and M(onth)
    delete_user_medals(organization_id, 'P')
    delete_user_medals(organization_id, 'M')

    unlocked_period_rv = get_unlocked_period_details(organization_id)

    if len(unlocked_period_rv) < 0:
        print("calculate_user_medals: Could not determine unlocked period.")
        return

    category_rv = get_available_categories(organization_id, 'sophomore')
    class_year_rv = get_available_class_years(organization_id)

    # Medals by Category for the current unlocked Period by Class Year
    for cat in category_rv:
        for year in class_year_rv:
            # Get user hours for category ordered by hours_worked descending
            query = """SELECT SUM(vl.hours_worked) AS [hours_worked], u.app_user_id, u.full_name, u.email AS [user_email]
                        FROM verification_log vl
                        INNER JOIN category c ON c.category_id = vl.category_id AND c.organization_id = ? AND c.name = ?
                        INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.class_of = ?
                        WHERE
                        vl.period_id = ?
                        GROUP BY u.app_user_id
                        ORDER BY 1 DESC
                    """

            bindings = [organization_id, cat['name'], year['year_num'], unlocked_period_rv[0]['period_id']]

            rankings_rv = app_db.query_db(query, bindings)

            if (year['name'] == 'Sophomore'):
                class_year_name = 'Soph'
            else:
                class_year_name = year['name']

            add_medals_from_rankings(organization_id, f"{class_year_name} {cat['name']}", 'P', rankings_rv)

    # Medals by Category for the current unlocked Period
    for cat in category_rv:
        # Get user hours for category ordered by hours_worked descending
        query = """SELECT SUM(vl.hours_worked) AS [hours_worked], u.app_user_id, u.full_name, u.email AS [user_email] FROM verification_log vl
                    INNER JOIN category c ON c.category_id = vl.category_id AND c.organization_id = ? AND c.name = ?
                    INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ?
                    WHERE
                    vl.period_id = ?
                    GROUP BY u.app_user_id
                    ORDER BY 1 DESC
                """

        bindings = [organization_id, cat['name'], organization_id, unlocked_period_rv[0]['period_id']]

        rankings_rv = app_db.query_db(query, bindings)

        add_medals_from_rankings(organization_id, cat['name'], 'P', rankings_rv)

    # Subtract one day from the first day of the current month to get the last day of the previous month
    current_month_first_day = date.today().replace(day=1)
    last_month_last_day = current_month_first_day - timedelta(days=1)

    # Get the first day of the previous month
    last_month_first_day = last_month_last_day.replace(day=1)

    # Medals for previous calendar month
    query = """SELECT SUM(vl.hours_worked) AS [hours_worked], u.app_user_id, u.full_name, u.email AS [user_email] FROM verification_log vl
                    INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ?
                    WHERE
                    vl.event_date >= ? AND vl.event_date < ?
                    GROUP BY u.app_user_id
                    ORDER BY 1 DESC
                """

    bindings = [organization_id, last_month_first_day, current_month_first_day]

    rankings_rv = app_db.query_db(query, bindings)

    add_medals_from_rankings(organization_id, last_month_first_day.strftime('%b'), 'M', rankings_rv)

    # Medals for previous calendar month by Class Year
    for year in class_year_rv:
        # Medals for previous calendar month
        query = """SELECT SUM(vl.hours_worked) AS [hours_worked], u.app_user_id, u.full_name, u.email AS [user_email] FROM verification_log vl
                        INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ? AND u.class_of = ?
                        WHERE
                        vl.event_date >= ? AND vl.event_date < ?
                        GROUP BY u.app_user_id
                        ORDER BY 1 DESC
                    """

        bindings = [organization_id, year['year_num'], last_month_first_day, current_month_first_day]

        rankings_rv = app_db.query_db(query, bindings)

        if (year['name'] == 'Sophomore'):
            class_year_name = 'Soph'
        else:
            class_year_name = year['name']

        add_medals_from_rankings(organization_id, f"{class_year_name} {last_month_first_day.strftime('%b')}", 'M', rankings_rv)


def add_medals_from_rankings(organization_id, medal_name, group_code, rankings_rv):
    current_rank = 0
    previous_hours = 999999
    for r in (rankings_rv):
        # Determine rank
        if r['hours_worked'] < previous_hours:
            current_rank += 1
            # Only award medals up to rank 10, if it's at the end it doesn't award ties
            if current_rank >= 11:
                return
            previous_hours = r['hours_worked']

        # Medals
        match current_rank:
            case 1:
                suffix = 'st'
            case 2:
                suffix = 'nd'
            case 3:
                suffix = 'rd'
            case _:
                suffix = 'th'
        
        add_user_medal(organization_id,
            r['user_email'],
            f"{current_rank}{suffix} {medal_name}",
            # P(eriod) or M(onth)
            group_code,
            # Zero-padded rank - 08, 09, 10, so string sorting works
            f'{current_rank:02}' 
        )   

        
#
# Returns user's medals, if any
#
def get_user_medals(organization_id, user_email, group_code=None):
    query = """SELECT m.name, m.group_code, m.type_code FROM app_user_medal m
                INNER JOIN app_user u ON u.app_user_id = m.app_user_id
                WHERE
                u.organization_id = ? AND u.email = ?
            """

    bindings = [organization_id, user_email]

    if group_code is not None:
        query += " AND m.group_code = ?"
        bindings.append(group_code)

    query += " ORDER BY m.type_code, m.name"

    return app_db.query_db(query, bindings)


#
# Returns user's medals, if any
#
def get_users_medals(organization_id, group_code=None):
    query = """SELECT m.name, m.group_code, m.type_code, u.app_user_id
                FROM app_user_medal m
                INNER JOIN app_user u ON u.app_user_id = m.app_user_id
                WHERE
                u.organization_id = ?
            """

    bindings = [organization_id]

    if group_code is not None:
        query += " AND group_code = ?"
        bindings.append(group_code)

    query += " ORDER BY m.type_code"

    return app_db.query_db(query, bindings)


#
# Delete user medals of a particular grouping (Period, Monthly, etc)
#
def delete_user_medals(organization_id, group_code=None):
    query = """DELETE FROM app_user_medal
                WHERE app_user_id IN (
                    SELECT um.app_user_id
                    FROM app_user_medal um
                    INNER JOIN app_user u ON u.app_user_id = um.app_user_id
                    WHERE u.organization_id = ?
                )
            """
    bindings = [organization_id]

    if group_code is not None:
        query += " AND group_code = ?"
        bindings.append(group_code)

    return app_db.update_db(query, bindings)
    

#
# Add user medal
#
def add_user_medal(organization_id, user_email, name, group_code, type_code):
    query = """INSERT OR IGNORE INTO app_user_medal
                (name, group_code, type_code, app_user_id)
                SELECT ?, ?, ?, u.app_user_id FROM app_user u
                WHERE
                u.organization_id = ? AND u.email = ?
            """

    return app_db.update_db(query, [name, group_code, type_code, organization_id, user_email])
    

#
# Turns empty string to None
#
def empty_to_none(text):
    if text == '':
        return None
    
    return text
