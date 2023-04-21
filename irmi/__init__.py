from flask import Flask
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

import config
from irmi.authenticate import CredentialManager


app = Flask(__name__)
app.config.from_object(config)
app.config.from_mapping(SECRET_KEY='dev')

# Authenticate with Google Cloud Platform to receive credentials.
cm = CredentialManager()

# Authenticate Irmi application with Spotify
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=cm.gcp_secrets['client_id'],
                                                                              client_secret=cm.gcp_secrets['client_secret']),
                          auth_manager=SpotifyOAuth(scope=config.SCOPE,
                                                    client_id=cm.gcp_secrets['client_id'],
                                                    client_secret=cm.gcp_secrets['client_secret'],
                                                    redirect_uri=config.REDIRECT_URI,
                                                    ))
