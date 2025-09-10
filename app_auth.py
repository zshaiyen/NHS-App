#
# Zane Shaiyen, zaneshaiyen@gmail.com, 2024
#

#
# Methods related to Google OAuth2 
#
import os
from time import time
from flask import redirect, url_for, session, request, flash, g
from requests_oauthlib import OAuth2Session

from urllib.parse import urlparse, parse_qs
from re import findall
from dotenv import load_dotenv

# Other app helpers
import app_lib

# Load environment variables from .env
load_dotenv()

#
# OAuth configuration
#
AUTHORIZATION_BASE_URL = os.getenv('GOOGLE_AUTHORIZATION_BASE_URL')
TOKEN_URL = os.getenv('GOOGLE_TOKEN_URL')
SCOPE = ['profile', 'email']


#
# After successful OAuth2 dance, get information from Google profile. Saves email and name in
# Session. Saves email, name, and photo URL in database. Ensures email domain is authorized
# to access the app, as defined in .env file.
#
def userinfo():
    if 'oauth_token' in session:
        # Load Google configuration
        init_google_globals()

        if g.organization_id is None:
            return "Could not determine organization details for " + request.headers['HOST']

        EXTRA = { 'client_id': g.google_client_id, 'client_secret': g.google_client_secret }

        google = OAuth2Session(g.google_client_id, token=session['oauth_token'], auto_refresh_url=TOKEN_URL,
            auto_refresh_kwargs=EXTRA, token_updater=token_saver)

        user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

        if 'email' in user_info:
            # user_info['email'] must be allowed domain
            email_domain = findall(r'@([A-Za-z0-9.-]+\.*)$', user_info['email'])

            ALLOWED_DOMAINS = [d.strip().lower() for d in g.allowed_domains.split(',') if d]

            if (len(email_domain) > 0):
                if email_domain[0] not in ALLOWED_DOMAINS:
                    flash("@" + str(email_domain[0]) + " emails are not authorized to sign in to this application.", 'danger')

                    return redirect(url_for('signon'))

            session['user_email'] = user_info['email']
        else:
            flash("Could not get email information from Google.", 'danger')

            return redirect(url_for('sigon'))

        if 'name' in user_info:
            session['full_name'] = user_info['name']
        else:
            session['full_name'] = None

        if 'picture' not in user_info:
            user_info['picture'] = url_for('static', filename='img/no-photo.png')

        # Add or update data from Google profile to the database
        if app_lib.update_user_profile(session['organization_id'], user_info['email'], None, full_name=user_info['name'], photo_url=user_info['picture']) == 0:
            inserted_count = app_lib.add_user_profile(session['organization_id'], user_info['email'], user_info['name'], user_info['picture'])

            if inserted_count == 0:
                flash("Could not add " + user_info['email'] + " to database", 'danger')
                
                return redirect(url_for('signon'))

        if 'user_id' not in session:
            user_rv = app_lib.get_user_profile(session['organization_id'], user_info['email'])

            if user_rv is not None:
                session['user_id'] = user_rv[0]['app_user_id']

        # Remove unnecessary items from the session cookie
        if 'oauth_state' in session:
            session.pop('oauth_state')

        if 'oauth_token' in session:
            session.pop('oauth_token')

        if 'id_token' in session:
            session.pop('id_token')

        return redirect(url_for('home'))

    return redirect(url_for('signon'))


#
# OAuth2 authorization.
#
def login():
    # Load Google configuration
    init_google_globals()

    if g.organization_id is None:
        return "Could not determine organization details for " + request.headers['HOST']

    session['organization_id'] = g.organization_id

    google = OAuth2Session(g.google_client_id, redirect_uri=g.google_redirect_uri, scope=SCOPE)
    authorization_url, state = google.authorization_url(AUTHORIZATION_BASE_URL, access_type='offline', prompt='select_account')
    session['oauth_state'] = state
    return redirect(authorization_url)


#
# OAuth2 callback from Google. Saves token to Session.
#
def callback():
    init_google_globals()

    if g.organization_id is None:
        return "Could not determine organization details for " + request.headers['HOST']

    google = OAuth2Session(g.google_client_id, state=session['oauth_state'], redirect_uri=g.google_redirect_uri)

    # Handle access_denied by user on consent screen
    if 'error' in parse_qs(urlparse(request.url).query):
        flash('Google consent screen failure: ' + str(parse_qs(urlparse(request.url).query)['error']), 'danger')

        return redirect(url_for('signon'))

    token = google.fetch_token(TOKEN_URL, client_secret=g.google_client_secret, authorization_response=request.url)
    session['oauth_token'] = token

    return redirect(url_for('userinfo'))


#
# Logout from the app. Clears Session cookie.
#
def logout():
    session.clear()
    return redirect(url_for('signon'))


#
# Save OAuth2 token to Session
#
def token_saver(token):
    session['oauth_token'] = token

#
# Get Google configuration data for organization
#
def init_google_globals():
    organization_rv = app_lib.get_organization_detail(request.headers['Host'])

    if len(organization_rv) <= 0:
        g.organization_id = None
        g.google_client_id = None
        g.google_client_secret = None
        g.google_redirect_uri = None
        g.allowed_domains = None

    else:
        org = organization_rv[0]
        g.organization_id = org['organization_id']
        g.google_client_id = org['google_client_id']
        g.google_client_secret = org['google_client_secret']
        g.google_redirect_uri = org['google_redirect_uri']
        g.allowed_domains = org['allowed_domains']
