#!/usr/bin/activate

import os
import pandas as pd
pd.options.mode.copy_on_write = True
import spotipy
import numpy as np
# import telegram_send
from time import sleep

import requests

from .utils import setup_logger

logger = setup_logger()

# refer all to position
# make tryouts
# gitname = 'raspberry'
# gitpath = os.popen('$HOME/.find_git_path.sh ' + gitname).read()[:-1]


class playlist:

    def __init__(self, data_folder='data'):
        """
        variables
        data_folder: path to 'data' file with usernam, clientID, clientsecret,
                                            list_id and show_names
        """
        file_path = os.path.dirname(__file__)
        path_data = os.path.join(os.path.dirname(file_path), 'data/data') 
        # with open(f'{data_folder}/data', 'r') as t:
        with open(path_data, 'r') as t:
            data = t.readlines()
        
        self.username, clientID, clientsecret, self.list_id, show_names1, show_names2, _ = [d[:-1] for d in data]
        
        scopes = ['playlist-modify-private',
                       'user-follow-read', 
                       'playlist-read-private',
                       'playlist-modify-public',
                       'user-read-playback-position',
                       'user-library-read']
        
        # first time it asks to loging, then saves authomatically token in .cache-xxxxxxx
        token = spotipy.util.prompt_for_user_token(self.username, scope=scopes,
                                           client_id=clientID,
                                           client_secret=clientsecret,
                                           redirect_uri='http://localhost:8080/callback')
        self.sp = spotipy.Spotify(auth=token)
        
        self.headers = {
                           "Authorization": f"Bearer {token}",
                       }
        
        self.daily_show_names = show_names1.split(",")
        self.long_show_names  = show_names2.split(",")

        self.shows = {daily_show:self.find_uri_show(daily_show) for daily_show in self.daily_show_names} | \
                     {long_show:self.find_uri_show(long_show) for long_show in self.long_show_names}
    
        self.ghosts = np.array([])
        self.count_ghosts(self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT'))
        self.playlist = self.get_playlist()
        logger.info('Playlist loaded.')

    def find_uri_show(self, show_name, market='IT'):
        """
        find URI from show name
        """
        search = self.sp.search(q=show_name, type='show', market=market)
        items = search['shows']['items']
        for item in items:
            if item['name'] == show_name:
                uri = item['uri']
                break
    
        return uri
    
    def get_plain_playlist(self):
        playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        return playlist
    
    def count_ghosts(self, playlist):
        for ni,item in enumerate(playlist['tracks']['items']):
            if item['track'] == None:
                self.ghosts = np.append(self.ghosts, ni)

    def get_playlist(self):
        """
        make pandas df?? 
        index: position in playlist
        name
        uri
        played: [T,F] --> Episode, None --> track
        """
        
        self.delete_ghosts(self.list_id) # this delete all ghosts tracks
        playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        # playlist = self.check_playlist(playlist) # DEPRECATED

        df = pd.DataFrame(columns=['position','name','show_name','uri','played'])

        for n,item in enumerate(playlist['tracks']['items']):
            track = item['track']
            new_row = pd.DataFrame({'position':n, 
                                    'name': track['name'],
                                    'show_name':None, 
                                    'uri':track['uri'], 
                                    'played': None}, 
                                   index=[0])
            if track['type'] == 'episode':
                played = self.sp.episode(track['uri'])['resume_point']['fully_played']
                new_row['played'] = played
                new_row['show_name'] = item['track']['show']['name']
            df = pd.concat([df,new_row], ignore_index=True, axis=0)
        
        return df
    
    def check_playlist(self, playlist):
        '''
        DEPRECATED: use delete ghosts
        '''
        while self.are_there_ghosts(playlist):
            for ni,item in enumerate(playlist['tracks']['items']):
                if item['track'] == None:
                    playlist['tracks']['items'].pop(ni)
    
        return playlist
    
    def get_playlist_tracks(self, playlist_id):
        BASE_URL = "https://api.spotify.com/v1"
        url = f"{BASE_URL}/playlists/{playlist_id}/tracks"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    
    def remove_tracks_by_position(self, user, playlist_id, tracks, snapshot_id):
        """
        credits: https://github.com/RatkoJ 
                 @ https://github.com/spotipy-dev/spotipy/issues/95#issuecomment-627208310
        """
        plid = self.sp._get_id("playlist", playlist_id)
        payload = {"snapshot_id": snapshot_id, "positions": []}
        for tr in tracks:
            payload["positions"].extend(tr["positions"])
        return self.sp._delete(f"users/{user}/playlists/{plid}/tracks", payload=payload)
    
    def delete_ghosts(self, playlist_id):

        tracks = self.get_playlist_tracks(playlist_id)
    
        # Identify ghost tracks
        ghost_tracks = [
            {"positions":[idx]} for idx, item in enumerate(tracks['items'])
            if not item['track'] or not item['track'].get("uri")
        ]
        if ghost_tracks:
            snapshot_id = self.sp.playlist(playlist_id)['snapshot_id']
        
            self.remove_tracks_by_position(self.sp.me()['id'],
                                           playlist_id,
                                           ghost_tracks,
                                           snapshot_id)
    
    
    def are_there_ghosts(self, playlist):
        for ni,item in enumerate(playlist['tracks']['items']):
            if item['track'] == None:
                return True
            else:
                pass
        return False

    def update_playlist(self):
        """
        Update playlist dataframe
        """
        
        new_playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        new_playlist = self.check_playlist(new_playlist)
        
        for n,item in enumerate(new_playlist['tracks']['items']):
            track = item['track']
            if track['uri'] in list(self.playlist.uri):
                iindex = self.playlist.index[self.playlist['uri'] == track['uri']][0]
                if iindex != n:
                    self.playlist.at[iindex,'position'] = n
            else:
                new_row = pd.DataFrame({'position':n,
                                        'name': track['name'],
                                        'show_name':None,
                                        'uri':track['uri'], 
                                        'played': None}, 
                                       index=[0])
                if track['type'] == 'episode':
                    played = self.sp.episode(track['uri'])['resume_point']['fully_played']
                    new_row['played'] = played
                    new_row['show_name'] = item['track']['show']['name']
                self.playlist = pd.concat([self.playlist, new_row], ignore_index=True)
        
        # reored list according to position
        self.playlist.sort_values('position', ignore_index=True, inplace=True)

        # check if len(new_playlist)==len(self.playlist) 
        # and delete episodes that have been deleted in the meantime
        if len(new_playlist['tracks']['items']) != len(self.playlist):
            uris = [track['track']['uri'] for track in new_playlist['tracks']['items']]
            for n in self.playlist.index:
                if self.playlist.loc[n].uri not in uris:
                    self.playlist.drop(n, inplace=True)
        

    def print_playlist_tracks(self):
        '''
        Function to print tracks and episodes of a playlist

        Output:
        nothing, only print
        '''
        tracks = self.playlist['tracks'] 
        to_print = ''
        to_print += 'Total number of tracks and episodes: {}\n\n'.format(len(tracks['items']))
        for ni,item in enumerate(tracks['items']):
            if 'track' in item:
                track = item['track']
            else:
                track = item
            to_print += f'{ni+1:02}. {track["name"]}\n'
        return to_print
        
    # from here think new more ordered ways to do what I want to do 
    # (and what I'm already doing but not so well)

    def get_new_episodes(self, show_name):
        """
        Check if there are new episodes of the show
        """
        show = self.sp.show(self.shows[show_name])
        new_episodes = []
        for item in show['episodes']['items']:
            if item:
                if not item['resume_point']['fully_played'] :
                    new_episodes.append(item['uri'])
                else:
                    break

        return new_episodes
    
    def get_episodes_in_playlist(self, show_name):
        """
        get position in playlist of episodes of a show
        """
        self.update_playlist()
        episodes = self.playlist[self.playlist.show_name == show_name]
        '''
        episodes = {}
        for n,item in enumerate(self.playlist['tracks']['items']):
            try:
                if item['track']['show']['uri'] == self.shows[show_name]:
                    episodes[n] = item['track']['uri']
            except:
                pass
        '''

        return episodes
    
    def add_new_episodes(self, show_name, verbose=True):
        """
        add new episodes
        """
        self.update_playlist()

        new_episodes = self.get_new_episodes(show_name)
        if len(new_episodes) > 0:
            # new_episodes = self.get_new_episodes(show_name)
            episodes_in_playlist = self.get_episodes_in_playlist(show_name)
            
            for ep in list(episodes_in_playlist.uri):
                try:
                    new_episodes.remove(ep)
                except ValueError:
                    pass
            
            if len(new_episodes) > 0 and len(new_episodes) < 10:
                # print(f'\n{new_episodes}\n')
                position0 = episodes_in_playlist.iloc[-1].position+1
                position = position0 + len(self.ghosts[self.ghosts < position0])
                self.sp.playlist_add_items(playlist_id = self.list_id, 
                                           items=new_episodes, 
                                           position=position)
                if verbose:
                    for episode in new_episodes:
                        name = self.sp.episode(episode)['name']
                        logger.info(f'Added episode "{name}"')
                
                self.update_playlist()

    def delete_played_items(self, verbose=True):
        """
        Deleted played postcast episodes
        """
        self.update_playlist()
        
        n_deleted = 0

        for n in self.playlist.index:
            track = self.playlist.loc[n]
            if track.played:
                 if self.playlist.show_name.value_counts()[track.show_name] > 1:
                      to_remove = [{"uri":track.uri, "positions":[track.position-n_deleted]}]
                      self.sp.playlist_remove_specific_occurrences_of_items(self.list_id, to_remove)
                      n_deleted += 1
                      self.playlist.drop(n, inplace=True)
                      if verbose:
                          logger.info(f'Deleted: "{track["name"]} - {track.show_name}"')

        self.update_playlist() 

    def check_long_show(self, show_name):
        episodes = self.playlist[self.playlist.show_name == show_name]
        episode_played = episodes[episodes.played]
        if not len(episode_played) > 0 :
            logger.info(f'{show_name} is up to date.')
        else:
            pass



    def main(self):
        
        for show_name in self.daily_show_names:
            self.add_new_episodes(show_name)
            logger.info(f'{show_name}: finished adding new episodes.')
            # sleep(1)
    
        self.delete_played_items()
        logger.info('Finished deleting played episodes.')
