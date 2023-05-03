import logging

import numpy as np
import requests
from collections import Counter

from irmi import SVCA
from irmi.authenticate import make_get_request


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


def create_set_of_potential(data, uris, w):
    vector = list()
    songs_uri = list()
    for i in range(0, len(data)):
        if SVCA.prediction(SVCA.calc_Wx(w, np.array(data[i]))) == 0:
            vector.append(data[i])
            songs_uri.append(uris[i])
    return vector, songs_uri


def get_playlist_data(playlist_uri, nlist, sp):
    Mlist = list()
    for track in sp.playlist_items(playlist_uri)["items"]:
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
        nlist.append(list(Mlist[i].values())[:9])
    return nlist


def get_user_data(data, sp):
    Mlist = list()
    Nlist = list()
    URIS = list()
    for i in range(0, len(data)):
        # URI
        track_uri = data[i]["track"]["uri"]
        Mlist.append([sp.audio_features(track_uri)[0], track_uri])
        URIS.append(track_uri)
    for i in range(0, len(Mlist)):
        Nlist.append(list(Mlist[i][0].values())[:9])
    return Nlist, URIS


def get_user_information(session):
    """Gets user information such as username, user ID, and user location
    Args:
        session (Session): Flask Session Object
    Returns:
        dict : JSON Response
    """
    url = 'https://api.spotify.com/v1/me'
    payload = make_get_request(session, url)

    if payload is None:
        return None

    return payload


def get_liked_track_ids(session):
    url = 'https://api.spotify.com/v1/me/tracks'
    payload = make_get_request(session, url)

    if payload is None:
        return None

    liked_tracks_ids = []
    for track in payload['items']:
        liked_id = track['track'].get('id', None)
        if liked_id:
            liked_tracks_ids.append(liked_id)

    return liked_tracks_ids


def get_recommendations(session, seed_artists, seed_genres, seed_tracks, limit, market, target_acousticness,
                        target_danceability, target_duration_ms, target_energy, target_instrumentalness,
                        target_key, target_liveness, target_loudness, target_mode, target_popularity,
                        target_speechiness, target_tempo, target_time_signature, target_valence):
    url = 'https://api.spotify.com/v1/recommendations'

    params = {
        'seed_artists': ','.join(seed_artists),
        'seed_genres': ','.join(seed_genres),
        'seed_tracks': ','.join(seed_tracks),
        'limit': limit,
        'market': market,
        'target_acousticness': target_acousticness,
        'target_danceability': target_danceability,
        'target_duration_ms': target_duration_ms,
        'target_energy': target_energy,
        'target_instrumentalness': target_instrumentalness,
        'target_key': target_key,
        'target_liveness': target_liveness,
        'target_loudness': target_loudness,
        'target_mode': target_mode,
        'target_popularity': target_popularity,
        'target_speechiness': target_speechiness,
        'target_tempo': target_tempo,
        'target_time_signature': target_time_signature,
        'target_valence': target_valence
    }

    headers = {'Authorization': f'Bearer {session}'}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        # TODO: Handle errors
        return None


def get_user_top_genres(session, time_range='medium_term', artist_limit=50):
    url = 'https://api.spotify.com/v1/me/top/artists'
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}
    params = {
        'time_range': time_range,  # short_term (last 4 weeks), medium_term (last 6 months), long_term (last several years)
        'limit': artist_limit  # The maximum number of artists to return (max: 50)
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        top_artists = response.json()['items']
        genre_counter = Counter()

        if top_artists:
            for artist in top_artists:
                genres = artist['genres']
                genre_counter.update(genres)

            return dict(genre_counter)
        else:
            logging.error('(get_user_top_genres) Top Artists not found!')
    else:
        logging.critical(f'(get_user_top_genres) Unable to make GetTopArtists Request! Status code: {response.status_code}')
        logging.critical(f'(get_user_top_genres) Response content: {response.content}')
        return None


def get_artist_genres(artist_id, session):
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('genres', [])
    else:
        return []


def group_tracks_by_genre(session, recommendations, user_top_genres):
    grouped_tracks = {genre: [] for genre in user_top_genres}
    grouped_tracks['other'] = []  # Add an "other" key to handle tracks that don't belong to user's top genres

    for track in recommendations:
        track_id = track.get('id')
        track_name = track.get('name')
        artist_id = track['artists'][0]['id']

        artist_genres = get_artist_genres(artist_id, session)
        assigned_genre = None

        for user_genre in user_top_genres:
            if any(user_genre in artist_genre for artist_genre in artist_genres):
                assigned_genre = user_genre
                break

        if not assigned_genre:
            assigned_genre = 'other'

        track_metadata = {
            'id': track_id,
            'name': track_name,
            'artist_id': artist_id,
            'artist_genres': artist_genres
        }
        grouped_tracks[assigned_genre].append(track_metadata)

    return grouped_tracks
