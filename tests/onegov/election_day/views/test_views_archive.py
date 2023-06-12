import transaction
import pytest
from onegov.election_day.collections import ArchivedResultCollection
from tests.onegov.election_day.common import login
from webtest import TestApp as Client


def test_view_archive(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # Current
    current = client.get('/')
    assert "Abstimmung 1. Januar 2013" in current
    assert "Wahl 1. Januar 2013" in current

    # ... JSON
    current = client.get('/json')
    assert list(current.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in current
    assert "Wahl 1. Januar 2013" in current
    assert current.headers['Access-Control-Allow-Origin'] == '*'

    # 2013
    assert "archive/2013" in client.get('/')

    archive = client.get('/archive/2013')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02')
    assert "noch keine Wahlen oder Abstimmungen" in archive

    # ... JSON
    archive = client.get('/archive/2013/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive
    assert archive.headers['Access-Control-Allow-Origin'] == '*'

    archive = client.get('/archive/2013-01-01/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive
    assert archive.headers['Access-Control-Allow-Origin'] == '*'

    archive = client.get('/archive/2013-02-02/json')
    assert list(archive.json['archive'].keys()) == ['2013']
    assert archive.json['results'] == []
    assert archive.headers['Access-Control-Allow-Origin'] == '*'

    # Update results
    assert len(client.get('/json').json['results']) == 2

    session = election_day_app_zg.session()
    archive = ArchivedResultCollection(session)

    results = archive.query().all()
    assert len(results) == 2

    for result in results:
        session.delete(result)

    transaction.commit()

    results = archive.query().count() == 0
    assert len(client.get('/json').json['results']) == 0

    client.get('/update-results').form.submit()

    results = archive.query().count() == 2
    assert len(client.get('/json').json['results']) == 2


@pytest.mark.parametrize("url", ['vote', 'election'])
def test_view_filter_archive(url, election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()
    new = client.get(f'/archive-search/{url}')
    assert new.form
    assert new.form.method == 'GET'
    resp = new.form.submit()
    assert resp.status_code == 200


def test_download_archive_link_click(election_day_app_zg, session):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Abstimmung 1. Januar 2022'
    new.form['date'] = '2022-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2022"
    new.form['date'] = '2022-01-01'
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    page = client.get('/')
    # archive not generated, so we don't show the download button
    assert 'Gesamtes Archiv herunterladen' not in page
