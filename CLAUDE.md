# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**iBroadcastAIO** is an async Python client library for the [iBroadcast API](https://devguide.ibroadcast.com/). It was built primarily for use in [Music Assistant](https://music-assistant.io/) as an iBroadcast music provider.

- Python 3.11+, Poetry-managed
- Async-first design using `aiohttp`
- Currently v0.5.0

## Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run python -m unittest discover -s tests

# Run a single test
poetry run python -m unittest tests.test_client.TestIBroadcastClient.<test_name>

# Format
black ibroadcastaio tests
isort ibroadcastaio tests --profile black

# Lint
ruff check ibroadcastaio tests
flake8 ibroadcastaio tests --max-line-length=160
mypy ibroadcastaio --python-version=3.11

# Run all pre-commit checks
pre-commit run --all-files

# Build / publish
poetry build
poetry publish
```

## Code Structure

```
ibroadcastaio/
├── __init__.py     # Exports IBroadcastClient
├── client.py       # Main client class (~324 lines)
└── const.py        # API base URLs and constants

tests/
└── test_client.py  # 30+ async unittest cases
```

The library has a single public class `IBroadcastClient` in [ibroadcastaio/client.py](ibroadcastaio/client.py). Everything is accessed through it.

## Architecture

**Two-phase usage:**
1. `login(username, password)` — authenticates, stores `_user_token`, `_user_id`, and `_status`
2. `refresh_library()` — fetches the full library and caches it in memory as `_albums`, `_artists`, `_tracks`, `_playlists`, `_tags`, `_settings`

After `refresh_library()`, all `get_*()` methods read from in-memory dicts. There is a noted TODO to replace this with fine-grained API calls per entity rather than a full library dump.

**iBroadcast's compressed format:** The API returns arrays instead of objects for efficiency. `__json_to_dict()` is an async generator that converts these index-based arrays to readable dicts using field maps defined at the top of `client.py` (e.g. `TRACKS_MAP`, `ALBUMS_MAP`).

**URL construction:**
- Artwork: `{artwork_server}/artwork/{artwork_id}-300`
- Stream: `{streaming_server}{file_path}?Signature={token}&file_id={id}&user_id={uid}&platform={platform}&version={version}`

Base URLs for artwork/stream are fetched from `_settings` (populated during `refresh_library()`).

## Code Style

- Line length: 100 chars (ruff), 160 chars (flake8)
- Strict mypy: `disallow_untyped_defs`, `disallow_untyped_calls`, `check_untyped_defs`
- Docstrings: PEP257 convention (ruff D rule group)
- Import order: black-compatible (isort profile=black)

## Testing

Tests in `tests/test_client.py` use `unittest.IsolatedAsyncioTestCase`. They mock `aiohttp.ClientSession.post` and load fixture data from `tests/example.json` (not committed — gitignored as `example-rob.json`; tests may use a bundled fixture).

When adding tests, follow the existing mock pattern using `unittest.mock.AsyncMock`.
