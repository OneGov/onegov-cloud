from __future__ import annotations

from tests.onegov.election_day.common import login
from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_sitemap(election_day_app_zg: TestApp) -> None:
    principal = election_day_app_zg.principal
    principal.email_notification = True
    principal.sms_notification = 'https://wab.ch/'
    election_day_app_zg.cache.set('principal', principal)

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = 'Abstimmung 1. Januar 2013'
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'Wahl 1. Januar 2013'
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # XML
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    xml = client.get('/sitemap.xml').xml
    assert xml.tag == f'{namespace}urlset'
    assert all((url.tag == f'{namespace}url') for url in xml)
    assert all(len(url) == 1 for url in xml)
    assert all(url[0].tag == f'{namespace}loc' for url in xml)
    assert {url[0].text for url in xml} == {
        'http://localhost/',
        'http://localhost/archive-search/vote',
        'http://localhost/archive/2013',
        'http://localhost/archive/2013-01-01',
        'http://localhost/election/wahl-1-januar-2013',
        'http://localhost/vote/abstimmung-1-januar-2013',
        'http://localhost/unsubscribe-email',
        'http://localhost/unsubscribe-sms',
        'http://localhost/subscribe-email',
        'http://localhost/subscribe-sms'
    }

    # JSON
    json = client.get('/sitemap.json').json
    assert json == {
        'urls': [
            'http://localhost/',
            'http://localhost/archive-search/vote',
            'http://localhost/archive/2013',
            'http://localhost/archive/2013-01-01',
            'http://localhost/election/wahl-1-januar-2013',
            'http://localhost/subscribe-email',
            'http://localhost/subscribe-sms',
            'http://localhost/unsubscribe-email',
            'http://localhost/unsubscribe-sms',
            'http://localhost/vote/abstimmung-1-januar-2013'
        ]
    }

    # HTML
    sitemap = client.get('/sitemap')
    assert 'Archivsuche' in sitemap
    assert '>2013<' in sitemap
    assert 'Urnengang vom 1. Januar 2013' in sitemap
    assert 'Abstimmung 1. Januar 2013' in sitemap
    assert 'Wahl 1. Januar 2013' in sitemap
