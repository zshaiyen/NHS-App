#
# Library of helper functions
#
from datetime import date

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
# Use this function to validate that user is logged in before accessing a route
#
def is_logged_in(session):
    if 'user_email' in session:
        # Check disabled
        query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE email = ? AND disabled_flag = 1"
        if app_db.query_db(query, [session['user_email']])[0]['ROWCOUNT'] > 0:
            # User is disabled
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
    query = "SELECT domain_root, name, short_name, logo, support_email, disabled_flag, organization_id FROM organization WHERE domain_root = ?"
    rv = app_db.query_db(query, [organization_domain_root])

    if len(rv) > 0:
        return rv
    
    return None


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
    rv = app_db.query_db(query, [organization_id, user_email])

    if len(rv) > 0:
        return rv[0]['class_year_name']
    
    return None


#
# Return available class years (for "Class of" drop-down)
#
def get_available_class_years(organization_id):
    query = "SELECT year_num, name FROM class_year WHERE organization_id = ? ORDER BY year_num"
    rv = app_db.query_db(query, [organization_id])

    if len(rv) > 0:
        return rv

    return None


#
# Return available categories for a class year
#
def get_available_categories(organization_id, class_year_name):
    if class_year_name is None:
        return None

    query = f"""SELECT name, category_id FROM category
                WHERE
                organization_id = ? AND {class_year_name}_visible_flag == 1
                ORDER BY display_order
            """
    rv = app_db.query_db(query, [organization_id])

    if len(rv) > 0:
        return rv

    return None


#
# Given a date, returns period row factory
#
def get_period_by_date(organization_id, date):
    if date is None:
        return None

    query = """SELECT academic_year, name, locked_flag, period_id FROM period
                WHERE
                organization_id = ? AND ? BETWEEN start_date AND end_date
            """
    rv = app_db.query_db(query, [organization_id, date])

    if len(rv) > 0:
        return rv

    return None


#
# Given a date, returns period row factory
#
def get_user_profile(organization_id, user_email):
    if user_email is None:
        return None

    query = """SELECT u.app_user_id, u.email AS user_email, u.full_name, u.photo_url, u.school_id, u.team_name, u.class_of, u.admin_flag, u.disabled_flag, cy.name AS class_year_name
               FROM app_user u
               LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
               WHERE u.organization_id = ? AND u.email = ?"""
    rv = app_db.query_db(query, [organization_id, user_email])

    if len(rv) > 0:
        return rv

    return None


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
def get_user_profiles(organization_id, name_filter=None, school_id=None, class_filter=None, admin_flag=None, disabled_flag=None, page_num=1):
    query = """SELECT u.app_user_id, u.email AS user_email, u.full_name, u.photo_url, u.school_id, u.team_name, u.class_of, u.admin_flag, u.disabled_flag, cy.name AS class_year_name
               FROM app_user u
               LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
               WHERE u.organization_id = ?"""
    
    bindings = [organization_id]

    if name_filter is not '' or None:
        query += " AND u.full_name like ?"
        bindings.append('%' + str(name_filter) + '%')

    if school_id is not None:
        query += " AND u.school_id = ?"
        bindings.append(school_id)

    if class_filter is not None:
        query += " AND u.class_of = ?"
        bindings.append(class_filter)    

    if admin_flag is not None:
        query += " AND admin_flag = 1"

    if disabled_flag is not None:
        query += " AND disabled_flag = 1"

    rv = app_db.query_db(query, bindings)
    if len(rv) > 0:
        return rv

    return None


#
# Returns verification_log row factory for user
#
def get_verification_logs(organization_id, user_email, name_filter=None, category=None, min_hours=None, max_hours=None, page_num=1, row_limit=25):
    query = """SELECT COUNT(*) AS ROWCOUNT 
               FROM verification_log vl
               INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
               WHERE u.organization_id = ?
            """

    bindings = [organization_id]

    if user_email is not None:
        query += " AND u.email = ?"
        bindings.append(user_email)

    row_count_rv = app_db.query_db(query, bindings)

    total_count = row_count_rv[0]['ROWCOUNT']
    verification_log_rv = []

    if total_count > 0:
        query = """SELECT c.name AS category_name, p.name AS period_name,
                    u.email, u.full_name,
                    vl.event_name, vl.event_date, vl.event_supervisor, 
                    vl.hours_worked, vl.supervisor_signature, 
                    vl.location_coords, vl.location_accuracy, vl.verification_log_id
                   FROM verification_log vl
                   INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
                   INNER JOIN category c ON c.category_id = vl.category_id
                   INNER JOIN period p ON p.period_id = vl.period_id
                   WHERE u.organization_id = ?
                """

        bindings = [organization_id]

        if user_email is not None:
            query += " AND u.email = ?"
            bindings.append(user_email)

        if category is not None:
            query += " AND category_name = ?"
            bindings.append(category)

        if min_hours is not None:
            query += " AND vl.hours_worked >= ?"
            bindings.append(min_hours)

        if max_hours is not None:
            query += " AND vl.hours_worked <= ?"
            bindings.append(max_hours)

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
                    vl.ip_address, vl.user_agent,
                    CASE
                        WHEN vl.mobile_flag = 1 THEN 'Yes'
                        WHEN vl.mobile_flag = 0 THEN 'No'
                    END AS mobile_flag
                    FROM verification_log vl
                    INNER JOIN category c ON c.category_id = vl.category_id
                    INNER JOIN period p ON p.period_id = vl.period_id
                    WHERE vl.verification_log_id = ?
                """

        verification_log_rv = app_db.query_db(query, [verification_log_id])

        if len(verification_log_rv) > 0:
            return verification_log_rv

    return None


#
# Add verification_log
#
def add_verification_log(category_name, event_date, hours_worked, event_name, supervisor, pathdata, coords, coords_accuracy,
                         orgnanization_id, user_email, created_by, ip_address='', user_agent='', mobile_flag=''):

    ## INSERT verification_log and UPDATE to period_category_user should happen as a single transaction?

    query = """INSERT OR IGNORE INTO verification_log
                (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, location_accuracy,
                category_id, app_user_id, period_id, created_by, updated_by, ip_address, user_agent, mobile_flag)
                SELECT ?, ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id, ?, ?, ?, ?, ?
                FROM app_user u
                LEFT JOIN period p on p.organization_id = u.organization_id AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN category c on c.organization_id = u.organization_id and c.name = ?
                WHERE u.organization_id = ? AND u.email = ?
            """

    mobile_flag = None

    insert_count = app_db.update_db(query, [event_name, event_date, supervisor, hours_worked, pathdata, coords, coords_accuracy,
                                            created_by, created_by, ip_address, user_agent, mobile_flag,
                                            event_date, category_name, orgnanization_id, user_email])

    if insert_count == 1:
        return True

    return False


#
# Update verification_log. Note Delete log is not allowed. Just set the Hours worked to 0 instead.
#
def update_verification_log(verification_log_id, event_name, hours_worked, updated_by):
#def update_verification_log(verification_log_id, category_name, event_date, hours_worked, event_name, supervisor, orgnanization_id, user_email, updated_by)

    ## UPDATE verification_log and UPDATE to period_category_user should happen as a single transaction?

    query = """UPDATE verification_log
                SET event_name = ?, hours_worked = ?, updated_by = ?, updated_at=datetime('now', 'localtime')
                WHERE verification_log_id = ?
            """
    update_count = app_db.update_db(query, [event_name, hours_worked, updated_by, verification_log_id])

    if update_count == 1:
        return True
    
    return False


#
# Return user hours summary by category for given period, including Total Hours
#
def get_user_category_hours(date, class_year_name, organization_id, user_email):

    # Category hours_worked/hours_required for given user
    query = f"""SELECT c.name AS category_name, c.informational_only_flag, c.{class_year_name}_hours_required AS hours_required,
                IFNULL(SUM(vl.hours_worked), 0) AS hours_worked
                FROM category c
                LEFT JOIN period p ON p.organization_id = ? AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN app_user u ON u.organization_id = ? AND u.email = ?
                LEFT JOIN verification_log vl ON vl.category_id = c.category_id AND vl.period_id = p.period_id AND vl.app_user_id = u.app_user_id
                WHERE
                c.{class_year_name}_visible_flag = 1
                GROUP BY c.name, c.informational_only_flag, c.{class_year_name}_hours_required
                ORDER BY c.display_order;
            """

    user_categories_rv = app_db.query_db(query, [organization_id, date, organization_id, user_email])

    if user_categories_rv is None:
            return None

    # Calculate total hours as sum of category hours
    total_hours_required = total_hours_worked = 0
    for row in user_categories_rv:
            total_hours_required += row['hours_required']
            total_hours_worked += row['hours_worked']

    ## Also return informational hours? Like Senior Cord?

    return total_hours_required, total_hours_worked, user_categories_rv


#
# Return hours summary by category for given period for ALL users
#
def get_users_category_hours(organization_id, class_year_name, period_date=None, category_name=None):

    # Category hours_worked/hours_required for ALL users
    query = f"""SELECT u.email AS user_email, u.full_name, c.name AS category_name, c.informational_only_flag,
                c.{class_year_name}_hours_required AS hours_required, IFNULL(SUM(vl.hours_worked), 0) AS hours_worked
                FROM category c
                LEFT JOIN period p ON p.organization_id = ? AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN app_user u ON u.organization_id = ?
                LEFT JOIN verification_log vl ON vl.category_id = c.category_id AND vl.period_id = p.period_id AND vl.app_user_id = u.app_user_id
                WHERE
                c.{class_year_name}_visible_flag = 1
                GROUP BY u.email, c.name, c.informational_only_flag, c.{class_year_name}_hours_required
                ORDER BY u.email, c.display_order
            """

    users_categories_rv = app_db.query_db(query, [organization_id, period_date, organization_id])

    if users_categories_rv is None:
            return None

    ## Also return informational hours? Like Senior Cord?

    return users_categories_rv


#
# Update period_category_user 
#
# def update_user_category_hours(date, category_name, organization_id, user_email):
#     if date is None or category_name is None:
#          return None

#     # By Period/Category for user
#     query = """INSERT OR REPLACE INTO period_category_user (period_id, category_id, app_user_id, hours_worked)
#                 SELECT p.period_id, c.category_id, u.app_user_id, sum(vl.hours_worked) FROM verification_log vl
#                 INNER JOIN period p ON p.period_id = vl.period_id AND ? BETWEEN p.start_date AND p.end_date
#                 INNER JOIN category c ON c.category_id = vl.category_id AND c.name = ?
#                 INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ? AND u.email = ?
#                 group by p.period_id, c.category_id, u.app_user_id
#             """

#     update_count = app_db.update_db(query, [date, category_name, organization_id, user_email])

#     ## If Senior, add sum of surplus hours to special Senior Cord category? Or simply sum up on the fly instead?

#     return update_count
