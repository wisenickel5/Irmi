from flask import request, session, redirect, render_template, make_response
from time import time
import logging

import config
from irmi.authenticate import get_token, create_state_key, CredentialManager
from irmi.services import get_user_information, get_recommendations
from irmi import app


@app.route('/')
@app.route('/index')
def index():
    return render_template('/index.html')


@app.route('/authorize')
def authorize():
    """
    This feature activates when, the user decides to not allow
    the app to use their account and the page redirects them to the account
    page.
    """
    client_id = CredentialManager().gcp_secrets['client_id']
    redirect_uri = config.REDIRECT_URI
    scope = config.SCOPE

    # State key used to protect against cross-site forgery attacks
    state_key = create_state_key(15)
    session['state_key'] = state_key

    # Redirect user to Spotify authorization page
    authorize_url = 'https://accounts.spotify.com/en/authorize?'
    parameters = 'client_id=' + client_id + '&response_type=code' + '&redirect_uri=' + redirect_uri + \
                 '&scope=' + scope + '&state=' + state_key
    response = make_response(redirect(authorize_url + parameters))

    return response


@app.route('/callback')
def callback():
    # make sure the response came from Spotify
    if request.args.get('state') != session['state_key']:
        raise RuntimeWarning('State failed.')
    if request.args.get('error'):
        raise RuntimeWarning('Spotify error.')
    else:
        code = request.args.get('code')
        session.pop('state_key', None)

        # get access token to make requests on behalf of the user
        payload = get_token(code)
        # app.logger.info(f'(Callback) Payload: {payload}')
        if payload is not None:
            session['token'] = payload[0]
            session['refresh_token'] = payload[1]
            session['token_expiration'] = time() + payload[2]
        else:
            raise RuntimeWarning('Failed to access token')

    current_user = get_user_information(session)
    session['user_id'] = current_user['id']
    logging.info('new user:' + session['user_id'])

    return redirect(session['previous_url'])


@app.route('/recommendations')
def recommendations():
    # make sure application is authorized for user
    if session.get('token') is None or session.get('token_expiration') is None:
        session['previous_url'] = '/tracks'
        return redirect('/authorize')

    # collect user information
    if session.get('user_id') is None:
        current_user = get_user_information(session)
        session['user_id'] = current_user['id']

    recommended_track_ids = get_recommendations(session)

    if recommended_track_ids is None:
        return render_template('index.html', error='Failed to get liked tracks')
    elif recommended_track_ids is not None:
        return render_template('recommendations.html', track_ids=recommended_track_ids)
