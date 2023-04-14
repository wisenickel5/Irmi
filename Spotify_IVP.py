import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import pandas as pd
import numpy as np
from sklearn import datasets
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

client_credentials_manager = SpotifyClientCredentials(client_id="12ba2ba13acd401a84603dfb6f678414",
                                                      client_secret="3dd66fc8821b44a58ad1f43081857ab4")
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


# Authentication - without user
def get_taste_vector(taste_data):
    taste_vector = list()
    for i in range(0, taste_data.shape[1]):
        taste_vector.append(np.mean(taste_data[:, i]))
    return taste_vector


def create_set_of_good_songs(taste_data):
    taste_vector = list()
    for i in range(0, len(taste_data)):
        taste_vector.append((taste_data[i], 0))
    return taste_vector


def create_set_of_bad_songs(taste_data):
    taste_vector = list()
    for i in range(0, len(taste_data)):
        taste_vector.append((taste_data[i], 1))
    return taste_vector


def get_playlist_data(playlist_URI,Nlist):
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


good_playlist_link = "https://open.spotify.com/playlist/4FJ7NmgSV8ttdozvfc6EgN?si=9dbbe50c19d44b56"
bad_playlist_link = "https://open.spotify.com/playlist/2OdWS5qgdX4oQEQQrqHYZe?si=afe1076fd7d14494"
playlist_URI = good_playlist_link.split("/")[-1].split("?")[0]
playlist_URI2 = bad_playlist_link.split("/")[-1].split("?")[0]
track_uris = [x["track"]["uri"] for x in sp.playlist_items(playlist_URI)["items"]]


Nlist = list()
Nlist2=list()
Nlist = get_playlist_data(playlist_URI,Nlist)
Nlist2=get_playlist_data(playlist_URI,Nlist2)
GS=create_set_of_good_songs(Nlist)
BS=create_set_of_bad_songs(Nlist2)
data=GS+BS
print(data)

