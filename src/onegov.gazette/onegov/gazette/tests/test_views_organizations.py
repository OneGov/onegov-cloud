from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_organizations(gazette_app):
    client = Client(gazette_app)
    login_admin(client)

    # Test data:
    # 100 / State Chancellery / active
    # 200 / Civic Community / active
    # 300 / Municipality / active
    # 400 / Evangelical Reformed Parish / active
    # 510 / Sikh Community / inactive
    # 500 / Catholic Parish / active
    # 600 / Corporation / active

    # add a organization
    manage = client.get('/organizations')
    manage = manage.click('Neu')
    manage.form['title'] = 'Organisation XY'
    manage = manage.form.submit().maybe_follow()
    assert 'Organisation hinzugefügt.' in manage
    assert 'Organisation XY' in manage
    organizations = [
        t.text for t in manage.pyquery('table.organizations tbody tr td')
    ]

    assert organizations[0] == 'State Chancellery'
    assert organizations[1] == 'Ja'
    assert organizations[2] == '100'

    assert organizations[4] == 'Civic Community'
    assert organizations[5] == 'Ja'
    assert organizations[6] == '200'

    assert organizations[8] == 'Municipality'
    assert organizations[9] == 'Ja'
    assert organizations[10] == '300'

    assert organizations[12] == 'Evangelical Reformed Parish'
    assert organizations[13] == 'Ja'
    assert organizations[14] == '400'

    assert organizations[16] == 'Sikh Community'
    assert organizations[17] == 'Nein'
    assert organizations[18] == '510'

    assert organizations[20] == 'Catholic Parish'
    assert organizations[21] == 'Ja'
    assert organizations[22] == '500'

    assert organizations[24] == 'Corporation'
    assert organizations[25] == 'Ja'
    assert organizations[26] == '600'

    assert organizations[28] == 'Organisation XY'
    assert organizations[29] == 'Ja'
    assert organizations[30] == '601'

    # use the first organization in a notice
    manage = client.get('/notices/drafted/new-notice')
    manage.form['title'] = 'Titel'
    manage.form['organization'] = '100'
    manage.form['category'] = '13'
    manage.form['issues'] = ['2017-44']
    manage.form['text'] = 'Text'
    manage = manage.form.submit().maybe_follow()
    assert '<h2>Titel</h2>' in manage
    assert 'State Chancellery' in manage

    # edit the first organization
    manage = client.get('/organizations')
    manage = manage.click('Bearbeiten', index=0)
    manage.form['title'] = 'Organisation Z'
    manage.form['active'] = False
    manage = manage.form.submit().maybe_follow()
    assert 'Organisation geändert.' in manage
    assert 'State Chancellery' not in manage
    assert 'Organisation Z' in manage

    organizations = [
        t.text for t in manage.pyquery('table.organizations tbody tr td')
    ]
    assert organizations[0] == 'Organisation Z'
    assert organizations[4] == 'Civic Community'
    assert organizations[8] == 'Municipality'
    assert organizations[12] == 'Evangelical Reformed Parish'
    assert organizations[16] == 'Sikh Community'
    assert organizations[20] == 'Catholic Parish'
    assert organizations[24] == 'Corporation'
    assert organizations[28] == 'Organisation XY'
    assert organizations[1] == 'Nein'

    # check if the notice has been updated
    manage = client.get('/notice/titel')
    assert 'State Chancellery' not in manage
    assert 'Organisation Z' in manage

    # delete all but one (unused) organizations
    manage = client.get('/organizations')
    manage.click('Löschen', index=1).form.submit()
    manage.click('Löschen', index=2).form.submit()
    manage.click('Löschen', index=3).form.submit()
    manage.click('Löschen', index=4).form.submit()
    manage.click('Löschen', index=5).form.submit()
    manage.click('Löschen', index=6).form.submit()
    manage.click('Löschen', index=7).form.submit()

    manage = client.get('/organizations')
    assert 'Organisation Z' in manage
    assert 'Civic Community' not in manage
    assert 'Municipality' not in manage
    assert 'Evangelical Reformed Parish' not in manage
    assert 'Sikh Community' not in manage
    assert 'Catholic Parish' not in manage
    assert 'Corporation' not in manage
    assert 'Organisation XY' not in manage

    # Try to delete the used organization
    manage = client.get('/organizations')
    manage = manage.click('Löschen')
    assert (
        'Nur unbenutzte Organisationen ohne Unterorganisationen können '
        'gelöscht werden.'
    ) in manage
    assert not manage.forms


def test_view_organizations_permissions(gazette_app):
    client = Client(gazette_app)

    login_admin(client)
    manage = client.get('/organizations').click('Neu')
    manage.form['title'] = 'XY'
    manage = manage.form.submit().maybe_follow()
    edit_link = manage.click('Bearbeiten', index=0).request.url
    delete_link = manage.click('Löschen', index=0).request.url

    login_publisher(client)
    client.get('/organizations', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor_1(client)
    client.get('/organizations', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)
