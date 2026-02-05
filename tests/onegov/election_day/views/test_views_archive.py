from __future__ import annotations

import transaction
import pytest

from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.utils.archive_generator import ArchiveGenerator
from tests.onegov.election_day.common import login, upload_complex_vote
from webtest import TestApp as Client
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_view_archive_no_results(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = '2013-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = '2013-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'majorz'
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
    assert "Noch keine Resultate" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Noch keine Resultate" in archive
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
    collection = ArchivedResultCollection(session)

    results = collection.query().all()
    assert len(results) == 2

    for result in results:
        session.delete(result)

    transaction.commit()

    assert collection.query().count() == 0
    assert len(client.get('/json').json['results']) == 0

    client.get('/update-results').form.submit()

    assert collection.query().count() == 2
    assert len(client.get('/json').json['results']) == 2

def test_view_archive_simple_results(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_vote(client, canton='zg')
    upload_majorz_election(client, canton='zg')

    root = client.get('/')
    assert "Majorz Election" in root
    assert "2 von 11" in root

    assert "Vote" in root
    assert "abgelehnt" in root
    assert "37.21" in root  # yeas percent
    assert "62.79" in root  # nays percent
    assert "11 von 11" in root

    archive = client.get('/archive/majorz-election')
    assert "Majorz Election" in archive
    assert "2 von 11" in archive

    archive = client.get('/archive/vote')
    assert "Vote" in archive
    assert "abgelehnt" in archive
    assert "37.21" in archive  # yeas percent
    assert "62.79" in archive  # nays percent
    assert "11 von 11" in archive


@pytest.mark.parametrize('result,expected_texts', [
    ('interim', {
        'Complex Vote',
        '',  # no result yet
        '37.37',  # yeas percentage
        '62.63',  # nays percentage
        '1 von 11',
        'Counter proposal',
        'Tie breaker',
    }),
    ('proposal declined', {
        'Complex Vote',
        'abgelehnt',  # result
        '37.21',  # yeas percentage
        '62.79',  # nays percentage
        '11 von 11',
        'Counter proposal',
        'Tie breaker',
    }),
    ('proposal accepted', {
        'Complex Vote',
        'Vorlage',  # result
        '50.98',  # yeas percentage
        '49.02',  # nays percentage
        '11 von 11',
        'Counter proposal',
        'Tie breaker',
    }),
    ('counterproposal accepted', {
        'Complex Vote',
        'Gegenentwurf',  # result
        '50.98',  # yeas percentage
        '49.02',  # nays percentage
        '11 von 11',
        'Counter proposal',
        'Tie breaker',
    }),
])
def test_view_archive_complex_results(
    election_day_app_zg: TestApp,
    result: str,
    expected_texts: str
) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)
    upload_complex_vote(client, canton='zg', result=result)

    page = client.get('/')
    for text in expected_texts:
        assert text in page

    archive = client.get('/archive/complex-vote')
    for text in expected_texts:
        assert text in archive


@pytest.mark.parametrize("url", ['vote', 'election'])
def test_view_filter_archive(url: str, election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()
    new = client.get(f'/archive-search/{url}')
    assert new.form
    assert new.form.method == 'GET'
    resp = new.form.submit()
    assert resp.status_code == 200


def test_download_archive(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    page = client.get('/')
    assert 'Gesamtes Archiv herunterladen' not in page

    login(client)
    upload_vote(client, canton='zg')
    upload_majorz_election(client, canton='zg')
    archive_generator = ArchiveGenerator(election_day_app_zg)
    assert archive_generator.generate_archive()

    archive = client.get('/').click('Gesamtes Archiv herunterladen')
    assert archive.headers['Content-Type'] == 'application/zip'
    assert len(archive.body)
