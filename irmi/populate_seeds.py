import random
import logging

from irmi.utils import get_items_from_api


class PopulateSeeds:
    def __init__(self, session):
        self.session = session

    def get_seed_artists(self, limit=10, seed_limit=5):
        url = 'https://api.spotify.com/v1/me/top/artists'
        params = {
            'time_range': 'medium_term',
            'limit': limit
        }

        top_artists = get_items_from_api(self.session, url, params, 'items')

        if top_artists:
            random.shuffle(top_artists)
            seed_artists = [artist['id'] for artist in top_artists[:seed_limit]]
            return seed_artists
        else:
            logging.error('Top Artists not found!')
            return None

    def get_seed_genres(self, time_range='medium_term', artist_limit=50, seed_limit=5):
        top_genres = get_user_top_genres(self.session, time_range, artist_limit)

        if top_genres:
            genres = list(top_genres.keys())
            random.shuffle(genres)
            seed_genres = genres[:seed_limit]
            return seed_genres
        else:
            logging.error('Top Genres not found!')
            return None

    def get_seed_tracks(self, limit=10, seed_limit=5):
        url = 'https://api.spotify.com/v1/me/top/tracks'
        params = {
            'time_range': 'medium_term',
            'limit': limit
        }

        top_tracks = get_items_from_api(self.session, url, params, 'items')

        if top_tracks:
            random.shuffle(top_tracks)
            seed_tracks = [track['id'] for track in top_tracks[:seed_limit]]
            return seed_tracks
        else:
            logging.error('Top Tracks not found!')
            return None



