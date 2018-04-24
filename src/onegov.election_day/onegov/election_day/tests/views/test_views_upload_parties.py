from datetime import date
from onegov.election_day.tests.common import create_election_compound
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_election_compound
from onegov.election_day.tests.common import upload_party_results
from onegov.election_day.tests.common import upload_proporz_election
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


def test_upload_parties_invalidate_cache(election_day_app_gr):
    anonymous = Client(election_day_app_gr)
    anonymous.get('/locale/de_CH').follow()

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()
    login(client)

    upload_proporz_election(client)
    upload_election_compound(client)
    urls = (
        '/election/proporz-election/party-strengths',
        '/elections/elections/party-strengths'
    )

    for url in urls:
        assert '49117' not in client.get(url)
        assert '49117' not in anonymous.get(url)

    upload_party_results(client)
    upload_party_results(client, slug='elections/elections')

    for url in urls:
        assert '49117' in client.get(url)
        assert '49117' in anonymous.get(url)


def test_upload_parties_submit(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    create_election_compound(client)

    for slug in ('election/election', 'elections/elections'):
        with patch(
            'onegov.election_day.views.upload.parties.import_party_results'
        ) as import_:
            import_.return_value = []

            csv = 'csv'.encode('utf-8')
            upload = client.get(f'/{slug}/upload-party-results')
            upload.form['parties'] = Upload('data.csv', csv, 'text/plain')
            upload = upload.form.submit()

            assert import_.called
