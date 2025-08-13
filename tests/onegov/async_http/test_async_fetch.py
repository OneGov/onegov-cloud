from __future__ import annotations

import pytest
from aiohttp import InvalidURL

from onegov.async_http.fetch import async_aiohttp_get_all
from onegov.core.utils import Bunch


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.async_http.fetch import UrlType

valid_urls = [
    'https://seantis.ch',
    'https://www.google.ch',
]

invalid_urls: list[Any] = [
    'invalid.url.com',
    Bunch(url='xxx', name='Failed')
]


def test_fetch_all_invalid() -> None:

    def callback(url: UrlType, response: object) -> UrlType:
        return url

    def handle_invalid(url: UrlType, exception: Exception) -> str:
        if isinstance(exception, InvalidURL):
            if isinstance(url, Bunch):
                return url.name
            return str(exception)
        else:
            raise exception

    with pytest.raises(InvalidURL):
        async_aiohttp_get_all(invalid_urls[0])

    results = async_aiohttp_get_all(
        invalid_urls,
        callback=callback,
        handle_exceptions=handle_invalid
    )

    assert isinstance(results[0], str)
    assert results[1] == 'Failed'


def test_fetch_all_valid() -> None:
    # get status 200 without waiting for the content
    results = async_aiohttp_get_all(valid_urls, response_attr='status')
    assert results == list(zip(valid_urls, [200, 200]))
