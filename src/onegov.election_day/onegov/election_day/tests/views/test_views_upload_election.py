from datetime import date
from onegov.ballot import Election
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests.common import login
from onegov.election_day.tests.common import upload_majorz_election
from onegov.election_day.tests.common import upload_proporz_election
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


def test_upload_election_year_unavailable(election_day_app_gr):
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(1990, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
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


def test_upload_election_invalidate_cache(election_day_app_gr):
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
        csv = csv.replace('56', '58').encode('utf-8')

        upload = client.get(f'/election/{slug}-election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()
        assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert ">56<" not in anonymous.get('/election/majorz-election').follow()
    assert ">56<" not in anonymous.get('/election/proporz-election').follow()
    assert ">58<" in anonymous.get('/election/majorz-election').follow()
    assert ">58<" in anonymous.get('/election/proporz-election').follow()


def test_upload_election_temporary_results_majorz(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # Wabsti: form value + (optionally) missing lines
    csv = '\n'.join((
        (
            'AnzMandate,'
            'BFS,'
            'StimmBer,'
            'StimmAbgegeben,'
            'StimmLeer,'
            'StimmUngueltig,'
            'StimmGueltig,'
            'KandID_1,'
            'KandName_1,'
            'KandVorname_1,'
            'Stimmen_1,'
            'KandResultArt_1,'
            'KandID_2,'
            'KandName_2,'
            'KandVorname_2,'
            'Stimmen_2,'
            'KandResultArt_2,'
            'KandID_3,'
            'KandName_3,'
            'KandVorname_3,'
            'Stimmen_3,'
            'KandResultArt_3,'
            'KandID_4,'
            'KandName_4,'
            'KandVorname_4,'
            'Stimmen_4,'
            'KandResultArt_4'
        ),
        (
            '7,1701,13567,40,0,0,40,1,Hegglin,Peter,36,1,2,'
            'Hürlimann,Urs,25,1,1000,Leere Zeilen,,18,9,1001,'
            'Ungültige Stimmen,,0,9'
        ),
        (
            '7,1702,9620,41,0,1,40,1,Hegglin,Peter,34,2,2,'
            'Hürlimann,Urs,28,2,1000,Leere Zeilen,,6,9,1001,'
            'Ungültige Stimmen,,0,9'
        )
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()

    assert election_day_app.session().query(Election).one().status == 'interim'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '1701,True,13567' in result_wabsti
    assert '1702,True,9620' in result_wabsti
    assert '1711' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert election_day_app.session().query(Election).one().status == 'final'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert 'Baar,1701,True' in result_wabsti

    # Onegov internal: misssing or uncounted
    csv = '\n'.join((
        (
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
            'candidate_votes'
        ),
        ',,1701,True,13567,40,0,0,18,0,Hegglin,Peter,1,False,,36',
        ',,1701,True,13567,40,0,0,18,0,Hürlimann,Urs,2,False,,25',
        ',,1702,True,9620,41,0,1,6,0,Hegglin,Peter,1,False,,34',
        ',,1702,True,9620,41,0,1,6,0,Hürlimann,Urs,2,False,,28',
        ',,1703,False,1000,0,0,0,0,0,Hegglin,Peter,1,False,,0',
        ',,1703,False,1000,0,0,0,0,0,Hürlimann,Urs,2,False,,0',
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text
    assert result_wabsti.replace('final', 'unknown') in result_onegov


def test_upload_election_temporary_results_proporz(election_day_app):
    archive = ArchivedResultCollection(election_day_app.session())
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # Wabsti: form value + (optionally) missing lines
    csv = '\n'.join((
        (
            'Einheit_BFS,'
            'Kand_Nachname,'
            'Kand_Vorname,'
            'Liste_KandID,'
            'Liste_ID,'
            'Liste_Code,'
            'Kand_StimmenTotal,'
            'Liste_ParteistimmenTotal'
        ),
        '1701,Lustenberger,Andreas,101,1,ALG,948,1435',
        '1701,Schriber-Neiger,Hanni,102,1,ALG,208,1435',
        '1702,Lustenberger,Andreas,101,1,ALG,290,533',
        '1702,Schriber-Neiger,Hanni,102,1,ALG,105,533',
    )).encode('utf-8')
    csv_stat = '\n'.join((
        (
            'Einheit_BFS,'
            'Einheit_Name,'
            'StimBerTotal,'
            'WZEingegangen,'
            'WZLeer,'
            'WZUngueltig,'
            'StmWZVeraendertLeerAmtlLeer'
        ),
        '1701,Baar,14119,7462,77,196,122',
        '1702,Cham,9926,4863,0,161,50',
    )).encode('utf-8')

    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'wabsti'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['statistics'] = Upload('data.csv', csv_stat, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert election_day_app.session().query(Election).one().status == 'interim'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '1701,True,14119' in result_wabsti
    assert '1702,True,9926' in result_wabsti
    assert '1711' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert election_day_app.session().query(Election).one().status == 'final'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert 'Baar,1701,True' in result_wabsti

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
            ',1701,True,14119,7462,77,196,122,0,'
            'ALG,1,0,1435,,,Lustenberger,Andreas,101,False,,948'
        ),
        (
            ',1701,True,14119,7462,77,196,122,0,'
            'ALG,1,0,1435,,,Schriber-Neiger,Hanni,102,False,,208'
        ),
        (
            ',1702,True,9926,4863,0,161,50,0,'
            'ALG,1,0,533,,,Lustenberger,Andreas,101,False,,290'
        ),
        (
            ',1702,True,9926,4863,0,161,50,0,'
            'ALG,1,0,533,,,Schriber-Neiger,Hanni,102,False,,105'
        ),
        (
            ',1703,False,1000,0,0,0,0,0,'
            'ALG,1,0,533,,,Lustenberger,Andreas,101,False,,290'
        ),
        (
            ',1703,False,1000,0,0,0,0,0,'
            'ALG,1,0,533,,,Schriber-Neiger,Hanni,102,False,,105'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text
    assert result_wabsti.replace('final', 'unknown') in result_onegov


def test_upload_election_available_formats_canton(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'federal-majorz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    upload = client.get('/election/federal-majorz-election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'federal-proporz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    upload = client.get('/election/federal-proporz-election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'cantonal-majorz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'canton'
    new.form.submit()
    upload = client.get('/election/cantonal-majorz-election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'cantonal-proporz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()
    upload = client.get('/election/cantonal-proporz-election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]


def test_upload_election_available_formats_municipality(election_day_app_bern):
    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'federal-majorz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()
    upload = client.get('/election/federal-majorz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == [
        'internal', 'wabsti_m'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'federal-proporz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    upload = client.get('/election/federal-proporz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'cantonal-majorz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'canton'
    new.form.submit()
    upload = client.get('/election/cantonal-majorz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == [
        'internal', 'wabsti_m'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'cantonal-proporz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()
    upload = client.get('/election/cantonal-proporz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'communal-majorz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'municipality'
    new.form.submit()
    upload = client.get('/election/communal-majorz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == [
        'internal', 'wabsti_m'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'communal-proporz-election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()
    upload = client.get('/election/communal-proporz-election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']


def test_upload_election_notify_zulip(election_day_app):

    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    with patch('urllib.request.urlopen') as urlopen:
        # No settings
        upload_majorz_election(client, canton='zg')
        sleep(5)
        assert not urlopen.called

        election_day_app.zulip_url = 'https://xx.zulipchat.com/api/v1/messages'
        election_day_app.zulip_stream = 'WAB'
        election_day_app.zulip_user = 'wab-bot@seantis.zulipchat.com'
        election_day_app.zulip_key = 'aabbcc'
        upload_majorz_election(client, canton='zg')
        sleep(5)
        assert urlopen.called
        assert 'xx.zulipchat.com' in urlopen.call_args[0][0].get_full_url()


def test_upload_election_submit(election_day_app):
    client = Client(election_day_app)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'majorz'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'majorz'
    new.form['domain'] = 'federation'
    new.form.submit()

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'proporz'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
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

    # Wabsti Majorz
    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_wabsti_majorz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/majorz/upload').follow()
        upload.form['file_format'] = 'wabsti'
        upload.form['majority'] = '5000'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called

        data = client.get('/election/majorz/json').json
        assert data['absolute_majority'] == 5000
        assert data['completed'] is False

    # Wabsti Proporz
    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_wabsti_proporz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/proporz/upload').follow()
        upload.form['file_format'] = 'wabsti'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called

    # Wabsti Municipality Majorz
    principal = election_day_app.principal
    principal.domain = 'municipality'
    principal.municipality = '351'
    election_day_app.cache.set('principal', principal)

    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_wabsti_majorz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/majorz/upload').follow()
        upload.form['file_format'] = 'wabsti_m'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
