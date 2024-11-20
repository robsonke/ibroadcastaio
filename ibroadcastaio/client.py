import json
from typing import Any, AsyncGenerator

from aiohttp import ClientSession

from ibroadcastaio.const import (
    BASE_API_URL,
    BASE_LIBRARY_URL,
    REFERER,
    STATUS_API,
    VERSION,
)


class IBroadcastClient:
    """iBroadcast API Client to use the API in an async manner"""

    _user_id = None
    _token = None

    _albums = None
    _artists = None
    _playlists = None
    _tags = None
    _tracks = None
    _settings = None

    def __init__(self, http_session: ClientSession) -> None:
        """Main constructor"""
        self.http_session = http_session

    async def login(self, username: str, password: str) -> dict[str, Any]:
        data = {
            "mode": "status",
            "email_address": username,
            "password": password,
            "version": VERSION,
            "client": REFERER,
            "supported_types": False,
        }

        status = await self.__post(
            f"{BASE_API_URL}{STATUS_API}", {"content_type": "application/json"}, data
        )
        if "user" not in status:
            raise ValueError("Invalid credentials")

        # Store the token and user id
        self._token = status["user"]["token"]
        self._user_id = status["user"]["id"]

        return status

    async def refresh_library(self):
        """Fetch the library to cache it locally"""
        data = {
            "_token": self._token,
            "_userid": self._user_id,
            "client": REFERER,
            "version": VERSION,
            "mode": "library",
            "supported_types": False,
        }

        """
            In a future version of this library, mainly once ibroadcast has a more fine grained API, we should not keep the library in memory.
            For now we fetch the complete librady and split it into in memory class members.
            Later, we remove this step and rewrite methods such as _get_albums(album_id) to directly fetch it from the API.
        """
        library = await self.__post(
            f"{BASE_LIBRARY_URL}", {"content_type": "application/json"}, data
        )

        self._albums = {
            album["album_id"]: album
            async for album in self.__jsonToDict(
                library["library"]["albums"], "album_id"
            )
        }

        self._artists = {
            artist["artist_id"]: artist
            async for artist in self.__jsonToDict(
                library["library"]["artists"], "artist_id"
            )
        }

        self._playlists = {
            playlist["playlist_id"]: playlist
            async for playlist in self.__jsonToDict(
                library["library"]["playlists"], "playlist_id"
            )
        }

        """See here the exception for tags: https://devguide.ibroadcast.com/?p=library#get-library"""
        if isinstance(library["library"]["tags"], dict):
            self._tags = {
                int(tag_id): {**tag, "tag_id": int(tag_id)}
                for tag_id, tag in library["library"]["tags"].items()
            }
        else:
            self._tags = {
                tag["tag_id"]: tag
                async for tag in self.__jsonToDict(library["library"]["tags"], "tag_id")
            }

        self._tracks = {
            track["track_id"]: track
            async for track in self.__jsonToDict(
                library["library"]["tracks"], "track_id"
            )
        }

        self._settings = library["settings"]

    async def get_album_art(self, album_id: int) -> str:
        self._check_library_loaded()
        album = self._albums.get(album_id)
        if not album:
            raise ValueError(f"Album with id {album_id} not found")

        artwork_id = album.get("artwork_id")
        if not artwork_id:
            raise ValueError(f"No artwork found for album with id {album_id}")

        base_url = self.get_artwork_base_url
        return f"{base_url}/{artwork_id}"

    async def get_artwork_base_url(self) -> str:
        self._check_library_loaded()
        base_url = self._settings.get("artwork_server")
        if not base_url:
            raise ValueError("Artwork base URL not found in settings")
        return base_url

    async def get_artist(self, artist_id: int):
        self._check_library_loaded()
        return self._artists.get(artist_id)

    async def get_artists(self):
        self._check_library_loaded()
        return self._artists

    async def get_tag(self, tag_id: int):
        self._check_library_loaded()
        return self._tags.get(tag_id)

    async def get_tags(self):
        self._check_library_loaded()
        return self._tags

    async def get_settings(self):
        self._check_library_loaded()
        return self._settings

    async def get_album(self, album_id: int):
        self._check_library_loaded()
        return self._albums.get(album_id)

    async def get_albums(self):
        self._check_library_loaded()
        return self._albums

    async def get_track(self, track_id: int):
        self._check_library_loaded()
        return self._tracks.get(track_id)

    async def get_tracks(self):
        self._check_library_loaded()
        return self._tracks

    async def get_playlist(self, playlist_id: int):
        self._check_library_loaded()
        return self._playlists.get(playlist_id)

    async def get_playlists(self):
        self._check_library_loaded()
        return self._playlists

    async def __post(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ):
        async with self.http_session.post(
            url=url, data=json.dumps(data), headers=headers
        ) as response:
            return await response.json()

    async def __jsonToDict(
        self, data: list[dict[str, Any]], main_key: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Convert the library json into python dicts. See the readme for all fields.

        Example Album:

            data = {
            "12345" : [
                "My album",
                [
                    123,
                    124,
                    125
                ],
                "123",
                false,
                null,
                null,
                null,
                456,
                1
            ],
            "map" : {
                "artwork_id" : 7,
                "description" : 6,
                "name" : 0,
                "public_id" : 4,
                "sort" : 8,
                "system_created" : 3,
                "tracks" : 1,
                "type" : 5,
                "uid" : 2
            }
        }

        will be turned into a dict as:

        data = {
            "12345" : {
                "album_id" : 12345, ==> this is an extra field, to make life easier
                "name": "My album",
                "tracks": [
                    123,
                    124,
                    125
                ],
                "uid": "123",
                "system_created": false,
                "public_id": null,
                "type": null,
                "description": null,
                "artwork_id": 456,
                "sort": 1
            }
        }
        """
        if "map" not in data or type(data["map"]) is not dict:
            return

        keymap = {v: k for (k, v) in data["map"].items() if not isinstance(v, dict)}

        for key, value in data.items():
            if type(value) is list:
                result = {keymap[i]: value[i] for i in range(len(value))}
                result[main_key] = int(key)
                yield result

    def _check_library_loaded(self):
        """Check if the library is loaded"""
        if self._settings is None:
            raise ValueError("Library not loaded. Please call refresh_library first.")
