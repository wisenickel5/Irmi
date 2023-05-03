import requests
from time import time
import string as string
import random as rand
import logging
import base64
from google.cloud import secretmanager

from irmi.utils import Singleton
import config


def create_state_key(size):
    """Provides a state key for authorization request. To prevent forgery attacks, the state key
    is used to make sure that the response comes from the same place that the request was sent from.
    Reference: https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits

    Args:
        size (int): Determines the size of the State Key

    Returns:
        string: A randomly generated code with the length of the size parameter
    """
    return ''.join(rand.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(size))


def get_token(code):
    """Requests an access token from Spotify API. This function is only called if
    the current user does not have a refresh token.

    Args:
        code (string): Value returned from HTTP GET Request

    Returns:
        tuple(str, str, str) : Access Token, Refresh Token, Expiration Time
    """
    request_body = {
        "grant_type": config.GRANT_TYPE,
        "code": code,
        "redirect_uri": config.REDIRECT_URI,
        "client_id": CredentialManager.instance().gcp_secrets['client_id'],
        "client_secret": CredentialManager.instance().gcp_secrets['client_secret'],
    }
    post_request = requests.post(url=config.TOKEN_URL, data=request_body)
    p_response = post_request.json()

    if post_request.status_code == 200:
        return p_response['access_token'], p_response['refresh_token'], p_response['expires_in']
    else:
        logging.error('get_token Failure: ' + str(post_request.status_code))
        return None


def refresh_token(token, client_id, client_secret):
    token_url = 'https://accounts.spotify.com/api/token'

    # Encode the client_id and client_secret in base64 format
    client_credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(client_credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    body = {'refresh_token': token, 'grant_type': 'refresh_token'}
    post_response = requests.post(token_url, headers=headers, data=body)

    if post_response.status_code == 200:
        token = post_response.json()['access_token']
        exp_time = post_response.json()['expires_in']
        return token, exp_time
    else:
        logging.error('refresh_token:' + str(post_response.status_code))
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
        payload = refresh_token(session['refresh_token'],
                                CredentialManager.instance().gcp_secrets['client_id'],
                                CredentialManager.instance().gcp_secrets['client_secret'])

    if payload is not None:
        session['token'] = payload[0]
        session['token_expiration'] = time() + payload[1]
    else:
        logging.error('check_token_status Failure...')
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

    if get_response.status_code == 200:
        return get_response.json()
    elif get_response.status_code == 401 and check_token_status(session) is not None:
        return make_get_request(session, url, params)
    else:
        logging.error('makeGetRequests:' + str(get_response.status_code))
        return None


@Singleton
class CredentialManager:
    def __init__(self):
        self.gcp_secrets = self.access_secrets_versions()

    @staticmethod
    def access_secrets_versions() -> dict:
        # Create the Secret Manager client.
        service_client = secretmanager.SecretManagerServiceClient()

        # Build the resource names of the secret version.
        client_id_name = f"projects/1058885278278/secrets/CLIENT_ID/versions/1"
        client_secret_name = "projects/1058885278278/secrets/CLIENT_SECRET/versions/1"

        # Access the secret version.
        responses = {
            'client_id': service_client.access_secret_version(name=client_id_name),
            'client_secret': service_client.access_secret_version(name=client_secret_name)
        }

        payload = {k: v.payload.data.decode('UTF-8') for (k, v) in responses.items()}
        logging.debug("Payload received from GCP")

        # Return the decoded payloads within a dictionary
        return payload
