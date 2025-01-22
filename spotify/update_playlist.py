#!/usr/bin/env python3

import os
import pandas as pd
import spotipy
import numpy as np
import requests
from tabulate import tabulate
from typing import List, Dict, Optional
from .utils import setup_logger

logger = setup_logger()

class Playlist:
    def __init__(self, data_folder: str = 'data'):
        """
        Initialize the Playlist object.

        Args:
            data_folder (str): Path to the 'data' file containing username, clientID, clientSecret,
                               list_id, and show names.
        """
        self.sp, self.headers = self._authenticate(data_folder)
        self.ghosts = np.array([])
        self.shows = {show: self.find_uri_show(show) for show in self.daily_show_names + self.long_show_names}
        self.playlist = self.get_playlist()
        logger.info('Playlist loaded.')

    def _authenticate(self, data_folder: str) -> tuple:
        """
        Authenticate with Spotify API.

        Args:
            data_folder (str): Path to the data folder.

        Returns:
            tuple: Spotify client object and headers for API requests.
        """
        file_path = os.path.dirname(__file__)
        path_data = os.path.join(os.path.dirname(file_path), f'{data_folder}/data')
        
        with open(path_data, 'r') as t:
            data = t.readlines()
        
        self.username, clientID, clientsecret, self.list_id, show_names1, show_names2, _ = [d.strip() for d in data]
        
        scopes = ['playlist-modify-private', 'user-follow-read', 'playlist-read-private',
                  'playlist-modify-public', 'user-read-playback-position', 'user-library-read']
        
        token = spotipy.util.prompt_for_user_token(self.username, scope=scopes,
                                                   client_id=clientID,
                                                   client_secret=clientsecret,
                                                   redirect_uri='http://localhost:8080/callback')
        
        sp = spotipy.Spotify(auth=token)
        headers = {"Authorization": f"Bearer {token}"}
        
        self.daily_show_names = show_names1.split(",")
        self.long_show_names = show_names2.split(",")
        
        return sp, headers

    def find_uri_show(self, show_name: str, market: str = 'IT') -> Optional[str]:
        """
        Find URI from show name.

        Args:
            show_name (str): Name of the show.
            market (str): Market code (default is 'IT' for Italy).

        Returns:
            Optional[str]: URI of the show if found, None otherwise.
        """
        search = self.sp.search(q=show_name, type='show', market=market)
        items = search['shows']['items']
        for item in items:
            if item['name'] == show_name:
                return item['uri']
        return None
    
    def get_raw_playlist(self):
        """
        Retrieve the playlist from Spotify.
        """
        return self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
    
    def get_playlist(self) -> pd.DataFrame:
        """
        Retrieve the playlist and create a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing playlist information.
        """
        self.delete_ghosts(self.list_id)
        playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        
        df = pd.DataFrame(columns=['position', 'name', 'show_name', 'uri', 'played'])
        
        for n, item in enumerate(playlist['tracks']['items']):
            track = item['track']
            new_row = pd.DataFrame({
                'position': n,
                'name': track['name'],
                'show_name': None,
                'uri': track['uri'],
                'played': None
            }, index=[0])
            
            if track['type'] == 'episode':
                played = self.sp.episode(track['uri'])['resume_point']['fully_played']
                new_row['played'] = played
                new_row['show_name'] = item['track']['show']['name']
            
            df = pd.concat([df, new_row], ignore_index=True, axis=0)
        
        return df

    def get_playlist_tracks(self, playlist_id: str) -> Dict:
        """
        Retrieve tracks from a playlist.

        Args:
            playlist_id (str): ID of the playlist.

        Returns:
            Dict: JSON response containing playlist tracks.
        """
        BASE_URL = "https://api.spotify.com/v1"
        url = f"{BASE_URL}/playlists/{playlist_id}/tracks"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def remove_tracks_by_position(self, user: str, playlist_id: str, tracks: List[Dict], snapshot_id: str) -> Dict:
        """
        Remove tracks from a playlist by their positions.
        
        credits: https://github.com/RatkoJ 
                 @ https://github.com/spotipy-dev/spotipy/issues/95#issuecomment-627208310

        Args:
            user (str): Spotify user ID.
            playlist_id (str): ID of the playlist.
            tracks (List[Dict]): List of tracks to remove, each containing positions.
            snapshot_id (str): Snapshot ID of the playlist.

        Returns:
            Dict: Response from the Spotify API.
        """
        plid = self.sp._get_id("playlist", playlist_id)
        payload = {"snapshot_id": snapshot_id, "positions": []}
        for tr in tracks:
            payload["positions"].extend(tr["positions"])
        return self.sp._delete(f"users/{user}/playlists/{plid}/tracks", payload=payload)

    def delete_ghosts(self, playlist_id: str) -> None:
        """
        Delete ghost tracks from the playlist.

        Args:
            playlist_id (str): ID of the playlist.
        """
        tracks = self.get_playlist_tracks(playlist_id)
        ghost_tracks = [
            {"positions": [idx]} for idx, item in enumerate(tracks['items'])
            if not item['track'] or not item['track'].get("uri")
        ]
        
        if ghost_tracks:
            snapshot_id = self.sp.playlist(playlist_id)['snapshot_id']
            self.remove_tracks_by_position(self.sp.me()['id'], playlist_id, ghost_tracks, snapshot_id)

    def update_playlist(self) -> None:
        """
        Update the playlist DataFrame with the latest information from Spotify.
        """
        new_playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        
        for n, item in enumerate(new_playlist['tracks']['items']):
            track = item['track']
            if track['uri'] in list(self.playlist.uri):
                iindex = self.playlist.index[self.playlist['uri'] == track['uri']][0]
                if iindex != n:
                    self.playlist.at[iindex, 'position'] = n
            else:
                new_row = pd.DataFrame({
                    'position': n,
                    'name': track['name'],
                    'show_name': None,
                    'uri': track['uri'],
                    'played': None
                }, index=[0])
                
                if track['type'] == 'episode':
                    played = self.sp.episode(track['uri'])['resume_point']['fully_played']
                    new_row['played'] = played
                    new_row['show_name'] = item['track']['show']['name']
                
                self.playlist = pd.concat([self.playlist, new_row], ignore_index=True)
        
        self.playlist.sort_values('position', ignore_index=True, inplace=True)
        
        if len(new_playlist['tracks']['items']) != len(self.playlist):
            uris = [track['track']['uri'] for track in new_playlist['tracks']['items']]
            self.playlist = self.playlist[self.playlist.uri.isin(uris)]


    def get_new_episodes(self, show_name: str) -> List[str]:
        """
        Check if there are new episodes of the show.

        Args:
            show_name (str): Name of the show to check for new episodes.

        Returns:
            List[str]: List of URIs for new episodes.
        """
        show = self.sp.show(self.shows[show_name])
        new_episodes = []
        for item in show['episodes']['items']:
            if item and not item['resume_point']['fully_played']:
                new_episodes.append(item['uri'])
            else:
                break
        return new_episodes
    
    def get_episodes_in_playlist(self, show_name: str) -> pd.DataFrame:
        """
        Get position in playlist of episodes of a show.

        Args:
            show_name (str): Name of the show to find episodes for.

        Returns:
            pd.DataFrame: DataFrame containing episodes of the specified show in the playlist.
        """
        self.update_playlist()
        episodes = self.playlist[self.playlist.show_name == show_name]
        return episodes
    

    def add_new_episodes(self, show_name: str, verbose: bool = True) -> None:
        """
        Add new episodes of a show to the playlist.

        Args:
            show_name (str): Name of the show.
            verbose (bool): If True, log information about added episodes.
        """
        self.update_playlist()
        new_episodes = self.get_new_episodes(show_name)
        
        if new_episodes:
            episodes_in_playlist = self.get_episodes_in_playlist(show_name)
            new_episodes = [ep for ep in new_episodes if ep not in episodes_in_playlist.uri.tolist()]
            
            if 0 < len(new_episodes) < 10:
                position = episodes_in_playlist.iloc[-1].position + 1 if not episodes_in_playlist.empty else 0
                self.sp.playlist_add_items(playlist_id=self.list_id, items=new_episodes, position=position)
                
                if verbose:
                    for episode in new_episodes:
                        name = self.sp.episode(episode)['name']
                        logger.info(f'Added episode "{name}"')
                
                self.update_playlist()

    def delete_played_items(self, verbose: bool = True) -> None:
        """
        Delete played podcast episodes from the playlist.

        Args:
            verbose (bool): If True, log information about deleted episodes.
        """
        self.update_playlist()
        n_deleted = 0
        
        for n in self.playlist.index:
            track = self.playlist.loc[n]
            if track.played and self.playlist.show_name.value_counts()[track.show_name] > 1:
                to_remove = [{"uri": track.uri, "positions": [track.position - n_deleted]}]
                self.sp.playlist_remove_specific_occurrences_of_items(self.list_id, to_remove)
                n_deleted += 1
                self.playlist.drop(n, inplace=True)
                
                if verbose:
                    logger.info(f'Deleted: "{track["name"]} - {track.show_name}"')
        
        self.update_playlist()

    def find_next_episodes(self, show_name, last_ep_name):
        """
        Finds the next episodes of a given show after the specified last episode.

        Args:
            show_name (str): The name of the show.
            last_ep_name (str): The name of the last episode watched.

        Returns:
            list: A list of URIs for the next three episodes in reverse order.
        """
        show_id = self.shows[show_name]
        offset = 0
        names = [dicct['name'] for dicct in self.sp.show_episodes(show_id, offset=offset)['items']]
        while last_ep_name not in names:
            offset += 50
            names = [dicct['name'] for dicct in self.sp.show_episodes(show_id, offset=offset)['items']]
        for n, name in enumerate(names):
            if name == last_ep_name:
                break
        new_episodes = self.sp.show_episodes(show_id, offset=offset+n-3, limit=3)['items']
        new_episodes_uri = [ep['uri'] for ep in new_episodes]
        return new_episodes_uri[::-1]
        

    def manage_long_shows(self, verbose: bool = True) -> None:
        """
        Manage episodes of shows in self.long_show_names:
        1. Check if there are at least 3 unplayed episodes of each show.
        2. If not, find the next episodes and add them to the end of the playlist.
        3. Delete played episodes of these shows from the playlist.
        
        Args:
            verbose (bool): If True, log information about added and deleted episodes.
        """
        self.update_playlist()
        
        for show_name in self.long_show_names:
            episodes = self.get_episodes_in_playlist(show_name)
            played_episodes = episodes[episodes['played'] == True]
            unplayed_episodes = episodes[episodes['played'] == False]
            if verbose:
                logger.info(f'{show_name}: {len(unplayed_episodes)} unplayed episodes.')
                logger.info(f'{show_name}: {len(played_episodes)} played episodes.')

            # Check if there are less than 3 unplayed episodes
            if len(unplayed_episodes) < 3:
                last_ep_name = episodes['name'].iloc[-1]
                new_episodes = self.find_next_episodes(show_name, last_ep_name)
                episodes_to_add = 3 - len(unplayed_episodes)
                
                for episode in new_episodes[:episodes_to_add]:
                    if episode not in episodes['uri'].tolist():
                        position = episodes.position.iloc[-1] + 2
                        self.sp.playlist_add_items(playlist_id=self.list_id, items=[episode], position=position)
                        if verbose:
                            episode_name = self.sp.episode(episode)['name']
                            logger.info(f'Added episode "{episode_name}" to {show_name}')
        
            # Delete played episodes
            for _, episode in played_episodes.iterrows():
                to_remove = [{"uri": episode['uri'], "positions": [episode['position']]}]
                self.sp.playlist_remove_specific_occurrences_of_items(self.list_id, to_remove)
                if verbose:
                    logger.info(f'Deleted: "{episode["name"]} - {show_name}"')
    
        self.update_playlist()


    def print_playlist_tracks(self):
        '''
        Function to print tracks and episodes of a playlist
        Output:
        nothing, only print
        '''
        print(tabulate(self.playlist, headers='keys', tablefmt='psql'))

    def main(self) -> None:
        """
        Main function to update the playlist with new episodes and delete played items.
        """
        for show_name in self.daily_show_names:
            self.add_new_episodes(show_name)
            logger.info(f'{show_name}: finished adding new episodes.')
        
        self.manage_long_shows()
        logger.info('Finished managing long shows.')
        
        self.delete_played_items()
        logger.info('Finished deleting played episodes.')