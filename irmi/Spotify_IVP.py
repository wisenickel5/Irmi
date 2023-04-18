import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np
import spotipy.util as util
import SVCA
import pandas as pd

def append_audio_features(df, spotify_auth, return_feat_df=False):
    #this is imported toutrial 
    audio_features = spotify_auth.audio_features(df["track_id"][:])
    # catch and delete songs that have no audio features
    if None in audio_features:
        NA_idx = [i for i, v in enumerate(audio_features) if v == None]
        df.drop(NA_idx, inplace=True)
        for i in NA_idx:
            audio_features.pop(i)
    assert len(audio_features) == len(df["track_id"][:])
    feature_cols = list(audio_features[0].keys())[:-7]
    features_list = []
    for features in audio_features:
        try:
            song_features = [features[col] for col in feature_cols]
            features_list.append(song_features)
        except TypeError:
            pass
    df_features = pd.DataFrame(features_list, columns=feature_cols)
    df = pd.concat([df, df_features], axis=1)
    if return_feat_df == False:
        return df
    else:
        return df, df_features

def authenticate(redirect_uri, client_cred_manager, username, scope, client_id, client_secret):
    #this is imported toutrial 
    sp = spotipy.Spotify(client_credentials_manager=client_cred_manager)
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    if token:
        sp = spotipy.Spotify(auth=token)
    else:
        print("No token for", username)
    return sp


client_id = "2cbda720019447bb8841a09360cd422d"
client_secret = "51f6f2ae04dd4b57ae64f961d1556a5d"
username = "EthanHunt2125"
redirect_uri = "https://developer.spotify.com/dashboard/applications/2cbda720019447bb8841a09360cd422d"
client_credentials_manager = SpotifyClientCredentials(client_id=client_id,
                                                      client_secret=client_secret)
scope = "user-library-read user-read-recently-played user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative"
sp = authenticate(redirect_uri, client_credentials_manager, username, scope, client_id, client_secret)


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


def create_set_of_potential(data, W):
    vector = list()
    for i in range(0, len(data)):
        if SVCA.prediction(SVCA.calc_Wx(W, np.array(data[i]))) == 0:
            vector.append(data[i])
    return vector


def get_playlist_data(playlist_URI, Nlist):
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


def get_user_data(data):
    Mlist = list()
    Nlist = list()
    for i in range(0, len(data)):
        # URI
        track_uri = data[i]["track"]["uri"]
        Mlist.append([sp.audio_features(track_uri)[0], track_uri])

    for i in range(0, len(Mlist)):
        Nlist.append(list(Mlist[i][0].values())[:9])
    return Nlist


results = sp.current_user_saved_tracks()["items"]
results = get_user_data(results)
good_playlist_link = "https://open.spotify.com/playlist/4FJ7NmgSV8ttdozvfc6EgN?si=9dbbe50c19d44b56"
bad_playlist_link = "https://open.spotify.com/playlist/2OdWS5qgdX4oQEQQrqHYZe?si=afe1076fd7d14494"
playlist_URI = good_playlist_link.split("/")[-1].split("?")[0]
playlist_URI2 = bad_playlist_link.split("/")[-1].split("?")[0]
track_uris = [x["track"]["uri"] for x in sp.playlist_items(playlist_URI)["items"]]

Nlist = list()
Nlist2 = list()
Nlist = get_playlist_data(playlist_URI, Nlist)
Nlist2 = get_playlist_data(playlist_URI, Nlist2)
GS = create_set_of_good_songs(Nlist)
BS = create_set_of_bad_songs(Nlist2)
data = GS + BS
Score, W = SVCA.IVP(data, .1)
MS=create_set_of_potential(results,W)
print(MS)
Mood_matrix = SVCA.MODEL(W)

print(Mood_matrix.model)

print(data)
