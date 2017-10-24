from onegov.gazette.tests import login_admin
from onegov.gazette.tests import login_editor_1
from onegov.gazette.tests import login_publisher
from webtest import TestApp as Client


def test_view_categories(gazette_app):
    client = Client(gazette_app)
    login_admin(client)

    # Test data:
    # 10 / Complaints / inactive
    # 11 / Education / active
    # 12 / Submissions / active
    # 13 / Commercial Register / active
    # 14 / Elections / active

    # add a category
    manage = client.get('/categories')
    manage = manage.click('Neu')
    manage.form['title'] = 'Rubrik XY'
    manage = manage.form.submit().maybe_follow()
    assert 'Rubrik hinzugefügt.' in manage
    assert 'Rubrik XY' in manage
    categories = [
        t.text for t in manage.pyquery('table.categories tbody tr td')
    ]
    assert categories[0] == 'Commercial Register'
    assert categories[1] == 'Ja'
    assert categories[2] == '13'

    assert categories[4] == 'Complaints'
    assert categories[5] == 'Nein'
    assert categories[6] == '10'

    assert categories[8] == 'Education'
    assert categories[9] == 'Ja'
    assert categories[10] == '11'

    assert categories[12] == 'Elections'
    assert categories[13] == 'Ja'
    assert categories[14] == '14'

    assert categories[16] == 'Rubrik XY'
    assert categories[17] == 'Ja'
    assert categories[18] == '15'

    assert categories[20] == 'Submissions'
    assert categories[21] == 'Ja'
    assert categories[22] == '12'

    # use the first category in a notice
    manage = client.get('/notices/drafted/new-notice')
    manage.form['title'] = 'Titel'
    manage.form['organization'] = '200'
    manage.form['category'] = '13'
    manage.form['issues'] = ['2017-44']
    manage.form['text'] = 'Text'
    manage = manage.form.submit().maybe_follow()
    assert '<h2>Titel</h2>' in manage
    assert 'Commercial Register' in manage

    # edit the first category
    manage = client.get('/categories')
    manage = manage.click('Bearbeiten', index=0)
    manage.form['title'] = 'Rubrik Z'
    manage.form['active'] = False
    manage = manage.form.submit().maybe_follow()
    assert 'Rubrik geändert.' in manage
    assert 'Commercial Register' not in manage

    categories = [
        t.text for t in manage.pyquery('table.categories tbody tr td')
    ]
    assert categories[0] == 'Complaints'
    assert categories[4] == 'Education'
    assert categories[8] == 'Elections'
    assert categories[12] == 'Rubrik XY'
    assert categories[16] == 'Rubrik Z'
    assert categories[20] == 'Submissions'
    assert categories[17] == 'Nein'

    # check if the notice has been updated
    manage = client.get('/notice/titel')
    assert 'Commercial Register' not in manage
    assert 'Rubrik Z' in manage

    # delete all but one (unused) categories
    manage = client.get('/categories')
    manage.click('Löschen', index=0).form.submit()
    manage.click('Löschen', index=1).form.submit()
    manage.click('Löschen', index=2).form.submit()
    manage.click('Löschen', index=3).form.submit()
    manage.click('Löschen', index=5).form.submit()

    manage = client.get('/categories')
    assert 'Complaints' not in manage
    assert 'Education' not in manage
    assert 'Elections' not in manage
    assert 'Rubrik XY' not in manage
    assert 'Rubrik Z' in manage
    assert 'Submissions' not in manage

    # Try to delete the used category
    manage = client.get('/categories')
    manage = manage.click('Löschen')
    assert 'Es können nur unbenutzte Rubriken gelöscht werden.' in manage
    assert not manage.forms


def test_view_categories_permissions(gazette_app):
    client = Client(gazette_app)

    login_admin(client)
    manage = client.get('/categories').click('Neu')
    manage.form['title'] = 'XY'
    manage = manage.form.submit().maybe_follow()
    edit_link = manage.click('Bearbeiten', index=0).request.url
    delete_link = manage.click('Löschen', index=0).request.url

    login_publisher(client)
    client.get('/categories', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)

    login_editor_1(client)
    client.get('/categories', status=403)
    client.get(edit_link, status=403)
    client.get(delete_link, status=403)
