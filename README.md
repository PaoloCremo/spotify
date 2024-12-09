# Spotify Playlist Manager

This project provides a Python-based tool for managing Spotify playlists, including updating playlists, adding new episodes, and removing played items.

## Project Structure
```
.  
├── setup.py  
├── requirements.txt  
├── README.md  
└── spotify/  
    ├── __init__.py
    ├── run_up.py
    ├── update_playlist.py
    └── utils.py
```


## Installation

1. Clone this repository
2. Install the required packages:  
```pip install -r requirements.txt```
3. Install the package:   
```pip install .```


## Usage

To use the Spotify Playlist Manager, you can run the `run_up.py` script:  
```python spotify/run_up.py```


Make sure to set up your Spotify API credentials and configure the necessary data files before running the script.

## Features

- Update playlists with new episodes
- Remove played items from playlists
- Manage podcast episodes in playlists
- Handle authentication with Spotify API

## Dependencies

- pandas
- spotipy
- numpy
- requests

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.


## Contact

Paolo Cremonese | [@PaoloCremo](https://github.com/PaoloCremo)