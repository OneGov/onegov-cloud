from datetime import date
from onegov.ballot import Election
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests import login
from time import sleep
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload


HEADER_COLUMNS_INTERNAL = (
    'election_title,'
    'election_date,'
    'election_type,'
    'election_mandates,'
    'election_absolute_majority,'
    'election_status,'
    'election_counted_entities,'
    'election_total_entities,'
    'entity_name,'
    'entity_id,'
    'entity_elegible_voters,'
    'entity_received_ballots,'
    'entity_blank_ballots,'
    'entity_invalid_ballots,'
    'entity_unaccounted_ballots,'
    'entity_accounted_ballots,'
    'entity_blank_votes,'
    'entity_invalid_votes,'
    'entity_accounted_votes,'
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
)

HEADER_COLUMNS_WABSTI_PROPORZ = (
    'Einheit_BFS,'
    'Einheit_Name,'
    'Kand_Nachname,'
    'Kand_Vorname,'
    'Liste_KandID,'
    'Liste_ID,'
    'Liste_Code,'
    'Kand_StimmenTotal,'
    'Liste_ParteistimmenTotal'
)


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

    csv = HEADER_COLUMNS_INTERNAL.encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Das Jahr 1990 wird noch nicht unterstützt" in upload


def test_upload_election_invalidate_cache(election_day_app_gr):
    archive = ArchivedResultCollection(election_day_app_gr.session())
    client = Client(election_day_app_gr)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()
    assert archive.query().one().progress == (0, 0)

    # Invalid data
    csv = (
        'election_title,election_date,election_type,election_mandates,'
        'election_absolute_majority,election_status,election_counted_entities,'
        'election_total_entities,entity_name,'
        'entity_id,entity_elegible_voters,'
        'entity_received_ballots,entity_blank_ballots,'
        'entity_invalid_ballots,entity_unaccounted_ballots,'
        'entity_accounted_ballots,entity_blank_votes,'
        'entity_invalid_votes,entity_accounted_votes,list_name,'
        'list_id,list_number_of_mandates,list_votes,list_connection,'
        'list_connection_parent,candidate_family_name,candidate_first_name,'
        'candidate_id,candidate_elected,canidate_party,candidate_votes\r\n'
        'Election,2015-03-02,proporz,1,0,,1,1,Town,3503,1013,428,2,16,18,410,'
        '13,0,2037,Party,1,0,1,5,1,Muster,Peter,1,False,Party,40'
    )

    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    assert archive.query().one().progress == (1, 1)

    anonymous = Client(election_day_app_gr)
    anonymous.get('/locale/de_CH').follow()

    assert "1'013" in anonymous.get('/election/election').follow()

    csv = csv.replace('1013', '1015')

    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload(
        'data.csv', csv.encode('utf-8'), 'text/plain'
    )
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload

    assert "1'013" not in anonymous.get('/election/election').follow()
    assert "1'015" in anonymous.get('/election/election').follow()


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
            'EinheitBez,'
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
            '7,1701,Baar,13567,40,0,0,40,1,Hegglin,Peter,36,2,2,'
            'Hürlimann,Urs,25,2,1000,Leere Zeilen,,18,9,1001,'
            'Ungültige Stimmen,,0,9'
        ),
        (
            '7,1702,Cham,9620,41,0,1,40,1,Hegglin,Peter,34,2,2,'
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
    assert 'Baar,1701,13567' in result_wabsti
    assert 'Cham,1702,9620' in result_wabsti
    assert 'Zug' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert election_day_app.session().query(Election).one().status == 'final'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '2,11,Baar,1701' in result_wabsti

    # Onegov internal: misssing and number of municpalities
    csv = '\n'.join((
        HEADER_COLUMNS_INTERNAL,
        (
            'majorz,2015-01-01,majorz,7,,,2,11,Baar,1701,13567,40,0,0,0,40,18,'
            '0,262,,,,0,,,Hegglin,Peter,1,False,,36'
        ),
        (
            'majorz,2015-01-01,majorz,7,,,2,11,Baar,1701,13567,40,0,0,0,40,18,'
            '0,262,,,,0,,,Hürlimann,Urs,2,False,,25'
        ),
        (
            'majorz,2015-01-01,majorz,7,,,2,11,Cham,1702,9620,41,0,1,1,40,6,0,'
            '274,,,,0,,,Hegglin,Peter,1,False,,34'
        ),
        (
            'majorz,2015-01-01,majorz,7,,,2,11,Cham,1702,9620,41,0,1,1,40,6,0,'
            '274,,,,0,,,Hürlimann,Urs,2,False,,28'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text

    assert result_wabsti.replace('final', 'unknown') == result_onegov


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
        HEADER_COLUMNS_WABSTI_PROPORZ,
        '1701,Baar,Lustenberger,Andreas,101,1,ALG,948,1435',
        '1701,Baar,Schriber-Neiger,Hanni,102,1,ALG,208,1435',
        '1702,Cham,Lustenberger,Andreas,101,1,ALG,290,533',
        '1702,Cham,Schriber-Neiger,Hanni,102,1,ALG,105,533',
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
    assert 'Baar,1701,14119' in result_wabsti
    assert 'Cham,1702,9926' in result_wabsti
    assert 'Zug' not in result_wabsti

    upload.form['complete'] = True
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert election_day_app.session().query(Election).one().status == 'final'
    assert archive.query().one().progress == (2, 11)

    result_wabsti = client.get('/election/election/data-csv').text
    assert '2,11,Baar,1701' in result_wabsti

    # Onegov internal: misssing and number of municpalities
    csv = '\n'.join((
        HEADER_COLUMNS_INTERNAL,
        (
            'election,2015-01-01,proporz,2,,,2,11,Baar,1701,14119,7462,77,196,'
            '273,7189,122,0,14256,ALG,1,0,1435,,,Lustenberger,Andreas,101,'
            'False,,948'
        ),
        (
            'election,2015-01-01,proporz,2,,,2,11,Baar,1701,14119,7462,77,196,'
            '273,7189,122,0,14256,ALG,1,0,1435,,,Schriber-Neiger,Hanni,102,'
            'False,,208'
        ),
        (
            'election,2015-01-01,proporz,2,,,2,11,Cham,1702,9926,4863,0,161,'
            '161,4702,50,0,9354,ALG,1,0,533,,,Lustenberger,Andreas,101,'
            'False,,290'
        ),
        (
            'election,2015-01-01,proporz,2,,,2,11,Cham,1702,9926,4863,0,161,'
            '161,4702,50,0,9354,ALG,1,0,533,,,Schriber-Neiger,Hanni,102,'
            'False,,105'
        ),
    )).encode('utf-8')
    upload = client.get('/election/election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    assert 'erfolgreich hochgeladen' in upload.form.submit()
    assert archive.query().one().progress == (2, 11)

    result_onegov = client.get('/election/election/data-csv').text

    assert result_onegov == result_wabsti.replace('final', 'unknown')


def test_upload_election_available_formats_canton(election_day_app):
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

    upload = client.get('/election/election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/election/election/upload').follow()
    assert sorted([o[0] for o in upload.form['file_format'].options]) == [
        'internal', 'wabsti'
    ]


def test_upload_election_available_formats_municipality(election_day_app_bern):
    client = Client(election_day_app_bern)
    client.get('/locale/de_CH').follow()

    login(client)

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'federation'
    new.form.submit()

    upload = client.get('/election/election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'canton'
    new.form.submit()

    upload = client.get('/election/election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']

    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'municipality'
    new.form.submit()

    upload = client.get('/election/election/upload').follow()
    assert [o[0] for o in upload.form['file_format'].options] == ['internal']


def test_upload_election_notify_hipchat(election_day_app):

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

    csv = '\n'.join((
        HEADER_COLUMNS_INTERNAL,
        (
            ','
            ','
            ','
            ','
            ','  # abs
            'unknown,'
            '1,'
            '1,'
            'Baar,'
            '1701,'
            '13567,'
            '40,'
            '0,'
            '0,'
            ','
            ','
            '18,'
            '0,'
            ','
            ','
            ','
            ','
            ','
            ','
            ','
            'Hegglin,'
            'Peter,'
            '1,'
            'False,'
            ','
            '36'
        ),
        (
            ',,,,,unknown,1,1,Baar,1701,13567,40,0,0,,,18,0,,,,,,,,'
            'Hegglin,Peter,1,False,,36'
        )
    )).encode('utf-8')

    with patch('urllib.request.urlopen') as urlopen:

        # Hipchat not set
        upload = client.get('/election/election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        sleep(5)

        assert not urlopen.called

        election_day_app.hipchat_token = 'abcd'
        election_day_app.hipchat_room_id = '1234'

        upload = client.get('/election/election/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        assert 'erfolgreich hochgeladen' in upload.form.submit()

        sleep(5)

        assert urlopen.called
        assert 'api.hipchat.com' in urlopen.call_args[0][0].get_full_url()


def test_upload_election_submit(election_day_app):
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

    # Internal format
    with patch(
        'onegov.election_day.views.upload.election.import_election_internal'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/election/upload').follow()
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
        upload = client.get('/election/election/upload').follow()
        upload.form['file_format'] = 'wabsti'
        upload.form['majority'] = '5000'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called

        data = client.get('/election/election/json').json
        assert data['absolute_majority'] == 5000
        assert data['completed'] == False

    edit = client.get('/election/election/edit')
    edit.form['election_type'] = 'proporz'
    edit.form.submit()

    # Wabsti Proporz
    with patch(
        'onegov.election_day.views.upload.election.'
        'import_election_wabsti_proporz'
    ) as import_:
        import_.return_value = []

        csv = 'csv'.encode('utf-8')
        upload = client.get('/election/election/upload').follow()
        upload.form['file_format'] = 'wabsti'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert import_.called
