import copy

import transaction

from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from tests.onegov.translator_directory.shared import translator_data, \
    create_languages, create_certificates



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

    page.form['first_name'] = 'Uncle'
    page.form['last_name'] = 'Bob'
    page.form['social_sec_number'] = 'xxxx'
    page.form['zip_code'] = 'xxxx'
    page = page.form.submit()
    assert "Ungültige AHV-Nummer" in page
    assert "Postleitzahl muss aus 4 Ziffern bestehen" in page

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

    page = page.form.submit().follow()
    assert 'Uncle' in page
    assert 'Bob' in page
    # test lower-casing the user input
    mail = 'test@test.com'
    assert f'<a href="mailto:{mail}">{mail}</a>' in page

    assert '756.1234.5678.97' in page
    assert 'All okay' in page
    assert '7890' in page

    # Test mother tongue set to the first ordered option
    assert language_names[3] in page

    # test spoken languages
    assert language_names[0] in page
    assert language_names[1] in page

    # test written languages
    assert language_names[2] in page

    # edit some key attribute
    page = page.click('Bearbeiten')
    assert 'Zulassung' in page

    tel_mobile = '044 123 50 50'
    page.form['pers_id'] = 123456
    page.form['admission'] = 'in_progress'
    page.form['withholding_tax'] = True
    page.form['gender'] = 'F'
    page.form['date_of_birth'] = '2019-01-01'
    page.form['nationality'] = 'PERU'
    page.form['address'] = 'Somestreet'
    page.form['zip_code'] = '4052'
    page.form['city'] = 'Somecity'
    page.form['drive_distance'] = 60.01
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

    # # Todo: self.content is nullable so I don't get it, in EventForm is works too
    # page.form['coordinates'] = encode_map_value({
    #     'lat': 47, 'lon': 8, 'zoom': 12
    # })

    # Todo: uncomment below and you get 404 cause a new model is beeing created wtf
    page.form['for_admins_only'] = True

    # test removing all languages
    page.form['spoken_languages_ids'] = []
    page.form['written_languages_ids'] = []

    page = page.form.submit().follow()
    assert 'Ihre Änderungen wurden gespeichert' in page

    assert '123456' in page
    assert 'im Zulassungsverfahren' in page
    assert 'Ja' in page
    assert 'Weiblich' in page
    assert '01.01.2019' in page
    assert 'PERU' in page
    assert 'Somestreet' in page
    assert '4052' in page
    assert 'Somecity' in page
    assert '60.01' in page
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

    assert language_names[3] in page
    assert language_names[0] not in page
    assert language_names[1] not in page
    assert language_names[2] not in page
    trs_url = page.request.url

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
