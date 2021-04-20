import pytest
from aiohttp import InvalidURL

from async_fetch import async_aiohttp_get_all
from onegov.core.utils import Bunch

valid_urls = [
    'https://seantis.ch',
    'https://www.google.ch',
]

invalid_urls = [
    'invalid.url.com',
    Bunch(url='xxx', name='Failed')
]


@pytest.mark.parametrize('url', invalid_urls)
def test_fetch_all_invalid(url):

    def handle_invalid(url, exception):
        if isinstance(exception, InvalidURL):
            if isinstance(url, Bunch):
                return url.name
            return str(exception)
        else:
            raise exception

    with pytest.raises(InvalidURL):
        async_aiohttp_get_all(invalid_urls[0])

    results = async_aiohttp_get_all(
        invalid_urls, handle_exceptions=handle_invalid)

    assert isinstance(results[0], str)
    assert results[1] == 'Failed'


def test_fetch_all_valid():
    # get status 200 without waiting for the content
    results = async_aiohttp_get_all(valid_urls, response_attr='status')
    assert results == list(zip(valid_urls, [200, 200]))
