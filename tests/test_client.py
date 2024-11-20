import json
import unittest
from unittest.mock import AsyncMock, patch

from aiohttp import ClientSession

from ibroadcastaio.client import IBroadcastClient


class TestIBroadcastClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session = ClientSession()
        self.client = IBroadcastClient(self.session)

    async def asyncTearDown(self):
        await self.session.close()

    async def _load_raw_mock_library(self):
        with open("tests/example.json", "r") as file:
            return json.load(file)

    async def _load_mock_library(self, identifier: str):
        result = {}
        data = await self._load_raw_mock_library()
        async for item in self.client._IBroadcastClient__jsonToDict(data, identifier):
            result[item[identifier]] = item
        return result

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_login_success(self, mock_post):
        mock_post.return_value = {"user": {"token": "fake_token", "id": "fake_id"}}
        result = await self.client.login("test@example.com", "password")
        self.assertEqual(self.client._token, "fake_token")
        self.assertEqual(self.client._user_id, "fake_id")
        self.assertIn("user", result)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_login_failure(self, mock_post):
        mock_post.return_value = {}
        with self.assertRaises(ValueError):
            await self.client.login("test@example.com", "password")

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_refresh_library(self, mock_post):
        mock_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_library

        await self.client.refresh_library()
        self.assertIsInstance(self.client._albums, dict)
        self.assertIsInstance(self.client._artists, dict)
        self.assertIsInstance(self.client._playlists, dict)
        self.assertIsInstance(self.client._tags, dict)
        self.assertIsInstance(self.client._tracks, dict)
        self.assertIsInstance(self.client._settings, dict)

    async def test_json_to_dict(self):
        data = {
            "12345": [
                "My album",
                [123, 124, 125],
                "123",
                False,
                None,
                None,
                None,
                456,
                1,
            ],
            "map": {
                "artwork_id": 7,
                "description": 6,
                "name": 0,
                "public_id": 4,
                "sort": 8,
                "system_created": 3,
                "tracks": 1,
                "type": 5,
                "uid": 2,
            },
        }

        expected_result = {
            "album_id": 12345,
            "name": "My album",
            "tracks": [123, 124, 125],
            "uid": "123",
            "system_created": False,
            "public_id": None,
            "type": None,
            "description": None,
            "artwork_id": 456,
            "sort": 1,
        }

        result = []
        async for item in self.client._IBroadcastClient__jsonToDict(data, "album_id"):
            result.append(item)

        self.assertEqual(result[0], expected_result)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_albums(self, mock_post):
        mock_post.return_value = await self._load_raw_mock_library()

        await self.client.refresh_library()
        albums = await self.client.get_albums()

        self.assertIsInstance(albums, dict)
        self.assertGreater(len(albums), 0)
        for album_id, album in albums.items():
            self.assertIsInstance(album_id, int)
            self.assertIsInstance(album, dict)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_settings(self, mock_post):
        mock_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_library

        await self.client.refresh_library()
        settings = await self.client.get_settings()

        self.assertIsInstance(settings, dict)
        self.assertEqual(settings, mock_library["settings"])

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_album(self, mock_post):
        mock_raw_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_raw_library

        await self.client.refresh_library()
        album_id = list(mock_raw_library["library"]["albums"].keys())[0]
        album = await self.client.get_album(int(album_id))

        self.assertIsInstance(album, dict)
        self.assertEqual(album["album_id"], int(album_id))

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_track(self, mock_post):
        mock_raw_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_raw_library

        await self.client.refresh_library()
        track_id = list(mock_raw_library["library"]["tracks"].keys())[0]
        track = await self.client.get_track(int(track_id))

        self.assertIsInstance(track, dict)
        self.assertEqual(track["track_id"], int(track_id))

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_playlist(self, mock_post):
        mock_raw_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_raw_library

        await self.client.refresh_library()
        playlist_id = list(mock_raw_library["library"]["playlists"].keys())[0]
        playlist = await self.client.get_playlist(int(playlist_id))

        self.assertIsInstance(playlist, dict)
        self.assertEqual(playlist["playlist_id"], int(playlist_id))

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_playlists(self, mock_post):
        mock_post.return_value = await self._load_raw_mock_library()

        await self.client.refresh_library()
        playlists = await self.client.get_playlists()

        self.assertIsInstance(playlists, dict)
        self.assertGreater(len(playlists), 0)
        for playlist_id, playlist in playlists.items():
            self.assertIsInstance(playlist_id, int)
            self.assertIsInstance(playlist, dict)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_artist(self, mock_post):
        mock_raw_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_raw_library

        await self.client.refresh_library()
        artist_id = list(mock_raw_library["library"]["artists"].keys())[0]
        artist = await self.client.get_artist(int(artist_id))

        self.assertIsInstance(artist, dict)
        self.assertEqual(artist["artist_id"], int(artist_id))

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_artists(self, mock_post):
        mock_post.return_value = await self._load_raw_mock_library()

        await self.client.refresh_library()
        artists = await self.client.get_artists()

        self.assertIsInstance(artists, dict)
        self.assertGreater(len(artists), 0)
        for artist_id, artist in artists.items():
            self.assertIsInstance(artist_id, int)
            self.assertIsInstance(artist, dict)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_tag(self, mock_post):
        mock_raw_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_raw_library

        await self.client.refresh_library()
        tag_id = list(mock_raw_library["library"]["tags"].keys())[0]
        tag = await self.client.get_tag(int(tag_id))

        self.assertIsInstance(tag, dict)
        self.assertEqual(tag["tag_id"], int(tag_id))

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_tags(self, mock_post):
        mock_post.return_value = await self._load_raw_mock_library()

        await self.client.refresh_library()
        tags = await self.client.get_tags()

        self.assertIsInstance(tags, dict)
        self.assertGreater(len(tags), 0)
        for tag_id, tag in tags.items():
            self.assertIsInstance(tag_id, int)
            self.assertIsInstance(tag, dict)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_tracks(self, mock_post):
        mock_post.return_value = await self._load_raw_mock_library()

        await self.client.refresh_library()
        tracks = await self.client.get_tracks()

        self.assertIsInstance(tracks, dict)
        self.assertGreater(len(tracks), 0)
        for track_id, track in tracks.items():
            self.assertIsInstance(track_id, int)
            self.assertIsInstance(track, dict)

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_artwork_base_url(self, mock_post):
        mock_library = await self._load_raw_mock_library()
        mock_post.return_value = mock_library

        await self.client.refresh_library()
        base_url = await self.client.get_artwork_base_url()

        self.assertIsInstance(base_url, str)
        self.assertEqual(base_url, mock_library["settings"]["artwork_server"])

    @patch(
        "ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post",
        new_callable=AsyncMock,
    )
    async def test_get_artwork_base_url_not_found(self, mock_post):
        mock_library = await self._load_raw_mock_library()
        mock_library["settings"].pop("artwork_server", None)
        mock_post.return_value = mock_library

        await self.client.refresh_library()
        with self.assertRaises(ValueError):
            await self.client.get_artwork_base_url()


if __name__ == "__main__":
    unittest.main()
