from morepath import Identity

from onegov.file import FileCollection
from onegov.org.request import OrgRequest
from onegov.town6.views.files import view_town_file_details


def DummyRequest(app, method='GET', csrf=True):
    request = OrgRequest({
        'PATH_INFO': 'http://example.com',
        'SERVER_NAME': 'example.com',
        'SERVER_PORT': '80',
        'wsgi.url_scheme': 'http',
    }, app)
    request.identity = Identity(
        userid='foo',
        groupid='admins',
        role='admin',
        application_id=app.application_id
    )
    request.method = method
    if method == 'POST' and csrf:
        request.GET['csrf-token'] = request.new_csrf_token().decode('utf-8')
    return request


def test_view_town_file_details(town_app):
    files = FileCollection(town_app.session())
    file = files.add('readme.txt', b'README')

    request = DummyRequest(town_app)
    html = view_town_file_details(file, request)
    assert f'http://example.com/storage/{file.id}' in html
    assert 'Öffentlich' in html
    assert 'Publikationsdatum:' not in html
    assert 'Enddatum der Publikation:' in html
    assert 'keine Publikation' in html

    file.published = False
    file.publication = True
    html = view_town_file_details(file, request)
    assert 'Privat' in html
    assert 'Publikationsdatum:' in html
    assert 'Enddatum der Publikation:' in html
    assert '<span>Publikation</span>' in html
