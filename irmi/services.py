from authenticate import make_get_request


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
