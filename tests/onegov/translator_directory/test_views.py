import transaction

from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import CERTIFICATES
from tests.onegov.translator_directory.shared import translator_data, \
    create_languages


def test_view_new_translator(client):
    """
    - validate unique email
    - validate always lowercase email
    - validate social security number
    - make a run to fill all the fields
    """

    session = client.app.session()
    create_languages(session)
    transaction.commit()

    client.login_editor()
    client.get('/translators/new', status=403)
    client.login_admin()
    page = client.get('/translators/new')

    # check choices
    assert 'Männlich' in page
    assert 'Arabic' in page
    assert CERTIFICATES[0] in page

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
    page = page.form.submit().follow()
    assert 'Uncle' in page
    # test lower-casing the user input
    assert 'test@test.com' in page
    # Test mother tongue set
    assert 'Arabic' in page


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
