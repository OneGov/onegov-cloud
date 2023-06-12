from freezegun import freeze_time
from onegov import election_day
from onegov.ballot import Ballot
from onegov.ballot import Vote
from onegov.election_day import ElectionDayApp
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_party_results
from tests.onegov.election_day.common import upload_proporz_election
from tests.onegov.election_day.common import upload_vote
from tests.shared import utils
from transaction import commit
from transaction import begin
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload
from xml.etree.ElementTree import fromstring


def test_view_permissions():
    utils.assert_explicit_permissions(election_day, ElectionDayApp)


def test_i18n(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Foo'
    new.form['vote_fr'] = 'Bar'
    new.form['vote_it'] = 'Baz'
    new.form['vote_rm'] = 'Qux'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Foo" in client.get('/')
    assert "Baz" in client.get('/?locale=it_CH')
    assert "Foo" in client.get('/?locale=en_US')
    assert "Bar" in client.get('/').click('Français').follow()
    assert "Baz" in client.get('/').click('Italiano').follow()
    assert "Qux" in client.get('/').click('Rumantsch').follow()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Tick'
    new.form['election_fr'] = 'Trick'
    new.form['election_it'] = 'Track'
    new.form['election_rm'] = 'Quack'
    new.form['date'] = '2015-01-01'
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "Quack" in client.get('/')
    assert "Track" in client.get('/?locale=it_CH')
    assert "Quack" in client.get('/?locale=en_US')
    assert "Trick" in client.get('/').click('Français').follow()
    assert "Track" in client.get('/').click('Italiano').follow()
    assert "Tick" in client.get('/').click('Deutsch').follow()


def test_cache_control(election_day_app_zg):
    client = Client(election_day_app_zg)

    response = client.get('/')
    assert 'cache-control' not in response.headers
    assert 'no_cache' not in response.headers['Set-Cookie']
    assert 'no_cache' not in client.cookies

    login(client)

    response = client.get('/')
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['Set-Cookie'] == 'no_cache=1; Path=/; SameSite=Lax'
    assert client.cookies['no_cache'] == '1'

    response = client.get('/')
    assert response.headers['cache-control'] == 'no-store'
    assert 'Set-Cookie' not in response.headers
    assert client.cookies['no_cache'] == '1'

    client.get('/auth/logout?to=/')

    response = client.get('/')
    assert 'cache-control' not in response.headers
    assert 'no_cache=;' in response.headers['Set-Cookie']
    assert 'no_cache' not in client.cookies


def test_content_security_policy(election_day_app_zg):
    principal = election_day_app_zg.principal
    principal.csp_script_src = ('https://scripts.onegov.cloud', )
    principal.csp_connect_src = ('https://data.onegov.cloud', )
    election_day_app_zg.cache.set('principal', principal)

    client = Client(election_day_app_zg)

    # create vote
    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    # check content security policy
    response = client.get('/')
    csp = response.headers['Content-Security-Policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp.split(';')}
    assert "frame-ancestors" not in csp
    assert "https://scripts.onegov.cloud" in csp['script-src']
    assert "https://data.onegov.cloud" in csp['connect-src']

    response = client.get('/auth/login')
    csp = response.headers['Content-Security-Policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp.split(';')}
    assert "'none'" in csp['frame-ancestors']
    assert "https://scripts.onegov.cloud" in csp['script-src']
    assert "https://data.onegov.cloud" in csp['connect-src']

    response = client.get('/vote/vote')
    csp = response.headers['Content-Security-Policy']
    csp = {v.split(' ')[0]: v.split(' ', 1)[-1] for v in csp.split(';')}
    assert "http://* https://*" in csp['frame-ancestors']
    assert "https://scripts.onegov.cloud" in csp['script-src']
    assert "https://data.onegov.cloud" in csp['connect-src']


def test_pages_cache(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH')

    # make sure codes != 200 are not cached
    anonymous = Client(election_day_app_zg)
    anonymous.get('/vote/0xdeadbeef/entities', status=404)
    assert len(election_day_app_zg.pages_cache.keys()) == 0

    # create vote
    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = '0xdeadbeef'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    # make sure set-cookies are not cached
    client.get('/auth/logout')
    response = login(client, to='/vote/0xdeadbeef/entities').follow()
    assert 'Set-Cookie' in response.headers  # no_cache
    assert len(election_day_app_zg.pages_cache.keys()) == 0

    anonymous = Client(election_day_app_zg)
    response = anonymous.get('/vote/0xdeadbeef/entities')
    assert 'Set-Cookie' in response.headers  # session_id
    assert len(election_day_app_zg.pages_cache.keys()) == 0

    # make sure HEAD requests are not cached
    anonymous.head('/vote/0xdeadbeef/')
    assert len(election_day_app_zg.pages_cache.keys()) == 0

    # Create cache entries
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef/entities')
    assert len(election_day_app_zg.pages_cache.keys()) == 1

    # Modify without invalidating the cache
    begin()
    election_day_app_zg.session().query(Vote).one().title = '0xdeadc0de'
    commit()

    assert '0xdeadc0de' not in anonymous.get('/vote/0xdeadbeef/entities')
    assert '0xdeadc0de' in anonymous.get(
        '/vote/0xdeadbeef/entities',
        headers=[('Cache-Control', 'no-cache')]
    )
    assert '0xdeadc0de' in client.get('/vote/0xdeadbeef/entities')

    # Modify with invalidating the cache
    edit = client.get('/vote/0xdeadbeef/edit')
    edit.form['vote_de'] = '0xd3adc0d3'
    edit.form.submit()

    assert '0xd3adc0d3' in anonymous.get('/vote/0xdeadbeef/entities')
    assert '0xd3adc0d3' in anonymous.get(
        '/vote/0xdeadbeef/entities',
        headers=[('Cache-Control', 'no-cache')]
    )
    assert '0xd3adc0d3' in client.get('/vote/0xdeadbeef/entities')


def test_view_last_modified(election_day_app_sg):
    with freeze_time("2014-01-01 12:00"):
        client = Client(election_day_app_sg)
        client.get('/locale/de_CH').follow()

        login(client)

        new = client.get('/manage/votes/new-vote')
        new.form['vote_type'] = "complex"
        new.form['vote_de'] = "Vote"
        new.form['date'] = '2013-01-01'
        new.form['domain'] = 'federation'
        new.form.submit()

        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = "Election"
        new.form['date'] = '2013-01-01'
        new.form['mandates'] = 1
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'municipality'
        new.form.submit()

        new = client.get('/manage/election-compounds/new-election-compound')
        new.form['election_de'] = "Elections"
        new.form['date'] = '2013-01-01'
        new.form['municipality_elections'] = ['election']
        new.form['domain'] = 'canton'
        new.form['domain_elections'] = 'municipality'
        new.form.submit()

        client = Client(election_day_app_sg)
        client.get('/locale/de_CH').follow()

        modified = 'Wed, 01 Jan 2014 12:00:00 GMT'

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
            '/elections-part/elections/district/Wil/summary',
            '/elections-part/elections/district/Wil/json',
            '/vote/vote/summary',
            '/vote/vote/json',
            '/vote/vote/data-json',
            '/vote/vote/data-csv',
        ):
            assert client.get(path).headers.get('Last-Modified') == modified
        for path in (
            '/election/election',
            '/elections/elections',
            '/elections-part/elections/district/Wil',
            '/vote/vote',
        ):
            assert client.head(path).headers.get('Last-Modified') == modified

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
            '/elections-part/elections/district/Wil',
            '/elections-part/elections/district/Wil/districts',
            '/vote/vote/',
            '/vote/vote/counter-proposal-entities',
            '/vote/vote/tie-breaker-entities',
        ):
            assert 'Last-Modified' not in client.get(path).headers


def test_view_headerless(election_day_app_zg):
    client = Client(election_day_app_zg)
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


def test_view_pdf(election_day_app_zg):
    client = Client(election_day_app_zg)
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
        assert client.get(path, expect_errors=True).status_code == 202

    pdf = '%PDF-1.6'.encode('utf-8')
    election_day_app_zg.filestorage.makedir('pdf')
    with election_day_app_zg.filestorage.open('pdf/test.pdf', 'wb') as f:
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


def test_view_svg(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)
    upload_majorz_election(client, canton='zg')
    upload_proporz_election(client, canton='zg')

    ballot_id = election_day_app_zg.session().query(Ballot).one().id
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
        assert client.get(path, expect_errors=True).status_code == 202

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.0" ></svg>'
    ).encode('utf-8')
    election_day_app_zg.filestorage.makedir('svg')
    with election_day_app_zg.filestorage.open('svg/test.svg', 'wb') as f:
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
        'vote-vorlage-gemeinden.svg',
        'vote-vorlage-gemeinden.svg'
    ]


def test_view_opendata_catalog(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    # Not configured
    response = client.get('/catalog.rdf', expect_errors=True)
    assert response.status_code == 501

    principal = election_day_app_zg.principal
    principal.open_data = {
        'id': 'kanton-govikon',
        'mail': 'info@govikon',
        'name': 'Staatskanzlei Kanton Govikon'
    }
    election_day_app_zg.cache.set('principal', principal)

    # Empty
    root = fromstring(client.get('/catalog.rdf').text)
    assert root.tag.lower().endswith('rdf')
    assert len(list(root[0])) == 0

    # With data
    login(client)
    upload_vote(client)
    upload_majorz_election(client, canton='zg', status='final')
    upload_proporz_election(client, canton='zg', status='final')
    upload_party_results(client)
    upload_election_compound(client, canton='zg', status='final')
    upload_party_results(client, slug='elections/elections')

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
        'proporz-election-parteien.csv',
        'proporz-election-parteien.json',
        'proporz-election-parti.csv',
        'proporz-election-parti.json',
        'proporz-election-partidas.csv',
        'proporz-election-partidas.json',
        'proporz-election-partis.csv',
        'proporz-election-partis.json',
        'Regional Election A',
        'regional-election-a.csv',
        'regional-election-a.json',
        'Regional Election B',
        'regional-election-b.csv',
        'regional-election-b.json',
        'Elections',
        'elections-parteien.csv',
        'elections-parteien.json',
        'elections-parti.csv',
        'elections-parti.json',
        'elections-partidas.csv',
        'elections-partidas.json',
        'elections-partis.csv',
        'elections-partis.json',
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


def test_view_screen(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    client.get('/screen/10', status=404)

    login(client)

    # Add two votes
    new = client.get('/manage/votes').click('Neue Abstimmung')
    new.form['vote_de'] = 'Einfache Vorlage'
    new.form['vote_type'] = 'simple'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'federation'
    new.form.submit().follow()

    # Add a screen
    new = client.get('/manage/screens').click('Neuer Screen')
    new.form['number'] = '10'
    new.form['description'] = 'Mein Screen'
    new.form['type'] = 'simple_vote'
    new.form['simple_vote'] = 'einfache-vorlage'
    new.form['structure'] = '<title />'
    new.form['css'] = '/* Custom CSS */'
    manage = new.form.submit().follow()
    assert 'Mein Screen' in manage
    assert 'Einfache Vorlage' in manage

    view = client.get('/screen/10')
    assert 'Einfache Vorlage' in view


def test_view_custom_css(election_day_app_zg):
    principal = election_day_app_zg.principal
    principal.custom_css = 'tr { display: none }'
    election_day_app_zg.cache.set('principal', principal)

    client = Client(election_day_app_zg)
    assert '<style>tr { display: none }</style>' in client.get('/')


def test_view_attachments(
    election_day_app_gr, explanations_pdf, upper_apportionment_pdf,
    lower_apportionment_pdf
):
    content = explanations_pdf.read()

    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()
    login(client)

    # Vote
    new = client.get('/manage/votes').click('Neue Abstimmung')
    new.form['vote_de'] = 'vote'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'federation'
    new.form['explanations_pdf'] = Upload(
        'Erläuterungen.pdf',
        content,
        'application/pdf'
    )
    new.form.submit().follow()

    page = client.get('/vote/vote').follow()
    page = page.click('(PDF)')
    assert page.headers['Content-Type'] == 'application/pdf'
    assert page.headers['Content-Length']
    assert 'Erlauterungen.pdf' in page.headers['Content-Disposition']

    # Election
    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['election_de'] = 'election'
    new.form['date'] = '2016-01-01'
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['mandates'] = 1
    new.form['explanations_pdf'] = Upload(
        'Erläuterungen.pdf',
        content,
        'application/pdf'
    )
    new.form.submit().follow()

    page = client.get('/election/election').follow()
    page = page.click('(PDF)')
    assert page.headers['Content-Type'] == 'application/pdf'
    assert page.headers['Content-Length']
    assert 'Erlauterungen.pdf' in page.headers['Content-Disposition']

    # Election Compound
    new = client.get('/manage/election-compounds').click('Neue Verbindung')
    new.form['election_de'] = 'elections'
    new.form['date'] = '2016-01-01'
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'region'
    new.form['region_elections'] = ['election']
    new.form['explanations_pdf'] = Upload(
        'Erläuterungen.pdf',
        content,
        'application/pdf'
    )
    new.form['upper_apportionment_pdf'] = Upload(
        'Oberzuteilung.pdf',
        upper_apportionment_pdf.read(),
        'application/pdf'
    )
    new.form['lower_apportionment_pdf'] = Upload(
        'Unterzuteilung.pdf',
        lower_apportionment_pdf.read(),
        'application/pdf'
    )
    new.form.submit().follow()

    page = client.get('/elections/elections').follow()
    page = page.click('Erläuterungen')
    assert page.headers['Content-Type'] == 'application/pdf'
    assert page.headers['Content-Length']
    assert 'Erlauterungen.pdf' in page.headers['Content-Disposition']

    page = client.get('/elections/elections').follow()
    page = page.click('Oberzuteilung')
    assert page.headers['Content-Type'] == 'application/pdf'
    assert page.headers['Content-Length']
    assert 'Oberzuteilung.pdf' in page.headers['Content-Disposition']

    page = client.get('/elections/elections').follow()
    page = page.click('Unterzuteilung')
    assert page.headers['Content-Type'] == 'application/pdf'
    assert page.headers['Content-Length']
    assert 'Unterzuteilung.pdf' in page.headers['Content-Disposition']
