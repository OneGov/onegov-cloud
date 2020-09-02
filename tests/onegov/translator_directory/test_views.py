import copy

import transaction

from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import CERTIFICATES, \
    Translator, Language
from tests.onegov.translator_directory.shared import translator_data, \
    create_languages, create_certificates
from tests.shared.utils import open_in_browser


def test_view_new_translator(client):
    """
    - validate unique email
    - validate always lowercase email
    - validate social security number
    - make a run to fill all the fields
    """

    session = client.app.session()
    languages = create_languages(session)
    certs = create_certificates(session)
    cert_names = [cert.name for cert in certs]
    cert_ids = [str(cert.id) for cert in certs]
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
    page = page.form.submit()
    assert "Ungültige AHV-Nummer" in page

    # input required fields
    page.form['social_sec_number'] = '756.1234.5678.97'
    page.form['tel_mobile'] = '079 700 80 97'
    page.form['agency_references'] = 'All okay'

    # non required fields
    page.form['email'] = 'Test@test.com'
    page.form['spoken_languages'] = [
        language_ids[0], language_ids[1]
    ]
    page.form['written_languages'] = [
        language_ids[2]
    ]

    page.form['mother_tongues'] = [language_ids[-1]]
    page = page.form.submit().follow()
    assert 'Uncle' in page
    # test lower-casing the user input
    assert 'test@test.com' in page

    # Test mother tongue set to the first ordered option
    assert language_names[-1] in page

    # test spoken languages
    assert language_names[0] in page
    assert language_names[1] in page

    # test written languages
    assert language_names[2] in page

    # try adding another with same email
    page = client.get('/translators/new')
    page.form['first_name'] = 'Uncle'
    page.form['last_name'] = 'Bob'
    page.form['agency_references'] = 'All okay'
    page.form['email'] = 'test@test.com'

    page = page.form.submit()
    assert 'Ein(e) Übersetzer/in mit dieser Email existiert bereits' in page


def test_view_translator(client):
    session = client.app.session()
    translators = TranslatorCollection(session)
    translator = translators.add(**translator_data)
    tr_id = translator.id
    transaction.commit()
    client.get(f'/translator/{tr_id}', status=403)
    client.login_member()
    page = client.get(f'/translator/{tr_id}')

    mail = translator_data['email']
    tel_mobile = translator_data['tel_mobile']
    assert f'<a href="mailto:{mail}">{mail}</a>' in page
    assert f'<a href="tel:{tel_mobile}">{tel_mobile}</a>' in page


def test_view_languages(client):
    client.get('/languages', status=403)
    client.login_member()
    page = client.get('/languages')
    assert 'Keine Ergebnisse gefunden' in page

    create_languages(client.app.session())
    transaction.commit()

    page = client.get('/languages')
    assert 'Italian' in page


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
    assert 'Added language English' in page
    assert 'English' in page

    page = client.get('/languages/new')
    page.form['name'] = 'English'
    page = page.form.submit()
    assert 'English existiert bereits' in page


def test_view_search_translator(client):
    """
    - test pagination
    - test fields not to be shown for member and

    """
    client.get('/translators', status=403)
    client.login_member()
    page = client.get('/translators')
    assert 'Keine Ergebnisse gefunden' in page

    session = client.app.session()
    languages = create_languages(session)
    translators = TranslatorCollection(session)
    for i in range(len(languages)):
        data = copy.deepcopy(translator_data)
        data['email'] = f'translator{1}@test.com'
        data['mother_tongues'] = [languages[i]]
        data['spoken_languages'] = [languages[i]]
        data['written_languages'] = [languages[0]]
        translators.add(**translator_data)

    transaction.commit()

    translator = session.query(Translator).first()
    languages = session.query(Language).all()

    page = client.get('/translators')
    open_in_browser(page)
    assert 'translator1@test.com' in page

