import onegov.election_day

from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.election_day.tests.common import create_election_compound
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_majorz_election
from onegov.election_day.tests.common import upload_proporz_election
from onegov.election_day.tests.common import upload_vote
from onegov_testing import utils
from unittest.mock import patch
from webtest import TestApp as Client
from xml.etree.ElementTree import fromstring


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.election_day, onegov.election_day.ElectionDayApp)


def test_i18n(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Foo'
    new.form['vote_fr'] = 'Bar'
    new.form['vote_it'] = 'Baz'
    new.form['vote_rm'] = 'Qux'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Foo" in homepage

    homepage = homepage.click('Français').follow()
    assert "Bar" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Baz" in homepage

    homepage = homepage.click('Rumantsch').follow()
    assert "Qux" in homepage

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Tick'
    new.form['election_fr'] = 'Trick'
    new.form['election_it'] = 'Track'
    new.form['election_rm'] = 'Quack'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    homepage = client.get('/')
    assert "Quack" in homepage

    homepage = homepage.click('Français').follow()
    assert "Trick" in homepage

    homepage = homepage.click('Italiano').follow()
    assert "Track" in homepage

    homepage = homepage.click('Deutsch').follow()
    assert "Tick" in homepage


def test_pages_cache(election_day_app):
    principal = election_day_app.principal
    principal.open_data = {
        'id': 'kanton-govikon',
        'mail': 'info@govikon',
        'name': 'Staatskanzlei Kanton Govikon'
    }
    election_day_app.cache.set('principal', principal)

    client = Client(election_day_app)
    client.get('/locale/de_CH')

    # make sure codes != 200 are not cached
    anonymous = Client(election_day_app)
    anonymous.get('/vote/0xdeadbeef/entities', status=404)

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = '0xdeadbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef/entities')
    assert '0xdeadbeef' in anonymous.get('/catalog.rdf')

    edit = client.get('/vote/0xdeadbeef/edit')
    edit.form['vote_de'] = '0xdeadc0de'
    edit.form.submit()

    assert '0xdeadc0de' in client.get('/')
    assert '0xdeadc0de' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef/entities')
    assert '0xdeadc0de' in anonymous.get('/vote/0xdeadbeef/entities', headers=[
        ('Cache-Control', 'no-cache')
    ])

    assert '0xdeadc0de' in client.get('/catalog.rdf')
    assert '0xdeadc0de' not in anonymous.get('/catalog.rdf')
    assert '0xdeadc0de' in anonymous.get('/catalog.rdf', headers=[
        ('Cache-Control', 'no-cache')
    ])


def test_view_last_modified(election_day_app):
    with freeze_time("2014-01-01 12:00"):
        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        login(client)

        new = client.get('/manage/votes/new-vote')
        new.form['vote_type'] = "complex"
        new.form['vote_de'] = "Vote"
        new.form['date'] = date(2013, 1, 1)
        new.form['domain'] = 'federation'
        new.form.submit()

        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = "Election"
        new.form['date'] = date(2013, 1, 1)
        new.form['mandates'] = 1
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'region'
        new.form.submit()

        new = client.get('/manage/election-compounds/new-election-compound')
        new.form['election_de'] = "Elections"
        new.form['date'] = date(2013, 1, 1)
        new.form['elections'] = ['election']
        new.form['domain'] = 'canton'
        new.form.submit()

        client = Client(election_day_app)
        client.get('/locale/de_CH').follow()

        for path in (
            '/json',
            '/election/election/summary',
            '/election/election/json',
            '/election/election/data-json',
            '/election/election/data-csv',
            '/elections/elections/summary',
            '/elections/elections/json',
            '/elections/elections/data-json',
            '/elections/elections/data-csv',
            '/vote/vote/summary',
            '/vote/vote/json',
            '/vote/vote/data-json',
            '/vote/vote/data-csv',
        ):
            assert client.get(path).headers.get('Last-Modified') == \
                'Wed, 01 Jan 2014 12:00:00 GMT'

        for path in (
            '/'
            '/archive/2013',
            '/election/election',
            '/election/election/lists',
            '/election/election/candidates',
            '/election/election/statistics',
            '/election/election/',
            '/election/election/party-strengths',
            '/election/election/data',
            '/elections/elections',
            '/elections/elections/districts',
            '/elections/elections/data',
            '/vote/vote/',
            '/vote/vote/counter-proposal-entities',
            '/vote/vote/tie-breaker-entities',
        ):
            assert 'Last-Modified' not in client.get(path).headers


def test_view_headerless(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')

    for path in (
        '/',
        '/archive/2013',
        '/election/majorz-election/candidates',
        '/election/majorz-election/statistics',
        '/election/majorz-election/data',
        '/vote/vote/entities',
    ):
        assert 'manage-links' in client.get(path)
        assert 'manage-links' not in client.get(path + '?headerless')
        assert 'manage-links' not in client.get(path)
        assert 'manage-links' in client.get(path + '?headerful')
        assert 'manage-links' in client.get(path)


def test_view_pdf(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')

    paths = (
        '/vote/vote/pdf',
        '/election/majorz-election/pdf',
        '/election/proporz-election/pdf',
    )
    for path in paths:
        assert client.get(path, expect_errors=True).status_code == 503

    pdf = '%PDF-1.6'.encode('utf-8')
    election_day_app.filestorage.makedir('pdf')
    with election_day_app.filestorage.open('pdf/test.pdf', 'wb') as f:
        f.write(pdf)

    filenames = []
    with patch('onegov.election_day.layouts.vote.pdf_filename',
               return_value='test.pdf'):
        result = client.get('/vote/vote/pdf')
        assert result.body == pdf
        assert result.headers['Content-Type'] == 'application/pdf'
        assert result.headers['Content-Length'] == '8'
        assert result.headers['Content-Disposition'].startswith(
            'inline; filename='
        )
        filenames.append(
            result.headers['Content-Disposition'].split('filename=')[1]
        )
    with patch('onegov.election_day.layouts.election.pdf_filename',
               return_value='test.pdf'):
        result = client.get('/election/majorz-election/pdf')
        assert result.body == pdf
        assert result.headers['Content-Type'] == 'application/pdf'
        assert result.headers['Content-Length'] == '8'
        assert result.headers['Content-Disposition'].startswith(
            'inline; filename='
        )
        filenames.append(
            result.headers['Content-Disposition'].split('filename=')[1]
        )

        result = client.get('/election/proporz-election/pdf')
        assert result.body == pdf
        assert result.headers['Content-Type'] == 'application/pdf'
        assert result.headers['Content-Length'] == '8'
        assert result.headers['Content-Disposition'].startswith(
            'inline; filename='
        )
        filenames.append(
            result.headers['Content-Disposition'].split('filename=')[1]
        )

    assert sorted(filenames) == [
        'majorz-election.pdf',
        'proporz-election.pdf',
        'vote.pdf'
    ]


def test_view_svg(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')

    ballot_id = election_day_app.session().query(Ballot).one().id
    paths = (
        f'/ballot/{ballot_id}/entities-map-svg',
        f'/ballot/{ballot_id}/districts-map-svg',
        '/election/majorz-election/candidates-svg',
        '/election/proporz-election/lists-svg',
        '/election/proporz-election/candidates-svg',
        '/election/proporz-election/lists-panachage-svg',
        '/election/proporz-election/connections-svg',
        '/election/proporz-election/party-strengths-svg',
    )
    for path in paths:
        assert client.get(path, expect_errors=True).status_code == 503

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.0" ></svg>'
    ).encode('utf-8')
    election_day_app.filestorage.makedir('svg')
    with election_day_app.filestorage.open('svg/test.svg', 'wb') as f:
        f.write(svg)

    filenames = []
    with patch('onegov.election_day.layouts.vote.svg_filename',
               return_value='test.svg'):
        for path in paths[:2]:
            result = client.get(paths[0])
            assert result.body == svg
            assert result.headers['Content-Type'] == (
                'application/svg; charset=utf-8'
            )
            assert result.headers['Content-Length'] == '99'
            assert result.headers['Content-Disposition'].startswith(
                'inline; filename='
            )
            filenames.append(
                result.headers['Content-Disposition'].split('filename=')[1]
            )
    with patch('onegov.election_day.layouts.election.svg_filename',
               return_value='test.svg'):
        for path in paths[2:]:
            result = client.get(path)
            assert result.body == svg
            assert result.headers['Content-Type'] == (
                'application/svg; charset=utf-8'
            )
            assert result.headers['Content-Length'] == '99'
            assert result.headers['Content-Disposition'].startswith(
                'inline; filename='
            )
            filenames.append(
                result.headers['Content-Disposition'].split('filename=')[1]
            )
    assert sorted(filenames) == [
        'majorz-election-kandidierende.svg',
        'proporz-election-kandidierende.svg',
        'proporz-election-listen-listenverbindungen.svg',
        'proporz-election-listen-panaschierstatistik.svg',
        'proporz-election-listen.svg',
        'proporz-election-parteien-parteistaerken.svg',
        'vote-vorlage.svg',
        'vote-vorlage.svg'
    ]


def test_opendata_catalog(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    # Not configured
    response = client.get('/catalog.rdf', expect_errors=True)
    assert response.status_code == 501

    principal = election_day_app.principal
    principal.open_data = {
        'id': 'kanton-govikon',
        'mail': 'info@govikon',
        'name': 'Staatskanzlei Kanton Govikon'
    }
    election_day_app.cache.set('principal', principal)

    # Empty
    root = fromstring(client.get('/catalog.rdf').text)
    assert root.tag.lower().endswith('rdf')
    assert len(root[0].getchildren()) == 0

    # With data
    login(client)
    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')
    create_election_compound(client)

    root = fromstring(client.get('/catalog.rdf').text)
    assert set([
        x[0][0].text
        for x in root.findall('.//{http://purl.org/dc/terms/}publisher')
    ]) == {'Staatskanzlei Kanton Govikon'}
    assert set([
        list(x.attrib.values())[0]
        for x in root.findall('.//{http://www.w3.org/2006/vcard/ns#}hasEmail')
    ]) == {'mailto:info@govikon'}
    assert set([
        x.text for x in root.findall('.//{http://purl.org/dc/terms/}title')
    ]) == {
        'Majorz Election',
        'majorz-election.csv',
        'majorz-election.json',
        'Proporz Election',
        'proporz-election.csv',
        'proporz-election.json',
        'Regional Election A',
        'regional-election-a.csv',
        'regional-election-a.json',
        'Regional Election B',
        'regional-election-b.csv',
        'regional-election-b.json',
        'Elections',
        'elections.csv',
        'elections.json',
        'Vote',
        'vote.csv',
        'vote.json'
    }
    assert set([list(x[0].attrib.values())[0] for x in root[0]]) == {
        'http://kanton-govikon/election-majorz-election',
        'http://kanton-govikon/election-proporz-election',
        'http://kanton-govikon/election-regional-election-a',
        'http://kanton-govikon/election-regional-election-b',
        'http://kanton-govikon/election-elections',
        'http://kanton-govikon/vote-vote'
    }
