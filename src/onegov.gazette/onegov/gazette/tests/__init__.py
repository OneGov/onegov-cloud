from onegov.gazette.models import Category
from onegov.gazette.models import Organization
from webtest import TestApp as Client


def login_admin(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_publisher(client):
    login = client.get('/auth/login')
    login.form['username'] = 'publisher@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_1(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor1@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_2(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor2@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_editor_3(client):
    login = client.get('/auth/login')
    login.form['username'] = 'editor3@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def login_users(gazette_app):
    admin = Client(gazette_app)
    login_admin(admin)

    editor_1 = Client(gazette_app)
    login_editor_1(editor_1)

    editor_2 = Client(gazette_app)
    login_editor_2(editor_2)

    editor_3 = Client(gazette_app)
    login_editor_3(editor_3)

    publisher = Client(gazette_app)
    login_publisher(publisher)

    return admin, editor_1, editor_2, editor_3, publisher


def submit_notice(user, slug, unable=False, forbidden=False, redirected=False):
    url = '/notice/{}/submit'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    elif redirected:
        assert '/edit' in user.get(url, status=302).location
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung eingereicht" in manage.maybe_follow()


def accept_notice(user, slug, unable=False, forbidden=False, redirected=False):
    url = '/notice/{}/accept'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    elif redirected:
        assert '/edit' in user.get(url, status=302).location
    else:
        manage = user.get(url)
        manage = manage.form.submit()
        assert "Meldung angenommen" in manage.maybe_follow()


def reject_notice(user, slug, unable=False, forbidden=False):
    url = '/notice/{}/reject'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        manage.form['comment'] = 'XYZ'
        manage = manage.form.submit()
        assert "Meldung zurückgewiesen" in manage.maybe_follow()


def edit_notice(user, slug, unable=False, forbidden=False, **kwargs):
    url = '/notice/{}/edit'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        for key, value in kwargs.items():
            manage.form[key] = value
        manage = manage.form.submit()
        assert "Meldung geändert" in manage.maybe_follow()


def edit_notice_unrestricted(user, slug, unable=False, forbidden=False,
                             **kwargs):
    url = '/notice/{}/edit_unrestricted'.format(slug)
    if unable:
        assert not user.get(url).forms
    elif forbidden:
        assert user.get(url, status=403)
    else:
        manage = user.get(url)
        for key, value in kwargs.items():
            manage.form[key] = value
        manage = manage.form.submit()
        assert "Meldung geändert" in manage.maybe_follow()


def change_category(gazette_app, name, **kwargs):
    admin = Client(gazette_app)
    login_admin(admin)

    session = gazette_app.session()
    category = session.query(Category.id).filter_by(name=name).one()[0]
    manage = admin.get('/category/{}/edit'.format(category))
    for key, value in kwargs.items():
        manage.form[key] = value
    manage.form.submit()


def change_organization(gazette_app, name, **kwargs):
    admin = Client(gazette_app)
    login_admin(admin)

    session = gazette_app.session()
    org = session.query(Organization.id).filter_by(name=name).one()[0]
    manage = admin.get('/organization/{}/edit'.format(org))
    for key, value in kwargs.items():
        manage.form[key] = value
    manage.form.submit()
