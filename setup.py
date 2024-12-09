import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spotify",
    version="0.2.0",
    author="Paolo Cremonese",
    author_email="cremonesep25@gmail.com",
    description="A tool for managing Spotify playlists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PaoloCremo/spotify/",
    packages=setuptools.find_packages(exclude=["tests*"]),
    install_requires=[
        "pandas",
        "spotipy",
        "numpy",
        "requests",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "spotify-playlist-manager=spotify.run_up:main",
        ],
    },
    include_package_data=True,
)