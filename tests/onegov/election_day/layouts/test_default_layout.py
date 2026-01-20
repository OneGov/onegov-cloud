from __future__ import annotations

from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


from typing import Any


def test_default_layout() -> None:
    layout_de = DefaultLayout(None, DummyRequest(locale='de'))  # type: ignore[arg-type]
    layout_en = DefaultLayout(None, DummyRequest(locale='en'))  # type: ignore[arg-type]
    layout_fr = DefaultLayout(None, DummyRequest(locale='fr'))  # type: ignore[arg-type]
    layout_it = DefaultLayout(None, DummyRequest(locale='it'))  # type: ignore[arg-type]
    layout_rm = DefaultLayout(None, DummyRequest(locale='rm'))  # type: ignore[arg-type]

    request: Any = DummyRequest()
    model = Vote()
    layout = DefaultLayout(model, request)
    assert layout.principal == request.app.principal
    assert layout.has_districts is False
    assert layout.has_regions is False
    assert layout.has_superregions is False

    assert layout_de.homepage_link == 'DummyPrincipal/archive'
    assert layout_en.homepage_link == 'DummyPrincipal/archive'

    assert layout_de.manage_link == 'VoteCollection/archive'
    assert layout_en.manage_link == 'VoteCollection/archive'

    assert layout_de.get_topojson_link('ag', 2015)
    assert layout_en.get_topojson_link('ag', 2015)

    assert layout_de.terms_link == 'https://opendata.swiss/de/terms-of-use'
    assert layout_en.terms_link == 'https://opendata.swiss/en/terms-of-use'
    assert layout_fr.terms_link == 'https://opendata.swiss/fr/terms-of-use'
    assert layout_it.terms_link == 'https://opendata.swiss/it/terms-of-use'
    assert layout_rm.terms_link == 'https://opendata.swiss/rm/terms-of-use'

    base_url = (
        'https://github.com/OneGov/onegov-cloud/blob/master/src'
        '/onegov/election_day/static/docs/api/'
    )

    assert layout_de.opendata_link == (
        base_url + 'open_data_de.md'
    )
    assert layout_en.opendata_link == (
        base_url + 'open_data_en.md'
    )
    assert layout_fr.opendata_link == (
        base_url + 'open_data_fr.md'
    )
    assert layout_it.opendata_link == (
        base_url + 'open_data_it.md'
    )
    assert layout_rm.opendata_link == (
        base_url + 'open_data_rm.md'
    )

    assert layout_de.format_description_link == (
        base_url + 'format__de.md'
    )
    assert layout_en.format_description_link == (
        base_url + 'format__en.md'
    )
    assert layout_fr.format_description_link == (
        base_url + 'format__fr.md'
    )
    assert layout_it.format_description_link == (
        base_url + 'format__it.md'
    )
    assert layout_rm.format_description_link == (
        base_url + 'format__rm.md'
    )

    assert layout_de.login_link == 'Auth/login'
    assert layout_de.logout_link is None
    assert layout_de.archive_search_link == (
        "SearchableArchivedResultCollection//{'item_type': 'vote'}"
    )

    layout_de = DefaultLayout(
        None, DummyRequest(locale='de', is_logged_in=True)  # type: ignore[arg-type]
    )

    assert layout_de.login_link is None
    assert layout_de.logout_link == 'Auth/logout'
