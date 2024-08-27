#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#

#
# This script should run at 1am PT nightly on the server (quick and dirty).
# OR This script should run at 1am PT only on dates in period.start_date (efficient)
#

from datetime import datetime, date, timedelta
from flask import Flask, request
import app_db       # Database helpers
import app_lib      # Other helpers

#
# Add/delete available class years in class_year based on current period's academic year
#
def populate_class_year(organization_id):
    current_period_rv = app_lib.get_period_by_date(organization_id, date.today())

    if len(current_period_rv) <= 0:
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
#       Transfer surplus from prior period to current period by adding verification_log with postiive hours up to hours_required
# Lock prior period once transfers are done
#
# Notes from NHS website:
#
# Hours obtained over the summer will be capped at the max amount of hours you can obtain during the first school semester 
#     for your grade; hours will not be capped at this amount if you have an hour deficiency. If you have an hour deficiency, you will 
#     have to make up those hours during the summer or you will be removed from NHS.#
#
# SENIOR CORD category should show sum of surplus from other categories
# Seniors are required to complete a total of 10 additional hours in any category in 
#  order to receive the NHS senior cord at the end of the year. This log will be 
#  collected with your second semester verification logs at the end of the school year.




#
# Run nightly tasks
#

app = Flask(__name__)

with app.app_context():

    # Active organizations only
    query = "SELECT organization_id, short_name, name FROM organization WHERE (disabled_flag is null OR disabled_flag = 0)"
    org_rv = app_db.query_db(query)

    # Run tasks for each organization
    for org in (org_rv):
        print('********* ORG = ' + str(org['short_name']) + ' **********')
        populate_class_year(org['organization_id'])

        ### 
        ### IMPORTANT: CHANGE DATE TO TODAY FROM 2024-08-28
        ###
        current_period_rv = app_lib.get_period_by_date(org['organization_id'], '2024-08-28')

        if len(current_period_rv) <= 0:
            print('X Could not determine current unlocked period')
            continue

        current_period_date = datetime.strptime(current_period_rv[0]['start_date'], "%Y-%m-%d").date()
        prior_period_date = current_period_date - timedelta(days=1)

        print("Current date=" + str(current_period_rv[0]['start_date']))
        print("Prior date=" + str(prior_period_date))

        prior_period_rv = app_lib.get_period_by_date(org['organization_id'], prior_period_date)

        if len(prior_period_rv) <= 0:
            print('X Could not determine prior period for date ' + str(prior_period_date))
            continue
        
        if prior_period_rv[0]['locked_flag'] == 1:
            continue
        ## If prior period is already locked, continue

        class_year_rv = app_lib.get_available_class_years(org['organization_id'])

        for cy in class_year_rv:
            ignore, users_cat_rv = app_lib.get_users_category_hours(org['organization_id'], cy['name'], prior_period_rv[0]['name'], user_limit=-1)

            print('Class=' + str(cy['name']) + ' count=' + str(len(users_cat_rv)))

            for user_cat in users_cat_rv:
                print(str(user_cat['hours_worked']) + ' / ' + str(user_cat['hours_required']))
                carryover_hours = user_cat['hours_worked'] - user_cat['hours_required']
                if carryover_hours > 0:
                    app_lib.add_verification_log(user_cat['name'], date.today(), carryover_hours, 'Surplus from Prior Period', None, None, None, None, None, org['organization_id'], user_cat['email'], user_cat['full_name'], None, None, None)
                if carryover_hours < 0:
                    app_lib.add_verification_log(user_cat['name'], date.today(), carryover_hours, 'Deficit from Prior Period', None, None, None, None, None, org['organization_id'], user_cat['email'], user_cat['full_name'], None, None, None)
                ## Calculate hours_worked - hours_required
                ## Add surplus/deficit log, if necessary
        
        app_lib.lock_period(org['organization_id'], prior_period_rv['period_id'])
        ## Lock prior period