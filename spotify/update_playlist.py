#!/usr/bin/activate

import os
import sys
import time
import json
import spotipy
import numpy as np
import telegram_send

# refer all to position
# make tryouts
# gitname = 'raspberry'
# gitpath = os.popen('$HOME/.find_git_path.sh ' + gitname).read()[:-1]

class playlist:

    def __init__(self, data_folder='data'):
        """
        variables:
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
        
        with open(f'{data_folder}/.cache', 'r') as f:
            token = f.read()
        
        try :
            self.sp = spotipy.Spotify(auth=token)
        except:
            # pass a warning saying you have to login and save token in "data/.cache"
            # see "https://git.ligo.org/cbc/projects/cbcflow/-/blob/main/src/cbcflow/core/database.py#L31"
            
            token = spotipy.util.prompt_for_user_token(self.username, scope=scopes,
                                               client_id=clientID,
                                               client_secret=clientsecret,
                                               redirect_uri='http://localhost:8080/callback')
            self.sp = spotipy.Spotify(auth=token)
        
        self.daily_show_names = show_names1.split(",")
        self.long_show_names  = show_names2.split(",")
         