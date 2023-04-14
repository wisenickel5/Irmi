from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import pandas as pd
import numpy as np


def authenticate(redirect_uri, client_cred_manager, username, scope, client_id, client_secret):
    sp = spotipy.Spotify(client_credentials_manager=client_cred_manager)
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    if token:
        sp = spotipy.Spotify(auth=token)
    else:
        print("Can't get token for", username)
    return sp


def create_df_top_songs(api_results):
    # create lists for df-columns
    track_name = []
    track_id = []
    artist = []
    album = []
    duration = []
    popularity = []
    # loop through api_results
    for items in api_results['items']:
        try:
            track_name.append(items['name'])
            track_id.append(items['id'])
            artist.append(items["artists"][0]["name"])
            duration.append(items["duration_ms"])
            album.append(items["album"]["name"])
            popularity.append(items["popularity"])
        except TypeError:
            pass
    # Create the final df
    df = pd.DataFrame({"track_name": track_name,
                       "album": album,
                       "track_id": track_id,
                       "artist": artist,
                       "duration": duration,
                       "popularity": popularity})

    return df


def create_df_saved_songs(api_results):
    # create lists for df-columns
    track_name = []
    track_id = []
    artist = []
    album = []
    duration = []
    popularity = []
    # loop through api_results
    for items in api_results["items"]:
        try:
            track_name.append(items["track"]['name'])
            track_id.append(items["track"]['id'])
            artist.append(items["track"]["artists"][0]["name"])
            duration.append(items["track"]["duration_ms"])
            album.append(items["track"]["album"]["name"])
            popularity.append(items["track"]["popularity"])
        except TypeError:
            pass
    # Create the final df
    df = pd.DataFrame({"track_name": track_name,
                       "album": album,
                       "track_id": track_id,
                       "artist": artist,
                       "duration": duration,
                       "popularity": popularity})
    return df


def top_artists_from_API(api_results):
    df = pd.DataFrame(api_results["items"])
    cols = ["name", "id", "genres", "popularity", "uri"]
    return df[cols]


def create_df_recommendations(api_results):
    track_name = []
    track_id = []
    artist = []
    album = []
    duration = []
    popularity = []
    for items in api_results['tracks']:
        try:
            track_name.append(items['name'])
            track_id.append(items['id'])
            artist.append(items["artists"][0]["name"])
            duration.append(items["duration_ms"])
            album.append(items["album"]["name"])
            popularity.append(items["popularity"])
        except TypeError:
            pass
        df = pd.DataFrame({"track_name": track_name,
                           "album": album,
                           "track_id": track_id,
                           "artist": artist,
                           "duration": duration,
                           "popularity": popularity})

    return df


def create_df_playlist(api_results, sp=None, append_audio=True):
    df = create_df_saved_songs(api_results["tracks"])
    if append_audio:
        assert sp is not None, "sp needs to be specified for appending audio features"
        df = append_audio_features(df, sp)
    return df


def append_audio_features(df, spotify_auth, return_feat_df=False):
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
    for feats in audio_features:
        try:
            song_features = [feats[col] for col in feature_cols]
            features_list.append(song_features)
        except TypeError:
            pass
    df_features = pd.DataFrame(features_list, columns=feature_cols)
    df = pd.concat([df, df_features], axis=1)
    if not return_feat_df:
        return df
    else:
        return df, df_features


def dataframe_difference(df1, df2, which=None):
    comparison_df = df1.merge(
        df2,
        indicator=True,
        how='outer'
    )
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]
    diff_df.drop("_merge", axis=1, inplace=True)
    return diff_df.drop_duplicates().reset_index(drop=True)


def create_similarity_score(df1, df2, similarity_score="cosine_sim"):
    assert list(df1.columns[6:]) == list(df2.columns[6:]), "dataframes need to contain the same columns"
    features = list(df1.columns[6:])
    features.remove('key')
    features.remove('mode')
    df_features1, df_features2 = df1[features], df2[features]
    scaler = MinMaxScaler()  # StandardScaler() not used anymore
    df_features_scaled1, df_features_scaled2 = scaler.fit_transform(df_features1), scaler.fit_transform(df_features2)
    if similarity_score == "linear":
        linear_sim = linear_kernel(df_features_scaled1, df_features_scaled2)
        return linear_sim
    elif similarity_score == "cosine_sim":
        cosine_sim = cosine_similarity(df_features_scaled1, df_features_scaled2)
        return cosine_sim
    # other measures may be implemented in the future


def filter_with_meansong(mean_song, recommendations_df, n_recommendations=10):
    feats = list(mean_song.columns[6:])
    feats.remove("key")
    feats.remove("mode")
    mean_song_feat = mean_song[feats].values
    mean_song_scaled = MinMaxScaler().fit_transform(mean_song_feat.reshape(-1, 1))
    recommendations_df_scaled = MinMaxScaler().fit_transform(recommendations_df[feats])
    mean_song_scaled = mean_song_scaled.reshape(1, -1)
    sim_mean_finrecomms = cosine_similarity(mean_song_scaled, recommendations_df_scaled)[0][:]
    indices = (-sim_mean_finrecomms).argsort()[:n_recommendations]
    final_recommendations = recommendations_df.iloc[indices]
    return final_recommendations


def feature_filter(df, feature, high=True):
    assert feature in ["speechiness",
                       "acousticness",
                       "instrumentalness",
                       "liveness"], \
        "Feature must be one of the following: Speechiness, Acousticness, Instrumentalness, Liveness"

    # more features may be added
    x = 0.9 if high is True else 0.1
    df = df[df[feature] > x] if high is True else df[df[feature] < x]
    return df


# TODO: WIP
def get_recommendations(df, song_title, similarity_score, num_recommends=5):
    indices = pd.Series(df.index, index=df['track_name']).drop_duplicates()
    idx = indices[song_title]
    sim_scores = list(enumerate(similarity_score[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_scores = sim_scores[1:num_recommends + 1]
    song_indices = [i[0] for i in top_scores]
    return df["track_name"].iloc[song_indices]


def get_dfs2(sp):
    # user top tracks
    top_tracks_short = sp.current_user_top_tracks(limit=50, offset=0, time_range='short_term')
    top_tracks_1ed = sp.current_user_top_tracks(limit=50, offset=0, time_range='medium_term')
    top_tracks_long = sp.current_user_top_tracks(limit=50, offset=0, time_range='long_term')

    # combine the top_tracks
    top_tracks_short_df = append_audio_features(create_df_top_songs(top_tracks_short), sp)
    top_tracks_1ed_df = append_audio_features(create_df_top_songs(top_tracks_1ed), sp)
    top_tracks_long_df = append_audio_features(create_df_top_songs(top_tracks_long), sp)
    # sample from long-term top tracks to introduce more randomness and avoid having the same artists
    top_tracks_long_df = top_tracks_long_df.sample(n=15)
    top_tracks_df = pd.concat(
        [top_tracks_short_df, top_tracks_long_df, top_tracks_long_df]).drop_duplicates().reset_index(drop=True)

    # user top artists
    top_artists_long = sp.current_user_top_artists(limit=50, time_range="long_term")
    top_artists_1ed = sp.current_user_top_artists(limit=50, time_range="medium_term")
    top_artists_short = sp.current_user_top_artists(limit=50, time_range="short_term")

    artists_short_df = top_artists_from_API(top_artists_short)
    artists_1ed_df = top_artists_from_API(top_artists_1ed)
    artists_long_df = top_artists_from_API(top_artists_long)
    artists_df = pd.concat([artists_short_df, artists_1ed_df, artists_long_df])
    artists_df["genres"] = artists_df["genres"].apply(lambda x: ",".join(x))
    artists_df.drop_duplicates().reset_index(drop=True)

    # user saved tracks
    user_saved_tracks = sp.current_user_saved_tracks(limit=50)
    saved_tracks_df = create_df_saved_songs(user_saved_tracks)

    return top_tracks_df, artists_df, saved_tracks_df


def get_dfs(sp):
    # user top tracks
    top_tracks_short = sp.current_user_top_tracks(limit=50, offset=0, time_range='short_term')
    top_tracks_1ed = sp.current_user_top_tracks(limit=50, offset=0, time_range='medium_term')
    top_tracks_long = sp.current_user_top_tracks(limit=50, offset=0, time_range='long_term')

    # combine the top_tracks
    top_tracks_short_df = append_audio_features(create_df_top_songs(top_tracks_short), sp)
    top_tracks_1ed_df = append_audio_features(create_df_top_songs(top_tracks_1ed), sp)
    top_tracks_long_df = append_audio_features(create_df_top_songs(top_tracks_long), sp)
    # sample from long-term top tracks to introduce more randomness and avoid having the same artists
    top_tracks_long_df = top_tracks_long_df.sample(n=15)
    top_tracks_df = pd.concat(
        [top_tracks_short_df, top_tracks_1ed_df, top_tracks_long_df]).drop_duplicates().reset_index(drop=True)

    # user top artists
    top_artists_long = sp.current_user_top_artists(limit=50, time_range="long_term")
    top_artists_1ed = sp.current_user_top_artists(limit=50, time_range="medium_term")
    top_artists_short = sp.current_user_top_artists(limit=50, time_range="short_term")

    artists_short_df = top_artists_from_API(top_artists_short)
    artists_1ed_df = top_artists_from_API(top_artists_1ed)
    artists_long_df = top_artists_from_API(top_artists_long)
    artists_df = pd.concat([artists_short_df, artists_1ed_df, artists_long_df])
    artists_df["genres"] = artists_df["genres"].apply(lambda x: ",".join(x))
    artists_df.drop_duplicates().reset_index(drop=True)

    # user saved tracks
    user_saved_tracks = sp.current_user_saved_tracks(limit=50)
    saved_tracks_df = create_df_saved_songs(user_saved_tracks)

    return top_tracks_df, artists_df, saved_tracks_df


if __name__ == "__main__":
    client_id = "2cbda720019447bb8841a09360cd422d"
    client_secret = "51f6f2ae04dd4b57ae64f961d1556a5d"
    username = "EthanHunt2125"
    redirect_uri = "https://developer.spotify.com/dashboard/applications/2cbda720019447bb8841a09360cd422d"
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id,
                                                          client_secret=client_secret)
    scope = "user-library-read user-read-recently-played user-top-read playlist-modify-public playlist-read-private playlist-read-collaborative"
    sp = authenticate(redirect_uri, client_credentials_manager, username, scope, client_id, client_secret)
    playlist_uri = input("Please paste in the URI of the playlist you wish to add songs to   ")
    playlist = sp.playlist(playlist_uri)
    playlist_df = create_df_playlist(playlist, sp=sp)

    # create mean_song
    mean_song = pd.DataFrame(columns=playlist_df.columns)
    mean_song.loc["mean"] = playlist_df.mean()

    # get seed tracks for recommendations
    seed_tracks = playlist_df["track_id"].tolist()
    # create recommendation df
    recomm_dfs = []
    for i in range(5, len(seed_tracks) + 1, 5):
        # Limit could be modified to get more or less recommendations per song in the original playlist
        recomms = sp.recommendations(seed_tracks=seed_tracks[i - 5:i],
                                     limit=25)
        recomms_df = append_audio_features(create_df_recommendations(recomms), sp)
        recomm_dfs.append(recomms_df)
    recomms_df = pd.concat(recomm_dfs)
    recomms_df.reset_index(drop=True, inplace=True)

    # create similarity scoring between playlist and recommendations
    similarity_score = create_similarity_score(playlist_df, recomms_df)
    while True:
        # get a filtered recommendations df
        final_recomms = recomms_df.iloc[[np.argmax(i) for i in similarity_score]]  # get indeces of most similar songs
        final_recomms = final_recomms.drop_duplicates()
        # filter again so tracks are not already in playlist_df
        final_recomms = final_recomms[~final_recomms["track_name"].isin(playlist_df["track_name"])]
        final_recomms.reset_index(drop=True, inplace=True)

        # manual filtering by audio feature
        manual_filter = input(
            "Do you wish to filter the recommendations manually by setting one of the following audio features very "
            "high or very low: speechiness, acousticness, instrumentalness, liveness [y/n]").lower()
        if manual_filter == "y":
            features = input(
                "Which features would you like to filter by? (Not more than 1-2 recommended) "
                "[e.g. speechiness,liveness]").split(",")

            assert isinstance(features, list), "Something went wrong. Please enter the features seperated by a comma"
            high_low = input("For each feature please enter 'high' if you want the feature to be high or 'low' "
                             "if you want it to be low [e.g. high,low]").split(",")
            high_low = [True if x == "high" else False for x in high_low]
            assert isinstance(high_low, list), "Something went wrong. Please enter the features seperated by a comma"
            assert len(features) == len(high_low), "Number of features and True/False must be equal"

            # loop through selected features to filter by
            for feat, high in zip(features, high_low):
                final_recomms = feature_filter(final_recomms, feature=feat, high=high)
            print(f"Your list of recommended songs is now {len(final_recomms)} songs long")
            proceed = input("Do you wish to proceed or filter differently? [proceed/filter]").lower()
            if proceed == "proceed":
                break
        else:
            break

    # filter with mean song or sample from recommended
    n_recommendations = int(
        input("how many songs would you like to add to your playlist? Please enter a number between 1 - 20   "))
    assert 21 > n_recommendations > 0, "Number of Recommendations must be between 1 and 20"
    assert len(final_recomms) > n_recommendations, "Can't add more song than the filtered dataframe contains"

    mean_song_filter = input(
        "Do you wish to filter the songs further by comparing them to the average playlist song? "
        "[y/n] (This is works for playlists with a very unified 'sound')").lower()
    if mean_song_filter == "y":
        final_recomms = filter_with_meansong(mean_song, final_recomms, n_recommendations=n_recommendations)
    else:
        final_recomms = final_recomms.sample(n=n_recommendations)
    confirm = input("Please confirm that you want to add songs to the playlist by typing YES   ")
    if confirm == "YES":
        sp.user_playlist_add_tracks(username, playlist_id=playlist_uri, tracks=final_recomms["track_id"].tolist())
