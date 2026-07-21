import logging
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
    return spotipy.Spotify(auth_manager=auth_manager)


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
