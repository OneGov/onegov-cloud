from __future__ import annotations
from urllib.parse import urlsplit


def test_url_parse_hostname() -> None:

    url = "http://stackoverflow.com/questions/1234567/blah-blah-blah-blah"
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    assert base_url == "http://stackoverflow.com/"

    url = "https://apitest.onegovgever.ch/ordnungssystem/umwelt/dossier-1811"
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))

    assert base_url == "https://apitest.onegovgever.ch/"
    url += "/"
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))

    assert base_url == "https://apitest.onegovgever.ch/"
