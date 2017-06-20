from datetime import date
from onegov.election_day.tests import login
from onegov.election_day.tests import upload_party_results
from onegov.election_day.tests import upload_proporz_election
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


def test_upload_parties_invalidate_cache(election_day_app):
    anonymous = Client(election_day_app)
    anonymous.get('/locale/de_CH').follow()

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_proporz_election(client, canton='zg')

    assert '49117' not in client.get('/election/proporz-election/parties')
    assert '49117' not in anonymous.get('/election/proporz-election/parties')

    upload_party_results(client)

    assert '49117' in client.get('/election/proporz-election/parties')
    assert '49117' in anonymous.get('/election/proporz-election/parties')


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

    with patch(
        'onegov.election_day.views.upload.parties.import_party_results'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/election/upload-party-results')
        upload.form['parties'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
