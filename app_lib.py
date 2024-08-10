#
# Library of helper functions
#
from datetime import date
from flask import flash

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
        query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE email = ? AND disabled_flag = 1"
        if app_db.query_db(query, [session['user_email']])[0]['ROWCOUNT'] > 0:
            flash('Sorry, your account has been disabled.', 'danger')

            return False

        return True
    
    return False


#
# Use this function before giving access to admin routes
#
def is_user_admin(session):
    query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE email = ? AND admin_flag = 1"
    if app_db.query_db(query, [session['user_email']])[0]['ROWCOUNT'] > 0:
        return True
    
    return False


#
# Use this function to validate that user's profile is complete before accessing a route
#
def is_profile_complete(session):
    # Profile is considered complete if Class of field is populated. What about Student ID?
    query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE email = ? AND class_of IS NOT NULL"

    if app_db.query_db(query, [session['user_email']])[0]['ROWCOUNT'] > 0:
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
def get_available_categories(organization_id, class_year_name, exclude_informational=0):
    if class_year_name is None:
        return []

    query = f"""SELECT name, category_id FROM category
                WHERE
                organization_id = ? AND {class_year_name}_visible_flag == 1
            """
    
    if exclude_informational == 1:
        query += " AND (informational_only_flag IS NULL OR informational_only_flag == 0)"

    query += "ORDER BY display_order"

    return app_db.query_db(query, [organization_id])


#
# Given a date, returns period row factory
#
def get_period_by_date(organization_id, date):
    if date is None:
        return []

    query = """SELECT academic_year, name, IFNULL(locked_flag, 0) AS locked_flag, period_id
                FROM period
                WHERE
                organization_id = ? AND ? BETWEEN start_date AND end_date
            """

    return app_db.query_db(query, [organization_id, date])


#
# Given a date, returns period row factory
#
def get_period_details(organization_id, period_name):
    if period_name is None:
        return []

    query = """SELECT academic_year, name, IFNULL(locked_flag, 0) AS locked_flag, start_date, end_date, period_id
                FROM period
                WHERE
                organization_id = ? AND name = ?
            """

    return app_db.query_db(query, [organization_id, period_name])


#
# Get available periods row factory
#
def get_available_periods(organization_id):
    query = """SELECT name, academic_year, start_date, end_date, IFNULL(locked_flag, 0) AS locked_flag, period_id
                FROM period
                WHERE
                organization_id = ?
                ORDER BY start_date DESC
            """

    return app_db.query_db(query, [organization_id])


#
# Given an email, returns user row factory
#
def get_user_profile(organization_id, user_email):
    if user_email is None:
        return []

    query = """SELECT u.app_user_id, u.email AS user_email, u.full_name, u.photo_url, u.school_id, u.team_name, u.class_of,
                IFNULL(u.admin_flag, 0) AS admin_flag, IFNULL(u.disabled_flag, 0) AS disabled_flag,
                IFNULL(u.super_user_flag, 0) AS super_user_flag, cy.name AS class_year_name
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE u.organization_id = ? AND u.email = ?"""

    return app_db.query_db(query, [organization_id, user_email])


#
# Add user profile
#
def add_user_profile(organization_id, user_email, full_name, photo_url):
    query = "INSERT INTO app_user (email, full_name, photo_url, organization_id) VALUES(?, ?, ?, ?)"
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
def get_verification_logs(organization_id, user_email=None, filter_name=None, filter_category=None, filter_period=None, filter_min_hours=None, filter_max_hours=None, page_num=1, row_limit=5):
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

    if filter_name != '':
        if filter_name is not None:
            query_where += " AND (u.full_name LIKE ? OR u.email LIKE ?)"
            bindings.append('%' + str(filter_name) + '%')
            bindings.append('%' + str(filter_name) + '%')

    total_count = app_db.query_db(query + query_where, bindings)[0]['ROWCOUNT']

    query = """SELECT c.name AS category_name, p.name AS period_name,
                u.email AS user_email, u.full_name,
                vl.event_name, vl.event_date, vl.event_supervisor, 
                vl.hours_worked, vl.supervisor_signature,
                vl.location_coords, vl.location_accuracy, vl.verification_log_id,
                vl.ip_address, vl.user_agent,
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
def get_verification_log(verification_log_id):
    if verification_log_id is not None:
        query = """SELECT c.name AS category_name, p.name AS period_name,
                    vl.event_name, vl.event_date, vl.event_supervisor, 
                    vl.hours_worked, vl.supervisor_signature, 
                    vl.location_coords, vl.location_accuracy, vl.verification_log_id,
                    vl.ip_address, vl.user_agent, IFNULL(vl.mobile_flag, 0) AS mobile_flag,
                    vl.created_at, vl.updated_at, cb.full_name AS created_by_name, ub.full_name AS updated_by_name
                    FROM verification_log vl
                    INNER JOIN category c ON c.category_id = vl.category_id
                    INNER JOIN period p ON p.period_id = vl.period_id
                    LEFT JOIN app_user cb ON cb.app_user_id = vl.created_by
                    LEFT JOIN app_user ub ON ub.app_user_id = vl.updated_by
                    WHERE vl.verification_log_id = ?
                """

        return app_db.query_db(query, [verification_log_id])

    return []


#
# Add verification_log
#
def add_verification_log(category_name, event_date, hours_worked, event_name, supervisor, pathdata, coords, coords_accuracy,
                         orgnanization_id, user_email, created_by, ip_address, user_agent, mobile_flag):

    query = """INSERT OR IGNORE INTO verification_log
                (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, location_accuracy,
                category_id, app_user_id, period_id, created_at, updated_at, created_by, updated_by, ip_address, user_agent, mobile_flag)
                SELECT ?, ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id, datetime('now', 'localtime'), datetime('now', 'localtime'),
                ?, ?, ?, ?, ?
                FROM app_user u
                LEFT JOIN period p on p.organization_id = u.organization_id AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN category c on c.organization_id = u.organization_id and c.name = ?
                WHERE u.organization_id = ? AND u.email = ?
            """

    insert_count = app_db.update_db(query, [event_name, event_date, supervisor, hours_worked, pathdata, coords, coords_accuracy,
                                            created_by, created_by, ip_address, user_agent, mobile_flag,
                                            event_date, category_name, orgnanization_id, user_email])

    if insert_count == 1:
        return True

    return False


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


#Transfer hours using an api called transfer user hours, takes organization id, user email, transfer_hours, fromcategory, tocategory
def transfer_user_hours(organization_id, user_email, created_by, transfer_hours, from_category, to_category, to_period_start_date, ip_address, user_agent, mobile_flag):
    
    transfer_removal = -1 * float(transfer_hours)

    add_verification_log(from_category, to_period_start_date, transfer_removal, f'Transfer of Hours to {to_category}', 'NHS App',
                            None, None, None, organization_id, user_email, created_by, ip_address, user_agent, mobile_flag)
    add_verification_log(to_category, to_period_start_date, transfer_hours, f'Transfer of Hours from {from_category}', 'NHS App',
                            None, None, None, organization_id, user_email, created_by, ip_address, user_agent, mobile_flag)

#
# Return user hours summary by category for given period, including Total Hours
#
def get_user_category_hours(date, class_year_name, organization_id, filter_name=None, filter_school_id=None, row_limit=25, offset=0):
    # Total count
    query = f"""SELECT COUNT(DISTINCT u.app_user_id) AS ROWCOUNT
                FROM app_user u
                INNER JOIN class_year cy ON cy.organization_id = u.organization_id AND cy.year_num = u.class_of
                WHERE
                u.organization_id = ? AND cy.name = ?
            """

    total_count = app_db.query_db(query, [organization_id, class_year_name])[0]['ROWCOUNT']

    if total_count <= 0:
        return 0, 0, 0, []

    # Category hours_worked/hours_required for given user
    query = f"""SELECT c.name AS category_name, c.{class_year_name}_hours_required AS hours_required, IFNULL(SUM(vl.hours_worked), 0) AS hours_worked,
                COUNT(vl.verification_log_id) AS log_count, SUBSTR(u.email, 1, INSTR(u.email, '@') -1) AS user_email_prefix, u.class_of, u.school_id, u.disabled_flag,
                CASE
                    WHEN INSTR(u.full_name, '(') THEN SUBSTR(u.full_name, 1, INSTR(u.full_name, '(') -2)
                    ELSE u.full_name
                END AS full_name_prefix,
                u.email AS user_email, u.full_name, u.school_id, p.name AS period_name
                FROM category c
                LEFT JOIN app_user u ON u.organization_id = c.organization_id
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
# Return hours summary by category for given period for ALL users
#
def get_users_category_hours(organization_id, class_year_name, period_name, filter_name=None, filter_school_id=None, page_num=1, user_limit=5):
    categories_count = len(get_available_categories(organization_id, class_year_name))

    period_rv = get_period_details(organization_id, period_name)

    row_limit = user_limit * categories_count
    offset = (page_num - 1) * row_limit

    user_cat_count, total_hours_required, total_hours_worked, user_categories_rv = get_user_category_hours(period_rv[0]['start_date'], class_year_name, organization_id,
                                                                                                           filter_name=filter_name, filter_school_id=filter_school_id,
                                                                                                           row_limit=row_limit, offset=offset)

    return user_cat_count, user_categories_rv


#
# Turns empty string to None
#
def empty_to_none(text):
    if text == '':
        return None
    
    return text
