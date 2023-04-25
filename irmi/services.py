from flask import redirect

from irmi.authenticate import make_get_request


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
