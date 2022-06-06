import copy
import re
import transaction

from datetime import datetime
from io import BytesIO
from onegov.gis import Coordinates
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.forms.settings import ALLOWED_MIME_TYPES
from onegov.user import UserCollection
from openpyxl import load_workbook
from tests.onegov.translator_directory.shared import translator_data, \
    create_languages, create_certificates
from tests.shared.utils import decode_map_value, encode_map_value
from unittest import mock
from webtest import Upload
from xlsxwriter import Workbook


class FakeResponse:
    def __init__(self, json_data=None, status_code=200):
        self.status_code = status_code
        self.json_data = json_data or {}

    def json(self):
        return self.json_data


def test_view_translator(client):
    session = client.app.session()
    languages = create_languages(session)
    certs = create_certificates(session)
    cert_ids = [str(cert.id) for cert in certs]
    cert_names = [cert.name for cert in certs]
    language_ids = [str(lang.id) for lang in languages]
    language_names = [lang.name for lang in languages]
    transaction.commit()

    client.login_editor()
    client.get('/translators/new', status=403)
    client.logout()

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
    page.form['certificates_ids'] = [cert_ids[0]]
    page.form['iban'] = 'DE07 1234 1234 1234 1234 12'
    page.form.get('expertise_professional_guilds', index=0).checked = True
    page.form['expertise_professional_guilds_other'] = ['Psychologie']
    page.form.get('expertise_interpreting_types', index=0).checked = True
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

    translator_url = page.request.url
    assert 'Uncle' in page
    assert 'Bob' in page
    assert '<a href="mailto:test@test.com">test@test.com</a>' in page
    values = {
        dl.find('dt').text_content().strip():
        dl.find('dd').text_content().strip()
        for dl in page.pyquery('dl')
    }
    assert values['Personal Nr.'] == '978654'
    assert values['Zulassung'] == 'nicht zertifiziert / Einsatz Dringlichkeit'
    assert values['Quellensteuer'] == 'Nein'
    assert values['Selbständig'] == 'Nein'
    assert values['Geschlecht'] == 'Männlich'
    assert values['PLZ'] == '7890'
    assert values['Wegberechnung'] == f'{round(drive_distance, 1)} km'
    assert values['AHV-Nr.'] == '756.1234.5678.97'
    assert values['IBAN'] == 'DE07 1234 1234 1234 1234 12'
    assert values['Email'] == 'test@test.com'
    assert values['Telefon Mobile'] == '079 700 80 97'
    assert values['Fachkenntnisse nach Dolmetscherart'] == \
        'Simultandolmetschen'
    assert 'Ernährung' in values['Fachkenntnisse nach Berufssparte']
    assert 'Psychologie' in values['Fachkenntnisse nach Berufssparte']
    assert values['Muttersprachen'] == language_names[3]
    assert language_names[0] in values['Sprachen Wort']
    assert language_names[1] in values['Sprachen Wort']
    assert values['Sprachen Schrift'] == language_names[2]
    assert values['Referenzen Behörden'] == 'All okay'
    assert values['Ausbildung Dolmetscher'] == 'Nein'
    assert values['Versteckt'] == 'Nein'
    assert values['Zertifikate'] == cert_names[0]

    # test user account created and activation mail sent
    user = UserCollection(session).by_username('test@test.com')
    assert user.translator.title == 'Bob, Uncle'
    assert user.active is True
    assert user.role == 'translator'

    mail = client.get_email(0)
    assert mail['To'] == 'test@test.com'
    assert mail['Subject'] == 'Ein Konto wurde für Sie erstellt'

    # test translator can login and view his own data
    client.logout()
    reset_password_url = re.search(
        r'(http://localhost/auth/reset-password[^)]+)',
        mail['TextBody']
    ).group()
    page = client.get(reset_password_url)
    page.form['email'] = 'test@test.com'
    page.form['password'] = 'p@ssw0rd'
    page.form.submit()

    page = client.login('test@test.com', 'p@ssw0rd', None).maybe_follow()
    assert '978654' in page
    assert 'Uncle' in page
    assert 'Bob' in page
    assert '<a href="mailto:test@test.com">test@test.com</a>' in page
    assert '756.1234.5678.97' in page
    assert 'All okay' in page
    assert '7890' in page
    assert 'DE07 1234 1234 1234 1234 12' in page
    assert 'Ernährung und Landwirtschaft' in page
    assert 'Psychologie' in page
    assert 'Simultandolmetschen' in page
    assert 'Versteckt' not in page
    assert str(round(drive_distance, 1)) in page
    assert language_names[3] in page
    assert language_names[0] in page
    assert language_names[1] in page
    assert language_names[2] in page
    client.logout()

    # test editors access on the edit view
    client.login_editor()
    page = client.get(translator_url)
    assert '978654' in page
    assert 'Abrechnungsvorlage' in page
    page = page.click('Bearbeiten')
    page.form['pers_id'] = 123456
    page = page.form.submit().follow()
    assert '123456' in page
    client.logout()

    # edit some key attribute
    client.login_admin()
    page = client.get(translator_url).click('Bearbeiten')
    assert 'Zulassung' in page
    assert decode_map_value(page.form['coordinates'].value) == Coordinates(
        lat=46, lon=7, zoom=12
    )
    drive_distance = 60.01
    tel_mobile = '044 123 50 50'

    page.form['first_name'] = 'Aunt'
    page.form['last_name'] = 'Maggie'
    page.form['email'] = 'aunt.maggie@translators.com'
    page.form['iban'] = 'CH5604835012345678009'
    page.form['pers_id'] = 234567
    page.form['admission'] = 'in_progress'
    page.form['withholding_tax'] = True
    page.form['self_employed'] = True
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
    page.form.get('expertise_professional_guilds', index=0).checked = False
    page.form.get('expertise_professional_guilds', index=1).checked = True
    page.form['expertise_professional_guilds_other'] = ['Religion']
    page.form.get('expertise_interpreting_types', index=0).checked = False
    page.form.get('expertise_interpreting_types', index=1).checked = True
    page.form['mother_tongues_ids'] = [language_ids[1]]
    page.form['spoken_languages_ids'] = [language_ids[2]]
    page.form['written_languages_ids'] = [language_ids[3]]
    page.form['certificates_ids'] = [cert_ids[1]]

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
    assert 'Aunt' in page
    assert 'Maggie' in page
    assert f'<a href="tel:{tel_mobile}">{tel_mobile}</a>' in page
    values = {
        dl.find('dt').text_content().strip():
        dl.find('dd').text_content().strip()
        for dl in page.pyquery('dl')
    }
    assert values['AHV-Nr.'] == '756.1111.1111.11'
    assert values['Anschrift'] == 'Somestreet'
    assert values['Ausbildung Dolmetscher'] == 'Ja'
    assert values['Bank Adresse'] == 'AB Address'
    assert values['Bank Konto lautend auf'] == 'AccountOwner'
    assert values['Bank Name'] == 'Abank'
    assert values['Bemerkungen'] == 'My Comments'
    assert values['Besondere Hinweise Einsatzmöglichkeiten'] == 'operational'
    assert values['Bewerbung Datum'] == '01.01.2015'
    assert values['Email'] == 'aunt.maggie@translators.com'
    assert values['Entscheid Datum'] == '01.01.2016'
    assert values['Erreich- und Verfügbarkeit'] == 'always 24h'
    assert 'Wirtschaft' in values['Fachkenntnisse nach Berufssparte']
    assert 'Religion' in values['Fachkenntnisse nach Berufssparte']
    assert values['Fachkenntnisse nach Dolmetscherart'] == \
        'Konsektutivdolmetschen'
    assert values['Geburtsdatum'] == '01.01.2019'
    assert values['Geschlecht'] == 'Weiblich'
    assert values['IBAN'] == 'CH5604835012345678009'
    assert values['Nachweis der Voraussetzung'] == 'ZHCW'
    assert values['Nationalität'] == 'PERU'
    assert values['Ort'] == 'Somecity'
    assert values['PLZ'] == '4052'
    assert values['Personal Nr.'] == '234567'
    assert values['Quellensteuer'] == 'Ja'
    assert values['Referenzen Behörden'] == 'Kt. ZG'
    assert values['Selbständig'] == 'Ja'
    assert values['Telefon Geschäft'] == '044 123 50 52'
    assert values['Telefon Mobile'] == '044 123 50 50'
    assert values['Telefon Privat'] == '044 123 50 51'
    assert values['Versteckt'] == 'Ja'
    assert values['Wegberechnung'] == f'{round(new_drive_distance, 1)} km'
    assert values['Zulassung'] == 'im Zulassungsverfahren'
    assert values['Muttersprachen'] == language_names[1]
    assert values['Sprachen Wort'] == language_names[2]
    assert values['Sprachen Schrift'] == language_names[3]
    assert values['Zertifikate'] == cert_names[1]

    # test user account updated
    users = UserCollection(session)
    assert not users.by_username('test@test.com')
    user = users.by_username('aunt.maggie@translators.com')
    assert user.translator.title == 'Maggie, Aunt'
    assert user.active is True
    assert user.role == 'translator'

    # try adding another with same email
    page = client.get('/translators/new')
    page.form['first_name'] = 'Uncle'
    page.form['last_name'] = 'Bob'
    page.form['agency_references'] = 'All okay'
    page.form['email'] = 'aunt.maggie@translators.com'

    page = page.form.submit()
    assert 'Ein(e) Übersetzer/in mit dieser Email existiert bereits' in page

    # Test if the for_admins_only works
    client.logout()
    client.login_editor()
    client.get(translator_url, status=403)
    client.logout()


def test_view_languages(client):
    create_languages(client.app.session())
    transaction.commit()

    client.get('/languages', status=403)

    client.login_member()
    client.get('/languages', status=403)

    client.login_editor()
    page = client.get('/languages')
    assert 'Italian' in page
    assert 'French' in page
    assert 'Arabic' in page


def test_manage_language(client):
    client.login_editor()
    client.get('/languages/new', status=403)
    client.login_admin()
    page = client.get('/languages/new')

    page.form['name'] = '     '
    page = page.form.submit()
    assert 'Dieses Feld wird benötigt' in page

    page.form['name'] = ' English   '
    page = page.form.submit().follow()
    assert 'Sprache English hinzugefügt' in page
    assert 'English' in page

    page = client.get('/languages/new')
    page.form['name'] = 'English'
    page = page.form.submit()
    assert 'English existiert bereits' in page

    page = client.get('/languages').click('English')
    page.form['name'] = 'English (British)'
    page = page.form.submit().follow()
    assert 'English (British)' in page

    page = client.get('/languages').click('English').click('Löschen')
    page = client.get('/languages')
    assert 'English' not in page
    assert 'English (British)' not in page


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


def test_view_export_translators(client):
    session = client.app.session()
    languages = create_languages(session)
    translators = TranslatorCollection(session)

    data = copy.deepcopy(translator_data)
    data['spoken_languages'] = [languages[0]]
    data['written_languages'] = [languages[1]]
    data['expertise_professional_guilds'] = ['economy']
    data['expertise_professional_guilds_other'] = ['Psychologie', 'Religion']
    data['expertise_interpreting_types'] = ['simultaneous', 'whisper']

    translators.add(**data)
    transaction.commit()

    client.login_admin()
    response = client.get('/translators').click('Export')
    sheet = load_workbook(BytesIO(response.body)).worksheets[0]
    assert sheet.cell(2, 1).value == 1234
    assert sheet.cell(2, 2).value == (
        'nicht zertifiziert / Einsatz Dringlichkeit'
    )
    assert sheet.cell(2, 3).value == 0
    assert sheet.cell(2, 4).value == 0
    assert sheet.cell(2, 5).value == 'Benito'
    assert sheet.cell(2, 6).value == 'Hugo'
    assert sheet.cell(2, 7).value == 'Männlich'
    assert sheet.cell(2, 8).value == data['date_of_birth'].isoformat()
    assert sheet.cell(2, 9).value == 'CH'
    # assert sheet.cell(2, 10).value == '{"lon":null,"zoom":null,"lat":null}'
    assert sheet.cell(2, 11).value == 'Downing Street 5'
    assert sheet.cell(2, 12).value == '4000'
    assert sheet.cell(2, 13).value == 'Luzern'
    assert sheet.cell(2, 14).value == None
    assert sheet.cell(2, 15).value == '756.1234.4568.90'
    assert sheet.cell(2, 16).value == 'R-BS'
    assert sheet.cell(2, 17).value == 'Bullstreet 5'
    assert sheet.cell(2, 18).value == 'Hugo Benito'
    assert sheet.cell(2, 19).value == None
    assert sheet.cell(2, 20).value == 'hugo@benito.com'
    assert sheet.cell(2, 21).value == None
    assert sheet.cell(2, 22).value == '079 000 00 00'
    assert sheet.cell(2, 23).value == '041 444 44 44'
    assert sheet.cell(2, 24).value == 'always'
    assert sheet.cell(2, 25).value == None
    assert sheet.cell(2, 26).value == 0
    assert sheet.cell(2, 27).value == data['date_of_application'].isoformat()
    assert sheet.cell(2, 28).value == data['date_of_decision'].isoformat()
    assert sheet.cell(2, 29).value == None
    assert sheet.cell(2, 30).value == 'German'
    assert sheet.cell(2, 31).value == 'French'
    assert sheet.cell(2, 32).value == 'Wirtschaft|Psychologie|Religion'
    assert sheet.cell(2, 33).value == 'Simultandolmetschen|Flüsterdolmetschen'
    assert sheet.cell(2, 34).value == 'all okay'
    assert sheet.cell(2, 35).value == 'Some ref'
    assert sheet.cell(2, 36).value == 0
    assert sheet.cell(2, 37).value == None
    assert sheet.cell(2, 38).value == None


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
    settings = client.get('/').follow().click('Verzeichniseinstellungen')

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


def test_view_redirects(client):
    # Create a translator
    languages = create_languages(client.app.session())
    language_id = str(languages[0].id)
    transaction.commit()

    client.login_admin()
    page = client.get('/translators/new')
    page.form['pers_id'] = 123456
    page.form['first_name'] = 'First'
    page.form['last_name'] = 'Last'
    page.form['email'] = 'translator@example.org'
    page.form['agency_references'] = 'OK'
    page.form['mother_tongues_ids'] = [language_id]
    page = page.form.submit().follow()
    assert 'Übersetzer/in hinzugefügt' in page
    translator_url = page.request.url
    client.logout()

    mail = client.get_email(0)['TextBody']
    reset_password_url = re.search(
        r'(http://localhost/auth/reset-password[^)]+)', mail
    ).group()
    page = client.get(reset_password_url)
    page.form['email'] = 'translator@example.org'
    page.form['password'] = 'p@ssword'
    page.form.submit()

    # Test redirects
    urls = {
        'translator@example.org': {
            'homepage': translator_url,
            'login': translator_url,
            'logout': 'http://localhost/auth/login',
            'password': 'p@ssword',
            'to': 'http://localhost/topics/informationen'
        },
        'member@example.org': {
            'homepage': 'http://localhost/translators',
            'login': 'http://localhost/translators',
            'logout': 'http://localhost/auth/login',
            'password': 'hunter2',
            'to': translator_url
        }
    }
    urls['editor@example.org'] = urls['member@example.org']
    urls['admin@example.org'] = urls['member@example.org']

    for user, data in urls.items():
        page = client.login(user, data['password']).maybe_follow()
        assert page.request.url == data['login']

        page = client.login(user, data['password'], data['to']).maybe_follow()
        assert page.request.url == data['to']

        page = client.get('/').maybe_follow()
        assert page.request.url == data['homepage']

        page = client.logout().maybe_follow()
        assert page.request.url == data['logout']
