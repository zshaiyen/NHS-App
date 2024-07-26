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
# Given a date, returns period row factory
#
def get_period_by_date(organization_id, date):
    if date is None:
        return None

    query = f"""SELECT academic_year, name, locked_flag, period_id FROM period
                WHERE
                organization_id = ? AND '{date}' BETWEEN start_date AND end_date
            """
    rv = app_db.query_db(query, [organization_id])

    if len(rv) > 0:
        return rv

    return None


#
# Update period_category_user 
#
def update_user_category_hours(date, category_name, organization_id, user_email):
    if date is None or category_name is None:
         return None

    # By Period/Category for user
    query = f"""INSERT OR REPLACE INTO period_category_user (period_id, category_id, app_user_id, hours_worked)
                SELECT p.period_id, c.category_id, u.app_user_id, sum(vl.hours_worked) FROM verification_log vl
                INNER JOIN period p ON p.period_id = vl.period_id AND '{date}' BETWEEN p.start_date AND p.end_date
                INNER JOIN category c ON c.category_id = vl.category_id AND c.name = ?
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id AND u.organization_id = ? AND u.email = ?
                group by p.period_id, c.category_id, u.app_user_id
            """

    update1 = app_db.update_db(query, [category_name, organization_id, user_email])

    ## If Senior, add sum of surplus hours to special Senior Cord category?

    return update1

#
# Return user hours summary by category for given period
#
def get_user_category_hours(date, class_year_name, organization_id, user_email):
        # Category hours worked / hours required for user for the period
        query = f"""SELECT c.name AS category_name, c.{class_year_name}_hours_required AS hours_required, IFNULL(pcu.hours_worked, 0) AS hours_worked, c.informational_only_flag FROM category c
                    LEFT JOIN app_user u ON u.organization_id = c.organization_id AND u.email = ?
                    LEFT JOIN period p ON p.organization_id = c.organization_id AND '{date}' BETWEEN start_date AND end_date
                    LEFT JOIN period_category_user pcu ON pcu.period_id = p.period_id AND pcu.category_id = c.category_id AND pcu.app_user_id = u.app_user_id
                    WHERE
                    c.organization_id = ? AND c.{class_year_name}_visible_flag == 1
                    ORDER BY c.display_order
                """
        user_categories_rv = app_db.query_db(query, [user_email, organization_id])

        return user_categories_rv


#
# Return user total hours for period
#
def get_user_total_hours(date, class_year_name, organization_id, user_email):
        # Category hours worked / hours required for user for the period
        query = f"""SELECT SUM(c.{class_year_name}_hours_required) AS hours_required, IFNULL(pcu.hours_worked, 0) AS hours_worked FROM category c
                    LEFT JOIN app_user u ON u.organization_id = c.organization_id AND u.email = ?
                    LEFT JOIN period p ON p.organization_id = c.organization_id AND '{date}' BETWEEN start_date AND end_date
                    LEFT JOIN period_category_user pcu ON pcu.period_id = p.period_id AND pcu.app_user_id = u.app_user_id AND pcu.category_id = 0
                    WHERE
                    c.organization_id = ? AND c.{class_year_name}_visible_flag == 1
                """
        user_categories_rv = app_db.query_db(query, [user_email, organization_id])

        if len(user_categories_rv) > 0:
             return user_categories_rv[0]['hours_required'], user_categories_rv[0]['hours_worked']

        return None


#
# Returns verification_log row factory for user. By default, returns 50 most recent rows.
#
def get_verification_logs(user_email, row_limit=50):
    query = f"""SELECT c.name AS category_name, p.name AS period_name, vl.event_name, vl.event_date, vl.event_supervisor, vl.hours_worked, vl.supervisor_signature, vl.location_coords, vl.verification_log_id
                FROM verification_log vl
                INNER JOIN app_user u ON u.app_user_id = vl.app_user_id
                INNER JOIN category c ON c.category_id = vl.category_id
                INNER JOIN period p ON p.period_id = vl.period_id
                WHERE u.email = ?
                ORDER BY verification_log_id DESC
                LIMIT {row_limit}
            """

    verification_log_rv = app_db.query_db(query, [user_email])

    return verification_log_rv