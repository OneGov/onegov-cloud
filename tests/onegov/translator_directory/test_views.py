import copy
from datetime import datetime
from io import BytesIO
from unittest import mock

import transaction
from webtest import Upload
from xlsxwriter import Workbook

from onegov.gis import Coordinates
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.forms.settings import ALLOWED_MIME_TYPES
from tests.onegov.translator_directory.shared import translator_data, \
    create_languages, create_certificates
from tests.shared.utils import decode_map_value, encode_map_value


class FakeResponse:
    def __init__(self, json_data=None, status_code=200):
        self.status_code = status_code
        self.json_data = json_data or {}

    def json(self):
        return self.json_data


def test_view_new_translator(client):
    session = client.app.session()
    languages = create_languages(session)
    certs = create_certificates(session)
    cert_names = [cert.name for cert in certs]
    language_ids = [str(lang.id) for lang in languages]
    language_names = [lang.name for lang in languages]
    transaction.commit()

    client.login_editor()
    client.get('/translators/new', status=403)
    client.login_admin()
    page = client.get('/translators/new')

    # check choices
    assert 'Männlich' in page
    assert language_names[0] in page
    assert cert_names[0] in page
    assert 'Simultandolmetschen' in page
    assert 'Human- und Sozialwissenschaften' in page
    assert not decode_map_value(page.form['coordinates'].value)

    page.form['pers_id'] = 978654
    page.form['first_name'] = 'Uncle'
    page.form['last_name'] = 'Bob'
    page.form['social_sec_number'] = 'xxxx'
    page.form['zip_code'] = 'xxxx'
    page.form['iban'] = 'xxxx'
    page = page.form.submit()
    assert "Ungültige AHV-Nummer" in page
    assert "Postleitzahl muss aus 4 Ziffern bestehen" in page
    assert "Ungültige Eingabe" in page

    # input required fields
    page.form['social_sec_number'] = '756.1234.5678.97'
    page.form['tel_mobile'] = '079 700 80 97'
    page.form['agency_references'] = 'All okay'
    page.form['zip_code'] = '7890'
    page.form['mother_tongues_ids'] = [language_ids[3]]

    # non required fields
    page.form['email'] = 'Test@test.com'
    page.form['spoken_languages_ids'] = [language_ids[0], language_ids[1]]
    page.form['written_languages_ids'] = [language_ids[2]]
    page.form['iban'] = 'DE07 1234 1234 1234 1234 12'
    page.form['coordinates'] = encode_map_value({
        'lat': 46, 'lon': 7, 'zoom': 12
    })
    drive_distance = 111.11
    with mock.patch(
            'onegov.gis.utils.MapboxRequests.directions',
            return_value=FakeResponse({
                'code': 'Ok',
                'routes': [{'distance': drive_distance * 1000}]})
    ):
        page = page.form.submit()
        assert 'Der eigene Standort ist nicht konfiguriert' in page
        settings = client.get('/directory-settings')
        settings.form['coordinates'] = encode_map_value({
            'lat': 46, 'lon': 7, 'zoom': 12
        })
        settings.form.submit()
        page = page.form.submit().follow()

    assert '978654' in page
    assert 'Uncle' in page
    assert 'Bob' in page
    # test lower-casing the user input
    mail = 'test@test.com'
    assert f'<a href="mailto:{mail}">{mail}</a>' in page

    assert '756.1234.5678.97' in page
    assert 'All okay' in page
    assert '7890' in page
    assert 'DE07 1234 1234 1234 1234 12' in page
    assert str(round(drive_distance, 1)) in page

    # Test mother tongue set to the first ordered option
    assert language_names[3] in page

    # test spoken languages
    assert language_names[0] in page
    assert language_names[1] in page

    # test written languages
    assert language_names[2] in page

    # test editors access on the edit view
    trs_url = page.request.url
    editor = client.spawn()
    editor.login_editor()
    edit_page = editor.get(trs_url).click('Bearbeiten')
    assert '978654' in page
    assert 'Abrechnungsvorlage' in page
    edit_page.form['pers_id'] = 123456
    edit_page.form.submit().follow()

    # edit some key attribute
    page = page.click('Bearbeiten')
    assert 'Zulassung' in page
    assert decode_map_value(page.form['coordinates'].value) == Coordinates(
        lat=46, lon=7, zoom=12
    )
    drive_distance = 60.01
    iban = 'CH5604835012345678009'

    tel_mobile = '044 123 50 50'
    page.form['first_name'] = 'Aunt'
    page.form['last_name'] = 'Maggie'
    page.form['iban'] = iban

    page.form['pers_id'] = 123456
    page.form['admission'] = 'in_progress'
    page.form['withholding_tax'] = True
    page.form['gender'] = 'F'
    page.form['date_of_birth'] = '2019-01-01'
    page.form['nationality'] = 'PERU'
    page.form['address'] = 'Somestreet'
    page.form['zip_code'] = '4052'
    page.form['city'] = 'Somecity'
    page.form['drive_distance'] = drive_distance
    page.form['social_sec_number'] = '756.1111.1111.11'
    page.form['bank_name'] = 'Abank'
    page.form['bank_address'] = 'AB Address'
    page.form['account_owner'] = 'AccountOwner'
    page.form['tel_mobile'] = tel_mobile
    page.form['tel_private'] = '044 123 50 51'
    page.form['tel_office'] = '044 123 50 52'
    page.form['availability'] = 'always 24h'
    page.form['confirm_name_reveal'] = False
    page.form['date_of_application'] = '2015-01-01'
    page.form['date_of_decision'] = '2016-01-01'
    page.form['proof_of_preconditions'] = 'ZHCW'
    page.form['agency_references'] = 'Kt. ZG'
    page.form['education_as_interpreter'] = True
    page.form['comments'] = 'My Comments'
    page.form['operation_comments'] = 'operational'
    page.form['for_admins_only'] = True

    # test removing all languages
    page.form['spoken_languages_ids'] = []
    page.form['written_languages_ids'] = []

    new_drive_distance = 250.666
    # when old and new coords are not same, we update the driving_distance
    page.form['coordinates'] = encode_map_value({
        'lat': 47, 'lon': 8, 'zoom': 12
    })
    with mock.patch(
            'onegov.gis.utils.MapboxRequests.directions',
            return_value=FakeResponse({
                'code': 'Ok',
                'routes': [{'distance': new_drive_distance * 1000}]})
    ):
        page = page.form.submit().follow()

    assert 'Ihre Änderungen wurden gespeichert' in page

    assert '123456' in page
    assert 'Aunt' in page
    assert 'Maggie' in page
    assert iban in page
    assert 'im Zulassungsverfahren' in page
    assert 'Ja' in page
    assert 'Weiblich' in page
    assert '01.01.2019' in page
    assert 'PERU' in page
    assert 'Somestreet' in page
    assert '4052' in page
    assert 'Somecity' in page
    assert str(round(new_drive_distance, 1)) in page
    assert str(drive_distance) not in page
    assert '756.1111.1111.11' in page
    assert 'Abank' in page
    assert 'AB Address' in page
    assert 'AccountOwner' in page
    assert f'<a href="tel:{tel_mobile}">{tel_mobile}</a>' in page
    assert '044 123 50 51' in page
    assert '044 123 50 52' in page
    assert 'always 24h' in page
    assert '01.01.2015' in page
    assert '01.01.2016' in page
    assert 'ZHCW' in page
    assert 'Kt. ZG' in page
    assert 'My Comments' in page
    assert 'operational' in page

    assert language_names[3] in page
    assert language_names[0] not in page
    assert language_names[1] not in page
    assert language_names[2] not in page

    # # try adding another with same email
    page = client.get('/translators/new')
    page.form['first_name'] = 'Uncle'
    page.form['last_name'] = 'Bob'
    page.form['agency_references'] = 'All okay'
    page.form['email'] = 'test@test.com'

    page = page.form.submit()
    assert 'Ein(e) Übersetzer/in mit dieser Email existiert bereits' in page

    # Test if the for_admins_only works
    editor = client.spawn()
    editor.login_editor()
    editor.get(trs_url, status=403)


def test_view_languages(client):
    create_languages(client.app.session())
    transaction.commit()
    client.get('/languages', status=403)
    client.login_member()
    page = client.get('/languages')
    assert 'Italian' in page
    assert 'French' in page
    assert 'Arabic' in page


def test_create_new_language(client):
    client.login_editor()
    client.get('/languages/new', status=403)
    client.login_admin()
    page = client.get('/languages/new')

    page.form['name'] = '     '
    page = page.form.submit()
    assert 'Dieses Feld wird benötigt' in page

    page.form['name'] = ' enGlish   '
    page = page.form.submit().follow()
    assert 'Sprache English hinzugefügt' in page
    assert 'English' in page

    page = client.get('/languages/new')
    page.form['name'] = 'English'
    page = page.form.submit()
    assert 'English existiert bereits' in page


def test_view_search_translator(client):
    """
    - test excluding hidden ones for non-admins
    """
    client.get('/translators', status=403)
    client.login_member()
    page = client.get('/translators')
    assert 'Keine Ergebnisse gefunden' in page
    assert 'Suche in Vor- und Nachname' in page

    session = client.app.session()
    languages = create_languages(session)
    lang_ids = [str(lang.id) for lang in languages]
    translators = TranslatorCollection(session)

    data = copy.deepcopy(translator_data)
    mail = 'first@test.com'
    data['email'] = mail
    data['spoken_languages'] = [languages[0]]
    data['written_languages'] = [languages[1]]
    data['first_name'] = 'Sebastian Stefan'
    data['last_name'] = 'Hugentobler Meeringer'

    translators.add(**data)

    data = copy.deepcopy(translator_data)
    hide_mail = 'hidden@test.com'
    data['email'] = hide_mail
    data['spoken_languages'] = []
    data['written_languages'] = []
    data['first_name'] = 'Maryan'
    data['last_name'] = 'Sitkova Lavrova'
    translators.add(**data)

    transaction.commit()

    page = client.get('/translators')
    assert mail in page
    page.form['spoken_langs'] = [lang_ids[0]]
    page = page.form.submit().follow()
    assert mail in page
    assert hide_mail not in page

    # Check condition both must be fulfilled (AND not OR)
    page.form['spoken_langs'] = [lang_ids[0]]
    page.form['written_langs'] = [lang_ids[0]]
    page = page.form.submit().follow()
    assert 'Keine Ergebnisse gefunden' in page

    page.form['spoken_langs'] = [lang_ids[0], lang_ids[1]]
    page.form['written_langs'] = []
    page = page.form.submit().follow()
    assert 'Keine Ergebnisse gefunden' in page

    page.form['spoken_langs'] = []

    # Test search simple search, the rest is covered in the collection tests
    page.form['search'] = 'xxx Lavrov'
    page = page.form.submit().follow()
    assert 'Sitkova Lavrova' in page
    assert 'Hugentobler' not in page


def test_file_security(client):
    session = client.app.session()
    translators = TranslatorCollection(session)
    trs_id = translators.add(**translator_data).id
    transaction.commit()

    forbidden = 403

    client.login_admin()
    page = client.get(f'/translator/{trs_id}')
    assert 'Dokumente' in page

    client.login_editor()
    page = client.get(f'/translator/{trs_id}')
    assert 'Dokumente' not in page
    client.get(f'/documents/{trs_id}', status=forbidden)
    client.get('/files', status=forbidden)


def test_translator_directory_settings(client):
    client.login_admin()
    client.get('/voucher-template', status=404)
    settings = client.get('/').click('Verzeichniseinstellungen')

    def map_value(page):
        return decode_map_value(page.form['coordinates'].value)

    assert not map_value(settings)

    settings = client.get('/directory-settings')
    assert map_value(settings) == Coordinates()

    settings.form['coordinates'] = encode_map_value({
        'lat': 46, 'lon': 7, 'zoom': 12
    })

    file = BytesIO()
    wb = Workbook(file)
    wb.add_worksheet()
    wb.close()
    file.seek(0)

    settings.form['voucher_excel'] = Upload(
        'example.xlsx', file.read(), tuple(ALLOWED_MIME_TYPES)[0])

    page = settings.form.submit().follow()
    assert 'Ihre Änderungen wurden gespeichert' in page
    settings = client.get('/directory-settings')
    assert map_value(settings) == Coordinates(lat=46, lon=7, zoom=12)
    year = datetime.now().year
    filename = f'abrechnungsvorlage_{year}.xlsx'
    assert filename in settings

    # Get the file
    file_page = client.get('/voucher')
    assert filename in file_page.content_disposition
