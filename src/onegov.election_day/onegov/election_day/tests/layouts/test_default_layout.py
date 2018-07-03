from onegov.ballot import Vote
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.tests.common import DummyRequest


def test_default_layout():
    layout_de = DefaultLayout(None, DummyRequest(locale='de'))
    layout_en = DefaultLayout(None, DummyRequest(locale='en'))
    layout_fr = DefaultLayout(None, DummyRequest(locale='fr'))
    layout_it = DefaultLayout(None, DummyRequest(locale='it'))
    layout_rm = DefaultLayout(None, DummyRequest(locale='rm'))

    request = DummyRequest()
    model = Vote()
    layout = DefaultLayout(model, request)
    assert layout.principal == request.app.principal
    assert layout.has_districts is False

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

    assert layout_de.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_de.md'
    )
    assert layout_en.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_en.md'
    )
    assert layout_fr.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_fr.md'
    )
    assert layout_it.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_it.md'
    )
    assert layout_rm.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_rm.md'
    )

    assert layout_de.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__de.md'
    )
    assert layout_en.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__en.md'
    )
    assert layout_fr.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__fr.md'
    )
    assert layout_it.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__it.md'
    )
    assert layout_rm.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__rm.md'
    )

    assert layout_de.login_link == 'Auth/login'
    assert layout_de.logout_link is None

    layout_de = DefaultLayout(
        None, DummyRequest(locale='de', is_logged_in=True)
    )

    assert layout_de.login_link is None
    assert layout_de.logout_link == 'Auth/logout'
