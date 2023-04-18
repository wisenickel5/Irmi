from google.cloud import secretmanager


def access_secrets_versions() -> dict:
    # Create the Secret Manager client.
    service_client = secretmanager.SecretManagerServiceClient()

    # Build the resource names of the secret version.
    client_id_name = f"projects/1058885278278/secrets/CLIENT_ID"
    client_secret_name = f"projects/1058885278278/secrets/CLIENT_SECRET"

    # Access the secret version.
    responses = {
        'client_id': service_client.access_secret_version(name=client_id_name),
        'client_secret': service_client.access_secret_version(name=client_secret_name)
    }

    # Return the decoded payloads within a dictionary
    return {k: v.payload.data.decdode('UTF-8') for (k, v) in responses.items()}


if __name__ == "__main__":
    import argparse
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

    # Use the argparse library to read in command line arguments passed in
    parser = argparse.ArgumentParser(prog='Irmi - (Impressionable) Music Recommendation Inquiry System',
                                     description="Analyzes a user’s Spotify listening history with sound & mood "
                                                 "classification models to build a more tasteful playlists.")
    args = parser.parse_args()
    print("Welcome to the (Impressionable) Music Recommendation System!")

    # TODO: Authenticate User
    SCOPE = 'user-read-email%20user-read-private%20user-top-read%20user-read-playback-state%20playlist-modify-public%20playlist-modify-private%20user-top-read%20user-read-recently-played%20user-library-read'
    secrets = access_secrets_versions()
    REDIRECT_URI = "https://irmi.app/callback"  # TODO: Create Flask server to handle this.
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=secrets['client_id'],
                                                                                  client_secret=secrets['client_secret']),
                              auth_manager=SpotifyOAuth(scope=SCOPE))

    # TODO: Retrieve desired mood from user
