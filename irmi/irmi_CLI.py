import numpy as np
from flask import request, session, redirect, render_template, make_response
from time import time
import logging

import config
from irmi.authenticate import get_token, create_state_key, CredentialManager
from irmi.services import get_user_information, get_recommendations, get_liked_track_ids
from irmi import app, SVCA


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

    current_user = get_user_information(session)
    session['user_id'] = current_user['id']
    logging.info('new user:' + session['user_id'])

    return redirect(session['previous_url'])

def get_taste_vector(taste_data):
    taste_vector = list()
    for i in range(0, taste_data.shape[1]):
        taste_vector.append(np.mean(taste_data[:, i]))
    return taste_vector


def create_set_of_good_songs(taste_data):
    taste_vector = list()
    for i in range(0, len(taste_data)):
        taste_vector.append([taste_data[i], 0])
    return taste_vector


def create_set_of_bad_songs(taste_data):
    taste_vector = list()
    for i in range(0, len(taste_data)):
        taste_vector.append([taste_data[i], 1])
    return taste_vector


def create_set_of_potential(data,URIS, W):
    vector = list()
    songs_uri=list()
    for i in range(0, len(data)):
        if SVCA.prediction(SVCA.calc_Wx(W, np.array(data[i]))) == 0:
            vector.append(data[i])
            songs_uri.append(URIS[i])
    return vector,songs_uri


def get_playlist_data(playlist_URI, Nlist,sp):
    Matrix = []
    Mlist = list()
    for track in sp.playlist_items(playlist_URI)["items"]:
        # URI
        track_uri = track["track"]["uri"]
        Mlist.append(sp.audio_features(track_uri)[0])
        # Track name
        track_name = track["track"]["name"]

        # Main Artist
        artist_uri = track["track"]["artists"][0]["uri"]
        artist_info = sp.artist(artist_uri)

        # Name, popularity, genre
        artist_name = track["track"]["artists"][0]["name"]
        artist_pop = artist_info["popularity"]
        artist_genres = artist_info["genres"]

        # Album
        album = track["track"]["album"]["name"]

        # Popularity of the track
        track_pop = track["track"]["popularity"]

    for i in range(0, len(Mlist)):
        Nlist.append(list(Mlist[i].values())[:9])
    return Nlist


def get_user_data(data,sp):
    Mlist = list()
    Nlist = list()
    URIS=list()
    for i in range(0, len(data)):
        # URI
        track_uri = data[i]["track"]["uri"]
        Mlist.append([sp.audio_features(track_uri)[0], track_uri])
        URIS.append(track_uri)
    for i in range(0, len(Mlist)):
        Nlist.append(list(Mlist[i][0].values())[:9])
    return Nlist,URIS
@app.route('/recommendations')
def recommendations():
    # Authorization flow for user
    if session.get('token') is None or session.get('token_expiration') is None:
        session['previous_url'] = '/index'
        return redirect('/authorize')

    # Collect user information
    if session.get('user_id') is None:
        current_user = get_user_information(session)
        session['user_id'] = current_user['id']

    # TODO: Get recommended tracks. Placing user's liked tracks for now as a placeholder
    # recommended_track_ids = get_recommendations(session)
    recommended_track_ids = get_liked_track_ids(session)

    if recommended_track_ids is None:
        return render_template('index.html', error='Failed to get liked tracks')
    elif recommended_track_ids is not None:
        return render_template('recommendations.html', track_ids=recommended_track_ids)
