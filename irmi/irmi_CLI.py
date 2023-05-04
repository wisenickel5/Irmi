from flask import request, session, redirect, render_template, make_response
from time import time
import logging

import config
from irmi.authenticate import get_token, create_state_key, CredentialManager
import irmi.services as sv
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
    client_id = CredentialManager.instance().gcp_secrets['client_id']
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

        # Get access token to make requests on behalf of the user
        payload = get_token(code)
        if payload is not None:
            session['token'] = payload[0]
            session['refresh_token'] = payload[1]
            session['token_expiration'] = time() + payload[2]
        else:
            raise RuntimeWarning('Failed to access token')

    current_user = sv.get_user_information(session)
    session['user_id'] = current_user['id']
    logging.info('new user:' + session['user_id'])

    return redirect(session['previous_url'])


@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    # Authorization flow for user
    if session.get('token') is None or session.get('token_expiration') is None:
        session['previous_url'] = '/index'
        return redirect('/authorize')

    # Collect user information
    if session.get('user_id') is None:
        current_user = sv.get_user_information(session)
        session['user_id'] = current_user['id']

    mood = request.form.get('mood')

    # TODO: Get recommended tracks. Placing user's liked tracks for now as a placeholder
    # recommended_track_ids = get_recommendations(session,mood)
    recommended_track_ids = sv.get_liked_track_ids(session)
    top_genres = sv.get_user_top_genres(session)

    if recommended_track_ids and top_genres:
        # Group the tracks based on the users most listened to genres
        grouped_recommended_tracks = sv.group_tracks_by_genre(session, recommended_track_ids, top_genres)
    else:
        logging.error('Failed to get top genres and recommended tracks!')
        return render_template('index.html')

    if grouped_recommended_tracks is None:
        logging.error('Failed to group recommendations')
        return render_template('index.html')

    elif grouped_recommended_tracks is not None:
        return render_template('recommendations.html', track_ids=grouped_recommended_tracks)