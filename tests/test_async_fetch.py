import pytest
from aiohttp import InvalidURL

from async_fetch import async_aiohttp_get_all

valid_urls = [
    'https://seantis.ch',
    'https://www.google.ch',
]

invalid_urls = [
    'invalid.url.com'
]


@pytest.mark.parametrize('url', invalid_urls)
def test_fetch_all_invalid(url):

    def handle_invalid(url, exception):
        if isinstance(exception, InvalidURL):
            return str(exception)
        else:
            raise exception

    with pytest.raises(InvalidURL):
        async_aiohttp_get_all([url])

    results = async_aiohttp_get_all(
        [url], handle_exceptions=handle_invalid)

    assert isinstance(results[0], str)


def test_fetch_all_valid():
    # get status 200 without waiting for the content
    results = async_aiohttp_get_all(valid_urls, response_attr='status')
    assert results == [200, 200]
