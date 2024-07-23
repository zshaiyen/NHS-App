#
# Methods related to Google OAuth2
#
import os
from time import time
from flask import redirect, url_for, session, request, flash
from requests_oauthlib import OAuth2Session

from urllib.parse import urlparse, parse_qs
from re import findall

import app_db

from dotenv import load_dotenv
load_dotenv()

# OAuth configuration
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
AUTHORIZATION_BASE_URL = os.getenv('GOOGLE_AUTHORIZATION_BASE_URL')
TOKEN_URL = os.getenv('GOOGLE_TOKEN_URL')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
SCOPE = ['profile', 'email']
EXTRA = { 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET }
ALLOWED_DOMAINS = os.getenv('ALLOWED_DOMAINS')


def userinfo():
    if 'oauth_token' in session:
        google = OAuth2Session(CLIENT_ID, token=session['oauth_token'], auto_refresh_url=TOKEN_URL,
            auto_refresh_kwargs=EXTRA, token_updater=token_saver)

        user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

        if 'email' in user_info:
            # user_info['email'] must be allowed domain
            email_domain = findall('@([A-Za-z0-9.-]+\.*)$', user_info['email'])
            if (len(email_domain) > 0):
                if email_domain[0] not in ALLOWED_DOMAINS:
                    return redirect(url_for('logout'))

            session['user_email'] = user_info['email']
        else:
            # Something went wrong and did not get email
            return redirect(url_for('logout'))

        if 'name' in user_info:
            session['full_name'] = user_info['name']
        else:
            session['full_name'] = None

        if 'picture' not in user_info:
            user_info['picture'] = url_for('static', filename='img/no-photo.png')

        # Add to app_user table
        query = "UPDATE app_user SET full_name = ?, photo_url = ? WHERE email = ?"
        if app_db.update_db(query, [user_info['name'], user_info['picture'], user_info['email']]) == 0:
            query = "INSERT INTO app_user (email, full_name, photo_url, organization_id) VALUES(?, ?, ?, ?)"
            app_db.update_db(query, [user_info['email'], user_info['name'], user_info['picture'], session['organization_id']])

        return redirect(url_for('home'))

    return redirect(url_for('login'))


def login():
    # Use request.headers['HOST'] again organization.app_domain to set session['organization_id'
    query = "SELECT organization_id FROM organization WHERE domain_root = ?"
    rv = app_db.query_db(query, [request.headers['HOST']])
    if (len(rv) <= 0):
        # Domain root not authorized
        return redirect(url_for('login'))
    else:
        session['organization_id'] = rv[0]['organization_id']

    google = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = google.authorization_url(AUTHORIZATION_BASE_URL, access_type='offline', prompt='select_account')
    session['oauth_state'] = state
    return redirect(authorization_url)


def callback():
    google = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=REDIRECT_URI)

    # Handle access_denied by user
    if 'error' in parse_qs(urlparse(request.url).query):
        flash(parse_qs(urlparse(request.url).query)['error'])
        return redirect(url_for('signon'))

    token = google.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    session['oauth_token'] = token
    return redirect(url_for('userinfo'))


def logout():
    session.clear()
    return redirect(url_for('signon'))


# Save token to session
def token_saver(token):
    # Save token in session
    session['oauth_token'] = token


def is_logged_in():
    if 'user_email' in session:
        return True
    
    return False


def is_profile_complete():
    # Check app_user.class_of and app_user.student_id are populated
    query = "SELECT COUNT(*) AS ROWCOUNT FROM app_user WHERE email = ? AND class_of IS NOT NULL"

    if app_db.query_db(query, [ session['user_email'] ])[0]['ROWCOUNT'] > 0:
        return True
    
    return False