from typing import Any, Type
import requests
import logging


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.
    https://stackoverflow.com/questions/31875/is-there-a-simple-elegant-way-to-define-singletons
    """

    def __init__(self, decorated: Type) -> None:
        self._decorated = decorated

    def instance(self) -> Any:
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self) -> None:
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst: Any) -> bool:
        return isinstance(inst, self._decorated)


def get_items_from_api(session, url, params, item_key):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {session['token']}"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()[item_key]
    else:
        logging.error(f'Unable to make API request! Status code: {response.status_code}')
        logging.error(f'Response content: {response.content}')
        return None

