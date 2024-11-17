import json
import unittest
from unittest.mock import patch, AsyncMock
from aiohttp import ClientSession
from ibroadcastaio.client import IBroadcastClient

class TestIBroadcastClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session = ClientSession()
        self.client = IBroadcastClient(self.session)

    async def asyncTearDown(self):
        await self.session.close()

    @patch('ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post', new_callable=AsyncMock)
    async def test_login_success(self, mock_post):
        mock_post.return_value = {
            "user": {
                "token": "fake_token",
                "id": "fake_id"
            }
        }
        result = await self.client.login("test@example.com", "password")
        self.assertEqual(self.client._token, "fake_token")
        self.assertEqual(self.client._user_id, "fake_id")
        self.assertIn("user", result)

    @patch('ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post', new_callable=AsyncMock)
    async def test_login_failure(self, mock_post):
        mock_post.return_value = {}
        with self.assertRaises(ValueError):
            await self.client.login("test@example.com", "password")

    @patch('ibroadcastaio.client.IBroadcastClient._IBroadcastClient__post', new_callable=AsyncMock)
    async def test_refresh_library(self, mock_post):

        with open('tests/example.json', 'r') as file:
            mock_library = json.load(file)
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
                1
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
                "uid": 2
            }
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
            "sort": 1
        }

        result = []
        async for item in self.client._IBroadcastClient__jsonToDict(data, 'album_id'):
            result.append(item)

        self.assertEqual(result[0], expected_result)

if __name__ == '__main__':
    unittest.main()