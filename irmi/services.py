import logging

import numpy as np
import requests
from collections import Counter
import random

from irmi import SVCA
from irmi.authenticate import make_get_request
from utils import get_items_from_api
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def group_songs_by_mood(username, mood):
    # Initialize the Spotify API client
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, username=username))

    # Retrieve the user's liked songs
    tracks = sp.current_user_saved_tracks(limit=50)['items']

    # Get the audio features of each song
    audio_features = sp.audio_features([track['track']['id'] for track in tracks])

    # Group the songs by mood
    happy_songs = []
    sad_songs = []
    energetic_songs = []
    songs = []
    for track, features in zip(tracks, audio_features):
        valence = features['valence']
        energy = features['energy']
        tempo = features['tempo']
        f13= features['acousticness']
        f0 = features['danceability']
        f1 = features['duration_ms']
        f2 = features['energy']
        f3 =  features['instrumentalness']
        f4 =  features['key']
        f5 =  features['liveness']
        f6 =  features['loudness']
        f7 =   features['mode']
        f8 =   features['popularity']
        f9 =   features['speechiness']
        f10 =   features['tempo']
        f11 =   features['time_signature']
        f12 =    features['valence']
        # Classify the song into a mood category
        if mood == 'happy':
            if valence < 0.3 and energy < 0.4 and tempo < 100:
                songs.append([f0,f1,f2,f3,f4,f5,f6,f7,f8,f8,f10,f11,f12,f13,1])
            else:
                songs.append([f0,f1,f2,f3,f4,f5,f6,f7,f8,f8,f10,f11,f12,f13,0])
        if mood == 'sad':
            if valence < 0.3 and energy < 0.4 and tempo < 100:
                songs.append([f0,f1,f2,f3,f4,f5,f6,f7,f8,f8,f10,f11,f12,f13,0])
            else:
                songs.append([f0,f1,f2,f3,f4,f5,f6,f7,f8,f8,f10,f11,f12,f13,1])


    S, W, potential_songs = SVCA.IVP(songs, .1)
    tv = get_taste_vector(potential_songs)
    target_dictionary={'target_acousticness': tv[13],
        'target_danceability': tv[0],
        'target_duration_ms': tv[2],
        'target_energy': tv[2],
        'target_instrumentalness': tv[3],
        'target_key': tv[4],
        'target_liveness': tv[5],
        'target_loudness': tv[6],
        'target_mode': tv[7],
        'target_popularity': tv[8],
        'target_speechiness': tv[9],
        'target_tempo': tv[10],
        'target_time_signature': tv[11],
        'target_valence': tv[12]}
    # Return the songs grouped by mood
    return potential_songs, target_dictionary


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


def get_recommendations(session, mood: str):
    """
    Read the following Spotify documentation: https://developer.spotify.com/documentation/web-api/reference/get-recommendations
    For each of the tunable track attributes (below) a target value may be provided.
    Tracks with the attribute values nearest to the target values will be preferred
    """
    Data, target_dict = group_songs_by_mood(session.get('user_id'), mood)
    # this gets the max and min values of the features
    #max_values = np.amax(np.array(Data), axis=0)
    #min_values = min_values = np.amin(min, axis=0)

    # TODO: Populate seed_artists, seed_genres, & seed_tracks with calls to Spotify API
    seeds = PopulateSeeds(session)

    url = 'https://api.spotify.com/v1/recommendations'
    params = {
        'seed_artists': ','.join(seeds.artists),
        'seed_genres': ','.join(seeds.genres),
        'seed_tracks': ','.join(seeds.tracks),
        'limit': 50,
        'market': 'US',
        'target_acousticness': target_dict['target_acousticness'],
        'target_danceability': target_dict['target_danceability'],
        'target_duration_ms': target_dict['target_duration_ms'],
        'target_energy': target_dict['target_energy'],
        'target_instrumentalness': target_dict['target_instrumentalness'],
        'target_key': target_dict['target_key'],
        'target_liveness': target_dict['target_liveness'],
        'target_loudness': target_dict['target_loudness'],
        'target_mode': target_dict['target_mode'],
        'target_popularity': target_dict['target_popularity'],
        'target_speechiness': target_dict['target_speechiness'],
        'target_tempo': target_dict['target_tempo'],
        'target_time_signature': target_dict['target_time_signature'],
        'target_valence': target_dict['target_valence']
    }

    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}
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
        'time_range': time_range,
        # short_term (last 4 weeks), medium_term (last 6 months), long_term (last several years)
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
        logging.critical(
            f'(get_user_top_genres) Unable to make GetTopArtists Request! Status code: {response.status_code}')
        logging.critical(f'(get_user_top_genres) Response content: {response.content}')
        return None


def get_artist_genres(session, artist_id):
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('genres', [])
    else:
        return []


def get_track_info(session, track_id):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'

    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Authorization': f"Bearer {session['token']}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(
            f'(get_track_info) Unable to get track info for track ID: {track_id}, Status code: {response.status_code}')
        return None


def group_tracks_by_genre(session, recommendations, top_genres):
    genre_groups = {genre: [] for genre in top_genres}
    other_genre_group = []

    for track_id in recommendations:
        track = get_track_info(session, track_id)  # Get track information using track ID
        if not track:
            continue

        track_genres = get_artist_genres(session, track['artists'][0]['id'])  # Get genres of the first artist

        added_to_group = False
        for genre in top_genres:
            if genre in track_genres:
                genre_groups[genre].append(track)
                added_to_group = True
                break

        if not added_to_group:
            other_genre_group.append(track)

    genre_groups['Other'] = other_genre_group
    return genre_groups


class PopulateSeeds:
    def __init__(self, session):
        self.artists = self.get_seed_artists(session)
        self.genres = self.get_seed_genres(session)
        self.tracks = self.get_seed_tracks(session)

    @staticmethod
    def get_seed_artists(session, limit=10, seed_limit=5):
        url = 'https://api.spotify.com/v1/me/top/artists'
        params = {
            'time_range': 'medium_term',
            'limit': limit
        }

        top_artists = get_items_from_api(session, url, params, 'items')

        if top_artists:
            random.shuffle(top_artists)
            seed_artists = [artist['id'] for artist in top_artists[:seed_limit]]
            return seed_artists
        else:
            logging.error('Top Artists not found!')
            return None

    @staticmethod
    def get_seed_genres(session, time_range='medium_term', artist_limit=50, seed_limit=5):
        top_genres = get_user_top_genres(session, time_range, artist_limit)

        if top_genres:
            genres = list(top_genres.keys())
            random.shuffle(genres)
            seed_genres = genres[:seed_limit]
            return seed_genres
        else:
            logging.error('Top Genres not found!')
            return None

    @staticmethod
    def get_seed_tracks(session, limit=10, seed_limit=5):
        url = 'https://api.spotify.com/v1/me/top/tracks'
        params = {
            'time_range': 'medium_term',
            'limit': limit
        }

        top_tracks = get_items_from_api(session, url, params, 'items')

        if top_tracks:
            random.shuffle(top_tracks)
            seed_tracks = [track['id'] for track in top_tracks[:seed_limit]]
            return seed_tracks
        else:
            logging.error('Top Tracks not found!')
            return None
