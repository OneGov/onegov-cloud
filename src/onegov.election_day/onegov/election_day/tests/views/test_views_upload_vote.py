from datetime import date
from onegov.ballot import VoteCollection
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_vote
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload

COLUMNS = [
    'ID',
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
        '1711,3821,7405,16516,80,1',  # Zug
        '1706,unbekannt,7405,16516,80,1',  # Oberägeri
    )).encode('utf-8')
    upload.form['proposal'] = Upload('data.csv', proposal, 'text/plain')
    result = upload.form.submit().click("Hier klicken").maybe_follow()
    result = ' '.join([td.text for td in result.pyquery('td')])

    assert "Noch keine Resultate" not in result
    assert "Zug Abgelehnt" in result
    assert "Oberägeri Noch nicht ausgezählt" in result
    assert archive.query().one().progress == (1, 11)

    # adding unknown results should override existing results
    upload = client.get('/vote/bacon-yea-or-nay/upload')
    proposal = '\n'.join((
        ','.join(COLUMNS),
        '1711,unbekannt,7405,16516,80,1',
    )).encode('utf-8')
    upload.form['proposal'] = Upload('data.csv', proposal, 'text/plain')
    result = upload.form.submit().click("Hier klicken").maybe_follow()

    assert "Noch keine Resultate" in result
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
    new.form['vote_type'] = 'simple'
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/votes/new-vote')
    new.form['vote_type'] = 'complex'
    new.form['vote_de'] = 'complex'
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

    # Default (complex)
    with patch(
        'onegov.election_day.views.upload.vote.import_vote_default'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/complex/upload')
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

    # Wabsti municipalities
    principal = election_day_app.principal
    principal.domain = 'municipality'
    principal.municipality = '351'
    election_day_app.cache.set('principal', principal)

    with patch(
        'onegov.election_day.views.upload.vote.import_vote_wabstim'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/vote/vote/upload')
        upload.form['file_format'] = 'wabsti_m'
        upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called


def test_upload_vote_invalidate_cache(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)

    anonymous = Client(election_day_app)
    anonymous.get('/locale/de_CH').follow()

    assert ">522<" in anonymous.get('/vote/vote/entities')

    csv = anonymous.get('/vote/vote/data-csv').text
    csv = csv.replace('522', '533').encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form['file_format'] = 'internal'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()
    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert ">522<" not in anonymous.get('/vote/vote/entities')
    assert ">533<" in anonymous.get('/vote/vote/entities')


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
        'default', 'internal', 'wabsti_m'
    ]

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal', 'wabsti_m'
    ]

    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'municipality'
    new.form.submit()

    upload = client.get('/vote/vote/upload')
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'default', 'internal', 'wabsti_m'
    ]


def test_upload_vote_notify_zulip(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    with patch('urllib.request.urlopen') as urlopen:
        # No settings
        upload_vote(client)
        sleep(5)
        assert not urlopen.called

        election_day_app.zulip_url = 'https://xx.zulipchat.com/api/v1/messages'
        election_day_app.zulip_stream = 'WAB'
        election_day_app.zulip_user = 'wab-bot@seantis.zulipchat.com'
        election_day_app.zulip_key = 'aabbcc'
        upload_vote(client)
        sleep(5)
        assert urlopen.called
        assert 'xx.zulipchat.com' in urlopen.call_args[0][0].get_full_url()


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
        '1711,8321,7405,16516,80,1'
    ))

    fails = '\n'.join((
        ','.join(COLUMNS),
        'abc,8321,7405,16516,80,1'
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
    assert [ballot.results.count() for ballot in vote.ballots] == [0, 0, 0]
