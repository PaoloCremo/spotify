#!/usr/bin/activate

import os
import sys
import time
import json
import pandas as pd
pd.options.mode.copy_on_write = True
import spotipy
import numpy as np
import telegram_send

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
        
        with open(f'{data_folder}/data', 'r') as t:
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
        
        self.daily_show_names = show_names1.split(",")
        self.long_show_names  = show_names2.split(",")

        self.shows = {daily_show:self.find_uri_show(daily_show) for daily_show in self.daily_show_names} | \
                     {long_show:self.find_uri_show(long_show) for long_show in self.long_show_names}
    
        self.playlist = self.get_playlist()

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

    def get_playlist(self):
        """
        make pandas df?? 
        index: position in playlist
        name
        uri
        played: [T,F] --> Episode, None --> track
        """
        
        playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
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

    def update_playlist(self):
        """
        Update playlist dataframe
        """
        
        new_playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')
        for n,item in enumerate(new_playlist['tracks']['items']):
            track = item['track']
            if track['uri'] in list(self.playlist.uri):
                iindex = self.playlist.index[self.playlist['uri'] == track['uri']][0]
                # if iindex != n:
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
        

        self.playlist.sort_values('position', ignore_index=True, inplace=True)


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
        episodes = {}
        for n,item in enumerate(self.playlist['tracks']['items']):
            try:
                if item['track']['show']['uri'] == self.shows[show_name]:
                    episodes[n] = item['track']['uri']
            except:
                pass

        return episodes
    
    def add_new_episodes(self, show_name, verbose=True):
        """
        add new episodes
        """
        self.update_playlist()

        new_episodes = self.get_new_episodes(show_name)
        if len(new_episodes) > 0:
            new_episodes = self.get_new_episodes(show_name)
            episodes_in_playlist = self.get_episodes_in_playlist(show_name)
            
            for ep in list(episodes_in_playlist.values()):
                try:
                    new_episodes.remove(ep)
                except ValueError:
                    pass
            
            if len(new_episodes) > 0 :
                self.sp.playlist_add_items(playlist_id = self.list_id, 
                                           items=new_episodes, 
                                           position=list(episodes_in_playlist.keys())[-1]+1)
                if verbose:
                    for episode in new_episodes:
                        name = self.sp.episode(episode)['name']
                        logger.warning(f'Added episode "{name}"')
                
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
                          logger.warning(f'Deleted: "{track["name"]} - {track.show_name}"')

        self.update_playlist() 



def main():
    pl = playlist()
    logger.warning('Playlist loaded.')
    
    for show_name in pl.daily_show_names:
        pl.get_new_episodes(show_name)
        logger.warning(f'{show_name}: finished adding new episodes.')

    pl.delete_played_items()
    logger.warning('Finished deleting played episodes.')

if __name__ == "__main__":
    main()
