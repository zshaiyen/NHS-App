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
client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
authorization_base_url = os.getenv('GOOGLE_AUTHORIZATION_BASE_URL')
token_url = os.getenv('GOOGLE_TOKEN_URL')
redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
scope = ['profile', 'email']
extra = { 'client_id': client_id, 'client_secret': client_secret }
allowed_domains = os.getenv('ALLOWED_DOMAINS')

# Save token to session
def token_saver(token):
    # save token in database / session
    session['oauth_token'] = token


def userinfo():
    if 'oauth_token' in session:
        #google = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope, token=session['oauth_token'])
        #session['oauth_token']['expires_in'] = -10
        #session['oauth_token']['expires_at'] = time() - 10

        google = OAuth2Session(client_id, token=session['oauth_token'], auto_refresh_url=token_url,
            auto_refresh_kwargs=extra, token_updater=token_saver)

        user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

        if 'email' in user_info:
            # user_info['email'] must be allowed domain
            email_domain = findall('@([A-Za-z0-9.-]+\.*)$', user_info['email'])
            if (len(email_domain) > 0):
                if email_domain[0] not in allowed_domains:
                    return redirect('/logout')

            session['user_email'] = user_info['email']
        else:
            session['user_email'] = ''

        if 'name' in user_info:
           session['full_name'] = user_info['name']
        else:
           session['full_name'] = ''
        
        if 'picture' in user_info:
            session['picture'] = user_info['picture']
        else:
            session['picture'] = '/static/img/no-photo.png'

        return redirect('/home')

    return redirect('/login')


def login():
    google = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = google.authorization_url(authorization_base_url, access_type='offline', prompt='select_account')
    session['oauth_state'] = state
    return redirect(authorization_url)


def callback():
    google = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri)

    # Handle access_denied by user
    if 'error' in parse_qs(urlparse(request.url).query):
        flash(parse_qs(urlparse(request.url).query)['error'])
        return redirect('/')

    token = google.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
    session['oauth_token'] = token
    return redirect(url_for('.userinfo'))


def logout():
    #session.pop('oauth_token', None)
    session.clear()
    return redirect('/')

def is_logged_in():
    if 'oauth_token' in session:
        return True
    
    return False