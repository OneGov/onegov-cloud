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


def test_upload_vote_submit(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()
    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    # Default
    with patch(
        'onegov.election_day.views.upload.vote.import_vote_default'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'default'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_args[0][2] == 'proposal'

    edit = client.get('/vote/vote/edit')
    edit.form['vote_type'] = 'complex'
    edit.form.submit()

    # Default (complex)
    with patch(
        'onegov.election_day.views.upload.vote.import_vote_default'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'default'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload.form['counter_proposal'] = Upload('data.csv', csv, 'text/plain')
        upload.form['tie_breaker'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_count == 3
        set([call[0][2] for call in import_.call_args_list]) == {
            'proposal', 'counter-proposal', 'tie-breaker'
        }

    # Internal
    with patch(
        'onegov.election_day.views.upload.vote.import_vote_internal'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'internal'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called

    # Wabsti
    with patch(
        'onegov.election_day.views.upload.vote.import_vote_wabsti'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'wabsti'
        upload.form['vote_number'] = '1'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_args[0][2] == 1
        assert import_.call_args[0][3] == False

    # Wabsti complex
    edit = client.get('/vote/vote/edit')
    edit.form['vote_type'] = 'complex'
    edit.form.submit()

    with patch(
        'onegov.election_day.views.upload.vote.import_vote_wabsti'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'wabsti'
        upload.form['vote_number'] = '2'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
        assert import_.call_args[0][2] == 2
        assert import_.call_args[0][3] == True


def test_upload_vote_invalidate_cache(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Bacon, yea or nay?'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

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
