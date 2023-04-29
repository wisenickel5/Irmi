import numpy as np
from flask import redirect

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


def get_recommendations(session):
	"""
	Returns a set of recommended tracks in JSON format.
	:param session:
	:return: (dict) A list of recommended tracks.
	"""
	return None
