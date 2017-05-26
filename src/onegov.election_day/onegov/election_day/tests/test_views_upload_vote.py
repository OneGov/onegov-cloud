from datetime import date
from onegov.ballot import VoteCollection
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests import login
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload

COLUMNS = [
    'Bezirk',
    'ID',
    'Name',
    'Ja Stimmen',
    'Nein Stimmen',
    'Stimmberechtigte',
    'Leere Stimmzettel',
    'Ungültige Stimmzettel'
]


def test_upload_vote_all_or_nothing(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form['vote_type'] = 'complex'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')

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

    assert "Ihre Resultate konnten leider nicht hochgeladen werden" in upload
    assert '<span class="error-line">Vorlage</span>' not in upload
    assert '<span class="error-line">Gegenentwurf</span>' not in upload
    assert '<span class="error-line">Stichfrage</span>' in upload
    assert "Ungültige ID" in upload
    assert '<span class="error-line"><span>Zeile</span>2</span>' in upload
    assert archive.query().one().progress == (0, 0)

    vote = VoteCollection(election_day_app.session()).by_id('bacon-yea-or-nay')
    assert not vote.ballots.count()


def test_upload_vote_success(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')

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
    assert archive.query().one().progress == (11, 11)

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
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    upload = client.get('/vote/bacon-yea-or-nay/upload')

    # invalid file
    upload.form['proposal'] = Upload('data.csv', b'text', 'text/plain')
    upload = upload.form.submit()

    assert "Keine gültige CSV/XLS/XLSX Datei" in upload
    assert archive.query().one().progress == (0, 0)

    # missing columns
    csv = '\n'.join((
        ','.join(COLUMNS[:-2]),
        ',1711,Zug,8321,7405,16516'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Spalten: Leere Stimmzettel, Ungültige Stimmzettel"\
        in upload
    assert archive.query().one().progress == (0, 0)

    # duplicate columns
    csv = '\n'.join((
        ','.join(COLUMNS + ['Ja Stimmen']),
        ',1711,Zug,8321,7405,16516,80,1,8321'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Einige Spaltennamen erscheinen doppelt" in upload
    assert archive.query().one().progress == (0, 0)

    # missing municipality
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Fehlende Bezeichnung" in upload
    assert archive.query().one().progress == (0, 0)

    # duplicate municipality
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,80,1',
        ',1711,Zug,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Zug kommt zweimal vor" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid municipality id
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',a,Zug,8321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Ungültige ID" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid yeas
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,a,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Ja Stimmen' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid nays
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,a,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Nein Stimmen' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid nays
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,a,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Nein Stimmen' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid elegible voters
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,a,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Stimmberechtigte' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid empty votes
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,a,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Leere Stimmzettel' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # invalid faulty votes
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,8321,7405,16516,80,a'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Konnte 'Ungültige Stimmzettel' nicht lesen" in upload
    assert archive.query().one().progress == (0, 0)

    # more votes than elegible voters
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,18321,7405,16516,80,1'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Mehr eingelegte Stimmen als Stimmberechtigte" in upload
    assert archive.query().one().progress == (0, 0)

    # no elegible voters at all
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,0,0,0,0,0'
    ))

    upload.form['proposal'] = Upload('csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()

    assert "Keine Stimmberechtigten" in upload
    assert archive.query().one().progress == (0, 0)


def test_upload_vote_unknown_result(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')

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
    assert archive.query().one().progress == (1, 11)

    # adding unknown results should override existing results
    upload = client.get('/vote/bacon-yea-or-nay/upload')

    proposal = '\n'.join((
        ','.join(COLUMNS),
        ',1711,Zug,unbekannt,7405,16516,80,1',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', proposal.encode('utf-8'), 'text/plain'
    )

    r = upload.form.submit().click("Hier klicken")

    assert archive.query().one().progress == (0, 11)


def test_upload_vote_year_unavailable(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2000, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/vote/bacon-yea-or-nay/upload')

    csv = '\n'.join((','.join(COLUMNS),))
    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )

    results = upload.form.submit()
    assert "Das Jahr 2000 wird noch nicht unterstützt" in results


def test_upload_vote_roundtrip(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')

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

    results = upload.form.submit()
    assert 'Ihre Resultate wurden erfolgreich hochgeladen' in results
    assert archive.query().one().progress == (11, 11)

    export = client.get('/vote/bacon-yea-or-nay/data-csv').text.encode('utf-8')

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['file_format'] = 'internal'
    upload.form['proposal'] = Upload('data.csv', export, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    second_export = client.get(
        '/vote/bacon-yea-or-nay/data-csv'
    ).text.encode('utf-8')

    assert export == second_export


# @pytest.mark.parametrize("tar_file", [
#     module_path('onegov.election_day', 'tests/fixtures/wabsti_vote.tar.gz'),
# ])
# def test_upload_vote_wabsti(election_day_app_sg, tar_file):
def test_upload_vote_wabsti(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    with patch(
        'onegov.election_day.views.upload.vote.import_vote_wabsti'
    ) as import_:
        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'wabsti'
        upload.form['vote_number'] = '1'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_args[0][4] == 1
        assert import_.call_args[0][5] == False

    edit = client.get('/vote/vote/edit')
    edit.form['vote_type'] = 'complex'
    edit.form.submit()

    with patch(
        'onegov.election_day.views.upload.vote.import_vote_wabsti'
    ) as import_:
        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'wabsti'
        upload.form['vote_number'] = '2'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_args[0][4] == 2
        assert import_.call_args[0][5] == True


def test_upload_vote_invalidate_cache(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # when uploading a proposal, a counter-proposal and a tie-breaker we
    # want the process to stop completely if any of these three files has
    # an error

    upload = client.get('/vote/bacon-yea-or-nay/upload')

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

    results = upload.form.submit()
    assert 'Ihre Resultate wurden erfolgreich hochgeladen' in results

    anonymous = Client(election_day_app)
    anonymous.get('/locale/de_CH').follow()

    assert "3'821" in anonymous.get('/vote/bacon-yea-or-nay/')

    csv = csv.replace('3821,7405', '3221,8005')
    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )

    results = upload.form.submit()
    assert 'Ihre Resultate wurden erfolgreich hochgeladen' in results

    assert "3'821" not in anonymous.get('/vote/bacon-yea-or-nay/')
    assert "3'221" in anonymous.get('/vote/bacon-yea-or-nay/')


def test_upload_vote_temporary_results(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # standard format: missing
    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1706,Oberägeri,811,1298,3560,18,',
        ',1709,Unterägeri,1096,2083,5245,18,1',
    )).encode('utf-8')
    upload = client.get('/vote/vote/upload')
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_standard = client.get('/vote/vote/data-csv').text
    assert 'Baar,1701,False' in result_standard
    assert 'Cham,1702,False' in result_standard
    assert 'Oberägeri,1706,True' in result_standard
    assert 'Unterägeri,1709,True' in result_standard

    # onegov: missing or counted=False
    csv = '\n'.join((
        (
            'status,type,group,entity_id,counted,yeas,nays,invalid,empty,'
            'elegible_voters'
        ),
        ',proposal,Baar,1701,False,0,0,0,0,0',
        ',proposal,Oberägeri,1706,True,811,1298,0,18,3560',
        ',proposal,Unterägeri,1709,True,1096,2083,1,18,5245',
    )).encode('utf-8')
    upload = client.get('/vote/vote/upload')
    upload.form['file_format'] = 'internal'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_internal = client.get('/vote/vote/data-csv').text
    assert result_standard == result_internal


def test_upload_vote_available_formats_canton(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal', 'wabsti'
    ]

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal', 'wabsti'
    ]


def test_upload_vote_available_formats_municipality(election_day_app_bern):
    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal'
    ]

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal'
    ]

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'municipality'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal'
    ]


def test_upload_communal_vote(election_day_app_kriens):
    archive = ArchivedResultCollection(election_day_app_kriens.session())

    client = Client(election_day_app_kriens)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'municipality'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    upload = client.get('/vote/vote/upload')

    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1059,Kriens,2182,4913,18690,56,27'
    ))

    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )

    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (1, 1)

    result = client.get('/vote/vote')
    assert '38.41' in result
    assert 'ballot-map' not in result
    assert '<td>Total' not in result


def test_upload_communal_vote_districts(election_day_app_bern):
    archive = ArchivedResultCollection(election_day_app_bern.session())

    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'municipality'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    upload = client.get('/vote/vote/upload')

    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1,Innere Stadt,4142,1121,14431,218,2',
        ',2,Länggasse/Felsenau,2907,676,9788,129,7',
        ',3,Mattenhof/Weissenbühl,3978,1043,13750,201,2',
        ',4,Kirchenfeld/Schosshalde,5459,1730,19329,146,9',
        ',5,Breitenrain/Lorraine,3742,1139,13410,211,3',
        ',6,Bümpliz/Bethlehem,3491,1036,12276,133,4',
    ))

    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )

    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (6, 6)

    result = client.get('/vote/vote')
    assert '37.99' in result
    assert 'ballot-map' in result
    assert '<td>Total' in result


def test_upload_vote_with_expats(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    for id_ in (0, 9170):
        # simple
        csv = '\n'.join((
            ','.join(COLUMNS),
            ',{},Auslandschweizer,10,20,30,0,0'.format(id_),
        )).encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        result_standard = client.get('/vote/vote/data-csv').text
        assert 'Auslandschweizer,0' in result_standard

        # onegov
        csv = '\n'.join((
            (
                'status,type,group,entity_id,counted,yeas,nays,invalid,empty,'
                'elegible_voters'
            ),
            ',proposal,Auslandschweizer,{},True,10,20,0,0,30'.format(id_),
        )).encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'internal'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        result_internal = client.get('/vote/vote/data-csv').text
        assert result_standard == result_internal


def test_upload_vote_notify_hipchat(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = '\n'.join((
        ','.join(COLUMNS),
        ',1706,Oberägeri,811,1298,3560,18,',
    )).encode('utf-8')

    with patch('urllib.request.urlopen') as urlopen:

        # Hipchat not set
        upload = client.get('/vote/vote/upload')
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        sleep(5)

        assert not urlopen.called

        election_day_app.hipchat_token = 'abcd'
        election_day_app.hipchat_room_id = '1234'

        upload = client.get('/vote/vote/upload')
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        sleep(5)

        assert urlopen.called
        assert 'api.hipchat.com' in urlopen.call_args[0][0].get_full_url()
