import onegov.election_day
import pytest
import tarfile

from datetime import date
from onegov.ballot import VoteCollection
from onegov.core.utils import module_path
from onegov.testing import utils
from webtest import TestApp as Client
from webtest.forms import Upload


COLUMNS = [
    'Bezirk',
    'BFS Nummer',
    'Gemeinde',
    'Ja Stimmen',
    'Nein Stimmen',
    'Stimmberechtigte',
    'Leere Stimmzettel',
    'Ungültige Stimmzettel'
]


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.election_day)


def test_view_login_logout(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/').click('Anmelden')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter1'

    assert "Unbekannter Benutzername oder falsches Passwort" \
        in login.form.submit()
    assert 'Anmelden' in client.get('/')

    login.form['password'] = 'hunter2'
    homepage = login.form.submit().follow()

    assert 'Sie sind angemeldet' in homepage
    assert 'Abmelden' in homepage
    assert 'Anmelden' not in homepage

    assert 'Anmelden' in client.get('/').click('Abmelden').follow()


def test_view_manage(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    assert client.get('/manage', expect_errors=True).status_code == 403

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/manage')
    assert "Noch keine Wahlen erfasst" in manage
    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Abstimmung')
    new.form['vote_de'] = 'Vote for a better yesterday'
    new.form['date'] = date(2016, 1, 1)
    new.form['domain'] = 'federation'
    manage = new.form.submit().follow()

    assert "Vote for a better yesterday" in manage
    edit = manage.click('Bearbeiten')
    edit.form['vote_de'] = 'Vote for a better tomorrow'
    manage = edit.form.submit().follow()

    assert "Vote for a better tomorrow" in manage

    delete = manage.click("Löschen")
    assert "Abstimmung löschen" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Wahl')
    new.form['election_de'] = 'Elect a new president'
    new.form['date'] = date(2016, 1, 1)
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form['mandates'] = 1
    manage = new.form.submit().follow()

    assert "Elect a new president" in manage
    edit = manage.click('Bearbeiten')
    edit.form['election_de'] = 'Elect a new federal councillor'
    manage = edit.form.submit().follow()

    assert "Elect a new federal councillor" in manage

    delete = manage.click("Löschen")
    assert "Wahl löschen" in delete
    assert "Elect a new federal councillor" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Wahlen erfasst" in manage


def test_upload_vote_all_or_nothing(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'complex'

    passes = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,80,1'
    ))

    fails = '\n'.join((
        ','.join(COLUMNS),
        ',abc,Zug,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload(
        'data.csv', passes.encode('utf-8'), 'text/plain'
    )
    upload.form['counter_proposal'] = Upload(
        'data.csv', passes.encode('utf-8'), 'text/plain'
    )
    upload.form['tie_breaker'] = Upload(
        'data.csv', fails.encode('utf-8'), 'text/plain'
    )
    upload = upload.form.submit()

    assert "Keine Fehler im Vorschlag" in upload
    assert "Keine Fehler im Gegenvorschlag" in upload
    assert "Fehler in der Stichfrage" in upload
    assert "Ungültige BFS Nummer" in upload
    assert '<span class="error-line"><span>Zeile</span>2</span>' in upload

    vote = VoteCollection(election_day_app.session()).by_id('bacon-yea-or-nay')
    assert not vote.ballots


def test_upload_vote_success(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'simple'

    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,3821,7405,16516,80,1',
        ',1706,Oberägeri,811,1298,3560,18,',
        ',1709,Unterägeri,1096,2083,5245,18,1',
        ',1704,Menzingen,599,1171,2917,17,',
        ',1701,Baar,3049,5111,13828,54,3',
        ',1702,Cham,2190,3347,9687,60,',
        ',1703,Hünenberg,1497,2089,5842,15,1',
        ',1708,Steinhausen,1211,2350,5989,17,',
        ',1707,Risch,1302,1779,6068,17,',
        ',1710,Walchwil,651,743,2016,8,',
        ',1705,Neuheim,307,522,1289,10,1',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )

    results = upload.form.submit().click("Hier klicken")

    assert 'Zug' in results
    assert 'Oberägeri' in results
    assert "16'534" in results
    assert "27'898" in results

    # all elegible voters
    assert "72'957" in results

    # entered votes
    assert "44'753" in results

    # turnout
    assert "61.34 %" in results

    # yea %
    assert '<dd class="accepted" >37.21%</dd>' in results

    # nay %
    assert '<dd class="rejected" >62.79%</dd>' in results


def test_upload_vote_validation(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'simple'

    # invalid file
    upload.form['proposal'] = Upload('data.csv', b'text', 'text/plain')
    upload = upload.form.submit()

    assert "Keine gültige CSV/XLS/XLSX Datei" in upload

    # missing columns
    csv = '\n'.join((
        ','.join(COLUMNS[:-2]),
        ',1711,Zug,8321,7405,16516'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Spalten: Leere Stimmzettel, Ungültige Stimmzettel"\
        in upload

    # duplicate columns
    csv = '\n'.join((
        ','.join(COLUMNS + ['Ja Stimmen']),
        ',1711,Zug,8321,7405,16516,80,1,8321'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Einige Spaltennamen erscheinen doppelt" in upload

    # missing municipality
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Fehlender Ort" in upload

    # duplicate municipality
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,80,1',
        ',1711,Zug,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Zug kommt zweimal vor" in upload

    # invalid municipality id
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',a,Zug,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige BFS Nummer" in upload

    # invalid yeas
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,a,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Ja Stimmen' nicht lesen" in upload

    # invalid nays
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,a,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Nein Stimmen' nicht lesen" in upload

    # invalid nays
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,a,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Nein Stimmen' nicht lesen" in upload

    # invalid elegible voters
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,a,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Stimmberechtigte' nicht lesen" in upload

    # invalid empty votes
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,a,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Leere Stimmzettel' nicht lesen" in upload

    # invalid faulty votes
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,80,a'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Ungültige Stimmzettel' nicht lesen" in upload

    # more votes than elegible voters
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,18321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Mehr eingelegte Stimmen als Stimmberechtigte" in upload

    # no elegible voters at all
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,0,0,0,0,0'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Keine Stimmberechtigten" in upload


def test_upload_vote_missing_town(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'complex'

    proposal = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,3821,7405,16516,80,1',
        ',1706,Oberägeri,811,1298,3560,18,',
    ))
    counter_proposal = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,3821,7405,16516,80,1',
        ',1706,Oberägeri,811,1298,3560,18,',
    ))
    tie_breaker = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,3821,7405,16516,80,1',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', proposal.encode('utf-8'), 'text/plain'
    )

    upload.form['counter_proposal'] = Upload(
        'data.csv', counter_proposal.encode('utf-8'), 'text/plain'
    )

    upload.form['tie_breaker'] = Upload(
        'data.csv', tie_breaker.encode('utf-8'), 'text/plain'
    )

    assert "Diese Vorlage hat weniger Resultate als die Anderen" in \
        upload.form.submit()


def test_upload_vote_unknown_result(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'simple'

    proposal = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,3821,7405,16516,80,1',
        ',1706,Oberägeri,unbekannt,7405,16516,80,1',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', proposal.encode('utf-8'), 'text/plain'
    )

    r = upload.form.submit().click("Hier klicken")

    assert "Abgelehnt" in r.pyquery('tr[data-municipality-id="1711"]').text()
    assert "Noch nicht ausgezählt" in r.pyquery(
        'tr[data-municipality-id="1706"]').text()

    # adding unknown results should override existing results
    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['type'] = 'simple'

    proposal = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,unbekannt,7405,16516,80,1',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', proposal.encode('utf-8'), 'text/plain'
    )

    r = upload.form.submit().click("Hier klicken")

    assert "Noch nicht ausgezählt" in r.pyquery(
        'tr[data-municipality-id="1711"]').text()


def test_i18n(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
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

    new = client.get('/manage/new-election')
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
    client = Client(election_day_app)
    client.get('/locale/de_CH')

    # make sure codes != 200 are not cached
    anonymous = Client(election_day_app)
    anonymous.get('/vote/0xdeadbeef', status=404)
    anonymous.get('/election/0xdeafbeef', status=404)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = '0xdeadbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadbeef' in anonymous.get('/vote/0xdeadbeef')

    edit = client.get('/vote/0xdeadbeef/edit')
    edit.form['vote_de'] = '0xdeadc0de'
    edit.form.submit()

    assert '0xdeadc0de' in client.get('/')
    assert '0xdeadbeef' in anonymous.get('/')
    assert '0xdeadc0de' in anonymous.get('/', headers=[
        ('Cache-Control', 'no-cache')
    ])

    new = client.get('/manage/new-election')
    new.form['election_de'] = '0xdeafbeef'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert '0xdeafbeef' not in anonymous.get('/')
    assert '0xdeafbeef' in anonymous.get(
        '/', headers=[('Cache-Control', 'no-cache')]
    )


def test_opendata(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    assert "Open Data" in client.get('/opendata')


def test_view_archive(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote_de'] = "Abstimmung 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = "Wahl 1. Januar 2013"
    new.form['date'] = date(2013, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    assert "archive/2013" in client.get('/')

    archive = client.get('/archive/2013')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-01-01')
    assert "Abstimmung 1. Januar 2013" in archive
    assert "Wahl 1. Januar 2013" in archive

    archive = client.get('/archive/2013-02-02')
    assert "noch keine Wahlen oder Abstimmungen" in archive


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_majorz.tar.gz'),
])
def test_upload_election_sesam_majorz(election_day_app_gr, tar_file):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "2 von 2", "137'126", "55'291", "40.32 %",
        "48'778", "5'365", "1'148", "84'046",
        # candidates
        "39'608", "35'926"
    )))


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/sesam_proporz.tar.gz'),
])
def test_upload_election_sesam_proporz(election_day_app_gr, tar_file):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "125 von 125", "5 von 5", "137'126", "63'053", "45.98 %", "145",
        "2'314", "60'594", "300'743",
        # list connectinos
        "20'610", "33'950", "41'167", "23'673",
        "39'890", "52'992", "76'665",
        # candidates
        "1'788", "1'038", "520"
    )))


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_majorz.tar.gz'),
])
def test_upload_election_wabsti_majorz(election_day_app_sg, tar_file):
    client = Client(election_day_app_sg)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2011, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "144'529", "942", "223", "145'694",
        # candidates
        "53'308", "36'282", "54'616",
    )))

    elected = "ID,Name,Vorname\n3,Rechsteiner,Paul".encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['type'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "1 von 1", "304'850", "47.79 %", "85 von 85", "144'529", "942", "223",
        "145'694",
        # candidates
        "53'308", "36'282", "54'616",
    )))


@pytest.mark.parametrize("tar_file", [
    module_path('onegov.election_day', 'tests/fixtures/wabsti_proporz.tar.gz'),
])
def test_upload_election_wabsti_proporz(election_day_app, tar_file):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 3
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()
        connections = f.extractfile(f.next()).read()
        stats = f.extractfile(f.next()).read()

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # candidates
        "3'240", "10'174", "17'034"
    )))

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['connections'] = Upload('cons.csv', connections, 'text/plain')
    upload.form['statistics'] = Upload('stats.csv', stats, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')

    assert all((expected in results for expected in (
        # totals
        "11 von 11", "74'803", "40'200", "53.74 %", "39'067", "118", "1'015",
        "116'689",
        # connections
        "30'532", "4'178", "807",
        "25'528", "20'584", "35'543",
        # candidates
        "3'240", "10'174", "17'034"
    )))

    elected = "ID,Name,Vorname\n401,Pfister,Gerhard\n"
    elected = elected + "601,Pezzatti,Bruno\n1501,Aeschi,Thomas\n"
    elected = elected.encode('utf-8')
    upload = client.get('/election/election/upload')
    upload.form['type'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['connections'] = Upload('cons.csv', connections, 'text/plain')
    upload.form['statistics'] = Upload('stats.csv', stats, 'text/plain')
    upload.form['elected'] = Upload('elected.csv', elected, 'text/plain')
    upload.form['complete'] = True
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    results = client.get('/election/election')
    assert all((expected in results for expected in (
        # totals
        "11 von 11", "3 von 3", "74'803", "40'200", "53.74 %", "39'067",
        "118", "1'015", "116'689",
        # connections
        "30'532", "4'178", "807",
        # candidates
        "3'240", "10'174", "17'034"
    )))


def test_view_election_candidates(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,"
        "Ungueltige Stimmen,Kandidaten-Nr,Gewaehlt,Name,Vorname,Stimmen,"
        "Anzahl Gemeinden\n"
    )
    csv += "2,3503,56,25,0,4,1,0,1,Gewaehlt,Engler,Stefan,20,1 von 1\n"
    csv += "2,3503,56,25,0,4,1,0,2,Gewaehlt,Schmid,Martin,18,1 von 1\n"
    csv = csv.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    candidates = client.get('/election/election/candidates')
    assert all((expected in candidates for expected in (
        "Engler Stefan", "20", "Schmid Martin", "18"
    )))


def test_view_election_lists(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,Listen-Nr,"
        "Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,Anzahl Sitze Liste,"
        "Unveränderte Wahlzettel Liste,Veränderte Wahlzettel Liste,"
        "Kandidatenstimmen unveränderte Wahlzettel,"
        "Zusatzstimmen unveränderte Wahlzettel,"
        "Kandidatenstimmen veränderte Wahlzettel,"
        "Zusatzstimmen veränderte Wahlzettel,Kandidaten-Nr,Gewählt,Name,"
        "Vorname,Stimmen unveränderte Wahlzettel,"
        "Stimmen veränderte Wahlzettel,Stimmen Total aus Wahlzettel,"
        "01 FDP,02 CVP, Anzahl Gemeinden\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,1,19,FDP,1,1,0,0,0,0,0,8,0,101,"
        "nicht gewählt,Casanova,Angela,0,0,0,0,0,1 von 1\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,2,20,CVP,1,2,0,1,0,5,0,0,0,201,"
        "nicht gewählt,Caluori,Corina,1,0,1,0,0,1 von 1\n"
    )
    csv = csv.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    lists = client.get('/election/election/lists')
    assert all((expected in lists for expected in ("FDP", "8", "CVP", "5")))


def test_view_election_export(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,Listen-Nr,"
        "Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,Anzahl Sitze Liste,"
        "Unveränderte Wahlzettel Liste,Veränderte Wahlzettel Liste,"
        "Kandidatenstimmen unveränderte Wahlzettel,"
        "Zusatzstimmen unveränderte Wahlzettel,"
        "Kandidatenstimmen veränderte Wahlzettel,"
        "Zusatzstimmen veränderte Wahlzettel,Kandidaten-Nr,Gewählt,Name,"
        "Vorname,Stimmen unveränderte Wahlzettel,"
        "Stimmen veränderte Wahlzettel,Stimmen Total aus Wahlzettel,"
        "01 FDP,02 CVP, Anzahl Gemeinden\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,1,19,FDP,1,1,0,0,0,0,0,8,0,101,"
        "nicht gewählt,Casanova,Angela,0,0,0,0,0,1 von 1\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,2,20,CVP,1,2,0,1,0,5,0,0,0,201,"
        "nicht gewählt,Caluori,Corina,1,0,1,0,0,1 von 1\n"
    )
    csv = csv.encode('utf-8')

    upload = client.get('/election/election/upload')
    upload.form['type'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    export = client.get('/election/election/json')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/election/csv')
    assert all((expected in export for expected in ("FDP", "Caluori", "56")))

    export = client.get('/election/election/xlsx')
    assert export.status == '200 OK'
