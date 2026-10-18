import logging
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth


def get_spotify_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scope,
    cache_path: str,
    open_browser: bool = False,
) -> "spotipy.Spotify":
    """Authenticate with Spotify and return a Spotify client.

    Instead of opening a browser automatically, prints the
    authorization URL to the console (set open_browser=True to
    restore the automatic-browser behavior).
    """
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
        open_browser=open_browser,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=20, retries=1)
    return _RetryingClient(sp)


class _RetryingClient:
    """Proxy that retries any Spotify API call failing with a network error."""

    def __init__(self, sp: "spotipy.Spotify", attempts: int = 4, backoff: float = 5.0):
        self._sp = sp
        self._attempts = attempts
        self._backoff = backoff

    def __getattr__(self, name):
        attr = getattr(self._sp, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            for attempt in range(self._attempts):
                try:
                    return attr(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == self._attempts - 1:
                        raise
                    delay = self._backoff * 3 ** attempt
                    logging.getLogger(__name__).warning(
                        f"{name} failed ({e.__class__.__name__}), retry in {delay:.0f}s")
                    time.sleep(delay)

        return call


def setup_logger() -> "logging.Logger":
    """Setup a logger for the module"""

    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    ch = logging.StreamHandler()
    print_formatter = logging.Formatter(
        "%(asctime)s spytify %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(print_formatter)
    logger.addHandler(ch)

    return logger
