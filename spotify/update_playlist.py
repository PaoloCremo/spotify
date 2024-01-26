#!/usr/bin/activate

import os
import sys
import time
import json
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
    
        self.playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')


    def update_playlist(self):

        self.playlist = self.sp.playlist(self.list_id, additional_types=('tracks', 'episodes'), market='IT')


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
        
         