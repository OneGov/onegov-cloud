from datetime import date
from onegov.election_day.collections import ArchivedResultCollection
from tests.onegov.election_day.common import login
from tests.onegov.election_day.common import upload_election_compound
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


def test_upload_election_compound_year_unavailable(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(1990, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['election_de'] = "Elections"
    new.form['date'] = date(1990, 1, 1)
    new.form['municipality_elections'] = ['election']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
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
    upload = client.get('/elections/elections/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Das Jahr 1990 wird noch nicht unterstützt" in upload


def test_upload_election_compound_invalidate_cache(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    upload_election_compound(client, pukelsheim=True)

    anonymous = Client(election_day_app_gr)
    anonymous.get('/locale/de_CH').follow()

    assert ">56<" in anonymous.get('/election/regional-election-a').follow()
    assert ">56<" in anonymous.get('/election/regional-election-b').follow()

    csv = anonymous.get('/elections/elections/data-csv').text
    csv = csv.replace('56', '58').encode('utf-8')

    upload = client.get('/elections/elections/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()
    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    a = anonymous.get('/election/regional-election-a').follow()
    b = anonymous.get('/election/regional-election-b').follow()
    assert ">56<" not in a
    assert ">56<" not in b
    assert ">58<" in a
    assert ">58<" in b


def test_upload_election_compound_temporary_results(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2022, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['region'] = 'Ilanz'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['election_de'] = "Elections"
    new.form['date'] = date(2022, 1, 1)
    new.form['region_elections'] = ['election']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'region'
    new.form.submit()

    assert sorted([result.progress for result in archive.query()]) == [
        (0, 0),  # election
        (0, 1)   # compound
    ]

    # Onegov internal: misssing and number of municpalities
    csv = '\n'.join((
        (
            'election_status,'
            'entity_id,'
            'entity_counted,'
            'entity_eligible_voters,'
            'entity_received_ballots,'
            'entity_blank_ballots,'
            'entity_invalid_ballots,'
            'entity_blank_votes,'
            'entity_invalid_votes,'
            'list_name,'
            'list_id,'
            'list_number_of_mandates,'
            'list_votes,'
            'list_connection,'
            'list_connection_parent,'
            'candidate_family_name,'
            'candidate_first_name,'
            'candidate_id,'
            'candidate_elected,'
            'candidate_party,'
            'candidate_votes'
        ),
        (
            ',3572,True,14119,7462,77,196,122,0,'
            'ALG,1,0,1435,,,Lustenberger,Andreas,101,False,,948'
        ),
        (
            ',3572,True,14119,7462,77,196,122,0,'
            'ALG,1,0,1435,,,Schriber-Neiger,Hanni,102,False,,208'
        ),
        (
            ',3575,True,9926,4863,0,161,50,0,'
            'ALG,1,0,533,,,Lustenberger,Andreas,101,False,,290'
        ),
        (
            ',3575,True,9926,4863,0,161,50,0,'
            'ALG,1,0,533,,,Schriber-Neiger,Hanni,102,False,,105'
        ),
        (
            ',3581,False,1000,0,0,0,0,0,'
            'ALG,1,0,533,,,Lustenberger,Andreas,101,False,,290'
        ),
        (
            ',3581,False,1000,0,0,0,0,0,'
            'ALG,1,0,533,,,Schriber-Neiger,Hanni,102,False,,105'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert sorted([result.progress for result in archive.query()]) == [
        (0, 1),  # compound
        (2, 6)  # election
    ]


def test_upload_election_compound_notify_zulip(election_day_app_zg):

    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    with patch('urllib.request.urlopen') as urlopen:
        # No settings
        upload_election_compound(client, canton='zg')
        sleep(5)
        assert not urlopen.called

        election_day_app_zg.zulip_url = 'https://zulipchat.com/api/v1/messages'
        election_day_app_zg.zulip_stream = 'WAB'
        election_day_app_zg.zulip_user = 'wab-bot@seantis.zulipchat.com'
        election_day_app_zg.zulip_key = 'aabbcc'
        upload_election_compound(client, canton='zg')
        sleep(5)
        assert urlopen.called
        assert 'zulipchat.com' in urlopen.call_args[0][0].get_full_url()


def test_upload_election_compound_submit(election_day_app_zg):
    client = Client(election_day_app_zg)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    new = client.get('/manage/election-compounds/new-election-compound')
    new.form['election_de'] = "Elections"
    new.form['date'] = date(2015, 1, 1)
    new.form['municipality_elections'] = ['election']
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = 'municipality'
    new.form.submit()

    with patch(
        'onegov.election_day.views.upload.election_compound.'
        'import_election_compound_internal'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/elections/elections/upload')
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
