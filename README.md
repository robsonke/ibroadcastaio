# iBroadcastAIO

A Python library inspired by [ibroadcast-python](https://github.com/ctrueden/ibroadcast-python) for interacting with the iBroadcast API in an async manner.
This library is initially built for usage in an iBroadcast music provider in [Music Assistant](https://music-assistant.io/).

## Shortcomings of the Current API

While the iBroadcast API provides a robust set of features for interacting with the service, it has some shortcomings. One of the main issues is the lack of fine-grained control over data retrieval and manipulation, which can lead to higher memory usage. This library aims to address these issues by providing more efficient data handling in future updates, allowing for better memory management and performance.

For more info, see their [documentation](https://devguide.ibroadcast.com/).


## Installation

To see if you already have a virtual env (but `poetry install` should create this for you):

```bash
poetry env info --path
source venv/bin/activate
```

This project uses Poetry for dependency management. To install the dependencies and run the example script:

```bash
poetry install
poetry run example
```

To build and publish the package, use:

```bash
poetry build
poetry publish
```

To run the unit tests:

```bash
poetry run python -m unittest discover -s tests
```

## Example Usage

### Initialize the client and fetch albums

```python
from ibroadcastaio import IBroadcastClient
from aiohttp import ClientSession

async with ClientSession() as session:
    client = IBroadcastClient(session)
    await client.login("your@email.com", "andyourpassword")
    await client.refresh_library()

    albums = await client.get_albums()
    for album in albums:
        print(album['name'])
```

## Status object
The login() method returns a status object which contains valuable data. Just print the status object to get a good understanding, but these are the main fields:

```json
{
   "messages":[ ],
   "message":"ok",
   "dropbox":{ },
   "lastfm":{ },
   "googledrive":{ },
   "settings":{ },
   "status":{ },
   "authenticated":true,
   "result":true,
   "user":{ }
}
```

## Data Structures

For a very short and simplified example of the complete library JSON that the API provides, see [example.json](./tests/example.json). Below you will find the fields of each main topic.

### Tracks

```json
{
    "trashed": 10,
    "track": 0,
    "artists_additional_map": {
        "type": 2,
        "phrase": 1,
        "artist_id": 0
    },
    "type": 17,
    "genre": 3,
    "year": 1,
    "enid": 8,
    "uploaded_time": 19,
    "length": 4,
    "size": 11,
    "uid": 13,
    "path": 12,
    "artwork_id": 6,
    "artists_additional": 20,
    "album_id": 5,
    "uploaded_on": 9,
    "rating": 14,
    "title": 2,
    "artist_id": 7,
    "icatid": 22,
    "genres_additional": 21,
    "plays": 15,
    "file": 16,
    "replay_gain": 18
}
```

### Playlist

```json
{
    "public_id": 4,
    "uid": 2,
    "sort": 8,
    "system_created": 3,
    "artwork_id": 7,
    "type": 5,
    "tracks": 1,
    "name": 0,
    "description": 6
}
```

### Artist

```json
{
    "tracks": 1,
    "trashed": 2,
    "artwork_id": 4,
    "rating": 3,
    "name": 0,
    "icatid": 5
}
```

### Album

```json
{
    "year": 6,
    "name": 0,
    "artists_additional": 7,
    "artists_additional_map": {
        "type": 2,
        "artist_id": 0,
        "phrase": 1
    },
    "tracks": 1,
    "rating": 4,
    "icatid": 8,
    "disc": 5,
    "trashed": 3,
    "artist_id": 2
}
```
