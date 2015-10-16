import onegov.election_day

from datetime import date
from onegov.ballot import VoteCollection
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

    assert client.get('/manage', expect_errors=True).status_code == 403

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/manage')
    assert "Noch keine Abstimmungen erfasst" in manage

    new = manage.click('Neue Abstimmung')
    new.form['vote'] = 'Vote for a better yesterday'
    new.form['date'] = date(2016, 1, 1)
    new.form['domain'] = 'federation'
    manage = new.form.submit().follow()

    assert "Vote for a better yesterday" in manage
    edit = manage.click('Bearbeiten')
    edit.form['vote'] = 'Vote for a better tomorrow'
    manage = edit.form.submit().follow()

    assert "Vote for a better tomorrow" in manage

    delete = manage.click("Löschen")
    assert "Abstimmung löschen" in delete
    assert "Vote for a better tomorrow" in delete
    assert "Bearbeiten" in delete.click("Abbrechen")

    manage = delete.form.submit().follow()
    assert "Noch keine Abstimmungen erfasst" in manage


def test_upload_all_or_nothing(election_day_app):
    client = Client(election_day_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote'] = 'Bacon, yea or nay?'
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


def test_upload_success(election_day_app):
    client = Client(election_day_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote'] = 'Bacon, yea or nay?'
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


def test_upload_validation(election_day_app):
    client = Client(election_day_app)

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    new = client.get('/manage/new-vote')
    new.form['vote'] = 'Bacon, yea or nay?'
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
