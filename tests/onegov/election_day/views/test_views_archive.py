from __future__ import annotations

import transaction
import pytest

from datetime import date
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
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

    # no municipal results exist, so the municipal archive link is hidden
    assert "Alle kommunalen Wahlen und Abstimmungen" not in archive

    municipal = client.get('/archive/municipal')
    assert "Es sind noch keine kommunalen Wahlen und Abstimmungen verfügbar." \
        in municipal

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
        'Gegenentwurf/Gegenvorschlag',  # default title counterproposal
        'Stichfrage',  # default title tie-breaker
    }),
    ('proposal declined', {
        'Complex Vote',
        'abgelehnt',  # result
        '37.21',  # yeas percentage
        '62.79',  # nays percentage
        '11 von 11',
        'Gegenentwurf/Gegenvorschlag',  # default title counterproposal
        'Stichfrage',  # default title tie-breaker
    }),
    ('proposal accepted', {
        'Complex Vote',
        'Vorlage',  # result
        '50.98',  # yeas percentage
        '49.02',  # nays percentage
        '11 von 11',
        'Gegenentwurf/Gegenvorschlag',  # default title counterproposal
        'Stichfrage',  # default title tie-breaker
    }),
    ('counterproposal accepted', {
        'Complex Vote',
        'Gegenentwurf',  # result
        '50.98',  # yeas percentage
        '49.02',  # nays percentage
        '11 von 11',
        'Gegenentwurf/Gegenvorschlag',  # default title counterproposal
        'Stichfrage',  # default title tie-breaker
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


def _add_municipal_results(app: TestApp) -> None:
    """Add two municipalities (Au, Wil) with results across two years."""
    session = app.session()
    for domain_segment, title, result_date, result_type in (
        ('au', 'Au Abstimmung 2025', date(2025, 5, 18), 'vote'),
        ('au', 'Au Wahl 2024', date(2024, 3, 3), 'election'),
        ('wil', 'Wil Abstimmung 2025', date(2025, 5, 18), 'vote'),
    ):
        session.add(ArchivedResult(
            date=result_date,
            type=result_type,
            domain='municipality',
            name=domain_segment,
            url=f'https://example.com/{result_type}/{domain_segment}',
            title_translations={'de_CH': title},
            meta={'domain_segment': domain_segment},
            schema='other-instance',
        ))
    transaction.commit()


def test_view_archive_all_municipal(election_day_app_sg: TestApp) -> None:
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    # link to communal results does not exist
    main = client.get('/')
    assert 'Alle kommunalen Wahlen und Abstimmungen' not in main

    _add_municipal_results(election_day_app_sg)

    page = client.get('/archive/municipal')
    assert 'Kommunale Wahlen und Abstimmungen nach Gemeinde' in page

    # year-specific URL when results exist; au has 2024 + 2025 so latest
    # is 2025
    assert '/municipality/au/2025' in page
    assert '/municipality/wil/2025' in page

    # slug resolved to proper display name
    assert 'Au (SG)' in page
    assert 'Wil (SG)' in page

    # municipality with no results is not listed at all
    assert '/municipality/rorschach' not in page

    # only links shown, no inline result titles
    assert 'Au Abstimmung 2025' not in page
    assert 'Au Wahl 2024' not in page

    # link to communal results exists
    main = client.get('/')
    assert 'Alle kommunalen Wahlen und Abstimmungen' in main


def test_view_archive_all_municipal_link_hidden_for_cantonal_vote(
    election_day_app_sg: TestApp
) -> None:
    # a cantonal/national vote is not a communal vote, so it must not surface
    # the all-municipal link even though its results are in the archive
    session = election_day_app_sg.session()
    session.add(ArchivedResult(
        date=date(2025, 5, 18),
        type='vote',
        domain='canton',
        name='kantonal',
        url='https://example.com/vote/kantonal',
        title_translations={'de_CH': 'Kantonale Abstimmung'},
        meta={'id': 'kantonal'},
        schema=election_day_app_sg.schema,
    ))
    transaction.commit()

    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    # the cantonal vote is shown, but there is no all-municipal link ...
    archive = client.get('/archive/2025-05-18')
    assert 'Kantonale Abstimmung' in archive
    assert 'Alle kommunalen Wahlen und Abstimmungen' not in archive

    # ... and the all-municipal page shows the empty state
    page = client.get('/archive/municipal')
    assert 'Es sind noch keine kommunalen Wahlen und Abstimmungen verfügbar.' \
        in page


def test_view_archive_municipal_by_date(election_day_app_sg: TestApp) -> None:
    _add_municipal_results(election_day_app_sg)
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    page = client.get('/archive/2025-05-18/municipal')
    assert 'Au' in page
    assert 'Wil' in page
    assert '/municipality/au/2025' in page
    assert '/municipality/wil/2025' in page
    assert '/municipality/au"' not in page
    assert '/municipality/wil"' not in page
    assert 'Au Wahl 2024' not in page


def test_view_archive_municipality(election_day_app_sg: TestApp) -> None:
    _add_municipal_results(election_day_app_sg)
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    page = client.get('/municipality/au')
    assert 'Au Abstimmung 2025' in page
    assert 'Au Wahl 2024' in page
    # Wil's item isn't shown
    assert 'Wil Abstimmung 2025' not in page
    # Year archive footer: both years present as links
    assert '/municipality/au/2025' in page
    assert '/municipality/au/2024' in page
    # "All" shown as plain text (no year filter active)
    assert 'href="/municipality/au"' not in page


def test_view_archive_municipality_year(election_day_app_sg: TestApp) -> None:
    _add_municipal_results(election_day_app_sg)
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    page = client.get('/municipality/au/2025')
    assert 'Au Abstimmung 2025' in page
    # 2024 item filtered out
    assert 'Au Wahl 2024' not in page
    # "All" shown as a link back to /municipality/au
    assert '/municipality/au"' in page
    # 2024 year link present; 2025 shown as plain text (current)
    assert '/municipality/au/2024' in page
    assert 'href="/municipality/au/2025"' not in page


def test_view_municipality_redirect(election_day_app_sg: TestApp) -> None:
    _add_municipal_results(election_day_app_sg)
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    response = client.get('/gemeinde/au')
    assert response.status_int == 302
    assert response.location is not None
    assert response.location.endswith('/municipality/au')
