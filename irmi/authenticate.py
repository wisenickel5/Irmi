from flask import current_app
import requests
from time import time
import logging


def get_token(code):
    """Requests an access token from Spotify API. This function is only called if
    the current user does not have a refresh token.

    Args:
        code (string): Value returned from HTTP GET Request

    Returns:
        tuple(str, str, str) : Access Token, Refresh Token, Expiration Time
    """
    grant_type = current_app.config['GRANT_TYPE']
    redirect_uri = current_app.config['REDIRECT_URI']
    client_id = current_app.config['CLIENT_ID']
    client_secret = current_app.config['CLIENT_SECRET']
    token_url = current_app.config['TOKEN_URL']
    request_body = {
        "grant_type": grant_type,
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    post_request = requests.post(url=token_url, data=request_body)
    p_response = post_request.json()

    # Log POST Response output in terminal
    current_app.logger.debug(f"\n\nCurrent code {code}")
    current_app.logger.debug(f'\n\n(getToken) Post Response Status Code -> {post_request.status_code}')
    current_app.logger.debug(f'\n\nPost Response Formatted -> {post_request}\n\n')

    if post_request.status_code == 200:
        return p_response['access_token'], p_response['refresh_token'], p_response['expires_in']
    else:
        logging.error('getToken: ' + str(post_request.status_code))
        return None


def refresh_token(token):
    """
    POST Request is made to Spotify API with refresh token (only if access token and
    refresh token were previously acquired) creating a new access token

    Args:
        token (string)

    Returns:
        tuple(str, str): Access Token, Expiration Time
    """
    token_url = 'https://accounts.spotify.com/api/token'
    authorization = current_app.config['AUTHORIZATION']

    headers = {'Authorization': authorization, 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    body = {'refresh_token': token, 'grant_type': 'refresh_token'}
    post_response = requests.post(token_url, headers=headers, data=body)

    # 200 code indicates access token was properly granted
    if post_response.status_code == 200:
        token = post_response.json()['access_token']
        exp_time = post_response.json()['expires_in']
        current_app.logger.info(f"Refresh Token: {token}\nExpiration time: {exp_time}")
        return token, exp_time
    else:
        logging.error('refreshToken:' + str(post_response.status_code))
        return None


def check_token_status(session):
    """Determines if the new access token must be requested based on time expiration
    of previous token.

    Args:
        session (Session): Flask Session Object

    Returns:
        string: Success log
    """
    payload = None
    if time() > session['token_expiration']:
        payload = refresh_token(session['refresh_token'])

    if payload is not None:
        session['token'] = payload[0]
        session['token_expiration'] = time() + payload[1]
    else:
        logging.error('checkTokenStatus')
        return None
    return "Success"


def make_get_request(session, url, params=None):
    """
    Recursively make GET Request to Spotify API with necessary headers
    until a status code that equals 200 is received or log the error.

    Args:
        session (Session): Flask Session Object
        url (string): URL
        params (dict, optional): Parameters being sent to API. Defaults to {}.

    Returns:
        dictionary: JSON Response
    """
    if params is None:
        params = {}
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}
    get_response = requests.get(url, headers=headers, params=params)

    # Log GET Response output in terminal
    current_app.logger.debug(f'\n\n(makeGetRequest) GET Response Status Code -> {get_response.status_code}')

    if get_response.status_code == 200:
        return get_response.json()
    elif get_response.status_code == 401 and check_token_status(session) is not None:
        return make_get_request(session, url, params)
    else:
        logging.error('makeGetRequests:' + str(get_response.status_code))
        return None
