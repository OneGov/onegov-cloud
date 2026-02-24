from __future__ import annotations

from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_vote
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_upload_vote_year_unavailable(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['title_de'] = 'Bacon, yea or nay?'
    new.form['date'] = '2000-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/vote/bacon-yea-or-nay/upload')
    upload.form['proposal'] = Upload(
        'data.csv', 'csv'.encode('utf-8'), 'text/plain'
    )

    results = upload.form.submit()
    assert "Das Jahr 2000 wird noch nicht unterstützt" in results


def test_upload_vote_submit(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()
    login(client)

    new = client.get('/manage/votes/new-vote')
    new.form['type'] = 'simple'
    new.form['title_de'] = 'vote'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/votes/new-vote')
    new.form['type'] = 'complex'
    new.form['title_de'] = 'complex'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()

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


def test_upload_vote_invalidate_cache(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_vote(client)

    anonymous = Client(election_day_app_zg)
    anonymous.get('/locale/de_CH').follow()

    assert ">522<" in anonymous.get('/vote/vote/entities')

    csv = anonymous.get('/vote/vote/data-csv').text
    csv = csv.replace('522', '533')

    upload = client.get('/vote/vote/upload')
    upload.form['file_format'] = 'internal'
    upload.form['proposal'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain')
    upload = upload.form.submit()
    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert ">522<" not in anonymous.get('/vote/vote/entities')
    assert ">533<" in anonymous.get('/vote/vote/entities')


def test_upload_vote_notify_zulip(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    with patch('urllib.request.urlopen') as urlopen:
        # No settings
        upload_vote(client)
        sleep(5)
        assert not urlopen.called

        election_day_app_zg.zulip_url = 'https://zulipchat.com/api/v1/messages'
        election_day_app_zg.zulip_stream = 'WAB'
        election_day_app_zg.zulip_user = 'wab-bot@seantis.zulipchat.com'
        election_day_app_zg.zulip_key = 'aabbcc'
        upload_vote(client)
        sleep(5)
        urlopen = urlopen  # undo mypy narrowing
        assert urlopen.called
        assert 'zulipchat.com' in urlopen.call_args[0][0].get_full_url()
