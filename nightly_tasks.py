#
# This script should run at 1am PT nightly on the server (quick and dirty).
# OR This script should run at 1am PT only on dates in period.start_date (efficient)
#

from datetime import date
from flask import Flask, request
import app_db       # Database helpers
import app_lib      # Other helpers

#
# Add/delete available class years in class_year based on current period's academic year
#
def populate_class_year(organization_id):
    current_period_rv = app_lib.get_period_by_date(organization_id, date.today())

    if current_period_rv is None:
        return

    query = "DELETE FROM class_year WHERE year_num < ? AND organization_id = ?"
    app_db.update_db(query, [current_period_rv[0]['academic_year'], organization_id])

    for i in range(4):
        insert_year_num = current_period_rv[0]['academic_year'] + i

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
# Transfer hours automation algorithm
#
# Automatically run on first day of a new period (say, at 1am PT)
# Get current period
# If current period locked_flag = 1, then STOP
# Get prior period (-1 day from current period start_date)
# Get current class years that will be freshman, sophomore, junior, or senior (must run after populate_class_year)
# For each period_cat_user where user is now sophomore, junior, senior in current period
#   Transfer deficit from prior period to current period by adding verification_log with negative hours
#   If prior period academic year == current period academic year
#       Transfer surplus from prior period to current period by adding verification_log with postiive hours
#   Update user's period_category_user for prior period (if all went well, all hours_worked should now equal hours_required)
#   Update user's period_category_user for current period
#   
# Lock prior period once transfers are done



#
# Run nightly tasks
#

## Check to see if today is a date in period.start_date. Otherwise, exit.

app = Flask(__name__)

with app.app_context():

    # Active organizations only
    query = "SELECT organization_id FROM organization WHERE (disabled_flag is null OR disabled_flag = 0)"
    org_rv = app_db.query_db(query)

    # Run tasks for each organization
    for org in (org_rv):
        populate_class_year(org['organization_id'])

