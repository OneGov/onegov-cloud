from __future__ import annotations

from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_majorz_election
from tests.onegov.election_day.common import upload_proporz_election
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def test_upload_election_year_unavailable(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'Election'
    new.form['date'] = '1990-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    csv = (
        'election_absolute_majority,'
        'election_status,'
        'entity_id,'
        'entity_counted,'
        'entity_eligible_voters,'
        'entity_received_ballots,'
        'entity_blank_ballots,'
        'entity_invalid_ballots,'
        'entity_blank_votes,'
        'entity_invalid_votes,'
        'candidate_family_name,'
        'candidate_first_name,'
        'candidate_id,'
        'candidate_elected,'
        'candidate_party,'
        'candidate_votes\n'
    ).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Das Jahr 1990 wird noch nicht unterstützt" in upload


def test_upload_election_invalidate_cache(
    election_day_app_gr: TestApp
) -> None:
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_majorz_election(client)
    upload_proporz_election(client)

    anonymous = Client(election_day_app_gr)
    anonymous.get('/locale/de_CH').follow()

    assert ">56<" in anonymous.get('/election/majorz-election').follow()
    assert ">56<" in anonymous.get('/election/proporz-election').follow()

    for slug in ('majorz', 'proporz'):
        csv = anonymous.get(f'/election/{slug}-election/data-csv').text
        csv = csv.replace('56', '58')

        upload = client.get(f'/election/{slug}-election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload(
            'data.csv', csv.encode('utf-8'), 'text/plain')
        upload = upload.form.submit()
        assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert ">56<" not in anonymous.get('/election/majorz-election').follow()
    assert ">56<" not in anonymous.get('/election/proporz-election').follow()
    assert ">58<" in anonymous.get('/election/majorz-election').follow()
    assert ">58<" in anonymous.get('/election/proporz-election').follow()


def test_upload_election_notify_zulip(election_day_app_zg: TestApp) -> None:

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    with patch('urllib.request.urlopen') as urlopen:
        # No settings
        upload_majorz_election(client, canton='zg')
        sleep(5)
        assert not urlopen.called

        election_day_app_zg.zulip_url = 'https://zulipchat.com/api/v1/messages'
        election_day_app_zg.zulip_stream = 'WAB'
        election_day_app_zg.zulip_user = 'wab-bot@seantis.zulipchat.com'
        election_day_app_zg.zulip_key = 'aabbcc'
        upload_majorz_election(client, canton='zg')
        sleep(5)
        urlopen = urlopen  # undo mypy narrowing
        assert urlopen.called
        assert 'zulipchat.com' in urlopen.call_args[0][0].get_full_url()


def test_upload_election_submit(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'majorz'
    new.form['date'] = '2015-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['title_de'] = 'proporz'
    new.form['date'] = '2015-01-01'
    new.form['mandates'] = 1
    new.form['type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    # Internal Majorz
    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_internal_majorz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/majorz/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called

    # Internal Proporz
    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_internal_proporz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/proporz/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
