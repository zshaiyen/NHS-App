#
# Library of helper functions
#
from datetime import date

# Database helpers
import app_db


#
# Given a date, returns period row factory
#
def get_period_by_date(date):
    if date is None:
        return None

    query = """SELECT academic_year, name, period_id FROM period
                WHERE
                start_date <= ?
                ORDER BY start_date DESC
                LIMIT 1
            """
    rv = app_db.query_db(query, [date])

    if (len(rv) > 0):
        return rv

    return None


#
# Returns Freshman, Sophomore, etc, depening on class_of and current period
#
def get_class_year_name(class_of):
    if class_of is None:
        return ''
    
    rv = get_period_by_date(date.today())
    if rv is not None:
        diff = int(class_of) - rv[0]['academic_year']

        match diff:
            case 0:
                return "Senior"
            case 1:
                return "Junior"
            case 2:
                return "Sophomore"
            case 3:
                return "Freshman"

    return ''
