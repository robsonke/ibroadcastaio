import importlib.metadata
import json
from typing import Any, AsyncGenerator

from aiohttp import ClientSession

from ibroadcastaio.const import BASE_API_URL, BASE_LIBRARY_URL, REFERER, STATUS_API


class IBroadcastClient:
    """iBroadcast API Client to use the API in an async manner"""

    _albums = None
    _artists = None
    _playlists = None
    _tags = None
    _tracks = None

    _settings = None
    _status = None

    def __init__(self, http_session: ClientSession) -> None:
        """Main constructor"""
        self.http_session = http_session

    async def login(self, username: str, password: str) -> dict[str, Any]:
        """Login to the iBroadcast API and return the status dict"""
        data = {
            "mode": "status",
            "email_address": username,
            "password": password,
            "version": self.get_version(),
            "client": REFERER,
            "supported_types": False,
        }

        try:
            self._status = await self.__post(
                f"{BASE_API_URL}{STATUS_API}",
                {"content_type": "application/json"},
                data,
            )
        except Exception as e:
            raise ValueError(f"Failed to login: {e}")

        if "user" not in self._status:
            raise ValueError("Invalid credentials")

        # result: Bool
        # authenticated: Bool
        # token: String
        # status: Dictionary
        # user: Dictionary
        # settings: Dictionary
        # status["user"]["token"]
        # status["user"]["id"]

        return self._status

    def get_version(self) -> str:
        return importlib.metadata.version("ibroadcastaio")

    async def refresh_library(self):
        """Fetch the library to cache it locally"""
        data = {
            "_token": self._status["user"]["token"],
            "_userid": self._status["user"]["id"],
            "client": REFERER,
            "version": self.get_version(),
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

    async def get_artwork_url(self, entity_id: int, entity_type: str) -> str:
        self._check_library_loaded()

        if entity_type == "track":
            entity = await self.get_track(entity_id)
        elif entity_type == "artist":
            entity = await self.get_artist(entity_id)
        elif entity_type == "playlist":
            entity = await self.get_playlist(entity_id)
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        if not entity:
            raise ValueError(
                f"{entity_type.capitalize()} with id {entity_id} not found"
            )

        if "artwork_id" not in entity:
            raise ValueError(f"No artwork found for {entity_type} with id {entity_id}")

        artwork_id = entity["artwork_id"]

        base_url = await self.get_artwork_base_url()

        return f"{base_url}/artwork/{artwork_id}-300"

    async def get_album_artwork_url(self, album_id: int) -> str:
        """Get the artwork URL for an album from the first track in the album with a valid artwork_id"""

        track_id = next(
            (
                track_id
                for track_id in self.get_album(album_id)["tracks"]
                if self._client.get_track(track_id)["artwork_id"] is not None
            ),
            None,
        )
        return await self.get_track_artwork_url(track_id)

    async def get_track_artwork_url(self, track_id: int) -> str:
        return await self.get_artwork_url(track_id, "track")

    async def get_artist_artwork_url(self, artist_id: int) -> str:
        return await self.get_artwork_url(artist_id, "artist")

    async def get_playlist_artwork_url(self, playlist_id: int) -> str:
        return await self.get_artwork_url(playlist_id, "playlist")

    async def get_artwork_base_url(self) -> str:
        self._check_library_loaded()
        base_url = self._settings.get("artwork_server")
        if not base_url:
            raise ValueError("Artwork base URL not found in settings")
        return base_url

    async def get_stream_url(self) -> str:
        self._check_library_loaded()
        stream_url = self._settings.get("streaming_server")
        if not stream_url:
            raise ValueError("Stream server not found in settings")
        return stream_url

    async def get_full_stream_url(
        self, track_id: int, platform: str = "ibroadcastaio"
    ) -> str:
        track = self.get_track(track_id)

        return (
            f'{self.get_stream_url()}{track["file"]}?'
            f'&Signature={self._status["user"]["token"]}'
            f"&file_id={track_id}"
            f'&user_id={self._status["user"]["id"]}'
            f"&platform={platform}"
            f"&version={self.get_version()}"
        )

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
