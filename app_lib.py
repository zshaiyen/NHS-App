#
# Library of helper functions
#
from datetime import date

# Database helpers
import app_db

#
# Return user class year name (Freshman, Sophomore, Junior, Senior)
def get_user_class_year_name(organization_id, user_email):
    query = """SELECT cy.name as class_year_name
                FROM app_user u
                LEFT JOIN class_year cy ON cy.year_num = u.class_of AND cy.organization_id = u.organization_id
                WHERE
                u.organization_id = ? AND u.email = ?
            """
    user_profile_rv = app_db.query_db(query, [organization_id, user_email])

    if len(user_profile_rv) > 0:
        return user_profile_rv[0]['class_year_name']
    
    return None


#
# Return available class years (for "Class of" drop-down)
#
def get_available_class_years(organization_id):
    query = "SELECT year_num FROM class_year WHERE organization_id = ?"
    rv = app_db.query_db(query, [organization_id])

    if len(rv) > 0:
        return rv

    return None


#
# Return available categories
#
def get_available_class_years(organization_id):
    query = "SELECT year_num FROM class_year WHERE organization_id = ?"
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
# Returns verification_log row factory for user. By default, returns 50 most recent rows.
#
def get_verification_logs(organization_id, user_email, name_filter=None, category=None, period=None, row_limit=50):
    bindings = []

    query = """SELECT c.name AS category_name, p.name AS period_name, vl.event_name, vl.event_date, vl.event_supervisor, vl.hours_worked, vl.supervisor_signature, vl.location_coords, vl.verification_log_id
                FROM verification_log vl
            """

    query += """INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
            """
    if name_filter:
        query += "AND (u.email like ? OR u.full_name like ?)"
        bindings.append(name_filter)
        bindings.append(name_filter)

    query += """INNER JOIN category c ON c.category_id = vl.category_id
            """
    if category:
        query += "AND c.name = ?"
        bindings.append(category)

    query += """INNER JOIN period p ON p.period_id = vl.period_id
            """
    if period:
        query += "AND p.name = ?"
        bindings.append(period)
    
    query += f"""WHERE u.organization_id = ? AND u.email = ?
                ORDER BY verification_log_id DESC
                LIMIT {row_limit}
            """
    bindings.append(organization_id)
    bindings.append(user_email)

    verification_log_rv = app_db.query_db(query, bindings)

    return verification_log_rv


#
# Add verification_log
#
def add_verification_log(category_name, event_date, hours_worked, event_name, supervisor, pathdata, coords, orgnanization_id, user_email, created_by):

    ## INSERT verification_log and UPDATE to period_category_user should happen as a single transaction?

    query = """INSERT OR IGNORE INTO verification_log
                (event_name, event_date, event_supervisor, hours_worked, supervisor_signature, location_coords, category_id, app_user_id, period_id, created_by, updated_by)
                SELECT ?, ?, ?, ?, ?, ?, c.category_id, u.app_user_id, p.period_id, ?, ? FROM app_user u
                LEFT JOIN period p on p.organization_id = u.organization_id AND ? BETWEEN p.start_date AND p.end_date
                LEFT JOIN category c on c.organization_id = u.organization_id and c.name = ?
                WHERE u.email = ? AND u.organization_id = ?
            """
    insert_count = app_db.update_db(query, [event_name, event_date, supervisor, hours_worked, pathdata, coords,
                                            event_date, category_name, user_email, orgnanization_id, created_by, created_by])

    if insert_count == 1:
        # Update summary table
        update_count = update_user_category_hours(event_date, category_name, orgnanization_id, user_email)
    
    if (insert_count + update_count) == 2:
        return True
    
    return False


#
# Update verification_log. Note Delete log is not allowed for audit purposes. Just set the Hours workd to 0 instead.
#
def update_verification_log(verification_log_id, date, category_name, hours_worked, organization_id, user_email, updated_by):

    ## UPDATE verification_log and UPDATE to period_category_user should happen as a single transaction?

    query = """UPDATE verification_log
                SET hours_worked = ?, updated_by = ?, updated_at=datetime()
                WHERE verification_log_id = ?
            """
    update_count = app_db.update_db(query, [hours_worked, updated_by, verification_log_id])

    if update_count >= 1:
        # Update user's period/category/hours summary
        update_user_category_hours(date, category_name, organization_id, user_email)

        return True
    
    return False


#
# Return user hours summary by category for given period, including Total Hours
#
def get_user_category_hours(date, class_year_name, organization_id, user_email):
        # Category hours worked / hours required for user for the period
        query = f"""SELECT c.name AS category_name, c.{class_year_name}_hours_required AS hours_required, IFNULL(pcu.hours_worked, 0) AS hours_worked, c.informational_only_flag FROM category c
                    LEFT JOIN period p ON p.organization_id = c.organization_id AND ? BETWEEN start_date AND end_date
                    LEFT JOIN app_user u ON u.organization_id = c.organization_id AND u.email = ?
                    LEFT JOIN period_category_user pcu ON pcu.period_id = p.period_id AND pcu.category_id = c.category_id AND pcu.app_user_id = u.app_user_id
                    WHERE
                    c.organization_id = ? AND c.{class_year_name}_visible_flag == 1
                    ORDER BY c.display_order
                """
        user_categories_rv = app_db.query_db(query, [date, user_email, organization_id])

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
# Update period_category_user 
#
def update_user_category_hours(date, category_name, organization_id, user_email):
    if date is None or category_name is None:
         return None

    # By Period/Category for user
    query = """INSERT OR REPLACE INTO period_category_user (period_id, category_id, app_user_id, hours_worked)
                SELECT p.period_id, c.category_id, u.app_user_id, sum(vl.hours_worked) FROM verification_log vl
                INNER JOIN period p ON p.period_id = vl.period_id AND ? BETWEEN p.start_date AND p.end_date
                INNER JOIN category c ON c.category_id = vl.category_id AND c.name = ?
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ? AND u.email = ?
                group by p.period_id, c.category_id, u.app_user_id
            """

    update_count = app_db.update_db(query, [date, category_name, organization_id, user_email])

    ## If Senior, add sum of surplus hours to special Senior Cord category? Or simply sum up on the fly instead?

    return update_count
